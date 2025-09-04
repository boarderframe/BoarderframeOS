# MCP-UI Framework Architecture

## Comprehensive, Reusable UI Framework for MCP Servers

### Executive Summary

The MCP-UI Framework is a production-ready, scalable architecture for building MCP servers with rich interactive UI capabilities. It provides a complete infrastructure following the MCP-UI Protocol specification, enabling 90-95% token reduction while delivering rich user experiences through sandboxed iframe rendering.

## 1. Core Framework Architecture

### 1.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (MCP Servers: Kroger, Playwright, Filesystem, Custom)      │
├─────────────────────────────────────────────────────────────┤
│                    Component Layer                           │
│  (Cards, Tables, Forms, Charts, Widgets)                    │
├─────────────────────────────────────────────────────────────┤
│                     Framework Core                           │
│  (Protocol, Security, State, Communication)                  │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                       │
│  (FastAPI, WebSocket, Storage, Cache)                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Core Modules

#### Protocol Module (`core/protocol.py`)
```python
class MCPUIProtocol:
    """Handles MCP-UI Protocol compliance"""
    - Resource validation
    - URI scheme management (ui://)
    - MIME type handling
    - Token optimization
    - Protocol versioning
```

#### Security Module (`core/security.py`)
```python
class SecurityManager:
    """Central security management"""
    - Authentication (Bearer, API Key, OAuth2)
    - Authorization & ACL
    - Rate limiting (token bucket)
    - Content validation & sanitization
    - Token budget management
    - CORS & CSP headers
```

#### State Module (`core/state.py`)
```python
class StateManager:
    """Server-side state management"""
    - Persistent storage (memory/file/redis)
    - Event sourcing
    - State snapshots
    - Cache management
    - Client synchronization
```

#### Communication Module (`core/communication.py`)
```python
class MessageBus:
    """Component communication infrastructure"""
    - PostMessage handling
    - Event emitter pattern
    - Pub/sub messaging
    - Intent routing
    - WebSocket support
```

### 1.3 Base Server Class

```python
class MCPServer(ABC):
    """Base class for all MCP servers"""
    
    def __init__(self, config: MCPServerConfig):
        self.protocol = MCPUIProtocol()
        self.security = SecurityManager()
        self.state = StateManager()
        self.message_bus = MessageBus()
    
    @abstractmethod
    async def handle_request(self, request: Request) -> MCPUIResponse:
        """Handle incoming requests with protocol compliance"""
    
    def create_component(self, type: str, data: Any) -> MCPUIResource:
        """Create UI component with theme and security"""
    
    def build_response(self, data: Any, ui_resources: List) -> MCPUIResponse:
        """Build protocol-compliant response"""
```

## 2. Component Library Structure

### 2.1 Component Hierarchy

```
Component (Abstract Base)
├── DataComponent
│   ├── CardGrid
│   ├── DataTable
│   └── Chart
├── FormComponent
│   ├── Form
│   ├── SearchBox
│   └── FilterPanel
└── WidgetComponent
    ├── Alert
    ├── Modal
    ├── Tabs
    └── Accordion
```

### 2.2 Component Interface

```python
class Component(ABC):
    """Base component interface"""
    
    @abstractmethod
    def render(self) -> str:
        """Render component to HTML"""
    
    def get_styles(self) -> str:
        """Get component CSS"""
    
    def get_scripts(self) -> str:
        """Get component JavaScript"""
    
    def emit(self, event: str, data: Any):
        """Emit component event"""
```

### 2.3 Reusable Components

#### Product Card Grid
```python
class ProductCardGrid(Component):
    """E-commerce product display"""
    - Responsive grid layout
    - Image lazy loading
    - Price formatting
    - Add to cart actions
    - Availability indicators
```

#### Data Table
```python
class DataTable(Component):
    """Sortable, filterable data table"""
    - Column sorting
    - Pagination
    - Search/filter
    - Row selection
    - Export capabilities
```

#### Interactive Form
```python
class Form(Component):
    """Dynamic form with validation"""
    - Field validation
    - Error handling
    - File uploads
    - Multi-step forms
    - Conditional fields
```

## 3. Theme System

### 3.1 Theme Architecture

```python
class Theme:
    """Base theme class"""
    
    colors: ColorPalette
    typography: Typography
    spacing: SpacingScale
    components: ComponentStyles
    
    def get_component_styles(self, component: str) -> str:
        """Get themed styles for component"""
```

### 3.2 Built-in Themes

- **Default Theme**: Clean, modern design
- **Dark Theme**: Dark mode support
- **Corporate Theme**: Professional branding
- **Compact Theme**: Information-dense layouts

### 3.3 Theme Inheritance

```python
class CustomTheme(DefaultTheme):
    """Custom theme extending default"""
    
    def __init__(self):
        super().__init__()
        self.colors.primary = "#007bff"
        self.colors.secondary = "#6c757d"
```

## 4. Server Integration Patterns

### 4.1 FastAPI Integration

```python
from mcp_ui_framework import MCPServer
from fastapi import FastAPI

class MyMCPServer(MCPServer):
    def initialize(self):
        # Custom initialization
        pass

server = MyMCPServer(config)
app = FastAPI()

@app.get("/search")
async def search(query: str):
    return await server.handle_request(
        method="GET",
        path="/search",
        params={"query": query}
    )
```

### 4.2 Plugin System

```python
class MCPPlugin(ABC):
    """Base plugin interface"""
    
    @abstractmethod
    async def initialize(self, server: MCPServer):
        """Initialize plugin"""
    
    @abstractmethod
    async def handle_request(self, request: Request) -> Optional[Response]:
        """Handle plugin-specific requests"""
```

#### API Integration Plugins
- **Kroger API Plugin**: Grocery product search
- **OpenAI Plugin**: AI model integration
- **Database Plugin**: Direct DB queries
- **Cache Plugin**: Redis/Memcached support

### 4.3 Middleware Chain

```python
class MCPMiddleware:
    """Request/Response middleware"""
    
    async def process_request(self, request: Request) -> Request:
        """Pre-process requests"""
    
    async def process_response(self, response: Response) -> Response:
        """Post-process responses"""
```

## 5. Communication Infrastructure

### 5.1 PostMessage Protocol

```javascript
// Client-side communication
window.addEventListener('message', (event) => {
    if (event.data.source === 'mcp-component') {
        handleComponentMessage(event.data);
    }
});

// Send intent to server
function sendIntent(type, data) {
    window.parent.postMessage({
        type: 'mcp:intent',
        target: componentId,
        data: data
    }, '*');
}
```

### 5.2 WebSocket Support

```python
class WebSocketHandler:
    """Real-time communication"""
    
    async def connect(self, websocket: WebSocket):
        """Handle new connection"""
    
    async def receive(self, message: str):
        """Handle incoming message"""
    
    async def broadcast(self, message: str):
        """Broadcast to all clients"""
```

### 5.3 Server-Sent Events

```python
class SSEHandler:
    """Server-sent events for streaming"""
    
    async def stream_updates(self):
        """Stream real-time updates"""
        while True:
            update = await self.get_update()
            yield f"data: {json.dumps(update)}\n\n"
```

## 6. Security Framework

### 6.1 Authentication Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Client  │────▶│   API   │────▶│  Auth   │
└─────────┘     └─────────┘     └─────────┘
     │               │                │
     │   Token       │   Validate     │
     ◀───────────────┼────────────────┘
     │               │
     │   Request     │
     ├──────────────▶│
     │               │
     │   Response    │
     ◀───────────────┤
```

### 6.2 Content Security

- **XSS Protection**: Content sanitization
- **CSRF Protection**: Token validation
- **SQL Injection**: Parameterized queries
- **Path Traversal**: Path validation
- **Rate Limiting**: Token bucket algorithm

### 6.3 Token Budget Management

```python
class TokenBudget:
    """Manage LLM token consumption"""
    
    def consume(self, tokens: int) -> bool:
        """Check and consume tokens"""
    
    def get_remaining(self) -> int:
        """Get remaining budget"""
    
    def reset(self):
        """Reset budget (hourly)"""
```

## 7. State Management Patterns

### 7.1 Event Sourcing

```python
class StateEvent:
    """Immutable state change event"""
    type: StateEventType  # CREATED, UPDATED, DELETED
    key: str
    value: Any
    previous_value: Any
    timestamp: datetime
```

### 7.2 State Synchronization

```python
async def sync_state():
    """Synchronize server and client state"""
    state = await state_manager.get_all()
    await websocket.send(json.dumps({
        "type": "state:sync",
        "state": state
    }))
```

### 7.3 Snapshot & Restore

```python
# Create snapshot
snapshot = await state_manager.create_snapshot()

# Restore from snapshot
await state_manager.restore_snapshot(snapshot.id)
```

## 8. Testing Framework

### 8.1 Component Testing

```python
def test_component_rendering():
    component = ProductCard(data=product_data)
    html = component.render()
    assert "product-card" in html
    assert product_data["name"] in html
```

### 8.2 Protocol Validation

```python
def test_protocol_compliance():
    response = MCPUIResponse(...)
    protocol = MCPUIProtocol()
    assert protocol.validate_response(response)
```

### 8.3 Integration Testing

```python
async def test_full_request_flow():
    server = TestMCPServer()
    response = await server.handle_request(
        method="GET",
        path="/products",
        params={"query": "test"}
    )
    assert response.ui_resources
    assert response.calculate_token_usage() < 1000
```

## 9. Performance Optimization

### 9.1 Token Efficiency

- **Data Minimization**: Send only essential data
- **HTML Compression**: Gzip responses
- **Resource Caching**: Cache UI components
- **Lazy Loading**: Load resources on demand

### 9.2 Caching Strategy

```python
class CacheManager:
    """Multi-level caching"""
    
    levels = [
        MemoryCache(ttl=60),      # L1: Memory
        RedisCache(ttl=3600),     # L2: Redis
        FileCache(ttl=86400)      # L3: Disk
    ]
```

### 9.3 Performance Metrics

```python
metrics = {
    "avg_response_time": 50,  # ms
    "token_reduction": 93,     # %
    "cache_hit_rate": 85,      # %
    "concurrent_requests": 100
}
```

## 10. Deployment Architecture

### 10.1 Container Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0"]
```

### 10.2 Scaling Strategy

```yaml
# docker-compose.yml
services:
  mcp-server:
    build: .
    scale: 3
  
  nginx:
    image: nginx
    depends_on:
      - mcp-server
    ports:
      - "80:80"
```

### 10.3 Monitoring & Observability

- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack
- **Tracing**: OpenTelemetry
- **Alerts**: PagerDuty integration

## 11. Migration Guide

### 11.1 From Legacy to MCP-UI

```python
# Before (Legacy)
return {"products": full_data}  # 8000+ tokens

# After (MCP-UI)
return server.build_response(
    data=server.minimize_data(products),  # 500 tokens
    ui_resources=[product_grid_component]
)
```

### 11.2 Adopting the Framework

1. **Install Framework**
   ```bash
   pip install mcp-ui-framework
   ```

2. **Extend Base Server**
   ```python
   class MyServer(MCPServer):
       def initialize(self):
           self.register_component("ProductGrid", ProductGrid)
   ```

3. **Create Components**
   ```python
   component = self.create_component("ProductGrid", products)
   ```

4. **Build Responses**
   ```python
   return self.build_response(data=minimal, ui_resources=[component])
   ```

## 12. Best Practices

### 12.1 Component Design
- Keep components small and focused
- Use composition over inheritance
- Implement proper error boundaries
- Follow accessibility guidelines

### 12.2 Security
- Always validate and sanitize input
- Use CSP headers
- Implement rate limiting
- Audit third-party dependencies

### 12.3 Performance
- Minimize initial payload
- Use progressive enhancement
- Implement proper caching
- Monitor token usage

### 12.4 Development
- Use TypeScript for type safety
- Write comprehensive tests
- Document component APIs
- Use semantic versioning

## Conclusion

The MCP-UI Framework provides a complete, production-ready infrastructure for building sophisticated MCP servers with rich UI capabilities. By following the MCP-UI Protocol and leveraging the framework's modular architecture, developers can create scalable, secure, and efficient MCP servers that deliver exceptional user experiences while maintaining optimal token efficiency for LLM interactions.

The framework's emphasis on reusability, security, and performance makes it suitable for enterprise deployments while remaining simple enough for rapid prototyping and development.