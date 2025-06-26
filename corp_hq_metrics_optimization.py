#!/usr/bin/env python3
"""
Corporate HQ Metrics Optimization - Fix Timeout Issues
Implements caching and parallel processing for better performance
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from concurrent.futures import ThreadPoolExecutor
import functools


class MetricsCache:
    """In-memory cache for metrics data"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
        
    def set(self, key: str, value: Any) -> None:
        """Store value in cache with timestamp"""
        self.cache[key] = (value, time.time())
        
    def invalidate(self, pattern: str = None) -> None:
        """Invalidate cache entries matching pattern"""
        if pattern is None:
            self.cache.clear()
        else:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]


class OptimizedMetricsHandler:
    """Optimized metrics handler with caching and parallel processing"""
    
    def __init__(self, dashboard_data):
        self.dashboard = dashboard_data
        self.cache = MetricsCache(ttl_seconds=60)  # 1 minute cache
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.mcp_servers = {
            "registry": 8000,
            "filesystem": 8001,
            "database_postgres": 8010,
            "analytics": 8007,
            "payment": 8006,
            "customer": 8008,
            "llm": 8005,
            "screenshot": 8011
        }
        
    async def get_metrics_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get metrics data with caching"""
        cache_key = "metrics_data"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
                
        # Fetch fresh data in parallel
        metrics = await self._fetch_metrics_parallel()
        
        # Cache the results
        self.cache.set(cache_key, metrics)
        
        return metrics
        
    async def _fetch_metrics_parallel(self) -> Dict[str, Any]:
        """Fetch all metrics in parallel for speed"""
        tasks = [
            self._get_agent_metrics(),
            self._get_server_metrics(),
            self._get_department_metrics(),
            self._get_database_metrics(),
            self._get_system_metrics()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics = {
            "agents": results[0] if not isinstance(results[0], Exception) else {},
            "servers": results[1] if not isinstance(results[1], Exception) else {},
            "departments": results[2] if not isinstance(results[2], Exception) else {},
            "database": results[3] if not isinstance(results[3], Exception) else {},
            "system": results[4] if not isinstance(results[4], Exception) else {},
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
        
        return metrics
        
    async def _get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent metrics from database"""
        try:
            # Use existing dashboard data if available
            agents_data = self.dashboard.unified_data.get("agents_status", {})
            
            running_count = len([a for a in agents_data.values() if a.get("status") == "running"])
            total_count = len(agents_data)
            
            return {
                "total": total_count,
                "running": running_count,
                "stopped": total_count - running_count,
                "agents": agents_data
            }
        except Exception as e:
            return {"error": str(e), "total": 0, "running": 0}
            
    async def _get_server_metrics(self) -> Dict[str, Any]:
        """Get server metrics with parallel health checks"""
        server_statuses = {}
        
        # Use small timeout for individual checks
        timeout = httpx.Timeout(3.0, connect=1.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = []
            for server_name, port in self.mcp_servers.items():
                task = self._check_server_health(client, server_name, port)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for (server_name, _), result in zip(self.mcp_servers.items(), results):
                if isinstance(result, Exception):
                    server_statuses[server_name] = {
                        "status": "offline",
                        "error": str(result),
                        "port": self.mcp_servers[server_name]
                    }
                else:
                    server_statuses[server_name] = result
                    
        # Add core infrastructure servers
        server_statuses["corporate_headquarters"] = {
            "status": "healthy",
            "port": 8888,
            "response_time": 0.001
        }
        
        healthy_count = len([s for s in server_statuses.values() if s.get("status") == "healthy"])
        
        return {
            "total": len(server_statuses),
            "healthy": healthy_count,
            "unhealthy": len(server_statuses) - healthy_count,
            "servers": server_statuses
        }
        
    async def _check_server_health(self, client: httpx.AsyncClient, server_name: str, port: int) -> Dict[str, Any]:
        """Check individual server health"""
        start_time = time.time()
        
        try:
            response = await client.get(f"http://localhost:{port}/health")
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "port": port,
                    "response_time": elapsed,
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "port": port,
                    "status_code": response.status_code,
                    "response_time": elapsed
                }
                
        except Exception as e:
            return {
                "status": "offline",
                "port": port,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            
    async def _get_department_metrics(self) -> Dict[str, Any]:
        """Get department metrics"""
        try:
            departments_data = self.dashboard.unified_data.get("departments_data", {})
            
            active_count = len([d for d in departments_data.values() if d.get("status") == "active"])
            
            return {
                "total": len(departments_data),
                "active": active_count,
                "planning": len(departments_data) - active_count,
                "departments": departments_data
            }
        except Exception as e:
            return {"error": str(e), "total": 0, "active": 0}
            
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database metrics"""
        try:
            db_health = self.dashboard.unified_data.get("database_health", {})
            
            return {
                "status": db_health.get("status", "unknown"),
                "size": db_health.get("size", "0 MB"),
                "tables": db_health.get("tables", 0),
                "connections": db_health.get("connections", 0),
                "uptime": db_health.get("uptime", "unknown")
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
            
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            }
        except Exception as e:
            return {"error": str(e)}
            
    def invalidate_cache(self, category: Optional[str] = None) -> None:
        """Invalidate cache for specific category or all"""
        if category:
            self.cache.invalidate(category)
        else:
            self.cache.invalidate()


def integrate_optimized_metrics(dashboard_data):
    """Integrate optimized metrics handler into Corporate HQ"""
    
    # Create optimized handler
    optimized_handler = OptimizedMetricsHandler(dashboard_data)
    
    # Store reference in dashboard
    dashboard_data.optimized_metrics = optimized_handler
    
    # Monkey-patch the metrics data method
    async def get_metrics_data_optimized(force_refresh=False):
        return await optimized_handler.get_metrics_data(force_refresh)
    
    dashboard_data.get_metrics_data = get_metrics_data_optimized
    
    print("✅ Optimized metrics handler integrated")
    print("   - 60 second cache for metrics data")
    print("   - Parallel health checks for all servers")
    print("   - 3 second timeout per server (vs 15s total)")
    print("   - Automatic cache invalidation")
    
    return optimized_handler


if __name__ == "__main__":
    print("Corporate HQ Metrics Optimization Module")
    print("=" * 60)
    print("This module provides:")
    print("1. In-memory caching for metrics (60s TTL)")
    print("2. Parallel server health checks")
    print("3. Reduced timeouts (3s per server)")
    print("4. Cache invalidation support")
    print("\nIntegrate by importing and calling:")
    print("  from corp_hq_metrics_optimization import integrate_optimized_metrics")
    print("  integrate_optimized_metrics(dashboard_data)")