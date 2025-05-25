"""
MCP Server Manager - Consolidated server launcher
Starts and manages all MCP servers from one control point
"""

import argparse
import sys
import importlib
import asyncio
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "../../logs/mcp_servers.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("mcp_manager")

# Server definitions with their ports and descriptions
SERVER_CONFIGS = {
    "filesystem": {
        "module": "boarderframeos.mcp.filesystem_server",
        "class": "MCPFilesystemServer",
        "port": 8001,
        "description": "File operations and agent storage"
    },
    "git": {
        "module": "boarderframeos.mcp.git_server",
        "class": "MCPGitServer",
        "port": 8002,
        "description": "Git version control operations"
    },
    "terminal": {
        "module": "boarderframeos.mcp.terminal_server",
        "class": "MCPTerminalServer",
        "port": 8003,
        "description": "Terminal command execution"
    }
}

class MCPManager:
    """Manages MCP server instances"""
    
    def __init__(self):
        self.servers = {}
        self.running = False
    
    async def start_server(self, server_name):
        """Start a specific MCP server"""
        if server_name not in SERVER_CONFIGS:
            logger.error(f"Unknown server: {server_name}")
            return False
            
        config = SERVER_CONFIGS[server_name]
        logger.info(f"Starting {server_name} server on port {config['port']}...")
        
        try:
            # Import the server module
            module = importlib.import_module(config['module'])
            server_class = getattr(module, config['class'])
            
            # Initialize and start the server
            server = server_class()
            await server.start(config['port'])
            
            self.servers[server_name] = server
            logger.info(f"✅ {server_name} server started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start {server_name} server: {e}")
            return False
    
    async def start_all(self):
        """Start all MCP servers"""
        self.running = True
        
        # Start each server
        for server_name in SERVER_CONFIGS:
            await self.start_server(server_name)
            
        logger.info("All MCP servers started")
        
    async def stop_all(self):
        """Stop all running MCP servers"""
        for server_name, server in self.servers.items():
            try:
                await server.stop()
                logger.info(f"Stopped {server_name} server")
            except Exception as e:
                logger.error(f"Error stopping {server_name} server: {e}")
                
        self.servers = {}
        self.running = False
        logger.info("All MCP servers stopped")

async def main():
    """Main entry point for the MCP manager"""
    parser = argparse.ArgumentParser(description="BoarderframeOS MCP Server Manager")
    parser.add_argument("--servers", "-s", nargs="+", default=["all"],
                        help="Servers to start (filesystem, git, terminal, or all)")
    args = parser.parse_args()
    
    manager = MCPManager()
    
    try:
        if "all" in args.servers:
            await manager.start_all()
        else:
            for server_name in args.servers:
                await manager.start_server(server_name)
        
        # Keep running until interrupted
        while manager.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down MCP servers...")
        await manager.stop_all()
        
if __name__ == "__main__":
    asyncio.run(main())
