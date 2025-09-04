"""
Kroger MCP Server Phase 2 - Fixed Version
Simplified dependencies for easier testing
"""

import asyncio
import os
import json
import secrets
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Float, Integer, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Import MCP-UI framework
from src.mcp_ui_core.base_mcp_server import BaseMCPServer, MCPServerConfig

# Load environment variables
load_dotenv()

# Database models
Base = declarative_base()

class UserSession(Base):
    """User session management"""
    __tablename__ = "user_sessions"
    
    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CartItem(Base):
    """Shopping cart items"""
    __tablename__ = "cart_items"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    product_id = Column(String, nullable=False)
    product_data = Column(JSON, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)


# Simplified cache service
class SimpleCacheService:
    """In-memory cache service"""
    
    def __init__(self):
        self.cache = {}
        
    async def connect(self):
        """Initialize cache"""
        print("📝 Using in-memory cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self.cache:
            value, expire_time = self.cache[key]
            if expire_time > datetime.utcnow():
                return value
            else:
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, expire: int = 300):
        """Set cached value with expiration"""
        expire_time = datetime.utcnow() + timedelta(seconds=expire)
        self.cache[key] = (value, expire_time)
    
    async def delete(self, key: str):
        """Delete cached value"""
        if key in self.cache:
            del self.cache[key]
    
    async def close(self):
        """Cleanup"""
        self.cache.clear()


class KrogerMCPServerPhase2(BaseMCPServer):
    """
    Kroger MCP Server Phase 2 - Simplified
    
    Core features:
    - OAuth 2.0 authentication flow
    - Shopping cart management
    - Product search with filters
    - Digital coupons
    - Store locator
    """
    
    def __init__(self):
        config = MCPServerConfig(
            name="Kroger Shopping Pro",
            description="Enhanced Kroger shopping with authentication",
            version="2.0.0",
            port=9011,
            enable_ui=True,
            ui_template_dir="ui_templates",
            debug=True
        )
        super().__init__(config)
        
        # Kroger API settings
        self.client_id = os.getenv("KROGER_CLIENT_ID", "")
        self.client_secret = os.getenv("KROGER_CLIENT_SECRET", "")
        self.api_base = "https://api.kroger.com/v1"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Cache
        self.cache = SimpleCacheService()
        
        # Database
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///kroger_phase2.db")
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # OAuth settings
        self.redirect_uri = os.getenv("KROGER_REDIRECT_URI", "http://localhost:9011/auth/callback")
        self.oauth_states = {}
        
        print("🛒 Kroger MCP Server Phase 2 - Simplified")
        print("🔐 OAuth 2.0 Authentication Ready")
        print(f"📍 Redirect URI: {self.redirect_uri}")
    
    async def initialize(self) -> None:
        """Initialize server components"""
        
        # Connect cache
        await self.cache.connect()
        
        # Setup OAuth routes
        self._setup_oauth_routes()
        
        # Register tools
        self._register_tools()
        
        self.logger.info("✅ Server initialized")
    
    def _setup_oauth_routes(self):
        """Setup OAuth authentication routes"""
        
        @self.app.get("/auth/login")
        async def login():
            """Initiate OAuth login"""
            state = secrets.token_urlsafe(32)
            self.oauth_states[state] = datetime.utcnow()
            
            # Build auth URL
            params = {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": "product.compact cart.basic:write",
                "state": state
            }
            auth_url = f"https://api.kroger.com/v1/connect/oauth2/authorize?{urlencode(params)}"
            
            # Return login page
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Kroger Login</title>
                <style>
                    body {{ font-family: system-ui; padding: 40px; text-align: center; }}
                    .container {{ max-width: 500px; margin: 0 auto; }}
                    .btn {{ 
                        display: inline-block; 
                        padding: 15px 30px; 
                        background: #007bff; 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 8px;
                        font-size: 18px;
                        margin-top: 20px;
                    }}
                    .btn:hover {{ background: #0056b3; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🛒 Kroger Shopping Assistant</h1>
                    <p>Login with your Kroger account to access personalized features:</p>
                    <ul style="text-align: left; display: inline-block;">
                        <li>Manage shopping cart</li>
                        <li>Browse digital coupons</li>
                        <li>Find nearby stores</li>
                        <li>View order history</li>
                    </ul>
                    <a href="{auth_url}" class="btn">Login with Kroger</a>
                    <p style="margin-top: 30px; color: #666;">
                        Don't have an account? 
                        <a href="https://www.kroger.com/register">Sign up at Kroger.com</a>
                    </p>
                </div>
            </body>
            </html>
            """
            
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html)
        
        @self.app.get("/auth/callback")
        async def auth_callback(code: str, state: str):
            """Handle OAuth callback"""
            
            # Verify state
            if state not in self.oauth_states:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Invalid state")
            
            del self.oauth_states[state]
            
            # Exchange code for token
            try:
                data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
                
                response = await self.http_client.post(
                    f"{self.api_base}/connect/oauth2/token",
                    data=data,
                    auth=(self.client_id, self.client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Create session
                    session_id = secrets.token_urlsafe(32)
                    expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
                    
                    with self.SessionLocal() as db:
                        session = UserSession(
                            session_id=session_id,
                            user_id=f"user_{secrets.token_hex(4)}",
                            access_token=token_data["access_token"],
                            refresh_token=token_data.get("refresh_token", ""),
                            expires_at=expires_at,
                            user_data={}
                        )
                        db.add(session)
                        db.commit()
                    
                    # Success page
                    html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Login Successful</title>
                        <style>
                            body {{ font-family: system-ui; padding: 40px; text-align: center; }}
                            .success {{ color: #28a745; }}
                            code {{ background: #f4f4f4; padding: 4px 8px; border-radius: 4px; }}
                        </style>
                    </head>
                    <body>
                        <h1 class="success">✅ Login Successful!</h1>
                        <p>Your session has been created.</p>
                        <p>Session ID: <code>{session_id}</code></p>
                        <p>You can now use the Kroger Shopping Assistant tools.</p>
                    </body>
                    </html>
                    """
                    
                    from fastapi.responses import HTMLResponse
                    return HTMLResponse(content=html)
                else:
                    raise Exception(f"Token exchange failed: {response.status_code}")
                    
            except Exception as e:
                from fastapi import HTTPException
                raise HTTPException(status_code=500, detail=str(e))
    
    def _register_tools(self):
        """Register MCP tools"""
        
        # Authentication
        self.register_ui_tool(
            name="login",
            description="Login to Kroger account",
            parameters={},
            handler=self._login_handler,
            component_type="auth-login"
        )
        
        # Shopping
        self.register_ui_tool(
            name="search_products",
            description="Search for products",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "session_id": {"type": "string", "description": "Session ID (optional)"},
                "limit": {"type": "integer", "description": "Number of results", "default": 20}
            },
            handler=self._search_products_handler,
            component_type="product-grid"
        )
        
        self.register_ui_tool(
            name="manage_cart",
            description="Manage shopping cart",
            parameters={
                "session_id": {"type": "string", "description": "Session ID"},
                "action": {"type": "string", "description": "Action: view, add, remove", "default": "view"},
                "product_id": {"type": "string", "description": "Product ID for actions"},
                "quantity": {"type": "integer", "description": "Quantity", "default": 1}
            },
            handler=self._manage_cart_handler,
            component_type="shopping-cart"
        )
        
        self.register_ui_tool(
            name="digital_coupons",
            description="Browse digital coupons",
            parameters={
                "session_id": {"type": "string", "description": "Session ID (optional)"}
            },
            handler=self._digital_coupons_handler,
            component_type="coupon-browser"
        )
        
        self.register_ui_tool(
            name="find_stores",
            description="Find nearby stores",
            parameters={
                "zipcode": {"type": "string", "description": "ZIP code"},
                "radius": {"type": "integer", "description": "Search radius", "default": 10}
            },
            handler=self._find_stores_handler,
            component_type="store-map"
        )
    
    # Tool handlers
    
    async def _login_handler(self) -> Dict[str, Any]:
        """Handle login UI"""
        
        # Create login UI
        ui_resource = await self.create_ui_component(
            component_type="auth-login",
            data={
                "title": "Login to Kroger",
                "auth_url": "/auth/login",
                "features": [
                    "Access your Kroger account",
                    "Manage shopping cart",
                    "Browse digital coupons",
                    "Find nearby stores"
                ]
            }
        )
        
        return await self.build_ui_response(
            ui_resources=[ui_resource],
            message="Click to login to your Kroger account."
        )
    
    async def _search_products_handler(self, query: str, session_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Search for products"""
        
        # Check cache
        cache_key = f"search:{query}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            products = cached
        else:
            # Use mock data for demo
            products = [
                {
                    "id": f"prod_{i}",
                    "name": f"{query} Product {i}",
                    "brand": "Kroger",
                    "price": 2.99 + i * 0.5,
                    "size": "1 unit",
                    "available": True
                }
                for i in range(1, min(limit + 1, 11))
            ]
            
            await self.cache.set(cache_key, products)
        
        # Create UI
        ui_resource = await self.create_ui_component(
            component_type="product-grid",
            data={
                "title": f"Search: {query}",
                "products": products,
                "total": len(products)
            }
        )
        
        return await self.build_ui_response(
            ui_resources=[ui_resource],
            data={"count": len(products)},
            message=f"Found {len(products)} products."
        )
    
    async def _manage_cart_handler(self, session_id: str, action: str = "view", 
                                  product_id: Optional[str] = None, quantity: int = 1) -> Dict[str, Any]:
        """Manage shopping cart"""
        
        with self.SessionLocal() as db:
            # Verify session
            session = db.query(UserSession).filter_by(session_id=session_id).first()
            if not session:
                return {"error": "Invalid session. Please login first."}
            
            # Handle actions
            if action == "add" and product_id:
                cart_item = CartItem(
                    id=f"{session_id}_{product_id}_{datetime.utcnow().timestamp()}",
                    session_id=session_id,
                    product_id=product_id,
                    product_data={"name": f"Product {product_id}"},
                    quantity=quantity,
                    price=9.99
                )
                db.add(cart_item)
                db.commit()
            
            elif action == "remove" and product_id:
                cart_item = db.query(CartItem).filter_by(
                    session_id=session_id,
                    product_id=product_id
                ).first()
                if cart_item:
                    db.delete(cart_item)
                    db.commit()
            
            # Get cart items
            cart_items = db.query(CartItem).filter_by(session_id=session_id).all()
            
            # Build cart data
            items = []
            subtotal = 0
            for item in cart_items:
                items.append({
                    "product_id": item.product_id,
                    "name": item.product_data.get("name", "Unknown"),
                    "quantity": item.quantity,
                    "price": item.price
                })
                subtotal += item.price * item.quantity
        
        # Create cart UI
        ui_resource = await self.create_ui_component(
            component_type="shopping-cart",
            data={
                "items": items,
                "subtotal": subtotal,
                "tax": subtotal * 0.08,
                "total": subtotal * 1.08,
                "item_count": len(items)
            }
        )
        
        return await self.build_ui_response(
            ui_resources=[ui_resource],
            data={"item_count": len(items), "total": subtotal * 1.08},
            message=f"Cart has {len(items)} items (${subtotal * 1.08:.2f} total)."
        )
    
    async def _digital_coupons_handler(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Browse digital coupons"""
        
        # Mock coupons
        coupons = [
            {
                "id": "coup1",
                "title": "$2 off Dairy Products",
                "description": "Save on milk, cheese, and yogurt",
                "value": 2.00,
                "expires": "2024-02-01"
            },
            {
                "id": "coup2",
                "title": "20% off Produce",
                "description": "Fresh fruits and vegetables",
                "value": 0.20,
                "expires": "2024-02-01"
            },
            {
                "id": "coup3",
                "title": "$5 off $25 Purchase",
                "description": "Minimum purchase required",
                "value": 5.00,
                "expires": "2024-02-01"
            }
        ]
        
        # Create coupon UI
        ui_resource = await self.create_ui_component(
            component_type="coupon-browser",
            data={
                "title": "Digital Coupons",
                "coupons": coupons,
                "total_savings": sum(c["value"] for c in coupons)
            }
        )
        
        return await self.build_ui_response(
            ui_resources=[ui_resource],
            data={"count": len(coupons)},
            message=f"Found {len(coupons)} digital coupons."
        )
    
    async def _find_stores_handler(self, zipcode: str, radius: int = 10) -> Dict[str, Any]:
        """Find nearby stores"""
        
        # Mock stores
        stores = [
            {
                "id": "store1",
                "name": "Kroger Marketplace",
                "address": f"123 Main St, {zipcode}",
                "distance": 2.3,
                "services": ["Pharmacy", "Fuel", "Pickup"]
            },
            {
                "id": "store2",
                "name": "Kroger Fresh",
                "address": f"456 Oak Ave, {zipcode}",
                "distance": 4.1,
                "services": ["Pharmacy", "Deli"]
            }
        ]
        
        # Create store map UI
        ui_resource = await self.create_ui_component(
            component_type="store-map",
            data={
                "title": f"Stores near {zipcode}",
                "stores": stores,
                "center_zip": zipcode,
                "radius": radius
            }
        )
        
        return await self.build_ui_response(
            ui_resources=[ui_resource],
            data={"count": len(stores)},
            message=f"Found {len(stores)} stores near {zipcode}."
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        
        # Check database
        try:
            with self.SessionLocal() as db:
                session_count = db.query(UserSession).count()
            db_status = "healthy"
        except:
            db_status = "error"
            session_count = 0
        
        return {
            "kroger_api": "configured" if self.client_id else "not_configured",
            "database": db_status,
            "sessions": session_count,
            "features": ["oauth", "cart", "coupons", "stores"]
        }
    
    async def shutdown(self) -> None:
        """Cleanup on shutdown"""
        await self.cache.close()
        await self.http_client.aclose()
        await super().shutdown()


# Run the server
if __name__ == "__main__":
    server = KrogerMCPServerPhase2()
    server.run()