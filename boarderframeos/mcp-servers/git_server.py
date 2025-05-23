#!/usr/bin/env python3
"""
Git MCP Server for BoarderframeOS
Provides version control operations with security restrictions
"""

from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import subprocess
import json
import os

app = FastAPI()

# SECURITY: Restrict git operations to BoarderframeOS project directory only
ALLOWED_BASE_PATH = Path("/Users/cosburn/BoarderframeOS").resolve()

class GitOperation(BaseModel):
    method: str
    params: dict

def run_git_command(cmd_args: list, cwd: Path = None) -> dict:
    """Run git command safely in allowed directory"""
    try:
        if cwd is None:
            cwd = ALLOWED_BASE_PATH
            
        # Ensure we're in allowed directory
        if not str(cwd.resolve()).startswith(str(ALLOWED_BASE_PATH)):
            return {"error": "Git operations restricted to BoarderframeOS directory"}
        
        # Run git command
        result = subprocess.run(
            ["git"] + cmd_args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {"result": result.stdout.strip(), "success": True}
        else:
            return {"error": result.stderr.strip(), "success": False}
            
    except subprocess.TimeoutExpired:
        return {"error": "Git command timed out", "success": False}
    except Exception as e:
        return {"error": f"Git command failed: {str(e)}", "success": False}

@app.get("/health")
async def health_check():
    # Check if git is available and repo exists
    git_check = run_git_command(["status", "--porcelain"])
    return {
        "status": "healthy",
        "service": "git_mcp",
        "allowed_path": str(ALLOWED_BASE_PATH),
        "git_available": git_check.get("success", False),
        "security": "sandboxed"
    }

@app.get("/info")
async def get_info():
    """Get Git MCP server information"""
    return {
        "service": "BoarderframeOS Git MCP",
        "version": "1.0.0",
        "security": {
            "sandboxed": True,
            "allowed_base_path": str(ALLOWED_BASE_PATH),
            "restrictions": [
                "No git operations outside BoarderframeOS directory",
                "Commands timeout after 30 seconds",
                "No system-level git config changes"
            ]
        },
        "capabilities": [
            "git.status",
            "git.add", 
            "git.commit",
            "git.push",
            "git.pull",
            "git.branch",
            "git.diff",
            "git.log",
            "git.init",
            "git.remote"
        ]
    }

@app.post("/rpc")
async def handle_rpc(operation: GitOperation):
    try:
        method = operation.method
        params = operation.params
        
        if method == "git.status":
            return run_git_command(["status", "--porcelain", "-b"])
            
        elif method == "git.status_verbose":
            return run_git_command(["status"])
            
        elif method == "git.add":
            files = params.get("files", [])
            if not files:
                return {"error": "No files specified for git add"}
            return run_git_command(["add"] + files)
            
        elif method == "git.commit":
            message = params.get("message", "")
            if not message:
                return {"error": "Commit message required"}
            return run_git_command(["commit", "-m", message])
            
        elif method == "git.push":
            remote = params.get("remote", "origin")
            branch = params.get("branch", "main")
            return run_git_command(["push", remote, branch])
            
        elif method == "git.pull":
            remote = params.get("remote", "origin")
            branch = params.get("branch", "main")
            return run_git_command(["pull", remote, branch])
            
        elif method == "git.diff":
            files = params.get("files", [])
            cmd = ["diff"]
            if files:
                cmd.extend(files)
            return run_git_command(cmd)
            
        elif method == "git.log":
            count = params.get("count", 10)
            oneline = params.get("oneline", True)
            cmd = ["log", f"--max-count={count}"]
            if oneline:
                cmd.append("--oneline")
            return run_git_command(cmd)
            
        elif method == "git.branch":
            action = params.get("action", "list")  # list, create, delete, switch
            name = params.get("name", "")
            
            if action == "list":
                return run_git_command(["branch", "-a"])
            elif action == "create":
                if not name:
                    return {"error": "Branch name required"}
                return run_git_command(["branch", name])
            elif action == "switch":
                if not name:
                    return {"error": "Branch name required"}
                return run_git_command(["checkout", name])
            elif action == "delete":
                if not name:
                    return {"error": "Branch name required"}
                return run_git_command(["branch", "-d", name])
            else:
                return {"error": f"Unknown branch action: {action}"}
                
        elif method == "git.remote":
            action = params.get("action", "list")  # list, add, remove
            name = params.get("name", "")
            url = params.get("url", "")
            
            if action == "list":
                return run_git_command(["remote", "-v"])
            elif action == "add":
                if not name or not url:
                    return {"error": "Remote name and URL required"}
                return run_git_command(["remote", "add", name, url])
            elif action == "remove":
                if not name:
                    return {"error": "Remote name required"}
                return run_git_command(["remote", "remove", name])
            else:
                return {"error": f"Unknown remote action: {action}"}
                
        elif method == "git.init":
            return run_git_command(["init"])
            
        elif method == "git.clone":
            url = params.get("url", "")
            directory = params.get("directory", "")
            if not url:
                return {"error": "Repository URL required"}
            
            cmd = ["clone", url]
            if directory:
                cmd.append(directory)
                
            return run_git_command(cmd, cwd=ALLOWED_BASE_PATH.parent)
            
        else:
            return {"error": f"Unknown git method: {method}"}
            
    except Exception as e:
        return {"error": f"Git operation failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)