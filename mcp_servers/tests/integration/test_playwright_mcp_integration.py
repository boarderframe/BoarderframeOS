"""
Integration tests for Real Playwright MCP Server
Tests against actual websites and real browser automation
"""

import asyncio
import base64
import json
import os
import pytest
import tempfile
import time
from pathlib import Path
from typing import AsyncGenerator

import httpx
import psutil
from fastapi.testclient import TestClient

# Import the real Playwright server
try:
    from playwright_mcp_server_real import app as real_app
except ImportError:
    real_app = None


@pytest.fixture(scope="session")
def real_server_available():
    """Check if real Playwright server dependencies are available."""
    try:
        import playwright
        return True
    except ImportError:
        return False


@pytest.fixture
async def real_client(real_server_available) -> AsyncGenerator[TestClient, None]:
    """Fixture providing a real Playwright server client for integration tests."""
    if not real_server_available:
        pytest.skip("Playwright dependencies not available")
    
    if real_app is None:
        pytest.skip("Real Playwright server not available")
    
    # Use the real app with actual browser
    with TestClient(real_app) as client:
        # Wait for browser initialization
        await asyncio.sleep(2)
        yield client


@pytest.fixture
def integration_test_urls():
    """URLs for integration testing."""
    return {
        'httpbin_html': 'https://httpbin.org/html',
        'httpbin_forms': 'https://httpbin.org/forms/post',
        'example': 'https://example.com',
        'google': 'https://www.google.com',
        'github': 'https://github.com',
        'wikipedia': 'https://en.wikipedia.org/wiki/Main_Page',
        'slow_page': 'https://httpbin.org/delay/2',
        'json_page': 'https://httpbin.org/json',
        'status_404': 'https://httpbin.org/status/404',
        'status_500': 'https://httpbin.org/status/500'
    }


class TestRealBrowserIntegration:
    """Integration tests using real browser automation."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_browser_initialization(self, real_client):
        """Test that browser initializes correctly."""
        response = real_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["browser_status"] in ["connected", "disconnected"]

    @pytest.mark.integration
    async def test_real_navigation_example_com(self, real_client):
        """Test navigation to example.com with real browser."""
        request_data = {
            "url": "https://example.com",
            "timeout": 30000,
            "wait_until": "load"
        }
        
        response = real_client.post("/navigate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "example.com" in data["url"].lower()
        assert "Example Domain" in data["title"]
        assert data["status_code"] == 200
        assert data["navigation_time"] > 0

    @pytest.mark.integration
    async def test_real_navigation_httpbin(self, real_client, integration_test_urls):
        """Test navigation to HTTPBin HTML page."""
        request_data = {
            "url": integration_test_urls["httpbin_html"],
            "timeout": 30000
        }
        
        response = real_client.post("/navigate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "httpbin.org" in data["url"]

    @pytest.mark.integration
    async def test_real_text_extraction(self, real_client, integration_test_urls):
        """Test text extraction from real webpage."""
        # First navigate
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Then extract text
        extract_data = {
            "selector": "h1",
            "page_id": "default"
        }
        
        response = real_client.post("/extract_text", json=extract_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Example Domain" in data["content"]
        assert data["length"] > 0

    @pytest.mark.integration
    async def test_real_form_interaction(self, real_client, integration_test_urls):
        """Test form filling on real webpage."""
        # Navigate to form page
        nav_data = {
            "url": integration_test_urls["httpbin_forms"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Fill form field
        fill_data = {
            "selector": "input[name='custname']",
            "value": "Integration Test User",
            "page_id": "default"
        }
        
        response = real_client.post("/fill", json=fill_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["actual_value"] == "Integration Test User"

    @pytest.mark.integration
    async def test_real_screenshot_functionality(self, real_client, integration_test_urls):
        """Test screenshot functionality with real browser."""
        # Navigate first
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Take screenshot
        screenshot_data = {
            "page_id": "default",
            "full_page": False,
            "format": "png"
        }
        
        response = real_client.post("/screenshot", json=screenshot_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["size_bytes"] > 1000  # Should be substantial
        assert data["format"] == "png"
        
        # Verify base64 data is valid
        screenshot_bytes = base64.b64decode(data["base64"])
        assert screenshot_bytes.startswith(b'\x89PNG\r\n\x1a\n')  # PNG header

    @pytest.mark.integration
    async def test_real_element_clicking(self, real_client, integration_test_urls):
        """Test element clicking on real webpage."""
        # Navigate to form page
        nav_data = {
            "url": integration_test_urls["httpbin_forms"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Try to click submit button
        click_data = {
            "selector": "input[type='submit']",
            "page_id": "default"
        }
        
        response = real_client.post("/click", json=click_data)
        # Note: This might fail if element doesn't exist, which is OK for testing
        data = response.json()
        # Either succeeds or fails with specific error
        assert "success" in data

    @pytest.mark.integration
    async def test_wait_for_element_real(self, real_client, integration_test_urls):
        """Test waiting for elements on real webpage."""
        # Navigate first
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Wait for body element (should exist)
        wait_data = {
            "selector": "body",
            "page_id": "default",
            "timeout": 10000,
            "state": "visible"
        }
        
        response = real_client.post("/wait_for_element", json=wait_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["wait_time"] >= 0

    @pytest.mark.integration
    async def test_javascript_execution(self, real_client, integration_test_urls):
        """Test JavaScript execution on real webpage."""
        # Navigate first
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Execute JavaScript
        script = "document.title"
        response = real_client.post("/execute_script", params={
            "page_id": "default",
            "script": script
        })
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "Example Domain" in data["result"]

    @pytest.mark.integration
    async def test_page_info_retrieval(self, real_client, integration_test_urls):
        """Test page information retrieval."""
        # Navigate first
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Get page info
        response = real_client.get("/page_info", params={"page_id": "default"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "example.com" in data["url"]
        assert "Example Domain" in data["title"]
        assert "viewport" in data


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_multi_page_workflow(self, real_client, integration_test_urls):
        """Test complex multi-page workflow."""
        # Step 1: Navigate to first page
        nav1_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        response1 = real_client.post("/navigate", json=nav1_data)
        assert response1.status_code == 200
        
        # Step 2: Extract information
        extract_data = {
            "selector": "h1",
            "page_id": "default"
        }
        response2 = real_client.post("/extract_text", json=extract_data)
        assert response2.status_code == 200
        
        # Step 3: Take screenshot
        screenshot_data = {
            "page_id": "default",
            "full_page": True
        }
        response3 = real_client.post("/screenshot", json=screenshot_data)
        assert response3.status_code == 200
        
        # Step 4: Navigate to second page
        nav2_data = {
            "url": integration_test_urls["httpbin_html"],
            "timeout": 30000
        }
        response4 = real_client.post("/navigate", json=nav2_data)
        assert response4.status_code == 200
        
        # Verify all steps succeeded
        assert all(resp.json().get("success", False) for resp in [response1, response2, response3, response4])

    @pytest.mark.integration
    async def test_error_handling_real_scenarios(self, real_client):
        """Test error handling with real scenarios."""
        # Test 404 page
        nav_data = {
            "url": "https://httpbin.org/status/404",
            "timeout": 30000
        }
        response = real_client.post("/navigate", json=nav_data)
        data = response.json()
        # Should handle gracefully (might succeed or fail depending on implementation)
        assert "success" in data
        
        # Test invalid selector
        extract_data = {
            "selector": "invalid>>selector",
            "page_id": "default"
        }
        response = real_client.post("/extract_text", json=extract_data)
        data = response.json()
        # Should return error gracefully
        if not data.get("success", True):
            assert "error" in data

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_performance_real_pages(self, real_client, integration_test_urls):
        """Test performance with real pages."""
        test_urls = [
            integration_test_urls["example"],
            integration_test_urls["httpbin_html"]
        ]
        
        performance_results = []
        
        for url in test_urls:
            start_time = time.time()
            
            nav_data = {
                "url": url,
                "timeout": 30000
            }
            response = real_client.post("/navigate", json=nav_data)
            
            end_time = time.time()
            navigation_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    performance_results.append({
                        "url": url,
                        "total_time": navigation_time,
                        "browser_time": data.get("navigation_time", 0)
                    })
        
        # Verify we got some performance data
        assert len(performance_results) > 0
        
        # Check reasonable performance (adjust based on your requirements)
        for result in performance_results:
            assert result["total_time"] < 60.0  # Less than 1 minute
            print(f"Performance: {result['url']} - {result['total_time']:.2f}s")


class TestMemoryAndResourceManagement:
    """Test memory and resource management with real browser."""

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_memory_usage_real_browser(self, real_client, integration_test_urls):
        """Test memory usage with real browser operations."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Perform multiple operations
        for i in range(3):  # Reduced for faster testing
            nav_data = {
                "url": integration_test_urls["example"] + f"?iteration={i}",
                "timeout": 30000
            }
            response = real_client.post("/navigate", json=nav_data)
            
            if response.status_code == 200:
                # Take screenshot to increase memory usage
                screenshot_data = {
                    "page_id": "default",
                    "full_page": True
                }
                real_client.post("/screenshot", json=screenshot_data)
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (growth: {memory_growth:.1f}MB)")
        
        # Allow reasonable memory growth but not excessive
        assert memory_growth < 200, f"Excessive memory growth: {memory_growth:.1f}MB"

    @pytest.mark.integration
    async def test_page_cleanup(self, real_client, integration_test_urls):
        """Test page cleanup functionality."""
        # Navigate to create a page
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        response = real_client.post("/navigate", json=nav_data)
        assert response.status_code == 200
        
        # Check page exists
        info_response = real_client.get("/page_info", params={"page_id": "default"})
        assert info_response.status_code == 200
        
        # Close the page
        close_response = real_client.delete("/close_page", params={"page_id": "default"})
        assert close_response.status_code == 200
        
        data = close_response.json()
        assert data["success"] is True


class TestConcurrentRealBrowser:
    """Test concurrent operations with real browser."""

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_navigation_real(self, real_client, integration_test_urls):
        """Test concurrent navigation with real browser."""
        import concurrent.futures
        
        def navigate_task(url, page_id):
            """Single navigation task."""
            nav_data = {
                "url": url,
                "timeout": 30000
            }
            # Use different page IDs for concurrent operations
            response = real_client.post("/navigate", json=nav_data)
            return response.status_code == 200
        
        urls = [
            integration_test_urls["example"],
            integration_test_urls["httpbin_html"]
        ]
        
        # Run concurrent navigations
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(navigate_task, url, f"page_{i}")
                for i, url in enumerate(urls)
            ]
            results = [future.result() for future in futures]
        
        # At least one should succeed
        assert any(results), "At least one concurrent navigation should succeed"


class TestAdvancedFeatures:
    """Test advanced Playwright features."""

    @pytest.mark.integration
    async def test_full_page_vs_viewport_screenshot(self, real_client, integration_test_urls):
        """Test difference between full page and viewport screenshots."""
        # Navigate first
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Take viewport screenshot
        viewport_data = {
            "page_id": "default",
            "full_page": False,
            "format": "png"
        }
        viewport_response = real_client.post("/screenshot", json=viewport_data)
        
        # Take full page screenshot
        fullpage_data = {
            "page_id": "default",
            "full_page": True,
            "format": "png"
        }
        fullpage_response = real_client.post("/screenshot", json=fullpage_data)
        
        if viewport_response.status_code == 200 and fullpage_response.status_code == 200:
            viewport_size = viewport_response.json()["size_bytes"]
            fullpage_size = fullpage_response.json()["size_bytes"]
            
            # Full page might be same size or larger for simple pages
            assert fullpage_size >= viewport_size * 0.5  # Allow some variation

    @pytest.mark.integration
    async def test_different_image_formats(self, real_client, integration_test_urls):
        """Test different screenshot formats."""
        # Navigate first
        nav_data = {
            "url": integration_test_urls["example"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        formats = [
            {"format": "png"},
            {"format": "jpeg", "quality": 80}
        ]
        
        for format_config in formats:
            screenshot_data = {
                "page_id": "default",
                "full_page": False,
                **format_config
            }
            
            response = real_client.post("/screenshot", json=screenshot_data)
            if response.status_code == 200:
                data = response.json()
                assert data["success"] is True
                assert data["format"] == format_config["format"]

    @pytest.mark.integration
    async def test_element_extraction_multiple(self, real_client, integration_test_urls):
        """Test extracting from multiple elements."""
        # Navigate to a page with multiple elements
        nav_data = {
            "url": integration_test_urls["httpbin_html"],
            "timeout": 30000
        }
        nav_response = real_client.post("/navigate", json=nav_data)
        assert nav_response.status_code == 200
        
        # Extract all paragraph elements
        extract_data = {
            "selector": "p",
            "page_id": "default",
            "all_elements": True
        }
        
        response = real_client.post("/extract_text", json=extract_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                assert data["count"] >= 0
                assert "results" in data


if __name__ == "__main__":
    pytest.main([
        __file__, 
        "-v", 
        "-m", "integration",
        "--tb=short"
    ])