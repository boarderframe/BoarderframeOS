#!/usr/bin/env python3
"""
Minimal test of the coordination demo to identify issues
"""

import os
import sys

sys.path.insert(0, 'boarderframeos')

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minimal_demo")

async def test_basic_functionality():
    """Test basic AgentController functionality"""
    try:
        from core.agent_controller import AgentController

        logger.info("Creating AgentController...")
        controller = AgentController()

        logger.info("Starting controller...")
        await controller.start()

        logger.info("✅ Controller started successfully")

        # Test basic methods
        logger.info("Testing basic methods...")

        # Try to get status
        logger.info("Getting controller status...")
        # status = await controller.get_status()
        # logger.info(f"Status: {status}")

        logger.info("Stopping controller...")
        await controller.stop()

        logger.info("✅ Test completed successfully")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
