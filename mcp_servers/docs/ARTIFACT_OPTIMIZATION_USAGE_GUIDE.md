# Artifact Optimization Usage Guide

## Quick Start

This guide demonstrates how to implement LLM artifact response optimization in your MCP servers for reliable Open WebUI rendering.

## Installation

```python
# Import the formatter
from app.services.llm_artifact_formatter import (
    LLMArtifactFormatter,
    ArtifactResponseBuilder,
    format_product_search_response
)

# Initialize formatter
formatter = LLMArtifactFormatter()
```

## Basic Usage Examples

### Example 1: Simple Product Search Response

```python
# Your product search results
products = [
    {"name": "Organic Milk", "price": 4.99},
    {"name": "Almond Milk", "price": 3.49}
]

# Format response with artifact
response = format_product_search_response(products, "milk")

# LLM will receive and format as:
"""
Found 2 products for 'milk'

```html
<div class="g">
  <div class="c"><h4>Organic Milk</h4><p class="pr">$4.99</p></div>
  <div class="c"><h4>Almond Milk</h4><p class="pr">$3.49</p></div>
</div>
```
"""
```

### Example 2: Using the Builder Pattern

```python
builder = ArtifactResponseBuilder()

response = (
    builder
    .with_message("Your search returned 5 results")
    .with_artifact(html_content)
    .with_context("All items eligible for same-day delivery")
    .with_pattern(ResponsePattern.DIRECT_HTML)
    .optimize_tokens(True)
    .build()
)
```

### Example 3: Custom Artifact Generation

```python
formatter = LLMArtifactFormatter()

# Generate product grid
html = formatter.create_product_grid_artifact(
    products=[
        {"name": "Item 1", "price": 9.99, "description": "Description"},
        {"name": "Item 2", "price": 14.99, "description": "Description"}
    ],
    max_items=5
)

# Create formatted response
response = formatter.format_response(
    message="Here are your search results",
    artifact_html=html,
    artifact_type=ArtifactType.PRODUCT_GRID
)
```

## Integration with FastAPI

### Basic Endpoint

```python
from fastapi import FastAPI, Query
from app.services.llm_artifact_formatter import LLMArtifactFormatter

app = FastAPI()
formatter = LLMArtifactFormatter()

@app.get("/search")
async def search(query: str = Query(...)):
    # Search logic
    results = search_products(query)
    
    # Generate artifact
    html = formatter.create_product_grid_artifact(results)
    
    # Return with display instructions
    return {
        "message": f"Found {len(results)} products",
        "display_instructions": f"```html\n{html}\n```",
        "token_estimate": len(html) // 4
    }
```

### Advanced Endpoint with Validation

```python
@app.post("/validate-response")
async def validate(response_text: str):
    is_valid, issues = formatter.validate_response(response_text)
    artifact = formatter.extract_artifact(response_text)
    
    return {
        "valid": is_valid,
        "issues": issues,
        "has_artifact": artifact is not None,
        "recommendations": generate_recommendations(issues)
    }
```

## LLM Prompt Templates

### For GPT-4/GPT-4-Turbo

```markdown
You are a helpful assistant that provides search results with visual HTML artifacts.

When responding to searches:
1. Briefly summarize the results
2. Include the HTML artifact using ```html blocks
3. Add any relevant context

Example:
I found 3 products matching your search.

```html
[HTML content here]
```

All items are in stock and available for delivery.
```

### For Claude (Anthropic)

```markdown
You are Claude, providing rich visual responses using HTML artifacts.

Format your responses as:
- Natural language explanation
- HTML artifact in ```html blocks
- Additional helpful context

The HTML will be rendered visually in Open WebUI.
```

### For Open Source Models (Llama, Mistral, etc.)

```markdown
Instructions: Include HTML artifacts in responses.

Format:
[Explanation]
```html
[HTML content]
```
[Context]

Keep responses concise for token efficiency.
```

## Response Patterns

### Pattern 1: Direct HTML (Recommended)

```python
# Most reliable for Open WebUI
response = formatter.format_response(
    message="Found products",
    artifact_html=html,
    pattern=ResponsePattern.DIRECT_HTML
)

# Output:
"""
Found products

```html
<div>...</div>
```
"""
```

### Pattern 2: Structured JSON

```python
# For API responses
response = formatter.format_response(
    message="Found products",
    artifact_html=html,
    pattern=ResponsePattern.STRUCTURED_JSON
)

# Output:
{
    "message": "Found products",
    "artifact": {
        "type": "html",
        "content": "<div>...</div>"
    }
}
```

### Pattern 3: Hybrid Natural

```python
# For conversational interfaces
response = formatter.format_response(
    message="Found products",
    artifact_html=html,
    pattern=ResponsePattern.HYBRID_NATURAL
)

# Output:
"""
Found products

**Visual Display:**
```html
<div>...</div>
```
"""
```

### Pattern 4: Minimal Token

```python
# For maximum efficiency
response = formatter.format_response(
    message="Results",
    artifact_html=html,
    pattern=ResponsePattern.MINIMAL_TOKEN
)

# Output:
"""
Results
```html
<div>...</div>
```
"""
```

## Token Optimization Techniques

### 1. HTML Optimization

```python
# Automatically optimizes HTML
formatter = LLMArtifactFormatter()
optimized_response = formatter.format_response(
    message="Results",
    artifact_html=verbose_html,
    optimize_tokens=True  # Enables optimization
)
```

### 2. Class Name Shortening

```python
# Before optimization
<div class="product-card description-text">

# After optimization
<div class="pc d">
```

### 3. Style Consolidation

```python
# Before
<div style="color: red;">Text1</div>
<div style="color: red;">Text2</div>

# After
<style>.s1{color:red}</style>
<div class="s1">Text1</div>
<div class="s1">Text2</div>
```

## Validation and Testing

### Validate Response Format

```python
# Check if response will render correctly
is_valid, issues = formatter.validate_response(llm_response)

if not is_valid:
    print(f"Issues found: {issues}")
    # Fix issues before sending
```

### Extract Artifacts

```python
# Extract HTML from various response formats
artifact = formatter.extract_artifact(llm_response)

if artifact:
    print(f"Found artifact: {len(artifact)} chars")
else:
    print("No artifact found in response")
```

### Test Token Efficiency

```python
# Ensure response stays within limits
response = formatter.format_response(
    message="Large result set",
    artifact_html=large_html,
    optimize_tokens=True
)

tokens = len(response) // 4
assert tokens < 1000, f"Response too large: {tokens} tokens"
```

## Common Issues and Solutions

### Issue 1: Artifacts Not Rendering

**Problem:** Open WebUI doesn't detect the artifact

**Solution:**
```python
# Ensure proper formatting
response = f"""Your results:

```html
{html_content}
```

Additional information here."""
```

### Issue 2: Token Limit Exceeded

**Problem:** Response is too large

**Solution:**
```python
# Limit items and optimize
html = formatter.create_product_grid_artifact(
    products=all_products[:5],  # Limit to 5
    max_items=5
)

response = formatter.format_response(
    message="Top 5 results",
    artifact_html=html,
    optimize_tokens=True  # Enable optimization
)
```

### Issue 3: Security Warnings

**Problem:** HTML contains unsafe content

**Solution:**
```python
# Validate before sending
is_valid, issues = formatter.validate_response(response)

# Check for security issues
security_issues = [i for i in issues if "script" in i.lower()]
if security_issues:
    # Sanitize HTML
    clean_html = remove_scripts(html)
```

## Best Practices Checklist

- [ ] Always include ```html blocks for artifacts
- [ ] Place artifacts after explanation text
- [ ] Optimize for tokens when possible
- [ ] Validate responses before sending
- [ ] Test with multiple LLM models
- [ ] Cache artifacts for reuse
- [ ] Handle empty states gracefully
- [ ] Include fallback text
- [ ] Monitor token usage
- [ ] Test rendering in Open WebUI

## Performance Metrics

### Token Usage Targets

| Content Type | Target Tokens | Maximum Tokens |
|-------------|--------------|----------------|
| Product Grid (5 items) | 200-300 | 500 |
| Product List (10 items) | 300-400 | 700 |
| Empty State | 50-100 | 150 |
| Data Table | 150-250 | 400 |
| Chart/Visualization | 250-350 | 600 |

### Response Time Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Format Response | <10ms | 50ms |
| Optimize HTML | <20ms | 100ms |
| Validate Response | <5ms | 20ms |
| Extract Artifact | <5ms | 20ms |

## Advanced Patterns

### Dynamic Artifact Generation

```python
class DynamicArtifactGenerator:
    def __init__(self, formatter):
        self.formatter = formatter
        self.templates = {}
    
    def register_template(self, name, template_func):
        self.templates[name] = template_func
    
    def generate(self, template_name, data):
        if template_name in self.templates:
            html = self.templates[template_name](data)
            return self.formatter.format_response(
                message=f"Generated {template_name}",
                artifact_html=html
            )
```

### Artifact Caching

```python
from functools import lru_cache
import hashlib

class CachedArtifactFormatter:
    def __init__(self):
        self.formatter = LLMArtifactFormatter()
    
    @lru_cache(maxsize=100)
    def get_artifact(self, query_hash):
        return self.formatter.create_product_grid_artifact(
            self.search_products(query_hash)
        )
    
    def format_search(self, query):
        query_hash = hashlib.md5(query.encode()).hexdigest()
        artifact = self.get_artifact(query_hash)
        return self.formatter.format_response(
            message=f"Results for '{query}'",
            artifact_html=artifact
        )
```

### Multi-Model Support

```python
class MultiModelFormatter:
    def __init__(self):
        self.formatters = {
            "gpt4": LLMArtifactFormatter(ResponsePattern.DIRECT_HTML),
            "claude": LLMArtifactFormatter(ResponsePattern.HYBRID_NATURAL),
            "llama": LLMArtifactFormatter(ResponsePattern.MINIMAL_TOKEN)
        }
    
    def format_for_model(self, model_name, message, html):
        formatter = self.formatters.get(
            model_name, 
            self.formatters["gpt4"]
        )
        return formatter.format_response(
            message=message,
            artifact_html=html
        )
```

## Conclusion

By following this guide and using the provided optimization tools, you can ensure that your LLM responses will reliably trigger Open WebUI artifact rendering while maintaining token efficiency. The key is consistency in formatting and proper validation of responses before sending them to the client.

Remember:
1. Always use ```html blocks
2. Optimize for token efficiency
3. Validate responses
4. Test with your specific use case
5. Monitor performance metrics

For more examples and the latest updates, refer to the test suite in `tests/unit/test_llm_artifact_formatter.py`.