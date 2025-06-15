#!/usr/bin/env python3
"""
BoarderframeOS Unified Data Layer for Corporate Headquarters
Provides a single source of truth for all metrics and real-time updates
"""

import asyncio
import json
import logging
import time
import weakref
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class UnifiedDataLayer:
    """Central data management and synchronization layer for Corporate HQ"""

    def __init__(self):
        self._data_store = {
            "agents": {
                "total": 0,
                "active": 0,
                "productive": 0,
                "healthy": 0,
                "idle": 0,
                "details": {},
            },
            "leaders": {"total": 0, "active": 0, "hired": 0, "built": 0, "details": {}},
            "departments": {
                "total": 0,
                "active": 0,
                "planning": 0,
                "operational": 0,
                "details": {},
            },
            "divisions": {"total": 0, "active": 0, "details": {}},
            "servers": {
                "total": 10,  # Fixed count: 4 core + 4 mcp + 2 business
                "healthy": 0,
                "degraded": 0,
                "offline": 0,
                "details": {},
                "categories": {
                    "core": {"total": 4, "healthy": 0},
                    "mcp": {"total": 4, "healthy": 0},  # Fixed: 4 MCP servers
                    "business": {"total": 2, "healthy": 0},
                },
            },
            "database": {
                "connected": False,
                "tables": 0,
                "size_mb": 0,
                "connections": 0,
            },
            "registry": {"status": "unknown", "entries": 0, "last_check": None},
            "system": {
                "overall_status": "unknown",
                "health_score": 0,
                "last_refresh": None,
                "uptime": 0,
                "refresh_in_progress": False,
            },
            "metrics": {
                "refresh_count": 0,
                "last_refresh_duration": 0,
                "average_refresh_time": 0,
                "error_count": 0,
            },
        }

        # Cache configuration
        self._cache_ttl = 30  # seconds
        self._cache_timestamps = {}

        # Event subscribers using weakref to prevent memory leaks
        self._subscribers = defaultdict(set)

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Metrics tracking
        self._update_history = []
        self._max_history = 100

    async def get_all_data(self) -> Dict[str, Any]:
        """Get complete snapshot of all data"""
        async with self._lock:
            return self._data_store.copy()

    async def get_category(self, category: str) -> Dict[str, Any]:
        """Get data for a specific category"""
        async with self._lock:
            return self._data_store.get(category, {}).copy()

    async def update_category(
        self, category: str, data: Dict[str, Any], notify: bool = True
    ) -> bool:
        """Update an entire category of data"""
        try:
            async with self._lock:
                if category not in self._data_store:
                    logger.warning(f"Unknown category: {category}")
                    return False

                # Update data
                old_data = self._data_store[category].copy()
                self._data_store[category].update(data)
                self._cache_timestamps[category] = time.time()

                # Track update
                self._track_update(category, old_data, self._data_store[category])

            # Notify subscribers outside of lock
            if notify:
                await self._notify_subscribers(category, self._data_store[category])

            return True

        except Exception as e:
            logger.error(f"Error updating category {category}: {e}")
            return False

    async def update_metric(self, path: str, value: Any, notify: bool = True) -> bool:
        """Update a specific metric using dot notation (e.g., 'agents.active')"""
        try:
            parts = path.split(".")
            if not parts:
                return False

            async with self._lock:
                # Navigate to the target
                current = self._data_store
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Update the value
                old_value = current.get(parts[-1])
                current[parts[-1]] = value

                # Update cache timestamp for category
                self._cache_timestamps[parts[0]] = time.time()

                # Track update
                self._track_update(path, old_value, value)

            # Notify subscribers
            if notify:
                category = parts[0]
                await self._notify_subscribers(category, self._data_store[category])
                await self._notify_subscribers(path, value)

            return True

        except Exception as e:
            logger.error(f"Error updating metric {path}: {e}")
            return False

    async def calculate_health_score(self) -> int:
        """Calculate overall system health score (0-100)"""
        try:
            async with self._lock:
                scores = []

                # Agent health (30% weight)
                if self._data_store["agents"]["total"] > 0:
                    agent_score = (
                        self._data_store["agents"]["active"]
                        / self._data_store["agents"]["total"]
                    ) * 100
                    scores.append(agent_score * 0.3)

                # Server health (30% weight)
                if self._data_store["servers"]["total"] > 0:
                    server_score = (
                        self._data_store["servers"]["healthy"]
                        / self._data_store["servers"]["total"]
                    ) * 100
                    scores.append(server_score * 0.3)

                # Department health (20% weight)
                if self._data_store["departments"]["total"] > 0:
                    dept_score = (
                        self._data_store["departments"]["active"]
                        / self._data_store["departments"]["total"]
                    ) * 100
                    scores.append(dept_score * 0.2)

                # Database health (10% weight)
                db_score = 100 if self._data_store["database"]["connected"] else 0
                scores.append(db_score * 0.1)

                # Registry health (10% weight)
                reg_score = (
                    100 if self._data_store["registry"]["status"] == "healthy" else 0
                )
                scores.append(reg_score * 0.1)

                # Calculate final score
                health_score = int(sum(scores))

                # Update system health score
                self._data_store["system"]["health_score"] = health_score

                # Determine overall status
                if health_score >= 90:
                    status = "online"
                elif health_score >= 70:
                    status = "warning"
                else:
                    status = "critical"

                self._data_store["system"]["overall_status"] = status

            return health_score

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0

    async def subscribe(self, pattern: str, callback: Callable) -> str:
        """Subscribe to data changes matching pattern"""
        subscriber_id = f"{id(callback)}_{time.time()}"
        weak_callback = weakref.ref(callback)
        self._subscribers[pattern].add((subscriber_id, weak_callback))
        return subscriber_id

    async def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from data changes"""
        for pattern, subscribers in self._subscribers.items():
            self._subscribers[pattern] = {
                (sid, cb) for sid, cb in subscribers if sid != subscriber_id
            }

    async def _notify_subscribers(self, category: str, data: Any):
        """Notify all subscribers of data changes"""
        patterns_to_check = [category, "*", f"{category}.*"]

        for pattern in patterns_to_check:
            if pattern in self._subscribers:
                # Clean up dead references
                active_subscribers = []
                for subscriber_id, weak_callback in self._subscribers[pattern]:
                    callback = weak_callback()
                    if callback:
                        active_subscribers.append((subscriber_id, weak_callback))
                        try:
                            await callback(category, data)
                        except Exception as e:
                            logger.error(f"Error in subscriber callback: {e}")

                self._subscribers[pattern] = set(active_subscribers)

    def _track_update(self, path: str, old_value: Any, new_value: Any):
        """Track update history for metrics"""
        update_record = {
            "timestamp": datetime.now().isoformat(),
            "path": path,
            "old_value": old_value,
            "new_value": new_value,
        }

        self._update_history.append(update_record)

        # Maintain history limit
        if len(self._update_history) > self._max_history:
            self._update_history = self._update_history[-self._max_history :]

    async def get_update_history(self, path: Optional[str] = None) -> List[Dict]:
        """Get update history, optionally filtered by path"""
        if path:
            return [u for u in self._update_history if u["path"] == path]
        return self._update_history.copy()

    async def get_trends(
        self, metric_path: str, duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get trend data for a specific metric"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)

        relevant_updates = [
            u
            for u in self._update_history
            if u["path"] == metric_path
            and datetime.fromisoformat(u["timestamp"]) > cutoff_time
        ]

        if not relevant_updates:
            return {"trend": "stable", "change_percent": 0, "data_points": []}

        # Calculate trend
        values = [
            u["new_value"]
            for u in relevant_updates
            if isinstance(u["new_value"], (int, float))
        ]
        if len(values) >= 2:
            change = values[-1] - values[0]
            change_percent = (change / values[0] * 100) if values[0] != 0 else 0

            if change_percent > 5:
                trend = "up"
            elif change_percent < -5:
                trend = "down"
            else:
                trend = "stable"

            return {
                "trend": trend,
                "change_percent": round(change_percent, 2),
                "data_points": values[-20:],  # Last 20 points
            }

        return {"trend": "stable", "change_percent": 0, "data_points": values}

    def is_cache_valid(self, category: str) -> bool:
        """Check if cached data is still valid"""
        if category not in self._cache_timestamps:
            return False

        age = time.time() - self._cache_timestamps[category]
        return age < self._cache_ttl

    async def force_refresh(self, category: Optional[str] = None):
        """Force refresh of cached data"""
        if category:
            self._cache_timestamps.pop(category, None)
        else:
            self._cache_timestamps.clear()


# Global instance
_unified_data_layer = None


def get_unified_data_layer() -> UnifiedDataLayer:
    """Get the global unified data layer instance"""
    global _unified_data_layer
    if _unified_data_layer is None:
        _unified_data_layer = UnifiedDataLayer()
    return _unified_data_layer
