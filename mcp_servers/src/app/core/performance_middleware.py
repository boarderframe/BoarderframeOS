"""
Advanced Performance Middleware for MCP-UI System
Implements request/response optimization, compression, and caching strategies
"""
import asyncio
import gzip
import brotli
import zlib
import time
import hashlib
import json
from typing import Optional, Dict, Any, List, Set, Callable
from datetime import datetime, timedelta
import io

from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers, MutableHeaders
import orjson

from .cache import CacheManager, CacheConfig, CDNCacheHeaders


class CompressionAlgorithm:
    """Compression algorithm selection"""
    GZIP = "gzip"
    BROTLI = "br"
    DEFLATE = "deflate"
    IDENTITY = "identity"
    
    @staticmethod
    def get_best_algorithm(accept_encoding: str) -> str:
        """Select best compression algorithm based on client support"""
        if not accept_encoding:
            return CompressionAlgorithm.IDENTITY
            
        # Priority order: brotli > gzip > deflate
        if "br" in accept_encoding:
            return CompressionAlgorithm.BROTLI
        elif "gzip" in accept_encoding:
            return CompressionAlgorithm.GZIP
        elif "deflate" in accept_encoding:
            return CompressionAlgorithm.DEFLATE
        else:
            return CompressionAlgorithm.IDENTITY


class ResponseOptimizer:
    """Optimize response data for performance"""
    
    COMPRESSION_THRESHOLD = 1024  # 1KB minimum for compression
    COMPRESSION_LEVEL = 6  # Balance between speed and compression ratio
    
    @staticmethod
    def compress_data(data: bytes, algorithm: str) -> bytes:
        """Compress data using specified algorithm"""
        if algorithm == CompressionAlgorithm.GZIP:
            return gzip.compress(data, compresslevel=ResponseOptimizer.COMPRESSION_LEVEL)
        elif algorithm == CompressionAlgorithm.BROTLI:
            return brotli.compress(data, quality=ResponseOptimizer.COMPRESSION_LEVEL)
        elif algorithm == CompressionAlgorithm.DEFLATE:
            return zlib.compress(data, ResponseOptimizer.COMPRESSION_LEVEL)
        return data
        
    @staticmethod
    def should_compress(content_type: str, content_length: int) -> bool:
        """Determine if response should be compressed"""
        # Don't compress already compressed formats
        if any(fmt in content_type for fmt in ['image/', 'video/', 'audio/', '.zip', '.gz']):
            return False
            
        # Only compress text-based content above threshold
        compressible_types = ['text/', 'application/json', 'application/javascript', 
                            'application/xml', 'application/x-www-form-urlencoded']
        
        return (any(ct in content_type for ct in compressible_types) and 
                content_length > ResponseOptimizer.COMPRESSION_THRESHOLD)
                
    @staticmethod
    def optimize_json(data: Any) -> bytes:
        """Optimize JSON serialization"""
        # Use orjson for faster serialization
        return orjson.dumps(
            data,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )


class RequestOptimizer:
    """Optimize incoming requests"""
    
    @staticmethod
    async def decompress_body(request: Request) -> bytes:
        """Decompress request body if compressed"""
        content_encoding = request.headers.get("content-encoding", "").lower()
        body = await request.body()
        
        if content_encoding == "gzip":
            return gzip.decompress(body)
        elif content_encoding == "br":
            return brotli.decompress(body)
        elif content_encoding == "deflate":
            return zlib.decompress(body)
            
        return body
        
    @staticmethod
    def parse_quality_values(header: str) -> Dict[str, float]:
        """Parse quality values from Accept headers"""
        items = {}
        for item in header.split(','):
            parts = item.strip().split(';')
            value = parts[0].strip()
            quality = 1.0
            
            for part in parts[1:]:
                if part.strip().startswith('q='):
                    try:
                        quality = float(part.strip()[2:])
                    except ValueError:
                        quality = 1.0
                        
            items[value] = quality
            
        return items


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Comprehensive performance optimization middleware"""
    
    def __init__(self, app, cache_manager: Optional[CacheManager] = None):
        super().__init__(app)
        self.cache_manager = cache_manager
        self.request_optimizer = RequestOptimizer()
        self.response_optimizer = ResponseOptimizer()
        
        # Performance metrics
        self.metrics = {
            'requests_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'compression_saved_bytes': 0,
            'average_response_time': 0
        }
        
    async def dispatch(self, request: Request, call_next):
        """Process request with performance optimizations"""
        start_time = time.time()
        
        # Generate cache key for GET requests
        cache_key = None
        if request.method == "GET" and self.cache_manager:
            cache_key = self._generate_cache_key(request)
            
            # Try to get from cache
            cached_response = await self.cache_manager.get(cache_key)
            if cached_response:
                self.metrics['cache_hits'] += 1
                return self._build_cached_response(cached_response, request)
                
        # Process request
        response = await call_next(request)
        
        # Capture response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
            
        # Optimize response
        optimized_body, headers = await self._optimize_response(
            response_body,
            response.status_code,
            dict(response.headers),
            request
        )
        
        # Cache successful GET responses
        if cache_key and response.status_code == 200 and self.cache_manager:
            await self._cache_response(cache_key, optimized_body, headers)
            self.metrics['cache_misses'] += 1
            
        # Update metrics
        self.metrics['requests_processed'] += 1
        response_time = time.time() - start_time
        self._update_average_response_time(response_time)
        
        # Add performance headers
        headers['X-Response-Time'] = f"{response_time:.3f}s"
        headers['X-Cache'] = 'HIT' if cached_response else 'MISS'
        
        return Response(
            content=optimized_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        )
        
    def _generate_cache_key(self, request: Request) -> str:
        """Generate unique cache key for request"""
        key_parts = [
            request.url.path,
            request.url.query or '',
            request.headers.get('accept', ''),
            request.headers.get('accept-language', ''),
            request.headers.get('accept-encoding', '')
        ]
        
        key = ':'.join(key_parts)
        
        # Hash long keys
        if len(key) > 250:
            return f"perf:{hashlib.md5(key.encode()).hexdigest()}"
            
        return f"perf:{key}"
        
    async def _optimize_response(self, body: bytes, status_code: int, 
                                headers: Dict[str, str], request: Request) -> tuple:
        """Optimize response body and headers"""
        # Skip optimization for non-success responses
        if status_code >= 400:
            return body, headers
            
        content_type = headers.get('content-type', '')
        
        # Optimize JSON responses
        if 'application/json' in content_type:
            try:
                # Parse and re-serialize with optimization
                data = orjson.loads(body)
                body = self.response_optimizer.optimize_json(data)
            except:
                pass
                
        # Apply compression
        accept_encoding = request.headers.get('accept-encoding', '')
        algorithm = CompressionAlgorithm.get_best_algorithm(accept_encoding)
        
        if (algorithm != CompressionAlgorithm.IDENTITY and 
            self.response_optimizer.should_compress(content_type, len(body))):
            
            original_size = len(body)
            body = self.response_optimizer.compress_data(body, algorithm)
            compressed_size = len(body)
            
            # Update headers
            headers['content-encoding'] = algorithm
            headers['vary'] = 'Accept-Encoding'
            
            # Track compression savings
            self.metrics['compression_saved_bytes'] += (original_size - compressed_size)
            
        # Update content length
        headers['content-length'] = str(len(body))
        
        return body, headers
        
    def _build_cached_response(self, cached_data: Dict, request: Request) -> Response:
        """Build response from cached data"""
        body = cached_data.get('body', b'')
        headers = cached_data.get('headers', {})
        
        # Update cache headers
        headers['X-Cache'] = 'HIT'
        headers['Age'] = str(int(time.time() - cached_data.get('cached_at', 0)))
        
        return Response(
            content=body,
            status_code=cached_data.get('status_code', 200),
            headers=headers,
            media_type=cached_data.get('media_type', 'application/json')
        )
        
    async def _cache_response(self, key: str, body: bytes, headers: Dict):
        """Cache response data"""
        cache_data = {
            'body': body,
            'headers': headers,
            'status_code': 200,
            'media_type': headers.get('content-type', 'application/json'),
            'cached_at': time.time()
        }
        
        # Determine TTL based on content type
        ttl = self._get_cache_ttl(headers.get('content-type', ''))
        
        await self.cache_manager.set(key, cache_data, ttl=ttl)
        
    def _get_cache_ttl(self, content_type: str) -> int:
        """Determine cache TTL based on content type"""
        if 'text/html' in content_type:
            return 60  # 1 minute for HTML
        elif 'application/json' in content_type:
            return 300  # 5 minutes for JSON API responses
        elif any(static in content_type for static in ['css', 'javascript', 'image']):
            return 3600  # 1 hour for static assets
        else:
            return CacheConfig.TTL_MEDIUM  # Default
            
    def _update_average_response_time(self, response_time: float):
        """Update rolling average response time"""
        count = self.metrics['requests_processed']
        current_avg = self.metrics['average_response_time']
        
        # Calculate new average
        self.metrics['average_response_time'] = (
            (current_avg * (count - 1) + response_time) / count
        )
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (self.metrics['cache_hits'] / cache_total * 100 
                         if cache_total > 0 else 0)
        
        return {
            **self.metrics,
            'cache_hit_rate': f"{cache_hit_rate:.2f}%",
            'compression_saved_mb': self.metrics['compression_saved_bytes'] / (1024 * 1024),
            'average_response_time_ms': self.metrics['average_response_time'] * 1000
        }


class ConnectionPoolMiddleware(BaseHTTPMiddleware):
    """Manage connection pooling and keep-alive"""
    
    def __init__(self, app, max_connections: int = 100, keepalive_timeout: int = 60):
        super().__init__(app)
        self.max_connections = max_connections
        self.keepalive_timeout = keepalive_timeout
        self.active_connections: Set[str] = set()
        self.connection_times: Dict[str, float] = {}
        
    async def dispatch(self, request: Request, call_next):
        """Manage connection lifecycle"""
        client_id = self._get_client_id(request)
        
        # Check connection limit
        if len(self.active_connections) >= self.max_connections:
            if client_id not in self.active_connections:
                return JSONResponse(
                    status_code=503,
                    content={"error": "Service temporarily unavailable"},
                    headers={"Retry-After": "5"}
                )
                
        # Track connection
        self.active_connections.add(client_id)
        self.connection_times[client_id] = time.time()
        
        try:
            response = await call_next(request)
            
            # Set keep-alive headers
            response.headers['Connection'] = 'keep-alive'
            response.headers['Keep-Alive'] = f'timeout={self.keepalive_timeout}'
            
            return response
            
        finally:
            # Clean up old connections
            await self._cleanup_connections()
            
    def _get_client_id(self, request: Request) -> str:
        """Generate unique client identifier"""
        # Use combination of IP and user agent
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        return f"{client_host}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
        
    async def _cleanup_connections(self):
        """Remove stale connections"""
        current_time = time.time()
        stale_clients = []
        
        for client_id, last_seen in self.connection_times.items():
            if current_time - last_seen > self.keepalive_timeout:
                stale_clients.append(client_id)
                
        for client_id in stale_clients:
            self.active_connections.discard(client_id)
            del self.connection_times[client_id]


class AdaptiveRenderingMiddleware(BaseHTTPMiddleware):
    """Adaptive rendering based on device capabilities"""
    
    def __init__(self, app):
        super().__init__(app)
        self.device_profiles = {
            'mobile': {'max_image_width': 800, 'lazy_load': True, 'bundle_size': 'small'},
            'tablet': {'max_image_width': 1200, 'lazy_load': True, 'bundle_size': 'medium'},
            'desktop': {'max_image_width': 1920, 'lazy_load': False, 'bundle_size': 'full'}
        }
        
    async def dispatch(self, request: Request, call_next):
        """Adapt response based on device"""
        device_type = self._detect_device_type(request)
        request.state.device_profile = self.device_profiles.get(device_type, 
                                                                self.device_profiles['desktop'])
        
        response = await call_next(request)
        
        # Add client hints for optimization
        response.headers['Accept-CH'] = 'DPR, Width, Viewport-Width, Device-Memory, ECT'
        response.headers['Accept-CH-Lifetime'] = '86400'
        
        return response
        
    def _detect_device_type(self, request: Request) -> str:
        """Detect device type from user agent"""
        user_agent = request.headers.get('user-agent', '').lower()
        
        if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone']):
            return 'mobile'
        elif any(tablet in user_agent for tablet in ['ipad', 'tablet']):
            return 'tablet'
        else:
            return 'desktop'


class PreloadMiddleware(BaseHTTPMiddleware):
    """Preload and prefetch resources for performance"""
    
    def __init__(self, app):
        super().__init__(app)
        self.preload_resources = {
            '/': [  # Homepage preloads
                {'url': '/api/v1/servers', 'as': 'fetch'},
                {'url': '/static/css/main.css', 'as': 'style'},
                {'url': '/static/js/app.js', 'as': 'script'}
            ],
            '/dashboard': [  # Dashboard preloads
                {'url': '/api/v1/metrics', 'as': 'fetch'},
                {'url': '/api/v1/health', 'as': 'fetch'}
            ]
        }
        
    async def dispatch(self, request: Request, call_next):
        """Add preload headers for resources"""
        response = await call_next(request)
        
        # Add preload links for known routes
        path = str(request.url.path)
        if path in self.preload_resources:
            preload_links = []
            for resource in self.preload_resources[path]:
                link = f"<{resource['url']}>; rel=preload; as={resource['as']}"
                preload_links.append(link)
                
            if preload_links:
                response.headers['Link'] = ', '.join(preload_links)
                
        # Add resource hints
        response.headers['X-DNS-Prefetch-Control'] = 'on'
        
        return response


class BackgroundJobMiddleware:
    """Process heavy operations in background"""
    
    def __init__(self, max_workers: int = 10):
        self.job_queue = asyncio.Queue()
        self.workers = []
        self.max_workers = max_workers
        self.jobs: Dict[str, Dict] = {}
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
        await self.job_queue.join()
        
        for worker in self.workers:
            worker.cancel()
            
        await asyncio.gather(*self.workers, return_exceptions=True)
        
    async def _worker(self, name: str):
        """Background worker coroutine"""
        while self._running:
            try:
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                job_id = job['id']
                
                # Update job status
                self.jobs[job_id]['status'] = 'processing'
                self.jobs[job_id]['started_at'] = datetime.now()
                
                # Execute job
                try:
                    result = await job['func'](*job['args'], **job['kwargs'])
                    self.jobs[job_id]['status'] = 'completed'
                    self.jobs[job_id]['result'] = result
                except Exception as e:
                    self.jobs[job_id]['status'] = 'failed'
                    self.jobs[job_id]['error'] = str(e)
                    
                self.jobs[job_id]['completed_at'] = datetime.now()
                self.job_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker {name} error: {e}")
                
    async def submit_job(self, func: Callable, *args, **kwargs) -> str:
        """Submit job for background processing"""
        job_id = hashlib.md5(f"{time.time()}{func.__name__}".encode()).hexdigest()
        
        job = {
            'id': job_id,
            'func': func,
            'args': args,
            'kwargs': kwargs
        }
        
        self.jobs[job_id] = {
            'id': job_id,
            'status': 'queued',
            'created_at': datetime.now(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None
        }
        
        await self.job_queue.put(job)
        return job_id
        
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        return self.jobs.get(job_id)
        
    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs"""
        return list(self.jobs.values())