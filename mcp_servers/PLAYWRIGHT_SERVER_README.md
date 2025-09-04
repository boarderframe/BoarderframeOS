# Real Playwright MCP Server

A comprehensive Model Context Protocol (MCP) server providing real browser automation capabilities using Playwright. This server enables LLMs and agents to perform web automation tasks including navigation, content extraction, form interaction, and screenshot capture.

## 🎯 Features

### Core Browser Automation
- **Real Browser Control**: Uses actual Playwright browser instances (Chromium, Firefox, WebKit)
- **Multi-Context Support**: Manage multiple browser contexts and pages simultaneously
- **Headless & Headed Modes**: Configurable browser display mode
- **Session Management**: Proper browser resource cleanup and session handling

### Automation Tools
- **Navigation**: Navigate to URLs with configurable wait conditions
- **Content Extraction**: Extract text from entire pages or specific elements
- **Element Interaction**: Click buttons, fill forms, wait for elements
- **Screenshot Capture**: Take full-page or viewport screenshots
- **Page Information**: Get current page title, URL, and metadata

### Security & Compliance
- **Domain Restrictions**: Allow/deny lists for website access
- **Resource Limits**: CPU, memory, and timeout constraints
- **Audit Logging**: Comprehensive logging of all automation activities
- **Sensitive Data Masking**: Automatic masking of passwords and sensitive form fields

## 📁 Files

- `real_playwright_server.py` - Main MCP server implementation
- `test_playwright_server.py` - Standalone test script
- `demo_playwright_mcp_client.py` - MCP client demonstration
- `playwright_requirements.txt` - Python dependencies
- Configuration in `config/mcp.json` under `playwright-server-001`

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r playwright_requirements.txt
playwright install chromium
```

### 2. Test the Server (Standalone)
```bash
python test_playwright_server.py
```

### 3. Run as MCP Server
```bash
python real_playwright_server.py
```

### 4. Demo MCP Client Usage
```bash
python demo_playwright_mcp_client.py
```

## 🛠️ Available Tools

### `navigate`
Navigate to a URL and return page information.

**Parameters:**
- `url` (required): The URL to navigate to
- `wait_until`: When to consider navigation complete (`load`, `domcontentloaded`, `networkidle`)
- `timeout`: Navigation timeout in milliseconds (default: 30000)
- `context_id`: Browser context ID (optional)
- `page_id`: Page ID within context (optional)

**Example:**
```python
await call_tool("navigate", {
    "url": "https://example.com",
    "wait_until": "domcontentloaded"
})
```

### `extract_text`
Extract text content from the page or specific elements.

**Parameters:**
- `selector`: CSS selector to extract text from (optional, extracts all page text if not provided)
- `max_length`: Maximum length of extracted text (default: 100000)
- `context_id`: Browser context ID (optional)
- `page_id`: Page ID within context (optional)

**Example:**
```python
# Extract all page text
await call_tool("extract_text", {})

# Extract specific element text
await call_tool("extract_text", {
    "selector": "h1"
})
```

### `click`
Click on an element specified by CSS selector.

**Parameters:**
- `selector` (required): CSS selector of the element to click
- `timeout`: Timeout in milliseconds (default: 30000)
- `wait_for_navigation`: Whether to wait for navigation after click
- `context_id`: Browser context ID (optional)
- `page_id`: Page ID within context (optional)

**Example:**
```python
await call_tool("click", {
    "selector": "button#submit",
    "wait_for_navigation": true
})
```

### `fill`
Fill an input field with text.

**Parameters:**
- `selector` (required): CSS selector of the input field
- `text` (required): Text to fill in the field
- `clear_first`: Whether to clear existing content first (default: true)
- `timeout`: Timeout in milliseconds (default: 30000)
- `context_id`: Browser context ID (optional)
- `page_id`: Page ID within context (optional)

**Example:**
```python
await call_tool("fill", {
    "selector": "input[name='email']",
    "text": "user@example.com"
})
```

### `screenshot`
Take a screenshot of the current page.

**Parameters:**
- `full_page`: Whether to capture the full page or just viewport (default: false)
- `quality`: JPEG quality 0-100 (default: 90, only for JPEG format)
- `format`: Screenshot format (`png`, `jpeg`) (default: "png")
- `context_id`: Browser context ID (optional)
- `page_id`: Page ID within context (optional)

**Example:**
```python
await call_tool("screenshot", {
    "full_page": true,
    "format": "png"
})
```

### `wait_for_element`
Wait for an element to appear or reach a specific state.

**Parameters:**
- `selector` (required): CSS selector of the element to wait for
- `state`: State to wait for (`attached`, `detached`, `visible`, `hidden`) (default: "visible")
- `timeout`: Timeout in milliseconds (default: 30000)
- `context_id`: Browser context ID (optional)
- `page_id`: Page ID within context (optional)

**Example:**
```python
await call_tool("wait_for_element", {
    "selector": ".loading-spinner",
    "state": "hidden"
})
```

### `get_page_info`
Get information about the current page.

**Parameters:**
- `context_id`: Browser context ID (optional)
- `page_id`: Page ID within context (optional)

**Example:**
```python
await call_tool("get_page_info", {})
```

## 🔧 Configuration

### Environment Variables
- `PLAYWRIGHT_HEADLESS`: Set to "false" for headed mode (default: "true")
- `PLAYWRIGHT_BROWSER`: Browser type (`chromium`, `firefox`, `webkit`) (default: "chromium")

### MCP Configuration
The server is configured in `config/mcp.json` with comprehensive security settings:

```json
{
  "id": "playwright-server-001",
  "name": "playwright-automation-server",
  "security": {
    "access_restrictions": {
      "allowed_domains": ["*.example.com", "*.httpbin.org"],
      "denied_domains": ["*.banking.com", "localhost"],
      "max_concurrent_pages": 3,
      "max_screenshot_size_mb": 10
    },
    "resource_limits": {
      "max_cpu_percent": 80,
      "max_memory_mb": 2048,
      "timeout_seconds": 60
    }
  }
}
```

## 🔒 Security Features

### Access Control
- **Domain Allow/Deny Lists**: Restrict access to specific websites
- **Resource Monitoring**: CPU, memory, and timeout limits
- **Session Isolation**: Each context runs in isolation

### Audit Logging
- Page visits and navigation attempts
- Form submissions and data input
- Screenshot captures and downloads
- Failed automation attempts
- Automatic masking of sensitive form fields

### Safe Defaults
- Headless mode by default
- Popup blocking enabled
- File downloads disabled
- Reasonable timeouts and limits

## 🏗️ Architecture

### Browser Manager
- Singleton pattern for browser lifecycle management
- Automatic cleanup on exit or errors
- Context and page isolation
- Resource monitoring and limits

### Tool Implementation
- Async/await throughout for performance
- Comprehensive error handling
- Detailed logging for debugging
- Type hints for better developer experience

### MCP Integration
- Full MCP protocol compliance
- JSON Schema validation
- OpenAPI compatible for integration
- Structured error responses

## 🧪 Testing

### Unit Tests
Run the standalone test script to verify functionality:
```bash
python test_playwright_server.py
```

### Integration Tests
Test the MCP protocol integration:
```bash
python demo_playwright_mcp_client.py
```

### Manual Testing
1. Start server: `python real_playwright_server.py`
2. Use MCP Inspector: `npx @modelcontextprotocol/inspector`
3. Connect to stdio server and test tools

## 🐛 Troubleshooting

### Common Issues

**Browser not found:**
```bash
playwright install chromium
```

**Permission denied:**
```bash
chmod +x real_playwright_server.py
```

**Module not found:**
```bash
pip install -r playwright_requirements.txt
```

**Timeout errors:**
- Check network connectivity
- Increase timeout values
- Verify target website is accessible

### Debug Mode
Set environment variable for debug logging:
```bash
export LOG_LEVEL=debug
python real_playwright_server.py
```

### Log Files
- Server logs: `playwright_mcp.log`
- Audit logs: Configured in MCP settings
- Browser logs: Available through Playwright debugging

## 🔄 Integration Examples

### Open WebUI Integration
Configure in Open WebUI's MCP settings:
```json
{
  "command": "python",
  "args": ["/path/to/real_playwright_server.py"],
  "env": {
    "PLAYWRIGHT_HEADLESS": "true"
  }
}
```

### Python Client
```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

# Connect to server
server_params = StdioServerParameters(
    command="python",
    args=["real_playwright_server.py"]
)
stdio_transport = stdio_client(server_params)
session = ClientSession(stdio_transport[0], stdio_transport[1])

# Use the tools
await session.call_tool("navigate", {"url": "https://example.com"})
```

## 📈 Performance

### Benchmarks
- Cold start: ~2-3 seconds (browser initialization)
- Page navigation: ~1-2 seconds (typical website)
- Screenshot capture: ~500ms (viewport)
- Text extraction: ~100-500ms (depending on content size)

### Optimization Tips
- Reuse browser contexts when possible
- Use headless mode for better performance
- Set appropriate timeouts for your use case
- Limit concurrent pages to available resources

## 🤝 Contributing

1. Follow Python PEP 8 style guidelines
2. Add type hints to all functions
3. Include comprehensive error handling
4. Update tests for new features
5. Add security considerations for new tools

## 📄 License

This server is part of the MCP Server Manager project and follows the same licensing terms.

---

**Note**: This is a real browser automation server that can interact with actual websites. Use responsibly and in compliance with websites' terms of service and robots.txt files.