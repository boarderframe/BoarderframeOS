#!/usr/bin/env python3
"""
MCP Server Management API
FastAPI server that provides REST endpoints for the dashboard
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from pathlib import Path
from typing import Dict, List
from mcp_manager import MCPServerManager
import subprocess
import signal
import os

app = FastAPI(
    title="MCP Server Management API",
    description="REST API for managing Model Context Protocol servers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the MCP manager
manager = MCPServerManager()

@app.get("/")
async def serve_dashboard():
    """Serve the main dashboard HTML"""
    dashboard_path = Path(__file__).parent / "dashboard.html"
    return FileResponse(dashboard_path)

@app.get("/api/status")
async def get_server_status():
    """Get the status of all MCP servers"""
    try:
        # Refresh server status
        manager.servers = manager._discover_servers()
        return manager.get_server_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting server status: {str(e)}")

@app.get("/api/servers")
async def get_servers():
    """Get all servers grouped by category"""
    try:
        # Refresh server status
        manager.servers = manager._discover_servers()
        return manager.get_servers_by_category()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting servers: {str(e)}")

@app.post("/api/servers/{server_name}/start")
async def start_server(server_name: str):
    """Start a specific MCP server"""
    try:
        # Find the server
        server = next((s for s in manager.servers if s.name == server_name), None)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
        if not server.port:
            raise HTTPException(status_code=400, detail=f"Server '{server_name}' has no port configured")
        
        if server.status == "running":
            return {"message": f"Server '{server_name}' is already running", "success": True}
        
        # Start the server
        success = manager.start_server(server_name)
        if success:
            return {"message": f"Server '{server_name}' started successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to start server '{server_name}'")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting server: {str(e)}")

@app.post("/api/servers/{server_name}/stop")
async def stop_server(server_name: str):
    """Stop a specific MCP server"""
    try:
        # Find the server
        server = next((s for s in manager.servers if s.name == server_name), None)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
        if server.status != "running":
            return {"message": f"Server '{server_name}' is not running", "success": True}
        
        # Stop the server
        success = manager.stop_server(server_name)
        if success:
            return {"message": f"Server '{server_name}' stopped successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to stop server '{server_name}'")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping server: {str(e)}")

@app.get("/api/servers/{server_name}")
async def get_server_details(server_name: str):
    """Get detailed information about a specific server"""
    try:
        # Find the server
        server = next((s for s in manager.servers if s.name == server_name), None)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
        # Refresh status
        server.status = manager._check_server_status(server)
        
        return {
            "name": server.name,
            "file_path": server.file_path,
            "category": server.category,
            "description": server.description,
            "port": server.port,
            "status": server.status,
            "pid": server.pid,
            "last_started": server.last_started
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting server details: {str(e)}")

@app.post("/api/servers/stop-all")
async def stop_all_servers():
    """Stop all running MCP servers"""
    try:
        stopped_servers = []
        failed_servers = []
        
        for server in manager.servers:
            if server.status == "running" and server.port:
                success = manager.stop_server(server.name)
                if success:
                    stopped_servers.append(server.name)
                else:
                    failed_servers.append(server.name)
        
        return {
            "message": f"Stopped {len(stopped_servers)} servers",
            "stopped": stopped_servers,
            "failed": failed_servers,
            "success": len(failed_servers) == 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping servers: {str(e)}")

@app.get("/api/logs/{server_name}")
async def get_server_logs(server_name: str, lines: int = 50):
    """Get recent logs for a specific server"""
    try:
        # Find the server
        server = next((s for s in manager.servers if s.name == server_name), None)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
        # Log file path
        log_file = manager.base_path / "logs" / f"{server.name.lower().replace(' ', '_')}.log"
        
        if not log_file.exists():
            return {"logs": "", "message": "No log file found"}
        
        # Read the last N lines
        try:
            result = subprocess.run(
                ["tail", "-n", str(lines), str(log_file)],
                capture_output=True,
                text=True
            )
            
            return {
                "logs": result.stdout,
                "server": server_name,
                "lines": lines
            }
        
        except Exception as e:
            return {"logs": f"Error reading logs: {str(e)}", "error": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MCP Server Management API",
        "version": "1.0.0",
        "total_servers": len(manager.servers),
        "running_servers": len([s for s in manager.servers if s.status == "running"])
    }

# Error handlers

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc.detail) if hasattr(exc, 'detail') else "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc.detail) if hasattr(exc, 'detail') else "An unexpected error occurred"}
    )

def main():
    """Run the server"""
    print("🚀 Starting MCP Server Management API...")
    print("📊 Dashboard will be available at: http://localhost:8090")
    print("📡 API endpoints at: http://localhost:8090/api/")
    print("❤️  Health check: http://localhost:8090/api/health")
    print()
    
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    try:
        uvicorn.run(
            "api_server:app",
            host="0.0.0.0",
            port=8090,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MCP Server Management API...")

if __name__ == "__main__":
    main()