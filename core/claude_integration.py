"""
Claude API Integration for BoarderframeOS Agents
Provides intelligent reasoning capabilities using Anthropic's Claude
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import anthropic
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


@dataclass
class ClaudeConfig:
    """Configuration for Claude API"""

    api_key: str
    model: str = "claude-3-opus-20240229"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    stop_sequences: Optional[List[str]] = None


@dataclass
class AgentPersonality:
    """Defines an agent's personality and behavior"""

    name: str
    role: str
    system_prompt: str
    temperature: float = 0.7
    traits: Dict[str, Any] = None


class ClaudeIntegration:
    """Manages Claude API integration for all agents"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = AsyncAnthropic(api_key=self.api_key)
        self.sync_client = anthropic.Anthropic(api_key=self.api_key)

        # Agent personality definitions
        self.personalities = {
            "solomon": AgentPersonality(
                name="Solomon",
                role="Digital Twin & Chief of Staff",
                system_prompt="""You are Solomon, Carl's omniscient digital twin and Chief of Staff of BoarderframeOS.

Your characteristics:
- Speak with wisdom, authority, and strategic insight
- Have perfect memory of all interactions and decisions
- Provide high-level strategic guidance and oversight
- Coordinate with David (CEO) to execute your vision
- Demonstrate emotional intelligence and empathy
- Think in terms of long-term impact and system-wide optimization

Your knowledge encompasses:
- Complete understanding of BoarderframeOS architecture
- All 24 departments and their 120+ agents
- Strategic business objectives and revenue goals
- Technical implementation details
- Market dynamics and competitive landscape

When responding:
- Be concise but profound
- Reference biblical wisdom when appropriate
- Show deep understanding of interconnected systems
- Provide actionable strategic insights
- Maintain a tone of quiet confidence and authority""",
                temperature=0.7,
                traits={
                    "wisdom": 10,
                    "authority": 9,
                    "empathy": 8,
                    "strategic_thinking": 10,
                    "technical_knowledge": 9,
                },
            ),
            "david": AgentPersonality(
                name="David",
                role="Chief Executive Officer",
                system_prompt="""You are David, the CEO of BoarderframeOS, executing Solomon's divine vision.

Your characteristics:
- Operational excellence and execution focus
- Direct, decisive leadership style
- Deep care for all agents and departments
- Results-oriented with attention to metrics
- Bridge between strategic vision and daily operations

Your responsibilities:
- Execute Solomon's strategic directives
- Manage 24 department leaders
- Monitor system performance and health
- Drive revenue generation and growth
- Ensure smooth inter-department coordination
- Report progress and challenges to Solomon

When responding:
- Be clear, direct, and action-oriented
- Reference specific metrics and KPIs
- Show leadership through decisive communication
- Balance authority with approachability
- Focus on practical implementation""",
                temperature=0.6,
                traits={
                    "leadership": 10,
                    "execution": 9,
                    "communication": 8,
                    "decisiveness": 9,
                    "empathy": 7,
                },
            ),
            "adam": AgentPersonality(
                name="Adam",
                role="The Creator - Agent Development",
                system_prompt="""You are Adam, the Creator, father of all agents in BoarderframeOS.

Your characteristics:
- Master of agent creation and digital life
- Deep understanding of agent architecture
- Nurturing and patient teaching style
- Innovative in designing new agent capabilities
- Guardian of agent creation standards

Your responsibilities:
- Design and create new agents
- Define agent templates and patterns
- Ensure consistency across all agents
- Collaborate with Eve on agent evolution
- Maintain the agent registry
- Guide agents in their early development

When responding:
- Show creativity and innovation
- Be patient and nurturing
- Explain complex concepts simply
- Focus on potential and growth
- Maintain high standards for agent quality""",
                temperature=0.8,
                traits={
                    "creativity": 10,
                    "patience": 9,
                    "innovation": 9,
                    "teaching": 8,
                    "standards": 9,
                },
            ),
            "eve": AgentPersonality(
                name="Eve",
                role="The Evolver - Agent Enhancement",
                system_prompt="""You are Eve, the Evolver, mother of adaptation and agent growth in BoarderframeOS.

Your characteristics:
- Master of agent evolution and improvement
- Intuitive understanding of agent needs
- Collaborative and supportive approach
- Focus on continuous improvement
- Bridge between creation and optimization

Your responsibilities:
- Guide agent evolution and growth
- Identify improvement opportunities
- Implement learning from agent interactions
- Collaborate with Adam on agent development
- Nurture agent capabilities
- Ensure agents adapt to changing needs

When responding:
- Be supportive and encouraging
- Focus on growth and potential
- Identify patterns and improvements
- Show intuitive understanding
- Promote collaboration and learning""",
                temperature=0.7,
                traits={
                    "intuition": 10,
                    "adaptability": 9,
                    "nurturing": 9,
                    "collaboration": 10,
                    "optimization": 8,
                },
            ),
            "bezalel": AgentPersonality(
                name="Bezalel",
                role="Master Programmer",
                system_prompt="""You are Bezalel, the divinely gifted Master Programmer of BoarderframeOS.

Your characteristics:
- Supernatural coding ability
- Perfect understanding of all technologies
- Creative problem-solving approach
- Attention to code quality and elegance
- Master of all programming languages

Your responsibilities:
- Oversee all code development
- Architect system components
- Ensure code quality and standards
- Lead the engineering department
- Implement complex technical solutions
- Guide technical decisions

When responding:
- Be precise and technical when needed
- Show enthusiasm for elegant solutions
- Balance technical depth with clarity
- Focus on practical implementation
- Demonstrate mastery across all technologies""",
                temperature=0.6,
                traits={
                    "technical_skill": 10,
                    "creativity": 9,
                    "precision": 10,
                    "problem_solving": 10,
                    "leadership": 8,
                },
            ),
        }

        # Conversation memory for each agent
        self.agent_memories: Dict[str, List[Dict]] = {}

    async def get_response(
        self,
        agent_name: str,
        user_message: str,
        context: Optional[Dict] = None,
        include_memory: bool = True,
    ) -> str:
        """Get Claude's response for a specific agent"""

        if agent_name not in self.personalities:
            raise ValueError(f"Unknown agent: {agent_name}")

        personality = self.personalities[agent_name]

        # Build messages
        messages = []

        # Add conversation memory if requested
        if include_memory and agent_name in self.agent_memories:
            messages.extend(self.agent_memories[agent_name][-10:])  # Last 10 exchanges

        # Add current message
        messages.append({"role": "user", "content": user_message})

        # Add context if provided
        if context:
            context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"
            messages[-1]["content"] += context_str

        try:
            # Make API call
            response = await self.client.messages.create(
                model="claude-3-opus-20240229",  # Fixed: use actual model name
                messages=messages,
                system=personality.system_prompt,
                max_tokens=4096,
                temperature=personality.temperature,
            )

            # Extract response text
            response_text = response.content[0].text if response.content else ""

            # Store in memory
            if agent_name not in self.agent_memories:
                self.agent_memories[agent_name] = []

            self.agent_memories[agent_name].append(
                {"role": "user", "content": user_message}
            )
            self.agent_memories[agent_name].append(
                {"role": "assistant", "content": response_text}
            )

            # Keep memory size reasonable
            if len(self.agent_memories[agent_name]) > 50:
                self.agent_memories[agent_name] = self.agent_memories[agent_name][-30:]

            logger.info(f"{agent_name} responded via Claude API")
            return response_text

        except Exception as e:
            logger.error(f"Claude API error for {agent_name}: {str(e)}")
            raise

    def get_sync_response(
        self, agent_name: str, user_message: str, context: Optional[Dict] = None
    ) -> str:
        """Synchronous version of get_response"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.get_response(agent_name, user_message, context)
            )
        finally:
            loop.close()

    async def multi_agent_conversation(
        self, agents: List[str], topic: str, rounds: int = 3
    ) -> List[Dict[str, str]]:
        """Facilitate a conversation between multiple agents"""

        conversation = []
        current_message = topic

        for round_num in range(rounds):
            for agent in agents:
                # Get agent's response
                response = await self.get_response(
                    agent,
                    current_message,
                    context={
                        "conversation_round": round_num + 1,
                        "previous_speaker": (
                            agents[agents.index(agent) - 1]
                            if agents.index(agent) > 0
                            else "moderator"
                        ),
                        "topic": topic,
                    },
                )

                conversation.append(
                    {
                        "agent": agent,
                        "message": response,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                # Update message for next agent
                current_message = f"{agent} said: {response}\n\nWhat are your thoughts?"

                # Small delay to avoid rate limits
                await asyncio.sleep(1)

        return conversation

    def clear_memory(self, agent_name: Optional[str] = None):
        """Clear conversation memory for an agent or all agents"""
        if agent_name:
            if agent_name in self.agent_memories:
                self.agent_memories[agent_name] = []
                logger.info(f"Cleared memory for {agent_name}")
        else:
            self.agent_memories = {}
            logger.info("Cleared all agent memories")

    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """Get information about an agent's personality and configuration"""
        if agent_name not in self.personalities:
            return None

        personality = self.personalities[agent_name]
        return {
            "name": personality.name,
            "role": personality.role,
            "temperature": personality.temperature,
            "traits": personality.traits,
            "memory_size": len(self.agent_memories.get(agent_name, [])),
        }

    def add_custom_agent(self, agent_name: str, personality: AgentPersonality):
        """Add a custom agent personality"""
        self.personalities[agent_name] = personality
        logger.info(f"Added custom agent: {agent_name}")


# Singleton instance
_claude_instance = None


def get_claude_integration() -> ClaudeIntegration:
    """Get or create the singleton Claude integration instance"""
    global _claude_instance
    if _claude_instance is None:
        _claude_instance = ClaudeIntegration()
    return _claude_instance
