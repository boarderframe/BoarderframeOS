#!/usr/bin/env python3
"""
MCP Customer Server - stdio transport wrapper
Wraps the HTTP-based customer server for use with Claude CLI
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
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, "")]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith("mcp")]
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
log_file = Path(__file__).parent / "customer_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)],
)
logger = logging.getLogger("customer_stdio")

server = Server("customer")

# Mock data for development
customers = {}
interactions = []


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available customer tools."""
    return [
        types.Tool(
            name="create_customer",
            description="Create a new customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Customer email address",
                    },
                    "name": {
                        "type": "string",
                        "description": "Customer name (optional)",
                    },
                    "created_by_agent": {
                        "type": "string",
                        "description": "Agent that created the customer (optional)",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)",
                    },
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="get_customer",
            description="Get customer details by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier",
                    }
                },
                "required": ["customer_id"],
            },
        ),
        types.Tool(
            name="update_customer",
            description="Update customer details",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier",
                    },
                    "name": {
                        "type": "string",
                        "description": "Updated name (optional)",
                    },
                    "subscription_status": {
                        "type": "string",
                        "description": "Updated subscription status (optional)",
                    },
                    "monthly_value": {
                        "type": "number",
                        "description": "Updated monthly value (optional)",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)",
                    },
                },
                "required": ["customer_id"],
            },
        ),
        types.Tool(
            name="list_customers",
            description="List customers with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by subscription status (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 100,
                    },
                    "skip": {
                        "type": "integer",
                        "description": "Number of results to skip",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="create_interaction",
            description="Create a customer interaction record",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier",
                    },
                    "interaction_type": {
                        "type": "string",
                        "description": "Type of interaction (support, feedback, onboarding, etc.)",
                    },
                    "content": {"type": "string", "description": "Interaction content"},
                    "agent_id": {
                        "type": "string",
                        "description": "Agent handling the interaction (optional)",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)",
                    },
                },
                "required": ["customer_id", "interaction_type", "content"],
            },
        ),
        types.Tool(
            name="get_customer_interactions",
            description="Get interactions for a specific customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 100,
                    },
                    "skip": {
                        "type": "integer",
                        "description": "Number of results to skip",
                        "default": 0,
                    },
                },
                "required": ["customer_id"],
            },
        ),
        types.Tool(
            name="get_customer_stats",
            description="Get customer statistics",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "create_customer":
            return await create_customer(arguments)
        elif name == "get_customer":
            return await get_customer(arguments)
        elif name == "update_customer":
            return await update_customer(arguments)
        elif name == "list_customers":
            return await list_customers(arguments)
        elif name == "create_interaction":
            return await create_interaction(arguments)
        elif name == "get_customer_interactions":
            return await get_customer_interactions(arguments)
        elif name == "get_customer_stats":
            return await get_customer_stats()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def create_customer(args: Dict[str, Any]) -> List[types.TextContent]:
    """Create a new customer."""
    try:
        customer_id = str(uuid.uuid4())

        customer_data = {
            "id": customer_id,
            "email": args["email"],
            "name": args.get("name"),
            "created_at": datetime.now().isoformat(),
            "subscription_status": "none",
            "monthly_value": 0.0,
            "created_by_agent": args.get("created_by_agent"),
            "metadata": args.get("metadata", {}),
            "stripe_customer_id": None,
        }

        customers[customer_id] = customer_data

        result = {
            "success": True,
            "customer_id": customer_id,
            "email": args["email"],
            "name": args.get("name"),
            "created_at": customer_data["created_at"],
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error creating customer: {str(e)}")
        ]


async def get_customer(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get customer details."""
    try:
        customer_id = args["customer_id"]

        if customer_id not in customers:
            result = {
                "success": False,
                "error": "Customer not found",
                "customer_id": customer_id,
            }
        else:
            result = {
                "success": True,
                "customer": customers[customer_id],
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error getting customer: {str(e)}")
        ]


async def update_customer(args: Dict[str, Any]) -> List[types.TextContent]:
    """Update customer details."""
    try:
        customer_id = args["customer_id"]

        if customer_id not in customers:
            result = {
                "success": False,
                "error": "Customer not found",
                "customer_id": customer_id,
            }
        else:
            customer = customers[customer_id]

            # Update fields if provided
            if "name" in args and args["name"] is not None:
                customer["name"] = args["name"]

            if (
                "subscription_status" in args
                and args["subscription_status"] is not None
            ):
                customer["subscription_status"] = args["subscription_status"]

            if "monthly_value" in args and args["monthly_value"] is not None:
                customer["monthly_value"] = args["monthly_value"]

            if "metadata" in args and args["metadata"] is not None:
                customer["metadata"].update(args["metadata"])

            customer["updated_at"] = datetime.now().isoformat()

            result = {
                "success": True,
                "customer": customer,
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error updating customer: {str(e)}")
        ]


async def list_customers(args: Dict[str, Any]) -> List[types.TextContent]:
    """List customers with optional filtering."""
    try:
        status = args.get("status")
        limit = args.get("limit", 100)
        skip = args.get("skip", 0)

        customers_list = list(customers.values())

        # Apply status filter if provided
        if status:
            customers_list = [
                c for c in customers_list if c["subscription_status"] == status
            ]

        # Apply pagination
        total = len(customers_list)
        paginated = customers_list[skip : skip + limit]

        result = {
            "success": True,
            "customers": paginated,
            "total": total,
            "skip": skip,
            "limit": limit,
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error listing customers: {str(e)}")
        ]


async def create_interaction(args: Dict[str, Any]) -> List[types.TextContent]:
    """Create a customer interaction."""
    try:
        customer_id = args["customer_id"]

        # Check if customer exists
        if customer_id not in customers:
            result = {
                "success": False,
                "error": "Customer not found",
                "customer_id": customer_id,
            }
        else:
            interaction_id = str(uuid.uuid4())

            interaction_data = {
                "id": interaction_id,
                "customer_id": customer_id,
                "interaction_type": args["interaction_type"],
                "content": args["content"],
                "agent_id": args.get("agent_id"),
                "created_at": datetime.now().isoformat(),
                "metadata": args.get("metadata", {}),
            }

            interactions.append(interaction_data)

            result = {
                "success": True,
                "interaction_id": interaction_id,
                "customer_id": customer_id,
                "created_at": interaction_data["created_at"],
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error creating interaction: {str(e)}")
        ]


async def get_customer_interactions(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get interactions for a specific customer."""
    try:
        customer_id = args["customer_id"]
        limit = args.get("limit", 100)
        skip = args.get("skip", 0)

        if customer_id not in customers:
            result = {
                "success": False,
                "error": "Customer not found",
                "customer_id": customer_id,
            }
        else:
            # Filter interactions by customer
            customer_interactions = [
                i for i in interactions if i["customer_id"] == customer_id
            ]

            # Sort by creation date (newest first)
            customer_interactions.sort(key=lambda x: x["created_at"], reverse=True)

            # Apply pagination
            total = len(customer_interactions)
            paginated = customer_interactions[skip : skip + limit]

            result = {
                "success": True,
                "customer_id": customer_id,
                "interactions": paginated,
                "total": total,
                "skip": skip,
                "limit": limit,
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(
                type="text", text=f"Error getting customer interactions: {str(e)}"
            )
        ]


async def get_customer_stats() -> List[types.TextContent]:
    """Get customer statistics."""
    try:
        total_customers = len(customers)
        active_subscriptions = sum(
            1 for c in customers.values() if c["subscription_status"] == "active"
        )
        total_monthly_value = sum(c["monthly_value"] for c in customers.values())

        result = {
            "success": True,
            "stats": {
                "total_customers": total_customers,
                "active_subscriptions": active_subscriptions,
                "total_monthly_value": total_monthly_value,
                "average_monthly_value": (
                    total_monthly_value / active_subscriptions
                    if active_subscriptions > 0
                    else 0
                ),
                "total_interactions": len(interactions),
            },
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(
                type="text", text=f"Error getting customer stats: {str(e)}"
            )
        ]


async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="customer",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
