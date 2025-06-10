"""
BoarderframeOS Enhanced Registry System
======================================

A comprehensive, production-ready registry system that unifies all BoarderframeOS components
with real-time streaming, PostgreSQL persistence, and Redis pub/sub capabilities.

Key Features:
- Unified registry for Agents, Leaders, Departments, Divisions, Databases, and Servers
- Real-time event streaming with Redis Streams and WebSockets
- PostgreSQL backend with connection pooling and query optimization
- Automatic health monitoring and heartbeat tracking
- Service discovery with capability-based filtering
- Department hierarchy and organizational structure management
- HQ data synchronization
- Performance metrics and analytics
- RESTful API and WebSocket interfaces
- Comprehensive audit logging

Architecture:
- PostgreSQL: Primary persistence layer with JSONB for flexible metadata
- Redis: Real-time messaging, caching, and event streaming
- WebSockets: Live updates to connected clients
- FastAPI: High-performance REST API
- AsyncIO: Concurrent operations and background tasks
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
import asyncpg
import aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
from contextlib import asynccontextmanager
import hashlib
import time

logger = logging.getLogger(__name__)

# ==================== Enums and Constants ====================

class RegistryType(str, Enum):
    """All registry entry types in BoarderframeOS"""
    AGENT = "agent"
    LEADER = "leader"
    DEPARTMENT = "department"
    DIVISION = "division"
    DATABASE = "database"
    SERVER_CORE = "server_core"
    SERVER_MCP = "server_mcp"
    SERVER_BUSINESS = "server_business"

class ServiceStatus(str, Enum):
    """Service operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"

class HealthStatus(str, Enum):
    """Health status indicators"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class EventType(str, Enum):
    """Registry event types for streaming"""
    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    STATUS_CHANGED = "status_changed"
    HEARTBEAT = "heartbeat"
    HEALTH_CHANGED = "health_changed"
    CAPABILITY_ADDED = "capability_added"
    CAPABILITY_REMOVED = "capability_removed"
    ASSIGNMENT_CHANGED = "assignment_changed"
    METRIC_UPDATED = "metric_updated"
    ERROR = "error"

class LeadershipTier(str, Enum):
    """Leadership hierarchy tiers"""
    EXECUTIVE = "executive"
    DIVISION = "division"
    DEPARTMENT = "department"
    TEAM = "team"

class ServerType(str, Enum):
    """Server categories"""
    CORE_SYSTEM = "core_system"
    MCP_SERVER = "mcp_server"
    BUSINESS_SERVICE = "business_service"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"

# ==================== Base Models ====================

@dataclass
class RegistryMetrics:
    """Performance and operational metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    uptime_seconds: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

class BaseRegistryEntry(BaseModel):
    """Base model for all registry entries"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: RegistryType
    status: ServiceStatus = ServiceStatus.OFFLINE
    health_status: HealthStatus = HealthStatus.UNKNOWN
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    last_heartbeat: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AgentRegistryEntry(BaseRegistryEntry):
    """Registry entry for AI agents"""
    type: RegistryType = RegistryType.AGENT
    department_id: Optional[str] = None
    division_id: Optional[str] = None
    leader_id: Optional[str] = None
    llm_model: str = "gpt-4"
    llm_provider: str = "openai"
    max_tokens: int = 4096
    temperature: float = 0.7
    current_load: float = Field(default=0.0, ge=0.0, le=100.0)
    max_concurrent_tasks: int = 5
    current_tasks: int = 0
    total_interactions: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    success_rate: float = Field(default=100.0, ge=0.0, le=100.0)
    average_response_time: float = 0.0
    specializations: List[str] = Field(default_factory=list)
    supported_languages: List[str] = Field(default_factory=lambda: ["en"])
    
    @validator('current_tasks')
    def validate_current_tasks(cls, v, values):
        if 'max_concurrent_tasks' in values and v > values['max_concurrent_tasks']:
            raise ValueError('current_tasks cannot exceed max_concurrent_tasks')
        return v

class LeaderRegistryEntry(AgentRegistryEntry):
    """Registry entry for department/division leaders"""
    type: RegistryType = RegistryType.LEADER
    leadership_tier: LeadershipTier = LeadershipTier.DEPARTMENT
    subordinates: List[str] = Field(default_factory=list)
    departments_managed: List[str] = Field(default_factory=list)
    divisions_managed: List[str] = Field(default_factory=list)
    leadership_style: Optional[str] = None
    biblical_archetype: Optional[str] = None
    authority_level: int = Field(default=5, ge=1, le=10)
    delegation_capacity: int = 10
    strategic_initiatives: List[str] = Field(default_factory=list)

class DepartmentRegistryEntry(BaseRegistryEntry):
    """Registry entry for departments"""
    type: RegistryType = RegistryType.DEPARTMENT
    division_id: str
    leader_ids: List[str] = Field(default_factory=list)
    agent_ids: List[str] = Field(default_factory=list)
    operational_status: str = "planning"
    budget_allocated: float = 0.0
    budget_consumed: float = 0.0
    revenue_generated: float = 0.0
    agent_capacity: int = 10
    performance_score: float = Field(default=0.0, ge=0.0, le=100.0)
    efficiency_score: float = Field(default=0.0, ge=0.0, le=100.0)
    collaboration_score: float = Field(default=0.0, ge=0.0, le=100.0)
    objectives: List[Dict[str, Any]] = Field(default_factory=list)
    active_projects: int = 0
    completed_projects: int = 0

class DivisionRegistryEntry(BaseRegistryEntry):
    """Registry entry for divisions"""
    type: RegistryType = RegistryType.DIVISION
    department_ids: List[str] = Field(default_factory=list)
    executive_leader_id: Optional[str] = None
    division_leaders: List[str] = Field(default_factory=list)
    total_agents: int = 0
    total_budget: float = 0.0
    total_revenue: float = 0.0
    strategic_focus: Optional[str] = None
    market_position: Optional[str] = None
    growth_rate: float = 0.0
    division_purpose: Optional[str] = None

class DatabaseRegistryEntry(BaseRegistryEntry):
    """Registry entry for databases"""
    type: RegistryType = RegistryType.DATABASE
    db_type: str  # postgresql, sqlite, redis, mongodb
    host: str = "localhost"
    port: int
    database_name: Optional[str] = None
    connection_string: Optional[str] = None
    max_connections: int = 100
    current_connections: int = 0
    connection_pool_size: int = 10
    query_performance: float = 0.0  # avg query time in ms
    cache_hit_rate: float = 0.0
    storage_used_gb: float = 0.0
    storage_limit_gb: Optional[float] = None
    replication_status: Optional[str] = None
    backup_status: Optional[str] = None
    last_backup: Optional[datetime] = None

class ServerRegistryEntry(BaseRegistryEntry):
    """Registry entry for servers"""
    server_type: ServerType
    host: str = "localhost"
    port: int
    protocol: str = "http"
    base_url: Optional[str] = None
    api_version: str = "1.0"
    endpoints: List[Dict[str, str]] = Field(default_factory=list)
    authentication_required: bool = False
    authentication_type: Optional[str] = None
    rate_limit: Optional[int] = None
    current_load: float = Field(default=0.0, ge=0.0, le=100.0)
    max_load: float = 100.0
    response_time_ms: float = 0.0
    uptime_percentage: float = Field(default=100.0, ge=0.0, le=100.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    requests_per_minute: int = 0
    total_requests: int = 0
    ssl_enabled: bool = False
    cors_enabled: bool = True

# ==================== Event Models ====================

class RegistryEvent(BaseModel):
    """Base event model for registry changes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    entity_id: str
    entity_type: RegistryType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "registry"
    data: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== Registry Service ====================

class EnhancedRegistrySystem:
    """
    Enhanced registry system with comprehensive features for BoarderframeOS
    """
    
    def __init__(
        self,
        db_url: str,
        redis_url: str = "redis://localhost:6379",
        enable_caching: bool = True,
        cache_ttl: int = 300,
        enable_websockets: bool = True,
        enable_audit_log: bool = True
    ):
        self.db_url = db_url
        self.redis_url = redis_url
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.enable_websockets = enable_websockets
        self.enable_audit_log = enable_audit_log
        
        # Connections
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        
        # In-memory cache
        self.cache: Dict[str, BaseRegistryEntry] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
        # WebSocket connections
        self.websocket_connections: Set[WebSocket] = set()
        self.websocket_subscriptions: Dict[WebSocket, Set[str]] = {}
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Metrics
        self.start_time = datetime.utcnow()
        self.metrics = RegistryMetrics()
        
        # FastAPI app
        self.app = FastAPI(
            title="BoarderframeOS Enhanced Registry",
            version="2.0.0",
            lifespan=self.lifespan
        )
        self._setup_middleware()
        self._setup_routes()
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Lifespan manager for FastAPI"""
        await self.initialize()
        yield
        await self.shutdown()
        
    async def initialize(self):
        """Initialize all connections and background tasks"""
        try:
            logger.info("Initializing Enhanced Registry System...")
            
            # Initialize PostgreSQL with connection pooling
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=15,
                max_size=50,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60
            )
            
            # Initialize Redis
            self.redis = await aioredis.create_redis_pool(
                self.redis_url,
                minsize=5,
                maxsize=20
            )
            
            # Load initial data from database
            await self._load_from_database()
            
            # Start background tasks
            self._start_background_tasks()
            
            # Initialize audit log
            if self.enable_audit_log:
                await self._init_audit_log()
            
            logger.info("Enhanced Registry System initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize registry: {e}")
            raise
            
    async def shutdown(self):
        """Clean shutdown of all connections and tasks"""
        logger.info("Shutting down Enhanced Registry System...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Close WebSocket connections
        for ws in self.websocket_connections:
            await ws.close()
            
        # Close database pool
        if self.db_pool:
            await self.db_pool.close()
            
        # Close Redis connection
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            
        logger.info("Enhanced Registry System shut down successfully")
        
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Health and status endpoints
        @self.app.get("/health")
        async def health_check():
            return await self.get_health_status()
            
        @self.app.get("/metrics")
        async def get_metrics():
            return await self.get_metrics()
            
        # Registry operations
        @self.app.post("/register/{entity_type}")
        async def register_entity(
            entity_type: RegistryType,
            entity: BaseRegistryEntry,
            background_tasks: BackgroundTasks
        ):
            result = await self.register(entity)
            return {"status": "success", "entity": result.dict()}
            
        @self.app.get("/discover/{entity_type}")
        async def discover_entities(
            entity_type: RegistryType,
            status: Optional[ServiceStatus] = None,
            capability: Optional[str] = None,
            tag: Optional[str] = None,
            department_id: Optional[str] = None,
            division_id: Optional[str] = None,
            limit: int = Query(default=100, le=1000),
            offset: int = Query(default=0, ge=0)
        ):
            filters = {
                "status": status,
                "capability": capability,
                "tag": tag,
                "department_id": department_id,
                "division_id": division_id
            }
            entities = await self.discover(entity_type, filters, limit, offset)
            return {
                "entities": [e.dict() for e in entities],
                "total": len(entities),
                "limit": limit,
                "offset": offset
            }
            
        @self.app.get("/entity/{entity_id}")
        async def get_entity(entity_id: str):
            entity = await self.get_entity(entity_id)
            if not entity:
                raise HTTPException(status_code=404, detail="Entity not found")
            return entity.dict()
            
        @self.app.put("/entity/{entity_id}")
        async def update_entity(
            entity_id: str,
            updates: Dict[str, Any],
            background_tasks: BackgroundTasks
        ):
            entity = await self.update_entity(entity_id, updates)
            if not entity:
                raise HTTPException(status_code=404, detail="Entity not found")
            return {"status": "success", "entity": entity.dict()}
            
        @self.app.delete("/entity/{entity_id}")
        async def unregister_entity(entity_id: str, background_tasks: BackgroundTasks):
            await self.unregister(entity_id)
            return {"status": "success", "message": f"Entity {entity_id} unregistered"}
            
        @self.app.post("/entity/{entity_id}/heartbeat")
        async def heartbeat(entity_id: str):
            success = await self.heartbeat(entity_id)
            if not success:
                raise HTTPException(status_code=404, detail="Entity not found")
            return {"status": "success", "timestamp": datetime.utcnow()}
            
        # Specialized endpoints
        @self.app.post("/assign/agent/{agent_id}/department/{department_id}")
        async def assign_agent_to_department(
            agent_id: str,
            department_id: str,
            background_tasks: BackgroundTasks
        ):
            await self.assign_agent_to_department(agent_id, department_id)
            return {"status": "success", "message": f"Agent {agent_id} assigned to department {department_id}"}
            
        @self.app.get("/hierarchy/divisions")
        async def get_division_hierarchy():
            return await self.get_organizational_hierarchy()
            
        @self.app.get("/statistics")
        async def get_statistics():
            return await self.get_statistics()
            
        # WebSocket endpoint
        if self.enable_websockets:
            @self.app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                await self._handle_websocket(websocket)
                
    # ==================== Core Registry Operations ====================
    
    async def register(self, entity: BaseRegistryEntry) -> BaseRegistryEntry:
        """Register a new entity in the registry"""
        try:
            self.metrics.total_requests += 1
            
            # Validate entity
            if entity.id in self.cache:
                raise ValueError(f"Entity {entity.id} already registered")
                
            # Set registration timestamp
            entity.registered_at = datetime.utcnow()
            entity.updated_at = datetime.utcnow()
            
            # Store in cache
            self.cache[entity.id] = entity
            self.cache_timestamps[entity.id] = time.time()
            
            # Store in database
            async with self.db_pool.acquire() as conn:
                await self._store_entity(conn, entity)
                
            # Publish event
            event = RegistryEvent(
                event_type=EventType.REGISTERED,
                entity_id=entity.id,
                entity_type=entity.type,
                data=entity.dict()
            )
            await self._publish_event(event)
            
            # Audit log
            if self.enable_audit_log:
                await self._audit_log("register", entity.id, entity.dict())
                
            self.metrics.successful_requests += 1
            logger.info(f"Registered {entity.type} entity: {entity.name} ({entity.id})")
            return entity
            
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"Failed to register entity: {e}")
            raise
            
    async def unregister(self, entity_id: str):
        """Unregister an entity from the registry"""
        try:
            self.metrics.total_requests += 1
            
            if entity_id not in self.cache:
                raise ValueError(f"Entity {entity_id} not found")
                
            entity = self.cache[entity_id]
            
            # Remove from cache
            del self.cache[entity_id]
            if entity_id in self.cache_timestamps:
                del self.cache_timestamps[entity_id]
                
            # Remove from database
            async with self.db_pool.acquire() as conn:
                await self._delete_entity(conn, entity_id, entity.type)
                
            # Publish event
            event = RegistryEvent(
                event_type=EventType.UNREGISTERED,
                entity_id=entity_id,
                entity_type=entity.type,
                data={"name": entity.name}
            )
            await self._publish_event(event)
            
            # Audit log
            if self.enable_audit_log:
                await self._audit_log("unregister", entity_id, {"type": entity.type})
                
            self.metrics.successful_requests += 1
            logger.info(f"Unregistered entity: {entity_id}")
            
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"Failed to unregister entity: {e}")
            raise
            
    async def discover(
        self,
        entity_type: Optional[RegistryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseRegistryEntry]:
        """Discover entities based on filters"""
        try:
            results = []
            filters = filters or {}
            
            # Check cache first
            cache_key = self._generate_cache_key("discover", entity_type, filters)
            cached_result = await self._get_cached(cache_key)
            if cached_result:
                return cached_result[offset:offset + limit]
                
            # Filter entities
            for entity in self.cache.values():
                # Type filter
                if entity_type and entity.type != entity_type:
                    continue
                    
                # Status filter
                if filters.get("status") and entity.status != filters["status"]:
                    continue
                    
                # Capability filter
                if filters.get("capability") and filters["capability"] not in entity.capabilities:
                    continue
                    
                # Tag filter
                if filters.get("tag") and filters["tag"] not in entity.tags:
                    continue
                    
                # Department filter (for agents/leaders)
                if filters.get("department_id"):
                    if hasattr(entity, "department_id") and entity.department_id != filters["department_id"]:
                        continue
                        
                # Division filter
                if filters.get("division_id"):
                    if hasattr(entity, "division_id") and entity.division_id != filters["division_id"]:
                        continue
                        
                results.append(entity)
                
            # Sort by health score and status
            results.sort(key=lambda x: (x.health_score, x.status == ServiceStatus.ONLINE), reverse=True)
            
            # Cache result
            await self._set_cached(cache_key, results)
            
            return results[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to discover entities: {e}")
            raise
            
    async def get_entity(self, entity_id: str) -> Optional[BaseRegistryEntry]:
        """Get specific entity by ID"""
        return self.cache.get(entity_id)
        
    async def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> Optional[BaseRegistryEntry]:
        """Update entity properties"""
        try:
            if entity_id not in self.cache:
                return None
                
            entity = self.cache[entity_id]
            old_data = entity.dict()
            
            # Update allowed fields
            allowed_fields = {
                "status", "health_status", "health_score", "metadata",
                "capabilities", "tags", "metrics", "current_load",
                "current_tasks", "current_connections"
            }
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(entity, field):
                    setattr(entity, field, value)
                    
            entity.updated_at = datetime.utcnow()
            
            # Update database
            async with self.db_pool.acquire() as conn:
                await self._update_entity(conn, entity)
                
            # Publish event
            event = RegistryEvent(
                event_type=EventType.STATUS_CHANGED,
                entity_id=entity_id,
                entity_type=entity.type,
                data={
                    "old": old_data,
                    "new": entity.dict(),
                    "changes": updates
                }
            )
            await self._publish_event(event)
            
            # Invalidate cache
            await self._invalidate_cache(f"entity:{entity_id}")
            
            return entity
            
        except Exception as e:
            logger.error(f"Failed to update entity: {e}")
            raise
            
    async def heartbeat(self, entity_id: str) -> bool:
        """Update entity heartbeat"""
        try:
            if entity_id not in self.cache:
                return False
                
            entity = self.cache[entity_id]
            entity.last_heartbeat = datetime.utcnow()
            
            # Update health score based on heartbeat
            entity.health_score = min(100.0, entity.health_score + 10.0)
            if entity.status == ServiceStatus.OFFLINE:
                entity.status = ServiceStatus.ONLINE
                
            # Update database
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agent_registry 
                    SET last_heartbeat = $1, health_score = $2, status = $3
                    WHERE id = $4
                """, entity.last_heartbeat, entity.health_score, entity.status, entity_id)
                
            # Publish event
            event = RegistryEvent(
                event_type=EventType.HEARTBEAT,
                entity_id=entity_id,
                entity_type=entity.type,
                data={"health_score": entity.health_score}
            )
            await self._publish_event(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process heartbeat: {e}")
            return False
            
    # ==================== Specialized Operations ====================
    
    async def assign_agent_to_department(self, agent_id: str, department_id: str):
        """Assign an agent to a department"""
        try:
            agent = await self.get_entity(agent_id)
            department = await self.get_entity(department_id)
            
            if not agent or agent.type not in [RegistryType.AGENT, RegistryType.LEADER]:
                raise ValueError(f"Agent {agent_id} not found")
                
            if not department or department.type != RegistryType.DEPARTMENT:
                raise ValueError(f"Department {department_id} not found")
                
            # Update agent
            if isinstance(agent, (AgentRegistryEntry, LeaderRegistryEntry)):
                old_dept = agent.department_id
                agent.department_id = department_id
                agent.division_id = department.division_id
                
            # Update department
            if isinstance(department, DepartmentRegistryEntry):
                if agent_id not in department.agent_ids:
                    department.agent_ids.append(agent_id)
                    
            # Update database
            async with self.db_pool.acquire() as conn:
                # Update agent assignment
                await conn.execute("""
                    INSERT INTO agent_department_assignments (agent_id, department_id, assigned_at, assignment_status)
                    VALUES ($1, $2, $3, 'active')
                    ON CONFLICT (agent_id) DO UPDATE SET
                        department_id = EXCLUDED.department_id,
                        assigned_at = EXCLUDED.assigned_at,
                        assignment_status = 'active'
                """, agent_id, department_id, datetime.utcnow())
                
                # Update old department if exists
                if old_dept:
                    old_department = await self.get_entity(old_dept)
                    if old_department and isinstance(old_department, DepartmentRegistryEntry):
                        old_department.agent_ids = [aid for aid in old_department.agent_ids if aid != agent_id]
                        
            # Publish event
            event = RegistryEvent(
                event_type=EventType.ASSIGNMENT_CHANGED,
                entity_id=agent_id,
                entity_type=agent.type,
                data={
                    "agent_id": agent_id,
                    "old_department": old_dept,
                    "new_department": department_id
                }
            )
            await self._publish_event(event)
            
        except Exception as e:
            logger.error(f"Failed to assign agent to department: {e}")
            raise
            
    async def get_organizational_hierarchy(self) -> Dict[str, Any]:
        """Get complete organizational hierarchy"""
        hierarchy = {
            "divisions": [],
            "total_agents": 0,
            "total_departments": 0,
            "total_leaders": 0
        }
        
        # Get all divisions
        divisions = await self.discover(RegistryType.DIVISION)
        
        for division in divisions:
            if isinstance(division, DivisionRegistryEntry):
                div_data = {
                    "id": division.id,
                    "name": division.name,
                    "departments": [],
                    "metrics": {
                        "total_agents": division.total_agents,
                        "total_budget": division.total_budget,
                        "total_revenue": division.total_revenue
                    }
                }
                
                # Get departments in division
                departments = await self.discover(
                    RegistryType.DEPARTMENT,
                    {"division_id": division.id}
                )
                
                for dept in departments:
                    if isinstance(dept, DepartmentRegistryEntry):
                        dept_data = {
                            "id": dept.id,
                            "name": dept.name,
                            "leaders": [],
                            "agent_count": len(dept.agent_ids),
                            "performance_score": dept.performance_score
                        }
                        
                        # Get leaders
                        for leader_id in dept.leader_ids:
                            leader = await self.get_entity(leader_id)
                            if leader:
                                dept_data["leaders"].append({
                                    "id": leader.id,
                                    "name": leader.name,
                                    "tier": getattr(leader, "leadership_tier", "unknown")
                                })
                                hierarchy["total_leaders"] += 1
                                
                        div_data["departments"].append(dept_data)
                        hierarchy["total_departments"] += 1
                        hierarchy["total_agents"] += len(dept.agent_ids)
                        
                hierarchy["divisions"].append(div_data)
                
        return hierarchy
        
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        stats = {
            "total_entries": len(self.cache),
            "by_type": {},
            "by_status": {},
            "by_health": {
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "unknown": 0
            },
            "performance": {
                "average_health_score": 0.0,
                "online_percentage": 0.0,
                "average_response_time": 0.0
            },
            "organizational": {
                "divisions": 0,
                "departments": 0,
                "leaders": 0,
                "agents": 0,
                "servers": 0,
                "databases": 0
            }
        }
        
        total_health_score = 0.0
        online_count = 0
        total_response_time = 0.0
        response_time_count = 0
        
        for entity in self.cache.values():
            # Count by type
            stats["by_type"][entity.type] = stats["by_type"].get(entity.type, 0) + 1
            
            # Count by status
            stats["by_status"][entity.status] = stats["by_status"].get(entity.status, 0) + 1
            
            # Health categorization
            if entity.health_score >= 80:
                stats["by_health"]["healthy"] += 1
            elif entity.health_score >= 50:
                stats["by_health"]["warning"] += 1
            elif entity.health_score > 0:
                stats["by_health"]["critical"] += 1
            else:
                stats["by_health"]["unknown"] += 1
                
            # Accumulate metrics
            total_health_score += entity.health_score
            if entity.status == ServiceStatus.ONLINE:
                online_count += 1
                
            # Response time for servers
            if hasattr(entity, "response_time_ms") and entity.response_time_ms > 0:
                total_response_time += entity.response_time_ms
                response_time_count += 1
                
            # Organizational counts
            if entity.type == RegistryType.DIVISION:
                stats["organizational"]["divisions"] += 1
            elif entity.type == RegistryType.DEPARTMENT:
                stats["organizational"]["departments"] += 1
            elif entity.type == RegistryType.LEADER:
                stats["organizational"]["leaders"] += 1
            elif entity.type == RegistryType.AGENT:
                stats["organizational"]["agents"] += 1
            elif entity.type in [RegistryType.SERVER_CORE, RegistryType.SERVER_MCP, RegistryType.SERVER_BUSINESS]:
                stats["organizational"]["servers"] += 1
            elif entity.type == RegistryType.DATABASE:
                stats["organizational"]["databases"] += 1
                
        # Calculate averages
        if stats["total_entries"] > 0:
            stats["performance"]["average_health_score"] = total_health_score / stats["total_entries"]
            stats["performance"]["online_percentage"] = (online_count / stats["total_entries"]) * 100
            
        if response_time_count > 0:
            stats["performance"]["average_response_time"] = total_response_time / response_time_count
            
        return stats
        
    # ==================== Database Operations ====================
    
    async def _store_entity(self, conn: asyncpg.Connection, entity: BaseRegistryEntry):
        """Store entity in appropriate database table"""
        try:
            if entity.type in [RegistryType.AGENT, RegistryType.LEADER]:
                # Store in agent_registry table
                await conn.execute("""
                    INSERT INTO agent_registry (
                        id, agent_id, name, department_id, agent_type, status,
                        capabilities, supported_tools, health_status, health_check_url,
                        last_heartbeat, metadata, version, tags
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        status = EXCLUDED.status,
                        capabilities = EXCLUDED.capabilities,
                        health_status = EXCLUDED.health_status,
                        last_heartbeat = EXCLUDED.last_heartbeat,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, 
                entity.id, entity.id, entity.name,
                getattr(entity, 'department_id', None),
                entity.type, entity.status,
                json.dumps(entity.capabilities),
                json.dumps(entity.capabilities),  # Using capabilities as supported_tools
                entity.health_status,
                f"http://localhost:8100/entity/{entity.id}/health",
                entity.last_heartbeat,
                json.dumps(entity.metadata),
                entity.version,
                entity.tags
                )
                
            elif entity.type == RegistryType.DEPARTMENT:
                # Ensure department exists in departments table
                dept = entity
                if isinstance(dept, DepartmentRegistryEntry):
                    await conn.execute("""
                        INSERT INTO departments (
                            id, name, division_id, is_active
                        ) VALUES ($1, $2, $3, $4)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            division_id = EXCLUDED.division_id
                    """, dept.id, dept.name, dept.division_id, True)
                    
                    # Store in department_registry
                    await conn.execute("""
                        INSERT INTO department_registry (
                            id, department_id, name, status, capabilities,
                            agent_count, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (department_id) DO UPDATE SET
                            status = EXCLUDED.status,
                            capabilities = EXCLUDED.capabilities,
                            agent_count = EXCLUDED.agent_count,
                            metadata = EXCLUDED.metadata,
                            updated_at = CURRENT_TIMESTAMP
                    """,
                    str(uuid.uuid4()), dept.id, dept.name,
                    dept.operational_status,
                    json.dumps(dept.capabilities),
                    len(dept.agent_ids),
                    json.dumps(dept.metadata)
                    )
                    
            elif entity.type == RegistryType.DIVISION:
                # Store in divisions table
                div = entity
                if isinstance(div, DivisionRegistryEntry):
                    await conn.execute("""
                        INSERT INTO divisions (
                            division_key, division_name, division_description,
                            division_purpose, is_active
                        ) VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (division_key) DO UPDATE SET
                            division_name = EXCLUDED.division_name,
                            division_description = EXCLUDED.division_description,
                            updated_at = CURRENT_TIMESTAMP
                    """,
                    div.id, div.name,
                    div.metadata.get('description', ''),
                    div.division_purpose,
                    True
                    )
                    
            elif entity.type in [RegistryType.SERVER_CORE, RegistryType.SERVER_MCP, RegistryType.SERVER_BUSINESS]:
                # Store in server_registry
                server = entity
                if isinstance(server, ServerRegistryEntry):
                    await conn.execute("""
                        INSERT INTO server_registry (
                            id, name, server_type, status, endpoint_url,
                            health_check_url, capabilities, health_status,
                            last_heartbeat, metadata, version
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (id) DO UPDATE SET
                            status = EXCLUDED.status,
                            health_status = EXCLUDED.health_status,
                            last_heartbeat = EXCLUDED.last_heartbeat,
                            metadata = EXCLUDED.metadata,
                            updated_at = CURRENT_TIMESTAMP
                    """,
                    server.id, server.name, server.server_type,
                    server.status,
                    f"{server.protocol}://{server.host}:{server.port}",
                    f"{server.protocol}://{server.host}:{server.port}/health",
                    json.dumps(server.capabilities),
                    server.health_status,
                    server.last_heartbeat,
                    json.dumps(server.metadata),
                    server.version
                    )
                    
        except Exception as e:
            logger.error(f"Failed to store entity in database: {e}")
            raise
            
    async def _update_entity(self, conn: asyncpg.Connection, entity: BaseRegistryEntry):
        """Update entity in database"""
        try:
            if entity.type in [RegistryType.AGENT, RegistryType.LEADER]:
                await conn.execute("""
                    UPDATE agent_registry SET
                        status = $1, health_status = $2, capabilities = $3,
                        metadata = $4, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $5
                """, entity.status, entity.health_status,
                    json.dumps(entity.capabilities),
                    json.dumps(entity.metadata),
                    entity.id)
                    
            elif entity.type in [RegistryType.SERVER_CORE, RegistryType.SERVER_MCP, RegistryType.SERVER_BUSINESS]:
                await conn.execute("""
                    UPDATE server_registry SET
                        status = $1, health_status = $2, capabilities = $3,
                        metadata = $4, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $5
                """, entity.status, entity.health_status,
                    json.dumps(entity.capabilities),
                    json.dumps(entity.metadata),
                    entity.id)
                    
        except Exception as e:
            logger.error(f"Failed to update entity in database: {e}")
            raise
            
    async def _delete_entity(self, conn: asyncpg.Connection, entity_id: str, entity_type: RegistryType):
        """Delete entity from database"""
        try:
            if entity_type in [RegistryType.AGENT, RegistryType.LEADER]:
                await conn.execute("DELETE FROM agent_registry WHERE id = $1", entity_id)
            elif entity_type == RegistryType.DEPARTMENT:
                await conn.execute("DELETE FROM department_registry WHERE department_id = $1", entity_id)
            elif entity_type == RegistryType.DIVISION:
                await conn.execute("DELETE FROM divisions WHERE division_key = $1", entity_id)
            elif entity_type in [RegistryType.SERVER_CORE, RegistryType.SERVER_MCP, RegistryType.SERVER_BUSINESS]:
                await conn.execute("DELETE FROM server_registry WHERE id = $1", entity_id)
                
        except Exception as e:
            logger.error(f"Failed to delete entity from database: {e}")
            raise
            
    async def _load_from_database(self):
        """Load all entities from database into cache"""
        try:
            async with self.db_pool.acquire() as conn:
                # Load agents and leaders
                agents = await conn.fetch("SELECT * FROM agent_registry")
                for row in agents:
                    if row['agent_type'] == RegistryType.LEADER:
                        entity = LeaderRegistryEntry(
                            id=row['id'],
                            name=row['name'],
                            status=row['status'],
                            health_status=row.get('health_status', HealthStatus.UNKNOWN),
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
                            capabilities=json.loads(row['capabilities']) if row['capabilities'] else [],
                            tags=row.get('tags', []),
                            last_heartbeat=row.get('last_heartbeat'),
                            version=row.get('version', '1.0.0')
                        )
                    else:
                        entity = AgentRegistryEntry(
                            id=row['id'],
                            name=row['name'],
                            status=row['status'],
                            health_status=row.get('health_status', HealthStatus.UNKNOWN),
                            department_id=row.get('department_id'),
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
                            capabilities=json.loads(row['capabilities']) if row['capabilities'] else [],
                            tags=row.get('tags', []),
                            last_heartbeat=row.get('last_heartbeat'),
                            version=row.get('version', '1.0.0')
                        )
                    self.cache[entity.id] = entity
                    
                # Load servers
                servers = await conn.fetch("SELECT * FROM server_registry")
                for row in servers:
                    entity = ServerRegistryEntry(
                        id=row['id'],
                        name=row['name'],
                        type=row['server_type'],
                        server_type=row['server_type'],
                        status=row['status'],
                        health_status=row.get('health_status', HealthStatus.UNKNOWN),
                        host=row.get('endpoint_url', 'localhost').split('://')[1].split(':')[0],
                        port=int(row.get('endpoint_url', ':8000').split(':')[-1].split('/')[0]),
                        protocol=row.get('endpoint_url', 'http://').split('://')[0],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        capabilities=json.loads(row['capabilities']) if row['capabilities'] else [],
                        last_heartbeat=row.get('last_heartbeat'),
                        version=row.get('version', '1.0')
                    )
                    self.cache[entity.id] = entity
                    
                # Load departments
                departments = await conn.fetch("""
                    SELECT d.*, dr.status as reg_status, dr.capabilities, dr.metadata as reg_metadata
                    FROM departments d
                    LEFT JOIN department_registry dr ON d.id = dr.department_id
                    WHERE d.is_active = true
                """)
                for row in departments:
                    # Get agent assignments
                    assignments = await conn.fetch("""
                        SELECT agent_id FROM agent_department_assignments
                        WHERE department_id = $1 AND assignment_status = 'active'
                    """, row['id'])
                    agent_ids = [str(a['agent_id']) for a in assignments]
                    
                    entity = DepartmentRegistryEntry(
                        id=str(row['id']),
                        name=row['name'],
                        division_id=str(row['division_id']) if row['division_id'] else "",
                        agent_ids=agent_ids,
                        operational_status=row.get('reg_status', 'planning'),
                        capabilities=json.loads(row['capabilities']) if row.get('capabilities') else [],
                        metadata=json.loads(row['reg_metadata']) if row.get('reg_metadata') else {}
                    )
                    self.cache[entity.id] = entity
                    
                # Load divisions
                divisions = await conn.fetch("SELECT * FROM divisions WHERE is_active = true")
                for row in divisions:
                    # Get departments in division
                    depts = await conn.fetch("""
                        SELECT id FROM departments WHERE division_id = $1
                    """, row['id'])
                    dept_ids = [str(d['id']) for d in depts]
                    
                    entity = DivisionRegistryEntry(
                        id=row['division_key'],
                        name=row['division_name'],
                        department_ids=dept_ids,
                        division_purpose=row.get('division_purpose'),
                        metadata={
                            'description': row.get('division_description', ''),
                            'priority': row.get('priority', 5)
                        }
                    )
                    self.cache[entity.id] = entity
                    
            logger.info(f"Loaded {len(self.cache)} entities from database")
            
        except Exception as e:
            logger.error(f"Failed to load entities from database: {e}")
            raise
            
    # ==================== Event System ====================
    
    async def _publish_event(self, event: RegistryEvent):
        """Publish event to Redis Streams and WebSockets"""
        try:
            if self.redis:
                # Publish to Redis Stream
                event_data = json.dumps(event.dict())
                await self.redis.xadd(
                    "registry:events",
                    {"event": event_data}
                )
                
                # Publish to Redis Pub/Sub for immediate notification
                await self.redis.publish(
                    f"registry:events:{event.entity_type}",
                    event_data
                )
                
            # Notify WebSocket clients
            if self.websocket_connections:
                await self._notify_websockets(event.dict())
                
            # Call registered event handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            
    async def subscribe_to_events(self, event_type: EventType, handler: Callable):
        """Subscribe to specific event types"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    # ==================== WebSocket Handling ====================
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections"""
        await websocket.accept()
        self.websocket_connections.add(websocket)
        self.websocket_subscriptions[websocket] = set()
        
        try:
            while True:
                data = await websocket.receive_json()
                command = data.get("command")
                
                if command == "subscribe":
                    entity_types = data.get("entity_types", [])
                    for entity_type in entity_types:
                        self.websocket_subscriptions[websocket].add(entity_type)
                    await websocket.send_json({
                        "status": "subscribed",
                        "entity_types": entity_types
                    })
                    
                elif command == "unsubscribe":
                    entity_types = data.get("entity_types", [])
                    for entity_type in entity_types:
                        self.websocket_subscriptions[websocket].discard(entity_type)
                    await websocket.send_json({
                        "status": "unsubscribed",
                        "entity_types": entity_types
                    })
                    
                elif command == "ping":
                    await websocket.send_json({"pong": True})
                    
        except WebSocketDisconnect:
            self.websocket_connections.remove(websocket)
            del self.websocket_subscriptions[websocket]
            
    async def _notify_websockets(self, message: Dict[str, Any]):
        """Notify WebSocket clients of events"""
        if not self.websocket_connections:
            return
            
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.websocket_connections:
            try:
                # Check if client is subscribed to this entity type
                subscriptions = self.websocket_subscriptions.get(websocket, set())
                if not subscriptions or message.get("entity_type") in subscriptions:
                    await websocket.send_text(message_json)
            except:
                disconnected.add(websocket)
                
        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)
            self.websocket_subscriptions.pop(websocket, None)
            
    # ==================== Background Tasks ====================
    
    def _start_background_tasks(self):
        """Start all background tasks"""
        tasks = [
            self._heartbeat_monitor(),
            self._health_checker(),
            self._event_processor(),
            self._cache_cleanup(),
            self._metrics_collector()
        ]
        
        for task in tasks:
            t = asyncio.create_task(task)
            self.background_tasks.add(t)
            
    async def _heartbeat_monitor(self):
        """Monitor heartbeats and update health scores"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                now = datetime.utcnow()
                status_changes = []
                
                for entity in self.cache.values():
                    if entity.last_heartbeat:
                        time_diff = (now - entity.last_heartbeat).total_seconds()
                        
                        # Update health score based on heartbeat age
                        old_health = entity.health_score
                        if time_diff > 300:  # 5 minutes
                            entity.health_score = 0
                            if entity.status == ServiceStatus.ONLINE:
                                entity.status = ServiceStatus.ERROR
                                status_changes.append(entity)
                        elif time_diff > 120:  # 2 minutes
                            entity.health_score = max(0, entity.health_score - 20)
                        elif time_diff > 60:  # 1 minute
                            entity.health_score = max(0, entity.health_score - 10)
                            
                        # Update health status
                        if entity.health_score != old_health:
                            if entity.health_score >= 80:
                                entity.health_status = HealthStatus.HEALTHY
                            elif entity.health_score >= 50:
                                entity.health_status = HealthStatus.WARNING
                            else:
                                entity.health_status = HealthStatus.CRITICAL
                                
                # Batch update status changes
                if status_changes:
                    async with self.db_pool.acquire() as conn:
                        for entity in status_changes:
                            await self._update_entity(conn, entity)
                            
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                
    async def _health_checker(self):
        """Periodic health checks for all entities"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check servers
                servers = [e for e in self.cache.values() 
                          if e.type in [RegistryType.SERVER_CORE, RegistryType.SERVER_MCP, RegistryType.SERVER_BUSINESS]]
                
                for server in servers:
                    if isinstance(server, ServerRegistryEntry):
                        try:
                            # Simple HTTP health check
                            import aiohttp
                            async with aiohttp.ClientSession() as session:
                                url = f"{server.protocol}://{server.host}:{server.port}/health"
                                async with session.get(url, timeout=5) as response:
                                    if response.status == 200:
                                        server.health_status = HealthStatus.HEALTHY
                                        server.health_score = 100.0
                                    else:
                                        server.health_status = HealthStatus.WARNING
                                        server.health_score = 50.0
                        except:
                            server.health_status = HealthStatus.CRITICAL
                            server.health_score = 0.0
                            
            except Exception as e:
                logger.error(f"Health checker error: {e}")
                
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
                        try:
                            event_data = json.loads(data[b"event"])
                            # Process event if needed
                            logger.debug(f"Processed event: {event_data['event_type']}")
                        except Exception as e:
                            logger.error(f"Failed to process event: {e}")
                            
            except Exception as e:
                logger.error(f"Event processor error: {e}")
                await asyncio.sleep(5)
                
    async def _cache_cleanup(self):
        """Clean up expired cache entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                if not self.enable_caching:
                    continue
                    
                now = time.time()
                expired_keys = []
                
                for key, timestamp in self.cache_timestamps.items():
                    if now - timestamp > self.cache_ttl:
                        expired_keys.append(key)
                        
                for key in expired_keys:
                    self.cache_timestamps.pop(key, None)
                    
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                
    async def _metrics_collector(self):
        """Collect and aggregate metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                # Update uptime
                uptime = (datetime.utcnow() - self.start_time).total_seconds()
                self.metrics.uptime_seconds = int(uptime)
                
                # Calculate success rate
                if self.metrics.total_requests > 0:
                    success_rate = (self.metrics.successful_requests / self.metrics.total_requests) * 100
                    self.metrics.custom_metrics["success_rate"] = success_rate
                    
                # Store metrics in database
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO system_metrics (
                            service_name, metric_name, metric_value, metadata
                        ) VALUES ($1, $2, $3, $4)
                    """, "registry", "system_metrics", success_rate,
                    json.dumps(asdict(self.metrics)))
                    
            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                
    # ==================== Cache Management ====================
    
    def _generate_cache_key(self, operation: str, entity_type: Optional[RegistryType], 
                           filters: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for operations"""
        parts = [operation]
        if entity_type:
            parts.append(entity_type)
        if filters:
            # Sort filters for consistent keys
            filter_str = json.dumps(filters, sort_keys=True)
            parts.append(hashlib.md5(filter_str.encode()).hexdigest())
        return ":".join(parts)
        
    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enable_caching:
            return None
            
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    return json.loads(value)
            except:
                pass
        return None
        
    async def _set_cached(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        if not self.enable_caching or not self.redis:
            return
            
        try:
            ttl = ttl or self.cache_ttl
            await self.redis.setex(key, ttl, json.dumps(value, default=str))
        except:
            pass
            
    async def _invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if not self.redis:
            return
            
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except:
            pass
            
    # ==================== Audit Logging ====================
    
    async def _init_audit_log(self):
        """Initialize audit log table if not exists"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS registry_audit_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    operation VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(255),
                    entity_type VARCHAR(50),
                    user_id VARCHAR(255),
                    ip_address VARCHAR(45),
                    changes JSONB,
                    metadata JSONB
                )
            """)
            
            # Create index for faster queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_log_entity 
                ON registry_audit_log(entity_id, timestamp DESC)
            """)
            
    async def _audit_log(self, operation: str, entity_id: str, data: Dict[str, Any]):
        """Write audit log entry"""
        if not self.enable_audit_log:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO registry_audit_log (
                        operation, entity_id, entity_type, changes
                    ) VALUES ($1, $2, $3, $4)
                """, operation, entity_id, 
                data.get("type", "unknown"),
                json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            
    # ==================== Health and Metrics ====================
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        db_healthy = self.db_pool is not None and not self.db_pool.is_closed()
        redis_healthy = self.redis is not None
        
        # Calculate overall health
        health_score = 100.0
        if not db_healthy:
            health_score -= 50.0
        if not redis_healthy:
            health_score -= 25.0
            
        # Get entity health summary
        entity_health = {
            "total": len(self.cache),
            "healthy": sum(1 for e in self.cache.values() if e.health_score >= 80),
            "warning": sum(1 for e in self.cache.values() if 50 <= e.health_score < 80),
            "critical": sum(1 for e in self.cache.values() if e.health_score < 50),
            "online": sum(1 for e in self.cache.values() if e.status == ServiceStatus.ONLINE)
        }
        
        return {
            "status": "healthy" if health_score >= 80 else "degraded",
            "health_score": health_score,
            "components": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy",
                "cache": "enabled" if self.enable_caching else "disabled",
                "websockets": f"{len(self.websocket_connections)} connected"
            },
            "entities": entity_health,
            "uptime": self.metrics.uptime_seconds,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": (self.metrics.successful_requests / max(1, self.metrics.total_requests)) * 100
            }
        }
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics"""
        return {
            "system": asdict(self.metrics),
            "entities": await self.get_statistics(),
            "cache": {
                "size": len(self.cache),
                "hit_rate": self.metrics.custom_metrics.get("cache_hit_rate", 0.0)
            },
            "performance": {
                "average_response_time": self.metrics.average_response_time,
                "requests_per_minute": self.metrics.custom_metrics.get("rpm", 0)
            }
        }
        
    def run(self, host: str = "0.0.0.0", port: int = 8100):
        """Run the enhanced registry service"""
        logger.info(f"Starting Enhanced Registry System on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# ==================== Convenience Functions ====================

async def create_enhanced_registry(
    db_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    **kwargs
) -> EnhancedRegistrySystem:
    """Create and initialize enhanced registry instance"""
    if not db_url:
        db_url = "postgresql://boarderframe:boarderframe@localhost:5434/boarderframeos"
    if not redis_url:
        redis_url = "redis://localhost:6379"
        
    registry = EnhancedRegistrySystem(db_url, redis_url, **kwargs)
    await registry.initialize()
    return registry


if __name__ == "__main__":
    import os
    
    # Load configuration from environment
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://boarderframe:boarderframe@localhost:5434/boarderframeos"
    )
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Create and run registry
    registry = EnhancedRegistrySystem(
        db_url=db_url,
        redis_url=redis_url,
        enable_caching=True,
        cache_ttl=300,
        enable_websockets=True,
        enable_audit_log=True
    )
    
    registry.run(host="0.0.0.0", port=8100)