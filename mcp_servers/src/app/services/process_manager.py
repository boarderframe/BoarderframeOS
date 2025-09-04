"""
MCP Server Process Management Service

This service handles real process monitoring and management for MCP servers using psutil.
Provides functionality to start, stop, restart, and monitor MCP server processes.
"""
import asyncio
import logging
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import psutil
from psutil import Process, NoSuchProcess, AccessDenied

from app.schemas.mcp_server import MCPServerStatus


logger = logging.getLogger(__name__)


@dataclass
class ProcessMetrics:
    """Process metrics data class."""
    pid: int
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float
    status: str
    num_threads: int
    num_fds: int  # File descriptors on Unix, handles on Windows


@dataclass
class MCPProcessInfo:
    """MCP Server process information."""
    server_id: str
    name: str
    pid: Optional[int]
    status: MCPServerStatus
    command: List[str]
    working_directory: Optional[str]
    environment: Optional[Dict[str, str]]
    metrics: Optional[ProcessMetrics]
    start_time: Optional[datetime]
    restart_count: int
    last_error: Optional[str]
    process: Optional[Any] = None  # Store the subprocess object


class ProcessManager:
    """
    Manages MCP server processes with real-time monitoring capabilities.
    
    Features:
    - Start/stop/restart MCP server processes
    - Real-time process monitoring using psutil
    - Process health checking and auto-restart
    - Resource usage tracking (CPU, memory, uptime)
    - Error handling and logging
    """
    
    def __init__(self):
        self._processes: Dict[str, MCPProcessInfo] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()
        self._monitor_interval = 5.0  # seconds
        
    async def start_server(
        self,
        server_id: str,
        name: str,
        command: List[str],
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ) -> MCPProcessInfo:
        """
        Start an MCP server process.
        
        Args:
            server_id: Unique identifier for the server
            name: Human-readable name for the server
            command: Command and arguments to execute
            working_directory: Working directory for the process
            environment: Environment variables for the process
            timeout: Timeout in seconds for process startup
            
        Returns:
            MCPProcessInfo: Process information after startup
            
        Raises:
            RuntimeError: If process fails to start
            FileNotFoundError: If command executable not found
            PermissionError: If insufficient permissions to start process
        """
        logger.info(f"Starting MCP server '{name}' (ID: {server_id})")
        
        # Check if server is already running
        if server_id in self._processes:
            existing = self._processes[server_id]
            if existing.status == MCPServerStatus.ACTIVE:
                raise RuntimeError(f"Server {server_id} is already running (PID: {existing.pid})")
        
        try:
            # Prepare environment
            env = os.environ.copy()
            if environment:
                env.update(environment)
            
            # Validate working directory
            if working_directory:
                work_dir = Path(working_directory)
                if not work_dir.exists():
                    raise FileNotFoundError(f"Working directory does not exist: {working_directory}")
                if not work_dir.is_dir():
                    raise NotADirectoryError(f"Working directory is not a directory: {working_directory}")
            
            # Start the process
            process_info = MCPProcessInfo(
                server_id=server_id,
                name=name,
                pid=None,
                status=MCPServerStatus.STARTING,
                command=command,
                working_directory=working_directory,
                environment=environment,
                metrics=None,
                start_time=None,
                restart_count=0,
                last_error=None,
                process=None
            )
            
            self._processes[server_id] = process_info
            
            # Start the subprocess
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=working_directory,
                env=env,
                stdin=asyncio.subprocess.PIPE,  # Add stdin for MCP servers
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True  # Create new process group
            )
            
            # Update process info
            process_info.pid = proc.pid
            process_info.process = proc
            process_info.start_time = datetime.now()
            process_info.status = MCPServerStatus.ACTIVE
            
            # Send initial message to MCP server to keep it alive
            try:
                initial_msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
                proc.stdin.write(initial_msg.encode())
                await proc.stdin.drain()
            except Exception as e:
                logger.warning(f"Failed to send initial message to server {server_id}: {e}")
            
            # Start monitoring task
            monitor_task = asyncio.create_task(
                self._monitor_process(server_id)
            )
            self._monitoring_tasks[server_id] = monitor_task
            
            logger.info(f"Successfully started MCP server '{name}' with PID {proc.pid}")
            
            # Wait a moment to ensure process is stable
            await asyncio.sleep(1.0)
            
            # Verify process is still running
            if not self._is_process_running(proc.pid):
                process_info.status = MCPServerStatus.ERROR
                process_info.last_error = "Process died immediately after startup"
                raise RuntimeError(f"Process for server {server_id} died immediately after startup")
            
            return process_info
            
        except FileNotFoundError as e:
            error_msg = f"Command not found: {e}"
            logger.error(f"Failed to start server {server_id}: {error_msg}")
            if server_id in self._processes:
                self._processes[server_id].status = MCPServerStatus.ERROR
                self._processes[server_id].last_error = error_msg
            raise
            
        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            logger.error(f"Failed to start server {server_id}: {error_msg}")
            if server_id in self._processes:
                self._processes[server_id].status = MCPServerStatus.ERROR
                self._processes[server_id].last_error = error_msg
            raise
            
        except Exception as e:
            error_msg = f"Failed to start process: {e}"
            logger.error(f"Failed to start server {server_id}: {error_msg}")
            if server_id in self._processes:
                self._processes[server_id].status = MCPServerStatus.ERROR
                self._processes[server_id].last_error = error_msg
            raise RuntimeError(error_msg) from e
    
    async def stop_server(
        self,
        server_id: str,
        timeout: float = 10.0,
        force: bool = False
    ) -> bool:
        """
        Stop an MCP server process.
        
        Args:
            server_id: Unique identifier for the server
            timeout: Timeout in seconds for graceful shutdown
            force: Whether to force kill if graceful shutdown fails
            
        Returns:
            bool: True if process was stopped successfully
            
        Raises:
            ValueError: If server not found
        """
        if server_id not in self._processes:
            raise ValueError(f"Server {server_id} not found")
        
        process_info = self._processes[server_id]
        logger.info(f"Stopping MCP server '{process_info.name}' (ID: {server_id})")
        
        # Cancel monitoring task
        if server_id in self._monitoring_tasks:
            self._monitoring_tasks[server_id].cancel()
            try:
                await self._monitoring_tasks[server_id]
            except asyncio.CancelledError:
                pass
            del self._monitoring_tasks[server_id]
        
        if process_info.pid is None:
            process_info.status = MCPServerStatus.INACTIVE
            return True
        
        try:
            process_info.status = MCPServerStatus.STOPPING
            
            # Try graceful shutdown first
            success = await self._terminate_process(process_info.pid, timeout, force)
            
            if success:
                process_info.status = MCPServerStatus.INACTIVE
                process_info.pid = None
                logger.info(f"Successfully stopped server {server_id}")
            else:
                process_info.status = MCPServerStatus.ERROR
                process_info.last_error = "Failed to stop process"
                logger.error(f"Failed to stop server {server_id}")
            
            return success
            
        except Exception as e:
            error_msg = f"Error stopping process: {e}"
            logger.error(f"Error stopping server {server_id}: {error_msg}")
            process_info.status = MCPServerStatus.ERROR
            process_info.last_error = error_msg
            return False
    
    async def restart_server(
        self,
        server_id: str,
        timeout: float = 30.0
    ) -> MCPProcessInfo:
        """
        Restart an MCP server process.
        
        Args:
            server_id: Unique identifier for the server
            timeout: Timeout in seconds for stop/start operations
            
        Returns:
            MCPProcessInfo: Process information after restart
            
        Raises:
            ValueError: If server not found
            RuntimeError: If restart fails
        """
        if server_id not in self._processes:
            raise ValueError(f"Server {server_id} not found")
        
        process_info = self._processes[server_id]
        logger.info(f"Restarting MCP server '{process_info.name}' (ID: {server_id})")
        
        # Stop the server first
        await self.stop_server(server_id, timeout / 2, force=True)
        
        # Wait a moment before restarting
        await asyncio.sleep(1.0)
        
        # Increment restart count
        process_info.restart_count += 1
        
        # Start the server again
        return await self.start_server(
            server_id=server_id,
            name=process_info.name,
            command=process_info.command,
            working_directory=process_info.working_directory,
            environment=process_info.environment,
            timeout=timeout / 2
        )
    
    def get_server_info(self, server_id: str) -> Optional[MCPProcessInfo]:
        """Get process information for a server."""
        return self._processes.get(server_id)
    
    def list_servers(self) -> List[MCPProcessInfo]:
        """List all managed servers."""
        return list(self._processes.values())
    
    def get_server_metrics(self, server_id: str) -> Optional[ProcessMetrics]:
        """Get real-time metrics for a server."""
        if server_id not in self._processes:
            return None
        
        process_info = self._processes[server_id]
        if process_info.pid is None:
            return None
        
        try:
            return self._get_process_metrics(process_info.pid)
        except (NoSuchProcess, AccessDenied):
            # Process doesn't exist anymore
            process_info.status = MCPServerStatus.INACTIVE
            process_info.pid = None
            return None
    
    def is_server_running(self, server_id: str) -> bool:
        """Check if a server is currently running."""
        process_info = self._processes.get(server_id)
        if not process_info or process_info.pid is None:
            return False
        return self._is_process_running(process_info.pid)
    
    async def shutdown(self):
        """Shutdown the process manager and stop all servers."""
        logger.info("Shutting down process manager")
        self._shutdown_event.set()
        
        # Stop all servers
        stop_tasks = []
        for server_id in list(self._processes.keys()):
            if self._processes[server_id].status == MCPServerStatus.ACTIVE:
                stop_tasks.append(self.stop_server(server_id, timeout=5.0, force=True))
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        self._monitoring_tasks.clear()
        self._processes.clear()
        
        logger.info("Process manager shutdown complete")
    
    # Private methods
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (NoSuchProcess, AccessDenied):
            return False
    
    def _get_process_metrics(self, pid: int) -> ProcessMetrics:
        """Get metrics for a process."""
        try:
            process = psutil.Process(pid)
            
            # Get process info
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            
            # Calculate uptime
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            
            # Get additional metrics
            status = process.status()
            num_threads = process.num_threads()
            
            # Get file descriptors (Unix) or handles (Windows)
            try:
                if hasattr(process, 'num_fds'):
                    num_fds = process.num_fds()
                else:
                    num_fds = process.num_handles()
            except (AccessDenied, AttributeError):
                num_fds = 0
            
            return ProcessMetrics(
                pid=pid,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                uptime_seconds=uptime_seconds,
                status=status,
                num_threads=num_threads,
                num_fds=num_fds
            )
            
        except (NoSuchProcess, AccessDenied) as e:
            raise NoSuchProcess(f"Process {pid} not found or access denied") from e
    
    async def _terminate_process(
        self,
        pid: int,
        timeout: float,
        force: bool
    ) -> bool:
        """Terminate a process gracefully, with optional force kill."""
        try:
            process = psutil.Process(pid)
            
            # Try graceful termination first
            try:
                process.terminate()
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=timeout)
                    return True
                except psutil.TimeoutExpired:
                    if force:
                        logger.warning(f"Process {pid} didn't terminate gracefully, force killing")
                        process.kill()
                        try:
                            process.wait(timeout=5.0)
                            return True
                        except psutil.TimeoutExpired:
                            logger.error(f"Failed to force kill process {pid}")
                            return False
                    else:
                        logger.warning(f"Process {pid} didn't terminate within timeout")
                        return False
                        
            except AccessDenied:
                logger.error(f"Access denied when trying to terminate process {pid}")
                return False
                
        except NoSuchProcess:
            # Process already dead
            return True
        except Exception as e:
            logger.error(f"Error terminating process {pid}: {e}")
            return False
    
    async def _monitor_process(self, server_id: str):
        """Monitor a process and update its metrics."""
        logger.debug(f"Starting process monitor for server {server_id}")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    process_info = self._processes.get(server_id)
                    if not process_info or process_info.pid is None:
                        break
                    
                    # Check if process is still running
                    if not self._is_process_running(process_info.pid):
                        logger.warning(f"Process for server {server_id} is no longer running")
                        process_info.status = MCPServerStatus.INACTIVE
                        process_info.pid = None
                        process_info.metrics = None
                        break
                    
                    # Update metrics
                    try:
                        metrics = self._get_process_metrics(process_info.pid)
                        process_info.metrics = metrics
                        
                        # Update status if needed
                        if process_info.status == MCPServerStatus.STARTING:
                            process_info.status = MCPServerStatus.ACTIVE
                            
                    except (NoSuchProcess, AccessDenied):
                        logger.warning(f"Lost access to process {process_info.pid} for server {server_id}")
                        process_info.status = MCPServerStatus.INACTIVE
                        process_info.pid = None
                        process_info.metrics = None
                        break
                    
                    # Wait for next monitoring cycle
                    await asyncio.sleep(self._monitor_interval)
                    
                except asyncio.CancelledError:
                    logger.debug(f"Process monitor for server {server_id} was cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in process monitor for server {server_id}: {e}")
                    await asyncio.sleep(self._monitor_interval)
                    
        except Exception as e:
            logger.error(f"Critical error in process monitor for server {server_id}: {e}")
        
        logger.debug(f"Process monitor for server {server_id} stopped")


# Global process manager instance
process_manager = ProcessManager()