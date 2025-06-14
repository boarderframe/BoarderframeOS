"""
Agent Workflows - LangGraph integration for stateful agent workflows
Provides advanced workflow orchestration with state management
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
from uuid import uuid4

# LangGraph imports
try:
    from langchain.tools import Tool
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
    from langgraph.checkpoint import MemorySaver
    from langgraph.graph import END, Graph, StateGraph
    from langgraph.prebuilt import ToolExecutor

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph not available - workflow features disabled")

from .enhanced_agent_base import EnhancedBaseAgent
from .message_bus import MessagePriority, message_bus


class WorkflowState(TypedDict):
    """State for agent workflows"""

    messages: Sequence[BaseMessage]
    current_agent: str
    task_id: str
    context: Dict[str, Any]
    results: Dict[str, Any]
    next_action: str
    completed: bool


@dataclass
class WorkflowConfig:
    """Configuration for agent workflows"""

    name: str
    description: str
    agents: List[str]  # List of agent names involved
    steps: List[Dict[str, Any]]  # Workflow steps definition
    timeout_seconds: int = 300
    max_iterations: int = 10
    checkpoint_enabled: bool = True


class WorkflowStep(Enum):
    """Standard workflow steps"""

    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    REVIEW = "review"
    DELEGATE = "delegate"
    COMPLETE = "complete"


class AgentWorkflow:
    """Manages stateful agent workflows using LangGraph"""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.workflow_id = str(uuid4())
        self.logger = logging.getLogger(f"Workflow-{config.name}")
        self.graph: Optional[StateGraph] = None
        self.checkpointer = MemorySaver() if config.checkpoint_enabled else None

        if LANGGRAPH_AVAILABLE:
            self._build_workflow_graph()

    def _build_workflow_graph(self):
        """Build the workflow graph"""
        # Create state graph
        self.graph = StateGraph(WorkflowState)

        # Add nodes for each workflow step
        for step in self.config.steps:
            step_name = step["name"]
            step_type = step["type"]

            if step_type == WorkflowStep.ANALYZE.value:
                self.graph.add_node(step_name, self._analyze_node)
            elif step_type == WorkflowStep.PLAN.value:
                self.graph.add_node(step_name, self._plan_node)
            elif step_type == WorkflowStep.EXECUTE.value:
                self.graph.add_node(step_name, self._execute_node)
            elif step_type == WorkflowStep.REVIEW.value:
                self.graph.add_node(step_name, self._review_node)
            elif step_type == WorkflowStep.DELEGATE.value:
                self.graph.add_node(step_name, self._delegate_node)
            else:
                # Custom node
                self.graph.add_node(
                    step_name, lambda state: self._custom_node(state, step)
                )

        # Add edges based on workflow definition
        self._add_workflow_edges()

        # Set entry point
        if self.config.steps:
            self.graph.set_entry_point(self.config.steps[0]["name"])

    def _add_workflow_edges(self):
        """Add edges between workflow nodes"""
        for i, step in enumerate(self.config.steps):
            step_name = step["name"]

            # Add conditional edges based on step configuration
            if "conditions" in step:
                condition_map = {}
                for condition in step["conditions"]:
                    condition_map[condition["result"]] = condition["next_step"]

                self.graph.add_conditional_edges(
                    step_name,
                    lambda state, cm=condition_map: self._evaluate_condition(state, cm),
                    condition_map,
                )
            elif i < len(self.config.steps) - 1:
                # Default edge to next step
                next_step = self.config.steps[i + 1]["name"]
                self.graph.add_edge(step_name, next_step)
            else:
                # Last step goes to END
                self.graph.add_edge(step_name, END)

    async def _analyze_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze the current situation"""
        current_agent = state["current_agent"]

        # Send analysis request to agent
        response = await self._send_to_agent(
            current_agent,
            {
                "action": "analyze",
                "context": state["context"],
                "messages": [msg.content for msg in state["messages"][-5:]],
            },
        )

        # Update state
        state["results"]["analysis"] = response
        state["messages"].append(AIMessage(content=f"Analysis complete: {response}"))

        return state

    async def _plan_node(self, state: WorkflowState) -> WorkflowState:
        """Create a plan based on analysis"""
        current_agent = state["current_agent"]

        # Send planning request to agent
        response = await self._send_to_agent(
            current_agent,
            {
                "action": "plan",
                "analysis": state["results"].get("analysis", {}),
                "context": state["context"],
            },
        )

        # Update state
        state["results"]["plan"] = response
        state["messages"].append(AIMessage(content=f"Plan created: {response}"))

        return state

    async def _execute_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the plan"""
        current_agent = state["current_agent"]
        plan = state["results"].get("plan", {})

        execution_results = []

        # Execute each step in the plan
        if isinstance(plan, dict) and "steps" in plan:
            for step in plan["steps"]:
                result = await self._send_to_agent(
                    current_agent,
                    {
                        "action": "execute_step",
                        "step": step,
                        "context": state["context"],
                    },
                )
                execution_results.append(result)

        # Update state
        state["results"]["execution"] = execution_results
        state["messages"].append(
            AIMessage(content=f"Execution complete: {len(execution_results)} steps")
        )

        return state

    async def _review_node(self, state: WorkflowState) -> WorkflowState:
        """Review the execution results"""
        current_agent = state["current_agent"]

        # Send review request
        response = await self._send_to_agent(
            current_agent,
            {
                "action": "review",
                "execution_results": state["results"].get("execution", []),
                "original_plan": state["results"].get("plan", {}),
                "context": state["context"],
            },
        )

        # Update state
        state["results"]["review"] = response
        state["messages"].append(AIMessage(content=f"Review complete: {response}"))

        # Check if workflow should complete
        if isinstance(response, dict) and response.get("satisfied", False):
            state["completed"] = True

        return state

    async def _delegate_node(self, state: WorkflowState) -> WorkflowState:
        """Delegate to another agent"""
        delegation_info = state["context"].get("delegation", {})
        target_agent = delegation_info.get("target_agent")

        if target_agent and target_agent in self.config.agents:
            # Switch current agent
            state["current_agent"] = target_agent

            # Send delegation request
            response = await self._send_to_agent(
                target_agent,
                {
                    "action": "accept_delegation",
                    "task": delegation_info.get("task", {}),
                    "from_agent": state["current_agent"],
                    "context": state["context"],
                },
            )

            state["results"]["delegation"] = response
            state["messages"].append(
                AIMessage(content=f"Delegated to {target_agent}: {response}")
            )

        return state

    async def _custom_node(
        self, state: WorkflowState, step_config: Dict
    ) -> WorkflowState:
        """Handle custom workflow nodes"""
        current_agent = state["current_agent"]

        # Execute custom action
        response = await self._send_to_agent(
            current_agent,
            {
                "action": step_config.get("action", "custom"),
                "params": step_config.get("params", {}),
                "context": state["context"],
            },
        )

        # Update state
        state["results"][step_config["name"]] = response
        state["messages"].append(
            AIMessage(content=f"{step_config['name']} complete: {response}")
        )

        return state

    def _evaluate_condition(
        self, state: WorkflowState, condition_map: Dict[str, str]
    ) -> str:
        """Evaluate conditions to determine next step"""
        # Simple evaluation based on state
        if state.get("completed", False):
            return condition_map.get("complete", END)

        # Check for specific conditions in results
        last_result = list(state["results"].values())[-1] if state["results"] else {}

        if isinstance(last_result, dict):
            if last_result.get("error"):
                return condition_map.get("error", END)
            elif last_result.get("needs_delegation"):
                return condition_map.get("delegate", END)
            elif last_result.get("success"):
                return condition_map.get("success", END)

        # Default condition
        return condition_map.get("default", END)

    async def _send_to_agent(
        self, agent_name: str, task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send task to an agent via message bus"""
        try:
            # Create a unique correlation ID
            correlation_id = f"{self.workflow_id}-{uuid4()}"

            # Send task request
            await message_bus.send_message(
                {
                    "from_agent": f"workflow-{self.config.name}",
                    "to_agent": agent_name,
                    "message_type": "task_request",
                    "content": task,
                    "priority": MessagePriority.HIGH,
                    "correlation_id": correlation_id,
                }
            )

            # Wait for response (with timeout)
            response = await asyncio.wait_for(
                message_bus.wait_for_response(correlation_id), timeout=30
            )

            if response:
                return response.content
            else:
                return {"error": "No response from agent"}

        except asyncio.TimeoutError:
            return {"error": "Agent response timeout"}
        except Exception as e:
            return {"error": f"Failed to communicate with agent: {e}"}

    async def run(
        self, initial_context: Dict[str, Any], starting_agent: str
    ) -> Dict[str, Any]:
        """Run the workflow"""
        if not LANGGRAPH_AVAILABLE or not self.graph:
            return {"error": "LangGraph not available", "workflow_id": self.workflow_id}

        try:
            # Initialize state
            initial_state: WorkflowState = {
                "messages": [
                    HumanMessage(content=f"Starting workflow: {self.config.name}")
                ],
                "current_agent": starting_agent,
                "task_id": str(uuid4()),
                "context": initial_context,
                "results": {},
                "next_action": "",
                "completed": False,
            }

            # Compile the graph
            app = self.graph.compile(checkpointer=self.checkpointer)

            # Run the workflow
            config = (
                {"configurable": {"thread_id": self.workflow_id}}
                if self.checkpointer
                else {}
            )

            final_state = await app.ainvoke(initial_state, config)

            return {
                "workflow_id": self.workflow_id,
                "completed": final_state.get("completed", False),
                "results": final_state.get("results", {}),
                "messages": [msg.content for msg in final_state.get("messages", [])],
            }

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {"error": str(e), "workflow_id": self.workflow_id}


class WorkflowOrchestrator:
    """Manages multiple agent workflows"""

    def __init__(self):
        self.workflows: Dict[str, AgentWorkflow] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("WorkflowOrchestrator")

    def create_workflow(self, config: WorkflowConfig) -> AgentWorkflow:
        """Create a new workflow"""
        workflow = AgentWorkflow(config)
        self.workflows[workflow.workflow_id] = workflow

        self.workflow_history.append(
            {
                "workflow_id": workflow.workflow_id,
                "name": config.name,
                "created_at": datetime.now().isoformat(),
                "status": "created",
            }
        )

        return workflow

    async def run_workflow(
        self, workflow_id: str, initial_context: Dict[str, Any], starting_agent: str
    ) -> Dict[str, Any]:
        """Run a specific workflow"""
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}

        workflow = self.workflows[workflow_id]

        # Update history
        self.workflow_history.append(
            {
                "workflow_id": workflow_id,
                "started_at": datetime.now().isoformat(),
                "status": "running",
            }
        )

        # Run workflow
        result = await workflow.run(initial_context, starting_agent)

        # Update history
        self.workflow_history.append(
            {
                "workflow_id": workflow_id,
                "completed_at": datetime.now().isoformat(),
                "status": "completed" if not result.get("error") else "failed",
                "result_summary": result,
            }
        )

        return result

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow"""
        # Get latest status from history
        workflow_events = [
            event
            for event in self.workflow_history
            if event.get("workflow_id") == workflow_id
        ]

        if not workflow_events:
            return {"error": "Workflow not found"}

        latest_event = workflow_events[-1]
        return {
            "workflow_id": workflow_id,
            "status": latest_event.get("status"),
            "last_updated": latest_event.get("completed_at")
            or latest_event.get("started_at")
            or latest_event.get("created_at"),
        }


# Pre-defined workflow templates
WORKFLOW_TEMPLATES = {
    "customer_onboarding": WorkflowConfig(
        name="customer_onboarding",
        description="Onboard a new customer with multiple agent collaboration",
        agents=["david", "solomon", "support_agent"],
        steps=[
            {
                "name": "analyze_request",
                "type": WorkflowStep.ANALYZE.value,
                "description": "Analyze customer requirements",
            },
            {
                "name": "create_plan",
                "type": WorkflowStep.PLAN.value,
                "description": "Create onboarding plan",
            },
            {
                "name": "setup_account",
                "type": WorkflowStep.EXECUTE.value,
                "description": "Execute account setup",
            },
            {
                "name": "review_setup",
                "type": WorkflowStep.REVIEW.value,
                "description": "Review and verify setup",
                "conditions": [
                    {"result": "success", "next_step": END},
                    {"result": "error", "next_step": "delegate_to_support"},
                ],
            },
            {
                "name": "delegate_to_support",
                "type": WorkflowStep.DELEGATE.value,
                "description": "Delegate issues to support team",
            },
        ],
    ),
    "agent_creation": WorkflowConfig(
        name="agent_creation",
        description="Create a new agent with Adam and Eve collaboration",
        agents=["adam", "eve", "bezalel"],
        steps=[
            {
                "name": "design_agent",
                "type": WorkflowStep.PLAN.value,
                "description": "Design new agent architecture",
            },
            {
                "name": "implement_agent",
                "type": WorkflowStep.EXECUTE.value,
                "description": "Implement agent code",
            },
            {
                "name": "evolve_capabilities",
                "type": WorkflowStep.DELEGATE.value,
                "description": "Delegate to Eve for evolution",
            },
            {
                "name": "test_agent",
                "type": WorkflowStep.EXECUTE.value,
                "description": "Test agent functionality",
            },
            {
                "name": "deploy_agent",
                "type": WorkflowStep.COMPLETE.value,
                "description": "Deploy agent to production",
            },
        ],
    ),
}


# Global workflow orchestrator
workflow_orchestrator = WorkflowOrchestrator()
