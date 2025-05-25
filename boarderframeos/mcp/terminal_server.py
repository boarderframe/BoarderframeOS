"""
Terminal MCP Server for BoarderframeOS
Provides safe command execution with security restrictions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import subprocess
import json
import os
import shlex
import logging
import uvicorn
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "../../logs/terminal_mcp.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("terminal_server")

class CommandOperation(BaseModel):
    method: str
    params: dict

class MCPTerminalServer:
    """BoarderframeOS Terminal MCP Server"""
    
    def __init__(self):
        self.app = FastAPI(title="BoarderframeOS Terminal MCP")
        
        # SECURITY: Restrict terminal operations to BoarderframeOS project directory
        self.allowed_base_path = Path(".").resolve()
        
        # SECURITY: Allowed commands (whitelist approach)
        self.allowed_commands = [
            "ls", "cat", "grep", "find", "pwd", "mkdir", "touch", "rm",
            "cp", "mv", "echo", "python", "pip", "git", "curl", "wget",
            "tar", "zip", "unzip", "head", "tail", "wc", "sort",
            "diff", "chmod", "chown", "ps", "kill", "df", "du"
        ]
        
        # For storing long-running processes
        self.running_processes = {}
        
        # Set up middleware and routes
        self.setup_middleware()
        self.setup_routes()
    
    def setup_middleware(self):
        """Configure middleware for the FastAPI app"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Restrict in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def setup_routes(self):
        """Set up API routes"""
        self.app.post("/rpc")(self.handle_rpc)
        self.app.get("/health")(self.health_check)
        self.app.get("/processes")(self.list_processes)
        
    async def start(self, port=8003):
        """Start the server"""
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()
    
    async def stop(self):
        """Stop the server"""
        # Terminate any running processes
        for process_id, process_info in self.running_processes.items():
            try:
                process_info["process"].terminate()
            except Exception as e:
                logger.error(f"Error terminating process {process_id}: {e}")
    
    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "BoarderframeOS Terminal MCP",
            "version": "1.0.0",
            "active_processes": len(self.running_processes)
        }
    
    async def list_processes(self):
        """List running processes"""
        processes = []
        for process_id, process_info in self.running_processes.items():
            # Check if process is still running
            if process_info["process"].poll() is not None:
                status = "finished"
                exit_code = process_info["process"].returncode
            else:
                status = "running"
                exit_code = None
                
            processes.append({
                "id": process_id,
                "command": process_info["command"],
                "start_time": process_info["start_time"],
                "working_dir": process_info["working_dir"],
                "status": status,
                "exit_code": exit_code
            })
        
        return {"processes": processes, "count": len(processes)}
    
    async def handle_rpc(self, op: CommandOperation):
        """Handle RPC operation"""
        try:
            method = op.method
            params = op.params
            
            # Dispatch to appropriate method
            if method == "terminal.exec":
                return await self.execute_command(
                    params.get("command"),
                    params.get("working_dir", "."),
                    params.get("timeout")
                )
            elif method == "terminal.exec_background":
                return await self.execute_background(
                    params.get("command"),
                    params.get("working_dir", ".")
                )
            elif method == "terminal.get_output":
                return await self.get_process_output(params.get("process_id"))
            elif method == "terminal.kill":
                return await self.kill_process(params.get("process_id"))
            else:
                return {"error": f"Method {method} not supported"}
                
        except Exception as e:
            logger.error(f"Error handling Terminal operation: {e}")
            return {"error": str(e)}
    
    def validate_path(self, working_dir: str) -> Path:
        """Validate and sanitize working directory path"""
        try:
            # Convert to absolute path and resolve
            path = (self.allowed_base_path / working_dir).resolve()
            
            # Ensure path is within the allowed base path
            if not str(path).startswith(str(self.allowed_base_path)):
                raise ValueError(f"Path {working_dir} is outside the allowed directory")
            
            # Check if path exists
            if not path.exists():
                raise ValueError(f"Path {working_dir} does not exist")
                
            return path
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            raise ValueError(f"Invalid working directory: {working_dir}")
    
    def validate_command(self, command: str) -> list:
        """Validate and sanitize command"""
        if not command:
            raise ValueError("Command cannot be empty")
            
        # Split command into parts
        parts = shlex.split(command)
        if not parts:
            raise ValueError("Invalid command")
            
        # Check if command is allowed
        base_command = parts[0]
        if base_command not in self.allowed_commands and not base_command.startswith('./') and not base_command.startswith('../'):
            raise ValueError(f"Command '{base_command}' is not allowed for security reasons")
            
        return parts
    
    async def execute_command(self, command: str, working_dir: str = ".", timeout: int = 30) -> dict:
        """Execute a command and return the output"""
        try:
            # Validate
            path = self.validate_path(working_dir)
            command_parts = self.validate_command(command)
            
            # Execute
            process = subprocess.Popen(
                command_parts,
                cwd=path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                
                return {
                    "success": process.returncode == 0,
                    "command": command,
                    "exit_code": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr
                }
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    "success": False,
                    "command": command,
                    "error": f"Command timed out after {timeout} seconds"
                }
                
        except ValueError as e:
            return {"success": False, "command": command, "error": str(e)}
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {"success": False, "command": command, "error": str(e)}
    
    async def execute_background(self, command: str, working_dir: str = ".") -> dict:
        """Execute a command in the background"""
        try:
            # Validate
            path = self.validate_path(working_dir)
            command_parts = self.validate_command(command)
            
            # Create a unique ID for this process
            process_id = str(uuid.uuid4())
            
            # Start process
            process = subprocess.Popen(
                command_parts,
                cwd=path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Store process info
            self.running_processes[process_id] = {
                "process": process,
                "command": command,
                "working_dir": str(path),
                "start_time": datetime.now().isoformat(),
                "stdout_buffer": [],
                "stderr_buffer": []
            }
            
            # Start background task to collect output
            asyncio.create_task(self._collect_process_output(process_id))
            
            return {
                "success": True,
                "process_id": process_id,
                "command": command
            }
                
        except ValueError as e:
            return {"success": False, "command": command, "error": str(e)}
        except Exception as e:
            logger.error(f"Error executing background command: {e}")
            return {"success": False, "command": command, "error": str(e)}
    
    async def _collect_process_output(self, process_id: str):
        """Collect output from a background process"""
        if process_id not in self.running_processes:
            return
            
        process_info = self.running_processes[process_id]
        process = process_info["process"]
        
        # Collect stdout
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            process_info["stdout_buffer"].append(line)
        
        # Collect stderr
        for line in iter(process.stderr.readline, ""):
            if not line:
                break
            process_info["stderr_buffer"].append(line)
        
        # Wait for process to complete
        process.wait()
    
    async def get_process_output(self, process_id: str) -> dict:
        """Get output from a background process"""
        if process_id not in self.running_processes:
            return {"success": False, "error": f"Process {process_id} not found"}
            
        process_info = self.running_processes[process_id]
        process = process_info["process"]
        
        # Check if process is still running
        is_running = process.poll() is None
        
        # Get current output
        stdout = "".join(process_info["stdout_buffer"])
        stderr = "".join(process_info["stderr_buffer"])
        
        # Reset buffers
        process_info["stdout_buffer"] = []
        process_info["stderr_buffer"] = []
        
        return {
            "success": True,
            "process_id": process_id,
            "command": process_info["command"],
            "is_running": is_running,
            "exit_code": process.returncode if not is_running else None,
            "stdout": stdout,
            "stderr": stderr
        }
    
    async def kill_process(self, process_id: str) -> dict:
        """Kill a background process"""
        if process_id not in self.running_processes:
            return {"success": False, "error": f"Process {process_id} not found"}
            
        process_info = self.running_processes[process_id]
        process = process_info["process"]
        
        try:
            # Check if already finished
            if process.poll() is not None:
                return {
                    "success": True,
                    "process_id": process_id,
                    "status": "already_finished",
                    "exit_code": process.returncode
                }
                
            # Kill the process
            process.terminate()
            try:
                # Wait a bit for graceful termination
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if it didn't terminate
                process.kill()
                process.wait()
                
            return {
                "success": True,
                "process_id": process_id,
                "status": "killed",
                "exit_code": process.returncode
            }
            
        except Exception as e:
            logger.error(f"Error killing process {process_id}: {e}")
            return {"success": False, "process_id": process_id, "error": str(e)}


# Standalone entry point
async def main():
    """Run the server directly"""
    server = MCPTerminalServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
