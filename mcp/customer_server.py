#!/usr/bin/env python3
"""
BoarderframeOS MCP Customer Server
Manages customer data, subscriptions, and interactions
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
from pydantic import BaseModel, EmailStr, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_customer")


class CustomerCreate(BaseModel):
    """Customer creation model"""

    email: str  # Would use EmailStr in a full implementation
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_by_agent: Optional[str] = None


class CustomerUpdate(BaseModel):
    """Customer update model"""

    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    subscription_status: Optional[str] = None
    monthly_value: Optional[float] = None


class InteractionCreate(BaseModel):
    """Customer interaction model"""

    customer_id: str
    interaction_type: str  # support, feedback, onboarding, etc.
    content: str
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPCustomerServer:
    """
    MCP Customer Server
    Manages customer data, subscriptions, and interactions
    """

    def __init__(self):
        """Initialize the customer server"""
        self.app = FastAPI(title="MCP Customer Server")
        self.setup_app()
        self.database_url = "http://localhost:8010/rpc"  # PostgreSQL Database Server
        self.payment_url = "http://localhost:8006"  # MCP Payment Server
        self.customers = {}
        self.interactions = []

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
        self.app.post("/customers")(self.create_customer)
        self.app.get("/customers/{customer_id}")(self.get_customer)
        self.app.put("/customers/{customer_id}")(self.update_customer)
        self.app.delete("/customers/{customer_id}")(self.delete_customer)
        self.app.get("/customers")(self.list_customers)
        self.app.post("/interactions")(self.create_interaction)
        self.app.get("/customers/{customer_id}/interactions")(
            self.list_customer_interactions
        )
        self.app.get("/customers/{customer_id}/subscription")(
            self.get_customer_subscription
        )
        self.app.get("/stats")(self.get_stats)

    async def start(self, port: int = 8008):
        """Start the Customer server"""
        logger.info(f"Starting MCP Customer Server on port {port}")

        # Initialize database connection
        await self.initialize_database()

        # Start the server
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()

    async def initialize_database(self):
        """Initialize database connection"""
        logger.info("Initializing customer database connection")

    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "customers_count": len(self.customers),
            "interactions_count": len(self.interactions),
            "server": "mcp_customer",
        }

    async def create_customer(self, customer: CustomerCreate):
        """Create a new customer"""
        try:
            # Generate a customer ID
            customer_id = str(uuid.uuid4())

            # Record customer details
            customer_data = {
                "id": customer_id,
                "email": customer.email,
                "name": customer.name,
                "created_at": datetime.now().isoformat(),
                "subscription_status": "none",
                "monthly_value": 0.0,
                "created_by_agent": customer.created_by_agent,
                "metadata": customer.metadata or {},
                "stripe_customer_id": None,  # Would be populated by Stripe API
            }

            # Store customer
            self.customers[customer_id] = customer_data

            # If Stripe integration is enabled, create a Stripe customer
            # await self.create_stripe_customer(customer_id, customer.email)

            # Track this as an analytics event
            await self.track_analytics_event("new_customer", customer_id)

            return {
                "customer_id": customer_id,
                "email": customer.email,
                "name": customer.name,
                "created_at": customer_data["created_at"],
            }

        except Exception as e:
            logger.error(f"Customer creation error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Customer creation error: {str(e)}"
            )

    async def get_customer(self, customer_id: str):
        """Get customer details"""
        if customer_id not in self.customers:
            raise HTTPException(status_code=404, detail="Customer not found")

        return self.customers[customer_id]

    async def update_customer(self, customer_id: str, update: CustomerUpdate):
        """Update customer details"""
        if customer_id not in self.customers:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer = self.customers[customer_id]

        # Update fields
        if update.name is not None:
            customer["name"] = update.name

        if update.metadata is not None:
            customer["metadata"].update(update.metadata)

        if update.subscription_status is not None:
            customer["subscription_status"] = update.subscription_status

        if update.monthly_value is not None:
            customer["monthly_value"] = update.monthly_value

        return customer

    async def delete_customer(self, customer_id: str):
        """Delete a customer"""
        if customer_id not in self.customers:
            raise HTTPException(status_code=404, detail="Customer not found")

        # In a real implementation, this might mark as inactive instead of deleting
        del self.customers[customer_id]

        return {"status": "deleted", "customer_id": customer_id}

    async def list_customers(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ):
        """List customers with filtering options"""
        customers_list = list(self.customers.values())

        # Apply status filter if provided
        if status:
            customers_list = [
                c for c in customers_list if c["subscription_status"] == status
            ]

        # Apply pagination
        paginated = customers_list[skip : skip + limit]

        return {
            "total": len(customers_list),
            "skip": skip,
            "limit": limit,
            "customers": paginated,
        }

    async def create_interaction(self, interaction: InteractionCreate):
        """Create a new customer interaction"""
        try:
            # Check if customer exists
            if interaction.customer_id not in self.customers:
                raise HTTPException(status_code=404, detail="Customer not found")

            # Generate an interaction ID
            interaction_id = str(uuid.uuid4())

            # Record interaction details
            interaction_data = {
                "id": interaction_id,
                "customer_id": interaction.customer_id,
                "interaction_type": interaction.interaction_type,
                "content": interaction.content,
                "agent_id": interaction.agent_id,
                "created_at": datetime.now().isoformat(),
                "metadata": interaction.metadata or {},
            }

            # Store interaction
            self.interactions.append(interaction_data)

            return {
                "interaction_id": interaction_id,
                "customer_id": interaction.customer_id,
                "created_at": interaction_data["created_at"],
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Interaction creation error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Interaction creation error: {str(e)}"
            )

    async def list_customer_interactions(
        self, customer_id: str, skip: int = 0, limit: int = 100
    ):
        """List interactions for a specific customer"""
        if customer_id not in self.customers:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Filter interactions by customer
        customer_interactions = [
            i for i in self.interactions if i["customer_id"] == customer_id
        ]

        # Sort by creation date (newest first)
        customer_interactions.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        paginated = customer_interactions[skip : skip + limit]

        return {
            "total": len(customer_interactions),
            "skip": skip,
            "limit": limit,
            "interactions": paginated,
        }

    async def get_customer_subscription(self, customer_id: str):
        """Get subscription information for a customer"""
        if customer_id not in self.customers:
            raise HTTPException(status_code=404, detail="Customer not found")

        # In a real implementation, this would query the Payment Server
        # For now, we'll return mock data

        subscription_status = self.customers[customer_id]["subscription_status"]

        if subscription_status == "none":
            return {"status": "none", "message": "Customer has no active subscription"}

        return {
            "status": subscription_status,
            "plan": "pro",
            "monthly_value": self.customers[customer_id]["monthly_value"],
            "next_billing_date": "2023-07-01",
            "payment_method": "card",
        }

    async def track_analytics_event(
        self, event_type: str, customer_id: str, data: Dict[str, Any] = None
    ):
        """Track an analytics event"""
        # In a real implementation, this would call the Analytics Server
        logger.info(
            f"Tracking analytics event: {event_type} for customer {customer_id}"
        )

    async def get_stats(self):
        """Get customer statistics"""
        total_customers = len(self.customers)
        active_subscriptions = sum(
            1 for c in self.customers.values() if c["subscription_status"] == "active"
        )
        total_monthly_value = sum(c["monthly_value"] for c in self.customers.values())

        return {
            "total_customers": total_customers,
            "active_subscriptions": active_subscriptions,
            "total_monthly_value": total_monthly_value,
            "average_monthly_value": (
                total_monthly_value / active_subscriptions
                if active_subscriptions > 0
                else 0
            ),
        }


async def main():
    """Run the server directly"""
    import uvicorn

    # Default port
    port = 8008

    # Get port from command line if specified
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid port: {sys.argv[1]}. Using default: {port}")

    # Create and start the server
    server = MCPCustomerServer()
    await server.start(port)


if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Customer Server")
