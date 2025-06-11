#!/usr/bin/env python3
"""
MCP Analytics Server - stdio transport wrapper
Wraps the HTTP-based analytics server for use with Claude CLI
"""

import asyncio

# Handle MCP import conflicts by temporarily modifying sys.path
import importlib
import importlib.util
import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Save original sys.path
original_path = sys.path.copy()

# Remove current and parent directories to avoid local mcp module conflicts
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, '')]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith('mcp')]
for module_name in local_mcp_modules:
    del sys.modules[module_name]

try:
    # Import the real MCP package
    import mcp.server.stdio
    from mcp import types
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
finally:
    # Restore original sys.path
    sys.path = original_path

# Configure logging to file to avoid interfering with stdio
log_file = Path(__file__).parent / "analytics_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger("analytics_stdio")

server = Server("analytics")

# Mock data for development
events = []
metrics = {
    "customers_acquired": 0,
    "total_revenue": 0,
    "churn_count": 0,
    "revenue_per_agent": {},
    "api_usage": {}
}

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available analytics tools."""
    return [
        types.Tool(
            name="track_event",
            description="Track an analytics event",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "description": "Type of event to track"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent ID (optional)"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID (optional)"
                    },
                    "data": {
                        "type": "object",
                        "description": "Event data"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)"
                    }
                },
                "required": ["event_type", "data"]
            }
        ),
        types.Tool(
            name="get_customer_acquisition_cost",
            description="Calculate customer acquisition cost",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe: day, week, month",
                        "default": "month"
                    }
                }
            }
        ),
        types.Tool(
            name="get_customer_lifetime_value",
            description="Calculate customer lifetime value",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe: day, week, month",
                        "default": "month"
                    }
                }
            }
        ),
        types.Tool(
            name="get_churn_rate",
            description="Calculate churn rate",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe: day, week, month",
                        "default": "month"
                    }
                }
            }
        ),
        types.Tool(
            name="get_revenue_per_agent",
            description="Get revenue generated per agent",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_api_usage_metrics",
            description="Get API usage metrics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_dashboard_data",
            description="Get comprehensive dashboard data",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "track_event":
            return await track_event(arguments)
        elif name == "get_customer_acquisition_cost":
            return await get_customer_acquisition_cost(arguments)
        elif name == "get_customer_lifetime_value":
            return await get_customer_lifetime_value(arguments)
        elif name == "get_churn_rate":
            return await get_churn_rate(arguments)
        elif name == "get_revenue_per_agent":
            return await get_revenue_per_agent()
        elif name == "get_api_usage_metrics":
            return await get_api_usage_metrics()
        elif name == "get_dashboard_data":
            return await get_dashboard_data()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def track_event(args: Dict[str, Any]) -> List[types.TextContent]:
    """Track an analytics event."""
    try:
        event_id = str(uuid.uuid4())

        event_data = {
            "id": event_id,
            "event_type": args["event_type"],
            "agent_id": args.get("agent_id"),
            "customer_id": args.get("customer_id"),
            "data": args["data"],
            "metadata": args.get("metadata", {}),
            "timestamp": datetime.now().isoformat()
        }

        events.append(event_data)

        # Update relevant metrics
        await update_metrics(event_data)

        result = {
            "success": True,
            "event_id": event_id,
            "status": "recorded",
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error tracking event: {str(e)}")]

async def update_metrics(event_data: Dict[str, Any]):
    """Update metrics based on new event."""
    event_type = event_data["event_type"]

    if event_type == "new_customer":
        metrics["customers_acquired"] += 1

    elif event_type == "revenue":
        amount = event_data["data"].get("amount", 0)
        metrics["total_revenue"] += amount

        # Track revenue per agent if agent_id is provided
        if event_data["agent_id"]:
            agent_id = event_data["agent_id"]
            if "revenue_per_agent" not in metrics:
                metrics["revenue_per_agent"] = {}
            metrics["revenue_per_agent"][agent_id] = metrics["revenue_per_agent"].get(agent_id, 0) + amount

    elif event_type == "churn":
        metrics["churn_count"] += 1

    elif event_type == "api_usage":
        tokens = event_data["data"].get("tokens", 0)
        endpoint = event_data["data"].get("endpoint", "unknown")

        if "api_usage" not in metrics:
            metrics["api_usage"] = {}
        if endpoint not in metrics["api_usage"]:
            metrics["api_usage"][endpoint] = 0
        metrics["api_usage"][endpoint] += tokens

async def get_customer_acquisition_cost(args: Dict[str, Any]) -> List[types.TextContent]:
    """Calculate customer acquisition cost."""
    try:
        timeframe = args.get("timeframe", "month")

        # Mock values for development
        marketing_spend = 5000
        customers_acquired = metrics.get("customers_acquired", 10)

        if customers_acquired == 0:
            cac = 0
        else:
            cac = marketing_spend / customers_acquired

        result = {
            "success": True,
            "metric": "customer_acquisition_cost",
            "value": cac,
            "currency": "usd",
            "timeframe": timeframe,
            "customers_acquired": customers_acquired,
            "marketing_spend": marketing_spend,
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error calculating CAC: {str(e)}")]

async def get_customer_lifetime_value(args: Dict[str, Any]) -> List[types.TextContent]:
    """Calculate customer lifetime value."""
    try:
        timeframe = args.get("timeframe", "month")

        # Mock values for development
        avg_revenue_per_customer = 150
        avg_customer_lifespan = 12  # months
        clv = avg_revenue_per_customer * avg_customer_lifespan

        result = {
            "success": True,
            "metric": "customer_lifetime_value",
            "value": clv,
            "currency": "usd",
            "timeframe": timeframe,
            "avg_revenue_per_customer": avg_revenue_per_customer,
            "avg_customer_lifespan": avg_customer_lifespan,
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error calculating CLV: {str(e)}")]

async def get_churn_rate(args: Dict[str, Any]) -> List[types.TextContent]:
    """Calculate churn rate."""
    try:
        timeframe = args.get("timeframe", "month")

        # Mock values for development
        total_customers_start = 100
        churned_customers = metrics.get("churn_count", 5)

        if total_customers_start == 0:
            churn_rate = 0
        else:
            churn_rate = (churned_customers / total_customers_start) * 100

        result = {
            "success": True,
            "metric": "churn_rate",
            "value": churn_rate,
            "unit": "percentage",
            "timeframe": timeframe,
            "total_customers_start": total_customers_start,
            "churned_customers": churned_customers,
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error calculating churn rate: {str(e)}")]

async def get_revenue_per_agent() -> List[types.TextContent]:
    """Get revenue generated per agent."""
    try:
        revenue_per_agent = metrics.get("revenue_per_agent", {})

        # Sort agents by revenue (highest first)
        sorted_agents = sorted(
            revenue_per_agent.items(),
            key=lambda x: x[1],
            reverse=True
        )

        results = [
            {"agent_id": agent_id, "revenue": revenue}
            for agent_id, revenue in sorted_agents
        ]

        result = {
            "success": True,
            "metric": "revenue_per_agent",
            "data": results,
            "currency": "usd",
            "total_agents": len(results),
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting revenue per agent: {str(e)}")]

async def get_api_usage_metrics() -> List[types.TextContent]:
    """Get API usage metrics."""
    try:
        api_usage = metrics.get("api_usage", {})

        total_tokens = sum(api_usage.values())

        # Sort endpoints by usage (highest first)
        sorted_usage = sorted(
            api_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )

        results = [
            {"endpoint": endpoint, "tokens": tokens}
            for endpoint, tokens in sorted_usage
        ]

        result = {
            "success": True,
            "metric": "api_usage",
            "data": results,
            "total_tokens": total_tokens,
            "endpoints_count": len(results),
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting API usage metrics: {str(e)}")]

async def get_dashboard_data() -> List[types.TextContent]:
    """Get comprehensive dashboard data."""
    try:
        # Get all KPIs
        cac_result = await get_customer_acquisition_cost({"timeframe": "month"})
        clv_result = await get_customer_lifetime_value({"timeframe": "month"})
        churn_result = await get_churn_rate({"timeframe": "month"})
        revenue_result = await get_revenue_per_agent()
        api_result = await get_api_usage_metrics()

        # Parse results (they're in TextContent format)
        cac_data = json.loads(cac_result[0].text)
        clv_data = json.loads(clv_result[0].text)
        churn_data = json.loads(churn_result[0].text)
        revenue_data = json.loads(revenue_result[0].text)
        api_data = json.loads(api_result[0].text)

        # Calculate additional metrics
        clv_cac_ratio = clv_data["value"] / cac_data["value"] if cac_data["value"] > 0 else 0

        result = {
            "success": True,
            "dashboard": {
                "metrics": {
                    "total_revenue": metrics.get("total_revenue", 0),
                    "customers_acquired": metrics.get("customers_acquired", 0),
                    "churn_rate": churn_data["value"],
                    "clv_cac_ratio": clv_cac_ratio,
                    "customer_acquisition_cost": cac_data["value"],
                    "customer_lifetime_value": clv_data["value"]
                },
                "revenue_per_agent": revenue_data["data"],
                "api_usage": api_data["data"],
                "events_tracked": len(events)
            },
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting dashboard data: {str(e)}")]

async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="analytics",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
