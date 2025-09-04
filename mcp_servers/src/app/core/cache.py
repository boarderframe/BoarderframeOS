"""
Caching infrastructure for MCP Server Manager
Implements multi-layer caching with Redis, in-memory, and CDN strategies
"""
import asyncio
import json
import hashlib
from typing import Any, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import pickle

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from fastapi import Request
from starlette.responses import Response


class CacheConfig:
    """Cache configuration with performance optimizations"""
    
    # Cache TTL configurations (in seconds)
    TTL_SHORT = 60  # 1 minute for volatile data
    TTL_MEDIUM = 300  # 5 minutes for semi-static data
    TTL_LONG = 3600  # 1 hour for static data
    TTL_DAY = 86400  # 24 hours for rarely changing data
    
    # Cache key prefixes
    PREFIX_API = "api:"
    PREFIX_SESSION = "session:"
    PREFIX_SERVER = "server:"
    PREFIX_METRICS = "metrics:"
    PREFIX_CONFIG = "config:"
    
    # Performance settings
    MAX_CONNECTIONS = 100
    CONNECTION_TIMEOUT = 5
    SOCKET_TIMEOUT = 5
    RETRY_ON_TIMEOUT = True
    MAX_RETRIES = 3
    
    # Compression threshold (bytes)
    COMPRESSION_THRESHOLD = 1024


class RedisCache:
    """High-performance Redis cache with connection pooling"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize Redis connection pool"""
        async with self._lock:
            if not self._pool:
                self._pool = ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=CacheConfig.MAX_CONNECTIONS,
                    socket_timeout=CacheConfig.SOCKET_TIMEOUT,
                    socket_connect_timeout=CacheConfig.CONNECTION_TIMEOUT,
                    retry_on_timeout=CacheConfig.RETRY_ON_TIMEOUT,
                    health_check_interval=30,
                    decode_responses=False  # Handle encoding ourselves for flexibility
                )
                self._client = redis.Redis(connection_pool=self._pool)
                
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic deserialization"""
        try:
            value = await self._client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            # Log error but don't fail the request
            print(f"Cache get error for key {key}: {e}")
            return None
            
    async def set(self, key: str, value: Any, ttl: int = CacheConfig.TTL_MEDIUM) -> bool:
        """Set value in cache with automatic serialization"""
        try:
            serialized = pickle.dumps(value)
            # Compress large values
            if len(serialized) > CacheConfig.COMPRESSION_THRESHOLD:
                import zlib
                serialized = zlib.compress(serialized)
            return await self._client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return await self._client.delete(key) > 0
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False
            
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = await self._client.keys(pattern)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for {pattern}: {e}")
            return 0
            
    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomic increment operation"""
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            print(f"Cache increment error for key {key}: {e}")
            return 0
            
    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key"""
        try:
            return await self._client.ttl(key)
        except Exception as e:
            print(f"Cache TTL error for key {key}: {e}")
            return -1
            
    async def pipeline_get(self, keys: list[str]) -> list[Optional[Any]]:
        """Batch get multiple keys for performance"""
        try:
            pipe = self._client.pipeline()
            for key in keys:
                pipe.get(key)
            results = await pipe.execute()
            return [pickle.loads(r) if r else None for r in results]
        except Exception as e:
            print(f"Cache pipeline get error: {e}")
            return [None] * len(keys)
            
    async def close(self):
        """Close Redis connections"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()


class InMemoryCache:
    """Fast in-memory LRU cache for hot data"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: dict = {}
        self._access_times: dict = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        async with self._lock:
            if key in self._cache:
                # Check if expired
                if self._access_times[key]['expires'] > datetime.now():
                    self._access_times[key]['last_access'] = datetime.now()
                    return self._cache[key]
                else:
                    # Remove expired entry
                    del self._cache[key]
                    del self._access_times[key]
            return None
            
    async def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set value in in-memory cache with LRU eviction"""
        async with self._lock:
            # Evict LRU if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                lru_key = min(self._access_times.keys(), 
                            key=lambda k: self._access_times[k]['last_access'])
                del self._cache[lru_key]
                del self._access_times[lru_key]
                
            self._cache[key] = value
            self._access_times[key] = {
                'last_access': datetime.now(),
                'expires': datetime.now() + timedelta(seconds=ttl)
            }
            return True
            
    async def delete(self, key: str) -> bool:
        """Delete key from in-memory cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                return True
            return False
            
    async def clear(self):
        """Clear all entries"""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()


class CacheManager:
    """Unified cache manager with multi-layer strategy"""
    
    def __init__(self, redis_url: str):
        self.redis_cache = RedisCache(redis_url)
        self.memory_cache = InMemoryCache(max_size=500)
        self._initialized = False
        
    async def initialize(self):
        """Initialize cache systems"""
        if not self._initialized:
            await self.redis_cache.initialize()
            self._initialized = True
            
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        
        # Hash long keys to avoid Redis key length limits
        if len(key_string) > 250:
            hash_suffix = hashlib.md5(key_string.encode()).hexdigest()
            key_string = f"{key_string[:200]}:{hash_suffix}"
            
        return key_string
        
    async def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """Get from cache with fallback strategy"""
        # Try memory cache first for speed
        if use_memory:
            value = await self.memory_cache.get(key)
            if value is not None:
                return value
                
        # Fallback to Redis
        value = await self.redis_cache.get(key)
        
        # Populate memory cache on Redis hit
        if value is not None and use_memory:
            await self.memory_cache.set(key, value, ttl=60)
            
        return value
        
    async def set(self, key: str, value: Any, ttl: int = CacheConfig.TTL_MEDIUM,
                  use_memory: bool = True) -> bool:
        """Set in both cache layers"""
        success = await self.redis_cache.set(key, value, ttl)
        
        if success and use_memory:
            # Store in memory with shorter TTL
            memory_ttl = min(ttl, 300)  # Max 5 minutes in memory
            await self.memory_cache.set(key, value, memory_ttl)
            
        return success
        
    async def delete(self, key: str) -> bool:
        """Delete from all cache layers"""
        redis_success = await self.redis_cache.delete(key)
        memory_success = await self.memory_cache.delete(key)
        return redis_success or memory_success
        
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        await self.redis_cache.delete_pattern(pattern)
        # Clear memory cache as it might have stale data
        await self.memory_cache.clear()


def cache_response(ttl: int = CacheConfig.TTL_MEDIUM, 
                   key_prefix: str = CacheConfig.PREFIX_API,
                   use_memory: bool = True):
    """Decorator for caching API responses"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Generate cache key from request
            cache_key = f"{key_prefix}{request.url.path}:{request.url.query}"
            
            # Get cache manager from app state
            cache_manager = request.app.state.cache_manager
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key, use_memory=use_memory)
            if cached_value is not None:
                # Add cache hit header
                if isinstance(cached_value, Response):
                    cached_value.headers["X-Cache"] = "HIT"
                return cached_value
                
            # Execute function
            result = await func(request, *args, **kwargs)
            
            # Cache the result
            await cache_manager.set(cache_key, result, ttl=ttl, use_memory=use_memory)
            
            # Add cache miss header
            if isinstance(result, Response):
                result.headers["X-Cache"] = "MISS"
                
            return result
        return wrapper
    return decorator


def cache_key_decorator(prefix: str, ttl: int = CacheConfig.TTL_MEDIUM):
    """Decorator for caching function results with custom keys"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager from first arg if it has app context
            cache_manager = None
            if hasattr(args[0], 'app'):
                cache_manager = args[0].app.state.cache_manager
            elif hasattr(args[0], 'request'):
                cache_manager = args[0].request.app.state.cache_manager
                
            if not cache_manager:
                # No cache available, execute function directly
                return await func(*args, **kwargs)
                
            # Generate cache key
            cache_key = cache_manager.generate_key(prefix, *args[1:], **kwargs)
            
            # Try cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
                
            # Execute and cache
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


# CDN cache headers helper
class CDNCacheHeaders:
    """Helper for setting CDN cache control headers"""
    
    @staticmethod
    def public(max_age: int = 3600, s_maxage: int = None):
        """Public cacheable response"""
        s_maxage = s_maxage or max_age
        return {
            "Cache-Control": f"public, max-age={max_age}, s-maxage={s_maxage}",
            "Vary": "Accept-Encoding"
        }
        
    @staticmethod
    def private(max_age: int = 0):
        """Private, user-specific response"""
        return {
            "Cache-Control": f"private, max-age={max_age}, no-store",
            "Pragma": "no-cache"
        }
        
    @staticmethod
    def immutable(max_age: int = 31536000):
        """Immutable assets (1 year default)"""
        return {
            "Cache-Control": f"public, max-age={max_age}, immutable",
            "Vary": "Accept-Encoding"
        }
        
    @staticmethod
    def no_cache():
        """No caching allowed"""
        return {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }