#!/usr/bin/env python3
"""
BoarderframeOS MCP Server Launcher
Starts the MCP server infrastructure
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from analytics_server import MCPAnalyticsServer
from customer_server import MCPCustomerServer
from filesystem_server import MCPFilesystemServer
from git_server import MCPGitServer
from payment_server import MCPPaymentServer
from screenshot_server import MCPScreenshotServer
from terminal_server import MCPTerminalServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "../logs/mcp_launcher.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("mcp_launcher")

async def main():
    """Run the servers"""
    parser = argparse.ArgumentParser(description="BoarderframeOS MCP Server Launcher")
    parser.add_argument("--servers", "-s", nargs="+", default=["all"],
                       help="Servers to start (filesystem, git, terminal, payment, analytics, customer, screenshot, or all)")
    parser.add_argument("--port-fs", type=int, default=8001,
                       help="Port for filesystem server (default: 8001)")
    parser.add_argument("--port-git", type=int, default=8002,
                       help="Port for git server (default: 8002)")
    parser.add_argument("--port-terminal", type=int, default=8003,
                       help="Port for terminal server (default: 8003)")
    parser.add_argument("--port-payment", type=int, default=8006,
                       help="Port for payment server (default: 8006)")
    parser.add_argument("--port-analytics", type=int, default=8007,
                       help="Port for analytics server (default: 8007)")
    parser.add_argument("--port-customer", type=int, default=8008,
                       help="Port for customer server (default: 8008)")
    parser.add_argument("--port-screenshot", type=int, default=8011,
                       help="Port for screenshot server (default: 8011)")

    args = parser.parse_args()

    # Determine which servers to start
    start_filesystem = "all" in args.servers or "filesystem" in args.servers
    start_git = "all" in args.servers or "git" in args.servers
    start_terminal = "all" in args.servers or "terminal" in args.servers
    start_payment = "all" in args.servers or "payment" in args.servers
    start_analytics = "all" in args.servers or "analytics" in args.servers
    start_customer = "all" in args.servers or "customer" in args.servers
    start_screenshot = "all" in args.servers or "screenshot" in args.servers

    tasks = []

    # Start filesystem server
    if start_filesystem:
        logger.info(f"Starting filesystem server on port {args.port_fs}")
        fs_server = MCPFilesystemServer()
        tasks.append(asyncio.create_task(fs_server.start(args.port_fs)))

    # Start git server
    if start_git:
        logger.info(f"Starting git server on port {args.port_git}")
        git_server = MCPGitServer()
        tasks.append(asyncio.create_task(git_server.start(args.port_git)))

    # Start terminal server
    if start_terminal:
        logger.info(f"Starting terminal server on port {args.port_terminal}")
        terminal_server = MCPTerminalServer()
        tasks.append(asyncio.create_task(terminal_server.start(args.port_terminal)))

    # Start payment server
    if start_payment:
        logger.info(f"Starting payment server on port {args.port_payment}")
        payment_server = MCPPaymentServer()
        tasks.append(asyncio.create_task(payment_server.start(args.port_payment)))

    # Start analytics server
    if start_analytics:
        logger.info(f"Starting analytics server on port {args.port_analytics}")
        analytics_server = MCPAnalyticsServer()
        tasks.append(asyncio.create_task(analytics_server.start(args.port_analytics)))

    # Start customer server
    if start_customer:
        logger.info(f"Starting customer server on port {args.port_customer}")
        customer_server = MCPCustomerServer()
        tasks.append(asyncio.create_task(customer_server.start(args.port_customer)))

    # Start screenshot server
    if start_screenshot:
        logger.info(f"Starting screenshot server on port {args.port_screenshot}")
        screenshot_server = MCPScreenshotServer()
        tasks.append(asyncio.create_task(screenshot_server.start(args.port_screenshot)))

    if tasks:
        logger.info("All specified MCP servers started")
        await asyncio.gather(*tasks)
    else:
        logger.warning("No servers specified to start")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down MCP servers...")
        sys.exit(0)
