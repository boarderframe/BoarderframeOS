# Kroger MCP Server - SSE & Streaming Endpoints for Open WebUI

## Problem Statement
Open WebUI expects SSE (Server-Sent Events) format for streaming responses from MCP tools. Regular JSON responses are wrapped in SSE format by Open WebUI, which breaks HTML artifact rendering.

## Solution: New Streaming Endpoints

### 1. SSE Endpoint - `/products/search/sse`
**Port:** 9004  
**Method:** GET  
**Content-Type:** `text/event-stream`

#### Parameters:
- `term` (required): Product search term
- `limit` (optional): Number of products (1-12, default: 6)

#### Response Format:
```
data: {"type": "start", "model": "kroger-mcp"}

data: {"type": "content", "content": "chunk of text..."}

data: {"type": "content", "content": "more text with HTML..."}

data: {"type": "done"}
```

#### Example Usage:
```bash
curl -N -H "Accept: text/event-stream" \
  "http://localhost:9004/products/search/sse?term=milk&limit=3"
```

### 2. Pure Stream Endpoint - `/products/search/stream`
**Port:** 9004  
**Method:** GET  
**Content-Type:** `text/plain; charset=utf-8`

#### Parameters:
- `term` (required): Product search term
- `limit` (optional): Number of products (1-12, default: 6)

#### Response Format:
Pure text stream with embedded HTML code block that Open WebUI will automatically render as an artifact.

#### Example Response:
```
Found 3 milk products available for delivery:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Kroger Products</title>
    <style>/* Beautiful CSS styling */</style>
</head>
<body>
    <!-- Product cards HTML -->
</body>
</html>
```

**Product Summary:**
- 3 items available
- Prices range from $1.99 to $4.99
```

### 3. Original Endpoints (Still Available)

#### `/products/search/llm-ready`
Returns JSON with pre-formatted LLM response containing HTML artifact.

#### `/products/search/openwebui`
Returns plain text response (no HTML) for simple text output.

#### `/products/search/compact`
Returns compact JSON with product data and display instructions.

## Integration with Open WebUI

### Recommended Approach:

1. **For Visual Artifacts:** Use `/products/search/sse` or `/products/search/stream`
   - These return properly formatted streaming responses
   - HTML code blocks are embedded naturally in the text
   - Open WebUI will detect and render them as visual artifacts

2. **For Text-Only Results:** Use `/products/search/openwebui`
   - Returns simple text without HTML
   - No artifact rendering, just plain text results

3. **For Custom Integration:** Use `/products/search/llm-ready`
   - Returns JSON with the LLM response pre-formatted
   - Extract the `llm_response` field and use it in your response

## Testing

### Test HTML Page
A test page is available at: `/test_sse_openwebui.html`

This page demonstrates:
- SSE event streaming
- HTML artifact extraction and rendering
- Real-time updates as data streams in

### Command-Line Testing

Test SSE endpoint:
```bash
curl -N -H "Accept: text/event-stream" \
  "http://localhost:9004/products/search/sse?term=bread&limit=5"
```

Test streaming endpoint:
```bash
curl "http://localhost:9004/products/search/stream?term=eggs&limit=4"
```

## Key Improvements

1. **Proper SSE Format:** Events are formatted exactly as Open WebUI expects
2. **Streaming Support:** Character-by-character streaming simulates LLM typing
3. **HTML Preservation:** HTML code blocks are preserved in the stream
4. **Error Handling:** Graceful error messages in the stream
5. **CORS Headers:** Proper headers for cross-origin requests

## Troubleshooting

If artifacts don't render in Open WebUI:
1. Ensure the HTML is wrapped in triple backticks with `html` language identifier
2. Check that the streaming response isn't being double-wrapped
3. Verify CORS headers are present
4. Test with the HTML test page first to verify the endpoint works

## Server Status

To check if the Kroger MCP server is running:
```bash
curl http://localhost:9004/health
```

To get server configuration:
```bash
curl http://localhost:9004/config
```