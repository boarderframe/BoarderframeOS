"""
Agent Controller - BoarderframeOS
Centralized agent lifecycle management with task routing and control
"""

import asyncio
import subprocess
import signal
import os
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import importlib.util
import sys

from .base_agent import BaseAgent, AgentState, AgentConfig
from .agent_registry import agent_registry, AgentDiscoveryInfo, AgentCapability
from .resource_manager import resource_manager, ResourceLimit
from .message_bus import message_bus, MessageType, MessagePriority, AgentMessage
from .enhanced_message_bus import enhanced_message_bus, EnhancedAgentMessage, RoutingStrategy, DeliveryStatus
from .agent_coordination_manager import AgentCoordinationManager, CoordinationPattern

logger = logging.getLogger("agent_controller")

class ControlCommand(Enum):
    """Agent control commands"""
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    RESTART = "restart"
    UPDATE = "update"
    TERMINATE = "terminate"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class AgentTask:
    """Task to be assigned to an agent"""
    task_id: str
    agent_id: str
    task_type: str
    data: Dict[str, Any]
    priority: TaskPriority
    created_at: datetime
    deadline: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class AgentProcess:
    """Information about a running agent process"""
    agent_id: str
    process: subprocess.Popen
    started_at: datetime
    config: AgentConfig
    status: str = "running"
    restart_count: int = 0
    last_restart: Optional[datetime] = None

class AgentController:
    """Centralized controller for all agent operations"""
    
    def __init__(self):
        self.running_processes: Dict[str, AgentProcess] = {}
        self.task_queue: Dict[str, AgentTask] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.task_assignments: Dict[str, Set[str]] = {}  # agent_id -> task_ids
        self.running = False
        self.max_concurrent_tasks_per_agent = 5
        self.task_timeout_seconds = 3600  # 1 hour
        self.restart_cooldown_seconds = 60
        
        # Enhanced message bus and coordination
        self.coordination_manager = AgentCoordinationManager()
        self.active_workflows: Dict[str, Dict] = {}  # workflow_id -> workflow_info
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}
        
        # Agent templates directory
        self.agents_dir = Path("boarderframeos/agents")
        self.templates_dir = Path("boarderframeos/templates")
        
    async def start(self):
        """Start the agent controller"""
        self.running = True
        logger.info("Agent Controller started")
        
        # Start enhanced message bus and coordination manager
        await enhanced_message_bus.start()
        await self.coordination_manager.start()
        
        # Load existing agent configurations
        await self._load_agent_configs()
        
        # Start background tasks
        asyncio.create_task(self._task_processor())
        asyncio.create_task(self._process_monitor())
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._task_timeout_monitor())
        asyncio.create_task(self._coordination_monitor())
        asyncio.create_task(self._workflow_manager())
        
        # Subscribe to control messages (both buses for compatibility)
        await message_bus.subscribe_to_topic("agent_controller", "control_commands")
        await message_bus.subscribe_to_topic("agent_controller", "system_events")
        
        # Subscribe to enhanced message bus topics
        await enhanced_message_bus.subscribe_to_topic("agent_controller", "agent_coordination")
        await enhanced_message_bus.subscribe_to_topic("agent_controller", "workflow_management")
        await enhanced_message_bus.subscribe_to_topic("agent_controller", "agent_lifecycle")
    
    async def stop(self):
        """Stop the agent controller"""
        self.running = False
        
        # Stop all running agents
        for agent_id in list(self.running_processes.keys()):
            await self.stop_agent(agent_id, graceful=True)
        
        # Stop coordination manager and enhanced message bus
        await self.coordination_manager.stop()
        await enhanced_message_bus.stop()
        
        logger.info("Agent Controller stopped")
    
    async def _load_agent_configs(self):
        """Load agent configurations from files"""
        try:
            config_files = list(Path("configs/agents").glob("*.json"))
            for config_file in config_files:
                with open(config_file) as f:
                    config_data = json.load(f)
                    agent_config = AgentConfig(**config_data)
                    self.agent_configs[agent_config.name] = agent_config
                    logger.info(f"Loaded config for agent: {agent_config.name}")
        except Exception as e:
            logger.error(f"Error loading agent configs: {e}")
    
    async def create_agent(self, name: str, agent_type: str, role: str, goals: List[str],
                          zone: str = "default", model: str = "claude-3-opus-20240229",
                          capabilities: List[AgentCapability] = None,
                          resource_limits: Optional[ResourceLimit] = None) -> bool:
        """Create a new agent"""
        try:
            # Create agent configuration
            config = AgentConfig(
                name=name,
                role=role,
                goals=goals,
                tools=self._get_default_tools(agent_type),
                zone=zone,
                model=model
            )
            
            # Store configuration
            self.agent_configs[name] = config
            
            # Save configuration to file
            config_dir = Path("configs/agents")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            config_file = config_dir / f"{name}.json"
            with open(config_file, 'w') as f:
                config_dict = {
                    "name": config.name,
                    "role": config.role,
                    "goals": config.goals,
                    "tools": config.tools,
                    "zone": config.zone,
                    "model": config.model,
                    "temperature": config.temperature,
                    "max_concurrent_tasks": config.max_concurrent_tasks
                }
                json.dump(config_dict, f, indent=2)
            
            # Generate agent code
            agent_code = await self._generate_agent_code(name, agent_type, config)
            
            # Save agent code
            agent_file = self.agents_dir / f"{name.lower()}" / f"{name.lower()}.py"
            agent_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(agent_file, 'w') as f:
                f.write(agent_code)
            
            # Set resource limits
            if resource_limits:
                resource_manager.set_agent_limits(name, resource_limits)
            
            # Create agent discovery info
            discovery_info = AgentDiscoveryInfo(
                agent_id=name,
                name=name,
                role=role,
                capabilities=capabilities or [],
                state=AgentState.STOPPED,
                zone=zone,
                model=model
            )
            
            # Register with agent registry
            await agent_registry.register_agent(discovery_info)
            
            logger.info(f"Created agent: {name} ({agent_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {e}")
            return False
    
    async def start_agent(self, agent_id: str, **kwargs) -> bool:
        """Start an agent"""
        try:
            if agent_id in self.running_processes:
                logger.warning(f"Agent {agent_id} is already running")
                return True
            
            if agent_id not in self.agent_configs:
                logger.error(f"No configuration found for agent {agent_id}")
                return False
            
            config = self.agent_configs[agent_id]
            
            # Check resource availability
            if not await self._check_resource_availability(config):
                logger.error(f"Insufficient resources to start agent {agent_id}")
                return False
            
            # Start the agent process
            agent_file = self.agents_dir / f"{agent_id.lower()}" / f"{agent_id.lower()}.py"
            if not agent_file.exists():
                logger.error(f"Agent file not found: {agent_file}")
                return False
            
            # Start process
            process = await self._start_agent_process(agent_file, config, **kwargs)
            if not process:
                return False
            
            # Track the process
            agent_process = AgentProcess(
                agent_id=agent_id,
                process=process,
                started_at=datetime.now(),
                config=config
            )
            self.running_processes[agent_id] = agent_process
            
            # Initialize task assignment tracking
            self.task_assignments[agent_id] = set()
            
            # Update agent registry
            agent_info = agent_registry.get_agent(agent_id)
            if agent_info:
                agent_info.pid = process.pid
                agent_info.state = AgentState.IDLE
                agent_info.started_at = datetime.now()
                await agent_registry.update_agent_heartbeat(agent_id)
            
            logger.info(f"Started agent {agent_id} (PID: {process.pid})")
            
            # Notify system
            await message_bus.broadcast(AgentMessage(
                from_agent="agent_controller",
                to_agent="system",
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "event": "agent_started",
                    "agent_id": agent_id,
                    "pid": process.pid
                }
            ), topic="system_events")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}: {e}")
            return False
    
    async def stop_agent(self, agent_id: str, graceful: bool = True) -> bool:
        """Stop an agent"""
        try:
            if agent_id not in self.running_processes:
                logger.warning(f"Agent {agent_id} is not running")
                return True
            
            agent_process = self.running_processes[agent_id]
            process = agent_process.process
            
            if graceful:
                # Send termination signal
                await message_bus.send_message(AgentMessage(
                    from_agent="agent_controller",
                    to_agent=agent_id,
                    message_type=MessageType.STATUS_UPDATE,
                    content={"command": "shutdown"},
                    priority=MessagePriority.HIGH
                ))
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=30)
                except asyncio.TimeoutError:
                    logger.warning(f"Agent {agent_id} did not shutdown gracefully, forcing termination")
                    graceful = False
            
            if not graceful or process.poll() is None:
                # Force termination
                try:
                    process.terminate()
                    await asyncio.sleep(5)
                    if process.poll() is None:
                        process.kill()
                except Exception as e:
                    logger.error(f"Error terminating agent {agent_id}: {e}")
            
            # Clean up
            del self.running_processes[agent_id]
            if agent_id in self.task_assignments:
                del self.task_assignments[agent_id]
            
            # Update agent registry
            agent_info = agent_registry.get_agent(agent_id)
            if agent_info:
                agent_info.state = AgentState.TERMINATED
                agent_info.pid = None
            
            logger.info(f"Stopped agent {agent_id}")
            
            # Notify system
            await message_bus.broadcast(AgentMessage(
                from_agent="agent_controller",
                to_agent="system",
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "event": "agent_stopped",
                    "agent_id": agent_id
                }
            ), topic="system_events")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop agent {agent_id}: {e}")
            return False
    
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent"""
        logger.info(f"Restarting agent {agent_id}")
        
        # Check restart cooldown
        if agent_id in self.running_processes:
            agent_process = self.running_processes[agent_id]
            if (agent_process.last_restart and 
                (datetime.now() - agent_process.last_restart).total_seconds() < self.restart_cooldown_seconds):
                logger.warning(f"Agent {agent_id} restart blocked by cooldown")
                return False
        
        # Stop the agent
        await self.stop_agent(agent_id, graceful=True)
        await asyncio.sleep(2)
        
        # Start the agent
        success = await self.start_agent(agent_id)
        
        if success and agent_id in self.running_processes:
            self.running_processes[agent_id].restart_count += 1
            self.running_processes[agent_id].last_restart = datetime.now()
        
        return success
    
    async def assign_task(self, agent_id: str, task_type: str, data: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         deadline: Optional[datetime] = None) -> str:
        """Assign a task to an agent"""
        task_id = str(uuid.uuid4())
        
        task = AgentTask(
            task_id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            data=data,
            priority=priority,
            created_at=datetime.now(),
            deadline=deadline
        )
        
        self.task_queue[task_id] = task
        
        logger.info(f"Assigned task {task_id} to agent {agent_id}")
        
        return task_id
    
    async def auto_assign_task(self, task_type: str, data: Dict[str, Any],
                              required_capabilities: List[AgentCapability] = None,
                              zone: Optional[str] = None,
                              priority: TaskPriority = TaskPriority.NORMAL,
                              routing_strategy: str = "capability_based") -> Optional[str]:
        """Automatically assign a task to the best available agent using enhanced routing"""
        
        # Use enhanced routing for better agent selection
        if routing_strategy == "capability_based" and required_capabilities:
            # Find agents by capabilities using enhanced message bus
            suitable_agents = []
            for capability in required_capabilities:
                agents = await enhanced_message_bus.discover_agents_by_capability(capability.name)
                suitable_agents.extend(agents)
            
            # Remove duplicates and filter by zone if specified
            suitable_agents = list(set(suitable_agents))
            if zone:
                suitable_agents = [
                    agent for agent in suitable_agents 
                    if agent in self.agent_configs and self.agent_configs[agent].zone == zone
                ]
        else:
            # Fallback to traditional method
            suitable_agents = self._find_suitable_agents(
                required_capabilities=required_capabilities or [],
                zone=zone,
                max_load=self.max_concurrent_tasks_per_agent
            )
        
        if not suitable_agents:
            logger.warning("No suitable agents available for task assignment")
            return None
        
        # Select the best agent based on routing strategy
        if routing_strategy == "load_balanced":
            # Use enhanced message bus load balancing
            best_agent = await enhanced_message_bus.select_least_loaded_agent(suitable_agents)
        elif routing_strategy == "round_robin":
            # Simple round-robin selection
            best_agent = suitable_agents[len(self.task_queue) % len(suitable_agents)]
        else:
            # Default: least loaded agent
            best_agent = min(suitable_agents, 
                            key=lambda aid: len(self.task_assignments.get(aid, set())))
        
        # Create task with enhanced coordination
        task_id = await self.assign_task(best_agent, task_type, data, priority)
        
        if task_id:
            # Use enhanced coordination for task execution
            task = self.task_queue[task_id]
            success = await self.coordinate_task_execution(task, routing_strategy)
            if not success:
                logger.warning(f"Enhanced coordination failed for task {task_id}")
        
        return task_id
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive status for an agent"""
        status = {
            "agent_id": agent_id,
            "exists": agent_id in self.agent_configs,
            "running": agent_id in self.running_processes,
            "tasks_assigned": len(self.task_assignments.get(agent_id, set())),
            "registry_info": None,
            "resource_usage": None,
            "process_info": None
        }
        
        # Get registry information
        agent_info = agent_registry.get_agent(agent_id)
        if agent_info:
            status["registry_info"] = agent_info.to_dict()
        
        # Get resource usage
        resource_usage = resource_manager.get_agent_usage(agent_id)
        if resource_usage:
            status["resource_usage"] = resource_usage.to_dict()
        
        # Get process information
        if agent_id in self.running_processes:
            agent_process = self.running_processes[agent_id]
            status["process_info"] = {
                "pid": agent_process.process.pid,
                "started_at": agent_process.started_at.isoformat(),
                "restart_count": agent_process.restart_count,
                "last_restart": agent_process.last_restart.isoformat() if agent_process.last_restart else None
            }
        
        return status
    
    def list_agents(self, zone: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all agents with their status"""
        agents = []
        
        for agent_id in self.agent_configs.keys():
            if zone and self.agent_configs[agent_id].zone != zone:
                continue
            agents.append(self.get_agent_status(agent_id))
        
        return agents
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id not in self.task_queue:
            return None
        
        task = self.task_queue[task_id]
        return {
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "task_type": task.task_type,
            "priority": task.priority.name,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "retry_count": task.retry_count,
            "has_result": task.result is not None
        }
    
    def _find_suitable_agents(self, required_capabilities: List[AgentCapability],
                             zone: Optional[str] = None,
                             max_load: int = 5) -> List[str]:
        """Find agents suitable for a task"""
        suitable_agents = []
        
        for agent_id in self.running_processes.keys():
            agent_info = agent_registry.get_agent(agent_id)
            if not agent_info or not agent_info.is_healthy:
                continue
            
            # Check zone
            if zone and agent_info.zone != zone:
                continue
            
            # Check capabilities
            agent_capabilities = set(agent_info.capabilities)
            required_caps = set(required_capabilities)
            if not required_caps.issubset(agent_capabilities):
                continue
            
            # Check load
            current_load = len(self.task_assignments.get(agent_id, set()))
            if current_load >= max_load:
                continue
            
            suitable_agents.append(agent_id)
        
        return suitable_agents
    
    def _get_default_tools(self, agent_type: str) -> List[str]:
        """Get default tools for an agent type"""
        tool_mappings = {
            "research": ["mcp_filesystem", "web_search", "document_analysis"],
            "developer": ["mcp_filesystem", "mcp_git", "terminal"],
            "solomon": ["mcp_filesystem", "web_search"],
            "jarvis": ["mcp_filesystem", "mcp_git", "terminal", "web_search"],
            "default": ["mcp_filesystem"]
        }
        return tool_mappings.get(agent_type, tool_mappings["default"])
    
    async def _generate_agent_code(self, name: str, agent_type: str, config: AgentConfig) -> str:
        """Generate agent code from template"""
        template_file = self.templates_dir / f"{agent_type}_agent.py.template"
        if not template_file.exists():
            template_file = self.templates_dir / "base_agent.py.template"
        
        if template_file.exists():
            with open(template_file) as f:
                template = f.read()
        else:
            # Default template
            template = f'''"""
{name} Agent - BoarderframeOS
Generated agent implementation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_agent import BaseAgent, AgentConfig
from core.llm_client import LLMClient
import asyncio
from typing import Dict, Any

class {name}(BaseAgent):
    """Generated {agent_type} agent"""
    
    async def think(self, context: Dict[str, Any]) -> str:
        """Agent reasoning process"""
        # Use LLM for reasoning
        prompt = f"""
You are {config.role}.

Your goals are:
{chr(10).join(f"- {{goal}}" for goal in config.goals)}

Current context:
{{context}}

Based on this context, what should you do next? Provide a clear thought process.
"""
        
        response = await self.llm.chat([{{"role": "user", "content": prompt}}])
        return response.content
    
    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions based on thoughts"""
        # Simple action framework
        if "search" in thought.lower():
            return {{"action": "search", "query": thought}}
        elif "analyze" in thought.lower():
            return {{"action": "analyze", "data": context}}
        elif "create" in thought.lower():
            return {{"action": "create", "content": thought}}
        else:
            return {{"action": "wait", "reason": "No clear action identified"}}

async def main():
    """Main entry point"""
    config = AgentConfig(
        name="{name}",
        role="{config.role}",
        goals={config.goals},
        tools={config.tools},
        zone="{config.zone}",
        model="{config.model}"
    )
    
    agent = {name}(config)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        return template
    
    async def _check_resource_availability(self, config: AgentConfig) -> bool:
        """Check if sufficient resources are available to start an agent"""
        system_usage = resource_manager.get_system_usage()
        
        # Basic resource checks
        if system_usage.memory_percent > 90:
            return False
        
        if system_usage.cpu_percent > 95:
            return False
        
        return True
    
    async def _start_agent_process(self, agent_file: Path, config: AgentConfig, **kwargs) -> Optional[subprocess.Popen]:
        """Start an agent process"""
        try:
            # Set up environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd())
            
            # Start process
            process = subprocess.Popen(
                [sys.executable, str(agent_file)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment to check if process started successfully
            await asyncio.sleep(1)
            if process.poll() is not None:
                # Process died immediately
                stdout, stderr = process.communicate()
                logger.error(f"Agent process died immediately. stdout: {stdout}, stderr: {stderr}")
                return None
            
            return process
            
        except Exception as e:
            logger.error(f"Failed to start agent process: {e}")
            return None
    
    async def _task_processor(self):
        """Process the task queue"""
        while self.running:
            try:
                # Get pending tasks sorted by priority
                pending_tasks = [
                    task for task in self.task_queue.values()
                    if task.status == "pending"
                ]
                pending_tasks.sort(key=lambda t: t.priority.value, reverse=True)
                
                for task in pending_tasks:
                    # Check if agent is available
                    if task.agent_id not in self.running_processes:
                        continue
                    
                    current_load = len(self.task_assignments.get(task.agent_id, set()))
                    if current_load >= self.max_concurrent_tasks_per_agent:
                        continue
                    
                    # Assign task
                    task.status = "assigned"
                    task.assigned_at = datetime.now()
                    self.task_assignments[task.agent_id].add(task.task_id)
                    
                    # Send task to agent
                    await message_bus.send_message(AgentMessage(
                        from_agent="agent_controller",
                        to_agent=task.agent_id,
                        message_type=MessageType.TASK_REQUEST,
                        content={
                            "task_id": task.task_id,
                            "task_type": task.task_type,
                            "data": task.data,
                            "priority": task.priority.name
                        },
                        priority=MessagePriority.HIGH if task.priority in [TaskPriority.HIGH, TaskPriority.URGENT] else MessagePriority.NORMAL,
                        requires_response=True,
                        correlation_id=task.task_id
                    ))
                    
                    logger.info(f"Assigned task {task.task_id} to agent {task.agent_id}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Task processor error: {e}")
                await asyncio.sleep(5)
    
    async def _process_monitor(self):
        """Monitor agent processes"""
        while self.running:
            try:
                for agent_id, agent_process in list(self.running_processes.items()):
                    process = agent_process.process
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        logger.warning(f"Agent process {agent_id} (PID: {process.pid}) has terminated")
                        
                        # Clean up
                        del self.running_processes[agent_id]
                        if agent_id in self.task_assignments:
                            del self.task_assignments[agent_id]
                        
                        # Update registry
                        agent_info = agent_registry.get_agent(agent_id)
                        if agent_info:
                            agent_info.state = AgentState.ERROR
                            agent_info.pid = None
                            agent_info.is_healthy = False
                            agent_info.last_error = "Process terminated unexpectedly"
                        
                        # Notify system
                        await message_bus.broadcast(AgentMessage(
                            from_agent="agent_controller",
                            to_agent="system",
                            message_type=MessageType.ALERT,
                            content={
                                "event": "agent_process_died",
                                "agent_id": agent_id,
                                "pid": process.pid
                            }
                        ), topic="system_alerts")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Process monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _health_monitor(self):
        """Monitor agent health"""
        while self.running:
            try:
                for agent_id in list(self.running_processes.keys()):
                    # Send health check
                    await message_bus.send_message(AgentMessage(
                        from_agent="agent_controller",
                        to_agent=agent_id,
                        message_type=MessageType.STATUS_UPDATE,
                        content={"command": "health_check"},
                        priority=MessagePriority.LOW,
                        requires_response=False
                    ))
                
                await asyncio.sleep(120)  # Health check every 2 minutes
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(120)
    
    async def _task_timeout_monitor(self):
        """Monitor for task timeouts"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for task in self.task_queue.values():
                    if task.status == "assigned":
                        # Check deadline
                        if task.deadline and current_time > task.deadline:
                            task.status = "failed"
                            task.completed_at = current_time
                            
                            # Remove from assignments
                            if task.agent_id in self.task_assignments:
                                self.task_assignments[task.agent_id].discard(task.task_id)
                            
                            logger.warning(f"Task {task.task_id} missed deadline")
                        
                        # Check general timeout
                        elif (task.assigned_at and 
                              (current_time - task.assigned_at).total_seconds() > self.task_timeout_seconds):
                            task.status = "timeout"
                            task.completed_at = current_time
                            
                            # Remove from assignments
                            if task.agent_id in self.task_assignments:
                                self.task_assignments[task.agent_id].discard(task.task_id)
                            
                            logger.warning(f"Task {task.task_id} timed out")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Task timeout monitor error: {e}")
                await asyncio.sleep(60)

    # ==================== ENHANCED COORDINATION METHODS ====================
    
    async def _coordination_monitor(self):
        """Monitor coordination patterns and workflows"""
        while self.running:
            try:
                # Check for coordination timeouts
                await self.coordination_manager.check_timeouts()
                
                # Process pending coordination requests
                messages = await enhanced_message_bus.get_messages_for_agent("agent_controller")
                for message in messages:
                    if message.content.get("type") == "coordination_request":
                        await self._handle_coordination_request(message)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Coordination monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _workflow_manager(self):
        """Manage multi-agent workflows"""
        while self.running:
            try:
                # Process active workflows
                completed_workflows = []
                for workflow_id, workflow_info in self.active_workflows.items():
                    status = await self.coordination_manager.get_workflow_status(workflow_id)
                    
                    if status == "completed":
                        completed_workflows.append(workflow_id)
                        await self._notify_workflow_completion(workflow_id, workflow_info)
                    elif status == "failed":
                        completed_workflows.append(workflow_id)
                        await self._handle_workflow_failure(workflow_id, workflow_info)
                
                # Clean up completed workflows
                for workflow_id in completed_workflows:
                    del self.active_workflows[workflow_id]
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Workflow manager error: {e}")
                await asyncio.sleep(10)
    
    async def create_agent_workflow(self, workflow_type: str, participants: List[str], 
                                   tasks: List[Dict], coordinator: str = None) -> str:
        """Create a multi-agent workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Determine coordination pattern
            pattern = CoordinationPattern.SEQUENTIAL
            if workflow_type == "parallel":
                pattern = CoordinationPattern.PARALLEL
            elif workflow_type == "pipeline":
                pattern = CoordinationPattern.PIPELINE
            elif workflow_type == "scatter_gather":
                pattern = CoordinationPattern.SCATTER_GATHER
            
            # Create workflow with coordination manager
            await self.coordination_manager.create_workflow(
                workflow_id=workflow_id,
                pattern=pattern,
                participants=participants,
                coordinator=coordinator or "agent_controller",
                tasks=tasks
            )
            
            # Track workflow
            self.active_workflows[workflow_id] = {
                "type": workflow_type,
                "participants": participants,
                "tasks": tasks,
                "coordinator": coordinator,
                "created_at": datetime.now(),
                "status": "active"
            }
            
            logger.info(f"Created workflow {workflow_id} with {len(participants)} participants")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            raise
    
    async def coordinate_task_execution(self, task: AgentTask, strategy: str = "capability_based") -> bool:
        """Coordinate task execution using enhanced routing"""
        try:
            # Create enhanced message for task assignment
            routing_strategy = RoutingStrategy.CAPABILITY_BASED
            if strategy == "load_balanced":
                routing_strategy = RoutingStrategy.LOAD_BALANCED
            elif strategy == "round_robin":
                routing_strategy = RoutingStrategy.ROUND_ROBIN
            
            message = EnhancedAgentMessage(
                from_agent="agent_controller",
                to_agent=task.agent_id,
                message_type=MessageType.TASK_REQUEST,
                content={
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "data": task.data,
                    "priority": task.priority.value,
                    "deadline": task.deadline.isoformat() if task.deadline else None
                },
                priority=task.priority,
                routing_strategy=routing_strategy,
                requires_response=True,
                expected_capabilities=[task.task_type]
            )
            
            # Send via enhanced message bus
            response = await enhanced_message_bus.send_enhanced_message(message)
            
            if response and response.delivery_status == DeliveryStatus.ACKNOWLEDGED:
                task.status = "assigned"
                task.assigned_at = datetime.now()
                
                # Track assignment
                if task.agent_id not in self.task_assignments:
                    self.task_assignments[task.agent_id] = set()
                self.task_assignments[task.agent_id].add(task.task_id)
                
                logger.info(f"Task {task.task_id} assigned to {task.agent_id} via enhanced routing")
                return True
            else:
                logger.warning(f"Failed to assign task {task.task_id} to {task.agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error coordinating task execution: {e}")
            return False
    
    async def request_agent_consensus(self, decision_id: str, participants: List[str], 
                                    proposal: Dict, voting_method: str = "majority") -> Dict:
        """Request consensus decision from multiple agents"""
        try:
            result = await self.coordination_manager.consensus_manager.request_consensus(
                proposal_id=decision_id,
                participants=participants,
                proposal=proposal,
                voting_method=voting_method,
                timeout_seconds=300  # 5 minutes
            )
            
            logger.info(f"Consensus result for {decision_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error requesting consensus: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def initiate_agent_auction(self, auction_id: str, task: Dict, 
                                   participants: List[str], duration: int = 60) -> Dict:
        """Initiate task auction among agents"""
        try:
            result = await self.coordination_manager.auction_manager.start_auction(
                auction_id=auction_id,
                task=task,
                participants=participants,
                duration_seconds=duration
            )
            
            logger.info(f"Auction {auction_id} result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error initiating auction: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def register_agent_capabilities(self, agent_id: str, capabilities: List[AgentCapability]):
        """Register capabilities for an agent"""
        self.agent_capabilities[agent_id] = capabilities
        
        # Register with enhanced message bus for capability-based routing
        await enhanced_message_bus.register_agent_capabilities(agent_id, capabilities)
        
        logger.info(f"Registered {len(capabilities)} capabilities for agent {agent_id}")
    
    async def discover_agents_by_capability(self, capability: str) -> List[str]:
        """Discover agents that have a specific capability"""
        agents = await enhanced_message_bus.discover_agents_by_capability(capability)
        return agents
    
    async def get_agent_coordination_metrics(self) -> Dict[str, Any]:
        """Get coordination metrics for all agents"""
        metrics = {
            "active_workflows": len(self.active_workflows),
            "coordination_patterns": await self.coordination_manager.get_usage_statistics(),
            "message_bus_metrics": await enhanced_message_bus.get_performance_metrics(),
            "agent_capabilities": {
                agent_id: len(capabilities) 
                for agent_id, capabilities in self.agent_capabilities.items()
            }
        }
        
        return metrics
    
    async def _handle_coordination_request(self, message: EnhancedAgentMessage):
        """Handle incoming coordination requests"""
        try:
            request_type = message.content.get("request_type")
            
            if request_type == "workflow_creation":
                workflow_id = await self.create_agent_workflow(
                    workflow_type=message.content["workflow_type"],
                    participants=message.content["participants"],
                    tasks=message.content["tasks"]
                )
                
                # Send response
                response = EnhancedAgentMessage(
                    from_agent="agent_controller",
                    to_agent=message.from_agent,
                    message_type=MessageType.COORDINATION,
                    content={"workflow_id": workflow_id, "status": "created"},
                    routing_strategy=RoutingStrategy.DIRECT,
                    correlation_id=message.correlation_id
                )
                await enhanced_message_bus.send_enhanced_message(response)
                
            elif request_type == "capability_discovery":
                capability = message.content["capability"]
                agents = await self.discover_agents_by_capability(capability)
                
                response = EnhancedAgentMessage(
                    from_agent="agent_controller",
                    to_agent=message.from_agent,
                    message_type=MessageType.COORDINATION,
                    content={"agents": agents, "capability": capability},
                    routing_strategy=RoutingStrategy.DIRECT,
                    correlation_id=message.correlation_id
                )
                await enhanced_message_bus.send_enhanced_message(response)
                
        except Exception as e:
            logger.error(f"Error handling coordination request: {e}")
    
    async def _notify_workflow_completion(self, workflow_id: str, workflow_info: Dict):
        """Notify participants of workflow completion"""
        try:
            for participant in workflow_info["participants"]:
                message = EnhancedAgentMessage(
                    from_agent="agent_controller",
                    to_agent=participant,
                    message_type=MessageType.COORDINATION,
                    content={
                        "event": "workflow_completed",
                        "workflow_id": workflow_id,
                        "workflow_type": workflow_info["type"]
                    },
                    routing_strategy=RoutingStrategy.DIRECT
                )
                await enhanced_message_bus.send_enhanced_message(message)
            
            logger.info(f"Notified workflow completion: {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error notifying workflow completion: {e}")
    
    async def _handle_workflow_failure(self, workflow_id: str, workflow_info: Dict):
        """Handle workflow failure"""
        try:
            # Notify participants of failure
            for participant in workflow_info["participants"]:
                message = EnhancedAgentMessage(
                    from_agent="agent_controller",
                    to_agent=participant,
                    message_type=MessageType.ALERT,
                    content={
                        "event": "workflow_failed",
                        "workflow_id": workflow_id,
                        "workflow_type": workflow_info["type"]
                    },
                    routing_strategy=RoutingStrategy.DIRECT
                )
                await enhanced_message_bus.send_enhanced_message(message)
            
            logger.warning(f"Workflow failed: {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error handling workflow failure: {e}")

    # ==================== END ENHANCED COORDINATION METHODS ====================

# Global agent controller instance
agent_controller = AgentController()
