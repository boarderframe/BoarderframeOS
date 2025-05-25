"""
MCP Filesystem Server - BoarderframeOS Agent Storage
Handles agent code, configs, memories, and evolution history
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Security, WebSocket, WebSocketDisconnect
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
import yaml
import shutil
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import hashlib
import asyncio
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "../../logs/mcp_filesystem.log")),
        logging.StreamHandler()
    ]
)

# Make numpy and sklearn optional
try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    
# Make transformers optional
HAS_TRANSFORMERS = False
try:
    import torch
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    # Transformers not available, will use fallback methods
    pass

class MCPFilesystemServer:
    """BoarderframeOS Filesystem MCP Server"""
    
    def __init__(self):
        self.app = FastAPI(title="BoarderframeOS Filesystem MCP")
        self.setup_middleware()
        self.setup_routes()
        self.setup_storage()
        
        # Vector storage for embeddings
        self.vector_cache = {}
        self.vector_store = VectorStore()
        
        # WebSocket clients
        self.connected_clients = {"notifications": []}
    
    def setup_middleware(self):
        """Configure middleware for the FastAPI app"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Restrict in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_storage(self):
        """Initialize storage directories"""
        # Base paths for agent storage
        self.agents_path = Path("./boarderframeos/agents")
        self.memories_path = Path("./data/memories")
        self.evolution_path = Path("./data/evolution")
        self.configs_path = Path("./data/configs")
        self.templates_path = Path("./templates")
        
        # Ensure directories exist
        for path in [self.agents_path, self.memories_path, self.evolution_path, 
                    self.configs_path, self.templates_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def setup_routes(self):
        """Set up API routes for the server"""
        # Health check
        self.app.get("/health")(self.health_check)
        
        # File operations
        self.app.post("/rpc")(self.handle_rpc)
        self.app.get("/files/{path:path}")(self.get_file)
        self.app.post("/files/{path:path}")(self.create_file)
        self.app.put("/files/{path:path}")(self.update_file)
        self.app.delete("/files/{path:path}")(self.delete_file)
        
        # WebSocket for real-time notifications
        self.app.websocket("/ws/{topic}")(self.websocket_endpoint)
    
    async def start(self, port=8001):
        """Start the server"""
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()
    
    async def stop(self):
        """Stop the server"""
        # Additional cleanup if needed
        pass
    
    async def health_check(self):
        """Health check endpoint with system statistics"""
        # Collect basic system information
        storage_stats = {
            "agents": len(list(self.agents_path.glob("*"))),
            "memories": len(list(self.memories_path.glob("*/**/*.json"))),
            "evolution": len(list(self.evolution_path.glob("*.json"))),
            "configs": len(list(self.configs_path.glob("*"))),
            "templates": len(list(self.templates_path.glob("*")))
        }
        
        # Check available disk space
        import shutil
        total, used, free = shutil.disk_usage(str(self.agents_path))
        disk_stats = {
            "total_gb": total // (1024**3),
            "used_gb": used // (1024**3),
            "free_gb": free // (1024**3),
            "percent_used": round((used / total) * 100, 2)
        }
        
        # Check if vector search is available
        vector_search = {
            "available": HAS_TRANSFORMERS,
            "model_loaded": self.vector_store.model is not None,
            "cache_size": len(self.vector_cache)
        }
        
        return {
            "status": "healthy",
            "service": "BoarderframeOS MCP Filesystem",
            "version": "1.1.0",
            "uptime": "N/A",  # Would need to track server start time
            "storage": storage_stats,
            "disk": disk_stats,
            "features": {
                "vector_search": vector_search,
                "websocket_clients": {k: len(v) for k, v in self.connected_clients.items()},
                "authentication": "enabled"
            }
        }

    # Define handler for JSON-RPC requests
    async def handle_rpc(self, request_body: dict):
        """Handle JSON-RPC requests"""
        method = request_body.get("method")
        params = request_body.get("params", {})
        request_id = request_body.get("id", 0)
        
        # Dispatch to appropriate method based on the RPC method name
        if method == "fs.read":
            result = await self.read_file(params.get("path"))
        elif method == "fs.write":
            result = await self.write_file(params.get("path"), params.get("content"))
        elif method == "fs.delete":
            result = await self.delete_file(params.get("path"))
        elif method == "fs.list":
            result = await self.list_directory(params.get("path", "."))
        elif method == "fs.mkdir":
            result = await self.create_directory(params.get("path"))
        elif method == "fs.search":
            result = await self.search_files(
                params.get("pattern"), 
                params.get("path", "."), 
                params.get("recursive", True)
            )
        else:
            return {"error": {"code": -32601, "message": f"Method {method} not found"}, "id": request_id}
        
        # Return the result
        return {"result": result, "id": request_id}
    
    # Implement file operations
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file's contents"""
        try:
            file_path = self.validate_path(path)
            if not file_path.exists():
                return {"error": "File not found", "path": path}
            
            content = file_path.read_text(encoding="utf-8")
            return {
                "path": path,
                "content": content,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            }
        except Exception as e:
            logging.error(f"Error reading file {path}: {e}")
            return {"error": str(e), "path": path}
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        try:
            file_path = self.validate_path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content
            file_path.write_text(content, encoding="utf-8")
            
            return {
                "success": True,
                "path": path,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            }
        except Exception as e:
            logging.error(f"Error writing to file {path}: {e}")
            return {"error": str(e), "path": path}
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            file_path = self.validate_path(path)
            if not file_path.exists():
                return {"error": "File not found", "path": path}
            
            # Check if it's a directory
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
                
            return {"success": True, "path": path}
        except Exception as e:
            logging.error(f"Error deleting file {path}: {e}")
            return {"error": str(e), "path": path}
    
    async def list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents"""
        dir_path = self.validate_path(path)
        if not dir_path.exists():
            return {"error": "Directory not found", "path": path}
        
        items = []
        for item in dir_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": item.stat().st_mtime
            })
        
        return {
            "path": str(dir_path),
            "items": items,
            "count": len(items)
        }
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        try:
            dir_path = self.validate_path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": path}
        except Exception as e:
            logging.error(f"Error creating directory {path}: {e}")
            return {"error": str(e), "path": path}
    
    async def search_files(self, pattern: str, path: str = ".", recursive: bool = True) -> Dict[str, Any]:
        """Search for files matching a pattern"""
        import fnmatch
        import os
        
        base_path = self.validate_path(path)
        if not base_path.exists() or not base_path.is_dir():
            return {"error": "Directory not found", "path": path}
        
        matches = []
        
        if recursive:
            # Walk directory tree recursively
            for root, dirnames, filenames in os.walk(str(base_path)):
                for filename in fnmatch.filter(filenames, pattern):
                    file_path = Path(root) / filename
                    # Get relative path to base
                    rel_path = file_path.relative_to(base_path)
                    matches.append({
                        "path": str(rel_path),
                        "full_path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
        else:
            # Just search current directory
            for item in base_path.glob(pattern):
                if item.is_file():
                    rel_path = item.relative_to(base_path)
                    matches.append({
                        "path": str(rel_path),
                        "full_path": str(item),
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime
                    })
                    
        return {
            "pattern": pattern,
            "base_path": str(base_path),
            "matches": matches,
            "count": len(matches)
        }
    
    # Helper for file path validation
    def validate_path(self, path_str: str) -> Path:
        """Validate and sanitize file paths to prevent directory traversal attacks"""
        try:
            # Use an absolute base path to validate against
            base_path = Path(".").resolve()
            
            # Convert to absolute path and resolve
            path = (base_path / path_str).resolve()
            
            # Ensure path is within the allowed base path
            if not str(path).startswith(str(base_path)):
                raise ValueError(f"Path {path_str} is outside the allowed directory")
                
            return path
        except Exception as e:
            logging.error(f"Path validation error: {e}")
            raise ValueError(f"Invalid path: {path_str} - {str(e)}")
    
    # WebSocket endpoint for notifications
    async def websocket_endpoint(self, websocket: WebSocket, topic: str):
        """WebSocket endpoint for real-time notifications"""
        await websocket.accept()
        
        # Initialize topic if not exists
        if topic not in self.connected_clients:
            self.connected_clients[topic] = []
        
        self.connected_clients[topic].append(websocket)
        
        try:
            # Send initial successful connection message
            await websocket.send_json({
                "type": "connection_established",
                "topic": topic,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep the connection open and handle messages
            while True:
                message = await websocket.receive_text()
                await websocket.send_json({
                    "type": "echo",
                    "data": message,
                    "timestamp": datetime.now().isoformat()
                })
        except WebSocketDisconnect:
            self.connected_clients[topic].remove(websocket)
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
            if websocket in self.connected_clients[topic]:
                self.connected_clients[topic].remove(websocket)
    
    async def get_file(self, path: str):
        """HTTP endpoint to get a file"""
        return await self.read_file(path)
    
    async def create_file(self, path: str, content: str = None):
        """HTTP endpoint to create a file"""
        return await self.write_file(path, content or "")
    
    async def update_file(self, path: str, content: str):
        """HTTP endpoint to update a file"""
        return await self.write_file(path, content)
    
    async def delete_file(self, path: str):
        """HTTP endpoint to delete a file"""
        return await self.delete_file(path)


class VectorStore:
    """Manages vector embeddings for semantic search"""
    model = None
    
    def __init__(self):
        # Initialize embedding model if available
        if HAS_TRANSFORMERS:
            try:
                self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            except Exception as e:
                logging.error(f"Error loading transformer model: {e}")
                self.model = None


# Standalone entry point if running directly
async def main():
    """Run the server directly"""
    server = MCPFilesystemServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
