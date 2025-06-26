"""
ConfigCacheManager - Manages cache invalidation and refresh strategies
Ensures cache consistency across the system
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, timedelta
import json

from core.config.redis_cache import RedisConfigCache


class ConfigCacheManager:
    """Manages configuration cache lifecycle and consistency"""
    
    def __init__(self, cache: RedisConfigCache):
        """Initialize cache manager
        
        Args:
            cache: Redis cache instance
        """
        self.cache = cache
        self.logger = logging.getLogger("ConfigCacheManager")
        
        # Invalidation tracking
        self.invalidation_listeners: List[Callable] = []
        self.department_agents: Dict[str, Set[str]] = {}
        
        # Background tasks
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self) -> None:
        """Start cache manager"""
        self._running = True
        
        # Load department mappings
        await self._load_department_mappings()
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_config_changes())
        
        self.logger.info("Cache manager started")
        
    async def stop(self) -> None:
        """Stop cache manager"""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
                
        self.logger.info("Cache manager stopped")
        
    async def get_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get config through cache manager
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration or None
        """
        return await self.cache.get_config(agent_name)
        
    async def get_configs(self, agent_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple configs efficiently
        
        Args:
            agent_names: List of agent names
            
        Returns:
            Dict mapping agent name to config
        """
        return await self.cache.get_configs(agent_names)
        
    async def invalidate_agent(self, agent_name: str, reason: str = "manual") -> bool:
        """Invalidate specific agent config
        
        Args:
            agent_name: Name of the agent
            reason: Reason for invalidation
            
        Returns:
            True if invalidated
        """
        success = await self.cache.invalidate(agent_name)
        
        if success:
            self.logger.info(f"Invalidated {agent_name} config: {reason}")
            await self._notify_invalidation([agent_name], reason)
            
        return success
        
    async def invalidate_department(self, department: str, reason: str = "department update") -> int:
        """Invalidate all agents in a department
        
        Args:
            department: Department name
            reason: Reason for invalidation
            
        Returns:
            Number of agents invalidated
        """
        agents = self.department_agents.get(department, set())
        count = 0
        
        for agent in agents:
            if await self.cache.invalidate(agent):
                count += 1
                
        if count > 0:
            self.logger.info(f"Invalidated {count} agents in {department}: {reason}")
            await self._notify_invalidation(list(agents), reason)
            
        return count
        
    async def invalidate_all(self, reason: str = "global update") -> int:
        """Invalidate all cached configs
        
        Args:
            reason: Reason for invalidation
            
        Returns:
            Number of entries invalidated
        """
        count = await self.cache.invalidate_all()
        
        if count > 0:
            self.logger.info(f"Invalidated all {count} configs: {reason}")
            await self._notify_invalidation(["*"], reason)
            
        return count
        
    async def refresh_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Force refresh of agent config
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Fresh config or None
        """
        # Invalidate first
        await self.cache.invalidate(agent_name)
        
        # Load fresh
        return await self.cache.get_config(agent_name)
        
    async def refresh_stale_configs(self, max_age_hours: int = 24) -> int:
        """Refresh configs older than specified age
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of configs refreshed
        """
        count = 0
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        # Get all active agents
        from core.config.redis_cache import asyncpg
        
        async with self.cache.pg_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT name, updated_at
                FROM agent_configs
                WHERE is_active = true
            """)
            
            for row in rows:
                if row['updated_at'] < cutoff:
                    config = await self.refresh_agent(row['name'])
                    if config:
                        count += 1
                        
        self.logger.info(f"Refreshed {count} stale configs")
        return count
        
    def add_invalidation_listener(self, callback: Callable) -> None:
        """Add listener for cache invalidation events
        
        Args:
            callback: Function to call on invalidation
        """
        self.invalidation_listeners.append(callback)
        
    def remove_invalidation_listener(self, callback: Callable) -> None:
        """Remove invalidation listener
        
        Args:
            callback: Function to remove
        """
        if callback in self.invalidation_listeners:
            self.invalidation_listeners.remove(callback)
            
    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health metrics"""
        stats = await self.cache.get_cache_stats()
        
        # Add manager-specific metrics
        health = {
            "cache_stats": stats,
            "department_count": len(self.department_agents),
            "total_agents_tracked": sum(len(agents) for agents in self.department_agents.values()),
            "invalidation_listeners": len(self.invalidation_listeners),
            "status": "healthy" if stats.get("hit_rate", 0) > 50 else "degraded"
        }
        
        # Check for issues
        issues = []
        
        if stats.get("hit_rate", 0) < 50:
            issues.append("Low cache hit rate")
            
        if stats.get("errors", 0) > 10:
            issues.append("High error rate")
            
        if stats.get("cached_configs", 0) == 0:
            issues.append("No configs cached")
            
        health["issues"] = issues
        health["healthy"] = len(issues) == 0
        
        return health
        
    async def _load_department_mappings(self) -> None:
        """Load agent to department mappings"""
        try:
            from core.config.redis_cache import asyncpg
            
            async with self.cache.pg_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT name, department
                    FROM agent_configs
                    WHERE is_active = true
                """)
                
                self.department_agents.clear()
                
                for row in rows:
                    dept = row['department']
                    if dept not in self.department_agents:
                        self.department_agents[dept] = set()
                    self.department_agents[dept].add(row['name'])
                    
                self.logger.info(f"Loaded {len(rows)} agent department mappings")
                
        except Exception as e:
            self.logger.error(f"Failed to load department mappings: {e}")
            
    async def _monitor_config_changes(self) -> None:
        """Monitor for config changes in database"""
        check_interval = 60  # Check every minute
        
        while self._running:
            try:
                await asyncio.sleep(check_interval)
                
                # Check for updated configs
                await self._check_config_updates()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                
    async def _check_config_updates(self) -> None:
        """Check for config updates in database"""
        try:
            from core.config.redis_cache import asyncpg
            
            async with self.cache.pg_pool.acquire() as conn:
                # Get configs updated in last check interval
                rows = await conn.fetch("""
                    SELECT name, updated_at
                    FROM agent_configs
                    WHERE updated_at > NOW() - INTERVAL '65 seconds'
                    AND is_active = true
                """)
                
                for row in rows:
                    agent_name = row['name']
                    
                    # Check if cached version is older
                    cached_config = await self.cache.get_config(agent_name)
                    
                    if cached_config:
                        cached_version = cached_config.get('_version', '')
                        
                        # Get current version
                        current_version = await self.cache._get_config_version(conn, agent_name)
                        
                        if cached_version != current_version:
                            # Invalidate outdated config
                            await self.invalidate_agent(agent_name, "database update detected")
                            
        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            
    async def _notify_invalidation(self, agents: List[str], reason: str) -> None:
        """Notify listeners of cache invalidation"""
        event = {
            "type": "cache_invalidation",
            "agents": agents,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        for listener in self.invalidation_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                self.logger.error(f"Listener notification failed: {e}")