"""
MCP Registry Server for BoarderframeOS
Central registry for MCP servers, tools, and capabilities discovery
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Set
import asyncio
import json
import logging
import uvicorn
import httpx
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mcp_registry")

app = FastAPI(title="MCP Registry Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class MCPServerInfo(BaseModel):
    server_id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., description="Human-readable server name")
    description: str = Field(..., description="Server description")
    host: str = Field(..., description="Server host")
    port: int = Field(..., description="Server port")
    version: str = Field(default="1.0.0", description="Server version")
    status: str = Field(default="unknown", description="Server status")
    capabilities: List[str] = Field(default=[], description="Server capabilities")
    tools: List[str] = Field(default=[], description="Available tools")
    health_check_url: str = Field(..., description="Health check endpoint")
    last_seen: Optional[datetime] = Field(None, description="Last successful health check")

class ToolInfo(BaseModel):
    tool_id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    server_id: str = Field(..., description="Server providing the tool")
    category: str = Field(..., description="Tool category")
    parameters: Dict[str, Any] = Field(default={}, description="Tool parameters schema")
    examples: List[Dict] = Field(default=[], description="Usage examples")
    access_level: str = Field(default="public", description="Access level: public, restricted, private")

class AgentCapability(BaseModel):
    capability_id: str = Field(..., description="Unique capability identifier")
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    required_tools: List[str] = Field(default=[], description="Required tools")
    optional_tools: List[str] = Field(default=[], description="Optional tools")
    complexity_level: int = Field(default=1, description="Complexity level 1-5")

class RegistrationRequest(BaseModel):
    server_info: MCPServerInfo
    tools: List[ToolInfo] = Field(default=[], description="Tools provided by server")

class ToolSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    category: Optional[str] = Field(None, description="Tool category filter")
    server_id: Optional[str] = Field(None, description="Server filter")
    capabilities: Optional[List[str]] = Field(None, description="Required capabilities")

# Registry Storage
class MCPRegistry:
    """Central registry for MCP servers and tools"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerInfo] = {}
        self.tools: Dict[str, ToolInfo] = {}
        self.capabilities: Dict[str, AgentCapability] = {}
        self.server_tools: Dict[str, Set[str]] = {}  # server_id -> tool_ids
        self.tool_categories: Dict[str, Set[str]] = {}  # category -> tool_ids
        
        # Initialize with core capabilities
        self._initialize_core_capabilities()
    
    def _initialize_core_capabilities(self):
        """Initialize core agent capabilities"""
        core_capabilities = [
            AgentCapability(
                capability_id="file_operations",
                name="File Operations",
                description="Read, write, and manipulate files",
                required_tools=["filesystem:read", "filesystem:write"],
                optional_tools=["filesystem:search", "filesystem:backup"],
                complexity_level=1
            ),
            AgentCapability(
                capability_id="web_automation",
                name="Web Automation",
                description="Automate web browser interactions",
                required_tools=["browser:navigate", "browser:click", "browser:extract"],
                optional_tools=["browser:screenshot", "browser:script"],
                complexity_level=3
            ),
            AgentCapability(
                capability_id="code_generation",
                name="Code Generation",
                description="Generate and analyze code",
                required_tools=["llm:generate", "filesystem:write"],
                optional_tools=["git:commit", "browser:research"],
                complexity_level=4
            ),
            AgentCapability(
                capability_id="data_analysis",
                name="Data Analysis",
                description="Analyze and process data",
                required_tools=["database:query", "llm:analyze"],
                optional_tools=["filesystem:read", "browser:scrape"],
                complexity_level=3
            ),
            AgentCapability(
                capability_id="trading_operations",
                name="Trading Operations",
                description="Execute trading strategies",
                required_tools=["browser:navigate", "database:store"],
                optional_tools=["llm:analyze", "filesystem:log"],
                complexity_level=5
            )
        ]
        
        for capability in core_capabilities:
            self.capabilities[capability.capability_id] = capability
    
    def register_server(self, server_info: MCPServerInfo, tools: List[ToolInfo] = None) -> bool:
        """Register an MCP server and its tools"""
        try:
            self.servers[server_info.server_id] = server_info
            self.server_tools[server_info.server_id] = set()
            
            if tools:
                for tool in tools:
                    self.register_tool(tool)
            
            logger.info(f"Registered MCP server: {server_info.name} ({server_info.server_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register server {server_info.server_id}: {e}")
            return False
    
    def register_tool(self, tool_info: ToolInfo) -> bool:
        """Register a tool"""
        try:
            self.tools[tool_info.tool_id] = tool_info
            
            # Update server tools mapping
            if tool_info.server_id in self.server_tools:
                self.server_tools[tool_info.server_id].add(tool_info.tool_id)
            
            # Update category mapping
            category = tool_info.category
            if category not in self.tool_categories:
                self.tool_categories[category] = set()
            self.tool_categories[category].add(tool_info.tool_id)
            
            logger.info(f"Registered tool: {tool_info.name} ({tool_info.tool_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool_info.tool_id}: {e}")
            return False
    
    def unregister_server(self, server_id: str) -> bool:
        """Unregister an MCP server and its tools"""
        try:
            if server_id not in self.servers:
                return True
            
            # Remove server's tools
            if server_id in self.server_tools:
                tool_ids = self.server_tools[server_id].copy()
                for tool_id in tool_ids:
                    self.unregister_tool(tool_id)
                del self.server_tools[server_id]
            
            # Remove server
            del self.servers[server_id]
            logger.info(f"Unregistered MCP server: {server_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister server {server_id}: {e}")
            return False
    
    def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool"""
        try:
            if tool_id not in self.tools:
                return True
            
            tool_info = self.tools[tool_id]
            
            # Remove from category mapping
            category = tool_info.category
            if category in self.tool_categories:
                self.tool_categories[category].discard(tool_id)
                if not self.tool_categories[category]:
                    del self.tool_categories[category]
            
            # Remove from server mapping
            server_id = tool_info.server_id
            if server_id in self.server_tools:
                self.server_tools[server_id].discard(tool_id)
            
            # Remove tool
            del self.tools[tool_id]
            logger.info(f"Unregistered tool: {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_id}: {e}")
            return False
    
    def search_tools(self, search_request: ToolSearchRequest) -> List[ToolInfo]:
        """Search for tools based on criteria"""
        results = []
        
        for tool_id, tool_info in self.tools.items():
            # Apply filters
            if search_request.server_id and tool_info.server_id != search_request.server_id:
                continue
            
            if search_request.category and tool_info.category != search_request.category:
                continue
            
            # Text search
            if search_request.query:
                query_lower = search_request.query.lower()
                if not (query_lower in tool_info.name.lower() or 
                       query_lower in tool_info.description.lower()):
                    continue
            
            # Capability search
            if search_request.capabilities:
                tool_matches_capability = False
                for capability_id in search_request.capabilities:
                    if capability_id in self.capabilities:
                        capability = self.capabilities[capability_id]
                        if (tool_id in capability.required_tools or 
                            tool_id in capability.optional_tools):
                            tool_matches_capability = True
                            break
                
                if not tool_matches_capability:
                    continue
            
            results.append(tool_info)
        
        return results
    
    def get_tools_for_capability(self, capability_id: str) -> Dict[str, List[ToolInfo]]:
        """Get all tools needed for a specific capability"""
        if capability_id not in self.capabilities:
            return {"required": [], "optional": []}
        
        capability = self.capabilities[capability_id]
        
        required_tools = []
        for tool_id in capability.required_tools:
            if tool_id in self.tools:
                required_tools.append(self.tools[tool_id])
        
        optional_tools = []
        for tool_id in capability.optional_tools:
            if tool_id in self.tools:
                optional_tools.append(self.tools[tool_id])
        
        return {
            "required": required_tools,
            "optional": optional_tools
        }
    
    def update_server_status(self, server_id: str, status: str, last_seen: datetime = None):
        """Update server status"""
        if server_id in self.servers:
            self.servers[server_id].status = status
            if last_seen:
                self.servers[server_id].last_seen = last_seen

# Global registry instance
registry = MCPRegistry()

# Health Check Manager
class HealthCheckManager:
    """Manages health checks for registered servers"""
    
    def __init__(self, registry: MCPRegistry):
        self.registry = registry
        self.check_interval = 60  # seconds
        self.timeout = 10  # seconds
        self.running = False
    
    async def start(self):
        """Start health check monitoring"""
        self.running = True
        asyncio.create_task(self._health_check_loop())
        logger.info("Health check manager started")
    
    async def stop(self):
        """Stop health check monitoring"""
        self.running = False
        logger.info("Health check manager stopped")
    
    async def _health_check_loop(self):
        """Main health check loop"""
        while self.running:
            try:
                await self._check_all_servers()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(30)
    
    async def _check_all_servers(self):
        """Check health of all registered servers"""
        tasks = []
        for server_id, server_info in self.registry.servers.items():
            task = asyncio.create_task(self._check_server_health(server_info))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_server_health(self, server_info: MCPServerInfo):
        """Check health of a specific server"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"http://{server_info.host}:{server_info.port}{server_info.health_check_url}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    self.registry.update_server_status(
                        server_info.server_id, 
                        "healthy", 
                        datetime.now()
                    )
                else:
                    self.registry.update_server_status(server_info.server_id, "unhealthy")
                    
        except Exception as e:
            logger.warning(f"Health check failed for {server_info.server_id}: {e}")
            self.registry.update_server_status(server_info.server_id, "offline")

# Initialize health check manager
health_manager = HealthCheckManager(registry)

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize registry on startup"""
    await health_manager.start()
    
    # Auto-register core MCP servers
    await _register_core_servers()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await health_manager.stop()

async def _register_core_servers():
    """Register core MCP servers"""
    core_servers = [
        {
            "server_info": MCPServerInfo(
                server_id="filesystem",
                name="Filesystem MCP Server",
                description="File operations and management",
                host="127.0.0.1",
                port=8001,
                capabilities=["file_operations", "backup", "search"],
                tools=["read", "write", "delete", "search", "backup"],
                health_check_url="/health"
            ),
            "tools": [
                ToolInfo(
                    tool_id="filesystem:read",
                    name="Read File",
                    description="Read contents of a file",
                    server_id="filesystem",
                    category="file_operations",
                    parameters={"file_path": "string", "encoding": "string"},
                    access_level="public"
                ),
                ToolInfo(
                    tool_id="filesystem:write",
                    name="Write File", 
                    description="Write contents to a file",
                    server_id="filesystem",
                    category="file_operations",
                    parameters={"file_path": "string", "content": "string", "encoding": "string"},
                    access_level="public"
                )
            ]
        },
        {
            "server_info": MCPServerInfo(
                server_id="llm",
                name="LLM MCP Server",
                description="Large Language Model operations",
                host="127.0.0.1",
                port=8005,
                capabilities=["text_generation", "analysis"],
                tools=["generate", "chat", "analyze"],
                health_check_url="/health"
            ),
            "tools": [
                ToolInfo(
                    tool_id="llm:generate",
                    name="Generate Text",
                    description="Generate text using LLM",
                    server_id="llm",
                    category="ai_generation",
                    parameters={"prompt": "string", "model": "string", "temperature": "float"},
                    access_level="public"
                )
            ]
        },
        {
            "server_info": MCPServerInfo(
                server_id="browser",
                name="Browser MCP Server",
                description="Web browser automation",
                host="127.0.0.1",
                port=8003,
                capabilities=["web_automation", "scraping"],
                tools=["navigate", "click", "extract", "screenshot"],
                health_check_url="/health"
            ),
            "tools": [
                ToolInfo(
                    tool_id="browser:navigate",
                    name="Navigate to URL",
                    description="Navigate browser to specified URL",
                    server_id="browser",
                    category="web_automation",
                    parameters={"url": "string", "wait_for": "string"},
                    access_level="public"
                )
            ]
        }
    ]
    
    for server_config in core_servers:
        registry.register_server(
            server_config["server_info"],
            server_config["tools"]
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp_registry",
        "registered_servers": len(registry.servers),
        "registered_tools": len(registry.tools),
        "capabilities": len(registry.capabilities)
    }

@app.post("/register")
async def register_server(request: RegistrationRequest):
    """Register an MCP server and its tools"""
    success = registry.register_server(request.server_info, request.tools)
    
    if success:
        return {
            "success": True,
            "message": f"Server {request.server_info.server_id} registered successfully",
            "server_id": request.server_info.server_id
        }
    else:
        raise HTTPException(status_code=400, detail="Registration failed")

@app.delete("/servers/{server_id}")
async def unregister_server(server_id: str):
    """Unregister an MCP server"""
    success = registry.unregister_server(server_id)
    
    if success:
        return {"success": True, "message": f"Server {server_id} unregistered"}
    else:
        raise HTTPException(status_code=400, detail="Unregistration failed")

@app.get("/servers")
async def list_servers():
    """List all registered servers"""
    return {
        "servers": [
            {
                **server.dict(),
                "tools_count": len(registry.server_tools.get(server.server_id, set()))
            }
            for server in registry.servers.values()
        ]
    }

@app.get("/servers/{server_id}")
async def get_server(server_id: str):
    """Get specific server information"""
    if server_id not in registry.servers:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server = registry.servers[server_id]
    tools = [
        registry.tools[tool_id] 
        for tool_id in registry.server_tools.get(server_id, set())
        if tool_id in registry.tools
    ]
    
    return {
        "server": server.dict(),
        "tools": [tool.dict() for tool in tools]
    }

@app.post("/tools/search")
async def search_tools(request: ToolSearchRequest):
    """Search for tools"""
    results = registry.search_tools(request)
    return {
        "tools": [tool.dict() for tool in results],
        "total": len(results)
    }

@app.get("/tools")
async def list_tools():
    """List all registered tools"""
    return {
        "tools": [tool.dict() for tool in registry.tools.values()],
        "by_category": {
            category: len(tool_ids) 
            for category, tool_ids in registry.tool_categories.items()
        }
    }

@app.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get specific tool information"""
    if tool_id not in registry.tools:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return {"tool": registry.tools[tool_id].dict()}

@app.get("/capabilities")
async def list_capabilities():
    """List all available capabilities"""
    return {
        "capabilities": [cap.dict() for cap in registry.capabilities.values()]
    }

@app.get("/capabilities/{capability_id}/tools")
async def get_capability_tools(capability_id: str):
    """Get tools for a specific capability"""
    if capability_id not in registry.capabilities:
        raise HTTPException(status_code=404, detail="Capability not found")
    
    tools = registry.get_tools_for_capability(capability_id)
    return {
        "capability": registry.capabilities[capability_id].dict(),
        "required_tools": [tool.dict() for tool in tools["required"]],
        "optional_tools": [tool.dict() for tool in tools["optional"]]
    }

@app.get("/categories")
async def list_categories():
    """List all tool categories"""
    return {
        "categories": {
            category: {
                "tool_count": len(tool_ids),
                "tools": [
                    registry.tools[tool_id].name 
                    for tool_id in tool_ids 
                    if tool_id in registry.tools
                ]
            }
            for category, tool_ids in registry.tool_categories.items()
        }
    }

@app.get("/stats")
async def get_registry_stats():
    """Get registry statistics"""
    healthy_servers = len([s for s in registry.servers.values() if s.status == "healthy"])
    
    return {
        "servers": {
            "total": len(registry.servers),
            "healthy": healthy_servers,
            "unhealthy": len(registry.servers) - healthy_servers
        },
        "tools": {
            "total": len(registry.tools),
            "by_category": {
                category: len(tool_ids)
                for category, tool_ids in registry.tool_categories.items()
            }
        },
        "capabilities": len(registry.capabilities),
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Registry Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"Starting MCP Registry Server on {args.host}:{args.port}")
    uvicorn.run(
        "registry_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )