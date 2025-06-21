"""
Agent Cortex Client - Wrapper for agents to use centralized brain service
Maintains LLMClient interface while routing through Agent Cortex API
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx


class CortexClient:
    """
    Client for Agent Cortex API - replaces direct LLMClient usage.
    Provides the same interface as LLMClient but routes through Agent Cortex.
    """

    def __init__(self, agent_name: str, cortex_url: str = "http://localhost:8005"):
        self.agent_name = agent_name
        self.cortex_url = cortex_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logging.getLogger(f"cortex_client.{agent_name}")

        # Default parameters
        self.default_temperature = 0.7
        self.default_max_tokens = 1000
        self.default_strategy = "balanced"

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Generate text using Agent Cortex API.
        Maintains compatibility with LLMClient.generate() interface.
        """
        try:
            # Prepare request
            request_data = {
                "agent_name": self.agent_name,
                "prompt": prompt,
                "temperature": temperature or self.default_temperature,
                "max_tokens": max_tokens or self.default_max_tokens,
                "task_type": kwargs.get("task_type", "general"),
                "complexity": kwargs.get("complexity", 5),
                "urgency": kwargs.get("urgency", 5),
                "quality_requirements": kwargs.get("quality_requirements", 0.85),
                "strategy": kwargs.get("strategy", self.default_strategy),
                "context": kwargs.get("context", {}),
            }

            # Call Agent Cortex API
            response = await self.client.post(
                f"{self.cortex_url}/generate", json=request_data
            )

            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    self.logger.debug(
                        f"Used model: {result['model_used']} "
                        f"(Provider: {result['provider']}, Cost: ${result['expected_cost']:.4f})"
                    )
                    return result["response"]
                else:
                    self.logger.error(
                        f"Generation failed: {result.get('error', 'Unknown error')}"
                    )
                    return f"Error: {result.get('error', 'Generation failed')}"
            else:
                self.logger.error(f"API error: {response.status_code}")
                return f"Error: Agent Cortex API returned {response.status_code}"

        except httpx.ConnectError:
            self.logger.error("Failed to connect to Agent Cortex API")
            return "Error: Cannot connect to Agent Cortex service"
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return f"Error: {str(e)}"

    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings - not yet implemented in Agent Cortex.
        Returns empty list for now to maintain interface compatibility.
        """
        # TODO: Implement embedding endpoint in Agent Cortex
        self.logger.warning("Embeddings not yet supported by Agent Cortex")
        return []

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat interface - converts to single prompt for now.
        Future enhancement: Agent Cortex could maintain conversation context.
        """
        # Convert messages to single prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(f"User: {content}")

        prompt = "\n".join(prompt_parts)
        return await self.generate(prompt, **kwargs)

    async def set_strategy(self, strategy: str):
        """Set the model selection strategy for this agent"""
        valid_strategies = [
            "cost_optimized",
            "performance_optimized",
            "balanced",
            "emergency_budget",
            "local_only",
        ]
        if strategy in valid_strategies:
            self.default_strategy = strategy
        else:
            self.logger.warning(f"Invalid strategy: {strategy}")

    async def check_health(self) -> bool:
        """Check if Agent Cortex API is healthy"""
        try:
            response = await self.client.get(f"{self.cortex_url}/health")
            return response.status_code == 200
        except:
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this agent"""
        try:
            response = await self.client.get(f"{self.cortex_url}/stats")
            if response.status_code == 200:
                data = response.json()["data"]
                return {
                    "total_requests": data["requests_by_agent"].get(self.agent_name, 0),
                    "total_cost": data.get("total_cost", 0.0),
                    "models_used": data.get("requests_by_model", {}),
                }
            return {}
        except:
            return {}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Convenience function for backward compatibility
def create_cortex_client(agent_name: str, **kwargs) -> CortexClient:
    """Create a CortexClient instance for an agent"""
    return CortexClient(agent_name, **kwargs)
