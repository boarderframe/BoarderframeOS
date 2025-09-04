#!/usr/bin/env python3
"""
Real Playwright MCP Server
A Model Context Protocol server providing real web browser automation capabilities using Playwright.

This server implements comprehensive browser automation tools including:
- Page navigation and content extraction
- Element interaction (click, fill, wait)
- Screenshot capture
- Session management with proper cleanup
- OpenAPI compatibility for Open WebUI integration
"""

import asyncio
import base64
import json
import logging
import os
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import anyio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)
from playwright.async_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("playwright_mcp.log")
    ]
)
logger = logging.getLogger("playwright-mcp-server")

# Configuration
DEFAULT_TIMEOUT = 30000  # 30 seconds
MAX_CONTENT_LENGTH = 100000  # Limit content extraction length
SCREENSHOT_QUALITY = 90
HEADLESS_MODE = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
BROWSER_TYPE = os.getenv("PLAYWRIGHT_BROWSER", "chromium")  # chromium, firefox, webkit


class BrowserManager:
    """Manages browser instances and contexts with proper cleanup."""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.default_context_id = "default"
        
    async def initialize(self) -> None:
        """Initialize Playwright and browser."""
        try:
            logger.info("Initializing Playwright browser manager")
            self.playwright = await async_playwright().start()
            
            # Select browser based on configuration
            if BROWSER_TYPE == "firefox":
                browser_launcher = self.playwright.firefox
            elif BROWSER_TYPE == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                browser_launcher = self.playwright.chromium
                
            # Launch browser with optimized settings
            self.browser = await browser_launcher.launch(
                headless=HEADLESS_MODE,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-dev-shm-usage",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                ]
            )
            
            # Create default context
            await self._get_or_create_context(self.default_context_id)
            logger.info(f"Browser initialized successfully ({BROWSER_TYPE}, headless={HEADLESS_MODE})")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def _get_or_create_context(self, context_id: str) -> BrowserContext:
        """Get existing context or create new one."""
        if context_id not in self.contexts:
            if not self.browser:
                raise RuntimeError("Browser not initialized")
                
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ignore_https_errors=True,
                java_script_enabled=True,
            )
            
            # Set reasonable timeouts
            context.set_default_timeout(DEFAULT_TIMEOUT)
            context.set_default_navigation_timeout(DEFAULT_TIMEOUT)
            
            self.contexts[context_id] = context
            logger.info(f"Created new browser context: {context_id}")
            
        return self.contexts[context_id]
    
    async def get_page(self, context_id: str = None, page_id: str = None) -> Page:
        """Get or create a page in the specified context."""
        context_id = context_id or self.default_context_id
        page_key = f"{context_id}:{page_id}" if page_id else f"{context_id}:default"
        
        if page_key not in self.pages:
            context = await self._get_or_create_context(context_id)
            page = await context.new_page()
            self.pages[page_key] = page
            logger.info(f"Created new page: {page_key}")
            
        return self.pages[page_key]
    
    async def close_page(self, context_id: str = None, page_id: str = None) -> None:
        """Close a specific page."""
        context_id = context_id or self.default_context_id
        page_key = f"{context_id}:{page_id}" if page_id else f"{context_id}:default"
        
        if page_key in self.pages:
            await self.pages[page_key].close()
            del self.pages[page_key]
            logger.info(f"Closed page: {page_key}")
    
    async def close_context(self, context_id: str) -> None:
        """Close a browser context and all its pages."""
        if context_id in self.contexts:
            # Close all pages in this context
            pages_to_close = [key for key in self.pages.keys() if key.startswith(f"{context_id}:")]
            for page_key in pages_to_close:
                await self.pages[page_key].close()
                del self.pages[page_key]
            
            # Close the context
            await self.contexts[context_id].close()
            del self.contexts[context_id]
            logger.info(f"Closed browser context: {context_id}")
    
    async def cleanup(self) -> None:
        """Clean up all browser resources."""
        try:
            logger.info("Starting browser cleanup")
            
            # Close all pages
            for page in self.pages.values():
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")
            self.pages.clear()
            
            # Close all contexts
            for context in self.contexts.values():
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")
            self.contexts.clear()
            
            # Close browser
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Browser cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global browser manager instance
browser_manager = BrowserManager()


class PlaywrightTools:
    """Collection of Playwright automation tools."""
    
    @staticmethod
    async def navigate(
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: int = DEFAULT_TIMEOUT,
        context_id: str = None,
        page_id: str = None,
        _browser_manager: BrowserManager = None
    ) -> Dict[str, Any]:
        """Navigate to a URL and return page information."""
        try:
            manager = _browser_manager or browser_manager
            page = await manager.get_page(context_id, page_id)
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = f"https://{url}"
            
            logger.info(f"Navigating to: {url}")
            
            # Navigate with timeout
            response = await page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout
            )
            
            # Get page information
            title = await page.title()
            current_url = page.url
            
            result = {
                "success": True,
                "url": current_url,
                "title": title,
                "status_code": response.status if response else None,
                "final_url": current_url
            }
            
            logger.info(f"Navigation successful: {title} ({current_url})")
            return result
            
        except PlaywrightTimeoutError:
            error_msg = f"Navigation timeout after {timeout}ms"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "timeout"}
        except Exception as e:
            error_msg = f"Navigation failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "navigation_error"}
    
    @staticmethod
    async def extract_text(
        selector: str = None,
        max_length: int = MAX_CONTENT_LENGTH,
        context_id: str = None,
        page_id: str = None
    ) -> Dict[str, Any]:
        """Extract text content from the page or specific elements."""
        try:
            page = await browser_manager.get_page(context_id, page_id)
            
            if selector:
                # Extract text from specific elements
                elements = await page.query_selector_all(selector)
                if not elements:
                    return {
                        "success": False,
                        "error": f"No elements found with selector: {selector}",
                        "type": "element_not_found"
                    }
                
                texts = []
                for element in elements:
                    text = await element.inner_text()
                    if text.strip():
                        texts.append(text.strip())
                
                result_text = "\n".join(texts)
            else:
                # Extract all page text
                result_text = await page.inner_text("body")
            
            # Truncate if too long
            if len(result_text) > max_length:
                result_text = result_text[:max_length] + "..."
                truncated = True
            else:
                truncated = False
            
            logger.info(f"Extracted {len(result_text)} characters of text")
            
            return {
                "success": True,
                "text": result_text,
                "length": len(result_text),
                "truncated": truncated,
                "selector": selector
            }
            
        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "extraction_error"}
    
    @staticmethod
    async def click(
        selector: str,
        timeout: int = DEFAULT_TIMEOUT,
        wait_for_navigation: bool = False,
        context_id: str = None,
        page_id: str = None
    ) -> Dict[str, Any]:
        """Click on an element specified by selector."""
        try:
            page = await browser_manager.get_page(context_id, page_id)
            
            logger.info(f"Clicking element: {selector}")
            
            # Wait for element to be visible and enabled
            element = await page.wait_for_selector(
                selector,
                state="visible",
                timeout=timeout
            )
            
            if not element:
                return {
                    "success": False,
                    "error": f"Element not found or not visible: {selector}",
                    "type": "element_not_found"
                }
            
            # Scroll element into view
            await element.scroll_into_view_if_needed()
            
            # Perform click
            if wait_for_navigation:
                async with page.expect_navigation(timeout=timeout):
                    await element.click()
            else:
                await element.click()
            
            logger.info(f"Successfully clicked: {selector}")
            
            return {
                "success": True,
                "selector": selector,
                "action": "click"
            }
            
        except PlaywrightTimeoutError:
            error_msg = f"Click timeout: element '{selector}' not found within {timeout}ms"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "timeout"}
        except Exception as e:
            error_msg = f"Click failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "click_error"}
    
    @staticmethod
    async def fill(
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        context_id: str = None,
        page_id: str = None
    ) -> Dict[str, Any]:
        """Fill an input field with text."""
        try:
            page = await browser_manager.get_page(context_id, page_id)
            
            logger.info(f"Filling element '{selector}' with text")
            
            # Wait for element to be visible
            element = await page.wait_for_selector(
                selector,
                state="visible",
                timeout=timeout
            )
            
            if not element:
                return {
                    "success": False,
                    "error": f"Element not found: {selector}",
                    "type": "element_not_found"
                }
            
            # Scroll into view and focus
            await element.scroll_into_view_if_needed()
            await element.focus()
            
            # Clear existing content if requested
            if clear_first:
                await element.select_text()
                await element.press("Delete")
            
            # Fill with new text
            await element.fill(text)
            
            logger.info(f"Successfully filled: {selector}")
            
            return {
                "success": True,
                "selector": selector,
                "action": "fill",
                "text_length": len(text)
            }
            
        except PlaywrightTimeoutError:
            error_msg = f"Fill timeout: element '{selector}' not found within {timeout}ms"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "timeout"}
        except Exception as e:
            error_msg = f"Fill failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "fill_error"}
    
    @staticmethod
    async def screenshot(
        full_page: bool = False,
        quality: int = SCREENSHOT_QUALITY,
        format: str = "png",
        context_id: str = None,
        page_id: str = None
    ) -> Dict[str, Any]:
        """Take a screenshot of the current page."""
        try:
            page = await browser_manager.get_page(context_id, page_id)
            
            logger.info("Taking screenshot")
            
            # Take screenshot
            screenshot_options = {
                "full_page": full_page,
                "type": format,
            }
            
            if format == "jpeg":
                screenshot_options["quality"] = quality
            
            screenshot_bytes = await page.screenshot(**screenshot_options)
            
            # Encode as base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
            
            logger.info(f"Screenshot taken: {len(screenshot_bytes)} bytes")
            
            return {
                "success": True,
                "screenshot": screenshot_base64,
                "format": format,
                "size_bytes": len(screenshot_bytes),
                "full_page": full_page
            }
            
        except Exception as e:
            error_msg = f"Screenshot failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "screenshot_error"}
    
    @staticmethod
    async def wait_for_element(
        selector: str,
        state: str = "visible",
        timeout: int = DEFAULT_TIMEOUT,
        context_id: str = None,
        page_id: str = None
    ) -> Dict[str, Any]:
        """Wait for an element to reach a specific state."""
        try:
            page = await browser_manager.get_page(context_id, page_id)
            
            logger.info(f"Waiting for element '{selector}' to be {state}")
            
            # Wait for element
            element = await page.wait_for_selector(
                selector,
                state=state,
                timeout=timeout
            )
            
            if element:
                # Get element information
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                
                logger.info(f"Element found: {selector}")
                
                return {
                    "success": True,
                    "selector": selector,
                    "state": state,
                    "found": True,
                    "visible": is_visible,
                    "enabled": is_enabled,
                    "tag_name": tag_name
                }
            else:
                return {
                    "success": False,
                    "error": f"Element '{selector}' not found in state '{state}'",
                    "type": "element_not_found"
                }
                
        except PlaywrightTimeoutError:
            error_msg = f"Wait timeout: element '{selector}' not found in state '{state}' within {timeout}ms"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "timeout"}
        except Exception as e:
            error_msg = f"Wait for element failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "wait_error"}
    
    @staticmethod
    async def get_page_info(
        context_id: str = None,
        page_id: str = None
    ) -> Dict[str, Any]:
        """Get current page information."""
        try:
            page = await browser_manager.get_page(context_id, page_id)
            
            title = await page.title()
            url = page.url
            
            return {
                "success": True,
                "title": title,
                "url": url,
                "context_id": context_id or browser_manager.default_context_id,
                "page_id": page_id or "default"
            }
            
        except Exception as e:
            error_msg = f"Get page info failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "type": "info_error"}


# MCP Server setup
server = Server("playwright-mcp-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available Playwright automation tools."""
    return [
        Tool(
            name="navigate",
            description="Navigate to a URL in the browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to"
                    },
                    "wait_until": {
                        "type": "string",
                        "enum": ["load", "domcontentloaded", "networkidle"],
                        "default": "domcontentloaded",
                        "description": "When to consider navigation complete"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": DEFAULT_TIMEOUT,
                        "description": "Navigation timeout in milliseconds"
                    },
                    "context_id": {
                        "type": "string",
                        "description": "Browser context ID (optional)"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Page ID within context (optional)"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="extract_text",
            description="Extract text content from the page or specific elements",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to extract text from (optional, extracts all page text if not provided)"
                    },
                    "max_length": {
                        "type": "integer",
                        "default": MAX_CONTENT_LENGTH,
                        "description": "Maximum length of extracted text"
                    },
                    "context_id": {
                        "type": "string",
                        "description": "Browser context ID (optional)"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Page ID within context (optional)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="click",
            description="Click on an element specified by CSS selector",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to click"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": DEFAULT_TIMEOUT,
                        "description": "Timeout in milliseconds"
                    },
                    "wait_for_navigation": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to wait for navigation after click"
                    },
                    "context_id": {
                        "type": "string",
                        "description": "Browser context ID (optional)"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Page ID within context (optional)"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="fill",
            description="Fill an input field with text",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the input field"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to fill in the field"
                    },
                    "clear_first": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to clear existing content first"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": DEFAULT_TIMEOUT,
                        "description": "Timeout in milliseconds"
                    },
                    "context_id": {
                        "type": "string",
                        "description": "Browser context ID (optional)"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Page ID within context (optional)"
                    }
                },
                "required": ["selector", "text"]
            }
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "full_page": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to capture the full page or just viewport"
                    },
                    "quality": {
                        "type": "integer",
                        "default": SCREENSHOT_QUALITY,
                        "minimum": 0,
                        "maximum": 100,
                        "description": "JPEG quality (0-100, only for JPEG format)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["png", "jpeg"],
                        "default": "png",
                        "description": "Screenshot format"
                    },
                    "context_id": {
                        "type": "string",
                        "description": "Browser context ID (optional)"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Page ID within context (optional)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="wait_for_element",
            description="Wait for an element to appear or reach a specific state",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to wait for"
                    },
                    "state": {
                        "type": "string",
                        "enum": ["attached", "detached", "visible", "hidden"],
                        "default": "visible",
                        "description": "State to wait for"
                    },
                    "timeout": {
                        "type": "integer",
                        "default": DEFAULT_TIMEOUT,
                        "description": "Timeout in milliseconds"
                    },
                    "context_id": {
                        "type": "string",
                        "description": "Browser context ID (optional)"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Page ID within context (optional)"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="get_page_info",
            description="Get information about the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "context_id": {
                        "type": "string",
                        "description": "Browser context ID (optional)"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Page ID within context (optional)"
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls with proper error handling and logging."""
    try:
        logger.info(f"Executing tool: {name} with arguments: {json.dumps(arguments, indent=2)}")
        
        # Route to appropriate tool
        if name == "navigate":
            result = await PlaywrightTools.navigate(**arguments)
        elif name == "extract_text":
            result = await PlaywrightTools.extract_text(**arguments)
        elif name == "click":
            result = await PlaywrightTools.click(**arguments)
        elif name == "fill":
            result = await PlaywrightTools.fill(**arguments)
        elif name == "screenshot":
            result = await PlaywrightTools.screenshot(**arguments)
        elif name == "wait_for_element":
            result = await PlaywrightTools.wait_for_element(**arguments)
        elif name == "get_page_info":
            result = await PlaywrightTools.get_page_info(**arguments)
        else:
            result = {
                "success": False,
                "error": f"Unknown tool: {name}",
                "type": "unknown_tool"
            }
        
        logger.info(f"Tool {name} completed: {result.get('success', False)}")
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        error_msg = f"Tool execution error: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        error_result = {
            "success": False,
            "error": error_msg,
            "type": "execution_error",
            "tool": name
        }
        
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Playwright MCP Server")
        
        # Initialize browser manager
        await browser_manager.initialize()
        
        # Setup cleanup on exit
        import signal
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown")
            asyncio.create_task(cleanup_and_exit())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP server started successfully")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="playwright-mcp-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}\n{traceback.format_exc()}")
    finally:
        await cleanup_and_exit()


async def cleanup_and_exit():
    """Cleanup resources and exit gracefully."""
    try:
        logger.info("Performing cleanup...")
        await browser_manager.cleanup()
        logger.info("Cleanup completed, exiting")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    finally:
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)