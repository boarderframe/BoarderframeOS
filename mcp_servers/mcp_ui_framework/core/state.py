"""
State Management for MCP-UI Framework
Server-side state persistence and client synchronization
"""

from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import logging
from collections import defaultdict
import pickle
import hashlib


# ============================================================================
# State Events
# ============================================================================

class StateEventType(str, Enum):
    """State event types"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTORED = "restored"
    SYNCED = "synced"


class StateEvent:
    """State change event"""
    
    def __init__(
        self,
        event_type: StateEventType,
        key: str,
        value: Any,
        previous_value: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.type = event_type
        self.key = key
        self.value = value
        self.previous_value = previous_value
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique event ID"""
        data = f"{self.type}-{self.key}-{self.timestamp.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "key": self.key,
            "value": self.value,
            "previous_value": self.previous_value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# State Store
# ============================================================================

class StateStore:
    """
    Persistent state storage
    Supports multiple backends (memory, file, redis, etc.)
    """
    
    def __init__(self, backend: str = "memory", **backend_config):
        """
        Initialize state store
        
        Args:
            backend: Storage backend (memory, file, redis)
            **backend_config: Backend-specific configuration
        """
        self.backend = backend
        self.backend_config = backend_config
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize storage backend"""
        if self.backend == "memory":
            self.data = {}
        elif self.backend == "file":
            self._load_from_file()
        elif self.backend == "redis":
            self._connect_redis()
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from store
        
        Args:
            key: State key
            default: Default value if not found
            
        Returns:
            Stored value or default
        """
        if self.backend == "redis":
            return await self._get_redis(key, default)
        
        return self.data.get(key, default)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in store
        
        Args:
            key: State key
            value: Value to store
            ttl: Time to live in seconds
        """
        if self.backend == "redis":
            await self._set_redis(key, value, ttl)
        else:
            self.data[key] = value
            
            if ttl:
                self.metadata[key] = {
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }
            
            if self.backend == "file":
                self._save_to_file()
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from store
        
        Args:
            key: State key
            
        Returns:
            True if deleted, False if not found
        """
        if self.backend == "redis":
            return await self._delete_redis(key)
        
        if key in self.data:
            del self.data[key]
            self.metadata.pop(key, None)
            
            if self.backend == "file":
                self._save_to_file()
            
            return True
        
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self.backend == "redis":
            return await self._exists_redis(key)
        
        # Check expiration
        if key in self.metadata:
            expires = self.metadata[key].get("expires")
            if expires and datetime.now() > expires:
                await self.delete(key)
                return False
        
        return key in self.data
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern
        
        Args:
            pattern: Key pattern (supports * wildcard)
            
        Returns:
            List of matching keys
        """
        if self.backend == "redis":
            return await self._keys_redis(pattern)
        
        # Clean expired keys
        await self._clean_expired()
        
        if pattern == "*":
            return list(self.data.keys())
        
        # Simple pattern matching
        import fnmatch
        return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]
    
    async def clear(self) -> None:
        """Clear all data"""
        if self.backend == "redis":
            await self._clear_redis()
        else:
            self.data.clear()
            self.metadata.clear()
            
            if self.backend == "file":
                self._save_to_file()
    
    async def _clean_expired(self):
        """Remove expired keys"""
        now = datetime.now()
        expired_keys = []
        
        for key, meta in self.metadata.items():
            expires = meta.get("expires")
            if expires and now > expires:
                expired_keys.append(key)
        
        for key in expired_keys:
            await self.delete(key)
    
    # File backend methods
    def _load_from_file(self):
        """Load state from file"""
        file_path = self.backend_config.get("file_path", "state.pkl")
        try:
            with open(file_path, "rb") as f:
                stored = pickle.load(f)
                self.data = stored.get("data", {})
                self.metadata = stored.get("metadata", {})
        except FileNotFoundError:
            self.data = {}
            self.metadata = {}
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            self.data = {}
            self.metadata = {}
    
    def _save_to_file(self):
        """Save state to file"""
        file_path = self.backend_config.get("file_path", "state.pkl")
        try:
            with open(file_path, "wb") as f:
                pickle.dump({
                    "data": self.data,
                    "metadata": self.metadata
                }, f)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    # Redis backend methods (placeholders)
    def _connect_redis(self):
        """Connect to Redis"""
        # Implement Redis connection
        pass
    
    async def _get_redis(self, key: str, default: Any) -> Any:
        """Get from Redis"""
        # Implement Redis get
        return default
    
    async def _set_redis(self, key: str, value: Any, ttl: Optional[int]):
        """Set in Redis"""
        # Implement Redis set
        pass
    
    async def _delete_redis(self, key: str) -> bool:
        """Delete from Redis"""
        # Implement Redis delete
        return False
    
    async def _exists_redis(self, key: str) -> bool:
        """Check existence in Redis"""
        # Implement Redis exists
        return False
    
    async def _keys_redis(self, pattern: str) -> List[str]:
        """Get keys from Redis"""
        # Implement Redis keys
        return []
    
    async def _clear_redis(self):
        """Clear Redis data"""
        # Implement Redis clear
        pass


# ============================================================================
# State Snapshot
# ============================================================================

class StateSnapshot:
    """Point-in-time state snapshot"""
    
    def __init__(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        self.data = data.copy()
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate snapshot ID"""
        data_str = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:12]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from snapshot"""
        return self.data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# State Manager
# ============================================================================

class StateManager:
    """
    Central state management system
    Handles state persistence, synchronization, and event sourcing
    """
    
    def __init__(
        self,
        store_backend: str = "memory",
        enable_snapshots: bool = True,
        enable_events: bool = True,
        **store_config
    ):
        """
        Initialize state manager
        
        Args:
            store_backend: Storage backend type
            enable_snapshots: Enable state snapshots
            enable_events: Enable event sourcing
            **store_config: Store configuration
        """
        self.store = StateStore(store_backend, **store_config)
        self.enable_snapshots = enable_snapshots
        self.enable_events = enable_events
        
        # Event handling
        self.events: List[StateEvent] = []
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Snapshots
        self.snapshots: List[StateSnapshot] = []
        self.max_snapshots = 10
        
        # Cache
        self.cache: Dict[str, Any] = {}
        self.cache_stats = {"hits": 0, "misses": 0}
        
        # Sync tracking
        self.sync_callbacks: List[Callable] = []
        self.last_sync = datetime.now()
        
        self.logger = logging.getLogger(__name__)
    
    async def get(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """
        Get state value
        
        Args:
            key: State key
            default: Default value
            use_cache: Use cache if available
            
        Returns:
            State value or default
        """
        # Check cache
        if use_cache and key in self.cache:
            self.cache_stats["hits"] += 1
            return self.cache[key]
        
        self.cache_stats["misses"] += 1
        
        # Get from store
        value = await self.store.get(key, default)
        
        # Update cache
        if use_cache and value is not None:
            self.cache[key] = value
        
        return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        emit_event: bool = True
    ) -> None:
        """
        Set state value
        
        Args:
            key: State key
            value: Value to set
            ttl: Time to live in seconds
            emit_event: Emit state change event
        """
        # Get previous value
        previous = await self.store.get(key)
        
        # Set in store
        await self.store.set(key, value, ttl)
        
        # Update cache
        self.cache[key] = value
        
        # Emit event
        if emit_event and self.enable_events:
            event = StateEvent(
                StateEventType.UPDATED if previous is not None else StateEventType.CREATED,
                key,
                value,
                previous
            )
            await self._emit_event(event)
    
    async def delete(self, key: str, emit_event: bool = True) -> bool:
        """
        Delete state value
        
        Args:
            key: State key
            emit_event: Emit deletion event
            
        Returns:
            True if deleted
        """
        # Get value for event
        value = await self.store.get(key)
        
        # Delete from store
        result = await self.store.delete(key)
        
        # Clear cache
        self.cache.pop(key, None)
        
        # Emit event
        if result and emit_event and self.enable_events:
            event = StateEvent(StateEventType.DELETED, key, None, value)
            await self._emit_event(event)
        
        return result
    
    async def update(
        self,
        key: str,
        updater: Callable[[Any], Any],
        default: Any = None
    ) -> Any:
        """
        Update state value atomically
        
        Args:
            key: State key
            updater: Function to update value
            default: Default if key doesn't exist
            
        Returns:
            Updated value
        """
        current = await self.get(key, default)
        updated = updater(current)
        await self.set(key, updated)
        return updated
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values"""
        result = {}
        for key in keys:
            result[key] = await self.get(key)
        return result
    
    async def batch_set(self, updates: Dict[str, Any]) -> None:
        """Set multiple values"""
        for key, value in updates.items():
            await self.set(key, value)
    
    # Event handling
    def on_event(self, event_type: StateEventType, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event: StateEvent):
        """Emit state event"""
        self.events.append(event)
        
        # Call handlers
        for handler in self.event_handlers.get(event.type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}", exc_info=True)
        
        # Call generic handlers
        for handler in self.event_handlers.get("*", []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}", exc_info=True)
    
    def get_events(
        self,
        since: Optional[datetime] = None,
        event_type: Optional[StateEventType] = None
    ) -> List[StateEvent]:
        """Get events"""
        events = self.events
        
        if since:
            events = [e for e in events if e.timestamp > since]
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        return events
    
    # Snapshots
    async def create_snapshot(self, metadata: Optional[Dict[str, Any]] = None) -> StateSnapshot:
        """Create state snapshot"""
        if not self.enable_snapshots:
            raise RuntimeError("Snapshots are disabled")
        
        # Get all state
        keys = await self.store.keys()
        data = {}
        for key in keys:
            data[key] = await self.store.get(key)
        
        # Create snapshot
        snapshot = StateSnapshot(data, metadata)
        self.snapshots.append(snapshot)
        
        # Limit snapshots
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
        
        self.logger.info(f"Created snapshot: {snapshot.id}")
        return snapshot
    
    async def restore_snapshot(self, snapshot_id: str) -> bool:
        """
        Restore from snapshot
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            True if restored
        """
        # Find snapshot
        snapshot = None
        for s in self.snapshots:
            if s.id == snapshot_id:
                snapshot = s
                break
        
        if not snapshot:
            self.logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        # Clear current state
        await self.store.clear()
        self.cache.clear()
        
        # Restore data
        for key, value in snapshot.data.items():
            await self.store.set(key, value)
        
        # Emit event
        if self.enable_events:
            event = StateEvent(
                StateEventType.RESTORED,
                "*",
                snapshot.data,
                metadata={"snapshot_id": snapshot_id}
            )
            await self._emit_event(event)
        
        self.logger.info(f"Restored from snapshot: {snapshot_id}")
        return True
    
    def get_snapshots(self) -> List[StateSnapshot]:
        """Get all snapshots"""
        return self.snapshots.copy()
    
    # Synchronization
    def on_sync(self, callback: Callable):
        """Register sync callback"""
        self.sync_callbacks.append(callback)
    
    async def sync(self) -> Dict[str, Any]:
        """
        Synchronize state with clients
        
        Returns:
            Current state for synchronization
        """
        # Get all state
        keys = await self.store.keys()
        state = {}
        for key in keys:
            state[key] = await self.store.get(key)
        
        # Call sync callbacks
        for callback in self.sync_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                self.logger.error(f"Sync callback error: {e}", exc_info=True)
        
        self.last_sync = datetime.now()
        
        # Emit sync event
        if self.enable_events:
            event = StateEvent(
                StateEventType.SYNCED,
                "*",
                state,
                metadata={"sync_time": self.last_sync.isoformat()}
            )
            await self._emit_event(event)
        
        return state
    
    # Cache management
    def clear_cache(self):
        """Clear cache"""
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total if total > 0 else 0
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "size": len(self.cache)
        }
    
    def get_avg_response_time(self) -> float:
        """Get average response time (placeholder)"""
        # Implement actual timing metrics
        return 0.05  # 50ms placeholder
    
    # Cleanup
    async def close(self):
        """Close state manager"""
        # Save final snapshot if enabled
        if self.enable_snapshots:
            await self.create_snapshot({"reason": "shutdown"})
        
        # Clear resources
        self.cache.clear()
        self.event_handlers.clear()
        self.sync_callbacks.clear()
        
        self.logger.info("State manager closed")