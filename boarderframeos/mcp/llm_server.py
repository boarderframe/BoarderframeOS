"""
LLM MCP Server for BoarderframeOS
Provides unified interface to various LLM providers (Claude, local models)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import logging
import uvicorn
import httpx
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("llm_server")

app = FastAPI(title="LLM MCP Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")

class LLMRequest(BaseModel):
    provider: str = Field(..., description="LLM provider: claude, local, openai")
    model: str = Field(..., description="Model name")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    temperature: float = Field(0.7, description="Sampling temperature")
    max_tokens: int = Field(4000, description="Maximum tokens to generate")
    agent_id: Optional[str] = Field(None, description="Requesting agent ID")
    system_prompt: Optional[str] = Field(None, description="System prompt override")

class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    tokens_used: int
    cost_estimate: float
    response_time_ms: int

class ModelInfo(BaseModel):
    name: str
    provider: str
    context_length: int
    cost_per_token: float
    available: bool

# LLM Provider Configurations
PROVIDERS_CONFIG = {
    "claude": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "models": {
            "claude-3-opus-20240229": {"context": 200000, "cost": 0.000015},
            "claude-3-sonnet-20240229": {"context": 200000, "cost": 0.000003},
            "claude-3-haiku-20240307": {"context": 200000, "cost": 0.00000025}
        }
    },
    "local": {
        "base_url": "http://localhost:8080",  # Local LLM server
        "models": {
            "llama-maverick-30b": {"context": 8192, "cost": 0.0},
            "mistral-7b": {"context": 8192, "cost": 0.0}
        }
    }
}

class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.config = PROVIDERS_CONFIG.get(provider_name, {})
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM"""
        start_time = datetime.now()
        
        if self.provider_name == "claude":
            response = await self._generate_claude(request)
        elif self.provider_name == "local":
            response = await self._generate_local(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {self.provider_name}")
        
        end_time = datetime.now()
        response.response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Log the request for monitoring
        logger.info(f"LLM request: {request.agent_id} -> {request.provider}/{request.model} "
                   f"({response.tokens_used} tokens, {response.response_time_ms}ms)")
        
        return response
    
    async def _generate_claude(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Claude API"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
        
        # Prepare messages for Claude format
        messages = []
        system_prompt = request.system_prompt
        
        for msg in request.messages:
            if msg.role == "system" and not system_prompt:
                system_prompt = msg.content
            elif msg.role in ["user", "assistant"]:
                messages.append({"role": msg.role, "content": msg.content})
        
        payload = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        try:
            response = await self.client.post(
                f"{self.config['base_url']}/messages",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["content"][0]["text"]
            tokens_used = data["usage"]["output_tokens"]
            
            model_config = self.config["models"].get(request.model, {})
            cost_estimate = tokens_used * model_config.get("cost", 0.0)
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider="claude",
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                response_time_ms=0  # Will be set by caller
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Claude API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail="Claude API error")
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _generate_local(self, request: LLMRequest) -> LLMResponse:
        """Generate response using local LLM server"""
        # Format for local LLM (assuming OpenAI-compatible format)
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        try:
            response = await self.client.post(
                f"{self.config['base_url']}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider="local",
                tokens_used=tokens_used,
                cost_estimate=0.0,  # Local models are free
                response_time_ms=0
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Local LLM error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=502, detail="Local LLM server error")
        except Exception as e:
            logger.error(f"Local LLM generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Global provider instances
providers = {
    "claude": LLMProvider("claude"),
    "local": LLMProvider("local")
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "llm_server"}

@app.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List available models across all providers"""
    models = []
    
    for provider_name, config in PROVIDERS_CONFIG.items():
        for model_name, model_config in config["models"].items():
            # Check if provider is available
            available = True
            if provider_name == "claude":
                available = bool(os.getenv("ANTHROPIC_API_KEY"))
            elif provider_name == "local":
                # TODO: Ping local server to check availability
                available = False  # Assume not available until we can verify
            
            models.append(ModelInfo(
                name=model_name,
                provider=provider_name,
                context_length=model_config["context"],
                cost_per_token=model_config["cost"],
                available=available
            ))
    
    return models

@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    """Generate text using specified LLM provider"""
    try:
        provider = providers.get(request.provider)
        if not provider:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")
        
        response = await provider.generate(request)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/{agent_id}")
async def agent_chat(agent_id: str, request: LLMRequest):
    """Chat endpoint specifically for agent interactions"""
    # Override agent_id in request
    request.agent_id = agent_id
    
    # Add agent-specific system prompt if not provided
    if not request.system_prompt:
        request.system_prompt = f"You are {agent_id}, an AI agent in the BoarderframeOS system."
    
    return await generate_text(request)

@app.get("/stats")
async def get_stats():
    """Get usage statistics"""
    # TODO: Implement proper stats tracking
    return {
        "total_requests": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "active_providers": list(providers.keys())
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8005, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"Starting LLM MCP Server on {args.host}:{args.port}")
    uvicorn.run(
        "llm_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )