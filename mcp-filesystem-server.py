"""
MCP Filesystem Server - BoarderframeOS Agent Storage
Handles agent code, configs, memories, and evolution history
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Security, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from pathlib import Path
import json
import yaml
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple, Set
import hashlib
import asyncio
import logging

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

app = FastAPI(title="BoarderframeOS Filesystem MCP")

# Base paths for agent storage
AGENTS_PATH = Path("./agents")
MEMORIES_PATH = Path("./memories")
EVOLUTION_PATH = Path("./evolution")
CONFIGS_PATH = Path("./configs")
TEMPLATES_PATH = Path("./templates")

# Ensure directories exist
for path in [AGENTS_PATH, MEMORIES_PATH, EVOLUTION_PATH, CONFIGS_PATH, TEMPLATES_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Vector storage for embeddings
VECTOR_CACHE = {}

# Security settings
API_KEYS = {
    "default": "default-key-boarderframe-dev-1234567890",  # Default key for development
    "agent": "agent-key-secure-access-0987654321",         # Key for agent access
    "admin": "admin-key-full-access-1122334455"            # Admin access key
}

class SecurityManager:
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """Validate API key and return access level"""
        for level, key in API_KEYS.items():
            if key == api_key:
                return True, level
        return False, "unauthorized"

class VectorStore:
    model = None
    
    @classmethod
    def initialize(cls):
        """Initialize the embedding model if transformers is available"""
        if not HAS_TRANSFORMERS:
            logging.warning("Transformers not installed. Using fallback text search.")
            return False
        
        try:
            # Use a smaller model suitable for embeddings
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            cls.model = SentenceTransformer(model_name)
            logging.info(f"Vector store initialized with model: {model_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize vector store: {e}")
            return False
    
    @classmethod
    def get_embedding(cls, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text"""
        if not cls.model:
            return None
            
        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in VECTOR_CACHE:
            return VECTOR_CACHE[text_hash]
            
        try:
            # Generate embedding using SentenceTransformer
            embedding = cls.model.encode(text, convert_to_numpy=True)
            
            # Cache the result
            VECTOR_CACHE[text_hash] = embedding
            return embedding
        except Exception as e:
            logging.error(f"Embedding generation failed: {e}")
            return None

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]
    id: Optional[int] = 1
    api_key: Optional[str] = None

class MCPResponse(BaseModel):
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: int = 1

class AgentBlueprint(BaseModel):
    name: str
    parent: Optional[str] = None
    code: str
    config: Dict[str, Any]
    generation: int = 1
    mutations: List[str] = []

class BatchOperation(BaseModel):
    """Batch RPC operations"""
    operations: List[MCPRequest]
    id: Optional[int] = 1

api_key_header = Header(None, alias="X-API-Key")

async def get_api_key(api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Get and validate API key from header"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key missing")
        
    valid, level = SecurityManager.validate_api_key(api_key)
    if not valid:
        raise HTTPException(status_code=403, detail="Invalid API Key")
        
    return level

@app.post("/rpc", response_model=MCPResponse)
async def handle_rpc(request: MCPRequest, api_key: str = Depends(get_api_key)):
    """Main RPC endpoint for MCP protocol"""
    
    method = request.method
    params = request.params
    
    try:
        # Filesystem operations
        if method == "fs.read":
            result = await read_file(params.get("path"))
        elif method == "fs.write":
            result = await write_file(params.get("path"), params.get("content"))
        elif method == "fs.list":
            result = await list_directory(params.get("path", "."))
        elif method == "fs.delete":
            result = await delete_file(params.get("path"))
        elif method == "fs.mkdir":
            result = await create_directory(params.get("path"))
        elif method == "fs.search":
            result = await search_files(
                params.get("pattern", "*"), 
                params.get("path", "."),
                params.get("recursive", True)
            )
            
        # Agent-specific operations
        elif method == "agent.save":
            result = await save_agent(params.get("blueprint"))
        elif method == "agent.load":
            result = await load_agent(params.get("name"), params.get("version"))
        elif method == "agent.list":
            result = await list_agents(params.get("biome"))
        elif method == "agent.evolve":
            result = await save_evolution(params.get("parent"), params.get("child"), params.get("mutations"))
        elif method == "agent.get_lineage":
            result = await get_agent_lineage(params.get("name"))
            
        # Memory operations
        elif method == "memory.save":
            result = await save_memory(params.get("agent_name"), params.get("memory"))
        elif method == "memory.load":
            result = await load_memory(params.get("agent_name"), params.get("limit"))
        elif method == "memory.search":
            semantic = params.get("semantic", True)
            result = await search_memories(params.get("query"), params.get("agent_name"), semantic)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
        return MCPResponse(result=result, id=request.id)
        
    except Exception as e:
        return MCPResponse(
            error={"code": -32603, "message": str(e)},
            id=request.id
        )

@app.post("/batch", response_model=Dict[str, Any])
async def handle_batch(batch: BatchOperation, api_key: str = Depends(get_api_key)):
    """Handle multiple RPC operations in a single request"""
    results = []
    
    for op in batch.operations:
        # Process each operation individually
        op.api_key = api_key  # Pass through the API key
        result = await handle_rpc(op)
        results.append(result)
    
    return {
        "results": results,
        "count": len(results),
        "id": batch.id
    }

# Basic filesystem operations
async def read_file(path: str) -> Dict[str, Any]:
    """Read file contents"""
    file_path = Path(path)
    if not file_path.exists():
        return {"error": "File not found", "path": path}
    
    try:
        if file_path.suffix in ['.json']:
            content = json.loads(file_path.read_text())
        elif file_path.suffix in ['.yaml', '.yml']:
            content = yaml.safe_load(file_path.read_text())
        else:
            content = file_path.read_text()
            
        return {
            "content": content,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime
        }
    except Exception as e:
        return {"error": str(e), "path": path}

async def write_file(path: str, content: Any) -> Dict[str, Any]:
    """Write content to file"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if file_path.suffix in ['.json']:
            file_path.write_text(json.dumps(content, indent=2))
        elif file_path.suffix in ['.yaml', '.yml']:
            file_path.write_text(yaml.dump(content, default_flow_style=False))
        else:
            file_path.write_text(str(content))
            
        return {
            "success": True,
            "path": str(file_path),
            "size": file_path.stat().st_size
        }
    except Exception as e:
        return {"error": str(e), "path": path}

async def delete_file(path: str) -> Dict[str, Any]:
    """Delete a file or directory"""
    file_path = Path(path)
    if not file_path.exists():
        return {"error": "File not found", "path": path}
    
    try:
        if file_path.is_dir():
            shutil.rmtree(file_path)
        else:
            file_path.unlink()
            
        return {
            "success": True,
            "path": str(file_path),
            "deleted": True
        }
    except Exception as e:
        return {"error": str(e), "path": path}

async def create_directory(path: str) -> Dict[str, Any]:
    """Create a directory (and parents if needed)"""
    dir_path = Path(path)
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "path": str(dir_path),
            "created": True
        }
    except Exception as e:
        return {"error": str(e), "path": path}

async def list_directory(path: str) -> Dict[str, Any]:
    """List directory contents"""
    dir_path = Path(path)
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

async def search_files(pattern: str, path: str = ".", recursive: bool = True) -> Dict[str, Any]:
    """Search for files matching a pattern"""
    import fnmatch
    import os
    
    base_path = Path(path)
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
        "count": len(matches),
        "recursive": recursive
    }

# Agent-specific operations
async def save_agent(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """Save an agent blueprint with versioning"""
    agent = AgentBlueprint(**blueprint)
    
    # Create agent directory
    agent_dir = AGENTS_PATH / agent.name
    agent_dir.mkdir(exist_ok=True)
    
    # Generate version hash
    content_hash = hashlib.md5(agent.code.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version = f"{timestamp}_{content_hash}"
    
    # Save agent code
    code_file = agent_dir / f"{agent.name}_{version}.py"
    code_file.write_text(agent.code)
    
    # Save agent config
    config_file = agent_dir / f"config_{version}.yaml"
    config_data = {
        "name": agent.name,
        "version": version,
        "parent": agent.parent,
        "generation": agent.generation,
        "mutations": agent.mutations,
        "created": datetime.now().isoformat(),
        "config": agent.config
    }
    config_file.write_text(yaml.dump(config_data, default_flow_style=False))
    
    # Update latest symlink
    latest_code = agent_dir / f"{agent.name}_latest.py"
    latest_config = agent_dir / "config_latest.yaml"
    
    if latest_code.exists():
        latest_code.unlink()
    if latest_config.exists():
        latest_config.unlink()
        
    latest_code.symlink_to(code_file.name)
    latest_config.symlink_to(config_file.name)
    
    return {
        "success": True,
        "agent": agent.name,
        "version": version,
        "path": str(agent_dir),
        "generation": agent.generation
    }

async def load_agent(name: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Load an agent by name and version"""
    agent_dir = AGENTS_PATH / name
    
    if not agent_dir.exists():
        return {"error": f"Agent {name} not found"}
    
    # Load specific version or latest
    if version:
        code_file = agent_dir / f"{name}_{version}.py"
        config_file = agent_dir / f"config_{version}.yaml"
    else:
        code_file = agent_dir / f"{name}_latest.py"
        config_file = agent_dir / "config_latest.yaml"
    
    if not code_file.exists() or not config_file.exists():
        return {"error": f"Agent version not found"}
    
    # Load code and config
    code = code_file.read_text()
    config = yaml.safe_load(config_file.read_text())
    
    return {
        "name": name,
        "version": config.get("version"),
        "code": code,
        "config": config,
        "parent": config.get("parent"),
        "generation": config.get("generation", 1),
        "mutations": config.get("mutations", [])
    }

async def list_agents(biome: Optional[str] = None) -> Dict[str, Any]:
    """List all agents, optionally filtered by biome"""
    agents = []
    
    for agent_dir in AGENTS_PATH.iterdir():
        if agent_dir.is_dir():
            # Load latest config
            config_file = agent_dir / "config_latest.yaml"
            if config_file.exists():
                config = yaml.safe_load(config_file.read_text())
                
                # Filter by biome if specified
                if biome and config.get("config", {}).get("biome") != biome:
                    continue
                    
                agents.append({
                    "name": agent_dir.name,
                    "version": config.get("version"),
                    "generation": config.get("generation", 1),
                    "parent": config.get("parent"),
                    "biome": config.get("config", {}).get("biome"),
                    "created": config.get("created")
                })
    
    return {
        "agents": agents,
        "count": len(agents),
        "biome": biome
    }

async def save_evolution(parent_name: str, child_blueprint: Dict[str, Any], 
                        mutations: List[str]) -> Dict[str, Any]:
    """Save evolution history when an agent spawns a child"""
    
    # Save the child agent
    child_blueprint["parent"] = parent_name
    child_blueprint["mutations"] = mutations
    
    # Load parent to get generation
    parent = await load_agent(parent_name)
    if parent.get("generation"):
        child_blueprint["generation"] = parent["generation"] + 1
    
    child_result = await save_agent(child_blueprint)
    
    # Save evolution record
    evolution_record = {
        "parent": parent_name,
        "child": child_blueprint["name"],
        "generation": child_blueprint["generation"],
        "mutations": mutations,
        "timestamp": datetime.now().isoformat(),
        "parent_version": parent.get("version"),
        "child_version": child_result.get("version")
    }
    
    evolution_file = EVOLUTION_PATH / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{parent_name}_to_{child_blueprint['name']}.json"
    evolution_file.write_text(json.dumps(evolution_record, indent=2))
    
    return {
        "success": True,
        "parent": parent_name,
        "child": child_blueprint["name"],
        "generation": child_blueprint["generation"],
        "evolution_record": str(evolution_file)
    }

async def get_agent_lineage(name: str) -> Dict[str, Any]:
    """Get the complete lineage of an agent"""
    lineage = []
    current = name
    
    while current:
        agent = await load_agent(current)
        if "error" in agent:
            break
            
        lineage.append({
            "name": current,
            "generation": agent.get("generation", 1),
            "mutations": agent.get("mutations", []),
            "version": agent.get("version")
        })
        
        current = agent.get("parent")
    
    return {
        "agent": name,
        "lineage": lineage,
        "generations": len(lineage)
    }

# Memory operations
async def save_memory(agent_name: str, memory: Dict[str, Any]) -> Dict[str, Any]:
    """Save agent memory with timestamp"""
    memory_dir = MEMORIES_PATH / agent_name
    memory_dir.mkdir(exist_ok=True)
    
    # Add timestamp
    memory["timestamp"] = datetime.now().isoformat()
    memory["agent"] = agent_name
    
    # Save with timestamp filename
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{memory.get('type', 'general')}.json"
    memory_file = memory_dir / filename
    memory_file.write_text(json.dumps(memory, indent=2))
    
    return {
        "success": True,
        "agent": agent_name,
        "memory_file": str(memory_file),
        "timestamp": memory["timestamp"]
    }

async def load_memory(agent_name: str, limit: int = 100) -> Dict[str, Any]:
    """Load agent memories"""
    memory_dir = MEMORIES_PATH / agent_name
    
    if not memory_dir.exists():
        return {"memories": [], "count": 0}
    
    memories = []
    memory_files = sorted(memory_dir.glob("*.json"), reverse=True)[:limit]
    
    for memory_file in memory_files:
        memory = json.loads(memory_file.read_text())
        memories.append(memory)
    
    return {
        "agent": agent_name,
        "memories": memories,
        "count": len(memories),
        "total_available": len(list(memory_dir.glob("*.json")))
    }

async def search_memories(query: str, agent_name: Optional[str] = None, semantic: bool = True) -> Dict[str, Any]:
    """Search through memories with optional semantic search"""
    results = []
    search_dirs = [MEMORIES_PATH / agent_name] if agent_name else MEMORIES_PATH.iterdir()
    
    # Try to use semantic search if requested
    use_semantic = semantic and HAS_TRANSFORMERS and VectorStore.model is not None
    if use_semantic:
        query_embedding = VectorStore.get_embedding(query)
        if query_embedding is None:
            use_semantic = False
    
    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
            
        for memory_file in search_dir.glob("*.json"):
            memory = json.loads(memory_file.read_text())
            
            if use_semantic:
                # Get the memory text content to search
                memory_text = json.dumps(memory)
                memory_embedding = VectorStore.get_embedding(memory_text)
                
                if memory_embedding is not None:
                    # Compute semantic similarity with correct shapes
                    query_embedding_reshaped = query_embedding.reshape(1, -1)
                    memory_embedding_reshaped = memory_embedding.reshape(1, -1)
                    similarity = float(cosine_similarity(query_embedding_reshaped, memory_embedding_reshaped)[0][0])
                    
                    # Only include if similarity is above threshold
                    if similarity > 0.2:  # Lower threshold for better matches
                        results.append({
                            "agent": search_dir.name,
                            "memory": memory,
                            "file": memory_file.name,
                            "score": similarity
                        })
            else:
                # Fallback to simple text search
                if query.lower() in json.dumps(memory).lower():
                    results.append({
                        "agent": search_dir.name,
                        "memory": memory,
                        "file": memory_file.name,
                        "score": 1.0  # Placeholder for relevance scoring
                    })
    
    # Sort results by score
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "query": query,
        "semantic": use_semantic,
        "results": results[:50],  # Limit results
        "count": len(results)
    }

async def notify_clients(topic: str, data: Dict[str, Any]):
    """Send notification to all connected clients for a topic"""
    if topic not in connected_clients:
        return
        
    # Create notification message
    message = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    # Send to all connected clients for this topic
    disconnected = set()
    for client in connected_clients[topic]:
        try:
            await client.send_json(message)
        except WebSocketDisconnect:
            disconnected.add(client)
        except Exception as e:
            logging.error(f"Failed to send WebSocket message: {e}")
            disconnected.add(client)
    
    # Remove disconnected clients
    for client in disconnected:
        connected_clients[topic].remove(client)

connected_clients: Dict[str, Set[WebSocket]] = {
    "filesystem": set(),
    "agents": set(),
    "memories": set()
}

@app.websocket("/ws/{topic}")
async def websocket_endpoint(websocket: WebSocket, topic: str):
    """WebSocket endpoint for real-time updates"""
    if topic not in connected_clients:
        await websocket.close(code=1008, reason=f"Invalid topic: {topic}")
        return
        
    await websocket.accept()
    connected_clients[topic].add(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()
            # Handle any client messages if needed
            await websocket.send_json({
                "type": "acknowledgment",
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        connected_clients[topic].remove(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        if websocket in connected_clients[topic]:
            connected_clients[topic].remove(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint with system statistics"""
    # Collect basic system information
    storage_stats = {
        "agents": len(list(AGENTS_PATH.glob("*"))),
        "memories": len(list(MEMORIES_PATH.glob("*/**/*.json"))),
        "evolution": len(list(EVOLUTION_PATH.glob("*.json"))),
        "configs": len(list(CONFIGS_PATH.glob("*"))),
        "templates": len(list(TEMPLATES_PATH.glob("*")))
    }
    
    # Check available disk space
    import shutil
    total, used, free = shutil.disk_usage(str(AGENTS_PATH))
    disk_stats = {
        "total_gb": total // (1024**3),
        "used_gb": used // (1024**3),
        "free_gb": free // (1024**3),
        "percent_used": round((used / total) * 100, 2)
    }
    
    # Check if vector search is available
    vector_search = {
        "available": HAS_TRANSFORMERS,
        "model_loaded": VectorStore.model is not None,
        "cache_size": len(VECTOR_CACHE)
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
            "websocket_clients": {k: len(v) for k, v in connected_clients.items()},
            "authentication": "enabled"
        }
    }

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("mcp-filesystem.log")
        ]
    )
    
    # Initialize vector store if transformers is available
    try:
        VectorStore.initialize()
    except Exception as e:
        logging.warning(f"Failed to initialize vector store: {e}")
    
    # Generate server start message
    print("🗄️ BoarderframeOS MCP Filesystem Server v1.1.0")
    print("📁 Serving agent storage on port 8001")
    print("🔐 API Key authentication enabled")
    if HAS_TRANSFORMERS and VectorStore.model is not None:
        print("🧠 Vector search enabled with model: sentence-transformers/all-MiniLM-L6-v2")
    else:
        print("ℹ️ Vector search disabled: Install transformers and sentence-transformers packages")
    print("📡 WebSocket real-time updates available")
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8001)