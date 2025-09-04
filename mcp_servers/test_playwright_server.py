#!/usr/bin/env python3
"""
Test script for the Real Playwright MCP Server
Demonstrates the server's capabilities without requiring full MCP setup.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from real_playwright_server import PlaywrightTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_playwright_tools():
    """Test all Playwright tools with a real website."""
    
    # Import the global browser manager
    from real_playwright_server import browser_manager
    
    try:
        await browser_manager.initialize()
        logger.info("Browser initialized successfully")
        
        # Test 1: Navigate to a test website
        logger.info("\n=== Test 1: Navigation ===")
        result = await PlaywrightTools.navigate("https://httpbin.org/html")
        print(f"Navigation result: {json.dumps(result, indent=2)}")
        
        # Test 2: Extract page text
        logger.info("\n=== Test 2: Text Extraction ===")
        result = await PlaywrightTools.extract_text()
        print(f"Text extraction result: {json.dumps(result, indent=2)[:500]}...")
        
        # Test 3: Extract specific element text
        logger.info("\n=== Test 3: Specific Element Text ===")
        result = await PlaywrightTools.extract_text(selector="h1")
        print(f"H1 text result: {json.dumps(result, indent=2)}")
        
        # Test 4: Take a screenshot
        logger.info("\n=== Test 4: Screenshot ===")
        result = await PlaywrightTools.screenshot()
        if result.get("success"):
            screenshot_data = result.get("screenshot", "")
            print(f"Screenshot taken: {len(screenshot_data)} characters of base64 data")
            result_summary = {k: v for k, v in result.items() if k != "screenshot"}
            print(f"Screenshot metadata: {json.dumps(result_summary, indent=2)}")
        else:
            print(f"Screenshot failed: {json.dumps(result, indent=2)}")
        
        # Test 5: Navigate to a form page and test interactions
        logger.info("\n=== Test 5: Form Interaction ===")
        result = await PlaywrightTools.navigate("https://httpbin.org/forms/post")
        print(f"Form page navigation: {json.dumps(result, indent=2)}")
        
        # Test 6: Wait for an element
        logger.info("\n=== Test 6: Wait for Element ===")
        result = await PlaywrightTools.wait_for_element("input[name='custname']")
        print(f"Wait for element result: {json.dumps(result, indent=2)}")
        
        # Test 7: Fill a form field
        logger.info("\n=== Test 7: Fill Form Field ===")
        result = await PlaywrightTools.fill("input[name='custname']", "Test User")
        print(f"Fill field result: {json.dumps(result, indent=2)}")
        
        # Test 8: Fill another field
        logger.info("\n=== Test 8: Fill Email Field ===")
        result = await PlaywrightTools.fill("input[name='custemail']", "test@example.com")
        print(f"Fill email result: {json.dumps(result, indent=2)}")
        
        # Test 9: Get page info
        logger.info("\n=== Test 9: Page Info ===")
        result = await PlaywrightTools.get_page_info()
        print(f"Page info result: {json.dumps(result, indent=2)}")
        
        # Test 10: Try clicking the submit button
        logger.info("\n=== Test 10: Click Submit Button ===")
        result = await PlaywrightTools.click("input[type='submit']", wait_for_navigation=True)
        print(f"Click submit result: {json.dumps(result, indent=2)}")
        
        # Test 11: Final page info after form submission
        logger.info("\n=== Test 11: Final Page Info ===")
        result = await PlaywrightTools.get_page_info()
        print(f"Final page info: {json.dumps(result, indent=2)}")
        
        logger.info("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        await browser_manager.cleanup()
        logger.info("Browser cleanup completed")


if __name__ == "__main__":
    print("Testing Real Playwright MCP Server...")
    print("This will open a browser and test various automation features.")
    print("=" * 60)
    
    asyncio.run(test_playwright_tools())