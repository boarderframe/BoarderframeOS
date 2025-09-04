"""
MCP-UI Core Framework
Production-ready MCP server foundation with UI Protocol support
"""

from .base_mcp_server import BaseMCPServer, MCPServerConfig
from .protocol.mcp_ui_engine import MCPUIEngine, MCPUIResource, MCPUIResponse

__version__ = "1.0.0"
__all__ = ["BaseMCPServer", "MCPServerConfig", "MCPUIEngine", "MCPUIResource", "MCPUIResponse"]