"""
LLM Policy Engine for Cost Optimization
Intelligent policy-based management of LLM API calls
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Actions that policies can take"""
    ALLOW = "allow"
    DENY = "deny"
    THROTTLE = "throttle"
    CACHE = "cache"
    DOWNGRADE = "downgrade"
    COMPRESS = "compress"
    BATCH = "batch"
    REDIRECT = "redirect"


class ModelTier(Enum):
    """LLM model tiers for cost optimization"""
    PREMIUM = "premium"      # Claude-3-opus, GPT-4
    STANDARD = "standard"    # Claude-3-sonnet, GPT-3.5
    ECONOMY = "economy"      # Claude-instant, smaller models
    LOCAL = "local"          # Local models (no API cost)


@dataclass
class ModelCost:
    """Cost information for a model"""
    model_name: str
    tier: ModelTier
    input_cost_per_1k: float  # Cost per 1k input tokens
    output_cost_per_1k: float  # Cost per 1k output tokens
    max_context: int
    capabilities: List[str] = field(default_factory=list)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost


@dataclass
class PolicyRule:
    """Individual policy rule"""
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    action: PolicyAction
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True
    
    def evaluate(self, context: Dict[str, Any]) -> Optional[Tuple[PolicyAction, Dict[str, Any]]]:
        """Evaluate rule against context"""
        if not self.enabled:
            return None
            
        try:
            if self.condition(context):
                return (self.action, self.parameters)
        except Exception as e:
            logger.error(f"Policy rule '{self.name}' evaluation error: {e}")
            
        return None


@dataclass
class UsageMetrics:
    """Track usage metrics for cost analysis"""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    throttled_requests: int = 0
    denied_requests: int = 0
    downgraded_requests: int = 0
    
    def add_request(self, input_tokens: int, output_tokens: int, cost: float):
        """Add a request to metrics"""
        self.total_requests += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost


class LLMPolicyEngine:
    """
    Policy engine for LLM cost optimization
    
    Features:
    - Model tier management
    - Cost-based routing
    - Rate limiting and throttling
    - Intelligent caching
    - Request batching
    - Usage analytics
    """
    
    def __init__(self):
        self.policies: List[PolicyRule] = []
        self.model_costs = self._initialize_model_costs()
        self.usage_metrics: Dict[str, UsageMetrics] = defaultdict(UsageMetrics)
        self.cache: Dict[str, Any] = {}
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self.cost_budget = {
            "daily": 100.0,
            "monthly": 2000.0
        }
        self.current_spend = {
            "daily": 0.0,
            "monthly": 0.0
        }
        
        # Initialize default policies
        self._initialize_default_policies()
    
    async def initialize(self):
        """Async initialization for startup compatibility"""
        # Any async initialization can go here
        logger.info("LLM Policy Engine initialized successfully")
        logger.info(f"Loaded {len(self.policies)} policies")
        logger.info(f"Daily budget: ${self.cost_budget['daily']}")
        logger.info(f"Monthly budget: ${self.cost_budget['monthly']}")
        return True
    
    async def load_default_policies(self):
        """Load default policies - returns number of policies loaded"""
        # Policies are already loaded in __init__ via _initialize_default_policies
        return len(self.policies)
        
    def _initialize_model_costs(self) -> Dict[str, ModelCost]:
        """Initialize model cost information"""
        return {
            # Anthropic models
            "claude-3-opus-20240229": ModelCost(
                model_name="claude-3-opus-20240229",
                tier=ModelTier.PREMIUM,
                input_cost_per_1k=0.015,
                output_cost_per_1k=0.075,
                max_context=200000,
                capabilities=["complex_reasoning", "coding", "analysis"]
            ),
            "claude-3-sonnet-20240229": ModelCost(
                model_name="claude-3-sonnet-20240229",
                tier=ModelTier.STANDARD,
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
                max_context=200000,
                capabilities=["general", "coding", "analysis"]
            ),
            "claude-instant-1.2": ModelCost(
                model_name="claude-instant-1.2",
                tier=ModelTier.ECONOMY,
                input_cost_per_1k=0.00008,
                output_cost_per_1k=0.00024,
                max_context=100000,
                capabilities=["general", "simple_tasks"]
            ),
            
            # OpenAI models
            "gpt-4": ModelCost(
                model_name="gpt-4",
                tier=ModelTier.PREMIUM,
                input_cost_per_1k=0.03,
                output_cost_per_1k=0.06,
                max_context=8192,
                capabilities=["complex_reasoning", "coding", "analysis"]
            ),
            "gpt-3.5-turbo": ModelCost(
                model_name="gpt-3.5-turbo",
                tier=ModelTier.STANDARD,
                input_cost_per_1k=0.0005,
                output_cost_per_1k=0.0015,
                max_context=16384,
                capabilities=["general", "coding"]
            ),
            
            # Local models (no cost)
            "llama2-7b": ModelCost(
                model_name="llama2-7b",
                tier=ModelTier.LOCAL,
                input_cost_per_1k=0.0,
                output_cost_per_1k=0.0,
                max_context=4096,
                capabilities=["general", "simple_tasks"]
            )
        }
        
    def _initialize_default_policies(self):
        """Initialize default cost optimization policies"""
        
        # Policy 1: Budget protection
        self.add_policy(PolicyRule(
            name="daily_budget_protection",
            description="Deny requests when daily budget exceeded",
            condition=lambda ctx: self.current_spend["daily"] >= self.cost_budget["daily"],
            action=PolicyAction.DENY,
            parameters={"reason": "Daily budget exceeded"},
            priority=100
        ))
        
        # Policy 2: High-cost request throttling
        self.add_policy(PolicyRule(
            name="high_cost_throttle",
            description="Throttle high-cost model requests",
            condition=lambda ctx: ctx.get("model_tier") == ModelTier.PREMIUM and self._get_request_rate(ctx.get("agent_name", "unknown")) > 10,
            action=PolicyAction.THROTTLE,
            parameters={"delay": 5.0, "max_rate": 10},
            priority=90
        ))
        
        # Policy 3: Cache repeated requests
        self.add_policy(PolicyRule(
            name="cache_repeated",
            description="Cache responses for repeated requests",
            condition=lambda ctx: self._is_cacheable_request(ctx),
            action=PolicyAction.CACHE,
            parameters={"ttl": 3600},
            priority=80
        ))
        
        # Policy 4: Downgrade for simple tasks
        self.add_policy(PolicyRule(
            name="downgrade_simple",
            description="Use cheaper models for simple tasks",
            condition=lambda ctx: self._is_simple_task(ctx) and ctx.get("model_tier") == ModelTier.PREMIUM,
            action=PolicyAction.DOWNGRADE,
            parameters={"target_tier": ModelTier.STANDARD},
            priority=70
        ))
        
        # Policy 5: Compress long contexts
        self.add_policy(PolicyRule(
            name="compress_context",
            description="Compress context for long prompts",
            condition=lambda ctx: ctx.get("input_tokens", 0) > 10000,
            action=PolicyAction.COMPRESS,
            parameters={"target_reduction": 0.5},
            priority=60
        ))
        
        # Policy 6: Batch similar requests
        self.add_policy(PolicyRule(
            name="batch_requests",
            description="Batch similar requests together",
            condition=lambda ctx: self._can_batch_request(ctx),
            action=PolicyAction.BATCH,
            parameters={"max_batch_size": 5, "wait_time": 2.0},
            priority=50
        ))
        
        # Policy 7: Use local models for dev/test
        self.add_policy(PolicyRule(
            name="local_for_dev",
            description="Use local models in development",
            condition=lambda ctx: ctx.get("environment") == "development",
            action=PolicyAction.REDIRECT,
            parameters={"target_model": "llama2-7b"},
            priority=40
        ))
        
    def add_policy(self, policy: PolicyRule):
        """Add a policy rule"""
        self.policies.append(policy)
        # Sort by priority (higher priority first)
        self.policies.sort(key=lambda p: p.priority, reverse=True)
        
    def remove_policy(self, policy_name: str):
        """Remove a policy by name"""
        self.policies = [p for p in self.policies if p.name != policy_name]
        
    async def evaluate_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a request against all policies"""
        result = {
            "allowed": True,
            "actions": [],
            "model": context.get("model"),
            "modifications": {},
            "cost_estimate": 0.0
        }
        
        # Add context enrichment
        context = self._enrich_context(context)
        
        # Evaluate all policies
        for policy in self.policies:
            evaluation = policy.evaluate(context)
            
            if evaluation:
                action, parameters = evaluation
                result["actions"].append({
                    "policy": policy.name,
                    "action": action.value,
                    "parameters": parameters
                })
                
                # Handle specific actions
                if action == PolicyAction.DENY:
                    result["allowed"] = False
                    result["reason"] = parameters.get("reason", "Policy denied request")
                    break
                    
                elif action == PolicyAction.THROTTLE:
                    result["modifications"]["delay"] = parameters.get("delay", 1.0)
                    
                elif action == PolicyAction.DOWNGRADE:
                    target_tier = parameters.get("target_tier")
                    new_model = self._get_model_for_tier(target_tier)
                    if new_model:
                        result["model"] = new_model
                        result["modifications"]["downgraded"] = True
                        
                elif action == PolicyAction.CACHE:
                    cache_key = self._get_cache_key(context)
                    if cache_key in self.cache:
                        result["cached_response"] = self.cache[cache_key]
                        result["modifications"]["from_cache"] = True
                        
                elif action == PolicyAction.COMPRESS:
                    result["modifications"]["compress"] = True
                    result["modifications"]["target_reduction"] = parameters.get("target_reduction", 0.5)
                    
                elif action == PolicyAction.BATCH:
                    result["modifications"]["batch"] = True
                    result["modifications"]["batch_params"] = parameters
                    
                elif action == PolicyAction.REDIRECT:
                    result["model"] = parameters.get("target_model")
                    result["modifications"]["redirected"] = True
        
        # Calculate cost estimate
        if result["allowed"]:
            result["cost_estimate"] = self._estimate_cost(
                result["model"],
                context.get("input_tokens", 0),
                context.get("estimated_output_tokens", 500)
            )
        
        return result
        
    def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich context with additional information"""
        enriched = context.copy()
        
        # Add model tier
        model = context.get("model")
        if model and model in self.model_costs:
            enriched["model_tier"] = self.model_costs[model].tier
            
        # Add current spend info
        enriched["current_daily_spend"] = self.current_spend["daily"]
        enriched["current_monthly_spend"] = self.current_spend["monthly"]
        
        # Add timestamp
        enriched["timestamp"] = datetime.now()
        
        # Estimate tokens if not provided
        if "input_tokens" not in enriched and "prompt" in enriched:
            enriched["input_tokens"] = self._estimate_tokens(enriched["prompt"])
            
        return enriched
        
    def _get_request_rate(self, agent_name: str) -> float:
        """Get request rate for an agent (requests per minute)"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Clean old entries
        self.rate_limits[agent_name] = [
            ts for ts in self.rate_limits[agent_name] if ts > cutoff
        ]
        
        return len(self.rate_limits[agent_name])
        
    def _is_cacheable_request(self, context: Dict[str, Any]) -> bool:
        """Check if request is cacheable"""
        # Don't cache if explicitly disabled
        if context.get("no_cache", False):
            return False
            
        # Check if it's a deterministic request
        prompt = context.get("prompt", "")
        
        # Simple heuristic: cache factual questions
        factual_patterns = [
            r"what is",
            r"define",
            r"explain",
            r"list",
            r"describe"
        ]
        
        return any(re.search(pattern, prompt.lower()) for pattern in factual_patterns)
        
    def _is_simple_task(self, context: Dict[str, Any]) -> bool:
        """Check if task is simple enough for downgrade"""
        prompt = context.get("prompt", "")
        
        # Simple task indicators
        simple_patterns = [
            r"^(yes|no)",
            r"^(true|false)",
            r"summarize in \d+ words",
            r"classify",
            r"categorize"
        ]
        
        # Complex task indicators
        complex_patterns = [
            r"analyze",
            r"debug",
            r"implement",
            r"design",
            r"optimize"
        ]
        
        # Check for simple patterns
        if any(re.search(pattern, prompt.lower()) for pattern in simple_patterns):
            return True
            
        # Check for complex patterns
        if any(re.search(pattern, prompt.lower()) for pattern in complex_patterns):
            return False
            
        # Check token count
        return context.get("input_tokens", 0) < 1000
        
    def _can_batch_request(self, context: Dict[str, Any]) -> bool:
        """Check if request can be batched"""
        # Don't batch urgent requests
        if context.get("priority") == "urgent":
            return False
            
        # Check if it's a batchable type
        request_type = context.get("request_type")
        batchable_types = ["classification", "extraction", "summarization"]
        
        return request_type in batchable_types
        
    def _get_model_for_tier(self, tier: ModelTier) -> Optional[str]:
        """Get a model for a specific tier"""
        for model_name, model_cost in self.model_costs.items():
            if model_cost.tier == tier:
                return model_name
        return None
        
    def _get_cache_key(self, context: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Use model + prompt hash
        model = context.get("model", "unknown")
        prompt = context.get("prompt", "")
        
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        
        return f"{model}:{prompt_hash}"
        
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Simple estimation: ~4 characters per token
        return len(text) // 4
        
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request"""
        if model not in self.model_costs:
            return 0.0
            
        model_cost = self.model_costs[model]
        return model_cost.calculate_cost(input_tokens, output_tokens)
        
    async def track_usage(self, model: str, input_tokens: int, output_tokens: int, 
                         agent_name: str, success: bool = True):
        """Track usage for analytics"""
        cost = self._estimate_cost(model, input_tokens, output_tokens)
        
        # Update metrics
        metrics = self.usage_metrics[agent_name]
        metrics.add_request(input_tokens, output_tokens, cost)
        
        # Update spend tracking
        self.current_spend["daily"] += cost
        self.current_spend["monthly"] += cost
        
        # Update rate limits
        self.rate_limits[agent_name].append(datetime.now())
        
        # Log high-cost requests
        if cost > 1.0:
            logger.warning(f"High-cost request: ${cost:.2f} for {agent_name} using {model}")
            
    def get_usage_report(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get usage report"""
        if agent_name:
            metrics = self.usage_metrics[agent_name]
            return {
                "agent": agent_name,
                "total_requests": metrics.total_requests,
                "total_cost": metrics.total_cost,
                "average_cost": metrics.total_cost / max(metrics.total_requests, 1),
                "total_tokens": metrics.total_input_tokens + metrics.total_output_tokens,
                "cache_hit_rate": metrics.cache_hits / max(metrics.cache_hits + metrics.cache_misses, 1)
            }
        else:
            # Aggregate report
            total_cost = sum(m.total_cost for m in self.usage_metrics.values())
            total_requests = sum(m.total_requests for m in self.usage_metrics.values())
            
            return {
                "total_cost": total_cost,
                "total_requests": total_requests,
                "daily_spend": self.current_spend["daily"],
                "monthly_spend": self.current_spend["monthly"],
                "daily_budget_remaining": self.cost_budget["daily"] - self.current_spend["daily"],
                "top_spenders": self._get_top_spenders(5)
            }
            
    def _get_top_spenders(self, limit: int) -> List[Dict[str, Any]]:
        """Get top spending agents"""
        agent_costs = [
            {"agent": agent, "cost": metrics.total_cost}
            for agent, metrics in self.usage_metrics.items()
        ]
        
        agent_costs.sort(key=lambda x: x["cost"], reverse=True)
        return agent_costs[:limit]
        
    def set_budget(self, daily: Optional[float] = None, monthly: Optional[float] = None):
        """Set cost budgets"""
        if daily is not None:
            self.cost_budget["daily"] = daily
        if monthly is not None:
            self.cost_budget["monthly"] = monthly
            
    def reset_daily_spend(self):
        """Reset daily spend (call this daily)"""
        self.current_spend["daily"] = 0.0
        
    def reset_monthly_spend(self):
        """Reset monthly spend (call this monthly)"""
        self.current_spend["monthly"] = 0.0
        
    def get_model_recommendations(self, task_type: str, max_cost: float) -> List[str]:
        """Get model recommendations for a task type within budget"""
        recommendations = []
        
        for model_name, model_cost in self.model_costs.items():
            # Check if model supports the task
            if task_type in model_cost.capabilities:
                # Estimate cost for typical request
                typical_cost = model_cost.calculate_cost(1000, 500)
                
                if typical_cost <= max_cost:
                    recommendations.append({
                        "model": model_name,
                        "tier": model_cost.tier.value,
                        "estimated_cost": typical_cost,
                        "capabilities": model_cost.capabilities
                    })
                    
        # Sort by cost (cheapest first)
        recommendations.sort(key=lambda x: x["estimated_cost"])
        
        return recommendations


# Global policy engine instance
_policy_engine = None


def get_policy_engine() -> LLMPolicyEngine:
    """Get the global policy engine instance"""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = LLMPolicyEngine()
    return _policy_engine