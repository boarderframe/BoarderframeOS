"""
ConfigVersionManager - Tracks config versions and enables rollback
Maintains audit trail of all configuration changes
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import asyncpg
from dataclasses import dataclass, asdict


@dataclass
class ConfigVersion:
    """Represents a configuration version"""
    version_id: str
    agent_name: str
    config_data: Dict[str, Any]
    created_at: datetime
    created_by: str
    change_type: str  # create, update, delete
    change_reason: str
    previous_version_id: Optional[str] = None
    is_current: bool = True


class ConfigVersionManager:
    """Manages configuration versioning and history"""
    
    def __init__(self, postgres_dsn: str):
        """Initialize version manager
        
        Args:
            postgres_dsn: PostgreSQL connection string
        """
        self.postgres_dsn = postgres_dsn
        self.logger = logging.getLogger("ConfigVersionManager")
        self.pg_pool: Optional[asyncpg.Pool] = None
        
        # Version cache for quick lookups
        self.version_cache: Dict[str, List[ConfigVersion]] = {}
        self.max_cache_size = 1000
        
    async def initialize(self) -> None:
        """Initialize version manager and create tables"""
        # Create connection pool
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_dsn,
            min_size=2,
            max_size=10
        )
        
        # Create version table if not exists
        await self._create_version_table()
        
        self.logger.info("Version manager initialized")
        
    async def _create_version_table(self) -> None:
        """Create agent config version table"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_config_versions (
                    version_id VARCHAR(64) PRIMARY KEY,
                    agent_name VARCHAR(100) NOT NULL,
                    config_data JSONB NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100) NOT NULL,
                    change_type VARCHAR(20) NOT NULL,
                    change_reason TEXT,
                    previous_version_id VARCHAR(64),
                    is_current BOOLEAN DEFAULT true,
                    
                    -- Indexes
                    CONSTRAINT fk_previous_version 
                        FOREIGN KEY (previous_version_id) 
                        REFERENCES agent_config_versions(version_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_acv_agent_name 
                    ON agent_config_versions(agent_name);
                    
                CREATE INDEX IF NOT EXISTS idx_acv_created_at 
                    ON agent_config_versions(created_at);
                    
                CREATE INDEX IF NOT EXISTS idx_acv_is_current 
                    ON agent_config_versions(agent_name, is_current);
            """)
            
    async def save_version(
        self,
        agent_name: str,
        config: Dict[str, Any],
        created_by: str,
        change_type: str,
        change_reason: str
    ) -> ConfigVersion:
        """Save a new configuration version
        
        Args:
            agent_name: Name of the agent
            config: Configuration data
            created_by: User/system making the change
            change_type: Type of change (create, update, delete)
            change_reason: Reason for the change
            
        Returns:
            Created ConfigVersion
        """
        # Generate version ID
        version_id = self._generate_version_id(agent_name, config)
        
        # Get current version
        current_version = await self.get_current_version(agent_name)
        previous_version_id = current_version.version_id if current_version else None
        
        # Create version object
        version = ConfigVersion(
            version_id=version_id,
            agent_name=agent_name,
            config_data=config,
            created_at=datetime.now(),
            created_by=created_by,
            change_type=change_type,
            change_reason=change_reason,
            previous_version_id=previous_version_id,
            is_current=True
        )
        
        async with self.pg_pool.acquire() as conn:
            async with conn.transaction():
                # Mark previous versions as not current
                await conn.execute("""
                    UPDATE agent_config_versions
                    SET is_current = false
                    WHERE agent_name = $1 AND is_current = true
                """, agent_name)
                
                # Insert new version
                await conn.execute("""
                    INSERT INTO agent_config_versions (
                        version_id, agent_name, config_data, created_at,
                        created_by, change_type, change_reason,
                        previous_version_id, is_current
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    version.version_id,
                    version.agent_name,
                    json.dumps(version.config_data),
                    version.created_at,
                    version.created_by,
                    version.change_type,
                    version.change_reason,
                    version.previous_version_id,
                    version.is_current
                )
                
                # Update main config table
                await self._update_main_config(conn, agent_name, config)
                
        # Update cache
        self._update_cache(agent_name, version)
        
        self.logger.info(
            f"Saved version {version_id} for {agent_name}: {change_type} - {change_reason}"
        )
        
        return version
        
    async def get_version(self, version_id: str) -> Optional[ConfigVersion]:
        """Get specific version by ID
        
        Args:
            version_id: Version identifier
            
        Returns:
            ConfigVersion or None
        """
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM agent_config_versions
                WHERE version_id = $1
            """, version_id)
            
            if row:
                return self._row_to_version(row)
                
        return None
        
    async def get_current_version(self, agent_name: str) -> Optional[ConfigVersion]:
        """Get current version for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Current ConfigVersion or None
        """
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM agent_config_versions
                WHERE agent_name = $1 AND is_current = true
                LIMIT 1
            """, agent_name)
            
            if row:
                return self._row_to_version(row)
                
        return None
        
    async def get_version_history(
        self,
        agent_name: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConfigVersion]:
        """Get version history for an agent
        
        Args:
            agent_name: Name of the agent
            limit: Maximum versions to return
            offset: Offset for pagination
            
        Returns:
            List of ConfigVersions
        """
        # Check cache first
        if agent_name in self.version_cache and offset == 0:
            cached = self.version_cache[agent_name]
            return cached[:limit]
            
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM agent_config_versions
                WHERE agent_name = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """, agent_name, limit, offset)
            
            versions = [self._row_to_version(row) for row in rows]
            
            # Cache first page
            if offset == 0:
                self.version_cache[agent_name] = versions
                self._manage_cache_size()
                
            return versions
            
    async def rollback_to_version(
        self,
        agent_name: str,
        version_id: str,
        rollback_by: str,
        reason: str
    ) -> ConfigVersion:
        """Rollback to a specific version
        
        Args:
            agent_name: Name of the agent
            version_id: Version to rollback to
            rollback_by: User performing rollback
            reason: Reason for rollback
            
        Returns:
            New ConfigVersion created from rollback
        """
        # Get target version
        target_version = await self.get_version(version_id)
        
        if not target_version:
            raise ValueError(f"Version {version_id} not found")
            
        if target_version.agent_name != agent_name:
            raise ValueError(f"Version {version_id} does not belong to agent {agent_name}")
            
        # Create new version with old config
        rollback_version = await self.save_version(
            agent_name=agent_name,
            config=target_version.config_data,
            created_by=rollback_by,
            change_type="rollback",
            change_reason=f"Rollback to version {version_id}: {reason}"
        )
        
        self.logger.info(
            f"Rolled back {agent_name} to version {version_id}"
        )
        
        return rollback_version
        
    async def get_config_diff(
        self,
        version_id1: str,
        version_id2: str
    ) -> Dict[str, Any]:
        """Get differences between two versions
        
        Args:
            version_id1: First version ID
            version_id2: Second version ID
            
        Returns:
            Dict with differences
        """
        v1 = await self.get_version(version_id1)
        v2 = await self.get_version(version_id2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
            
        diff = {
            "version1": {
                "id": v1.version_id,
                "created_at": v1.created_at.isoformat(),
                "created_by": v1.created_by
            },
            "version2": {
                "id": v2.version_id,
                "created_at": v2.created_at.isoformat(),
                "created_by": v2.created_by
            },
            "changes": self._compute_diff(v1.config_data, v2.config_data)
        }
        
        return diff
        
    async def cleanup_old_versions(
        self,
        days_to_keep: int = 90,
        keep_minimum: int = 10
    ) -> int:
        """Clean up old versions
        
        Args:
            days_to_keep: Keep versions newer than this
            keep_minimum: Minimum versions to keep per agent
            
        Returns:
            Number of versions deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        async with self.pg_pool.acquire() as conn:
            # Get agents with versions to clean
            agents = await conn.fetch("""
                SELECT agent_name, COUNT(*) as version_count
                FROM agent_config_versions
                GROUP BY agent_name
                HAVING COUNT(*) > $1
            """, keep_minimum)
            
            total_deleted = 0
            
            for agent_row in agents:
                agent_name = agent_row['agent_name']
                
                # Delete old versions, keeping minimum
                result = await conn.execute("""
                    DELETE FROM agent_config_versions
                    WHERE agent_name = $1
                    AND created_at < $2
                    AND is_current = false
                    AND version_id NOT IN (
                        SELECT version_id
                        FROM agent_config_versions
                        WHERE agent_name = $1
                        ORDER BY created_at DESC
                        LIMIT $3
                    )
                """, agent_name, cutoff_date, keep_minimum)
                
                deleted = int(result.split()[-1])
                total_deleted += deleted
                
        self.logger.info(f"Cleaned up {total_deleted} old versions")
        return total_deleted
        
    async def get_change_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get summary of changes in date range
        
        Args:
            start_date: Start of range
            end_date: End of range
            
        Returns:
            Summary statistics
        """
        async with self.pg_pool.acquire() as conn:
            # Get change counts by type
            type_counts = await conn.fetch("""
                SELECT change_type, COUNT(*) as count
                FROM agent_config_versions
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY change_type
            """, start_date, end_date)
            
            # Get changes by agent
            agent_counts = await conn.fetch("""
                SELECT agent_name, COUNT(*) as count
                FROM agent_config_versions
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY agent_name
                ORDER BY count DESC
                LIMIT 10
            """, start_date, end_date)
            
            # Get active changers
            changer_counts = await conn.fetch("""
                SELECT created_by, COUNT(*) as count
                FROM agent_config_versions
                WHERE created_at BETWEEN $1 AND $2
                GROUP BY created_by
                ORDER BY count DESC
                LIMIT 10
            """, start_date, end_date)
            
        return {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "changes_by_type": {row['change_type']: row['count'] for row in type_counts},
            "top_changed_agents": [
                {"agent": row['agent_name'], "changes": row['count']}
                for row in agent_counts
            ],
            "top_changers": [
                {"user": row['created_by'], "changes": row['count']}
                for row in changer_counts
            ]
        }
        
    def _generate_version_id(self, agent_name: str, config: Dict[str, Any]) -> str:
        """Generate unique version ID"""
        # Combine agent name, config, and timestamp
        content = f"{agent_name}:{json.dumps(config, sort_keys=True)}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
        
    def _row_to_version(self, row: asyncpg.Record) -> ConfigVersion:
        """Convert database row to ConfigVersion"""
        return ConfigVersion(
            version_id=row['version_id'],
            agent_name=row['agent_name'],
            config_data=json.loads(row['config_data']),
            created_at=row['created_at'],
            created_by=row['created_by'],
            change_type=row['change_type'],
            change_reason=row['change_reason'] or "",
            previous_version_id=row['previous_version_id'],
            is_current=row['is_current']
        )
        
    async def _update_main_config(
        self,
        conn: asyncpg.Connection,
        agent_name: str,
        config: Dict[str, Any]
    ) -> None:
        """Update main agent_configs table"""
        await conn.execute("""
            UPDATE agent_configs
            SET 
                role = $2,
                department = $3,
                personality = $4,
                goals = $5,
                tools = $6,
                llm_model = $7,
                temperature = $8,
                max_tokens = $9,
                system_prompt = $10,
                context_prompt = $11,
                priority_level = $12,
                compute_allocation = $13,
                memory_limit_gb = $14,
                max_concurrent_tasks = $15,
                is_active = $16,
                development_status = $17,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = $1
        """,
            agent_name,
            config.get('role'),
            config.get('department'),
            json.dumps(config.get('personality', {})),
            config.get('goals', []),
            config.get('tools', []),
            config.get('llm_model', 'claude-3-sonnet'),
            config.get('temperature', 0.7),
            config.get('max_tokens', 4096),
            config.get('system_prompt', ''),
            config.get('context_prompt'),
            config.get('priority_level', 5),
            config.get('compute_allocation', 5.0),
            config.get('memory_limit_gb', 8.0),
            config.get('max_concurrent_tasks', 5),
            config.get('is_active', True),
            config.get('development_status', 'planned')
        )
        
    def _update_cache(self, agent_name: str, version: ConfigVersion) -> None:
        """Update version cache"""
        if agent_name not in self.version_cache:
            self.version_cache[agent_name] = []
            
        # Add to front of list
        self.version_cache[agent_name].insert(0, version)
        
        # Limit cache size per agent
        if len(self.version_cache[agent_name]) > 50:
            self.version_cache[agent_name] = self.version_cache[agent_name][:50]
            
    def _manage_cache_size(self) -> None:
        """Manage overall cache size"""
        if len(self.version_cache) > self.max_cache_size:
            # Remove least recently used
            oldest_agents = sorted(
                self.version_cache.keys(),
                key=lambda k: min(v.created_at for v in self.version_cache[k])
            )
            
            for agent in oldest_agents[:len(oldest_agents) // 4]:
                del self.version_cache[agent]
                
    def _compute_diff(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """Compute differences between configs"""
        diff = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # Find added and modified
        for key, value in config2.items():
            if key not in config1:
                diff["added"][key] = value
            elif config1[key] != value:
                diff["modified"][key] = {
                    "old": config1[key],
                    "new": value
                }
                
        # Find removed
        for key, value in config1.items():
            if key not in config2:
                diff["removed"][key] = value
                
        return diff
        
    async def cleanup(self) -> None:
        """Cleanup version manager resources"""
        if self.pg_pool:
            await self.pg_pool.close()
            
        self.version_cache.clear()
        self.logger.info("Version manager cleanup complete")