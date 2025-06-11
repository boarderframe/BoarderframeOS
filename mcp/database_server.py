"""
Database MCP Server for BoarderframeOS
Provides database operations for agent data persistence
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from collections import OrderedDict, defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiosqlite
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("database_server")

app = FastAPI(title="Database MCP Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "boarderframe.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Request/Response Models
class QueryRequest(BaseModel):
    sql: str = Field(..., description="SQL query to execute")
    params: Optional[List[Any]] = Field(default=[], description="Query parameters")
    fetch_all: bool = Field(True, description="Fetch all results or just one")

class InsertRequest(BaseModel):
    table: str = Field(..., description="Table name")
    data: Dict[str, Any] = Field(..., description="Data to insert")
    on_conflict: str = Field("IGNORE", description="Conflict resolution: IGNORE, REPLACE")

class UpdateRequest(BaseModel):
    table: str = Field(..., description="Table name")
    data: Dict[str, Any] = Field(..., description="Data to update")
    where: Dict[str, Any] = Field(..., description="WHERE conditions")

class DeleteRequest(BaseModel):
    table: str = Field(..., description="Table name")
    where: Dict[str, Any] = Field(..., description="WHERE conditions")

class CreateTableRequest(BaseModel):
    table: str = Field(..., description="Table name")
    column_schema: Dict[str, str] = Field(..., description="Column definitions")
    indexes: Optional[List[str]] = Field(default=[], description="Indexes to create")

class DatabaseResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    rows_affected: int = 0
    timestamp: str

# Connection Pool Implementation
class SQLiteConnectionPool:
    """Connection pool for SQLite database"""

    def __init__(self, db_path: Path, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self._initialized = False

    async def initialize(self):
        """Initialize the connection pool"""
        if self._initialized:
            return

        # Pre-populate the pool with connections
        for _ in range(min(3, self.max_connections)):  # Start with 3 connections
            conn = await self._create_connection()
            await self.pool.put(conn)

        self._initialized = True
        logger.info(f"Connection pool initialized with {self.pool.qsize()} connections")

    async def _create_connection(self):
        """Create a new database connection"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.execute("PRAGMA journal_mode = WAL")
        await conn.execute("PRAGMA synchronous = NORMAL")
        await conn.execute("PRAGMA cache_size = 10000")
        await conn.execute("PRAGMA temp_store = memory")
        self.active_connections += 1
        return conn

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        await self.initialize()

        try:
            # Try to get from pool first
            conn = await asyncio.wait_for(self.pool.get(), timeout=1.0)
        except asyncio.TimeoutError:
            # If pool is empty and we haven't reached max, create new connection
            if self.active_connections < self.max_connections:
                conn = await self._create_connection()
            else:
                # Wait longer for a connection to be returned
                conn = await self.pool.get()

        try:
            yield conn
        finally:
            # Return connection to pool
            await self.pool.put(conn)

    async def close_all(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            conn = await self.pool.get()
            await conn.close()
            self.active_connections -= 1

# Query Cache Implementation
class QueryCache:
    """LRU cache for query results"""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()

    def _get_cache_key(self, sql: str, params: list) -> str:
        """Generate cache key for query"""
        cache_input = f"{sql}:{params}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def get(self, sql: str, params: list):
        """Get cached result if available and not expired"""
        if not self._should_cache_query(sql):
            return None

        cache_key = self._get_cache_key(sql, params)
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(cache_key)
                return result
            else:
                # Expired, remove from cache
                del self.cache[cache_key]
        return None

    def set(self, sql: str, params: list, result):
        """Cache query result"""
        if not self._should_cache_query(sql):
            return

        cache_key = self._get_cache_key(sql, params)

        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[cache_key] = (result, time.time())

    def _should_cache_query(self, sql: str) -> bool:
        """Determine if query should be cached (only SELECT queries)"""
        return sql.strip().upper().startswith('SELECT')

    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()

# Database Manager
class DatabaseManager:
    """Manages SQLite database operations with connection pooling and caching"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.is_initialized = False
        self.connection_pool = SQLiteConnectionPool(db_path)
        self.query_cache = QueryCache()

        # Query statistics
        self.query_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_query_time': 0
        }

    async def initialize(self):
        """Initialize database with core tables"""
        if self.is_initialized:
            return

        try:
            async with self.connection_pool.get_connection() as db:
            # Connection pool already enables foreign keys and optimizations

                # Core tables for BoarderframeOS
                await self._create_core_tables(db)
                await db.commit()

                self.is_initialized = True
                logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise HTTPException(status_code=500, detail=f"Database init failed: {e}")

    async def _create_core_tables(self, db):
        """Create core system tables"""

        # Agents table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id TEXT,
                biome TEXT,
                generation INTEGER DEFAULT 1,
                fitness_score REAL DEFAULT 0.0,
                config TEXT,  -- JSON config
                code TEXT,    -- Agent code
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (parent_id) REFERENCES agents(id)
            )
        """)

        # Agent memories table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'short_term',
                importance REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        """)

        # Agent interactions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_interactions (
                id TEXT PRIMARY KEY,
                source_agent TEXT NOT NULL,
                target_agent TEXT,
                interaction_type TEXT,
                data TEXT,  -- JSON data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_agent) REFERENCES agents(id),
                FOREIGN KEY (target_agent) REFERENCES agents(id)
            )
        """)

        # Metrics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT,  -- JSON metadata
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        """)

        # Evolution log table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS evolution_log (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                child_id TEXT NOT NULL,
                generation INTEGER,
                mutations TEXT,  -- JSON list of mutations
                fitness_improvement REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES agents(id),
                FOREIGN KEY (child_id) REFERENCES agents(id)
            )
        """)

        # Tasks table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                task_type TEXT NOT NULL,
                description TEXT,
                data TEXT,  -- JSON task data
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        """)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_agents_biome ON agents(biome)",
            "CREATE INDEX IF NOT EXISTS idx_agents_generation ON agents(generation)",
            "CREATE INDEX IF NOT EXISTS idx_agents_fitness ON agents(fitness_score)",
            "CREATE INDEX IF NOT EXISTS idx_memories_agent ON agent_memories(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_memories_type ON agent_memories(memory_type)",
            "CREATE INDEX IF NOT EXISTS idx_interactions_source ON agent_interactions(source_agent)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_agent ON metrics(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
        ]

        for index_sql in indexes:
            await db.execute(index_sql)

        # Create business-related tables

        # Revenue tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS revenue_transactions (
                id TEXT PRIMARY KEY,
                customer_id TEXT,
                amount DECIMAL(10,2),
                currency TEXT,
                product TEXT,
                agent_id TEXT,  -- Which agent generated this revenue
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Customer subscriptions
        await db.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                stripe_customer_id TEXT,
                subscription_status TEXT,
                monthly_value DECIMAL(10,2),
                created_by_agent TEXT
            )
        """)

        # API usage for billing
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                customer_id TEXT,
                endpoint TEXT,
                tokens_used INTEGER,
                cost DECIMAL(10,4),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for business tables
        business_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_revenue_customer ON revenue_transactions(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_revenue_agent ON revenue_transactions(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_revenue_product ON revenue_transactions(product)",
            "CREATE INDEX IF NOT EXISTS idx_customers_subscription ON customers(subscription_status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_created_by ON customers(created_by_agent)",
            "CREATE INDEX IF NOT EXISTS idx_api_usage_customer ON api_usage(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint)"
        ]

        for index_sql in business_indexes:
            await db.execute(index_sql)

    async def execute_query(self, request: QueryRequest) -> DatabaseResponse:
        """Execute SQL query with connection pooling and caching"""
        start_time = time.time()
        self.query_stats['total_queries'] += 1

        try:
            await self.initialize()

            # Check cache for SELECT queries
            if request.sql.strip().upper().startswith('SELECT'):
                cached_result = self.query_cache.get(request.sql, request.params)
                if cached_result is not None:
                    self.query_stats['cache_hits'] += 1
                    return DatabaseResponse(
                        success=True,
                        data=cached_result,
                        rows_affected=0,
                        timestamp=datetime.now().isoformat()
                    )
                self.query_stats['cache_misses'] += 1

            # Execute query using connection pool
            async with self.connection_pool.get_connection() as db:
                cursor = await db.execute(request.sql, request.params)

                if request.sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    rows_affected = cursor.rowcount
                    await db.commit()
                    data = None

                    # Clear relevant cache entries for write operations
                    self.query_cache.clear()
                else:
                    if request.fetch_all:
                        rows = await cursor.fetchall()
                        data = [dict(row) for row in rows]
                    else:
                        row = await cursor.fetchone()
                        data = dict(row) if row else None
                    rows_affected = 0

                    # Cache SELECT results
                    if request.sql.strip().upper().startswith('SELECT'):
                        self.query_cache.set(request.sql, request.params, data)

                # Update query timing statistics
                query_time = time.time() - start_time
                self.query_stats['avg_query_time'] = (
                    self.query_stats['avg_query_time'] * (self.query_stats['total_queries'] - 1) + query_time
                ) / self.query_stats['total_queries']

                return DatabaseResponse(
                    success=True,
                    data=data,
                    rows_affected=rows_affected,
                    timestamp=datetime.now().isoformat()
                )

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def insert_data(self, request: InsertRequest) -> DatabaseResponse:
        """Insert data into table"""
        try:
            await self.initialize()

            columns = list(request.data.keys())
            placeholders = ['?' for _ in columns]
            values = [request.data[col] for col in columns]

            sql = f"""
                INSERT OR {request.on_conflict} INTO {request.table}
                ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """

            query_request = QueryRequest(sql=sql, params=values)
            return await self.execute_query(query_request)

        except Exception as e:
            logger.error(f"Insert failed: {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def update_data(self, request: UpdateRequest) -> DatabaseResponse:
        """Update data in table"""
        try:
            await self.initialize()

            set_clauses = [f"{col} = ?" for col in request.data.keys()]
            where_clauses = [f"{col} = ?" for col in request.where.keys()]

            set_values = list(request.data.values())
            where_values = list(request.where.values())

            sql = f"""
                UPDATE {request.table}
                SET {', '.join(set_clauses)}
                WHERE {' AND '.join(where_clauses)}
            """

            query_request = QueryRequest(sql=sql, params=set_values + where_values)
            return await self.execute_query(query_request)

        except Exception as e:
            logger.error(f"Update failed: {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def delete_data(self, request: DeleteRequest) -> DatabaseResponse:
        """Delete data from table"""
        try:
            await self.initialize()

            where_clauses = [f"{col} = ?" for col in request.where.keys()]
            where_values = list(request.where.values())

            sql = f"""
                DELETE FROM {request.table}
                WHERE {' AND '.join(where_clauses)}
            """

            query_request = QueryRequest(sql=sql, params=where_values)
            return await self.execute_query(query_request)

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def create_table(self, request: CreateTableRequest) -> DatabaseResponse:
        """Create new table"""
        try:
            await self.initialize()

            column_defs = [f"{col} {datatype}" for col, datatype in request.column_schema.items()]

            sql = f"""
                CREATE TABLE IF NOT EXISTS {request.table} (
                    {', '.join(column_defs)}
                )
            """

            async with self.connection_pool.get_connection() as db:
                await db.execute(sql)

                # Create indexes if specified
                for index in request.indexes:
                    index_sql = f"CREATE INDEX IF NOT EXISTS idx_{request.table}_{index} ON {request.table}({index})"
                    await db.execute(index_sql)

                await db.commit()

                # Clear cache after schema changes
                self.query_cache.clear()

                return DatabaseResponse(
                    success=True,
                    data={"table_created": request.table, "indexes": request.indexes},
                    timestamp=datetime.now().isoformat()
                )

        except Exception as e:
            logger.error(f"Create table failed: {e}")
            return DatabaseResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )

# Global database manager
db_manager = DatabaseManager(DB_PATH)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "database_server", "db_path": str(DB_PATH)}

@app.post("/query", response_model=DatabaseResponse)
async def execute_query(request: QueryRequest):
    """Execute raw SQL query"""
    return await db_manager.execute_query(request)

@app.post("/insert", response_model=DatabaseResponse)
async def insert_data(request: InsertRequest):
    """Insert data into table"""
    return await db_manager.insert_data(request)

@app.post("/update", response_model=DatabaseResponse)
async def update_data(request: UpdateRequest):
    """Update data in table"""
    return await db_manager.update_data(request)

@app.post("/delete", response_model=DatabaseResponse)
async def delete_data(request: DeleteRequest):
    """Delete data from table"""
    return await db_manager.delete_data(request)

@app.post("/create-table", response_model=DatabaseResponse)
async def create_table(request: CreateTableRequest):
    """Create new table"""
    return await db_manager.create_table(request)

@app.get("/tables")
async def list_tables():
    """List all tables in database"""
    query = QueryRequest(
        sql="SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        fetch_all=True
    )
    result = await db_manager.execute_query(query)

    if result.success:
        tables = [row['name'] for row in result.data]
        return {"tables": tables}
    else:
        return {"error": result.error}

@app.get("/schema/{table}")
async def get_table_schema(table: str):
    """Get schema for specific table"""
    query = QueryRequest(
        sql=f"PRAGMA table_info({table})",
        fetch_all=True
    )
    result = await db_manager.execute_query(query)

    if result.success:
        return {"table": table, "schema": result.data}
    else:
        return {"error": result.error}

@app.get("/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        await db_manager.initialize()

        async with db_manager.connection_pool.get_connection() as db:
            # Get table counts
            cursor = await db.execute("""
                SELECT name FROM sqlite_master WHERE type='table'
            """)
            tables = await cursor.fetchall()

            stats = {"tables": {}}

            for table in tables:
                table_name = table[0]
                cursor = await db.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count_result = await cursor.fetchone()
                stats["tables"][table_name] = count_result[0]

            # Database size
            db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
            stats["database_size_bytes"] = db_size

            return stats

    except Exception as e:
        return {"error": str(e)}

@app.get("/performance")
async def get_performance_stats():
    """Get performance statistics for connection pool and query cache"""
    try:
        cache_hit_rate = 0
        if db_manager.query_stats['total_queries'] > 0:
            cache_hit_rate = (db_manager.query_stats['cache_hits'] /
                            (db_manager.query_stats['cache_hits'] + db_manager.query_stats['cache_misses']))

        pool_stats = {
            "active_connections": db_manager.connection_pool.active_connections,
            "max_connections": db_manager.connection_pool.max_connections,
            "available_connections": db_manager.connection_pool.pool.qsize(),
            "pool_initialized": db_manager.connection_pool._initialized
        }

        cache_stats = {
            "cached_entries": len(db_manager.query_cache.cache),
            "cache_size_limit": db_manager.query_cache.max_size,
            "cache_ttl": db_manager.query_cache.ttl
        }

        query_stats = {
            "total_queries": db_manager.query_stats['total_queries'],
            "cache_hits": db_manager.query_stats['cache_hits'],
            "cache_misses": db_manager.query_stats['cache_misses'],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "avg_query_time": f"{db_manager.query_stats['avg_query_time']:.4f}s"
        }

        return {
            "connection_pool": pool_stats,
            "query_cache": cache_stats,
            "query_performance": query_stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8004, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting Database MCP Server on {args.host}:{args.port}")
    logger.info(f"Database location: {DB_PATH}")

    uvicorn.run(
        "database_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
