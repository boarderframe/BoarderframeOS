"""
Kroger Product Search Tool for Open WebUI
Connects to the Kroger MCP Enhanced server to provide product search functionality
"""

import requests
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Tools:
    def __init__(self):
        self.name = "Kroger Product Search"
        self.description = "Search for Kroger grocery products with interactive UI"
        
        # MCP server configuration
        self.mcp_server_url = "http://localhost:9006"
        
    class Valves(BaseModel):
        """Configuration options for the Kroger Product Search tool"""
        mcp_server_url: str = Field(
            default="http://localhost:9006",
            description="URL of the Kroger MCP Enhanced server"
        )
        timeout_seconds: int = Field(
            default=10,
            description="Request timeout in seconds"
        )
        max_results: int = Field(
            default=10,
            description="Maximum number of search results to return"
        )

    def __init__(self):
        self.valves = self.Valves()

    async def search_kroger_products(
        self,
        query: str,
        theme: str = "light",
        __user__: Optional[Dict] = None,
        __event_emitter__: Optional[Any] = None
    ) -> str:
        """
        Search for Kroger products and return interactive UI results
        
        Args:
            query: Product search query (e.g., 'bread', 'milk', 'eggs')
            theme: UI theme preference ('light', 'dark', or 'default')
            __user__: User context (provided by Open WebUI)
            __event_emitter__: Event emitter for streaming updates
        
        Returns:
            Formatted search results with interactive UI
        """
        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Searching Kroger products for '{query}'...",
                            "done": False
                        }
                    }
                )
            
            # Call Kroger MCP Enhanced server
            response = requests.get(
                f"{self.valves.mcp_server_url}/mcp/tools/search_products_ui",
                params={"query": query, "theme": theme},
                timeout=self.valves.timeout_seconds
            )
            
            if response.status_code == 200:
                data = response.json()
                result = self._format_search_results(data, query)
                
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "Search completed successfully!",
                                "done": True
                            }
                        }
                    )
                
                return result
            else:
                error_msg = f"❌ Error: Server returned status {response.status_code}"
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": error_msg,
                                "done": True
                            }
                        }
                    )
                return error_msg
                
        except requests.RequestException as e:
            error_msg = f"❌ Network error: Unable to connect to Kroger search service. {str(e)}"
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": error_msg,
                            "done": True
                        }
                    }
                )
            return error_msg
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": error_msg,
                            "done": True
                        }
                    }
                )
            return error_msg

    def _format_search_results(self, data: Dict, query: str) -> str:
        """Format the search results for display in Open WebUI"""
        try:
            # Extract basic info
            text_response = data.get("text", f"Found products for '{query}'")
            ui_resources = data.get("ui_resources", {})
            
            if not ui_resources:
                # Fallback to products list
                products = data.get("products", [])
                return self._format_products_list(products, query)
            
            # Get the UI resource
            resource_id = list(ui_resources.keys())[0]
            resource = ui_resources[resource_id]
            ui_content = resource.get("content", "")
            metadata = resource.get("metadata", {})
            
            # If content is a URL, fetch the actual UI
            if ui_content.startswith("http"):
                try:
                    ui_response = requests.get(ui_content, timeout=5)
                    if ui_response.status_code == 200:
                        ui_html = ui_response.text
                        
                        # Create a properly formatted response with embedded UI
                        formatted_response = f"""
## 🛒 Kroger Product Search Results

{text_response}

<div style="border: 2px solid #e2e8f0; border-radius: 16px; padding: 0; margin: 20px 0; background: white; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden;">
    <div style="background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: white; padding: 16px; text-align: center;">
        <h3 style="margin: 0; font-size: 18px;">🛒 Interactive Product Catalog</h3>
        <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Search: "{query}" • Results: {metadata.get('product_count', 'N/A')} • Theme: {metadata.get('theme', 'default')}</p>
    </div>
    <div style="max-height: 600px; overflow-y: auto;">
        {ui_html}
    </div>
    <div style="background: #f8fafc; padding: 12px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
        ✨ Powered by Kroger MCP Enhanced Server • MCP-UI Protocol v{metadata.get('protocol_version', '1.0.0')}
    </div>
</div>

**Search Summary:**
- **Query:** "{query}"
- **Results:** {metadata.get('product_count', 'Unknown')} products found
- **Generated:** {metadata.get('created_at', 'Just now')}
- **Server:** Kroger MCP Enhanced v2.0.0

💡 *Tip: You can search for items like 'bread', 'milk', 'eggs', 'chicken', 'vegetables', etc.*
"""
                        return formatted_response
                    else:
                        return f"❌ Unable to load interactive UI (status: {ui_response.status_code})"
                except Exception as e:
                    return f"❌ Error loading interactive UI: {str(e)}"
            else:
                # Content is inline HTML
                formatted_response = f"""
## 🛒 Kroger Product Search Results

{text_response}

<div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin: 16px 0; background: #f8fafc;">
    <div style="background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        {ui_content}
    </div>
    <p style="margin: 16px 0 0 0; font-size: 14px; color: #64748b; text-align: center;">
        ✨ Interactive results powered by Kroger MCP Enhanced Server
    </p>
</div>
"""
                return formatted_response
                
        except Exception as e:
            return f"❌ Error formatting search results: {str(e)}"

    def _format_products_list(self, products: List[Dict], query: str) -> str:
        """Format products as a simple list when UI resources aren't available"""
        if not products:
            return f"❌ No products found for '{query}'. Please try a different search term."
        
        response = f"## 🛒 Kroger Products for '{query}'\n\n"
        response += f"Found {len(products)} product(s):\n\n"
        
        for i, product in enumerate(products[:self.valves.max_results], 1):
            name = product.get("name", "Unknown Product")
            price = product.get("price", 0)
            brand = product.get("brand", "Unknown Brand")
            description = product.get("description", "No description available")
            available = product.get("available", True)
            
            status_emoji = "✅" if available else "❌"
            
            response += f"**{i}. {name}**\n"
            response += f"   • Brand: {brand}\n"
            response += f"   • Price: ${price:.2f}\n"
            response += f"   • Status: {status_emoji} {'Available' if available else 'Out of Stock'}\n"
            response += f"   • Description: {description}\n\n"
        
        if len(products) > self.valves.max_results:
            response += f"... and {len(products) - self.valves.max_results} more products.\n\n"
        
        response += "💡 *Try asking: 'Search for bread' or 'Find some organic milk'*"
        return response


# Create the tool instance
tools = Tools()