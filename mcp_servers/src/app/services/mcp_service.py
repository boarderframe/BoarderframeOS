"""
MCP Server Management Service

High-level service that coordinates between the process manager and database operations.
Provides business logic for managing MCP servers with real process monitoring.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.services.process_manager import (
    process_manager, 
    MCPProcessInfo,
    ProcessMetrics as ProcessMetricsData
)
from app.schemas.mcp_server import (
    MCPServerStatus,
    MCPServerWithMetrics,
    ProcessMetrics,
    MCPServerControlResponse,
    MCPServerCreate,
    MCPServerUpdate
)

logger = logging.getLogger(__name__)


class MCPServerService:
    """
    High-level service for managing MCP servers.
    
    This service provides:
    - Server lifecycle management (start/stop/restart)
    - Real-time process monitoring
    - Configuration management
    - Health checking
    - Error handling and logging
    """
    
    def __init__(self):
        self._predefined_servers = self._load_predefined_servers()
    
    def _load_predefined_servers(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined server configurations."""
        # Check if the MCP server file exists
        import os
        filesystem_server_path = "/Users/cosburn/MCP Servers/mcp_servers/filesystem/main.py"
        if not os.path.exists(filesystem_server_path):
            # Create a simple placeholder if it doesn't exist
            os.makedirs("/Users/cosburn/MCP Servers/mcp_servers/filesystem", exist_ok=True)
            with open(filesystem_server_path, "w") as f:
                f.write('#!/usr/bin/env python\n')
                f.write('"""MCP Filesystem Server"""\n')
                f.write('import sys\n')
                f.write('print("MCP Filesystem Server placeholder", file=sys.stderr)\n')
                f.write('# This is a placeholder - replace with actual MCP server implementation\n')
                f.write('while True:\n')
                f.write('    try:\n')
                f.write('        line = input()\n')
                f.write('        print(\'{"jsonrpc":"2.0","id":1,"result":"ok"}\')\n')
                f.write('    except EOFError:\n')
                f.write('        break\n')
        
        return {
            "filesystem-python-001": {
                "id": "filesystem-python-001",
                "name": "File System Server",
                "description": "Python-based file system operations server with read, write, list, and search capabilities",
                "type": "filesystem",
                "protocol": "stdio",
                "command": ["python", "/Users/cosburn/MCP Servers/mcp_servers/filesystem/test_simple.py"],
                "working_directory": "/Users/cosburn/MCP Servers/mcp_servers/filesystem",
                "environment": {
                    "PYTHONPATH": "/Users/cosburn/MCP Servers/.venv/lib/python3.13/site-packages",
                    "LOG_LEVEL": "info"
                },
                "tools": [
                    "read_file",
                    "write_file", 
                    "list_directory",
                    "search_files",
                    "get_file_info",
                    "create_directory"
                ],
                "health_check_interval": 30,
                "max_restart_attempts": 3,
                "timeout_seconds": 30
            }
        }
    
    async def get_servers(self, skip: int = 0, limit: int = 100) -> List[MCPServerWithMetrics]:
        """
        Get all managed MCP servers with real-time metrics.
        
        Args:
            skip: Number of servers to skip
            limit: Maximum number of servers to return
            
        Returns:
            List of servers with current process metrics
        """
        servers = []
        
        # Get all managed servers from process manager
        managed_servers = process_manager.list_servers()
        
        # Also include predefined servers that aren't running
        all_server_ids = set(self._predefined_servers.keys())
        all_server_ids.update(info.server_id for info in managed_servers)
        
        for server_id in list(all_server_ids)[skip:skip + limit]:
            server_data = await self._get_server_with_metrics(server_id)
            if server_data:
                servers.append(server_data)
        
        return servers
    
    async def get_server(self, server_id: str) -> Optional[MCPServerWithMetrics]:
        """
        Get a specific MCP server with real-time metrics.
        
        Args:
            server_id: Unique identifier for the server
            
        Returns:
            Server information with metrics, or None if not found
        """
        return await self._get_server_with_metrics(server_id)
    
    async def start_server(
        self,
        server_id: str,
        timeout: float = 30.0
    ) -> MCPServerControlResponse:
        """
        Start an MCP server.
        
        Args:
            server_id: Unique identifier for the server
            timeout: Timeout in seconds for the operation
            
        Returns:
            Control response with operation result
        """
        logger.info(f"Starting server {server_id}")
        
        try:
            # Check if server configuration exists
            if server_id not in self._predefined_servers:
                return MCPServerControlResponse(
                    server_id=server_id,
                    action="start",
                    success=False,
                    message=f"Server configuration not found: {server_id}",
                    timestamp=datetime.now()
                )
            
            config = self._predefined_servers[server_id]
            
            # Check if server is already running
            if process_manager.is_server_running(server_id):
                return MCPServerControlResponse(
                    server_id=server_id,
                    action="start",
                    success=False,
                    message=f"Server {server_id} is already running",
                    timestamp=datetime.now()
                )
            
            # Start the server
            process_info = await process_manager.start_server(
                server_id=server_id,
                name=config["name"],
                command=config["command"],
                working_directory=config.get("working_directory"),
                environment=config.get("environment"),
                timeout=timeout
            )
            
            return MCPServerControlResponse(
                server_id=server_id,
                action="start",
                success=True,
                message=f"Server {server_id} started successfully",
                process_id=process_info.pid,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            error_msg = f"Failed to start server {server_id}: {str(e)}"
            logger.error(error_msg)
            return MCPServerControlResponse(
                server_id=server_id,
                action="start",
                success=False,
                message=error_msg,
                timestamp=datetime.now()
            )
    
    async def stop_server(
        self,
        server_id: str,
        timeout: float = 10.0,
        force: bool = False
    ) -> MCPServerControlResponse:
        """
        Stop an MCP server.
        
        Args:
            server_id: Unique identifier for the server
            timeout: Timeout in seconds for graceful shutdown
            force: Whether to force kill if graceful shutdown fails
            
        Returns:
            Control response with operation result
        """
        logger.info(f"Stopping server {server_id}")
        
        try:
            # Check if server is running
            if not process_manager.is_server_running(server_id):
                return MCPServerControlResponse(
                    server_id=server_id,
                    action="stop",
                    success=False,
                    message=f"Server {server_id} is not running",
                    timestamp=datetime.now()
                )
            
            # Stop the server
            success = await process_manager.stop_server(
                server_id=server_id,
                timeout=timeout,
                force=force
            )
            
            message = f"Server {server_id} stopped successfully" if success else f"Failed to stop server {server_id}"
            
            return MCPServerControlResponse(
                server_id=server_id,
                action="stop",
                success=success,
                message=message,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            error_msg = f"Failed to stop server {server_id}: {str(e)}"
            logger.error(error_msg)
            return MCPServerControlResponse(
                server_id=server_id,
                action="stop",
                success=False,
                message=error_msg,
                timestamp=datetime.now()
            )
    
    async def restart_server(
        self,
        server_id: str,
        timeout: float = 30.0
    ) -> MCPServerControlResponse:
        """
        Restart an MCP server.
        
        Args:
            server_id: Unique identifier for the server
            timeout: Timeout in seconds for the operation
            
        Returns:
            Control response with operation result
        """
        logger.info(f"Restarting server {server_id}")
        
        try:
            # Check if server configuration exists
            if server_id not in self._predefined_servers:
                return MCPServerControlResponse(
                    server_id=server_id,
                    action="restart",
                    success=False,
                    message=f"Server configuration not found: {server_id}",
                    timestamp=datetime.now()
                )
            
            # Restart the server
            process_info = await process_manager.restart_server(
                server_id=server_id,
                timeout=timeout
            )
            
            return MCPServerControlResponse(
                server_id=server_id,
                action="restart",
                success=True,
                message=f"Server {server_id} restarted successfully",
                process_id=process_info.pid,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            error_msg = f"Failed to restart server {server_id}: {str(e)}"
            logger.error(error_msg)
            return MCPServerControlResponse(
                server_id=server_id,
                action="restart",
                success=False,
                message=error_msg,
                timestamp=datetime.now()
            )
    
    async def get_server_metrics(self, server_id: str) -> Optional[ProcessMetrics]:
        """
        Get real-time metrics for a server.
        
        Args:
            server_id: Unique identifier for the server
            
        Returns:
            Process metrics or None if server not running
        """
        metrics_data = process_manager.get_server_metrics(server_id)
        if metrics_data:
            return ProcessMetrics(
                pid=metrics_data.pid,
                cpu_percent=metrics_data.cpu_percent,
                memory_mb=metrics_data.memory_mb,
                uptime_seconds=metrics_data.uptime_seconds,
                status=metrics_data.status,
                num_threads=metrics_data.num_threads,
                num_fds=metrics_data.num_fds
            )
        return None
    
    async def health_check(self, server_id: str) -> Dict[str, Any]:
        """
        Perform health check on a server.
        
        Args:
            server_id: Unique identifier for the server
            
        Returns:
            Health check results
        """
        is_running = process_manager.is_server_running(server_id)
        process_info = process_manager.get_server_info(server_id)
        metrics = await self.get_server_metrics(server_id)
        
        health_status = {
            "server_id": server_id,
            "is_running": is_running,
            "status": process_info.status.value if process_info else "unknown",
            "last_check": datetime.now(),
            "metrics": metrics.dict() if metrics else None,
            "error_message": process_info.last_error if process_info else None
        }
        
        return health_status
    
    async def shutdown(self):
        """Shutdown the service and stop all managed servers."""
        logger.info("Shutting down MCP server service")
        await process_manager.shutdown()
    
    # Private methods
    
    async def _get_server_with_metrics(self, server_id: str) -> Optional[MCPServerWithMetrics]:
        """Get server information with current metrics."""
        # Get process info from manager
        process_info = process_manager.get_server_info(server_id)
        
        # Get predefined config
        config = self._predefined_servers.get(server_id)
        
        if not process_info and not config:
            return None
        
        # Build server response
        server_data = {
            "id": hash(server_id) % 1000000,  # Generate a stable numeric ID from string
            "name": process_info.name if process_info else config.get("name", server_id),
            "server_id": server_id,  # Add the actual string server ID
            "description": config.get("description", "") if config else "",
            "host": "localhost",
            "port": 8000,  # This would be configured per server
            "protocol": config.get("protocol", "stdio") if config else "stdio",
            "command": " ".join(process_info.command) if process_info else " ".join(config.get("command", [])),
            "args": process_info.command[1:] if process_info and len(process_info.command) > 1 else config.get("command", [])[1:] if config and len(config.get("command", [])) > 1 else [],
            "working_directory": process_info.working_directory if process_info else config.get("working_directory"),
            "env": process_info.environment if process_info else config.get("environment"),
            "config": config or {},
            "status": process_info.status if process_info else MCPServerStatus.INACTIVE,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_health_check": datetime.now(),
            "error_message": process_info.last_error if process_info else None,
            "process_id": process_info.pid if process_info else None,
            "restart_count": process_info.restart_count if process_info else 0,
            "start_time": process_info.start_time if process_info else None,
            "last_error": process_info.last_error if process_info else None
        }
        
        # Add metrics if available
        if process_info and process_info.metrics:
            metrics_data = process_info.metrics
            server_data["metrics"] = ProcessMetrics(
                pid=metrics_data.pid,
                cpu_percent=metrics_data.cpu_percent,
                memory_mb=metrics_data.memory_mb,
                uptime_seconds=metrics_data.uptime_seconds,
                status=metrics_data.status,
                num_threads=metrics_data.num_threads,
                num_fds=metrics_data.num_fds
            )
        
        return MCPServerWithMetrics(**server_data)


# Global service instance
mcp_service = MCPServerService()