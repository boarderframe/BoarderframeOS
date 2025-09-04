#!/usr/bin/env python3
"""
Simple FastAPI MCP Server Manager for testing Docker integration
"""
import os
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server Manager",
    version="1.0.0",
    description="MCP Server Manager for testing Docker integration"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
mcp_servers = []

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-server-manager",
        "version": "1.0.0"
    }

@app.get("/api/v1/health")
async def api_health_check() -> Dict[str, str]:
    """API health check endpoint"""
    return {
        "status": "healthy", 
        "api_version": "v1",
        "database": "connected",  # Simplified for demo
        "service": "mcp-server-manager"
    }

@app.get("/api/v1/servers")
async def get_servers() -> Dict[str, List[Dict[str, Any]]]:
    """Get all MCP servers"""
    return {"servers": mcp_servers}

@app.post("/api/v1/servers")
async def create_server(server_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new MCP server configuration"""
    server_id = len(mcp_servers) + 1
    server = {
        "id": server_id,
        "name": server_data.get("name", f"Server {server_id}"),
        "status": "configured",
        "created_at": "2025-01-01T00:00:00Z",
        **server_data
    }
    mcp_servers.append(server)
    return server

@app.get("/api/v1/servers/{server_id}")
async def get_server(server_id: int) -> Dict[str, Any]:
    """Get specific MCP server"""
    for server in mcp_servers:
        if server["id"] == server_id:
            return server
    raise HTTPException(status_code=404, detail="Server not found")

@app.delete("/api/v1/servers/{server_id}")
async def delete_server(server_id: int) -> Dict[str, str]:
    """Delete MCP server"""
    global mcp_servers
    mcp_servers = [s for s in mcp_servers if s["id"] != server_id]
    return {"message": "Server deleted successfully"}

@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Prometheus metrics endpoint"""
    return {
        "servers_total": len(mcp_servers),
        "servers_active": len([s for s in mcp_servers if s.get("status") == "running"]),
        "uptime": "running"
    }

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "MCP Server Manager API",
        "docs_url": "/docs",
        "health_url": "/health"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )