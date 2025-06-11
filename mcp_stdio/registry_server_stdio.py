#!/usr/bin/env python3
"""
MCP Registry Server - stdio transport wrapper
Wraps the HTTP-based registry server for use with Claude CLI
"""

import asyncio

# Handle MCP import conflicts by temporarily modifying sys.path
import importlib
import importlib.util
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Save original sys.path
original_path = sys.path.copy()

# Remove current and parent directories to avoid local mcp module conflicts
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, "")]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith("mcp")]
for module_name in local_mcp_modules:
    del sys.modules[module_name]

try:
    # Import the real MCP package
    import mcp.server.stdio
    from mcp import types
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
finally:
    # Restore original sys.path
    sys.path = original_path

# Configure logging to file to avoid interfering with stdio
log_file = Path(__file__).parent / "registry_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)],
)
logger = logging.getLogger("registry_stdio")

server = Server("registry")

# Mock data for development (in production would connect to actual database)
agents_registry = {}
servers_registry = {}


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available registry tools."""
    return [
        types.Tool(
            name="register_agent",
            description="Register a new agent in the registry",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique agent identifier",
                    },
                    "name": {"type": "string", "description": "Agent name"},
                    "agent_type": {"type": "string", "description": "Type of agent"},
                    "department_id": {
                        "type": "string",
                        "description": "Department assignment (optional)",
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of agent capabilities",
                    },
                },
                "required": ["agent_id", "name", "agent_type"],
            },
        ),
        types.Tool(
            name="discover_agents",
            description="Discover agents by type or department",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "description": "Filter by agent type (optional)",
                    },
                    "department_id": {
                        "type": "string",
                        "description": "Filter by department (optional)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status (optional)",
                    },
                },
            },
        ),
        types.Tool(
            name="register_server",
            description="Register a new server in the registry",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Server name"},
                    "server_type": {"type": "string", "description": "Type of server"},
                    "endpoint_url": {
                        "type": "string",
                        "description": "Server endpoint URL",
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of server capabilities",
                    },
                },
                "required": ["name", "server_type", "endpoint_url"],
            },
        ),
        types.Tool(
            name="discover_servers",
            description="Discover available servers",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_type": {
                        "type": "string",
                        "description": "Filter by server type (optional)",
                    }
                },
            },
        ),
        types.Tool(
            name="get_registry_health",
            description="Get registry health status",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "register_agent":
            return await register_agent(arguments)
        elif name == "discover_agents":
            return await discover_agents(arguments)
        elif name == "register_server":
            return await register_server(arguments)
        elif name == "discover_servers":
            return await discover_servers(arguments)
        elif name == "get_registry_health":
            return await get_registry_health()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def register_agent(args: Dict[str, Any]) -> List[types.TextContent]:
    """Register a new agent."""
    try:
        agent_id = args["agent_id"]
        agent_data = {
            "agent_id": agent_id,
            "name": args["name"],
            "agent_type": args["agent_type"],
            "department_id": args.get("department_id"),
            "capabilities": args.get("capabilities", []),
            "status": "online",
            "registered_at": datetime.now().isoformat(),
            "health_status": "healthy",
        }

        agents_registry[agent_id] = agent_data

        result = {
            "success": True,
            "agent_id": agent_id,
            "status": "registered",
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error registering agent: {str(e)}")
        ]


async def discover_agents(args: Dict[str, Any]) -> List[types.TextContent]:
    """Discover agents based on filters."""
    try:
        agent_type = args.get("agent_type")
        department_id = args.get("department_id")
        status = args.get("status")

        filtered_agents = []

        for agent_data in agents_registry.values():
            if agent_type and agent_data.get("agent_type") != agent_type:
                continue
            if department_id and agent_data.get("department_id") != department_id:
                continue
            if status and agent_data.get("status") != status:
                continue

            filtered_agents.append(agent_data)

        result = {
            "success": True,
            "agents": filtered_agents,
            "count": len(filtered_agents),
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error discovering agents: {str(e)}")
        ]


async def register_server(args: Dict[str, Any]) -> List[types.TextContent]:
    """Register a new server."""
    try:
        name = args["name"]
        server_data = {
            "name": name,
            "server_type": args["server_type"],
            "endpoint_url": args["endpoint_url"],
            "capabilities": args.get("capabilities", []),
            "status": "online",
            "registered_at": datetime.now().isoformat(),
            "health_status": "healthy",
        }

        servers_registry[name] = server_data

        result = {
            "success": True,
            "server_name": name,
            "status": "registered",
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error registering server: {str(e)}")
        ]


async def discover_servers(args: Dict[str, Any]) -> List[types.TextContent]:
    """Discover available servers."""
    try:
        server_type = args.get("server_type")

        filtered_servers = []

        for server_data in servers_registry.values():
            if server_type and server_data.get("server_type") != server_type:
                continue

            filtered_servers.append(server_data)

        result = {
            "success": True,
            "servers": filtered_servers,
            "count": len(filtered_servers),
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error discovering servers: {str(e)}")
        ]


async def get_registry_health() -> List[types.TextContent]:
    """Get registry health status."""
    try:
        result = {
            "status": "healthy",
            "agents": {
                "total": len(agents_registry),
                "online": len(
                    [a for a in agents_registry.values() if a.get("status") == "online"]
                ),
            },
            "servers": {
                "total": len(servers_registry),
                "online": len(
                    [
                        s
                        for s in servers_registry.values()
                        if s.get("status") == "online"
                    ]
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(
                type="text", text=f"Error getting registry health: {str(e)}"
            )
        ]


async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="registry",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
