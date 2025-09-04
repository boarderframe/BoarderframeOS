"""
Enhanced Kroger MCP Server with MCP-UI SDK Integration
Combines the existing Kroger API functionality with the new MCP-UI SDK
for rich interactive UI components in chat interfaces.

Port: 9005
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path as FilePath

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Import MCP UI Protocol from utils directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from mcp_ui_protocol import (
    MCPUIGenerator, UIRegistrationPayload, ThemeSettings,
    InitMessage, ActionMessage, PROTOCOL_VERSION
)

# Import existing UI infrastructure
from mcp_ui_infrastructure import MCPUIService, MCPUIResource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# FastAPI app initialization
app = FastAPI(
    title="Enhanced Kroger MCP Server with UI SDK",
    description="Kroger API integration with MCP-UI SDK for interactive components",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_version="3.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize services
mcp_ui_service = MCPUIService(service_name="kroger-enhanced")
ui_generator = MCPUIGenerator()

# Enhanced mock data for better UI demonstration
demo_products = [
    {
        "id": "001",
        "name": "Premium Thick Cut Bacon",
        "brand": "Wright Brand",
        "price": 8.99,
        "size": "16 oz",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1528607929212-2636ec44b55b?w=400&h=300&fit=crop",
        "description": "Delicious thick-cut bacon perfect for breakfast",
        "category": "Meat & Seafood",
        "discount": 15,
        "original_price": 10.58,
        "rating": 4.8,
        "nutrition": {"calories": 140, "protein": "12g", "fat": "11g"}
    },
    {
        "id": "002", 
        "name": "Organic Free Range Eggs",
        "brand": "Happy Egg Co",
        "price": 5.49,
        "size": "12 count",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400&h=300&fit=crop",
        "description": "Fresh organic eggs from free-range chickens",
        "category": "Dairy & Eggs",
        "discount": 0,
        "original_price": 5.49,
        "rating": 4.9,
        "nutrition": {"calories": 70, "protein": "6g", "fat": "5g"}
    },
    {
        "id": "003",
        "name": "Whole Milk",
        "brand": "Horizon Organic",
        "price": 4.99,
        "size": "1 gallon",
        "available": False,
        "image_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=300&fit=crop",
        "description": "Organic whole milk from grass-fed cows",
        "category": "Dairy & Eggs",
        "discount": 0,
        "original_price": 4.99,
        "rating": 4.7,
        "nutrition": {"calories": 150, "protein": "8g", "fat": "8g"}
    },
    {
        "id": "004",
        "name": "Artisan Sourdough Bread",
        "brand": "Dave's Killer Bread",
        "price": 4.29,
        "size": "24 oz",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=400&h=300&fit=crop",
        "description": "Organic artisan sourdough bread with seeds",
        "category": "Bakery",
        "discount": 8,
        "original_price": 4.67,
        "rating": 4.6,
        "nutrition": {"calories": 120, "protein": "5g", "fat": "2g"}
    },
    {
        "id": "005",
        "name": "Fresh Atlantic Salmon",
        "brand": "Wild Catch",
        "price": 12.99,
        "size": "1 lb",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=300&fit=crop",
        "description": "Fresh wild-caught Atlantic salmon fillet",
        "category": "Meat & Seafood",
        "discount": 20,
        "original_price": 16.24,
        "rating": 4.9,
        "nutrition": {"calories": 206, "protein": "22g", "fat": "12g"}
    },
    {
        "id": "006",
        "name": "Organic Baby Spinach",
        "brand": "Fresh Express",
        "price": 3.79,
        "size": "5 oz",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop",
        "description": "Organic baby spinach leaves, pre-washed",
        "category": "Produce",
        "discount": 0,
        "original_price": 3.79,
        "rating": 4.5,
        "nutrition": {"calories": 20, "protein": "2g", "fat": "0g"}
    },
    {
        "id": "007",
        "name": "Greek Yogurt Vanilla",
        "brand": "Chobani",
        "price": 1.29,
        "size": "5.3 oz",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1571212515416-6ae7b0e8e800?w=400&h=300&fit=crop",
        "description": "Creamy Greek yogurt with vanilla flavor",
        "category": "Dairy & Eggs",
        "discount": 12,
        "original_price": 1.47,
        "rating": 4.7,
        "nutrition": {"calories": 150, "protein": "15g", "fat": "0g"}
    },
    {
        "id": "008",
        "name": "Avocados",
        "brand": "Organic",
        "price": 2.49,
        "size": "2 count",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=400&h=300&fit=crop",
        "description": "Ripe organic Hass avocados",
        "category": "Produce",
        "discount": 0,
        "original_price": 2.49,
        "rating": 4.4,
        "nutrition": {"calories": 320, "protein": "4g", "fat": "29g"}
    },
    {
        "id": "009",
        "name": "Grass-Fed Ground Beef",
        "brand": "Nature's Reserve",
        "price": 7.99,
        "size": "1 lb",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1558030137-b69bb70b07e3?w=400&h=300&fit=crop",
        "description": "85% lean grass-fed ground beef",
        "category": "Meat & Seafood",
        "discount": 10,
        "original_price": 8.88,
        "rating": 4.8,
        "nutrition": {"calories": 240, "protein": "20g", "fat": "17g"}
    },
    {
        "id": "010",
        "name": "Honey Crisp Apples",
        "brand": "Organic",
        "price": 4.99,
        "size": "3 lb bag",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=400&h=300&fit=crop",
        "description": "Sweet and crispy organic Honey Crisp apples",
        "category": "Produce",
        "discount": 0,
        "original_price": 4.99,
        "rating": 4.6,
        "nutrition": {"calories": 80, "protein": "0g", "fat": "0g"}
    },
    {
        "id": "011",
        "name": "Artisan Cheddar Cheese",
        "brand": "Tillamook",
        "price": 6.49,
        "size": "8 oz",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400&h=300&fit=crop",
        "description": "Sharp aged cheddar cheese, extra sharp",
        "category": "Dairy & Eggs",
        "discount": 5,
        "original_price": 6.83,
        "rating": 4.9,
        "nutrition": {"calories": 110, "protein": "7g", "fat": "9g"}
    },
    {
        "id": "012",
        "name": "Sourdough Bagels",
        "brand": "Thomas'",
        "price": 3.99,
        "size": "6 count",
        "available": True,
        "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop",
        "description": "Fresh sourdough bagels, pre-sliced",
        "category": "Bakery",
        "discount": 0,
        "original_price": 3.99,
        "rating": 4.3,
        "nutrition": {"calories": 260, "protein": "10g", "fat": "2g"}
    }
]

demo_shopping_list = [
    {"id": "list_001", "name": "Bacon", "quantity": 2, "completed": False},
    {"id": "list_002", "name": "Eggs", "quantity": 1, "completed": True},
    {"id": "list_003", "name": "Milk", "quantity": 1, "completed": False},
    {"id": "list_004", "name": "Bread", "quantity": 1, "completed": False},
]

# Pydantic models
class ProductSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for products")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=50)
    theme: Optional[str] = Field("light", description="UI theme (light/dark)")

class UIComponentRequest(BaseModel):
    component_type: str = Field(..., description="Type of UI component to generate")
    data: Dict[str, Any] = Field(..., description="Data for the component")
    theme_settings: Optional[Dict[str, Any]] = Field(None, description="Theme customization")

class ShoppingListRequest(BaseModel):
    action: str = Field(..., description="Action to perform (add, toggle, remove)")
    item_data: Optional[Dict[str, Any]] = Field(None, description="Item data for add action")


# ============================================================================
# MCP-UI SDK Integration Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check with UI SDK information"""
    return {
        "status": "healthy",
        "service": "kroger-mcp-enhanced",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "mcp_ui_sdk": True,
            "interactive_components": True,
            "theme_support": True,
            "artifact_generation": True,
            "protocol_version": PROTOCOL_VERSION
        }
    }

@app.get("/ui/registry")
async def get_ui_registry():
    """Get registry of available UI components"""
    return {
        "ui_components": [
            {
                "ui_name": "Kroger Product Search",
                "ui_url_template": "http://localhost:9005/ui/product-search?query={query}&theme={theme}",
                "description": "Interactive product search with visual cards and filtering",
                "capabilities": ["search", "filter", "add_to_cart", "product_details"],
                "tool_association": "product_search",
                "data_type_handled": "grocery_products",
                "permissions": {
                    "required_scopes": ["read:products"],
                    "optional_scopes": ["write:cart", "read:user_preferences"]
                },
                "protocol_support": {
                    "min_version": "1.0.0",
                    "target_version": "1.0.0"
                }
            },
            {
                "ui_name": "Smart Shopping List",
                "ui_url_template": "http://localhost:9005/ui/shopping-list?theme={theme}",
                "description": "Interactive shopping list with item management",
                "capabilities": ["add_item", "toggle_completion", "remove_item", "bulk_actions"],
                "tool_association": "shopping_list",
                "data_type_handled": "shopping_list",
                "permissions": {
                    "required_scopes": ["read:shopping_list"],
                    "optional_scopes": ["write:shopping_list", "manage:list_items"]
                },
                "protocol_support": {
                    "min_version": "1.0.0",
                    "target_version": "1.0.0"
                }
            },
            {
                "ui_name": "Product Comparison",
                "ui_url_template": "http://localhost:9005/ui/product-compare?ids={product_ids}&theme={theme}",
                "description": "Side-by-side product comparison with detailed specs",
                "capabilities": ["compare_products", "highlight_differences", "price_analysis"],
                "tool_association": "product_compare",
                "data_type_handled": "product_comparison",
                "permissions": {
                    "required_scopes": ["read:products"],
                    "optional_scopes": ["read:price_history"]
                },
                "protocol_support": {
                    "min_version": "1.0.0",
                    "target_version": "1.0.0"
                }
            }
        ],
        "protocol_version": PROTOCOL_VERSION,
        "server_capabilities": ["interactive_ui", "theme_support", "real_time_updates"]
    }

@app.post("/ui/generate")
@limiter.limit("30/minute")
async def generate_ui_component(request: UIComponentRequest):
    """Generate UI components using MCP-UI SDK"""
    try:
        theme = None
        if request.theme_settings:
            theme = ThemeSettings(
                mode=request.theme_settings.get("mode", "light"),
                primary_color=request.theme_settings.get("primary_color"),
                secondary_color=request.theme_settings.get("secondary_color"),
                font_family=request.theme_settings.get("font_family"),
                border_radius=request.theme_settings.get("border_radius")
            )
        
        if request.component_type == "product_card":
            artifact = ui_generator.create_product_card_ui(request.data, theme)
        elif request.component_type == "shopping_list":
            items = request.data.get("items", [])
            artifact = ui_generator.create_shopping_list_ui(items, theme)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown component type: {request.component_type}")
        
        return {
            "artifact": artifact,
            "component_type": request.component_type,
            "protocol_version": PROTOCOL_VERSION,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error generating UI component: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ui/product-search", response_class=HTMLResponse)
@limiter.limit("50/minute")
async def product_search_ui(
    request: Request,
    query: str = Query(..., description="Search query"),
    theme: str = Query("light", description="UI theme"),
    limit: int = Query(10, description="Max results")
):
    """Generate interactive product search UI"""
    try:
        # Filter demo products based on query
        filtered_products = [
            p for p in demo_products 
            if query.lower() in p["name"].lower() or query.lower() in p["brand"].lower()
        ][:limit]
        
        if not filtered_products:
            # Show all products if no matches
            filtered_products = demo_products[:limit]
        
        # Create theme settings
        theme_settings = ThemeSettings(
            mode=theme,
            primary_color="#0066cc" if theme == "light" else "#4a9eff",
            secondary_color="#004499" if theme == "light" else "#357ab8",
            font_family="system-ui, -apple-system, sans-serif",
            border_radius="8px"
        )
        
        # Generate enhanced product search UI
        search_ui_html = generate_enhanced_product_search_ui(
            products=filtered_products,
            search_query=query,
            theme=theme_settings
        )
        
        return HTMLResponse(content=search_ui_html)
    
    except Exception as e:
        logger.error(f"Error generating product search UI: {e}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", status_code=500)

@app.get("/ui/shopping-list", response_class=HTMLResponse)
@limiter.limit("50/minute")
async def shopping_list_ui(
    request: Request,
    theme: str = Query("light", description="UI theme")
):
    """Generate interactive shopping list UI"""
    try:
        theme_settings = ThemeSettings(
            mode=theme,
            primary_color="#059669" if theme == "light" else "#10b981",
            secondary_color="#047857" if theme == "light" else "#0d9488",
            font_family="system-ui, -apple-system, sans-serif",
            border_radius="6px"
        )
        
        artifact = ui_generator.create_shopping_list_ui(demo_shopping_list, theme_settings)
        return HTMLResponse(content=artifact["content"])
    
    except Exception as e:
        logger.error(f"Error generating shopping list UI: {e}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", status_code=500)

@app.post("/ui/shopping-list/action")
@limiter.limit("100/minute")
async def shopping_list_action(request_data: ShoppingListRequest, request: Request):
    """Handle shopping list actions via UI components"""
    try:
        global demo_shopping_list
        
        if request_data.action == "add":
            if not request_data.item_data or "name" not in request_data.item_data:
                raise HTTPException(status_code=400, detail="Item name required for add action")
            
            new_item = {
                "id": f"list_{int(time.time())}",
                "name": request_data.item_data["name"],
                "quantity": request_data.item_data.get("quantity", 1),
                "completed": False
            }
            demo_shopping_list.append(new_item)
            
        elif request_data.action == "toggle":
            item_id = request_data.item_data.get("item_id") if request_data.item_data else None
            if not item_id:
                raise HTTPException(status_code=400, detail="Item ID required for toggle action")
            
            for item in demo_shopping_list:
                if item["id"] == item_id:
                    item["completed"] = not item["completed"]
                    break
            
        elif request_data.action == "remove":
            item_id = request_data.item_data.get("item_id") if request_data.item_data else None
            if not item_id:
                raise HTTPException(status_code=400, detail="Item ID required for remove action")
            
            demo_shopping_list = [item for item in demo_shopping_list if item["id"] != item_id]
        
        return {
            "success": True,
            "action": request_data.action,
            "shopping_list": demo_shopping_list,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error handling shopping list action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/search/enhanced")
@limiter.limit("50/minute")
async def enhanced_product_search(
    request: Request,
    query: str = Query(..., description="Search query"),
    theme: str = Query("light", description="UI theme"),
    return_ui: bool = Query(True, description="Return UI artifact")
):
    """Enhanced product search with UI artifacts"""
    try:
        # Filter products
        filtered_products = [
            p for p in demo_products 
            if query.lower() in p["name"].lower() or query.lower() in p["brand"].lower()
        ]
        
        if not filtered_products:
            filtered_products = demo_products
        
        if return_ui:
            # Generate UI resource using existing infrastructure
            ui_resource = mcp_ui_service.create_product_cards_resource(
                products=filtered_products,
                template_type="grid",
                search_query=query
            )
            
            # Also create MCP-UI SDK artifact
            theme_settings = ThemeSettings(mode=theme)
            sdk_artifacts = []
            
            for product in filtered_products[:3]:  # Create individual product cards
                product_artifact = ui_generator.create_product_card_ui(product, theme_settings)
                sdk_artifacts.append(product_artifact)
            
            return {
                "products": filtered_products,
                "search_query": query,
                "ui_resource": ui_resource.dict(),
                "sdk_artifacts": sdk_artifacts,
                "total_results": len(filtered_products),
                "protocol_version": PROTOCOL_VERSION,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "products": filtered_products,
                "search_query": query,
                "total_results": len(filtered_products)
            }
    
    except Exception as e:
        logger.error(f"Error in enhanced product search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ui/resources/{resource_id}")
async def get_ui_resource(resource_id: str):
    """Get UI resource by ID - MCP-UI Protocol compliant"""
    try:
        # For demo, create a resource based on the ID
        if "product-search" in resource_id:
            query = "bacon"  # Default query
            theme_settings = ThemeSettings(mode="light")
            
            # Filter products for the search
            filtered_products = [
                p for p in demo_products 
                if query.lower() in p["name"].lower() or query.lower() in p["brand"].lower()
            ]
            
            if not filtered_products:
                filtered_products = demo_products[:6]  # Show first 6 products
            
            # Generate the enhanced UI
            ui_html = generate_enhanced_product_search_ui(filtered_products, query, theme_settings)
            
            return {
                "uri": f"ui://kroger/{resource_id}",
                "mimeType": "text/html",
                "content": ui_html,
                "metadata": {
                    "component": "product-search",
                    "query": query,
                    "product_count": len(filtered_products),
                    "protocol_version": PROTOCOL_VERSION,
                    "capabilities": ["interactive", "responsive", "mcp-ui-compliant"],
                    "created_at": datetime.now().isoformat()
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Resource not found")
    
    except Exception as e:
        logger.error(f"Error getting UI resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/product_search_ui")
@limiter.limit("30/minute")
async def product_search_ui_tool(
    request: Request,
    query: str = Query(..., description="Search query"),
    theme: str = Query("light", description="UI theme")
):
    """MCP Tool for product search with UI - returns proper UI resource"""
    try:
        # Filter products
        filtered_products = [
            p for p in demo_products 
            if query.lower() in p["name"].lower() or query.lower() in p["brand"].lower()
        ]
        
        if not filtered_products:
            filtered_products = demo_products[:8]  # Show first 8 if no matches
        
        # Create theme settings
        theme_settings = ThemeSettings(
            mode=theme,
            primary_color="#0ea5e9" if theme == "light" else "#38bdf8",
            secondary_color="#0284c7" if theme == "light" else "#0369a1"
        )
        
        # Generate the UI
        ui_html = generate_enhanced_product_search_ui(filtered_products, query, theme_settings)
        
        # Create resource ID
        resource_id = f"product-search-{query}-{theme}-{len(filtered_products)}"
        
        # Return MCP-UI compliant response
        return {
            "text": f"Found {len(filtered_products)} products for '{query}'. Interactive UI available below:",
            "ui_resources": {
                f"ui://kroger/{resource_id}": {
                    "uri": f"ui://kroger/{resource_id}",
                    "mimeType": "text/html",
                    "content": ui_html,
                    "metadata": {
                        "component": "product-search",
                        "query": query,
                        "theme": theme,
                        "product_count": len(filtered_products),
                        "protocol_version": PROTOCOL_VERSION,
                        "capabilities": [
                            "interactive", "responsive", "add_to_cart", 
                            "favorites", "filtering", "quantity_control"
                        ],
                        "created_at": datetime.now().isoformat()
                    }
                }
            },
            "metadata": {
                "search_query": query,
                "results_count": len(filtered_products),
                "ui_protocol": "MCP-UI v1.0.0"
            }
        }
    
    except Exception as e:
        logger.error(f"Error in product search UI tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Enhanced UI Generation Functions
# ============================================================================

def generate_enhanced_product_search_ui(products: List[Dict], search_query: str, theme: ThemeSettings) -> str:
    """Generate enhanced product search UI with MCP-UI SDK integration"""
    
    # Generate product cards with enhanced design
    cards_html = ""
    for i, product in enumerate(products):
        availability_class = "available" if product["available"] else "unavailable"
        price_display = f"${product['price']:.2f}"
        
        # Handle discount pricing
        has_discount = product.get('discount', 0) > 0
        discount_html = ""
        price_html = f'<span class="current-price">{price_display}</span>'
        
        if has_discount:
            original_price = f"${product.get('original_price', product['price']):.2f}"
            discount_html = f'<span class="discount-badge">-{product["discount"]}%</span>'
            price_html = f'''
                <div class="price-group">
                    <span class="current-price">{price_display}</span>
                    <span class="original-price">{original_price}</span>
                </div>
            '''
        
        # Rating stars
        rating = product.get('rating', 0)
        stars_html = ""
        for star in range(5):
            if star < int(rating):
                stars_html += "★"
            elif star < rating:
                stars_html += "☆"
            else:
                stars_html += "☆"
        
        # Category color coding
        category_colors = {
            "Meat & Seafood": "#dc2626",
            "Dairy & Eggs": "#f59e0b", 
            "Produce": "#10b981",
            "Bakery": "#8b5cf6",
            "Pantry": "#6b7280"
        }
        category_color = category_colors.get(product.get('category', 'Pantry'), '#6b7280')
        
        cards_html += f"""
        <div class="product-card {availability_class}" data-product-id="{product['id']}">
            <div class="product-image-container">
                {discount_html}
                <img src="{product.get('image_url', '')}" 
                     alt="{product['name']}" 
                     class="product-image"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                />
                <div class="product-placeholder" style="display: none;">
                    <div class="placeholder-icon">🛒</div>
                    <span class="placeholder-text">{product.get('category', 'Product')}</span>
                </div>
                <div class="availability-badge {availability_class}">{('In Stock' if product['available'] else 'Out of Stock')}</div>
                <div class="quick-actions">
                    <button class="quick-view" onclick="quickView('{product['id']}')" title="Quick View">👁️</button>
                    <button class="add-to-favorites" onclick="toggleFavorite('{product['id']}')" title="Add to Favorites">♡</button>
                </div>
            </div>
            <div class="product-info">
                <div class="category-brand">
                    <span class="category" style="color: {category_color}">
                        {product.get('category', 'Product')}
                    </span>
                    <span class="brand">{product['brand']}</span>
                </div>
                <h3 class="product-name">{product['name']}</h3>
                <div class="product-details">
                    <span class="size">{product['size']}</span>
                    <div class="rating">
                        <span class="stars">{stars_html}</span>
                        <span class="rating-value">({rating})</span>
                    </div>
                </div>
                <p class="description">{product['description']}</p>
                <div class="nutrition-info">
                    <span class="calories">{product.get('nutrition', {}).get('calories', 0)} cal</span>
                    <span class="protein">{product.get('nutrition', {}).get('protein', '0g')} protein</span>
                </div>
                <div class="price-section">
                    {price_html}
                    <div class="actions">
                        <button class="quantity-btn minus" onclick="changeQuantity('{product['id']}', -1)">-</button>
                        <span class="quantity" id="qty-{product['id']}">1</span>
                        <button class="quantity-btn plus" onclick="changeQuantity('{product['id']}', 1)">+</button>
                        <button class="add-btn {'disabled' if not product['available'] else ''}" 
                                onclick="addToCart('{product['id']}')" 
                                {'disabled' if not product['available'] else ''}>
                            {'Add to Cart' if product['available'] else 'Unavailable'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
        """
    
    dark_mode = theme.mode == "dark"
    bg_color = "#f8fafc" if not dark_mode else "#0f172a"
    text_color = "#1f2937" if not dark_mode else "#f1f5f9"
    card_bg = "#ffffff" if not dark_mode else "#1e293b"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kroger Product Search - {search_query}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            :root {{
                --primary-color: {theme.primary_color or '#0ea5e9'};
                --secondary-color: {theme.secondary_color or '#0284c7'};
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --error-color: #ef4444;
                --font-family: 'Inter', {theme.font_family or 'system-ui, -apple-system, sans-serif'};
                --border-radius: {theme.border_radius or '12px'};
                --bg-color: {bg_color};
                --text-color: {text_color};
                --card-bg: {card_bg};
                --border-color: {'#334155' if dark_mode else '#e2e8f0'};
                --shadow: {'0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)' if dark_mode else '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'};
            }}
            
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: var(--font-family);
                background: var(--bg-color);
                color: var(--text-color);
                padding: 24px;
                min-height: 100vh;
                line-height: 1.6;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 32px;
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M20 20c0-11.046-8.954-20-20-20v20h20zm20 0c0-11.046-8.954-20-20-20v20h20z'/%3E%3C/g%3E%3C/svg%3E");
                opacity: 0.1;
            }}
            
            .header > * {{ position: relative; z-index: 2; }}
            
            .header h1 {{
                font-size: 3rem;
                margin-bottom: 12px;
                font-weight: 700;
                background: linear-gradient(45deg, #ffffff, #e2e8f0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .header .subtitle {{
                font-size: 1.25rem;
                opacity: 0.9;
                font-weight: 500;
            }}
            
            .search-info {{
                display: flex;
                justify-content: center;
                gap: 24px;
                margin: 20px 0;
                flex-wrap: wrap;
            }}
            
            .search-stat {{
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(10px);
                padding: 12px 20px;
                border-radius: calc(var(--border-radius) / 2);
                font-size: 0.95rem;
                font-weight: 600;
                border: 1px solid rgba(255,255,255,0.2);
            }}
            
            .products-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 24px;
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .product-card {{
                background: var(--card-bg);
                border-radius: var(--border-radius);
                border: 1px solid var(--border-color);
                overflow: hidden;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                box-shadow: var(--shadow);
            }}
            
            .product-card:hover {{
                transform: translateY(-8px);
                box-shadow: {'0 25px 50px -12px rgba(0, 0, 0, 0.4)' if dark_mode else '0 25px 50px -12px rgba(0, 0, 0, 0.25)'};
            }}
            
            .product-card.unavailable {{
                opacity: 0.6;
                filter: grayscale(0.5);
            }}
            
            .product-image-container {{
                position: relative;
                height: 240px;
                overflow: hidden;
                background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            }}
            
            .product-image {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: transform 0.3s ease;
            }}
            
            .product-card:hover .product-image {{
                transform: scale(1.05);
            }}
            
            .product-placeholder {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
            }}
            
            .placeholder-icon {{
                font-size: 4rem;
                margin-bottom: 8px;
            }}
            
            .placeholder-text {{
                font-size: 1.1rem;
                font-weight: 600;
                opacity: 0.9;
            }}
            
            .discount-badge {{
                position: absolute;
                top: 12px;
                left: 12px;
                background: var(--error-color);
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 700;
                z-index: 3;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            .availability-badge {{
                position: absolute;
                top: 12px;
                right: 12px;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                z-index: 3;
                backdrop-filter: blur(10px);
            }}
            
            .availability-badge.available {{
                background: rgba(16, 185, 129, 0.9);
                color: white;
            }}
            
            .availability-badge.unavailable {{
                background: rgba(239, 68, 68, 0.9);
                color: white;
            }}
            
            .quick-actions {{
                position: absolute;
                bottom: 12px;
                right: 12px;
                display: flex;
                gap: 8px;
                opacity: 0;
                transition: opacity 0.3s ease;
            }}
            
            .product-card:hover .quick-actions {{
                opacity: 1;
            }}
            
            .quick-view, .add-to-favorites {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                border: none;
                background: rgba(255,255,255,0.9);
                color: var(--text-color);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
                transition: all 0.2s ease;
                backdrop-filter: blur(10px);
            }}
            
            .quick-view:hover, .add-to-favorites:hover {{
                background: var(--primary-color);
                color: white;
                transform: scale(1.1);
            }}
            
            .product-info {{
                padding: 24px;
            }}
            
            .category-brand {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }}
            
            .category {{
                font-size: 0.8rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .brand {{
                font-size: 0.85rem;
                color: {'#94a3b8' if dark_mode else '#64748b'};
                font-weight: 500;
            }}
            
            .product-name {{
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 12px;
                line-height: 1.3;
                color: var(--text-color);
            }}
            
            .product-details {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }}
            
            .size {{
                font-size: 0.9rem;
                color: {'#94a3b8' if dark_mode else '#64748b'};
                font-weight: 500;
            }}
            
            .rating {{
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            
            .stars {{
                color: #fbbf24;
                font-size: 0.9rem;
                line-height: 1;
            }}
            
            .rating-value {{
                font-size: 0.8rem;
                color: {'#94a3b8' if dark_mode else '#64748b'};
                font-weight: 500;
            }}
            
            .description {{
                font-size: 0.9rem;
                color: {'#cbd5e1' if dark_mode else '#64748b'};
                line-height: 1.5;
                margin-bottom: 16px;
            }}
            
            .nutrition-info {{
                display: flex;
                gap: 16px;
                margin-bottom: 20px;
                padding: 12px;
                background: {'#334155' if dark_mode else '#f8fafc'};
                border-radius: 8px;
                border: 1px solid var(--border-color);
            }}
            
            .calories, .protein {{
                font-size: 0.8rem;
                font-weight: 600;
                color: {'#94a3b8' if dark_mode else '#64748b'};
            }}
            
            .price-section {{
                display: flex;
                flex-direction: column;
                gap: 16px;
            }}
            
            .price-group {{
                display: flex;
                align-items: baseline;
                gap: 8px;
            }}
            
            .current-price {{
                font-size: 1.75rem;
                font-weight: 700;
                color: var(--success-color);
            }}
            
            .original-price {{
                font-size: 1.2rem;
                color: {'#94a3b8' if dark_mode else '#64748b'};
                text-decoration: line-through;
                font-weight: 500;
            }}
            
            .actions {{
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .quantity-btn {{
                width: 36px;
                height: 36px;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                background: var(--card-bg);
                color: var(--text-color);
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .quantity-btn:hover {{
                background: var(--primary-color);
                color: white;
                border-color: var(--primary-color);
            }}
            
            .quantity {{
                min-width: 32px;
                text-align: center;
                font-weight: 600;
                font-size: 1.1rem;
            }}
            
            .add-btn {{
                flex: 1;
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 0.95rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .add-btn:hover:not(.disabled) {{
                background: var(--secondary-color);
                transform: translateY(-2px);
            }}
            
            .add-btn.disabled {{
                background: {'#475569' if dark_mode else '#e2e8f0'};
                color: {'#94a3b8' if dark_mode else '#64748b'};
                cursor: not-allowed;
                transform: none;
            }}
            
            .filters-bar {{
                display: flex;
                justify-content: center;
                gap: 16px;
                margin-bottom: 32px;
                flex-wrap: wrap;
            }}
            
            .filter-btn {{
                padding: 8px 16px;
                border: 1px solid var(--border-color);
                background: var(--card-bg);
                color: var(--text-color);
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            
            .filter-btn:hover, .filter-btn.active {{
                background: var(--primary-color);
                color: white;
                border-color: var(--primary-color);
            }}
            
            .mcp-ui-controls {{
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: var(--card-bg);
                padding: 20px;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
                backdrop-filter: blur(10px);
                z-index: 1000;
            }}
            
            .mcp-ui-controls h4 {{
                margin-bottom: 12px;
                font-size: 0.95rem;
                color: var(--primary-color);
                font-weight: 600;
            }}
            
            .mcp-ui-controls button {{
                display: block;
                width: 100%;
                margin-bottom: 8px;
                padding: 10px 16px;
                background: var(--primary-color);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 0.85rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            
            .mcp-ui-controls button:hover {{
                background: var(--secondary-color);
                transform: translateY(-1px);
            }}
            
            @keyframes fadeInUp {{
                from {{
                    opacity: 0;
                    transform: translateY(30px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .product-card {{
                animation: fadeInUp 0.5s ease forwards;
            }}
            
            .product-card:nth-child(2) {{ animation-delay: 0.1s; }}
            .product-card:nth-child(3) {{ animation-delay: 0.2s; }}
            .product-card:nth-child(4) {{ animation-delay: 0.3s; }}
            .product-card:nth-child(5) {{ animation-delay: 0.4s; }}
            .product-card:nth-child(6) {{ animation-delay: 0.5s; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛒 {search_query.title()}</h1>
            <div class="subtitle">Kroger Product Search • Enhanced with MCP-UI SDK</div>
            <div class="search-info">
                <div class="search-stat">{len(products)} Products Found</div>
                <div class="search-stat">Query: "{search_query}"</div>
                <div class="search-stat">Theme: {theme.mode.title()}</div>
            </div>
        </div>
        
        <div class="filters-bar">
            <button class="filter-btn active" onclick="filterProducts('all')">All Products</button>
            <button class="filter-btn" onclick="filterProducts('Meat & Seafood')">🥩 Meat & Seafood</button>
            <button class="filter-btn" onclick="filterProducts('Dairy & Eggs')">🥛 Dairy & Eggs</button>
            <button class="filter-btn" onclick="filterProducts('Produce')">🥬 Produce</button>
            <button class="filter-btn" onclick="filterProducts('Bakery')">🍞 Bakery</button>
        </div>
        
        <div class="products-grid">
            {cards_html}
        </div>
        
        <div class="mcp-ui-controls">
            <h4>🎮 MCP-UI Actions</h4>
            <button onclick="sendMCPAction('refresh_search')">🔄 Refresh</button>
            <button onclick="sendMCPAction('view_cart')">🛒 View Cart (0)</button>
            <button onclick="sendMCPAction('change_theme')">🎨 Toggle Theme</button>
            <button onclick="sendMCPAction('export_list')">📋 Export List</button>
            <button onclick="sendMCPAction('sort_by_price')">💰 Sort by Price</button>
        </div>
        
        <script>
            // MCP-UI SDK Integration
            console.log('🚀 MCP-UI Enhanced Product Search loaded');
            console.log('📋 Protocol Version: {PROTOCOL_VERSION}');
            console.log('🎨 Theme Mode: {theme.mode}');
            
            // Global state
            let cartItems = 0;
            let favorites = new Set();
            let quantities = {{}};
            
            // Initialize quantities
            document.querySelectorAll('.product-card').forEach(card => {{
                const productId = card.dataset.productId;
                quantities[productId] = 1;
            }});
            
            // Product interaction functions
            function addToCart(productId) {{
                console.log('🛒 Adding product to cart:', productId);
                
                const quantity = quantities[productId] || 1;
                cartItems += quantity;
                
                // Update cart button
                const cartBtn = document.querySelector('[onclick="sendMCPAction(\'view_cart\')"]');
                if (cartBtn) {{
                    cartBtn.innerHTML = `🛒 View Cart (${{cartItems}})`;
                }}
                
                // Send MCP-UI action message
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: 'add_to_cart',
                        payload: {{
                            product_id: productId,
                            quantity: quantity,
                            cart_total: cartItems,
                            source: 'enhanced_search_ui',
                            timestamp: new Date().toISOString()
                        }}
                    }}, '*');
                }}
                
                // Visual feedback with animation
                const button = event.target;
                const originalText = button.textContent;
                const card = button.closest('.product-card');
                
                button.textContent = 'Added! ✓';
                button.style.background = 'var(--success-color)';
                button.style.transform = 'scale(0.95)';
                
                // Add success animation to card
                card.style.transform = 'scale(1.02)';
                card.style.boxShadow = '0 20px 40px rgba(16, 185, 129, 0.2)';
                
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.style.background = '';
                    button.style.transform = '';
                    card.style.transform = '';
                    card.style.boxShadow = '';
                }}, 1500);
                
                // Show floating notification
                showNotification(`Added ${{quantity}}x to cart! 🎉`, 'success');
            }}
            
            function changeQuantity(productId, delta) {{
                const currentQty = quantities[productId] || 1;
                const newQty = Math.max(1, Math.min(10, currentQty + delta));
                quantities[productId] = newQty;
                
                const qtyElement = document.getElementById(`qty-${{productId}}`);
                if (qtyElement) {{
                    qtyElement.textContent = newQty;
                    qtyElement.style.transform = 'scale(1.2)';
                    qtyElement.style.color = 'var(--primary-color)';
                    
                    setTimeout(() => {{
                        qtyElement.style.transform = '';
                        qtyElement.style.color = '';
                    }}, 200);
                }}
                
                console.log(`📦 Updated quantity for ${{productId}}: ${{newQty}}`);
            }}
            
            function quickView(productId) {{
                console.log('👁️ Quick view for product:', productId);
                
                // Send MCP action
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: 'quick_view_product',
                        payload: {{
                            product_id: productId,
                            timestamp: new Date().toISOString()
                        }}
                    }}, '*');
                }}
                
                showNotification('Opening quick view... 👀', 'info');
            }}
            
            function toggleFavorite(productId) {{
                const isFavorite = favorites.has(productId);
                const heartBtn = event.target;
                
                if (isFavorite) {{
                    favorites.delete(productId);
                    heartBtn.textContent = '♡';
                    heartBtn.style.color = '';
                    showNotification('Removed from favorites 💔', 'info');
                }} else {{
                    favorites.add(productId);
                    heartBtn.textContent = '❤️';
                    heartBtn.style.color = '#ef4444';
                    showNotification('Added to favorites! ❤️', 'success');
                }}
                
                console.log(`💝 Toggled favorite for ${{productId}}:`, !isFavorite);
                
                // Send MCP action
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: 'toggle_favorite',
                        payload: {{
                            product_id: productId,
                            is_favorite: !isFavorite,
                            favorites_count: favorites.size,
                            timestamp: new Date().toISOString()
                        }}
                    }}, '*');
                }}
            }}
            
            function filterProducts(category) {{
                console.log('🔍 Filtering products by category:', category);
                
                const cards = document.querySelectorAll('.product-card');
                const filterBtns = document.querySelectorAll('.filter-btn');
                
                // Update filter button states
                filterBtns.forEach(btn => {{
                    btn.classList.remove('active');
                    if (btn.textContent.includes(category) || (category === 'all' && btn.textContent.includes('All'))) {{
                        btn.classList.add('active');
                    }}
                }});
                
                // Filter cards with animation
                cards.forEach((card, index) => {{
                    const productCategory = card.querySelector('.category').textContent.trim();
                    const shouldShow = category === 'all' || productCategory === category;
                    
                    if (shouldShow) {{
                        card.style.display = 'block';
                        card.style.animation = `fadeInUp 0.5s ease ${{index * 0.1}}s forwards`;
                    }} else {{
                        card.style.display = 'none';
                    }}
                }});
                
                // Update header stats
                const visibleCards = Array.from(cards).filter(card => card.style.display !== 'none');
                const headerSubtitle = document.querySelector('.header .subtitle');
                if (headerSubtitle) {{
                    const categoryText = category === 'all' ? 'All Categories' : category;
                    headerSubtitle.textContent = `Kroger Product Search • ${{categoryText}} • ${{visibleCards.length}} items`;
                }}
            }}
            
            function sendMCPAction(actionName) {{
                console.log('📤 Sending MCP action:', actionName);
                
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'action',
                        action_name: actionName,
                        payload: {{
                            search_query: '{search_query}',
                            product_count: {len(products)},
                            cart_items: cartItems,
                            favorites_count: favorites.size,
                            theme: '{theme.mode}',
                            timestamp: new Date().toISOString()
                        }}
                    }}, '*');
                }}
                
                // Visual feedback for different actions
                const actionMessages = {{
                    'refresh_search': '🔄 Refreshing search results...',
                    'view_cart': `🛒 Opening cart with ${{cartItems}} items...`,
                    'change_theme': '🎨 Switching theme...',
                    'export_list': '📋 Exporting product list...',
                    'sort_by_price': '💰 Sorting by price...'
                }};
                
                showNotification(actionMessages[actionName] || `✨ ${{actionName}}...`, 'info');
            }}
            
            function showNotification(message, type = 'info') {{
                const notification = document.createElement('div');
                const colors = {{
                    success: '#10b981',
                    error: '#ef4444',
                    warning: '#f59e0b',
                    info: '#0ea5e9'
                }};
                
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${{colors[type]}};
                    color: white;
                    padding: 16px 24px;
                    border-radius: 8px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                    z-index: 10000;
                    font-weight: 600;
                    font-size: 14px;
                    transform: translateX(100%);
                    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    backdrop-filter: blur(10px);
                `;
                notification.textContent = message;
                
                document.body.appendChild(notification);
                
                // Slide in
                requestAnimationFrame(() => {{
                    notification.style.transform = 'translateX(0)';
                }});
                
                // Auto-hide
                setTimeout(() => {{
                    notification.style.transform = 'translateX(100%)';
                    setTimeout(() => {{
                        if (notification.parentNode) {{
                            document.body.removeChild(notification);
                        }}
                    }}, 300);
                }}, 3000);
            }}
            
            // Notify parent that UI is ready
            window.addEventListener('load', function() {{
                console.log('✅ Product search UI fully loaded');
                
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'ready',
                        ui_name: 'Kroger Product Search',
                        protocol_version: '{PROTOCOL_VERSION}',
                        capabilities: [
                            'product_search', 'add_to_cart', 'quantity_control',
                            'favorites', 'filtering', 'theme_support', 'quick_view'
                        ],
                        product_count: {len(products)},
                        theme: '{theme.mode}',
                        timestamp: new Date().toISOString()
                    }}, '*');
                }}
                
                showNotification('🛒 Product search ready!', 'success');
            }});
            
            // Listen for theme updates from parent
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'theme') {{
                    console.log('🎨 Received theme update:', event.data.theme_settings);
                    showNotification('🎨 Theme updated!', 'info');
                }}
                
                if (event.data.type === 'update_context') {{
                    console.log('📝 Context updated:', event.data.context);
                }}
            }});
            
            // Add keyboard shortcuts
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    // Clear all filters
                    filterProducts('all');
                }}
                
                if (e.key === 'c' && e.ctrlKey) {{
                    // Open cart
                    sendMCPAction('view_cart');
                    e.preventDefault();
                }}
            }});
            
            // Add intersection observer for animations
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }}
                }});
            }}, {{ threshold: 0.1 }});
            
            document.querySelectorAll('.product-card').forEach(card => {{
                observer.observe(card);
            }});
        </script>
    </body>
    </html>
    """


# ============================================================================
# UI Template Serving Routes (MCP-UI Protocol Compliance)
# ============================================================================

# Mount static files for UI templates
ui_templates_path = FilePath(__file__).parent / "ui_templates"
if ui_templates_path.exists():
    app.mount("/ui/static", StaticFiles(directory=str(ui_templates_path / "static")), name="ui_static")

@app.get("/ui/template/{template_name}", response_class=HTMLResponse)
async def serve_ui_template(
    template_name: str,
    theme: str = Query("default", description="Theme name")
):
    """Serve UI templates with dynamic data injection - MCP-UI Protocol compliant"""
    try:
        template_path = ui_templates_path / "components" / f"{template_name}.html"
        
        if not template_path.exists():
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
        
        # Read the template
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Load theme settings
        theme_path = ui_templates_path / "themes" / f"{theme}.json"
        theme_settings = {"primary_color": "#0ea5e9", "secondary_color": "#0284c7"}
        
        if theme_path.exists():
            with open(theme_path, 'r', encoding='utf-8') as f:
                theme_settings.update(json.load(f))
        
        # Template replacement
        rendered_content = template_content
        rendered_content = rendered_content.replace('{{service_name}}', 'Kroger MCP Enhanced')
        rendered_content = rendered_content.replace('{{theme.primary_color}}', theme_settings.get('primary_color', '#0ea5e9'))
        rendered_content = rendered_content.replace('{{theme.secondary_color}}', theme_settings.get('secondary_color', '#0284c7'))
        rendered_content = rendered_content.replace('{{theme.success_color}}', theme_settings.get('success_color', '#10b981'))
        rendered_content = rendered_content.replace('{{theme.danger_color}}', theme_settings.get('danger_color', '#ef4444'))
        
        # Inject demo data for the template
        demo_data = {
            "title": f"Kroger {template_name.title().replace('-', ' ')}",
            "description": "Interactive MCP-UI component",
            "products": demo_products[:6]  # Limit to 6 products for template
        }
        
        # Replace data placeholder
        rendered_content = rendered_content.replace('{{{data}}}', json.dumps(demo_data))
        
        return HTMLResponse(content=rendered_content)
        
    except Exception as e:
        logger.error(f"Error serving UI template {template_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Template serving error: {str(e)}")

@app.get("/ui/roots")
async def list_ui_roots():
    """List available UI roots - MCP-UI Protocol discovery endpoint"""
    base_url = "http://localhost:9006"
    
    return {
        "ui_roots": [
            {
                "id": "product-grid",
                "name": "Product Grid",
                "description": "Interactive product grid with shopping features",
                "url": f"{base_url}/ui/template/product-grid",
                "icon": "🛒",
                "metadata": {
                    "component_type": "grid",
                    "data_types": ["products"],
                    "interactions": ["add_to_cart", "view_details"]
                }
            },
            {
                "id": "shopping-cart",
                "name": "Shopping Cart",
                "description": "Interactive shopping cart management",
                "url": f"{base_url}/ui/template/shopping-cart",
                "icon": "🛍️",
                "metadata": {
                    "component_type": "cart",
                    "data_types": ["cart_items"],
                    "interactions": ["update_quantity", "remove_item", "checkout"]
                }
            },
            {
                "id": "product-detail",
                "name": "Product Detail",
                "description": "Detailed product view with purchase options",
                "url": f"{base_url}/ui/template/product-detail",
                "icon": "📦",
                "metadata": {
                    "component_type": "detail",
                    "data_types": ["product"],
                    "interactions": ["add_to_cart", "favorite", "share"]
                }
            }
        ],
        "protocol_version": "1.0.0",
        "server_info": {
            "name": "kroger-mcp-enhanced",
            "version": "2.0.0",
            "capabilities": ["ui_serving", "theme_support", "dynamic_data"]
        }
    }

@app.get("/mcp/tools/search_products_ui")
async def mcp_tool_search_products_ui(
    query: str = Query(..., description="Search query for products"),
    theme: str = Query("default", description="UI theme")
):
    """MCP Tool endpoint that returns proper ui_resources for Open WebUI integration"""
    try:
        # Filter products based on query
        filtered_products = [p for p in demo_products if query.lower() in p["name"].lower() or query.lower() in p["description"].lower()]
        
        if not filtered_products:
            filtered_products = demo_products[:3]  # Fallback to first 3 products
        
        # Get the UI template URL that the server will serve
        ui_template_url = f"http://localhost:9006/ui/template/product-grid?theme={theme}"
        
        # Create the MCP-UI Protocol compliant response
        ui_resource_id = f"ui://kroger/product-search-{query.replace(' ', '-')}-{theme}-{int(time.time())}"
        
        return {
            "text": f"Found {len(filtered_products)} products for '{query}'. Interactive UI available below:",
            "ui_resources": {
                ui_resource_id: {
                    "uri": ui_resource_id,
                    "mimeType": "text/html",
                    "content": ui_template_url,  # Point to our served template
                    "metadata": {
                        "product_count": len(filtered_products),
                        "search_query": query,
                        "template_type": "product-grid",
                        "theme": theme,
                        "server_url": "http://localhost:9006",
                        "protocol_version": "1.0.0",
                        "created_at": datetime.now().isoformat()
                    }
                }
            },
            "expires_in": 3600,
            "metadata": {
                "mcp_ui_protocol": "1.0.0",
                "server_name": "kroger-mcp-enhanced",
                "interaction_model": "iframe_postmessage"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in MCP tool search_products_ui: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/ui/iframe/{resource_id}")
async def serve_mcp_ui_iframe(resource_id: str, theme: str = Query("default")):
    """Serve the actual iframe content for MCP UI resources"""
    try:
        # Extract the template type from resource_id
        if "product-search" in resource_id:
            template_name = "product-grid"
        elif "shopping-cart" in resource_id:
            template_name = "shopping-cart" 
        else:
            template_name = "product-grid"  # Default fallback
            
        # Redirect to our template serving endpoint
        return await serve_ui_template(template_name, theme)
        
    except Exception as e:
        logger.error(f"Error serving MCP UI iframe for {resource_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Application Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup event with UI SDK initialization"""
    logger.info("Starting Enhanced Kroger MCP Server with UI SDK...")
    logger.info(f"MCP-UI Protocol Version: {PROTOCOL_VERSION}")
    logger.info("UI Components registered: Product Search, Shopping List, Product Comparison")
    logger.info("Enhanced Kroger MCP Server started successfully on port 9005 with MCP-UI SDK integration")

@app.on_event("shutdown") 
async def shutdown_event():
    """Shutdown event"""
    logger.info("Enhanced Kroger MCP Server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9006, reload=False)