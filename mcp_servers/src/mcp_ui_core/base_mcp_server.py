"""
Base MCP Server with UI Protocol Support
Reusable foundation for all MCP servers with UI capabilities
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .protocol.mcp_ui_engine import MCPUIEngine, MCPUIResource, MCPUIResponse, UIResourceType


class MCPTool(BaseModel):
    """MCP Tool definition with UI support"""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns_ui: bool = False
    ui_component_type: Optional[str] = None


class MCPServerConfig(BaseModel):
    """Configuration for MCP Server"""
    name: str
    description: str
    version: str = "1.0.0"
    port: int = 8000
    host: str = "0.0.0.0"
    enable_ui: bool = True
    ui_template_dir: str = "ui_templates"
    enable_cors: bool = True
    debug: bool = False


class BaseMCPServer(ABC):
    """
    Base MCP Server with UI Protocol Support
    
    This class provides the foundation for all MCP servers that need to serve
    interactive UI components following the MCP-UI Protocol specification.
    
    Features:
    - Automatic UI resource serving
    - Token-optimized responses
    - Security and performance built-in
    - Easy component registration
    - Real-time updates via WebSocket
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.app = FastAPI(
            title=config.name,
            description=config.description,
            version=config.version,
            debug=config.debug
        )
        
        # Initialize UI engine
        self.ui_engine = MCPUIEngine(
            service_name=config.name.lower().replace(' ', '-'),
            template_dir=config.ui_template_dir
        )
        
        # Tool registry
        self.tools: Dict[str, MCPTool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        
        # Logger
        self.logger = logging.getLogger(f"mcp.{config.name}")
        
        print(f"🚀 {config.name} MCP Server initialized")
        print(f"📡 Server will run on {config.host}:{config.port}")
        print(f"🎨 UI templates: {config.ui_template_dir}")
    
    # Abstract methods for subclasses
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize server-specific components and register tools"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return server health status"""
        pass
    
    # Tool registration methods
    
    def register_tool(self, 
                     name: str,
                     description: str,
                     parameters: Dict[str, Any],
                     handler: Callable,
                     returns_ui: bool = False,
                     ui_component_type: Optional[str] = None) -> None:
        """Register a tool with optional UI support"""
        
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            returns_ui=returns_ui,
            ui_component_type=ui_component_type
        )
        
        self.tools[name] = tool
        self.tool_handlers[name] = handler
        
        self.logger.info(f"📝 Registered tool: {name} (UI: {returns_ui})")
    
    def register_ui_tool(self,
                        name: str,
                        description: str,
                        parameters: Dict[str, Any],
                        handler: Callable,
                        component_type: str) -> None:
        """Convenience method to register UI-enabled tool"""
        
        self.register_tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            returns_ui=True,
            ui_component_type=component_type
        )
    
    # UI resource methods
    
    async def create_ui_component(self,
                                component_type: str,
                                data: Any,
                                template_name: Optional[str] = None,
                                theme: str = "default",
                                **options) -> MCPUIResource:
        """Create UI component resource"""
        
        return self.ui_engine.create_component_resource(
            component_type=component_type,
            data=data,
            template_name=template_name,
            theme=theme,
            **options
        )
    
    async def build_ui_response(self,
                              ui_resources: List[MCPUIResource],
                              data: Optional[Any] = None,
                              message: str = "UI component loaded successfully.") -> Dict[str, Any]:
        """Build MCP-UI Protocol compliant response"""
        
        mcp_response = self.ui_engine.build_optimized_response(
            ui_resources=ui_resources,
            raw_data=data
        )
        
        return {
            "message": message,
            "ui_resources": {uri: resource.dict() for uri, resource in mcp_response.ui_resources.items()},
            "data": mcp_response.data,
            "metadata": mcp_response.metadata,
            "protocol": "mcp-ui",
            "version": "1.0.0"
        }
    
    # Server lifecycle methods
    
    async def startup(self) -> None:
        """Server startup tasks"""
        self.logger.info(f"🚀 Starting {self.config.name}")
        
        # Initialize server-specific components
        await self.initialize()
        
        # Setup UI template directory
        self._ensure_ui_templates()
        
        self.logger.info(f"✅ {self.config.name} startup complete")
    
    async def shutdown(self) -> None:
        """Server shutdown tasks"""
        self.logger.info(f"🛑 Shutting down {self.config.name}")
        
        # Cleanup resources
        self.ui_engine.cleanup_expired_resources()
        
        self.logger.info(f"✅ {self.config.name} shutdown complete")
    
    def run(self) -> None:
        """Run the server"""
        import uvicorn
        
        # Add startup and shutdown events
        @self.app.on_event("startup")
        async def startup_event():
            await self.startup()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown()
        
        # Run server
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            reload=self.config.debug,
            log_level="info" if not self.config.debug else "debug"
        )
    
    # Private setup methods
    
    def _setup_middleware(self) -> None:
        """Setup FastAPI middleware"""
        
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"]
            )
    
    def _setup_routes(self) -> None:
        """Setup FastAPI routes"""
        
        # Health check endpoint
        @self.app.get("/health")
        async def health():
            health_data = await self.health_check()
            return {
                "status": "healthy",
                "service": self.config.name,
                "version": self.config.version,
                "timestamp": datetime.now().isoformat(),
                "ui_enabled": self.config.enable_ui,
                **health_data
            }
        
        # MCP tools endpoint
        @self.app.get("/tools")
        async def list_tools():
            return {
                "tools": [tool.dict() for tool in self.tools.values()],
                "count": len(self.tools),
                "ui_enabled_count": len([t for t in self.tools.values() if t.returns_ui])
            }
        
        # Tool execution endpoint
        @self.app.post("/tools/{tool_name}")
        async def execute_tool(tool_name: str, request: Request):
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            
            # Get request data
            try:
                request_data = await request.json()
            except:
                request_data = {}
            
            # Execute tool
            handler = self.tool_handlers[tool_name]
            tool = self.tools[tool_name]
            
            try:
                result = await handler(**request_data)
                
                # Handle UI tools
                if tool.returns_ui and isinstance(result, dict) and "ui_resources" in result:
                    return result
                else:
                    # Standard tool response
                    return {
                        "tool": tool_name,
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                self.logger.error(f"Tool execution error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # UI resource serving
        if self.config.enable_ui:
            @self.app.get("/ui/{resource_id:path}")
            async def serve_ui_resource(resource_id: str):
                # Construct URI
                uri = f"ui://{self.ui_engine.service_name}/{resource_id}"
                
                # Serve resource
                content = self.ui_engine.serve_ui_resource(uri)
                if content is None:
                    raise HTTPException(status_code=404, detail="UI resource not found")
                
                return HTMLResponse(content=content)
            
            # Static UI assets
            ui_static_path = Path(self.config.ui_template_dir) / "static"
            if ui_static_path.exists():
                self.app.mount("/ui/static", StaticFiles(directory=str(ui_static_path)), name="ui-static")
        
        # Server statistics
        @self.app.get("/stats")
        async def server_stats():
            ui_stats = self.ui_engine.get_statistics()
            return {
                "server": {
                    "name": self.config.name,
                    "uptime": "calculated_in_production",
                    "tools_registered": len(self.tools),
                    "ui_tools": len([t for t in self.tools.values() if t.returns_ui])
                },
                "ui_engine": ui_stats,
                "timestamp": datetime.now().isoformat()
            }
    
    def _ensure_ui_templates(self) -> None:
        """Ensure UI template directory exists"""
        template_dir = Path(self.config.ui_template_dir)
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (template_dir / "components").mkdir(exist_ok=True)
        (template_dir / "themes").mkdir(exist_ok=True)
        (template_dir / "layouts").mkdir(exist_ok=True)
        (template_dir / "static").mkdir(exist_ok=True)
        
        # Create default theme if not exists
        default_theme = template_dir / "themes" / "default.json"
        if not default_theme.exists():
            theme_data = {
                "primary_color": "#007bff",
                "secondary_color": "#6c757d", 
                "success_color": "#28a745",
                "danger_color": "#dc3545",
                "warning_color": "#ffc107",
                "info_color": "#17a2b8",
                "font_family": "system-ui, -apple-system, sans-serif",
                "border_radius": "4px",
                "spacing_unit": "8px"
            }
            
            with open(default_theme, 'w') as f:
                json.dump(theme_data, f, indent=2)
            
            self.logger.info("📝 Created default theme")


# Example implementation class
class ExampleMCPServer(BaseMCPServer):
    """Example MCP server implementation"""
    
    async def initialize(self) -> None:
        """Initialize example server"""
        
        # Register a simple tool
        self.register_tool(
            name="echo",
            description="Echo back the input",
            parameters={"text": {"type": "string", "description": "Text to echo"}},
            handler=self._echo_handler
        )
        
        # Register a UI tool
        self.register_ui_tool(
            name="create_card",
            description="Create a UI card component",
            parameters={
                "title": {"type": "string", "description": "Card title"},
                "content": {"type": "string", "description": "Card content"}
            },
            handler=self._create_card_handler,
            component_type="card"
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for example server"""
        return {
            "example_status": "operational",
            "features": ["echo", "card_creation"]
        }
    
    async def _echo_handler(self, text: str) -> str:
        """Simple echo handler"""
        return f"Echo: {text}"
    
    async def _create_card_handler(self, title: str, content: str) -> Dict[str, Any]:
        """Create card UI component"""
        
        # Create UI resource
        ui_resource = await self.create_ui_component(
            component_type="card",
            data={"title": title, "content": content}
        )
        
        # Return UI response
        return await self.build_ui_response(
            ui_resources=[ui_resource],
            data={"title": title, "content_length": len(content)},
            message=f"Card '{title}' created successfully."
        )


# Factory function
def create_mcp_server(config: MCPServerConfig, server_class: type = ExampleMCPServer) -> BaseMCPServer:
    """Factory function to create MCP server instance"""
    return server_class(config)