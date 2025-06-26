"""
UniversalAgent - Database-driven agent implementation for BoarderframeOS
All agents share this base implementation with configurations loaded from PostgreSQL
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import asyncpg

from core.base_agent import BaseAgent, AgentConfig
from core.message_bus import MessageBus, AgentMessage, MessageType, MessagePriority


@dataclass
class DynamicAgentConfig(AgentConfig):
    """Extended configuration for database-driven agents"""
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


class UniversalAgent(BaseAgent):
    """Universal agent that loads its configuration and personality from database"""
    
    def __init__(self, agent_id: str = None, agent_name: str = None):
        """Initialize agent from database configuration
        
        Args:
            agent_id: UUID of the agent in database
            agent_name: Name of the agent (alternative to ID)
        """
        self.logger = logging.getLogger(f"UniversalAgent.{agent_name or agent_id}")
        
        # Load configuration from database
        config = asyncio.run(self.load_config_from_db(agent_id, agent_name))
        
        # Initialize base agent with loaded config
        super().__init__(config)
        
        # Store extended configuration
        self.personality = config.personality
        self.llm_model = config.llm_model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.system_prompt = config.system_prompt
        self.context_prompt = config.context_prompt
        self.priority_level = config.priority_level
        self.development_status = config.development_status
        
        self.logger.info(f"Initialized {self.name} with {self.llm_model} model")
        
    async def load_config_from_db(self, agent_id: str = None, agent_name: str = None) -> DynamicAgentConfig:
        """Load agent configuration from PostgreSQL database"""
        if not agent_id and not agent_name:
            raise ValueError("Either agent_id or agent_name must be provided")
            
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            user='boarderframe',
            password='boarderframe123',
            database='boarderframeos'
        )
        
        try:
            # Query for agent configuration
            if agent_id:
                query = """
                    SELECT agent_id, config 
                    FROM get_agent_config(
                        (SELECT name FROM agent_configs WHERE agent_id = $1)
                    )
                """
                row = await conn.fetchrow(query, agent_id)
            else:
                query = "SELECT agent_id, config FROM get_agent_config($1)"
                row = await conn.fetchrow(query, agent_name)
                
            if not row:
                raise ValueError(f"Agent not found: {agent_id or agent_name}")
                
            config_data = json.loads(row['config'])
            
            # Create DynamicAgentConfig from database data
            config = DynamicAgentConfig(
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
            
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Universal thinking process based on personality and goals"""
        thoughts = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "personality_traits": self.personality.get("traits", []),
            "current_goals": self.config.goals[:3],  # Top 3 goals
            "context_analysis": {}
        }
        
        # Analyze context based on personality
        if "analytical" in self.personality.get("traits", []):
            thoughts["context_analysis"]["data_points"] = len(context)
            thoughts["context_analysis"]["complexity"] = "high" if len(context) > 10 else "moderate"
            
        if "strategic" in self.personality.get("traits", []):
            thoughts["context_analysis"]["strategic_implications"] = self._analyze_strategic_implications(context)
            
        if "creative" in self.personality.get("traits", []):
            thoughts["context_analysis"]["innovation_opportunities"] = self._identify_innovation_opportunities(context)
            
        # Add role-specific thinking
        thoughts["role_perspective"] = self._get_role_perspective(context)
        
        return thoughts
        
    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Universal action execution based on available tools and personality"""
        action_result = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "decision": decision,
            "actions_taken": [],
            "personality_influence": {}
        }
        
        # Execute actions based on available tools
        for tool in self.config.tools:
            if tool in decision.get("recommended_tools", []):
                result = await self._execute_tool(tool, decision)
                action_result["actions_taken"].append({
                    "tool": tool,
                    "result": result
                })
                
        # Apply personality modifiers
        if "decisive" in self.personality.get("traits", []):
            action_result["personality_influence"]["execution_speed"] = "fast"
        elif "methodical" in self.personality.get("traits", []):
            action_result["personality_influence"]["execution_speed"] = "measured"
            
        return action_result
        
    async def handle_user_chat(self, message: str, user_id: str = "user") -> str:
        """Handle chat messages with personality-driven responses"""
        # Build context with system prompt and personality
        context = {
            "role": self.config.role,
            "personality": self.personality,
            "department": self.config.department,
            "system_prompt": self.system_prompt,
            "user_message": message
        }
        
        # Get LLM response with agent-specific configuration
        response = await self._generate_llm_response(context)
        
        # Apply communication style
        communication_style = self.personality.get("communication_style", "professional")
        if communication_style == "formal":
            response = self._apply_formal_style(response)
        elif communication_style == "friendly":
            response = self._apply_friendly_style(response)
            
        return response
        
    def _analyze_strategic_implications(self, context: Dict[str, Any]) -> List[str]:
        """Analyze strategic implications based on context"""
        implications = []
        
        if "budget" in context:
            implications.append("Financial impact assessment required")
        if "timeline" in context:
            implications.append("Schedule optimization needed")
        if "resources" in context:
            implications.append("Resource allocation review recommended")
            
        return implications
        
    def _identify_innovation_opportunities(self, context: Dict[str, Any]) -> List[str]:
        """Identify innovation opportunities in the context"""
        opportunities = []
        
        if "problem" in context:
            opportunities.append("Novel solution exploration possible")
        if "inefficiency" in context:
            opportunities.append("Process optimization candidate")
        if "manual_process" in context:
            opportunities.append("Automation opportunity identified")
            
        return opportunities
        
    def _get_role_perspective(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get role-specific perspective on the context"""
        perspective = {
            "role": self.config.role,
            "primary_concern": "",
            "recommended_approach": ""
        }
        
        # CEO perspective
        if "CEO" in self.config.role:
            perspective["primary_concern"] = "Strategic alignment and ROI"
            perspective["recommended_approach"] = "High-level decision with delegation"
            
        # Chief of Staff perspective
        elif "Chief of Staff" in self.config.role:
            perspective["primary_concern"] = "Operational efficiency and coordination"
            perspective["recommended_approach"] = "Cross-functional collaboration"
            
        # Engineering perspective
        elif "Engineer" in self.config.role or "Programmer" in self.config.role:
            perspective["primary_concern"] = "Technical feasibility and quality"
            perspective["recommended_approach"] = "Systematic implementation"
            
        # Security perspective
        elif "Security" in self.config.role:
            perspective["primary_concern"] = "Risk mitigation and compliance"
            perspective["recommended_approach"] = "Threat assessment first"
            
        return perspective
        
    async def _execute_tool(self, tool: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool based on agent capabilities"""
        result = {
            "tool": tool,
            "status": "completed",
            "output": {}
        }
        
        # Tool implementations would go here
        # This is where you'd integrate with actual tool capabilities
        
        if tool == "code_generation":
            result["output"] = {"files_generated": 1, "language": "python"}
        elif tool == "analysis":
            result["output"] = {"insights": 3, "recommendations": 2}
        elif tool == "coordination":
            result["output"] = {"messages_sent": 2, "departments_contacted": 1}
            
        return result
        
    async def _generate_llm_response(self, context: Dict[str, Any]) -> str:
        """Generate response using configured LLM model"""
        # This would integrate with your LLM client
        # For now, return a personality-appropriate placeholder
        
        if "wise" in self.personality.get("traits", []):
            return "After careful consideration of all factors involved..."
        elif "decisive" in self.personality.get("traits", []):
            return "The clear path forward is..."
        elif "creative" in self.personality.get("traits", []):
            return "I see an innovative approach we could take..."
        else:
            return "Based on my analysis..."
            
    def _apply_formal_style(self, response: str) -> str:
        """Apply formal communication style"""
        # In production, this would use more sophisticated style transfer
        formal_prefixes = [
            "I would like to inform you that ",
            "Please be advised that ",
            "It is my professional opinion that "
        ]
        
        import random
        return random.choice(formal_prefixes) + response
        
    def _apply_friendly_style(self, response: str) -> str:
        """Apply friendly communication style"""
        # In production, this would use more sophisticated style transfer
        friendly_additions = [
            " 😊",
            " - hope this helps!",
            " Let me know if you need anything else!"
        ]
        
        import random
        return response + random.choice(friendly_additions)
        
    async def update_config_from_db(self):
        """Refresh configuration from database (hot reload)"""
        new_config = await self.load_config_from_db(agent_name=self.name)
        
        # Update configuration
        self.config = new_config
        self.personality = new_config.personality
        self.llm_model = new_config.llm_model
        self.temperature = new_config.temperature
        self.system_prompt = new_config.system_prompt
        
        self.logger.info(f"Configuration updated for {self.name}")
        
    async def report_status(self) -> Dict[str, Any]:
        """Report current agent status"""
        status = await super().report_status()
        
        # Add universal agent specific status
        status.update({
            "llm_model": self.llm_model,
            "personality_traits": self.personality.get("traits", []),
            "development_status": self.development_status,
            "department": self.config.department,
            "active_tools": len(self.config.tools),
            "priority_level": self.priority_level
        })
        
        return status