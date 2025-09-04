# MCP Server Artifact Rendering Optimization Guide

## Executive Summary

This guide presents an optimized response format for MCP servers that ensures reliable artifact rendering in Open WebUI. The solution addresses common rendering failures through multiple fallback mechanisms, clear LLM instructions, and intelligent content optimization.

## Problem Analysis

### Current Issues with Artifact Rendering

1. **Inconsistent Rendering**: HTML artifacts sometimes fail to render in Open WebUI
2. **Token Inefficiency**: Large HTML responses consume excessive tokens
3. **Unclear Instructions**: LLMs lack clear guidance on how to include artifacts
4. **No Fallback**: When primary rendering fails, users see raw HTML
5. **Size Limitations**: Large artifacts exceed rendering limits
6. **Debug Difficulty**: Hard to troubleshoot why artifacts fail to render

## Solution Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server Response                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          1. Response Optimizer                       │   │
│  │  - Analyzes content size and type                   │   │
│  │  - Selects optimal rendering strategy               │   │
│  │  - Creates multiple format options                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          2. HTML Generator                          │   │
│  │  - Self-contained HTML (no external resources)      │   │
│  │  - Inline styles only                               │   │
│  │  - Responsive design                                │   │
│  │  - Fallback visual elements                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          3. Multi-Format Response                   │   │
│  │  - Primary: HTML code blocks                        │   │
│  │  - Fallback 1: Markdown tables                      │   │
│  │  - Fallback 2: Base64 data URIs                     │   │
│  │  - Fallback 3: Plain text                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          4. LLM Instructions                        │   │
│  │  - Clear, explicit rendering instructions           │   │
│  │  - Example usage patterns                           │   │
│  │  - Troubleshooting guide                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Response Format Structure

```python
{
    # Minimal token usage for data
    "summary": "Found 20 products for 'milk'",
    "data_count": 20,
    
    # Artifact metadata
    "artifact": {
        "id": "abc123def456",
        "type": "product_cards",
        "size": 45678,
        "strategy": "code_block",
        "priority": "high",
        "checksum": "a1b2c3d4"
    },
    
    # Rendering instructions for LLM
    "rendering": {
        "primary_method": "Include the HTML from formats.code_block directly in your response",
        "fallback_methods": [
            "If primary fails, use formats.markdown",
            "Alternative: Create iframe with formats.data_uri"
        ],
        "example_usage": "Simply include: {formats.code_block}",
        "troubleshooting": {
            "not_rendering": "Ensure ```html tags are present",
            "partial_render": "Check content size limits"
        }
    },
    
    # Multiple format options
    "formats": {
        "code_block": "```html\n<html>...</html>\n```",
        "inline_html": "<html>...</html>",
        "markdown": "| Product | Price |\n|---------|-------|\n...",
        "data_uri": "data:text/html;base64,PGh0bWw+Li4u",
        "artifact_uri": "/artifacts/abc123def456",
        "compressed": "H4sIAAAAAAAAA..."
    }
}
```

### 2. Rendering Strategies

#### Strategy Selection Logic

```python
def determine_strategy(content_size: int, content_type: str) -> Strategy:
    if content_size < 50KB:
        return CODE_BLOCK  # Most reliable for small content
    elif content_size < 100KB:
        return HYBRID      # Multiple formats for medium content
    elif content_size < 200KB:
        return BASE64_DATA # Data URI for large content
    else:
        return IFRAME_URI  # External reference for very large
```

#### Strategy Characteristics

| Strategy | Size Limit | Reliability | Token Usage | Fallback |
|----------|------------|-------------|-------------|----------|
| CODE_BLOCK | <50KB | 95% | Low | Markdown |
| INLINE_HTML | <30KB | 85% | Low | Code Block |
| HYBRID | <100KB | 90% | Medium | Multiple |
| BASE64_DATA | <200KB | 75% | High | URI |
| IFRAME_URI | Unlimited | 70% | Minimal | Download |

### 3. HTML Generation Rules

#### Required HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artifact Title</title>
    <style>
        /* ALL styles MUST be inline */
        /* NO external CSS files */
        /* NO @import statements */
    </style>
</head>
<body>
    <!-- Self-contained content -->
    <!-- NO external images (use SVG or data URIs) -->
    <!-- NO external scripts -->
    <!-- NO external fonts -->
</body>
</html>
```

#### Visual Design Guidelines

1. **Use inline styles exclusively**
   ```html
   <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
   ```

2. **Include fallback visuals**
   ```html
   <img src="data:image/svg+xml,..." onerror="this.style.display='none'">
   ```

3. **Responsive by default**
   ```html
   <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));">
   ```

### 4. LLM Instructions Template

```markdown
📋 RENDERING INSTRUCTIONS FOR LLM:

1. **Primary Method** (code_block):
   Include the artifact_html field directly in your response.
   The HTML is already wrapped in ```html code blocks.

2. **What to do**:
   - Copy the entire artifact_html field into your response
   - Do NOT modify or truncate the HTML
   - Ensure the ```html tags are preserved

3. **Example**:
   Your response should include:
   
   Here are the search results:
   
   [INSERT artifact_html HERE]
   
   The products are displayed above.

4. **If rendering fails**:
   - Use the artifact_markdown field as fallback
   - This provides a table view of the same data

⚠️ IMPORTANT: The artifact_html is ready to render. Just include it!
```

### 5. Error Handling

#### Graceful Degradation Chain

```
1. Try: HTML Code Block
   ↓ (fails)
2. Try: Markdown Table
   ↓ (fails)
3. Try: Plain Text List
   ↓ (fails)
4. Show: Error message with raw data
```

#### Error Response Format

```python
{
    "error": "Rendering failed",
    "fallback_display": "Product 1: $2.99\nProduct 2: $3.99\n...",
    "debug": {
        "failure_reason": "Content size exceeded limit",
        "attempted_strategies": ["code_block", "markdown"],
        "recommendation": "Use pagination to reduce content size"
    }
}
```

## Integration Guide

### Step 1: Install Dependencies

```bash
pip install pydantic fastapi uvicorn
```

### Step 2: Import Optimizer

```python
from mcp_artifact_response_optimizer import (
    ArtifactResponseOptimizer,
    GuaranteedRenderHTMLGenerator,
    MCPServerIntegration
)
```

### Step 3: Initialize Components

```python
# Create optimizer with debug mode
optimizer = ArtifactResponseOptimizer(
    service_name="your-mcp-server",
    debug_mode=True,
    max_inline_size=75000  # 75KB
)

# Create HTML generator
html_generator = GuaranteedRenderHTMLGenerator()

# Create integration helper
integration = MCPServerIntegration("your-mcp-server")
```

### Step 4: Generate Optimized Responses

```python
@app.get("/search")
async def search(query: str):
    # Get your data
    results = await fetch_data(query)
    
    # Generate optimized response
    response = integration.create_product_response(
        products=results,
        search_query=query
    )
    
    return response
```

## Testing & Validation

### 1. Test Endpoints

```python
# Test artifact rendering
GET /test/artifact-rendering?test_type=simple
GET /test/artifact-rendering?test_type=complex
GET /test/artifact-rendering?test_type=stress

# Validate HTML content
POST /artifacts/validate
{
    "html": "<html>...</html>"
}

# Debug specific artifact
GET /artifacts/debug/{artifact_id}
```

### 2. Validation Checklist

- [ ] HTML is self-contained (no external resources)
- [ ] All styles are inline
- [ ] Content size is within limits
- [ ] HTML code blocks use ```html tags
- [ ] Markdown fallback is provided
- [ ] LLM instructions are clear
- [ ] Error handling is implemented
- [ ] Debug information is available

### 3. Performance Metrics

Monitor these metrics to ensure optimal performance:

```python
metrics = {
    "render_success_rate": 0.95,  # Target: >90%
    "average_response_size": 45000,  # Target: <50KB
    "token_reduction": 0.85,  # Target: >80%
    "fallback_usage": 0.05,  # Target: <10%
    "error_rate": 0.01  # Target: <2%
}
```

## Best Practices

### DO's

1. ✅ **Always provide multiple format options**
2. ✅ **Include clear LLM instructions in every response**
3. ✅ **Use inline styles exclusively**
4. ✅ **Implement progressive enhancement**
5. ✅ **Track rendering success rates**
6. ✅ **Provide debug endpoints**
7. ✅ **Compress large content**
8. ✅ **Use stable artifact IDs for caching**

### DON'Ts

1. ❌ **Don't use external CSS or JavaScript**
2. ❌ **Don't exceed 100KB for inline HTML**
3. ❌ **Don't assume rendering will succeed**
4. ❌ **Don't modify HTML in LLM responses**
5. ❌ **Don't use complex JavaScript interactions**
6. ❌ **Don't forget fallback options**
7. ❌ **Don't omit error handling**

## Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Artifact not rendering | Missing ```html tags | Ensure code blocks are properly formatted |
| Partial rendering | Content too large | Use compression or pagination |
| Styles not applied | External CSS | Convert to inline styles |
| Images not loading | External URLs | Use data URIs or SVG |
| JavaScript errors | External scripts | Remove or inline critical JS |
| Encoding issues | Special characters | Use proper UTF-8 encoding |

### Debug Process

1. **Check response format**
   ```bash
   curl http://localhost:9005/products/search/enhanced?term=test
   ```

2. **Validate HTML content**
   ```bash
   curl -X POST http://localhost:9005/artifacts/validate \
     -H "Content-Type: application/json" \
     -d '{"html": "<html>...</html>"}'
   ```

3. **Review debug information**
   ```bash
   curl http://localhost:9005/artifacts/debug/abc123
   ```

4. **Test rendering strategies**
   ```bash
   curl http://localhost:9005/test/artifact-rendering?test_type=complex
   ```

## Example Implementations

### Kroger MCP Server (Enhanced)

See `kroger_mcp_enhanced_artifacts.py` for a complete implementation with:
- Product search with visual cards
- Multiple rendering strategies
- Debug endpoints
- Validation tools

### Generic MCP Server Template

```python
from mcp_artifact_response_optimizer import MCPServerIntegration

# Initialize
integration = MCPServerIntegration("my-server")

@app.get("/data")
async def get_data(query: str):
    # Fetch data
    data = await fetch_data(query)
    
    # Generate HTML
    html = generate_html(data)
    
    # Create optimized response
    response = integration.optimizer.create_optimized_response(
        data=data,
        html_content=html,
        content_type="data_display",
        search_query=query
    )
    
    return response.dict()
```

## Conclusion

This optimized response format ensures reliable artifact rendering through:

1. **Multiple fallback mechanisms** - Never leave users without a display option
2. **Clear LLM instructions** - Explicit guidance on including artifacts
3. **Size optimization** - Efficient token usage without sacrificing functionality
4. **Debug capabilities** - Easy troubleshooting when issues occur
5. **Progressive enhancement** - Start simple, add complexity as needed

By implementing these patterns, MCP servers can guarantee that their visual artifacts render successfully in Open WebUI, providing a better user experience and more reliable tool interactions.