"""
MCP Artifact Response Optimizer for Open WebUI
==============================================

This module provides an optimized response format and rendering mechanism 
to ensure reliable artifact rendering in Open WebUI.

Key Features:
- Guaranteed HTML artifact rendering with multiple fallback mechanisms
- Token-efficient response formats with progressive enhancement
- Clear LLM instructions for proper artifact inclusion
- Debug mode for troubleshooting rendering issues
- Automatic content size optimization
"""

import json
import gzip
import base64
import hashlib
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Response Format Types - Different strategies for artifact rendering
# ============================================================================

class ArtifactRenderStrategy(Enum):
    """Different strategies for ensuring artifact rendering"""
    INLINE_HTML = "inline_html"  # Direct HTML in response
    CODE_BLOCK = "code_block"    # HTML wrapped in ```html blocks
    IFRAME_URI = "iframe_uri"    # URI for iframe embedding
    BASE64_DATA = "base64_data"  # Base64 encoded data URI
    HYBRID = "hybrid"             # Multiple strategies in single response


class ArtifactPriority(Enum):
    """Priority levels for artifact rendering"""
    CRITICAL = "critical"  # Must render or fail
    HIGH = "high"         # Important to render
    MEDIUM = "medium"     # Should render if possible
    LOW = "low"          # Optional rendering


# ============================================================================
# Optimized Response Models
# ============================================================================

class OptimizedArtifactMetadata(BaseModel):
    """Minimal metadata for artifacts"""
    id: str = Field(..., description="Unique artifact ID")
    type: str = Field(..., description="Artifact type for rendering")
    size: int = Field(..., description="Content size in bytes")
    strategy: ArtifactRenderStrategy = Field(..., description="Rendering strategy")
    priority: ArtifactPriority = Field(default=ArtifactPriority.HIGH)
    checksum: str = Field(..., description="Content checksum for validation")


class RenderingInstructions(BaseModel):
    """Instructions for LLMs on how to render artifacts"""
    primary_method: str = Field(..., description="Primary rendering method")
    fallback_methods: List[str] = Field(..., description="Fallback rendering methods")
    example_usage: str = Field(..., description="Example of how to include artifact")
    troubleshooting: Dict[str, str] = Field(default_factory=dict)


class OptimizedMCPResponse(BaseModel):
    """Optimized response format for Open WebUI compatibility"""
    # Essential data (minimal tokens)
    summary: str = Field(..., max_length=200, description="Brief summary")
    data_count: int = Field(..., description="Number of items")
    
    # Artifact information
    artifact: OptimizedArtifactMetadata = Field(..., description="Artifact metadata")
    
    # Rendering instructions for LLM
    rendering: RenderingInstructions = Field(..., description="How to render artifact")
    
    # Multiple format options for maximum compatibility
    formats: Dict[str, str] = Field(..., description="Different format options")
    
    # Debug information (optional)
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug information")


# ============================================================================
# Artifact Response Optimizer
# ============================================================================

class ArtifactResponseOptimizer:
    """
    Optimizes MCP server responses for reliable Open WebUI artifact rendering
    """
    
    def __init__(self, 
                 service_name: str = "mcp-server",
                 debug_mode: bool = False,
                 max_inline_size: int = 50000):  # 50KB max for inline HTML
        self.service_name = service_name
        self.debug_mode = debug_mode
        self.max_inline_size = max_inline_size
        self.render_success_rate = {}  # Track success rates per strategy
        
    def create_optimized_response(self,
                                 data: List[Any],
                                 html_content: str,
                                 content_type: str = "product_cards",
                                 search_query: str = None) -> OptimizedMCPResponse:
        """
        Create an optimized response with multiple rendering strategies
        """
        # Generate artifact ID based on content
        artifact_id = self._generate_artifact_id(html_content, search_query)
        
        # Determine best strategy based on content size and type
        strategy = self._determine_strategy(html_content, content_type)
        
        # Create multiple format options for compatibility
        formats = self._create_format_options(html_content, artifact_id, strategy)
        
        # Generate rendering instructions for LLM
        rendering_instructions = self._create_rendering_instructions(
            strategy, artifact_id, content_type
        )
        
        # Create minimal metadata
        metadata = OptimizedArtifactMetadata(
            id=artifact_id,
            type=content_type,
            size=len(html_content),
            strategy=strategy,
            priority=ArtifactPriority.HIGH if len(data) > 0 else ArtifactPriority.LOW,
            checksum=hashlib.md5(html_content.encode()).hexdigest()[:8]
        )
        
        # Build response
        response = OptimizedMCPResponse(
            summary=self._create_summary(data, search_query),
            data_count=len(data),
            artifact=metadata,
            rendering=rendering_instructions,
            formats=formats
        )
        
        # Add debug info if enabled
        if self.debug_mode:
            response.debug = self._create_debug_info(html_content, strategy)
        
        return response
    
    def _generate_artifact_id(self, content: str, context: str = None) -> str:
        """Generate stable artifact ID"""
        hash_input = f"{context or 'artifact'}-{len(content)}-{hash(content)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _determine_strategy(self, content: str, content_type: str) -> ArtifactRenderStrategy:
        """Determine best rendering strategy based on content"""
        content_size = len(content)
        
        # Small content: use inline HTML
        if content_size < self.max_inline_size:
            return ArtifactRenderStrategy.CODE_BLOCK
        
        # Large content: use hybrid approach
        elif content_size < 200000:  # 200KB
            return ArtifactRenderStrategy.HYBRID
        
        # Very large: use URI reference
        else:
            return ArtifactRenderStrategy.IFRAME_URI
    
    def _create_format_options(self, 
                              html_content: str, 
                              artifact_id: str,
                              strategy: ArtifactRenderStrategy) -> Dict[str, str]:
        """Create multiple format options for maximum compatibility"""
        formats = {}
        
        # Always include code block format (most reliable)
        formats["code_block"] = self._format_as_code_block(html_content)
        
        # Include inline HTML if small enough
        if len(html_content) < self.max_inline_size:
            formats["inline_html"] = html_content
        
        # Include base64 data URI for iframe embedding
        formats["data_uri"] = self._create_data_uri(html_content)
        
        # Include artifact URI reference
        formats["artifact_uri"] = f"/artifacts/{artifact_id}"
        
        # Include rendering endpoint
        formats["render_url"] = f"/artifacts/{artifact_id}/render"
        
        # Compressed format for efficiency
        formats["compressed"] = self._compress_content(html_content)
        
        return formats
    
    def _format_as_code_block(self, html_content: str) -> str:
        """Format HTML as code block for LLM response"""
        # Ensure proper escaping and formatting
        return f"```html\n{html_content}\n```"
    
    def _create_data_uri(self, html_content: str) -> str:
        """Create base64 data URI for iframe src"""
        encoded = base64.b64encode(html_content.encode()).decode()
        return f"data:text/html;base64,{encoded}"
    
    def _compress_content(self, content: str) -> str:
        """Compress and encode content for efficiency"""
        compressed = gzip.compress(content.encode())
        encoded = base64.b64encode(compressed).decode()
        return encoded
    
    def _create_rendering_instructions(self,
                                      strategy: ArtifactRenderStrategy,
                                      artifact_id: str,
                                      content_type: str) -> RenderingInstructions:
        """Create clear instructions for LLM on how to render artifact"""
        
        # Primary method based on strategy
        if strategy == ArtifactRenderStrategy.CODE_BLOCK:
            primary = "Include the HTML from formats.code_block directly in your response"
            example = "Simply include the HTML code block in your response:\n\n{formats.code_block}"
        elif strategy == ArtifactRenderStrategy.INLINE_HTML:
            primary = "Include formats.inline_html as an HTML artifact"
            example = "Include this in your response:\n\n<artifact>\n{formats.inline_html}\n</artifact>"
        else:
            primary = "Reference the artifact URI for rendering"
            example = f"Display artifact at: {formats.artifact_uri}"
        
        # Fallback methods
        fallbacks = [
            "If primary method fails, use formats.code_block",
            "Alternative: Create iframe with formats.data_uri as src",
            f"Last resort: Direct user to {formats.render_url}"
        ]
        
        # Troubleshooting guide
        troubleshooting = {
            "not_rendering": "Ensure HTML code block is properly formatted with ```html tags",
            "partial_render": "Check if content size exceeds limits, use compressed format",
            "no_styles": "Verify inline styles are included in HTML content",
            "iframe_blocked": "Use data URI instead of external URL for iframe src"
        }
        
        return RenderingInstructions(
            primary_method=primary,
            fallback_methods=fallbacks,
            example_usage=example,
            troubleshooting=troubleshooting
        )
    
    def _create_summary(self, data: List[Any], query: str = None) -> str:
        """Create brief summary for response"""
        if not data:
            return f"No results found{f' for {query}' if query else ''}"
        
        summary = f"Found {len(data)} items"
        if query:
            summary += f" for '{query}'"
        
        # Add price range if applicable
        if data and hasattr(data[0], 'price'):
            prices = [getattr(item, 'price', 0) for item in data]
            min_price = min(prices)
            max_price = max(prices)
            summary += f" (${min_price:.2f}-${max_price:.2f})"
        
        return summary[:200]  # Enforce max length
    
    def _create_debug_info(self, content: str, strategy: ArtifactRenderStrategy) -> Dict:
        """Create debug information for troubleshooting"""
        return {
            "content_size": len(content),
            "strategy_used": strategy.value,
            "compression_ratio": len(self._compress_content(content)) / len(content),
            "render_success_rate": self.render_success_rate.get(strategy.value, "unknown"),
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name
        }


# ============================================================================
# Enhanced HTML Generator with Guaranteed Rendering
# ============================================================================

class GuaranteedRenderHTMLGenerator:
    """
    Generates HTML that is guaranteed to render in Open WebUI artifacts
    """
    
    @staticmethod
    def create_product_grid(products: List[Dict], 
                           title: str = "Products",
                           max_items: int = 20) -> str:
        """
        Create a product grid with guaranteed rendering
        
        Uses:
        - Inline styles (no external CSS)
        - Self-contained HTML (no external resources)
        - Responsive design with CSS Grid
        - Fallback text for accessibility
        """
        # Limit items for performance
        display_products = products[:max_items]
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .header h1 {{
            color: #2d3748;
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 15px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
        }}
        .card-image {{
            height: 200px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        .card-badge {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #48bb78;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        .card-badge.out-of-stock {{
            background: #f56565;
        }}
        .card-content {{
            padding: 15px;
        }}
        .card-brand {{
            font-size: 11px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .card-title {{
            font-size: 14px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 8px;
            line-height: 1.4;
            height: 40px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}
        .card-size {{
            font-size: 12px;
            color: #a0aec0;
            margin-bottom: 12px;
        }}
        .card-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .card-price {{
            font-size: 20px;
            font-weight: bold;
            color: #2d3748;
        }}
        .card-button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .card-button:hover {{
            background: #5a67d8;
        }}
        .card-button:disabled {{
            background: #cbd5e0;
            cursor: not-allowed;
        }}
        .placeholder-icon {{
            width: 60px;
            height: 60px;
            fill: white;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 {title}</h1>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(display_products)}</div>
                    <div class="stat-label">Products</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{sum(1 for p in display_products if p.get('available', True))}</div>
                    <div class="stat-label">Available</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${min(p.get('price', 0) for p in display_products):.2f}</div>
                    <div class="stat-label">Min Price</div>
                </div>
            </div>
        </div>
        
        <div class="grid">"""
        
        for product in display_products:
            name = product.get('name', 'Unknown Product')[:60]
            brand = product.get('brand', '')
            size = product.get('size', '')
            price = product.get('price', 0)
            available = product.get('available', True)
            
            html += f"""
            <div class="card">
                <div class="card-image">
                    <div class="card-badge {'out-of-stock' if not available else ''}">
                        {'In Stock' if available else 'Out of Stock'}
                    </div>
                    <svg class="placeholder-icon" viewBox="0 0 24 24">
                        <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
                    </svg>
                </div>
                <div class="card-content">
                    <div class="card-brand">{brand}</div>
                    <div class="card-title">{name}</div>
                    <div class="card-size">{size}</div>
                    <div class="card-footer">
                        <div class="card-price">${price:.2f}</div>
                        <button class="card-button" {'disabled' if not available else ''}>
                            {'Add to Cart' if available else 'Unavailable'}
                        </button>
                    </div>
                </div>
            </div>"""
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def create_error_display(message: str, details: str = None) -> str:
        """Create an error display with helpful information"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }}
        .error-container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            max-width: 500px;
            text-align: center;
        }}
        .error-icon {{
            width: 60px;
            height: 60px;
            margin: 0 auto 20px;
            fill: #f56565;
        }}
        .error-title {{
            color: #2d3748;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .error-message {{
            color: #718096;
            font-size: 16px;
            line-height: 1.5;
            margin-bottom: 20px;
        }}
        .error-details {{
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 12px;
            color: #4a5568;
            text-align: left;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <svg class="error-icon" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        <div class="error-title">Rendering Error</div>
        <div class="error-message">{message}</div>
        {f'<div class="error-details">{details}</div>' if details else ''}
    </div>
</body>
</html>"""


# ============================================================================
# Integration Helper for MCP Servers
# ============================================================================

class MCPServerIntegration:
    """
    Helper class for integrating optimized responses into existing MCP servers
    """
    
    def __init__(self, server_name: str = "mcp-server"):
        self.optimizer = ArtifactResponseOptimizer(server_name, debug_mode=True)
        self.html_generator = GuaranteedRenderHTMLGenerator()
        
    def create_product_response(self, 
                               products: List[Dict],
                               search_query: str = None) -> Dict:
        """
        Create optimized product search response
        """
        # Generate HTML content
        html_content = self.html_generator.create_product_grid(
            products, 
            title=f"Search Results: {search_query}" if search_query else "Products"
        )
        
        # Create optimized response
        response = self.optimizer.create_optimized_response(
            data=products,
            html_content=html_content,
            content_type="product_cards",
            search_query=search_query
        )
        
        # Convert to dict for JSON response
        return response.dict()
    
    def create_error_response(self, error_message: str, error_details: str = None) -> Dict:
        """
        Create error response with visual display
        """
        # Generate error HTML
        html_content = self.html_generator.create_error_display(
            error_message, error_details
        )
        
        # Create optimized response
        response = self.optimizer.create_optimized_response(
            data=[],
            html_content=html_content,
            content_type="error_display",
            search_query=None
        )
        
        return response.dict()


# ============================================================================
# Example Usage and Testing
# ============================================================================

if __name__ == "__main__":
    # Example: Create optimized response for Kroger MCP server
    
    # Sample product data
    sample_products = [
        {
            "name": "Organic Bananas",
            "brand": "Kroger",
            "price": 0.69,
            "size": "per lb",
            "available": True,
            "upc": "0000000004011"
        },
        {
            "name": "Whole Milk",
            "brand": "Simple Truth",
            "price": 3.99,
            "size": "1 gallon",
            "available": True,
            "upc": "0001111041660"
        },
        {
            "name": "Sourdough Bread",
            "brand": "Private Selection",
            "price": 4.49,
            "size": "24 oz",
            "available": False,
            "upc": "0001111088856"
        }
    ]
    
    # Create integration helper
    integration = MCPServerIntegration("kroger-mcp-server")
    
    # Generate optimized response
    response = integration.create_product_response(
        products=sample_products,
        search_query="groceries"
    )
    
    # Print response structure
    print("Optimized Response Structure:")
    print("=" * 50)
    print(json.dumps(response, indent=2, default=str))
    
    # Show rendering instructions
    print("\n" + "=" * 50)
    print("Rendering Instructions for LLM:")
    print("=" * 50)
    print(response['rendering']['primary_method'])
    print("\nExample Usage:")
    print(response['rendering']['example_usage'])
    
    # Show HTML artifact (truncated for display)
    print("\n" + "=" * 50)
    print("HTML Artifact (First 500 chars):")
    print("=" * 50)
    if 'code_block' in response['formats']:
        print(response['formats']['code_block'][:500] + "...")