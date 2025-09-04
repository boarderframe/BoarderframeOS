#!/usr/bin/env python3
"""
Demo MCP Client for Real Playwright Server
Demonstrates how to interact with the Playwright MCP server using the MCP protocol.
"""

import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightMCPClient:
    """MCP client for interacting with the Playwright server."""
    
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.session = None
        self.stdio_transport = None
        self.stdio_context = None
        
    async def connect(self):
        """Connect to the Playwright MCP server."""
        logger.info("Connecting to Playwright MCP server...")
        
        # Start the server process
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_path],
            env=None
        )
        
        # Create stdio client with async context manager
        self.stdio_context = stdio_client(server_params)
        self.stdio_transport = await self.stdio_context.__aenter__()
        
        # Initialize session
        self.session = ClientSession(self.stdio_transport[0], self.stdio_transport[1])
        await self.session.initialize()
        
        logger.info("Connected to Playwright MCP server")
        
    async def disconnect(self):
        """Disconnect from the server."""
        if self.session:
            await self.session.close()
        if self.stdio_context:
            await self.stdio_context.__aexit__(None, None, None)
        logger.info("Disconnected from Playwright MCP server")
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools from the server."""
        response = await self.session.list_tools()
        return response.model_dump()
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the server."""
        response = await self.session.call_tool(name, arguments)
        return response.model_dump()


async def demo_playwright_automation():
    """Demonstrate Playwright automation through MCP."""
    
    client = PlaywrightMCPClient("/Users/cosburn/MCP Servers/real_playwright_server.py")
    
    try:
        await client.connect()
        
        # List available tools
        logger.info("=== Available Tools ===")
        tools = await client.list_tools()
        for tool in tools.get("tools", []):
            print(f"- {tool.get('name')}: {tool.get('description')}")
        
        print("\n" + "="*60)
        logger.info("=== Demo: Web Automation ===")
        
        # Demo 1: Navigate to a website
        logger.info("1. Navigating to test website...")
        result = await client.call_tool("navigate", {
            "url": "https://httpbin.org/html"
        })
        print(f"Navigation result: {json.dumps(result, indent=2)}")
        
        # Demo 2: Extract page title
        logger.info("2. Extracting page title...")
        result = await client.call_tool("extract_text", {
            "selector": "h1"
        })
        print(f"Title extraction: {json.dumps(result, indent=2)}")
        
        # Demo 3: Take a screenshot
        logger.info("3. Taking screenshot...")
        result = await client.call_tool("screenshot", {
            "full_page": False,
            "format": "png"
        })
        if result.get("content", [{}])[0].get("text"):
            response_data = json.loads(result["content"][0]["text"])
            if response_data.get("success"):
                screenshot_size = response_data.get("size_bytes", 0)
                print(f"Screenshot captured: {screenshot_size} bytes")
            else:
                print(f"Screenshot failed: {response_data.get('error')}")
        
        # Demo 4: Navigate to form page and interact
        logger.info("4. Navigating to form page...")
        result = await client.call_tool("navigate", {
            "url": "https://httpbin.org/forms/post"
        })
        
        # Demo 5: Fill form fields
        logger.info("5. Filling form fields...")
        result = await client.call_tool("fill", {
            "selector": "input[name='custname']",
            "text": "MCP Demo User"
        })
        print(f"Fill name field: {json.dumps(result, indent=2)}")
        
        result = await client.call_tool("fill", {
            "selector": "input[name='custemail']",
            "text": "demo@mcp-server.com"
        })
        print(f"Fill email field: {json.dumps(result, indent=2)}")
        
        # Demo 6: Get page info
        logger.info("6. Getting final page info...")
        result = await client.call_tool("get_page_info", {})
        print(f"Page info: {json.dumps(result, indent=2)}")
        
        logger.info("=== Demo completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await client.disconnect()


async def demo_multiple_contexts():
    """Demonstrate multiple browser contexts."""
    
    client = PlaywrightMCPClient("/Users/cosburn/MCP Servers/real_playwright_server.py")
    
    try:
        await client.connect()
        
        logger.info("=== Demo: Multiple Browser Contexts ===")
        
        # Context 1: Navigate to page 1
        logger.info("Context 1: Navigating to example.com...")
        result = await client.call_tool("navigate", {
            "url": "https://httpbin.org/html",
            "context_id": "context1"
        })
        
        # Context 2: Navigate to page 2
        logger.info("Context 2: Navigating to forms page...")
        result = await client.call_tool("navigate", {
            "url": "https://httpbin.org/forms/post",
            "context_id": "context2"
        })
        
        # Get info from both contexts
        logger.info("Getting info from context 1...")
        result = await client.call_tool("get_page_info", {
            "context_id": "context1"
        })
        print(f"Context 1 info: {json.dumps(result, indent=2)}")
        
        logger.info("Getting info from context 2...")
        result = await client.call_tool("get_page_info", {
            "context_id": "context2"
        })
        print(f"Context 2 info: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Multiple contexts demo failed: {e}")
        
    finally:
        await client.disconnect()


if __name__ == "__main__":
    print("Playwright MCP Client Demo")
    print("==========================")
    print("This demonstrates how to use the Playwright MCP server through the MCP protocol.")
    print()
    
    # Run the main demo
    asyncio.run(demo_playwright_automation())
    
    print("\n" + "="*60)
    
    # Run the multiple contexts demo
    asyncio.run(demo_multiple_contexts())