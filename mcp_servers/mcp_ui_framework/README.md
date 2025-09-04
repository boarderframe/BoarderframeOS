# MCP-UI Framework

## A Comprehensive, Reusable UI Framework for MCP Servers

The MCP-UI Framework provides a complete, production-ready infrastructure for building MCP servers with rich interactive UI capabilities. This framework follows the MCP-UI Protocol specification and enables 90-95% token reduction while delivering rich user experiences.

## Architecture Overview

```
mcp_ui_framework/
├── core/                    # Core framework infrastructure
│   ├── __init__.py
│   ├── base_server.py      # Base MCP server with UI capabilities
│   ├── protocol.py         # MCP-UI Protocol implementation
│   ├── communication.py    # PostMessage infrastructure
│   ├── security.py         # Authentication & security
│   └── state.py           # State management patterns
│
├── components/             # Reusable UI component library
│   ├── __init__.py
│   ├── base.py           # Base component class
│   ├── cards.py          # Card components
│   ├── tables.py         # Data table components
│   ├── forms.py          # Form components
│   ├── charts.py         # Chart/visualization components
│   └── widgets.py        # Interactive widgets
│
├── themes/                # Theme system
│   ├── __init__.py
│   ├── base_theme.py     # Base theme class
│   ├── default.py        # Default theme
│   ├── dark.py          # Dark theme
│   └── corporate.py     # Corporate branding theme
│
├── server/               # Server integration patterns
│   ├── __init__.py
│   ├── fastapi.py       # FastAPI integration
│   ├── flask.py         # Flask integration
│   ├── websocket.py     # WebSocket support
│   └── sse.py          # Server-Sent Events
│
├── client/              # Client-side libraries
│   ├── __init__.py
│   ├── renderer.py     # UI rendering engine
│   ├── messenger.py    # PostMessage handler
│   ├── state.js       # Client state management
│   └── intents.js     # Intent system
│
├── plugins/            # Plugin system
│   ├── __init__.py
│   ├── base_plugin.py # Base plugin interface
│   ├── auth/          # Authentication plugins
│   ├── storage/       # Storage plugins
│   └── apis/          # API integration plugins
│
├── testing/           # Testing framework
│   ├── __init__.py
│   ├── fixtures.py   # Test fixtures
│   ├── mocks.py     # Mock components
│   └── validators.py # Protocol validators
│
└── examples/         # Example implementations
    ├── simple_server.py
    ├── ecommerce_server.py
    ├── dashboard_server.py
    └── templates/
```

## Key Features

### 1. **Protocol-First Design**
- Full MCP-UI Protocol compliance
- Automatic protocol validation
- Built-in error handling
- Token optimization strategies

### 2. **Component System**
- Reusable, composable components
- Automatic responsive design
- Theme inheritance
- Accessibility built-in

### 3. **Security Framework**
- Sandboxed iframe execution
- Content Security Policy (CSP)
- XSS protection
- Rate limiting & token budgets

### 4. **State Management**
- Server-side state persistence
- Client-side state synchronization
- Intent-based communication
- Event sourcing support

### 5. **Developer Experience**
- Type-safe interfaces
- Hot reload support
- Comprehensive documentation
- CLI tools for scaffolding

## Quick Start

```python
from mcp_ui_framework import MCPServer, Component, Theme

# Create your server
class MyMCPServer(MCPServer):
    def __init__(self):
        super().__init__(
            name="my-server",
            theme=Theme.default(),
            security_config={
                "max_token_budget": 10000,
                "rate_limit": 60
            }
        )
    
    async def search_products(self, query: str):
        # Your business logic
        products = await fetch_products(query)
        
        # Create UI component
        component = self.create_component(
            "ProductGrid",
            data=products,
            template="grid",
            interactive=True
        )
        
        # Return MCP-UI response
        return self.build_response(
            data=self.minimize_data(products),
            ui_resources=[component]
        )

# Run the server
server = MyMCPServer()
server.run(host="0.0.0.0", port=8000)
```

## Installation

```bash
pip install mcp-ui-framework

# Or from source
git clone https://github.com/your-org/mcp-ui-framework
cd mcp-ui-framework
pip install -e .
```

## Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Component Library](docs/components.md)
- [Theme Development](docs/themes.md)
- [Security Best Practices](docs/security.md)
- [API Reference](docs/api-reference.md)

## License

MIT License - See LICENSE file for details