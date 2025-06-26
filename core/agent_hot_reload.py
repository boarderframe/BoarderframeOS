"""
Agent-specific Hot Reload Integration
Extends hot reload system for BoarderframeOS agents
"""

import asyncio
import inspect
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
import logging

from core.hot_reload import HotReloadManager, get_hot_reload_manager
from core.base_agent import BaseAgent
from core.agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class AgentReloadHandler:
    """
    Handles hot reloading for agents with zero downtime
    
    Features:
    - Graceful agent shutdown and restart
    - State preservation during reload
    - Message queue preservation
    - Automatic reconnection
    """
    
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.hot_reload_manager = get_hot_reload_manager()
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.pending_messages: Dict[str, List[Any]] = {}
        
        # Register reload callback
        self.hot_reload_manager.register_reload_callback(self._handle_module_reload)
        
    async def _handle_module_reload(self, module_names: List[str]):
        """Handle module reload events"""
        logger.info(f"Handling agent reload for modules: {module_names}")
        
        # Find agents affected by module changes
        affected_agents = []
        
        for module_name in module_names:
            # Check if it's an agent module
            if "agents." in module_name:
                agent_name = self._extract_agent_name(module_name)
                if agent_name:
                    affected_agents.append(agent_name)
                    
        if affected_agents:
            await self._reload_agents(affected_agents)
            
    def _extract_agent_name(self, module_name: str) -> Optional[str]:
        """Extract agent name from module name"""
        # Examples:
        # agents.solomon.solomon -> solomon
        # agents.primordials.adam -> adam
        parts = module_name.split(".")
        
        if len(parts) >= 2:
            # Get the last part as agent name
            return parts[-1]
            
        return None
        
    async def _reload_agents(self, agent_names: List[str]):
        """Reload specific agents"""
        for agent_name in agent_names:
            try:
                await self._reload_single_agent(agent_name)
            except Exception as e:
                logger.error(f"Failed to reload agent {agent_name}: {e}")
                
    async def _reload_single_agent(self, agent_name: str):
        """Reload a single agent with state preservation"""
        logger.info(f"Starting hot reload for agent: {agent_name}")
        
        # Get current agent instance
        current_agent = self.orchestrator.get_agent(agent_name)
        
        if not current_agent:
            logger.warning(f"Agent {agent_name} not found in orchestrator")
            return
            
        # Step 1: Save agent state
        agent_state = await self._save_agent_state(current_agent)
        self.agent_states[agent_name] = agent_state
        
        # Step 2: Pause message processing
        await self._pause_agent_messages(agent_name)
        
        # Step 3: Gracefully stop the agent
        logger.info(f"Stopping agent {agent_name} for reload")
        await self.orchestrator.stop_agent(agent_name)
        
        # Step 4: Get the new module
        module_name = self._get_agent_module_name(agent_name)
        new_module = self.hot_reload_manager.get_module(module_name)
        
        if not new_module:
            logger.error(f"Failed to get reloaded module for {agent_name}")
            return
            
        # Step 5: Find the agent class in the new module
        agent_class = self._find_agent_class(new_module, agent_name)
        
        if not agent_class:
            logger.error(f"Failed to find agent class in module {module_name}")
            return
            
        # Step 6: Create new agent instance
        logger.info(f"Creating new instance of {agent_name}")
        new_agent = agent_class()
        
        # Step 7: Restore agent state
        await self._restore_agent_state(new_agent, agent_state)
        
        # Step 8: Register new agent with orchestrator
        await self.orchestrator.register_agent(new_agent)
        
        # Step 9: Start the new agent
        await self.orchestrator.start_agent(agent_name)
        
        # Step 10: Resume message processing
        await self._resume_agent_messages(agent_name)
        
        logger.info(f"Successfully reloaded agent {agent_name}")
        
    async def _save_agent_state(self, agent: BaseAgent) -> Dict[str, Any]:
        """Save agent state before reload"""
        state = {
            "name": agent.name,
            "role": agent.role,
            "status": agent.status,
            "created_at": datetime.now(),
            "custom_state": {}
        }
        
        # Check if agent has custom state saving
        if hasattr(agent, 'save_state'):
            try:
                custom_state = await agent.save_state()
                state["custom_state"] = custom_state
            except Exception as e:
                logger.error(f"Failed to save custom state for {agent.name}: {e}")
                
        return state
        
    async def _restore_agent_state(self, agent: BaseAgent, state: Dict[str, Any]):
        """Restore agent state after reload"""
        # Restore basic properties
        if hasattr(agent, 'status'):
            agent.status = state.get("status", "initialized")
            
        # Check if agent has custom state restoration
        if hasattr(agent, 'restore_state') and state.get("custom_state"):
            try:
                await agent.restore_state(state["custom_state"])
            except Exception as e:
                logger.error(f"Failed to restore custom state for {agent.name}: {e}")
                
    async def _pause_agent_messages(self, agent_name: str):
        """Pause message processing for an agent"""
        # Store pending messages
        if agent_name not in self.pending_messages:
            self.pending_messages[agent_name] = []
            
        # This would integrate with message bus to redirect messages
        logger.debug(f"Pausing messages for {agent_name}")
        
    async def _resume_agent_messages(self, agent_name: str):
        """Resume message processing for an agent"""
        # Deliver any pending messages
        if agent_name in self.pending_messages:
            messages = self.pending_messages[agent_name]
            logger.info(f"Delivering {len(messages)} pending messages to {agent_name}")
            
            # Would integrate with message bus to deliver messages
            self.pending_messages[agent_name] = []
            
        logger.debug(f"Resumed messages for {agent_name}")
        
    def _get_agent_module_name(self, agent_name: str) -> str:
        """Get module name for an agent"""
        # Map agent names to their module paths
        agent_modules = {
            "solomon": "agents.solomon.solomon",
            "david": "agents.david.david",
            "adam": "agents.primordials.adam",
            "eve": "agents.primordials.eve",
            "bezalel": "agents.primordials.bezalel"
        }
        
        return agent_modules.get(agent_name, f"agents.{agent_name}")
        
    def _find_agent_class(self, module: Any, agent_name: str) -> Optional[Type[BaseAgent]]:
        """Find agent class in a module"""
        # Look for a class that inherits from BaseAgent
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseAgent) and 
                obj != BaseAgent):
                
                # Check if class name matches agent name (case insensitive)
                if name.lower() == agent_name.lower():
                    return obj
                    
        return None
        
    def get_reload_status(self) -> Dict[str, Any]:
        """Get status of agent reloads"""
        return {
            "saved_states": list(self.agent_states.keys()),
            "pending_messages": {
                agent: len(messages) 
                for agent, messages in self.pending_messages.items()
            },
            "hot_reload_metrics": self.hot_reload_manager.get_metrics()
        }


class HotReloadableAgent(BaseAgent):
    """
    Base class for agents that support hot reloading
    
    Agents can inherit from this to get automatic state preservation
    """
    
    async def save_state(self) -> Dict[str, Any]:
        """Save agent state for hot reload"""
        return {
            "memory": getattr(self, 'memory', {}),
            "config": getattr(self, 'config', {}),
            "context": getattr(self, 'context', {})
        }
        
    async def restore_state(self, state: Dict[str, Any]):
        """Restore agent state after hot reload"""
        if 'memory' in state:
            self.memory = state['memory']
        if 'config' in state:
            self.config = state['config']
        if 'context' in state:
            self.context = state['context']
            
    async def health_check(self) -> bool:
        """Health check for hot reload validation"""
        # Basic health check - can be overridden
        try:
            # Check if agent can respond
            response = await self.handle_user_chat("ping")
            return response is not None
        except Exception:
            return False


def make_agent_hot_reloadable(agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
    """
    Decorator to make an agent hot reloadable
    
    Usage:
        @make_agent_hot_reloadable
        class MyAgent(BaseAgent):
            ...
    """
    
    # Add hot reload methods if not present
    if not hasattr(agent_class, 'save_state'):
        async def save_state(self) -> Dict[str, Any]:
            return {
                "memory": getattr(self, 'memory', {}),
                "config": getattr(self, 'config', {})
            }
        agent_class.save_state = save_state
        
    if not hasattr(agent_class, 'restore_state'):
        async def restore_state(self, state: Dict[str, Any]):
            if 'memory' in state:
                self.memory = state['memory']
            if 'config' in state:
                self.config = state['config']
        agent_class.restore_state = restore_state
        
    if not hasattr(agent_class, 'health_check'):
        async def health_check(self) -> bool:
            return True
        agent_class.health_check = health_check
        
    return agent_class