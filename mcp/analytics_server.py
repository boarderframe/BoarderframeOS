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
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import aiohttp
from fastapi import FastAPI, HTTPException, Request, Depends, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_analytics")

class EventData(BaseModel):
    """Event data model for tracking metrics"""
    event_type: str
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class KpiRequest(BaseModel):
    """Request for KPI calculation"""
    metric: str
    timeframe: str = "day"  # day, week, month
    filters: Optional[Dict[str, Any]] = None


class MCPAnalyticsServer:
    """
    MCP Analytics Server
    Tracks business KPIs and provides analytics functionality
    """
    
    def __init__(self):
        """Initialize the analytics server"""
        self.app = FastAPI(title="MCP Analytics Server")
        self.setup_app()
        self.database_url = "http://localhost:8004/rpc"  # MCP Database Server
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
        self.app.get("/metrics/customer-acquisition")(self.get_customer_acquisition_cost)
        self.app.get("/metrics/lifetime-value")(self.get_customer_lifetime_value)
        self.app.get("/metrics/churn")(self.get_churn_rate)
        self.app.get("/metrics/revenue-per-agent")(self.get_revenue_per_agent)
        self.app.get("/metrics/api-usage")(self.get_api_usage_metrics)
        self.app.post("/kpi")(self.calculate_kpi)
        self.app.get("/dashboard-data")(self.get_dashboard_data)
        
    async def start(self, port: int = 8007):
        """Start the Analytics server"""
        logger.info(f"Starting MCP Analytics Server on port {port}")
        
        # Initialize database connection
        await self.initialize_database()
        
        # Start the server
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()
        
    async def initialize_database(self):
        """Initialize database connection"""
        logger.info("Initializing analytics database connection")
        
    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "tracked_events": len(self.events),
            "metrics_count": len(self.metrics),
            "server": "mcp_analytics"
        }
        
    async def track_event(self, event: EventData):
        """Track an analytics event"""
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
                "timestamp": datetime.now().isoformat()
            }
            
            # Store event
            self.events.append(event_data)
            
            # Update relevant metrics
            await self.update_metrics(event_data)
            
            return {
                "event_id": event_id,
                "status": "recorded"
            }
            
        except Exception as e:
            logger.error(f"Event tracking error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Event tracking error: {str(e)}")
            
    async def update_metrics(self, event_data: Dict[str, Any]):
        """Update metrics based on new event"""
        event_type = event_data["event_type"]
        
        # Update different metrics based on event type
        if event_type == "new_customer":
            # Update customer acquisition metrics
            self.metrics["customers_acquired"] = self.metrics.get("customers_acquired", 0) + 1
            
        elif event_type == "revenue":
            # Update revenue metrics
            amount = event_data["data"].get("amount", 0)
            self.metrics["total_revenue"] = self.metrics.get("total_revenue", 0) + amount
            
            # Track revenue per agent if agent_id is provided
            if event_data["agent_id"]:
                agent_id = event_data["agent_id"]
                if "revenue_per_agent" not in self.metrics:
                    self.metrics["revenue_per_agent"] = {}
                self.metrics["revenue_per_agent"][agent_id] = self.metrics["revenue_per_agent"].get(agent_id, 0) + amount
                
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
            "marketing_spend": marketing_spend
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
            "avg_customer_lifespan": avg_customer_lifespan
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
            "churned_customers": churned_customers
        }
        
    async def get_revenue_per_agent(self):
        """Get revenue generated per agent"""
        revenue_per_agent = self.metrics.get("revenue_per_agent", {})
        
        # Sort agents by revenue (highest first)
        sorted_agents = sorted(
            revenue_per_agent.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        results = [
            {"agent_id": agent_id, "revenue": revenue}
            for agent_id, revenue in sorted_agents
        ]
        
        return {
            "metric": "revenue_per_agent",
            "data": results,
            "currency": "usd",
            "total_agents": len(results)
        }
        
    async def get_api_usage_metrics(self):
        """Get API usage metrics"""
        api_usage = self.metrics.get("api_usage", {})
        
        total_tokens = sum(api_usage.values())
        
        # Sort endpoints by usage (highest first)
        sorted_usage = sorted(
            api_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        results = [
            {"endpoint": endpoint, "tokens": tokens}
            for endpoint, tokens in sorted_usage
        ]
        
        return {
            "metric": "api_usage",
            "data": results,
            "total_tokens": total_tokens,
            "endpoints_count": len(results)
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
                "clv_cac_ratio": clv_cac_ratio
            },
            "revenue_per_agent": revenue_per_agent["data"],
            "api_usage": api_usage["data"]
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
        import uvicorn
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Analytics Server")