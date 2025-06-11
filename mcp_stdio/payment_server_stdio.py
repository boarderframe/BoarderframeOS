#!/usr/bin/env python3
"""
MCP Payment Server - stdio transport wrapper
Wraps the HTTP-based payment server for use with Claude CLI
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
log_file = Path(__file__).parent / "payment_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger("payment_stdio")

server = Server("payment")

# Mock data for development
transactions = []
subscriptions = {}
customers = {}
invoices = []

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available payment tools."""
    return [
        types.Tool(
            name="process_payment",
            description="Process a payment transaction",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Payment amount"
                    },
                    "currency": {
                        "type": "string",
                        "description": "Payment currency",
                        "default": "usd"
                    },
                    "description": {
                        "type": "string",
                        "description": "Payment description (optional)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)"
                    }
                },
                "required": ["customer_id", "amount"]
            }
        ),
        types.Tool(
            name="create_subscription",
            description="Create a new subscription",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier"
                    },
                    "plan_id": {
                        "type": "string",
                        "description": "Subscription plan ID"
                    },
                    "billing_cycle": {
                        "type": "string",
                        "description": "Billing cycle: monthly, quarterly, yearly",
                        "default": "monthly"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)"
                    }
                },
                "required": ["customer_id", "plan_id"]
            }
        ),
        types.Tool(
            name="get_subscription",
            description="Get subscription details for a customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier"
                    }
                },
                "required": ["customer_id"]
            }
        ),
        types.Tool(
            name="generate_invoice",
            description="Generate an invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier"
                    },
                    "items": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Invoice items"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Invoice due date (optional)"
                    }
                },
                "required": ["customer_id", "items"]
            }
        ),
        types.Tool(
            name="get_payment_stats",
            description="Get payment statistics",
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
        if name == "process_payment":
            return await process_payment(arguments)
        elif name == "create_subscription":
            return await create_subscription(arguments)
        elif name == "get_subscription":
            return await get_subscription(arguments)
        elif name == "generate_invoice":
            return await generate_invoice(arguments)
        elif name == "get_payment_stats":
            return await get_payment_stats()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def process_payment(args: Dict[str, Any]) -> List[types.TextContent]:
    """Process a payment."""
    try:
        transaction_id = str(uuid.uuid4())

        transaction = {
            "id": transaction_id,
            "customer_id": args["customer_id"],
            "amount": args["amount"],
            "currency": args.get("currency", "usd"),
            "description": args.get("description"),
            "status": "completed",  # Mock successful payment
            "processor": "mock",
            "created_at": datetime.now().isoformat(),
            "metadata": args.get("metadata", {})
        }

        transactions.append(transaction)

        result = {
            "success": True,
            "transaction_id": transaction_id,
            "status": "completed",
            "customer_id": args["customer_id"],
            "amount": args["amount"],
            "currency": args.get("currency", "usd"),
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error processing payment: {str(e)}")]

async def create_subscription(args: Dict[str, Any]) -> List[types.TextContent]:
    """Create a new subscription."""
    try:
        subscription_id = str(uuid.uuid4())

        subscription = {
            "id": subscription_id,
            "customer_id": args["customer_id"],
            "plan_id": args["plan_id"],
            "billing_cycle": args.get("billing_cycle", "monthly"),
            "status": "active",
            "processor": "mock",
            "created_at": datetime.now().isoformat(),
            "next_billing_date": None,  # Would calculate based on billing cycle
            "metadata": args.get("metadata", {})
        }

        subscriptions[subscription_id] = subscription
        customers[args["customer_id"]] = subscription_id

        result = {
            "success": True,
            "subscription_id": subscription_id,
            "status": "active",
            "customer_id": args["customer_id"],
            "plan_id": args["plan_id"],
            "billing_cycle": args.get("billing_cycle", "monthly"),
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error creating subscription: {str(e)}")]

async def get_subscription(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get subscription details for a customer."""
    try:
        customer_id = args["customer_id"]

        if customer_id not in customers:
            result = {
                "success": False,
                "error": "No subscription found for customer",
                "customer_id": customer_id
            }
        else:
            subscription_id = customers[customer_id]
            subscription = subscriptions[subscription_id]

            result = {
                "success": True,
                "subscription": subscription,
                "customer_id": customer_id,
                "timestamp": datetime.now().isoformat()
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting subscription: {str(e)}")]

async def generate_invoice(args: Dict[str, Any]) -> List[types.TextContent]:
    """Generate an invoice."""
    try:
        invoice_id = str(uuid.uuid4())

        # Calculate total
        total = sum(item.get("amount", 0) for item in args["items"])

        invoice = {
            "id": invoice_id,
            "customer_id": args["customer_id"],
            "items": args["items"],
            "total": total,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "due_date": args.get("due_date")
        }

        invoices.append(invoice)

        result = {
            "success": True,
            "invoice_id": invoice_id,
            "customer_id": args["customer_id"],
            "total": total,
            "status": "pending",
            "due_date": args.get("due_date"),
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error generating invoice: {str(e)}")]

async def get_payment_stats() -> List[types.TextContent]:
    """Get payment statistics."""
    try:
        total_revenue = sum(t["amount"] for t in transactions if t["status"] == "completed")
        active_subscriptions = len([s for s in subscriptions.values() if s["status"] == "active"])

        result = {
            "success": True,
            "stats": {
                "total_transactions": len(transactions),
                "total_revenue": total_revenue,
                "active_customers": len(customers),
                "active_subscriptions": active_subscriptions,
                "pending_invoices": len([i for i in invoices if i["status"] == "pending"])
            },
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting payment stats: {str(e)}")]

async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="payment",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
