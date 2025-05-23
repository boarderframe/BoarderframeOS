"""
MCP Client Library for BoarderframeOS
Provides agents with easy access to the MCP filesystem server
"""

import httpx
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class MCPConfig:
    """Configuration for MCP client"""
    base_url: str = "http://localhost:8001"
    api_key: str = "default-key-boarderframe-dev-1234567890"
    timeout: float = 30.0
    max_retries: int = 3

class MCPClient:
    """Client for communicating with MCP filesystem server"""
    
    def __init__(self, config: MCPConfig = None):
        self.config = config or MCPConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={"X-API-Key": self.config.api_key}
        )
        self.logger = logging.getLogger(f"mcp_client")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(self, method: str, params: Dict[str, Any], request_id: int = None) -> Dict[str, Any]:
        """Make an RPC request to the MCP server"""
        request_id = request_id or int(datetime.now().timestamp() * 1000)
        
        payload = {
            "method": method,
            "params": params,
            "id": request_id
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post("/rpc", json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("error"):
                    raise MCPError(result["error"]["message"], result["error"].get("code", -1))
                
                return result.get("result")
                
            except httpx.RequestError as e:
                if attempt == self.config.max_retries - 1:
                    raise MCPError(f"Connection failed after {self.config.max_retries} attempts: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.HTTPStatusError as e:
                raise MCPError(f"HTTP error {e.response.status_code}: {e.response.text}")
    
    # File operations
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file"""
        return await self._make_request("fs.read", {"path": path})
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        return await self._make_request("fs.write", {"path": path, "content": content})
    
    async def list_files(self, path: str = ".") -> Dict[str, Any]:
        """List files in a directory"""
        return await self._make_request("fs.list", {"path": path})
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file"""
        return await self._make_request("fs.delete", {"path": path})
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        return await self._make_request("fs.mkdir", {"path": path})
    
    # Agent operations
    async def save_agent(self, name: str, config: Dict[str, Any], code: str = None) -> Dict[str, Any]:
        """Save an agent configuration"""
        params = {"name": name, "config": config}
        if code:
            params["code"] = code
        return await self._make_request("agent.save", params)
    
    async def load_agent(self, name: str, version: str = None) -> Dict[str, Any]:
        """Load an agent configuration"""
        params = {"name": name}
        if version:
            params["version"] = version
        return await self._make_request("agent.load", params)
    
    async def list_agents(self, biome: str = None) -> Dict[str, Any]:
        """List all agents"""
        params = {}
        if biome:
            params["biome"] = biome
        return await self._make_request("agent.list", params)
    
    async def delete_agent(self, name: str, version: str = None) -> Dict[str, Any]:
        """Delete an agent"""
        params = {"name": name}
        if version:
            params["version"] = version
        return await self._make_request("agent.delete", params)
    
    # Memory operations
    async def save_memory(self, agent_name: str, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Save a memory for an agent"""
        return await self._make_request("memory.save", {"agent": agent_name, "memory": memory})
    
    async def search_memories(self, query: str, agent_name: str = None, semantic: bool = True) -> Dict[str, Any]:
        """Search through memories"""
        params = {"query": query, "semantic": semantic}
        if agent_name:
            params["agent_name"] = agent_name
        return await self._make_request("memory.search", params)
    
    async def list_memories(self, agent_name: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List memories for an agent"""
        return await self._make_request("memory.list", {
            "agent": agent_name,
            "limit": limit,
            "offset": offset
        })
    
    async def delete_memory(self, agent_name: str, memory_id: str) -> Dict[str, Any]:
        """Delete a specific memory"""
        return await self._make_request("memory.delete", {
            "agent": agent_name,
            "id": memory_id
        })
    
    # Evolution operations
    async def save_evolution(self, agent_name: str, generation: int, changes: List[str], 
                           performance: Dict[str, Any]) -> Dict[str, Any]:
        """Save evolution data for an agent"""
        return await self._make_request("evolution.save", {
            "agent": agent_name,
            "generation": generation,
            "changes": changes,
            "performance": performance
        })
    
    async def get_evolution_history(self, agent_name: str) -> Dict[str, Any]:
        """Get evolution history for an agent"""
        return await self._make_request("evolution.list", {"agent": agent_name})
    
    # Batch operations
    async def batch_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple operations in a batch"""
        batch_ops = []
        for i, op in enumerate(operations):
            batch_ops.append({
                "method": op["method"],
                "params": op["params"],
                "id": i + 1
            })
        
        return await self._make_request("batch", {"operations": batch_ops})
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        response = await self.client.get("/health")
        response.raise_for_status()
        return response.json()

class MCPError(Exception):
    """Exception raised for MCP-related errors"""
    
    def __init__(self, message: str, code: int = -1):
        super().__init__(message)
        self.code = code
        self.message = message

# Convenience functions for quick operations
async def quick_save_memory(agent_name: str, content: str, memory_type: str = "observation"):
    """Quick helper to save a memory"""
    async with MCPClient() as client:
        memory = {
            "content": content,
            "type": memory_type,
            "timestamp": datetime.now().isoformat()
        }
        return await client.save_memory(agent_name, memory)

async def quick_search_memories(query: str, agent_name: str = None):
    """Quick helper to search memories"""
    async with MCPClient() as client:
        return await client.search_memories(query, agent_name)

async def quick_save_agent_config(name: str, config: Dict[str, Any]):
    """Quick helper to save agent configuration"""
    async with MCPClient() as client:
        return await client.save_agent(name, config)
