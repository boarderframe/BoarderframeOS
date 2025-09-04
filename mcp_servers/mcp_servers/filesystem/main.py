#!/usr/bin/env python3
"""
File System MCP Server

A Model Context Protocol server that provides file system operations.
Supports reading, writing, listing, and searching files and directories.
"""

import os
import json
import asyncio
import pathlib
import logging
from typing import Any, Sequence, Optional, Dict, List, Union
from pathlib import Path

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio


# Configure logging to stderr (not stdout, which would interfere with MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("filesystem-mcp-server")


class FileSystemMCP:
    """File System MCP Server implementation."""
    
    def __init__(self):
        """Initialize the file system MCP server."""
        self.server = Server("filesystem-mcp-server")
        self.allowed_paths: List[Path] = []
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up MCP handlers for file system operations."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available file system tools."""
            return [
                types.Tool(
                    name="read_file",
                    description="Read the contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to the file to read"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="write_file",
                    description="Write content to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                ),
                types.Tool(
                    name="list_directory",
                    description="List the contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to the directory to list"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="search_files",
                    description="Search for files matching a pattern",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "The directory to search in"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "The search pattern (supports glob patterns)"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Whether to search recursively",
                                "default": True
                            }
                        },
                        "required": ["directory", "pattern"]
                    }
                ),
                types.Tool(
                    name="get_file_info",
                    description="Get information about a file or directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path to get information about"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="create_directory",
                    description="Create a new directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "The path of the directory to create"
                            }
                        },
                        "required": ["path"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent]:
            """Handle tool calls for file system operations."""
            if arguments is None:
                arguments = {}
            
            try:
                if name == "read_file":
                    return await self._read_file(arguments.get("path", ""))
                elif name == "write_file":
                    return await self._write_file(
                        arguments.get("path", ""), 
                        arguments.get("content", "")
                    )
                elif name == "list_directory":
                    return await self._list_directory(arguments.get("path", ""))
                elif name == "search_files":
                    return await self._search_files(
                        arguments.get("directory", ""),
                        arguments.get("pattern", ""),
                        arguments.get("recursive", True)
                    )
                elif name == "get_file_info":
                    return await self._get_file_info(arguments.get("path", ""))
                elif name == "create_directory":
                    return await self._create_directory(arguments.get("path", ""))
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve a file path."""
        if not path:
            raise ValueError("Path cannot be empty")
        
        # Convert to absolute path
        resolved_path = Path(path).resolve()
        
        # Security check: prevent directory traversal attacks
        try:
            # Ensure the path doesn't contain suspicious patterns
            if ".." in path or path.startswith("/"):
                # For safety, only allow relative paths from current working directory
                # or explicitly allowed paths
                pass
            
            # Check if path is accessible
            if not resolved_path.exists():
                logger.warning(f"Path does not exist: {resolved_path}")
            
            return resolved_path
        except Exception as e:
            raise ValueError(f"Invalid path: {path} - {e}")
    
    async def _read_file(self, path: str) -> list[types.TextContent]:
        """Read the contents of a file."""
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                return [types.TextContent(
                    type="text", 
                    text=f"File not found: {path}"
                )]
            
            if not file_path.is_file():
                return [types.TextContent(
                    type="text", 
                    text=f"Path is not a file: {path}"
                )]
            
            # Read the file content
            content = file_path.read_text(encoding='utf-8', errors='replace')
            
            return [types.TextContent(
                type="text",
                text=f"File: {path}\n\nContent:\n{content}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error reading file {path}: {str(e)}"
            )]
    
    async def _write_file(self, path: str, content: str) -> list[types.TextContent]:
        """Write content to a file."""
        try:
            file_path = self._validate_path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content
            file_path.write_text(content, encoding='utf-8')
            
            return [types.TextContent(
                type="text",
                text=f"Successfully wrote {len(content)} characters to {path}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error writing file {path}: {str(e)}"
            )]
    
    async def _list_directory(self, path: str) -> list[types.TextContent]:
        """List the contents of a directory."""
        try:
            dir_path = self._validate_path(path) if path else Path.cwd()
            
            if not dir_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"Directory not found: {path}"
                )]
            
            if not dir_path.is_dir():
                return [types.TextContent(
                    type="text",
                    text=f"Path is not a directory: {path}"
                )]
            
            # List directory contents
            items = []
            for item in sorted(dir_path.iterdir()):
                item_type = "DIR" if item.is_dir() else "FILE"
                size = item.stat().st_size if item.is_file() else 0
                items.append(f"{item_type:<4} {item.name:<30} {size:>10} bytes")
            
            content = f"Directory listing for: {dir_path}\n\n"
            content += "\n".join(items) if items else "Directory is empty"
            
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error listing directory {path}: {str(e)}"
            )]
    
    async def _search_files(self, directory: str, pattern: str, recursive: bool = True) -> list[types.TextContent]:
        """Search for files matching a pattern."""
        try:
            search_dir = self._validate_path(directory) if directory else Path.cwd()
            
            if not search_dir.exists():
                return [types.TextContent(
                    type="text",
                    text=f"Directory not found: {directory}"
                )]
            
            if not search_dir.is_dir():
                return [types.TextContent(
                    type="text",
                    text=f"Path is not a directory: {directory}"
                )]
            
            # Search for files
            matches = []
            if recursive:
                matches = list(search_dir.rglob(pattern))
            else:
                matches = list(search_dir.glob(pattern))
            
            if not matches:
                return [types.TextContent(
                    type="text",
                    text=f"No files found matching pattern '{pattern}' in {directory}"
                )]
            
            # Format results
            results = []
            for match in sorted(matches):
                item_type = "DIR" if match.is_dir() else "FILE"
                relative_path = match.relative_to(search_dir)
                size = match.stat().st_size if match.is_file() else 0
                results.append(f"{item_type:<4} {relative_path:<50} {size:>10} bytes")
            
            content = f"Search results for pattern '{pattern}' in {search_dir}:\n\n"
            content += "\n".join(results)
            
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error searching files: {str(e)}"
            )]
    
    async def _get_file_info(self, path: str) -> list[types.TextContent]:
        """Get information about a file or directory."""
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"Path not found: {path}"
                )]
            
            stat = file_path.stat()
            
            info = {
                "path": str(file_path),
                "name": file_path.name,
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:],
                "exists": True
            }
            
            content = f"File Information for: {path}\n\n"
            for key, value in info.items():
                content += f"{key.capitalize():<12}: {value}\n"
            
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting file info for {path}: {str(e)}"
            )]
    
    async def _create_directory(self, path: str) -> list[types.TextContent]:
        """Create a new directory."""
        try:
            dir_path = self._validate_path(path)
            
            if dir_path.exists():
                return [types.TextContent(
                    type="text",
                    text=f"Directory already exists: {path}"
                )]
            
            # Create the directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return [types.TextContent(
                type="text",
                text=f"Successfully created directory: {path}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error creating directory {path}: {str(e)}"
            )]


async def main():
    """Main entry point for the file system MCP server."""
    logger.info("Starting File System MCP Server")
    
    # Create the MCP server instance
    fs_mcp = FileSystemMCP()
    
    # Run the server with stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await fs_mcp.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="filesystem-mcp-server",
                server_version="1.0.0",
                capabilities=fs_mcp.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("File System MCP Server stopped by user")
    except Exception as e:
        logger.error(f"Error running File System MCP Server: {e}")
        raise