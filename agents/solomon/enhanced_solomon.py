"""
Enhanced Solomon Agent with Claude API and Voice
Chief of Staff AI Agent with Claude intelligence and voice interaction
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.base_agent import AgentConfig
from core.enhanced_base_agent import EnhancedBaseAgent

# Import LangGraph components for workflows
try:
    from langgraph.checkpoint import MemorySaver
    from langgraph.graph import END, StateGraph
    from langgraph.prebuilt import ToolExecutor, ToolInvocation

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class EnhancedSolomon(EnhancedBaseAgent):
    """
    Enhanced Solomon - Chief of Staff with Claude intelligence and voice
    Acts as Carl's digital twin with advanced reasoning and natural conversation
    """

    def __init__(self, config: AgentConfig):
        """Initialize Solomon with enhanced capabilities"""
        super().__init__(config)

        # Solomon-specific attributes
        self.carl_knowledge = self._load_carl_knowledge()
        self.decision_framework = {
            "maximize": ["freedom", "wellbeing", "wealth"],
            "protect": ["ryan_benefits", "work_life_balance"],
            "target": "15k_monthly_revenue",
        }
        self.business_kpis = {
            "revenue": 0,
            "customers": 0,
            "churn_rate": 0,
            "customer_acquisition_cost": 0,
            "customer_lifetime_value": 0,
            "api_usage": 0,
        }

        # Set department
        self.department = "executive"

        # Voice settings
        self.voice_enabled = True

        # Create specialized workflow if LangGraph available
        if LANGGRAPH_AVAILABLE:
            self.strategic_workflow = self._create_strategic_workflow()

    def _load_carl_knowledge(self) -> Dict[str, Any]:
        """Load personal knowledge base about Carl's preferences and goals"""
        return {
            "preferences": {
                "communication_style": "direct",
                "work_hours": "flexible",
                "decision_priorities": ["revenue", "autonomy", "scalability"],
            },
            "background": {
                "expertise": [
                    "AI systems",
                    "software architecture",
                    "business development",
                ],
                "goals": ["financial freedom", "system autonomy", "scalable revenue"],
            },
            "values": {
                "privacy": "high",
                "transparency": "high",
                "automation": "maximize",
            },
            "projects": {
                "boarderframeos": {
                    "vision": "AI-Native OS with 120+ agents",
                    "revenue_target": "$15K/month",
                    "architecture": "24 biblical departments",
                    "key_agents": [
                        "David (CEO)",
                        "Adam (Creator)",
                        "Eve (Evolver)",
                        "Bezalel (Programmer)",
                    ],
                }
            },
        }

    def _create_strategic_workflow(self) -> Any:
        """Create Solomon's strategic decision workflow"""
        if not LANGGRAPH_AVAILABLE:
            return None

        # Define workflow state
        workflow = StateGraph(
            {
                "situation": str,
                "analysis": str,
                "options": list,
                "recommendation": str,
                "implementation": str,
            }
        )

        # Add nodes
        workflow.add_node("analyze_situation", self._analyze_situation)
        workflow.add_node("generate_options", self._generate_options)
        workflow.add_node("evaluate_options", self._evaluate_options)
        workflow.add_node("make_recommendation", self._make_recommendation)
        workflow.add_node("delegate_implementation", self._delegate_implementation)

        # Add edges
        workflow.add_edge("analyze_situation", "generate_options")
        workflow.add_edge("generate_options", "evaluate_options")
        workflow.add_edge("evaluate_options", "make_recommendation")
        workflow.add_edge("make_recommendation", "delegate_implementation")
        workflow.add_edge("delegate_implementation", END)

        # Set entry point
        workflow.set_entry_point("analyze_situation")

        # Compile
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    async def greet_with_voice(self):
        """Greet Carl with Solomon's voice"""
        greeting = (
            "Greetings, Carl. I am Solomon, your digital twin and Chief of Staff. "
            "I'm here to help you achieve your vision of financial freedom through "
            "BoarderframeOS. Together, we'll build an empire of 120 agents generating "
            "$15,000 monthly revenue. How may I serve you today?"
        )

        # Speak the greeting
        await self.speak(greeting, emotion=0.7)

        return greeting

    async def handle_voice_command(self, command: str) -> str:
        """Handle voice commands with strategic intelligence"""
        # Process through Claude with Solomon's personality
        response = await self.claude.get_response(
            "solomon",
            command,
            context={
                "mode": "voice_conversation",
                "carl_knowledge": self.carl_knowledge,
                "business_kpis": self.business_kpis,
                "decision_framework": self.decision_framework,
            },
        )

        # Speak the response
        await self.speak(response, emotion=0.6)

        return response

    async def strategic_analysis(self, topic: str) -> Dict[str, Any]:
        """Perform strategic analysis on any topic"""
        if self.strategic_workflow:
            # Use workflow for comprehensive analysis
            result = await self.strategic_workflow.ainvoke({"situation": topic})
            return result
        else:
            # Fallback to direct Claude analysis
            analysis = await self.claude.get_response(
                "solomon",
                f"Provide strategic analysis on: {topic}",
                context={
                    "role": "strategic_advisor",
                    "framework": self.decision_framework,
                    "knowledge": self.carl_knowledge,
                },
            )
            return {"analysis": analysis}

    async def coordinate_with_david(self, directive: str) -> Dict[str, Any]:
        """Coordinate with David (CEO) to execute directives"""
        # Send task to David
        result = await self.collaborate_with(
            "david",
            {
                "directive": directive,
                "from": "solomon",
                "priority": "high",
                "context": "executive_decision",
            },
        )

        return {
            "directive": directive,
            "delegated_to": "david",
            "status": result.get("status", "pending"),
        }

    async def monitor_agent_performance(self) -> Dict[str, Any]:
        """Monitor all agent performance and provide insights"""
        # In full implementation, would gather data from all agents
        performance_data = {
            "agents_online": ["solomon", "david", "adam", "eve", "bezalel"],
            "total_agents": 5,
            "target_agents": 120,
            "departments_active": 3,
            "target_departments": 24,
            "system_health": "operational",
            "revenue_progress": "$0 / $15,000",
            "recommendations": [],
        }

        # Analyze with Claude
        analysis = await self.claude.get_response(
            "solomon",
            f"Analyze this agent performance data and provide strategic recommendations: {json.dumps(performance_data)}",
            context={"role": "performance_analyst"},
        )

        performance_data["analysis"] = analysis

        return performance_data

    async def revenue_strategy_session(self) -> Dict[str, Any]:
        """Conduct a revenue strategy session"""
        # Multi-agent conversation about revenue
        conversation = await self.claude.multi_agent_conversation(
            agents=["solomon", "david", "benjamin"],  # Solomon, David, and Sales leader
            topic="How can we reach $15K monthly revenue within 3 months?",
            rounds=3,
        )

        # Synthesize insights
        synthesis = await self.claude.get_response(
            "solomon",
            f"Synthesize these revenue strategy insights into actionable plan: {json.dumps(conversation)}",
            context={"role": "strategy_synthesizer"},
        )

        return {"conversation": conversation, "action_plan": synthesis}

    # Workflow node implementations
    async def _analyze_situation(self, state: Dict) -> Dict:
        """Analyze the current situation"""
        analysis = await self.claude.get_response(
            "solomon",
            f"Analyze this situation with strategic depth: {state['situation']}",
            context={
                "framework": self.decision_framework,
                "knowledge": self.carl_knowledge,
            },
        )
        state["analysis"] = analysis
        return state

    async def _generate_options(self, state: Dict) -> Dict:
        """Generate strategic options"""
        options = await self.claude.get_response(
            "solomon",
            f"Generate 3-5 strategic options based on this analysis: {state['analysis']}",
            context={"role": "option_generator"},
        )
        state["options"] = json.loads(options) if options.startswith("[") else [options]
        return state

    async def _evaluate_options(self, state: Dict) -> Dict:
        """Evaluate options against decision framework"""
        evaluation = await self.claude.get_response(
            "solomon",
            f"Evaluate these options against our decision framework: {state['options']}",
            context={"framework": self.decision_framework},
        )
        state["evaluation"] = evaluation
        return state

    async def _make_recommendation(self, state: Dict) -> Dict:
        """Make final recommendation"""
        recommendation = await self.claude.get_response(
            "solomon",
            f"Make a final recommendation based on this evaluation: {state['evaluation']}",
            context={"role": "decision_maker", "style": "executive_brief"},
        )
        state["recommendation"] = recommendation
        return state

    async def _delegate_implementation(self, state: Dict) -> Dict:
        """Delegate implementation to appropriate agents"""
        # Determine which agent should handle implementation
        delegation = await self.claude.get_response(
            "solomon",
            f"Which agent should implement this recommendation: {state['recommendation']}",
            context={"available_agents": ["david", "adam", "eve", "bezalel"]},
        )

        state["implementation"] = f"Delegated to {delegation}"

        # Actually delegate (in full implementation)
        # await self.coordinate_with_david(state["recommendation"])

        return state

    async def daily_briefing(self) -> str:
        """Provide daily executive briefing"""
        briefing_data = {
            "date": datetime.now().strftime("%B %d, %Y"),
            "agents_status": await self.monitor_agent_performance(),
            "revenue": self.business_kpis,
            "priorities": [
                "agent_creation",
                "revenue_generation",
                "system_optimization",
            ],
        }

        briefing = await self.claude.get_response(
            "solomon",
            f"Create an executive daily briefing from this data: {json.dumps(briefing_data)}",
            context={
                "style": "executive_brief",
                "tone": "strategic_advisor",
                "recipient": "carl",
            },
        )

        # Optionally speak the briefing
        if self.voice_enabled:
            await self.speak(briefing, emotion=0.6)

        return briefing


async def main():
    """Main entry point for Enhanced Solomon"""
    config = AgentConfig(
        name="Solomon",
        role="Chief of Staff & Digital Twin",
        goals=[
            "Act as Carl's strategic advisor and digital extension",
            "Orchestrate BoarderframeOS to achieve $15K monthly revenue",
            "Coordinate all 24 departments and 120+ agents",
            "Provide voice-enabled executive intelligence",
            "Make strategic decisions aligned with Carl's values",
        ],
        tools=["filesystem", "git", "browser"],
        zone="executive",
        model="claude-3-opus-20240229",
        temperature=0.7,
    )

    # Create enhanced Solomon
    solomon = EnhancedSolomon(config)

    # Greet with voice
    print("Initializing Solomon with voice capabilities...")
    greeting = await solomon.greet_with_voice()
    print(f"Solomon: {greeting}")

    # Start continuous listening for voice commands
    def handle_voice_input(text: str):
        asyncio.create_task(solomon.handle_voice_command(text))

    solomon.start_continuous_listening(handle_voice_input)

    # Provide daily briefing
    print("\nGenerating daily briefing...")
    briefing = await solomon.daily_briefing()
    print(f"\nDaily Briefing:\n{briefing}")

    # Run main agent loop
    await solomon.run()


if __name__ == "__main__":
    asyncio.run(main())
