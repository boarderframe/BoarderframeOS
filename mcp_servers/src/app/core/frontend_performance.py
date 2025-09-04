"""
Frontend Performance Optimization for MCP-UI System
Implements PWA features, service workers, and JavaScript optimization
"""
import json
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from fastapi import Request, Response
from fastapi.responses import FileResponse, JSONResponse


class ServiceWorkerGenerator:
    """Generate and manage service workers for offline functionality"""
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.cache_name = f"mcp-ui-v{version}"
        
    def generate_service_worker(self, config: Dict[str, Any]) -> str:
        """Generate service worker JavaScript code"""
        return f"""
// MCP-UI Service Worker v{self.version}
const CACHE_NAME = '{self.cache_name}';
const API_CACHE = 'mcp-api-cache';
const IMAGE_CACHE = 'mcp-image-cache';

// Files to cache for offline use
const urlsToCache = {json.dumps(config.get('urls_to_cache', []))};

// API endpoints to cache
const apiEndpoints = {json.dumps(config.get('api_endpoints', []))};

// Install event - cache essential files
self.addEventListener('install', (event) => {{
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {{
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            }})
            .then(() => self.skipWaiting())
    );
}});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {{
    event.waitUntil(
        caches.keys().then((cacheNames) => {{
            return Promise.all(
                cacheNames.map((cacheName) => {{
                    if (cacheName !== CACHE_NAME && 
                        cacheName !== API_CACHE && 
                        cacheName !== IMAGE_CACHE) {{
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }}
                }})
            );
        }}).then(() => self.clients.claim())
    );
}});

// Fetch event - serve from cache when possible
self.addEventListener('fetch', (event) => {{
    const url = new URL(event.request.url);
    
    // Handle API requests
    if (url.pathname.startsWith('/api/')) {{
        event.respondWith(handleApiRequest(event.request));
        return;
    }}
    
    // Handle image requests
    if (isImageRequest(event.request)) {{
        event.respondWith(handleImageRequest(event.request));
        return;
    }}
    
    // Handle other requests
    event.respondWith(
        caches.match(event.request)
            .then((response) => {{
                if (response) {{
                    return response;
                }}
                
                return fetch(event.request).then((response) => {{
                    // Don't cache non-successful responses
                    if (!response || response.status !== 200 || response.type !== 'basic') {{
                        return response;
                    }}
                    
                    // Clone the response
                    const responseToCache = response.clone();
                    
                    caches.open(CACHE_NAME).then((cache) => {{
                        cache.put(event.request, responseToCache);
                    }});
                    
                    return response;
                }});
            }})
            .catch(() => {{
                // Return offline page if available
                return caches.match('/offline.html');
            }})
    );
}});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {{
    try {{
        const response = await fetch(request);
        
        // Cache successful GET requests
        if (request.method === 'GET' && response.status === 200) {{
            const cache = await caches.open(API_CACHE);
            cache.put(request, response.clone());
        }}
        
        return response;
    }} catch (error) {{
        // Try cache on network failure
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {{
            // Add header to indicate cached response
            const headers = new Headers(cachedResponse.headers);
            headers.set('X-From-Cache', 'true');
            
            return new Response(cachedResponse.body, {{
                status: cachedResponse.status,
                statusText: cachedResponse.statusText,
                headers: headers
            }});
        }}
        
        // Return error response
        return new Response(JSON.stringify({{error: 'Network error'}}), {{
            status: 503,
            headers: {{'Content-Type': 'application/json'}}
        }});
    }}
}}

// Handle image requests with cache-first strategy
async function handleImageRequest(request) {{
    const cache = await caches.open(IMAGE_CACHE);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {{
        return cachedResponse;
    }}
    
    try {{
        const response = await fetch(request);
        
        if (response.status === 200) {{
            cache.put(request, response.clone());
        }}
        
        return response;
    }} catch (error) {{
        // Return placeholder image if available
        return caches.match('/images/placeholder.png');
    }}
}}

// Check if request is for an image
function isImageRequest(request) {{
    const url = new URL(request.url);
    return /\\.(jpg|jpeg|png|gif|svg|webp)$/i.test(url.pathname);
}}

// Background sync for offline actions
self.addEventListener('sync', (event) => {{
    if (event.tag === 'sync-data') {{
        event.waitUntil(syncOfflineData());
    }}
}});

// Sync offline data when connection is restored
async function syncOfflineData() {{
    // Implementation for syncing offline changes
    console.log('Syncing offline data...');
}}

// Push notifications
self.addEventListener('push', (event) => {{
    const options = {{
        body: event.data ? event.data.text() : 'New update available',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {{
            dateOfArrival: Date.now(),
            primaryKey: 1
        }}
    }};
    
    event.waitUntil(
        self.registration.showNotification('MCP-UI Update', options)
    );
}});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {{
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow('/')
    );
}});

// Cache management utilities
const CacheManager = {{
    async clearOldCaches() {{
        const cacheNames = await caches.keys();
        const oldCaches = cacheNames.filter(name => 
            name.startsWith('mcp-ui-') && name !== CACHE_NAME
        );
        
        return Promise.all(oldCaches.map(name => caches.delete(name)));
    }},
    
    async getCacheSize() {{
        if ('estimate' in navigator.storage) {{
            const estimate = await navigator.storage.estimate();
            return estimate.usage;
        }}
        return null;
    }},
    
    async pruneCache(cacheName, maxItems = 50) {{
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        
        if (keys.length > maxItems) {{
            const keysToDelete = keys.slice(0, keys.length - maxItems);
            return Promise.all(keysToDelete.map(key => cache.delete(key)));
        }}
    }}
}};
"""
        
    def generate_manifest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PWA manifest.json"""
        return {
            "name": config.get("name", "MCP-UI Server Manager"),
            "short_name": config.get("short_name", "MCP-UI"),
            "description": config.get("description", "Manage MCP servers with optimized UI"),
            "start_url": config.get("start_url", "/"),
            "display": "standalone",
            "background_color": config.get("background_color", "#ffffff"),
            "theme_color": config.get("theme_color", "#000000"),
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "/icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
            "categories": ["productivity", "utilities"],
            "screenshots": config.get("screenshots", []),
            "shortcuts": [
                {
                    "name": "Dashboard",
                    "short_name": "Dashboard",
                    "description": "View system dashboard",
                    "url": "/dashboard",
                    "icons": [{"src": "/icons/dashboard.png", "sizes": "192x192"}]
                },
                {
                    "name": "Servers",
                    "short_name": "Servers",
                    "description": "Manage MCP servers",
                    "url": "/servers",
                    "icons": [{"src": "/icons/servers.png", "sizes": "192x192"}]
                }
            ],
            "prefer_related_applications": False,
            "related_applications": []
        }


class JavaScriptOptimizer:
    """Optimize JavaScript bundles and loading"""
    
    def __init__(self):
        self.bundle_cache: Dict[str, str] = {}
        
    def generate_lazy_loader(self) -> str:
        """Generate lazy loading script"""
        return """
// Lazy loading implementation
const LazyLoader = {
    // Intersection Observer for lazy loading
    observer: null,
    
    init() {
        // Check for IntersectionObserver support
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                this.handleIntersection.bind(this),
                {
                    root: null,
                    rootMargin: '50px',
                    threshold: 0.01
                }
            );
            
            // Observe all lazy elements
            this.observeElements();
        } else {
            // Fallback for older browsers
            this.loadAllElements();
        }
    },
    
    observeElements() {
        // Images
        document.querySelectorAll('img[data-src]').forEach(img => {
            this.observer.observe(img);
        });
        
        // Iframes
        document.querySelectorAll('iframe[data-src]').forEach(iframe => {
            this.observer.observe(iframe);
        });
        
        // Components
        document.querySelectorAll('[data-component]').forEach(element => {
            this.observer.observe(element);
        });
    },
    
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                
                if (element.tagName === 'IMG') {
                    this.loadImage(element);
                } else if (element.tagName === 'IFRAME') {
                    this.loadIframe(element);
                } else if (element.hasAttribute('data-component')) {
                    this.loadComponent(element);
                }
                
                this.observer.unobserve(element);
            }
        });
    },
    
    loadImage(img) {
        const src = img.getAttribute('data-src');
        const srcset = img.getAttribute('data-srcset');
        
        if (src) {
            img.src = src;
            img.removeAttribute('data-src');
        }
        
        if (srcset) {
            img.srcset = srcset;
            img.removeAttribute('data-srcset');
        }
        
        img.classList.add('loaded');
    },
    
    loadIframe(iframe) {
        const src = iframe.getAttribute('data-src');
        
        if (src) {
            iframe.src = src;
            iframe.removeAttribute('data-src');
        }
    },
    
    async loadComponent(element) {
        const componentName = element.getAttribute('data-component');
        const props = JSON.parse(element.getAttribute('data-props') || '{}');
        
        try {
            // Dynamic import
            const module = await import(`/components/${componentName}.js`);
            const Component = module.default;
            
            // Render component
            if (typeof Component === 'function') {
                Component(element, props);
            }
            
            element.classList.add('component-loaded');
        } catch (error) {
            console.error(`Failed to load component ${componentName}:`, error);
        }
    },
    
    loadAllElements() {
        // Fallback for browsers without IntersectionObserver
        document.querySelectorAll('img[data-src]').forEach(img => {
            this.loadImage(img);
        });
        
        document.querySelectorAll('iframe[data-src]').forEach(iframe => {
            this.loadIframe(iframe);
        });
    }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => LazyLoader.init());
} else {
    LazyLoader.init();
}
"""
        
    def generate_code_splitting_config(self) -> Dict[str, Any]:
        """Generate code splitting configuration for bundlers"""
        return {
            "optimization": {
                "splitChunks": {
                    "chunks": "all",
                    "cacheGroups": {
                        "vendor": {
                            "test": "/node_modules/",
                            "name": "vendors",
                            "priority": 10,
                            "reuseExistingChunk": True
                        },
                        "common": {
                            "minChunks": 2,
                            "priority": 5,
                            "reuseExistingChunk": True
                        },
                        "async": {
                            "test": "/async/",
                            "name": "async",
                            "chunks": "async",
                            "priority": 15
                        }
                    }
                },
                "runtimeChunk": "single",
                "moduleIds": "deterministic"
            }
        }
        
    def generate_prefetch_script(self, resources: List[str]) -> str:
        """Generate resource prefetching script"""
        return f"""
// Resource prefetching
const ResourcePrefetcher = {{
    resources: {json.dumps(resources)},
    
    init() {{
        // Check for prefetch support
        if (this.supportsPrefetch()) {{
            this.prefetchResources();
        }} else {{
            // Fallback to preload
            this.preloadResources();
        }}
        
        // Prefetch on idle
        if ('requestIdleCallback' in window) {{
            requestIdleCallback(() => this.prefetchOnIdle());
        }}
    }},
    
    supportsPrefetch() {{
        const link = document.createElement('link');
        return link.relList && link.relList.supports && link.relList.supports('prefetch');
    }},
    
    prefetchResources() {{
        this.resources.forEach(resource => {{
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = resource;
            link.as = this.getResourceType(resource);
            document.head.appendChild(link);
        }});
    }},
    
    preloadResources() {{
        // Use preload as fallback
        this.resources.slice(0, 3).forEach(resource => {{
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource;
            link.as = this.getResourceType(resource);
            document.head.appendChild(link);
        }});
    }},
    
    getResourceType(url) {{
        if (url.endsWith('.js')) return 'script';
        if (url.endsWith('.css')) return 'style';
        if (/\\.(jpg|jpeg|png|gif|webp)$/i.test(url)) return 'image';
        if (url.endsWith('.woff2')) return 'font';
        return 'fetch';
    }},
    
    prefetchOnIdle() {{
        // Prefetch additional resources when idle
        const additionalResources = [
            '/api/v1/metrics',
            '/api/v1/health',
            '/static/images/dashboard-bg.webp'
        ];
        
        additionalResources.forEach(resource => {{
            fetch(resource, {{
                method: 'GET',
                mode: 'no-cors',
                cache: 'force-cache'
            }});
        }});
    }}
}};

ResourcePrefetcher.init();
"""


class WebVitalsTracker:
    """Track and report Core Web Vitals from client"""
    
    def generate_tracking_script(self) -> str:
        """Generate Web Vitals tracking script"""
        return """
// Web Vitals tracking
(function() {
    // Check if Performance Observer is supported
    if (!('PerformanceObserver' in window)) {
        return;
    }
    
    const vitals = {
        LCP: null,
        FID: null,
        CLS: null,
        FCP: null,
        TTFB: null,
        INP: null
    };
    
    // Largest Contentful Paint
    new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1];
        vitals.LCP = lastEntry.renderTime || lastEntry.loadTime;
        reportVital('LCP', vitals.LCP);
    }).observe({type: 'largest-contentful-paint', buffered: true});
    
    // First Input Delay
    new PerformanceObserver((entryList) => {
        const firstInput = entryList.getEntries()[0];
        vitals.FID = firstInput.processingStart - firstInput.startTime;
        reportVital('FID', vitals.FID);
    }).observe({type: 'first-input', buffered: true});
    
    // Cumulative Layout Shift
    let clsValue = 0;
    let clsEntries = [];
    
    new PerformanceObserver((entryList) => {
        for (const entry of entryList.getEntries()) {
            if (!entry.hadRecentInput) {
                clsValue += entry.value;
                clsEntries.push(entry);
            }
        }
        vitals.CLS = clsValue;
        reportVital('CLS', vitals.CLS);
    }).observe({type: 'layout-shift', buffered: true});
    
    // First Contentful Paint
    new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        for (const entry of entries) {
            if (entry.name === 'first-contentful-paint') {
                vitals.FCP = entry.startTime;
                reportVital('FCP', vitals.FCP);
            }
        }
    }).observe({type: 'paint', buffered: true});
    
    // Time to First Byte
    new PerformanceObserver((entryList) => {
        const [pageNav] = entryList.getEntriesByType('navigation');
        vitals.TTFB = pageNav.responseStart - pageNav.fetchStart;
        reportVital('TTFB', vitals.TTFB);
    }).observe({type: 'navigation', buffered: true});
    
    // Interaction to Next Paint (INP)
    let inpValue = 0;
    const processedInteractions = new Set();
    
    new PerformanceObserver((entryList) => {
        for (const entry of entryList.getEntries()) {
            if (entry.interactionId && !processedInteractions.has(entry.interactionId)) {
                processedInteractions.add(entry.interactionId);
                inpValue = Math.max(inpValue, entry.duration);
                vitals.INP = inpValue;
                reportVital('INP', vitals.INP);
            }
        }
    }).observe({type: 'event', buffered: true, durationThreshold: 40});
    
    // Report vital to server
    function reportVital(name, value) {
        // Batch and send to analytics endpoint
        if (navigator.sendBeacon) {
            const data = JSON.stringify({
                metric: name,
                value: value,
                page: window.location.pathname,
                timestamp: Date.now()
            });
            
            navigator.sendBeacon('/api/v1/analytics/vitals', data);
        }
    }
    
    // Report all vitals on page unload
    window.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            const allVitals = Object.entries(vitals)
                .filter(([_, value]) => value !== null)
                .map(([name, value]) => ({name, value}));
                
            if (allVitals.length > 0 && navigator.sendBeacon) {
                navigator.sendBeacon('/api/v1/analytics/vitals/batch', 
                    JSON.stringify(allVitals));
            }
        }
    });
})();
"""


class BundleOptimizer:
    """Optimize JavaScript and CSS bundles"""
    
    def __init__(self):
        self.bundle_hashes: Dict[str, str] = {}
        
    def generate_critical_css(self, html: str, css: str) -> str:
        """Extract critical CSS for above-the-fold content"""
        # Simplified critical CSS extraction
        # In production, use tools like critical or penthouse
        critical_selectors = [
            'body', 'html', 'header', 'nav', 'main',
            '.hero', '.above-fold', '#app', '.container'
        ]
        
        critical_css = []
        for selector in critical_selectors:
            # Find CSS rules for selector
            pattern = rf'{re.escape(selector)}\s*{{[^}}]+}}'
            matches = re.findall(pattern, css, re.IGNORECASE)
            critical_css.extend(matches)
            
        return '\n'.join(critical_css)
        
    def inline_critical_resources(self, html: str, critical_css: str, 
                                critical_js: str = "") -> str:
        """Inline critical CSS and JS in HTML"""
        # Add critical CSS to head
        if critical_css:
            css_tag = f'<style>{critical_css}</style>'
            html = html.replace('</head>', f'{css_tag}</head>')
            
        # Add critical JS to head
        if critical_js:
            js_tag = f'<script>{critical_js}</script>'
            html = html.replace('</head>', f'{js_tag}</head>')
            
        return html
        
    def generate_resource_hints(self, resources: Dict[str, List[str]]) -> str:
        """Generate resource hints for HTML head"""
        hints = []
        
        # DNS prefetch
        for domain in resources.get('dns_prefetch', []):
            hints.append(f'<link rel="dns-prefetch" href="{domain}">')
            
        # Preconnect
        for domain in resources.get('preconnect', []):
            hints.append(f'<link rel="preconnect" href="{domain}" crossorigin>')
            
        # Prefetch
        for resource in resources.get('prefetch', []):
            hints.append(f'<link rel="prefetch" href="{resource}">')
            
        # Preload
        for resource in resources.get('preload', []):
            resource_type = self._get_resource_type(resource)
            hints.append(f'<link rel="preload" href="{resource}" as="{resource_type}">')
            
        return '\n'.join(hints)
        
    def _get_resource_type(self, url: str) -> str:
        """Determine resource type from URL"""
        if url.endswith('.js'):
            return 'script'
        elif url.endswith('.css'):
            return 'style'
        elif any(url.endswith(ext) for ext in ['.woff', '.woff2']):
            return 'font'
        elif any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return 'image'
        else:
            return 'fetch'