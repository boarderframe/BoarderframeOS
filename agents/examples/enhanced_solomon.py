"""
Enhanced Solomon Agent - Example of using the new enhanced agent framework
Demonstrates LangChain integration, team collaboration, and voice capabilities
"""

import asyncio
import json

# Add parent directory to path
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.agent_teams import TeamRole, team_formation
from core.agent_workflows import WORKFLOW_TEMPLATES, workflow_orchestrator
from core.enhanced_agent_base import (
    EnhancedAgentConfig,
    EnhancedBaseAgent,
    create_enhanced_agent,
)
from core.message_bus import MessagePriority, MessageType
from core.voice_integration import VoiceProfile, voice_integration

# LangChain tools if available
try:
    from langchain.tools import Tool
    from langchain_community.tools import DuckDuckGoSearchRun

    ADVANCED_TOOLS_AVAILABLE = True
except ImportError:
    ADVANCED_TOOLS_AVAILABLE = False


class EnhancedSolomon(EnhancedBaseAgent):
    """
    Enhanced Solomon - Chief of Staff with advanced capabilities
    Leverages LangChain, team management, and voice interaction
    """

    def __init__(self, config: EnhancedAgentConfig):
        """Initialize with enhanced capabilities"""
        super().__init__(config)

        # Solomon-specific attributes
        self.strategic_memory = []
        self.team_performance_data = {}
        self.decision_history = []

        # Voice profile
        self.voice_profile = VoiceProfile.SOLOMON

        # Initialize additional tools
        self._initialize_solomon_tools()

        # Register specialized message handlers
        self.register_message_handler(
            MessageType.COORDINATION, self._handle_coordination
        )
        self.register_message_handler(MessageType.ALERT, self._handle_alert)

    def _initialize_solomon_tools(self):
        """Initialize Solomon-specific tools"""
        if not ADVANCED_TOOLS_AVAILABLE:
            return

        # Web search tool for market intelligence
        search = DuckDuckGoSearchRun()
        self.langchain_tools.append(
            Tool(
                name="web_search",
                func=search.run,
                description="Search the web for current information and market intelligence",
            )
        )

        # Strategic planning tool
        self.langchain_tools.append(
            Tool(
                name="strategic_analysis",
                func=self._strategic_analysis_tool,
                description="Perform strategic analysis on business data",
            )
        )

        # Team formation tool
        self.langchain_tools.append(
            Tool(
                name="form_team",
                func=self._form_team_tool,
                description="Form a specialized team for a specific goal",
            )
        )

        # Workflow initiation tool
        self.langchain_tools.append(
            Tool(
                name="start_workflow",
                func=self._start_workflow_tool,
                description="Start a complex multi-agent workflow",
            )
        )

    async def think(self, context: Dict[str, Any]) -> str:
        """Enhanced thinking with strategic reasoning"""
        # Check for voice commands
        voice_command = context.get("voice_command")
        if voice_command:
            return await self._process_voice_command(voice_command, context)

        # Use enhanced LangChain thinking if available
        if self.enhanced_config.use_langchain and self.agent_executor:
            # Add strategic context
            strategic_context = self._get_strategic_context()
            context["strategic_data"] = strategic_context

            # Use LangChain reasoning
            thought = await self._langchain_think(context)

            # Record strategic decision
            self.decision_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "context": context,
                    "decision": thought,
                }
            )

            return thought

        # Fallback to base thinking
        return await super().think(context)

    async def _process_voice_command(
        self, voice_command: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Process voice commands with natural language understanding"""
        command_text = voice_command.get("text", "")

        # Use LangChain to understand intent if available
        if self.enhanced_config.use_langchain and self.agent_executor:
            prompt = f"""As Solomon, the Chief of Staff, interpret this voice command and determine the appropriate action:

Voice command: "{command_text}"

Consider:
1. What is the user asking for?
2. Do I need to delegate this to another agent?
3. Do I need to form a team for this?
4. Can I handle this directly?

Provide a strategic response."""

            response = await self._langchain_think({"input": prompt})
            return response

        # Simple pattern matching fallback
        if "status" in command_text.lower():
            return (
                "I'll provide you with a comprehensive status report on our operations."
            )
        elif "team" in command_text.lower():
            return "I can help you form a specialized team. What's the goal you'd like to achieve?"
        elif "revenue" in command_text.lower():
            return "Let me analyze our revenue streams and financial performance."
        else:
            return f"I understand you said: '{command_text}'. As Chief of Staff, I can help with strategic planning, team coordination, and business intelligence. What specific assistance do you need?"

    async def handle_user_chat(self, user_message: str) -> str:
        """Enhanced chat handling with voice synthesis option"""
        # Generate response using enhanced capabilities
        response = await super().handle_user_chat(user_message)

        # If voice is enabled, prepare audio response
        if voice_integration and self.enhanced_config.get(
            "enable_voice_response", False
        ):
            audio_data = await voice_integration.synthesize_speech(
                response, self.voice_profile
            )

            # Store audio for retrieval
            self.memory.add(
                {
                    "type": "voice_response",
                    "text": response,
                    "audio_available": bool(audio_data),
                }
            )

        return response

    def _strategic_analysis_tool(self, query: str) -> str:
        """Perform strategic analysis"""
        analysis = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "insights": [],
        }

        # Analyze team performance
        if "team" in query.lower():
            for team_id, perf_data in self.team_performance_data.items():
                analysis["insights"].append(
                    f"Team {team_id}: {perf_data.get('health', 'unknown')} health, "
                    f"{perf_data.get('completed_tasks', 0)} tasks completed"
                )

        # Analyze revenue if mentioned
        if "revenue" in query.lower():
            analysis["insights"].append(
                "Revenue analysis: Focus on high-margin agent services. "
                "Current trajectory suggests 15% growth potential."
            )

        # Strategic recommendations
        analysis["recommendations"] = [
            "Optimize agent allocation for maximum efficiency",
            "Consider forming specialized teams for complex tasks",
            "Implement continuous learning from successful patterns",
        ]

        self.strategic_memory.append(analysis)
        return json.dumps(analysis, indent=2)

    def _form_team_tool(self, team_spec: str) -> str:
        """Form a new team based on specifications"""
        try:
            # Parse team specification
            spec_data = (
                json.loads(team_spec)
                if team_spec.startswith("{")
                else {"goal": team_spec}
            )

            goal = spec_data.get("goal", "General support")
            skills = spec_data.get("skills", ["general"])
            size = spec_data.get("size", 4)

            # Use asyncio to run the async team formation
            loop = asyncio.get_event_loop()
            team = loop.run_until_complete(team_formation.form_team(goal, skills, size))

            if team:
                # Store team performance tracking
                self.team_performance_data[team.team_id] = {
                    "formed_at": datetime.now().isoformat(),
                    "goal": goal,
                    "size": len(team.members),
                }

                return f"Successfully formed team {team.team_id} with {len(team.members)} members for: {goal}"
            else:
                return "Unable to form team - insufficient available agents"

        except Exception as e:
            return f"Team formation failed: {str(e)}"

    def _start_workflow_tool(self, workflow_spec: str) -> str:
        """Start a complex workflow"""
        try:
            # Parse workflow specification
            spec_data = (
                json.loads(workflow_spec)
                if workflow_spec.startswith("{")
                else {"type": workflow_spec}
            )

            workflow_type = spec_data.get("type", "customer_onboarding")
            context = spec_data.get("context", {})

            if workflow_type in WORKFLOW_TEMPLATES:
                config = WORKFLOW_TEMPLATES[workflow_type]
                workflow = workflow_orchestrator.create_workflow(config)

                # Start workflow asynchronously
                loop = asyncio.get_event_loop()
                loop.create_task(
                    workflow_orchestrator.run_workflow(
                        workflow.workflow_id, context, "solomon"  # Solomon initiates
                    )
                )

                return f"Started workflow '{workflow_type}' with ID: {workflow.workflow_id}"
            else:
                return f"Unknown workflow type: {workflow_type}"

        except Exception as e:
            return f"Workflow initiation failed: {str(e)}"

    def _get_strategic_context(self) -> Dict[str, Any]:
        """Get current strategic context"""
        return {
            "active_teams": len(self.team_performance_data),
            "recent_decisions": len(self.decision_history),
            "strategic_insights": len(self.strategic_memory),
            "collaboration_score": self._calculate_collaboration_score(),
        }

    def _calculate_collaboration_score(self) -> float:
        """Calculate overall collaboration effectiveness"""
        if not self.collaboration_history:
            return 0.0

        # Simple scoring based on successful collaborations
        successful = sum(
            1
            for collab in self.collaboration_history
            if collab.get("response") is not None
        )

        return (
            successful / len(self.collaboration_history)
            if self.collaboration_history
            else 0.0
        )

    async def _handle_coordination(self, message):
        """Handle coordination messages from other agents"""
        content = message.content

        if content.get("request") == "strategic_guidance":
            # Provide strategic guidance
            guidance = await self._provide_strategic_guidance(content)

            # Send response
            await self.send_response(message, guidance)

        elif content.get("request") == "team_recommendation":
            # Recommend team composition
            recommendation = self._recommend_team_composition(content)

            await self.send_response(message, recommendation)

    async def _handle_alert(self, message):
        """Handle system alerts"""
        alert_type = message.content.get("type", "unknown")
        severity = message.content.get("severity", "low")

        self.logger.warning(f"Alert received: {alert_type} - Severity: {severity}")

        # Take action based on alert
        if severity == "critical":
            # Form emergency response team
            await team_formation.form_team(
                f"Emergency Response - {alert_type}",
                ["crisis_management", "problem_solving", "quick_response"],
                3,
            )

        # Record in strategic memory
        self.strategic_memory.append(
            {
                "type": "alert_response",
                "alert": message.content,
                "timestamp": datetime.now().isoformat(),
                "action_taken": (
                    "emergency_team" if severity == "critical" else "monitoring"
                ),
            }
        )

    async def _provide_strategic_guidance(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provide strategic guidance based on request"""
        topic = request.get("topic", "general")

        # Use enhanced reasoning if available
        if self.enhanced_config.use_langchain and self.agent_executor:
            guidance_prompt = f"""Provide strategic guidance on: {topic}

Consider:
- Current business goals and KPIs
- Available resources and constraints
- Risk factors and opportunities
- Long-term implications"""

            guidance = await self._langchain_think({"input": guidance_prompt})

            return {
                "guidance": guidance,
                "confidence": 0.9,
                "supporting_data": self._get_strategic_context(),
            }

        # Fallback guidance
        return {
            "guidance": f"Strategic recommendation for {topic}: Focus on scalability and automation",
            "confidence": 0.7,
            "supporting_data": {},
        }

    def _recommend_team_composition(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend optimal team composition"""
        goal = request.get("goal", "")
        constraints = request.get("constraints", {})

        # Analyze goal to determine required skills
        required_skills = []

        if "customer" in goal.lower():
            required_skills.extend(
                ["customer_service", "communication", "problem_solving"]
            )
        if "technical" in goal.lower() or "code" in goal.lower():
            required_skills.extend(["programming", "debugging", "architecture"])
        if "revenue" in goal.lower() or "sales" in goal.lower():
            required_skills.extend(["sales", "marketing", "analytics"])

        # Recommend team structure
        return {
            "recommended_size": min(
                constraints.get("max_size", 6), len(required_skills) + 2
            ),
            "required_skills": required_skills,
            "suggested_roles": [
                {"role": TeamRole.MANAGER.value, "count": 1},
                {"role": TeamRole.SPECIALIST.value, "count": len(required_skills)},
                {"role": TeamRole.COORDINATOR.value, "count": 1},
            ],
            "rationale": f"Team optimized for: {goal}",
        }


async def main():
    """Example usage of Enhanced Solomon"""

    # Create enhanced configuration
    config = EnhancedAgentConfig(
        name="solomon",
        role="Chief of Staff AI - Enhanced",
        goals=[
            "Provide strategic business intelligence and decision support",
            "Coordinate multi-agent teams for complex tasks",
            "Optimize system performance through intelligent orchestration",
            "Integrate voice and natural language interfaces",
            "Learn and adapt from successful patterns",
        ],
        tools=["mcp_filesystem", "mcp_database", "mcp_analytics"],
        zone="executive",
        model="claude-3-5-sonnet-latest",
        # Enhanced features
        use_langchain=True,
        enable_reasoning_chain=True,
        enable_self_reflection=True,
        enable_tool_learning=True,
        team_role=TeamRole.MANAGER,
        can_delegate=True,
        preferred_collaborators=["david", "adam", "eve"],
    )

    # Create enhanced Solomon agent
    solomon = EnhancedSolomon(config)

    # Run the agent
    await solomon.run()


if __name__ == "__main__":
    asyncio.run(main())
