"""
MCP-UI Embedding Protocol SDK - Python Implementation
Adapted from the TypeScript reference implementation
Version: 1.0.0

This module provides Python types and utilities for implementing the MCP-UI 
Embedding Protocol, enabling interactive UI components to be embedded within 
AI chat interfaces.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import json


PROTOCOL_VERSION = "1.0.0"


class HostMessageType(Enum):
    """Message types for Host → UI communication"""
    INIT = "init"
    UPDATE_CONTEXT = "update_context"
    THEME = "theme"
    AUTH_UPDATE = "auth_update"
    AUTH_REVOKE = "auth_revoke"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"


class UIMessageType(Enum):
    """Message types for UI → Host communication"""
    READY = "ready"
    ACTION = "action"
    ERROR = "error"
    RESIZE = "resize"
    REQUEST_PERMISSION = "request_permission"


class ErrorCode(Enum):
    """Error codes for UI → Host error messages"""
    PROTOCOL_ERROR = "protocol_error"
    AUTH_ERROR = "auth_error"
    CONTEXT_ERROR = "context_error"
    RENDER_ERROR = "render_error"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class User:
    """Basic user information"""
    id: str
    additional_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_properties is None:
            self.additional_properties = {}


@dataclass
class Auth:
    """Authentication information"""
    token: str
    jwks_url: str
    additional_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_properties is None:
            self.additional_properties = {}


@dataclass
class ThemeSettings:
    """Theme settings for UI customization"""
    mode: Optional[str] = None  # "light" or "dark"
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    border_radius: Optional[str] = None
    additional_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_properties is None:
            self.additional_properties = {}


@dataclass
class UIRegistrationPayload:
    """Interface for UI Registration Payload as defined in the spec"""
    ui_name: str
    ui_url_template: str
    description: str
    capabilities: List[str]
    permissions: Dict[str, List[str]]  # {"required_scopes": [...], "optional_scopes": [...]}
    protocol_support: Dict[str, str]  # {"min_version": "1.0.0", "target_version": "1.0.0"}
    tool_association: Optional[str] = None
    data_type_handled: Optional[str] = None


class MCPUIMessage:
    """Base class for MCP-UI protocol messages"""
    
    def __init__(self, message_type: Union[HostMessageType, UIMessageType], **kwargs):
        self.type = message_type.value if isinstance(message_type, Enum) else message_type
        self.data = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization"""
        result = {"type": self.type}
        result.update(self.data)
        return result
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPUIMessage':
        """Create message from dictionary"""
        message_type = data.pop("type")
        return cls(message_type, **data)


class InitMessage(MCPUIMessage):
    """Init message from Host to UI"""
    
    def __init__(self, protocol_version: str = PROTOCOL_VERSION, 
                 user: Optional[User] = None, auth: Optional[Auth] = None,
                 context: Optional[Dict[str, Any]] = None, 
                 theme_settings: Optional[ThemeSettings] = None):
        super().__init__(
            HostMessageType.INIT,
            protocol_version=protocol_version,
            user=user.__dict__ if user else None,
            auth=auth.__dict__ if auth else None,
            context=context,
            theme_settings=theme_settings.__dict__ if theme_settings else None
        )


class UpdateContextMessage(MCPUIMessage):
    """Update context message from Host to UI"""
    
    def __init__(self, context: Optional[Dict[str, Any]]):
        super().__init__(HostMessageType.UPDATE_CONTEXT, context=context)


class ThemeMessage(MCPUIMessage):
    """Theme message from Host to UI"""
    
    def __init__(self, theme_settings: ThemeSettings):
        super().__init__(HostMessageType.THEME, theme_settings=theme_settings.__dict__)


class ActionMessage(MCPUIMessage):
    """Action message from UI to Host"""
    
    def __init__(self, action_name: str, payload: Optional[Dict[str, Any]] = None):
        super().__init__(UIMessageType.ACTION, action_name=action_name, payload=payload)


class ErrorMessage(MCPUIMessage):
    """Error message from UI to Host"""
    
    def __init__(self, code: Union[ErrorCode, str], message: str):
        error_code = code.value if isinstance(code, ErrorCode) else code
        super().__init__(UIMessageType.ERROR, code=error_code, message=message)


class ResizeMessage(MCPUIMessage):
    """Resize message from UI to Host"""
    
    def __init__(self, width: Optional[str] = None, height: Optional[str] = None):
        super().__init__(UIMessageType.RESIZE, width=width, height=height)


class RequestPermissionMessage(MCPUIMessage):
    """Request permission message from UI to Host"""
    
    def __init__(self, scope: str, reasoning: Optional[str] = None):
        super().__init__(UIMessageType.REQUEST_PERMISSION, scope=scope, reasoning=reasoning)


class MCPUIGenerator:
    """Utility class for generating MCP-UI compatible artifacts and responses"""
    
    @staticmethod
    def create_ui_artifact(content: str, ui_type: str = "html", 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a UI artifact that can be embedded in chat interfaces
        
        Args:
            content: HTML/JavaScript/CSS content for the UI
            ui_type: Type of UI content (html, react, vue, etc.)
            metadata: Additional metadata for the UI
        
        Returns:
            Dictionary containing the UI artifact specification
        """
        artifact = {
            "type": "ui_artifact",
            "ui_type": ui_type,
            "content": content,
            "protocol_version": PROTOCOL_VERSION,
            "metadata": metadata or {}
        }
        
        # Add default metadata
        if "capabilities" not in artifact["metadata"]:
            artifact["metadata"]["capabilities"] = ["interactive", "responsive"]
        
        if "permissions" not in artifact["metadata"]:
            artifact["metadata"]["permissions"] = {
                "required_scopes": [],
                "optional_scopes": []
            }
        
        return artifact
    
    @staticmethod
    def create_product_card_ui(product_data: Dict[str, Any], 
                               theme: Optional[ThemeSettings] = None) -> Dict[str, Any]:
        """
        Create a product card UI artifact for e-commerce data
        
        Args:
            product_data: Product information (name, price, image, etc.)
            theme: Theme settings for styling
        
        Returns:
            UI artifact with embedded product card
        """
        theme_vars = ""
        if theme:
            theme_vars = f"""
                :root {{
                    --primary-color: {theme.primary_color or '#007bff'};
                    --secondary-color: {theme.secondary_color or '#6c757d'};
                    --font-family: {theme.font_family or 'system-ui, -apple-system, sans-serif'};
                    --border-radius: {theme.border_radius or '8px'};
                }}
                .product-card {{
                    background: {('var(--bg-dark)' if theme.mode == 'dark' else 'white')};
                    color: {('white' if theme.mode == 'dark' else 'black')};
                }}
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                {theme_vars}
                .product-card {{
                    font-family: var(--font-family, system-ui);
                    max-width: 400px;
                    border-radius: var(--border-radius, 8px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    overflow: hidden;
                    margin: 16px auto;
                    background: white;
                }}
                .product-image {{
                    width: 100%;
                    height: 200px;
                    object-fit: cover;
                    background: #f8f9fa;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #6c757d;
                }}
                .product-info {{
                    padding: 16px;
                }}
                .product-name {{
                    font-size: 18px;
                    font-weight: 600;
                    margin: 0 0 8px 0;
                    color: var(--primary-color, #007bff);
                }}
                .product-price {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #28a745;
                    margin: 8px 0;
                }}
                .product-description {{
                    color: #6c757d;
                    font-size: 14px;
                    line-height: 1.4;
                    margin: 8px 0;
                }}
                .product-actions {{
                    display: flex;
                    gap: 8px;
                    margin-top: 16px;
                }}
                .btn {{
                    padding: 8px 16px;
                    border: none;
                    border-radius: var(--border-radius, 4px);
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.2s;
                }}
                .btn-primary {{
                    background: var(--primary-color, #007bff);
                    color: white;
                }}
                .btn-secondary {{
                    background: var(--secondary-color, #6c757d);
                    color: white;
                }}
                .btn:hover {{
                    opacity: 0.9;
                    transform: translateY(-1px);
                }}
            </style>
        </head>
        <body>
            <div class="product-card">
                <div class="product-image">
                    {f'<img src="{product_data.get("image", "")}" alt="{product_data.get("name", "Product")}" style="width:100%;height:100%;object-fit:cover;">' if product_data.get("image") else f'<span>📦 {product_data.get("name", "Product")}</span>'}
                </div>
                <div class="product-info">
                    <h3 class="product-name">{product_data.get('name', 'Unknown Product')}</h3>
                    <div class="product-price">${product_data.get('price', '0.00')}</div>
                    <p class="product-description">{product_data.get('description', 'No description available.')}</p>
                    <div class="product-actions">
                        <button class="btn btn-primary" onclick="addToCart()">Add to Cart</button>
                        <button class="btn btn-secondary" onclick="viewDetails()">View Details</button>
                    </div>
                </div>
            </div>
            
            <script>
                function addToCart() {{
                    // Send action to parent (MCP host)
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: 'add_to_cart',
                        payload: {{
                            product_id: '{product_data.get("id", "")}',
                            product_name: '{product_data.get("name", "")}',
                            price: '{product_data.get("price", "0.00")}'
                        }}
                    }}, '*');
                }}
                
                function viewDetails() {{
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: 'view_product_details',
                        payload: {{
                            product_id: '{product_data.get("id", "")}'
                        }}
                    }}, '*');
                }}
                
                // Notify parent that UI is ready
                window.addEventListener('load', function() {{
                    window.parent.postMessage({{
                        type: 'ready'
                    }}, '*');
                }});
            </script>
        </body>
        </html>
        """
        
        return MCPUIGenerator.create_ui_artifact(
            content=html_content,
            ui_type="html",
            metadata={
                "capabilities": ["interactive", "responsive", "product_display"],
                "data_type_handled": "product_info",
                "permissions": {
                    "required_scopes": ["read:product_basic"],
                    "optional_scopes": ["write:cart", "read:user_preferences"]
                }
            }
        )
    
    @staticmethod
    def create_shopping_list_ui(items: List[Dict[str, Any]], 
                               theme: Optional[ThemeSettings] = None) -> Dict[str, Any]:
        """
        Create a shopping list UI artifact
        
        Args:
            items: List of shopping list items
            theme: Theme settings for styling
        
        Returns:
            UI artifact with interactive shopping list
        """
        theme_vars = ""
        if theme:
            theme_vars = f"""
                :root {{
                    --primary-color: {theme.primary_color or '#007bff'};
                    --font-family: {theme.font_family or 'system-ui, -apple-system, sans-serif'};
                    --border-radius: {theme.border_radius or '4px'};
                }}
            """
        
        items_html = ""
        for item in items:
            checked = "checked" if item.get("completed", False) else ""
            items_html += f"""
                <div class="list-item">
                    <input type="checkbox" {checked} onchange="toggleItem('{item.get('id', '')}')">
                    <span class="item-name {'completed' if item.get('completed') else ''}">{item.get('name', 'Unknown Item')}</span>
                    <span class="item-quantity">{item.get('quantity', 1)}</span>
                </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                {theme_vars}
                body {{
                    font-family: var(--font-family, system-ui);
                    margin: 0;
                    padding: 16px;
                    background: #f8f9fa;
                }}
                .shopping-list {{
                    background: white;
                    border-radius: var(--border-radius, 8px);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .list-header {{
                    background: var(--primary-color, #007bff);
                    color: white;
                    padding: 16px;
                    font-size: 18px;
                    font-weight: 600;
                }}
                .list-item {{
                    display: flex;
                    align-items: center;
                    padding: 12px 16px;
                    border-bottom: 1px solid #eee;
                    gap: 12px;
                }}
                .list-item:hover {{
                    background: #f8f9fa;
                }}
                .item-name {{
                    flex: 1;
                    font-size: 14px;
                }}
                .item-name.completed {{
                    text-decoration: line-through;
                    opacity: 0.6;
                }}
                .item-quantity {{
                    background: #e9ecef;
                    padding: 4px 8px;
                    border-radius: var(--border-radius, 4px);
                    font-size: 12px;
                    font-weight: 500;
                }}
                .list-actions {{
                    padding: 16px;
                    text-align: center;
                }}
                .btn {{
                    background: var(--primary-color, #007bff);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: var(--border-radius, 4px);
                    cursor: pointer;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="shopping-list">
                <div class="list-header">Shopping List ({len(items)} items)</div>
                {items_html}
                <div class="list-actions">
                    <button class="btn" onclick="addItem()">Add Item</button>
                </div>
            </div>
            
            <script>
                function toggleItem(itemId) {{
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: 'toggle_list_item',
                        payload: {{ item_id: itemId }}
                    }}, '*');
                }}
                
                function addItem() {{
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: 'add_list_item',
                        payload: {{}}
                    }}, '*');
                }}
                
                window.addEventListener('load', function() {{
                    window.parent.postMessage({{ type: 'ready' }}, '*');
                }});
            </script>
        </body>
        </html>
        """
        
        return MCPUIGenerator.create_ui_artifact(
            content=html_content,
            ui_type="html",
            metadata={
                "capabilities": ["interactive", "responsive", "list_management"],
                "data_type_handled": "shopping_list",
                "permissions": {
                    "required_scopes": ["read:shopping_list"],
                    "optional_scopes": ["write:shopping_list", "manage:list_items"]
                }
            }
        )


def register_ui_with_mcp_server(ui_registration: UIRegistrationPayload) -> Dict[str, Any]:
    """
    Register a UI component with an MCP server
    
    Args:
        ui_registration: UI registration payload
    
    Returns:
        Registration response for MCP server
    """
    return {
        "ui_registration": {
            "ui_name": ui_registration.ui_name,
            "ui_url_template": ui_registration.ui_url_template,
            "description": ui_registration.description,
            "capabilities": ui_registration.capabilities,
            "tool_association": ui_registration.tool_association,
            "data_type_handled": ui_registration.data_type_handled,
            "permissions": ui_registration.permissions,
            "protocol_support": ui_registration.protocol_support,
        },
        "protocol_version": PROTOCOL_VERSION,
        "timestamp": None  # Should be set by the server
    }