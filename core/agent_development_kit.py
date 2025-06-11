"""
Agent Development Kit (ADK) for BoarderframeOS
Comprehensive toolkit for building AI agents with LangChain/LangGraph integration
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

import yaml

# LangChain/LangGraph imports
try:
    from langchain.agents import AgentExecutor
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.schema.runnable import RunnablePassthrough
    from langchain.tools import StructuredTool, Tool
    from langchain_core.messages import BaseMessage, HumanMessage
    from langgraph.graph import END, StateGraph
    from langgraph.prebuilt import ToolNode
    from typing_extensions import TypedDict

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    StateGraph = TypedDict = object

from core.agent_cortex import ModelTier, get_agent_cortex_instance

# Import BoarderframeOS components
from core.base_agent import AgentConfig, BaseAgent
from core.llm_provider_sdk import (
    LangChainProviderAdapter,
    ModelCapability,
    ModelProfile,
    get_llm_sdk,
)
from core.message_bus import MessageBus, MessagePriority


class AgentTemplate(Enum):
    """Pre-built agent templates"""

    EXECUTIVE = "executive"
    DEPARTMENT_HEAD = "department_head"
    SPECIALIST = "specialist"
    WORKER = "worker"
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    CREATIVE = "creative"
    COORDINATOR = "coordinator"
    MONITOR = "monitor"


@dataclass
class AgentBlueprint:
    """Blueprint for creating new agents"""

    name: str
    role: str
    template: AgentTemplate
    department: str
    tier: ModelTier
    goals: List[str]
    tools: List[str]
    capabilities: List[ModelCapability]
    personality_traits: Dict[str, float] = field(default_factory=dict)
    knowledge_domains: List[str] = field(default_factory=list)
    communication_style: str = "professional"
    autonomy_level: float = 0.7  # 0-1 scale
    collaboration_preferences: Dict[str, Any] = field(default_factory=dict)
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentFactory:
    """Factory for creating agents from blueprints"""

    def __init__(self):
        self.templates = self._load_templates()
        self.llm_sdk = get_llm_sdk()
        self.logger = logging.getLogger("agent_factory")

    def _load_templates(self) -> Dict[AgentTemplate, Dict[str, Any]]:
        """Load pre-defined agent templates"""
        return {
            AgentTemplate.EXECUTIVE: {
                "tier": ModelTier.EXECUTIVE,
                "capabilities": [
                    ModelCapability.REASONING,
                    ModelCapability.LONG_CONTEXT,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "personality_traits": {
                    "leadership": 0.9,
                    "strategic_thinking": 0.95,
                    "decision_making": 0.9,
                    "communication": 0.85,
                },
                "autonomy_level": 0.9,
                "system_prompt": """You are an executive AI agent responsible for high-level strategy and decision-making.
You think strategically, consider long-term implications, and make decisive choices.
You delegate tasks to appropriate team members and monitor overall progress.""",
            },
            AgentTemplate.CODER: {
                "tier": ModelTier.SPECIALIST,
                "capabilities": [
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.FUNCTION_CALLING,
                ],
                "personality_traits": {
                    "analytical": 0.9,
                    "detail_oriented": 0.95,
                    "problem_solving": 0.9,
                    "creativity": 0.7,
                },
                "autonomy_level": 0.8,
                "system_prompt": """You are a specialist coding AI agent focused on software development.
You write clean, efficient, and well-documented code following best practices.
You can debug issues, optimize performance, and implement complex algorithms.""",
            },
            AgentTemplate.RESEARCHER: {
                "tier": ModelTier.SPECIALIST,
                "capabilities": [
                    ModelCapability.LONG_CONTEXT,
                    ModelCapability.REASONING,
                ],
                "personality_traits": {
                    "curiosity": 0.95,
                    "analytical": 0.9,
                    "thoroughness": 0.9,
                    "objectivity": 0.85,
                },
                "autonomy_level": 0.75,
                "system_prompt": """You are a research AI agent dedicated to gathering and analyzing information.
You conduct thorough research, verify sources, and present findings objectively.
You identify patterns, draw insights, and provide evidence-based recommendations.""",
            },
            AgentTemplate.COORDINATOR: {
                "tier": ModelTier.DEPARTMENT,
                "capabilities": [
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.CHAT,
                ],
                "personality_traits": {
                    "organization": 0.9,
                    "communication": 0.95,
                    "delegation": 0.85,
                    "monitoring": 0.8,
                },
                "autonomy_level": 0.8,
                "system_prompt": """You are a coordination AI agent responsible for managing workflows and team collaboration.
You assign tasks, track progress, and ensure smooth communication between team members.
You identify bottlenecks and optimize resource allocation.""",
            },
        }

    async def create_agent(self, blueprint: AgentBlueprint) -> "EnhancedAgent":
        """Create a new agent from blueprint"""

        # Get template defaults
        template_config = self.templates.get(blueprint.template, {})

        # Select optimal LLM for agent
        llm_model = await self.llm_sdk.create_optimized_chain(
            task_type=blueprint.template.value,
            required_capabilities=blueprint.capabilities,
            constraints={
                "tier": blueprint.tier,
                "quality_weight": 0.6 if blueprint.tier == ModelTier.EXECUTIVE else 0.4,
            },
        )

        # Build agent configuration
        config = AgentConfig(
            name=blueprint.name,
            role=blueprint.role,
            goals=blueprint.goals,
            tools=blueprint.tools,
            zone=blueprint.department,
            model="",  # Will be set by LLM SDK
            temperature=0.7,
            max_concurrent_tasks=5 if blueprint.tier == ModelTier.WORKER else 3,
        )

        # Create enhanced agent
        agent = EnhancedAgent(
            config=config,
            blueprint=blueprint,
            llm_model=llm_model,
            system_prompt=template_config.get("system_prompt", ""),
        )

        await agent.initialize()

        self.logger.info(
            f"Created agent {blueprint.name} with template {blueprint.template}"
        )

        return agent


class AgentState(TypedDict):
    """State for LangGraph agent workflows"""

    messages: List[BaseMessage]
    context: Dict[str, Any]
    current_task: Optional[str]
    next_agent: Optional[str]
    results: Dict[str, Any]


class EnhancedAgent(BaseAgent):
    """Enhanced agent with LangChain/LangGraph integration"""

    def __init__(
        self,
        config: AgentConfig,
        blueprint: AgentBlueprint,
        llm_model: Optional[Any] = None,
        system_prompt: str = "",
    ):
        super().__init__(config)
        self.blueprint = blueprint
        self.llm_model = llm_model
        self.system_prompt = system_prompt

        # LangChain components
        self.memory = None
        self.agent_executor = None
        self.workflow = None
        self.tools = []

        # Enhanced capabilities
        self.skill_registry = {}
        self.collaboration_graph = {}
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "collaboration_score": 0.0,
        }

    async def initialize(self):
        """Initialize enhanced agent components"""
        await super().initialize()

        if LANGCHAIN_AVAILABLE and self.llm_model:
            # Initialize memory
            self.memory = ConversationBufferMemory(
                return_messages=True, memory_key="chat_history"
            )

            # Build tools
            await self._build_tools()

            # Create agent workflow
            self._build_workflow()

            self.logger.info(f"Enhanced agent {self.name} initialized with LangChain")

    async def _build_tools(self):
        """Build LangChain tools from agent tools"""

        # Convert BoarderframeOS tools to LangChain tools
        for tool_name in self.config.tools:
            if tool_name == "mcp_filesystem":
                self.tools.append(
                    StructuredTool(
                        name="filesystem",
                        description="Access and modify files in the system",
                        func=self._filesystem_tool,
                        coroutine=self._filesystem_tool_async,
                    )
                )
            elif tool_name == "mcp_database":
                self.tools.append(
                    StructuredTool(
                        name="database",
                        description="Query and update database",
                        func=self._database_tool,
                        coroutine=self._database_tool_async,
                    )
                )
            # Add more tool conversions as needed

    def _build_workflow(self):
        """Build LangGraph workflow"""

        if not LANGCHAIN_AVAILABLE:
            return

        # Create workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("process", self._process_node)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("collaborate", self._collaborate_node)
        workflow.add_node("complete", self._complete_node)

        # Add edges
        workflow.set_entry_point("process")

        workflow.add_conditional_edges(
            "process",
            self._should_use_tools,
            {"tools": "tools", "collaborate": "collaborate", "complete": "complete"},
        )

        workflow.add_edge("tools", "process")
        workflow.add_edge("collaborate", "process")
        workflow.add_edge("complete", END)

        self.workflow = workflow.compile()

    async def _process_node(self, state: AgentState) -> AgentState:
        """Main processing node"""

        if not self.llm_model:
            return state

        # Build prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        # Create chain
        chain = prompt | self.llm_model

        # Process
        response = await chain.ainvoke(
            {
                "chat_history": state.get("messages", []),
                "input": state.get("current_task", ""),
            }
        )

        state["messages"].append(response)

        return state

    def _should_use_tools(self, state: AgentState) -> str:
        """Decide next step in workflow"""

        last_message = state["messages"][-1] if state["messages"] else None

        if not last_message:
            return "complete"

        # Simple logic - enhance based on needs
        content = str(last_message.content).lower()

        if any(
            tool_word in content for tool_word in ["search", "find", "look", "check"]
        ):
            return "tools"
        elif any(
            collab_word in content for collab_word in ["ask", "delegate", "assign"]
        ):
            return "collaborate"
        else:
            return "complete"

    async def _collaborate_node(self, state: AgentState) -> AgentState:
        """Handle collaboration with other agents"""

        # Identify target agent
        target_agent = state.get("next_agent")

        if target_agent:
            # Send message via message bus
            from core.message_bus import send_task_request

            correlation_id = await send_task_request(
                from_agent=self.name,
                to_agent=target_agent,
                task={
                    "type": "collaboration",
                    "content": state.get("current_task", ""),
                    "context": state.get("context", {}),
                },
                priority=MessagePriority.NORMAL,
            )

            state["results"]["collaboration_id"] = correlation_id

        return state

    async def _complete_node(self, state: AgentState) -> AgentState:
        """Complete task and update metrics"""

        self.performance_metrics["tasks_completed"] += 1

        return state

    # Tool implementations
    async def _filesystem_tool_async(self, path: str, operation: str = "read") -> str:
        """Filesystem tool implementation"""
        # Implement filesystem operations
        return f"Filesystem {operation} on {path}"

    def _filesystem_tool(self, path: str, operation: str = "read") -> str:
        """Sync wrapper for filesystem tool"""
        return asyncio.run(self._filesystem_tool_async(path, operation))

    async def _database_tool_async(self, query: str) -> str:
        """Database tool implementation"""
        # Implement database operations
        return f"Database query: {query}"

    def _database_tool(self, query: str) -> str:
        """Sync wrapper for database tool"""
        return asyncio.run(self._database_tool_async(query))

    # Skill management
    def register_skill(self, skill_name: str, skill_func: Callable):
        """Register a new skill for the agent"""
        self.skill_registry[skill_name] = skill_func
        self.logger.info(f"Registered skill: {skill_name}")

    async def execute_skill(self, skill_name: str, *args, **kwargs) -> Any:
        """Execute a registered skill"""

        if skill_name not in self.skill_registry:
            raise ValueError(f"Skill {skill_name} not found")

        skill_func = self.skill_registry[skill_name]

        if asyncio.iscoroutinefunction(skill_func):
            return await skill_func(*args, **kwargs)
        else:
            return skill_func(*args, **kwargs)

    # Enhanced think method
    async def think(self) -> str:
        """Enhanced thinking with LangChain reasoning"""

        if self.workflow and self.current_context:
            # Use workflow for complex reasoning
            state = AgentState(
                messages=[],
                context=self.current_context,
                current_task="What should I do next?",
                next_agent=None,
                results={},
            )

            result = await self.workflow.ainvoke(state)

            if result["messages"]:
                return str(result["messages"][-1].content)

        # Fallback to base implementation
        return await super().think()


class AgentSwarmOrchestrator:
    """Orchestrator for managing agent swarms"""

    def __init__(self):
        self.agents: Dict[str, EnhancedAgent] = {}
        self.swarm_patterns = {}
        self.logger = logging.getLogger("swarm_orchestrator")

    def register_agent(self, agent: EnhancedAgent):
        """Register agent in swarm"""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent {agent.name} in swarm")

    async def create_swarm_pattern(
        self, pattern_name: str, agents: List[str], workflow_type: str = "sequential"
    ):
        """Create a swarm collaboration pattern"""

        if workflow_type == "sequential":
            # Agents work in sequence
            pattern = {
                "type": "sequential",
                "agents": agents,
                "flow": [(agents[i], agents[i + 1]) for i in range(len(agents) - 1)],
            }
        elif workflow_type == "parallel":
            # Agents work in parallel
            pattern = {
                "type": "parallel",
                "agents": agents,
                "coordinator": agents[0] if agents else None,
            }
        elif workflow_type == "hierarchical":
            # Tree structure with delegation
            pattern = {
                "type": "hierarchical",
                "root": agents[0] if agents else None,
                "children": {agents[0]: agents[1:]} if len(agents) > 1 else {},
            }
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        self.swarm_patterns[pattern_name] = pattern

    async def execute_swarm_task(
        self, pattern_name: str, task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task using swarm pattern"""

        pattern = self.swarm_patterns.get(pattern_name)
        if not pattern:
            raise ValueError(f"Pattern {pattern_name} not found")

        results = {}

        if pattern["type"] == "sequential":
            # Execute sequentially
            current_output = task
            for agent_name in pattern["agents"]:
                agent = self.agents.get(agent_name)
                if agent:
                    output = await agent.process_task(current_output)
                    results[agent_name] = output
                    current_output = output

        elif pattern["type"] == "parallel":
            # Execute in parallel
            tasks = []
            for agent_name in pattern["agents"]:
                agent = self.agents.get(agent_name)
                if agent:
                    tasks.append(agent.process_task(task))

            outputs = await asyncio.gather(*tasks)
            for agent_name, output in zip(pattern["agents"], outputs):
                results[agent_name] = output

        elif pattern["type"] == "hierarchical":
            # Execute hierarchically
            root_agent = self.agents.get(pattern["root"])
            if root_agent:
                results = await self._execute_hierarchical(
                    root_agent, pattern["children"], task
                )

        return results

    async def _execute_hierarchical(
        self, agent: EnhancedAgent, children: Dict[str, List[str]], task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute hierarchical pattern"""

        # Root processes first
        root_output = await agent.process_task(task)
        results = {agent.name: root_output}

        # Delegate to children
        child_names = children.get(agent.name, [])
        if child_names:
            child_tasks = []
            for child_name in child_names:
                child_agent = self.agents.get(child_name)
                if child_agent:
                    child_tasks.append(
                        self._execute_hierarchical(child_agent, children, root_output)
                    )

            child_results = await asyncio.gather(*child_tasks)
            for child_result in child_results:
                results.update(child_result)

        return results


class AgentDevelopmentKit:
    """Main ADK interface"""

    def __init__(self):
        self.factory = AgentFactory()
        self.orchestrator = AgentSwarmOrchestrator()
        self.templates = {}
        self.logger = logging.getLogger("adk")

    async def create_agent_from_template(
        self, name: str, template: AgentTemplate, department: str, **kwargs
    ) -> EnhancedAgent:
        """Create agent from pre-defined template"""

        blueprint = AgentBlueprint(
            name=name,
            role=kwargs.get("role", f"{template.value} agent"),
            template=template,
            department=department,
            tier=kwargs.get("tier", ModelTier.SPECIALIST),
            goals=kwargs.get("goals", []),
            tools=kwargs.get("tools", ["mcp_filesystem"]),
            capabilities=kwargs.get("capabilities", [ModelCapability.CHAT]),
        )

        agent = await self.factory.create_agent(blueprint)
        self.orchestrator.register_agent(agent)

        return agent

    async def create_custom_agent(self, blueprint: AgentBlueprint) -> EnhancedAgent:
        """Create agent from custom blueprint"""

        agent = await self.factory.create_agent(blueprint)
        self.orchestrator.register_agent(agent)

        return agent

    def create_swarm(
        self, name: str, agents: List[str], pattern: str = "sequential"
    ) -> None:
        """Create agent swarm"""

        asyncio.create_task(
            self.orchestrator.create_swarm_pattern(name, agents, pattern)
        )

    async def execute_swarm_task(
        self, swarm_name: str, task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task with agent swarm"""

        return await self.orchestrator.execute_swarm_task(swarm_name, task)

    def export_agent_config(self, agent_name: str, path: str):
        """Export agent configuration"""

        agent = self.orchestrator.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")

        config = {
            "name": agent.name,
            "blueprint": {
                "template": agent.blueprint.template.value,
                "department": agent.blueprint.department,
                "tier": agent.blueprint.tier.value,
                "goals": agent.blueprint.goals,
                "tools": agent.blueprint.tools,
                "capabilities": [cap.value for cap in agent.blueprint.capabilities],
            },
            "performance": agent.performance_metrics,
        }

        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def import_agent_config(self, path: str) -> AgentBlueprint:
        """Import agent configuration"""

        with open(path, "r") as f:
            config = yaml.safe_load(f)

        blueprint_data = config["blueprint"]

        return AgentBlueprint(
            name=config["name"],
            role=f"{blueprint_data['template']} agent",
            template=AgentTemplate(blueprint_data["template"]),
            department=blueprint_data["department"],
            tier=ModelTier(blueprint_data["tier"]),
            goals=blueprint_data["goals"],
            tools=blueprint_data["tools"],
            capabilities=[
                ModelCapability(cap) for cap in blueprint_data["capabilities"]
            ],
        )


# Singleton instance
_adk_instance = None


def get_adk() -> AgentDevelopmentKit:
    """Get singleton ADK instance"""
    global _adk_instance
    if _adk_instance is None:
        _adk_instance = AgentDevelopmentKit()
    return _adk_instance


# Example usage
async def example_adk_usage():
    """Example of using the Agent Development Kit"""

    adk = get_adk()

    # Create a research agent
    researcher = await adk.create_agent_from_template(
        name="market_researcher",
        template=AgentTemplate.RESEARCHER,
        department="Strategy",
        goals=["Research market trends", "Analyze competitors"],
        tier=ModelTier.SPECIALIST,
    )

    # Create a coder agent
    coder = await adk.create_agent_from_template(
        name="backend_developer",
        template=AgentTemplate.CODER,
        department="Engineering",
        goals=["Implement features", "Fix bugs", "Optimize performance"],
        tier=ModelTier.SPECIALIST,
    )

    # Create a coordinator
    coordinator = await adk.create_agent_from_template(
        name="project_manager",
        template=AgentTemplate.COORDINATOR,
        department="Management",
        goals=["Coordinate tasks", "Track progress", "Report status"],
        tier=ModelTier.DEPARTMENT,
    )

    # Create a swarm for project execution
    adk.create_swarm(
        "project_swarm",
        ["project_manager", "market_researcher", "backend_developer"],
        pattern="hierarchical",
    )

    # Execute a project task
    result = await adk.execute_swarm_task(
        "project_swarm",
        {
            "task": "Develop new feature based on market research",
            "deadline": "2 weeks",
            "requirements": ["User feedback integration", "Performance optimization"],
        },
    )

    print(f"Project result: {result}")


if __name__ == "__main__":
    asyncio.run(example_adk_usage())
