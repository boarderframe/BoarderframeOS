#!/usr/bin/env python3
"""
Simple test of the coordination demo functionality
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "boarderframeos"))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

import asyncio
import logging
from datetime import datetime, timedelta

from core.agent_controller import AgentController, AgentTask, TaskPriority
from core.agent_registry import AgentCapability
from core.enhanced_message_bus import (
    DeliveryStatus,
    EnhancedAgentMessage,
    RoutingStrategy,
)
from core.message_bus import MessagePriority, MessageType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_demo")


async def simple_test():
    """Simple test of the coordination functionality"""
    try:
        logger.info("Starting simple coordination test...")

        # Start the agent controller
        controller = AgentController()
        await controller.start()
        logger.info("✅ Agent controller started")

        # Register some capabilities
        solomon_capabilities = [
            AgentCapability.PLANNING,
            AgentCapability.COORDINATION,
            AgentCapability.ANALYSIS,
        ]
        await controller.register_agent_capabilities("solomon", solomon_capabilities)
        logger.info("✅ Registered capabilities for solomon")

        # Test agent discovery
        agents = await controller.discover_agents_by_capability("planning")
        logger.info(f"✅ Agents with planning capability: {agents}")

        # Test creating a task
        task_id = await controller.auto_assign_task(
            task_type="test_task",
            data={"test": "data"},
            required_capabilities=[AgentCapability.PLANNING],
            routing_strategy="capability_based",
        )

        if task_id:
            logger.info(f"✅ Task created successfully: {task_id}")
        else:
            logger.info("ℹ️ Task creation returned None (no agents available to handle)")

        # Get metrics
        metrics = await controller.get_agent_coordination_metrics()
        logger.info(f"✅ Got coordination metrics: {len(metrics)} items")

        # Stop controller
        await controller.stop()
        logger.info("✅ Controller stopped successfully")

        logger.info("🎉 Simple test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_test())
