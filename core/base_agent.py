"""
BoarderframeOS Core Agent Framework
The foundation for all AI agents in the system
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import httpx

from .cost_management import (
    API_COST_SETTINGS,
    estimate_daily_cost,
    get_agent_cost_policy,
)
from .llm_client import (
    ANTHROPIC_CONFIG,
    CLAUDE_OPUS_CONFIG,
    OLLAMA_CONFIG,
    LLMClient,
    LLMConfig,
)
from .message_bus import (
    AgentMessage,
    MessagePriority,
    MessageType,
    broadcast_status,
    message_bus,
    send_task_request,
)
from .registry_integration import get_registry_client, register_agent_with_database


# Agent States
class AgentState(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentStatus(Enum):
    """Simplified status enumeration used by tests."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for an agent"""

    name: str
    role: str
    goals: List[str]
    tools: List[str]
    department: str = "general"
    compute_allocation: float = 5.0  # Percentage of total TOPS
    memory_limit_gb: float = 8.0
    zone: str = "default"
    model: str = "llama-maverick-30b"  # Which LLM to use
    temperature: float = 0.7
    max_concurrent_tasks: int = 5


@dataclass
class AgentMemory:
    """Short and long-term memory storage"""

    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: List[Dict[str, Any]] = field(default_factory=list)
    max_short_term: int = 100

    def add(self, memory: Dict[str, Any], permanent: bool = False):
        """Add a memory"""
        memory["timestamp"] = datetime.now().isoformat()

        if permanent:
            self.long_term.append(memory)
        else:
            self.short_term.append(memory)
            if len(self.short_term) > self.max_short_term:
                # Move oldest to long-term
                self.long_term.append(self.short_term.pop(0))

    def recall(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recall memories matching query"""
        results = []
        all_memories = self.short_term + self.long_term

        for memory in all_memories:
            if query.lower() in str(memory).lower():
                results.append(memory)
                if len(results) >= limit:
                    break

        return results

    def __len__(self) -> int:
        """Return total number of stored memories."""
        return len(self.short_term) + len(self.long_term)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        """Allow index access to combined memory."""
        combined = self.short_term + self.long_term
        return combined[index]


class BaseAgent(ABC):
    """Base class for all BoarderframeOS agents"""

    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            allowed = {k: v for k, v in kwargs.items() if k in AgentConfig.__annotations__}
            allowed.setdefault("goals", [])
            allowed.setdefault("tools", [])
            config = AgentConfig(**allowed)
        self.config = config
        self.state = AgentState.INITIALIZING
        self.memory = AgentMemory()
        self.active_tasks: List[asyncio.Task] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.tools: Dict[str, Callable] = {}
        self.active = True
        self.logger = self._setup_logger()
        self.message_handlers: Dict[MessageType, Callable] = {}

        # Cost management
        self.cost_policy = get_agent_cost_policy(config.name)
        self.api_call_count = 0
        self.daily_cost = 0.0
        self.cost_optimization_enabled = API_COST_SETTINGS["cost_optimization_enabled"]

        # LLM client for reasoning
        if "claude" in config.model.lower():
            llm_config = CLAUDE_OPUS_CONFIG
        else:
            llm_config = OLLAMA_CONFIG

        # Override with agent-specific settings
        llm_config.model = config.model
        llm_config.temperature = config.temperature
        self.llm = LLMClient(llm_config)

        # Performance metrics
        self.metrics = {
            "thoughts_processed": 0,
            "actions_taken": 0,
            "errors": 0,
            "start_time": datetime.now(),
            "api_calls_made": 0,
            "estimated_cost": 0.0,
        }

        # Initialize tools
        self._load_tools()

        # Register with message bus
        asyncio.create_task(self._register_with_message_bus())

        # Register with database registry
        self.registry_id = None
        asyncio.create_task(self._register_with_database_registry())

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return self.config.name

    @property
    def department(self) -> str:
        return self.config.department

    @property
    def role(self) -> str:
        return self.config.role

    @property
    def status(self) -> AgentStatus:
        mapping = {
            AgentState.INITIALIZING: AgentStatus.INITIALIZING,
            AgentState.IDLE: AgentStatus.IDLE,
            AgentState.RUNNING: AgentStatus.RUNNING,
            AgentState.THINKING: AgentStatus.RUNNING,
            AgentState.ACTING: AgentStatus.RUNNING,
            AgentState.WAITING: AgentStatus.RUNNING,
            AgentState.STOPPED: AgentStatus.STOPPED,
            AgentState.ERROR: AgentStatus.ERROR,
            AgentState.TERMINATED: AgentStatus.STOPPED,
        }
        return mapping.get(self.state, AgentStatus.ERROR)

    # ------------------------------------------------------------------
    # Lifecycle helpers used in tests
    # ------------------------------------------------------------------
    async def initialize(self) -> None:
        """Initialize the agent."""
        self.state = AgentState.IDLE

    async def start(self) -> None:
        """Start the agent."""
        self.state = AgentState.RUNNING

    async def stop(self) -> None:
        """Stop the agent."""
        self.state = AgentState.STOPPED

    async def add_memory(self, item: Dict[str, Any], permanent: bool = False) -> None:
        """Add an item to memory."""
        self.memory.add(item, permanent)

    async def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search memory for items containing the query."""
        return self.memory.recall(query)

    async def health_check(self) -> Dict[str, Any]:
        """Return a simple health report."""
        uptime = (datetime.now() - self.metrics["start_time"]).total_seconds()
        return {
            "status": "healthy",
            "name": self.config.name,
            "uptime": uptime,
            "memory_usage": len(self.memory),
        }

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Basic message handler that simply echoes the content."""
        self.log(f"Received message: {message}")
        return {"received": message}

    def _setup_logger(self) -> logging.Logger:
        """Set up agent-specific logger"""
        logger = logging.getLogger(f"agent.{self.config.name}")

        # Create logs directory if it doesn't exist
        log_dir = Path("logs/agents")
        log_dir.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(f"logs/agents/{self.config.name}.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _load_tools(self):
        """Load MCP tools based on configuration"""
        for tool_name in self.config.tools:
            if tool_name == "filesystem":
                self.tools["filesystem"] = self._filesystem_tool
            elif tool_name == "git":
                self.tools["git"] = self._git_tool
            elif tool_name == "browser":
                self.tools["browser"] = self._browser_tool

    async def _filesystem_tool(self, action: str, **params) -> Dict[str, Any]:
        """Filesystem operations via MCP"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8001/rpc",
                    json={"method": f"filesystem.{action}", "params": params},
                )
                return response.json()
        except Exception as e:
            return {"error": f"Filesystem tool error: {e}"}

    async def _git_tool(self, action: str, **params) -> Dict[str, Any]:
        """Git operations via MCP"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8002/rpc",
                    json={"method": f"git.{action}", "params": params},
                )
                return response.json()
        except Exception as e:
            return {"error": f"Git tool error: {e}"}

    async def _browser_tool(self, action: str, **params) -> Dict[str, Any]:
        """Browser automation via MCP"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8003/rpc",
                    json={"method": f"browser.{action}", "params": params},
                )
                return response.json()
        except Exception as e:
            return {"error": f"Browser tool error: {e}"}

    async def think(self, context: Dict[str, Any]) -> str:
        """Basic reasoning step used when no custom logic is provided."""
        return "acknowledged"

    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Basic action step used when no custom logic is provided."""
        return {"thought": thought, "performed": True}

    async def get_context(self) -> Dict[str, Any]:
        """Gather context from environment and memory"""
        # Get messages from message bus
        messages = await message_bus.get_messages(self.config.name)

        context = {
            "current_time": datetime.now().isoformat(),
            "agent_name": self.config.name,
            "agent_role": self.config.role,
            "current_goals": self.config.goals,
            "available_tools": list(self.tools.keys()),
            "recent_memories": self.memory.short_term[-10:],
            "message_queue_size": self.message_queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "new_messages": messages,
        }

        return context

    async def run(self):
        """Main agent loop - Event-driven to minimize API costs"""
        self.log(f"Starting {self.config.name} agent...")
        self.state = AgentState.IDLE

        try:
            # Initial broadcast
            await self.broadcast_status()

            while self.active and self.state not in [
                AgentState.TERMINATED,
                AgentState.ERROR,
            ]:
                # Check for new messages/tasks
                context = await self.get_context()
                new_messages = context.get("new_messages", [])

                if new_messages or self.message_queue.qsize() > 0:
                    # Only think/act when there's actual work to do
                    self.state = AgentState.THINKING
                    thought = await self.think(context)
                    self.metrics["thoughts_processed"] += 1

                    # Act
                    self.state = AgentState.ACTING
                    result = await self.act(thought, context)
                    self.metrics["actions_taken"] += 1

                    # Remember
                    self.memory.add(
                        {"thought": thought, "action": result, "context": context}
                    )

                    # Log
                    self.log(f"Thought: {thought[:100]}...")
                    self.log(f"Action result: {str(result)[:100]}...")

                    # Process messages
                    await self._process_messages(new_messages)
                else:
                    # No work to do - stay idle and save API costs
                    self.state = AgentState.IDLE
                    self.log(
                        "No tasks - remaining idle to save API costs", level="debug"
                    )

                # Broadcast status less frequently to save resources
                if self.metrics["thoughts_processed"] % 50 == 0:
                    await self.broadcast_status()

                # Longer wait time to reduce resource usage
                await asyncio.sleep(5)  # Check every 5 seconds instead of 1

        except Exception as e:
            self.state = AgentState.ERROR
            self.metrics["errors"] += 1
            self.log(f"Error in main loop: {e}", level="error")
            raise

    def log(self, message: str, level: str = "info"):
        """Log a message"""
        log_func = getattr(self.logger, level)
        log_func(message)
        print(f"[{self.config.name}] {message}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        uptime = (datetime.now() - self.metrics["start_time"]).total_seconds()
        return {
            **self.metrics,
            "uptime_seconds": uptime,
            "thoughts_per_minute": (
                self.metrics["thoughts_processed"] / max(uptime / 60, 1)
            ),
            "actions_per_minute": (self.metrics["actions_taken"] / max(uptime / 60, 1)),
            "error_rate": self.metrics["errors"]
            / max(self.metrics["thoughts_processed"], 1),
        }

    async def _register_with_message_bus(self):
        """Register this agent with the message bus"""
        await message_bus.register_agent(self.config.name)

        # Subscribe to relevant topics
        await message_bus.subscribe_to_topic(self.config.name, "broadcast")
        await message_bus.subscribe_to_topic(self.config.name, self.config.zone)

        self.log(f"Registered with message bus")

    async def _register_with_database_registry(self):
        """Register this agent with the database registry"""
        try:
            self.registry_id = await register_agent_with_database(self.config)
            self.log(f"Registered with database registry, ID: {self.registry_id}")

            # Update health status periodically
            asyncio.create_task(self._update_registry_health())

        except Exception as e:
            self.log(
                f"Failed to register with database registry: {e}", level=logging.WARNING
            )

    async def _update_registry_health(self):
        """Periodically update health status in the registry"""
        while self.active:
            try:
                if self.registry_id:
                    registry_client = await get_registry_client()

                    # Calculate current load percentage
                    load_percentage = (
                        len(self.active_tasks) / self.config.max_concurrent_tasks
                    ) * 100

                    # Determine health status based on agent state
                    health_status = "healthy"
                    if self.state == AgentState.ERROR:
                        health_status = "unhealthy"
                    elif self.state in [AgentState.THINKING, AgentState.ACTING]:
                        health_status = "busy"

                    await registry_client.update_agent_health(
                        self.registry_id, health_status, load_percentage
                    )

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.log(f"Registry health update error: {e}", level=logging.DEBUG)
                await asyncio.sleep(60)  # Wait longer on error

    async def _process_messages(self, messages: List[AgentMessage]):
        """Process incoming messages"""
        for message in messages:
            try:
                # Check if we have a handler for this message type
                if message.message_type in self.message_handlers:
                    await self.message_handlers[message.message_type](message)
                else:
                    # Default handling
                    self.log(
                        f"Received {message.message_type} from {message.from_agent}"
                    )

                    if message.requires_response:
                        # Send acknowledgment
                        response = AgentMessage(
                            from_agent=self.config.name,
                            to_agent=message.from_agent,
                            message_type=MessageType.TASK_RESPONSE,
                            content={
                                "status": "received",
                                "original_message": message.content,
                            },
                            correlation_id=message.correlation_id,
                        )
                        await message_bus.send_message(response)

            except Exception as e:
                self.log(f"Error processing message: {e}", level="error")

    async def send_task_to_agent(
        self,
        to_agent: str,
        task: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> Optional[AgentMessage]:
        """Send a task to another agent and wait for response"""
        correlation_id = await send_task_request(
            self.config.name, to_agent, task, priority
        )

        # Wait for response
        response = await message_bus.wait_for_response(correlation_id, timeout=30.0)
        return response

    async def broadcast_status(self):
        """Broadcast current status to other agents"""
        status = {
            "state": self.state.value,
            "metrics": self.get_metrics(),
            "memory_size": len(self.memory.short_term) + len(self.memory.long_term),
            "active_tasks": len(self.active_tasks),
        }

        await broadcast_status(self.config.name, status)

    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
        self.log(f"Registered handler for {message_type}")

    async def terminate(self):
        """Gracefully shut down the agent"""
        self.log(f"Terminating {self.config.name}...")
        self.active = False

        # Unregister from message bus
        await message_bus.unregister_agent(self.config.name)

        # Cancel active tasks
        for task in self.active_tasks:
            task.cancel()

        # Save memory to disk
        memory_file = Path(f"data/agents/{self.config.name}_memory.json")
        memory_file.parent.mkdir(parents=True, exist_ok=True)

        with open(memory_file, "w") as f:
            json.dump(
                {
                    "short_term": self.memory.short_term,
                    "long_term": self.memory.long_term,
                    "metrics": self.get_metrics(),
                },
                f,
                default=str,
            )

        self.state = AgentState.TERMINATED
        self.log(f"{self.config.name} terminated successfully")
