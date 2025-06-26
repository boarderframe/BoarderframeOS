"""
Multi-Tenancy with Row Level Security (RLS) for BoarderframeOS
Provides tenant isolation and secure data access
"""

import asyncio
import asyncpg
import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class TenantType(Enum):
    """Types of tenants in the system"""
    ENTERPRISE = "enterprise"
    TEAM = "team"
    INDIVIDUAL = "individual"
    TRIAL = "trial"


class IsolationLevel(Enum):
    """Data isolation levels"""
    STRICT = "strict"          # Complete isolation
    SHARED = "shared"          # Some shared resources
    COLLABORATIVE = "collaborative"  # Cross-tenant collaboration


@dataclass
class Tenant:
    """Tenant information"""
    id: str
    name: str
    type: TenantType
    isolation_level: IsolationLevel
    created_at: datetime
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    # Resource limits
    max_agents: int = 10
    max_departments: int = 5
    max_storage_gb: int = 100
    max_api_calls_per_day: int = 10000
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "advanced_analytics": False,
        "custom_agents": False,
        "api_access": True,
        "data_export": True,
        "cross_tenant_messaging": False
    })


@dataclass
class TenantContext:
    """Context for tenant-aware operations"""
    tenant_id: str
    user_id: Optional[str] = None
    role: str = "user"
    permissions: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    request_id: Optional[str] = None


class MultiTenancyManager:
    """
    Manages multi-tenancy with Row Level Security
    
    Features:
    - Tenant isolation at database level
    - Dynamic RLS policy management
    - Cross-tenant resource sharing (when allowed)
    - Tenant-aware connection pooling
    - Resource quota enforcement
    """
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._pools: Dict[str, asyncpg.Pool] = {}
        self._admin_pool: Optional[asyncpg.Pool] = None
        self._tenants: Dict[str, Tenant] = {}
        self._current_context: Optional[TenantContext] = None
        
    async def initialize(self):
        """Initialize multi-tenancy system"""
        # Create admin connection pool
        self._admin_pool = await asyncpg.create_pool(
            self.db_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        
        # Set up RLS policies
        await self._setup_rls_policies()
        
        # Load existing tenants
        await self._load_tenants()
        
        logger.info("Multi-tenancy manager initialized")
        
    async def _setup_rls_policies(self):
        """Set up Row Level Security policies"""
        async with self._admin_pool.acquire() as conn:
            # Create tenant tables if not exist
            await conn.execute("""
                -- Check if tenants table exists, if not create it
                CREATE TABLE IF NOT EXISTS tenants (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL UNIQUE,
                    status VARCHAR(50) DEFAULT 'active',
                    plan VARCHAR(50) DEFAULT 'free',
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Add columns if they don't exist for multi-tenancy features
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS type TEXT DEFAULT 'team';
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS isolation_level TEXT DEFAULT 'strict';
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}';
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
                
                -- tenant_users should already exist from migrations
                CREATE TABLE IF NOT EXISTS tenant_users (
                    tenant_id UUID REFERENCES tenants(id),
                    user_id UUID NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    permissions TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, user_id)
                );
                
                CREATE TABLE IF NOT EXISTS tenant_resources (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID REFERENCES tenants(id),
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    shared_with TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tenant_id, resource_type, resource_id)
                );
            """)
            
            # Add tenant_id to existing tables
            tables_to_update = [
                'agents', 'departments', 'messages', 'agent_configs',
                'agent_states', 'llm_usage', 'audit_logs'
            ]
            
            for table in tables_to_update:
                # Check if table exists
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = $1
                    )
                """, table)
                
                if exists:
                    # Check if tenant_id column exists
                    has_tenant_id = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = $1 AND column_name = 'tenant_id'
                        )
                    """, table)
                    
                    if not has_tenant_id:
                        # Add tenant_id column
                        await conn.execute(f"""
                            ALTER TABLE {table} 
                            ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000000'::uuid;
                            
                            CREATE INDEX IF NOT EXISTS idx_{table}_tenant_id 
                            ON {table}(tenant_id);
                        """)
                        
                    # Enable RLS
                    await conn.execute(f"""
                        ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
                        
                        -- Drop existing policies if any
                        DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};
                        DROP POLICY IF EXISTS {table}_tenant_insert ON {table};
                        
                        -- Create select policy
                        CREATE POLICY {table}_tenant_isolation ON {table}
                            FOR SELECT
                            USING (
                                tenant_id = current_setting('app.current_tenant_id', true)::uuid
                                OR 
                                tenant_id = ANY(
                                    string_to_array(
                                        current_setting('app.allowed_tenant_ids', true), 
                                        ','
                                    )::uuid[]
                                )
                            );
                        
                        -- Create insert/update/delete policy
                        CREATE POLICY {table}_tenant_insert ON {table}
                            FOR ALL
                            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
                            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
                    """)
            
            logger.info("Row Level Security policies configured")
            
    async def _load_tenants(self):
        """Load existing tenants from database"""
        async with self._admin_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tenants WHERE is_active = TRUE")
            
            for row in rows:
                tenant = Tenant(
                    id=row['id'],
                    name=row['name'],
                    type=TenantType(row['type']),
                    isolation_level=IsolationLevel(row['isolation_level']),
                    created_at=row['created_at'],
                    settings=row['settings'] or {},
                    metadata=row['metadata'] or {},
                    is_active=row['is_active']
                )
                self._tenants[tenant.id] = tenant
                
    async def ensure_default_tenant(self) -> Optional[Tenant]:
        """Ensure default tenant exists"""
        default_tenant_id = "00000000-0000-0000-0000-000000000000"
        
        # Check if default tenant already exists
        if default_tenant_id in self._tenants:
            return self._tenants[default_tenant_id]
            
        # Check in database
        async with self._admin_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tenants WHERE id = $1", default_tenant_id)
            
            if row:
                tenant = Tenant(
                    id=row['id'],
                    name=row['name'],
                    type=TenantType(row['type']),
                    isolation_level=IsolationLevel(row['isolation_level']),
                    created_at=row['created_at'],
                    settings=row['settings'] or {},
                    metadata=row['metadata'] or {},
                    is_active=row['is_active']
                )
                self._tenants[tenant.id] = tenant
                return tenant
                
        # Create default tenant
        return await self.create_tenant(
            name="Default",
            type=TenantType.ENTERPRISE,
            isolation_level=IsolationLevel.STRICT,
            id=default_tenant_id
        )
    
    async def create_tenant(self, name: str, type: TenantType, 
                          isolation_level: IsolationLevel = IsolationLevel.STRICT,
                          **kwargs) -> Tenant:
        """Create a new tenant"""
        tenant_id = kwargs.get('id', str(uuid.uuid4()))
        
        tenant = Tenant(
            id=tenant_id,
            name=name,
            type=type,
            isolation_level=isolation_level,
            created_at=datetime.now(),
            **kwargs
        )
        
        async with self._admin_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tenants (id, name, type, isolation_level, settings, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, tenant.id, tenant.name, tenant.type.value, 
                tenant.isolation_level.value, 
                json.dumps(tenant.settings),
                json.dumps(tenant.metadata))
            
            # Create default admin user
            await conn.execute("""
                INSERT INTO tenant_users (tenant_id, user_id, role, permissions)
                VALUES ($1, $2, 'admin', ARRAY['*'])
            """, tenant.id, f"{tenant.id}-admin")
            
        self._tenants[tenant.id] = tenant
        logger.info(f"Created tenant: {tenant.name} ({tenant.id})")
        
        # Initialize tenant resources
        await self._initialize_tenant_resources(tenant)
        
        return tenant
        
    async def _initialize_tenant_resources(self, tenant: Tenant):
        """Initialize resources for a new tenant"""
        async with self.get_tenant_connection(tenant.id) as conn:
            # Create default department
            await conn.execute("""
                INSERT INTO departments (id, name, description, tenant_id)
                VALUES ($1, 'Executive', 'Executive Department', $2)
            """, str(uuid.uuid4()), tenant.id)
            
            # Initialize default agents based on tenant type
            if tenant.type == TenantType.ENTERPRISE:
                # Create full agent suite
                default_agents = ['Solomon', 'David', 'Adam', 'Eve', 'Bezalel']
            elif tenant.type == TenantType.TEAM:
                # Create essential agents
                default_agents = ['Solomon', 'David']
            else:
                # Create minimal setup
                default_agents = ['Solomon']
                
            for agent_name in default_agents:
                await conn.execute("""
                    INSERT INTO agents (id, name, type, status, tenant_id)
                    VALUES ($1, $2, 'executive', 'active', $3)
                """, str(uuid.uuid4()), agent_name, tenant.id)
                
    @asynccontextmanager
    async def get_tenant_connection(self, tenant_id: str):
        """Get a tenant-scoped database connection"""
        if tenant_id not in self._tenants:
            raise ValueError(f"Unknown tenant: {tenant_id}")
            
        # Get or create tenant connection pool
        if tenant_id not in self._pools:
            self._pools[tenant_id] = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=20,
                init=self._init_tenant_connection,
                server_settings={
                    'app.current_tenant_id': tenant_id,
                    'app.allowed_tenant_ids': tenant_id
                }
            )
            
        pool = self._pools[tenant_id]
        async with pool.acquire() as conn:
            # Set tenant context
            await conn.execute(f"SET app.current_tenant_id = '{tenant_id}'")
            await conn.execute(f"SET app.allowed_tenant_ids = '{tenant_id}'")
            yield conn
            
    async def _init_tenant_connection(self, conn):
        """Initialize tenant connection with RLS settings"""
        # This is called when a new connection is created in the pool
        pass
        
    def set_current_context(self, context: TenantContext):
        """Set current tenant context for operations"""
        self._current_context = context
        
    def get_current_context(self) -> Optional[TenantContext]:
        """Get current tenant context"""
        return self._current_context
        
    @asynccontextmanager
    async def with_tenant_context(self, tenant_id: str, user_id: Optional[str] = None):
        """Context manager for tenant-scoped operations"""
        previous_context = self._current_context
        
        context = TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
        
        self._current_context = context
        
        try:
            yield context
        finally:
            self._current_context = previous_context
            
    async def share_resource(self, tenant_id: str, resource_type: str, 
                           resource_id: str, target_tenant_ids: List[str]):
        """Share a resource with other tenants"""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Unknown tenant: {tenant_id}")
            
        if tenant.isolation_level == IsolationLevel.STRICT:
            raise ValueError("Tenant has strict isolation - cannot share resources")
            
        if not tenant.features.get("cross_tenant_messaging", False):
            raise ValueError("Cross-tenant messaging not enabled for this tenant")
            
        async with self._admin_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tenant_resources (id, tenant_id, resource_type, resource_id, shared_with)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (tenant_id, resource_type, resource_id)
                DO UPDATE SET shared_with = EXCLUDED.shared_with
            """, str(uuid.uuid4()), tenant_id, resource_type, resource_id, target_tenant_ids)
            
    async def get_shared_resources(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get resources shared with a tenant"""
        async with self._admin_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM tenant_resources 
                WHERE $1 = ANY(shared_with)
            """, tenant_id)
            
            return [dict(row) for row in rows]
            
    async def check_resource_quota(self, tenant_id: str, resource_type: str) -> bool:
        """Check if tenant has quota for a resource"""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
            
        async with self.get_tenant_connection(tenant_id) as conn:
            if resource_type == "agents":
                count = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE tenant_id = $1", tenant_id)
                return count < tenant.max_agents
                
            elif resource_type == "departments":
                count = await conn.fetchval("SELECT COUNT(*) FROM departments WHERE tenant_id = $1", tenant_id)
                return count < tenant.max_departments
                
            elif resource_type == "api_calls":
                # Check daily API call limit
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM api_calls 
                    WHERE tenant_id = $1 AND created_at >= $2
                """, tenant_id, today_start)
                return count < tenant.max_api_calls_per_day
                
        return True
        
    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get resource usage for a tenant"""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Unknown tenant: {tenant_id}")
            
        async with self.get_tenant_connection(tenant_id) as conn:
            # Get counts
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE tenant_id = $1", tenant_id)
            dept_count = await conn.fetchval("SELECT COUNT(*) FROM departments WHERE tenant_id = $1", tenant_id)
            
            # Get storage usage (simplified)
            storage_mb = await conn.fetchval("""
                SELECT SUM(pg_column_size(t.*)) / 1024 / 1024 as size_mb
                FROM (
                    SELECT * FROM agents WHERE tenant_id = $1
                    UNION ALL
                    SELECT * FROM messages WHERE tenant_id = $1
                ) t
            """, tenant_id) or 0
            
            # Get API usage
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            api_calls_today = await conn.fetchval("""
                SELECT COUNT(*) FROM api_calls 
                WHERE tenant_id = $1 AND created_at >= $2
            """, tenant_id, today_start) or 0
            
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "agents": {
                "used": agent_count,
                "limit": tenant.max_agents,
                "percentage": (agent_count / tenant.max_agents * 100) if tenant.max_agents > 0 else 0
            },
            "departments": {
                "used": dept_count,
                "limit": tenant.max_departments,
                "percentage": (dept_count / tenant.max_departments * 100) if tenant.max_departments > 0 else 0
            },
            "storage": {
                "used_gb": storage_mb / 1024,
                "limit_gb": tenant.max_storage_gb,
                "percentage": (storage_mb / 1024 / tenant.max_storage_gb * 100) if tenant.max_storage_gb > 0 else 0
            },
            "api_calls": {
                "today": api_calls_today,
                "daily_limit": tenant.max_api_calls_per_day,
                "percentage": (api_calls_today / tenant.max_api_calls_per_day * 100) if tenant.max_api_calls_per_day > 0 else 0
            }
        }
        
    async def migrate_to_tenant(self, tenant_id: str, table: str, 
                              where_clause: str = "1=1", 
                              update_refs: bool = True):
        """Migrate existing data to a tenant"""
        async with self._admin_pool.acquire() as conn:
            # Update records
            await conn.execute(f"""
                UPDATE {table} 
                SET tenant_id = $1 
                WHERE tenant_id IS NULL AND {where_clause}
            """, tenant_id)
            
            if update_refs:
                # Update related tables based on common patterns
                if table == "agents":
                    await conn.execute("""
                        UPDATE agent_configs 
                        SET tenant_id = $1 
                        WHERE agent_id IN (
                            SELECT id FROM agents WHERE tenant_id = $1
                        )
                    """, tenant_id)
                    
                    await conn.execute("""
                        UPDATE agent_states 
                        SET tenant_id = $1 
                        WHERE agent_id IN (
                            SELECT id FROM agents WHERE tenant_id = $1
                        )
                    """, tenant_id)
                    
    async def cleanup_tenant(self, tenant_id: str, hard_delete: bool = False):
        """Clean up tenant data"""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Unknown tenant: {tenant_id}")
            
        async with self._admin_pool.acquire() as conn:
            if hard_delete:
                # Delete all tenant data
                tables = ['messages', 'agent_states', 'agent_configs', 'agents', 'departments']
                for table in tables:
                    await conn.execute(f"DELETE FROM {table} WHERE tenant_id = $1", tenant_id)
                    
                # Delete tenant
                await conn.execute("DELETE FROM tenants WHERE id = $1", tenant_id)
                
                # Remove from cache
                del self._tenants[tenant_id]
                
                # Close and remove pool
                if tenant_id in self._pools:
                    await self._pools[tenant_id].close()
                    del self._pools[tenant_id]
            else:
                # Soft delete - mark as inactive
                await conn.execute("""
                    UPDATE tenants 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = $1
                """, tenant_id)
                
                self._tenants[tenant_id].is_active = False
                
    async def shutdown(self):
        """Shutdown multi-tenancy manager"""
        # Close all tenant pools
        for pool in self._pools.values():
            await pool.close()
            
        # Close admin pool
        if self._admin_pool:
            await self._admin_pool.close()
            
        logger.info("Multi-tenancy manager shut down")


# Global multi-tenancy manager instance
_mt_manager = None


def get_multi_tenancy_manager() -> MultiTenancyManager:
    """Get the global multi-tenancy manager instance"""
    global _mt_manager
    if _mt_manager is None:
        db_url = "postgresql://boarderframe:boarderframe123@localhost:5434/boarderframeos"
        _mt_manager = MultiTenancyManager(db_url)
    return _mt_manager


# Decorators for tenant-aware operations
def tenant_aware(func):
    """Decorator to ensure operations are tenant-scoped"""
    async def wrapper(*args, **kwargs):
        mt_manager = get_multi_tenancy_manager()
        context = mt_manager.get_current_context()
        
        if not context:
            raise ValueError("No tenant context set")
            
        # Add tenant_id to kwargs if not present
        if 'tenant_id' not in kwargs:
            kwargs['tenant_id'] = context.tenant_id
            
        return await func(*args, **kwargs)
        
    return wrapper


def require_permission(permission: str):
    """Decorator to check permissions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            mt_manager = get_multi_tenancy_manager()
            context = mt_manager.get_current_context()
            
            if not context:
                raise ValueError("No tenant context set")
                
            if permission not in context.permissions and '*' not in context.permissions:
                raise PermissionError(f"Permission denied: {permission}")
                
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator