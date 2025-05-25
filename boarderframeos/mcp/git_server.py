"""
Git MCP Server for BoarderframeOS
Provides version control operations with security restrictions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import subprocess
import json
import os
import logging
import uvicorn
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "../../logs/git_mcp.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("git_server")

class GitOperation(BaseModel):
    method: str
    params: dict

class MCPGitServer:
    """BoarderframeOS Git MCP Server"""
    
    def __init__(self):
        self.app = FastAPI(title="BoarderframeOS Git MCP")
        
        # SECURITY: Restrict git operations to BoarderframeOS project directory only
        self.allowed_base_path = Path(".").resolve()
        
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
    
    async def start(self, port=8002):
        """Start the server"""
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()
    
    async def stop(self):
        """Stop the server"""
        # Additional cleanup if needed
        pass
    
    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "BoarderframeOS Git MCP",
            "version": "1.0.0"
        }
    
    async def handle_rpc(self, op: GitOperation):
        """Handle RPC operation"""
        try:
            method = op.method
            params = op.params
            
            # Dispatch to appropriate method
            if method == "git.status":
                return await self.git_status(params.get("repo_path"))
            elif method == "git.log":
                return await self.git_log(
                    params.get("repo_path"),
                    params.get("max_count", 10)
                )
            elif method == "git.add":
                return await self.git_add(
                    params.get("repo_path"),
                    params.get("files", [])
                )
            elif method == "git.commit":
                return await self.git_commit(
                    params.get("repo_path"),
                    params.get("message")
                )
            elif method == "git.diff":
                return await self.git_diff(
                    params.get("repo_path"),
                    params.get("target", "HEAD")
                )
            elif method == "git.diff_staged":
                return await self.git_diff_staged(params.get("repo_path"))
            elif method == "git.checkout":
                return await self.git_checkout(
                    params.get("repo_path"),
                    params.get("branch_name")
                )
            elif method == "git.create_branch":
                return await self.git_create_branch(
                    params.get("repo_path"),
                    params.get("branch_name"),
                    params.get("base_branch")
                )
            else:
                return {"error": f"Method {method} not supported"}
                
        except Exception as e:
            logger.error(f"Error handling Git operation: {e}")
            return {"error": str(e)}
    
    def validate_path(self, repo_path: str) -> Path:
        """Validate and sanitize repository path"""
        try:
            # Convert to absolute path and resolve
            path = (self.allowed_base_path / repo_path).resolve()
            
            # Ensure path is within the allowed base path
            if not str(path).startswith(str(self.allowed_base_path)):
                raise ValueError(f"Path {repo_path} is outside the allowed directory")
            
            # Check if path exists
            if not path.exists():
                raise ValueError(f"Path {repo_path} does not exist")
                
            # Check if it's a git repository
            git_dir = path / ".git"
            if not git_dir.exists():
                raise ValueError(f"Path {repo_path} is not a git repository")
                
            return path
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            raise ValueError(f"Invalid repository path: {repo_path}")
    
    async def run_git_command(self, repo_path: str, command: list) -> dict:
        """Run a git command and return the result"""
        try:
            path = self.validate_path(repo_path)
            
            # Run the command
            process = subprocess.Popen(
                command,
                cwd=path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.strip(),
                    "exit_code": process.returncode
                }
                
            return {
                "success": True,
                "output": stdout.strip(),
                "exit_code": process.returncode
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error running git command {command}: {e}")
            return {"success": False, "error": str(e)}
    
    async def git_status(self, repo_path: str) -> dict:
        """Get git status"""
        result = await self.run_git_command(repo_path, ["git", "status", "--porcelain"])
        
        if not result["success"]:
            return result
            
        # Parse porcelain output
        changes = []
        for line in result["output"].split("\n"):
            if not line.strip():
                continue
                
            status = line[:2]
            file_path = line[3:]
            
            change_type = self._parse_status_code(status)
            changes.append({"file": file_path, "status": change_type})
            
        return {
            "success": True,
            "changes": changes,
            "clean": len(changes) == 0,
            "count": len(changes)
        }
    
    def _parse_status_code(self, code: str) -> str:
        """Parse git status code"""
        if code == "??":
            return "untracked"
        elif code == "M ":
            return "modified_staged"
        elif code == " M":
            return "modified_unstaged"
        elif code == "A ":
            return "added"
        elif code == "D ":
            return "deleted_staged"
        elif code == " D":
            return "deleted_unstaged"
        elif code == "R ":
            return "renamed"
        elif code == "C ":
            return "copied"
        else:
            return "unknown"
    
    async def git_log(self, repo_path: str, max_count: int = 10) -> dict:
        """Get git commit history"""
        result = await self.run_git_command(
            repo_path,
            [
                "git", "log",
                f"--max-count={max_count}",
                "--pretty=format:%H|%an|%ae|%at|%s"
            ]
        )
        
        if not result["success"]:
            return result
            
        commits = []
        for line in result["output"].split("\n"):
            if not line.strip():
                continue
                
            parts = line.split("|")
            if len(parts) >= 5:
                commits.append({
                    "hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "timestamp": int(parts[3]),
                    "message": parts[4]
                })
                
        return {
            "success": True,
            "commits": commits,
            "count": len(commits)
        }
    
    async def git_add(self, repo_path: str, files: list) -> dict:
        """Add files to git staging area"""
        # Use . if no files specified
        if not files:
            files = ["."]
            
        command = ["git", "add"] + files
        return await self.run_git_command(repo_path, command)
    
    async def git_commit(self, repo_path: str, message: str) -> dict:
        """Commit staged changes"""
        if not message:
            return {"success": False, "error": "Commit message is required"}
            
        return await self.run_git_command(
            repo_path,
            ["git", "commit", "-m", message]
        )
    
    async def git_diff(self, repo_path: str, target: str = "HEAD") -> dict:
        """Get git diff"""
        result = await self.run_git_command(
            repo_path,
            ["git", "diff", target]
        )
        
        if not result["success"]:
            return result
            
        return {
            "success": True,
            "diff": result["output"]
        }
    
    async def git_diff_staged(self, repo_path: str) -> dict:
        """Get git diff for staged changes"""
        result = await self.run_git_command(
            repo_path,
            ["git", "diff", "--staged"]
        )
        
        if not result["success"]:
            return result
            
        return {
            "success": True,
            "diff": result["output"]
        }
    
    async def git_checkout(self, repo_path: str, branch_name: str) -> dict:
        """Checkout a branch"""
        if not branch_name:
            return {"success": False, "error": "Branch name is required"}
            
        return await self.run_git_command(
            repo_path,
            ["git", "checkout", branch_name]
        )
    
    async def git_create_branch(self, repo_path: str, branch_name: str, base_branch: str = None) -> dict:
        """Create a new branch"""
        if not branch_name:
            return {"success": False, "error": "Branch name is required"}
            
        command = ["git", "branch", branch_name]
        if base_branch:
            command.append(base_branch)
            
        result = await self.run_git_command(repo_path, command)
        
        if not result["success"]:
            return result
            
        # Checkout the new branch
        return await self.git_checkout(repo_path, branch_name)


# Standalone entry point
async def main():
    """Run the server directly"""
    server = MCPGitServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
