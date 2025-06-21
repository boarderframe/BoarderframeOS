#!/usr/bin/env python3
"""
BoarderframeOS MCP Analytics Server
Tracks business KPIs and provides analytics functionality
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import uvicorn
from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

try:
    import aiosqlite

    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False
    logging.warning("aiosqlite not available - using in-memory storage only")

try:
    import asyncpg

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    logging.warning("asyncpg not available - PostgreSQL support disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_analytics")


class EventData(BaseModel):
    """Event data model for tracking metrics"""

    event_type: str
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


# Background Processing Configuration
BATCH_SIZE = 50  # Process events in batches
BATCH_TIMEOUT = 5.0  # Process partial batches after timeout
MAX_QUEUE_SIZE = 10000  # Maximum events in queue

# PostgreSQL Configuration
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos",
)
POSTGRES_POOL_MIN = int(os.getenv("ANALYTICS_POOL_MIN", "5"))
POSTGRES_POOL_MAX = int(os.getenv("ANALYTICS_POOL_MAX", "15"))


class KpiRequest(BaseModel):
    """Request for KPI calculation"""

    metric: str
    timeframe: str = "day"  # day, week, month
    filters: Optional[Dict[str, Any]] = None


class EventProcessor:
    """Background event processor with batching and PostgreSQL persistence"""

    def __init__(self, db_path: str = None, use_postgres: bool = True):
        self.db_path = db_path
        self.use_postgres = use_postgres and HAS_ASYNCPG
        self.event_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self.processing_task = None
        self.metrics_cache = defaultdict(float)
        self.last_batch_time = time.time()

        # PostgreSQL connection pool
        self.pg_pool = None

        # Performance tracking
        self.stats = {
            "events_processed": 0,
            "batches_processed": 0,
            "avg_batch_size": 0,
            "processing_errors": 0,
            "queue_full_drops": 0,
            "database_type": "postgresql" if self.use_postgres else "sqlite",
        }

    async def initialize(self):
        """Initialize database and start background processing"""
        if self.use_postgres:
            await self._initialize_postgresql()
        elif HAS_SQLITE:
            await self._initialize_database()
        self.processing_task = asyncio.create_task(self._process_events())

    async def _initialize_database(self):
        """Initialize SQLite database for analytics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create events table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    agent_id TEXT,
                    customer_id TEXT,
                    data TEXT,  -- JSON data
                    metadata TEXT,  -- JSON metadata
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for performance
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON analytics_events(event_type)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_agent ON analytics_events(agent_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON analytics_events(timestamp)"
            )

            await db.commit()
            logger.info("Analytics database initialized")

    async def _initialize_postgresql(self):
        """Initialize PostgreSQL database for analytics"""
        try:
            # Create connection pool
            self.pg_pool = await asyncpg.create_pool(
                POSTGRES_URL,
                min_size=POSTGRES_POOL_MIN,
                max_size=POSTGRES_POOL_MAX,
                command_timeout=60,
            )

            # Create analytics tables if they don't exist
            async with self.pg_pool.acquire() as conn:
                # Create events table
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        event_type TEXT NOT NULL,
                        agent_id TEXT,
                        customer_id TEXT,
                        data JSONB,
                        metadata JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create metrics table for aggregated data
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analytics_metrics (
                        id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                        metric_name TEXT NOT NULL,
                        metric_value DECIMAL NOT NULL,
                        metric_type TEXT,
                        dimensions JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes for performance
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type)"
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_events_agent ON analytics_events(agent_id)"
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_events_customer ON analytics_events(customer_id)"
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp)"
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name ON analytics_metrics(metric_name)"
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_metrics_timestamp ON analytics_metrics(timestamp)"
                )

                # Create GIN index for JSONB data
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_events_data ON analytics_events USING GIN(data)"
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_analytics_metrics_dimensions ON analytics_metrics USING GIN(dimensions)"
                )

            logger.info("Analytics PostgreSQL database initialized")

        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")
            raise

    async def queue_event(self, event_data: Dict[str, Any]) -> bool:
        """Queue event for background processing"""
        try:
            self.event_queue.put_nowait(event_data)
            return True
        except asyncio.QueueFull:
            self.stats["queue_full_drops"] += 1
            logger.warning("Event queue full, dropping event")
            return False

    async def _process_events(self):
        """Background task to process events in batches"""
        batch = []

        while True:
            try:
                # Wait for event with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(), timeout=BATCH_TIMEOUT
                    )
                    batch.append(event)
                except asyncio.TimeoutError:
                    # Process partial batch on timeout
                    if batch:
                        await self._process_batch(batch)
                        batch = []
                    continue

                # Process batch if full or timeout reached
                current_time = time.time()
                if (
                    len(batch) >= BATCH_SIZE
                    or current_time - self.last_batch_time >= BATCH_TIMEOUT
                ):
                    await self._process_batch(batch)
                    batch = []
                    self.last_batch_time = current_time

            except Exception as e:
                logger.error(f"Event processing error: {e}")
                self.stats["processing_errors"] += 1
                await asyncio.sleep(1)  # Brief pause on error

    async def _process_batch(self, events: List[Dict[str, Any]]):
        """Process a batch of events efficiently"""
        if not events:
            return

        try:
            # Update stats
            self.stats["events_processed"] += len(events)
            self.stats["batches_processed"] += 1
            self.stats["avg_batch_size"] = (
                self.stats["events_processed"] / self.stats["batches_processed"]
            )

            # Group events by type for efficient processing
            events_by_type = defaultdict(list)
            for event in events:
                events_by_type[event["event_type"]].append(event)

            # Process each type efficiently
            for event_type, type_events in events_by_type.items():
                await self._process_events_by_type(event_type, type_events)

            # Store events in database if available
            if self.use_postgres and self.pg_pool:
                await self._store_events_batch_postgres(events)
            elif HAS_SQLITE:
                await self._store_events_batch(events)

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            self.stats["processing_errors"] += 1

    async def _process_events_by_type(
        self, event_type: str, events: List[Dict[str, Any]]
    ):
        """Process events of the same type efficiently"""
        if event_type == "revenue":
            total_revenue = sum(event["data"].get("amount", 0) for event in events)
            self.metrics_cache["total_revenue"] += total_revenue

            # Update per-agent revenue
            for event in events:
                if event.get("agent_id"):
                    self.metrics_cache[
                        f"revenue_per_agent_{event['agent_id']}"
                    ] += event["data"].get("amount", 0)

        elif event_type == "new_customer":
            self.metrics_cache["customers_acquired"] += len(events)

        elif event_type == "churn":
            self.metrics_cache["churn_count"] += len(events)

        elif event_type == "api_usage":
            for event in events:
                endpoint = event["data"].get("endpoint", "unknown")
                tokens = event["data"].get("tokens", 0)
                self.metrics_cache[f"api_usage_{endpoint}"] += tokens

    async def _store_events_batch(self, events: List[Dict[str, Any]]):
        """Store events batch in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                """
                INSERT INTO analytics_events
                (id, event_type, agent_id, customer_id, data, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        event["id"],
                        event["event_type"],
                        event.get("agent_id"),
                        event.get("customer_id"),
                        json.dumps(event["data"]),
                        json.dumps(event.get("metadata", {})),
                        event["timestamp"],
                    )
                    for event in events
                ],
            )
            await db.commit()

    async def _store_events_batch_postgres(self, events: List[Dict[str, Any]]):
        """Store events batch in PostgreSQL database"""
        async with self.pg_pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO analytics_events
                (id, event_type, agent_id, customer_id, data, metadata, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                [
                    (
                        event["id"],
                        event["event_type"],
                        event.get("agent_id"),
                        event.get("customer_id"),
                        json.dumps(event["data"]),
                        json.dumps(event.get("metadata", {})),
                        event["timestamp"],
                    )
                    for event in events
                ],
            )

    def get_cached_metrics(self) -> Dict[str, float]:
        """Get cached metrics"""
        return dict(self.metrics_cache)

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "queue_size": self.event_queue.qsize(),
            "max_queue_size": MAX_QUEUE_SIZE,
            "database_type": self.stats["database_type"],
            "processing_stats": self.stats,
            "batch_config": {"batch_size": BATCH_SIZE, "batch_timeout": BATCH_TIMEOUT},
        }


class MCPAnalyticsServer:
    """
    MCP Analytics Server with background processing and database persistence
    Tracks business KPIs and provides analytics functionality
    """

    def __init__(self):
        """Initialize the analytics server"""
        self.app = FastAPI(title="MCP Analytics Server")
        self.setup_app()
        self.database_url = "http://localhost:8010/rpc"  # PostgreSQL Database Server

        # Background event processor (prefer PostgreSQL)
        self.db_path = "analytics.db"
        self.event_processor = EventProcessor(self.db_path, use_postgres=True)

        # Legacy in-memory storage for compatibility
        self.events = []
        self.metrics = {}

    def setup_app(self):
        """Set up the FastAPI application"""
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add routes
        self.app.get("/health")(self.health_check)
        self.app.post("/track")(self.track_event)
        self.app.get("/metrics/customer-acquisition")(
            self.get_customer_acquisition_cost
        )
        self.app.get("/metrics/lifetime-value")(self.get_customer_lifetime_value)
        self.app.get("/metrics/churn")(self.get_churn_rate)
        self.app.get("/metrics/revenue-per-agent")(self.get_revenue_per_agent)
        self.app.get("/metrics/api-usage")(self.get_api_usage_metrics)
        self.app.post("/kpi")(self.calculate_kpi)
        self.app.get("/dashboard-data")(self.get_dashboard_data)

        # New performance and monitoring endpoints
        self.app.get("/performance")(self.get_performance_stats)
        self.app.get("/metrics/cached")(self.get_cached_metrics)

    async def start(self, port: int = 8007):
        """Start the Analytics server"""
        logger.info(f"Starting MCP Analytics Server on port {port}")

        # Initialize database connection
        await self.initialize_database()

        # Initialize background event processor
        await self.event_processor.initialize()

        # Start the server
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()

    async def initialize_database(self):
        """Initialize database connection"""
        logger.info("Initializing analytics database connection")

    async def health_check(self):
        """Health check endpoint"""
        processor_stats = self.event_processor.get_processing_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "tracked_events": len(self.events),
            "metrics_count": len(self.metrics),
            "server": "mcp_analytics",
            "background_processing": {
                "queue_size": processor_stats["queue_size"],
                "events_processed": processor_stats["processing_stats"][
                    "events_processed"
                ],
                "batches_processed": processor_stats["processing_stats"][
                    "batches_processed"
                ],
            },
            "database_available": HAS_ASYNCPG or HAS_SQLITE,
            "postgresql_available": HAS_ASYNCPG,
            "sqlite_available": HAS_SQLITE,
        }

    async def track_event(self, event: EventData):
        """Track an analytics event with background processing"""
        try:
            # Generate an event ID
            event_id = str(uuid.uuid4())

            # Record event details
            event_data = {
                "id": event_id,
                "event_type": event.event_type,
                "agent_id": event.agent_id,
                "customer_id": event.customer_id,
                "data": event.data,
                "metadata": event.metadata or {},
                "timestamp": datetime.now().isoformat(),
            }

            # Queue event for background processing
            queued = await self.event_processor.queue_event(event_data)

            # Also store in legacy in-memory storage for immediate access
            self.events.append(event_data)
            await self.update_metrics(event_data)

            return {
                "event_id": event_id,
                "status": "queued" if queued else "queued_failed_stored_memory",
                "background_processing": queued,
            }

        except Exception as e:
            logger.error(f"Event tracking error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Event tracking error: {str(e)}"
            )

    async def update_metrics(self, event_data: Dict[str, Any]):
        """Update metrics based on new event"""
        event_type = event_data["event_type"]

        # Update different metrics based on event type
        if event_type == "new_customer":
            # Update customer acquisition metrics
            self.metrics["customers_acquired"] = (
                self.metrics.get("customers_acquired", 0) + 1
            )

        elif event_type == "revenue":
            # Update revenue metrics
            amount = event_data["data"].get("amount", 0)
            self.metrics["total_revenue"] = (
                self.metrics.get("total_revenue", 0) + amount
            )

            # Track revenue per agent if agent_id is provided
            if event_data["agent_id"]:
                agent_id = event_data["agent_id"]
                if "revenue_per_agent" not in self.metrics:
                    self.metrics["revenue_per_agent"] = {}
                self.metrics["revenue_per_agent"][agent_id] = (
                    self.metrics["revenue_per_agent"].get(agent_id, 0) + amount
                )

        elif event_type == "churn":
            # Update churn metrics
            self.metrics["churn_count"] = self.metrics.get("churn_count", 0) + 1

        elif event_type == "api_usage":
            # Update API usage metrics
            tokens = event_data["data"].get("tokens", 0)
            endpoint = event_data["data"].get("endpoint", "unknown")

            if "api_usage" not in self.metrics:
                self.metrics["api_usage"] = {}
            if endpoint not in self.metrics["api_usage"]:
                self.metrics["api_usage"][endpoint] = 0
            self.metrics["api_usage"][endpoint] += tokens

    async def get_customer_acquisition_cost(self, timeframe: str = "month"):
        """Calculate customer acquisition cost"""
        # In a real implementation, this would query the database
        # For now, we'll return mock data

        marketing_spend = 5000  # Mock value
        customers_acquired = self.metrics.get("customers_acquired", 10)  # Mock fallback

        if customers_acquired == 0:
            cac = 0
        else:
            cac = marketing_spend / customers_acquired

        return {
            "metric": "customer_acquisition_cost",
            "value": cac,
            "currency": "usd",
            "timeframe": timeframe,
            "customers_acquired": customers_acquired,
            "marketing_spend": marketing_spend,
        }

    async def get_customer_lifetime_value(self, timeframe: str = "month"):
        """Calculate customer lifetime value"""
        # In a real implementation, this would query the database
        # For now, we'll return mock data

        avg_revenue_per_customer = 150  # Mock value
        avg_customer_lifespan = 12  # Mock value in months
        clv = avg_revenue_per_customer * avg_customer_lifespan

        return {
            "metric": "customer_lifetime_value",
            "value": clv,
            "currency": "usd",
            "timeframe": timeframe,
            "avg_revenue_per_customer": avg_revenue_per_customer,
            "avg_customer_lifespan": avg_customer_lifespan,
        }

    async def get_churn_rate(self, timeframe: str = "month"):
        """Calculate churn rate"""
        # In a real implementation, this would query the database
        # For now, we'll return mock data

        total_customers_start = 100  # Mock value
        churned_customers = self.metrics.get("churn_count", 5)  # Mock fallback

        if total_customers_start == 0:
            churn_rate = 0
        else:
            churn_rate = (churned_customers / total_customers_start) * 100

        return {
            "metric": "churn_rate",
            "value": churn_rate,
            "unit": "percentage",
            "timeframe": timeframe,
            "total_customers_start": total_customers_start,
            "churned_customers": churned_customers,
        }

    async def get_revenue_per_agent(self):
        """Get revenue generated per agent"""
        revenue_per_agent = self.metrics.get("revenue_per_agent", {})

        # Sort agents by revenue (highest first)
        sorted_agents = sorted(
            revenue_per_agent.items(), key=lambda x: x[1], reverse=True
        )

        results = [
            {"agent_id": agent_id, "revenue": revenue}
            for agent_id, revenue in sorted_agents
        ]

        return {
            "metric": "revenue_per_agent",
            "data": results,
            "currency": "usd",
            "total_agents": len(results),
        }

    async def get_api_usage_metrics(self):
        """Get API usage metrics"""
        api_usage = self.metrics.get("api_usage", {})

        total_tokens = sum(api_usage.values())

        # Sort endpoints by usage (highest first)
        sorted_usage = sorted(api_usage.items(), key=lambda x: x[1], reverse=True)

        results = [
            {"endpoint": endpoint, "tokens": tokens}
            for endpoint, tokens in sorted_usage
        ]

        return {
            "metric": "api_usage",
            "data": results,
            "total_tokens": total_tokens,
            "endpoints_count": len(results),
        }

    async def calculate_kpi(self, request: KpiRequest):
        """Calculate a specific KPI"""
        metric = request.metric
        timeframe = request.timeframe
        filters = request.filters or {}

        if metric == "customer_acquisition_cost":
            return await self.get_customer_acquisition_cost(timeframe)
        elif metric == "customer_lifetime_value":
            return await self.get_customer_lifetime_value(timeframe)
        elif metric == "churn_rate":
            return await self.get_churn_rate(timeframe)
        elif metric == "revenue_per_agent":
            return await self.get_revenue_per_agent()
        elif metric == "api_usage":
            return await self.get_api_usage_metrics()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

    async def get_dashboard_data(self):
        """Get data for the analytics dashboard"""
        # Collect all KPIs for dashboard display
        revenue_per_agent = await self.get_revenue_per_agent()
        cac = await self.get_customer_acquisition_cost()
        clv = await self.get_customer_lifetime_value()
        churn = await self.get_churn_rate()
        api_usage = await self.get_api_usage_metrics()

        # Calculate additional metrics
        clv_cac_ratio = clv["value"] / cac["value"] if cac["value"] > 0 else 0

        return {
            "metrics": {
                "total_revenue": self.metrics.get("total_revenue", 0),
                "customers_acquired": self.metrics.get("customers_acquired", 0),
                "churn_rate": churn["value"],
                "clv_cac_ratio": clv_cac_ratio,
            },
            "revenue_per_agent": revenue_per_agent["data"],
            "api_usage": api_usage["data"],
        }

    async def get_performance_stats(self):
        """Get performance statistics for background processing"""
        processor_stats = self.event_processor.get_processing_stats()
        cached_metrics = self.event_processor.get_cached_metrics()

        return {
            "background_processing": processor_stats,
            "cached_metrics_count": len(cached_metrics),
            "memory_metrics_count": len(self.metrics),
            "memory_events_count": len(self.events),
            "database_available": HAS_SQLITE,
            "timestamp": datetime.now().isoformat(),
        }

    async def get_cached_metrics(self):
        """Get cached metrics from background processor"""
        cached_metrics = self.event_processor.get_cached_metrics()

        # Convert to more readable format
        formatted_metrics = {}
        for key, value in cached_metrics.items():
            if key.startswith("revenue_per_agent_"):
                agent_id = key.replace("revenue_per_agent_", "")
                if "revenue_per_agent" not in formatted_metrics:
                    formatted_metrics["revenue_per_agent"] = {}
                formatted_metrics["revenue_per_agent"][agent_id] = value
            elif key.startswith("api_usage_"):
                endpoint = key.replace("api_usage_", "")
                if "api_usage" not in formatted_metrics:
                    formatted_metrics["api_usage"] = {}
                formatted_metrics["api_usage"][endpoint] = value
            else:
                formatted_metrics[key] = value

        return {
            "cached_metrics": formatted_metrics,
            "cache_count": len(cached_metrics),
            "data_source": "background_processor",
            "timestamp": datetime.now().isoformat(),
        }


async def main():
    """Run the server directly"""
    import uvicorn

    # Default port
    port = 8007

    # Get port from command line if specified
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid port: {sys.argv[1]}. Using default: {port}")

    # Create and start the server
    server = MCPAnalyticsServer()
    await server.start(port)


if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Analytics Server")
