"""
BoarderframeOS Registry Client
==============================

A high-performance async client for interacting with the Enhanced Registry System.
Provides simple interfaces for agents, servers, and other components to register
themselves and discover other services.

Features:
- Automatic registration and heartbeat management
- Service discovery with caching
- Event subscriptions via WebSockets
- Retry logic and connection pooling
- Type-safe interfaces for all registry operations
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import websockets
from websockets.exceptions import WebSocketException

from .enhanced_registry_system import (
    AgentRegistryEntry,
    BaseRegistryEntry,
    DatabaseRegistryEntry,
    DepartmentRegistryEntry,
    DivisionRegistryEntry,
    EventType,
    HealthStatus,
    LeaderRegistryEntry,
    LeadershipTier,
    RegistryEvent,
    RegistryType,
    ServerRegistryEntry,
    ServerType,
    ServiceStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class RegistryConfig:
    """Configuration for registry client"""
    registry_url: str = "http://localhost:8100"
    websocket_url: str = "ws://localhost:8100/ws"
    heartbeat_interval: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    timeout: int = 10  # seconds
    enable_caching: bool = True
    cache_ttl: int = 60  # seconds


class RegistryClient:
    """
    Async client for the Enhanced Registry System
    """

    def __init__(self, config: Optional[RegistryConfig] = None):
        self.config = config or RegistryConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._websocket_task: Optional[asyncio.Task] = None
        self._registered_entity: Optional[BaseRegistryEntry] = None
        self._event_handlers: Dict[EventType, List[Callable]] = {}
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        """Establish connection to registry"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

        # Test connection
        try:
            async with self.session.get(f"{self.config.registry_url}/health") as response:
                if response.status != 200:
                    raise ConnectionError(f"Registry health check failed: {response.status}")
            logger.info("Successfully connected to registry")
        except Exception as e:
            logger.error(f"Failed to connect to registry: {e}")
            raise

    async def disconnect(self):
        """Close all connections"""
        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        if self._websocket_task:
            self._websocket_task.cancel()
            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass

        if self.websocket:
            await self.websocket.close()

        # Close HTTP session
        if self.session:
            await self.session.close()

    # ==================== Registration ====================

    async def register_agent(
        self,
        name: str,
        agent_id: Optional[str] = None,
        department_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        llm_model: str = "gpt-4",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentRegistryEntry:
        """Register an AI agent"""
        agent = AgentRegistryEntry(
            id=agent_id or kwargs.get("id", None),
            name=name,
            department_id=department_id,
            capabilities=capabilities or [],
            llm_model=llm_model,
            metadata=metadata or {},
            **kwargs
        )

        result = await self._register_entity(agent)
        if isinstance(result, AgentRegistryEntry):
            await self._start_heartbeat()
            return result
        raise TypeError("Unexpected response type")

    async def register_leader(
        self,
        name: str,
        leader_id: Optional[str] = None,
        leadership_tier: LeadershipTier = LeadershipTier.DEPARTMENT,
        departments_managed: Optional[List[str]] = None,
        biblical_archetype: Optional[str] = None,
        **kwargs
    ) -> LeaderRegistryEntry:
        """Register a leader"""
        leader = LeaderRegistryEntry(
            id=leader_id or kwargs.get("id", None),
            name=name,
            leadership_tier=leadership_tier,
            departments_managed=departments_managed or [],
            biblical_archetype=biblical_archetype,
            **kwargs
        )

        result = await self._register_entity(leader)
        if isinstance(result, LeaderRegistryEntry):
            await self._start_heartbeat()
            return result
        raise TypeError("Unexpected response type")

    async def register_department(
        self,
        name: str,
        division_id: str,
        department_id: Optional[str] = None,
        leader_ids: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        **kwargs
    ) -> DepartmentRegistryEntry:
        """Register a department"""
        department = DepartmentRegistryEntry(
            id=department_id or kwargs.get("id", None),
            name=name,
            division_id=division_id,
            leader_ids=leader_ids or [],
            capabilities=capabilities or [],
            **kwargs
        )

        result = await self._register_entity(department)
        if isinstance(result, DepartmentRegistryEntry):
            return result
        raise TypeError("Unexpected response type")

    async def register_server(
        self,
        name: str,
        server_type: ServerType,
        host: str,
        port: int,
        server_id: Optional[str] = None,
        protocol: str = "http",
        endpoints: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> ServerRegistryEntry:
        """Register a server"""
        server = ServerRegistryEntry(
            id=server_id or kwargs.get("id", None),
            name=name,
            type=f"server_{server_type.value}",
            server_type=server_type,
            host=host,
            port=port,
            protocol=protocol,
            endpoints=endpoints or [],
            **kwargs
        )

        result = await self._register_entity(server)
        if isinstance(result, ServerRegistryEntry):
            await self._start_heartbeat()
            return result
        raise TypeError("Unexpected response type")

    async def register_database(
        self,
        name: str,
        db_type: str,
        host: str,
        port: int,
        database_id: Optional[str] = None,
        database_name: Optional[str] = None,
        **kwargs
    ) -> DatabaseRegistryEntry:
        """Register a database"""
        database = DatabaseRegistryEntry(
            id=database_id or kwargs.get("id", None),
            name=name,
            db_type=db_type,
            host=host,
            port=port,
            database_name=database_name,
            **kwargs
        )

        result = await self._register_entity(database)
        if isinstance(result, DatabaseRegistryEntry):
            await self._start_heartbeat()
            return result
        raise TypeError("Unexpected response type")

    async def _register_entity(self, entity: BaseRegistryEntry) -> BaseRegistryEntry:
        """Internal method to register any entity"""
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.post(
                    f"{self.config.registry_url}/register/{entity.type}",
                    json=entity.dict()
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._registered_entity = self._parse_entity(data["entity"])
                        logger.info(f"Successfully registered {entity.type}: {entity.name}")
                        return self._registered_entity
                    else:
                        error = await response.text()
                        raise Exception(f"Registration failed: {error}")

            except Exception as e:
                logger.error(f"Registration attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    raise

    # ==================== Discovery ====================

    async def discover_agents(
        self,
        status: Optional[ServiceStatus] = None,
        capability: Optional[str] = None,
        department_id: Optional[str] = None,
        division_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentRegistryEntry]:
        """Discover AI agents"""
        entities = await self._discover(
            RegistryType.AGENT,
            status=status,
            capability=capability,
            department_id=department_id,
            division_id=division_id,
            limit=limit
        )
        return [e for e in entities if isinstance(e, AgentRegistryEntry)]

    async def discover_leaders(
        self,
        leadership_tier: Optional[LeadershipTier] = None,
        department_id: Optional[str] = None,
        division_id: Optional[str] = None
    ) -> List[LeaderRegistryEntry]:
        """Discover leaders"""
        entities = await self._discover(
            RegistryType.LEADER,
            department_id=department_id,
            division_id=division_id
        )

        leaders = [e for e in entities if isinstance(e, LeaderRegistryEntry)]

        # Filter by tier if specified
        if leadership_tier:
            leaders = [l for l in leaders if l.leadership_tier == leadership_tier]

        return leaders

    async def discover_departments(
        self,
        division_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[DepartmentRegistryEntry]:
        """Discover departments"""
        entities = await self._discover(
            RegistryType.DEPARTMENT,
            division_id=division_id
        )

        departments = [e for e in entities if isinstance(e, DepartmentRegistryEntry)]

        # Filter by operational status if specified
        if status:
            departments = [d for d in departments if d.operational_status == status]

        return departments

    async def discover_servers(
        self,
        server_type: Optional[ServerType] = None,
        status: Optional[ServiceStatus] = None,
        capability: Optional[str] = None
    ) -> List[ServerRegistryEntry]:
        """Discover servers"""
        # Determine registry type based on server type
        if server_type == ServerType.MCP_SERVER:
            registry_type = RegistryType.SERVER_MCP
        elif server_type == ServerType.BUSINESS_SERVICE:
            registry_type = RegistryType.SERVER_BUSINESS
        else:
            registry_type = RegistryType.SERVER_CORE

        entities = await self._discover(
            registry_type,
            status=status,
            capability=capability
        )

        return [e for e in entities if isinstance(e, ServerRegistryEntry)]

    async def discover_databases(
        self,
        db_type: Optional[str] = None,
        status: Optional[ServiceStatus] = None
    ) -> List[DatabaseRegistryEntry]:
        """Discover databases"""
        entities = await self._discover(
            RegistryType.DATABASE,
            status=status
        )

        databases = [e for e in entities if isinstance(e, DatabaseRegistryEntry)]

        # Filter by database type if specified
        if db_type:
            databases = [d for d in databases if d.db_type == db_type]

        return databases

    async def _discover(
        self,
        entity_type: RegistryType,
        **filters
    ) -> List[BaseRegistryEntry]:
        """Internal discovery method with caching"""
        # Check cache first
        cache_key = f"discover:{entity_type}:{json.dumps(filters, sort_keys=True)}"
        if self.config.enable_caching:
            cached = self._get_cached(cache_key)
            if cached:
                return cached

        # Make request
        params = {k: v for k, v in filters.items() if v is not None}

        try:
            async with self.session.get(
                f"{self.config.registry_url}/discover/{entity_type}",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    entities = [self._parse_entity(e) for e in data["entities"]]

                    # Cache result
                    if self.config.enable_caching:
                        self._set_cached(cache_key, entities)

                    return entities
                else:
                    error = await response.text()
                    raise Exception(f"Discovery failed: {error}")

        except Exception as e:
            logger.error(f"Discovery error: {e}")
            return []

    # ==================== Entity Operations ====================

    async def get_entity(self, entity_id: str) -> Optional[BaseRegistryEntry]:
        """Get specific entity by ID"""
        # Check cache
        cache_key = f"entity:{entity_id}"
        if self.config.enable_caching:
            cached = self._get_cached(cache_key)
            if cached:
                return cached

        try:
            async with self.session.get(
                f"{self.config.registry_url}/entity/{entity_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    entity = self._parse_entity(data)

                    # Cache result
                    if self.config.enable_caching:
                        self._set_cached(cache_key, entity)

                    return entity
                elif response.status == 404:
                    return None
                else:
                    error = await response.text()
                    raise Exception(f"Get entity failed: {error}")

        except Exception as e:
            logger.error(f"Get entity error: {e}")
            return None

    async def update_status(self, entity_id: str, status: ServiceStatus):
        """Update entity status"""
        await self.update_entity(entity_id, {"status": status})

    async def update_entity(self, entity_id: str, updates: Dict[str, Any]):
        """Update entity properties"""
        try:
            async with self.session.put(
                f"{self.config.registry_url}/entity/{entity_id}",
                json=updates
            ) as response:
                if response.status == 200:
                    # Invalidate cache
                    self._invalidate_cache(f"entity:{entity_id}")
                    logger.info(f"Successfully updated entity {entity_id}")
                else:
                    error = await response.text()
                    raise Exception(f"Update failed: {error}")

        except Exception as e:
            logger.error(f"Update entity error: {e}")
            raise

    async def unregister(self, entity_id: Optional[str] = None):
        """Unregister entity from registry"""
        entity_id = entity_id or (self._registered_entity.id if self._registered_entity else None)
        if not entity_id:
            raise ValueError("No entity ID provided")

        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        try:
            async with self.session.delete(
                f"{self.config.registry_url}/entity/{entity_id}"
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully unregistered entity {entity_id}")
                    self._registered_entity = None
                else:
                    error = await response.text()
                    raise Exception(f"Unregister failed: {error}")

        except Exception as e:
            logger.error(f"Unregister error: {e}")
            raise

    # ==================== Heartbeat Management ====================

    async def _start_heartbeat(self):
        """Start automatic heartbeat for registered entity"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self._registered_entity:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self._registered_entity:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def send_heartbeat(self, entity_id: Optional[str] = None):
        """Send heartbeat for entity"""
        entity_id = entity_id or (self._registered_entity.id if self._registered_entity else None)
        if not entity_id:
            raise ValueError("No entity ID provided")

        try:
            async with self.session.post(
                f"{self.config.registry_url}/entity/{entity_id}/heartbeat"
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Heartbeat failed: {error}")

        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            raise

    # ==================== Event Subscriptions ====================

    async def subscribe_to_events(
        self,
        event_types: Optional[List[EventType]] = None,
        entity_types: Optional[List[RegistryType]] = None
    ):
        """Subscribe to registry events via WebSocket"""
        if self._websocket_task:
            return  # Already subscribed

        self._websocket_task = asyncio.create_task(
            self._websocket_handler(event_types, entity_types)
        )

    async def _websocket_handler(
        self,
        event_types: Optional[List[EventType]],
        entity_types: Optional[List[RegistryType]]
    ):
        """Handle WebSocket connection and events"""
        while True:
            try:
                async with websockets.connect(self.config.websocket_url) as websocket:
                    self.websocket = websocket

                    # Subscribe to entity types
                    if entity_types:
                        await websocket.send(json.dumps({
                            "command": "subscribe",
                            "entity_types": entity_types
                        }))

                    # Listen for events
                    async for message in websocket:
                        try:
                            event_data = json.loads(message)
                            event = RegistryEvent(**event_data)

                            # Filter by event type if specified
                            if event_types and event.event_type not in event_types:
                                continue

                            # Call handlers
                            await self._handle_event(event)

                        except Exception as e:
                            logger.error(f"Error processing event: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(self.config.retry_delay)

    async def _handle_event(self, event: RegistryEvent):
        """Handle incoming registry event"""
        # Invalidate relevant caches
        if event.event_type in [EventType.REGISTERED, EventType.UNREGISTERED,
                               EventType.STATUS_CHANGED]:
            self._invalidate_cache(f"entity:{event.entity_id}")
            self._invalidate_cache(f"discover:{event.entity_type}:*")

        # Call registered handlers
        if event.event_type in self._event_handlers:
            for handler in self._event_handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

    def on_event(self, event_type: EventType, handler: Callable):
        """Register event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    # ==================== Special Operations ====================

    async def assign_agent_to_department(self, agent_id: str, department_id: str):
        """Assign an agent to a department"""
        try:
            async with self.session.post(
                f"{self.config.registry_url}/assign/agent/{agent_id}/department/{department_id}"
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully assigned agent {agent_id} to department {department_id}")
                else:
                    error = await response.text()
                    raise Exception(f"Assignment failed: {error}")

        except Exception as e:
            logger.error(f"Assignment error: {e}")
            raise

    async def get_organizational_hierarchy(self) -> Dict[str, Any]:
        """Get complete organizational hierarchy"""
        try:
            async with self.session.get(
                f"{self.config.registry_url}/hierarchy/divisions"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Get hierarchy failed: {error}")

        except Exception as e:
            logger.error(f"Get hierarchy error: {e}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        try:
            async with self.session.get(
                f"{self.config.registry_url}/statistics"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Get statistics failed: {error}")

        except Exception as e:
            logger.error(f"Get statistics error: {e}")
            raise

    # ==================== Cache Management ====================

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from local cache"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if asyncio.get_event_loop().time() - timestamp < self.config.cache_ttl:
                return self._cache[key]
        return None

    def _set_cached(self, key: str, value: Any):
        """Set value in local cache"""
        self._cache[key] = value
        self._cache_timestamps[key] = asyncio.get_event_loop().time()

    def _invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        import fnmatch
        keys_to_remove = []

        for key in self._cache:
            if fnmatch.fnmatch(key, pattern):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)

    # ==================== Entity Parsing ====================

    def _parse_entity(self, data: Dict[str, Any]) -> BaseRegistryEntry:
        """Parse entity data into appropriate model"""
        entity_type = data.get("type")

        if entity_type == RegistryType.AGENT:
            return AgentRegistryEntry(**data)
        elif entity_type == RegistryType.LEADER:
            return LeaderRegistryEntry(**data)
        elif entity_type == RegistryType.DEPARTMENT:
            return DepartmentRegistryEntry(**data)
        elif entity_type == RegistryType.DIVISION:
            return DivisionRegistryEntry(**data)
        elif entity_type == RegistryType.DATABASE:
            return DatabaseRegistryEntry(**data)
        elif entity_type in [RegistryType.SERVER_CORE, RegistryType.SERVER_MCP,
                            RegistryType.SERVER_BUSINESS]:
            return ServerRegistryEntry(**data)
        else:
            return BaseRegistryEntry(**data)


# ==================== Convenience Functions ====================

async def quick_register_agent(
    name: str,
    capabilities: Optional[List[str]] = None,
    **kwargs
) -> AgentRegistryEntry:
    """Quick function to register an agent"""
    async with RegistryClient() as client:
        return await client.register_agent(name, capabilities=capabilities, **kwargs)


async def quick_discover_agents(
    capability: Optional[str] = None,
    department_id: Optional[str] = None
) -> List[AgentRegistryEntry]:
    """Quick function to discover agents"""
    async with RegistryClient() as client:
        return await client.discover_agents(
            capability=capability,
            department_id=department_id
        )


async def quick_register_server(
    name: str,
    server_type: ServerType,
    port: int,
    **kwargs
) -> ServerRegistryEntry:
    """Quick function to register a server"""
    async with RegistryClient() as client:
        return await client.register_server(
            name=name,
            server_type=server_type,
            host="localhost",
            port=port,
            **kwargs
        )
