#!/usr/bin/env python3
"""
Standalone launcher for BoarderframeOS Screenshot MCP Server
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from screenshot_server import MCPScreenshotServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("screenshot_launcher")

async def main():
    """Start the screenshot server"""
    port = 8011

    # Get port from command line if specified
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid port: {sys.argv[1]}. Using default: {port}")

    logger.info(f"Starting Screenshot MCP Server on port {port}")

    # Create and start server
    server = MCPScreenshotServer()
    await server.start(port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Screenshot Server")
        sys.exit(0)
