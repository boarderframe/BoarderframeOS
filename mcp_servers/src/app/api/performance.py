"""
High-performance API utilities for MCP Server Manager
Implements streaming, pagination, compression, and async optimizations
"""
import asyncio
import gzip
import json
from typing import Any, AsyncGenerator, Optional, List, Dict, Callable
from datetime import datetime
import hashlib

from fastapi import Query, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import orjson  # Faster JSON serialization
from starlette.background import BackgroundTask

# Performance constants
MAX_PAGE_SIZE = 1000
DEFAULT_PAGE_SIZE = 100
COMPRESSION_THRESHOLD = 1024  # Compress responses > 1KB
STREAM_CHUNK_SIZE = 8192  # 8KB chunks for streaming


class PaginationParams(BaseModel):
    """Pagination parameters with validation"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: str = Field(default="asc", regex="^(asc|desc)$")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
        
    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel):
    """Standardized paginated response"""
    data: List[Any]
    pagination: Dict[str, Any]
    
    @classmethod
    def create(cls, data: List[Any], total: int, params: PaginationParams):
        """Create paginated response with metadata"""
        total_pages = (total + params.page_size - 1) // params.page_size
        return cls(
            data=data,
            pagination={
                "page": params.page,
                "page_size": params.page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": params.page < total_pages,
                "has_prev": params.page > 1,
            }
        )


class OptimizedJSONResponse(JSONResponse):
    """JSON response with performance optimizations"""
    
    def render(self, content: Any) -> bytes:
        """Use orjson for faster JSON serialization"""
        return orjson.dumps(
            content,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )


class CompressedResponse(Response):
    """Automatically compress large responses"""
    
    def __init__(self, content: Any, **kwargs):
        # Serialize content
        if isinstance(content, (dict, list)):
            content = orjson.dumps(content)
        elif isinstance(content, str):
            content = content.encode('utf-8')
            
        # Compress if above threshold
        if len(content) > COMPRESSION_THRESHOLD:
            content = gzip.compress(content, compresslevel=6)
            kwargs['headers'] = kwargs.get('headers', {})
            kwargs['headers']['Content-Encoding'] = 'gzip'
            
        super().__init__(content=content, **kwargs)


async def stream_large_dataset(
    query_func: Callable,
    chunk_size: int = 100,
    transform_func: Optional[Callable] = None
) -> AsyncGenerator[bytes, None]:
    """
    Stream large datasets in chunks to avoid memory issues
    
    Args:
        query_func: Async function that yields data chunks
        chunk_size: Number of items per chunk
        transform_func: Optional transformation for each item
    """
    buffer = []
    
    async for item in query_func():
        # Apply transformation if provided
        if transform_func:
            item = await transform_func(item) if asyncio.iscoroutinefunction(transform_func) else transform_func(item)
            
        buffer.append(item)
        
        # Yield chunk when buffer is full
        if len(buffer) >= chunk_size:
            yield orjson.dumps(buffer) + b'\n'
            buffer = []
            
    # Yield remaining items
    if buffer:
        yield orjson.dumps(buffer) + b'\n'


class StreamingJSONResponse(StreamingResponse):
    """Stream JSON data efficiently"""
    
    def __init__(self, generator: AsyncGenerator, **kwargs):
        super().__init__(
            content=generator,
            media_type="application/x-ndjson",  # Newline-delimited JSON
            **kwargs
        )


class ETagMiddleware:
    """ETag support for caching"""
    
    @staticmethod
    def generate_etag(content: bytes) -> str:
        """Generate ETag from content"""
        return f'W/"{hashlib.md5(content).hexdigest()}"'
        
    @staticmethod
    async def check_etag(request: Request, response: Response) -> bool:
        """Check if client has valid cached version"""
        if not hasattr(response, 'body'):
            return False
            
        etag = ETagMiddleware.generate_etag(response.body)
        response.headers['ETag'] = etag
        
        # Check If-None-Match header
        if_none_match = request.headers.get('If-None-Match')
        if if_none_match and if_none_match == etag:
            response.status_code = 304  # Not Modified
            response.body = b''
            return True
            
        return False


class RateLimiter:
    """Token bucket rate limiter for API endpoints"""
    
    def __init__(self, rate: int = 100, per: int = 60):
        """
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.buckets: Dict[str, Dict] = {}
        self._cleanup_task = None
        
    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limit"""
        now = datetime.now().timestamp()
        
        if key not in self.buckets:
            self.buckets[key] = {
                'tokens': self.rate,
                'last_update': now
            }
            
        bucket = self.buckets[key]
        
        # Refill tokens based on time passed
        time_passed = now - bucket['last_update']
        tokens_to_add = (time_passed / self.per) * self.rate
        bucket['tokens'] = min(self.rate, bucket['tokens'] + tokens_to_add)
        bucket['last_update'] = now
        
        # Check if request is allowed
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
            
        return False
        
    async def cleanup_old_buckets(self):
        """Remove old buckets to prevent memory leak"""
        while True:
            await asyncio.sleep(300)  # Clean every 5 minutes
            now = datetime.now().timestamp()
            cutoff = now - 3600  # Remove buckets older than 1 hour
            
            self.buckets = {
                k: v for k, v in self.buckets.items()
                if v['last_update'] > cutoff
            }


class BackgroundTaskQueue:
    """Queue for processing tasks in background"""
    
    def __init__(self, max_workers: int = 10):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers = []
        self.max_workers = max_workers
        self._running = False
        
    async def start(self):
        """Start background workers"""
        self._running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
            
    async def stop(self):
        """Stop all workers"""
        self._running = False
        
        # Wait for queue to be empty
        await self.queue.join()
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
            
        await asyncio.gather(*self.workers, return_exceptions=True)
        
    async def _worker(self, name: str):
        """Worker coroutine"""
        while self._running:
            try:
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                await task()
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker {name} error: {e}")
                
    async def add_task(self, task: Callable):
        """Add task to queue"""
        await self.queue.put(task)


class ResponseCache:
    """In-memory response cache with TTL"""
    
    def __init__(self, ttl: int = 60):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached response"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now().timestamp() < entry['expires']:
                return entry['value']
            else:
                del self.cache[key]
        return None
        
    def set(self, key: str, value: Any):
        """Cache response with TTL"""
        self.cache[key] = {
            'value': value,
            'expires': datetime.now().timestamp() + self.ttl
        }
        
    def clear_expired(self):
        """Remove expired entries"""
        now = datetime.now().timestamp()
        self.cache = {
            k: v for k, v in self.cache.items()
            if v['expires'] > now
        }


def paginate(query_params: PaginationParams = Query()):
    """Dependency for pagination parameters"""
    return query_params


async def compress_response(request: Request, call_next):
    """Middleware to compress responses"""
    response = await call_next(request)
    
    # Check if client accepts gzip
    accept_encoding = request.headers.get('Accept-Encoding', '')
    if 'gzip' not in accept_encoding:
        return response
        
    # Only compress certain content types
    content_type = response.headers.get('Content-Type', '')
    if not any(ct in content_type for ct in ['json', 'text', 'javascript', 'css']):
        return response
        
    return response


class PerformanceMiddleware:
    """Middleware for performance monitoring and optimization"""
    
    def __init__(self):
        self.request_times = []
        
    async def __call__(self, request: Request, call_next):
        """Track request performance"""
        start_time = datetime.now()
        
        # Add request ID for tracing
        request_id = hashlib.md5(f"{start_time}{request.url}".encode()).hexdigest()[:16]
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (datetime.now() - start_time).total_seconds()
        
        # Add performance headers
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Process-Time'] = str(process_time)
        
        # Store metrics
        self.request_times.append({
            'timestamp': start_time,
            'duration': process_time,
            'path': str(request.url.path),
            'method': request.method,
            'status': response.status_code
        })
        
        # Keep only last hour of metrics
        cutoff = datetime.now() - timedelta(hours=1)
        self.request_times = [
            m for m in self.request_times
            if m['timestamp'] > cutoff
        ]
        
        return response
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.request_times:
            return {}
            
        durations = [m['duration'] for m in self.request_times]
        return {
            'total_requests': len(self.request_times),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p50_duration': sorted(durations)[len(durations) // 2],
            'p95_duration': sorted(durations)[int(len(durations) * 0.95)],
            'p99_duration': sorted(durations)[int(len(durations) * 0.99)],
        }


# Helper functions for common patterns

async def batch_process(
    items: List[Any],
    process_func: Callable,
    batch_size: int = 100,
    max_concurrent: int = 10
) -> List[Any]:
    """
    Process items in batches with concurrency control
    
    Args:
        items: List of items to process
        process_func: Async function to process each item
        batch_size: Items per batch
        max_concurrent: Maximum concurrent batches
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(batch):
        async with semaphore:
            return await asyncio.gather(*[process_func(item) for item in batch])
            
    # Create batches
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    # Process all batches
    batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])
    
    # Flatten results
    for batch_result in batch_results:
        results.extend(batch_result)
        
    return results


def cache_key_from_request(request: Request) -> str:
    """Generate cache key from request"""
    # Include query parameters and relevant headers
    key_parts = [
        request.url.path,
        request.url.query or '',
        request.headers.get('Accept', ''),
        request.headers.get('Accept-Language', ''),
    ]
    
    key = ':'.join(key_parts)
    
    # Hash if too long
    if len(key) > 250:
        return hashlib.md5(key.encode()).hexdigest()
        
    return key