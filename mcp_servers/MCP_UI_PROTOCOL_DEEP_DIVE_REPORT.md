# MCP-UI Protocol Deep Dive Report

## Executive Summary

The MCP-UI Protocol is an extension of the Model Context Protocol (MCP) that enables MCP servers to provide interactive user interfaces directly to clients. Unlike standard MCP servers that only provide tools and data, MCP-UI servers can serve rich HTML/JavaScript interfaces that integrate seamlessly with the client environment. This protocol establishes a secure, bidirectional communication channel between server-provided UIs and the host application through a structured postMessage API.

The key innovation of MCP-UI is that **the MCP server itself serves the UI content**, not the LLM generating HTML. This is a critical distinction that affects implementation architecture.

## 1. Architecture Overview

### Core Design Principles

The MCP-UI Protocol follows a **three-layer architecture**:

1. **Server Layer**: MCP servers that implement UI capabilities
2. **Protocol Layer**: Standardized message passing and lifecycle management
3. **Client Layer**: Host applications that render and manage UI components

### Component Separation

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MCP Server    │────▶│  MCP-UI Protocol │────▶│  Host Client    │
│  (Serves UI)    │◀────│  (Message Bus)   │◀────│ (Renders UI)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

The protocol maintains strict separation between:
- **UI Provider** (MCP server)
- **UI Consumer** (Host application)
- **Communication Channel** (postMessage API)

## 2. Core Components

### 2.1 Client Module (`@mcp-ui/client`)

The client module handles the consumer side of UI components:

```typescript
interface McpUiClient {
  connect(config: ConnectionConfig): Promise<void>
  disconnect(): Promise<void>
  listRoots(): Promise<Root[]>
  openRoot(rootId: string): Promise<void>
  sendMessage(message: any): void
  onMessage(handler: MessageHandler): void
}
```

**Key Responsibilities:**
- Establishing connections to MCP servers
- Managing UI component lifecycle
- Handling message routing
- Security enforcement

### 2.2 Host Module (`@mcp-ui/host`)

The host module manages the embedding environment:

```typescript
interface McpUiHost {
  registerRoot(root: UiRoot): void
  unregisterRoot(rootId: string): void
  handleMessage(message: HostMessage): void
  updateState(state: any): void
}
```

**Key Features:**
- iframe/WebView management
- Sandbox configuration
- State synchronization
- Event delegation

### 2.3 Types Module (`@mcp-ui/types`)

Provides TypeScript definitions for the entire protocol:

```typescript
// Core message types
type MessageType = 
  | 'mcp-ui:request'
  | 'mcp-ui:response'
  | 'mcp-ui:notification'
  | 'mcp-ui:error'

// UI Root definition
interface UiRoot {
  id: string
  name: string
  description?: string
  icon?: string
  url: string
  metadata?: Record<string, any>
}
```

## 3. Registration and Discovery

### 3.1 UI Root Registration

MCP servers register UI roots through the protocol:

```javascript
// Server-side registration
server.registerUiRoot({
  id: 'product-search',
  name: 'Product Search',
  description: 'Search and browse products',
  url: '/ui/product-search.html',  // Server serves this
  icon: 'search'
});
```

### 3.2 Discovery Flow

1. **Client Discovery Request**:
```javascript
// Client requests available UIs
const roots = await client.listRoots();
```

2. **Server Response**:
```json
{
  "roots": [
    {
      "id": "product-search",
      "name": "Product Search",
      "url": "/ui/product-search.html"
    }
  ]
}
```

3. **UI Instantiation**:
```javascript
// Client opens a UI root
await client.openRoot('product-search');
// Host creates iframe with server-provided URL
```

### 3.3 Dynamic Registration

UI roots can be registered dynamically based on:
- User permissions
- Server state
- Configuration changes
- Runtime conditions

## 4. Communication Protocol

### 4.1 Message Flow Architecture

```
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│   UI Frame   │◀────────▶│     Host     │◀────────▶│  MCP Server  │
│  (iframe)    │postMessage│  (Bridge)    │    MCP   │   (Backend)  │
└──────────────┘          └──────────────┘          └──────────────┘
```

### 4.2 Message Types and Formats

#### Request Messages
```javascript
{
  type: 'mcp-ui:request',
  id: 'req-123',
  method: 'getData',
  params: { query: 'example' },
  metadata: {
    timestamp: 1234567890,
    origin: 'ui-frame'
  }
}
```

#### Response Messages
```javascript
{
  type: 'mcp-ui:response',
  id: 'req-123',
  result: { data: [...] },
  metadata: {
    timestamp: 1234567891,
    duration: 150
  }
}
```

#### Notification Messages
```javascript
{
  type: 'mcp-ui:notification',
  event: 'stateChanged',
  data: { newState: {...} }
}
```

### 4.3 Bidirectional Communication

The protocol supports full duplex communication:

```javascript
// UI to Host
iframe.contentWindow.postMessage({
  type: 'mcp-ui:request',
  method: 'searchProducts',
  params: { query: 'milk' }
}, '*');

// Host to UI
iframe.contentWindow.postMessage({
  type: 'mcp-ui:response',
  result: { products: [...] }
}, iframe.origin);
```

### 4.4 State Synchronization

The protocol maintains state consistency through:
- Incremental updates
- State snapshots
- Conflict resolution
- Optimistic UI patterns

## 5. Security Framework

### 5.1 Sandboxing Requirements

All UI components run in sandboxed environments:

```html
<iframe 
  src="https://mcp-server.com/ui/component.html"
  sandbox="allow-scripts allow-forms allow-same-origin"
  csp="default-src 'self'; script-src 'self' 'unsafe-inline'">
</iframe>
```

### 5.2 Authentication Flow

```javascript
// 1. Initial authentication
const token = await client.authenticate({
  clientId: 'app-123',
  clientSecret: 'secret'
});

// 2. Token passed to UI
iframe.contentWindow.postMessage({
  type: 'mcp-ui:auth',
  token: token
}, iframe.origin);

// 3. UI validates with server
fetch('/api/validate', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### 5.3 Security Best Practices

1. **Origin Validation**: Always verify message origins
2. **Input Sanitization**: Sanitize all data from UI frames
3. **CSP Headers**: Implement strict Content Security Policies
4. **Token Rotation**: Regularly rotate authentication tokens
5. **Rate Limiting**: Implement message rate limiting

## 6. Implementation Guidelines

### 6.1 Server Implementation Pattern

```python
# Python MCP server with UI support
class MCPUIServer:
    def __init__(self):
        self.ui_roots = {}
        
    def register_ui_root(self, root):
        """Register a UI root that the server will serve"""
        self.ui_roots[root.id] = root
        
    def serve_ui(self, root_id):
        """Serve the actual UI HTML/JS content"""
        root = self.ui_roots.get(root_id)
        if root:
            # Server provides the UI content
            return self.load_ui_template(root.template)
    
    def handle_ui_request(self, request):
        """Handle requests from UI components"""
        if request.method == 'searchProducts':
            return self.search_products(request.params)
```

### 6.2 Client Integration Pattern

```javascript
// Client-side integration
class MCPUIClient {
  async connectToServer(serverUrl) {
    this.connection = await establishMCPConnection(serverUrl);
    
    // Discover available UIs
    const roots = await this.connection.listUIRoots();
    
    // Open a UI root
    const ui = await this.openUIRoot(roots[0].id);
    
    // The server provides the UI URL
    this.embedUI(ui.url);
  }
  
  embedUI(uiUrl) {
    const iframe = document.createElement('iframe');
    iframe.src = uiUrl;  // URL served by MCP server
    iframe.sandbox = 'allow-scripts allow-same-origin';
    document.body.appendChild(iframe);
    
    // Set up message handling
    window.addEventListener('message', (e) => {
      if (e.origin === new URL(uiUrl).origin) {
        this.handleUIMessage(e.data);
      }
    });
  }
}
```

### 6.3 Testing Approach

```javascript
// Test UI component isolation
describe('MCP UI Component', () => {
  it('should handle messages correctly', async () => {
    const mockHost = new MockMCPHost();
    const ui = await mockHost.loadUI('test-ui');
    
    // Send message to UI
    ui.postMessage({ type: 'mcp-ui:request', method: 'test' });
    
    // Verify response
    const response = await ui.waitForMessage();
    expect(response.type).toBe('mcp-ui:response');
  });
});
```

## 7. Key Differences from Standard MCP

### 7.1 Standard MCP vs MCP-UI

| Feature | Standard MCP | MCP-UI |
|---------|-------------|---------|
| **Purpose** | Tool/Resource provision | Interactive UI provision |
| **Output** | JSON data/text | HTML/JS interfaces |
| **Interaction** | Request-response | Bidirectional messaging |
| **State** | Stateless | Stateful with sync |
| **Rendering** | Client renders | Server provides UI |

### 7.2 Critical Distinction

**Standard MCP Flow:**
```
LLM → Generates response → Client renders
```

**MCP-UI Flow:**
```
MCP Server → Serves UI → Client embeds → User interacts
```

The fundamental difference: **MCP-UI servers provide pre-built UIs, not generated HTML**.

## 8. Critical Findings

### 8.1 Common Implementation Mistakes

1. **LLM Generating UI**: The most common mistake is having the LLM generate HTML instead of the MCP server serving pre-built UIs.

2. **Missing UI Registration**: Servers not properly registering UI roots through the protocol.

3. **Incorrect Message Routing**: Mixing MCP tool responses with UI responses.

4. **Security Violations**: Not properly sandboxing UI components.

### 8.2 Architecture Insights

- **UI Serving is Server Responsibility**: The MCP server must serve actual UI files, not return HTML strings.
- **Protocol is Transport-Agnostic**: Can work over WebSocket, HTTP, or IPC.
- **State Management is Crucial**: UI components need consistent state synchronization.
- **Security Cannot be Optional**: Sandboxing and origin validation are mandatory.

### 8.3 Performance Considerations

- **Lazy Loading**: UI components should load on-demand
- **Caching**: Implement aggressive caching for UI assets
- **Message Batching**: Batch multiple messages to reduce overhead
- **Compression**: Use compression for large state updates

## 9. Recommendations for Our Project

### 9.1 Immediate Fixes Required

1. **Stop LLM HTML Generation**:
   - Remove any prompts asking LLM to generate HTML
   - LLM should only trigger UI display, not create it

2. **Implement Proper UI Serving**:
```python
# Kroger MCP server should serve UI files
@app.route('/ui/<path:filename>')
def serve_ui(filename):
    return send_from_directory('ui_templates', filename)
```

3. **Register UI Roots Correctly**:
```python
def register_ui_roots(self):
    self.register_root({
        'id': 'product-search',
        'name': 'Product Search',
        'url': f'{self.base_url}/ui/search.html'
    })
```

4. **Set Up Message Bridge**:
```javascript
// In the served UI file
window.addEventListener('message', (event) => {
  if (event.data.type === 'mcp-ui:request') {
    // Handle MCP request
    handleMCPRequest(event.data);
  }
});
```

### 9.2 Architecture Corrections

**Current (Incorrect) Flow:**
```
User → LLM → Generate HTML → Display
```

**Correct MCP-UI Flow:**
```
User → LLM → Trigger UI → MCP Server serves UI → Display in iframe
```

### 9.3 Implementation Checklist

- [ ] Create `ui_templates/` directory with pre-built HTML/JS files
- [ ] Implement UI serving endpoints in MCP server
- [ ] Register UI roots with proper URLs
- [ ] Set up postMessage communication bridge
- [ ] Implement iframe sandboxing in client
- [ ] Add authentication token passing
- [ ] Test with MCP Inspector for UI capabilities
- [ ] Validate security policies

### 9.4 Testing Strategy

1. **Unit Tests**: Test message handling and UI registration
2. **Integration Tests**: Test full UI loading and interaction flow
3. **Security Tests**: Validate sandboxing and origin checks
4. **Performance Tests**: Measure UI load times and message latency

## Conclusion

The MCP-UI Protocol enables rich, interactive experiences by allowing MCP servers to serve and manage their own user interfaces. The critical insight is that **the server provides the UI**, not the LLM. Our current implementation incorrectly has the LLM generating HTML, which violates the protocol design. 

To fix this, we need to:
1. Build actual UI templates on the server
2. Serve them via proper endpoints
3. Register them through the MCP-UI protocol
4. Handle bidirectional communication correctly

This architectural correction will resolve the HTML rendering issues and align our implementation with the MCP-UI specification.