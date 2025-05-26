"""
Browser MCP Server for BoarderframeOS
Provides web automation and scraping capabilities for agents
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import logging
import uvicorn
from pathlib import Path
from datetime import datetime
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("browser_server")

app = FastAPI(title="Browser MCP Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class NavigateRequest(BaseModel):
    url: str = Field(..., description="URL to navigate to")
    wait_for_selector: Optional[str] = Field(None, description="CSS selector to wait for")
    timeout: int = Field(30000, description="Timeout in milliseconds")
    user_agent: Optional[str] = Field(None, description="Custom user agent")

class ClickRequest(BaseModel):
    selector: str = Field(..., description="CSS selector to click")
    wait_after: int = Field(1000, description="Wait time after click in ms")

class TypeRequest(BaseModel):
    selector: str = Field(..., description="CSS selector of input element")
    text: str = Field(..., description="Text to type")
    clear_first: bool = Field(True, description="Clear field before typing")

class ExtractRequest(BaseModel):
    selector: str = Field(..., description="CSS selector to extract from")
    attribute: Optional[str] = Field(None, description="Attribute to extract (default: text)")
    multiple: bool = Field(False, description="Extract from multiple elements")

class ScreenshotRequest(BaseModel):
    full_page: bool = Field(False, description="Take full page screenshot")
    selector: Optional[str] = Field(None, description="Screenshot specific element")

class BrowserResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: str

class PageInfo(BaseModel):
    url: str
    title: str
    status_code: int
    content_type: str

# Browser Session Manager
class BrowserSession:
    """Manages a browser session with Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize Playwright browser"""
        if self.is_initialized:
            return
        
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.page = await self.browser.new_page()
            
            # Set reasonable defaults
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            await self.page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9"
            })
            
            self.is_initialized = True
            logger.info("Browser session initialized")
            
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install")
            raise HTTPException(status_code=500, detail="Playwright not available")
        except Exception as e:
            logger.error(f"Browser initialization failed: {e}")
            raise HTTPException(status_code=500, detail=f"Browser init failed: {e}")
    
    async def navigate(self, request: NavigateRequest) -> BrowserResponse:
        """Navigate to URL"""
        try:
            await self.initialize()
            
            if request.user_agent:
                await self.page.set_extra_http_headers({"User-Agent": request.user_agent})
            
            response = await self.page.goto(request.url, timeout=request.timeout)
            
            if request.wait_for_selector:
                await self.page.wait_for_selector(request.wait_for_selector, timeout=request.timeout)
            
            page_info = PageInfo(
                url=self.page.url,
                title=await self.page.title(),
                status_code=response.status if response else 0,
                content_type=response.headers.get("content-type", "") if response else ""
            )
            
            return BrowserResponse(
                success=True,
                data=page_info.dict(),
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return BrowserResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def click_element(self, request: ClickRequest) -> BrowserResponse:
        """Click on element"""
        try:
            await self.initialize()
            
            await self.page.click(request.selector)
            await asyncio.sleep(request.wait_after / 1000)
            
            return BrowserResponse(
                success=True,
                data={"clicked": request.selector},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return BrowserResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def type_text(self, request: TypeRequest) -> BrowserResponse:
        """Type text in input field"""
        try:
            await self.initialize()
            
            if request.clear_first:
                await self.page.fill(request.selector, "")
            
            await self.page.type(request.selector, request.text)
            
            return BrowserResponse(
                success=True,
                data={"typed": request.text, "selector": request.selector},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return BrowserResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def extract_content(self, request: ExtractRequest) -> BrowserResponse:
        """Extract content from page"""
        try:
            await self.initialize()
            
            if request.multiple:
                elements = await self.page.query_selector_all(request.selector)
                if request.attribute:
                    data = [await el.get_attribute(request.attribute) for el in elements]
                else:
                    data = [await el.text_content() for el in elements]
            else:
                element = await self.page.query_selector(request.selector)
                if not element:
                    raise Exception(f"Element not found: {request.selector}")
                
                if request.attribute:
                    data = await element.get_attribute(request.attribute)
                else:
                    data = await element.text_content()
            
            return BrowserResponse(
                success=True,
                data=data,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Extract failed: {e}")
            return BrowserResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def take_screenshot(self, request: ScreenshotRequest) -> BrowserResponse:
        """Take screenshot"""
        try:
            await self.initialize()
            
            if request.selector:
                element = await self.page.query_selector(request.selector)
                if not element:
                    raise Exception(f"Element not found: {request.selector}")
                screenshot_bytes = await element.screenshot()
            else:
                screenshot_bytes = await self.page.screenshot(full_page=request.full_page)
            
            # Encode as base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            
            return BrowserResponse(
                success=True,
                data={"screenshot": screenshot_b64, "format": "png"},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return BrowserResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def get_page_source(self) -> BrowserResponse:
        """Get current page HTML source"""
        try:
            await self.initialize()
            
            content = await self.page.content()
            
            return BrowserResponse(
                success=True,
                data={"html": content, "url": self.page.url},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Get source failed: {e}")
            return BrowserResponse(
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.is_initialized = False
            logger.info("Browser session cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global browser session
browser_session = BrowserSession()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "browser_server"}

@app.post("/navigate", response_model=BrowserResponse)
async def navigate_to_url(request: NavigateRequest):
    """Navigate to a URL"""
    return await browser_session.navigate(request)

@app.post("/click", response_model=BrowserResponse)
async def click_element(request: ClickRequest):
    """Click on an element"""
    return await browser_session.click_element(request)

@app.post("/type", response_model=BrowserResponse)
async def type_text(request: TypeRequest):
    """Type text in an input field"""
    return await browser_session.type_text(request)

@app.post("/extract", response_model=BrowserResponse)
async def extract_content(request: ExtractRequest):
    """Extract content from the page"""
    return await browser_session.extract_content(request)

@app.post("/screenshot", response_model=BrowserResponse)
async def take_screenshot(request: ScreenshotRequest):
    """Take a screenshot of the page or element"""
    return await browser_session.take_screenshot(request)

@app.get("/source", response_model=BrowserResponse)
async def get_page_source():
    """Get the current page HTML source"""
    return await browser_session.get_page_source()

@app.get("/current-url")
async def get_current_url():
    """Get the current page URL"""
    if browser_session.page:
        return {"url": browser_session.page.url}
    return {"url": None}

@app.post("/execute-script")
async def execute_script(script: str):
    """Execute JavaScript on the current page"""
    try:
        await browser_session.initialize()
        result = await browser_session.page.evaluate(script)
        
        return BrowserResponse(
            success=True,
            data=result,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        return BrowserResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.delete("/session")
async def close_session():
    """Close the current browser session"""
    await browser_session.cleanup()
    return {"message": "Browser session closed"}

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await browser_session.cleanup()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Browser MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8003, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Browser MCP Server on {args.host}:{args.port}")
    logger.info("Note: Requires 'pip install playwright && playwright install'")
    
    uvicorn.run(
        "browser_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )