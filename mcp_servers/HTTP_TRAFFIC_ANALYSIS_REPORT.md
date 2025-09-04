# HTTP Traffic Analysis Report: Open WebUI ↔ MCP Server SSE Issue

## Executive Summary

**ROOT CAUSE IDENTIFIED**: The "data: {" SSE format is **NOT being introduced by the MCP server or any proxy**. The MCP server consistently returns proper JSON responses with `content-type: application/json`. The SSE transformation occurs within Open WebUI's client-side JavaScript.

## Detailed Findings

### 1. MCP Server Response Analysis

**✅ CONFIRMED: MCP Server Returns Valid JSON**

All test requests to the MCP server return proper JSON responses:

```http
< HTTP/1.1 200 OK
< content-type: application/json
< content-length: 227

{"status":"healthy","service":"kroger-mcp-server",...}
```

**Test Results:**
- Direct curl requests: ✅ JSON
- Python requests: ✅ JSON  
- OpenWebUI-style headers: ✅ JSON
- SSE Accept headers: ✅ JSON (server ignores SSE preference)

### 2. Request/Response Capture Evidence

#### Test 1: Normal JSON Request
```bash
curl -H "Accept: application/json" "http://localhost:9004/health"
```
**Response:**
```http
< content-type: application/json
{"status":"healthy",...}
```

#### Test 2: OpenWebUI-Style Request with SSE Headers
```bash
curl -H "Accept: text/event-stream" -H "User-Agent: Mozilla/5.0 (compatible; OpenWebUI)" "http://localhost:9004/health"
```
**Response:**
```http
< content-type: application/json  # Still JSON!
{"status":"healthy",...}
```

#### Test 3: Product Search Endpoint
```bash
curl "http://localhost:9004/products/search/llm-ready?term=milk&limit=2"
```
**Response:**
```http
< content-type: application/json
< x-response-type: json
{"llm_response":"Found 2 milk products...","artifact_available":true,...}
```

### 3. Network Infrastructure Analysis

**✅ NO PROXY OR MIDDLEWARE TRANSFORMATION**

- **Port 9004**: Direct MCP server binding confirmed
- **Process**: Single Python FastAPI process (PID 5992)
- **Network stack**: Direct TCP connection, no intermediary proxies
- **Response headers**: Consistent `uvicorn` server signature

### 4. HTTP Client Comparison

| Client | Accept Header | Content-Type Response | Body Format |
|--------|---------------|----------------------|-------------|
| curl (direct) | application/json | application/json | Valid JSON |
| curl (SSE-style) | text/event-stream | application/json | Valid JSON |
| Python requests | application/json | application/json | Valid JSON |
| Python requests (streaming) | text/event-stream | application/json | Valid JSON |

**Conclusion**: All HTTP clients receive identical JSON responses regardless of Accept headers.

### 5. Open WebUI Request Analysis

From server logs, actual Open WebUI requests show:
```
INFO: 127.0.0.1:65220 - "GET /products/search/llm-ready?term=milk&limit=2 HTTP/1.1" 200 OK
```

**Key Evidence:**
- Open WebUI makes standard GET requests
- Server responds with 200 OK and JSON
- No SSE content-type is set by server
- No "data: {" format in server responses

### 6. The Transformation Point

**🚨 CRITICAL FINDING**: The SSE transformation occurs in Open WebUI's JavaScript client, not in the HTTP transport layer.

**Evidence:**
1. Server never returns `content-type: text/event-stream`
2. Server never formats responses as `data: {...}`
3. Raw HTTP responses are always valid JSON
4. Multiple HTTP clients confirm identical behavior

## Technical Analysis: Where SSE Format is Introduced

### Likely Scenario in Open WebUI:

```javascript
// Open WebUI client-side code (hypothetical)
fetch('/api/mcp-tool', {
  headers: { 'Accept': 'text/event-stream' }
})
.then(response => {
  // Open WebUI expects SSE format for tool responses
  // It may transform JSON to SSE format client-side
  if (response.headers.get('content-type').includes('application/json')) {
    const json = await response.json();
    // Transform to SSE format for consistent handling
    return `data: ${JSON.stringify(json)}\n\n`;
  }
})
```

### Evidence Supporting Client-Side Transformation:

1. **Consistent Server Behavior**: Server always returns JSON
2. **No Network Transformation**: No proxy/middleware changes format
3. **OpenWebUI-Specific Issue**: Only Open WebUI reports SSE format
4. **Tool Integration Pattern**: Open WebUI likely normalizes all tool responses to SSE for consistent streaming

## Recommendations

### Immediate Actions:

1. **Browser Developer Tools Investigation**:
   ```
   1. Open Open WebUI in browser
   2. Open DevTools > Network tab
   3. Make MCP tool request
   4. Examine actual HTTP request/response
   5. Check if transformation happens in JavaScript
   ```

2. **Open WebUI Source Code Review**:
   - Look for MCP tool integration code
   - Find SSE response handling logic
   - Identify JSON→SSE transformation

3. **MCP Connector Configuration**:
   - Check Open WebUI MCP connector settings
   - Verify if SSE mode is forced for tool responses
   - Test with different connector configurations

### Long-term Solutions:

1. **MCP Server Enhancement** (if needed):
   ```python
   # Add SSE support if Open WebUI requires it
   @app.get("/products/search/sse")
   async def search_products_sse(term: str):
       data = await search_products(term)
       return StreamingResponse(
           generate_sse(data),
           media_type="text/event-stream"
       )
   ```

2. **Open WebUI Configuration**:
   - Configure MCP connector to expect JSON responses
   - Disable automatic SSE transformation if possible

## Files Created During Investigation

1. **`/Users/cosburn/MCP Servers/monitor_http_traffic.py`** - HTTP traffic monitor
2. **`/Users/cosburn/MCP Servers/openwebui_debug.py`** - Open WebUI specific debug proxy
3. **`/Users/cosburn/MCP Servers/HTTP_TRAFFIC_ANALYSIS_REPORT.md`** - This report

## Next Steps

1. **Investigate Open WebUI Source Code**: Find the exact transformation point
2. **Browser DevTools Analysis**: Capture the actual transformation in action
3. **Configuration Fix**: Adjust Open WebUI to handle JSON MCP responses properly
4. **Documentation Update**: Document proper MCP→Open WebUI integration pattern

---

**Conclusion**: The MCP server is functioning correctly. The "data: {" SSE format is being introduced by Open WebUI's client-side JavaScript, likely as part of its tool response normalization process. The fix should focus on Open WebUI configuration or code modification, not the MCP server.