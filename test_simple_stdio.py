#!/usr/bin/env python3
"""
Simple test STDIO server for debugging
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Handle MCP import conflicts
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, '')]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith('mcp')]
for module_name in local_mcp_modules:
    del sys.modules[module_name]

import mcp.server.stdio
from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Configure logging to file
log_file = Path(__file__).parent / "test_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger("test_stdio")

# Create the server
server = Server("test")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Test message"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "test_tool":
        message = arguments.get("message", "Hello from test tool!")
        return [types.TextContent(type="text", text=f"Test response: {message}")]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point."""
    logger.info("Starting simple test STDIO server")

    # Get transport options
    options = InitializationOptions()

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("STDIO server initialized")
        await server.run(
            read_stream,
            write_stream,
            options
        )

if __name__ == "__main__":
    asyncio.run(main())
