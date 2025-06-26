"""
AgentLauncher - Dynamic agent launcher for database-driven agents
Launches and manages UniversalAgent instances from PostgreSQL configurations
"""

import asyncio
import logging
from typing import Dict, List, Optional
import asyncpg
from datetime import datetime

from core.universal_agent_v2 import UniversalAgentV2
from core.agent_orchestrator import AgentOrchestrator
from core.message_bus import message_bus


class AgentLauncher:
    """Launches and manages agents from database configurations"""
    
    def __init__(self):
        self.logger = logging.getLogger("AgentLauncher")
        self.active_agents: Dict[str, UniversalAgent] = {}
        self.db_pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize the agent launcher with database connection pool"""
        self.db_pool = await asyncpg.create_pool(
            host='localhost',
            port=5434,
            user='boarderframe',
            password='boarderframe123',
            database='boarderframeos',
            min_size=5,
            max_size=20
        )
        self.logger.info("Agent launcher initialized with database pool")
        
    async def launch_agent(self, agent_name: str) -> UniversalAgent:
        """Launch an agent instance from database config
        
        Args:
            agent_name: Name of the agent to launch
            
        Returns:
            UniversalAgent instance
        """
        try:
            # Check if agent already active
            if agent_name in self.active_agents:
                self.logger.warning(f"Agent {agent_name} already active")
                return self.active_agents[agent_name]
                
            # Create UniversalAgent instance
            agent = UniversalAgent(agent_name=agent_name)
            
            # Register with orchestrator
            await agent_orchestrator.register_agent(agent)
            
            # Register with message bus
            await message_bus.register_agent(agent_name)
            
            # Store in active agents
            self.active_agents[agent_name] = agent
            
            # Start the agent
            await agent.start()
            
            self.logger.info(f"Successfully launched agent: {agent_name}")
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to launch agent {agent_name}: {str(e)}")
            raise
            
    async def launch_all_active_agents(self) -> List[UniversalAgent]:
        """Launch all active agents from database
        
        Returns:
            List of launched UniversalAgent instances
        """
        launched_agents = []
        
        async with self.db_pool.acquire() as conn:
            # Query for all active agents
            rows = await conn.fetch("""
                SELECT name, role, department, development_status
                FROM agent_configs
                WHERE is_active = true
                ORDER BY priority_level DESC, name
            """)
            
            self.logger.info(f"Found {len(rows)} active agents to launch")
            
            for row in rows:
                agent_name = row['name']
                try:
                    agent = await self.launch_agent(agent_name)
                    launched_agents.append(agent)
                    
                    self.logger.info(
                        f"Launched {agent_name} ({row['role']}) "
                        f"from {row['department']} department "
                        f"[{row['development_status']}]"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Failed to launch {agent_name}: {str(e)}")
                    
        self.logger.info(f"Successfully launched {len(launched_agents)} agents")
        return launched_agents
        
    async def launch_department_agents(self, department: str) -> List[UniversalAgent]:
        """Launch all agents from a specific department
        
        Args:
            department: Name of the department
            
        Returns:
            List of launched agents from the department
        """
        launched_agents = []
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT name
                FROM agent_configs
                WHERE department = $1 AND is_active = true
                ORDER BY priority_level DESC, name
            """, department)
            
            for row in rows:
                try:
                    agent = await self.launch_agent(row['name'])
                    launched_agents.append(agent)
                except Exception as e:
                    self.logger.error(f"Failed to launch {row['name']}: {str(e)}")
                    
        return launched_agents
        
    async def stop_agent(self, agent_name: str):
        """Stop and unregister an agent
        
        Args:
            agent_name: Name of the agent to stop
        """
        if agent_name not in self.active_agents:
            self.logger.warning(f"Agent {agent_name} not active")
            return
            
        agent = self.active_agents[agent_name]
        
        # Stop the agent
        await agent.stop()
        
        # Unregister from orchestrator
        await agent_orchestrator.unregister_agent(agent_name)
        
        # Unregister from message bus
        await message_bus.unregister_agent(agent_name)
        
        # Remove from active agents
        del self.active_agents[agent_name]
        
        self.logger.info(f"Stopped agent: {agent_name}")
        
    async def stop_all_agents(self):
        """Stop all active agents"""
        agent_names = list(self.active_agents.keys())
        
        for agent_name in agent_names:
            await self.stop_agent(agent_name)
            
        self.logger.info("All agents stopped")
        
    async def reload_agent(self, agent_name: str) -> UniversalAgent:
        """Reload an agent with updated configuration from database
        
        Args:
            agent_name: Name of the agent to reload
            
        Returns:
            Reloaded UniversalAgent instance
        """
        # Stop existing agent if running
        if agent_name in self.active_agents:
            await self.stop_agent(agent_name)
            
        # Launch with fresh configuration
        return await self.launch_agent(agent_name)
        
    async def update_agent_model(self, agent_name: str, new_model: str):
        """Update an agent's LLM model in database and reload
        
        Args:
            agent_name: Name of the agent
            new_model: New LLM model to use
        """
        async with self.db_pool.acquire() as conn:
            # Update model in database
            await conn.execute("""
                UPDATE agent_configs
                SET llm_model = $1, updated_at = CURRENT_TIMESTAMP
                WHERE name = $2
            """, new_model, agent_name)
            
        # Reload agent if active
        if agent_name in self.active_agents:
            await self.reload_agent(agent_name)
            self.logger.info(f"Updated {agent_name} to use {new_model}")
            
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all managed agents"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "total_active": len(self.active_agents),
            "agents": {}
        }
        
        for agent_name, agent in self.active_agents.items():
            status["agents"][agent_name] = await agent.report_status()
            
        return status
        
    async def create_new_agent(
        self,
        name: str,
        role: str,
        department: str,
        personality_traits: List[str],
        goals: List[str],
        tools: List[str],
        llm_model: str = "claude-3-sonnet",
        system_prompt: str = ""
    ) -> UniversalAgent:
        """Create a new agent in database and launch it
        
        Args:
            name: Agent name
            role: Agent role
            department: Department assignment
            personality_traits: List of personality traits
            goals: List of agent goals
            tools: List of available tools
            llm_model: LLM model to use
            system_prompt: System prompt for the agent
            
        Returns:
            Newly created and launched agent
        """
        async with self.db_pool.acquire() as conn:
            # Generate system prompt if not provided
            if not system_prompt:
                system_prompt = self._generate_system_prompt(name, role, personality_traits)
                
            # Insert new agent configuration
            await conn.execute("""
                INSERT INTO agent_configs (
                    name, role, department, personality, goals, tools,
                    llm_model, system_prompt, is_active, development_status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, 'operational')
            """, 
                name, role, department,
                {"traits": personality_traits},
                goals, tools, llm_model, system_prompt
            )
            
        # Launch the new agent
        agent = await self.launch_agent(name)
        self.logger.info(f"Created and launched new agent: {name}")
        
        return agent
        
    def _generate_system_prompt(self, name: str, role: str, traits: List[str]) -> str:
        """Generate a system prompt based on agent attributes"""
        traits_str = ", ".join(traits)
        
        return f"""You are {name}, {role} at BoarderframeOS. 
Your personality traits include being {traits_str}. 
You work to achieve your assigned goals while embodying these traits in all interactions.
Maintain consistency with your role and personality while being helpful and effective."""
        
    async def cleanup(self):
        """Clean up resources"""
        # Stop all agents
        await self.stop_all_agents()
        
        # Close database pool
        if self.db_pool:
            await self.db_pool.close()
            
        self.logger.info("Agent launcher cleaned up")


# Global agent launcher instance
agent_launcher = AgentLauncher()