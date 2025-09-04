"""
CDN Integration for MCP-UI System
Implements static asset delivery, edge caching, and global distribution
"""
import hashlib
import mimetypes
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import aiohttp

from fastapi import Request, Response, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask


class CDNProvider:
    """Base CDN provider interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key', '')
        
    async def upload_asset(self, file_path: str, content: bytes) -> str:
        """Upload asset to CDN"""
        raise NotImplementedError
        
    async def purge_cache(self, paths: List[str]) -> bool:
        """Purge CDN cache for specified paths"""
        raise NotImplementedError
        
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get CDN usage statistics"""
        raise NotImplementedError


class CloudflareCDN(CDNProvider):
    """Cloudflare CDN integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.zone_id = config.get('zone_id')
        self.api_base = "https://api.cloudflare.com/client/v4"
        
    async def upload_asset(self, file_path: str, content: bytes) -> str:
        """Upload to Cloudflare R2 or Workers KV"""
        # Implementation for Cloudflare upload
        url = f"{self.base_url}/{file_path}"
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": self._get_content_type(file_path)
            }
            
            async with session.put(url, data=content, headers=headers) as response:
                if response.status == 200:
                    return f"{self.base_url}/{file_path}"
                raise Exception(f"Upload failed: {response.status}")
                
    async def purge_cache(self, paths: List[str]) -> bool:
        """Purge Cloudflare cache"""
        url = f"{self.api_base}/zones/{self.zone_id}/purge_cache"
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {"files": [f"{self.base_url}{path}" for path in paths]}
            
            async with session.post(url, json=data, headers=headers) as response:
                return response.status == 200
                
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get Cloudflare analytics"""
        url = f"{self.api_base}/zones/{self.zone_id}/analytics/dashboard"
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return {}
                
    def _get_content_type(self, file_path: str) -> str:
        """Get content type for file"""
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"


class FastlyCDN(CDNProvider):
    """Fastly CDN integration"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.service_id = config.get('service_id')
        self.api_base = "https://api.fastly.com"
        
    async def upload_asset(self, file_path: str, content: bytes) -> str:
        """Upload to Fastly edge storage"""
        # Implementation for Fastly
        pass
        
    async def purge_cache(self, paths: List[str]) -> bool:
        """Instant purge on Fastly"""
        url = f"{self.api_base}/service/{self.service_id}/purge"
        
        async with aiohttp.ClientSession() as session:
            headers = {"Fastly-Key": self.api_key}
            
            for path in paths:
                purge_url = f"{url}/{path}"
                async with session.post(purge_url, headers=headers) as response:
                    if response.status != 200:
                        return False
                        
        return True
        
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get Fastly real-time analytics"""
        url = f"{self.api_base}/stats/service/{self.service_id}"
        
        async with aiohttp.ClientSession() as session:
            headers = {"Fastly-Key": self.api_key}
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return {}


class CDNManager:
    """Manage CDN operations and static asset delivery"""
    
    def __init__(self, provider: str = "cloudflare", config: Optional[Dict] = None):
        self.config = config or {}
        self.provider = self._initialize_provider(provider)
        
        # Asset versioning
        self.asset_versions: Dict[str, str] = {}
        self.asset_cache: Dict[str, bytes] = {}
        
        # CDN configuration
        self.static_paths = ['/static', '/assets', '/media']
        self.cache_rules = self._initialize_cache_rules()
        
    def _initialize_provider(self, provider: str) -> CDNProvider:
        """Initialize CDN provider"""
        if provider == "cloudflare":
            return CloudflareCDN(self.config)
        elif provider == "fastly":
            return FastlyCDN(self.config)
        else:
            # Default to local CDN emulation
            return LocalCDN(self.config)
            
    def _initialize_cache_rules(self) -> Dict[str, Dict]:
        """Initialize cache rules for different asset types"""
        return {
            # Immutable assets (versioned)
            r'.*\.(css|js)$': {
                'cache_control': 'public, max-age=31536000, immutable',
                'cdn_cache': 31536000,  # 1 year
                'browser_cache': 31536000
            },
            # Images
            r'.*\.(jpg|jpeg|png|gif|svg|webp)$': {
                'cache_control': 'public, max-age=86400',
                'cdn_cache': 604800,  # 1 week
                'browser_cache': 86400  # 1 day
            },
            # Fonts
            r'.*\.(woff|woff2|ttf|eot)$': {
                'cache_control': 'public, max-age=31536000',
                'cdn_cache': 31536000,
                'browser_cache': 31536000
            },
            # Videos
            r'.*\.(mp4|webm|ogg)$': {
                'cache_control': 'public, max-age=3600',
                'cdn_cache': 86400,
                'browser_cache': 3600
            },
            # Documents
            r'.*\.(pdf|doc|docx)$': {
                'cache_control': 'public, max-age=3600',
                'cdn_cache': 3600,
                'browser_cache': 3600
            }
        }
        
    async def serve_static_asset(self, request: Request, file_path: str) -> Response:
        """Serve static asset with CDN optimization"""
        # Security check
        if '..' in file_path or file_path.startswith('/'):
            raise HTTPException(status_code=403, detail="Invalid file path")
            
        # Get full path
        full_path = Path(self.config.get('static_dir', './static')) / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        # Check if file is cached
        cache_key = str(full_path)
        if cache_key in self.asset_cache:
            content = self.asset_cache[cache_key]
        else:
            # Read file
            async with aiofiles.open(full_path, 'rb') as f:
                content = await f.read()
                
            # Cache small files in memory
            if len(content) < 1024 * 1024:  # 1MB
                self.asset_cache[cache_key] = content
                
        # Get cache headers
        headers = self._get_cache_headers(file_path)
        
        # Add ETag
        etag = self._generate_etag(content)
        headers['ETag'] = etag
        
        # Check If-None-Match
        if request.headers.get('If-None-Match') == etag:
            return Response(status_code=304, headers=headers)
            
        # Return response
        return Response(
            content=content,
            media_type=self._get_content_type(file_path),
            headers=headers
        )
        
    def _get_cache_headers(self, file_path: str) -> Dict[str, str]:
        """Get cache headers for file type"""
        import re
        
        for pattern, rules in self.cache_rules.items():
            if re.match(pattern, file_path):
                return {
                    'Cache-Control': rules['cache_control'],
                    'Vary': 'Accept-Encoding',
                    'X-CDN-Cache': f"max-age={rules['cdn_cache']}"
                }
                
        # Default headers
        return {
            'Cache-Control': 'public, max-age=3600',
            'Vary': 'Accept-Encoding'
        }
        
    def _generate_etag(self, content: bytes) -> str:
        """Generate ETag for content"""
        return f'W/"{hashlib.md5(content).hexdigest()}"'
        
    def _get_content_type(self, file_path: str) -> str:
        """Get content type for file"""
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"
        
    async def optimize_image(self, image_data: bytes, format: str = "webp", 
                           quality: int = 85, max_width: Optional[int] = None) -> bytes:
        """Optimize image for web delivery"""
        try:
            from PIL import Image
            import io
            
            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Resize if needed
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
                
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
                
            # Save optimized image
            output = io.BytesIO()
            img.save(output, format=format.upper(), quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Image optimization failed: {e}")
            return image_data
            
    async def generate_responsive_images(self, image_path: str, sizes: List[int] = None) -> Dict[str, str]:
        """Generate responsive image variants"""
        sizes = sizes or [320, 640, 768, 1024, 1920]
        variants = {}
        
        # Read original image
        async with aiofiles.open(image_path, 'rb') as f:
            original_data = await f.read()
            
        for size in sizes:
            # Optimize for each size
            optimized = await self.optimize_image(
                original_data,
                format="webp",
                quality=85,
                max_width=size
            )
            
            # Generate filename
            base_name = Path(image_path).stem
            ext = Path(image_path).suffix
            variant_name = f"{base_name}-{size}w.webp"
            
            # Upload to CDN
            cdn_url = await self.provider.upload_asset(
                f"images/{variant_name}",
                optimized
            )
            
            variants[f"{size}w"] = cdn_url
            
        return variants
        
    async def bundle_assets(self, asset_type: str, files: List[str]) -> str:
        """Bundle multiple assets into single file"""
        bundled_content = []
        
        for file_path in files:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                
                # Add source map comment
                bundled_content.append(f"/* Source: {file_path} */")
                bundled_content.append(content)
                
        # Join content
        final_content = '\n'.join(bundled_content)
        
        # Generate hash for cache busting
        content_hash = hashlib.md5(final_content.encode()).hexdigest()[:8]
        
        # Create bundle filename
        bundle_name = f"bundle-{asset_type}-{content_hash}.{asset_type}"
        
        # Upload to CDN
        cdn_url = await self.provider.upload_asset(
            f"bundles/{bundle_name}",
            final_content.encode()
        )
        
        return cdn_url
        
    async def invalidate_cache(self, paths: List[str]) -> bool:
        """Invalidate CDN cache for paths"""
        return await self.provider.purge_cache(paths)
        
    async def get_cdn_metrics(self) -> Dict[str, Any]:
        """Get CDN performance metrics"""
        stats = await self.provider.get_usage_stats()
        
        return {
            'bandwidth_usage': stats.get('bandwidth', 0),
            'requests_served': stats.get('requests', 0),
            'cache_hit_ratio': stats.get('cache_hit_ratio', 0),
            'average_response_time': stats.get('avg_response_time', 0),
            'edge_locations': stats.get('edge_locations', [])
        }


class LocalCDN(CDNProvider):
    """Local CDN emulation for development"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.storage_dir = Path(config.get('storage_dir', './cdn_storage'))
        self.storage_dir.mkdir(exist_ok=True)
        
    async def upload_asset(self, file_path: str, content: bytes) -> str:
        """Store asset locally"""
        full_path = self.storage_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(content)
            
        return f"/cdn/{file_path}"
        
    async def purge_cache(self, paths: List[str]) -> bool:
        """Clear local cache"""
        for path in paths:
            full_path = self.storage_dir / path.lstrip('/')
            if full_path.exists():
                full_path.unlink()
        return True
        
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get local storage stats"""
        total_size = sum(f.stat().st_size for f in self.storage_dir.rglob('*') if f.is_file())
        file_count = sum(1 for f in self.storage_dir.rglob('*') if f.is_file())
        
        return {
            'total_size_mb': total_size / (1024 * 1024),
            'file_count': file_count,
            'storage_path': str(self.storage_dir)
        }


class ImageOptimizationService:
    """Advanced image optimization service"""
    
    def __init__(self):
        self.supported_formats = ['webp', 'avif', 'jpg', 'png']
        
    async def generate_srcset(self, image_path: str, sizes: List[int] = None) -> str:
        """Generate srcset attribute for responsive images"""
        sizes = sizes or [320, 640, 768, 1024, 1440, 1920]
        srcset_parts = []
        
        for size in sizes:
            # Generate optimized variant URL
            variant_url = f"{image_path}?w={size}&format=webp"
            srcset_parts.append(f"{variant_url} {size}w")
            
        return ', '.join(srcset_parts)
        
    async def generate_picture_element(self, image_path: str, alt: str = "") -> str:
        """Generate picture element with multiple formats"""
        return f"""
        <picture>
            <source type="image/avif" srcset="{image_path}?format=avif">
            <source type="image/webp" srcset="{image_path}?format=webp">
            <img src="{image_path}" alt="{alt}" loading="lazy">
        </picture>
        """
        
    async def lazy_load_config(self) -> Dict[str, Any]:
        """Get lazy loading configuration"""
        return {
            'root_margin': '50px',
            'threshold': 0.01,
            'loading_class': 'lazy-loading',
            'loaded_class': 'lazy-loaded',
            'error_class': 'lazy-error'
        }


class EdgeComputeService:
    """Edge computing integration for CDN"""
    
    def __init__(self, provider: str = "cloudflare"):
        self.provider = provider
        self.workers: Dict[str, str] = {}
        
    async def deploy_worker(self, name: str, code: str) -> str:
        """Deploy edge worker/function"""
        # Implementation depends on provider
        # Cloudflare Workers, Fastly Compute@Edge, etc.
        worker_id = hashlib.md5(f"{name}{code}".encode()).hexdigest()[:8]
        self.workers[name] = worker_id
        return worker_id
        
    async def create_ab_test_worker(self, variants: Dict[str, float]) -> str:
        """Create A/B testing edge worker"""
        code = """
        addEventListener('fetch', event => {
            event.respondWith(handleRequest(event.request))
        })
        
        async function handleRequest(request) {
            const random = Math.random()
            let cumulative = 0
            let selectedVariant = 'control'
            
            // Variant selection logic
            %s
            
            // Modify request or response based on variant
            const response = await fetch(request)
            const newResponse = new Response(response.body, response)
            newResponse.headers.set('X-AB-Variant', selectedVariant)
            
            return newResponse
        }
        """ % self._generate_variant_logic(variants)
        
        return await self.deploy_worker('ab_test', code)
        
    def _generate_variant_logic(self, variants: Dict[str, float]) -> str:
        """Generate variant selection logic"""
        logic = []
        for variant, weight in variants.items():
            logic.append(f"""
            cumulative += {weight}
            if (random < cumulative) {{
                selectedVariant = '{variant}'
            }}
            """)
        return '\n'.join(logic)