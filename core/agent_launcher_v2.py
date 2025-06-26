"""
AgentLauncher V2 - Dynamic agent launcher for UniversalAgentV2
Simplified version that works with the new mixin-based architecture
"""

import asyncio
import logging
from typing import Dict, List, Optional
import asyncpg

from core.universal_agent_v2 import UniversalAgentV2
from core.message_bus import message_bus


class AgentLauncher:
    """Launches and manages agents from database configurations"""
    
    def __init__(self):
        self.logger = logging.getLogger("AgentLauncherV2")
        self.active_agents: Dict[str, UniversalAgentV2] = {}
        self.db_pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize the agent launcher with database connection pool"""
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5434,
            user='boarderframe',
            password='boarderframe_secure_2025',
            database='boarderframeos',
            min_size=2,
            max_size=10
        )
        self.logger.info("Agent launcher V2 initialized")
        
    async def create_agent(self, agent_name: str) -> Optional[UniversalAgentV2]:
        """Create and start an agent from database config
        
        Args:
            agent_name: Name of the agent to create
            
        Returns:
            UniversalAgentV2 instance or None
        """
        try:
            # Check if agent already active
            if agent_name in self.active_agents:
                self.logger.info(f"Agent {agent_name} already active")
                return self.active_agents[agent_name]
                
            # Verify agent exists in database
            async with self.db_pool.acquire() as conn:
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM agent_configs WHERE name = $1 AND is_active = true)",
                    agent_name
                )
                
                if not exists:
                    self.logger.error(f"Agent {agent_name} not found or not active")
                    return None
            
            # Create agent instance
            agent = UniversalAgentV2(agent_name)
            
            # Start the agent
            await agent.start()
            
            # Register with message bus
            await message_bus.register_agent(agent_name)
            
            # Store in active agents
            self.active_agents[agent_name] = agent
            
            self.logger.info(f"Successfully created agent: {agent_name}")
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent {agent_name}: {e}")
            return None
            
    def get_agent(self, agent_name: str) -> Optional[UniversalAgentV2]:
        """Get an active agent by name"""
        return self.active_agents.get(agent_name)
        
    def get_all_agents(self) -> Dict[str, UniversalAgentV2]:
        """Get all active agents"""
        return self.active_agents.copy()
        
    async def stop_agent(self, agent_name: str):
        """Stop and remove an agent"""
        if agent_name in self.active_agents:
            agent = self.active_agents[agent_name]
            await agent.stop()
            
            # Unregister from message bus
            await message_bus.unregister_agent(agent_name)
            
            del self.active_agents[agent_name]
            self.logger.info(f"Stopped agent: {agent_name}")
            
    async def cleanup(self):
        """Stop all agents and cleanup resources"""
        # Stop all agents
        agent_names = list(self.active_agents.keys())
        for agent_name in agent_names:
            await self.stop_agent(agent_name)
            
        # Close database pool
        if self.db_pool:
            await self.db_pool.close()
            
        self.logger.info("Agent launcher cleanup complete")