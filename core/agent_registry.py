"""
Agent Registry & Discovery Service - BoarderframeOS
Real-time tracking and discovery of all agents in the system
"""

import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .base_agent import AgentConfig, AgentState
from .message_bus import AgentMessage, MessagePriority, MessageType, message_bus

logger = logging.getLogger("agent_registry")

class AgentCapability(Enum):
    """Agent capabilities"""
    RESEARCH = "research"
    DEVELOPMENT = "development"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    MONITORING = "monitoring"
    COORDINATION = "coordination"
    PLANNING = "planning"

@dataclass
class AgentDiscoveryInfo:
    """Agent discovery and metadata information"""
    agent_id: str
    name: str
    role: str
    capabilities: List[AgentCapability]
    state: AgentState
    zone: str
    model: str
    version: str = "1.0.0"

    # Runtime information
    pid: Optional[int] = None
    host: str = "localhost"
    port: Optional[int] = None
    started_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None

    # Performance metrics
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_usage: float = 0.0
    tasks_completed: int = 0
    uptime_seconds: float = 0.0

    # Networking
    endpoints: Dict[str, str] = field(default_factory=dict)
    message_queue_size: int = 0

    # Health status
    is_healthy: bool = True
    last_error: Optional[str] = None
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['capabilities'] = [cap.value for cap in self.capabilities]
        data['state'] = self.state.value if isinstance(self.state, AgentState) else self.state
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.last_heartbeat:
            data['last_heartbeat'] = self.last_heartbeat.isoformat()
        return data

class AgentRegistry:
    """Centralized registry for agent discovery and tracking"""

    def __init__(self):
        self.agents: Dict[str, AgentDiscoveryInfo] = {}
        self.zone_agents: Dict[str, Set[str]] = {}
        self.capability_index: Dict[AgentCapability, Set[str]] = {}
        self.discovery_callbacks: List[callable] = []
        self.heartbeat_timeout = 300  # 5 minutes
        self.running = False

        # Initialize capability index
        for capability in AgentCapability:
            self.capability_index[capability] = set()

    async def start(self):
        """Start the registry service"""
        self.running = True
        logger.info("Agent Registry started")

        # Start background tasks
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._discovery_service())
        asyncio.create_task(self._health_checker())

        # Subscribe to system messages
        await message_bus.subscribe_to_topic("registry", "system_events")
        await message_bus.subscribe_to_topic("registry", "agent_heartbeats")

    async def stop(self):
        """Stop the registry service"""
        self.running = False
        logger.info("Agent Registry stopped")

    async def register_agent(self, agent_info: AgentDiscoveryInfo) -> bool:
        """Register a new agent"""
        try:
            agent_id = agent_info.agent_id

            # Update agent info
            agent_info.last_heartbeat = datetime.now()
            if not agent_info.started_at:
                agent_info.started_at = datetime.now()

            # Store in registry
            self.agents[agent_id] = agent_info

            # Update zone index
            zone = agent_info.zone
            if zone not in self.zone_agents:
                self.zone_agents[zone] = set()
            self.zone_agents[zone].add(agent_id)

            # Update capability index
            for capability in agent_info.capabilities:
                self.capability_index[capability].add(agent_id)

            logger.info(f"Registered agent: {agent_id} ({agent_info.name}) in zone {zone}")

            # Notify discovery callbacks
            for callback in self.discovery_callbacks:
                try:
                    await callback("agent_registered", agent_info)
                except Exception as e:
                    logger.error(f"Discovery callback error: {e}")

            # Broadcast agent registration
            await message_bus.broadcast(AgentMessage(
                from_agent="registry",
                to_agent="system",
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "event": "agent_registered",
                    "agent_id": agent_id,
                    "agent_info": agent_info.to_dict()
                }
            ), topic="system_events")

            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_info.agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id not in self.agents:
                logger.warning(f"Agent {agent_id} not found in registry")
                return False

            agent_info = self.agents[agent_id]

            # Remove from zone index
            if agent_info.zone in self.zone_agents:
                self.zone_agents[agent_info.zone].discard(agent_id)
                if not self.zone_agents[agent_info.zone]:
                    del self.zone_agents[agent_info.zone]

            # Remove from capability index
            for capability in agent_info.capabilities:
                self.capability_index[capability].discard(agent_id)

            # Remove from registry
            del self.agents[agent_id]

            logger.info(f"Unregistered agent: {agent_id}")

            # Notify discovery callbacks
            for callback in self.discovery_callbacks:
                try:
                    await callback("agent_unregistered", agent_info)
                except Exception as e:
                    logger.error(f"Discovery callback error: {e}")

            # Broadcast agent unregistration
            await message_bus.broadcast(AgentMessage(
                from_agent="registry",
                to_agent="system",
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "event": "agent_unregistered",
                    "agent_id": agent_id
                }
            ), topic="system_events")

            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False

    async def update_agent_heartbeat(self, agent_id: str, metrics: Optional[Dict[str, Any]] = None):
        """Update agent heartbeat and metrics"""
        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            agent_info.last_heartbeat = datetime.now()
            agent_info.is_healthy = True

            # Update metrics if provided
            if metrics:
                agent_info.cpu_usage = metrics.get('cpu_usage', agent_info.cpu_usage)
                agent_info.memory_usage_mb = metrics.get('memory_usage_mb', agent_info.memory_usage_mb)
                agent_info.gpu_usage = metrics.get('gpu_usage', agent_info.gpu_usage)
                agent_info.tasks_completed = metrics.get('tasks_completed', agent_info.tasks_completed)
                agent_info.uptime_seconds = metrics.get('uptime_seconds', agent_info.uptime_seconds)
                agent_info.message_queue_size = metrics.get('message_queue_size', agent_info.message_queue_size)

                if 'state' in metrics:
                    agent_info.state = AgentState(metrics['state'])

            logger.debug(f"Updated heartbeat for agent: {agent_id}")

    def get_agent(self, agent_id: str) -> Optional[AgentDiscoveryInfo]:
        """Get agent information by ID"""
        return self.agents.get(agent_id)

    def list_agents(self, zone: Optional[str] = None, state: Optional[AgentState] = None,
                   capability: Optional[AgentCapability] = None) -> List[AgentDiscoveryInfo]:
        """List agents with optional filters"""
        agents = list(self.agents.values())

        if zone:
            agents = [a for a in agents if a.zone == zone]

        if state:
            agents = [a for a in agents if a.state == state]

        if capability:
            agents = [a for a in agents if capability in a.capabilities]

        return agents

    def find_agents_by_capability(self, capability: AgentCapability) -> List[AgentDiscoveryInfo]:
        """Find agents with a specific capability"""
        agent_ids = self.capability_index.get(capability, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]

    def get_zone_agents(self, zone: str) -> List[AgentDiscoveryInfo]:
        """Get all agents in a specific zone"""
        agent_ids = self.zone_agents.get(zone, set())
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]

    def get_healthy_agents(self) -> List[AgentDiscoveryInfo]:
        """Get all healthy agents"""
        return [agent for agent in self.agents.values() if agent.is_healthy]

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        total_agents = len(self.agents)
        healthy_agents = len(self.get_healthy_agents())

        states = {}
        for agent in self.agents.values():
            state = agent.state.value if isinstance(agent.state, AgentState) else agent.state
            states[state] = states.get(state, 0) + 1

        zones = {}
        for zone, agent_ids in self.zone_agents.items():
            zones[zone] = len(agent_ids)

        capabilities = {}
        for capability, agent_ids in self.capability_index.items():
            capabilities[capability.value] = len(agent_ids)

        # Resource usage
        total_cpu = sum(agent.cpu_usage for agent in self.agents.values())
        total_memory = sum(agent.memory_usage_mb for agent in self.agents.values())
        total_gpu = sum(agent.gpu_usage for agent in self.agents.values())
        total_tasks = sum(agent.tasks_completed for agent in self.agents.values())

        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "health_percentage": (healthy_agents / max(total_agents, 1)) * 100,
            "states": states,
            "zones": zones,
            "capabilities": capabilities,
            "resource_usage": {
                "total_cpu_usage": total_cpu,
                "average_cpu_usage": total_cpu / max(total_agents, 1),
                "total_memory_mb": total_memory,
                "average_memory_mb": total_memory / max(total_agents, 1),
                "total_gpu_usage": total_gpu,
                "average_gpu_usage": total_gpu / max(total_agents, 1)
            },
            "total_tasks_completed": total_tasks,
            "timestamp": datetime.now().isoformat()
        }

    def add_discovery_callback(self, callback: callable):
        """Add a discovery event callback"""
        self.discovery_callbacks.append(callback)

    def remove_discovery_callback(self, callback: callable):
        """Remove a discovery event callback"""
        if callback in self.discovery_callbacks:
            self.discovery_callbacks.remove(callback)

    async def _heartbeat_monitor(self):
        """Monitor agent heartbeats and mark unhealthy agents"""
        while self.running:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(seconds=self.heartbeat_timeout)

                for agent_id, agent_info in self.agents.items():
                    if agent_info.last_heartbeat and agent_info.last_heartbeat < timeout_threshold:
                        if agent_info.is_healthy:
                            agent_info.is_healthy = False
                            agent_info.last_error = "Heartbeat timeout"
                            logger.warning(f"Agent {agent_id} marked as unhealthy (heartbeat timeout)")

                            # Broadcast health change
                            await message_bus.broadcast(AgentMessage(
                                from_agent="registry",
                                to_agent="system",
                                message_type=MessageType.ALERT,
                                content={
                                    "event": "agent_unhealthy",
                                    "agent_id": agent_id,
                                    "reason": "heartbeat_timeout"
                                }
                            ), topic="system_events")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(60)

    async def _discovery_service(self):
        """Active discovery of new agents"""
        while self.running:
            try:
                # TODO: Implement network discovery for agents on different hosts
                # For now, agents self-register
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Discovery service error: {e}")
                await asyncio.sleep(30)

    async def _health_checker(self):
        """Periodic health checks for all agents"""
        while self.running:
            try:
                for agent_id, agent_info in self.agents.items():
                    if agent_info.is_healthy:
                        # Send health check message
                        await message_bus.send_message(AgentMessage(
                            from_agent="registry",
                            to_agent=agent_id,
                            message_type=MessageType.STATUS_UPDATE,
                            content={"command": "health_check"},
                            priority=MessagePriority.LOW,
                            requires_response=False
                        ))

                await asyncio.sleep(120)  # Health check every 2 minutes

            except Exception as e:
                logger.error(f"Health checker error: {e}")
                await asyncio.sleep(120)

# Global registry instance
agent_registry = AgentRegistry()
