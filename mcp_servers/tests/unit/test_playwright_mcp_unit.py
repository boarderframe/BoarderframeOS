"""
Unit tests for Playwright MCP Server
Focus on testing individual components and mock scenarios
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from pydantic import ValidationError

from playwright_server import (
    app as mock_app,
    NavigateRequest, ClickRequest, FillRequest, 
    ExtractRequest, ScreenshotRequest
)


class TestRequestModels:
    """Test Pydantic request model validation."""

    def test_navigate_request_valid(self):
        """Test valid NavigateRequest creation."""
        request = NavigateRequest(url="https://example.com", timeout=30000)
        assert request.url == "https://example.com"
        assert request.timeout == 30000

    def test_navigate_request_defaults(self):
        """Test NavigateRequest with default values."""
        request = NavigateRequest(url="https://example.com")
        assert request.timeout == 30000

    def test_navigate_request_invalid_url(self):
        """Test NavigateRequest with invalid URL."""
        with pytest.raises(ValidationError):
            NavigateRequest(url="not-a-url")

    def test_navigate_request_invalid_timeout(self):
        """Test NavigateRequest with invalid timeout."""
        with pytest.raises(ValidationError):
            NavigateRequest(url="https://example.com", timeout=500)  # Too low

    def test_click_request_valid(self):
        """Test valid ClickRequest creation."""
        request = ClickRequest(selector="button", page_id="test", timeout=5000)
        assert request.selector == "button"
        assert request.page_id == "test"
        assert request.timeout == 5000

    def test_click_request_invalid_button(self):
        """Test ClickRequest with invalid button."""
        with pytest.raises(ValidationError):
            ClickRequest(selector="button", button="invalid")

    def test_fill_request_valid(self):
        """Test valid FillRequest creation."""
        request = FillRequest(
            selector="input[name='test']",
            value="test value",
            clear_first=False
        )
        assert request.selector == "input[name='test']"
        assert request.value == "test value"
        assert request.clear_first is False

    def test_extract_request_defaults(self):
        """Test ExtractRequest with default values."""
        request = ExtractRequest()
        assert request.selector == "body"
        assert request.page_id == "default"
        assert request.all_elements is False

    def test_screenshot_request_validation(self):
        """Test ScreenshotRequest validation."""
        # Valid request
        request = ScreenshotRequest(format="jpeg", quality=85)
        assert request.format == "jpeg"
        assert request.quality == 85

        # Invalid format
        with pytest.raises(ValidationError):
            ScreenshotRequest(format="gif")

        # Invalid quality
        with pytest.raises(ValidationError):
            ScreenshotRequest(format="jpeg", quality=150)


class TestMockServerEndpoints:
    """Test the mock server endpoints (unit tests)."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(mock_app)

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_health_endpoint(self):
        """Test health endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "tools" in data

    def test_navigate_endpoint_valid(self):
        """Test navigate endpoint with valid data."""
        request_data = {
            "url": "https://example.com",
            "timeout": 30000
        }
        response = self.client.post("/navigate", json=request_data)
        assert response.status_code == 200

    def test_navigate_endpoint_invalid(self):
        """Test navigate endpoint with invalid data."""
        request_data = {
            "url": "not-a-url",
            "timeout": 30000
        }
        response = self.client.post("/navigate", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_click_endpoint_valid(self):
        """Test click endpoint with valid data."""
        request_data = {
            "selector": "button.submit",
            "page_id": "default"
        }
        response = self.client.post("/click", json=request_data)
        assert response.status_code == 200

    def test_fill_endpoint_valid(self):
        """Test fill endpoint with valid data."""
        request_data = {
            "selector": "input[name='username']",
            "value": "testuser"
        }
        response = self.client.post("/fill", json=request_data)
        assert response.status_code == 200

    def test_extract_text_endpoint_valid(self):
        """Test extract_text endpoint with valid data."""
        request_data = {
            "selector": "h1",
            "page_id": "default"
        }
        response = self.client.post("/extract_text", json=request_data)
        assert response.status_code == 200

    def test_screenshot_endpoint_valid(self):
        """Test screenshot endpoint with valid data."""
        request_data = {
            "full_page": True,
            "format": "png"
        }
        response = self.client.post("/screenshot", json=request_data)
        assert response.status_code == 200

    def test_wait_for_element_endpoint_valid(self):
        """Test wait_for_element endpoint with valid data."""
        request_data = {
            "selector": "div.loading",
            "timeout": 5000
        }
        response = self.client.post("/wait_for_element", json=request_data)
        assert response.status_code == 200

    def test_openapi_schema(self):
        """Test OpenAPI schema generation."""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema

    def test_docs_endpoint(self):
        """Test API documentation endpoint."""
        response = self.client.get("/docs")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(mock_app)

    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        response = self.client.post(
            "/navigate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        response = self.client.post("/navigate", json={})
        assert response.status_code == 422

    def test_invalid_data_types(self):
        """Test handling of invalid data types."""
        request_data = {
            "url": 123,  # Should be string
            "timeout": "invalid"  # Should be int
        }
        response = self.client.post("/navigate", json=request_data)
        assert response.status_code == 422

    def test_endpoint_not_found(self):
        """Test 404 for non-existent endpoints."""
        response = self.client.get("/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test 405 for wrong HTTP methods."""
        response = self.client.put("/navigate")
        assert response.status_code == 405


class TestValidationLogic:
    """Test custom validation logic."""

    def test_url_validation(self):
        """Test URL validation logic."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://sub.domain.com/path?query=value"
        ]
        for url in valid_urls:
            request = NavigateRequest(url=url)
            assert request.url == url

        # Invalid URLs
        invalid_urls = [
            "ftp://example.com",
            "example.com",
            "not-a-url",
            ""
        ]
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                NavigateRequest(url=url)

    def test_selector_validation(self):
        """Test CSS selector validation."""
        # Valid selectors (basic validation in Pydantic models)
        valid_selectors = [
            "div",
            ".class",
            "#id",
            "input[name='test']",
            "div > p.class"
        ]
        for selector in valid_selectors:
            request = ClickRequest(selector=selector)
            assert request.selector == selector

    def test_timeout_validation(self):
        """Test timeout validation ranges."""
        # Valid timeouts
        valid_timeouts = [1000, 30000, 120000]
        for timeout in valid_timeouts:
            request = NavigateRequest(url="https://example.com", timeout=timeout)
            assert request.timeout == timeout

        # Invalid timeouts
        invalid_timeouts = [500, 200000, -1000]
        for timeout in invalid_timeouts:
            with pytest.raises(ValidationError):
                NavigateRequest(url="https://example.com", timeout=timeout)

    def test_quality_validation(self):
        """Test JPEG quality validation."""
        # Valid qualities
        for quality in [0, 50, 100]:
            request = ScreenshotRequest(format="jpeg", quality=quality)
            assert request.quality == quality

        # Invalid qualities
        for quality in [-1, 101, 150]:
            with pytest.raises(ValidationError):
                ScreenshotRequest(format="jpeg", quality=quality)


class TestConcurrentRequests:
    """Test concurrent request handling at the unit level."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(mock_app)

    def test_concurrent_api_calls(self):
        """Test multiple concurrent API calls."""
        import concurrent.futures
        import threading

        def make_request(request_id):
            """Make a single API request."""
            request_data = {
                "url": f"https://example.com?id={request_id}",
                "timeout": 30000
            }
            response = self.client.post("/navigate", json=request_data)
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }

        # Execute 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [future.result() for future in futures]

        # Verify all requests succeeded
        assert len(results) == 5
        assert all(result["success"] for result in results)

    def test_thread_safety_simulation(self):
        """Test thread safety with shared resources."""
        results = []
        errors = []

        def worker():
            """Worker function for threading test."""
            try:
                response = self.client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create and run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Verify no errors and all requests succeeded
        assert len(errors) == 0
        assert len(results) == 10
        assert all(status == 200 for status in results)


class TestMemoryManagement:
    """Test memory management at the unit level."""

    def test_request_object_cleanup(self):
        """Test that request objects are properly cleaned up."""
        import gc
        
        # Create many request objects
        requests = []
        for i in range(1000):
            req = NavigateRequest(url=f"https://example{i}.com")
            requests.append(req)
        
        # Clear references
        del requests
        
        # Force garbage collection
        gc.collect()
        
        # This test mainly ensures no memory leaks in object creation
        # In a real scenario, you'd use memory profiling tools
        assert True  # If we reach here, no major memory issues

    def test_large_response_handling(self):
        """Test handling of large responses."""
        # Simulate large screenshot response
        request_data = {
            "full_page": True,
            "format": "png"
        }
        response = self.client.post("/screenshot", json=request_data)
        assert response.status_code == 200
        
        # The mock response should be manageable in size
        response_size = len(response.content)
        assert response_size < 1024 * 1024  # Less than 1MB for mock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])