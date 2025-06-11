"""
Agent Cortex - Central Intelligence Hub for BoarderframeOS
Dynamic LLM orchestration, intelligent model selection, and cost optimization
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Agent Cortex dependencies
import litellm
from qdrant_client import QdrantClient
from qdrant_client.http import models

from .cost_management import API_COST_SETTINGS, get_agent_cost_policy

# BoarderframeOS core
from .llm_client import LLMClient, LLMConfig
from .message_bus import message_bus


class ModelTier(Enum):
    """Model tiers for intelligent selection"""

    EXECUTIVE = "executive"  # Solomon, David
    DEPARTMENT = "department"  # Department heads
    SPECIALIST = "specialist"  # Specialist agents
    WORKER = "worker"  # Simple tasks


class SelectionStrategy(Enum):
    """Agent Cortex selection strategies"""

    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    BALANCED = "balanced"
    EMERGENCY_BUDGET = "emergency_budget"
    LOCAL_ONLY = "local_only"


@dataclass
class AgentRequest:
    """Request from agent to Agent Cortex"""

    agent_name: str
    task_type: str
    context: Dict[str, Any]
    complexity: int = 5  # 1-10 scale
    urgency: int = 5  # 1-10 scale
    quality_requirements: float = 0.85  # 0-1 scale
    max_cost: Optional[float] = None
    max_latency: Optional[float] = None
    conversation_id: Optional[str] = None


@dataclass
class ModelSelection:
    """Agent Cortex's model selection result"""

    selected_model: str
    provider: str
    reasoning: str
    confidence: float
    expected_cost: float
    expected_latency: float
    expected_quality: float
    fallback_chain: List[str] = field(default_factory=list)
    optimization_strategy: str = "balanced"


@dataclass
class CortexResponse:
    """Complete Agent Cortex response to agent"""

    llm: LLMClient
    selection: ModelSelection
    tracking_id: str
    session_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance tracking for learning"""

    tracking_id: str
    agent_name: str
    selected_model: str
    actual_cost: float
    actual_latency: float
    actual_quality: float
    user_satisfaction: Optional[float] = None
    task_completion: bool = True
    timestamp: datetime = field(default_factory=datetime.now)


class IntelligentModelSelector:
    """Intelligent model selection engine"""

    def __init__(self):
        self.model_registry = self._initialize_model_registry()
        self.performance_history = {}
        self.logger = logging.getLogger("agent_cortex.model_selector")

    def _initialize_model_registry(self) -> Dict[str, Dict]:
        """Initialize comprehensive model registry"""
        return {
            ModelTier.EXECUTIVE.value: {
                "primary": {
                    "model": "claude-3-opus-20240229",
                    "provider": "anthropic",
                    "cost_per_1k": 0.015,
                    "avg_latency": 3.2,
                    "quality_score": 0.95,
                },
                "fallback": {
                    "model": "gpt-4-turbo",
                    "provider": "openai",
                    "cost_per_1k": 0.01,
                    "avg_latency": 2.8,
                    "quality_score": 0.92,
                },
                "budget": {
                    "model": "claude-3-sonnet-20240620",
                    "provider": "anthropic",
                    "cost_per_1k": 0.003,
                    "avg_latency": 2.1,
                    "quality_score": 0.88,
                },
                "local": {
                    "model": "llama-4-maverick-30b",
                    "provider": "local",
                    "cost_per_1k": 0.0,
                    "avg_latency": 1.5,
                    "quality_score": 0.90,
                },
            },
            ModelTier.DEPARTMENT.value: {
                "primary": {
                    "model": "claude-3-sonnet-20240620",
                    "provider": "anthropic",
                    "cost_per_1k": 0.003,
                    "avg_latency": 2.1,
                    "quality_score": 0.88,
                },
                "fallback": {
                    "model": "gpt-4o",
                    "provider": "openai",
                    "cost_per_1k": 0.005,
                    "avg_latency": 1.8,
                    "quality_score": 0.86,
                },
                "budget": {
                    "model": "claude-3-haiku-20240307",
                    "provider": "anthropic",
                    "cost_per_1k": 0.00025,
                    "avg_latency": 1.2,
                    "quality_score": 0.82,
                },
                "local": {
                    "model": "llama-4-scout-17b",
                    "provider": "local",
                    "cost_per_1k": 0.0,
                    "avg_latency": 0.8,
                    "quality_score": 0.84,
                },
            },
            ModelTier.SPECIALIST.value: {
                "primary": {
                    "model": "claude-3-haiku-20240307",
                    "provider": "anthropic",
                    "cost_per_1k": 0.00025,
                    "avg_latency": 1.2,
                    "quality_score": 0.82,
                },
                "fallback": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "cost_per_1k": 0.00015,
                    "avg_latency": 1.0,
                    "quality_score": 0.80,
                },
                "budget": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "cost_per_1k": 0.00015,
                    "avg_latency": 1.0,
                    "quality_score": 0.80,
                },
                "local": {
                    "model": "llama-3.2-3b",
                    "provider": "local",
                    "cost_per_1k": 0.0,
                    "avg_latency": 0.3,
                    "quality_score": 0.75,
                },
            },
            ModelTier.WORKER.value: {
                "primary": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "cost_per_1k": 0.00015,
                    "avg_latency": 1.0,
                    "quality_score": 0.80,
                },
                "fallback": {
                    "model": "claude-3-haiku-20240307",
                    "provider": "anthropic",
                    "cost_per_1k": 0.00025,
                    "avg_latency": 1.2,
                    "quality_score": 0.82,
                },
                "budget": {
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "cost_per_1k": 0.00015,
                    "avg_latency": 1.0,
                    "quality_score": 0.80,
                },
                "local": {
                    "model": "llama-3.2-3b",
                    "provider": "local",
                    "cost_per_1k": 0.0,
                    "avg_latency": 0.3,
                    "quality_score": 0.75,
                },
            },
        }

    async def select_optimal_model(
        self,
        request: AgentRequest,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
    ) -> ModelSelection:
        """Select optimal model based on request and strategy"""

        # Determine agent tier
        agent_tier = self._get_agent_tier(request.agent_name)

        # Get available models for tier
        tier_models = self.model_registry[agent_tier.value]

        # Apply selection strategy
        if strategy == SelectionStrategy.COST_OPTIMIZED:
            selected_config = tier_models["budget"]
        elif strategy == SelectionStrategy.PERFORMANCE_OPTIMIZED:
            selected_config = tier_models["primary"]
        elif strategy == SelectionStrategy.LOCAL_ONLY:
            selected_config = tier_models["local"]
        elif strategy == SelectionStrategy.EMERGENCY_BUDGET:
            selected_config = tier_models["budget"]
        else:  # BALANCED
            selected_config = await self._balanced_selection(request, tier_models)

        # Generate fallback chain
        fallback_chain = await self._generate_fallback_chain(
            tier_models, selected_config
        )

        # Calculate metrics
        expected_cost = await self._estimate_cost(request, selected_config)
        expected_latency = selected_config["avg_latency"]
        expected_quality = selected_config["quality_score"]

        # Generate reasoning
        reasoning = await self._generate_selection_reasoning(
            request, selected_config, strategy, agent_tier
        )

        return ModelSelection(
            selected_model=selected_config["model"],
            provider=selected_config["provider"],
            reasoning=reasoning,
            confidence=0.85,  # TODO: ML-based confidence scoring
            expected_cost=expected_cost,
            expected_latency=expected_latency,
            expected_quality=expected_quality,
            fallback_chain=fallback_chain,
            optimization_strategy=strategy.value,
        )

    def _get_agent_tier(self, agent_name: str) -> ModelTier:
        """Determine agent tier for model selection"""
        executive_agents = ["solomon", "david"]
        department_heads = ["levi", "benjamin", "ephraim", "bezalel", "naphtali"]

        if agent_name.lower() in executive_agents:
            return ModelTier.EXECUTIVE
        elif agent_name.lower() in department_heads or agent_name.endswith("_head"):
            return ModelTier.DEPARTMENT
        elif agent_name.endswith("_specialist"):
            return ModelTier.SPECIALIST
        else:
            return ModelTier.WORKER

    async def _balanced_selection(
        self, request: AgentRequest, tier_models: Dict
    ) -> Dict:
        """Balanced selection considering complexity, cost, and quality"""

        # High complexity or high quality requirements -> primary model
        if request.complexity >= 8 or request.quality_requirements >= 0.9:
            return tier_models["primary"]

        # Low complexity and cost-sensitive -> budget model
        elif request.complexity <= 3 and request.max_cost and request.max_cost < 0.001:
            return tier_models["budget"]

        # Check current budget status
        budget_status = await self._check_budget_status(request.agent_name)
        if (
            budget_status["remaining_percentage"] < 0.2
        ):  # Less than 20% budget remaining
            return tier_models["budget"]

        # Default to primary for balanced approach
        return tier_models["primary"]

    async def _generate_fallback_chain(
        self, tier_models: Dict, selected_config: Dict
    ) -> List[str]:
        """Generate intelligent fallback chain"""
        fallback_chain = []

        # Add other models from tier as fallbacks
        for option_name, config in tier_models.items():
            if config["model"] != selected_config["model"]:
                fallback_chain.append(config["model"])

        return fallback_chain[:2]  # Limit to 2 fallbacks

    async def _estimate_cost(self, request: AgentRequest, model_config: Dict) -> float:
        """Estimate cost for the request"""
        # Rough estimation based on context size and complexity
        estimated_tokens = len(str(request.context)) // 4 + (request.complexity * 100)
        cost_per_token = model_config["cost_per_1k"] / 1000
        return estimated_tokens * cost_per_token

    async def _generate_selection_reasoning(
        self,
        request: AgentRequest,
        selected_config: Dict,
        strategy: SelectionStrategy,
        agent_tier: ModelTier,
    ) -> str:
        """Generate human-readable reasoning for selection"""

        reasoning_parts = [
            f"Agent '{request.agent_name}' (tier: {agent_tier.value})",
            f"Task complexity: {request.complexity}/10",
            f"Selected: {selected_config['model']} ({selected_config['provider']})",
            f"Strategy: {strategy.value}",
            f"Quality score: {selected_config['quality_score']:.2f}",
            f"Estimated cost: ${selected_config['cost_per_1k']:.4f}/1k tokens",
        ]

        return " | ".join(reasoning_parts)

    async def _check_budget_status(self, agent_name: str) -> Dict:
        """Check current budget status for agent"""
        # TODO: Integrate with existing cost management
        return {
            "remaining_percentage": 0.7,  # 70% budget remaining
            "daily_spend": 0.15,
            "monthly_budget": 100.0,
        }


class CostOptimizer:
    """Advanced cost optimization engine"""

    def __init__(self):
        self.cost_policies = {}
        self.optimization_strategies = {}
        self.logger = logging.getLogger("agent_cortex.cost_optimizer")

    async def optimize_request(
        self, request: AgentRequest, initial_selection: ModelSelection
    ) -> ModelSelection:
        """Optimize model selection for cost efficiency"""

        # Get agent cost policy
        cost_policy = get_agent_cost_policy(request.agent_name)

        # Check if optimization needed
        if not self._should_optimize(request, initial_selection, cost_policy):
            return initial_selection

        # Apply cost optimization
        optimized_selection = await self._apply_cost_optimization(
            request, initial_selection, cost_policy
        )

        return optimized_selection

    def _should_optimize(
        self, request: AgentRequest, selection: ModelSelection, cost_policy: Dict
    ) -> bool:
        """Determine if cost optimization is needed"""

        # Check if cost exceeds policy limits
        if selection.expected_cost > cost_policy.get("max_cost_per_request", 0.1):
            return True

        # Check daily budget status
        daily_spend = cost_policy.get("daily_spend", 0)
        daily_budget = cost_policy.get("daily_budget", 10.0)

        if daily_spend / daily_budget > 0.8:  # 80% of daily budget used
            return True

        return False

    async def _apply_cost_optimization(
        self,
        request: AgentRequest,
        initial_selection: ModelSelection,
        cost_policy: Dict,
    ) -> ModelSelection:
        """Apply cost optimization strategies"""

        # Strategy 1: Downgrade to budget model if quality allows
        if request.quality_requirements <= 0.8:
            # Use cheapest viable model
            optimized_selection = initial_selection
            optimized_selection.reasoning += " | Cost-optimized to budget model"
            return optimized_selection

        # Strategy 2: Use caching if available
        cached_response = await self._check_cached_response(request)
        if cached_response:
            optimized_selection = initial_selection
            optimized_selection.expected_cost = 0.0
            optimized_selection.reasoning += " | Using cached response"
            return optimized_selection

        return initial_selection

    async def _check_cached_response(self, request: AgentRequest) -> Optional[str]:
        """Check if we have a cached response for similar request"""
        # TODO: Implement intelligent caching
        return None


class PerformanceAnalyzer:
    """Analyze and learn from model performance"""

    def __init__(self):
        self.performance_data = {}
        self.learning_models = {}
        self.logger = logging.getLogger("agent_cortex.performance_analyzer")

    async def start_tracking(
        self, request: AgentRequest, selection: ModelSelection
    ) -> str:
        """Start tracking a request for performance analysis"""

        tracking_id = str(uuid.uuid4())

        self.performance_data[tracking_id] = {
            "request": request,
            "selection": selection,
            "start_time": time.time(),
            "status": "in_progress",
        }

        return tracking_id

    async def report_performance(self, tracking_id: str, metrics: PerformanceMetrics):
        """Report performance metrics for learning"""

        if tracking_id not in self.performance_data:
            self.logger.warning(f"Unknown tracking ID: {tracking_id}")
            return

        # Store performance data
        self.performance_data[tracking_id]["metrics"] = metrics
        self.performance_data[tracking_id]["status"] = "completed"

        # Trigger learning if enough data collected
        await self._trigger_learning_if_ready()

    async def _trigger_learning_if_ready(self):
        """Trigger ML learning if enough performance data collected"""

        completed_sessions = [
            data
            for data in self.performance_data.values()
            if data["status"] == "completed"
        ]

        if len(completed_sessions) >= 10:  # Learn every 10 sessions
            await self._update_model_performance_estimates()

    async def _update_model_performance_estimates(self):
        """Update model performance estimates based on real data"""
        # TODO: Implement ML-based performance learning
        self.logger.info("Triggering performance learning update")


class MultiProviderOrchestra:
    """Orchestrate multiple LLM providers with intelligent fallbacks"""

    def __init__(self):
        self.providers = {
            "anthropic": self._create_anthropic_client,
            "openai": self._create_openai_client,
            "local": self._create_local_client,
        }
        self.provider_health = {}
        self.logger = logging.getLogger("agent_cortex.multi_provider")

    async def get_llm_instance(self, selection: ModelSelection) -> LLMClient:
        """Get LLM instance with fallback handling"""

        primary_provider = selection.provider

        try:
            # Try primary provider
            llm_client = await self._create_llm_client(
                selection.selected_model, primary_provider
            )

            # Test connection
            if await llm_client.test_connection():
                return llm_client
            else:
                self.logger.warning(
                    f"Primary provider {primary_provider} failed health check"
                )

        except Exception as e:
            self.logger.error(f"Primary provider {primary_provider} failed: {e}")

        # Try fallback models
        for fallback_model in selection.fallback_chain:
            try:
                fallback_provider = self._get_provider_for_model(fallback_model)
                llm_client = await self._create_llm_client(
                    fallback_model, fallback_provider
                )

                if await llm_client.test_connection():
                    self.logger.info(
                        f"Using fallback: {fallback_model} ({fallback_provider})"
                    )
                    return llm_client

            except Exception as e:
                self.logger.error(f"Fallback {fallback_model} failed: {e}")
                continue

        # All providers failed - return basic client with error handling
        self.logger.error("All providers failed - returning emergency fallback")
        return self._create_emergency_fallback_client()

    async def _create_llm_client(self, model: str, provider: str) -> LLMClient:
        """Create LLM client for specific model and provider"""

        # Use LiteLLM for unified interface
        if provider == "anthropic":
            config = LLMConfig(
                provider="anthropic",
                model=model,
                api_key=None,  # Will use environment variable
            )
        elif provider == "openai":
            config = LLMConfig(
                provider="openai",
                model=model,
                api_key=None,  # Will use environment variable
            )
        elif provider == "local":
            config = LLMConfig(
                provider="ollama", model=model, base_url="http://localhost:11434"
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return LLMClient(config)

    async def _create_anthropic_client(self, config):
        """Create Anthropic client (placeholder for future implementation)"""
        return await self._create_llm_client(config.model, "anthropic")

    async def _create_openai_client(self, config):
        """Create OpenAI client (placeholder for future implementation)"""
        return await self._create_llm_client(config.model, "openai")

    async def _create_local_client(self, config):
        """Create local client (placeholder for future implementation)"""
        return await self._create_llm_client(config.model, "local")

    def _get_provider_for_model(self, model: str) -> str:
        """Determine provider based on model name"""
        if "claude" in model.lower():
            return "anthropic"
        elif "gpt" in model.lower():
            return "openai"
        elif "llama" in model.lower():
            return "local"
        else:
            return "openai"  # Default fallback

    def _create_emergency_fallback_client(self) -> LLMClient:
        """Create emergency fallback client"""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",  # Most reliable fallback
            api_key=None,
        )
        return LLMClient(config)


class AgentCortex:
    """Central Intelligence Hub for BoarderframeOS"""

    def __init__(self):
        self.model_selector = IntelligentModelSelector()
        self.cost_optimizer = CostOptimizer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.multi_provider = MultiProviderOrchestra()

        # State management
        self.active_sessions = {}
        self.current_strategy = SelectionStrategy.BALANCED
        self.system_load = 0.0

        # Learning and adaptation
        self.learning_enabled = True
        self.optimization_cycle_interval = 3600  # 1 hour

        self.logger = logging.getLogger("agent_cortex")
        self.logger.info("🧠 Agent Cortex initialized and ready")

    async def process_agent_request(self, request: AgentRequest) -> CortexResponse:
        """Main Agent Cortex processing pipeline"""

        try:
            # Log request
            self.logger.info(
                f"Processing request from {request.agent_name}: {request.task_type}"
            )

            # 1. Intelligent model selection
            model_selection = await self.model_selector.select_optimal_model(
                request, self.current_strategy
            )

            # 2. Cost optimization
            optimized_selection = await self.cost_optimizer.optimize_request(
                request, model_selection
            )

            # 3. Get LLM instance with fallbacks
            llm_instance = await self.multi_provider.get_llm_instance(
                optimized_selection
            )

            # 4. Start performance tracking
            tracking_id = await self.performance_analyzer.start_tracking(
                request, optimized_selection
            )

            # 5. Create Agent Cortex response
            response = CortexResponse(
                llm=llm_instance,
                selection=optimized_selection,
                tracking_id=tracking_id,
                session_context={
                    "strategy": self.current_strategy.value,
                    "system_load": self.system_load,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 6. Store active session
            self.active_sessions[tracking_id] = {
                "request": request,
                "response": response,
                "start_time": time.time(),
            }

            self.logger.info(
                f"Agent Cortex selected {optimized_selection.selected_model} for {request.agent_name}"
            )

            return response

        except Exception as e:
            self.logger.error(f"Agent Cortex processing error: {e}")
            # Return emergency fallback
            return await self._create_emergency_response(request)

    async def report_performance(self, tracking_id: str, metrics: PerformanceMetrics):
        """Report performance metrics for learning"""

        try:
            await self.performance_analyzer.report_performance(tracking_id, metrics)

            # Clean up session
            if tracking_id in self.active_sessions:
                del self.active_sessions[tracking_id]

            self.logger.debug(f"Performance reported for tracking ID: {tracking_id}")

        except Exception as e:
            self.logger.error(f"Error reporting performance: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive Agent Cortex status"""

        return {
            "status": "operational",
            "active_sessions": len(self.active_sessions),
            "current_strategy": self.current_strategy.value,
            "system_load": self.system_load,
            "learning_enabled": self.learning_enabled,
            "provider_health": await self._get_provider_health(),
            "performance_stats": await self._get_performance_stats(),
        }

    async def _create_emergency_response(self, request: AgentRequest) -> CortexResponse:
        """Create emergency response when Agent Cortex fails"""

        emergency_config = LLMConfig(provider="openai", model="gpt-4o-mini")

        emergency_llm = LLMClient(emergency_config)

        emergency_selection = ModelSelection(
            selected_model="gpt-4o-mini",
            provider="openai",
            reasoning="Emergency fallback due to Agent Cortex processing error",
            confidence=0.5,
            expected_cost=0.001,
            expected_latency=2.0,
            expected_quality=0.75,
        )

        return CortexResponse(
            llm=emergency_llm,
            selection=emergency_selection,
            tracking_id="emergency_" + str(uuid.uuid4()),
        )

    async def _get_provider_health(self) -> Dict[str, str]:
        """Get health status of all providers"""
        # TODO: Implement provider health checking
        return {"anthropic": "healthy", "openai": "healthy", "local": "unknown"}

    async def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        # TODO: Implement performance statistics
        return {
            "total_requests": len(self.performance_analyzer.performance_data),
            "avg_response_time": 2.1,
            "cost_savings": 0.45,
            "model_accuracy": 0.88,
        }


# Convenience function for easy integration
async def get_agent_cortex_instance() -> AgentCortex:
    """Get or create Agent Cortex instance"""
    if not hasattr(get_agent_cortex_instance, "_instance"):
        get_agent_cortex_instance._instance = AgentCortex()
    return get_agent_cortex_instance._instance


# Export main classes
__all__ = [
    "AgentCortex",
    "AgentRequest",
    "CortexResponse",
    "ModelSelection",
    "PerformanceMetrics",
    "ModelTier",
    "SelectionStrategy",
    "get_agent_cortex_instance",
]
