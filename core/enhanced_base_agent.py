"""
Enhanced BaseAgent with Agent Cortex + LangGraph Integration
Next-generation agent framework for BoarderframeOS
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

# LangGraph integration
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Agent Cortex integration
from .the_agent_cortex import TheAgentCortex, AgentRequest, get_agent_cortex_instance, PerformanceMetrics
from .agent_cortex_langgraph_orchestrator import AgentCortexLangGraphOrchestrator, get_orchestrator

# Monitoring integration
import agentops
from langsmith import Client as LangSmithClient

# BoarderframeOS core (keeping existing integrations)
from .base_agent import AgentConfig, AgentState, AgentMemory  # Import from original
from .message_bus import message_bus, MessageType, MessagePriority
from .cost_management import get_agent_cost_policy
from .registry_integration import register_agent_with_database


class EnhancedAgentState(Enum):
    """Enhanced agent states with Agent Cortex integration"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING_WITH_AGENT_CORTEX = "thinking_with_agent_cortex"
    ACTING_WITH_AGENT_CORTEX = "acting_with_agent_cortex"
    ORCHESTRATING = "orchestrating"
    LEARNING = "learning"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class AgentCortexSession:
    """Agent Cortex session tracking for agent"""
    agent_name: str
    session_id: str
    active_requests: List[str] = field(default_factory=list)
    performance_history: List[PerformanceMetrics] = field(default_factory=list)
    model_preferences: Dict[str, Any] = field(default_factory=dict)
    cost_budget: float = 10.0
    quality_threshold: float = 0.85


@dataclass
class EnhancedAgentMetrics:
    """Enhanced metrics with Agent Cortex and LangGraph tracking"""
    # Original metrics
    thoughts_processed: int = 0
    actions_taken: int = 0
    errors: int = 0
    
    # Agent Cortex-specific metrics
    agent_cortex_requests: int = 0
    model_switches: int = 0
    cost_savings: float = 0.0
    
    # LangGraph metrics
    workflows_completed: int = 0
    handoffs_executed: int = 0
    orchestration_time: float = 0.0
    
    # Performance metrics
    avg_response_time: float = 0.0
    quality_score: float = 0.0
    user_satisfaction: float = 0.0
    
    # Timestamps
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


class EnhancedBaseAgent(ABC):
    """Enhanced BaseAgent with Agent Cortex + LangGraph + Monitoring integration"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = EnhancedAgentState.INITIALIZING
        self.memory = AgentMemory()
        
        # Agent Cortex integration
        self.agent_cortex = None  # Will be initialized async
        self.agent_cortex_session = AgentCortexSession(
            agent_name=config.name,
            session_id=str(uuid.uuid4())
        )
        
        # LangGraph integration
        self.orchestrator = None  # Will be initialized async
        self.agent_graph = None
        self.memory_checkpoint = MemorySaver()
        
        # Monitoring integration
        self.langsmith_client = None
        self.agentops_session = None
        
        # Enhanced metrics
        self.metrics = EnhancedAgentMetrics()
        
        # Message handling (keeping existing)
        self.active_tasks: List[asyncio.Task] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Tools and capabilities (enhanced)
        self.tools: Dict[str, Callable] = {}
        self.mcp_tools: Dict[str, Any] = {}
        
        # State management
        self.active = True
        self.logger = self._setup_enhanced_logger()
        
        # Cost management (keeping existing integration)
        self.cost_policy = get_agent_cost_policy(config.name)
        
        # Registry integration
        self.registry_id = None
    
    async def initialize(self):
        """Initialize all enhanced systems"""
        
        self.logger.info(f"🚀 Initializing enhanced agent: {self.config.name}")
        
        # Initialize Agent Cortex connection
        self.agent_cortex = await get_agent_cortex_instance()
        self.logger.info("🧠 Agent Cortex connection established")
        
        # Initialize LangGraph orchestrator
        self.orchestrator = await get_orchestrator()
        self.logger.info("🕸️ LangGraph orchestrator connected")
        
        # Create agent-specific graph
        self.agent_graph = await self._create_agent_graph()
        self.logger.info("📊 Agent-specific graph created")
        
        # Initialize monitoring
        await self._initialize_monitoring()
        self.logger.info("📈 Monitoring systems initialized")
        
        # Load enhanced tools
        await self._load_enhanced_tools()
        self.logger.info("🛠️ Enhanced tools loaded")
        
        # Register with systems
        await self._register_with_systems()
        self.logger.info("📝 Registered with all systems")
        
        self.state = EnhancedAgentState.IDLE
        self.logger.info(f"✅ Enhanced agent {self.config.name} ready")
    
    def _setup_enhanced_logger(self) -> logging.Logger:
        """Setup enhanced logging with Agent Cortex/LangGraph context"""
        logger = logging.getLogger(f"enhanced_agent.{self.config.name}")
        
        # Enhanced formatter with more context
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [AgentCortex:%(agent_cortex_model)s] - %(message)s',
            defaults={'agent_cortex_model': 'none'}
        )
        
        # File handler
        from pathlib import Path
        log_dir = Path("logs/enhanced_agents")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(f"logs/enhanced_agents/{self.config.name}.log")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    async def _create_agent_graph(self) -> StateGraph:
        """Create LangGraph workflow specific to this agent"""
        
        from .agent_cortex_langgraph_orchestrator import BoarderframeState
        
        # Create agent-specific state graph
        graph = StateGraph(BoarderframeState)
        
        # Standard agent workflow nodes
        graph.add_node("perceive", self._agent_cortex_perceive)
        graph.add_node("think", self._agent_cortex_think)
        graph.add_node("act", self._agent_cortex_act)
        graph.add_node("reflect", self._agent_cortex_reflect)
        graph.add_node("learn", self._agent_cortex_learn)
        
        # Agent-specific specialized nodes
        await self._add_specialized_nodes(graph)
        
        # Standard workflow edges
        graph.add_edge(START, "perceive")
        graph.add_edge("perceive", "think")
        graph.add_edge("think", "act")
        graph.add_edge("act", "reflect")
        graph.add_edge("reflect", "learn")
        graph.add_edge("learn", END)
        
        # Compile with checkpointing
        return graph.compile(checkpointer=self.memory_checkpoint)
    
    async def _add_specialized_nodes(self, graph: StateGraph):
        """Add agent-specific specialized nodes (override in subclasses)"""
        # Base implementation - subclasses can add specific nodes
        pass
    
    async def _agent_cortex_perceive(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced perception with Agent Cortex context awareness"""
        
        self.state = EnhancedAgentState.THINKING_WITH_AGENT_CORTEX
        
        # Gather enhanced context
        perception_context = {
            "user_input": state.get("user_request", ""),
            "conversation_history": await self._get_conversation_history(),
            "agent_state": self.state.value,
            "recent_performance": self.agent_cortex_session.performance_history[-5:],
            "available_tools": list(self.tools.keys()),
            "system_context": await self._get_system_context()
        }
        
        # Update state with perception
        state["perception_context"] = perception_context
        state["current_agent"] = self.config.name
        state["perception_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _agent_cortex_think(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced thinking with Agent Cortex model selection"""
        
        # Assess thinking complexity
        complexity = await self._assess_thinking_complexity(state)
        
        # Create Agent Cortex request for thinking
        agent_cortex_request = AgentRequest(
            agent_name=self.config.name,
            task_type="thinking",
            context=state.get("perception_context", {}),
            complexity=complexity,
            quality_requirements=self.agent_cortex_session.quality_threshold,
            conversation_id=state.get("conversation_id")
        )
        
        # Get optimal model from Agent Cortex
        agent_cortex_response = await self.agent_cortex.process_agent_request(agent_cortex_request)
        
        # Track Agent Cortex selection
        self.agent_cortex_session.active_requests.append(agent_cortex_response.tracking_id)
        self.metrics.agent_cortex_requests += 1
        
        # Enhanced thinking prompt
        thinking_prompt = await self._create_thinking_prompt(state, agent_cortex_response)
        
        # Execute thinking with Agent Cortex-selected model
        try:
            thinking_result = await agent_cortex_response.llm.generate(thinking_prompt)
            
            # Report success to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                thinking_result,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Thinking error: {e}")
            thinking_result = f"I encountered an issue while thinking: {str(e)}"
            
            # Report error to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                thinking_result,
                success=False
            )
        
        # Update state
        state["thoughts"] = thinking_result
        state["agent_cortex_selection"] = agent_cortex_response.selection.__dict__
        state["thinking_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _agent_cortex_act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced action with Agent Cortex optimization"""
        
        self.state = EnhancedAgentState.ACTING_WITH_AGENT_CORTEX
        
        # Determine action complexity
        action_complexity = await self._assess_action_complexity(state)
        
        # Create Agent Cortex request for action
        agent_cortex_request = AgentRequest(
            agent_name=self.config.name,
            task_type="action",
            context={
                "thoughts": state.get("thoughts", ""),
                "perception": state.get("perception_context", {}),
                "required_action": await self._determine_required_action(state)
            },
            complexity=action_complexity,
            quality_requirements=self.agent_cortex_session.quality_threshold
        )
        
        # Get optimal model from Agent Cortex
        agent_cortex_response = await self.agent_cortex.process_agent_request(agent_cortex_request)
        
        # Execute action with Agent Cortex-selected model
        action_result = await self._execute_enhanced_action(state, agent_cortex_response)
        
        # Update metrics
        self.metrics.actions_taken += 1
        
        # Update state
        state["action_result"] = action_result
        state["action_agent_cortex_selection"] = agent_cortex_response.selection.__dict__
        state["action_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _agent_cortex_reflect(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced reflection with performance analysis"""
        
        # Analyze performance of this interaction
        performance_analysis = await self._analyze_interaction_performance(state)
        
        # Store in memory
        await self._store_reflection_in_memory(state, performance_analysis)
        
        # Update state
        state["reflection"] = performance_analysis
        state["reflection_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _agent_cortex_learn(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced learning with Agent Cortex feedback"""
        
        self.state = EnhancedAgentState.LEARNING
        
        # Extract learning insights
        learning_insights = await self._extract_learning_insights(state)
        
        # Update agent preferences based on Agent Cortex performance
        await self._update_agent_cortex_preferences(state)
        
        # Update metrics
        self.metrics.workflows_completed += 1
        self.metrics.last_activity = datetime.now()
        
        # Update state
        state["learning_insights"] = learning_insights
        state["learning_timestamp"] = datetime.now().isoformat()
        
        self.state = EnhancedAgentState.IDLE
        
        return state
    
    async def _initialize_monitoring(self):
        """Initialize LangSmith and AgentOps monitoring"""
        
        try:
            # Initialize LangSmith
            self.langsmith_client = LangSmithClient()
            await self._setup_langsmith_project()
            
            # Initialize AgentOps
            agentops.init(
                tags=["boarderframeos", "enhanced_agent", "agent_cortex_powered"]
            )
            self.agentops_session = agentops.start_session()
            
        except Exception as e:
            self.logger.warning(f"Monitoring initialization failed: {e}")
    
    async def _load_enhanced_tools(self):
        """Load enhanced tools with MCP integration"""
        
        # Load MCP tools based on agent configuration
        for tool_name in self.config.tools:
            if tool_name == "analytics":
                self.mcp_tools["analytics"] = await self._create_analytics_tool()
            elif tool_name == "customer":
                self.mcp_tools["customer"] = await self._create_customer_tool()
            elif tool_name == "registry":
                self.mcp_tools["registry"] = await self._create_registry_tool()
            elif tool_name == "filesystem":
                self.mcp_tools["filesystem"] = await self._create_filesystem_tool()
            elif tool_name == "database":
                self.mcp_tools["database"] = await self._create_database_tool()
        
        # Combine with existing tools
        self.tools.update(self.mcp_tools)
    
    async def _register_with_systems(self):
        """Register with all BoarderframeOS systems"""
        
        # Register with database registry (existing)
        try:
            self.registry_id = await register_agent_with_database(self.config)
        except Exception as e:
            self.logger.warning(f"Registry registration failed: {e}")
            self.registry_id = "unregistered"
        
        # Register with message bus (existing)
        await self._register_with_message_bus()
        
        # Register with Agent Cortex
        await self._register_with_agent_cortex()
    
    async def _register_with_agent_cortex(self):
        """Register this agent with The Agent Cortex"""
        
        # Update Agent Cortex's agent registry
        # This would be implemented when Agent Cortex has agent registry
        pass
    
    # Enhanced user chat interface
    async def handle_user_chat(self, message: str, conversation_id: Optional[str] = None) -> str:
        """Enhanced chat handling with full Agent Cortex + LangGraph integration"""
        
        self.logger.info(f"Handling user chat: {message[:100]}...")
        
        try:
            # Use the orchestrator for complex multi-agent workflows
            if await self._should_use_orchestrator(message):
                result = await self.orchestrator.process_user_request(message, conversation_id)
                return result["response"]
            
            # Use agent-specific graph for single-agent tasks
            else:
                return await self._process_with_agent_graph(message, conversation_id)
                
        except Exception as e:
            self.logger.error(f"Enhanced chat error: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def _should_use_orchestrator(self, message: str) -> bool:
        """Determine if request should use multi-agent orchestrator"""
        
        # Use orchestrator for complex requests that might need multiple agents
        complex_keywords = [
            "create agent", "new agent", "department", "team", "coordinate",
            "multiple", "complex", "strategy", "business plan", "analysis"
        ]
        
        return any(keyword in message.lower() for keyword in complex_keywords)
    
    async def _process_with_agent_graph(self, message: str, 
                                      conversation_id: Optional[str]) -> str:
        """Process using agent-specific LangGraph"""
        
        from .agent_cortex_langgraph_orchestrator import BoarderframeState
        
        # Create initial state
        initial_state = BoarderframeState(
            user_request=message,
            conversation_id=conversation_id or str(uuid.uuid4()),
            workflow_type="single_agent",
            current_agent=self.config.name,
            agent_chain=[self.config.name],
            reasoning_chain=[],
            context={},
            conversation_history=await self._get_conversation_history(),
            task_context={},
            agent_cortex_selections=[],
            performance_tracking=[],
            available_tools=list(self.tools.keys()),
            tool_results=[],
            department=None,
            handoff_context=None,
            final_response="",
            completion_status="pending",
            quality_score=0.0,
            timestamp=datetime.now().isoformat(),
            processing_time=0.0
        )
        
        # Process through agent graph
        config = {"configurable": {"thread_id": initial_state["conversation_id"]}}
        final_state = await self.agent_graph.ainvoke(initial_state, config=config)
        
        # Extract response
        if final_state.get("action_result"):
            return final_state["action_result"]
        elif final_state.get("thoughts"):
            return final_state["thoughts"]
        else:
            return "I've processed your request but don't have a specific response."
    
    # Helper methods
    async def _assess_thinking_complexity(self, state: Dict[str, Any]) -> int:
        """Assess complexity of thinking task"""
        
        user_input = state.get("perception_context", {}).get("user_input", "")
        
        complexity = 5  # Base complexity
        
        # Increase complexity for certain keywords
        if any(keyword in user_input.lower() for keyword in ["analyze", "strategy", "complex"]):
            complexity += 2
        if any(keyword in user_input.lower() for keyword in ["business", "revenue", "optimization"]):
            complexity += 1
        if len(user_input) > 500:  # Long requests
            complexity += 1
        
        return min(complexity, 10)
    
    async def _assess_action_complexity(self, state: Dict[str, Any]) -> int:
        """Assess complexity of action task"""
        
        thoughts = state.get("thoughts", "")
        
        complexity = 4  # Base complexity for actions
        
        # Increase complexity for complex actions
        if any(keyword in thoughts.lower() for keyword in ["create", "generate", "complex"]):
            complexity += 3
        if any(keyword in thoughts.lower() for keyword in ["coordinate", "multiple", "integrate"]):
            complexity += 2
        
        return min(complexity, 10)
    
    async def _create_thinking_prompt(self, state: Dict[str, Any], 
                                    agent_cortex_response) -> str:
        """Create enhanced thinking prompt"""
        
        perception = state.get("perception_context", {})
        
        prompt = f"""
        You are {self.config.name}, an enhanced AI agent with the role: {self.config.role}
        
        Your primary goals:
        {chr(10).join(f"- {goal}" for goal in self.config.goals)}
        
        Current situation:
        - User input: {perception.get('user_input', '')}
        - Available tools: {', '.join(perception.get('available_tools', []))}
        - Recent performance: {len(perception.get('recent_performance', []))} interactions tracked
        
        Agent Cortex selected model: {agent_cortex_response.selection.selected_model} 
        Reasoning: {agent_cortex_response.selection.reasoning}
        
        Think step by step about how to best respond to this user input.
        Consider your role, goals, and available capabilities.
        Be specific and actionable in your thinking.
        """
        
        return prompt
    
    async def _determine_required_action(self, state: Dict[str, Any]) -> str:
        """Determine what action is required based on thinking"""
        
        thoughts = state.get("thoughts", "")
        
        # Simple action determination logic
        if "tool" in thoughts.lower():
            return "use_tool"
        elif "respond" in thoughts.lower():
            return "generate_response"
        elif "analyze" in thoughts.lower():
            return "perform_analysis"
        else:
            return "general_response"
    
    async def _execute_enhanced_action(self, state: Dict[str, Any], 
                                     agent_cortex_response) -> str:
        """Execute action with Agent Cortex-selected model"""
        
        required_action = await self._determine_required_action(state)
        thoughts = state.get("thoughts", "")
        
        action_prompt = f"""
        Based on my thinking: {thoughts}
        
        Required action: {required_action}
        
        Execute this action and provide the result.
        Be helpful, accurate, and aligned with my role as {self.config.role}.
        """
        
        try:
            action_result = await agent_cortex_response.llm.generate(action_prompt)
            
            # Report success to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                action_result,
                success=True
            )
            
            return action_result
            
        except Exception as e:
            error_result = f"Action execution failed: {str(e)}"
            
            # Report error to Agent Cortex
            await self._report_agent_cortex_performance(
                agent_cortex_response.tracking_id,
                error_result,
                success=False
            )
            
            return error_result
    
    async def _report_agent_cortex_performance(self, tracking_id: str, 
                                      result: str, success: bool):
        """Report performance metrics to Agent Cortex"""
        
        try:
            metrics = PerformanceMetrics(
                tracking_id=tracking_id,
                agent_name=self.config.name,
                selected_model="",  # Will be filled by Agent Cortex
                actual_cost=0.001,  # Estimated
                actual_latency=1.5,  # Estimated
                actual_quality=0.8 if success else 0.3,
                user_satisfaction=0.8 if success else 0.4,
                task_completion=success
            )
            
            await self.agent_cortex.report_performance(tracking_id, metrics)
            
            # Update local metrics
            if success:
                self.metrics.quality_score = (self.metrics.quality_score + 0.8) / 2
            else:
                self.metrics.errors += 1
            
        except Exception as e:
            self.logger.error(f"Error reporting Agent Cortex performance: {e}")
    
    # Abstract methods for subclasses
    @abstractmethod
    async def think(self, context: Dict[str, Any]) -> str:
        """Abstract method for agent-specific thinking (compatibility with old interface)"""
        pass
    
    @abstractmethod
    async def act(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Abstract method for agent-specific actions (compatibility with old interface)"""
        pass
    
    # Additional helper methods
    async def _get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.memory.recall("conversation", limit=10)
    
    async def _get_system_context(self) -> Dict[str, Any]:
        """Get current system context"""
        return {
            "agent_count": len(await self._get_active_agents()),
            "system_load": 0.3,  # TODO: Get real system load
            "time_of_day": datetime.now().hour
        }
    
    async def _get_active_agents(self) -> List[str]:
        """Get list of active agents"""
        # TODO: Integrate with registry
        return ["solomon", "david", "adam"]
    
    async def _analyze_interaction_performance(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance of the interaction"""
        
        start_time = datetime.fromisoformat(state.get("timestamp", datetime.now().isoformat()))
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "processing_time": processing_time,
            "agent_cortex_selections": len(state.get("agent_cortex_selections", [])),
            "tools_used": len(state.get("tool_results", [])),
            "quality_indicators": {
                "response_length": len(state.get("action_result", "")),
                "complexity_handled": state.get("complexity", 5),
                "error_free": state.get("completion_status") != "error"
            }
        }
    
    async def _store_reflection_in_memory(self, state: Dict[str, Any], 
                                        performance_analysis: Dict[str, Any]):
        """Store reflection in agent memory"""
        
        reflection_entry = {
            "type": "reflection",
            "user_request": state.get("user_request", ""),
            "response": state.get("action_result", ""),
            "performance": performance_analysis,
            "agent_cortex_selections": state.get("agent_cortex_selections", []),
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory.add(reflection_entry, permanent=True)
    
    async def _extract_learning_insights(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract learning insights from the interaction"""
        
        agent_cortex_selections = state.get("agent_cortex_selections", [])
        performance = state.get("reflection", {})
        
        insights = {
            "model_effectiveness": {},
            "tool_usage_patterns": {},
            "improvement_opportunities": []
        }
        
        # Analyze Agent Cortex model selections
        for selection in agent_cortex_selections:
            model = selection.get("selected_model", "unknown")
            if model not in insights["model_effectiveness"]:
                insights["model_effectiveness"][model] = {"uses": 0, "avg_quality": 0.0}
            
            insights["model_effectiveness"][model]["uses"] += 1
            # TODO: Track actual quality scores
        
        return insights
    
    async def _update_agent_cortex_preferences(self, state: Dict[str, Any]):
        """Update Agent Cortex preferences based on performance"""
        
        # Update quality threshold based on recent performance
        if state.get("quality_score", 0) > 0.9:
            self.agent_cortex_session.quality_threshold = min(0.95, self.agent_cortex_session.quality_threshold + 0.01)
        elif state.get("quality_score", 0) < 0.7:
            self.agent_cortex_session.quality_threshold = max(0.75, self.agent_cortex_session.quality_threshold - 0.01)
    
    # Tool creation methods
    async def _create_analytics_tool(self):
        """Create analytics MCP tool"""
        # TODO: Implement actual MCP integration
        async def analytics_tool(query: str) -> str:
            return f"Analytics query executed: {query}"
        return analytics_tool
    
    async def _create_customer_tool(self):
        """Create customer MCP tool"""
        async def customer_tool(action: str, data: Dict = None) -> str:
            return f"Customer action {action} executed"
        return customer_tool
    
    async def _create_registry_tool(self):
        """Create registry MCP tool"""
        async def registry_tool(operation: str, agent_data: Dict = None) -> str:
            return f"Registry operation {operation} executed"
        return registry_tool
    
    async def _create_filesystem_tool(self):
        """Create filesystem MCP tool"""
        async def filesystem_tool(action: str, path: str, content: str = None) -> str:
            return f"Filesystem {action} on {path} executed"
        return filesystem_tool
    
    async def _create_database_tool(self):
        """Create database MCP tool"""
        async def database_tool(query: str, data: Dict = None) -> str:
            return f"Database query executed: {query}"
        return database_tool
    
    # Compatibility methods
    async def _register_with_message_bus(self):
        """Register with message bus (existing functionality)"""
        # TODO: Implement message bus registration
        pass
    
    async def _setup_langsmith_project(self):
        """Setup LangSmith project for this agent"""
        try:
            # Create agent-specific project
            project_name = f"boarderframeos-{self.config.name}"
            # TODO: Implement LangSmith project setup
        except Exception as e:
            self.logger.warning(f"LangSmith setup failed: {e}")
    
    # Status and monitoring
    async def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive enhanced agent status"""
        
        return {
            "agent_name": self.config.name,
            "state": self.state.value,
            "agent_cortex_session": {
                "session_id": self.agent_cortex_session.session_id,
                "active_requests": len(self.agent_cortex_session.active_requests),
                "cost_budget": self.agent_cortex_session.cost_budget,
                "quality_threshold": self.agent_cortex_session.quality_threshold
            },
            "metrics": {
                "agent_cortex_requests": self.metrics.agent_cortex_requests,
                "workflows_completed": self.metrics.workflows_completed,
                "avg_response_time": self.metrics.avg_response_time,
                "quality_score": self.metrics.quality_score,
                "errors": self.metrics.errors
            },
            "capabilities": {
                "tools": list(self.tools.keys()),
                "mcp_tools": list(self.mcp_tools.keys()),
                "goals": self.config.goals
            },
            "last_activity": self.metrics.last_activity.isoformat()
        }


# Export main class
__all__ = ["EnhancedBaseAgent", "EnhancedAgentState", "AgentCortexSession", "EnhancedAgentMetrics"]