"""
BoarderframeOS Unified Registry System
=====================================

A robust, real-time registry system for managing all BoarderframeOS components:
- Agents (120+ AI agents)
- Leaders (Department heads)
- Departments (24 biblical-named departments)
- Divisions (9 major organizational divisions)
- Databases (PostgreSQL, SQLite, Redis)
- Servers (Core Systems, MCP Servers, Business Services)

Features:
- PostgreSQL persistence with advanced indexing
- Redis Streams for real-time events
- WebSocket support for live updates
- In-memory caching for performance
- Automatic health monitoring
- Service discovery protocol
- Department hierarchy management
- Resource allocation tracking
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
import aiohttp
import asyncpg
import aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Registry Entry Types
class RegistryType(str, Enum):
    AGENT = "agent"
    LEADER = "leader"
    DEPARTMENT = "department"
    DIVISION = "division"
    DATABASE = "database"
    SERVER_CORE = "server_core"
    SERVER_MCP = "server_mcp"
    SERVER_BUSINESS = "server_business"

# Service Status
class ServiceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"

# Base Registry Entry Models
class RegistryEntry(BaseModel):
    """Base model for all registry entries"""
    id: str
    name: str
    type: RegistryType
    status: ServiceStatus = ServiceStatus.OFFLINE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=list)
    health_score: float = Field(default=100.0)
    last_heartbeat: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentEntry(RegistryEntry):
    """Registry entry for AI agents"""
    type: RegistryType = RegistryType.AGENT
    department_id: Optional[str] = None
    division_id: Optional[str] = None
    leader_id: Optional[str] = None
    llm_model: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    current_load: float = 0.0
    max_load: float = 100.0
    total_interactions: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    
class LeaderEntry(AgentEntry):
    """Registry entry for department leaders"""
    type: RegistryType = RegistryType.LEADER
    subordinates: List[str] = Field(default_factory=list)
    department_managed: Optional[str] = None
    leadership_style: Optional[str] = None

class DepartmentEntry(RegistryEntry):
    """Registry entry for departments"""
    type: RegistryType = RegistryType.DEPARTMENT
    division_id: str
    leader_id: Optional[str] = None
    agent_ids: List[str] = Field(default_factory=list)
    budget: float = 0.0
    revenue: float = 0.0
    description: Optional[str] = None

class DivisionEntry(RegistryEntry):
    """Registry entry for divisions"""
    type: RegistryType = RegistryType.DIVISION
    department_ids: List[str] = Field(default_factory=list)
    executive_id: Optional[str] = None
    total_agents: int = 0
    total_budget: float = 0.0
    total_revenue: float = 0.0

class DatabaseEntry(RegistryEntry):
    """Registry entry for databases"""
    type: RegistryType = RegistryType.DATABASE
    db_type: str  # postgresql, sqlite, redis
    connection_string: str
    port: int
    max_connections: int = 100
    current_connections: int = 0
    query_performance: float = 0.0  # avg query time in ms

class ServerEntry(RegistryEntry):
    """Registry entry for servers"""
    host: str = "localhost"
    port: int
    protocol: str = "http"
    api_version: str = "1.0"
    endpoints: List[str] = Field(default_factory=list)
    current_load: float = 0.0
    max_load: float = 100.0
    response_time: float = 0.0  # avg response time in ms
    uptime: float = 0.0  # uptime percentage

# Unified Registry Service
class UnifiedRegistry:
    def __init__(self, db_url: str, redis_url: str = "redis://localhost:6379"):
        self.db_url = db_url
        self.redis_url = redis_url
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.websocket_connections: Set[WebSocket] = set()
        self.cache: Dict[str, RegistryEntry] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.app = FastAPI(lifespan=self.lifespan)
        self._setup_routes()
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Lifespan manager for FastAPI"""
        await self.initialize()
        yield
        await self.shutdown()
        
    async def initialize(self):
        """Initialize database and Redis connections"""
        try:
            # Initialize PostgreSQL
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=10,
                max_size=50,
                command_timeout=60
            )
            
            # Initialize Redis
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            
            # Load cache from database
            await self._load_cache()
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_monitor())
            asyncio.create_task(self._event_processor())
            
            logger.info("Unified Registry initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize registry: {e}")
            raise
            
    async def shutdown(self):
        """Clean shutdown of registry"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "registry_size": len(self.cache),
                "db_connected": self.db_pool is not None,
                "redis_connected": self.redis is not None,
                "websocket_clients": len(self.websocket_connections)
            }
            
        @self.app.post("/register")
        async def register_entry(entry: RegistryEntry):
            """Register a new entry in the registry"""
            result = await self.register(entry)
            return {"status": "registered", "id": result.id}
            
        @self.app.get("/discover/{entry_type}")
        async def discover_entries(
            entry_type: RegistryType,
            status: Optional[ServiceStatus] = None,
            capability: Optional[str] = None
        ):
            """Discover entries by type and filters"""
            entries = await self.discover(entry_type, status, capability)
            return {"entries": [e.dict() for e in entries]}
            
        @self.app.get("/entry/{entry_id}")
        async def get_entry(entry_id: str):
            """Get specific entry by ID"""
            entry = await self.get_entry(entry_id)
            if not entry:
                raise HTTPException(status_code=404, detail="Entry not found")
            return entry.dict()
            
        @self.app.put("/entry/{entry_id}/status")
        async def update_status(entry_id: str, status: ServiceStatus):
            """Update entry status"""
            await self.update_status(entry_id, status)
            return {"status": "updated"}
            
        @self.app.post("/entry/{entry_id}/heartbeat")
        async def heartbeat(entry_id: str):
            """Update entry heartbeat"""
            await self.update_heartbeat(entry_id)
            return {"status": "heartbeat_received"}
            
        @self.app.delete("/entry/{entry_id}")
        async def unregister(entry_id: str):
            """Unregister entry from registry"""
            await self.unregister(entry_id)
            return {"status": "unregistered"}
            
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_connections.add(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle WebSocket messages if needed
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
                
        @self.app.get("/stats")
        async def get_statistics():
            """Get registry statistics"""
            stats = await self.get_statistics()
            return stats
            
    async def register(self, entry: RegistryEntry) -> RegistryEntry:
        """Register a new entry in the registry"""
        try:
            # Update cache
            self.cache[entry.id] = entry
            
            # Store in database
            async with self.db_pool.acquire() as conn:
                await self._store_entry(conn, entry)
                
            # Publish event
            await self._publish_event("register", entry)
            
            # Notify WebSocket clients
            await self._notify_websockets({
                "event": "register",
                "entry": entry.dict()
            })
            
            logger.info(f"Registered {entry.type} entry: {entry.name} ({entry.id})")
            return entry
            
        except Exception as e:
            logger.error(f"Failed to register entry: {e}")
            raise
            
    async def unregister(self, entry_id: str):
        """Unregister an entry from the registry"""
        try:
            if entry_id in self.cache:
                entry = self.cache[entry_id]
                del self.cache[entry_id]
                
                # Remove from database
                async with self.db_pool.acquire() as conn:
                    await self._delete_entry(conn, entry_id)
                    
                # Publish event
                await self._publish_event("unregister", entry)
                
                # Notify WebSocket clients
                await self._notify_websockets({
                    "event": "unregister",
                    "entry_id": entry_id
                })
                
                logger.info(f"Unregistered entry: {entry_id}")
                
        except Exception as e:
            logger.error(f"Failed to unregister entry: {e}")
            raise
            
    async def discover(
        self,
        entry_type: Optional[RegistryType] = None,
        status: Optional[ServiceStatus] = None,
        capability: Optional[str] = None
    ) -> List[RegistryEntry]:
        """Discover entries based on filters"""
        results = []
        
        for entry in self.cache.values():
            # Filter by type
            if entry_type and entry.type != entry_type:
                continue
                
            # Filter by status
            if status and entry.status != status:
                continue
                
            # Filter by capability
            if capability and capability not in entry.capabilities:
                continue
                
            results.append(entry)
            
        return results
        
    async def get_entry(self, entry_id: str) -> Optional[RegistryEntry]:
        """Get specific entry by ID"""
        return self.cache.get(entry_id)
        
    async def update_status(self, entry_id: str, status: ServiceStatus):
        """Update entry status"""
        if entry_id in self.cache:
            entry = self.cache[entry_id]
            old_status = entry.status
            entry.status = status
            entry.updated_at = datetime.utcnow()
            
            # Update database
            async with self.db_pool.acquire() as conn:
                await self._update_entry_status(conn, entry_id, status)
                
            # Publish event
            await self._publish_event("status_change", {
                "entry": entry,
                "old_status": old_status,
                "new_status": status
            })
            
            # Notify WebSocket clients
            await self._notify_websockets({
                "event": "status_change",
                "entry_id": entry_id,
                "old_status": old_status,
                "new_status": status
            })
            
    async def update_heartbeat(self, entry_id: str):
        """Update entry heartbeat timestamp"""
        if entry_id in self.cache:
            entry = self.cache[entry_id]
            entry.last_heartbeat = datetime.utcnow()
            entry.health_score = 100.0  # Reset health on heartbeat
            
            # Update database
            async with self.db_pool.acquire() as conn:
                await self._update_entry_heartbeat(conn, entry_id)
                
    async def assign_agent_to_department(self, agent_id: str, department_id: str):
        """Assign an agent to a department"""
        agent = await self.get_entry(agent_id)
        department = await self.get_entry(department_id)
        
        if not agent or agent.type != RegistryType.AGENT:
            raise ValueError(f"Agent {agent_id} not found")
            
        if not department or department.type != RegistryType.DEPARTMENT:
            raise ValueError(f"Department {department_id} not found")
            
        # Update agent
        if isinstance(agent, AgentEntry):
            agent.department_id = department_id
            agent.division_id = department.division_id
            
        # Update department
        if isinstance(department, DepartmentEntry):
            if agent_id not in department.agent_ids:
                department.agent_ids.append(agent_id)
                
        # Update database
        async with self.db_pool.acquire() as conn:
            await self._assign_agent_to_department(conn, agent_id, department_id)
            
        # Publish event
        await self._publish_event("agent_assigned", {
            "agent_id": agent_id,
            "department_id": department_id
        })
        
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        stats = {
            "total_entries": len(self.cache),
            "by_type": {},
            "by_status": {},
            "health_summary": {
                "healthy": 0,
                "warning": 0,
                "critical": 0
            },
            "departments": {
                "total": 0,
                "with_leaders": 0,
                "average_agents": 0
            },
            "agents": {
                "total": 0,
                "online": 0,
                "average_load": 0
            }
        }
        
        # Calculate statistics
        for entry in self.cache.values():
            # By type
            stats["by_type"][entry.type] = stats["by_type"].get(entry.type, 0) + 1
            
            # By status
            stats["by_status"][entry.status] = stats["by_status"].get(entry.status, 0) + 1
            
            # Health summary
            if entry.health_score >= 80:
                stats["health_summary"]["healthy"] += 1
            elif entry.health_score >= 50:
                stats["health_summary"]["warning"] += 1
            else:
                stats["health_summary"]["critical"] += 1
                
            # Type-specific stats
            if entry.type == RegistryType.AGENT:
                stats["agents"]["total"] += 1
                if entry.status == ServiceStatus.ONLINE:
                    stats["agents"]["online"] += 1
                    
            elif entry.type == RegistryType.DEPARTMENT:
                stats["departments"]["total"] += 1
                if isinstance(entry, DepartmentEntry) and entry.leader_id:
                    stats["departments"]["with_leaders"] += 1
                    
        # Calculate averages
        if stats["departments"]["total"] > 0:
            total_agents_in_depts = sum(
                len(e.agent_ids) for e in self.cache.values()
                if isinstance(e, DepartmentEntry)
            )
            stats["departments"]["average_agents"] = (
                total_agents_in_depts / stats["departments"]["total"]
            )
            
        if stats["agents"]["online"] > 0:
            total_load = sum(
                e.current_load for e in self.cache.values()
                if isinstance(e, AgentEntry) and e.status == ServiceStatus.ONLINE
            )
            stats["agents"]["average_load"] = total_load / stats["agents"]["online"]
            
        return stats
        
    # Database operations
    async def _store_entry(self, conn: asyncpg.Connection, entry: RegistryEntry):
        """Store entry in appropriate database table"""
        if entry.type in [RegistryType.AGENT, RegistryType.LEADER]:
            await conn.execute("""
                INSERT INTO agent_registry (
                    id, name, type, status, metadata, capabilities,
                    health_score, department_id, division_id, llm_model,
                    max_tokens, temperature, current_load, max_load
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    capabilities = EXCLUDED.capabilities,
                    health_score = EXCLUDED.health_score,
                    updated_at = CURRENT_TIMESTAMP
            """, entry.id, entry.name, entry.type, entry.status,
                json.dumps(entry.metadata), entry.capabilities,
                entry.health_score, 
                getattr(entry, 'department_id', None),
                getattr(entry, 'division_id', None),
                getattr(entry, 'llm_model', None),
                getattr(entry, 'max_tokens', 4096),
                getattr(entry, 'temperature', 0.7),
                getattr(entry, 'current_load', 0.0),
                getattr(entry, 'max_load', 100.0))
                
        elif entry.type == RegistryType.DEPARTMENT:
            await conn.execute("""
                INSERT INTO departments (
                    id, name, division_id, description, leader_id
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    division_id = EXCLUDED.division_id,
                    description = EXCLUDED.description,
                    leader_id = EXCLUDED.leader_id
            """, entry.id, entry.name, 
                getattr(entry, 'division_id', None),
                getattr(entry, 'description', None),
                getattr(entry, 'leader_id', None))
                
        elif entry.type == RegistryType.DIVISION:
            await conn.execute("""
                INSERT INTO divisions (
                    id, name, description
                ) VALUES ($1, $2, $3)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description
            """, entry.id, entry.name, 
                entry.metadata.get('description', ''))
                
        elif entry.type in [RegistryType.SERVER_CORE, RegistryType.SERVER_MCP, 
                           RegistryType.SERVER_BUSINESS]:
            await conn.execute("""
                INSERT INTO server_registry (
                    id, name, type, status, host, port, protocol,
                    metadata, capabilities, health_score, endpoints
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    health_score = EXCLUDED.health_score,
                    updated_at = CURRENT_TIMESTAMP
            """, entry.id, entry.name, entry.type, entry.status,
                getattr(entry, 'host', 'localhost'),
                getattr(entry, 'port', 0),
                getattr(entry, 'protocol', 'http'),
                json.dumps(entry.metadata), entry.capabilities,
                entry.health_score,
                getattr(entry, 'endpoints', []))
                
    async def _update_entry_status(self, conn: asyncpg.Connection, 
                                  entry_id: str, status: ServiceStatus):
        """Update entry status in database"""
        await conn.execute("""
            UPDATE agent_registry SET status = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, status, entry_id)
        
        await conn.execute("""
            UPDATE server_registry SET status = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, status, entry_id)
        
    async def _update_entry_heartbeat(self, conn: asyncpg.Connection, entry_id: str):
        """Update entry heartbeat in database"""
        await conn.execute("""
            UPDATE agent_registry 
            SET last_heartbeat = CURRENT_TIMESTAMP, health_score = 100
            WHERE id = $1
        """, entry_id)
        
        await conn.execute("""
            UPDATE server_registry 
            SET last_heartbeat = CURRENT_TIMESTAMP, health_score = 100
            WHERE id = $1
        """, entry_id)
        
    async def _delete_entry(self, conn: asyncpg.Connection, entry_id: str):
        """Delete entry from database"""
        await conn.execute("DELETE FROM agent_registry WHERE id = $1", entry_id)
        await conn.execute("DELETE FROM server_registry WHERE id = $1", entry_id)
        await conn.execute("DELETE FROM departments WHERE id = $1", entry_id)
        await conn.execute("DELETE FROM divisions WHERE id = $1", entry_id)
        
    async def _assign_agent_to_department(self, conn: asyncpg.Connection,
                                         agent_id: str, department_id: str):
        """Assign agent to department in database"""
        await conn.execute("""
            INSERT INTO agent_department_assignments (agent_id, department_id)
            VALUES ($1, $2)
            ON CONFLICT (agent_id) DO UPDATE SET
                department_id = EXCLUDED.department_id,
                assigned_at = CURRENT_TIMESTAMP
        """, agent_id, department_id)
        
    async def _load_cache(self):
        """Load all entries from database into cache"""
        async with self.db_pool.acquire() as conn:
            # Load agents
            agents = await conn.fetch("SELECT * FROM agent_registry")
            for row in agents:
                entry = AgentEntry(
                    id=row['id'],
                    name=row['name'],
                    type=row['type'],
                    status=row['status'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    capabilities=row['capabilities'] or [],
                    health_score=row['health_score'],
                    department_id=row.get('department_id'),
                    division_id=row.get('division_id'),
                    llm_model=row.get('llm_model'),
                    max_tokens=row.get('max_tokens', 4096),
                    temperature=row.get('temperature', 0.7),
                    current_load=row.get('current_load', 0.0),
                    max_load=row.get('max_load', 100.0)
                )
                self.cache[entry.id] = entry
                
            # Load servers
            servers = await conn.fetch("SELECT * FROM server_registry")
            for row in servers:
                entry = ServerEntry(
                    id=row['id'],
                    name=row['name'],
                    type=row['type'],
                    status=row['status'],
                    host=row['host'],
                    port=row['port'],
                    protocol=row['protocol'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    capabilities=row['capabilities'] or [],
                    health_score=row['health_score'],
                    endpoints=row.get('endpoints', [])
                )
                self.cache[entry.id] = entry
                
            # Load departments
            departments = await conn.fetch("SELECT * FROM departments")
            for row in departments:
                # Get agent assignments
                assignments = await conn.fetch("""
                    SELECT agent_id FROM agent_department_assignments
                    WHERE department_id = $1
                """, row['id'])
                agent_ids = [a['agent_id'] for a in assignments]
                
                entry = DepartmentEntry(
                    id=row['id'],
                    name=row['name'],
                    type=RegistryType.DEPARTMENT,
                    division_id=row['division_id'],
                    leader_id=row.get('leader_id'),
                    agent_ids=agent_ids,
                    description=row.get('description')
                )
                self.cache[entry.id] = entry
                
            # Load divisions
            divisions = await conn.fetch("SELECT * FROM divisions")
            for row in divisions:
                # Get departments in division
                depts = await conn.fetch("""
                    SELECT id FROM departments WHERE division_id = $1
                """, row['id'])
                dept_ids = [d['id'] for d in depts]
                
                entry = DivisionEntry(
                    id=row['id'],
                    name=row['name'],
                    type=RegistryType.DIVISION,
                    department_ids=dept_ids,
                    metadata={'description': row.get('description', '')}
                )
                self.cache[entry.id] = entry
                
    # Event handling
    async def _publish_event(self, event_type: str, data: Any):
        """Publish event to Redis Streams"""
        if self.redis:
            event = {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data.dict() if hasattr(data, 'dict') else data
            }
            await self.redis.xadd(
                "registry:events",
                {"event": json.dumps(event)}
            )
            
    async def _notify_websockets(self, message: Dict[str, Any]):
        """Notify all WebSocket clients"""
        if self.websocket_connections:
            message_json = json.dumps(message)
            disconnected = set()
            
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(message_json)
                except:
                    disconnected.add(websocket)
                    
            # Remove disconnected clients
            self.websocket_connections -= disconnected
            
    async def _heartbeat_monitor(self):
        """Monitor heartbeats and update health scores"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                now = datetime.utcnow()
                for entry in self.cache.values():
                    if entry.last_heartbeat:
                        # Calculate time since last heartbeat
                        time_diff = (now - entry.last_heartbeat).total_seconds()
                        
                        # Degrade health score based on time
                        if time_diff > 300:  # 5 minutes
                            entry.health_score = 0
                            if entry.status == ServiceStatus.ONLINE:
                                await self.update_status(entry.id, ServiceStatus.ERROR)
                        elif time_diff > 120:  # 2 minutes
                            entry.health_score = max(0, entry.health_score - 20)
                        elif time_diff > 60:  # 1 minute
                            entry.health_score = max(0, entry.health_score - 10)
                            
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                
    async def _event_processor(self):
        """Process events from Redis Streams"""
        if not self.redis:
            return
            
        while True:
            try:
                # Read events from stream
                events = await self.redis.xread(
                    {"registry:events": "$"},
                    block=1000
                )
                
                for stream, messages in events:
                    for message_id, data in messages:
                        event = json.loads(data[b"event"])
                        
                        # Call registered event handlers
                        event_type = event["type"]
                        if event_type in self.event_handlers:
                            for handler in self.event_handlers[event_type]:
                                try:
                                    await handler(event["data"])
                                except Exception as e:
                                    logger.error(f"Event handler error: {e}")
                                    
            except Exception as e:
                logger.error(f"Event processor error: {e}")
                await asyncio.sleep(5)
                
    def on_event(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def run(self, host: str = "0.0.0.0", port: int = 8100):
        """Run the registry service"""
        uvicorn.run(self.app, host=host, port=port)


# Convenience functions for standalone usage
async def create_registry(db_url: str = None, redis_url: str = None) -> UnifiedRegistry:
    """Create and initialize a registry instance"""
    if not db_url:
        db_url = "postgresql://boarderframe:boarderframe@localhost:5434/boarderframeos"
    if not redis_url:
        redis_url = "redis://localhost:6379"
        
    registry = UnifiedRegistry(db_url, redis_url)
    await registry.initialize()
    return registry


if __name__ == "__main__":
    # Run as standalone service
    import os
    
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://boarderframe:boarderframe@localhost:5434/boarderframeos"
    )
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    registry = UnifiedRegistry(db_url, redis_url)
    registry.run(port=8100)