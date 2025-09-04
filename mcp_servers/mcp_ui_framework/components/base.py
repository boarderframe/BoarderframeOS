"""
Base Component Class
Foundation for all UI components in MCP-UI Framework
"""

from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
import json
import hashlib


# ============================================================================
# Component Configuration
# ============================================================================

class ComponentConfig(BaseModel):
    """Base configuration for components"""
    id: Optional[str] = Field(None, description="Component ID")
    className: Optional[str] = Field(None, description="CSS class names")
    style: Optional[Dict[str, str]] = Field(default_factory=dict, description="Inline styles")
    attributes: Optional[Dict[str, str]] = Field(default_factory=dict, description="HTML attributes")
    interactive: bool = Field(default=True, description="Enable interactivity")
    responsive: bool = Field(default=True, description="Enable responsive design")
    animation: bool = Field(default=True, description="Enable animations")
    accessibility: bool = Field(default=True, description="Enable accessibility features")


# ============================================================================
# Base Component
# ============================================================================

class Component(ABC):
    """
    Abstract base class for all UI components
    
    Provides:
    - Consistent rendering interface
    - Theme support
    - Event handling
    - State management
    - Accessibility features
    """
    
    def __init__(
        self,
        data: Any = None,
        config: Optional[ComponentConfig] = None,
        theme: Optional["Theme"] = None,
        **kwargs
    ):
        """
        Initialize component
        
        Args:
            data: Component data
            config: Component configuration
            theme: Theme to apply
            **kwargs: Additional options
        """
        self.data = data
        self.config = config or ComponentConfig()
        self.theme = theme
        self.options = kwargs
        
        # Component metadata
        self.component_type = self.__class__.__name__
        self.component_id = self.config.id or self._generate_id()
        self.rendering_mode = "iframe_sandboxed"
        self.tags: List[str] = []
        
        # State
        self.state: Dict[str, Any] = {}
        self.props: Dict[str, Any] = {}
        
        # Events
        self.event_handlers: Dict[str, str] = {}
        
        # Initialize component
        self._initialize()
    
    def _initialize(self):
        """Initialize component (override in subclasses)"""
        pass
    
    def _generate_id(self) -> str:
        """Generate unique component ID"""
        data = f"{self.component_type}-{datetime.now().isoformat()}-{id(self)}"
        return hashlib.md5(data.encode()).hexdigest()[:8]
    
    @abstractmethod
    def render(self) -> str:
        """
        Render component to HTML
        
        Returns:
            Complete HTML string
        """
        pass
    
    def render_partial(self) -> str:
        """
        Render component content only (without wrapper)
        
        Returns:
            Partial HTML string
        """
        return self.render_content()
    
    @abstractmethod
    def render_content(self) -> str:
        """
        Render component content
        
        Returns:
            Content HTML string
        """
        pass
    
    # ========================================================================
    # HTML Generation Helpers
    # ========================================================================
    
    def get_base_html(self, content: str, include_scripts: bool = True) -> str:
        """
        Get base HTML structure
        
        Args:
            content: Component content
            include_scripts: Include JavaScript
            
        Returns:
            Complete HTML document
        """
        styles = self.get_styles()
        scripts = self.get_scripts() if include_scripts else ""
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.component_type}</title>
            <style>
                {self.get_base_styles()}
                {styles}
            </style>
        </head>
        <body>
            <div id="{self.component_id}" class="mcp-component {self.component_type.lower()}">
                {content}
            </div>
            {scripts}
        </body>
        </html>
        """
    
    def get_base_styles(self) -> str:
        """Get base component styles"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                         'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        .mcp-component {
            padding: 16px;
            min-height: 100vh;
        }
        
        /* Responsive utilities */
        @media (max-width: 768px) {
            .mcp-component {
                padding: 8px;
            }
        }
        
        /* Animation utilities */
        .fade-in {
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        /* Accessibility */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0,0,0,0);
            white-space: nowrap;
            border: 0;
        }
        
        :focus-visible {
            outline: 2px solid #007bff;
            outline-offset: 2px;
        }
        """
    
    def get_styles(self) -> str:
        """Get component-specific styles (override in subclasses)"""
        if self.theme:
            return self.theme.get_component_styles(self.component_type)
        return ""
    
    def get_scripts(self) -> str:
        """Get component JavaScript"""
        event_handlers = self.generate_event_handlers()
        state_management = self.generate_state_management()
        
        return f"""
        <script>
        (function() {{
            // Component state
            const state = {json.dumps(self.state)};
            const props = {json.dumps(self.props)};
            
            // State management
            {state_management}
            
            // Event handlers
            {event_handlers}
            
            // Intent system
            function sendIntent(type, data) {{
                window.dispatchEvent(new CustomEvent('mcp:intent', {{
                    detail: {{
                        type: type,
                        target: '{self.component_id}',
                        data: data,
                        timestamp: new Date().toISOString()
                    }}
                }}));
            }}
            
            // PostMessage communication
            function sendMessage(message) {{
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        source: 'mcp-component',
                        componentId: '{self.component_id}',
                        ...message
                    }}, '*');
                }}
            }}
            
            // Initialize component
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('Component initialized:', '{self.component_id}');
                sendMessage({{type: 'ready'}});
            }});
            
            // Expose API
            window.MCPComponent = {{
                id: '{self.component_id}',
                type: '{self.component_type}',
                state: state,
                props: props,
                sendIntent: sendIntent,
                sendMessage: sendMessage,
                getState: () => state,
                setState: (newState) => {{
                    Object.assign(state, newState);
                    sendMessage({{type: 'stateUpdate', state: state}});
                }}
            }};
        }})();
        </script>
        """
    
    def generate_event_handlers(self) -> str:
        """Generate event handler JavaScript"""
        handlers = []
        
        for event, handler in self.event_handlers.items():
            handlers.append(f"""
            document.addEventListener('{event}', function(e) {{
                {handler}
            }});
            """)
        
        return "\n".join(handlers)
    
    def generate_state_management(self) -> str:
        """Generate state management JavaScript"""
        return """
        function updateState(key, value) {
            state[key] = value;
            sendMessage({type: 'stateUpdate', key: key, value: value});
        }
        
        function getState(key) {
            return key ? state[key] : state;
        }
        """
    
    # ========================================================================
    # Event Handling
    # ========================================================================
    
    def on(self, event: str, handler: str):
        """
        Register event handler
        
        Args:
            event: Event name
            handler: JavaScript handler code
        """
        self.event_handlers[event] = handler
    
    def emit(self, event: str, data: Any = None) -> str:
        """
        Generate code to emit event
        
        Args:
            event: Event name
            data: Event data
            
        Returns:
            JavaScript code
        """
        data_json = json.dumps(data) if data else "{}"
        return f"sendIntent('{event}', {data_json});"
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def add_class(self, class_name: str):
        """Add CSS class"""
        if self.config.className:
            self.config.className += f" {class_name}"
        else:
            self.config.className = class_name
    
    def add_style(self, key: str, value: str):
        """Add inline style"""
        self.config.style[key] = value
    
    def set_attribute(self, key: str, value: str):
        """Set HTML attribute"""
        self.config.attributes[key] = value
    
    def get_attributes_string(self) -> str:
        """Get HTML attributes as string"""
        attrs = []
        
        if self.config.className:
            attrs.append(f'class="{self.config.className}"')
        
        if self.config.style:
            style_str = "; ".join([f"{k}: {v}" for k, v in self.config.style.items()])
            attrs.append(f'style="{style_str}"')
        
        for key, value in self.config.attributes.items():
            attrs.append(f'{key}="{value}"')
        
        return " ".join(attrs)
    
    def escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def format_number(self, value: Union[int, float], decimals: int = 2) -> str:
        """Format number for display"""
        if isinstance(value, int):
            return f"{value:,}"
        else:
            return f"{value:,.{decimals}f}"
    
    def format_currency(self, value: Union[int, float], symbol: str = "$") -> str:
        """Format currency value"""
        return f"{symbol}{self.format_number(value)}"
    
    def format_date(self, date: datetime, format: str = "%Y-%m-%d") -> str:
        """Format date for display"""
        return date.strftime(format)
    
    def truncate_text(self, text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix