"""
LLM Client for BoarderframeOS
Connects agents to language models (local/cloud)
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

try:
    import anthropic
except ImportError:
    anthropic = None

@dataclass
class LLMConfig:
    """Configuration for LLM connection"""
    provider: str = "ollama"  # ollama, openai, anthropic, local
    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30

class LLMProvider(ABC):
    """Abstract base for LLM providers"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)
        self.logger = logging.getLogger("ollama")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama"""
        try:
            response = await self.client.post(
                f"{self.config.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "stream": False
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                self.logger.error(f"Ollama error: {response.status_code}")
                return f"Error: {response.status_code}"

        except Exception as e:
            self.logger.error(f"Ollama connection error: {e}")
            return f"LLM Error: {e}"

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings"""
        try:
            response = await self.client.post(
                f"{self.config.base_url}/api/embeddings",
                json={"model": self.config.model, "prompt": text}
            )
            if response.status_code == 200:
                return response.json().get("embedding", [])
            return []
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
            return []

class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout
        )

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate using OpenAI API"""
        try:
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"OpenAI Error: {response.status_code}"

        except Exception as e:
            return f"OpenAI Error: {e}"

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI"""
        try:
            response = await self.client.post(
                "https://api.openai.com/v1/embeddings",
                json={"input": text, "model": "text-embedding-3-small"}
            )
            if response.status_code == 200:
                return response.json()["data"][0]["embedding"]
            return []
        except Exception as e:
            return []

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""

    def __init__(self, config: LLMConfig):
        self.config = config
        if not anthropic:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var or pass in config")

        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.logger = logging.getLogger("anthropic")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate using Claude"""
        try:
            message = await self.client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}]
            )

            # Handle Claude 4 refusal stop reason
            if message.stop_reason == "refusal":
                self.logger.warning("Claude declined to generate content for safety reasons")
                return "I cannot provide a response to that request for safety reasons."

            return message.content[0].text

        except Exception as e:
            self.logger.error(f"Anthropic error: {e}")
            return f"Claude Error: {e}"

    async def think_with_tools(self, prompt: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """Advanced reasoning with tool use"""
        try:
            message = await self.client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                tools=tools,
                messages=[{"role": "user", "content": prompt}]
            )

            # Handle Claude 4 refusal stop reason
            if message.stop_reason == "refusal":
                self.logger.warning("Claude declined to generate content with tools for safety reasons")
                return {
                    "content": [{"type": "text", "text": "I cannot provide a response to that request for safety reasons."}],
                    "usage": message.usage,
                    "stop_reason": "refusal",
                    "refusal": True
                }

            # Return full response for tool use parsing
            return {
                "content": message.content,
                "usage": message.usage,
                "stop_reason": message.stop_reason
            }

        except Exception as e:
            self.logger.error(f"Anthropic tool error: {e}")
            return {"error": str(e)}

    async def embed(self, text: str) -> List[float]:
        """Claude doesn't provide embeddings, use OpenAI or local"""
        self.logger.warning("Claude doesn't provide embeddings")
        return []

class LocalProvider(LLMProvider):
    """Local inference server (vLLM, TGI, etc.)"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate using local inference server"""
        try:
            # Adjust for your local inference setup
            response = await self.client.post(
                f"{self.config.base_url}/generate",
                json={
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "max_new_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("generated_text", "")
            else:
                return f"Local LLM Error: {response.status_code}"

        except Exception as e:
            return f"Local LLM Error: {e}"

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings locally"""
        # Implement based on your local embedding setup
        return []

class LLMClient:
    """Main LLM client for BoarderframeOS"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = self._create_provider()
        self.logger = logging.getLogger("llm_client")

    def _create_provider(self) -> LLMProvider:
        """Create appropriate provider based on config"""
        if self.config.provider == "anthropic":
            return AnthropicProvider(self.config)
        elif self.config.provider == "ollama":
            return OllamaProvider(self.config)
        elif self.config.provider == "openai":
            return OpenAIProvider(self.config)
        elif self.config.provider == "local":
            return LocalProvider(self.config)
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    async def think(self, agent_name: str, role: str, context: Dict[str, Any],
                   goals: List[str]) -> str:
        """Generate agent thoughts based on context"""

        # Build comprehensive prompt
        prompt = f"""You are {agent_name}, an AI agent with the role of {role}.

Your primary goals are:
{chr(10).join(f"- {goal}" for goal in goals)}

Current context:
- Time: {context.get('current_time', 'unknown')}
- Recent memories: {len(context.get('recent_memories', []))} items
- Message queue: {context.get('message_queue_size', 0)} pending
- Active tasks: {context.get('active_tasks', 0)}
- Available tools: {', '.join(context.get('available_tools', []))}

Recent memories:
{json.dumps(context.get('recent_memories', [])[-3:], indent=2)}

Based on this context, what should you do next? Think step by step about your current situation and decide on your next action. Be specific and actionable.

Response:"""

        return await self.provider.generate(prompt)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text"""
        return await self.provider.generate(prompt, **kwargs)

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings"""
        return await self.provider.embed(text)

    async def test_connection(self) -> bool:
        """Test if LLM is accessible"""
        try:
            response = await self.generate("Hello! Please respond with 'OK' if you can hear me.")
            return "ok" in response.lower()
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

# Default configurations for different setups
ANTHROPIC_CONFIG = LLMConfig(
    provider="anthropic",
    model="claude-4-sonnet-20250514",  # Claude 4 Sonnet - Latest and most balanced
    max_tokens=4000,
    temperature=0.7
)

CLAUDE_OPUS_CONFIG = LLMConfig(
    provider="anthropic",
    model="claude-opus-4-20250514",  # Claude 4 Opus - Most powerful
    max_tokens=4000,
    temperature=0.3  # Lower temp for more focused reasoning
)

OLLAMA_CONFIG = LLMConfig(
    provider="ollama",
    model="llama3.2",
    base_url="http://localhost:11434"
)

OPENAI_CONFIG = LLMConfig(
    provider="openai",
    model="gpt-4o-mini",
    api_key="your-api-key-here"
)

LOCAL_CONFIG = LLMConfig(
    provider="local",
    model="llama-maverick-30b",
    base_url="http://localhost:8000"  # Your local inference server
)
