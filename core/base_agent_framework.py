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


# Agent States
class AgentState(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"
    TERMINATED = "terminated"

# Agent Message Types
@dataclass
class AgentMessage:
    """Messages passed between agents"""
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    correlation_id: Optional[str] = None

@dataclass
class AgentMemory:
    """Short and long-term memory storage"""
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: List[Dict[str, Any]] = field(default_factory=list)
    max_short_term: int = 100

    def add(self, memory: Dict[str, Any], permanent: bool = False):
        """Add a memory"""
        memory['timestamp'] = datetime.now().isoformat()

        if permanent:
            self.long_term.append(memory)
        else:
            self.short_term.append(memory)
            if len(self.short_term) > self.max_short_term:
                # Move oldest to long-term
                self.long_term.append(self.short_term.pop(0))

    def recall(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recall memories matching query"""
        # Simple keyword search for now
        # TODO: Implement vector similarity search
        results = []
        all_memories = self.short_term + self.long_term

        for memory in all_memories:
            if query.lower() in str(memory).lower():
                results.append(memory)
                if len(results) >= limit:
                    break

        return results

@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    role: str
    goals: List[str]
    tools: List[str]
    compute_allocation: float = 5.0  # Percentage of total TOPS
    memory_limit_gb: float = 8.0
    zone: str = "default"
    model: str = "llama-maverick-30b"  # Which LLM to use
    temperature: float = 0.7
    max_concurrent_tasks: int = 5

class BaseAgent(ABC):
    """Base class for all BoarderframeOS agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.INITIALIZING
        self.memory = AgentMemory()
        self.active_tasks: List[asyncio.Task] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.tools: Dict[str, Callable] = {}
        self.logger = self._setup_logger()

        # Performance metrics
        self.metrics = {
            'thoughts_processed': 0,
            'actions_taken': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

        # Initialize tools
        self._load_tools()

    def _setup_logger(self) -> logging.Logger:
        """Set up agent-specific logger"""
        logger = logging.getLogger(f"agent.{self.config.name}")
        handler = logging.FileHandler(f"logs/agents/{self.config.name}.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
            # Add more tools as needed

    async def _filesystem_tool(self, action: str, **params) -> Dict[str, Any]:
        """Filesystem operations via MCP"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/rpc",
                json={
                    "method": f"filesystem.{action}",
                    "params": params
                }
            )
            return response.json()

    async def _git_tool(self, action: str, **params) -> Dict[str, Any]:
        """Git operations via MCP"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8002/rpc",
                json={
                    "method": f"git.{action}",
                    "params": params
                }
            )
            return response.json()

    async def _browser_tool(self, action: str, **params) -> Dict[str, Any]:
        """Browser automation via MCP"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/rpc",
                json={
                    "method": f"browser.{action}",
                    "params": params
                }
            )
            return response.json()

    @abstractmethod
    async def think(self, context: Dict[str, Any]) -> str:
        """
        Core reasoning method - must be implemented by each agent
        This is where the LLM reasoning happens
        """
        pass

    @abstractmethod
    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute actions based on thoughts
        This is where tool usage happens
        """
        pass

    async def perceive(self) -> Dict[str, Any]:
        """Gather context from environment and memory"""
        context = {
            'current_time': datetime.now().isoformat(),
            'agent_name': self.config.name,
            'agent_role': self.config.role,
            'current_goals': self.config.goals,
            'available_tools': list(self.tools.keys()),
            'recent_memories': self.memory.short_term[-10:],
            'message_queue_size': self.message_queue.qsize(),
            'active_tasks': len(self.active_tasks)
        }

        # Check for new messages
        messages = []
        while not self.message_queue.empty():
            try:
                msg = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
                messages.append(msg)
            except asyncio.TimeoutError:
                break

        if messages:
            context['new_messages'] = messages

        return context

    async def run(self):
        """Main agent loop"""
        self.log(f"Starting {self.config.name} agent...")
        self.state = AgentState.IDLE

        try:
            while self.state not in [AgentState.TERMINATED, AgentState.ERROR]:
                # Perceive
                context = await self.perceive()

                # Think
                self.state = AgentState.THINKING
                thought = await self.think(context)
                self.metrics['thoughts_processed'] += 1

                # Act
                self.state = AgentState.ACTING
                result = await self.act(thought, context)
                self.metrics['actions_taken'] += 1

                # Remember
                self.memory.add({
                    'thought': thought,
                    'action': result,
                    'context': context
                })

                # Log
                self.log(f"Thought: {thought[:100]}...")
                self.log(f"Action result: {result}")

                # Wait before next cycle
                self.state = AgentState.WAITING
                await asyncio.sleep(1)  # Adjust based on needs

        except Exception as e:
            self.state = AgentState.ERROR
            self.metrics['errors'] += 1
            self.log(f"Error in main loop: {e}", level="error")
            raise

    async def send_message(self, to_agent: str, message_type: str,
                          content: Dict[str, Any], requires_response: bool = False):
        """Send a message to another agent"""
        message = AgentMessage(
            from_agent=self.config.name,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            requires_response=requires_response
        )

        # TODO: Implement actual message routing
        self.log(f"Sending message to {to_agent}: {message_type}")

    async def receive_message(self, message: AgentMessage):
        """Receive a message from another agent"""
        await self.message_queue.put(message)

    def log(self, message: str, level: str = "info"):
        """Log a message"""
        log_func = getattr(self.logger, level)
        log_func(message)

        # Also send to UI console
        # TODO: Implement WebSocket broadcast

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
        return {
            **self.metrics,
            'uptime_seconds': uptime,
            'thoughts_per_minute': (self.metrics['thoughts_processed'] / uptime) * 60,
            'actions_per_minute': (self.metrics['actions_taken'] / uptime) * 60,
            'error_rate': self.metrics['errors'] / max(self.metrics['thoughts_processed'], 1)
        }

    async def spawn_sub_agent(self, name: str, role: str, goal: str) -> 'BaseAgent':
        """Spawn a temporary sub-agent for specific tasks"""
        # TODO: Implement sub-agent spawning
        self.log(f"Spawning sub-agent: {name} for {goal}")

    async def terminate(self):
        """Gracefully shut down the agent"""
        self.log(f"Terminating {self.config.name}...")

        # Cancel active tasks
        for task in self.active_tasks:
            task.cancel()

        # Save memory to disk
        memory_file = Path(f"data/agents/{self.config.name}_memory.json")
        memory_file.parent.mkdir(parents=True, exist_ok=True)

        with open(memory_file, 'w') as f:
            json.dump({
                'short_term': self.memory.short_term,
                'long_term': self.memory.long_term,
                'metrics': self.get_metrics()
            }, f, default=str)

        self.state = AgentState.TERMINATED
        self.log(f"{self.config.name} terminated successfully")


class AgentOrchestrator:
    """Manages all agents in the system"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.zones: Dict[str, List[str]] = {}  # zone_name -> [agent_names]

    async def register_agent(self, agent: BaseAgent):
        """Register a new agent"""
        self.agents[agent.config.name] = agent

        # Add to zone
        zone = agent.config.zone
        if zone not in self.zones:
            self.zones[zone] = []
        self.zones[zone].append(agent.config.name)

    async def start_all(self):
        """Start all registered agents"""
        tasks = []
        for agent in self.agents.values():
            task = asyncio.create_task(agent.run())
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def route_message(self, message: AgentMessage):
        """Route messages between agents"""
        if message.to_agent in self.agents:
            await self.agents[message.to_agent].receive_message(message)
        else:
            logging.error(f"Agent {message.to_agent} not found")

    def get_zone_metrics(self, zone_name: str) -> Dict[str, Any]:
        """Get metrics for all agents in a zone"""
        if zone_name not in self.zones:
            return {}

        metrics = {
            'zone': zone_name,
            'agent_count': len(self.zones[zone_name]),
            'agents': {}
        }

        for agent_name in self.zones[zone_name]:
            if agent_name in self.agents:
                metrics['agents'][agent_name] = self.agents[agent_name].get_metrics()

        return metrics


# Example: Jarvis implementation
class JarvisAgent(BaseAgent):
    """Jarvis - Your AI Chief of Staff"""

    async def think(self, context: Dict[str, Any]) -> str:
        """Jarvis's reasoning process"""
        # In production, this would call your local LLM
        # For now, we'll simulate reasoning

        prompt = f"""
        You are Jarvis, the AI Chief of Staff.

        Current context:
        - Time: {context['current_time']}
        - Active tasks: {context['active_tasks']}
        - Messages pending: {context['message_queue_size']}

        Recent memories:
        {json.dumps(context.get('recent_memories', []), indent=2)}

        What should we do next?
        """

        # TODO: Call local LLaMA model
        # response = await self.llm_call(prompt)

        # Simulated response
        if context['message_queue_size'] > 0:
            return "Process pending messages from other agents"
        elif context['active_tasks'] == 0:
            return "Check for new tasks in the task queue"
        else:
            return "Monitor active tasks and prepare status report"

    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Jarvis's decisions"""

        if "Process pending messages" in thought:
            # Process messages
            messages = context.get('new_messages', [])
            results = []

            for msg in messages:
                self.log(f"Processing message from {msg.from_agent}")
                # Handle different message types
                if msg.message_type == "task_request":
                    results.append(await self._handle_task_request(msg))
                elif msg.message_type == "status_query":
                    results.append(await self._handle_status_query(msg))

            return {"action": "processed_messages", "count": len(messages), "results": results}

        elif "Check for new tasks" in thought:
            # Check filesystem for new tasks
            tasks = await self.tools['filesystem']('list_directory', path='tasks/pending')
            return {"action": "checked_tasks", "found": len(tasks.get('files', []))}

        else:
            # Default: generate status report
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "operational",
                "active_agents": len(self.active_tasks),
                "metrics": self.get_metrics()
            }

            await self.tools['filesystem']('write_file',
                                         path=f"reports/status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                         content=json.dumps(report, indent=2))

            return {"action": "generated_report", "report": report}

    async def _handle_task_request(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle task requests from other agents"""
        task = message.content

        # Validate task
        if 'goal' not in task:
            return {"status": "error", "message": "Task missing goal"}

        # Assign task or spawn sub-agent
        self.log(f"Received task: {task['goal']}")

        # TODO: Implement task assignment logic
        return {"status": "accepted", "task_id": f"task_{datetime.now().timestamp()}"}

    async def _handle_status_query(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle status queries from other agents"""
        return {
            "agent": self.config.name,
            "status": self.state.value,
            "metrics": self.get_metrics()
        }
