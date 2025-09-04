"""
Enhanced Kroger MCP Server with Guaranteed Artifact Rendering
==============================================================

This enhanced version of the Kroger MCP server implements the optimized
artifact response format to ensure reliable rendering in Open WebUI.

Key Improvements:
1. Multiple rendering strategies with automatic fallback
2. Clear LLM instructions embedded in responses
3. Compressed and optimized HTML artifacts
4. Debug mode for troubleshooting rendering issues
5. Success tracking and adaptive strategy selection
"""

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from pydantic import BaseModel, Field

# Import the optimizer
from mcp_artifact_response_optimizer import (
    ArtifactResponseOptimizer,
    GuaranteedRenderHTMLGenerator,
    MCPServerIntegration,
    ArtifactRenderStrategy,
    ArtifactPriority
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kroger MCP Server - Enhanced Artifacts",
    version="2.0.0",
    description="Kroger API integration with guaranteed Open WebUI artifact rendering"
)

# Initialize optimizer and integration
optimizer = ArtifactResponseOptimizer(
    service_name="kroger-enhanced",
    debug_mode=True,  # Enable debug for development
    max_inline_size=75000  # 75KB max for inline HTML
)

html_generator = GuaranteedRenderHTMLGenerator()
integration = MCPServerIntegration("kroger-enhanced")


# ============================================================================
# Enhanced Response Models
# ============================================================================

class EnhancedProductSearchResponse(BaseModel):
    """Enhanced response with guaranteed artifact rendering"""
    # Core data (minimal tokens)
    query: str = Field(..., description="Search query")
    count: int = Field(..., description="Number of products")
    summary: str = Field(..., description="Brief summary")
    
    # Artifact rendering (multiple strategies)
    artifact_html: str = Field(..., description="Primary HTML artifact")
    artifact_markdown: str = Field(..., description="Markdown fallback")
    artifact_instructions: str = Field(..., description="LLM rendering instructions")
    
    # Rendering metadata
    render_strategy: str = Field(..., description="Recommended rendering strategy")
    render_confidence: float = Field(..., description="Confidence in rendering success")
    
    # Debug information
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug information")


class ArtifactTestResponse(BaseModel):
    """Response for testing artifact rendering"""
    test_name: str = Field(..., description="Name of the test")
    test_html: str = Field(..., description="Test HTML content")
    expected_result: str = Field(..., description="Expected rendering result")
    instructions: str = Field(..., description="Instructions for verification")


# ============================================================================
# Enhanced Endpoints with Guaranteed Rendering
# ============================================================================

@app.get("/products/search/enhanced", response_model=EnhancedProductSearchResponse)
async def search_products_enhanced(
    term: str = Query(..., description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Max products to return"),
    render_test: bool = Query(False, description="Include rendering test")
):
    """
    🚀 Enhanced product search with GUARANTEED artifact rendering
    
    This endpoint uses multiple strategies to ensure artifacts render:
    1. Primary: HTML code blocks with ```html tags
    2. Fallback: Markdown tables for data display
    3. Emergency: Plain text with formatting
    
    IMPORTANT FOR LLMs:
    - Always include the artifact_html in your response
    - Use the exact format shown in artifact_instructions
    - If rendering fails, use artifact_markdown as fallback
    """
    
    # Mock product data (replace with actual Kroger API call)
    products = [
        {
            "name": f"Product {i} - {term}",
            "brand": "Kroger" if i % 2 == 0 else "Simple Truth",
            "price": 2.99 + (i * 0.5),
            "size": "16 oz",
            "available": i % 3 != 0,
            "upc": f"000000000{i:04d}"
        }
        for i in range(1, min(limit + 1, 21))
    ]
    
    # Generate optimized HTML artifact
    html_content = html_generator.create_product_grid(
        products,
        title=f"Search: {term}",
        max_items=limit
    )
    
    # Create markdown fallback
    markdown_content = _create_markdown_table(products)
    
    # Determine rendering strategy based on content
    strategy = _determine_best_strategy(html_content, render_test)
    
    # Create rendering instructions for LLM
    instructions = _create_llm_instructions(strategy, html_content)
    
    # Calculate rendering confidence
    confidence = _calculate_render_confidence(strategy, len(html_content))
    
    # Build response
    response = EnhancedProductSearchResponse(
        query=term,
        count=len(products),
        summary=f"Found {len(products)} products for '{term}'",
        artifact_html=_format_html_for_strategy(html_content, strategy),
        artifact_markdown=markdown_content,
        artifact_instructions=instructions,
        render_strategy=strategy.value if isinstance(strategy, ArtifactRenderStrategy) else strategy,
        render_confidence=confidence
    )
    
    # Add debug info if requested
    if render_test:
        response.debug = {
            "html_size": len(html_content),
            "markdown_size": len(markdown_content),
            "strategy_used": strategy.value if isinstance(strategy, ArtifactRenderStrategy) else strategy,
            "test_mode": True,
            "timestamp": datetime.now().isoformat()
        }
    
    return response


@app.get("/test/artifact-rendering")
async def test_artifact_rendering(
    test_type: str = Query("simple", description="Type of test: simple, complex, stress")
) -> ArtifactTestResponse:
    """
    🧪 Test endpoint for verifying artifact rendering
    
    Use this to test if artifacts are rendering correctly in Open WebUI.
    Returns different test cases based on test_type parameter.
    """
    
    if test_type == "simple":
        test_html = """<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; text-align: center;">
            <h1>✅ Artifact Rendering Test</h1>
            <p>If you can see this styled content, artifacts are working!</p>
            <button style="background: white; color: #667eea; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer;">Success!</button>
        </div>"""
        
        expected = "A purple gradient box with white text and a button"
        
    elif test_type == "complex":
        test_html = html_generator.create_product_grid(
            [{"name": f"Test Product {i}", "price": i * 10, "brand": "Test", "size": "1 unit", "available": True} 
             for i in range(1, 6)],
            title="Complex Rendering Test"
        )
        expected = "A product grid with 5 test products"
        
    else:  # stress test
        # Large HTML to test size limits
        test_html = """<div style="padding: 20px;">""" + \
                   "".join([f"<p>Line {i}: Testing artifact rendering with large content...</p>" 
                           for i in range(1, 101)]) + \
                   """</div>"""
        expected = "100 lines of test content"
    
    return ArtifactTestResponse(
        test_name=f"Artifact Rendering Test - {test_type}",
        test_html=f"```html\n{test_html}\n```",
        expected_result=expected,
        instructions=f"""
To verify artifact rendering:
1. The LLM should include the test_html in its response
2. You should see: {expected}
3. If you don't see the rendered content, check:
   - Are HTML code blocks enabled in Open WebUI?
   - Is the artifact size within limits?
   - Are inline styles being processed?

Include this HTML in your response to test:

{test_html}
"""
    )


@app.get("/artifacts/debug/{artifact_id}")
async def debug_artifact(artifact_id: str):
    """
    🔍 Debug endpoint for troubleshooting artifact rendering issues
    
    Returns detailed information about why an artifact might not be rendering.
    """
    
    # Mock debug information (replace with actual artifact lookup)
    debug_info = {
        "artifact_id": artifact_id,
        "status": "available",
        "rendering_issues": [],
        "recommendations": []
    }
    
    # Check common issues
    checks = {
        "size_check": {
            "passed": True,
            "message": "Artifact size is within limits",
            "details": "Size: 45KB (limit: 100KB)"
        },
        "format_check": {
            "passed": True,
            "message": "HTML format is valid",
            "details": "Properly formatted HTML with inline styles"
        },
        "encoding_check": {
            "passed": True,
            "message": "UTF-8 encoding verified",
            "details": "No encoding issues detected"
        },
        "style_check": {
            "passed": False,
            "message": "Some styles may not render",
            "details": "External CSS references found - use inline styles instead"
        }
    }
    
    # Add recommendations based on checks
    for check_name, check_result in checks.items():
        if not check_result["passed"]:
            debug_info["rendering_issues"].append(check_result["message"])
            debug_info["recommendations"].append(check_result["details"])
    
    # Add general recommendations
    if not debug_info["rendering_issues"]:
        debug_info["recommendations"].append("No issues detected. Artifact should render correctly.")
    
    debug_info["recommendations"].extend([
        "Ensure HTML code blocks are wrapped with ```html tags",
        "Try the /test/artifact-rendering endpoint to verify rendering",
        "Check Open WebUI console for any JavaScript errors"
    ])
    
    return debug_info


@app.post("/artifacts/validate")
async def validate_artifact(content: Dict[str, str]):
    """
    ✅ Validate HTML content for artifact rendering compatibility
    
    Send HTML content to check if it will render correctly in Open WebUI.
    """
    html_content = content.get("html", "")
    
    validation_results = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "optimizations": []
    }
    
    # Size check
    size = len(html_content)
    if size > 100000:
        validation_results["valid"] = False
        validation_results["issues"].append(f"Content too large: {size} bytes (max: 100000)")
    elif size > 50000:
        validation_results["warnings"].append(f"Large content: {size} bytes (recommended: <50000)")
    
    # Structure checks
    if not html_content.strip().startswith("<!DOCTYPE html>") and not html_content.strip().startswith("<"):
        validation_results["valid"] = False
        validation_results["issues"].append("Invalid HTML structure")
    
    # Style checks
    if "<link" in html_content and "stylesheet" in html_content:
        validation_results["warnings"].append("External stylesheets detected - use inline styles")
    
    if "<script" in html_content and "src=" in html_content:
        validation_results["warnings"].append("External scripts detected - may not load")
    
    # Optimization suggestions
    if "style=" not in html_content:
        validation_results["optimizations"].append("Add inline styles for better rendering")
    
    if size > 20000 and "minified" not in html_content.lower():
        validation_results["optimizations"].append("Consider minifying HTML to reduce size")
    
    # Add recommended fixes
    validation_results["recommended_format"] = f"""```html
{html_content[:500]}...
```"""
    
    return validation_results


# ============================================================================
# Helper Functions
# ============================================================================

def _create_markdown_table(products: List[Dict]) -> str:
    """Create markdown table as fallback display"""
    if not products:
        return "No products found."
    
    markdown = "| Product | Brand | Price | Size | Status |\n"
    markdown += "|---------|-------|-------|------|--------|\n"
    
    for p in products[:10]:  # Limit to 10 for space
        name = p.get('name', 'Unknown')[:30]
        brand = p.get('brand', '-')
        price = f"${p.get('price', 0):.2f}"
        size = p.get('size', '-')
        status = "✅ Available" if p.get('available', False) else "❌ Out of Stock"
        markdown += f"| {name} | {brand} | {price} | {size} | {status} |\n"
    
    if len(products) > 10:
        markdown += f"\n*... and {len(products) - 10} more products*"
    
    return markdown


def _determine_best_strategy(content: str, test_mode: bool) -> ArtifactRenderStrategy:
    """Determine the best rendering strategy"""
    size = len(content)
    
    if test_mode:
        return ArtifactRenderStrategy.CODE_BLOCK
    
    if size < 50000:
        return ArtifactRenderStrategy.CODE_BLOCK
    elif size < 100000:
        return ArtifactRenderStrategy.HYBRID
    else:
        return ArtifactRenderStrategy.BASE64_DATA


def _format_html_for_strategy(html: str, strategy: ArtifactRenderStrategy) -> str:
    """Format HTML based on selected strategy"""
    if strategy == ArtifactRenderStrategy.CODE_BLOCK:
        return f"```html\n{html}\n```"
    elif strategy == ArtifactRenderStrategy.INLINE_HTML:
        return html
    else:
        # For other strategies, provide code block as primary
        return f"```html\n{html}\n```"


def _create_llm_instructions(strategy: ArtifactRenderStrategy, content: str) -> str:
    """Create clear instructions for LLM"""
    size_kb = len(content) / 1024
    
    instructions = f"""
📋 RENDERING INSTRUCTIONS FOR LLM:

1. **Primary Method** ({strategy.value}):
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

5. **Content Info**:
   - Size: {size_kb:.1f} KB
   - Strategy: {strategy.value}
   - Pre-formatted: Yes

⚠️ IMPORTANT: The artifact_html is ready to render. Just include it in your response!
"""
    
    return instructions


def _calculate_render_confidence(strategy: ArtifactRenderStrategy, size: int) -> float:
    """Calculate confidence that artifact will render successfully"""
    confidence = 1.0
    
    # Adjust based on strategy
    if strategy == ArtifactRenderStrategy.CODE_BLOCK:
        confidence = 0.95
    elif strategy == ArtifactRenderStrategy.HYBRID:
        confidence = 0.85
    else:
        confidence = 0.75
    
    # Adjust based on size
    if size > 75000:
        confidence *= 0.9
    if size > 100000:
        confidence *= 0.8
    
    return min(max(confidence, 0.0), 1.0)


# ============================================================================
# Startup and Health
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize enhanced artifact system"""
    logger.info("Starting Kroger MCP Server with Enhanced Artifact Rendering")
    logger.info(f"Debug mode: {optimizer.debug_mode}")
    logger.info(f"Max inline size: {optimizer.max_inline_size} bytes")


@app.get("/health")
async def health_check():
    """Health check with artifact system status"""
    return {
        "status": "healthy",
        "service": "kroger-mcp-enhanced",
        "version": "2.0.0",
        "features": {
            "artifact_rendering": "enhanced",
            "strategies_available": [s.value for s in ArtifactRenderStrategy],
            "debug_mode": optimizer.debug_mode,
            "markdown_fallback": True,
            "validation_endpoint": True
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9005, log_level="info")