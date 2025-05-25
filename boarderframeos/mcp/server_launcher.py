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

# Add parent directory to path so we can import from boarderframeos package
sys.path.insert(0, str(Path(__file__).parent.parent))

from boarderframeos.mcp.filesystem_server import MCPFilesystemServer
from boarderframeos.mcp.git_server import MCPGitServer
from boarderframeos.mcp.terminal_server import MCPTerminalServer

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
                       help="Servers to start (filesystem, git, terminal, or all)")
    parser.add_argument("--port-fs", type=int, default=8001,
                       help="Port for filesystem server (default: 8001)")
    parser.add_argument("--port-git", type=int, default=8002,
                       help="Port for git server (default: 8002)")
    parser.add_argument("--port-terminal", type=int, default=8003,
                       help="Port for terminal server (default: 8003)")
    
    args = parser.parse_args()
    
    # Determine which servers to start
    start_filesystem = "all" in args.servers or "filesystem" in args.servers
    start_git = "all" in args.servers or "git" in args.servers
    start_terminal = "all" in args.servers or "terminal" in args.servers
    
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
