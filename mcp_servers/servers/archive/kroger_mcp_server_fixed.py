"""
Kroger MCP Server - Fixed JSON Response Version
Ensures clean JSON responses without streaming or SSE formatting
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Kroger MCP Server - Fixed",
    description="Clean JSON response version without SSE/streaming",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Response Models
# ============================================================================

class ProductItem(BaseModel):
    """Minimal product representation"""
    id: str
    name: str
    brand: Optional[str] = None
    price: float
    size: Optional[str] = None
    image_url: Optional[str] = None
    in_stock: bool = True

class LLMReadyResponse(BaseModel):
    """Response model for LLM-ready endpoint"""
    llm_response: str
    artifact_available: bool
    artifact_html: Optional[str] = None
    fallback_text: str
    search_term: str
    product_count: int
    instructions: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SimpleJSONResponse(BaseModel):
    """Simple JSON response for testing"""
    status: str
    message: str
    data: Dict[str, Any]
    timestamp: str

# ============================================================================
# Mock Data for Testing
# ============================================================================

def get_mock_products(term: str, limit: int) -> List[ProductItem]:
    """Generate mock product data for testing"""
    mock_products = {
        "milk": [
            ProductItem(
                id="001",
                name="Kroger® Vitamin D Whole Milk Gallon",
                brand="Kroger",
                price=2.99,
                size="1 gal",
                image_url="https://www.kroger.com/product/images/medium/front/0001111040101"
            ),
            ProductItem(
                id="002",
                name="Kroger® 2% Reduced Fat Milk Half Gallon",
                brand="Kroger",
                price=1.99,
                size="1/2 gal",
                image_url="https://www.kroger.com/product/images/medium/front/0001111041600"
            ),
            ProductItem(
                id="003",
                name="Simple Truth® Organic Whole Milk",
                brand="Simple Truth",
                price=4.99,
                size="1 gal",
                image_url="https://www.kroger.com/product/images/medium/front/0001111082123"
            )
        ],
        "bread": [
            ProductItem(
                id="004",
                name="Kroger® White Bread",
                brand="Kroger",
                price=1.29,
                size="20 oz",
                image_url="https://www.kroger.com/product/images/medium/front/0001111087200"
            ),
            ProductItem(
                id="005",
                name="Dave's Killer Bread® 21 Whole Grains",
                brand="Dave's Killer Bread",
                price=5.99,
                size="27 oz",
                image_url="https://www.kroger.com/product/images/medium/front/0001356400021"
            )
        ]
    }
    
    products = mock_products.get(term.lower(), [])
    if not products:
        # Generate generic products for any search term
        products = [
            ProductItem(
                id=f"gen_{i}",
                name=f"{term.title()} Product {i+1}",
                brand="Generic",
                price=2.99 + i,
                size="Standard",
                image_url=f"https://via.placeholder.com/150?text={term}"
            )
            for i in range(min(3, limit))
        ]
    
    return products[:limit]

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint with explicit JSON response"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "kroger-mcp-server-fixed"
        },
        media_type="application/json"
    )

@app.get("/test/json")
async def test_json_response() -> JSONResponse:
    """Test endpoint to verify clean JSON responses"""
    return JSONResponse(
        content={
            "status": "success",
            "message": "This is a clean JSON response",
            "data": {
                "test_key": "test_value",
                "numbers": [1, 2, 3],
                "nested": {
                    "level": 2,
                    "value": "nested_value"
                }
            },
            "timestamp": datetime.now().isoformat()
        },
        media_type="application/json",
        headers={
            "X-Response-Type": "json",
            "Cache-Control": "no-cache"
        }
    )

@app.get("/products/search/llm-ready", response_model=LLMReadyResponse)
async def search_products_llm_ready(
    term: str = Query(..., description="Product search term"),
    limit: int = Query(6, ge=1, le=12, description="Number of products (1-12)")
) -> JSONResponse:
    """
    Fixed LLM-ready endpoint that returns clean JSON responses.
    No SSE, no streaming, just pure JSON.
    """
    try:
        # Get mock products
        products = get_mock_products(term, limit)
        
        if not products:
            response_data = LLMReadyResponse(
                llm_response=f"No products found for '{term}'. Please try a different search term.",
                artifact_available=False,
                artifact_html=None,
                fallback_text=f"No {term} products available.",
                search_term=term,
                product_count=0,
                instructions="No products to display.",
                metadata={"timestamp": datetime.now().isoformat()}
            )
            return JSONResponse(
                content=response_data.dict(),
                media_type="application/json"
            )
        
        # Generate HTML artifact
        html_content = generate_html_artifact(products, term)
        
        # Calculate price range
        prices = [p.price for p in products]
        min_price = min(prices)
        max_price = max(prices)
        
        # Create LLM-ready response
        llm_response_text = f"""Found {len(products)} {term} products available for delivery:

```html
{html_content}
```

**Product Summary:**
- {len(products)} items available
- All items available for delivery
- Prices range from ${min_price:.2f} to ${max_price:.2f}"""
        
        # Create response data
        response_data = LLMReadyResponse(
            llm_response=llm_response_text,
            artifact_available=True,
            artifact_html=html_content,
            fallback_text=f"Found {len(products)} {term} products: " + 
                         ", ".join([f"{p.name} (${p.price:.2f})" for p in products[:3]]) + 
                         ("..." if len(products) > 3 else ""),
            search_term=term,
            product_count=len(products),
            instructions="Copy the 'llm_response' field directly into your chat response. The HTML code block will automatically render as a visual artifact in Open WebUI.",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "api_version": "1.0.0",
                "response_format": "json"
            }
        )
        
        # Return clean JSON response
        return JSONResponse(
            content=response_data.dict(),
            media_type="application/json",
            headers={
                "X-Response-Type": "json",
                "X-API-Version": "1.0.0",
                "Cache-Control": "max-age=300"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in search_products_llm_ready: {e}")
        error_response = {
            "error": str(e),
            "llm_response": f"Error searching for '{term}': {str(e)}",
            "artifact_available": False,
            "artifact_html": None,
            "fallback_text": f"Error searching for {term}",
            "search_term": term,
            "product_count": 0,
            "instructions": "An error occurred. Please try again.",
            "metadata": {"timestamp": datetime.now().isoformat()}
        }
        return JSONResponse(
            content=error_response,
            status_code=500,
            media_type="application/json"
        )

@app.get("/products/search/simple")
async def search_products_simple(
    term: str = Query(..., description="Product search term"),
    limit: int = Query(6, ge=1, le=12, description="Number of products")
) -> JSONResponse:
    """
    Simple endpoint that returns products as clean JSON array.
    No HTML, no formatting, just data.
    """
    try:
        products = get_mock_products(term, limit)
        
        return JSONResponse(
            content={
                "success": True,
                "search_term": term,
                "count": len(products),
                "products": [p.dict() for p in products],
                "timestamp": datetime.now().isoformat()
            },
            media_type="application/json"
        )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "search_term": term,
                "products": [],
                "timestamp": datetime.now().isoformat()
            },
            status_code=500,
            media_type="application/json"
        )

# ============================================================================
# Helper Functions
# ============================================================================

def generate_html_artifact(products: List[ProductItem], search_term: str) -> str:
    """Generate clean HTML artifact for product display"""
    
    product_cards = ""
    for product in products:
        price_display = f"${product.price:.2f}" if product.price > 0 else "Price N/A"
        display_name = product.name[:40] + '...' if len(product.name) > 40 else product.name
        
        product_cards += f"""
        <div class="card">
            <div class="img">
                <div class="status">In Stock</div>
                <img src="{product.image_url or ''}" alt="{display_name}" onerror="this.style.display='none'">
            </div>
            <div class="content">
                <div class="brand">{product.brand or 'Generic'}</div>
                <div class="name">{display_name}</div>
                <div class="size">{product.size or 'Standard Size'}</div>
                <div class="price-row">
                    <div class="price">{price_display}</div>
                    <button class="btn">Add</button>
                </div>
            </div>
        </div>"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{search_term} - Kroger Products</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; padding: 16px; }}
        .header {{ text-align: center; margin-bottom: 24px; padding: 20px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border-radius: 12px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .stats {{ display: flex; justify-content: center; gap: 20px; margin-top: 12px; font-size: 14px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }}
        .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-2px); }}
        .img {{ height: 160px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; position: relative; }}
        .img img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .status {{ position: absolute; top: 8px; right: 8px; background: #10b981; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
        .content {{ padding: 16px; }}
        .brand {{ color: #6b7280; font-size: 11px; text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }}
        .name {{ font-size: 14px; font-weight: 600; margin-bottom: 6px; line-height: 1.3; }}
        .size {{ color: #6b7280; font-size: 12px; margin-bottom: 8px; }}
        .price-row {{ display: flex; align-items: center; justify-content: space-between; }}
        .price {{ font-size: 18px; font-weight: 700; color: #111827; }}
        .btn {{ background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 {search_term.title()}</h1>
        <div class="stats">
            <span>{len(products)} Products</span>
            <span>Kroger Delivery</span>
        </div>
    </div>
    <div class="grid">{product_cards}
    </div>
</body>
</html>"""
    
    return html_content

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Fixed Kroger MCP Server on port 9005...")
    print("Test endpoints:")
    print("  - http://localhost:9005/health")
    print("  - http://localhost:9005/test/json")
    print("  - http://localhost:9005/products/search/simple?term=milk&limit=3")
    print("  - http://localhost:9005/products/search/llm-ready?term=milk&limit=3")
    print("  - http://localhost:9005/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9005,
        log_level="info"
    )