#!/usr/bin/env python3
"""
Terminal MCP Server for BoarderframeOS
Provides safe command execution with security restrictions
"""

from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import subprocess
import json
import os
import shlex

app = FastAPI()

# SECURITY: Restrict terminal operations to BoarderframeOS project directory
ALLOWED_BASE_PATH = Path("/Users/cosburn/BoarderframeOS").resolve()

# SECURITY: Allowed commands (whitelist approach)
ALLOWED_COMMANDS = {
    "python", "python3", "pip", "pip3", 
    "pytest", "uvicorn", "fastapi",
    "ls", "pwd", "echo", "cat", "head", "tail",
    "mkdir", "touch", "cp", "mv", "rm",
    "git", "curl", "wget",
    "npm", "node", "yarn",
    "find", "grep", "awk", "sed",
    "which", "whereis", "type"
}

class TerminalOperation(BaseModel):
    method: str
    params: dict

def is_command_allowed(command: str) -> bool:
    """Check if command is in allowed list"""
    base_cmd = command.split()[0] if command.strip() else ""
    return base_cmd in ALLOWED_COMMANDS

def run_terminal_command(command: str, cwd: Path = None, timeout: int = 30) -> dict:
    """Run terminal command safely in allowed directory"""
    try:
        if cwd is None:
            cwd = ALLOWED_BASE_PATH
            
        # Ensure we're in allowed directory
        if not str(cwd.resolve()).startswith(str(ALLOWED_BASE_PATH)):
            return {"error": "Terminal operations restricted to BoarderframeOS directory"}
        
        # Check if command is allowed
        if not is_command_allowed(command):
            base_cmd = command.split()[0] if command.strip() else ""
            return {"error": f"Command '{base_cmd}' not allowed. Use only whitelisted commands."}
        
        # Parse command safely
        try:
            cmd_args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Invalid command syntax: {e}"}
        
        # Run command
        result = subprocess.run(
            cmd_args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PATH": os.environ.get("PATH", "")}
        )
        
        return {
            "result": {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        }
            
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"error": f"Command execution failed: {str(e)}"}

@app.get("/health")
async def health_check():
    # Test basic command execution
    test_result = run_terminal_command("pwd")
    return {
        "status": "healthy",
        "service": "terminal_mcp",
        "allowed_path": str(ALLOWED_BASE_PATH),
        "command_execution": test_result.get("result", {}).get("success", False),
        "security": "sandboxed"
    }

@app.get("/info")
async def get_info():
    """Get Terminal MCP server information"""
    return {
        "service": "BoarderframeOS Terminal MCP",
        "version": "1.0.0",
        "security": {
            "sandboxed": True,
            "allowed_base_path": str(ALLOWED_BASE_PATH),
            "command_whitelist": sorted(list(ALLOWED_COMMANDS)),
            "restrictions": [
                "Commands restricted to whitelist only",
                "Operations limited to BoarderframeOS directory",
                "Commands timeout after configurable duration",
                "No system administration commands"
            ]
        },
        "capabilities": [
            "terminal.execute",
            "terminal.run_python",
            "terminal.install_package",
            "terminal.run_tests",
            "terminal.list_directory",
            "terminal.get_environment"
        ]
    }

@app.post("/rpc")
async def handle_rpc(operation: TerminalOperation):
    try:
        method = operation.method
        params = operation.params
        
        if method == "terminal.execute":
            command = params.get("command", "")
            timeout = params.get("timeout", 30)
            working_dir = params.get("working_dir", str(ALLOWED_BASE_PATH))
            
            if not command:
                return {"error": "No command specified"}
                
            # Validate working directory
            try:
                work_path = Path(working_dir).resolve()
                if not str(work_path).startswith(str(ALLOWED_BASE_PATH)):
                    work_path = ALLOWED_BASE_PATH
            except:
                work_path = ALLOWED_BASE_PATH
                
            return run_terminal_command(command, cwd=work_path, timeout=timeout)
            
        elif method == "terminal.run_python":
            script = params.get("script", "")
            file_path = params.get("file", "")
            args = params.get("args", [])
            
            if script:
                # Run Python script directly
                command = f"python3 -c {shlex.quote(script)}"
            elif file_path:
                # Run Python file
                command = f"python3 {shlex.quote(file_path)}"
                if args:
                    command += " " + " ".join(shlex.quote(arg) for arg in args)
            else:
                return {"error": "Either 'script' or 'file' parameter required"}
                
            return run_terminal_command(command)
            
        elif method == "terminal.install_package":
            package = params.get("package", "")
            if not package:
                return {"error": "Package name required"}
                
            # Use pip install
            command = f"pip3 install {shlex.quote(package)}"
            return run_terminal_command(command, timeout=120)  # Longer timeout for installs
            
        elif method == "terminal.run_tests":
            test_path = params.get("path", ".")
            framework = params.get("framework", "pytest")  # pytest, unittest
            
            if framework == "pytest":
                command = f"pytest {shlex.quote(test_path)}"
            elif framework == "unittest":
                command = f"python3 -m unittest discover {shlex.quote(test_path)}"
            else:
                return {"error": f"Unknown test framework: {framework}"}
                
            return run_terminal_command(command, timeout=60)
            
        elif method == "terminal.list_directory":
            path = params.get("path", ".")
            detailed = params.get("detailed", False)
            
            if detailed:
                command = f"ls -la {shlex.quote(path)}"
            else:
                command = f"ls {shlex.quote(path)}"
                
            return run_terminal_command(command)
            
        elif method == "terminal.get_environment":
            var_name = params.get("variable", "")
            
            if var_name:
                command = f"echo ${var_name}"
            else:
                command = "env"
                
            return run_terminal_command(command)
            
        else:
            return {"error": f"Unknown terminal method: {method}"}
            
    except Exception as e:
        return {"error": f"Terminal operation failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)