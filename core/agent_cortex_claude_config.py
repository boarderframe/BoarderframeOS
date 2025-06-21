"""
Agent Cortex Configuration - Claude-First Setup
Prioritizes Anthropic Claude models and includes comprehensive cost tracking
Updated with latest pricing from Anthropic (2024-2025)
"""

from typing import Any, Dict

# Claude-first model registry configuration with updated pricing
# Prices are per 1K tokens (divide official per-million prices by 1000)
CLAUDE_FIRST_MODEL_REGISTRY = {
    "executive": {
        "primary": {
            "model": "claude-3-opus-20240229",
            "provider": "anthropic",
            "input_cost_per_1k": 0.015,  # $15 per million tokens
            "output_cost_per_1k": 0.075,  # $75 per million tokens
            "avg_latency": 3.2,
            "quality_score": 0.95,
        },
        "fallback": {
            "model": "claude-3-5-sonnet-20241022",  # Latest version
            "provider": "anthropic",
            "input_cost_per_1k": 0.003,  # $3 per million tokens
            "output_cost_per_1k": 0.015,  # $15 per million tokens
            "avg_latency": 2.5,
            "quality_score": 0.93,
        },
        "budget": {
            "model": "claude-3-5-haiku-20241022",  # New Claude 3.5 Haiku
            "provider": "anthropic",
            "input_cost_per_1k": 0.0008,  # $0.80 per million tokens
            "output_cost_per_1k": 0.004,  # $4 per million tokens
            "avg_latency": 1.0,
            "quality_score": 0.88,
        },
    },
    "department": {
        "primary": {
            "model": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "input_cost_per_1k": 0.003,  # $3 per million tokens
            "output_cost_per_1k": 0.015,  # $15 per million tokens
            "avg_latency": 2.5,
            "quality_score": 0.93,
        },
        "fallback": {
            "model": "claude-3-sonnet-20240229",
            "provider": "anthropic",
            "input_cost_per_1k": 0.003,  # $3 per million tokens
            "output_cost_per_1k": 0.015,  # $15 per million tokens
            "avg_latency": 2.1,
            "quality_score": 0.88,
        },
        "budget": {
            "model": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "input_cost_per_1k": 0.00025,  # $0.25 per million tokens
            "output_cost_per_1k": 0.00125,  # $1.25 per million tokens
            "avg_latency": 1.2,
            "quality_score": 0.82,
        },
    },
    "specialist": {
        "primary": {
            "model": "claude-3-5-haiku-20241022",  # Use newer Haiku for specialists
            "provider": "anthropic",
            "input_cost_per_1k": 0.0008,  # $0.80 per million tokens
            "output_cost_per_1k": 0.004,  # $4 per million tokens
            "avg_latency": 1.0,
            "quality_score": 0.88,
        },
        "fallback": {
            "model": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "input_cost_per_1k": 0.00025,  # $0.25 per million tokens
            "output_cost_per_1k": 0.00125,  # $1.25 per million tokens
            "avg_latency": 1.2,
            "quality_score": 0.82,
        },
        "budget": {
            "model": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "input_cost_per_1k": 0.00025,  # $0.25 per million tokens
            "output_cost_per_1k": 0.00125,  # $1.25 per million tokens
            "avg_latency": 1.2,
            "quality_score": 0.82,
        },
    },
    "worker": {
        "primary": {
            "model": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "input_cost_per_1k": 0.00025,  # $0.25 per million tokens
            "output_cost_per_1k": 0.00125,  # $1.25 per million tokens
            "avg_latency": 1.2,
            "quality_score": 0.82,
        },
        "fallback": {
            "model": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "input_cost_per_1k": 0.00025,  # $0.25 per million tokens
            "output_cost_per_1k": 0.00125,  # $1.25 per million tokens
            "avg_latency": 1.2,
            "quality_score": 0.82,
        },
        "budget": {
            "model": "claude-3-haiku-20240307",
            "provider": "anthropic",
            "input_cost_per_1k": 0.00025,  # $0.25 per million tokens
            "output_cost_per_1k": 0.00125,  # $1.25 per million tokens
            "avg_latency": 1.2,
            "quality_score": 0.82,
        },
    },
}

# Cost tracking database schema
COST_TRACKING_SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_cost_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_id TEXT UNIQUE NOT NULL,
    agent_name TEXT NOT NULL,
    model_used TEXT NOT NULL,
    provider TEXT NOT NULL,
    task_type TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    input_cost DECIMAL(10,6),
    output_cost DECIMAL(10,6),
    total_cost DECIMAL(10,6),
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_latency_ms INTEGER,
    quality_score DECIMAL(3,2),
    strategy_used TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    INDEX idx_agent_name (agent_name),
    INDEX idx_timestamp (request_timestamp),
    INDEX idx_model (model_used)
);

CREATE TABLE IF NOT EXISTS llm_cost_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0,
    avg_latency_ms INTEGER,
    success_rate DECIMAL(5,2),
    models_used TEXT,  -- JSON array of models
    UNIQUE(agent_name, date)
);

CREATE TABLE IF NOT EXISTS llm_budget_tracking (
    agent_name TEXT PRIMARY KEY,
    daily_budget DECIMAL(10,2),
    current_daily_spend DECIMAL(10,4) DEFAULT 0,
    monthly_budget DECIMAL(10,2),
    current_monthly_spend DECIMAL(10,4) DEFAULT 0,
    last_reset_date DATE,
    budget_warnings INTEGER DEFAULT 0,
    is_throttled BOOLEAN DEFAULT FALSE
);
"""


def calculate_actual_cost(
    input_tokens: int, output_tokens: int, model_config: Dict[str, Any]
) -> Dict[str, float]:
    """Calculate actual cost based on token usage"""
    input_cost = (input_tokens / 1000) * model_config.get("input_cost_per_1k", 0)
    output_cost = (output_tokens / 1000) * model_config.get("output_cost_per_1k", 0)
    total_cost = input_cost + output_cost

    return {
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
    }


# Default API keys configuration
CLAUDE_API_CONFIG = {
    "api_key_env": "ANTHROPIC_API_KEY",
    "base_url": "https://api.anthropic.com/v1",
    "default_max_tokens": 1000,
    "default_temperature": 0.7,
    "timeout": 30,
}
