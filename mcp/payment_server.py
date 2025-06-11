#!/usr/bin/env python3
"""
BoarderframeOS MCP Payment Server
Handles payments, subscriptions, and billing operations
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import uvicorn
from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_payment")

class PaymentRequest(BaseModel):
    customer_id: str
    amount: float
    currency: str = "usd"
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionRequest(BaseModel):
    customer_id: str
    plan_id: str
    billing_cycle: str = "monthly"  # monthly, quarterly, yearly
    metadata: Optional[Dict[str, Any]] = None


class InvoiceRequest(BaseModel):
    customer_id: str
    items: List[Dict[str, Any]]
    due_date: Optional[str] = None


class MCPPaymentServer:
    """
    MCP Payment Server
    Handles payments, subscriptions, and billing operations
    """

    def __init__(self):
        """Initialize the payment server"""
        self.app = FastAPI(title="MCP Payment Server")
        self.setup_app()
        self.stripe_key = os.environ.get("STRIPE_API_KEY", "")
        self.stripe_enabled = bool(self.stripe_key)
        self.database_url = "http://localhost:8004/rpc"  # MCP Database Server
        self.customers = {}
        self.subscriptions = {}
        self.transactions = []
        self.invoices = []

    def setup_app(self):
        """Set up the FastAPI application"""
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add routes
        self.app.get("/health")(self.health_check)
        self.app.post("/payment")(self.process_payment)
        self.app.post("/subscription")(self.create_subscription)
        self.app.get("/subscription/{customer_id}")(self.get_subscription)
        self.app.post("/invoice")(self.generate_invoice)
        self.app.get("/invoice/{invoice_id}")(self.get_invoice)
        self.app.post("/webhook")(self.handle_webhook)
        self.app.get("/stats")(self.get_stats)

    async def start(self, port: int = 8006):
        """Start the Payment server"""
        logger.info(f"Starting MCP Payment Server on port {port}")

        # Initialize database connection and tables
        await self.initialize_database()

        # Start the server
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()

    async def initialize_database(self):
        """Initialize database connection and create tables if they don't exist"""
        # This would connect to the MCP Database Server to ensure tables exist
        logger.info("Initializing payment database connection")
        # In a full implementation, this would check for required tables
        # and create them if needed

    async def health_check(self):
        """Health check endpoint"""
        stripe_status = "enabled" if self.stripe_enabled else "disabled"
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stripe_integration": stripe_status,
            "transactions": len(self.transactions),
            "active_subscriptions": len(self.subscriptions),
            "server": "mcp_payment"
        }

    async def process_payment(self, request: PaymentRequest):
        """Process a payment"""
        try:
            # Generate a transaction ID
            transaction_id = str(uuid.uuid4())

            # Record transaction details
            transaction = {
                "id": transaction_id,
                "customer_id": request.customer_id,
                "amount": request.amount,
                "currency": request.currency,
                "description": request.description,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "metadata": request.metadata or {}
            }

            # If Stripe is enabled, process with Stripe API
            if self.stripe_enabled:
                # In a real implementation, this would call the Stripe API
                transaction["status"] = "completed"
                transaction["processor"] = "stripe"
                logger.info(f"Payment processed via Stripe: {transaction_id}")
            else:
                # Mock successful payment for development
                transaction["status"] = "completed"
                transaction["processor"] = "mock"
                logger.info(f"Payment processed via mock: {transaction_id}")

            # Store transaction
            self.transactions.append(transaction)

            # Store in database (in a full implementation)
            # await self.store_transaction(transaction)

            return {
                "transaction_id": transaction_id,
                "status": transaction["status"],
                "customer_id": request.customer_id,
                "amount": request.amount,
                "currency": request.currency
            }

        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Payment processing error: {str(e)}")

    async def create_subscription(self, request: SubscriptionRequest):
        """Create a new subscription"""
        try:
            # Generate a subscription ID
            subscription_id = str(uuid.uuid4())

            # Record subscription details
            subscription = {
                "id": subscription_id,
                "customer_id": request.customer_id,
                "plan_id": request.plan_id,
                "billing_cycle": request.billing_cycle,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "next_billing_date": None,  # Would calculate based on billing cycle
                "metadata": request.metadata or {}
            }

            # If Stripe is enabled, create subscription with Stripe API
            if self.stripe_enabled:
                # In a real implementation, this would call the Stripe API
                subscription["processor"] = "stripe"
                logger.info(f"Subscription created via Stripe: {subscription_id}")
            else:
                # Mock subscription for development
                subscription["processor"] = "mock"
                logger.info(f"Subscription created via mock: {subscription_id}")

            # Store subscription
            self.subscriptions[subscription_id] = subscription

            # Store customer's active subscription
            self.customers[request.customer_id] = subscription_id

            return {
                "subscription_id": subscription_id,
                "status": "active",
                "customer_id": request.customer_id,
                "plan_id": request.plan_id,
                "billing_cycle": request.billing_cycle
            }

        except Exception as e:
            logger.error(f"Subscription creation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Subscription creation error: {str(e)}")

    async def get_subscription(self, customer_id: str):
        """Get subscription details for a customer"""
        if customer_id not in self.customers:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription_id = self.customers[customer_id]
        return self.subscriptions[subscription_id]

    async def generate_invoice(self, request: InvoiceRequest):
        """Generate an invoice"""
        try:
            # Generate an invoice ID
            invoice_id = str(uuid.uuid4())

            # Calculate total
            total = sum(item.get("amount", 0) for item in request.items)

            # Record invoice details
            invoice = {
                "id": invoice_id,
                "customer_id": request.customer_id,
                "items": request.items,
                "total": total,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "due_date": request.due_date,
            }

            # Store invoice
            self.invoices.append(invoice)

            return {
                "invoice_id": invoice_id,
                "customer_id": request.customer_id,
                "total": total,
                "status": "pending",
                "due_date": request.due_date
            }

        except Exception as e:
            logger.error(f"Invoice generation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Invoice generation error: {str(e)}")

    async def get_invoice(self, invoice_id: str):
        """Get invoice details"""
        for invoice in self.invoices:
            if invoice["id"] == invoice_id:
                return invoice

        raise HTTPException(status_code=404, detail="Invoice not found")

    async def handle_webhook(self, request: Request):
        """Handle webhooks from payment processors"""
        try:
            # Get the webhook payload
            payload = await request.json()

            # Extract event type and data
            event_type = payload.get("type")
            event_data = payload.get("data", {})

            logger.info(f"Received webhook: {event_type}")

            # Process different event types
            if event_type == "payment_succeeded":
                # Update transaction status
                pass
            elif event_type == "payment_failed":
                # Handle failed payment
                pass
            elif event_type == "subscription_updated":
                # Update subscription details
                pass

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_stats(self):
        """Get payment statistics"""
        total_revenue = sum(t["amount"] for t in self.transactions if t["status"] == "completed")
        active_subscriptions = len([s for s in self.subscriptions.values() if s["status"] == "active"])

        return {
            "total_transactions": len(self.transactions),
            "total_revenue": total_revenue,
            "active_customers": len(self.customers),
            "active_subscriptions": active_subscriptions
        }

    async def store_transaction(self, transaction):
        """Store transaction in the database"""
        # This would make an RPC call to the database server
        # to store the transaction in the revenue_transactions table
        pass

async def main():
    """Run the server directly"""
    import uvicorn

    # Default port
    port = 8006

    # Get port from command line if specified
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid port: {sys.argv[1]}. Using default: {port}")

    # Create and start the server
    server = MCPPaymentServer()
    await server.start(port)

if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Payment Server")
