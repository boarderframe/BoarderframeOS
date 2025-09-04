#!/usr/bin/env python3
"""
Real Playwright MCP Server for Open WebUI
Web automation and scraping tools with actual Playwright implementation
"""
import asyncio
import base64
import os
import tempfile
import time
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright
from pydantic import BaseModel, Field, validator

# Global browser management
_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_contexts: Dict[str, BrowserContext] = {}
_pages: Dict[str, Page] = {}


# Request models with enhanced validation
class NavigateRequest(BaseModel):
    url: str = Field(..., description="URL to navigate to")
    timeout: int = Field(30000, description="Navigation timeout in milliseconds", ge=1000, le=120000)
    wait_until: str = Field("load", description="When to consider navigation successful")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('wait_until')
    def validate_wait_until(cls, v):
        valid_options = ['load', 'domcontentloaded', 'networkidle', 'commit']
        if v not in valid_options:
            raise ValueError(f'wait_until must be one of: {valid_options}')
        return v


class ClickRequest(BaseModel):
    selector: str = Field(..., description="CSS selector for element to click")
    page_id: str = Field("default", description="Page identifier")
    timeout: int = Field(30000, description="Timeout for finding element")
    button: str = Field("left", description="Mouse button to click")
    click_count: int = Field(1, description="Number of clicks", ge=1, le=3)
    
    @validator('button')
    def validate_button(cls, v):
        valid_buttons = ['left', 'right', 'middle']
        if v not in valid_buttons:
            raise ValueError(f'button must be one of: {valid_buttons}')
        return v


class FillRequest(BaseModel):
    selector: str = Field(..., description="CSS selector for input element")
    value: str = Field(..., description="Text to fill")
    page_id: str = Field("default", description="Page identifier")
    timeout: int = Field(30000, description="Timeout for finding element")
    clear_first: bool = Field(True, description="Clear field before filling")


class ExtractRequest(BaseModel):
    selector: str = Field("body", description="CSS selector for element(s) to extract text from")
    page_id: str = Field("default", description="Page identifier")
    attribute: Optional[str] = Field(None, description="Attribute to extract instead of text")
    all_elements: bool = Field(False, description="Extract from all matching elements")
    timeout: int = Field(10000, description="Timeout for finding element")


class ScreenshotRequest(BaseModel):
    page_id: str = Field("default", description="Page identifier")
    full_page: bool = Field(False, description="Take full page screenshot")
    element_selector: Optional[str] = Field(None, description="Take screenshot of specific element")
    format: str = Field("png", description="Screenshot format")
    quality: Optional[int] = Field(None, description="JPEG quality (0-100)", ge=0, le=100)
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['png', 'jpeg']
        if v not in valid_formats:
            raise ValueError(f'format must be one of: {valid_formats}')
        return v


class WaitRequest(BaseModel):
    selector: str = Field(..., description="CSS selector to wait for")
    page_id: str = Field("default", description="Page identifier")
    timeout: int = Field(30000, description="Timeout for waiting")
    state: str = Field("visible", description="State to wait for")
    
    @validator('state')
    def validate_state(cls, v):
        valid_states = ['attached', 'detached', 'visible', 'hidden']
        if v not in valid_states:
            raise ValueError(f'state must be one of: {valid_states}')
        return v


# Browser lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage browser lifecycle."""
    global _playwright, _browser
    
    # Startup
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
    )
    
    yield
    
    # Shutdown
    for page_id, page in _pages.items():
        try:
            await page.close()
        except Exception:
            pass
    
    for context_id, context in _contexts.items():
        try:
            await context.close()
        except Exception:
            pass
    
    if _browser:
        await _browser.close()
    
    if _playwright:
        await _playwright.stop()


app = FastAPI(
    title="Real Playwright Web Tools",
    description="Web automation and scraping tools using actual Playwright browser automation",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_or_create_page(page_id: str = "default") -> Page:
    """Get or create a browser page."""
    global _browser, _contexts, _pages
    
    if not _browser:
        raise HTTPException(status_code=500, detail="Browser not initialized")
    
    if page_id not in _pages:
        # Create new context and page
        context = await _browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        _contexts[page_id] = context
        _pages[page_id] = page
    
    return _pages[page_id]


# API Endpoints
@app.post("/navigate")
async def navigate_to_page(request: NavigateRequest) -> dict:
    """Navigate to a web page."""
    try:
        page = await get_or_create_page()
        
        start_time = time.time()
        
        response = await page.goto(
            request.url,
            timeout=request.timeout,
            wait_until=request.wait_until
        )
        
        navigation_time = time.time() - start_time
        
        if not response:
            raise HTTPException(status_code=400, detail=f"Failed to navigate to {request.url}")
        
        title = await page.title()
        url = page.url
        
        return {
            "success": True,
            "url": url,
            "title": title,
            "status_code": response.status,
            "navigation_time": round(navigation_time, 3),
            "message": f"Successfully navigated to {request.url}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Navigation failed: {str(e)}"
        }


@app.post("/click")
async def click_element(request: ClickRequest) -> dict:
    """Click an element on the page."""
    try:
        page = await get_or_create_page(request.page_id)
        
        # Wait for element to be visible
        await page.wait_for_selector(request.selector, timeout=request.timeout, state="visible")
        
        # Perform click
        await page.click(
            request.selector,
            button=request.button,
            click_count=request.click_count,
            timeout=request.timeout
        )
        
        return {
            "success": True,
            "selector": request.selector,
            "message": f"Successfully clicked element: {request.selector}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Click failed: {str(e)}"
        }


@app.post("/fill")
async def fill_form_field(request: FillRequest) -> dict:
    """Fill a form field with text."""
    try:
        page = await get_or_create_page(request.page_id)
        
        # Wait for element
        await page.wait_for_selector(request.selector, timeout=request.timeout)
        
        if request.clear_first:
            await page.fill(request.selector, "")
        
        await page.fill(request.selector, request.value)
        
        # Verify the value was set
        actual_value = await page.input_value(request.selector)
        
        return {
            "success": True,
            "selector": request.selector,
            "value": request.value,
            "actual_value": actual_value,
            "message": f"Successfully filled '{request.selector}' with '{request.value}'"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Fill failed: {str(e)}"
        }


@app.post("/extract_text")
async def extract_text(request: ExtractRequest) -> dict:
    """Extract text from page elements."""
    try:
        page = await get_or_create_page(request.page_id)
        
        # Wait for element
        await page.wait_for_selector(request.selector, timeout=request.timeout)
        
        if request.all_elements:
            elements = await page.query_selector_all(request.selector)
            results = []
            
            for i, element in enumerate(elements):
                if request.attribute:
                    content = await element.get_attribute(request.attribute)
                else:
                    content = await element.text_content()
                
                results.append({
                    "index": i,
                    "content": content,
                    "selector": request.selector
                })
            
            return {
                "success": True,
                "selector": request.selector,
                "count": len(results),
                "results": results,
                "message": f"Extracted text from {len(results)} elements matching '{request.selector}'"
            }
        else:
            element = await page.query_selector(request.selector)
            if not element:
                raise Exception(f"Element not found: {request.selector}")
            
            if request.attribute:
                content = await element.get_attribute(request.attribute)
            else:
                content = await element.text_content()
            
            return {
                "success": True,
                "selector": request.selector,
                "content": content,
                "length": len(content) if content else 0,
                "message": f"Extracted text from '{request.selector}': {len(content) if content else 0} characters"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Text extraction failed: {str(e)}"
        }


@app.post("/screenshot")
async def take_screenshot(request: ScreenshotRequest) -> dict:
    """Take a screenshot of the page or element."""
    try:
        page = await get_or_create_page(request.page_id)
        
        screenshot_options = {
            "type": request.format,
            "full_page": request.full_page
        }
        
        if request.format == "jpeg" and request.quality:
            screenshot_options["quality"] = request.quality
        
        if request.element_selector:
            # Screenshot specific element
            element = await page.query_selector(request.element_selector)
            if not element:
                raise Exception(f"Element not found: {request.element_selector}")
            screenshot_bytes = await element.screenshot(**screenshot_options)
        else:
            # Screenshot entire page/viewport
            screenshot_bytes = await page.screenshot(**screenshot_options)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f".{request.format}",
            prefix="playwright_screenshot_"
        ) as temp_file:
            temp_file.write(screenshot_bytes)
            screenshot_path = temp_file.name
        
        # Convert to base64 for API response
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        return {
            "success": True,
            "path": screenshot_path,
            "size_bytes": len(screenshot_bytes),
            "format": request.format,
            "full_page": request.full_page,
            "base64": screenshot_base64,
            "message": f"Screenshot saved to: {screenshot_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Screenshot failed: {str(e)}"
        }


@app.post("/wait_for_element")
async def wait_for_element(request: WaitRequest) -> dict:
    """Wait for an element to appear on the page."""
    try:
        page = await get_or_create_page(request.page_id)
        
        start_time = time.time()
        
        await page.wait_for_selector(
            request.selector,
            timeout=request.timeout,
            state=request.state
        )
        
        wait_time = time.time() - start_time
        
        return {
            "success": True,
            "selector": request.selector,
            "state": request.state,
            "wait_time": round(wait_time, 3),
            "message": f"Element '{request.selector}' appeared after {wait_time:.3f} seconds"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Wait failed: {str(e)}"
        }


@app.post("/execute_script")
async def execute_script(page_id: str = "default", script: str = "") -> dict:
    """Execute JavaScript on the page."""
    try:
        page = await get_or_create_page(page_id)
        
        result = await page.evaluate(script)
        
        return {
            "success": True,
            "result": result,
            "message": "Script executed successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Script execution failed: {str(e)}"
        }


@app.get("/page_info")
async def get_page_info(page_id: str = "default") -> dict:
    """Get information about the current page."""
    try:
        page = await get_or_create_page(page_id)
        
        return {
            "success": True,
            "url": page.url,
            "title": await page.title(),
            "viewport": page.viewport_size,
            "message": "Page info retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get page info: {str(e)}"
        }


@app.delete("/close_page")
async def close_page(page_id: str = "default") -> dict:
    """Close a browser page and context."""
    try:
        if page_id in _pages:
            await _pages[page_id].close()
            del _pages[page_id]
        
        if page_id in _contexts:
            await _contexts[page_id].close()
            del _contexts[page_id]
        
        return {
            "success": True,
            "message": f"Page '{page_id}' closed successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to close page: {str(e)}"
        }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Real Playwright Web Tools API for Open WebUI",
        "version": "2.0.0",
        "status": "ready"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    browser_status = "connected" if _browser and _browser.is_connected() else "disconnected"
    
    return {
        "status": "healthy",
        "browser_status": browser_status,
        "active_pages": len(_pages),
        "active_contexts": len(_contexts),
        "tools": [
            "navigate", "click", "fill", "extract_text", 
            "screenshot", "wait_for_element", "execute_script",
            "page_info", "close_page"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)