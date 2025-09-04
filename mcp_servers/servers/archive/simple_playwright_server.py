#!/usr/bin/env python3
"""
Simple Playwright Server for Open WebUI - No Enums
Provides basic web automation without complex enums to avoid Vertex AI issues
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Simple Playwright Web Tools",
    description="Basic web automation tools without complex enums",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global browser instance
browser: Optional[Browser] = None
context: Optional[BrowserContext] = None
page: Optional[Page] = None

# Simple request models without enums
class NavigateRequest(BaseModel):
    url: str
    timeout: int = 30000

class ClickRequest(BaseModel):
    selector: str
    timeout: int = 5000

class FillRequest(BaseModel):
    selector: str
    value: str
    timeout: int = 5000

class ExtractRequest(BaseModel):
    selector: str = "body"
    timeout: int = 5000

class ScreenshotRequest(BaseModel):
    full_page: bool = False

class NewsSearchRequest(BaseModel):
    query: str = "latest news"
    source: str = "google"  # google, cnn, bbc, etc.
    max_results: int = 10

# Browser management
async def get_browser():
    global browser, context, page
    if not browser:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        logger.info("Browser started successfully")
    return browser, context, page

async def cleanup_browser():
    global browser, context, page
    try:
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()
        page = context = browser = None
        logger.info("Browser cleanup completed")
    except Exception as e:
        logger.error(f"Error during browser cleanup: {e}")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting simple Playwright server...")
    await get_browser()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down simple Playwright server...")
    await cleanup_browser()

# Tool endpoints
@app.post("/navigate")
async def navigate_to_page(request: NavigateRequest) -> str:
    """Navigate to a web page"""
    try:
        _, _, current_page = await get_browser()
        
        logger.info(f"Navigating to: {request.url}")
        response = await current_page.goto(request.url, timeout=request.timeout)
        
        title = await current_page.title()
        url = current_page.url
        
        return f"Successfully navigated to {url}. Page title: {title}. Status: {response.status if response else 'OK'}"
        
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        return f"Navigation failed: {str(e)}"

@app.post("/extract_text")
async def extract_text(request: ExtractRequest) -> str:
    """Extract text from page elements"""
    try:
        _, _, current_page = await get_browser()
        
        # Wait for element to be present
        await current_page.wait_for_selector(request.selector, timeout=request.timeout)
        
        # Extract text content
        elements = await current_page.query_selector_all(request.selector)
        texts = []
        for element in elements:
            text = await element.inner_text()
            if text and text.strip():
                texts.append(text.strip())
        
        result = "\n".join(texts)
        logger.info(f"Extracted {len(result)} characters from {request.selector}")
        
        # Enhanced truncation with better formatting
        if len(result) > 3000:
            result = result[:3000] + "\n\n[Content truncated - showing first 3000 characters]"
        
        return f"Text extracted from '{request.selector}':\n\n{result}"
            
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return f"Text extraction failed: {str(e)}"

@app.post("/click")
async def click_element(request: ClickRequest) -> str:
    """Click an element on the page"""
    try:
        _, _, current_page = await get_browser()
        
        # Wait for element and click
        await current_page.wait_for_selector(request.selector, timeout=request.timeout)
        await current_page.click(request.selector)
        
        logger.info(f"Clicked element: {request.selector}")
        return f"Successfully clicked element: {request.selector}"
        
    except Exception as e:
        logger.error(f"Click failed: {e}")
        return f"Click failed: {str(e)}"

@app.post("/fill")
async def fill_form_field(request: FillRequest) -> str:
    """Fill a form field with text"""
    try:
        _, _, current_page = await get_browser()
        
        # Wait for element and fill
        await current_page.wait_for_selector(request.selector, timeout=request.timeout)
        await current_page.fill(request.selector, request.value)
        
        logger.info(f"Filled '{request.selector}' with '{request.value}'")
        return f"Successfully filled '{request.selector}' with '{request.value}'"
        
    except Exception as e:
        logger.error(f"Fill failed: {e}")
        return f"Fill failed: {str(e)}"

@app.post("/screenshot")
async def take_screenshot(request: ScreenshotRequest) -> str:
    """Take a screenshot of the page"""
    try:
        _, _, current_page = await get_browser()
        
        # Take screenshot
        screenshot_bytes = await current_page.screenshot(
            full_page=request.full_page,
            type="png"
        )
        
        # Save to file
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/tmp/screenshot_{timestamp}.png"
        
        with open(filename, "wb") as f:
            f.write(screenshot_bytes)
        
        logger.info(f"Screenshot saved: {filename} ({len(screenshot_bytes)} bytes)")
        return f"Screenshot saved to: {filename}. Size: {len(screenshot_bytes)} bytes. Full page: {request.full_page}"
        
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return f"Screenshot failed: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Simple Playwright Web Tools API for Open WebUI", "status": "running"}

@app.post("/search_news")
async def search_news(request: NewsSearchRequest) -> str:
    """Enhanced news search with better formatting"""
    try:
        _, _, current_page = await get_browser()
        
        # Navigate to Google News specifically
        if request.source.lower() == "google":
            search_url = f"https://news.google.com/search?q={request.query.replace(' ', '%20')}"
        else:
            search_url = f"https://www.google.com/search?q={request.query.replace(' ', '%20')}%20news&tbm=nws"
        
        logger.info(f"Searching news: {search_url}")
        await current_page.goto(search_url, timeout=15000)
        
        # Wait for results to load
        await current_page.wait_for_selector("article, .result, .g", timeout=10000)
        
        # Extract news headlines and snippets
        headlines_selector = "article h3, .LC20lb, h3 a, [role='heading']"
        snippets_selector = ".st, .Y3v8qd, .s3v9rd"
        
        headlines = await current_page.query_selector_all(headlines_selector)
        snippets = await current_page.query_selector_all(snippets_selector)
        
        news_items = []
        count = 0
        
        for i, headline in enumerate(headlines[:request.max_results]):
            if count >= request.max_results:
                break
                
            try:
                title = await headline.inner_text()
                title = title.strip()
                
                if title and len(title) > 10:  # Filter out very short titles
                    snippet = ""
                    if i < len(snippets):
                        snippet_text = await snippets[i].inner_text()
                        snippet = snippet_text.strip()[:200] + "..." if len(snippet_text) > 200 else snippet_text.strip()
                    
                    news_items.append(f"**{title}**\n{snippet}\n")
                    count += 1
            except:
                continue
        
        if not news_items:
            # Fallback to generic text extraction
            await current_page.wait_for_selector("body", timeout=5000)
            content = await current_page.inner_text("body")
            return f"News search results for '{request.query}':\n\n{content[:2000]}..."
        
        result = f"📰 Latest News Results for '{request.query}':\n\n" + "\n".join(news_items)
        
        logger.info(f"Found {len(news_items)} news items")
        return result
        
    except Exception as e:
        logger.error(f"News search failed: {e}")
        return f"News search failed: {str(e)}"

@app.get("/health")
async def health():
    try:
        _, _, current_page = await get_browser()
        browser_status = "connected" if current_page else "disconnected"
        return {
            "status": "healthy", 
            "browser": browser_status,
            "tools": ["navigate", "click", "fill", "extract_text", "screenshot", "search_news"]
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)