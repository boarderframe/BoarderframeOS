"""
LLM Provider SDK for BoarderframeOS
Comprehensive SDK for integrating various LLM providers with LangChain support
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

# LangChain imports
try:
    from langchain.callbacks import AsyncCallbackHandler
    from langchain.chat_models.base import BaseChatModel
    from langchain.embeddings.base import Embeddings
    from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage
    from langchain_anthropic import ChatAnthropic
    from langchain_community.chat_models import ChatOllama
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.llms import Ollama
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseMessage = HumanMessage = AIMessage = SystemMessage = object
    AsyncCallbackHandler = object
    BaseChatModel = object
    Embeddings = object
    OpenAIEmbeddings = object
    OllamaEmbeddings = object

# Additional provider imports
try:
    from langchain_cohere import ChatCohere
    from langchain_community.chat_models import ChatPerplexity
    from langchain_community.llms import HuggingFaceHub, Replicate
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_groq import ChatGroq
    EXTENDED_PROVIDERS = True
except ImportError:
    EXTENDED_PROVIDERS = False
    ChatGoogleGenerativeAI = object
    ChatCohere = object
    ChatPerplexity = object
    HuggingFaceHub = object
    Replicate = object
    ChatGroq = object

from core.cost_management import MODEL_COSTS
from core.llm_client import LLMConfig, LLMProvider


class ModelCapability(Enum):
    """Model capabilities for routing decisions"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDINGS = "embeddings"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    LONG_CONTEXT = "long_context"  # 100k+ tokens
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    CREATIVE_WRITING = "creative_writing"


@dataclass
class ModelProfile:
    """Detailed model profile for intelligent routing"""
    provider: str
    model_name: str
    capabilities: List[ModelCapability]
    context_window: int
    max_output_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    latency_ms: int  # Average latency
    quality_score: float  # 0-1 quality rating
    specialties: List[str] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=lambda: ["en"])
    is_available: bool = True
    requires_api_key: bool = True
    base_url: Optional[str] = None


class ProviderRegistry:
    """Registry of all available LLM providers and their models"""

    def __init__(self):
        self.providers: Dict[str, Dict[str, ModelProfile]] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize with known provider profiles"""

        # Anthropic Models
        self.providers["anthropic"] = {
            "claude-opus-4-20250514": ModelProfile(
                provider="anthropic",
                model_name="claude-opus-4-20250514",
                capabilities=[
                    ModelCapability.CHAT, ModelCapability.REASONING,
                    ModelCapability.CODE_GENERATION, ModelCapability.LONG_CONTEXT,
                    ModelCapability.VISION, ModelCapability.FUNCTION_CALLING
                ],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                latency_ms=2000,
                quality_score=0.98,
                specialties=["reasoning", "coding", "analysis", "creative"]
            ),
            "claude-4-sonnet-20250514": ModelProfile(
                provider="anthropic",
                model_name="claude-4-sonnet-20250514",
                capabilities=[
                    ModelCapability.CHAT, ModelCapability.CODE_GENERATION,
                    ModelCapability.LONG_CONTEXT, ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING
                ],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                latency_ms=1200,
                quality_score=0.95,
                specialties=["balanced", "coding", "analysis"]
            ),
            "claude-3-haiku-20240307": ModelProfile(
                provider="anthropic",
                model_name="claude-3-haiku-20240307",
                capabilities=[ModelCapability.CHAT, ModelCapability.CODE_GENERATION],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_1k_input=0.00025,
                cost_per_1k_output=0.00125,
                latency_ms=500,
                quality_score=0.85,
                specialties=["fast", "efficient"]
            )
        }

        # OpenAI Models
        self.providers["openai"] = {
            "gpt-4o": ModelProfile(
                provider="openai",
                model_name="gpt-4o",
                capabilities=[
                    ModelCapability.CHAT, ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING, ModelCapability.CODE_GENERATION
                ],
                context_window=128000,
                max_output_tokens=4096,
                cost_per_1k_input=0.005,
                cost_per_1k_output=0.015,
                latency_ms=1500,
                quality_score=0.94,
                specialties=["multimodal", "coding", "analysis"]
            ),
            "gpt-4o-mini": ModelProfile(
                provider="openai",
                model_name="gpt-4o-mini",
                capabilities=[
                    ModelCapability.CHAT, ModelCapability.VISION,
                    ModelCapability.FUNCTION_CALLING
                ],
                context_window=128000,
                max_output_tokens=16384,
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.0006,
                latency_ms=800,
                quality_score=0.88,
                specialties=["fast", "efficient", "multimodal"]
            ),
            "gpt-4-turbo": ModelProfile(
                provider="openai",
                model_name="gpt-4-turbo",
                capabilities=[
                    ModelCapability.CHAT, ModelCapability.CODE_GENERATION,
                    ModelCapability.FUNCTION_CALLING, ModelCapability.LONG_CONTEXT
                ],
                context_window=128000,
                max_output_tokens=4096,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
                latency_ms=2000,
                quality_score=0.93,
                specialties=["reasoning", "coding"]
            )
        }

        # Google Models
        if EXTENDED_PROVIDERS:
            self.providers["google"] = {
                "gemini-1.5-pro": ModelProfile(
                    provider="google",
                    model_name="gemini-1.5-pro",
                    capabilities=[
                        ModelCapability.CHAT, ModelCapability.VISION,
                        ModelCapability.LONG_CONTEXT, ModelCapability.CODE_GENERATION
                    ],
                    context_window=2000000,  # 2M tokens!
                    max_output_tokens=8192,
                    cost_per_1k_input=0.0035,
                    cost_per_1k_output=0.0105,
                    latency_ms=1800,
                    quality_score=0.92,
                    specialties=["ultra-long-context", "multimodal"]
                ),
                "gemini-1.5-flash": ModelProfile(
                    provider="google",
                    model_name="gemini-1.5-flash",
                    capabilities=[
                        ModelCapability.CHAT, ModelCapability.VISION,
                        ModelCapability.LONG_CONTEXT
                    ],
                    context_window=1000000,  # 1M tokens
                    max_output_tokens=8192,
                    cost_per_1k_input=0.00035,
                    cost_per_1k_output=0.00105,
                    latency_ms=600,
                    quality_score=0.86,
                    specialties=["fast", "long-context"]
                )
            }

        # Groq Models (Ultra-fast inference)
        if EXTENDED_PROVIDERS:
            self.providers["groq"] = {
                "llama-3.3-70b-versatile": ModelProfile(
                    provider="groq",
                    model_name="llama-3.3-70b-versatile",
                    capabilities=[ModelCapability.CHAT, ModelCapability.CODE_GENERATION],
                    context_window=8192,
                    max_output_tokens=8192,
                    cost_per_1k_input=0.00059,
                    cost_per_1k_output=0.00079,
                    latency_ms=200,  # Ultra-fast!
                    quality_score=0.90,
                    specialties=["ultra-fast", "coding"]
                ),
                "mixtral-8x7b-32768": ModelProfile(
                    provider="groq",
                    model_name="mixtral-8x7b-32768",
                    capabilities=[ModelCapability.CHAT, ModelCapability.CODE_GENERATION],
                    context_window=32768,
                    max_output_tokens=32768,
                    cost_per_1k_input=0.00024,
                    cost_per_1k_output=0.00024,
                    latency_ms=150,
                    quality_score=0.88,
                    specialties=["ultra-fast", "efficient"]
                )
            }

        # Local/Ollama Models
        self.providers["ollama"] = {
            "llama3.2": ModelProfile(
                provider="ollama",
                model_name="llama3.2",
                capabilities=[ModelCapability.CHAT, ModelCapability.CODE_GENERATION],
                context_window=128000,
                max_output_tokens=128000,
                cost_per_1k_input=0.0,  # Free!
                cost_per_1k_output=0.0,
                latency_ms=1000,
                quality_score=0.85,
                specialties=["local", "private"],
                requires_api_key=False,
                base_url="http://localhost:11434"
            ),
            "mistral": ModelProfile(
                provider="ollama",
                model_name="mistral",
                capabilities=[ModelCapability.CHAT, ModelCapability.CODE_GENERATION],
                context_window=8192,
                max_output_tokens=8192,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                latency_ms=800,
                quality_score=0.82,
                specialties=["local", "efficient"],
                requires_api_key=False,
                base_url="http://localhost:11434"
            ),
            "deepseek-coder-v2": ModelProfile(
                provider="ollama",
                model_name="deepseek-coder-v2",
                capabilities=[ModelCapability.CHAT, ModelCapability.CODE_GENERATION],
                context_window=16384,
                max_output_tokens=16384,
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                latency_ms=1200,
                quality_score=0.88,
                specialties=["coding", "local"],
                requires_api_key=False,
                base_url="http://localhost:11434"
            )
        }

        # Perplexity Models (Internet-connected)
        if EXTENDED_PROVIDERS:
            self.providers["perplexity"] = {
                "llama-3.1-sonar-large-128k-online": ModelProfile(
                    provider="perplexity",
                    model_name="llama-3.1-sonar-large-128k-online",
                    capabilities=[ModelCapability.CHAT],
                    context_window=128000,
                    max_output_tokens=4096,
                    cost_per_1k_input=0.001,
                    cost_per_1k_output=0.001,
                    latency_ms=2000,
                    quality_score=0.89,
                    specialties=["internet-search", "real-time-info"]
                )
            }

    def get_model(self, provider: str, model_name: str) -> Optional[ModelProfile]:
        """Get specific model profile"""
        return self.providers.get(provider, {}).get(model_name)

    def get_models_by_capability(self, capability: ModelCapability) -> List[ModelProfile]:
        """Get all models with a specific capability"""
        models = []
        for provider_models in self.providers.values():
            for model in provider_models.values():
                if capability in model.capabilities and model.is_available:
                    models.append(model)
        return sorted(models, key=lambda m: (m.quality_score, -m.latency_ms), reverse=True)

    def get_best_model_for_task(self,
                                task_type: str,
                                max_cost_per_1k: Optional[float] = None,
                                max_latency_ms: Optional[int] = None,
                                min_quality: float = 0.8) -> Optional[ModelProfile]:
        """Get best model for a specific task type"""
        specialty_models = []

        for provider_models in self.providers.values():
            for model in provider_models.values():
                if not model.is_available:
                    continue

                # Check if model specializes in this task
                if task_type.lower() in [s.lower() for s in model.specialties]:
                    # Apply filters
                    if max_cost_per_1k and model.cost_per_1k_input > max_cost_per_1k:
                        continue
                    if max_latency_ms and model.latency_ms > max_latency_ms:
                        continue
                    if model.quality_score < min_quality:
                        continue

                    specialty_models.append(model)

        # Sort by quality score and latency
        if specialty_models:
            return sorted(specialty_models,
                         key=lambda m: (m.quality_score, -m.latency_ms),
                         reverse=True)[0]

        return None


class LangChainProviderAdapter:
    """Adapter to create LangChain chat models from provider configs"""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.logger = logging.getLogger("langchain_adapter")

    def create_chat_model(self,
                         provider: str,
                         model_name: str,
                         temperature: float = 0.7,
                         max_tokens: Optional[int] = None,
                         **kwargs) -> Optional[BaseChatModel]:
        """Create LangChain chat model instance"""

        if not LANGCHAIN_AVAILABLE:
            self.logger.error("LangChain not installed")
            return None

        model_profile = self.registry.get_model(provider, model_name)
        if not model_profile:
            self.logger.error(f"Model {provider}/{model_name} not found")
            return None

        try:
            if provider == "anthropic":
                api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
                return ChatAnthropic(
                    model=model_name,
                    anthropic_api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens or model_profile.max_output_tokens
                )

            elif provider == "openai":
                api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
                return ChatOpenAI(
                    model=model_name,
                    openai_api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            elif provider == "ollama":
                base_url = kwargs.get("base_url") or model_profile.base_url
                return ChatOllama(
                    model=model_name,
                    base_url=base_url,
                    temperature=temperature,
                    num_predict=max_tokens
                )

            elif provider == "google" and EXTENDED_PROVIDERS:
                api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY")
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=api_key,
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )

            elif provider == "groq" and EXTENDED_PROVIDERS:
                api_key = kwargs.get("api_key") or os.getenv("GROQ_API_KEY")
                return ChatGroq(
                    model=model_name,
                    groq_api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            elif provider == "cohere" and EXTENDED_PROVIDERS:
                api_key = kwargs.get("api_key") or os.getenv("COHERE_API_KEY")
                return ChatCohere(
                    model=model_name,
                    cohere_api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            elif provider == "perplexity" and EXTENDED_PROVIDERS:
                api_key = kwargs.get("api_key") or os.getenv("PERPLEXITY_API_KEY")
                return ChatPerplexity(
                    model=model_name,
                    pplx_api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            else:
                self.logger.error(f"Provider {provider} not supported")
                return None

        except Exception as e:
            self.logger.error(f"Error creating {provider} model: {e}")
            return None

    def create_embeddings(self, provider: str, **kwargs) -> Optional[Embeddings]:
        """Create LangChain embeddings instance"""

        if not LANGCHAIN_AVAILABLE:
            return None

        try:
            if provider == "openai":
                api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
                return OpenAIEmbeddings(
                    openai_api_key=api_key,
                    model=kwargs.get("model", "text-embedding-3-small")
                )

            elif provider == "ollama":
                base_url = kwargs.get("base_url", "http://localhost:11434")
                return OllamaEmbeddings(
                    base_url=base_url,
                    model=kwargs.get("model", "nomic-embed-text")
                )

            # Add more embedding providers as needed

        except Exception as e:
            self.logger.error(f"Error creating embeddings: {e}")
            return None


class ModelRouter:
    """Intelligent routing of requests to appropriate models"""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.logger = logging.getLogger("model_router")

    async def route_request(self,
                          task_type: str,
                          input_tokens: int,
                          required_capabilities: List[ModelCapability],
                          constraints: Optional[Dict[str, Any]] = None) -> Optional[ModelProfile]:
        """Route request to best available model"""

        constraints = constraints or {}
        max_cost = constraints.get("max_cost_per_1k")
        max_latency = constraints.get("max_latency_ms")
        min_quality = constraints.get("min_quality", 0.8)
        required_context = constraints.get("required_context_window", 0)

        # Get models with required capabilities
        candidate_models = []
        for capability in required_capabilities:
            models = self.registry.get_models_by_capability(capability)
            candidate_models.extend(models)

        # Remove duplicates and filter
        seen = set()
        filtered_models = []

        for model in candidate_models:
            model_id = f"{model.provider}/{model.model_name}"
            if model_id in seen:
                continue
            seen.add(model_id)

            # Apply constraints
            if required_context > model.context_window:
                continue
            if max_cost and model.cost_per_1k_input > max_cost:
                continue
            if max_latency and model.latency_ms > max_latency:
                continue
            if model.quality_score < min_quality:
                continue

            filtered_models.append(model)

        if not filtered_models:
            # Fallback to task-based selection
            return self.registry.get_best_model_for_task(
                task_type, max_cost, max_latency, min_quality
            )

        # Score models based on task fit
        scored_models = []
        for model in filtered_models:
            score = self._calculate_model_score(model, task_type, constraints)
            scored_models.append((score, model))

        # Return best scoring model
        scored_models.sort(key=lambda x: x[0], reverse=True)
        return scored_models[0][1] if scored_models else None

    def _calculate_model_score(self,
                              model: ModelProfile,
                              task_type: str,
                              constraints: Dict[str, Any]) -> float:
        """Calculate model fitness score for task"""

        score = 0.0

        # Quality weight
        quality_weight = constraints.get("quality_weight", 0.4)
        score += model.quality_score * quality_weight

        # Cost efficiency weight
        cost_weight = constraints.get("cost_weight", 0.3)
        if model.cost_per_1k_input == 0:  # Free models get bonus
            score += cost_weight
        else:
            # Inverse cost scoring (lower cost = higher score)
            max_cost = 0.075  # Most expensive model cost
            cost_score = 1 - (model.cost_per_1k_input / max_cost)
            score += cost_score * cost_weight

        # Speed weight
        speed_weight = constraints.get("speed_weight", 0.2)
        max_latency = 3000  # Max expected latency
        speed_score = 1 - (model.latency_ms / max_latency)
        score += speed_score * speed_weight

        # Task specialty bonus
        if task_type.lower() in [s.lower() for s in model.specialties]:
            score += 0.1

        return min(score, 1.0)


class LLMProviderSDK:
    """Main SDK for LLM provider management in BoarderframeOS"""

    def __init__(self):
        self.registry = ProviderRegistry()
        self.adapter = LangChainProviderAdapter(self.registry)
        self.router = ModelRouter(self.registry)
        self.logger = logging.getLogger("llm_sdk")

    def list_providers(self) -> List[str]:
        """List all available providers"""
        return list(self.registry.providers.keys())

    def list_models(self, provider: Optional[str] = None) -> List[ModelProfile]:
        """List all models or models for specific provider"""
        models = []

        if provider:
            models = list(self.registry.providers.get(provider, {}).values())
        else:
            for provider_models in self.registry.providers.values():
                models.extend(provider_models.values())

        return models

    def get_model_info(self, provider: str, model_name: str) -> Optional[ModelProfile]:
        """Get detailed information about a model"""
        return self.registry.get_model(provider, model_name)

    async def create_optimized_chain(self,
                                   task_type: str,
                                   required_capabilities: List[ModelCapability],
                                   constraints: Optional[Dict[str, Any]] = None,
                                   **model_kwargs) -> Optional[BaseChatModel]:
        """Create optimized LangChain model for task"""

        # Route to best model
        model_profile = await self.router.route_request(
            task_type=task_type,
            input_tokens=constraints.get("estimated_input_tokens", 1000),
            required_capabilities=required_capabilities,
            constraints=constraints
        )

        if not model_profile:
            self.logger.error("No suitable model found")
            return None

        self.logger.info(f"Selected model: {model_profile.provider}/{model_profile.model_name}")

        # Create LangChain model
        return self.adapter.create_chat_model(
            provider=model_profile.provider,
            model_name=model_profile.model_name,
            **model_kwargs
        )

    def estimate_cost(self,
                     provider: str,
                     model_name: str,
                     input_tokens: int,
                     output_tokens: int) -> float:
        """Estimate cost for a request"""

        model = self.registry.get_model(provider, model_name)
        if not model:
            return 0.0

        input_cost = (input_tokens / 1000) * model.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model.cost_per_1k_output

        return input_cost + output_cost

    def get_provider_status(self, provider: str) -> Dict[str, Any]:
        """Get provider availability status"""

        models = self.registry.providers.get(provider, {})
        available_models = [m for m in models.values() if m.is_available]

        return {
            "provider": provider,
            "total_models": len(models),
            "available_models": len(available_models),
            "requires_api_key": any(m.requires_api_key for m in models.values()),
            "capabilities": list(set(
                cap for m in models.values()
                for cap in m.capabilities
            ))
        }


# Singleton instance
_sdk_instance = None

def get_llm_sdk() -> LLMProviderSDK:
    """Get singleton LLM Provider SDK instance"""
    global _sdk_instance
    if _sdk_instance is None:
        _sdk_instance = LLMProviderSDK()
    return _sdk_instance


# Example usage
async def example_usage():
    """Example of using the LLM Provider SDK"""

    sdk = get_llm_sdk()

    # List all providers
    providers = sdk.list_providers()
    print(f"Available providers: {providers}")

    # Get model info
    model_info = sdk.get_model_info("anthropic", "claude-opus-4-20250514")
    print(f"Claude Opus info: {model_info}")

    # Create optimized model for coding task
    code_model = await sdk.create_optimized_chain(
        task_type="coding",
        required_capabilities=[ModelCapability.CODE_GENERATION],
        constraints={
            "max_cost_per_1k": 0.01,
            "max_latency_ms": 2000,
            "quality_weight": 0.6
        },
        temperature=0.5
    )

    if code_model and LANGCHAIN_AVAILABLE:
        # Use the model
        response = await code_model.ainvoke("Write a Python hello world")
        print(response)


if __name__ == "__main__":
    asyncio.run(example_usage())
