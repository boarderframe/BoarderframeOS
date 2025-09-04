"""
Artifact-Optimized API Endpoints for Open WebUI Integration
Demonstrates LLM response formatting for reliable artifact rendering
"""

from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import hashlib
import json
from datetime import datetime

from app.services.llm_artifact_formatter import (
    LLMArtifactFormatter,
    ArtifactResponseBuilder,
    ArtifactType,
    ResponsePattern,
    format_product_search_response
)

# Create router for artifact-optimized endpoints
router = APIRouter(
    prefix="/api/v1/optimized",
    tags=["artifact-optimized"],
    responses={404: {"description": "Not found"}}
)

# Initialize formatter with default settings
formatter = LLMArtifactFormatter(default_pattern=ResponsePattern.DIRECT_HTML)

# Response models
class ArtifactResponse(BaseModel):
    """Response model with artifact support"""
    message: str = Field(..., description="Natural language message")
    artifact_html: str = Field(..., description="HTML artifact content")
    display_instructions: str = Field(..., description="Instructions for LLM to display artifact")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    token_estimate: int = Field(..., description="Estimated token usage")


class OptimizedSearchResponse(BaseModel):
    """Token-optimized search response"""
    summary: str = Field(..., description="Brief search summary")
    items: List[Dict[str, Any]] = Field(..., description="Minimal item data")
    artifact_id: str = Field(..., description="Reference to cached artifact")
    display_html: str = Field(..., description="HTML block for direct inclusion")


# In-memory artifact cache
artifact_cache = {}


@router.get("/search/products", response_model=ArtifactResponse)
async def search_products_optimized(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=10, description="Result limit"),
    pattern: str = Query("direct_html", description="Response pattern: direct_html, structured_json, hybrid_natural, minimal_token")
):
    """
    Search products with optimized artifact response
    
    This endpoint demonstrates how to format responses for guaranteed
    Open WebUI artifact rendering while maintaining token efficiency.
    """
    
    # Map string to enum
    pattern_map = {
        "direct_html": ResponsePattern.DIRECT_HTML,
        "structured_json": ResponsePattern.STRUCTURED_JSON,
        "hybrid_natural": ResponsePattern.HYBRID_NATURAL,
        "minimal_token": ResponsePattern.MINIMAL_TOKEN
    }
    response_pattern = pattern_map.get(pattern, ResponsePattern.DIRECT_HTML)
    
    # Simulate product search (replace with actual search logic)
    products = simulate_product_search(query, limit)
    
    # Generate artifact HTML
    if not products:
        artifact_html = formatter.generate_empty_state_artifact(
            f"No products found for '{query}'",
            "Try different search terms or browse categories"
        )
        message = f"Your search for '{query}' returned no results."
        artifact_type = ArtifactType.EMPTY_STATE
    else:
        artifact_html = formatter.create_product_grid_artifact(products, max_items=limit)
        message = f"Found {len(products)} products matching '{query}'."
        artifact_type = ArtifactType.PRODUCT_GRID
    
    # Format response with chosen pattern
    formatted_response = formatter.format_response(
        message=message,
        artifact_html=artifact_html,
        artifact_type=artifact_type,
        pattern=response_pattern,
        optimize_tokens=True
    )
    
    # Create display instructions for LLM
    display_instructions = formatter.create_display_instructions(
        artifact_html,
        instruction_level="concise"
    )
    
    # Estimate token usage
    token_estimate = len(formatted_response) // 4
    
    return ArtifactResponse(
        message=message,
        artifact_html=artifact_html,
        display_instructions=display_instructions,
        metadata={
            "query": query,
            "result_count": len(products),
            "pattern_used": pattern,
            "artifact_type": artifact_type.value,
            "optimized": True
        },
        token_estimate=token_estimate
    )


@router.get("/search/minimal", response_model=OptimizedSearchResponse)
async def search_minimal_tokens(
    query: str = Query(..., description="Search query"),
    limit: int = Query(3, ge=1, le=5, description="Result limit (max 5 for token efficiency)")
):
    """
    Ultra-minimal token search response
    
    Returns the absolute minimum data needed for display,
    with pre-rendered HTML artifact for visual presentation.
    """
    
    # Search products
    products = simulate_product_search(query, limit)
    
    # Generate and cache artifact
    artifact_html = formatter.create_product_grid_artifact(products, max_items=limit)
    artifact_id = hashlib.md5(f"{query}-{limit}-{datetime.now().isoformat()}".encode()).hexdigest()[:8]
    
    # Cache the artifact
    artifact_cache[artifact_id] = {
        "html": artifact_html,
        "created": datetime.now().isoformat(),
        "query": query
    }
    
    # Create minimal item list (name and price only)
    minimal_items = [
        {
            "n": product["name"][:20],  # Truncated name
            "p": product["price"]  # Price only
        }
        for product in products[:limit]
    ]
    
    # Format for direct HTML inclusion
    display_html = f"```html\n{artifact_html}\n```"
    
    return OptimizedSearchResponse(
        summary=f"{len(products)} results",
        items=minimal_items,
        artifact_id=artifact_id,
        display_html=display_html
    )


@router.get("/artifact/{artifact_id}")
async def get_cached_artifact(
    artifact_id: str,
    format: str = Query("html", description="Response format: html, json, instructions")
):
    """
    Retrieve cached artifact by ID
    
    Allows retrieval of pre-rendered artifacts for display
    without regenerating the HTML content.
    """
    
    if artifact_id not in artifact_cache:
        raise HTTPException(status_code=404, detail="Artifact not found or expired")
    
    artifact_data = artifact_cache[artifact_id]
    
    if format == "html":
        # Return raw HTML for direct rendering
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=artifact_data["html"])
    
    elif format == "instructions":
        # Return display instructions for LLM
        instructions = formatter.create_display_instructions(
            artifact_data["html"],
            instruction_level="detailed"
        )
        return {"instructions": instructions}
    
    else:  # json
        # Return full artifact data
        return {
            "artifact_id": artifact_id,
            "html": artifact_data["html"],
            "created": artifact_data["created"],
            "query": artifact_data.get("query", "unknown"),
            "display_instructions": f"```html\n{artifact_data['html']}\n```"
        }


@router.post("/validate/response")
async def validate_llm_response(
    request: Request
):
    """
    Validate that an LLM response will trigger artifact rendering
    
    Send the LLM's response in the request body to validate
    whether it will successfully render artifacts in Open WebUI.
    """
    
    body = await request.json()
    response_text = body.get("response", "")
    
    if not response_text:
        raise HTTPException(status_code=400, detail="No response text provided")
    
    # Validate the response
    is_valid, issues = formatter.validate_response(response_text)
    extracted_artifact = formatter.extract_artifact(response_text)
    
    # Calculate metrics
    token_estimate = len(response_text) // 4
    artifact_detected = extracted_artifact is not None
    artifact_length = len(extracted_artifact) if extracted_artifact else 0
    
    # Generate recommendations
    recommendations = []
    
    if not artifact_detected:
        recommendations.append("Add ```html code block to include artifact")
    
    if token_estimate > 1000:
        recommendations.append(f"Reduce response size (currently ~{token_estimate} tokens)")
    
    if extracted_artifact and "<script" in extracted_artifact.lower():
        recommendations.append("Remove script tags for security")
    
    if not response_text.startswith("```html") and "```html" in response_text:
        recommendations.append("Consider placing artifact after explanation text")
    
    return {
        "valid": is_valid,
        "issues": issues,
        "metrics": {
            "token_estimate": token_estimate,
            "artifact_detected": artifact_detected,
            "artifact_length": artifact_length,
            "response_length": len(response_text)
        },
        "recommendations": recommendations,
        "artifact_preview": extracted_artifact[:200] if extracted_artifact else None
    }


@router.post("/format/builder")
async def build_formatted_response(
    request: Request
):
    """
    Build a formatted response using the builder pattern
    
    Provides a flexible way to construct artifact responses
    with various options and patterns.
    """
    
    body = await request.json()
    
    # Extract parameters
    message = body.get("message", "")
    artifact_html = body.get("artifact_html", "")
    context = body.get("context", None)
    artifact_type = body.get("artifact_type", "product_grid")
    pattern = body.get("pattern", "direct_html")
    optimize = body.get("optimize_tokens", True)
    
    # Map strings to enums
    type_map = {
        "product_grid": ArtifactType.PRODUCT_GRID,
        "product_list": ArtifactType.PRODUCT_LIST,
        "chart": ArtifactType.CHART,
        "table": ArtifactType.TABLE,
        "empty_state": ArtifactType.EMPTY_STATE
    }
    
    pattern_map = {
        "direct_html": ResponsePattern.DIRECT_HTML,
        "structured_json": ResponsePattern.STRUCTURED_JSON,
        "hybrid_natural": ResponsePattern.HYBRID_NATURAL,
        "minimal_token": ResponsePattern.MINIMAL_TOKEN
    }
    
    # Build response
    builder = ArtifactResponseBuilder()
    response = (
        builder
        .with_message(message)
        .with_artifact(artifact_html)
        .with_context(context)
        .with_type(type_map.get(artifact_type, ArtifactType.PRODUCT_GRID))
        .with_pattern(pattern_map.get(pattern, ResponsePattern.DIRECT_HTML))
        .optimize_tokens(optimize)
        .build()
    )
    
    # Validate the built response
    is_valid, issues = formatter.validate_response(response)
    
    return {
        "formatted_response": response,
        "valid": is_valid,
        "issues": issues,
        "token_estimate": len(response) // 4,
        "pattern_used": pattern,
        "optimized": optimize
    }


@router.get("/templates/prompts")
async def get_prompt_templates():
    """
    Get prompt templates for different LLM models
    
    Returns optimized prompt templates that ensure
    consistent artifact inclusion across different LLMs.
    """
    
    return {
        "gpt4_prompt": """You are a helpful assistant that formats responses with HTML artifacts for visual display.

IMPORTANT: When providing search results or data visualizations:
1. Start with a brief text explanation
2. Include HTML content in a ```html code block
3. End with any additional context

Example format:
I found 5 products matching your search.

```html
<div class="results">...</div>
```

All items are available for immediate delivery.""",
        
        "claude_prompt": """You are Claude, an AI assistant that provides rich visual responses using HTML artifacts.

When responding with search results or data:
- First explain what you found in natural language
- Then include the HTML artifact using ```html blocks
- The HTML will be rendered visually in the interface
- Keep responses concise and token-efficient

Always include artifacts for visual data presentation.""",
        
        "open_source_prompt": """Format responses with HTML artifacts for display.

Rules:
- Use ```html for code blocks
- Place HTML after text
- Keep responses short
- Include artifacts always

Format: [text] ```html [content] ``` [context]""",
        
        "function_calling_template": {
            "name": "display_with_artifact",
            "description": "Display response with HTML artifact",
            "parameters": {
                "message": "Text message",
                "artifact_html": "HTML content to display",
                "context": "Additional context (optional)"
            },
            "response_format": "message\n\n```html\nartifact_html\n```\n\ncontext"
        }
    }


@router.get("/test/patterns")
async def test_response_patterns():
    """
    Test different response patterns with sample data
    
    Returns examples of each response pattern for testing
    and comparison of token efficiency and rendering.
    """
    
    # Sample data
    sample_products = [
        {"name": "Organic Milk", "price": 4.99, "description": "Fresh organic whole milk"},
        {"name": "Almond Milk", "price": 3.49, "description": "Unsweetened almond milk"}
    ]
    
    sample_html = formatter.create_product_grid_artifact(sample_products)
    
    # Generate responses in each pattern
    patterns = {}
    
    for pattern in ResponsePattern:
        response = formatter.format_response(
            message="Found 2 products",
            artifact_html=sample_html,
            context="Available today",
            pattern=pattern,
            optimize_tokens=True
        )
        
        patterns[pattern.value] = {
            "response": response,
            "token_estimate": len(response) // 4,
            "length": len(response),
            "has_artifact": "```html" in response or '"artifact"' in response
        }
    
    return {
        "patterns": patterns,
        "recommendation": "Use 'direct_html' for best Open WebUI compatibility",
        "most_efficient": min(patterns.items(), key=lambda x: x[1]["token_estimate"])[0]
    }


# Helper functions
def simulate_product_search(query: str, limit: int) -> List[Dict[str, Any]]:
    """
    Simulate product search results
    Replace with actual search implementation
    """
    
    # Generate mock products based on query
    if not query or query.lower() == "empty":
        return []
    
    products = []
    for i in range(min(limit, 10)):
        products.append({
            "name": f"{query.title()} Product {i+1}",
            "price": round(2.99 + (i * 1.5), 2),
            "description": f"High quality {query} product with excellent reviews",
            "in_stock": i % 2 == 0,
            "rating": 4.5 - (i * 0.1)
        })
    
    return products


@router.get("/health")
async def health_check():
    """Health check endpoint for artifact-optimized API"""
    return {
        "status": "healthy",
        "service": "artifact-optimized-api",
        "formatter_ready": formatter is not None,
        "cache_size": len(artifact_cache),
        "timestamp": datetime.now().isoformat()
    }