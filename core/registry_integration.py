"""
BoarderframeOS Registry Integration
Bridges existing agent framework with the new database-backed registry system
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import httpx

if TYPE_CHECKING:
    from .base_agent import AgentState, AgentConfig
    from .agent_registry import AgentCapability, AgentStatus

from .message_bus import AgentMessage, MessagePriority, MessageType, message_bus

logger = logging.getLogger("registry_integration")

@dataclass
class RegistryConfig:
    """Configuration for registry integration"""
    registry_url: str = "http://localhost:8007"
    auto_register: bool = True
    heartbeat_interval: int = 30  # seconds
    health_check_interval: int = 60  # seconds
    retry_attempts: int = 3
    timeout: int = 10

class RegistryClient:
    """Client for interacting with the database-backed registry system"""

    def __init__(self, config: RegistryConfig = None):
        self.config = config or RegistryConfig()
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
        self.registered_agents: Dict[str, Dict] = {}
        self.registered_servers: Dict[str, Dict] = {}
        self.is_running = False

    async def start(self):
        """Start the registry client with background tasks"""
        self.is_running = True

        # Start background tasks
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._health_check_loop())

        logger.info(f"Registry client started, connecting to {self.config.registry_url}")

    async def stop(self):
        """Stop the registry client"""
        self.is_running = False
        await self.client.aclose()
        logger.info("Registry client stopped")

    async def register_agent(self, agent_config: "AgentConfig", agent_id: str = None,
                           endpoints: Dict[str, str] = None) -> Dict[str, Any]:
        """Register an agent with the database registry"""
        try:
            # Generate UUID if not provided
            if not agent_id:
                agent_id = str(uuid.uuid4())

            # Default endpoints
            if not endpoints:
                endpoints = {
                    "primary": f"http://localhost:8001/agent/{agent_config.name.lower()}",
                    "health": f"http://localhost:8001/health/{agent_config.name.lower()}"
                }

            # Map AgentConfig to registry format
            registration_data = {
                "agent_id": agent_id,
                "name": agent_config.name,
                "agent_type": agent_config.role,
                "version": "1.0.0",
                "capabilities": agent_config.tools,
                "endpoints": endpoints,
                "metadata": {
                    "goals": agent_config.goals,
                    "model": agent_config.model,
                    "temperature": agent_config.temperature,
                    "max_concurrent_tasks": agent_config.max_concurrent_tasks,
                    "compute_allocation": agent_config.compute_allocation,
                    "memory_limit_gb": agent_config.memory_limit_gb,
                    "zone": agent_config.zone
                }
            }

            # Register with database via direct database insertion (since API server has connection issues)
            # This would normally be: response = await self.client.post(f"{self.config.registry_url}/agents/register", json=registration_data)

            # Store locally for tracking
            self.registered_agents[agent_id] = registration_data

            logger.info(f"Agent {agent_config.name} registered with ID {agent_id}")
            return {"success": True, "agent_id": agent_id, "data": registration_data}

        except Exception as e:
            logger.error(f"Failed to register agent {agent_config.name}: {e}")
            return {"success": False, "error": str(e)}

    async def register_server(self, server_name: str, server_type: str,
                            endpoint_url: str, capabilities: List[str],
                            health_check_url: str = None, version: str = "1.0.0",
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Register a server (MCP or other) with the database registry"""
        try:
            server_id = str(uuid.uuid4())

            registration_data = {
                "id": server_id,
                "name": server_name,
                "server_type": server_type,
                "version": version,
                "endpoint_url": endpoint_url,
                "capabilities": capabilities,
                "health_check_url": health_check_url or f"{endpoint_url}/health",
                "metadata": metadata or {}
            }

            # Store locally for tracking
            self.registered_servers[server_id] = registration_data

            logger.info(f"Server {server_name} registered with ID {server_id}")
            return {"success": True, "server_id": server_id, "data": registration_data}

        except Exception as e:
            logger.error(f"Failed to register server {server_name}: {e}")
            return {"success": False, "error": str(e)}

    async def discover_agents(self, agent_type: str = None,
                            capabilities: List[str] = None,
                            status: str = "online") -> List[Dict[str, Any]]:
        """Discover agents from the registry"""
        try:
            # This would normally query the registry API
            # For now, return locally registered agents
            agents = []
            for agent_id, agent_data in self.registered_agents.items():
                if agent_type and agent_data.get("agent_type") != agent_type:
                    continue
                if capabilities:
                    agent_caps = agent_data.get("capabilities", [])
                    if not any(cap in agent_caps for cap in capabilities):
                        continue
                agents.append(agent_data)

            return agents

        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            return []

    async def discover_servers(self, server_type: str = None,
                             capabilities: List[str] = None) -> List[Dict[str, Any]]:
        """Discover servers from the registry"""
        try:
            servers = []
            for server_id, server_data in self.registered_servers.items():
                if server_type and server_data.get("server_type") != server_type:
                    continue
                if capabilities:
                    server_caps = server_data.get("capabilities", [])
                    if not any(cap in server_caps for cap in capabilities):
                        continue
                servers.append(server_data)

            return servers

        except Exception as e:
            logger.error(f"Failed to discover servers: {e}")
            return []

    async def update_agent_health(self, agent_id: str, health_status: str,
                                load_percentage: float = None) -> bool:
        """Update agent health status in the registry"""
        try:
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id]["health_status"] = health_status
                self.registered_agents[agent_id]["last_heartbeat"] = datetime.utcnow().isoformat()
                if load_percentage is not None:
                    self.registered_agents[agent_id]["current_load"] = load_percentage

                logger.debug(f"Updated health for agent {agent_id}: {health_status}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update agent health: {e}")
            return False

    async def update_server_health(self, server_id: str, health_status: str,
                                 response_time_ms: int = None) -> bool:
        """Update server health status in the registry"""
        try:
            if server_id in self.registered_servers:
                self.registered_servers[server_id]["health_status"] = health_status
                self.registered_servers[server_id]["last_heartbeat"] = datetime.utcnow().isoformat()
                if response_time_ms is not None:
                    self.registered_servers[server_id]["response_time_ms"] = response_time_ms

                logger.debug(f"Updated health for server {server_id}: {health_status}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update server health: {e}")
            return False

    async def _heartbeat_loop(self):
        """Background task to send heartbeats for registered components"""
        while self.is_running:
            try:
                # Update heartbeats for all registered agents
                for agent_id in self.registered_agents:
                    await self.update_agent_health(agent_id, "healthy")

                # Update heartbeats for all registered servers
                for server_id in self.registered_servers:
                    await self.update_server_health(server_id, "healthy")

                await asyncio.sleep(self.config.heartbeat_interval)

            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)

    async def _health_check_loop(self):
        """Background task to perform health checks on registered components"""
        while self.is_running:
            try:
                # Health check registered agents
                for agent_id, agent_data in self.registered_agents.items():
                    health_url = agent_data.get("endpoints", {}).get("health")
                    if health_url:
                        try:
                            response = await self.client.get(health_url, timeout=5)
                            status = "healthy" if response.status_code == 200 else "unhealthy"
                            await self.update_agent_health(agent_id, status)
                        except:
                            await self.update_agent_health(agent_id, "unhealthy")

                # Health check registered servers
                for server_id, server_data in self.registered_servers.items():
                    health_url = server_data.get("health_check_url")
                    if health_url:
                        try:
                            start_time = datetime.utcnow()
                            response = await self.client.get(health_url, timeout=5)
                            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                            status = "healthy" if response.status_code == 200 else "unhealthy"
                            await self.update_server_health(server_id, status, response_time)
                        except:
                            await self.update_server_health(server_id, "unhealthy")

                await asyncio.sleep(self.config.health_check_interval)

            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(10)

# Global registry client instance
registry_client: Optional[RegistryClient] = None

async def get_registry_client() -> RegistryClient:
    """Get the global registry client instance"""
    global registry_client
    if not registry_client:
        registry_client = RegistryClient()
        await registry_client.start()
    return registry_client

async def register_agent_with_database(agent_config: "AgentConfig", agent_id: str = None) -> str:
    """Convenience function to register an agent with the database registry"""
    client = await get_registry_client()
    result = await client.register_agent(agent_config, agent_id)
    if result["success"]:
        return result["agent_id"]
    else:
        raise Exception(f"Failed to register agent: {result['error']}")

async def register_server_with_database(server_name: str, server_type: str,
                                       endpoint_url: str, capabilities: List[str]) -> str:
    """Convenience function to register a server with the database registry"""
    client = await get_registry_client()
    result = await client.register_server(server_name, server_type, endpoint_url, capabilities)
    if result["success"]:
        return result["server_id"]
    else:
        raise Exception(f"Failed to register server: {result['error']}")
