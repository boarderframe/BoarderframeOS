#!/usr/bin/env python3
"""
Agent Cortex API Server - Centralized Brain Service for BoarderframeOS
Provides intelligent LLM orchestration for all agents via HTTP API
"""

import asyncio
import json
import logging

# Add parent directory to Python path
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent.parent))

from core.agent_cortex import (
    AgentCortex,
    AgentRequest,
    CortexResponse,
    ModelSelection,
    SelectionStrategy,
    get_agent_cortex_instance,
)
from core.agent_cortex_claude_config import calculate_actual_cost
from core.cost_tracker import cost_tracker, track_llm_cost
from core.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("agent_cortex_server")

# Global variables
cortex: Optional[AgentCortex] = None
start_time: float = 0

# Statistics tracking
stats = {
    "total_requests": 0,
    "total_tokens": 0,
    "total_cost": 0.0,
    "requests_by_agent": {},
    "requests_by_model": {},
    "errors": 0,
    "start_time": datetime.now().isoformat(),
}


class GenerateRequest(BaseModel):
    """Request model for text generation"""

    agent_name: str
    prompt: str
    task_type: str = "general"
    temperature: float = 0.7
    max_tokens: int = 1000
    complexity: int = 5
    urgency: int = 5
    quality_requirements: float = 0.85
    strategy: str = "balanced"
    context: Dict[str, Any] = {}


class GenerateResponse(BaseModel):
    """Response model for text generation"""

    success: bool
    response: str
    model_used: str
    provider: str
    tracking_id: str
    expected_cost: float
    reasoning: str
    error: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    global cortex, start_time
    try:
        logger.info("🧠 Initializing Agent Cortex...")
        cortex = await get_agent_cortex_instance()

        # Initialize cost tracker
        logger.info("💰 Initializing cost tracker...")
        await cost_tracker.initialize()

        start_time = time.time()
        logger.info("✅ Agent Cortex initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Agent Cortex: {e}")
        raise

    yield

    # Shutdown
    logger.info("👋 Shutting down Agent Cortex API")
    await cost_tracker.close()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Agent Cortex API",
    description="Centralized Brain Service for BoarderframeOS Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    global start_time
    return {
        "status": "healthy",
        "service": "Agent Cortex API",
        "version": "1.0.0",
        "cortex_initialized": cortex is not None,
        "uptime": time.time() - start_time if start_time else 0,
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate text using Agent Cortex's intelligent model selection.
    This is the main endpoint that replaces direct LLMClient usage.
    """
    global stats

    if not cortex:
        raise HTTPException(status_code=503, detail="Agent Cortex not initialized")

    try:
        # Check budget before processing
        budget_allowed, budget_reason, budget_action = await cost_tracker.check_budget(
            request.agent_name
        )
        if not budget_allowed:
            logger.warning(
                f"Budget limit reached for {request.agent_name}: {budget_reason}. {budget_action}"
            )
            # Still allow but switch to budget strategy
            request.strategy = "emergency_budget"

        # Update statistics
        stats["total_requests"] += 1
        stats["requests_by_agent"][request.agent_name] = (
            stats["requests_by_agent"].get(request.agent_name, 0) + 1
        )

        # Create Agent Cortex request
        cortex_request = AgentRequest(
            agent_name=request.agent_name,
            task_type=request.task_type,
            context=request.context,
            complexity=request.complexity,
            urgency=request.urgency,
            quality_requirements=request.quality_requirements,
        )

        # Get strategy enum
        strategy_map = {
            "cost_optimized": SelectionStrategy.COST_OPTIMIZED,
            "performance_optimized": SelectionStrategy.PERFORMANCE_OPTIMIZED,
            "balanced": SelectionStrategy.BALANCED,
            "emergency_budget": SelectionStrategy.EMERGENCY_BUDGET,
            "local_only": SelectionStrategy.LOCAL_ONLY,
        }
        strategy = strategy_map.get(request.strategy, SelectionStrategy.BALANCED)

        # Process through Agent Cortex
        cortex_response: CortexResponse = await cortex.process_agent_request(
            cortex_request
        )

        # Generate response using selected LLM
        start_time = time.time()
        llm_response = await cortex_response.llm.generate(
            request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        latency_ms = int((time.time() - start_time) * 1000)

        # Update statistics
        model_used = cortex_response.selection.selected_model
        stats["requests_by_model"][model_used] = (
            stats["requests_by_model"].get(model_used, 0) + 1
        )

        # Calculate actual cost based on response
        # Estimate tokens (words * 1.3 for token approximation)
        input_tokens = int(len(request.prompt.split()) * 1.3)
        output_tokens = int(len(llm_response.split()) * 1.3)
        estimated_tokens = input_tokens + output_tokens

        # Get model config for accurate cost calculation
        model_config = None
        for tier_configs in cortex.model_selector.model_registry.values():
            for variant_config in tier_configs.values():
                if variant_config["model"] == model_used:
                    model_config = variant_config
                    break
            if model_config:
                break

        # Calculate actual costs
        if model_config:
            costs = calculate_actual_cost(input_tokens, output_tokens, model_config)
            actual_cost = costs["total_cost"]
        else:
            # Fallback to expected cost
            actual_cost = cortex_response.selection.expected_cost

        stats["total_cost"] += actual_cost
        stats["total_tokens"] += estimated_tokens

        # Log cost tracking info
        logger.info(
            f"Cost tracking - Agent: {request.agent_name}, Model: {model_used}, "
            f"Tokens: ~{estimated_tokens}, Cost: ${actual_cost:.6f}, Latency: {latency_ms}ms"
        )

        # Track in database
        await track_llm_cost(
            tracking_id=cortex_response.tracking_id,
            agent_name=request.agent_name,
            model_used=model_used,
            provider=cortex_response.selection.provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=costs["input_cost"] if model_config else actual_cost * 0.3,
            output_cost=costs["output_cost"] if model_config else actual_cost * 0.7,
            latency_ms=latency_ms,
            strategy=request.strategy,
            task_type=request.task_type,
            complexity=request.complexity,
            quality_score=cortex_response.selection.expected_quality,
            success=True,
        )

        # Report performance back to Agent Cortex for learning
        # (In a real implementation, we'd track actual metrics)

        return GenerateResponse(
            success=True,
            response=llm_response,
            model_used=model_used,
            provider=cortex_response.selection.provider,
            tracking_id=cortex_response.tracking_id,
            expected_cost=cortex_response.selection.expected_cost,
            reasoning=cortex_response.selection.reasoning,
        )

    except Exception as e:
        stats["errors"] += 1
        logger.error(f"Generation error for {request.agent_name}: {e}")
        return GenerateResponse(
            success=False,
            response="",
            model_used="none",
            provider="none",
            tracking_id="error",
            expected_cost=0.0,
            reasoning="Error occurred",
            error=str(e),
        )


@app.get("/stats")
async def get_stats():
    """Get usage statistics - compatible with UI expectations"""
    return {
        "success": True,
        "data": {
            **stats,
            "active_models": list(stats["requests_by_model"].keys()),
            "active_agents": list(stats["requests_by_agent"].keys()),
            "average_cost_per_request": (
                stats["total_cost"] / stats["total_requests"]
                if stats["total_requests"] > 0
                else 0
            ),
            "cortex_status": "active" if cortex else "inactive",
        },
    }


@app.post("/report_performance")
async def report_performance(
    tracking_id: str,
    actual_cost: float,
    actual_latency: float,
    quality_score: float,
    task_completed: bool = True,
):
    """
    Report actual performance metrics back to Agent Cortex for learning.
    This helps improve future model selection.
    """
    if not cortex:
        raise HTTPException(status_code=503, detail="Agent Cortex not initialized")

    # In a full implementation, this would report back to Agent Cortex
    # for continuous learning and improvement

    return {"success": True, "message": "Performance reported"}


@app.get("/models")
async def get_available_models():
    """Get list of available models and their tiers"""
    if not cortex:
        raise HTTPException(status_code=503, detail="Agent Cortex not initialized")

    # Extract model registry information
    model_info = {}
    if hasattr(cortex, "model_selector") and hasattr(
        cortex.model_selector, "model_registry"
    ):
        model_info = cortex.model_selector.model_registry

    return {
        "success": True,
        "models": model_info,
        "tiers": ["executive", "department", "specialist", "worker"],
    }


@app.get("/cost-report")
async def get_cost_report(agent_name: Optional[str] = None):
    """Get detailed cost report from database"""
    try:
        if agent_name:
            # Get specific agent stats
            agent_stats = await cost_tracker.get_agent_stats(agent_name)
            if not agent_stats:
                return {
                    "success": False,
                    "error": f"No data found for agent {agent_name}",
                }

            return {
                "success": True,
                "agent": agent_name,
                "stats": agent_stats,
                "message": f"Agent {agent_name} has used {agent_stats['budget_percentage_used']:.1f}% of daily budget",
            }
        else:
            # Get system-wide summary
            system_summary = await cost_tracker.get_system_summary()
            if not system_summary:
                return {"success": False, "error": "Unable to retrieve system summary"}

            return {
                "success": True,
                "summary": system_summary,
                "message": f"System total: ${system_summary['total_cost']:.6f} across {system_summary['total_requests']} requests today",
            }
    except Exception as e:
        logger.error(f"Error generating cost report: {e}")
        return {"success": False, "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Agent Cortex API",
        "description": "Centralized Brain Service for BoarderframeOS",
        "endpoints": {
            "/health": "Health check",
            "/generate": "Generate text with intelligent model selection",
            "/stats": "Usage statistics",
            "/models": "Available models and tiers",
            "/report_performance": "Report actual performance metrics",
            "/cost-report": "Detailed cost report from database",
        },
        "documentation": "/docs",
    }


def run_server(host: str = "0.0.0.0", port: int = 8005):
    """Run the Agent Cortex API server"""
    logger.info(f"🧠 Starting Agent Cortex API Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
