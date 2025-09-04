"""
MCP-UI Protocol Implementation
Core protocol definitions and validators for MCP-UI Framework
"""

from typing import Dict, List, Any, Optional, Union, Literal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator
import hashlib
import json


# ============================================================================
# Protocol Enums
# ============================================================================

class ResourceType(str, Enum):
    """MCP-UI Resource MIME types"""
    HTML = "text/html"
    URI_LIST = "text/uri-list"
    REMOTE_DOM = "application/vnd.mcp-ui.remote-dom"
    JSON = "application/json"
    MARKDOWN = "text/markdown"
    
    @classmethod
    def from_extension(cls, ext: str) -> "ResourceType":
        """Determine resource type from file extension"""
        mapping = {
            ".html": cls.HTML,
            ".htm": cls.HTML,
            ".url": cls.URI_LIST,
            ".json": cls.JSON,
            ".md": cls.MARKDOWN
        }
        return mapping.get(ext.lower(), cls.HTML)


class IntentType(str, Enum):
    """Standard MCP-UI Intent types"""
    ACTION = "mcp:action"
    SELECT = "mcp:select"
    SUBMIT = "mcp:submit"
    NAVIGATE = "mcp:navigate"
    UPDATE = "mcp:update"
    CANCEL = "mcp:cancel"
    REFRESH = "mcp:refresh"
    CUSTOM = "mcp:custom"


class RenderingMode(str, Enum):
    """UI rendering modes"""
    IFRAME_SANDBOXED = "iframe_sandboxed"
    IFRAME_REMOTE = "iframe_remote"
    INLINE = "inline"
    MODAL = "modal"
    FULLSCREEN = "fullscreen"


# ============================================================================
# Core Protocol Models
# ============================================================================

class MCPUIMetadata(BaseModel):
    """Metadata for MCP-UI resources"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: str = Field(default="1.0.0")
    service: str = Field(..., description="Service that created this resource")
    component: Optional[str] = Field(None, description="Component name")
    rendering: RenderingMode = Field(default=RenderingMode.IFRAME_SANDBOXED)
    cacheable: bool = Field(default=True)
    ttl: Optional[int] = Field(default=3600, description="Time to live in seconds")
    content_size: Optional[int] = Field(None, description="Size of content in bytes")
    checksum: Optional[str] = Field(None, description="Content checksum")
    tags: List[str] = Field(default_factory=list)
    custom: Dict[str, Any] = Field(default_factory=dict)


class MCPUIResource(BaseModel):
    """
    MCP-UI Protocol Resource
    Standard compliant resource definition for UI components
    """
    uri: str = Field(..., description="Resource URI with ui:// scheme")
    mimeType: ResourceType = Field(..., description="MIME type of the resource")
    content: str = Field(..., description="Resource content")
    metadata: MCPUIMetadata = Field(default_factory=MCPUIMetadata)
    
    @validator("uri")
    def validate_uri(cls, v):
        """Ensure URI follows ui:// scheme"""
        if not v.startswith("ui://"):
            raise ValueError(f"URI must start with 'ui://' scheme, got: {v}")
        return v
    
    @validator("content")
    def validate_content_size(cls, v, values):
        """Track content size in metadata"""
        if "metadata" in values and values["metadata"]:
            values["metadata"].content_size = len(v)
        return v
    
    def calculate_checksum(self) -> str:
        """Calculate content checksum for caching"""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]
    
    def to_minimal_dict(self) -> Dict[str, Any]:
        """Convert to minimal dictionary for token efficiency"""
        return {
            "uri": self.uri,
            "mimeType": self.mimeType.value if isinstance(self.mimeType, Enum) else self.mimeType,
            "content": self.content,
            "metadata": {
                "component": self.metadata.component,
                "rendering": self.metadata.rendering.value,
                "ttl": self.metadata.ttl
            }
        }


class MCPUIIntent(BaseModel):
    """
    MCP-UI Intent
    Represents user interactions from UI components
    """
    type: IntentType = Field(..., description="Intent type")
    target: str = Field(..., description="Target component URI")
    action: str = Field(..., description="Action to perform")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Intent payload")
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    def to_event(self) -> Dict[str, Any]:
        """Convert to JavaScript event format"""
        return {
            "type": self.type.value,
            "detail": {
                "target": self.target,
                "action": self.action,
                "data": self.data,
                "timestamp": self.timestamp.isoformat()
            }
        }


class MCPUIResponse(BaseModel):
    """
    MCP-UI Protocol Response
    Standard format for API responses with UI resources
    """
    # Core response data (minimal for token efficiency)
    data: Optional[Any] = Field(None, description="Minimal data for LLM")
    count: Optional[int] = Field(None, description="Result count")
    
    # UI resources
    ui_resources: Dict[str, MCPUIResource] = Field(
        default_factory=dict,
        description="UI resources keyed by URI"
    )
    
    # Response metadata
    expires_in: int = Field(default=3600, description="TTL in seconds")
    session_id: Optional[str] = Field(None, description="Session identifier")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    
    # Performance metrics
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Performance metrics"
    )
    
    def add_resource(self, resource: MCPUIResource) -> None:
        """Add a UI resource to the response"""
        self.ui_resources[resource.uri] = resource
    
    def to_minimal_dict(self) -> Dict[str, Any]:
        """Convert to minimal dictionary for token efficiency"""
        result = {}
        
        if self.data is not None:
            result["data"] = self.data
        if self.count is not None:
            result["count"] = self.count
        
        if self.ui_resources:
            result["ui_resources"] = {
                uri: resource.to_minimal_dict()
                for uri, resource in self.ui_resources.items()
            }
        
        result["expires_in"] = self.expires_in
        
        return result
    
    def calculate_token_usage(self) -> int:
        """Estimate token usage for this response"""
        # Rough estimation: 1 token ≈ 4 characters
        json_str = json.dumps(self.to_minimal_dict())
        return len(json_str) // 4


# ============================================================================
# Protocol Manager
# ============================================================================

class MCPUIProtocol:
    """
    MCP-UI Protocol Manager
    Handles protocol compliance and validation
    """
    
    VERSION = "1.0.0"
    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_RESOURCES_PER_RESPONSE = 10
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize protocol manager
        
        Args:
            strict_mode: Enable strict protocol validation
        """
        self.strict_mode = strict_mode
    
    def validate_resource(self, resource: MCPUIResource) -> bool:
        """
        Validate a UI resource for protocol compliance
        
        Args:
            resource: Resource to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails in strict mode
        """
        errors = []
        
        # Check URI scheme
        if not resource.uri.startswith("ui://"):
            errors.append(f"Invalid URI scheme: {resource.uri}")
        
        # Check content size
        content_size = len(resource.content)
        if content_size > self.MAX_CONTENT_SIZE:
            errors.append(f"Content too large: {content_size} bytes")
        
        # Check MIME type
        if resource.mimeType not in ResourceType:
            errors.append(f"Invalid MIME type: {resource.mimeType}")
        
        # Validate HTML content
        if resource.mimeType == ResourceType.HTML:
            if not self._validate_html_content(resource.content):
                errors.append("Invalid HTML content")
        
        if errors and self.strict_mode:
            raise ValueError(f"Resource validation failed: {'; '.join(errors)}")
        
        return len(errors) == 0
    
    def validate_response(self, response: MCPUIResponse) -> bool:
        """
        Validate a complete MCP-UI response
        
        Args:
            response: Response to validate
            
        Returns:
            True if valid
        """
        # Check resource count
        if len(response.ui_resources) > self.MAX_RESOURCES_PER_RESPONSE:
            if self.strict_mode:
                raise ValueError(
                    f"Too many resources: {len(response.ui_resources)} "
                    f"(max: {self.MAX_RESOURCES_PER_RESPONSE})"
                )
            return False
        
        # Validate each resource
        for uri, resource in response.ui_resources.items():
            if uri != resource.uri:
                if self.strict_mode:
                    raise ValueError(f"URI mismatch: {uri} != {resource.uri}")
                return False
            
            if not self.validate_resource(resource):
                return False
        
        return True
    
    def create_resource_uri(self, component: str, identifier: str = None) -> str:
        """
        Create a protocol-compliant resource URI
        
        Args:
            component: Component name
            identifier: Optional unique identifier
            
        Returns:
            Protocol-compliant URI
        """
        if identifier:
            return f"ui://component/{component}/{identifier}"
        else:
            # Generate deterministic ID from component name
            hash_id = hashlib.md5(f"{component}-{datetime.now().isoformat()}".encode()).hexdigest()[:8]
            return f"ui://component/{component}/{hash_id}"
    
    def _validate_html_content(self, content: str) -> bool:
        """Basic HTML validation"""
        # Check for basic HTML structure
        required_tags = ["<html", "<head", "<body"]
        content_lower = content.lower()
        
        for tag in required_tags:
            if tag not in content_lower:
                return False
        
        # Check for potential XSS vectors
        dangerous_patterns = [
            "javascript:",
            "onerror=",
            "onload=",
            "<script",
            "eval(",
            "document.write"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                # Allow safe event handlers with proper sandboxing
                if pattern.startswith("on") and "dispatchEvent" in content:
                    continue
                return False
        
        return True
    
    def sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML content for safe rendering
        
        Args:
            html: Raw HTML content
            
        Returns:
            Sanitized HTML
        """
        # Basic sanitization (in production, use a proper library like bleach)
        replacements = {
            "<script": "&lt;script",
            "</script": "&lt;/script",
            "javascript:": "javascript&#58;",
            "onerror": "data-error",
            "onload": "data-load"
        }
        
        sanitized = html
        for pattern, replacement in replacements.items():
            sanitized = sanitized.replace(pattern, replacement)
        
        return sanitized


# ============================================================================
# Protocol Utilities
# ============================================================================

def create_error_response(
    error: str,
    code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None
) -> MCPUIResponse:
    """Create a standard error response"""
    error_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: system-ui, -apple-system, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: #f8f9fa;
            }}
            .error {{
                background: white;
                border: 1px solid #dc3545;
                border-radius: 8px;
                padding: 24px;
                max-width: 500px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .error-title {{
                color: #dc3545;
                margin: 0 0 8px 0;
                font-size: 18px;
                font-weight: 600;
            }}
            .error-message {{
                color: #495057;
                margin: 0 0 16px 0;
            }}
            .error-code {{
                font-family: monospace;
                background: #f8f9fa;
                padding: 4px 8px;
                border-radius: 4px;
                color: #6c757d;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="error">
            <h2 class="error-title">Error Occurred</h2>
            <p class="error-message">{error}</p>
            <span class="error-code">Code: {code}</span>
        </div>
    </body>
    </html>
    """
    
    resource = MCPUIResource(
        uri="ui://component/error/display",
        mimeType=ResourceType.HTML,
        content=error_html,
        metadata=MCPUIMetadata(
            service="mcp-ui-framework",
            component="error",
            cacheable=False
        )
    )
    
    response = MCPUIResponse(
        data={"error": error, "code": code, "details": details},
        ui_resources={resource.uri: resource},
        expires_in=0
    )
    
    return response


def create_loading_response(message: str = "Loading...") -> MCPUIResponse:
    """Create a loading state response"""
    loading_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            body {{
                font-family: system-ui, -apple-system, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: #f8f9fa;
            }}
            .loader {{
                text-align: center;
            }}
            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #007bff;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 16px;
            }}
            .message {{
                color: #6c757d;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="loader">
            <div class="spinner"></div>
            <div class="message">{message}</div>
        </div>
    </body>
    </html>
    """
    
    resource = MCPUIResource(
        uri="ui://component/loading/display",
        mimeType=ResourceType.HTML,
        content=loading_html,
        metadata=MCPUIMetadata(
            service="mcp-ui-framework",
            component="loading",
            cacheable=False
        )
    )
    
    response = MCPUIResponse(
        data={"loading": True, "message": message},
        ui_resources={resource.uri: resource},
        expires_in=60
    )
    
    return response