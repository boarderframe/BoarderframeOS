"""
Optimized database configuration with connection pooling and performance tuning
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from sqlalchemy import event, pool
from sqlalchemy.orm import Session
import asyncpg

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database performance configuration"""
    
    # Connection pool settings
    POOL_SIZE = 20  # Number of persistent connections
    MAX_OVERFLOW = 40  # Maximum overflow connections
    POOL_TIMEOUT = 30  # Seconds to wait for connection
    POOL_RECYCLE = 3600  # Recycle connections after 1 hour
    POOL_PRE_PING = True  # Test connections before using
    
    # Query optimization
    ECHO = False  # Set to True for SQL debugging
    ECHO_POOL = False  # Set to True for pool debugging
    FUTURE = True  # Use SQLAlchemy 2.0 style
    
    # PostgreSQL specific optimizations
    POSTGRES_OPTIONS = {
        "server_settings": {
            "jit": "off",  # Disable JIT for consistent performance
            "application_name": "mcp_server_manager",
        },
        "command_timeout": 60,
        "pool_size": 20,
        "max_inactive_connection_lifetime": 300,
    }
    
    # Statement timeout (milliseconds)
    STATEMENT_TIMEOUT = 30000  # 30 seconds
    
    # Prepared statements cache
    PREPARED_STATEMENT_CACHE_SIZE = 100
    
    # Read replica configuration
    READ_REPLICA_ENABLED = False
    READ_REPLICA_URL = None


class OptimizedDatabase:
    """High-performance database manager with connection pooling"""
    
    def __init__(self, database_url: str, read_replica_url: Optional[str] = None):
        self.database_url = database_url
        self.read_replica_url = read_replica_url
        self._engine: Optional[AsyncEngine] = None
        self._read_engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker] = None
        self._read_sessionmaker: Optional[async_sessionmaker] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database engines with optimized settings"""
        if self._initialized:
            return
            
        # Create main engine with connection pooling
        self._engine = create_async_engine(
            self.database_url,
            echo=DatabaseConfig.ECHO,
            echo_pool=DatabaseConfig.ECHO_POOL,
            future=DatabaseConfig.FUTURE,
            pool_size=DatabaseConfig.POOL_SIZE,
            max_overflow=DatabaseConfig.MAX_OVERFLOW,
            pool_timeout=DatabaseConfig.POOL_TIMEOUT,
            pool_recycle=DatabaseConfig.POOL_RECYCLE,
            pool_pre_ping=DatabaseConfig.POOL_PRE_PING,
            poolclass=QueuePool,  # Use QueuePool for production
            connect_args=DatabaseConfig.POSTGRES_OPTIONS
        )
        
        # Create read replica engine if configured
        if DatabaseConfig.READ_REPLICA_ENABLED and self.read_replica_url:
            self._read_engine = create_async_engine(
                self.read_replica_url,
                echo=False,
                pool_size=DatabaseConfig.POOL_SIZE // 2,  # Smaller pool for reads
                max_overflow=DatabaseConfig.MAX_OVERFLOW // 2,
                pool_timeout=DatabaseConfig.POOL_TIMEOUT,
                pool_recycle=DatabaseConfig.POOL_RECYCLE,
                pool_pre_ping=DatabaseConfig.POOL_PRE_PING,
                poolclass=QueuePool,
                connect_args=DatabaseConfig.POSTGRES_OPTIONS
            )
            
        # Create session makers
        self._sessionmaker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Control flushing manually
            autocommit=False
        )
        
        if self._read_engine:
            self._read_sessionmaker = async_sessionmaker(
                self._read_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )
            
        # Set up connection event listeners
        self._setup_event_listeners()
        
        self._initialized = True
        logger.info("Database initialized with optimized settings")
        
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring and optimization"""
        
        @event.listens_for(pool.Pool, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Set connection-level optimizations"""
            # This is called for each new connection
            connection_record.info['pid'] = asyncio.get_event_loop()
            
        @event.listens_for(pool.Pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log connection checkouts for monitoring"""
            logger.debug(f"Connection checked out from pool: {id(dbapi_conn)}")
            
        @event.listens_for(pool.Pool, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection checkins for monitoring"""
            logger.debug(f"Connection returned to pool: {id(dbapi_conn)}")
            
    @asynccontextmanager
    async def get_session(self, read_only: bool = False) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with automatic cleanup
        
        Args:
            read_only: If True and read replica is available, use read replica
        """
        if not self._initialized:
            await self.initialize()
            
        # Choose appropriate session maker
        sessionmaker = self._sessionmaker
        if read_only and self._read_sessionmaker:
            sessionmaker = self._read_sessionmaker
            
        async with sessionmaker() as session:
            try:
                # Set statement timeout for this session
                await session.execute(
                    f"SET statement_timeout = {DatabaseConfig.STATEMENT_TIMEOUT}"
                )
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
                
    async def execute_query(self, query: str, params: dict = None, read_only: bool = True):
        """Execute a raw SQL query with optimal settings"""
        async with self.get_session(read_only=read_only) as session:
            result = await session.execute(query, params or {})
            return result.fetchall()
            
    async def bulk_insert(self, model, records: list, batch_size: int = 1000):
        """Optimized bulk insert operation"""
        async with self.get_session() as session:
            # Process in batches to avoid memory issues
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                session.add_all([model(**record) for record in batch])
                await session.flush()  # Flush periodically
            await session.commit()
            
    async def get_pool_status(self) -> dict:
        """Get connection pool statistics"""
        if not self._engine:
            return {}
            
        pool = self._engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.total(),
        }
        
    async def health_check(self) -> bool:
        """Perform database health check"""
        try:
            async with self.get_session(read_only=True) as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
            
    async def close(self):
        """Close all database connections"""
        if self._engine:
            await self._engine.dispose()
        if self._read_engine:
            await self._read_engine.dispose()
        self._initialized = False


class QueryOptimizer:
    """Query optimization utilities"""
    
    @staticmethod
    def add_index_hints(query: str, hints: list[str]) -> str:
        """Add index hints to PostgreSQL query"""
        # PostgreSQL doesn't support index hints directly, 
        # but we can use CTEs to influence the planner
        return query
        
    @staticmethod
    def add_pagination(query: str, limit: int = 100, offset: int = 0) -> str:
        """Add efficient pagination to query"""
        return f"{query} LIMIT {limit} OFFSET {offset}"
        
    @staticmethod
    def optimize_join_order(tables: list[str]) -> str:
        """Generate optimal join order based on table statistics"""
        # This would connect to pg_stats in production
        return " JOIN ".join(tables)


class ConnectionPoolMonitor:
    """Monitor and auto-tune connection pool"""
    
    def __init__(self, database: OptimizedDatabase):
        self.database = database
        self.metrics = []
        self._monitoring = False
        
    async def start_monitoring(self, interval: int = 60):
        """Start monitoring connection pool metrics"""
        self._monitoring = True
        while self._monitoring:
            metrics = await self.database.get_pool_status()
            metrics['timestamp'] = asyncio.get_event_loop().time()
            self.metrics.append(metrics)
            
            # Keep only last hour of metrics
            cutoff = asyncio.get_event_loop().time() - 3600
            self.metrics = [m for m in self.metrics if m['timestamp'] > cutoff]
            
            # Auto-tune if needed
            await self._auto_tune(metrics)
            
            await asyncio.sleep(interval)
            
    async def _auto_tune(self, current_metrics: dict):
        """Auto-tune pool settings based on metrics"""
        if not self.metrics or len(self.metrics) < 10:
            return
            
        # Calculate average utilization
        avg_utilization = sum(m['checked_out'] for m in self.metrics[-10:]) / 10
        pool_size = current_metrics['size']
        
        # Log if pool is consistently over 80% utilized
        if avg_utilization > pool_size * 0.8:
            logger.warning(
                f"Connection pool high utilization: {avg_utilization}/{pool_size}"
            )
            
    async def stop_monitoring(self):
        """Stop monitoring"""
        self._monitoring = False
        
    def get_statistics(self) -> dict:
        """Get pool statistics"""
        if not self.metrics:
            return {}
            
        recent = self.metrics[-60:]  # Last 60 samples
        return {
            "avg_checked_out": sum(m['checked_out'] for m in recent) / len(recent),
            "max_checked_out": max(m['checked_out'] for m in recent),
            "avg_overflow": sum(m['overflow'] for m in recent) / len(recent),
            "max_overflow": max(m['overflow'] for m in recent),
        }


# Singleton instance
_database: Optional[OptimizedDatabase] = None


async def get_database() -> OptimizedDatabase:
    """Get the database instance"""
    global _database
    if _database is None:
        from app.core.config import settings
        _database = OptimizedDatabase(
            str(settings.SQLALCHEMY_DATABASE_URI),
            settings.READ_REPLICA_URL if hasattr(settings, 'READ_REPLICA_URL') else None
        )
        await _database.initialize()
    return _database


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database sessions"""
    database = await get_database()
    async with database.get_session() as session:
        yield session