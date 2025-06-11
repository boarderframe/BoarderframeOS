"""
Cost Management Configuration for BoarderframeOS
Controls API usage, throttling, and cost optimization settings
"""

# API Cost Management Settings
API_COST_SETTINGS = {
    # Enable/disable cost optimization features
    "cost_optimization_enabled": True,

    # Agent idle behavior
    "idle_mode": {
        "enabled": True,
        "check_interval_seconds": 5,  # How often to check for new work
        "max_idle_time_minutes": 60,  # Max time to stay completely idle
    },

    # Message filtering for API calls
    "message_filtering": {
        "enabled": True,
        "urgent_keywords": [
            "urgent", "critical", "error", "down", "issue", "problem",
            "revenue", "customer", "strategic", "priority", "ceo", "executive"
        ],
        "routine_message_threshold": 5,  # Process routine messages in batches
    },

    # API rate limiting
    "rate_limiting": {
        "enabled": True,
        "max_calls_per_minute": 30,    # Per agent
        "max_calls_per_hour": 300,     # Per agent
        "max_calls_per_day": 2000,     # Per agent
    },

    # Cost monitoring
    "cost_monitoring": {
        "enabled": True,
        "track_token_usage": True,
        "daily_budget_usd": 50.0,      # Daily spending limit
        "warning_threshold_usd": 40.0,  # Warning when approaching limit
        "emergency_stop_usd": 55.0,    # Emergency stop if exceeded
    },

    # Smart batching
    "smart_batching": {
        "enabled": True,
        "batch_size": 5,               # Batch multiple messages together
        "batch_timeout_seconds": 30,   # Max time to wait for batch
    },

    # Emergency cost controls
    "emergency_controls": {
        "auto_shutdown_on_budget_exceeded": True,
        "fallback_to_rule_based": True,  # Use rules instead of LLM when budget low
        "reduced_functionality_mode": True,  # Disable non-essential features
    }
}

# Model-specific cost settings (approximate costs)
MODEL_COSTS = {
    "claude-3-5-sonnet-latest": {
        "input_cost_per_1k_tokens": 0.003,
        "output_cost_per_1k_tokens": 0.015,
        "estimated_tokens_per_call": 1000,  # Conservative estimate
    },
    "claude-3-opus-20240229": {
        "input_cost_per_1k_tokens": 0.015,
        "output_cost_per_1k_tokens": 0.075,
        "estimated_tokens_per_call": 1200,
    },
    "claude-3-haiku-20240307": {
        "input_cost_per_1k_tokens": 0.00025,
        "output_cost_per_1k_tokens": 0.00125,
        "estimated_tokens_per_call": 800,
    }
}

# Agent-specific cost policies
AGENT_COST_POLICIES = {
    "solomon": {
        "priority": "high",  # Chief of Staff needs more API access
        "daily_budget_usd": 25.0,
        "emergency_mode_threshold": 20.0,
        "fallback_strategy": "rule_based_decisions",
    },
    "david": {
        "priority": "high",  # CEO needs strategic capability
        "daily_budget_usd": 20.0,
        "emergency_mode_threshold": 15.0,
        "fallback_strategy": "simplified_reasoning",
    },
    "default": {
        "priority": "medium",
        "daily_budget_usd": 10.0,
        "emergency_mode_threshold": 8.0,
        "fallback_strategy": "rule_based_only",
    }
}

def get_agent_cost_policy(agent_name: str) -> dict:
    """Get cost policy for specific agent"""
    return AGENT_COST_POLICIES.get(agent_name, AGENT_COST_POLICIES["default"])

def estimate_daily_cost(agent_name: str, calls_per_day: int, model: str = "claude-3-5-sonnet-latest") -> float:
    """Estimate daily cost for an agent"""
    if model not in MODEL_COSTS:
        model = "claude-3-5-sonnet-latest"

    model_cost = MODEL_COSTS[model]
    tokens_per_call = model_cost["estimated_tokens_per_call"]
    input_cost = model_cost["input_cost_per_1k_tokens"]
    output_cost = model_cost["output_cost_per_1k_tokens"]

    # Assume 70% input, 30% output tokens
    input_tokens = tokens_per_call * 0.7
    output_tokens = tokens_per_call * 0.3

    cost_per_call = (input_tokens / 1000 * input_cost) + (output_tokens / 1000 * output_cost)
    daily_cost = cost_per_call * calls_per_day

    return daily_cost

def get_cost_optimization_status() -> dict:
    """Get current cost optimization status"""
    return {
        "cost_optimization_enabled": API_COST_SETTINGS["cost_optimization_enabled"],
        "idle_mode_enabled": API_COST_SETTINGS["idle_mode"]["enabled"],
        "message_filtering_enabled": API_COST_SETTINGS["message_filtering"]["enabled"],
        "rate_limiting_enabled": API_COST_SETTINGS["rate_limiting"]["enabled"],
        "estimated_savings": "99.9% reduction in idle API usage",
        "before_optimization": "~86,400 API calls per day per agent",
        "after_optimization": "~0-50 API calls per day when idle"
    }

# Example usage and calculations
if __name__ == "__main__":
    print("💰 BoarderframeOS Cost Management Configuration")
    print("=" * 50)

    # Show optimization status
    status = get_cost_optimization_status()
    for key, value in status.items():
        print(f"✅ {key}: {value}")

    print(f"\n📊 Cost Estimates:")

    # Before optimization
    calls_before = 86400  # Every second for 24 hours
    cost_before_solomon = estimate_daily_cost("solomon", calls_before)
    cost_before_david = estimate_daily_cost("david", calls_before)

    print(f"Before optimization (continuous polling):")
    print(f"  Solomon: ${cost_before_solomon:.2f}/day")
    print(f"  David: ${cost_before_david:.2f}/day")
    print(f"  Total: ${cost_before_solomon + cost_before_david:.2f}/day")

    # After optimization
    calls_after = 10  # Only when needed
    cost_after_solomon = estimate_daily_cost("solomon", calls_after)
    cost_after_david = estimate_daily_cost("david", calls_after)

    print(f"\nAfter optimization (event-driven):")
    print(f"  Solomon: ${cost_after_solomon:.2f}/day")
    print(f"  David: ${cost_after_david:.2f}/day")
    print(f"  Total: ${cost_after_solomon + cost_after_david:.2f}/day")

    # Savings
    total_savings = (cost_before_solomon + cost_before_david) - (cost_after_solomon + cost_after_david)
    savings_percent = (total_savings / (cost_before_solomon + cost_before_david)) * 100

    print(f"\n💡 Savings:")
    print(f"  Daily savings: ${total_savings:.2f}")
    print(f"  Monthly savings: ${total_savings * 30:.2f}")
    print(f"  Percentage saved: {savings_percent:.1f}%")
