"""
BoarderframeOS Registry Server
Centralized registry management for agents, servers, departments, tools, workflows, and resources
"""

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import asyncpg
import redis.asyncio as redis
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "registry.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("registry_server")

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REGISTRY_PORT = int(os.getenv("REGISTRY_PORT", "8000"))

# Global connections
db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class RegistryResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: str
    count: Optional[int] = None


# Agent Registry Models
class AgentRegistration(BaseModel):
    agent_id: str
    name: str
    department_id: Optional[str] = None
    agent_type: str
    capabilities: List[str] = []
    supported_tools: List[str] = []
    communication_endpoints: Dict[str, str] = {}
    api_endpoints: Dict[str, str] = {}
    health_check_url: Optional[str] = None
    resource_requirements: Dict[str, Any] = {}
    max_concurrent_tasks: int = 1
    version: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class AgentHeartbeat(BaseModel):
    agent_id: str
    status: str = "online"
    current_load: float = 0.0
    current_tasks: int = 0
    response_time_ms: Optional[int] = None
    health_status: str = "healthy"


# Server Registry Models
class ServerRegistration(BaseModel):
    name: str
    server_type: str
    endpoint_url: str
    internal_url: Optional[str] = None
    health_check_url: Optional[str] = None
    capabilities: List[str] = []
    supported_protocols: List[str] = []
    api_version: Optional[str] = None
    max_connections: int = 100
    authentication: Dict[str, Any] = {}
    configuration: Dict[str, Any] = {}
    environment: str = "development"
    version: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


# ============================================================================
# REGISTRY MANAGER
# ============================================================================


class RegistryManager:
    """Centralized registry management for all BoarderframeOS components"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[redis.Redis] = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize PostgreSQL pool and Redis connection"""
        if self.is_initialized:
            return

        try:
            # Initialize PostgreSQL connection pool
            self.pool = await asyncpg.create_pool(
                DATABASE_URL, min_size=5, max_size=15, command_timeout=60
            )

            # Initialize Redis connection
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)

            # Test connections
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                logger.info("Registry PostgreSQL connection pool initialized")

            await self.redis.ping()
            logger.info("Registry Redis connection initialized")

            self.is_initialized = True

        except Exception as e:
            logger.error(f"Registry initialization failed: {e}")
            raise HTTPException(status_code=500, detail=f"Registry init failed: {e}")

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
        if self.redis:
            await self.redis.close()

    # ========================================================================
    # AGENT REGISTRY METHODS
    # ========================================================================

    async def register_agent(self, registration: AgentRegistration) -> RegistryResponse:
        """Register a new agent or update existing registration"""
        try:
            await self.initialize()

            async with self.pool.acquire() as conn:
                # Insert or update agent registry
                await conn.execute(
                    """
                    INSERT INTO agent_registry (
                        agent_id, name, department_id, agent_type, capabilities,
                        supported_tools, communication_endpoints, api_endpoints,
                        health_check_url, resource_requirements, max_concurrent_tasks,
                        version, tags, metadata, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        department_id = EXCLUDED.department_id,
                        agent_type = EXCLUDED.agent_type,
                        capabilities = EXCLUDED.capabilities,
                        supported_tools = EXCLUDED.supported_tools,
                        communication_endpoints = EXCLUDED.communication_endpoints,
                        api_endpoints = EXCLUDED.api_endpoints,
                        health_check_url = EXCLUDED.health_check_url,
                        resource_requirements = EXCLUDED.resource_requirements,
                        max_concurrent_tasks = EXCLUDED.max_concurrent_tasks,
                        version = EXCLUDED.version,
                        tags = EXCLUDED.tags,
                        metadata = EXCLUDED.metadata,
                        status = 'online',
                        updated_at = NOW()
                """,
                    registration.agent_id,
                    registration.name,
                    registration.department_id,
                    registration.agent_type,
                    json.dumps(registration.capabilities),
                    json.dumps(registration.supported_tools),
                    json.dumps(registration.communication_endpoints),
                    json.dumps(registration.api_endpoints),
                    registration.health_check_url,
                    json.dumps(registration.resource_requirements),
                    registration.max_concurrent_tasks,
                    registration.version,
                    registration.tags,
                    json.dumps(registration.metadata),
                    "online",
                )

                # Publish registration event
                await self._publish_registry_event(
                    "agent_registered",
                    {
                        "agent_id": registration.agent_id,
                        "name": registration.name,
                        "agent_type": registration.agent_type,
                    },
                )

                return RegistryResponse(
                    success=True,
                    data={"agent_id": registration.agent_id, "status": "registered"},
                    timestamp=datetime.utcnow().isoformat(),
                )

        except Exception as e:
            logger.error(f"Agent registration failed: {e}")
            return RegistryResponse(
                success=False, error=str(e), timestamp=datetime.utcnow().isoformat()
            )

    async def discover_agents(
        self,
        agent_type: Optional[str] = None,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> RegistryResponse:
        """Discover agents based on filters"""
        try:
            await self.initialize()

            # Build dynamic query
            where_conditions = ["1=1"]
            params = []
            param_count = 1

            if agent_type:
                where_conditions.append(f"agent_type = ${param_count}")
                params.append(agent_type)
                param_count += 1

            if department_id:
                where_conditions.append(f"department_id = ${param_count}")
                params.append(department_id)
                param_count += 1

            if status:
                where_conditions.append(f"status = ${param_count}")
                params.append(status)
                param_count += 1

            query = f"""
                SELECT
                    agent_id, name, department_id, agent_type, status, health_status,
                    capabilities, supported_tools, communication_endpoints, api_endpoints,
                    current_load, current_tasks, max_concurrent_tasks, last_heartbeat,
                    version, tags, metadata
                FROM agent_registry
                WHERE {' AND '.join(where_conditions)}
                ORDER BY last_heartbeat DESC
            """

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                agents = [dict(row) for row in rows]

                return RegistryResponse(
                    success=True,
                    data=agents,
                    count=len(agents),
                    timestamp=datetime.utcnow().isoformat(),
                )

        except Exception as e:
            logger.error(f"Agent discovery failed: {e}")
            return RegistryResponse(
                success=False, error=str(e), timestamp=datetime.utcnow().isoformat()
            )

    # ========================================================================
    # SERVER REGISTRY METHODS
    # ========================================================================

    async def register_server(
        self, registration: ServerRegistration
    ) -> RegistryResponse:
        """Register a new server or update existing registration"""
        try:
            await self.initialize()

            async with self.pool.acquire() as conn:
                server_id = await conn.fetchval(
                    """
                    INSERT INTO server_registry (
                        name, server_type, endpoint_url, internal_url, health_check_url,
                        capabilities, supported_protocols, api_version, max_connections,
                        authentication, configuration, environment, version, tags, metadata, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    ON CONFLICT (name) DO UPDATE SET
                        server_type = EXCLUDED.server_type,
                        endpoint_url = EXCLUDED.endpoint_url,
                        internal_url = EXCLUDED.internal_url,
                        health_check_url = EXCLUDED.health_check_url,
                        capabilities = EXCLUDED.capabilities,
                        supported_protocols = EXCLUDED.supported_protocols,
                        api_version = EXCLUDED.api_version,
                        max_connections = EXCLUDED.max_connections,
                        authentication = EXCLUDED.authentication,
                        configuration = EXCLUDED.configuration,
                        environment = EXCLUDED.environment,
                        version = EXCLUDED.version,
                        tags = EXCLUDED.tags,
                        metadata = EXCLUDED.metadata,
                        status = 'online',
                        updated_at = NOW()
                    RETURNING id
                """,
                    registration.name,
                    registration.server_type,
                    registration.endpoint_url,
                    registration.internal_url,
                    registration.health_check_url,
                    json.dumps(registration.capabilities),
                    json.dumps(registration.supported_protocols),
                    registration.api_version,
                    registration.max_connections,
                    json.dumps(registration.authentication),
                    json.dumps(registration.configuration),
                    registration.environment,
                    registration.version,
                    registration.tags,
                    json.dumps(registration.metadata),
                    "online",
                )

                return RegistryResponse(
                    success=True,
                    data={"server_id": str(server_id), "status": "registered"},
                    timestamp=datetime.utcnow().isoformat(),
                )

        except Exception as e:
            logger.error(f"Server registration failed: {e}")
            return RegistryResponse(
                success=False, error=str(e), timestamp=datetime.utcnow().isoformat()
            )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def _publish_registry_event(self, event_type: str, data: Dict[str, Any]):
        """Publish registry events to Redis Streams"""
        try:
            if self.redis:
                event = {
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": json.dumps(data, default=str),
                }
                await self.redis.xadd("registry_events", event)
        except Exception as e:
            logger.warning(f"Failed to publish registry event: {e}")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive registry health status"""
        try:
            await self.initialize()

            async with self.pool.acquire() as conn:
                # Get agent counts
                agent_stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'online') as online,
                        COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy
                    FROM agent_registry
                """
                )

                # Get server counts
                server_stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'online') as online,
                        COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy
                    FROM server_registry
                """
                )

                return {
                    "status": "healthy",
                    "agents": {
                        "total": agent_stats["total"] if agent_stats else 0,
                        "online": agent_stats["online"] if agent_stats else 0,
                        "healthy": agent_stats["healthy"] if agent_stats else 0,
                    },
                    "servers": {
                        "total": server_stats["total"] if server_stats else 0,
                        "online": server_stats["online"] if server_stats else 0,
                        "healthy": server_stats["healthy"] if server_stats else 0,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Health status check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="BoarderframeOS Registry Server",
    version="1.0.0",
    description="Centralized registry for agents, servers, departments, tools, and workflows",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global registry manager
registry_manager = RegistryManager()


async def get_registry_manager():
    """Dependency for registry manager"""
    await registry_manager.initialize()
    return registry_manager


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    """Registry health check endpoint"""
    try:
        # Try to get registry manager if possible
        registry = await get_registry_manager()
        return await registry.get_health_status()
    except Exception as e:
        # Return basic health info if registry not available
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "registry_server",
            "port": REGISTRY_PORT,
            "database_status": "unavailable",
            "redis_status": "unknown",
            "error": str(e)[:100],
        }


# Agent Registry Endpoints
@app.post("/agents/register", response_model=RegistryResponse)
async def register_agent(
    registration: AgentRegistration,
    registry: RegistryManager = Depends(get_registry_manager),
):
    """Register a new agent"""
    return await registry.register_agent(registration)


@app.get("/agents/discover", response_model=RegistryResponse)
async def discover_agents(
    agent_type: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    registry: RegistryManager = Depends(get_registry_manager),
):
    """Discover agents based on filters"""
    return await registry.discover_agents(agent_type, department_id, status)


# Server Registry Endpoints
@app.post("/servers/register", response_model=RegistryResponse)
async def register_server(
    registration: ServerRegistration,
    registry: RegistryManager = Depends(get_registry_manager),
):
    """Register a new server"""
    return await registry.register_server(registration)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BoarderframeOS Registry Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument(
        "--port", type=int, default=REGISTRY_PORT, help="Port to bind to"
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting Registry Server on {args.host}:{args.port}")
    logger.info(f"PostgreSQL: {DATABASE_URL}")
    logger.info(f"Redis: {REDIS_URL}")

    uvicorn.run(
        "registry_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
