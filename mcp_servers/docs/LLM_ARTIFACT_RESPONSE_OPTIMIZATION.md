# LLM Artifact Response Optimization for Open WebUI

## Executive Summary

This document provides a comprehensive solution for optimizing how LLMs format responses to reliably trigger Open WebUI artifact rendering when using MCP UI Protocol. The solution focuses on prompt engineering, response templates, and token-efficient methods to ensure consistent artifact inclusion and rendering.

## Problem Statement

Open WebUI's artifact rendering system requires specific response patterns from LLMs to detect and render HTML artifacts. Without proper formatting, artifacts may not be displayed, resulting in a degraded user experience. The challenge is to:

1. Ensure LLMs consistently include artifacts in responses
2. Minimize token usage while maintaining functionality
3. Provide clear display instructions that LLMs will follow
4. Handle various artifact types (product cards, charts, interactive components)

## Solution Architecture

### 1. Optimal LLM Response Patterns

#### Pattern A: Direct HTML Code Block (Most Reliable)
```markdown
Here are the search results for "organic milk":

```html
<div class="product-grid">
  <div class="product-card">
    <h3>Organic Whole Milk</h3>
    <p class="price">$4.99</p>
    <p class="description">Fresh organic whole milk, 1 gallon</p>
  </div>
</div>
```

I found 3 products matching your search.
```

**Why it works:**
- Open WebUI automatically detects ```html blocks
- No additional parsing required
- Visual rendering triggered immediately
- Token efficient (no extra metadata)

#### Pattern B: Structured Response with Artifact Reference
```json
{
  "response": "Found 5 products for 'organic milk'",
  "artifact": {
    "type": "html",
    "content": "<div>...</div>"
  }
}
```

**Why it works:**
- Explicit artifact field
- Machine-readable format
- Easy to parse programmatically
- Supports metadata inclusion

#### Pattern C: Hybrid Natural Language + Artifact
```markdown
I found 5 organic milk products at your local store.

**Visual Display:**
```html
[HTML content here]
```

The average price is $4.99 with 2 items on sale.
```

**Why it works:**
- Natural conversation flow
- Clear artifact boundary
- Combines explanation with visualization
- User-friendly presentation

### 2. Display Instructions Structure

#### Effective Display Instructions Template
```python
display_instructions = """
ARTIFACT DISPLAY INSTRUCTIONS:
1. Include the HTML code block below in your response
2. Use ```html syntax for Open WebUI artifact detection
3. Place the artifact after your text explanation
4. Do NOT modify or summarize the HTML content

HTML ARTIFACT:
```html
{html_content}
```

USAGE: Copy the entire HTML block above (including backticks) into your response.
"""
```

#### Token-Efficient Version
```python
display_instructions = f"Display: ```html\n{html_content}\n```"
```

### 3. Response Templates for Guaranteed Rendering

#### Template 1: Product Search Results
```python
PRODUCT_SEARCH_TEMPLATE = """
{search_summary}

```html
{artifact_html}
```

{additional_context}
"""

# Example usage
response = PRODUCT_SEARCH_TEMPLATE.format(
    search_summary="Found 5 organic milk products:",
    artifact_html=ui_resource.content,
    additional_context="All products are available for pickup today."
)
```

#### Template 2: Data Visualization
```python
DATA_VIZ_TEMPLATE = """
{analysis_summary}

**Interactive Chart:**
```html
{chart_html}
```

{insights}
"""
```

#### Template 3: Interactive Components
```python
INTERACTIVE_TEMPLATE = """
{component_description}

```html
{component_html}
```

{usage_instructions}
"""
```

### 4. Token-Efficient Methods

#### Method 1: Compressed HTML with CSS Classes
```html
<!-- Instead of inline styles -->
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 16px; border-radius: 8px;">

<!-- Use classes -->
<div class="pc-1">
```

With accompanying minimal CSS:
```css
.pc-1{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:16px;border-radius:8px}
```

#### Method 2: Data Attributes for Dynamic Content
```html
<div data-product='{"id":"123","price":4.99,"name":"Milk"}' class="p-card"></div>
```

With JavaScript expansion:
```javascript
document.querySelectorAll('[data-product]').forEach(el => {
  const data = JSON.parse(el.dataset.product);
  el.innerHTML = `<h3>${data.name}</h3><p>$${data.price}</p>`;
});
```

#### Method 3: Template Literals
```python
# Server-side template generation
html_template = """<div class="grid">{cards}</div>"""
card_template = """<div class="c" data-id="{id}">{name}: ${price}</div>"""

# Generate compact HTML
cards = "".join(card_template.format(**product) for product in products[:5])
final_html = html_template.format(cards=cards)
```

### 5. Prompt Engineering for Consistent Artifact Inclusion

#### System Prompt Addition
```markdown
## Artifact Display Rules

When providing search results, data visualizations, or interactive content:

1. ALWAYS include HTML artifacts using ```html code blocks
2. Place artifacts AFTER your text explanation
3. Never summarize or modify provided HTML content
4. Include artifacts even for empty results (show "no results" message)
5. Use this format:

   [Your explanation]
   
   ```html
   [Provided HTML content]
   ```
   
   [Additional context if needed]
```

#### Function Calling Instructions
```python
def format_artifact_response(explanation: str, html_content: str, context: str = None) -> str:
    """
    Format response to ensure artifact rendering in Open WebUI
    
    Args:
        explanation: Natural language explanation
        html_content: HTML artifact content
        context: Optional additional context
    
    Returns:
        Formatted response with guaranteed artifact inclusion
    """
    response_parts = [explanation, "", "```html", html_content, "```"]
    
    if context:
        response_parts.extend(["", context])
    
    return "\n".join(response_parts)
```

### 6. Testing Strategies

#### Test Case 1: Basic Artifact Detection
```python
def test_artifact_detection():
    """Test if Open WebUI detects HTML code blocks"""
    test_responses = [
        "Results:\n```html\n<div>Test</div>\n```",
        "```html\n<div>Test</div>\n```\nResults above",
        "Found items\n\n```html\n<div>Test</div>\n```\n\nEnd"
    ]
    
    for response in test_responses:
        assert "```html" in response
        assert "```" appears at least twice
```

#### Test Case 2: Token Efficiency
```python
def test_token_efficiency():
    """Ensure responses stay within token limits"""
    html_content = generate_product_cards(products[:5])
    response = format_artifact_response(
        "Found 5 products",
        html_content,
        "Available today"
    )
    
    # Check token count (approximate)
    token_count = len(response) / 4  # Rough estimate
    assert token_count < 1000  # Target: under 1000 tokens
```

#### Test Case 3: Rendering Validation
```python
def test_rendering_validation():
    """Validate HTML structure for Open WebUI rendering"""
    html = generate_artifact_html(test_data)
    
    # Check for required elements
    assert "<div" in html
    assert "class=" in html
    assert html.count("<") == html.count(">")
    
    # Validate no problematic patterns
    assert "<script" not in html  # No inline scripts
    assert "javascript:" not in html  # No JS protocols
    assert "onerror=" not in html  # No event handlers
```

## Implementation Examples

### Example 1: Product Search with Artifacts
```python
@app.get("/products/search/optimized")
async def search_products_optimized(term: str, limit: int = 5):
    """Optimized endpoint for LLM artifact responses"""
    
    # Search products
    products = await kroger_api.search_products(term, limit)
    
    # Generate compact HTML
    html = generate_compact_html(products)
    
    # Create response with guaranteed artifact inclusion
    response = {
        "summary": f"Found {len(products)} products for '{term}'",
        "display_instructions": f"```html\n{html}\n```",
        "products": [
            {"name": p.name[:30], "price": p.price}
            for p in products
        ],
        "artifact_html": html  # Backup field for parsing
    }
    
    return response
```

### Example 2: LLM Response Handler
```python
class LLMResponseFormatter:
    """Ensures consistent artifact formatting in LLM responses"""
    
    @staticmethod
    def format_with_artifact(
        message: str,
        artifact_html: str,
        artifact_type: str = "product_grid"
    ) -> str:
        """
        Format LLM response with guaranteed artifact inclusion
        
        Args:
            message: Main response message
            artifact_html: HTML content to display
            artifact_type: Type of artifact for styling
        
        Returns:
            Formatted response with artifact
        """
        # Ensure HTML is properly formatted
        if not artifact_html.startswith("<"):
            artifact_html = f"<div class='{artifact_type}'>{artifact_html}</div>"
        
        # Build response with artifact
        response = f"""{message}

```html
{artifact_html}
```"""
        
        return response
    
    @staticmethod
    def validate_artifact_response(response: str) -> bool:
        """Validate that response will trigger artifact rendering"""
        
        # Check for HTML code block
        if "```html" not in response:
            return False
        
        # Ensure proper closing
        if response.count("```") < 2:
            return False
        
        # Extract HTML content
        start = response.index("```html") + 7
        end = response.index("```", start)
        html_content = response[start:end].strip()
        
        # Validate HTML content exists
        return len(html_content) > 0 and "<" in html_content
```

### Example 3: Prompt Template for Claude/GPT
```python
ARTIFACT_RESPONSE_PROMPT = """
You are responding to a product search query. Follow these rules:

1. Start with a brief summary of the results
2. Include the HTML artifact using ```html blocks
3. End with any additional helpful information

Response format:
[Summary]

```html
[HTML artifact - DO NOT MODIFY]
```

[Additional information]

Now respond to: {user_query}

Products found: {product_count}
HTML artifact: {html_artifact}
"""
```

## Best Practices

### 1. Always Include Artifacts
- Even for empty results, include an artifact showing "No results found"
- This maintains UI consistency and user expectations

### 2. Use Consistent Formatting
- Always use ```html for code blocks
- Place artifacts in predictable locations (after explanation)
- Maintain the same structure across all responses

### 3. Optimize for Token Efficiency
- Use CSS classes instead of inline styles
- Compress HTML where possible
- Limit product cards to 5-10 items
- Use data attributes for dynamic content

### 4. Test with Multiple LLMs
- Test response formatting with GPT-4, Claude, and open-source models
- Validate artifact detection across different response styles
- Ensure prompts work consistently across models

### 5. Provide Fallbacks
```python
# Include both artifact and structured data
response = {
    "message": "Found 5 products",
    "artifact_html": html_content,  # For parsing
    "display": f"```html\n{html_content}\n```"  # For rendering
}
```

## Monitoring and Validation

### Metrics to Track
1. **Artifact Inclusion Rate**: % of responses with artifacts
2. **Rendering Success Rate**: % of artifacts successfully rendered
3. **Token Usage**: Average tokens per response
4. **User Engagement**: Interaction with rendered artifacts

### Validation Checklist
- [ ] HTML code blocks properly formatted
- [ ] Artifacts appear after text explanation
- [ ] Token count within limits (<1000 tokens)
- [ ] HTML validates without errors
- [ ] No JavaScript security issues
- [ ] Responsive design works
- [ ] Empty state handled gracefully

## Conclusion

This optimization framework ensures reliable artifact rendering in Open WebUI through:

1. **Consistent Response Patterns**: Using ```html blocks reliably
2. **Clear Instructions**: Explicit display_instructions field
3. **Token Efficiency**: Compressed HTML and smart templating
4. **Robust Testing**: Validation across multiple scenarios
5. **Prompt Engineering**: System prompts that enforce artifact inclusion

By implementing these patterns, LLMs will consistently produce responses that trigger Open WebUI's artifact rendering, providing users with rich, interactive visualizations while maintaining token efficiency.

## Appendix: Quick Reference

### Minimal Working Example
```python
# Server response
{
    "message": "Found products",
    "display_instructions": "```html\n<div>Product Cards</div>\n```"
}

# LLM formats as:
"I found several products for you:\n\n```html\n<div>Product Cards</div>\n```"
```

### Token-Efficient HTML Template
```html
<style>.g{display:grid;gap:8px}.c{padding:8px;border:1px solid #ddd}</style>
<div class="g">
  <div class="c">Milk $4.99</div>
  <div class="c">Bread $2.99</div>
</div>
```

### Artifact Validation Regex
```python
import re

ARTIFACT_PATTERN = r'```html\s*\n([\s\S]*?)\n```'

def extract_artifact(response: str) -> str:
    match = re.search(ARTIFACT_PATTERN, response)
    return match.group(1) if match else None
```