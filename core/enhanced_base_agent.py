"""
Enhanced Base Agent with Claude API and Voice Integration
Extends the existing BaseAgent with modern capabilities
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Import existing base agent
from .base_agent import AgentConfig, AgentState, BaseAgent
from .claude_integration import get_claude_integration
from .message_bus import MessagePriority, send_task_request
from .voice_integration import get_voice_integration

# Import LangChain components
try:
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.prompts import PromptTemplate
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import AIMessage, HumanMessage

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available - some features will be limited")

# Import LangGraph for workflows
try:
    from langgraph.checkpoint import MemorySaver
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph not available - workflow features will be limited")

logger = logging.getLogger(__name__)


class EnhancedBaseAgent(BaseAgent):
    """
    Enhanced agent with Claude intelligence and voice capabilities
    Fully backward compatible with existing BaseAgent
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)

        # Get singleton instances
        self.claude = get_claude_integration()
        self.voice = get_voice_integration()

        # Enhanced capabilities flags
        self.has_voice = True
        self.has_claude = True
        self.has_langchain = LANGCHAIN_AVAILABLE
        self.has_workflows = LANGGRAPH_AVAILABLE

        # Initialize LangChain if available
        if LANGCHAIN_AVAILABLE:
            self._init_langchain()

        # Voice conversation state
        self.is_listening = False
        self.voice_callback = None

        # Team collaboration
        self.team_members: List[str] = []
        self.is_team_leader = False

        # Learning and improvement
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "user_satisfaction": 0.0,
        }

        logger.info(f"Enhanced agent {config.name} initialized with Claude and voice")

    def _init_langchain(self):
        """Initialize LangChain components"""
        try:
            # Create LangChain LLM with Claude
            self.langchain_llm = ChatAnthropic(
                model="claude-3-opus-20240229",
                anthropic_api_key=self.claude.api_key,
                temperature=0.7,
                max_tokens=4096,
            )

            # Create memory
            self.langchain_memory = ConversationBufferWindowMemory(
                k=10, return_messages=True  # Keep last 10 exchanges
            )

            # Create a general-purpose chain
            self.general_chain = LLMChain(
                llm=self.langchain_llm, memory=self.langchain_memory, verbose=False
            )

            logger.info(f"LangChain initialized for {self.config.name}")

        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {e}")
            self.has_langchain = False

    async def think(self, context: Dict[str, Any]) -> str:
        """
        Enhanced thinking with Claude API
        Backward compatible with original think method
        """
        # Extract message from context
        message = context.get("message", context.get("task", str(context)))

        # Add system context
        enhanced_context = {
            "agent_name": self.config.name,
            "department": getattr(self, "department", "general"),
            "current_time": datetime.utcnow().isoformat(),
            "team_members": self.team_members,
            **context,
        }

        try:
            # Use Claude for intelligent response
            response = await self.claude.get_response(
                agent_name=self.config.name.lower(),
                user_message=message,
                context=enhanced_context,
            )

            # Update metrics
            self.performance_metrics["tasks_completed"] += 1

            return response

        except Exception as e:
            logger.error(f"Claude thinking error: {e}")
            # Fallback to simple response
            return f"I understand the task: {message}. Let me process this."

    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced acting based on thoughts
        Backward compatible with original act method
        """
        # Default implementation that can be overridden
        result = {
            "status": "completed",
            "thought": thought,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # If the thought suggests using a tool, try to use it
        if "use tool" in thought.lower():
            for tool_name, tool_func in self.tools.items():
                if tool_name in thought.lower():
                    try:
                        tool_result = await tool_func("execute", context=context)
                        result["tool_used"] = tool_name
                        result["tool_result"] = tool_result
                        break
                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")

        return result

    async def speak(
        self, text: str, emotion: Optional[float] = None
    ) -> Optional[bytes]:
        """
        Speak the given text with voice synthesis
        """
        if not self.has_voice:
            logger.warning(f"{self.config.name} has no voice capability")
            return None

        try:
            audio_data = await self.voice.text_to_speech(
                text=text, agent_name=self.config.name.lower(), emotion=emotion
            )

            logger.info(f"{self.config.name} spoke: {text[:50]}...")
            return audio_data

        except Exception as e:
            logger.error(f"Voice synthesis error: {e}")
            return None

    async def listen(self, duration: int = 5) -> Optional[str]:
        """
        Listen for speech input
        """
        if not self.has_voice:
            logger.warning(f"{self.config.name} has no voice capability")
            return None

        try:
            text = await self.voice.speech_to_text(duration=duration)

            if text:
                logger.info(f"{self.config.name} heard: {text}")

            return text

        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None

    def start_continuous_listening(self, callback: Callable[[str], None]):
        """
        Start listening continuously for voice commands
        """
        if not self.has_voice:
            logger.warning(f"{self.config.name} has no voice capability")
            return

        self.is_listening = True
        self.voice_callback = callback

        def voice_handler(text: str):
            # Process through Claude first
            response = self.claude.get_sync_response(self.config.name.lower(), text)
            callback(response)

        self.voice.start_continuous_listening(voice_handler)
        logger.info(f"{self.config.name} started continuous listening")

    def stop_continuous_listening(self):
        """
        Stop continuous listening
        """
        self.is_listening = False
        self.voice.stop_continuous_listening()
        logger.info(f"{self.config.name} stopped continuous listening")

    async def handle_user_chat(self, message: str) -> str:
        """
        Enhanced chat handling with Claude
        For Corporate HQ integration
        """
        try:
            # Get intelligent response from Claude
            response = await self.claude.get_response(
                agent_name=self.config.name.lower(),
                user_message=message,
                context={"chat_interface": "corporate_hq", "user": "operator"},
            )

            # Optionally speak the response
            if self.has_voice and hasattr(self, "voice_enabled") and self.voice_enabled:
                await self.speak(response)

            return response

        except Exception as e:
            logger.error(f"Chat handling error: {e}")
            return f"I apologize, but I encountered an error processing your message: {str(e)}"

    async def collaborate_with(self, agent_name: str, task: Dict[str, Any]) -> Any:
        """
        Collaborate with another agent on a task
        """
        logger.info(f"{self.config.name} collaborating with {agent_name} on task")

        # Send task to other agent
        response = await send_task_request(
            from_agent=self.config.name,
            to_agent=agent_name,
            task=task,
            priority=MessagePriority.NORMAL,
        )

        return response

    def form_team(self, members: List[str], make_leader: bool = False):
        """
        Form a team with other agents
        """
        self.team_members = members
        self.is_team_leader = make_leader

        logger.info(f"{self.config.name} formed team with {members}")

        if make_leader:
            logger.info(f"{self.config.name} is team leader")

    async def delegate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate task to team members
        """
        if not self.is_team_leader or not self.team_members:
            logger.warning(f"{self.config.name} cannot delegate - not a team leader")
            return {"error": "Not a team leader"}

        # Use Claude to decide best agent for task
        decision = await self.claude.get_response(
            self.config.name.lower(),
            f"Which team member should handle this task? Members: {self.team_members}. Task: {task}",
            context={"role": "delegation"},
        )

        # Extract agent name from decision (simplified)
        selected_agent = self.team_members[0]  # Default to first member

        # Delegate to selected agent
        result = await self.collaborate_with(selected_agent, task)

        return {"delegated_to": selected_agent, "result": result}

    async def learn_from_interaction(self, interaction: Dict[str, Any]):
        """
        Learn and improve from interactions
        """
        # Update performance metrics
        if interaction.get("success", False):
            self.performance_metrics["success_rate"] = (
                self.performance_metrics["success_rate"] * 0.9 + 0.1
            )

        # Store learning in Claude's memory
        await self.claude.get_response(
            self.config.name.lower(),
            f"Learn from this interaction: {json.dumps(interaction)}",
            context={"learning_mode": True},
        )

    def create_workflow(self) -> Optional[Any]:
        """
        Create a LangGraph workflow for complex tasks
        """
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph not available")
            return None

        # Create state graph
        workflow = StateGraph(dict)

        # Add nodes for common agent tasks
        workflow.add_node("analyze", self._analyze_task)
        workflow.add_node("plan", self._plan_execution)
        workflow.add_node("execute", self._execute_plan)
        workflow.add_node("review", self._review_results)

        # Add edges
        workflow.add_edge("analyze", "plan")
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", "review")
        workflow.add_edge("review", END)

        # Set entry point
        workflow.set_entry_point("analyze")

        # Compile with memory
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    async def _analyze_task(self, state: Dict) -> Dict:
        """Analyze incoming task"""
        analysis = await self.think({"task": state.get("task"), "phase": "analysis"})
        state["analysis"] = analysis
        return state

    async def _plan_execution(self, state: Dict) -> Dict:
        """Plan task execution"""
        plan = await self.think(
            {"analysis": state.get("analysis"), "phase": "planning"}
        )
        state["plan"] = plan
        return state

    async def _execute_plan(self, state: Dict) -> Dict:
        """Execute the plan"""
        result = await self.act(state.get("plan"), {"phase": "execution"})
        state["result"] = result
        return state

    async def _review_results(self, state: Dict) -> Dict:
        """Review and learn from results"""
        review = await self.think({"result": state.get("result"), "phase": "review"})
        state["review"] = review

        # Learn from the interaction
        await self.learn_from_interaction(
            {"task": state.get("task"), "result": state.get("result"), "success": True}
        )

        return state

    async def process_with_workflow(self, task: Dict) -> Dict:
        """
        Process a task using the workflow
        """
        workflow = self.create_workflow()
        if not workflow:
            # Fallback to simple processing
            thought = await self.think(task)
            return await self.act(thought, task)

        # Run workflow
        result = await workflow.ainvoke({"task": task})
        return result

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get agent's enhanced capabilities
        """
        return {
            "voice": self.has_voice,
            "claude_ai": self.has_claude,
            "langchain": self.has_langchain,
            "workflows": self.has_workflows,
            "team_collaboration": True,
            "continuous_learning": True,
        }

    def __repr__(self) -> str:
        """Enhanced representation"""
        return (
            f"EnhancedAgent(name='{self.config.name}', "
            f"role='{self.config.role}', "
            f"voice={self.has_voice}, "
            f"claude={self.has_claude}, "
            f"team_size={len(self.team_members)})"
        )
