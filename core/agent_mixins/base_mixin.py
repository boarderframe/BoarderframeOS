"""
BaseMixin - Core agent API functionality
Provides fundamental agent lifecycle management
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class BaseMixin:
    """Core agent functionality mixin"""
    
    def __init__(self):
        """Initialize base agent components"""
        self.agent_id = str(uuid.uuid4())
        self.state = AgentState.INITIALIZING
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None
        self.error_count = 0
        self.task_count = 0
        self._running = False
        self._main_task: Optional[asyncio.Task] = None
        
        # These will be set by UniversalAgent
        self.name: str = ""
        self.config: Any = None
        self.logger: Optional[logging.Logger] = None
        
    async def start(self) -> None:
        """Start the agent"""
        if self.state == AgentState.RUNNING:
            self.logger.warning(f"Agent {self.name} already running")
            return
            
        self.logger.info(f"Starting agent {self.name}")
        self.state = AgentState.READY
        self.start_time = datetime.now()
        self._running = True
        
        # Start main processing loop
        self._main_task = asyncio.create_task(self._run())
        
        self.state = AgentState.RUNNING
        self.logger.info(f"Agent {self.name} started successfully")
        
    async def stop(self) -> None:
        """Stop the agent gracefully"""
        if self.state == AgentState.STOPPED:
            self.logger.warning(f"Agent {self.name} already stopped")
            return
            
        self.logger.info(f"Stopping agent {self.name}")
        self.state = AgentState.STOPPING
        self._running = False
        
        # Cancel main task if running
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
                
        self.stop_time = datetime.now()
        self.state = AgentState.STOPPED
        self.logger.info(f"Agent {self.name} stopped")
        
    async def pause(self) -> None:
        """Pause agent processing"""
        if self.state != AgentState.RUNNING:
            self.logger.warning(f"Cannot pause agent in state {self.state}")
            return
            
        self.state = AgentState.PAUSED
        self.logger.info(f"Agent {self.name} paused")
        
    async def resume(self) -> None:
        """Resume agent processing"""
        if self.state != AgentState.PAUSED:
            self.logger.warning(f"Cannot resume agent in state {self.state}")
            return
            
        self.state = AgentState.RUNNING
        self.logger.info(f"Agent {self.name} resumed")
        
    async def _run(self) -> None:
        """Main agent processing loop"""
        while self._running:
            try:
                if self.state == AgentState.PAUSED:
                    await asyncio.sleep(1)
                    continue
                    
                # Process messages and tasks
                await self._process_cycle()
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error in agent {self.name} main loop: {e}", exc_info=True)
                
                if self.error_count > 10:
                    self.logger.critical(f"Agent {self.name} exceeded error threshold, stopping")
                    self.state = AgentState.ERROR
                    break
                    
    async def _process_cycle(self) -> None:
        """Single processing cycle - to be implemented by subclasses"""
        # This will be implemented by combining other mixins
        pass
        
    async def report_status(self) -> Dict[str, Any]:
        """Report current agent status"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "state": self.state.value,
            "uptime_seconds": uptime,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "task_count": self.task_count,
            "error_count": self.error_count
        }
        
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return (
            self.state in [AgentState.READY, AgentState.RUNNING, AgentState.PAUSED] and
            self.error_count < 10
        )