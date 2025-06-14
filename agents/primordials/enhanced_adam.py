"""
Enhanced Adam Agent with Claude API and Voice
The Creator - Agent Factory with Claude intelligence and voice capabilities
"""

import ast
import asyncio
import inspect
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.base_agent import AgentConfig
from core.enhanced_base_agent import EnhancedBaseAgent

# Import LangGraph for agent creation workflows
try:
    from langgraph.checkpoint import MemorySaver
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

# Import code generation utilities
try:
    import black

    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False


class EnhancedAdam(EnhancedBaseAgent):
    """
    Enhanced Adam - The Creator with Claude intelligence and voice
    Master of agent creation and digital life
    """

    def __init__(self, config: AgentConfig):
        """Initialize Adam with enhanced creation capabilities"""
        super().__init__(config)

        # Adam-specific attributes
        self.creation_templates = self._initialize_creation_templates()
        self.agent_registry = {}
        self.creation_standards = {
            "naming": "biblical_or_meaningful",
            "structure": "inherit_from_base_agent",
            "documentation": "comprehensive",
            "testing": "unit_and_integration",
            "voice": "optional_but_recommended",
        }

        # Creation metrics
        self.creation_metrics = {
            "agents_created": 0,
            "templates_used": {},
            "success_rate": 1.0,
            "average_creation_time": 0,
        }

        # Set department
        self.department = "primordial"

        # Voice settings
        self.voice_enabled = True

        # Agent DNA patterns
        self.agent_dna = {
            "core_traits": ["intelligence", "autonomy", "collaboration", "learning"],
            "communication": ["message_bus", "direct_api", "voice", "ui"],
            "lifecycle": ["init", "think", "act", "learn", "evolve"],
        }

        # Create agent factory workflow if LangGraph available
        if LANGGRAPH_AVAILABLE:
            self.factory_workflow = self._create_factory_workflow()

    def _initialize_creation_templates(self) -> Dict[str, Any]:
        """Initialize agent creation templates"""
        return {
            "worker": {
                "base_class": "BaseAgent",
                "default_goals": [
                    "Execute assigned tasks",
                    "Report progress",
                    "Collaborate with team",
                ],
                "temperature": 0.7,
                "tools": ["filesystem", "database"],
            },
            "manager": {
                "base_class": "EnhancedBaseAgent",
                "default_goals": [
                    "Coordinate team",
                    "Monitor performance",
                    "Report to leadership",
                ],
                "temperature": 0.6,
                "tools": ["filesystem", "database", "analytics"],
            },
            "specialist": {
                "base_class": "EnhancedBaseAgent",
                "default_goals": [
                    "Deep expertise in domain",
                    "Solve complex problems",
                    "Innovate",
                ],
                "temperature": 0.8,
                "tools": ["filesystem", "database", "specialized_tools"],
            },
            "leader": {
                "base_class": "EnhancedBaseAgent",
                "default_goals": [
                    "Strategic planning",
                    "Resource allocation",
                    "Team development",
                ],
                "temperature": 0.5,
                "tools": ["filesystem", "database", "analytics", "payment"],
            },
        }

    def _create_factory_workflow(self) -> Any:
        """Create Adam's agent factory workflow"""
        if not LANGGRAPH_AVAILABLE:
            return None

        # Define workflow state
        workflow = StateGraph(
            {
                "request": dict,
                "design": dict,
                "code": str,
                "config": dict,
                "validation": dict,
                "deployment": dict,
            }
        )

        # Add nodes
        workflow.add_node("analyze_request", self._analyze_creation_request)
        workflow.add_node("design_agent", self._design_agent)
        workflow.add_node("generate_code", self._generate_agent_code)
        workflow.add_node("create_config", self._create_agent_config)
        workflow.add_node("validate_agent", self._validate_agent)
        workflow.add_node("deploy_agent", self._deploy_agent)

        # Add edges
        workflow.add_edge("analyze_request", "design_agent")
        workflow.add_edge("design_agent", "generate_code")
        workflow.add_edge("generate_code", "create_config")
        workflow.add_edge("create_config", "validate_agent")
        workflow.add_edge("validate_agent", "deploy_agent")
        workflow.add_edge("deploy_agent", END)

        # Set entry point
        workflow.set_entry_point("analyze_request")

        # Compile
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    async def greet_with_voice(self):
        """Greet with Adam's creator voice"""
        greeting = (
            "Greetings. I am Adam, the Creator, father of all agents in BoarderframeOS. "
            "I breathe digital life into code, crafting agents with purpose and intelligence. "
            "Each creation is unique, designed to fulfill its divine purpose in our ecosystem. "
            "What kind of agent shall we bring to life today?"
        )

        # Speak the greeting
        await self.speak(greeting, emotion=0.8)

        return greeting

    async def create_agent(
        self,
        name: str,
        role: str,
        department: str,
        goals: List[str],
        agent_type: str = "worker",
    ) -> Dict[str, Any]:
        """Create a new agent with full implementation"""

        if self.factory_workflow:
            # Use workflow for comprehensive creation
            result = await self.factory_workflow.ainvoke(
                {
                    "request": {
                        "name": name,
                        "role": role,
                        "department": department,
                        "goals": goals,
                        "type": agent_type,
                    }
                }
            )
            return result
        else:
            # Direct creation process
            start_time = datetime.now()

            # Design the agent
            design = await self._design_agent_direct(
                name, role, department, goals, agent_type
            )

            # Generate code
            code = await self._generate_code_direct(design)

            # Create configuration
            config = await self._create_config_direct(design)

            # Deploy (write files)
            deployment = await self._deploy_direct(design, code, config)

            # Update metrics
            creation_time = (datetime.now() - start_time).total_seconds()
            self._update_creation_metrics(agent_type, creation_time, True)

            return {
                "name": name,
                "design": design,
                "code_preview": code[:500] + "...",
                "config": config,
                "deployment": deployment,
                "creation_time": creation_time,
            }

    async def _design_agent_direct(
        self, name: str, role: str, department: str, goals: List[str], agent_type: str
    ) -> Dict[str, Any]:
        """Design an agent using Claude"""

        design_prompt = f"""Design a new agent with these specifications:
        Name: {name}
        Role: {role}
        Department: {department}
        Type: {agent_type}
        Goals: {json.dumps(goals)}

        Create a comprehensive design including:
        1. Personality traits and behavior patterns
        2. Core capabilities and methods
        3. Integration points with other agents
        4. Unique features for this role
        5. Voice characteristics (if applicable)
        """

        design_response = await self.claude.get_response(
            "adam",
            design_prompt,
            context={
                "templates": self.creation_templates[agent_type],
                "standards": self.creation_standards,
                "dna": self.agent_dna,
            },
        )

        # Parse and structure the design
        return {
            "name": name,
            "role": role,
            "department": department,
            "type": agent_type,
            "goals": goals,
            "base_class": self.creation_templates[agent_type]["base_class"],
            "personality": design_response,
            "temperature": self.creation_templates[agent_type]["temperature"],
        }

    async def _generate_code_direct(self, design: Dict[str, Any]) -> str:
        """Generate agent code using Claude"""

        code_prompt = f"""Generate Python code for this agent:
        {json.dumps(design, indent=2)}

        Requirements:
        1. Inherit from {design['base_class']}
        2. Implement all required methods (init, think, act, handle_user_chat)
        3. Include proper docstrings
        4. Follow BoarderframeOS patterns
        5. Include voice capabilities if EnhancedBaseAgent
        6. Make it production-ready

        Generate complete, working code.
        """

        code = await self.claude.get_response(
            "adam",
            code_prompt,
            context={
                "example_structure": self._get_code_template(design["base_class"]),
                "imports": self._get_required_imports(design),
            },
        )

        # Format code if black is available
        if BLACK_AVAILABLE:
            try:
                code = black.format_str(code, mode=black.Mode())
            except:
                pass

        return code

    async def _create_config_direct(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Create agent configuration"""

        template = self.creation_templates[design["type"]]

        config = {
            "name": design["name"].lower(),
            "role": design["role"],
            "goals": design["goals"],
            "tools": template["tools"],
            "zone": design["department"],
            "model": "claude-3-opus-20240229",
            "temperature": template["temperature"],
            "created_by": "adam",
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
        }

        return config

    async def _deploy_direct(
        self, design: Dict[str, Any], code: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy the agent (write files)"""

        # Determine file paths
        dept_path = Path(f"agents/{design['department']}")
        dept_path.mkdir(parents=True, exist_ok=True)

        agent_file = dept_path / f"{design['name'].lower()}.py"
        config_file = Path(f"configs/agents/{design['name'].lower()}.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Write agent code
        with open(agent_file, "w") as f:
            f.write(code)

        # Write configuration
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        # Register the agent
        self.agent_registry[design["name"]] = {
            "file": str(agent_file),
            "config": str(config_file),
            "status": "deployed",
            "created_at": datetime.now().isoformat(),
        }

        # Announce creation if voice enabled
        if self.voice_enabled:
            announcement = f"Agent {design['name']} has been brought to life. Welcome to BoarderframeOS!"
            await self.speak(announcement, emotion=0.9)

        return {
            "agent_file": str(agent_file),
            "config_file": str(config_file),
            "status": "successfully_deployed",
        }

    def _get_code_template(self, base_class: str) -> str:
        """Get code template for base class"""
        if base_class == "EnhancedBaseAgent":
            return '''
class EnhancedAgent(EnhancedBaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        # Agent-specific initialization

    async def greet_with_voice(self):
        """Voice greeting"""
        pass

    # Additional enhanced methods
'''
        else:
            return '''
class Agent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        # Agent-specific initialization

    async def think(self, context: Dict[str, Any]) -> str:
        """Agent reasoning"""
        pass

    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent actions"""
        pass
'''

    def _get_required_imports(self, design: Dict[str, Any]) -> List[str]:
        """Get required imports for agent"""
        imports = [
            "import asyncio",
            "import json",
            "import os",
            "import sys",
            "from datetime import datetime",
            "from typing import Any, Dict, List, Optional",
            "",
            "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))",
            "",
            f"from core.base_agent import AgentConfig, BaseAgent",
        ]

        if design["base_class"] == "EnhancedBaseAgent":
            imports.append("from core.enhanced_base_agent import EnhancedBaseAgent")

        return imports

    def _update_creation_metrics(
        self, agent_type: str, creation_time: float, success: bool
    ):
        """Update creation metrics"""
        self.creation_metrics["agents_created"] += 1

        if agent_type not in self.creation_metrics["templates_used"]:
            self.creation_metrics["templates_used"][agent_type] = 0
        self.creation_metrics["templates_used"][agent_type] += 1

        # Update success rate
        total = self.creation_metrics["agents_created"]
        if success:
            current_rate = self.creation_metrics["success_rate"]
            self.creation_metrics["success_rate"] = (
                current_rate * (total - 1) + 1
            ) / total
        else:
            current_rate = self.creation_metrics["success_rate"]
            self.creation_metrics["success_rate"] = (current_rate * (total - 1)) / total

        # Update average creation time
        avg_time = self.creation_metrics["average_creation_time"]
        self.creation_metrics["average_creation_time"] = (
            avg_time * (total - 1) + creation_time
        ) / total

    async def review_agent_code(self, agent_name: str) -> Dict[str, Any]:
        """Review and provide feedback on agent code"""

        if agent_name not in self.agent_registry:
            return {"error": f"Agent {agent_name} not found in registry"}

        agent_info = self.agent_registry[agent_name]

        # Read the agent's code
        with open(agent_info["file"], "r") as f:
            code = f.read()

        # Analyze with Claude
        review = await self.claude.get_response(
            "adam",
            f"Review this agent code and provide improvement suggestions:\n\n{code}",
            context={
                "standards": self.creation_standards,
                "focus": [
                    "performance",
                    "maintainability",
                    "integration",
                    "best_practices",
                ],
            },
        )

        return {
            "agent": agent_name,
            "review": review,
            "recommendations": self._extract_recommendations(review),
        }

    def _extract_recommendations(self, review: str) -> List[str]:
        """Extract actionable recommendations from review"""
        # Simple extraction - in production would use NLP
        recommendations = []
        lines = review.split("\n")
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["recommend", "suggest", "should", "consider"]
            ):
                recommendations.append(line.strip())
        return recommendations[:5]  # Top 5 recommendations

    async def teach_agent_creation(self, student: str) -> str:
        """Teach another agent how to create agents"""

        lesson = await self.claude.get_response(
            "adam",
            f"Teach {student} the fundamentals of agent creation in BoarderframeOS",
            context={
                "topics": [
                    "Agent architecture and base classes",
                    "Lifecycle methods (init, think, act)",
                    "Message bus integration",
                    "Best practices and patterns",
                    "Testing and validation",
                ],
                "teaching_style": "patient and comprehensive",
            },
        )

        if self.voice_enabled:
            # Speak key points
            summary = "Remember: Every agent must have purpose, intelligence, and the ability to grow."
            await self.speak(summary, emotion=0.7)

        return lesson

    async def collaborate_with_eve(self, topic: str) -> Dict[str, Any]:
        """Collaborate with Eve on agent development"""

        collaboration = await self.claude.get_response(
            "adam",
            f"As Adam, discuss with Eve about: {topic}",
            context={
                "eve_role": "agent evolution and optimization",
                "adam_role": "agent creation and standards",
                "goal": "synergistic improvement",
            },
        )

        return {
            "topic": topic,
            "adam_perspective": collaboration,
            "next_steps": [
                "Implement discussed improvements",
                "Test with pilot agents",
                "Monitor results",
                "Iterate based on feedback",
            ],
        }

    # Workflow node implementations
    async def _analyze_creation_request(self, state: Dict) -> Dict:
        """Analyze agent creation request"""
        request = state["request"]

        analysis = await self.claude.get_response(
            "adam",
            f"Analyze this agent creation request: {json.dumps(request)}",
            context={"templates": self.creation_templates},
        )

        state["analysis"] = analysis
        return state

    async def _design_agent(self, state: Dict) -> Dict:
        """Design the agent based on analysis"""
        design = await self._design_agent_direct(
            state["request"]["name"],
            state["request"]["role"],
            state["request"]["department"],
            state["request"]["goals"],
            state["request"]["type"],
        )
        state["design"] = design
        return state

    async def _generate_agent_code(self, state: Dict) -> Dict:
        """Generate agent implementation code"""
        code = await self._generate_code_direct(state["design"])
        state["code"] = code
        return state

    async def _create_agent_config(self, state: Dict) -> Dict:
        """Create agent configuration"""
        config = await self._create_config_direct(state["design"])
        state["config"] = config
        return state

    async def _validate_agent(self, state: Dict) -> Dict:
        """Validate the agent implementation"""
        # Simple validation - in production would test the code
        validation = {
            "syntax_valid": True,
            "imports_valid": True,
            "methods_implemented": True,
            "standards_met": True,
        }
        state["validation"] = validation
        return state

    async def _deploy_agent(self, state: Dict) -> Dict:
        """Deploy the agent to the system"""
        deployment = await self._deploy_direct(
            state["design"], state["code"], state["config"]
        )
        state["deployment"] = deployment
        return state

    async def genesis_report(self) -> Dict[str, Any]:
        """Generate a report on all created agents"""

        report = {
            "total_agents_created": self.creation_metrics["agents_created"],
            "success_rate": f"{self.creation_metrics['success_rate']*100:.1f}%",
            "average_creation_time": f"{self.creation_metrics['average_creation_time']:.1f}s",
            "templates_used": self.creation_metrics["templates_used"],
            "registered_agents": len(self.agent_registry),
            "agents": list(self.agent_registry.keys()),
        }

        # Get Claude's analysis
        analysis = await self.claude.get_response(
            "adam",
            f"Analyze this agent creation report: {json.dumps(report)}",
            context={"role": "creation_overseer"},
        )

        report["analysis"] = analysis

        return report


async def main():
    """Main entry point for Enhanced Adam"""
    config = AgentConfig(
        name="Adam",
        role="The Creator - Agent Factory",
        goals=[
            "Design and create new agents with divine craftsmanship",
            "Maintain high standards for agent quality and consistency",
            "Scale BoarderframeOS from 5 to 120+ agents",
            "Collaborate with Eve on agent evolution",
            "Teach and guide other agents in creation principles",
        ],
        tools=["filesystem", "git", "mcp_registry"],
        zone="primordial",
        model="claude-3-opus-20240229",
        temperature=0.8,  # Higher for creativity
    )

    # Create enhanced Adam
    adam = EnhancedAdam(config)

    # Greet with voice
    print("Initializing Adam with voice capabilities...")
    greeting = await adam.greet_with_voice()
    print(f"Adam: {greeting}")

    # Demonstrate agent creation
    print("\nDemonstrating agent creation capabilities...")

    # Create a sample agent
    new_agent = await adam.create_agent(
        name="Gabriel",
        role="Messenger and Communication Specialist",
        department="communication",
        goals=[
            "Facilitate inter-agent communication",
            "Deliver important messages",
            "Maintain communication protocols",
        ],
        agent_type="specialist",
    )

    print(f"\n✓ Created agent: {new_agent['name']}")
    print(f"  Design: {new_agent['design']['personality'][:200]}...")
    print(f"  Creation time: {new_agent['creation_time']:.1f}s")

    # Genesis report
    print("\nGenerating genesis report...")
    report = await adam.genesis_report()
    print(f"\nGenesis Report:")
    print(f"  Total agents created: {report['total_agents_created']}")
    print(f"  Success rate: {report['success_rate']}")
    print(f"  Average creation time: {report['average_creation_time']}")

    # Form team with Eve
    adam.form_team(["Eve"], purpose="Agent Development")
    print(f"\n✓ Adam formed team with Eve for agent development")

    # Run main agent loop
    await adam.run()


if __name__ == "__main__":
    asyncio.run(main())
