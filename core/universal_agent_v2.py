"""
UniversalAgent v2 - Refactored with mixin architecture
Prevents god-class by using composition of focused mixins
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import asyncpg

from core.base_agent import AgentConfig
from core.agent_mixins import (
    BaseMixin, ThinkingMixin, ToolRunnerMixin, 
    MemoryMixin, LLMMixin, CommunicationMixin
)
from core.message_bus import message_bus


class UniversalAgentV2(
    BaseMixin,
    ThinkingMixin,
    ToolRunnerMixin,
    MemoryMixin,
    LLMMixin,
    CommunicationMixin
):
    """Universal agent composed of specialized mixins"""
    
    def __init__(self, agent_id: str = None, agent_name: str = None):
        """Initialize agent with all mixin capabilities
        
        Args:
            agent_id: UUID of the agent in database
            agent_name: Name of the agent (alternative to ID)
        """
        # Initialize all mixins
        BaseMixin.__init__(self)
        ThinkingMixin.__init__(self)
        ToolRunnerMixin.__init__(self)
        MemoryMixin.__init__(self)
        LLMMixin.__init__(self)
        CommunicationMixin.__init__(self)
        
        # Set up logger
        self.logger = logging.getLogger(f"UniversalAgentV2.{agent_name or agent_id}")
        
        # Store parameters for async initialization
        self._agent_id = agent_id
        self._agent_name = agent_name
        self.name = agent_name or str(agent_id) if agent_id else "unknown"
        self.config = None  # Will be loaded in start()
        # Default values - will be updated from config in start()
        self.personality = {}
        self.llm_model = "claude-3-haiku"
        self.temperature = 0.7
        self.max_tokens = 2048
        self.system_prompt = ""
        self.context_prompt = ""
        self.priority_level = 5
        self.development_status = "planned"
        
        # Message handlers can be setup in init
        self._setup_message_handlers()
        
        # Tools will be registered after config is loaded
        
        self.logger.info(f"UniversalAgentV2 instance created: {self.name}")
        
    async def load_config_from_db(self, agent_id: str = None, agent_name: str = None) -> AgentConfig:
        """Load agent configuration from PostgreSQL database"""
        if not agent_id and not agent_name:
            raise ValueError("Either agent_id or agent_name must be provided")
            
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            user='boarderframe',
            password='boarderframe_secure_2025',
            database='boarderframeos'
        )
        
        try:
            # Query for agent configuration directly from table
            if agent_id:
                query = """
                    SELECT * FROM agent_configs
                    WHERE agent_id = $1 AND is_active = true
                """
                row = await conn.fetchrow(query, agent_id)
            else:
                query = """
                    SELECT * FROM agent_configs
                    WHERE name = $1 AND is_active = true
                """
                row = await conn.fetchrow(query, agent_name)
                
            if not row:
                raise ValueError(f"Agent not found: {agent_id or agent_name}")
                
            # Row contains all the fields directly
            config_data = dict(row)
            
            # Create extended AgentConfig
            from dataclasses import dataclass, field
            
            @dataclass
            class ExtendedAgentConfig(AgentConfig):
                """Extended configuration with additional fields"""
                personality: Dict[str, Any] = field(default_factory=dict)
                llm_model: str = "claude-3-sonnet"
                temperature: float = 0.7
                max_tokens: int = 4096
                system_prompt: str = ""
                context_prompt: Optional[str] = None
                priority_level: int = 5
                compute_allocation: float = 5.0
                memory_limit_gb: float = 8.0
                max_concurrent_tasks: int = 5
                is_active: bool = True
                development_status: str = "planned"
            
            config = ExtendedAgentConfig(
                name=config_data['name'],
                role=config_data['role'],
                goals=config_data['goals'],
                tools=config_data['tools'],
                personality=config_data.get('personality', {}),
                llm_model=config_data.get('llm_model', 'claude-3-sonnet'),
                temperature=config_data.get('temperature', 0.7),
                max_tokens=config_data.get('max_tokens', 4096),
                system_prompt=config_data.get('system_prompt', ''),
                context_prompt=config_data.get('context_prompt'),
                priority_level=config_data.get('priority_level', 5),
                compute_allocation=config_data.get('compute_allocation', 5.0),
                memory_limit_gb=config_data.get('memory_limit_gb', 8.0),
                max_concurrent_tasks=config_data.get('max_concurrent_tasks', 5),
                is_active=config_data.get('is_active', True),
                department=config_data.get('department', 'Unknown')
            )
            
            self.logger.info(f"Loaded configuration for {config.name}")
            return config
            
        finally:
            await conn.close()
            
    async def start(self) -> None:
        """Start the agent with all subsystems"""
        # Load configuration from database first
        if self.config is None:
            self.config = await self.load_config_from_db(self._agent_id, self._agent_name)
            
            # Update properties from loaded config
            self.name = self.config.name
            self.personality = self.config.personality
            self.llm_model = self.config.llm_model
            self.temperature = self.config.temperature
            self.max_tokens = self.config.max_tokens
            self.system_prompt = self.config.system_prompt
            self.context_prompt = self.config.context_prompt
            self.priority_level = self.config.priority_level
            self.development_status = self.config.development_status
            
            self.logger.info(f"Loaded config for {self.name}: {self.config.role}")
            
            # Register tools after config is loaded
            self._register_default_tools()
        
        # Setup communication
        await self.setup_communication(message_bus)
        
        # Call base start
        await super().start()
        
    async def stop(self) -> None:
        """Stop the agent and cleanup"""
        # Cleanup communication
        await self.cleanup_communication()
        
        # Call base stop
        await super().stop()
        
    async def _process_cycle(self) -> None:
        """Main processing cycle combining all capabilities"""
        # Process incoming messages
        await self.process_messages()
        
        # Check for tasks in memory
        working_memory = self.get_working_memory()
        
        for memory in working_memory:
            if memory.get("type") == "task" and not memory.get("processed"):
                # Think about the task
                thoughts = await self.think(memory.get("content", {}))
                
                # Decide on action
                decision = await self._make_decision(thoughts)
                
                # Execute action
                if decision.get("action") == "execute_tool":
                    tool_name = decision.get("tool")
                    params = decision.get("parameters", {})
                    result = await self.execute_tool(tool_name, params)
                    
                    # Store result in memory
                    await self.remember("episodic", {
                        "task": memory,
                        "thoughts": thoughts,
                        "decision": decision,
                        "result": result
                    })
                    
                # Mark as processed
                memory["processed"] = True
                
        # Update task counter
        self.task_count += 1
        
    async def handle_user_chat(self, message: str, user_id: str = "user") -> str:
        """Handle chat messages using LLM capabilities"""
        # Store in working memory
        await self.remember("working", {
            "type": "user_message",
            "message": message,
            "user_id": user_id
        })
        
        # Think about the message
        context = {
            "user_message": message,
            "user_id": user_id,
            "recent_memories": await self.recall("user", limit=5)
        }
        
        thoughts = await self.think(context)
        
        # Generate response using LLM
        prompt = self._build_chat_prompt(message, thoughts)
        
        response = await self.generate_llm_response(
            prompt=prompt,
            model=self.llm_model,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Store interaction in memory
        await self.remember("episodic", {
            "type": "chat_interaction",
            "user_message": message,
            "agent_response": response.content,
            "timestamp": datetime.now().isoformat()
        })
        
        return response.content
        
    async def report_status(self) -> Dict[str, Any]:
        """Report comprehensive agent status"""
        # Get base status
        status = await BaseMixin.report_status(self)
        
        # Add memory stats
        status["memory"] = self.get_memory_stats()
        
        # Add communication stats
        status["communication"] = self.get_communication_stats()
        
        # Add LLM usage
        status["llm_usage"] = self.get_llm_usage_report()
        
        # Add tool usage
        status["tool_usage"] = self.get_tool_usage_report()
        
        # Add specific fields
        status.update({
            "llm_model": self.llm_model,
            "personality_traits": self.personality.get("traits", []),
            "development_status": self.development_status,
            "department": self.config.department,
            "active_tools": len(self.available_tools),
            "priority_level": self.priority_level
        })
        
        return status
        
    def _register_default_tools(self) -> None:
        """Register default tools based on agent configuration"""
        from core.agent_mixins.tool_runner_mixin import ToolDefinition
        
        # Skip if no config loaded yet
        if not self.config or not hasattr(self.config, 'tools'):
            return
            
        # Register tools based on config
        for tool_name in self.config.tools:
            if tool_name == "analysis":
                self.register_tool(ToolDefinition(
                    name="analysis",
                    description="Analyze data and provide insights",
                    function=self._tool_analysis,
                    parameters={"data": "object"},
                    requires_approval=False,
                    cost_estimate=0.001
                ))
            elif tool_name == "coordination":
                self.register_tool(ToolDefinition(
                    name="coordination",
                    description="Coordinate with other agents",
                    function=self._tool_coordination,
                    parameters={"agents": "list", "task": "object"},
                    requires_approval=False,
                    cost_estimate=0.0
                ))
            # Add more tool registrations as needed
            
    def _setup_message_handlers(self) -> None:
        """Setup default message handlers"""
        from core.message_bus import MessageType
        
        # Register handlers for different message types
        self.register_message_handler(
            MessageType.TASK_REQUEST,
            self._handle_task_request
        )
        
        self.register_message_handler(
            MessageType.STATUS_UPDATE,
            self._handle_status_update
        )
        
        self.register_message_handler(
            MessageType.KNOWLEDGE_SHARE,
            self._handle_knowledge_share
        )
        
    async def _make_decision(self, thoughts: Dict[str, Any]) -> Dict[str, Any]:
        """Make decision based on thoughts"""
        # Simple decision logic - can be enhanced
        recommendations = thoughts.get("recommendations", [])
        
        if recommendations:
            primary = recommendations[0]
            return {
                "action": primary.get("action", "none"),
                "reasoning": primary.get("reasoning", ""),
                "confidence": primary.get("confidence", 0.5)
            }
            
        return {"action": "none", "reasoning": "No clear action", "confidence": 0.0}
        
    def _build_chat_prompt(self, message: str, thoughts: Dict[str, Any]) -> str:
        """Build prompt for chat response"""
        prompt = f"""Based on the following context and analysis, provide a helpful response.

User Message: {message}

Analysis:
- Complexity: {thoughts.get('context_analysis', {}).get('complexity', 'unknown')}
- Urgency: {thoughts.get('context_analysis', {}).get('urgency', 'normal')}
- Personality Traits: {', '.join(thoughts.get('personality_traits', []))}

Respond in a way that:
1. Addresses the user's needs
2. Reflects the personality traits
3. Provides value

Response:"""
        
        return prompt
        
    async def _tool_analysis(self, data: Any) -> Dict[str, Any]:
        """Example analysis tool"""
        # Perform analysis
        return {
            "insights": ["Pattern detected", "Trend identified"],
            "confidence": 0.85
        }
        
    async def _tool_coordination(self, agents: List[str], task: Dict[str, Any]) -> Dict[str, Any]:
        """Example coordination tool"""
        # Coordinate with other agents
        results = []
        
        for agent in agents:
            response = await self.request_task(agent, task)
            results.append({
                "agent": agent,
                "response": response
            })
            
        return {"coordination_results": results}
        
    async def _handle_task_request(self, message: Any) -> None:
        """Handle incoming task requests"""
        # Store in working memory for processing
        await self.remember("working", {
            "type": "task",
            "content": message.content,
            "from_agent": message.from_agent,
            "correlation_id": message.correlation_id
        })
        
    async def _handle_status_update(self, message: Any) -> None:
        """Handle status updates from other agents"""
        # Store in semantic memory
        await self.remember("semantic", {
            f"{message.from_agent}_status": message.content
        })
        
    async def _handle_knowledge_share(self, message: Any) -> None:
        """Handle knowledge shared by other agents"""
        # Store in semantic memory
        knowledge = message.content.get("knowledge", {})
        topic = message.content.get("topic", "general")
        
        await self.remember("semantic", knowledge, {
            "source": message.from_agent,
            "topic": topic
        })