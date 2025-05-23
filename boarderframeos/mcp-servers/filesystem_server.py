from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import os

app = FastAPI()

# SECURITY: Restrict access to BoarderframeOS project directory only
ALLOWED_BASE_PATH = Path("/Users/cosburn/BoarderframeOS").resolve()

class FileOperation(BaseModel):
    method: str
    params: dict

def validate_path(path_str: str) -> Path:
    """Validate and sanitize file paths to prevent directory traversal attacks"""
    try:
        # Convert to absolute path and resolve
        path = Path(path_str).resolve()
        
        # Check if path is within allowed directory
        if not str(path).startswith(str(ALLOWED_BASE_PATH)):
            raise ValueError(f"Access denied: Path outside allowed directory. Allowed: {ALLOWED_BASE_PATH}")
        
        return path
    except Exception as e:
        raise ValueError(f"Invalid path: {e}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "filesystem_mcp",
        "allowed_path": str(ALLOWED_BASE_PATH),
        "security": "sandboxed"
    }

@app.get("/info")
async def get_info():
    """Get information about MCP server capabilities and restrictions"""
    return {
        "service": "BoarderframeOS Filesystem MCP",
        "version": "1.1.0",
        "security": {
            "sandboxed": True,
            "allowed_base_path": str(ALLOWED_BASE_PATH),
            "restrictions": [
                "No access outside BoarderframeOS directory",
                "No system file access",
                "No home directory access beyond project"
            ]
        },
        "capabilities": [
            "filesystem.read_file",
            "filesystem.write_file", 
            "filesystem.list_directory",
            "filesystem.get_info",
            "filesystem.create_directory"
        ]
    }

@app.post("/rpc")
async def handle_rpc(operation: FileOperation):
    try:
        if operation.method == "filesystem.read_file":
            path = validate_path(operation.params['path'])
            if path.exists() and path.is_file():
                try:
                    content = path.read_text(encoding='utf-8')
                    return {"result": content}
                except UnicodeDecodeError:
                    return {"error": f"Cannot read binary file: {path.name}"}
            return {"error": f"File not found: {path}"}
        
        elif operation.method == "filesystem.write_file":
            path = validate_path(operation.params['path'])
            content = operation.params.get('content', '')
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            return {"result": f"File written successfully: {path.name}"}
        
        elif operation.method == "filesystem.list_directory":
            path = validate_path(operation.params.get('path', '.'))
            if not path.exists():
                return {"error": f"Directory not found: {path}"}
            if not path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
                
            files = []
            for item in sorted(path.iterdir()):
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(ALLOWED_BASE_PATH)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return {"result": {"files": files, "path": str(path.relative_to(ALLOWED_BASE_PATH))}}
        
        elif operation.method == "filesystem.create_directory":
            path = validate_path(operation.params['path'])
            path.mkdir(parents=True, exist_ok=True)
            return {"result": f"Directory created: {path.relative_to(ALLOWED_BASE_PATH)}"}
        
        elif operation.method == "filesystem.get_info":
            path = validate_path(operation.params.get('path', '.'))
            if not path.exists():
                return {"error": f"Path not found: {path}"}
                
            stat = path.stat()
            return {"result": {
                "path": str(path.relative_to(ALLOWED_BASE_PATH)),
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "exists": True
            }}
        
        else:
            return {"error": f"Unknown method: {operation.method}"}
            
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Server error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
