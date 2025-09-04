"""
Base MCP Server with UI Capabilities
Extensible base class for building MCP servers with rich UI support
"""

from typing import Dict, List, Any, Optional, Union, Type
from abc import ABC, abstractmethod
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from .protocol import (
    MCPUIResource,
    MCPUIResponse,
    MCPUIProtocol,
    MCPUIMetadata,
    ResourceType,
    RenderingMode,
    create_error_response,
    create_loading_response
)
from .security import SecurityManager, SecurityConfig
from .state import StateManager
from .communication import MessageBus


# ============================================================================
# Server Configuration
# ============================================================================

class MCPServerConfig(BaseModel):
    """Configuration for MCP Server"""
    name: str = Field(..., description="Server name")
    version: str = Field(default="1.0.0")
    description: Optional[str] = Field(None)
    
    # Network settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    base_path: str = Field(default="/api/v1")
    
    # Security settings
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # UI settings
    ui_enabled: bool = Field(default=True)
    max_ui_resources: int = Field(default=10)
    default_theme: str = Field(default="default")
    
    # Performance settings
    cache_enabled: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)
    max_concurrent_requests: int = Field(default=100)
    request_timeout: int = Field(default=30)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# ============================================================================
# Base MCP Server
# ============================================================================

class MCPServer(ABC):
    """
    Base MCP Server with UI capabilities
    
    Provides:
    - Protocol compliance
    - Security management
    - State management
    - Component creation
    - Response building
    """
    
    def __init__(self, config: Union[MCPServerConfig, Dict[str, Any]]):
        """
        Initialize MCP Server
        
        Args:
            config: Server configuration
        """
        # Parse config
        if isinstance(config, dict):
            self.config = MCPServerConfig(**config)
        else:
            self.config = config
        
        # Setup logging
        self._setup_logging()
        
        # Initialize core components
        self.protocol = MCPUIProtocol(strict_mode=True)
        self.security = SecurityManager(self.config.security)
        self.state = StateManager()
        self.message_bus = MessageBus()
        
        # Component registry
        self._components: Dict[str, Type["Component"]] = {}
        self._themes: Dict[str, "Theme"] = {}
        
        # Request tracking
        self._active_requests: Dict[str, datetime] = {}
        
        # Initialize server
        self._initialize()
        
        self.logger.info(f"MCP Server '{self.config.name}' initialized")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=self.config.log_format
        )
        self.logger = logging.getLogger(self.config.name)
    
    def _initialize(self):
        """Initialize server components"""
        # Register default components
        self._register_default_components()
        
        # Load default theme
        self._load_default_theme()
        
        # Custom initialization
        self.initialize()
    
    @abstractmethod
    def initialize(self):
        """
        Custom initialization logic
        Override in subclasses
        """
        pass
    
    # ========================================================================
    # Component Management
    # ========================================================================
    
    def register_component(self, name: str, component_class: Type["Component"]):
        """
        Register a UI component
        
        Args:
            name: Component name
            component_class: Component class
        """
        self._components[name] = component_class
        self.logger.debug(f"Registered component: {name}")
    
    def create_component(
        self,
        component_type: str,
        data: Any = None,
        **kwargs
    ) -> MCPUIResource:
        """
        Create a UI component
        
        Args:
            component_type: Type of component to create
            data: Component data
            **kwargs: Additional component options
            
        Returns:
            MCPUIResource ready for response
        """
        # Get component class
        component_class = self._components.get(component_type)
        if not component_class:
            raise ValueError(f"Unknown component type: {component_type}")
        
        # Create component instance
        component = component_class(
            data=data,
            theme=self._themes.get(self.config.default_theme),
            **kwargs
        )
        
        # Validate security
        if not self.security.validate_content(component.render()):
            raise SecurityError(f"Component failed security validation: {component_type}")
        
        # Create resource
        resource = MCPUIResource(
            uri=self.protocol.create_resource_uri(component_type),
            mimeType=ResourceType.HTML,
            content=component.render(),
            metadata=MCPUIMetadata(
                service=self.config.name,
                component=component_type,
                rendering=component.rendering_mode,
                tags=component.tags
            )
        )
        
        # Validate protocol compliance
        self.protocol.validate_resource(resource)
        
        return resource
    
    def _register_default_components(self):
        """Register built-in components"""
        from ..components import (
            CardGrid,
            DataTable,
            Form,
            Chart,
            Alert,
            Loading
        )
        
        default_components = {
            "CardGrid": CardGrid,
            "DataTable": DataTable,
            "Form": Form,
            "Chart": Chart,
            "Alert": Alert,
            "Loading": Loading
        }
        
        for name, component_class in default_components.items():
            self.register_component(name, component_class)
    
    def _load_default_theme(self):
        """Load default theme"""
        from ..themes import DefaultTheme, DarkTheme
        
        self._themes["default"] = DefaultTheme()
        self._themes["dark"] = DarkTheme()
    
    # ========================================================================
    # Response Building
    # ========================================================================
    
    def build_response(
        self,
        data: Any = None,
        ui_resources: Optional[List[MCPUIResource]] = None,
        **kwargs
    ) -> MCPUIResponse:
        """
        Build MCP-UI Protocol response
        
        Args:
            data: Minimal data for LLM
            ui_resources: UI resources to include
            **kwargs: Additional response options
            
        Returns:
            Protocol-compliant response
        """
        response = MCPUIResponse(
            data=self.minimize_data(data) if data else None,
            expires_in=kwargs.get("expires_in", self.config.cache_ttl),
            session_id=kwargs.get("session_id"),
            correlation_id=kwargs.get("correlation_id")
        )
        
        # Add UI resources
        if ui_resources:
            for resource in ui_resources[:self.config.max_ui_resources]:
                response.add_resource(resource)
        
        # Add metrics
        if kwargs.get("include_metrics", False):
            response.metrics = self._collect_metrics()
        
        # Validate response
        self.protocol.validate_response(response)
        
        # Check token budget
        token_usage = response.calculate_token_usage()
        if not self.security.check_token_budget(token_usage):
            raise SecurityError(f"Response exceeds token budget: {token_usage}")
        
        return response
    
    def minimize_data(self, data: Any) -> Any:
        """
        Minimize data for token efficiency
        
        Args:
            data: Full data object
            
        Returns:
            Minimized data for LLM consumption
        """
        if isinstance(data, list):
            # For lists, return count and sample
            return {
                "count": len(data),
                "sample": data[:3] if len(data) > 3 else data
            }
        elif isinstance(data, dict):
            # For dicts, remove large fields
            minimized = {}
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 100:
                    minimized[key] = value[:100] + "..."
                elif isinstance(value, (list, dict)) and len(str(value)) > 200:
                    minimized[key] = f"<{type(value).__name__}>"
                else:
                    minimized[key] = value
            return minimized
        else:
            return data
    
    # ========================================================================
    # Request Handling
    # ========================================================================
    
    async def handle_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> MCPUIResponse:
        """
        Handle incoming request
        
        Args:
            method: HTTP method
            path: Request path
            params: Query parameters
            body: Request body
            headers: Request headers
            
        Returns:
            MCP-UI response
        """
        request_id = self._generate_request_id()
        self._active_requests[request_id] = datetime.now()
        
        try:
            # Security checks
            if not self.security.validate_request(method, path, headers):
                return create_error_response("Unauthorized", "AUTH_ERROR")
            
            # Rate limiting
            if not self.security.check_rate_limit(self._get_client_id(headers)):
                return create_error_response("Rate limit exceeded", "RATE_LIMIT")
            
            # Route request
            handler = self._get_handler(method, path)
            if not handler:
                return create_error_response("Not found", "NOT_FOUND")
            
            # Execute handler
            response = await handler(params=params, body=body, headers=headers)
            
            # Ensure response is MCP-UI compliant
            if not isinstance(response, MCPUIResponse):
                response = self.build_response(data=response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Request failed: {e}", exc_info=True)
            return create_error_response(str(e), "INTERNAL_ERROR")
        
        finally:
            del self._active_requests[request_id]
    
    def _get_handler(self, method: str, path: str):
        """Get request handler for path"""
        # Override in subclasses to implement routing
        handler_name = f"handle_{method.lower()}_{path.replace('/', '_')}"
        return getattr(self, handler_name, None)
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _get_client_id(self, headers: Optional[Dict[str, str]]) -> str:
        """Extract client ID from headers"""
        if not headers:
            return "anonymous"
        return headers.get("X-Client-Id", headers.get("X-Forwarded-For", "anonymous"))
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        return {
            "active_requests": len(self._active_requests),
            "cache_hit_rate": self.state.get_cache_stats().get("hit_rate", 0),
            "avg_response_time": self.state.get_avg_response_time(),
            "memory_usage": self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    
    # ========================================================================
    # Server Lifecycle
    # ========================================================================
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Run the server
        
        Args:
            host: Override config host
            port: Override config port
        """
        host = host or self.config.host
        port = port or self.config.port
        
        self.logger.info(f"Starting MCP Server on {host}:{port}")
        
        # Start server based on framework
        if self._detect_framework() == "fastapi":
            self._run_fastapi(host, port)
        elif self._detect_framework() == "flask":
            self._run_flask(host, port)
        else:
            self._run_standalone(host, port)
    
    def _detect_framework(self) -> str:
        """Detect web framework"""
        try:
            import fastapi
            return "fastapi"
        except ImportError:
            pass
        
        try:
            import flask
            return "flask"
        except ImportError:
            pass
        
        return "standalone"
    
    def _run_fastapi(self, host: str, port: int):
        """Run with FastAPI"""
        from ..server.fastapi import create_fastapi_app
        app = create_fastapi_app(self)
        
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    
    def _run_flask(self, host: str, port: int):
        """Run with Flask"""
        from ..server.flask import create_flask_app
        app = create_flask_app(self)
        app.run(host=host, port=port)
    
    def _run_standalone(self, host: str, port: int):
        """Run standalone server"""
        from ..server.standalone import StandaloneServer
        server = StandaloneServer(self)
        asyncio.run(server.run(host, port))
    
    async def shutdown(self):
        """Shutdown server gracefully"""
        self.logger.info("Shutting down MCP Server")
        
        # Wait for active requests
        max_wait = 30
        start = datetime.now()
        while self._active_requests and (datetime.now() - start).seconds < max_wait:
            await asyncio.sleep(0.1)
        
        # Force close remaining
        if self._active_requests:
            self.logger.warning(f"Force closing {len(self._active_requests)} requests")
        
        # Cleanup
        await self.state.close()
        await self.message_bus.close()
        
        self.logger.info("MCP Server shutdown complete")


# ============================================================================
# Security Error
# ============================================================================

class SecurityError(Exception):
    """Security validation error"""
    pass