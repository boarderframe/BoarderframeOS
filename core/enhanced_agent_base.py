"""
Enhanced Agent Base - Advanced agent framework with LangChain integration
Maintains full backward compatibility with existing BaseAgent
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

# LangChain imports
try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.prompts import PromptTemplate
    from langchain.schema import AgentAction, AgentFinish, BaseMemory
    from langchain.tools import StructuredTool, Tool
    from langchain_anthropic import ChatAnthropic
    from langchain_core.language_models import BaseLLM
    from langchain_openai import ChatOpenAI

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available - enhanced features disabled")

# Import base agent for inheritance
from .base_agent import AgentConfig, AgentMemory, AgentState, BaseAgent
from .llm_client import LLMClient
from .message_bus import MessagePriority, message_bus


@dataclass
class EnhancedAgentConfig(AgentConfig):
    """Extended configuration for enhanced agents"""

    # LangChain specific settings
    use_langchain: bool = True
    langchain_model: Optional[str] = None
    memory_type: str = "conversation"  # conversation, summary, kg
    memory_window_size: int = 10

    # Advanced features
    enable_reasoning_chain: bool = True
    enable_self_reflection: bool = True
    enable_tool_learning: bool = True
    max_reasoning_steps: int = 5

    # Team collaboration
    team_role: Optional[str] = None  # leader, specialist, supporter
    can_delegate: bool = False
    preferred_collaborators: List[str] = field(default_factory=list)


class EnhancedAgentMemory(AgentMemory):
    """Enhanced memory with LangChain integration"""

    def __init__(self, config: EnhancedAgentConfig):
        super().__init__()
        self.config = config
        self.langchain_memory: Optional[BaseMemory] = None

        if LANGCHAIN_AVAILABLE and config.use_langchain:
            self._initialize_langchain_memory()

    def _initialize_langchain_memory(self):
        """Initialize LangChain memory based on configuration"""
        if self.config.memory_type == "conversation":
            self.langchain_memory = ConversationBufferWindowMemory(
                k=self.config.memory_window_size, return_messages=True
            )

    def add_interaction(self, user_input: str, agent_output: str):
        """Add an interaction to both native and LangChain memory"""
        # Add to native memory
        self.add(
            {
                "type": "interaction",
                "user_input": user_input,
                "agent_output": agent_output,
            }
        )

        # Add to LangChain memory if available
        if self.langchain_memory:
            self.langchain_memory.save_context(
                {"input": user_input}, {"output": agent_output}
            )


class EnhancedBaseAgent(BaseAgent):
    """Enhanced agent with LangChain integration and advanced capabilities"""

    def __init__(self, config: Union[AgentConfig, EnhancedAgentConfig]):
        # Convert regular config to enhanced if needed
        if not isinstance(config, EnhancedAgentConfig):
            enhanced_config = EnhancedAgentConfig(**config.__dict__)
            config = enhanced_config

        # Initialize base agent
        super().__init__(config)

        # Override with enhanced memory
        self.memory = EnhancedMemory(config)
        self.enhanced_config = config

        # LangChain components
        self.langchain_llm: Optional[BaseLLM] = None
        self.langchain_tools: List[Tool] = []
        self.agent_executor: Optional[AgentExecutor] = None

        # Enhanced capabilities
        self.reasoning_chain: List[Dict[str, Any]] = []
        self.learned_patterns: List[Dict[str, Any]] = []
        self.collaboration_history: List[Dict[str, Any]] = []

        # Initialize LangChain if available
        if LANGCHAIN_AVAILABLE and config.use_langchain:
            self._initialize_langchain()

    def _initialize_langchain(self):
        """Initialize LangChain components"""
        try:
            # Initialize LLM
            if "claude" in self.enhanced_config.model.lower():
                self.langchain_llm = ChatAnthropic(
                    model_name=self.enhanced_config.langchain_model
                    or self.enhanced_config.model,
                    temperature=self.enhanced_config.temperature,
                )
            elif "gpt" in self.enhanced_config.model.lower():
                self.langchain_llm = ChatOpenAI(
                    model_name=self.enhanced_config.langchain_model
                    or self.enhanced_config.model,
                    temperature=self.enhanced_config.temperature,
                )

            # Initialize tools
            self._initialize_langchain_tools()

            # Create agent executor
            if self.langchain_llm and self.langchain_tools:
                self._create_agent_executor()

        except Exception as e:
            self.logger.warning(f"Failed to initialize LangChain: {e}")
            self.enhanced_config.use_langchain = False

    def _initialize_langchain_tools(self):
        """Initialize LangChain tools from agent tools"""
        # Convert existing tools to LangChain tools
        for tool_name, tool_func in self.tools.items():
            langchain_tool = Tool(
                name=tool_name,
                func=lambda x, tf=tool_func: asyncio.run(tf(**json.loads(x))),
                description=f"Use this tool for {tool_name} operations",
            )
            self.langchain_tools.append(langchain_tool)

        # Add enhanced tools
        if self.enhanced_config.enable_self_reflection:
            self.langchain_tools.append(
                Tool(
                    name="self_reflect",
                    func=self._self_reflect_tool,
                    description="Reflect on recent actions and learnings",
                )
            )

        if self.enhanced_config.can_delegate:
            self.langchain_tools.append(
                Tool(
                    name="delegate_task",
                    func=self._delegate_task_tool,
                    description="Delegate a task to another agent",
                )
            )

    def _create_agent_executor(self):
        """Create LangChain agent executor"""
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            template="""You are {agent_name}, {agent_role}.

Your goals are:
{agent_goals}

You have access to the following tools:
{tools}

Use the following format:
Thought: Think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Current context: {input}
{agent_scratchpad}""",
        )

        # Format prompt with agent details
        prompt = prompt.partial(
            agent_name=self.config.name,
            agent_role=self.config.role,
            agent_goals="\n".join(f"- {goal}" for goal in self.config.goals),
        )

        # Create agent
        agent = create_react_agent(
            llm=self.langchain_llm, tools=self.langchain_tools, prompt=prompt
        )

        # Create executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.langchain_tools,
            memory=self.memory.langchain_memory,
            verbose=True,
            max_iterations=self.enhanced_config.max_reasoning_steps,
        )

    async def think(self, context: Dict[str, Any]) -> str:
        """Enhanced thinking with reasoning chains"""
        # Check if we should use LangChain
        if self.enhanced_config.use_langchain and self.agent_executor:
            return await self._langchain_think(context)

        # Fall back to base agent thinking
        return await super().think(context)

    async def _langchain_think(self, context: Dict[str, Any]) -> str:
        """Think using LangChain reasoning"""
        try:
            # Prepare input
            input_text = f"""Current context:
- Time: {context.get('current_time')}
- Active tasks: {context.get('active_tasks')}
- New messages: {len(context.get('new_messages', []))}

What should I do next?"""

            # Run agent executor
            result = await asyncio.to_thread(self.agent_executor.run, input_text)

            # Store reasoning chain
            if self.enhanced_config.enable_reasoning_chain:
                self.reasoning_chain.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "context": context,
                        "reasoning": result,
                    }
                )

            return result

        except Exception as e:
            self.logger.error(f"LangChain thinking failed: {e}")
            # Fall back to base thinking
            return await super().think(context)

    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced action execution"""
        # Store action for learning
        action_record = {
            "timestamp": datetime.now().isoformat(),
            "thought": thought,
            "context": context,
        }

        # Execute base action
        result = await super().act(thought, context)

        # Record result
        action_record["result"] = result

        # Learn from action if enabled
        if self.enhanced_config.enable_tool_learning:
            await self._learn_from_action(action_record)

        return result

    async def collaborate_with(
        self, agent_name: str, task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collaborate with another agent"""
        # Record collaboration
        self.collaboration_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "collaborator": agent_name,
                "task": task,
            }
        )

        # Send task via message bus
        response = await self.send_task_to_agent(agent_name, task, MessagePriority.HIGH)

        return {
            "collaborator": agent_name,
            "response": response.content if response else None,
        }

    def _self_reflect_tool(self, query: str) -> str:
        """Tool for self-reflection"""
        recent_actions = self.reasoning_chain[-5:] if self.reasoning_chain else []
        recent_learnings = self.learned_patterns[-3:] if self.learned_patterns else []

        reflection = {
            "query": query,
            "recent_actions": len(recent_actions),
            "recent_learnings": len(recent_learnings),
            "performance_metrics": self.get_metrics(),
            "insights": [],
        }

        # Generate insights
        if recent_actions:
            reflection["insights"].append(
                f"Completed {len(recent_actions)} actions recently"
            )

        if self.metrics["errors"] > 0:
            reflection["insights"].append(
                f"Encountered {self.metrics['errors']} errors - need to improve error handling"
            )

        return json.dumps(reflection, indent=2)

    def _delegate_task_tool(self, task_json: str) -> str:
        """Tool for delegating tasks to other agents"""
        try:
            task_data = json.loads(task_json)
            target_agent = task_data.get(
                "agent",
                self.enhanced_config.preferred_collaborators[0]
                if self.enhanced_config.preferred_collaborators
                else "david",
            )

            # Send delegation request
            asyncio.create_task(self.collaborate_with(target_agent, task_data))

            return f"Task delegated to {target_agent}"

        except Exception as e:
            return f"Failed to delegate task: {e}"

    async def _learn_from_action(self, action_record: Dict[str, Any]):
        """Learn patterns from actions"""
        # Simple pattern recognition
        if action_record["result"].get("action") == "error":
            # Learn from errors
            self.learned_patterns.append(
                {
                    "type": "error_pattern",
                    "thought": action_record["thought"],
                    "error": action_record["result"].get("error"),
                    "timestamp": action_record["timestamp"],
                }
            )
        elif action_record["result"].get("action") != "idle":
            # Learn from successful actions
            self.learned_patterns.append(
                {
                    "type": "success_pattern",
                    "thought": action_record["thought"],
                    "action": action_record["result"].get("action"),
                    "timestamp": action_record["timestamp"],
                }
            )

        # Limit pattern memory
        if len(self.learned_patterns) > 100:
            self.learned_patterns = self.learned_patterns[-100:]

    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """Get enhanced metrics including LangChain stats"""
        metrics = super().get_metrics()

        # Add enhanced metrics
        metrics.update(
            {
                "reasoning_chains": len(self.reasoning_chain),
                "learned_patterns": len(self.learned_patterns),
                "collaborations": len(self.collaboration_history),
                "langchain_enabled": self.enhanced_config.use_langchain,
                "langchain_tools": len(self.langchain_tools)
                if LANGCHAIN_AVAILABLE
                else 0,
            }
        )

        return metrics


# Convenience function for creating enhanced agents
def create_enhanced_agent(
    name: str, role: str, goals: List[str], **kwargs
) -> EnhancedBaseAgent:
    """Factory function for creating enhanced agents"""
    config = EnhancedAgentConfig(name=name, role=role, goals=goals, **kwargs)

    # Return appropriate agent class based on LangChain availability
    if LANGCHAIN_AVAILABLE and config.use_langchain:
        return EnhancedBaseAgent(config)
    else:
        # Fall back to regular base agent
        return BaseAgent(config)
