"""
LLMMixin - Language model interaction layer
Manages LLM calls with cost tracking and fallback logic
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass
import json


@dataclass
class LLMResponse:
    """Response from LLM call"""
    content: str
    model_used: str
    tokens_used: Dict[str, int]  # input, output, total
    cost: float
    latency_ms: float
    metadata: Dict[str, Any]


@dataclass 
class ModelConfig:
    """Configuration for an LLM model"""
    name: str
    provider: str  # openai, anthropic, local
    max_tokens: int
    temperature: float
    cost_per_1k_input: float
    cost_per_1k_output: float
    rate_limit_rpm: int
    timeout_seconds: int
    supports_tools: bool = False
    supports_vision: bool = False


class LLMMixin:
    """LLM interaction capabilities"""
    
    # Model configurations with pricing
    MODEL_CONFIGS = {
        "claude-3-opus": ModelConfig(
            name="claude-3-opus-20240229",
            provider="anthropic",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
            rate_limit_rpm=1000,
            timeout_seconds=60,
            supports_tools=True,
            supports_vision=True
        ),
        "claude-3-sonnet": ModelConfig(
            name="claude-3-sonnet-20240229", 
            provider="anthropic",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            rate_limit_rpm=2000,
            timeout_seconds=30,
            supports_tools=True,
            supports_vision=True
        ),
        "claude-3-haiku": ModelConfig(
            name="claude-3-haiku-20240307",
            provider="anthropic",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            rate_limit_rpm=4000,
            timeout_seconds=20,
            supports_tools=True,
            supports_vision=True
        ),
        "gpt-4-turbo": ModelConfig(
            name="gpt-4-turbo-preview",
            provider="openai",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
            rate_limit_rpm=500,
            timeout_seconds=60,
            supports_tools=True,
            supports_vision=True
        ),
        "gpt-3.5-turbo": ModelConfig(
            name="gpt-3.5-turbo",
            provider="openai",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_input=0.0005,
            cost_per_1k_output=0.0015,
            rate_limit_rpm=3500,
            timeout_seconds=20,
            supports_tools=True,
            supports_vision=False
        )
    }
    
    def __init__(self):
        """Initialize LLM interaction layer"""
        self.llm_call_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        self.total_tokens_used = {"input": 0, "output": 0}
        self.total_cost = 0.0
        self.model_usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Rate limiting
        self.rate_limiter: Dict[str, List[float]] = {}  # model -> timestamps
        
        # Cost controls
        self.max_cost_per_call = 0.1  # $0.10
        self.max_cost_per_hour = 10.0  # $10.00
        self.hourly_costs: List[Tuple[float, float]] = []  # (timestamp, cost)
        
    async def generate_llm_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[str]] = None
    ) -> LLMResponse:
        """Generate response from LLM with automatic fallback"""
        
        # Use configured model or default
        if model is None:
            model = getattr(self, 'llm_model', 'claude-3-sonnet')
            
        # Get model config
        if model not in self.MODEL_CONFIGS:
            raise ValueError(f"Unknown model: {model}")
            
        config = self.MODEL_CONFIGS[model]
        
        # Check rate limits
        if not await self._check_rate_limit(model):
            # Try fallback model
            fallback = self._get_fallback_model(model)
            if fallback:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.warning(f"Rate limited on {model}, falling back to {fallback}")
                return await self.generate_llm_response(
                    prompt, fallback, system_prompt, temperature, max_tokens, tools, images
                )
            else:
                raise Exception(f"Rate limited on {model} with no fallback available")
                
        # Check cost limits
        estimated_cost = self._estimate_cost(prompt, config, max_tokens)
        if not await self._check_cost_limits(estimated_cost):
            raise Exception(f"Cost limit exceeded. Estimated cost: ${estimated_cost:.4f}")
            
        # Prepare the call
        start_time = time.time()
        
        try:
            # Call appropriate provider
            if config.provider == "anthropic":
                response = await self._call_anthropic(
                    prompt, config, system_prompt, temperature, max_tokens, tools, images
                )
            elif config.provider == "openai":
                response = await self._call_openai(
                    prompt, config, system_prompt, temperature, max_tokens, tools, images
                )
            else:
                raise ValueError(f"Unknown provider: {config.provider}")
                
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            tokens_used = response.get("usage", {})
            actual_cost = self._calculate_actual_cost(tokens_used, config)
            
            # Update statistics
            await self._update_statistics(model, tokens_used, actual_cost, latency_ms, True)
            
            # Record the call
            self._record_llm_call(model, prompt, response["content"], tokens_used, actual_cost, latency_ms, True)
            
            return LLMResponse(
                content=response["content"],
                model_used=model,
                tokens_used=tokens_used,
                cost=actual_cost,
                latency_ms=latency_ms,
                metadata=response.get("metadata", {})
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            # Try fallback on error
            fallback = self._get_fallback_model(model)
            if fallback:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.warning(f"Error with {model}: {e}. Trying fallback {fallback}")
                return await self.generate_llm_response(
                    prompt, fallback, system_prompt, temperature, max_tokens, tools, images
                )
            else:
                # Record failure
                await self._update_statistics(model, {}, 0, latency_ms, False)
                self._record_llm_call(model, prompt, None, {}, 0, latency_ms, False, str(e))
                raise
                
    async def generate_with_retry(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """Generate response with automatic retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.generate_llm_response(prompt, model, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.warning(f"LLM call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    
        raise Exception(f"LLM call failed after {max_retries} attempts: {last_error}")
        
    async def stream_llm_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from LLM"""
        # Implementation would stream tokens as they arrive
        # For now, return full response
        response = await self.generate_llm_response(prompt, model, **kwargs)
        yield response.content
        
    def get_llm_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive LLM usage report"""
        return {
            "total_calls": len(self.llm_call_history),
            "total_tokens": self.total_tokens_used,
            "total_cost": round(self.total_cost, 4),
            "model_breakdown": self.model_usage_stats,
            "average_latency_ms": self._calculate_average_latency(),
            "success_rate": self._calculate_success_rate(),
            "cost_by_hour": self._get_hourly_costs()
        }
        
    async def _call_anthropic(
        self,
        prompt: str,
        config: ModelConfig,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        tools: Optional[List[Dict[str, Any]]],
        images: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Call Anthropic API"""
        # This would integrate with actual Anthropic client
        # For now, return mock response
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        # Mock response
        content = f"Mock response from {config.name} for prompt: {prompt[:50]}..."
        tokens = {
            "input": len(prompt.split()) * 2,  # Rough estimate
            "output": len(content.split()) * 2,
            "total": 0
        }
        tokens["total"] = tokens["input"] + tokens["output"]
        
        return {
            "content": content,
            "usage": tokens,
            "metadata": {
                "model": config.name,
                "temperature": temperature or config.temperature
            }
        }
        
    async def _call_openai(
        self,
        prompt: str,
        config: ModelConfig,
        system_prompt: Optional[str],
        temperature: Optional[float], 
        max_tokens: Optional[int],
        tools: Optional[List[Dict[str, Any]]],
        images: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Call OpenAI API"""
        # This would integrate with actual OpenAI client
        # For now, return mock response
        
        # Simulate API call
        await asyncio.sleep(0.1)
        
        # Mock response
        content = f"Mock response from {config.name} for prompt: {prompt[:50]}..."
        tokens = {
            "input": len(prompt.split()) * 2,
            "output": len(content.split()) * 2,
            "total": 0
        }
        tokens["total"] = tokens["input"] + tokens["output"]
        
        return {
            "content": content,
            "usage": tokens,
            "metadata": {
                "model": config.name,
                "temperature": temperature or config.temperature
            }
        }
        
    async def _check_rate_limit(self, model: str) -> bool:
        """Check if we're within rate limits"""
        config = self.MODEL_CONFIGS[model]
        current_time = time.time()
        
        # Initialize rate limiter for model
        if model not in self.rate_limiter:
            self.rate_limiter[model] = []
            
        # Remove old timestamps (older than 1 minute)
        self.rate_limiter[model] = [
            ts for ts in self.rate_limiter[model] 
            if current_time - ts < 60
        ]
        
        # Check if we can make a call
        if len(self.rate_limiter[model]) < config.rate_limit_rpm:
            self.rate_limiter[model].append(current_time)
            return True
            
        return False
        
    async def _check_cost_limits(self, estimated_cost: float) -> bool:
        """Check if we're within cost limits"""
        # Check per-call limit
        if estimated_cost > self.max_cost_per_call:
            return False
            
        # Check hourly limit
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Remove old entries
        self.hourly_costs = [
            (ts, cost) for ts, cost in self.hourly_costs
            if ts > hour_ago
        ]
        
        # Calculate hourly total
        hourly_total = sum(cost for _, cost in self.hourly_costs)
        
        if hourly_total + estimated_cost > self.max_cost_per_hour:
            return False
            
        return True
        
    def _estimate_cost(self, prompt: str, config: ModelConfig, max_tokens: Optional[int]) -> float:
        """Estimate cost of LLM call"""
        # Rough token estimation
        input_tokens = len(prompt.split()) * 1.5  # Approximate
        output_tokens = (max_tokens or config.max_tokens) * 0.7  # Assume 70% usage
        
        input_cost = (input_tokens / 1000) * config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * config.cost_per_1k_output
        
        return input_cost + output_cost
        
    def _calculate_actual_cost(self, tokens_used: Dict[str, int], config: ModelConfig) -> float:
        """Calculate actual cost based on token usage"""
        input_tokens = tokens_used.get("input", 0)
        output_tokens = tokens_used.get("output", 0)
        
        input_cost = (input_tokens / 1000) * config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * config.cost_per_1k_output
        
        return round(input_cost + output_cost, 6)
        
    def _get_fallback_model(self, primary_model: str) -> Optional[str]:
        """Get fallback model for primary"""
        fallback_chain = {
            "claude-3-opus": "claude-3-sonnet",
            "claude-3-sonnet": "claude-3-haiku",
            "claude-3-haiku": "gpt-3.5-turbo",
            "gpt-4-turbo": "gpt-3.5-turbo",
            "gpt-3.5-turbo": "claude-3-haiku"
        }
        
        return fallback_chain.get(primary_model)
        
    async def _update_statistics(
        self,
        model: str,
        tokens_used: Dict[str, int],
        cost: float,
        latency_ms: float,
        success: bool
    ) -> None:
        """Update usage statistics"""
        # Update total counters
        self.total_tokens_used["input"] += tokens_used.get("input", 0)
        self.total_tokens_used["output"] += tokens_used.get("output", 0)
        self.total_cost += cost
        
        # Add to hourly costs
        if cost > 0:
            self.hourly_costs.append((time.time(), cost))
            
        # Update model-specific stats
        if model not in self.model_usage_stats:
            self.model_usage_stats[model] = {
                "calls": 0,
                "successful_calls": 0,
                "tokens": {"input": 0, "output": 0},
                "total_cost": 0.0,
                "total_latency_ms": 0.0
            }
            
        stats = self.model_usage_stats[model]
        stats["calls"] += 1
        if success:
            stats["successful_calls"] += 1
        stats["tokens"]["input"] += tokens_used.get("input", 0)
        stats["tokens"]["output"] += tokens_used.get("output", 0)
        stats["total_cost"] += cost
        stats["total_latency_ms"] += latency_ms
        
    def _record_llm_call(
        self,
        model: str,
        prompt: str,
        response: Optional[str],
        tokens_used: Dict[str, int],
        cost: float,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Record LLM call in history"""
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "response_preview": (response[:100] + "..." if response and len(response) > 100 else response),
            "tokens_used": tokens_used,
            "cost": cost,
            "latency_ms": latency_ms,
            "success": success,
            "error": error
        }
        
        self.llm_call_history.append(call_record)
        
        # Maintain history size
        if len(self.llm_call_history) > self.max_history_size:
            self.llm_call_history.pop(0)
            
    def _calculate_average_latency(self) -> float:
        """Calculate average latency across all calls"""
        if not self.llm_call_history:
            return 0.0
            
        total_latency = sum(call["latency_ms"] for call in self.llm_call_history)
        return round(total_latency / len(self.llm_call_history), 2)
        
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of LLM calls"""
        if not self.llm_call_history:
            return 100.0
            
        successful = sum(1 for call in self.llm_call_history if call["success"])
        return round((successful / len(self.llm_call_history)) * 100, 2)
        
    def _get_hourly_costs(self) -> List[Dict[str, Any]]:
        """Get costs broken down by hour"""
        # Group costs by hour
        hourly = {}
        
        for timestamp, cost in self.hourly_costs:
            hour = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:00")
            if hour not in hourly:
                hourly[hour] = 0.0
            hourly[hour] += cost
            
        return [
            {"hour": hour, "cost": round(cost, 4)}
            for hour, cost in sorted(hourly.items())
        ]