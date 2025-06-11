#!/usr/bin/env python3
"""
MCP Filesystem Server - stdio transport wrapper
Wraps the HTTP-based filesystem server for use with Claude CLI
"""

import asyncio

# Handle MCP import conflicts by temporarily modifying sys.path
import importlib
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Save original sys.path
original_path = sys.path.copy()

# Remove current and parent directories to avoid local mcp module conflicts
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, '')]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith('mcp')]
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
log_file = Path(__file__).parent / "filesystem_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger("filesystem_stdio")

# Base path for file operations
BASE_PATH = Path(__file__).parent.parent

server = Server("filesystem")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available filesystem tools."""
    return [
        types.Tool(
            name="read_file",
            description="Read file contents",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="write_file",
            description="Write file contents",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        types.Tool(
            name="list_directory",
            description="List directory contents",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="create_directory",
            description="Create directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to create"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="delete_file",
            description="Delete file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to delete"
                    }
                },
                "required": ["path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "read_file":
            return await read_file(arguments["path"])
        elif name == "write_file":
            return await write_file(arguments["path"], arguments["content"])
        elif name == "list_directory":
            return await list_directory(arguments["path"])
        elif name == "create_directory":
            return await create_directory(arguments["path"])
        elif name == "delete_file":
            return await delete_file(arguments["path"])
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def read_file(path: str) -> List[types.TextContent]:
    """Read file contents."""
    try:
        file_path = BASE_PATH / path
        if not file_path.exists():
            return [types.TextContent(type="text", text=f"File not found: {path}")]

        content = file_path.read_text(encoding='utf-8')
        return [types.TextContent(type="text", text=content)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]

async def write_file(path: str, content: str) -> List[types.TextContent]:
    """Write file contents."""
    try:
        file_path = BASE_PATH / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return [types.TextContent(type="text", text=f"File written successfully: {path}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error writing file: {str(e)}")]

async def list_directory(path: str) -> List[types.TextContent]:
    """List directory contents."""
    try:
        dir_path = BASE_PATH / path
        if not dir_path.exists():
            return [types.TextContent(type="text", text=f"Directory not found: {path}")]

        if not dir_path.is_dir():
            return [types.TextContent(type="text", text=f"Not a directory: {path}")]

        items = []
        for item in sorted(dir_path.iterdir()):
            item_type = "directory" if item.is_dir() else "file"
            items.append(f"{item.name} ({item_type})")

        result = f"Contents of {path}:\n" + "\n".join(items)
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing directory: {str(e)}")]

async def create_directory(path: str) -> List[types.TextContent]:
    """Create directory."""
    try:
        dir_path = BASE_PATH / path
        dir_path.mkdir(parents=True, exist_ok=True)
        return [types.TextContent(type="text", text=f"Directory created: {path}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error creating directory: {str(e)}")]

async def delete_file(path: str) -> List[types.TextContent]:
    """Delete file or directory."""
    try:
        file_path = BASE_PATH / path
        if not file_path.exists():
            return [types.TextContent(type="text", text=f"Path not found: {path}")]

        if file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
            return [types.TextContent(type="text", text=f"Directory deleted: {path}")]
        else:
            file_path.unlink()
            return [types.TextContent(type="text", text=f"File deleted: {path}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error deleting: {str(e)}")]

async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="filesystem",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
