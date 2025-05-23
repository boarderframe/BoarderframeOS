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
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import httpx
from pathlib import Path
from .llm_client import LLMClient, LLMConfig, ANTHROPIC_CONFIG, CLAUDE_OPUS_CONFIG

# Agent States
class AgentState(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"
    TERMINATED = "terminated"

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
        results = []
        all_memories = self.short_term + self.long_term
        
        for memory in all_memories:
            if query.lower() in str(memory).lower():
                results.append(memory)
                if len(results) >= limit:
                    break
        
        return results

class BaseAgent(ABC):
    """Base class for all BoarderframeOS agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.INITIALIZING
        self.memory = AgentMemory()
        self.active_tasks: List[asyncio.Task] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.tools: Dict[str, Callable] = {}
        self.active = True
        self.logger = self._setup_logger()
        
        # LLM client for reasoning - default to Claude
        if "claude" in config.model.lower() or config.model == "claude-3-opus-20240229":
            llm_config = CLAUDE_OPUS_CONFIG
        else:
            llm_config = ANTHROPIC_CONFIG
        
        # Override with agent-specific settings
        llm_config.model = config.model
        llm_config.temperature = config.temperature
        self.llm = LLMClient(llm_config)
        
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
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs/agents")
        log_dir.mkdir(parents=True, exist_ok=True)
        
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
    
    async def _filesystem_tool(self, action: str, **params) -> Dict[str, Any]:
        """Filesystem operations via MCP"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8001/rpc",
                    json={
                        "method": f"filesystem.{action}",
                        "params": params
                    }
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
                    json={
                        "method": f"git.{action}",
                        "params": params
                    }
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
                    json={
                        "method": f"browser.{action}",
                        "params": params
                    }
                )
                return response.json()
        except Exception as e:
            return {"error": f"Browser tool error: {e}"}
    
    @abstractmethod
    async def think(self, context: Dict[str, Any]) -> str:
        """Core reasoning method - must be implemented by each agent"""
        pass
    
    @abstractmethod
    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions based on thoughts"""
        pass
    
    async def get_context(self) -> Dict[str, Any]:
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
        
        return context
    
    async def run(self):
        """Main agent loop"""
        self.log(f"Starting {self.config.name} agent...")
        self.state = AgentState.IDLE
        
        try:
            while self.active and self.state not in [AgentState.TERMINATED, AgentState.ERROR]:
                # Get context
                context = await self.get_context()
                
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
                self.log(f"Action result: {str(result)[:100]}...")
                
                # Wait before next cycle
                self.state = AgentState.WAITING
                await asyncio.sleep(1)
                
        except Exception as e:
            self.state = AgentState.ERROR
            self.metrics['errors'] += 1
            self.log(f"Error in main loop: {e}", level="error")
            raise
    
    def log(self, message: str, level: str = "info"):
        """Log a message"""
        log_func = getattr(self.logger, level)
        log_func(message)
        print(f"[{self.config.name}] {message}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
        return {
            **self.metrics,
            'uptime_seconds': uptime,
            'thoughts_per_minute': (self.metrics['thoughts_processed'] / max(uptime/60, 1)),
            'actions_per_minute': (self.metrics['actions_taken'] / max(uptime/60, 1)),
            'error_rate': self.metrics['errors'] / max(self.metrics['thoughts_processed'], 1)
        }
    
    async def terminate(self):
        """Gracefully shut down the agent"""
        self.log(f"Terminating {self.config.name}...")
        self.active = False
        
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