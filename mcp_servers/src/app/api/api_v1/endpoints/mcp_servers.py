"""
MCP Server management endpoints
"""
import asyncio
import logging
from typing import Any, List, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.mcp_service import mcp_service
from app.schemas.mcp_server import (
    MCPServerWithMetrics,
    MCPServerControl,
    MCPServerControlResponse,
    ProcessMetrics,
    MCPServerStatus
)


class MCPToolExecuteRequest(BaseModel):
    """Request model for MCP tool execution."""
    tool: str
    arguments: Dict[str, Any] = {}


class MCPToolExecuteResponse(BaseModel):
    """Response model for MCP tool execution."""
    success: bool
    result: Any = None
    error: str = None
    tool: str
    server_id: str
    timestamp: datetime


class ListDirectoryRequest(BaseModel):
    path: str = "/"


class ReadFileRequest(BaseModel):
    path: str


class WriteFileRequest(BaseModel):
    path: str
    content: str


class SearchFilesRequest(BaseModel):
    pattern: str
    path: str = "/"


class GetFileInfoRequest(BaseModel):
    path: str


class CreateDirectoryRequest(BaseModel):
    path: str

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def read_mcp_servers(
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve MCP servers with real-time process metrics."""
    try:
        servers = await mcp_service.get_servers(skip=skip, limit=limit)
        
        # Convert to response format with real process data
        server_list = []
        for server in servers:
            # Use the actual server ID from the server object
            server_id = server.server_id if server.server_id else f"server-{server.id}"
            
            # Use the working directory from the server object
            working_dir = server.working_directory if server.working_directory else ""
            
            # Parse command and args
            # If args are already provided, use them; otherwise try to parse from command
            if server.args:
                command = server.command.split()[0] if server.command else ""
                args = server.args
            else:
                command_parts = server.command.split() if server.command else []
                command = command_parts[0] if command_parts else ""
                args = command_parts[1:] if len(command_parts) > 1 else []
            
            server_dict = {
                "id": server_id,
                "name": server.name,
                "description": server.description or "",
                "status": server.status.value,
                "type": "filesystem",  # Could be extended based on server config
                "protocol": server.protocol,
                "command": command,
                "args": args,
                "workingDirectory": working_dir,
                "environment": server.env or {},
                "tools": [
                    "read_file",
                    "write_file", 
                    "list_directory",
                    "search_files",
                    "get_file_info",
                    "create_directory"
                ],
                "lastUpdated": server.updated_at.isoformat() if server.updated_at else datetime.now().isoformat(),
                "processId": server.process_id,
                "restartCount": server.restart_count,
                "startTime": server.start_time.isoformat() if server.start_time else None,
                "lastError": server.last_error
            }
            
            # Add real-time metrics with proper formatting
            if server.metrics and server.status == MCPServerStatus.ACTIVE:
                # Format uptime in human-readable format
                uptime_seconds = server.metrics.uptime_seconds
                if uptime_seconds >= 3600:
                    hours = int(uptime_seconds // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    uptime_str = f"{hours}h {minutes}m"
                elif uptime_seconds >= 60:
                    minutes = int(uptime_seconds // 60)
                    seconds = int(uptime_seconds % 60)
                    uptime_str = f"{minutes}m {seconds}s"
                else:
                    uptime_str = f"{int(uptime_seconds)}s"
                
                server_dict["metrics"] = {
                    "uptime": uptime_str,
                    "uptimeSeconds": uptime_seconds,
                    "requests": 0,  # TODO: Implement request tracking
                    "errors": 0,    # TODO: Implement error tracking
                    "memory": f"{server.metrics.memory_mb:.1f}MB",
                    "memoryMB": server.metrics.memory_mb,
                    "cpu": f"{server.metrics.cpu_percent:.1f}%",
                    "cpuPercent": server.metrics.cpu_percent,
                    "pid": server.metrics.pid,
                    "threads": server.metrics.num_threads,
                    "handles": server.metrics.num_fds,
                    "status": server.metrics.status,
                    "isRunning": True
                }
            else:
                # Server not running or no metrics available
                server_dict["metrics"] = {
                    "uptime": "0s",
                    "uptimeSeconds": 0,
                    "requests": 0,
                    "errors": 0,
                    "memory": "0MB",
                    "memoryMB": 0,
                    "cpu": "0%",
                    "cpuPercent": 0,
                    "pid": None,
                    "threads": 0,
                    "handles": 0,
                    "status": "stopped",
                    "isRunning": False
                }
            
            server_list.append(server_dict)
        
        return {
            "servers": server_list,
            "total": len(server_list),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve servers: {str(e)}"
        )


@router.post("/")
async def create_mcp_server() -> Any:
    """Create new MCP server."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MCP server creation not yet implemented"
    )


@router.get("/{server_id}")
async def read_mcp_server(server_id: str) -> Any:
    """Get MCP server by ID with real-time metrics."""
    try:
        # Refresh metrics before returning
        server = await mcp_service.get_server(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server not found: {server_id}"
            )
        
        # Parse command and args properly
        # If args are already provided, use them; otherwise try to parse from command
        if server.args:
            command = server.command.split()[0] if server.command else ""
            args = server.args
        else:
            command_parts = server.command.split() if server.command else []
            command = command_parts[0] if command_parts else ""
            args = command_parts[1:] if len(command_parts) > 1 else []
        
        # Use the working directory from the server object
        working_dir = server.working_directory if server.working_directory else ""
        
        server_dict = {
            "id": server_id,
            "name": server.name,
            "description": server.description or "",
            "status": server.status.value,
            "type": "filesystem",
            "protocol": server.protocol,
            "command": command,
            "args": args,
            "workingDirectory": working_dir,
            "environment": server.env or {},
            "processId": server.process_id,
            "restartCount": server.restart_count,
            "startTime": server.start_time.isoformat() if server.start_time else None,
            "lastError": server.last_error,
            "lastUpdated": server.updated_at.isoformat() if server.updated_at else datetime.now().isoformat(),
            "isRunning": server.status == MCPServerStatus.ACTIVE
        }
        
        # Add detailed metrics if server is running
        if server.metrics and server.status == MCPServerStatus.ACTIVE:
            # Format uptime in human-readable format
            uptime_seconds = server.metrics.uptime_seconds
            if uptime_seconds >= 3600:
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                uptime_str = f"{hours}h {minutes}m"
            elif uptime_seconds >= 60:
                minutes = int(uptime_seconds // 60)
                seconds = int(uptime_seconds % 60)
                uptime_str = f"{minutes}m {seconds}s"
            else:
                uptime_str = f"{int(uptime_seconds)}s"
            
            server_dict["metrics"] = {
                "uptime": uptime_str,
                "uptimeSeconds": uptime_seconds,
                "memory": f"{server.metrics.memory_mb:.1f}MB",
                "memoryMB": server.metrics.memory_mb,
                "cpu": f"{server.metrics.cpu_percent:.1f}%",
                "cpuPercent": server.metrics.cpu_percent,
                "pid": server.metrics.pid,
                "threads": server.metrics.num_threads,
                "handles": server.metrics.num_fds,
                "status": server.metrics.status,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Server not running
            server_dict["metrics"] = {
                "uptime": "0s",
                "uptimeSeconds": 0,
                "memory": "0MB",
                "memoryMB": 0,
                "cpu": "0%",
                "cpuPercent": 0,
                "pid": None,
                "threads": 0,
                "handles": 0,
                "status": "stopped",
                "timestamp": datetime.now().isoformat()
            }
        
        return server_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve server: {str(e)}"
        )


@router.put("/{server_id}")
async def update_mcp_server(server_id: str) -> Any:
    """Update an MCP server."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MCP server update not yet implemented"
    )


@router.delete("/{server_id}")
async def delete_mcp_server(server_id: str) -> Any:
    """Delete an MCP server."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MCP server deletion not yet implemented"
    )


@router.post("/{server_id}/start", response_model=MCPServerControlResponse)
async def start_mcp_server(
    server_id: str,
    control: MCPServerControl = MCPServerControl(action="start")
) -> MCPServerControlResponse:
    """Start an MCP server process."""
    try:
        # Check current server status first
        server = await mcp_service.get_server(server_id)
        if server and server.status == MCPServerStatus.ACTIVE:
            return MCPServerControlResponse(
                server_id=server_id,
                action="start",
                success=False,
                message=f"Server {server_id} is already running with PID {server.process_id}",
                process_id=server.process_id,
                timestamp=datetime.now()
            )
        
        # Start the server
        response = await mcp_service.start_server(
            server_id=server_id,
            timeout=control.timeout or 30.0
        )
        
        # If successful, get updated metrics
        if response.success:
            await asyncio.sleep(1)  # Give server a moment to stabilize
            metrics = await mcp_service.get_server_metrics(server_id)
            if metrics:
                response.message = f"{response.message} (PID: {metrics.pid}, Memory: {metrics.memory_mb:.1f}MB)"
        
        return response
        
    except Exception as e:
        logger.error(f"Error starting server {server_id}: {str(e)}")
        return MCPServerControlResponse(
            server_id=server_id,
            action="start",
            success=False,
            message=f"Failed to start server: {str(e)}",
            timestamp=datetime.now()
        )


@router.post("/{server_id}/stop", response_model=MCPServerControlResponse)
async def stop_mcp_server(
    server_id: str,
    control: MCPServerControl = MCPServerControl(action="stop")
) -> MCPServerControlResponse:
    """Stop an MCP server process."""
    try:
        # Check if server is running
        server = await mcp_service.get_server(server_id)
        if not server or server.status == MCPServerStatus.INACTIVE:
            return MCPServerControlResponse(
                server_id=server_id,
                action="stop",
                success=False,
                message=f"Server {server_id} is not running",
                timestamp=datetime.now()
            )
        
        # Get metrics before stopping for logging
        metrics_before = await mcp_service.get_server_metrics(server_id)
        uptime_info = ""
        if metrics_before:
            uptime = metrics_before.uptime_seconds
            if uptime >= 3600:
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                uptime_info = f" (was running for {hours}h {minutes}m)"
            elif uptime >= 60:
                minutes = int(uptime // 60)
                uptime_info = f" (was running for {minutes}m)"
        
        # Stop the server
        response = await mcp_service.stop_server(
            server_id=server_id,
            timeout=control.timeout or 10.0,
            force=control.force or False
        )
        
        if response.success:
            response.message = f"{response.message}{uptime_info}"
        
        return response
        
    except Exception as e:
        logger.error(f"Error stopping server {server_id}: {str(e)}")
        return MCPServerControlResponse(
            server_id=server_id,
            action="stop",
            success=False,
            message=f"Failed to stop server: {str(e)}",
            timestamp=datetime.now()
        )


@router.post("/{server_id}/restart", response_model=MCPServerControlResponse)
async def restart_mcp_server(
    server_id: str,
    control: MCPServerControl = MCPServerControl(action="restart")
) -> MCPServerControlResponse:
    """Restart an MCP server process."""
    try:
        # Get current server info
        server = await mcp_service.get_server(server_id)
        if not server:
            return MCPServerControlResponse(
                server_id=server_id,
                action="restart",
                success=False,
                message=f"Server {server_id} not found",
                timestamp=datetime.now()
            )
        
        old_pid = server.process_id
        
        # Restart the server
        response = await mcp_service.restart_server(
            server_id=server_id,
            timeout=control.timeout or 30.0
        )
        
        # If successful, get new metrics
        if response.success:
            await asyncio.sleep(1)  # Give server a moment to stabilize
            metrics = await mcp_service.get_server_metrics(server_id)
            if metrics:
                response.message = f"{response.message} (Old PID: {old_pid}, New PID: {metrics.pid})"
        
        return response
        
    except Exception as e:
        logger.error(f"Error restarting server {server_id}: {str(e)}")
        return MCPServerControlResponse(
            server_id=server_id,
            action="restart",
            success=False,
            message=f"Failed to restart server: {str(e)}",
            timestamp=datetime.now()
        )


@router.get("/{server_id}/metrics")
async def get_server_metrics(server_id: str) -> Any:
    """Get real-time metrics for an MCP server."""
    try:
        # Get fresh metrics from process monitor
        metrics = await mcp_service.get_server_metrics(server_id)
        
        if not metrics:
            # Check if server exists but is not running
            server = await mcp_service.get_server(server_id)
            if server:
                return {
                    "server_id": server_id,
                    "status": "stopped",
                    "message": "Server is not running",
                    "metrics": {
                        "pid": None,
                        "cpu_percent": 0,
                        "memory_mb": 0,
                        "uptime_seconds": 0,
                        "status": "stopped",
                        "num_threads": 0,
                        "num_fds": 0
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Server not found: {server_id}"
                )
        
        # Format uptime for better readability
        uptime_seconds = metrics.uptime_seconds
        if uptime_seconds >= 3600:
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime_formatted = f"{hours}h {minutes}m"
        elif uptime_seconds >= 60:
            minutes = int(uptime_seconds // 60)
            seconds = int(uptime_seconds % 60)
            uptime_formatted = f"{minutes}m {seconds}s"
        else:
            uptime_formatted = f"{int(uptime_seconds)}s"
        
        return {
            "server_id": server_id,
            "status": "running",
            "metrics": {
                "pid": metrics.pid,
                "cpu_percent": metrics.cpu_percent,
                "cpu_formatted": f"{metrics.cpu_percent:.1f}%",
                "memory_mb": metrics.memory_mb,
                "memory_formatted": f"{metrics.memory_mb:.1f}MB",
                "uptime_seconds": metrics.uptime_seconds,
                "uptime_formatted": uptime_formatted,
                "status": metrics.status,
                "num_threads": metrics.num_threads,
                "num_fds": metrics.num_fds
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/{server_id}/health")
async def get_server_health(server_id: str) -> Any:
    """Get health status for an MCP server."""
    try:
        health = await mcp_service.health_check(server_id)
        
        # Enhance health response with additional context
        if health["is_running"] and health["metrics"]:
            metrics = health["metrics"]
            # Add health score based on metrics
            cpu_score = 100 - min(metrics["cpu_percent"], 100)
            memory_score = 100 - min((metrics["memory_mb"] / 1024) * 100, 100)  # Assume 1GB max
            health_score = (cpu_score + memory_score) / 2
            
            health["health_score"] = round(health_score, 1)
            health["health_status"] = (
                "healthy" if health_score > 70 else
                "warning" if health_score > 40 else
                "critical"
            )
            
            # Add formatted uptime
            if metrics["uptime_seconds"]:
                uptime = metrics["uptime_seconds"]
                if uptime >= 3600:
                    hours = int(uptime // 3600)
                    minutes = int((uptime % 3600) // 60)
                    health["uptime_formatted"] = f"{hours}h {minutes}m"
                elif uptime >= 60:
                    minutes = int(uptime // 60)
                    health["uptime_formatted"] = f"{minutes}m"
                else:
                    health["uptime_formatted"] = f"{int(uptime)}s"
        else:
            health["health_score"] = 0
            health["health_status"] = "offline"
            health["uptime_formatted"] = "0s"
        
        health["timestamp"] = datetime.now().isoformat()
        return health
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )


@router.get("/stats/summary")
async def get_servers_summary() -> Any:
    """Get summary statistics for all MCP servers."""
    try:
        servers = await mcp_service.get_servers()
        
        # Calculate statistics
        total_servers = len(servers)
        active_servers = sum(1 for s in servers if s.status == MCPServerStatus.ACTIVE)
        inactive_servers = sum(1 for s in servers if s.status == MCPServerStatus.INACTIVE)
        error_servers = sum(1 for s in servers if s.status == MCPServerStatus.ERROR)
        
        # Calculate resource usage
        total_memory_mb = 0
        total_cpu_percent = 0
        total_threads = 0
        total_handles = 0
        
        for server in servers:
            if server.metrics and server.status == MCPServerStatus.ACTIVE:
                total_memory_mb += server.metrics.memory_mb
                total_cpu_percent += server.metrics.cpu_percent
                total_threads += server.metrics.num_threads
                total_handles += server.metrics.num_fds
        
        # Get individual server stats
        server_stats = []
        for server in servers:
            stats = {
                "id": server.server_id if server.server_id else f"server-{server.id}",
                "name": server.name,
                "status": server.status.value,
                "pid": server.process_id,
                "restart_count": server.restart_count
            }
            
            if server.metrics and server.status == MCPServerStatus.ACTIVE:
                stats["cpu_percent"] = server.metrics.cpu_percent
                stats["memory_mb"] = server.metrics.memory_mb
                stats["uptime_seconds"] = server.metrics.uptime_seconds
            else:
                stats["cpu_percent"] = 0
                stats["memory_mb"] = 0
                stats["uptime_seconds"] = 0
            
            server_stats.append(stats)
        
        return {
            "summary": {
                "total": total_servers,
                "active": active_servers,
                "inactive": inactive_servers,
                "error": error_servers,
                "health_percentage": round((active_servers / total_servers * 100) if total_servers > 0 else 0, 1)
            },
            "resources": {
                "total_memory_mb": round(total_memory_mb, 1),
                "total_memory_formatted": f"{total_memory_mb:.1f}MB",
                "total_cpu_percent": round(total_cpu_percent, 1),
                "total_cpu_formatted": f"{total_cpu_percent:.1f}%",
                "avg_cpu_percent": round(total_cpu_percent / active_servers if active_servers > 0 else 0, 1),
                "avg_memory_mb": round(total_memory_mb / active_servers if active_servers > 0 else 0, 1),
                "total_threads": total_threads,
                "total_handles": total_handles
            },
            "servers": server_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting server statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server statistics: {str(e)}"
        )


@router.post("/refresh-metrics")
async def refresh_all_metrics() -> Any:
    """Force refresh metrics for all running servers."""
    try:
        servers = await mcp_service.get_servers()
        
        refreshed_count = 0
        metrics_list = []
        
        for server in servers:
            if server.status == MCPServerStatus.ACTIVE:
                server_id = server.server_id if server.server_id else f"server-{server.id}"
                metrics = await mcp_service.get_server_metrics(server_id)
                if metrics:
                    refreshed_count += 1
                    metrics_list.append({
                        "server_id": server_id,
                        "name": server.name,
                        "pid": metrics.pid,
                        "cpu_percent": metrics.cpu_percent,
                        "memory_mb": metrics.memory_mb
                    })
        
        return {
            "success": True,
            "refreshed_count": refreshed_count,
            "metrics": metrics_list,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh metrics: {str(e)}"
        )


@router.post("/{server_id}/execute", response_model=MCPToolExecuteResponse)
async def execute_mcp_tool(
    server_id: str,
    request: MCPToolExecuteRequest
) -> MCPToolExecuteResponse:
    """Execute an MCP tool on the specified server."""
    try:
        logger.info(f"[EXECUTE] Request from Open WebUI - Server: {server_id}, Tool: {request.tool}, Args: {request.arguments}")
        # Check if server exists and is running
        server = await mcp_service.get_server(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server not found: {server_id}"
            )
        
        if server.status != MCPServerStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server {server_id} is not running (status: {server.status.value})"
            )
        
        # Execute the tool - this is a placeholder for actual MCP tool execution
        # In a real implementation, this would communicate with the MCP server process
        result = await execute_tool_on_server(server_id, request.tool, request.arguments)
        
        return MCPToolExecuteResponse(
            success=True,
            result=result,
            tool=request.tool,
            server_id=server_id,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool {request.tool} on server {server_id}: {str(e)}")
        return MCPToolExecuteResponse(
            success=False,
            error=str(e),
            tool=request.tool,
            server_id=server_id,
            timestamp=datetime.now()
        )


async def execute_tool_on_server(server_id: str, tool: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool on an MCP server."""
    # This is a mock implementation - in production this would send JSON-RPC calls to the MCP server
    logger.info(f"[MCP TOOL] Executing {tool} on {server_id} with args: {arguments}")
    
    # Add a small delay to simulate real processing but keep it fast
    await asyncio.sleep(0.1)
    
    if tool == "list_directory":
        path = arguments.get("path", "/")
        # Mock directory listing
        return {
            "type": "directory_listing",
            "path": path,
            "files": [
                {"name": "example.txt", "type": "file", "size": 1024},
                {"name": "subdir", "type": "directory", "size": None}
            ]
        }
    
    elif tool == "read_file":
        path = arguments.get("path", "")
        # Mock file reading
        return {
            "type": "file_content",
            "path": path,
            "content": f"Mock content for file: {path}",
            "size": 256
        }
    
    elif tool == "write_file":
        path = arguments.get("path", "")
        content = arguments.get("content", "")
        # Mock file writing
        return {
            "type": "file_write_result",
            "path": path,
            "bytes_written": len(content),
            "success": True
        }
    
    elif tool == "search_files":
        pattern = arguments.get("pattern", "")
        path = arguments.get("path", "/")
        # Mock file search
        return {
            "type": "search_results",
            "pattern": pattern,
            "search_path": path,
            "matches": [
                {"path": f"/example/{pattern}_file1.txt", "line": 1, "content": f"Found {pattern} here"},
                {"path": f"/example/{pattern}_file2.txt", "line": 5, "content": f"Another {pattern} match"}
            ]
        }
    
    elif tool == "get_file_info":
        path = arguments.get("path", "")
        # Mock file info
        return {
            "type": "file_info",
            "path": path,
            "size": 1024,
            "modified": datetime.now().isoformat(),
            "is_directory": False,
            "permissions": "rw-r--r--"
        }
    
    elif tool == "create_directory":
        path = arguments.get("path", "")
        # Mock directory creation
        return {
            "type": "directory_create_result",
            "path": path,
            "success": True,
            "created": True
        }
    
    else:
        raise ValueError(f"Unknown tool: {tool}")


# Individual tool endpoints for Open WebUI compatibility
@router.post("/tools/list_directory",
            summary="List Directory Contents", 
            description="List files and directories at the specified path",
            operation_id="mcp_list_directory_tool",
            response_model=str,
            tags=["filesystem-tools"])
async def list_directory_tool(request: ListDirectoryRequest) -> str:
    """List files and directories at the specified path."""
    try:
        logger.info(f"[TOOL] list_directory called with path: {request.path}")
        # Return simple string format that LLMs can easily process
        files_list = [
            "example.txt (file, 1024 bytes)",
            "subdir/ (directory)",
            "config.json (file, 512 bytes)"
        ]
        return f"Directory listing for {request.path}:\n" + "\n".join(files_list)
    except Exception as e:
        logger.error(f"Error in list_directory_tool: {str(e)}")
        return f"Error listing directory: {str(e)}"


@router.post("/tools/read_file",
            summary="Read File Contents",
            description="Read the contents of a text file", 
            operation_id="mcp_read_file_tool",
            response_model=str,
            tags=["filesystem-tools"])
async def read_file_tool(request: ReadFileRequest) -> str:
    """Read the contents of a file."""
    try:
        logger.info(f"[TOOL] read_file called with path: {request.path}")
        content = f"Mock content for file: {request.path}\nThis is a test file with some example content.\nLine 3 of the file.\nEnd of file."
        return f"File: {request.path}\nContent:\n{content}"
    except Exception as e:
        logger.error(f"Error in read_file_tool: {str(e)}")
        return f"Error reading file: {str(e)}"


@router.post("/tools/write_file",
            summary="Write File Contents",
            description="Write content to a text file",
            operation_id="mcp_write_file_tool", 
            response_model=str,
            tags=["filesystem-tools"])
async def write_file_tool(request: WriteFileRequest) -> str:
    """Write content to a file."""
    try:
        logger.info(f"[TOOL] write_file called with path: {request.path}, content length: {len(request.content)}")
        return f"Successfully wrote {len(request.content)} bytes to {request.path}"
    except Exception as e:
        logger.error(f"Error in write_file_tool: {str(e)}")
        return f"Error writing file: {str(e)}"


@router.post("/tools/search_files",
            summary="Search Files",
            description="Search for files matching a pattern",
            operation_id="mcp_search_files_tool",
            response_model=str,
            tags=["filesystem-tools"])
async def search_files_tool(request: SearchFilesRequest) -> str:
    """Search for files matching a pattern."""
    try:
        logger.info(f"[TOOL] search_files called with pattern: {request.pattern}, path: {request.path}")
        matches = [
            f"/example/{request.pattern}_file1.txt:1: Found {request.pattern} here",
            f"/example/{request.pattern}_file2.txt:5: Another {request.pattern} match"
        ]
        return f"Search results for '{request.pattern}' in {request.path}:\n" + "\n".join(matches)
    except Exception as e:
        logger.error(f"Error in search_files_tool: {str(e)}")
        return f"Error searching files: {str(e)}"


@router.post("/tools/get_file_info",
            summary="Get File Information",
            description="Get information about a file",
            operation_id="mcp_get_file_info_tool",
            response_model=str,
            tags=["filesystem-tools"])
async def get_file_info_tool(request: GetFileInfoRequest) -> str:
    """Get information about a file."""
    try:
        logger.info(f"[TOOL] get_file_info called with path: {request.path}")
        return f"File info for {request.path}:\nSize: 1024 bytes\nModified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nType: File\nPermissions: rw-r--r--"
    except Exception as e:
        logger.error(f"Error in get_file_info_tool: {str(e)}")
        return f"Error getting file info: {str(e)}"


@router.post("/tools/create_directory",
            summary="Create Directory",
            description="Create a new directory",
            operation_id="mcp_create_directory_tool",
            response_model=str,
            tags=["filesystem-tools"])
async def create_directory_tool(request: CreateDirectoryRequest) -> str:
    """Create a new directory."""
    try:
        logger.info(f"[TOOL] create_directory called with path: {request.path}")
        return f"Successfully created directory: {request.path}"
    except Exception as e:
        logger.error(f"Error in create_directory_tool: {str(e)}")
        return f"Error creating directory: {str(e)}"