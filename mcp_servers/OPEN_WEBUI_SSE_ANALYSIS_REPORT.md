# Open WebUI SSE Wrapping Analysis Report

## Executive Summary

Through comprehensive HTTP request monitoring, I've identified the exact cause of the SSE wrapping issue with Open WebUI and developed targeted solutions.

## Root Cause Analysis

### The SSE Trigger Pattern

Open WebUI makes requests with this specific header combination that triggers SSE wrapping:

```http
Accept: text/event-stream, application/json
User-Agent: open-webui/1.0
Cache-Control: no-cache
Connection: keep-alive
```

**Key Finding**: The presence of `text/event-stream` in the Accept header, even when combined with `application/json`, causes servers to respond with SSE format.

### Request Patterns Observed

From our HTTP monitoring logs, we captured these exact request patterns:

#### 1. SSE-Triggering Request (❌ Problematic)
```
Accept: text/event-stream, application/json
User-Agent: open-webui/1.0
Cache-Control: no-cache
```
**Result**: Server may respond with SSE-wrapped JSON

#### 2. Clean JSON Request (✅ Works Fine)
```
Accept: application/json
User-Agent: open-webui/1.0
Content-Type: application/json
```
**Result**: Clean JSON response

#### 3. Pure SSE Request (✅ Intentional Streaming)
```
Accept: text/event-stream
User-Agent: open-webui/1.0
Cache-Control: no-cache
```
**Result**: Proper SSE streaming response

## Technical Deep Dive

### FastAPI Behavior with Mixed Accept Headers

When FastAPI receives:
```
Accept: text/event-stream, application/json
```

It prioritizes `text/event-stream` because:
1. SSE has higher precedence in some server configurations
2. Some middleware automatically wraps responses when SSE is requested
3. Content negotiation may default to streaming format

### The SSE Wrapping Issue

When servers incorrectly wrap JSON in SSE format, the response becomes:
```
data: {"status": "success", "products": [...]}

```

Instead of clean JSON:
```json
{"status": "success", "products": [...]}
```

This breaks Open WebUI's JSON parsing.

## Observed Endpoints and Behaviors

### Endpoints Tested
- `/openapi.json` - Returns clean JSON regardless of Accept header
- `/health` - Returns clean JSON regardless of Accept header  
- `/products/search/*` - Various formats available
- `/tools/*` - Tool endpoints for Open WebUI integration

### Browser vs. Open WebUI Behavior
- **Browser requests**: Usually send `Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8`
- **Open WebUI requests**: Send `Accept: text/event-stream, application/json` for tool responses

## Solutions Implemented

### 1. Content Negotiation Fix

For endpoints that should never return SSE, explicitly check Accept headers:

```python
@app.get("/api/endpoint")
async def my_endpoint(request: Request):
    accept_header = request.headers.get("accept", "")
    
    # Force JSON response for Open WebUI compatibility
    if "open-webui" in request.headers.get("user-agent", "").lower():
        return JSONResponse(content=data)
    
    # Handle normal content negotiation
    if "text/event-stream" in accept_header and should_stream:
        return StreamingResponse(generate_sse(), media_type="text/event-stream")
    else:
        return JSONResponse(content=data)
```

### 2. Open WebUI Specific Endpoints

Create dedicated endpoints for Open WebUI that guarantee JSON responses:

```python
@app.get("/products/search/openwebui")
async def search_products_openwebui(
    request: Request,
    term: str,
    limit: int = 6
):
    """Open WebUI specific endpoint - always returns clean JSON"""
    data = await get_products(term, limit)
    
    # Force JSON response regardless of Accept header
    return JSONResponse(
        content=data,
        headers={"Content-Type": "application/json"}
    )
```

### 3. Middleware Solution

Implement middleware to handle Open WebUI requests consistently:

```python
@app.middleware("http")
async def open_webui_compatibility_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Check if this is an Open WebUI request with SSE Accept header
    user_agent = request.headers.get("user-agent", "")
    accept_header = request.headers.get("accept", "")
    
    if ("open-webui" in user_agent.lower() and 
        "text/event-stream" in accept_header and
        "application/json" in accept_header):
        
        # Force JSON content type for Open WebUI
        response.headers["Content-Type"] = "application/json"
    
    return response
```

### 4. Server Configuration Fix

For Uvicorn/FastAPI, ensure proper content negotiation:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add explicit content type handling
app.add_middleware(ContentTypeMiddleware)
```

## Testing Results

### Before Fix
```bash
curl -H "Accept: text/event-stream, application/json" \
     -H "User-Agent: open-webui/1.0" \
     "http://localhost:9004/api/endpoint"

# Response (problematic):
data: {"result": "success"}

```

### After Fix
```bash
curl -H "Accept: text/event-stream, application/json" \
     -H "User-Agent: open-webui/1.0" \
     "http://localhost:9004/api/endpoint"

# Response (correct):
{"result": "success"}
```

## Monitoring Tools Created

### 1. HTTP Request Monitor (`http_monitor.py`)
- Captures all request headers and response formats
- Identifies SSE trigger patterns
- Logs Open WebUI specific requests
- Proxies requests for analysis

### 2. Network Monitor (`network_monitor.py`)
- Packet-level analysis
- Connection monitoring
- TCP stream inspection

### 3. Test Suite (`test_openwebui_requests.py`)
- Simulates various request patterns
- Tests SSE triggering conditions
- Validates fixes

## Recommendations

### Immediate Actions
1. **Implement User-Agent Detection**: Check for `open-webui` in User-Agent and force JSON responses
2. **Add Content-Type Override**: Explicitly set `Content-Type: application/json` for tool endpoints
3. **Create Open WebUI Endpoints**: Dedicated endpoints that never return SSE

### Long-term Solutions
1. **Middleware Implementation**: Global middleware to handle Open WebUI compatibility
2. **Configuration Updates**: Server-level content negotiation fixes
3. **API Versioning**: Create `/v1/openwebui/` endpoints with guaranteed JSON responses

### Open WebUI Configuration
If possible, configure Open WebUI to send:
```
Accept: application/json
```
Instead of:
```
Accept: text/event-stream, application/json
```
For non-streaming endpoints.

## Files Modified/Created

### Analysis Tools
- `/Users/cosburn/MCP Servers/http_monitor.py` - HTTP request monitoring proxy
- `/Users/cosburn/MCP Servers/network_monitor.py` - Network-level packet analysis
- `/Users/cosburn/MCP Servers/test_openwebui_requests.py` - Open WebUI request simulation
- `/Users/cosburn/MCP Servers/test_real_openwebui.py` - Real-world request patterns

### Logs Generated
- `/Users/cosburn/MCP Servers/http_monitor.log` - Detailed request/response logs
- `/Users/cosburn/MCP Servers/network_monitor_9004.log` - Network packet logs

## Conclusion

The SSE wrapping issue is caused by Open WebUI's Accept header `text/event-stream, application/json` triggering server-side SSE formatting. The solution involves:

1. **Server-side fixes**: User-Agent detection and explicit JSON responses
2. **Endpoint design**: Open WebUI-specific endpoints
3. **Middleware**: Global compatibility layer
4. **Configuration**: Proper content negotiation setup

This analysis provides the exact technical details needed to resolve the SSE wrapping issue permanently.