"""
Agent Orchestrator - Manages agent lifecycle, communication, and coordination
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import httpx
import uuid
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentState
from .message_bus import message_bus, MessageType, MessagePriority, AgentMessage

logger = logging.getLogger("agent_orchestrator")

class OrchestrationMode(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class AgentInstance:
    """Represents a running agent instance"""
    agent_id: str
    name: str
    class_name: str
    module_path: str
    biome: str
    state: AgentState
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    resource_usage: Dict[str, float] = None
    performance_metrics: Dict[str, float] = None

@dataclass
class TaskAssignment:
    """Represents a task assigned to an agent"""
    task_id: str
    agent_id: str
    task_type: str
    data: Dict[str, Any]
    priority: MessagePriority
    created_at: datetime
    deadline: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict] = None

class AgentOrchestrator:
    """Central orchestrator for all agent operations"""
    
    def __init__(self, mode: OrchestrationMode = OrchestrationMode.DEVELOPMENT):
        self.mode = mode
        self.running_agents: Dict[str, AgentInstance] = {}
        self.agent_registry: Dict[str, Dict] = {}
        self.task_queue: Dict[str, TaskAssignment] = {}
        self.mesh_networks: Dict[str, Set[str]] = {}
        self.orchestrator_id = "orchestrator"
        
        # Performance thresholds
        self.performance_thresholds = {
            "response_time_ms": 5000,
            "memory_usage_mb": 1024,
            "cpu_usage_percent": 80,
            "heartbeat_timeout_seconds": 300
        }
        
        # Agent limits by mode
        self.agent_limits = {
            OrchestrationMode.DEVELOPMENT: {"max_agents": 10},
            OrchestrationMode.PRODUCTION: {"max_agents": 100},
            OrchestrationMode.TESTING: {"max_agents": 5}
        }
    
    async def initialize(self):
        """Initialize the orchestrator"""
        logger.info(f"Initializing Agent Orchestrator in {self.mode.value} mode")
        
        # Load agent registry from database
        await self._load_agent_registry()
        
        # Start orchestrator services
        await self._start_orchestrator_services()
        
        # Register with message bus
        await message_bus.subscribe(self.orchestrator_id, self._handle_orchestrator_message)
        
        logger.info("Agent Orchestrator initialized successfully")
    
    async def _load_agent_registry(self):
        """Load agent registry from database"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8004/query", json={
                    "sql": "SELECT id, name, config FROM agents WHERE status = 'active'"
                })
                
                if response.status_code == 200 and response.json().get("success"):
                    for row in response.json().get("data", []):
                        config = json.loads(row["config"])
                        self.agent_registry[row["id"]] = {
                            "name": row["name"],
                            "config": config,
                            "class_name": config.get("class_name", row["name"]),
                            "module_path": config.get("module_path", f"agents.{row['name'].lower()}.{row['name'].lower()}"),
                            "biome": config.get("biome", "default")
                        }
                    
                    logger.info(f"Loaded {len(self.agent_registry)} agents from registry")
                    
        except Exception as e:
            logger.error(f"Failed to load agent registry: {e}")
    
    async def _start_orchestrator_services(self):
        """Start background orchestrator services"""
        asyncio.create_task(self._agent_health_monitor())
        asyncio.create_task(self._task_processor())
        asyncio.create_task(self._performance_monitor())
        asyncio.create_task(self._mesh_coordinator())
        asyncio.create_task(self._system_optimizer())
    
    async def start_agent(self, agent_id: str, **kwargs) -> bool:
        """Start a specific agent"""
        if agent_id not in self.agent_registry:
            logger.error(f"Agent {agent_id} not found in registry")
            return False
        
        if agent_id in self.running_agents:
            logger.warning(f"Agent {agent_id} is already running")
            return True
        
        try:
            # Check agent limits
            if len(self.running_agents) >= self.agent_limits[self.mode]["max_agents"]:
                logger.error("Maximum agent limit reached")
                return False
            
            registry_entry = self.agent_registry[agent_id]
            
            # Create agent instance
            instance = AgentInstance(
                agent_id=agent_id,
                name=registry_entry["name"],
                class_name=registry_entry["class_name"],
                module_path=registry_entry["module_path"],
                biome=registry_entry["biome"],
                state=AgentState.INITIALIZING,
                started_at=datetime.now(),
                resource_usage={},
                performance_metrics={}
            )
            
            # Start the agent
            success = await self._launch_agent_process(instance, **kwargs)
            
            if success:
                self.running_agents[agent_id] = instance
                logger.info(f"Agent {agent_id} ({registry_entry['name']}) started successfully")
                
                # Notify system of agent start
                await message_bus.broadcast(AgentMessage(
                    from_agent=self.orchestrator_id,
                    to_agent="system",
                    message_type=MessageType.STATUS_UPDATE,
                    data={"event": "agent_started", "agent_id": agent_id, "name": registry_entry["name"]},
                    priority=MessagePriority.NORMAL
                ))
                
                return True
            else:
                logger.error(f"Failed to start agent {agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting agent {agent_id}: {e}")
            return False
    
    async def stop_agent(self, agent_id: str, graceful: bool = True) -> bool:
        """Stop a running agent"""
        if agent_id not in self.running_agents:
            logger.warning(f"Agent {agent_id} is not running")
            return True
        
        try:
            instance = self.running_agents[agent_id]
            
            if graceful:
                # Send shutdown signal
                await message_bus.send_direct(AgentMessage(
                    from_agent=self.orchestrator_id,
                    to_agent=agent_id,
                    message_type=MessageType.CONTROL,
                    data={"command": "shutdown"},
                    priority=MessagePriority.HIGH
                ))
                
                # Wait for graceful shutdown
                await asyncio.sleep(5)
            
            # Force stop if necessary
            if instance.pid:
                try:
                    import os
                    import signal
                    os.kill(instance.pid, signal.SIGTERM)
                except:
                    pass
            
            # Remove from running agents
            del self.running_agents[agent_id]
            
            logger.info(f"Agent {agent_id} stopped")
            
            # Notify system
            await message_bus.broadcast(AgentMessage(
                from_agent=self.orchestrator_id,
                to_agent="system",
                message_type=MessageType.STATUS_UPDATE,
                data={"event": "agent_stopped", "agent_id": agent_id},
                priority=MessagePriority.NORMAL
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            return False
    
    async def start_core_agents(self) -> Dict[str, bool]:
        """Start the core agents in proper order"""
        results = {}
        
        # Core agent startup order
        startup_order = ["solomon", "david", "adam", "eve", "bezalel"]
        
        for agent_name in startup_order:
            # Find agent by name
            agent_id = None
            for aid, info in self.agent_registry.items():
                if info["name"].lower() == agent_name:
                    agent_id = aid
                    break
            
            if agent_id:
                logger.info(f"Starting core agent: {agent_name}")
                success = await self.start_agent(agent_id)
                results[agent_name] = success
                
                if success:
                    # Wait a bit between core agent starts
                    await asyncio.sleep(2)
                else:
                    logger.error(f"Failed to start core agent: {agent_name}")
            else:
                logger.warning(f"Core agent not found in registry: {agent_name}")
                results[agent_name] = False
        
        return results
    
    async def assign_task(self, agent_id: str, task_type: str, data: Dict, priority: MessagePriority = MessagePriority.NORMAL, deadline: Optional[datetime] = None) -> str:
        """Assign a task to an agent"""
        task_id = str(uuid.uuid4())[:8]
        
        assignment = TaskAssignment(
            task_id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            data=data,
            priority=priority,
            created_at=datetime.now(),
            deadline=deadline
        )
        
        self.task_queue[task_id] = assignment
        
        # Send task to agent
        await message_bus.send_direct(AgentMessage(
            from_agent=self.orchestrator_id,
            to_agent=agent_id,
            message_type=MessageType.TASK_REQUEST,
            data={
                "task_id": task_id,
                "task_type": task_type,
                "task_data": data,
                "deadline": deadline.isoformat() if deadline else None
            },
            priority=priority
        ))
        
        logger.info(f"Task {task_id} assigned to agent {agent_id}")
        return task_id
    
    async def create_mesh_network(self, mesh_id: str, agent_ids: List[str], purpose: str) -> bool:
        """Create a consciousness mesh network"""
        try:
            # Validate agents are running
            valid_agents = [aid for aid in agent_ids if aid in self.running_agents]
            
            if len(valid_agents) < 2:
                logger.error("Mesh requires at least 2 running agents")
                return False
            
            self.mesh_networks[mesh_id] = set(valid_agents)
            
            # Notify agents of mesh formation
            for agent_id in valid_agents:
                await message_bus.send_direct(AgentMessage(
                    from_agent=self.orchestrator_id,
                    to_agent=agent_id,
                    message_type=MessageType.MESH_CONTROL,
                    data={
                        "action": "join_mesh",
                        "mesh_id": mesh_id,
                        "mesh_members": valid_agents,
                        "purpose": purpose
                    },
                    priority=MessagePriority.HIGH
                ))
            
            logger.info(f"Mesh network {mesh_id} created with {len(valid_agents)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create mesh network: {e}")
            return False
    
    async def dissolve_mesh_network(self, mesh_id: str) -> bool:
        """Dissolve a consciousness mesh network"""
        if mesh_id not in self.mesh_networks:
            return True
        
        try:
            agent_ids = list(self.mesh_networks[mesh_id])
            
            # Notify agents of mesh dissolution
            for agent_id in agent_ids:
                if agent_id in self.running_agents:
                    await message_bus.send_direct(AgentMessage(
                        from_agent=self.orchestrator_id,
                        to_agent=agent_id,
                        message_type=MessageType.MESH_CONTROL,
                        data={
                            "action": "leave_mesh",
                            "mesh_id": mesh_id
                        },
                        priority=MessagePriority.HIGH
                    ))
            
            del self.mesh_networks[mesh_id]
            logger.info(f"Mesh network {mesh_id} dissolved")
            return True
            
        except Exception as e:
            logger.error(f"Failed to dissolve mesh network: {e}")
            return False
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "orchestrator": {
                "mode": self.mode.value,
                "running_since": datetime.now().isoformat(),
                "total_agents": len(self.agent_registry),
                "running_agents": len(self.running_agents),
                "active_tasks": len([t for t in self.task_queue.values() if t.status == "pending"]),
                "mesh_networks": len(self.mesh_networks)
            },
            "agents": {
                agent_id: {
                    "name": instance.name,
                    "biome": instance.biome,
                    "state": instance.state.value,
                    "uptime_minutes": (datetime.now() - instance.started_at).total_seconds() / 60 if instance.started_at else 0,
                    "last_heartbeat": instance.last_heartbeat.isoformat() if instance.last_heartbeat else None
                }
                for agent_id, instance in self.running_agents.items()
            },
            "performance": {
                "healthy_agents": len([a for a in self.running_agents.values() if a.state == AgentState.IDLE]),
                "system_load": self._calculate_system_load(),
                "average_response_time": self._calculate_average_response_time()
            }
        }
    
    async def _launch_agent_process(self, instance: AgentInstance, **kwargs) -> bool:
        """Launch an agent process"""
        try:
            # This is simplified - in production would use proper process management
            # For now, we'll simulate agent startup
            
            instance.state = AgentState.IDLE
            instance.last_heartbeat = datetime.now()
            
            # Store agent startup in database
            await self._log_agent_event(instance.agent_id, "started", {"instance": instance.name})
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch agent process: {e}")
            return False
    
    async def _handle_orchestrator_message(self, message: AgentMessage):
        """Handle messages sent to the orchestrator"""
        try:
            if message.message_type == MessageType.TASK_RESPONSE:
                await self._handle_task_response(message)
            elif message.message_type == MessageType.STATUS_UPDATE:
                await self._handle_agent_status_update(message)
            elif message.message_type == MessageType.HEARTBEAT:
                await self._handle_agent_heartbeat(message)
            else:
                logger.debug(f"Unhandled orchestrator message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error handling orchestrator message: {e}")
    
    async def _handle_task_response(self, message: AgentMessage):
        """Handle task completion responses"""
        task_id = message.data.get("task_id")
        if task_id in self.task_queue:
            assignment = self.task_queue[task_id]
            assignment.status = "completed"
            assignment.result = message.data.get("result")
            
            logger.info(f"Task {task_id} completed by agent {message.from_agent}")
    
    async def _handle_agent_status_update(self, message: AgentMessage):
        """Handle agent status updates"""
        agent_id = message.from_agent
        if agent_id in self.running_agents:
            instance = self.running_agents[agent_id]
            
            status = message.data.get("status")
            if status:
                try:
                    instance.state = AgentState(status)
                except ValueError:
                    logger.warning(f"Invalid agent state: {status}")
    
    async def _handle_agent_heartbeat(self, message: AgentMessage):
        """Handle agent heartbeat messages"""
        agent_id = message.from_agent
        if agent_id in self.running_agents:
            instance = self.running_agents[agent_id]
            instance.last_heartbeat = datetime.now()
            
            # Update performance metrics if provided
            metrics = message.data.get("metrics")
            if metrics:
                instance.performance_metrics.update(metrics)
    
    async def _agent_health_monitor(self):
        """Monitor agent health and restart if necessary"""
        while True:
            try:
                current_time = datetime.now()
                timeout_threshold = timedelta(seconds=self.performance_thresholds["heartbeat_timeout_seconds"])
                
                for agent_id, instance in list(self.running_agents.items()):
                    # Check heartbeat timeout
                    if instance.last_heartbeat and (current_time - instance.last_heartbeat) > timeout_threshold:
                        logger.warning(f"Agent {agent_id} heartbeat timeout - restarting")
                        await self.stop_agent(agent_id, graceful=False)
                        await self.start_agent(agent_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Agent health monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _task_processor(self):
        """Process task queue and handle timeouts"""
        while True:
            try:
                current_time = datetime.now()
                
                # Check for task timeouts
                for task_id, assignment in list(self.task_queue.items()):
                    if assignment.deadline and current_time > assignment.deadline and assignment.status == "pending":
                        assignment.status = "timeout"
                        logger.warning(f"Task {task_id} timed out")
                
                # Clean up completed tasks older than 1 hour
                cutoff_time = current_time - timedelta(hours=1)
                for task_id in list(self.task_queue.keys()):
                    assignment = self.task_queue[task_id]
                    if assignment.status in ["completed", "timeout"] and assignment.created_at < cutoff_time:
                        del self.task_queue[task_id]
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Task processor error: {e}")
                await asyncio.sleep(30)
    
    async def _performance_monitor(self):
        """Monitor system performance"""
        while True:
            try:
                # Collect performance metrics
                system_metrics = await self._collect_system_metrics()
                
                # Log metrics to database
                await self._log_performance_metrics(system_metrics)
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _mesh_coordinator(self):
        """Coordinate mesh networks"""
        while True:
            try:
                # Monitor mesh health and performance
                for mesh_id, agent_ids in list(self.mesh_networks.items()):
                    active_agents = [aid for aid in agent_ids if aid in self.running_agents]
                    
                    if len(active_agents) < 2:
                        logger.info(f"Dissolving mesh {mesh_id} - insufficient active agents")
                        await self.dissolve_mesh_network(mesh_id)
                
                await asyncio.sleep(120)  # Every 2 minutes
                
            except Exception as e:
                logger.error(f"Mesh coordinator error: {e}")
                await asyncio.sleep(60)
    
    async def _system_optimizer(self):
        """Optimize system performance"""
        while True:
            try:
                # System optimization logic
                await self._optimize_agent_distribution()
                await self._balance_workloads()
                
                await asyncio.sleep(1800)  # Every 30 minutes
                
            except Exception as e:
                logger.error(f"System optimizer error: {e}")
                await asyncio.sleep(300)
    
    def _calculate_system_load(self) -> float:
        """Calculate current system load"""
        if not self.running_agents:
            return 0.0
        
        busy_agents = len([a for a in self.running_agents.values() if a.state in [AgentState.THINKING, AgentState.ACTING]])
        return busy_agents / len(self.running_agents)
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time across agents"""
        # Simplified calculation
        response_times = []
        for instance in self.running_agents.values():
            if instance.performance_metrics and "response_time_ms" in instance.performance_metrics:
                response_times.append(instance.performance_metrics["response_time_ms"])
        
        return sum(response_times) / len(response_times) if response_times else 0.0
    
    async def _collect_system_metrics(self) -> Dict:
        """Collect comprehensive system metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.running_agents),
            "system_load": self._calculate_system_load(),
            "average_response_time": self._calculate_average_response_time(),
            "active_tasks": len([t for t in self.task_queue.values() if t.status == "pending"]),
            "mesh_networks": len(self.mesh_networks)
        }
    
    async def _log_agent_event(self, agent_id: str, event: str, data: Dict):
        """Log agent events to database"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:8004/insert", json={
                    "table": "agent_interactions",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "source_agent": self.orchestrator_id,
                        "target_agent": agent_id,
                        "interaction_type": f"orchestrator_{event}",
                        "data": json.dumps(data)
                    }
                })
        except Exception as e:
            logger.error(f"Failed to log agent event: {e}")
    
    async def _log_performance_metrics(self, metrics: Dict):
        """Log performance metrics to database"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:8004/insert", json={
                    "table": "metrics",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "agent_id": self.orchestrator_id,
                        "metric_name": "system_performance",
                        "metric_value": metrics.get("system_load", 0.0),
                        "metadata": json.dumps(metrics)
                    }
                })
        except Exception as e:
            logger.error(f"Failed to log performance metrics: {e}")
    
    async def _optimize_agent_distribution(self):
        """Optimize agent distribution across biomes"""
        # This would implement intelligent agent rebalancing
        pass
    
    async def _balance_workloads(self):
        """Balance workloads across agents"""
        # This would implement load balancing logic
        pass

# Global orchestrator instance
orchestrator = AgentOrchestrator()

# Export
__all__ = ["AgentOrchestrator", "orchestrator", "AgentInstance", "TaskAssignment", "OrchestrationMode"]