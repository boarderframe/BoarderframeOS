#!/usr/bin/env python3
"""
Start Solomon agent and chat server together
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'boarderframeos'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / 'logs' / 'solomon_combined.log')
    ]
)

logger = logging.getLogger("solomon_combined")

from boarderframeos.agents.solomon.solomon import Solomon
from boarderframeos.core.message_bus import message_bus

# Import required modules
from boarderframeos.ui.solomon_chat_server import SolomonChatServer


async def main():
    """Start Solomon agent and chat server together"""
    try:
        # Create message bus is already initialized as a singleton
        logger.info("Message bus is ready...")

        # Create and start Solomon agent
        logger.info("Starting Solomon agent...")
        solomon_agent = Solomon()
        agent_task = asyncio.create_task(solomon_agent.run())

        # Create and start chat server
        logger.info("Starting Solomon chat server...")
        chat_server = SolomonChatServer(port=8889)
        server_task = asyncio.create_task(chat_server.start_server())

        logger.info("Solomon agent and chat server are running!")
        logger.info("Chat server available at: ws://localhost:8889")

        # Keep running until interrupted
        await asyncio.gather(agent_task, server_task)

    except KeyboardInterrupt:
        logger.info("Shutting down Solomon systems...")
    except Exception as e:
        logger.error(f"Error starting Solomon systems: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
