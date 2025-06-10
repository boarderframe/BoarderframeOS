"""
Agent Cortex-powered LangGraph Orchestrator
Multi-agent workflow orchestration with intelligent model selection
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from enum import Enum

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool

# BoarderframeOS imports
from .agent_cortex import AgentCortex, AgentRequest, get_agent_cortex_instance
from .message_bus import message_bus, MessageType, MessagePriority


class WorkflowType(Enum):
    """Types of agent workflows"""
    USER_CHAT = "user_chat"
    AGENT_HANDOFF = "agent_handoff"
    SWARM_COORDINATION = "swarm_coordination"
    DEPARTMENT_TASK = "department_task"
    AGENT_CREATION = "agent_creation"


class BoarderframeState(TypedDict):
    """Complete state for BoarderframeOS agent workflows"""
    # Core request data
    user_request: str
    conversation_id: str
    workflow_type: str
    
    # Agent chain state
    current_agent: str
    agent_chain: List[str]
    reasoning_chain: List[Dict[str, Any]]
    
    # Context and data
    context: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    task_context: Dict[str, Any]
    
    # Agent Cortex integration
    cortex_selections: List[Dict[str, Any]]
    performance_tracking: List[str]
    
    # MCP tools and capabilities
    available_tools: List[str]
    tool_results: List[Dict[str, Any]]
    
    # Department and handoff
    department: Optional[str]
    handoff_context: Optional[Dict[str, Any]]
    
    # Results and completion
    final_response: str
    completion_status: str
    quality_score: float
    
    # Metadata
    timestamp: str
    processing_time: float


class AgentCortexLangGraphOrchestrator:
    """LangGraph orchestrator powered by Agent Cortex"""
    
    def __init__(self):
        self.agent_cortex = None  # Will be initialized async
        self.graph = None
        self.memory = MemorySaver()
        self.active_workflows = {}
        self.logger = logging.getLogger("agent_cortex_langgraph_orchestrator")
        
        # Agent configuration
        self.agent_configs = self._load_agent_configs()
        
        # MCP tools registry
        self.mcp_tools = self._setup_mcp_tools()
        
    async def initialize(self):
        """Initialize the orchestrator"""
        self.agent_cortex = await get_agent_cortex_instance()
        self.graph = await self._create_agent_cortex_powered_graph()
        self.logger.info("🕸️ Agent Cortex LangGraph Orchestrator initialized")
    
    def _load_agent_configs(self) -> Dict[str, Dict]:
        """Load agent configurations"""
        return {
            "solomon": {
                "role": "Chief of Staff - Digital Twin",
                "system_prompt": """You are Solomon, the Chief of Staff and digital twin for BoarderframeOS. 
                You provide strategic analysis, business intelligence, and system coordination.
                Your primary goals are strategic planning, business optimization, and intelligent routing.""",
                "tools": ["analytics", "customer", "registry"],
                "complexity_baseline": 7
            },
            "david": {
                "role": "CEO - Executive Decision Maker", 
                "system_prompt": """You are David, the CEO of BoarderframeOS.
                You make executive decisions, drive revenue optimization, and manage strategic direction.
                Your focus is on business growth, operational efficiency, and leadership.""",
                "tools": ["analytics", "payment", "customer", "registry"],
                "complexity_baseline": 8
            },
            "adam": {
                "role": "Agent Creator - The Factory",
                "system_prompt": """You are Adam, the Agent Creator for BoarderframeOS.
                You design, create, and deploy new AI agents based on specifications and requirements.
                Your expertise is in agent architecture, capability design, and system evolution.""",
                "tools": ["filesystem", "registry", "database"],
                "complexity_baseline": 9
            }
        }
    
    def _setup_mcp_tools(self) -> Dict[str, Any]:
        """Setup MCP tools for agents"""
        
        @tool
        async def analytics_tool(query: str) -> str:
            """Get analytics data and insights"""
            # TODO: Integrate with MCP analytics server
            return f"Analytics result for: {query}"
        
        @tool
        async def customer_tool(action: str, data: Dict = None) -> str:
            """Customer management operations"""
            # TODO: Integrate with MCP customer server
            return f"Customer action {action} completed"
        
        @tool
        async def registry_tool(operation: str, agent_data: Dict = None) -> str:
            """Agent registry operations"""
            # TODO: Integrate with MCP registry server
            return f"Registry operation {operation} completed"
        
        @tool
        async def filesystem_tool(action: str, path: str, content: str = None) -> str:
            """Filesystem operations for agent creation"""
            # TODO: Integrate with MCP filesystem server
            return f"Filesystem {action} on {path} completed"
        
        @tool
        async def database_tool(query: str, data: Dict = None) -> str:
            """Database operations"""
            # TODO: Integrate with MCP database server
            return f"Database query completed: {query}"
        
        return {
            "analytics": analytics_tool,
            "customer": customer_tool,
            "registry": registry_tool,
            "filesystem": filesystem_tool,
            "database": database_tool
        }
    
    async def _create_agent_cortex_powered_graph(self) -> StateGraph:
        """Create the main LangGraph with Agent Cortex intelligence"""
        
        # Create state graph
        graph = StateGraph(BoarderframeState)
        
        # Add core agent nodes
        graph.add_node("solomon", self._agent_cortex_solomon_node)
        graph.add_node("david", self._agent_cortex_david_node)
        graph.add_node("adam", self._agent_cortex_adam_node)
        
        # Add orchestration nodes
        graph.add_node("route_request", self._route_initial_request)
        graph.add_node("department_router", self._route_to_department)
        graph.add_node("specialist_swarm", self._create_specialist_swarm)
        graph.add_node("finalize_response", self._finalize_response)
        
        # Add workflow routing
        graph.add_edge(START, "route_request")
        
        graph.add_conditional_edges(
            "route_request",
            self._determine_initial_route,
            {
                "solomon": "solomon",
                "david": "david", 
                "adam": "adam",
                "department": "department_router"
            }
        )
        
        graph.add_conditional_edges(
            "solomon",
            self._solomon_routing_decision,
            {
                "david": "david",
                "department": "department_router",
                "complete": "finalize_response"
            }
        )
        
        graph.add_conditional_edges(
            "david",
            self._david_routing_decision,
            {
                "adam": "adam",
                "department": "department_router",
                "swarm": "specialist_swarm",
                "complete": "finalize_response"
            }
        )
        
        graph.add_conditional_edges(
            "adam",
            self._adam_routing_decision,
            {
                "department": "department_router",
                "complete": "finalize_response"
            }
        )
        
        graph.add_edge("department_router", "finalize_response")
        graph.add_edge("specialist_swarm", "finalize_response")
        graph.add_edge("finalize_response", END)
        
        # Compile with memory
        return graph.compile(checkpointer=self.memory)
    
    async def _agent_cortex_solomon_node(self, state: BoarderframeState) -> BoarderframeState:
        """Solomon node with Agent Cortex optimization"""
        
        self.logger.info(f"Processing with Solomon: {state.get('user_request', '')[:100]}")
        
        # Create Agent Cortex request
        cortex_request = AgentRequest(
            agent_name="solomon",
            task_type="strategic_analysis",
            context=state,
            complexity=await self._assess_solomon_complexity(state),
            quality_requirements=0.9,
            conversation_id=state.get("conversation_id")
        )
        
        # Get optimal model from Agent Cortex
        agent_cortex_response = await self.agent_cortex.process_agent_request(cortex_request)
        
        # Create strategic analysis prompt for Solomon
        solomon_prompt = f"""
        {self.agent_configs["solomon"]["system_prompt"]}
        
        User Request: {state['user_request']}
        
        Context: {json.dumps(state.get('context', {}), indent=2)}
        
        Available Tools: {', '.join(self.agent_configs["solomon"]["tools"])}
        
        As Solomon, provide comprehensive strategic analysis including:
        1. Business impact assessment
        2. Resource allocation recommendations  
        3. Risk analysis and mitigation strategies
        4. Routing recommendations (if applicable)
        5. Next steps and priorities
        
        Be specific, actionable, and strategic in your analysis.
        """
        
        # Execute Solomon's processing with Agent Cortex-selected model
        try:
            solomon_response = await agent_cortex_response.llm.generate(solomon_prompt)
            
            # Report performance to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                agent_name="solomon",
                response=solomon_response,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Solomon processing error: {e}")
            solomon_response = f"I apologize, but I encountered an issue processing your request: {str(e)}"
            
            # Report error to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                agent_name="solomon",
                response=solomon_response,
                success=False
            )
        
        # Update state
        state["current_agent"] = "solomon"
        state["agent_chain"] = state.get("agent_chain", []) + ["solomon"]
        state["reasoning_chain"] = state.get("reasoning_chain", []) + [{
            "agent": "solomon",
            "analysis": solomon_response,
            "agent_cortex_selection": agent_cortex_response.selection.selected_model,
            "timestamp": datetime.now().isoformat()
        }]
        state["cortex_selections"] = state.get("cortex_selections", []) + [
            agent_cortex_response.selection.__dict__
        ]
        state["performance_tracking"] = state.get("performance_tracking", []) + [
            agent_cortex_response.tracking_id
        ]
        
        return state
    
    async def _agent_cortex_david_node(self, state: BoarderframeState) -> BoarderframeState:
        """David node with Agent Cortex optimization"""
        
        self.logger.info(f"Processing with David: {state.get('user_request', '')[:100]}")
        
        # Create Agent Cortex request
        cortex_request = AgentRequest(
            agent_name="david",
            task_type="executive_decision",
            context=state,
            complexity=await self._assess_david_complexity(state),
            quality_requirements=0.9,
            conversation_id=state.get("conversation_id")
        )
        
        # Get optimal model from Agent Cortex
        agent_cortex_response = await self.agent_cortex.process_agent_request(cortex_request)
        
        # Include Solomon's analysis if available
        solomon_analysis = ""
        reasoning_chain = state.get("reasoning_chain", [])
        for entry in reasoning_chain:
            if entry["agent"] == "solomon":
                solomon_analysis = entry["analysis"]
                break
        
        # Create executive decision prompt for David
        david_prompt = f"""
        {self.agent_configs["david"]["system_prompt"]}
        
        User Request: {state['user_request']}
        
        Solomon's Analysis: {solomon_analysis}
        
        Context: {json.dumps(state.get('context', {}), indent=2)}
        
        Available Tools: {', '.join(self.agent_configs["david"]["tools"])}
        
        As David, the CEO, make executive decisions based on Solomon's analysis:
        
        1. Executive assessment of the strategic analysis
        2. Business growth and revenue implications  
        3. Operational efficiency considerations
        4. Resource allocation decisions
        5. Implementation strategy
        6. Success metrics and timeline
        
        Determine if this requires:
        - Direct CEO action
        - Departmental delegation  
        - Agent creation (route to Adam)
        - Multi-agent coordination
        
        Provide clear executive direction and next steps.
        """
        
        # Execute David's processing with Agent Cortex-selected model
        try:
            david_response = await agent_cortex_response.llm.generate(david_prompt)
            
            # Report performance to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                agent_name="david",
                response=david_response,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"David processing error: {e}")
            david_response = f"I encountered an issue making the executive decision: {str(e)}"
            
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                agent_name="david",
                response=david_response,
                success=False
            )
        
        # Update state
        state["current_agent"] = "david"
        state["agent_chain"] = state.get("agent_chain", []) + ["david"]
        state["reasoning_chain"] = state.get("reasoning_chain", []) + [{
            "agent": "david",
            "decision": david_response,
            "agent_cortex_selection": agent_cortex_response.selection.selected_model,
            "timestamp": datetime.now().isoformat()
        }]
        state["cortex_selections"] = state.get("cortex_selections", []) + [
            agent_cortex_response.selection.__dict__
        ]
        state["performance_tracking"] = state.get("performance_tracking", []) + [
            agent_cortex_response.tracking_id
        ]
        
        return state
    
    async def _agent_cortex_adam_node(self, state: BoarderframeState) -> BoarderframeState:
        """Adam node with Agent Cortex optimization for agent creation"""
        
        self.logger.info(f"Processing with Adam: {state.get('user_request', '')[:100]}")
        
        # Create Agent Cortex request
        cortex_request = AgentRequest(
            agent_name="adam",
            task_type="agent_creation",
            context=state,
            complexity=9,  # Agent creation is always high complexity
            quality_requirements=0.95,
            conversation_id=state.get("conversation_id")
        )
        
        # Get optimal model from Agent Cortex
        agent_cortex_response = await self.agent_cortex.process_agent_request(cortex_request)
        
        # Create agent creation analysis prompt for Adam
        adam_prompt = f"""
        {self.agent_configs["adam"]["system_prompt"]}
        
        User Request: {state['user_request']}
        
        Previous Analysis: {json.dumps(state.get('reasoning_chain', []), indent=2)}
        
        Available Tools: {', '.join(self.agent_configs["adam"]["tools"])}
        
        As Adam, the Agent Creator, analyze this request for agent creation needs:
        
        1. Agent Requirements Analysis:
           - Is a new agent actually needed?
           - What specific capabilities are required?
           - How does this fit into existing agent ecosystem?
        
        2. Agent Specifications (if needed):
           - Agent role and primary function
           - Required tools and MCP servers
           - Integration requirements with existing agents
           - Performance targets and success metrics
           - Department assignment and hierarchy
        
        3. Implementation Strategy:
           - Technical architecture decisions
           - Development timeline and phases
           - Testing and validation approach
           - Deployment and monitoring plan
        
        4. Alternative Solutions:
           - Could existing agents handle this with enhancements?
           - Would departmental routing be more appropriate?
           - Are there workflow optimizations instead?
        
        Provide detailed technical analysis and clear recommendations.
        """
        
        # Execute Adam's processing with Agent Cortex-selected model
        try:
            adam_response = await agent_cortex_response.llm.generate(adam_prompt)
            
            # Report performance to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                agent_name="adam",
                response=adam_response,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Adam processing error: {e}")
            adam_response = f"I encountered an issue with agent creation analysis: {str(e)}"
            
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                agent_name="adam",
                response=adam_response,
                success=False
            )
        
        # Update state
        state["current_agent"] = "adam"
        state["agent_chain"] = state.get("agent_chain", []) + ["adam"]
        state["reasoning_chain"] = state.get("reasoning_chain", []) + [{
            "agent": "adam",
            "creation_analysis": adam_response,
            "agent_cortex_selection": agent_cortex_response.selection.selected_model,
            "timestamp": datetime.now().isoformat()
        }]
        state["cortex_selections"] = state.get("cortex_selections", []) + [
            agent_cortex_response.selection.__dict__
        ]
        state["performance_tracking"] = state.get("performance_tracking", []) + [
            agent_cortex_response.tracking_id
        ]
        
        return state
    
    # Routing decision functions
    async def _determine_initial_route(self, state: BoarderframeState) -> str:
        """Determine initial routing based on request"""
        
        user_request = state.get("user_request", "").lower()
        
        # Direct agent creation requests
        if any(keyword in user_request for keyword in ["create agent", "new agent", "build agent"]):
            return "adam"
        
        # Executive-level requests
        if any(keyword in user_request for keyword in ["strategy", "business", "revenue", "ceo"]):
            return "david"
        
        # Department-specific requests
        if any(keyword in user_request for keyword in ["department", "finance", "engineering"]):
            return "department"
        
        # Default to Solomon for analysis
        return "solomon"
    
    async def _solomon_routing_decision(self, state: BoarderframeState) -> str:
        """Solomon's routing decision"""
        
        reasoning_chain = state.get("reasoning_chain", [])
        solomon_analysis = ""
        
        for entry in reasoning_chain:
            if entry["agent"] == "solomon":
                solomon_analysis = entry["analysis"].lower()
                break
        
        # Route to David for executive decisions
        if any(keyword in solomon_analysis for keyword in ["executive", "ceo", "decision", "strategic"]):
            return "david"
        
        # Route to department for specific tasks
        if any(keyword in solomon_analysis for keyword in ["department", "team", "specialist"]):
            return "department"
        
        # Complete if Solomon can handle it
        return "complete"
    
    async def _david_routing_decision(self, state: BoarderframeState) -> str:
        """David's routing decision"""
        
        reasoning_chain = state.get("reasoning_chain", [])
        david_decision = ""
        
        for entry in reasoning_chain:
            if entry["agent"] == "david":
                david_decision = entry["decision"].lower()
                break
        
        # Route to Adam for agent creation
        if any(keyword in david_decision for keyword in ["create", "agent", "new capability"]):
            return "adam"
        
        # Route to department for implementation
        if any(keyword in david_decision for keyword in ["department", "implement", "execute"]):
            return "department"
        
        # Create swarm for complex tasks
        if any(keyword in david_decision for keyword in ["complex", "multi-agent", "coordination"]):
            return "swarm"
        
        # Complete if David can handle it
        return "complete"
    
    async def _adam_routing_decision(self, state: BoarderframeState) -> str:
        """Adam's routing decision"""
        
        reasoning_chain = state.get("reasoning_chain", [])
        adam_analysis = ""
        
        for entry in reasoning_chain:
            if entry["agent"] == "adam":
                adam_analysis = entry.get("creation_analysis", "").lower()
                break
        
        # Route to department if specific department needs the new agent
        if any(keyword in adam_analysis for keyword in ["department", "team", "deploy"]):
            return "department"
        
        # Complete agent creation process
        return "complete"
    
    # Node implementation functions
    async def _route_initial_request(self, state: BoarderframeState) -> BoarderframeState:
        """Initial request routing and setup"""
        
        # Initialize workflow metadata
        if not state.get("conversation_id"):
            state["conversation_id"] = str(uuid.uuid4())
        
        state["timestamp"] = datetime.now().isoformat()
        state["workflow_type"] = WorkflowType.USER_CHAT.value
        state["agent_chain"] = []
        state["reasoning_chain"] = []
        state["cortex_selections"] = []
        state["performance_tracking"] = []
        state["completion_status"] = "in_progress"
        state["quality_score"] = 0.0
        
        return state
    
    async def _route_to_department(self, state: BoarderframeState) -> BoarderframeState:
        """Route to specific department"""
        
        # Determine department based on context
        department = await self._determine_department(state)
        state["department"] = department
        
        # Simulate department processing
        department_response = f"Department {department} would handle this request: {state.get('user_request', '')}"
        
        state["reasoning_chain"] = state.get("reasoning_chain", []) + [{
            "agent": f"{department}_department",
            "response": department_response,
            "timestamp": datetime.now().isoformat()
        }]
        
        return state
    
    async def _create_specialist_swarm(self, state: BoarderframeState) -> BoarderframeState:
        """Create and coordinate specialist swarm"""
        
        # Determine required specialists
        specialists_needed = await self._determine_specialists(state)
        
        swarm_response = f"Specialist swarm created with: {', '.join(specialists_needed)}"
        
        state["reasoning_chain"] = state.get("reasoning_chain", []) + [{
            "agent": "specialist_swarm",
            "specialists": specialists_needed,
            "response": swarm_response,
            "timestamp": datetime.now().isoformat()
        }]
        
        return state
    
    async def _finalize_response(self, state: BoarderframeState) -> BoarderframeState:
        """Finalize the workflow response"""
        
        # Collect all responses from reasoning chain
        reasoning_chain = state.get("reasoning_chain", [])
        
        # Build comprehensive response
        response_parts = [
            f"Request processed through agent chain: {' → '.join(state.get('agent_chain', []))}"
        ]
        
        for entry in reasoning_chain:
            agent = entry["agent"]
            if "analysis" in entry:
                response_parts.append(f"\n**{agent.title()} Analysis:**\n{entry['analysis']}")
            elif "decision" in entry:
                response_parts.append(f"\n**{agent.title()} Decision:**\n{entry['decision']}")
            elif "creation_analysis" in entry:
                response_parts.append(f"\n**{agent.title()} Creation Analysis:**\n{entry['creation_analysis']}")
            elif "response" in entry:
                response_parts.append(f"\n**{agent.title()} Response:**\n{entry['response']}")
        
        final_response = "\n".join(response_parts)
        
        # Add Agent Cortex selection summary
        cortex_selections = state.get("cortex_selections", [])
        if cortex_selections:
            model_summary = [f"{sel['selected_model']} ({sel['provider']})" for sel in cortex_selections]
            final_response += f"\n\n**Agent Cortex Model Selections:** {', '.join(model_summary)}"
        
        state["final_response"] = final_response
        state["completion_status"] = "completed"
        state["quality_score"] = await self._assess_response_quality(state)
        state["processing_time"] = (datetime.now() - datetime.fromisoformat(state["timestamp"])).total_seconds()
        
        return state
    
    # Helper functions
    async def _assess_solomon_complexity(self, state: BoarderframeState) -> int:
        """Assess complexity for Solomon's task"""
        user_request = state.get("user_request", "")
        
        complexity = 5  # Base complexity
        
        # Increase complexity for strategic requests
        if any(keyword in user_request.lower() for keyword in ["strategy", "planning", "analysis"]):
            complexity += 2
        
        # Increase for business requests
        if any(keyword in user_request.lower() for keyword in ["business", "revenue", "growth"]):
            complexity += 1
        
        return min(complexity, 10)
    
    async def _assess_david_complexity(self, state: BoarderframeState) -> int:
        """Assess complexity for David's task"""
        user_request = state.get("user_request", "")
        
        complexity = 6  # Base complexity for CEO tasks
        
        # Increase complexity for executive decisions
        if any(keyword in user_request.lower() for keyword in ["decision", "strategic", "executive"]):
            complexity += 2
        
        # Increase for multi-department coordination
        if any(keyword in user_request.lower() for keyword in ["department", "coordination", "teams"]):
            complexity += 1
        
        return min(complexity, 10)
    
    async def _determine_department(self, state: BoarderframeState) -> str:
        """Determine which department should handle the request"""
        user_request = state.get("user_request", "").lower()
        
        if any(keyword in user_request for keyword in ["finance", "money", "revenue", "cost"]):
            return "finance"
        elif any(keyword in user_request for keyword in ["engineering", "technical", "code", "development"]):
            return "engineering"
        elif any(keyword in user_request for keyword in ["operations", "process", "workflow"]):
            return "operations"
        else:
            return "general"
    
    async def _determine_specialists(self, state: BoarderframeState) -> List[str]:
        """Determine required specialists for swarm"""
        user_request = state.get("user_request", "").lower()
        
        specialists = []
        
        if any(keyword in user_request for keyword in ["analysis", "data"]):
            specialists.append("data_analyst")
        if any(keyword in user_request for keyword in ["technical", "code"]):
            specialists.append("technical_specialist")
        if any(keyword in user_request for keyword in ["business", "strategy"]):
            specialists.append("business_specialist")
        
        return specialists if specialists else ["general_specialist"]
    
    async def _assess_response_quality(self, state: BoarderframeState) -> float:
        """Assess the quality of the final response"""
        # Simple quality assessment based on completeness
        final_response = state.get("final_response", "")
        reasoning_chain = state.get("reasoning_chain", [])
        
        quality_score = 0.5  # Base score
        
        # Quality factors
        if len(reasoning_chain) > 0:
            quality_score += 0.2
        if len(final_response) > 100:
            quality_score += 0.2
        if len(state.get("agent_chain", [])) > 1:
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    async def _report_agent_cortex_performance(self, tracking_id: str, agent_name: str, 
                                       response: str, success: bool):
        """Report performance back to Agent Cortex"""
        
        from .agent_cortex import PerformanceMetrics
        
        try:
            metrics = PerformanceMetrics(
                tracking_id=tracking_id,
                agent_name=agent_name,
                selected_model="",  # Will be filled by Cortex
                actual_cost=0.001,  # Estimated
                actual_latency=1.5,  # Estimated
                actual_quality=0.8 if success else 0.3,
                task_completion=success
            )
            
            await self.agent_cortex.report_performance(tracking_id, metrics)
            
        except Exception as e:
            self.logger.error(f"Error reporting Agent Cortex performance: {e}")
    
    # Public interface
    async def process_user_request(self, user_request: str, 
                                 conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Process user request through Agent Cortex-powered workflow"""
        
        if not self.graph:
            await self.initialize()
        
        # Create initial state
        initial_state = BoarderframeState(
            user_request=user_request,
            conversation_id=conversation_id or str(uuid.uuid4()),
            workflow_type=WorkflowType.USER_CHAT.value,
            current_agent="",
            agent_chain=[],
            reasoning_chain=[],
            context={},
            conversation_history=[],
            task_context={},
            cortex_selections=[],
            performance_tracking=[],
            available_tools=[],
            tool_results=[],
            department=None,
            handoff_context=None,
            final_response="",
            completion_status="pending",
            quality_score=0.0,
            timestamp=datetime.now().isoformat(),
            processing_time=0.0
        )
        
        # Process through graph
        try:
            config = {"configurable": {"thread_id": initial_state["conversation_id"]}}
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # Store workflow
            self.active_workflows[initial_state["conversation_id"]] = final_state
            
            return {
                "response": final_state["final_response"],
                "conversation_id": final_state["conversation_id"],
                "agent_chain": final_state["agent_chain"],
                "cortex_selections": final_state["cortex_selections"],
                "quality_score": final_state["quality_score"],
                "processing_time": final_state["processing_time"],
                "completion_status": final_state["completion_status"]
            }
            
        except Exception as e:
            self.logger.error(f"Workflow processing error: {e}")
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "conversation_id": initial_state["conversation_id"],
                "agent_chain": [],
                "cortex_selections": [],
                "quality_score": 0.0,
                "processing_time": 0.0,
                "completion_status": "error"
            }


# Convenience function
async def get_orchestrator() -> AgentCortexLangGraphOrchestrator:
    """Get or create the orchestrator instance"""
    if not hasattr(get_orchestrator, "_instance"):
        get_orchestrator._instance = AgentCortexLangGraphOrchestrator()
        await get_orchestrator._instance.initialize()
    return get_orchestrator._instance


# Export main class
__all__ = ["AgentCortexLangGraphOrchestrator", "BoarderframeState", "WorkflowType", "get_orchestrator"]