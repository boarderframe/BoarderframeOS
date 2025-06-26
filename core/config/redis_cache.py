"""
RedisConfigCache - High-performance agent config caching
Provides millisecond lookups with automatic refresh
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
import hashlib
import redis.asyncio as redis
from redis.asyncio.lock import Lock as RedisLock
import asyncpg


class RedisConfigCache:
    """Redis-based configuration cache for agent configs"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        postgres_dsn: str = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos",
        ttl_seconds: int = 300,  # 5 minutes
        refresh_threshold: float = 0.8  # Refresh when 80% of TTL reached
    ):
        """Initialize Redis config cache
        
        Args:
            redis_url: Redis connection URL
            postgres_dsn: PostgreSQL connection string
            ttl_seconds: Cache TTL in seconds
            refresh_threshold: When to trigger background refresh (0.8 = 80% of TTL)
        """
        self.redis_url = redis_url
        self.postgres_dsn = postgres_dsn
        self.ttl_seconds = ttl_seconds
        self.refresh_threshold = refresh_threshold
        
        self.logger = logging.getLogger("RedisConfigCache")
        self.redis_client: Optional[redis.Redis] = None
        self.pg_pool: Optional[asyncpg.Pool] = None
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "refreshes": 0,
            "errors": 0
        }
        
        # Background refresh tracking
        self._refresh_tasks: Dict[str, asyncio.Task] = {}
        self._refresh_lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize cache connections"""
        # Connect to Redis
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test Redis connection
        await self.redis_client.ping()
        self.logger.info("Connected to Redis")
        
        # Create PostgreSQL connection pool
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_dsn,
            min_size=2,
            max_size=10
        )
        self.logger.info("PostgreSQL pool created")
        
        # Warm cache with active agents
        await self._warm_cache()
        
    async def get_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration with cache
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dict or None
        """
        cache_key = f"agent:config:{agent_name}"
        
        # Try cache first
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            self.stats["hits"] += 1
            config = json.loads(cached_data)
            
            # Check if refresh needed
            cache_age = await self._get_cache_age(cache_key)
            if cache_age and cache_age > (self.ttl_seconds * self.refresh_threshold):
                # Trigger background refresh
                await self._trigger_refresh(agent_name)
                
            return config
            
        else:
            self.stats["misses"] += 1
            
            # Load from database
            config = await self._load_from_database(agent_name)
            
            if config:
                # Store in cache
                await self._set_cache(cache_key, config)
                
            return config
            
    async def get_configs(self, agent_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get multiple agent configurations efficiently
        
        Args:
            agent_names: List of agent names
            
        Returns:
            Dict mapping agent name to config
        """
        # Build cache keys
        cache_keys = [f"agent:config:{name}" for name in agent_names]
        
        # Multi-get from Redis
        cached_values = await self.redis_client.mget(cache_keys)
        
        results = {}
        missing_agents = []
        
        for i, (name, cached) in enumerate(zip(agent_names, cached_values)):
            if cached:
                self.stats["hits"] += 1
                results[name] = json.loads(cached)
                
                # Check refresh
                cache_age = await self._get_cache_age(cache_keys[i])
                if cache_age and cache_age > (self.ttl_seconds * self.refresh_threshold):
                    await self._trigger_refresh(name)
            else:
                self.stats["misses"] += 1
                missing_agents.append(name)
                
        # Load missing from database
        if missing_agents:
            db_configs = await self._load_multiple_from_database(missing_agents)
            
            for name, config in db_configs.items():
                if config:
                    results[name] = config
                    await self._set_cache(f"agent:config:{name}", config)
                else:
                    results[name] = None
                    
        return results
        
    async def invalidate(self, agent_name: str) -> bool:
        """Invalidate cached config for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            True if cache was invalidated
        """
        cache_key = f"agent:config:{agent_name}"
        deleted = await self.redis_client.delete(cache_key)
        
        # Cancel any pending refresh
        if agent_name in self._refresh_tasks:
            self._refresh_tasks[agent_name].cancel()
            del self._refresh_tasks[agent_name]
            
        self.logger.info(f"Invalidated cache for {agent_name}")
        return bool(deleted)
        
    async def invalidate_all(self) -> int:
        """Invalidate all cached configs
        
        Returns:
            Number of entries invalidated
        """
        pattern = "agent:config:*"
        
        # Find all config keys
        cursor = 0
        keys_deleted = 0
        
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor, match=pattern, count=100
            )
            
            if keys:
                keys_deleted += await self.redis_client.delete(*keys)
                
            if cursor == 0:
                break
                
        # Cancel all refresh tasks
        for task in self._refresh_tasks.values():
            task.cancel()
        self._refresh_tasks.clear()
        
        self.logger.info(f"Invalidated {keys_deleted} cached configs")
        return keys_deleted
        
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Count cached entries
        cursor = 0
        cached_count = 0
        
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor, match="agent:config:*", count=100
            )
            cached_count += len(keys)
            
            if cursor == 0:
                break
                
        return {
            "total_requests": total_requests,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "refreshes": self.stats["refreshes"],
            "errors": self.stats["errors"],
            "cached_configs": cached_count,
            "active_refresh_tasks": len(self._refresh_tasks)
        }
        
    async def _warm_cache(self) -> None:
        """Warm cache with active agent configs"""
        try:
            async with self.pg_pool.acquire() as conn:
                # Get all active agents
                rows = await conn.fetch("""
                    SELECT name 
                    FROM agent_configs 
                    WHERE is_active = true
                """)
                
                agent_names = [row['name'] for row in rows]
                
                # Load all configs
                if agent_names:
                    await self.get_configs(agent_names)
                    self.logger.info(f"Warmed cache with {len(agent_names)} agent configs")
                    
        except Exception as e:
            self.logger.error(f"Cache warming failed: {e}")
            self.stats["errors"] += 1
            
    async def _load_from_database(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load agent config from database"""
        try:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT agent_id, config FROM get_agent_config($1)",
                    agent_name
                )
                
                if row:
                    config = json.loads(row['config'])
                    config['_loaded_at'] = datetime.now().isoformat()
                    config['_version'] = await self._get_config_version(conn, agent_name)
                    return config
                    
        except Exception as e:
            self.logger.error(f"Database load failed for {agent_name}: {e}")
            self.stats["errors"] += 1
            
        return None
        
    async def _load_multiple_from_database(self, agent_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Load multiple agent configs from database"""
        results = {}
        
        try:
            async with self.pg_pool.acquire() as conn:
                # Use a single query for all agents
                query = """
                    SELECT name, agent_id, 
                           jsonb_build_object(
                               'name', name,
                               'role', role,
                               'department', department,
                               'personality', personality,
                               'goals', goals,
                               'tools', tools,
                               'llm_model', llm_model,
                               'temperature', temperature,
                               'max_tokens', max_tokens,
                               'system_prompt', system_prompt,
                               'context_prompt', context_prompt,
                               'priority_level', priority_level,
                               'compute_allocation', compute_allocation,
                               'memory_limit_gb', memory_limit_gb,
                               'max_concurrent_tasks', max_concurrent_tasks,
                               'is_active', is_active
                           ) as config
                    FROM agent_configs
                    WHERE name = ANY($1) AND is_active = true
                """
                
                rows = await conn.fetch(query, agent_names)
                
                for row in rows:
                    # row['config'] is already a dict from JSONB
                    if isinstance(row['config'], dict):
                        config = row['config'].copy()
                    else:
                        # If it's a string, parse it
                        config = json.loads(row['config']) if isinstance(row['config'], str) else {}
                    
                    config['_loaded_at'] = datetime.now().isoformat()
                    config['_version'] = await self._get_config_version(conn, row['name'])
                    results[row['name']] = config
                    
                # Mark missing agents
                for name in agent_names:
                    if name not in results:
                        results[name] = None
                        
        except Exception as e:
            self.logger.error(f"Batch database load failed: {e}")
            self.stats["errors"] += 1
            
            # Return None for all on error
            for name in agent_names:
                results[name] = None
                
        return results
        
    async def _set_cache(self, cache_key: str, config: Dict[str, Any]) -> None:
        """Set cache entry with TTL"""
        try:
            await self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(config)
            )
        except Exception as e:
            self.logger.error(f"Cache set failed for {cache_key}: {e}")
            self.stats["errors"] += 1
            
    async def _get_cache_age(self, cache_key: str) -> Optional[float]:
        """Get age of cache entry in seconds"""
        try:
            ttl = await self.redis_client.ttl(cache_key)
            if ttl > 0:
                return self.ttl_seconds - ttl
        except Exception as e:
            self.logger.error(f"TTL check failed for {cache_key}: {e}")
            
        return None
        
    async def _trigger_refresh(self, agent_name: str) -> None:
        """Trigger background refresh for agent config"""
        async with self._refresh_lock:
            # Check if refresh already in progress
            if agent_name in self._refresh_tasks:
                if not self._refresh_tasks[agent_name].done():
                    return  # Already refreshing
                    
            # Start refresh task
            task = asyncio.create_task(self._refresh_config(agent_name))
            self._refresh_tasks[agent_name] = task
            
    async def _refresh_config(self, agent_name: str) -> None:
        """Background task to refresh config"""
        try:
            self.logger.debug(f"Refreshing config for {agent_name}")
            
            # Use Redis lock to prevent stampede
            lock_key = f"agent:config:refresh:{agent_name}"
            lock = RedisLock(self.redis_client, lock_key, timeout=10)
            
            async with lock:
                # Double-check if refresh still needed
                cache_key = f"agent:config:{agent_name}"
                cache_age = await self._get_cache_age(cache_key)
                
                if cache_age and cache_age < (self.ttl_seconds * self.refresh_threshold):
                    return  # Another process refreshed it
                    
                # Load fresh config
                config = await self._load_from_database(agent_name)
                
                if config:
                    await self._set_cache(cache_key, config)
                    self.stats["refreshes"] += 1
                    self.logger.debug(f"Refreshed config for {agent_name}")
                    
        except Exception as e:
            self.logger.error(f"Background refresh failed for {agent_name}: {e}")
            self.stats["errors"] += 1
            
        finally:
            # Clean up task reference
            async with self._refresh_lock:
                if agent_name in self._refresh_tasks:
                    del self._refresh_tasks[agent_name]
                    
    async def _get_config_version(self, conn: asyncpg.Connection, agent_name: str) -> str:
        """Get config version hash"""
        try:
            row = await conn.fetchrow(
                "SELECT updated_at FROM agent_configs WHERE name = $1",
                agent_name
            )
            
            if row:
                # Create version hash from timestamp
                version_str = str(row['updated_at'])
                return hashlib.md5(version_str.encode()).hexdigest()[:8]
                
        except Exception as e:
            self.logger.error(f"Version check failed: {e}")
            
        return "unknown"
        
    async def cleanup(self) -> None:
        """Cleanup cache resources"""
        # Cancel all refresh tasks
        for task in self._refresh_tasks.values():
            task.cancel()
            
        # Close connections
        if self.redis_client:
            await self.redis_client.aclose()
            
        if self.pg_pool:
            await self.pg_pool.close()
            
        self.logger.info("Cache cleanup complete")