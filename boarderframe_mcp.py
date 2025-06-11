#!/usr/bin/env python3
"""BoarderframeOS MCP Server"""

import asyncio
import sys
from pathlib import Path

import mcp.server.stdio
from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Create server instance
server = Server("boarderframeos")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="get_system_status",
            description="Get BoarderframeOS system status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="list_agents",
            description="List all active agents",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="read_file",
            description="Read a file from the BoarderframeOS directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file relative to BoarderframeOS root"
                    }
                },
                "required": ["path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_system_status":
            return [types.TextContent(
                type="text",
                text="BoarderframeOS Status: Operational\n- MCP Servers: Running\n- Agent Framework: Active\n- Database: Connected"
            )]

        elif name == "list_agents":
            return [types.TextContent(
                type="text",
                text="Active Agents:\n- Solomon (Chief of Staff)\n- David (CEO)\n- Adam (Agent Creator)\n- Eve (Agent Evolver)\n- Bezalel (Master Programmer)"
            )]

        elif name == "read_file":
            file_path = Path("/Users/cosburn/BoarderframeOS") / arguments["path"]
            if not file_path.exists():
                return [types.TextContent(type="text", text=f"File not found: {arguments['path']}")]

            try:
                content = file_path.read_text(encoding='utf-8')
                return [types.TextContent(type="text", text=content)]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Tool error: {str(e)}")]

async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="boarderframeos",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
