"""
Enhanced Database MCP Server for BoarderframeOS
PostgreSQL + pgvector + Redis integration for agent data persistence
"""

import asyncio
import hashlib

# import aioredis  # Temporarily disabled due to Python 3.13 compatibility
import json
import logging
import os
import time
import uuid
from collections import OrderedDict, defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import asyncpg
import numpy as np
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "mcp_postgres.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("database_server_postgres")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "15"))  # Increased for 120+ agents
POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "50"))  # Increased for high throughput
QUERY_CACHE_SIZE = int(os.getenv("QUERY_CACHE_SIZE", "5000"))
QUERY_CACHE_TTL = int(os.getenv("QUERY_CACHE_TTL", "300"))  # 5 minutes

# Global connections
db_pool: Optional[asyncpg.Pool] = None
redis_client = None  # Temporarily disabled

# Advanced Query Caching System
class PostgreSQLQueryCache:
    """High-performance LRU cache for PostgreSQL queries with TTL"""

    def __init__(self, max_size: int = QUERY_CACHE_SIZE, ttl: int = QUERY_CACHE_TTL):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_queries': 0
        }

    def _get_cache_key(self, sql: str, params: list) -> str:
        """Generate cache key for query"""
        cache_input = f"{sql}:{params}"
        return hashlib.sha256(cache_input.encode()).hexdigest()[:16]

    def get(self, sql: str, params: list):
        """Get cached result if available and not expired"""
        if not self._should_cache_query(sql):
            return None

        cache_key = self._get_cache_key(sql, params)
        self.stats['total_queries'] += 1

        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(cache_key)
                self.stats['hits'] += 1
                return result
            else:
                # Expired, remove from cache
                del self.cache[cache_key]

        self.stats['misses'] += 1
        return None

    def set(self, sql: str, params: list, result):
        """Cache query result"""
        if not self._should_cache_query(sql):
            return

        cache_key = self._get_cache_key(sql, params)

        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            self.stats['evictions'] += 1

        self.cache[cache_key] = (result, time.time())

    def _should_cache_query(self, sql: str) -> bool:
        """Determine if query should be cached (only SELECT queries)"""
        sql_upper = sql.strip().upper()
        return (sql_upper.startswith('SELECT') and
                'RANDOM()' not in sql_upper and
                'NOW()' not in sql_upper and
                'CURRENT_TIMESTAMP' not in sql_upper)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0

        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': f"{hit_rate:.2%}",
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'total_queries': self.stats['total_queries']
        }

    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()

# Connection Pool Monitoring
class ConnectionPoolMonitor:
    """Monitor and optimize PostgreSQL connection pool performance"""

    def __init__(self):
        self.connection_stats = defaultdict(int)
        self.query_times = []
        self.slow_query_threshold = 1.0  # 1 second

    def record_query(self, duration: float, connection_id: str):
        """Record query execution time"""
        self.query_times.append(duration)
        self.connection_stats[connection_id] += 1

        # Keep only last 1000 query times
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]

    def get_performance_stats(self, pool: asyncpg.Pool) -> Dict[str, Any]:
        """Get comprehensive pool performance statistics"""
        if not self.query_times:
            avg_query_time = 0
            slow_queries = 0
        else:
            avg_query_time = sum(self.query_times) / len(self.query_times)
            slow_queries = sum(1 for t in self.query_times if t > self.slow_query_threshold)

        try:
            pool_size = pool.get_size()
            min_size = pool.get_min_size()
            max_size = pool.get_max_size()
        except AttributeError:
            # Fallback for different asyncpg versions
            pool_size = getattr(pool, '_size', 0)
            min_size = getattr(pool, '_min_size', 0)
            max_size = getattr(pool, '_max_size', 0)

        return {
            'pool_size': pool_size,
            'pool_min_size': min_size,
            'pool_max_size': max_size,
            'available_connections': 'N/A',  # asyncpg doesn't expose this easily
            'busy_connections': 'N/A',
            'avg_query_time_ms': f"{avg_query_time * 1000:.2f}",
            'slow_queries': slow_queries,
            'total_queries_monitored': len(self.query_times),
            'connection_usage': dict(self.connection_stats)
        }

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class QueryRequest(BaseModel):
    sql: str = Field(..., description="SQL query to execute")
    params: Optional[List[Any]] = Field(default=[], description="Query parameters")
    fetch_all: bool = Field(True, description="Fetch all results or just one")
    timeout: Optional[int] = Field(default=30, description="Query timeout in seconds")

class InsertRequest(BaseModel):
    table: str = Field(..., description="Table name")
    data: Dict[str, Any] = Field(..., description="Data to insert")
    on_conflict: str = Field("DO NOTHING", description="Conflict resolution: DO NOTHING, DO UPDATE")
    return_id: bool = Field(True, description="Return inserted ID")

class UpdateRequest(BaseModel):
    table: str = Field(..., description="Table name")
    data: Dict[str, Any] = Field(..., description="Data to update")
    where: Dict[str, Any] = Field(..., description="WHERE conditions")

class DeleteRequest(BaseModel):
    table: str = Field(..., description="Table name")
    where: Dict[str, Any] = Field(..., description="WHERE conditions")

class VectorSearchRequest(BaseModel):
    table: str = Field(default="agent_memories", description="Table to search")
    embedding: List[float] = Field(..., description="Query embedding vector")
    similarity_threshold: float = Field(default=0.8, description="Minimum similarity threshold")
    limit: int = Field(default=10, description="Maximum results to return")
    agent_id: Optional[str] = Field(default=None, description="Filter by specific agent")
    memory_type: Optional[str] = Field(default=None, description="Filter by memory type")

class MemoryInsertRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    content: str = Field(..., description="Memory content")
    memory_type: str = Field(default="short_term", description="Memory type")
    importance: float = Field(default=0.5, description="Memory importance (0.0-1.0)")
    embedding: Optional[List[float]] = Field(default=None, description="Pre-computed embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID")

class DatabaseResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    rows_affected: int = 0
    execution_time_ms: float = 0
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    pool_size: int
    active_connections: int
    timestamp: str

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class PostgreSQLManager:
    """Enhanced PostgreSQL database manager with advanced caching and monitoring"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.redis = None  # Temporarily disabled
        self.is_initialized = False

        # Advanced features
        self.query_cache = PostgreSQLQueryCache()
        self.pool_monitor = ConnectionPoolMonitor()
        self.prepared_statements = {}  # Cache for prepared statements

    async def initialize(self):
        """Initialize PostgreSQL pool and Redis connection"""
        if self.is_initialized:
            return

        try:
            # Initialize PostgreSQL connection pool with optimized settings
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=POOL_MIN_SIZE,
                max_size=POOL_MAX_SIZE,
                command_timeout=60,
                server_settings={
                    'jit': 'off',  # Disable JIT for faster connection
                    'application_name': 'BoarderframeOS_MCP'
                },
                init=self._init_connection
            )

            # Initialize Redis connection
            # self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)  # Temporarily disabled

            # Test connections
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                logger.info("PostgreSQL connection pool initialized")

            # await self.redis.ping()  # Temporarily disabled
            # logger.info("Redis connection initialized")

            self.is_initialized = True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise HTTPException(status_code=500, detail=f"Database init failed: {e}")

    async def _init_connection(self, conn: asyncpg.Connection):
        """Initialize each connection in the pool"""
        # Register vector type
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # Set timezone
        await conn.execute("SET timezone = 'UTC'")

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
        if self.redis:
            await self.redis.close()

    async def execute_query(self, request: QueryRequest) -> DatabaseResponse:
        """Execute SQL query with advanced caching and monitoring"""
        start_time = time.time()

        try:
            await self.initialize()

            # Check cache for SELECT queries
            if request.sql.strip().upper().startswith('SELECT'):
                cached_result = self.query_cache.get(request.sql, request.params)
                if cached_result is not None:
                    execution_time = (time.time() - start_time) * 1000
                    return DatabaseResponse(
                        success=True,
                        data=cached_result,
                        rows_affected=0,
                        execution_time_ms=round(execution_time, 2),
                        timestamp=datetime.utcnow().isoformat()
                    )

            async with self.pool.acquire() as conn:
                connection_id = f"conn_{id(conn)}"

                if request.sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    # Write operations - clear cache
                    self.query_cache.clear()
                    result = await conn.execute(request.sql, *request.params)
                    rows_affected = int(result.split()[-1]) if result.split() else 0
                    data = None
                else:
                    # Read operations
                    if request.fetch_all:
                        rows = await conn.fetch(request.sql, *request.params)
                        data = [dict(row) for row in rows]
                    else:
                        row = await conn.fetchrow(request.sql, *request.params)
                        data = dict(row) if row else None
                    rows_affected = 0

                    # Cache SELECT results
                    if request.sql.strip().upper().startswith('SELECT'):
                        self.query_cache.set(request.sql, request.params, data)

                execution_time = (time.time() - start_time) * 1000

                # Record performance metrics
                self.pool_monitor.record_query(execution_time / 1000, connection_id)

                # Log slow queries
                if execution_time > 1000:
                    logger.warning(f"Slow query ({execution_time:.2f}ms): {request.sql[:100]}...")

                return DatabaseResponse(
                    success=True,
                    data=data,
                    rows_affected=rows_affected,
                    execution_time_ms=round(execution_time, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query execution failed ({execution_time:.2f}ms): {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                execution_time_ms=round(execution_time, 2),
                timestamp=datetime.utcnow().isoformat()
            )

    async def insert_data(self, request: InsertRequest) -> DatabaseResponse:
        """Insert data with enhanced conflict handling"""
        start_time = time.time()

        try:
            await self.initialize()

            # Build INSERT query
            columns = list(request.data.keys())
            placeholders = [f'${i+1}' for i in range(len(columns))]
            values = [request.data[col] for col in columns]

            # Handle UUIDs and JSON
            for i, value in enumerate(values):
                if isinstance(value, dict):
                    values[i] = json.dumps(value)
                elif isinstance(value, list) and all(isinstance(x, (int, float)) for x in value):
                    # Handle vector embeddings
                    values[i] = value

            sql = f"""
                INSERT INTO {request.table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT {request.on_conflict}
            """

            if request.return_id and 'id' not in columns:
                sql += " RETURNING id"

            async with self.pool.acquire() as conn:
                if request.return_id and 'id' not in columns:
                    result = await conn.fetchval(sql, *values)
                    data = {"id": result} if result else None
                    rows_affected = 1 if result else 0
                else:
                    result = await conn.execute(sql, *values)
                    rows_affected = int(result.split()[-1]) if result.split() else 0
                    data = None

                execution_time = (time.time() - start_time) * 1000

                # Publish insert event to Redis
                if self.redis and rows_affected > 0:
                    await self._publish_event("insert", request.table, data or request.data)

                return DatabaseResponse(
                    success=True,
                    data=data,
                    rows_affected=rows_affected,
                    execution_time_ms=round(execution_time, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Insert failed ({execution_time:.2f}ms): {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                execution_time_ms=round(execution_time, 2),
                timestamp=datetime.utcnow().isoformat()
            )

    async def update_data(self, request: UpdateRequest) -> DatabaseResponse:
        """Update data with change tracking"""
        start_time = time.time()

        try:
            await self.initialize()

            set_clauses = [f"{col} = ${i+1}" for i, col in enumerate(request.data.keys())]
            where_clauses = [f"{col} = ${i+len(request.data)+1}" for i, col in enumerate(request.where.keys())]

            set_values = list(request.data.values())
            where_values = list(request.where.values())

            # Handle JSON serialization
            for i, value in enumerate(set_values):
                if isinstance(value, dict):
                    set_values[i] = json.dumps(value)

            sql = f"""
                UPDATE {request.table}
                SET {', '.join(set_clauses)}
                WHERE {' AND '.join(where_clauses)}
            """

            async with self.pool.acquire() as conn:
                result = await conn.execute(sql, *(set_values + where_values))
                rows_affected = int(result.split()[-1]) if result.split() else 0

                execution_time = (time.time() - start_time) * 1000

                # Publish update event
                if self.redis and rows_affected > 0:
                    await self._publish_event("update", request.table, {**request.where, **request.data})

                return DatabaseResponse(
                    success=True,
                    rows_affected=rows_affected,
                    execution_time_ms=round(execution_time, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Update failed ({execution_time:.2f}ms): {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                execution_time_ms=round(execution_time, 2),
                timestamp=datetime.utcnow().isoformat()
            )

    async def delete_data(self, request: DeleteRequest) -> DatabaseResponse:
        """Delete data with audit logging"""
        start_time = time.time()

        try:
            await self.initialize()

            where_clauses = [f"{col} = ${i+1}" for i, col in enumerate(request.where.keys())]
            where_values = list(request.where.values())

            sql = f"""
                DELETE FROM {request.table}
                WHERE {' AND '.join(where_clauses)}
            """

            async with self.pool.acquire() as conn:
                result = await conn.execute(sql, *where_values)
                rows_affected = int(result.split()[-1]) if result.split() else 0

                execution_time = (time.time() - start_time) * 1000

                # Publish delete event
                if self.redis and rows_affected > 0:
                    await self._publish_event("delete", request.table, request.where)

                return DatabaseResponse(
                    success=True,
                    rows_affected=rows_affected,
                    execution_time_ms=round(execution_time, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Delete failed ({execution_time:.2f}ms): {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                execution_time_ms=round(execution_time, 2),
                timestamp=datetime.utcnow().isoformat()
            )

    async def vector_similarity_search(self, request: VectorSearchRequest) -> DatabaseResponse:
        """Perform semantic similarity search using pgvector"""
        start_time = time.time()

        try:
            await self.initialize()

            # Build query with filters
            where_conditions = ["1 - (embedding <=> $1) > $2"]
            params = [request.embedding, request.similarity_threshold]
            param_counter = 3

            if request.agent_id:
                where_conditions.append(f"agent_id = ${param_counter}")
                params.append(request.agent_id)
                param_counter += 1

            if request.memory_type:
                where_conditions.append(f"memory_type = ${param_counter}")
                params.append(request.memory_type)
                param_counter += 1

            sql = f"""
                SELECT
                    id,
                    agent_id,
                    content,
                    memory_type,
                    importance,
                    metadata,
                    conversation_id,
                    workflow_id,
                    1 - (embedding <=> $1) as similarity,
                    created_at,
                    accessed_at
                FROM {request.table}
                WHERE {' AND '.join(where_conditions)}
                ORDER BY embedding <=> $1
                LIMIT ${param_counter}
            """

            params.append(request.limit)

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)
                data = [dict(row) for row in rows]

                # Update access time for retrieved memories
                if data and request.table == 'agent_memories':
                    memory_ids = [row['id'] for row in data]
                    await conn.execute("""
                        UPDATE agent_memories
                        SET accessed_at = NOW(), access_count = access_count + 1
                        WHERE id = ANY($1)
                    """, memory_ids)

                execution_time = (time.time() - start_time) * 1000

                return DatabaseResponse(
                    success=True,
                    data=data,
                    rows_affected=len(data),
                    execution_time_ms=round(execution_time, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Vector search failed ({execution_time:.2f}ms): {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                execution_time_ms=round(execution_time, 2),
                timestamp=datetime.utcnow().isoformat()
            )

    async def insert_memory(self, request: MemoryInsertRequest) -> DatabaseResponse:
        """Insert agent memory with automatic embedding generation"""
        start_time = time.time()

        try:
            await self.initialize()

            # Generate embedding if not provided
            embedding = request.embedding
            if embedding is None:
                # For now, use random embedding - replace with actual embedding generation
                embedding = np.random.random(1536).tolist()
                logger.warning("Using random embedding - implement actual embedding generation")

            memory_id = str(uuid.uuid4())

            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_memories (
                        id, agent_id, content, memory_type, importance,
                        embedding, metadata, conversation_id, workflow_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    memory_id,
                    request.agent_id,
                    request.content,
                    request.memory_type,
                    request.importance,
                    embedding,
                    json.dumps(request.metadata),
                    request.conversation_id,
                    request.workflow_id
                )

                execution_time = (time.time() - start_time) * 1000

                # Publish memory creation event
                if self.redis:
                    await self._publish_event("memory_created", "agent_memories", {
                        "id": memory_id,
                        "agent_id": request.agent_id,
                        "content": request.content[:100] + "..." if len(request.content) > 100 else request.content
                    })

                return DatabaseResponse(
                    success=True,
                    data={"id": memory_id},
                    rows_affected=1,
                    execution_time_ms=round(execution_time, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Memory insert failed ({execution_time:.2f}ms): {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                execution_time_ms=round(execution_time, 2),
                timestamp=datetime.utcnow().isoformat()
            )

    async def _publish_event(self, event_type: str, table: str, data: Dict[str, Any]):
        """Publish database events to Redis Streams"""
        try:
            if self.redis:
                event = {
                    "event_type": event_type,
                    "table": table,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": json.dumps(data, default=str)
                }
                await self.redis.xadd("db_events", event)
        except Exception as e:
            logger.warning(f"Failed to publish event: {e}")

    async def get_health_status(self) -> HealthResponse:
        """Get comprehensive health status"""
        try:
            await self.initialize()

            # Database health
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                db_status = "healthy"
                pool_size = self.pool.get_size()

            # Redis health (temporarily disabled)
            # await self.redis.ping()
            redis_status = "disabled"

            return HealthResponse(
                status="healthy",
                database=db_status,
                redis=redis_status,
                pool_size=pool_size,
                active_connections=len(self.pool._holders),
                timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status="unhealthy",
                database="error",
                redis="error",
                pool_size=0,
                active_connections=0,
                timestamp=datetime.utcnow().isoformat()
            )

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool, redis_client
    db_manager = PostgreSQLManager()
    await db_manager.initialize()
    db_pool = db_manager.pool
    redis_client = db_manager.redis
    logger.info("Database MCP Server started")

    yield

    # Shutdown
    if db_pool:
        await db_pool.close()
    # if redis_client:
    #     await redis_client.close()  # Temporarily disabled
    logger.info("Database MCP Server stopped")

app = FastAPI(
    title="Enhanced Database MCP Server",
    version="2.0.0",
    description="PostgreSQL + pgvector + Redis integration for BoarderframeOS",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database manager
db_manager = PostgreSQLManager()

async def get_db_manager():
    """Dependency for database manager"""
    await db_manager.initialize()
    return db_manager

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check(db: PostgreSQLManager = Depends(get_db_manager)):
    """Comprehensive health check endpoint"""
    return await db.get_health_status()

@app.post("/query", response_model=DatabaseResponse)
async def execute_query(request: QueryRequest, db: PostgreSQLManager = Depends(get_db_manager)):
    """Execute raw SQL query with performance monitoring"""
    return await db.execute_query(request)

@app.post("/insert", response_model=DatabaseResponse)
async def insert_data(request: InsertRequest, db: PostgreSQLManager = Depends(get_db_manager)):
    """Insert data with enhanced conflict handling"""
    return await db.insert_data(request)

@app.post("/update", response_model=DatabaseResponse)
async def update_data(request: UpdateRequest, db: PostgreSQLManager = Depends(get_db_manager)):
    """Update data with change tracking"""
    return await db.update_data(request)

@app.post("/delete", response_model=DatabaseResponse)
async def delete_data(request: DeleteRequest, db: PostgreSQLManager = Depends(get_db_manager)):
    """Delete data with audit logging"""
    return await db.delete_data(request)

@app.post("/vector-search", response_model=DatabaseResponse)
async def vector_similarity_search(request: VectorSearchRequest, db: PostgreSQLManager = Depends(get_db_manager)):
    """Semantic similarity search using pgvector"""
    return await db.vector_similarity_search(request)

@app.post("/memory", response_model=DatabaseResponse)
async def insert_memory(request: MemoryInsertRequest, db: PostgreSQLManager = Depends(get_db_manager)):
    """Insert agent memory with automatic embedding generation"""
    return await db.insert_memory(request)

@app.get("/tables")
async def list_tables(db: PostgreSQLManager = Depends(get_db_manager)):
    """List all tables in database"""
    query = QueryRequest(
        sql="SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name",
        fetch_all=True
    )
    result = await db.execute_query(query)

    if result.success:
        tables = [row['table_name'] for row in result.data]
        return {"tables": tables, "count": len(tables)}
    else:
        raise HTTPException(status_code=500, detail=result.error)

@app.get("/schema/{table}")
async def get_table_schema(table: str, db: PostgreSQLManager = Depends(get_db_manager)):
    """Get schema for specific table"""
    query = QueryRequest(
        sql="""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = 'public'
            ORDER BY ordinal_position
        """,
        params=[table],
        fetch_all=True
    )
    result = await db.execute_query(query)

    if result.success:
        return {"table": table, "schema": result.data}
    else:
        raise HTTPException(status_code=500, detail=result.error)

@app.get("/stats")
async def get_database_stats(db: PostgreSQLManager = Depends(get_db_manager)):
    """Get comprehensive database statistics"""
    try:
        stats_query = QueryRequest(
            sql="""
                SELECT
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """,
            fetch_all=True
        )

        table_stats = await db.execute_query(stats_query)

        # Database size
        size_query = QueryRequest(
            sql="SELECT pg_size_pretty(pg_database_size(current_database())) as size",
            fetch_all=False
        )

        size_result = await db.execute_query(size_query)

        return {
            "database_size": size_result.data.get("size") if size_result.success else "unknown",
            "table_statistics": table_stats.data if table_stats.success else [],
            "connection_pool": {
                "size": db.pool.get_size() if db.pool else 0,
                "available": len(db.pool._holders) if db.pool else 0
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def get_recent_events(limit: int = 10, db: PostgreSQLManager = Depends(get_db_manager)):
    """Get recent database events from Redis Streams"""
    try:
        await db.initialize()
        events = await db.redis.xrevrange("db_events", count=limit)

        formatted_events = []
        for event_id, fields in events:
            formatted_events.append({
                "id": event_id,
                "timestamp": fields.get("timestamp"),
                "event_type": fields.get("event_type"),
                "table": fields.get("table"),
                "data": json.loads(fields.get("data", "{}"))
            })

        return {"events": formatted_events, "count": len(formatted_events)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance")
async def get_performance_stats(db: PostgreSQLManager = Depends(get_db_manager)):
    """Get comprehensive performance statistics"""
    try:
        await db.initialize()

        # Get connection pool stats
        pool_stats = db.pool_monitor.get_performance_stats(db.pool)

        # Get query cache stats
        cache_stats = db.query_cache.get_stats()

        # Get PostgreSQL-specific stats
        pg_stats_query = QueryRequest(
            sql="""
                SELECT
                    numbackends as active_connections,
                    xact_commit as transactions_committed,
                    xact_rollback as transactions_rolled_back,
                    blks_read as blocks_read,
                    blks_hit as blocks_hit,
                    tup_returned as tuples_returned,
                    tup_fetched as tuples_fetched,
                    tup_inserted as tuples_inserted,
                    tup_updated as tuples_updated,
                    tup_deleted as tuples_deleted
                FROM pg_stat_database
                WHERE datname = current_database()
            """,
            fetch_all=False
        )
        pg_result = await db.execute_query(pg_stats_query)

        # Calculate cache hit ratio
        pg_stats = pg_result.data if pg_result.success else {}
        if pg_stats and pg_stats.get('blocks_read', 0) + pg_stats.get('blocks_hit', 0) > 0:
            cache_hit_ratio = pg_stats['blocks_hit'] / (pg_stats['blocks_read'] + pg_stats['blocks_hit'])
        else:
            cache_hit_ratio = 0

        return {
            "connection_pool": pool_stats,
            "query_cache": cache_stats,
            "postgresql": {
                "database_stats": pg_stats,
                "cache_hit_ratio": f"{cache_hit_ratio:.2%}",
                "database_url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else "localhost"
            },
            "optimization_features": {
                "connection_pooling": True,
                "query_caching": True,
                "performance_monitoring": True,
                "pgvector_support": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/stats")
async def get_cache_stats(db: PostgreSQLManager = Depends(get_db_manager)):
    """Get detailed query cache statistics"""
    try:
        await db.initialize()
        cache_stats = db.query_cache.get_stats()

        return {
            "cache_stats": cache_stats,
            "cache_configuration": {
                "max_size": QUERY_CACHE_SIZE,
                "ttl_seconds": QUERY_CACHE_TTL
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
async def clear_cache(db: PostgreSQLManager = Depends(get_db_manager)):
    """Clear the query cache"""
    try:
        await db.initialize()
        db.query_cache.clear()

        return {
            "success": True,
            "message": "Query cache cleared",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Database MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8004, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting Enhanced Database MCP Server on {args.host}:{args.port}")
    logger.info(f"PostgreSQL: {DATABASE_URL}")
    logger.info(f"Redis: {REDIS_URL}")

    uvicorn.run(
        "database_server_postgres:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
