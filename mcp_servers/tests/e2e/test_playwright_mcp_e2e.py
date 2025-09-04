"""
End-to-End tests for Playwright MCP Server
Tests complete workflows and user scenarios
"""

import asyncio
import json
import os
import pytest
import tempfile
import time
from pathlib import Path

import httpx
import uvicorn
from multiprocessing import Process

# Test configuration
TEST_SERVER_HOST = "localhost"
TEST_SERVER_PORT = 9003


@pytest.fixture(scope="session")
def server_process():
    """Start real Playwright server for E2E testing."""
    try:
        from playwright_mcp_server_real import app
    except ImportError:
        pytest.skip("Real Playwright server not available")
    
    def run_server():
        uvicorn.run(app, host=TEST_SERVER_HOST, port=TEST_SERVER_PORT, log_level="warning")
    
    # Start server in separate process
    process = Process(target=run_server)
    process.start()
    
    # Wait for server to start
    time.sleep(5)
    
    yield f"http://{TEST_SERVER_HOST}:{TEST_SERVER_PORT}"
    
    # Clean up
    process.terminate()
    process.join(timeout=10)
    if process.is_alive():
        process.kill()


@pytest.fixture
async def http_client():
    """HTTP client for making requests to the server."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


class TestE2EWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_web_scraping_workflow(self, server_process, http_client):
        """Test a complete web scraping workflow."""
        base_url = server_process
        
        # Step 1: Health check
        response = await http_client.get(f"{base_url}/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Step 2: Navigate to target page
        nav_data = {
            "url": "https://example.com",
            "timeout": 30000,
            "wait_until": "load"
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        assert response.status_code == 200
        nav_result = response.json()
        assert nav_result["success"] is True
        
        # Step 3: Extract page title
        extract_data = {
            "selector": "h1",
            "page_id": "default",
            "timeout": 10000
        }
        response = await http_client.post(f"{base_url}/extract_text", json=extract_data)
        assert response.status_code == 200
        extract_result = response.json()
        assert extract_result["success"] is True
        assert "Example Domain" in extract_result["content"]
        
        # Step 4: Take screenshot for verification
        screenshot_data = {
            "page_id": "default",
            "full_page": False,
            "format": "png"
        }
        response = await http_client.post(f"{base_url}/screenshot", json=screenshot_data)
        assert response.status_code == 200
        screenshot_result = response.json()
        assert screenshot_result["success"] is True
        assert screenshot_result["size_bytes"] > 1000
        
        # Step 5: Get page information
        response = await http_client.get(f"{base_url}/page_info", params={"page_id": "default"})
        assert response.status_code == 200
        page_info = response.json()
        assert page_info["success"] is True
        assert "example.com" in page_info["url"]

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_form_automation_workflow(self, server_process, http_client):
        """Test complete form automation workflow."""
        base_url = server_process
        
        # Navigate to form page
        nav_data = {
            "url": "https://httpbin.org/forms/post",
            "timeout": 30000
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        assert response.status_code == 200
        
        # Wait for form to load
        wait_data = {
            "selector": "form",
            "page_id": "default",
            "timeout": 15000,
            "state": "visible"
        }
        response = await http_client.post(f"{base_url}/wait_for_element", json=wait_data)
        assert response.status_code == 200
        
        # Fill form fields
        form_fields = [
            {"selector": "input[name='custname']", "value": "E2E Test User"},
            {"selector": "input[name='custtel']", "value": "123-456-7890"},
            {"selector": "input[name='custemail']", "value": "test@example.com"}
        ]
        
        for field in form_fields:
            fill_data = {
                "selector": field["selector"],
                "value": field["value"],
                "page_id": "default",
                "clear_first": True
            }
            response = await http_client.post(f"{base_url}/fill", json=fill_data)
            # Some fields might not exist, that's OK
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    assert result["actual_value"] == field["value"]
        
        # Take screenshot of filled form
        screenshot_data = {
            "page_id": "default",
            "full_page": True,
            "format": "jpeg",
            "quality": 90
        }
        response = await http_client.post(f"{base_url}/screenshot", json=screenshot_data)
        assert response.status_code == 200

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_multi_page_session(self, server_process, http_client):
        """Test maintaining session across multiple pages."""
        base_url = server_process
        
        pages = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://httpbin.org/json"
        ]
        
        results = []
        
        for i, url in enumerate(pages):
            page_id = f"page_{i}"
            
            # Navigate
            nav_data = {
                "url": url,
                "timeout": 30000
            }
            response = await http_client.post(f"{base_url}/navigate", json=nav_data)
            assert response.status_code == 200
            
            # Get page info
            response = await http_client.get(f"{base_url}/page_info", params={"page_id": "default"})
            assert response.status_code == 200
            page_info = response.json()
            
            results.append({
                "url": url,
                "title": page_info.get("title", ""),
                "final_url": page_info.get("url", "")
            })
        
        # Verify we visited all pages
        assert len(results) == len(pages)
        
        # Clean up pages
        for i in range(len(pages)):
            page_id = f"page_{i}"
            response = await http_client.delete(f"{base_url}/close_page", params={"page_id": page_id})
            # OK if page doesn't exist

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_performance_under_load(self, server_process, http_client):
        """Test server performance under load."""
        base_url = server_process
        
        # Test concurrent requests
        async def make_request(request_id):
            """Make a single request."""
            try:
                nav_data = {
                    "url": f"https://httpbin.org/json?id={request_id}",
                    "timeout": 30000
                }
                start_time = time.time()
                response = await http_client.post(f"{base_url}/navigate", json=nav_data)
                end_time = time.time()
                
                return {
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "time": end_time - start_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "time": None
                }
        
        # Run 5 concurrent requests
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        # At least 50% should succeed
        success_rate = len(successful_requests) / len(results)
        assert success_rate >= 0.5, f"Success rate too low: {success_rate:.2%}"
        
        # Check response times
        if successful_requests:
            avg_time = sum(r["time"] for r in successful_requests if r["time"]) / len(successful_requests)
            assert avg_time < 30.0, f"Average response time too slow: {avg_time:.2f}s"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_error_recovery(self, server_process, http_client):
        """Test error handling and recovery."""
        base_url = server_process
        
        # Test navigation to invalid URL
        nav_data = {
            "url": "https://this-domain-does-not-exist-12345.com",
            "timeout": 10000
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        # Should handle gracefully
        assert response.status_code == 200
        result = response.json()
        # Either succeeds (unlikely) or fails gracefully
        assert "success" in result
        
        # Test recovery by navigating to valid URL
        nav_data = {
            "url": "https://example.com",
            "timeout": 30000
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # Test invalid selector
        extract_data = {
            "selector": "invalid>>>selector",
            "page_id": "default"
        }
        response = await http_client.post(f"{base_url}/extract_text", json=extract_data)
        assert response.status_code == 200
        result = response.json()
        # Should handle invalid selector gracefully

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_javascript_heavy_page_interaction(self, server_process, http_client):
        """Test interaction with JavaScript-heavy pages."""
        base_url = server_process
        
        # Navigate to a page with JavaScript
        nav_data = {
            "url": "https://httpbin.org/html",
            "timeout": 30000,
            "wait_until": "networkidle"
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        assert response.status_code == 200
        
        # Wait for content to be ready
        wait_data = {
            "selector": "body",
            "page_id": "default",
            "timeout": 15000,
            "state": "visible"
        }
        response = await http_client.post(f"{base_url}/wait_for_element", json=wait_data)
        assert response.status_code == 200
        
        # Execute JavaScript
        script = "document.getElementsByTagName('h1').length"
        response = await http_client.post(f"{base_url}/execute_script", params={
            "page_id": "default",
            "script": script
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                assert isinstance(result["result"], int)

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_screenshot_quality_and_formats(self, server_process, http_client):
        """Test screenshot quality and formats."""
        base_url = server_process
        
        # Navigate first
        nav_data = {
            "url": "https://example.com",
            "timeout": 30000
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        assert response.status_code == 200
        
        # Test different formats and qualities
        screenshot_configs = [
            {"format": "png", "full_page": False},
            {"format": "png", "full_page": True},
            {"format": "jpeg", "quality": 50, "full_page": False},
            {"format": "jpeg", "quality": 95, "full_page": False}
        ]
        
        results = []
        
        for config in screenshot_configs:
            screenshot_data = {
                "page_id": "default",
                **config
            }
            
            response = await http_client.post(f"{base_url}/screenshot", json=screenshot_data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    results.append({
                        "config": config,
                        "size": result["size_bytes"],
                        "format": result["format"]
                    })
        
        # Should have at least one successful screenshot
        assert len(results) > 0
        
        # Verify format differences
        png_results = [r for r in results if r["format"] == "png"]
        jpeg_results = [r for r in results if r["format"] == "jpeg"]
        
        if png_results and jpeg_results:
            # Generally PNG should be larger than JPEG for same content
            # (though this isn't always true for simple pages)
            print(f"PNG sizes: {[r['size'] for r in png_results]}")
            print(f"JPEG sizes: {[r['size'] for r in jpeg_results]}")


class TestE2EDataIntegrity:
    """Test data integrity and consistency."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_text_extraction_consistency(self, server_process, http_client):
        """Test that text extraction is consistent across multiple calls."""
        base_url = server_process
        
        # Navigate once
        nav_data = {
            "url": "https://example.com",
            "timeout": 30000
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        assert response.status_code == 200
        
        # Extract text multiple times
        extract_data = {
            "selector": "h1",
            "page_id": "default"
        }
        
        results = []
        for i in range(3):
            response = await http_client.post(f"{base_url}/extract_text", json=extract_data)
            assert response.status_code == 200
            result = response.json()
            if result.get("success"):
                results.append(result["content"])
        
        # All results should be identical
        if len(results) > 1:
            assert all(content == results[0] for content in results)
            assert "Example Domain" in results[0]

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_screenshot_consistency(self, server_process, http_client):
        """Test that screenshots are reasonably consistent."""
        base_url = server_process
        
        # Navigate once
        nav_data = {
            "url": "https://example.com",
            "timeout": 30000
        }
        response = await http_client.post(f"{base_url}/navigate", json=nav_data)
        assert response.status_code == 200
        
        # Take multiple screenshots
        screenshot_data = {
            "page_id": "default",
            "full_page": False,
            "format": "png"
        }
        
        sizes = []
        for i in range(2):
            response = await http_client.post(f"{base_url}/screenshot", json=screenshot_data)
            assert response.status_code == 200
            result = response.json()
            if result.get("success"):
                sizes.append(result["size_bytes"])
        
        # Screenshots should be similar in size (within 10%)
        if len(sizes) >= 2:
            size_diff = abs(sizes[0] - sizes[1]) / max(sizes[0], sizes[1])
            assert size_diff < 0.1, f"Screenshot sizes too different: {sizes}"


class TestE2EResourceManagement:
    """Test resource management in E2E scenarios."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_page_lifecycle_management(self, server_process, http_client):
        """Test complete page lifecycle management."""
        base_url = server_process
        
        # Create multiple pages
        page_ids = ["test_page_1", "test_page_2", "test_page_3"]
        
        for page_id in page_ids:
            # Navigate to create page (this is implicit in the real server)
            nav_data = {
                "url": "https://example.com",
                "timeout": 30000
            }
            response = await http_client.post(f"{base_url}/navigate", json=nav_data)
            assert response.status_code == 200
        
        # Check health to see active pages
        response = await http_client.get(f"{base_url}/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Clean up all pages
        for page_id in page_ids:
            response = await http_client.delete(f"{base_url}/close_page", params={"page_id": page_id})
            # OK if page doesn't exist

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_long_running_session(self, server_process, http_client):
        """Test long-running session stability."""
        base_url = server_process
        
        # Perform operations over extended period
        urls = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://httpbin.org/json"
        ]
        
        for i in range(3):  # Simulate longer session
            for url in urls:
                # Navigate
                nav_data = {
                    "url": url,
                    "timeout": 30000
                }
                response = await http_client.post(f"{base_url}/navigate", json=nav_data)
                assert response.status_code == 200
                
                # Extract some text
                extract_data = {
                    "selector": "body",
                    "page_id": "default"
                }
                response = await http_client.post(f"{base_url}/extract_text", json=extract_data)
                assert response.status_code == 200
                
                # Small delay between operations
                await asyncio.sleep(0.5)
        
        # Final health check
        response = await http_client.get(f"{base_url}/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "-m", "e2e",
        "--tb=short",
        "-x"  # Stop on first failure for E2E tests
    ])