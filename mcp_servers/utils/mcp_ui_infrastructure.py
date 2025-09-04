"""
MCP UI Protocol Infrastructure
Reusable components for implementing MCP UI Protocol across all MCP servers

This module provides standard-compliant MCP UI Protocol implementation following
the official specification for interactive UI components over Model Context Protocol.
"""

import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# MCP UI Protocol Models (Standard Compliant)
# ============================================================================

class MCPUIResource(BaseModel):
    """
    MCP UI Protocol Resource - Standard compliant resource definition
    
    Based on MCP UI Protocol specification for interactive components.
    Supports text/html, text/uri-list, and application/vnd.mcp-ui.remote-dom
    """
    uri: str = Field(..., description="Resource URI with ui:// scheme")
    mimeType: str = Field(..., description="MIME type (text/html, text/uri-list, etc)")
    content: str = Field(..., description="Resource content (HTML, URL, etc)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class MCPUIResponse(BaseModel):
    """
    Base MCP UI Protocol Response
    
    Standard format for returning UI resources with minimal data for token efficiency
    """
    ui_resources: Dict[str, MCPUIResource] = Field(..., description="UI resources keyed by URI")
    content: Optional[Any] = Field(default=None, description="Additional response data")


# ============================================================================
# MCP UI Service (Reusable Infrastructure)
# ============================================================================

class MCPUIService:
    """
    Reusable MCP UI Protocol service for all MCP servers
    
    Provides standard-compliant MCP UI Protocol implementation with:
    - ui:// URI scheme support
    - Multiple MIME types (text/html, text/uri-list, remote-dom)
    - Sandboxed iframe rendering support
    - Intent-based messaging system
    """
    
    def __init__(self, service_name: str = "generic"):
        self.service_name = service_name
        print(f"MCPUIService initialized for {service_name} with MCP UI Protocol support")
    
    def create_ui_resource(self, uri_id: str, html_content: str, 
                          metadata: Optional[Dict] = None, 
                          mime_type: str = "text/html") -> MCPUIResource:
        """
        Create MCP UI Protocol resource from content
        
        Args:
            uri_id: Unique identifier for the resource
            html_content: HTML content or URL (depending on mime_type)
            metadata: Optional metadata dictionary
            mime_type: MIME type (text/html, text/uri-list, application/vnd.mcp-ui.remote-dom)
        
        Returns:
            MCPUIResource: Standard compliant UI resource
        """
        uri = f"ui://component/{uri_id}"
        
        return MCPUIResource(
            uri=uri,
            mimeType=mime_type,
            content=html_content,
            metadata=metadata or {
                "created_at": datetime.now().isoformat(),
                "service": self.service_name
            }
        )
    
    def create_html_resource(self, component_name: str, html_content: str, 
                           extra_metadata: Optional[Dict] = None) -> MCPUIResource:
        """
        Create HTML UI resource with sandboxed iframe support
        
        Args:
            component_name: Name of the component
            html_content: Complete HTML content
            extra_metadata: Additional metadata
        
        Returns:
            MCPUIResource: HTML resource ready for iframe embedding
        """
        # Create deterministic ID based on content hash (not timestamp)
        # This ensures same content always gets same ID for Open WebUI caching
        resource_id = hashlib.md5(
            f"{component_name}-{len(html_content)}-{hash(html_content)}".encode()
        ).hexdigest()[:8]
        
        metadata = {
            "component": component_name,
            "content_size": len(html_content),
            "created_at": datetime.now().isoformat(),
            "service": self.service_name,
            "rendering": "iframe_sandboxed"
        }
        
        if extra_metadata:
            metadata.update(extra_metadata)
        
        return self.create_ui_resource(
            uri_id=f"{component_name}-{resource_id}",
            html_content=html_content,
            metadata=metadata,
            mime_type="text/html"
        )
    
    def create_remote_resource(self, component_name: str, resource_url: str,
                             extra_metadata: Optional[Dict] = None) -> MCPUIResource:
        """
        Create remote UI resource that loads from external URL
        
        Args:
            component_name: Name of the component
            resource_url: External URL to load
            extra_metadata: Additional metadata
        
        Returns:
            MCPUIResource: Remote resource for iframe loading
        """
        resource_id = hashlib.md5(
            f"{component_name}-{resource_url}-{time.time()}".encode()
        ).hexdigest()[:8]
        
        metadata = {
            "component": component_name,
            "resource_url": resource_url,
            "created_at": datetime.now().isoformat(),
            "service": self.service_name,
            "rendering": "iframe_remote"
        }
        
        if extra_metadata:
            metadata.update(extra_metadata)
        
        return self.create_ui_resource(
            uri_id=f"{component_name}-remote-{resource_id}",
            html_content=resource_url,
            metadata=metadata,
            mime_type="text/uri-list"
        )
    
    def build_ui_response(self, ui_resources: List[MCPUIResource], 
                         additional_data: Optional[Any] = None) -> MCPUIResponse:
        """
        Build complete MCP UI Protocol response
        
        Args:
            ui_resources: List of UI resources
            additional_data: Optional additional response data
        
        Returns:
            MCPUIResponse: Complete MCP UI Protocol response
        """
        resources_dict = {resource.uri: resource for resource in ui_resources}
        
        return MCPUIResponse(
            ui_resources=resources_dict,
            content=additional_data
        )
    
    def create_error_resource(self, error_message: str, error_code: Optional[str] = None) -> MCPUIResource:
        """
        Create error UI resource for displaying errors
        
        Args:
            error_message: Error message to display
            error_code: Optional error code
        
        Returns:
            MCPUIResource: Error display resource
        """
        error_html = f"""
        <div style="
            padding: 20px;
            background: #fef2f2;
            border: 1px solid #fca5a5;
            border-radius: 8px;
            color: #dc2626;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            text-align: center;
        ">
            <h3 style="margin: 0 0 8px 0; font-size: 16px;">⚠️ Error</h3>
            <p style="margin: 0; font-size: 14px;">{error_message}</p>
            {f'<code style="font-size: 12px; color: #991b1b;">Error Code: {error_code}</code>' if error_code else ''}
        </div>
        """
        
        return self.create_html_resource(
            component_name="error",
            html_content=error_html,
            extra_metadata={
                "error_message": error_message,
                "error_code": error_code,
                "is_error": True
            }
        )
    
    def create_product_cards_resource(self, products: List[Dict], template_type: str = "grid", search_query: str = None) -> MCPUIResource:
        """
        Create product cards UI resource for grocery products
        
        Args:
            products: List of product dictionaries
            template_type: Type of template (grid, list, compact)
        
        Returns:
            MCPUIResource: Product cards resource ready for iframe embedding
        """
        if not products:
            return self.create_error_resource("No products to display", "NO_PRODUCTS")
        
        # Generate HTML using template system
        if template_type == "grid":
            html_content = self._generate_product_grid_html(products, search_query)
        elif template_type == "list":
            html_content = self._generate_product_list_html(products, search_query)
        else:
            html_content = self._generate_product_grid_html(products, search_query)  # Default to grid
        
        # Create stable resource with search-based ID for Open WebUI caching
        search_term = search_query or "products"
        resource_id = hashlib.md5(f"product-cards-{search_term}-{template_type}".encode()).hexdigest()[:8]
        
        return self.create_ui_resource(
            uri_id=f"product-cards-{resource_id}",
            html_content=html_content,
            metadata={
                "component": "product-cards",
                "product_count": len(products),
                "template_type": template_type,
                "search_query": search_term,
                "content_size": len(html_content),
                "created_at": datetime.now().isoformat(),
                "service": self.service_name,
                "rendering": "iframe_sandboxed",
                "total_value": sum(
                    getattr(p, "price", 0) if hasattr(p, '__dict__') else p.get("price", 0) 
                    for p in products
                )
            },
            mime_type="text/html"
        )
    
    def _generate_product_grid_html(self, products: List[Dict], search_query: str = None) -> str:
        """Generate responsive product grid HTML"""
        cards_html = ""
        
        # Generate gradients for visual appeal
        gradients = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
        ]
        
        for i, product in enumerate(products):
            # Handle both dictionaries and Pydantic models
            if hasattr(product, '__dict__'):
                # Pydantic model - access attributes directly
                name = getattr(product, 'name', 'Unknown Product')
                price_raw = getattr(product, 'price', None)
                price = float(price_raw) if price_raw is not None else 0.0
                brand = getattr(product, 'brand', '')
                size = getattr(product, 'size', '')
                available = getattr(product, 'available', False)
                upc = getattr(product, 'upc', '')
                image_url = getattr(product, 'image_url', None)
            else:
                # Dictionary - use .get() method
                name = product.get('name', 'Unknown Product')
                price_raw = product.get('price')
                price = float(price_raw) if price_raw is not None else 0.0
                brand = product.get('brand', '')
                size = product.get('size', '')
                available = product.get('available', False)
                upc = product.get('upc', '')
                image_url = product.get('image_url', None)
            
            # Clean name (remove redundant brand)
            clean_name = name.replace(f"{brand}", "").strip() if brand else name
            display_name = clean_name[:60] + "..." if len(clean_name) > 60 else clean_name
            
            # Price formatting
            price_dollars = int(price)
            price_cents = int((price - price_dollars) * 100)
            
            # Availability styling
            availability_color = '#10b981' if available else '#ef4444'
            availability_text = 'In Stock' if available else 'Out of Stock'
            card_opacity = '1' if available else '0.8'
            
            # Random gradient
            gradient = gradients[i % len(gradients)] if available else 'linear-gradient(135deg, #a8a8a8 0%, #6b6b6b 100%)'
            
            cards_html += f"""
            <div class="product-card" style="
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                overflow: hidden;
                transition: transform 0.2s, box-shadow 0.2s;
                opacity: {card_opacity};
            ">
                <div style="
                    height: 180px;
                    background: {gradient if not image_url else 'white'};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    overflow: hidden;
                ">
                    <div style="
                        position: absolute;
                        top: 12px;
                        right: 12px;
                        background: {availability_color};
                        color: white;
                        padding: 4px 10px;
                        border-radius: 20px;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        z-index: 2;
                    ">
                        {availability_text}
                    </div>
                    
                    {f'''
                    <img src="{image_url}" 
                         alt="{display_name}"
                         style="
                             width: 100%;
                             height: 100%;
                             object-fit: contain;
                             padding: 8px;
                         "
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                    />
                    <div style="
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        display: none;
                        align-items: center;
                        justify-content: center;
                        background: {gradient};
                    ">
                        <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                            <path d="M9 2L3 7v13a2 2 0 002 2h14a2 2 0 002-2V7l-6-5z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                        </svg>
                    </div>
                    ''' if image_url else f'''
                    <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <path d="M9 2L3 7v13a2 2 0 002 2h14a2 2 0 002-2V7l-6-5z"/>
                        <polyline points="9 22 9 12 15 12 15 22"/>
                    </svg>
                    '''}
                </div>
                
                <div style="padding: 16px;">
                    <div style="
                        color: #666;
                        font-size: 11px;
                        font-weight: 500;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 4px;
                    ">
                        {brand}
                    </div>
                    
                    <h3 style="
                        margin: 0 0 6px 0;
                        font-size: 14px;
                        font-weight: 600;
                        color: #222;
                        line-height: 1.3;
                        min-height: 36px;
                    ">
                        {display_name}
                    </h3>
                    
                    <div style="
                        color: #666;
                        font-size: 12px;
                        margin-bottom: 10px;
                    ">
                        {size}
                    </div>
                    
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        gap: 12px;
                    ">
                        <div style="
                            display: flex;
                            align-items: baseline;
                            gap: 2px;
                        ">
                            <span style="font-size: 12px; color: #666; font-weight: 500;">$</span>
                            <span style="font-size: 20px; font-weight: 700; color: #222;">{price_dollars}</span>
                            <span style="font-size: 14px; color: #666; font-weight: 500;">.{price_cents:02d}</span>
                        </div>
                        
                        {"<button style='background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;'>Add</button>" if available else "<span style='color: #ef4444; font-size: 11px; font-weight: 600;'>Unavailable</span>"}
                    </div>
                </div>
            </div>
            """
        
        # Data-driven UI generation based on telemetry
        product_count = len(products)
        # Use provided search query or extract from product data
        actual_search_query = search_query if search_query else self._extract_search_context(products)
        category_info = self._analyze_product_category(products, actual_search_query)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{search_query} - Kroger Products</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    background: #f8fafc; 
                    padding: 16px; 
                    color: #1f2937;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 32px;
                    padding: 24px;
                    background: linear-gradient(135deg, {category_info['primary_color']} 0%, {category_info['secondary_color']} 100%);
                    color: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
                }}
                .header h1 {{
                    font-size: 28px;
                    margin-bottom: 8px;
                    font-weight: 700;
                }}
                .header .subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                    font-weight: 500;
                }}
                .stats {{
                    display: flex;
                    justify-content: center;
                    gap: 24px;
                    margin: 16px 0;
                }}
                .stat {{
                    background: rgba(255,255,255,0.2);
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-size: 14px;
                }}
                .grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); 
                    gap: 16px; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                }}
                .product-card:hover {{ 
                    transform: translateY(-2px); 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.12); 
                }}
                .category-badge {{
                    display: inline-block;
                    background: {category_info['accent_color']};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 16px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="category-badge">{category_info['emoji']} {category_info['category']}</div>
                <h1>{actual_search_query.title()}</h1>
                <div class="subtitle">Kroger Products • {category_info['description']}</div>
                <div class="stats">
                    <div class="stat">{product_count} Products</div>
                    <div class="stat">Avg ${category_info['avg_price']:.2f}</div>
                    <div class="stat">{category_info['availability_rate']}% Available</div>
                </div>
            </div>
            
            <div class="grid">
                {cards_html}
            </div>
            
            <script>
                // Data-driven analytics
                window.mcpTelemetry = {{
                    searchQuery: '{actual_search_query}',
                    category: '{category_info['category']}',
                    productCount: {product_count},
                    avgPrice: {category_info['avg_price']},
                    timestamp: '{datetime.now().isoformat()}'
                }};
                
                console.log('MCP UI Telemetry:', window.mcpTelemetry);
            </script>
        </body>
        </html>
        """
    
    def _extract_search_context(self, products: List[Dict]) -> str:
        """Extract search context from product data"""
        if not products:
            return "products"
        
        # Try to infer search term from product names
        first_product = products[0]
        name = first_product.get('name', '') if isinstance(first_product, dict) else getattr(first_product, 'name', '')
        
        # Simple keyword extraction
        name_lower = name.lower()
        if 'bacon' in name_lower:
            return "bacon"
        elif 'egg' in name_lower:
            return "eggs"
        elif 'milk' in name_lower:
            return "milk"
        elif 'bread' in name_lower:
            return "bread"
        elif 'butter' in name_lower:
            return "butter"
        elif 'taco' in name_lower:
            return "tacos"
        elif 'pizza' in name_lower:
            return "pizza"
        elif 'ice cream' in name_lower or 'cream' in name_lower:
            return "ice cream"
        elif 'cheese' in name_lower:
            return "cheese"
        else:
            return "products"
    
    def _analyze_product_category(self, products: List[Dict], search_query: str = None) -> Dict[str, Any]:
        """Analyze product data to determine category, colors, and stats"""
        if not products:
            return self._get_default_category_info()
        
        # Calculate telemetry data
        prices = []
        available_count = 0
        
        for product in products:
            if isinstance(product, dict):
                price = product.get('price')
                available = product.get('available', False)
            else:
                price = getattr(product, 'price', None)
                available = getattr(product, 'available', False)
            
            if price is not None and price > 0:
                prices.append(float(price))
            if available:
                available_count += 1
        
        avg_price = sum(prices) / len(prices) if prices else 0
        availability_rate = int((available_count / len(products)) * 100) if products else 0
        
        # Determine category from search query or product analysis
        search_term = search_query if search_query else self._extract_search_context(products)
        
        # Data-driven category mapping
        category_map = {
            "bacon": {
                "category": "Breakfast Meat",
                "emoji": "🥓",
                "description": "Premium breakfast selections",
                "primary_color": "#dc2626",
                "secondary_color": "#991b1b",
                "accent_color": "#ef4444"
            },
            "eggs": {
                "category": "Dairy & Eggs",
                "emoji": "🥚",
                "description": "Fresh farm eggs",
                "primary_color": "#f59e0b",
                "secondary_color": "#d97706",
                "accent_color": "#fbbf24"
            },
            "milk": {
                "category": "Dairy Products",
                "emoji": "🥛",
                "description": "Fresh dairy essentials",
                "primary_color": "#3b82f6",
                "secondary_color": "#2563eb",
                "accent_color": "#60a5fa"
            },
            "bread": {
                "category": "Bakery",
                "emoji": "🍞",
                "description": "Fresh baked goods",
                "primary_color": "#d97706",
                "secondary_color": "#b45309",
                "accent_color": "#f59e0b"
            },
            "butter": {
                "category": "Dairy Spreads",
                "emoji": "🧈",
                "description": "Premium butter selections",
                "primary_color": "#fbbf24",
                "secondary_color": "#f59e0b",
                "accent_color": "#fed7aa"
            },
            "tacos": {
                "category": "Mexican Food",
                "emoji": "🌮",
                "description": "Authentic taco essentials",
                "primary_color": "#dc2626",
                "secondary_color": "#991b1b",
                "accent_color": "#f97316"
            },
            "pizza": {
                "category": "Italian Food",
                "emoji": "🍕",
                "description": "Pizza and Italian classics",
                "primary_color": "#dc2626",
                "secondary_color": "#991b1b",
                "accent_color": "#10b981"
            },
            "ice cream": {
                "category": "Frozen Desserts",
                "emoji": "🍨",
                "description": "Premium frozen treats",
                "primary_color": "#ec4899",
                "secondary_color": "#db2777",
                "accent_color": "#f472b6"
            },
            "cheese": {
                "category": "Dairy Products",
                "emoji": "🧀",
                "description": "Artisan cheese selection",
                "primary_color": "#f59e0b",
                "secondary_color": "#d97706",
                "accent_color": "#fbbf24"
            }
        }
        
        category_info = category_map.get(search_term, self._get_default_category_info())
        
        # Add calculated telemetry
        category_info.update({
            "avg_price": avg_price,
            "availability_rate": availability_rate,
            "product_count": len(products)
        })
        
        return category_info
    
    def _get_default_category_info(self) -> Dict[str, Any]:
        """Default category info for unknown products"""
        return {
            "category": "Grocery Products",
            "emoji": "🛒",
            "description": "Quality grocery selections",
            "primary_color": "#6b7280",
            "secondary_color": "#4b5563",
            "accent_color": "#9ca3af",
            "avg_price": 0,
            "availability_rate": 100,
            "product_count": 0
        }
    
    def _generate_product_list_html(self, products: List[Dict], search_query: str = None) -> str:
        """Generate compact product list HTML"""
        # Similar implementation but in list format
        return self._generate_product_grid_html(products, search_query)  # Simplified for now
    
    def create_loading_resource(self, message: str = "Loading...") -> MCPUIResource:
        """
        Create loading UI resource for async operations
        
        Args:
            message: Loading message to display
        
        Returns:
            MCPUIResource: Loading display resource
        """
        loading_html = f"""
        <div style="
            padding: 20px;
            text-align: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #666;
        ">
            <div style="
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 8px;
                vertical-align: middle;
            "></div>
            <span style="vertical-align: middle;">{message}</span>
            
            <style>
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </div>
        """
        
        return self.create_html_resource(
            component_name="loading",
            html_content=loading_html,
            extra_metadata={
                "loading_message": message,
                "is_loading": True
            }
        )


# ============================================================================
# MCP UI Templates (Common Components)
# ============================================================================

class MCPUITemplates:
    """Common UI templates for MCP servers"""
    
    @staticmethod
    def card_grid_template(items: List[Dict[str, Any]], title: str = "Items") -> str:
        """Generate responsive card grid HTML"""
        cards_html = ""
        
        for item in items:
            name = item.get('name', 'Unknown')
            price = item.get('price', 0)
            description = item.get('description', '')
            
            cards_html += f"""
            <div class="card">
                <h3>{name}</h3>
                <p class="price">${price:.2f}</p>
                <p class="description">{description}</p>
                <button onclick="selectItem('{item.get('id', '')}')">Select</button>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 16px; background: #f5f7fa; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }}
                .card {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
                .price {{ font-size: 20px; font-weight: bold; color: #059669; }}
                .description {{ color: #666; font-size: 14px; }}
                button {{ background: #059669; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="grid">
                {cards_html}
            </div>
            <script>
                function selectItem(id) {{
                    window.dispatchEvent(new CustomEvent('mcp:itemSelected', {{
                        detail: {{ itemId: id }}
                    }}));
                }}
            </script>
        </body>
        </html>
        """


# ============================================================================
# Export main components
# ============================================================================

__all__ = [
    'MCPUIResource',
    'MCPUIResponse', 
    'MCPUIService',
    'MCPUITemplates'
]