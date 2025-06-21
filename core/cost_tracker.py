"""
Cost Tracker - Database integration for LLM cost tracking
Persists all Agent Cortex API usage to PostgreSQL
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple
from uuid import UUID

import asyncpg

logger = logging.getLogger("cost_tracker")


class CostTracker:
    """Handles persistent cost tracking for Agent Cortex"""

    def __init__(
        self,
        db_url: str = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos",
    ):
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url, min_size=2, max_size=10, command_timeout=10
            )
            logger.info("Cost tracker database pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize cost tracker: {e}")
            raise

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()

    async def track_request(
        self,
        tracking_id: str,
        agent_name: str,
        model_used: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        input_cost: float,
        output_cost: float,
        total_cost: float,
        latency_ms: int,
        strategy: str,
        task_type: str,
        complexity: int = 5,
        quality_score: float = 0.85,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Track a single LLM request"""
        if not self.pool:
            logger.warning("Cost tracker not initialized, skipping tracking")
            return False

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO llm_cost_tracking (
                        tracking_id, agent_name, model_used, provider,
                        input_tokens, output_tokens, input_cost, output_cost, total_cost,
                        response_latency_ms, strategy_used, task_type,
                        complexity_score, quality_score, success, error_message, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """,
                    UUID(tracking_id),
                    agent_name,
                    model_used,
                    provider,
                    input_tokens,
                    output_tokens,
                    Decimal(str(input_cost)),
                    Decimal(str(output_cost)),
                    Decimal(str(total_cost)),
                    latency_ms,
                    strategy,
                    task_type,
                    complexity,
                    quality_score,
                    success,
                    error_message,
                    json.dumps(metadata or {}),
                )

                logger.debug(f"Tracked cost for {agent_name}: ${total_cost:.6f}")
                return True

        except Exception as e:
            logger.error(f"Failed to track cost: {e}")
            return False

    async def check_budget(self, agent_name: str) -> Tuple[bool, str, str]:
        """Check if agent is within budget limits"""
        if not self.pool:
            return True, "Budget check skipped", "Continue normal operation"

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    "SELECT * FROM check_budget_limit($1)", agent_name
                )

                if result:
                    return (
                        result["allowed"],
                        result["reason"],
                        result["recommended_action"],
                    )
                else:
                    # Agent not in budget tracking, allow by default
                    return True, "No budget limits set", "Continue normal operation"

        except Exception as e:
            logger.error(f"Budget check failed: {e}")
            # On error, allow request but log warning
            return True, f"Budget check error: {str(e)}", "Continue with caution"

    async def get_agent_stats(self, agent_name: str) -> Optional[Dict]:
        """Get current stats for an agent"""
        if not self.pool:
            return None

        try:
            async with self.pool.acquire() as conn:
                # Get today's stats
                today_stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as requests_today,
                        COALESCE(SUM(total_cost), 0) as cost_today,
                        COALESCE(AVG(response_latency_ms), 0) as avg_latency
                    FROM llm_cost_tracking
                    WHERE agent_name = $1
                    AND DATE(request_timestamp) = CURRENT_DATE
                """,
                    agent_name,
                )

                # Get budget info
                budget_info = await conn.fetchrow(
                    """
                    SELECT daily_budget, monthly_budget, current_daily_spend
                    FROM llm_budget_tracking
                    WHERE agent_name = $1
                """,
                    agent_name,
                )

                return {
                    "requests_today": today_stats["requests_today"],
                    "cost_today": float(today_stats["cost_today"]),
                    "avg_latency_ms": float(today_stats["avg_latency"]),
                    "daily_budget": float(budget_info["daily_budget"])
                    if budget_info
                    else 10.0,
                    "budget_remaining": float(
                        budget_info["daily_budget"] - budget_info["current_daily_spend"]
                    )
                    if budget_info
                    else 10.0,
                    "budget_percentage_used": float(
                        budget_info["current_daily_spend"]
                        / budget_info["daily_budget"]
                        * 100
                    )
                    if budget_info and budget_info["daily_budget"] > 0
                    else 0,
                }

        except Exception as e:
            logger.error(f"Failed to get agent stats: {e}")
            return None

    async def get_system_summary(self) -> Optional[Dict]:
        """Get system-wide cost summary"""
        if not self.pool:
            return None

        try:
            async with self.pool.acquire() as conn:
                # Get overall stats
                overall = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_requests,
                        COALESCE(SUM(total_cost), 0) as total_cost,
                        COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens,
                        COUNT(DISTINCT agent_name) as active_agents,
                        COUNT(DISTINCT model_used) as models_used
                    FROM llm_cost_tracking
                    WHERE DATE(request_timestamp) = CURRENT_DATE
                """
                )

                # Get per-model breakdown
                model_stats = await conn.fetch(
                    """
                    SELECT
                        model_used,
                        COUNT(*) as requests,
                        COALESCE(SUM(total_cost), 0) as cost
                    FROM llm_cost_tracking
                    WHERE DATE(request_timestamp) = CURRENT_DATE
                    GROUP BY model_used
                """
                )

                return {
                    "total_requests": overall["total_requests"],
                    "total_cost": float(overall["total_cost"]),
                    "total_tokens": overall["total_tokens"],
                    "active_agents": overall["active_agents"],
                    "models_used": overall["models_used"],
                    "model_breakdown": {
                        row["model_used"]: {
                            "requests": row["requests"],
                            "cost": float(row["cost"]),
                        }
                        for row in model_stats
                    },
                }

        except Exception as e:
            logger.error(f"Failed to get system summary: {e}")
            return None


# Global instance
cost_tracker = CostTracker()


async def track_llm_cost(
    tracking_id: str,
    agent_name: str,
    model_used: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    input_cost: float,
    output_cost: float,
    latency_ms: int,
    strategy: str = "balanced",
    task_type: str = "general",
    **kwargs,
) -> bool:
    """Convenience function to track LLM costs"""
    total_cost = input_cost + output_cost

    return await cost_tracker.track_request(
        tracking_id=tracking_id,
        agent_name=agent_name,
        model_used=model_used,
        provider=provider,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
        latency_ms=latency_ms,
        strategy=strategy,
        task_type=task_type,
        **kwargs,
    )


async def check_agent_budget(agent_name: str) -> Tuple[bool, str]:
    """Check if agent has budget available"""
    result = await cost_tracker.check_budget(agent_name)
    return result[0], f"{result[1]}. {result[2]}"
