"""
LLM Cost Optimizer
Integrates policy engine with LLM client for automatic optimization
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import logging
import json
from datetime import datetime
from functools import wraps

from core.llm_policy_engine import get_policy_engine, PolicyAction, ModelTier
from core.secret_manager import get_secret

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of optimization process"""
    original_model: str
    optimized_model: str
    original_cost: float
    optimized_cost: float
    savings: float
    optimizations_applied: List[str]
    response: Optional[Any] = None
    from_cache: bool = False


class CostAwareLLMClient:
    """
    Cost-aware LLM client with automatic optimization
    
    Features:
    - Automatic model selection based on cost
    - Request caching
    - Token usage optimization
    - Cost tracking and reporting
    """
    
    def __init__(self, default_model: str = "claude-3-sonnet-20240229"):
        self.policy_engine = get_policy_engine()
        self.default_model = default_model
        self._response_cache = {}
        self._pending_batches: Dict[str, List[Dict]] = {}
        self._compression_strategies = {
            "summarize": self._compress_by_summary,
            "truncate": self._compress_by_truncation,
            "extract": self._compress_by_extraction
        }
        
    async def complete(self, prompt: str, model: Optional[str] = None, 
                      agent_name: str = "unknown", **kwargs) -> OptimizationResult:
        """Complete a prompt with cost optimization"""
        start_time = time.time()
        
        # Prepare context for policy evaluation
        context = {
            "prompt": prompt,
            "model": model or self.default_model,
            "agent_name": agent_name,
            "input_tokens": self._estimate_tokens(prompt),
            "estimated_output_tokens": kwargs.get("max_tokens", 500),
            "environment": kwargs.get("environment", "production"),
            "priority": kwargs.get("priority", "normal"),
            "request_type": self._classify_request(prompt),
            **kwargs
        }
        
        # Evaluate against policies
        policy_result = await self.policy_engine.evaluate_request(context)
        
        if not policy_result["allowed"]:
            logger.warning(f"Request denied by policy: {policy_result.get('reason')}")
            raise Exception(f"Request denied: {policy_result.get('reason')}")
        
        # Track original cost
        original_cost = policy_result["cost_estimate"]
        optimizations_applied = []
        
        # Apply optimizations
        optimized_model = policy_result["model"]
        optimized_prompt = prompt
        response = None
        from_cache = False
        
        # Handle modifications
        modifications = policy_result.get("modifications", {})
        
        # 1. Check cache
        if modifications.get("from_cache"):
            response = policy_result["cached_response"]
            from_cache = True
            optimizations_applied.append("cache_hit")
            logger.info(f"Cache hit for request from {agent_name}")
            
        # 2. Apply compression if needed
        elif modifications.get("compress"):
            target_reduction = modifications.get("target_reduction", 0.5)
            optimized_prompt = await self._compress_prompt(prompt, target_reduction)
            optimizations_applied.append(f"compressed_{int((1-target_reduction)*100)}%")
            logger.info(f"Compressed prompt from {len(prompt)} to {len(optimized_prompt)} chars")
            
        # 3. Handle throttling
        if modifications.get("delay"):
            delay = modifications["delay"]
            logger.info(f"Throttling request for {delay}s")
            await asyncio.sleep(delay)
            optimizations_applied.append(f"throttled_{delay}s")
            
        # 4. Handle batching
        if modifications.get("batch"):
            batch_params = modifications["batch_params"]
            response = await self._handle_batch_request(
                optimized_prompt, optimized_model, agent_name, batch_params
            )
            optimizations_applied.append("batched")
            
        # 5. Model downgrade tracking
        if modifications.get("downgraded"):
            optimizations_applied.append(f"downgraded_to_{optimized_model}")
            
        # 6. Model redirect tracking
        if modifications.get("redirected"):
            optimizations_applied.append(f"redirected_to_{optimized_model}")
            
        # Execute request if not from cache or batch
        if response is None and not from_cache:
            response = await self._execute_request(
                optimized_prompt, optimized_model, **kwargs
            )
            
            # Cache the response if policy allows
            for action in policy_result.get("actions", []):
                if action["action"] == PolicyAction.CACHE.value:
                    cache_key = self._get_cache_key(optimized_model, optimized_prompt)
                    self._response_cache[cache_key] = {
                        "response": response,
                        "timestamp": datetime.now(),
                        "ttl": action["parameters"].get("ttl", 3600)
                    }
                    
        # Track usage
        actual_output_tokens = self._count_response_tokens(response)
        await self.policy_engine.track_usage(
            optimized_model,
            self._estimate_tokens(optimized_prompt),
            actual_output_tokens,
            agent_name
        )
        
        # Calculate optimized cost
        optimized_cost = self.policy_engine._estimate_cost(
            optimized_model,
            self._estimate_tokens(optimized_prompt),
            actual_output_tokens
        )
        
        # Log optimization results
        savings = original_cost - optimized_cost
        if savings > 0:
            logger.info(f"Saved ${savings:.4f} ({(savings/original_cost*100):.1f}%) for {agent_name}")
            
        return OptimizationResult(
            original_model=context["model"],
            optimized_model=optimized_model,
            original_cost=original_cost,
            optimized_cost=optimized_cost,
            savings=savings,
            optimizations_applied=optimizations_applied,
            response=response,
            from_cache=from_cache
        )
        
    async def _execute_request(self, prompt: str, model: str, **kwargs) -> str:
        """Execute the actual LLM request"""
        # This would integrate with the actual LLM client
        # For now, we'll simulate based on model
        
        if model.startswith("claude"):
            # Anthropic API call
            api_key = get_secret("ANTHROPIC_API_KEY")
            # Actual implementation would use anthropic client
            return f"[Claude Response to: {prompt[:50]}...]"
            
        elif model.startswith("gpt"):
            # OpenAI API call
            api_key = get_secret("OPENAI_API_KEY")
            # Actual implementation would use openai client
            return f"[GPT Response to: {prompt[:50]}...]"
            
        elif model == "llama2-7b":
            # Local model call
            return f"[Local Model Response to: {prompt[:50]}...]"
            
        else:
            raise ValueError(f"Unknown model: {model}")
            
    async def _compress_prompt(self, prompt: str, target_reduction: float) -> str:
        """Compress prompt to reduce tokens"""
        strategy = "summarize"  # Default strategy
        
        if strategy in self._compression_strategies:
            return await self._compression_strategies[strategy](prompt, target_reduction)
        
        # Fallback: simple truncation
        target_length = int(len(prompt) * (1 - target_reduction))
        return prompt[:target_length] + "..."
        
    async def _compress_by_summary(self, prompt: str, target_reduction: float) -> str:
        """Compress by summarizing"""
        # Use a cheap model to summarize
        summary_prompt = f"Summarize the following in {int((1-target_reduction)*100)}% of the length:\n\n{prompt}"
        
        # Use economy tier model
        result = await self.complete(
            summary_prompt,
            model="claude-instant-1.2",
            agent_name="compression_engine",
            no_cache=True  # Don't cache compression requests
        )
        
        return result.response
        
    async def _compress_by_truncation(self, prompt: str, target_reduction: float) -> str:
        """Compress by intelligent truncation"""
        # Keep beginning and end, remove middle
        target_length = int(len(prompt) * (1 - target_reduction))
        
        if len(prompt) <= target_length:
            return prompt
            
        keep_start = target_length // 2
        keep_end = target_length - keep_start
        
        return f"{prompt[:keep_start]}\n...[truncated]...\n{prompt[-keep_end:]}"
        
    async def _compress_by_extraction(self, prompt: str, target_reduction: float) -> str:
        """Compress by extracting key information"""
        # Extract key sentences
        sentences = prompt.split('. ')
        
        # Simple importance scoring (can be enhanced)
        important_sentences = []
        keywords = ["important", "critical", "must", "required", "key"]
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                important_sentences.append(sentence)
                
        # Add more sentences if needed
        target_sentences = int(len(sentences) * (1 - target_reduction))
        if len(important_sentences) < target_sentences:
            # Add remaining sentences
            for sentence in sentences:
                if sentence not in important_sentences:
                    important_sentences.append(sentence)
                if len(important_sentences) >= target_sentences:
                    break
                    
        return '. '.join(important_sentences[:target_sentences])
        
    async def _handle_batch_request(self, prompt: str, model: str, 
                                   agent_name: str, batch_params: Dict) -> str:
        """Handle batched requests"""
        batch_key = f"{model}:{agent_name}"
        
        if batch_key not in self._pending_batches:
            self._pending_batches[batch_key] = []
            
        # Add to batch
        self._pending_batches[batch_key].append({
            "prompt": prompt,
            "timestamp": time.time()
        })
        
        # Check if batch is ready
        max_size = batch_params.get("max_batch_size", 5)
        wait_time = batch_params.get("wait_time", 2.0)
        
        if len(self._pending_batches[batch_key]) >= max_size:
            # Execute batch
            return await self._execute_batch(batch_key, model)
            
        # Wait for more requests
        await asyncio.sleep(wait_time)
        
        # Execute whatever is in the batch
        return await self._execute_batch(batch_key, model)
        
    async def _execute_batch(self, batch_key: str, model: str) -> str:
        """Execute a batch of requests"""
        if batch_key not in self._pending_batches:
            return ""
            
        batch = self._pending_batches[batch_key]
        if not batch:
            return ""
            
        # Combine prompts
        combined_prompt = "\n---\n".join([item["prompt"] for item in batch])
        
        # Execute combined request
        response = await self._execute_request(combined_prompt, model)
        
        # Clear batch
        self._pending_batches[batch_key] = []
        
        return response
        
    def _classify_request(self, prompt: str) -> str:
        """Classify request type for policy evaluation"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["classify", "categorize", "label"]):
            return "classification"
        elif any(word in prompt_lower for word in ["summarize", "summary", "brief"]):
            return "summarization"
        elif any(word in prompt_lower for word in ["extract", "find", "identify"]):
            return "extraction"
        elif any(word in prompt_lower for word in ["analyze", "explain", "understand"]):
            return "analysis"
        elif any(word in prompt_lower for word in ["generate", "create", "write"]):
            return "generation"
        else:
            return "general"
            
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        # More accurate estimation based on model
        # Claude/GPT average ~3.5 characters per token
        return len(text) // 3
        
    def _count_response_tokens(self, response: Any) -> int:
        """Count tokens in response"""
        if response is None:
            return 0
        
        # Convert to string if needed
        response_text = str(response)
        return self._estimate_tokens(response_text)
        
    def _get_cache_key(self, model: str, prompt: str) -> str:
        """Generate cache key"""
        import hashlib
        prompt_hash = hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()
        return prompt_hash
        
    def get_cost_report(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get cost optimization report"""
        usage_report = self.policy_engine.get_usage_report(agent_name)
        
        # Add optimization metrics
        if agent_name:
            metrics = self.policy_engine.usage_metrics[agent_name]
            
            usage_report["optimization_metrics"] = {
                "cache_hit_rate": metrics.cache_hits / max(metrics.cache_hits + metrics.cache_misses, 1),
                "throttled_requests": metrics.throttled_requests,
                "denied_requests": metrics.denied_requests,
                "downgraded_requests": metrics.downgraded_requests
            }
            
        return usage_report


def cost_optimized(func: Callable) -> Callable:
    """Decorator to add cost optimization to LLM calls"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract prompt and model from function arguments
        prompt = kwargs.get("prompt") or (args[0] if args else "")
        model = kwargs.get("model")
        agent_name = kwargs.get("agent_name", func.__name__)
        
        # Use cost-aware client
        client = CostAwareLLMClient()
        
        # Get optimization result
        result = await client.complete(
            prompt=prompt,
            model=model,
            agent_name=agent_name,
            **kwargs
        )
        
        # Log optimization details
        if result.savings > 0:
            logger.info(f"{func.__name__} saved ${result.savings:.4f} using {', '.join(result.optimizations_applied)}")
            
        # Return just the response for compatibility
        return result.response
        
    return wrapper