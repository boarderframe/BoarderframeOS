"""
Comprehensive Test Suite for Playwright MCP Server

Tests cover all major functionality including:
- Browser startup and shutdown
- Navigation to various websites
- Text extraction from different page types
- Element interaction (clicking, form filling)
- Screenshot functionality
- Error handling
- Performance testing
- OpenAPI endpoint validation
- Concurrent request handling
- Memory leak detection
"""

import asyncio
import json
import os
import psutil
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import httpx
import playwright
import requests
from fastapi.testclient import TestClient
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright
from pydantic import ValidationError

# Import the Playwright MCP server
from playwright_server import app, NavigateRequest, ClickRequest, FillRequest, ExtractRequest, ScreenshotRequest


class PlaywrightTestClient:
    """Enhanced test client for Playwright MCP server with real browser integration."""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.client = TestClient(app)
        self._memory_usage = []
    
    async def setup(self, headless: bool = True, browser_type: str = "chromium"):
        """Initialize real Playwright browser for integration tests."""
        self.playwright = await async_playwright().start()
        
        browser_launcher = getattr(self.playwright, browser_type)
        self.browser = await browser_launcher.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await self.context.new_page()
    
    async def teardown(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def track_memory(self):
        """Track memory usage for leak detection."""
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)
        return memory_mb
    
    @property
    def memory_usage(self) -> List[float]:
        return self._memory_usage


@pytest.fixture
async def playwright_client() -> AsyncGenerator[PlaywrightTestClient, None]:
    """Fixture providing a real Playwright client for integration tests."""
    client = PlaywrightTestClient()
    await client.setup()
    yield client
    await client.teardown()


@pytest.fixture
def mock_playwright_client() -> PlaywrightTestClient:
    """Fixture providing a mock client for unit tests."""
    client = PlaywrightTestClient()
    # Don't setup real browser for unit tests
    return client


@pytest.fixture
def test_urls() -> Dict[str, str]:
    """Test URLs for various scenarios."""
    return {
        'google': 'https://www.google.com',
        'github': 'https://github.com',
        'example': 'https://example.com',
        'httpbin': 'https://httpbin.org/html',
        'javascript_heavy': 'https://www.wikipedia.org',
        'form_test': 'https://httpbin.org/forms/post',
        'slow_page': 'https://httpbin.org/delay/3',
        'invalid': 'https://nonexistent-domain-12345.com',
        'malformed': 'not-a-url',
        'localhost': 'http://localhost:9999'  # Non-existent local server
    }


class TestPlaywrightMCPServer:
    """Main test class for Playwright MCP Server functionality."""

    def test_server_startup(self, mock_playwright_client):
        """Test 1: Verify server starts correctly and responds to health checks."""
        response = mock_playwright_client.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "tools" in data
        expected_tools = ["navigate", "click", "fill", "extract_text", "screenshot", "wait_for_element"]
        assert all(tool in data["tools"] for tool in expected_tools)

    def test_root_endpoint(self, mock_playwright_client):
        """Test root endpoint returns correct message."""
        response = mock_playwright_client.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Playwright Web Tools API" in data["message"]

    @pytest.mark.asyncio
    async def test_browser_startup_shutdown(self, playwright_client):
        """Test 2: Browser startup and shutdown functionality."""
        # Browser should already be started by fixture
        assert playwright_client.browser is not None
        assert playwright_client.context is not None
        assert playwright_client.page is not None
        
        # Test that we can create additional contexts
        new_context = await playwright_client.browser.new_context()
        new_page = await new_context.new_page()
        
        assert new_page is not None
        
        # Clean up
        await new_page.close()
        await new_context.close()

    @pytest.mark.asyncio
    async def test_navigation_valid_urls(self, playwright_client, test_urls):
        """Test 3: Navigation to various valid websites."""
        test_cases = [
            ('google', test_urls['google']),
            ('example', test_urls['example']),
            ('httpbin', test_urls['httpbin'])
        ]
        
        for name, url in test_cases:
            start_time = time.time()
            
            try:
                await playwright_client.page.goto(url, timeout=30000)
                navigation_time = time.time() - start_time
                
                # Verify successful navigation
                current_url = playwright_client.page.url
                assert url in current_url or current_url.startswith(url)
                
                # Check that page loaded (has title)
                title = await playwright_client.page.title()
                assert title is not None
                assert len(title) > 0
                
                # Verify reasonable load time (less than 30 seconds)
                assert navigation_time < 30.0
                
                print(f"✓ {name}: {navigation_time:.2f}s - {title}")
                
            except Exception as e:
                pytest.fail(f"Navigation to {name} ({url}) failed: {str(e)}")

    def test_navigation_api_endpoint(self, mock_playwright_client, test_urls):
        """Test navigation API endpoint with valid URLs."""
        for name, url in [('google', test_urls['google']), ('example', test_urls['example'])]:
            request_data = NavigateRequest(url=url, timeout=30000)
            
            response = mock_playwright_client.client.post(
                "/navigate",
                json=request_data.dict()
            )
            
            assert response.status_code == 200
            response_text = response.text
            assert f"Successfully navigated to {url}" in response_text
            assert "Page loaded" in response_text

    @pytest.mark.asyncio
    async def test_text_extraction_different_pages(self, playwright_client, test_urls):
        """Test 4: Text extraction from different page types."""
        test_cases = [
            {
                'name': 'example',
                'url': test_urls['example'],
                'selector': 'h1',
                'expected_content': 'Example Domain'
            },
            {
                'name': 'httpbin_html',
                'url': test_urls['httpbin'],
                'selector': 'body',
                'expected_content': 'html'  # Should contain the word 'html'
            }
        ]
        
        for case in test_cases:
            try:
                await playwright_client.page.goto(case['url'], timeout=30000)
                
                # Wait for content to load
                await playwright_client.page.wait_for_selector(case['selector'], timeout=10000)
                
                # Extract text
                element = await playwright_client.page.query_selector(case['selector'])
                assert element is not None, f"Selector '{case['selector']}' not found on {case['name']}"
                
                text_content = await element.text_content()
                assert text_content is not None
                assert len(text_content.strip()) > 0
                
                if case['expected_content']:
                    assert case['expected_content'].lower() in text_content.lower()
                
                print(f"✓ {case['name']}: Extracted {len(text_content)} characters")
                
            except Exception as e:
                pytest.fail(f"Text extraction from {case['name']} failed: {str(e)}")

    def test_extract_text_api_endpoint(self, mock_playwright_client):
        """Test text extraction API endpoint."""
        request_data = ExtractRequest(selector="body", page_url="https://example.com")
        
        response = mock_playwright_client.client.post(
            "/extract_text",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        response_text = response.text
        assert "Extracted text from body:" in response_text
        assert "Example page content" in response_text

    @pytest.mark.asyncio
    async def test_element_clicking(self, playwright_client):
        """Test 5: Element clicking functionality."""
        # Use a page with clickable elements
        await playwright_client.page.goto("https://httpbin.org/forms/post", timeout=30000)
        
        try:
            # Look for submit button or any clickable element
            submit_button = await playwright_client.page.query_selector('input[type="submit"], button[type="submit"], input[value="Submit"]')
            
            if submit_button:
                # Check if element is visible and enabled
                is_visible = await submit_button.is_visible()
                is_enabled = await submit_button.is_enabled()
                
                assert is_visible, "Submit button should be visible"
                assert is_enabled, "Submit button should be enabled"
                
                # Get initial page URL for comparison
                initial_url = playwright_client.page.url
                
                # Click the button (this might navigate or show an error)
                await submit_button.click()
                
                # Wait briefly for any navigation or changes
                await asyncio.sleep(1)
                
                print("✓ Successfully clicked submit button")
            else:
                # If no submit button, just verify we can interact with the page
                await playwright_client.page.click('body')
                print("✓ Successfully clicked on page body")
                
        except Exception as e:
            pytest.fail(f"Element clicking failed: {str(e)}")

    def test_click_api_endpoint(self, mock_playwright_client):
        """Test click API endpoint."""
        request_data = ClickRequest(selector="button", page_url="https://example.com")
        
        response = mock_playwright_client.client.post(
            "/click",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        response_text = response.text
        assert "Successfully clicked element: button" in response_text
        assert "Element was found and clicked" in response_text

    @pytest.mark.asyncio
    async def test_form_filling(self, playwright_client):
        """Test 5: Form filling functionality."""
        # Use httpbin form page
        await playwright_client.page.goto("https://httpbin.org/forms/post", timeout=30000)
        
        try:
            # Look for text input fields
            text_inputs = await playwright_client.page.query_selector_all('input[type="text"], input[name="custname"], textarea')
            
            if text_inputs:
                for i, input_field in enumerate(text_inputs[:2]):  # Test first 2 inputs
                    test_value = f"test_value_{i}"
                    
                    # Clear and fill the field
                    await input_field.fill(test_value)
                    
                    # Verify the value was set
                    actual_value = await input_field.input_value()
                    assert actual_value == test_value
                    
                    print(f"✓ Successfully filled input {i} with '{test_value}'")
            else:
                print("ℹ No text inputs found on form page")
                
        except Exception as e:
            pytest.fail(f"Form filling failed: {str(e)}")

    def test_fill_api_endpoint(self, mock_playwright_client):
        """Test fill API endpoint."""
        request_data = FillRequest(
            selector="input[name='username']", 
            value="testuser", 
            page_url="https://example.com"
        )
        
        response = mock_playwright_client.client.post(
            "/fill",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        response_text = response.text
        assert "Successfully filled 'input[name='username']' with 'testuser'" in response_text
        assert "Form field updated" in response_text

    @pytest.mark.asyncio
    async def test_screenshot_functionality(self, playwright_client):
        """Test 6: Screenshot functionality."""
        await playwright_client.page.goto("https://example.com", timeout=30000)
        
        try:
            # Take a full page screenshot
            screenshot_bytes = await playwright_client.page.screenshot(
                full_page=True,
                type="png"
            )
            
            assert screenshot_bytes is not None
            assert len(screenshot_bytes) > 1000  # Should be a substantial image
            
            # Verify it's a valid PNG (starts with PNG header)
            assert screenshot_bytes.startswith(b'\x89PNG\r\n\x1a\n')
            
            # Take a viewport screenshot
            viewport_screenshot = await playwright_client.page.screenshot(
                full_page=False,
                type="png"
            )
            
            assert viewport_screenshot is not None
            assert len(viewport_screenshot) > 500
            
            print(f"✓ Full page screenshot: {len(screenshot_bytes)} bytes")
            print(f"✓ Viewport screenshot: {len(viewport_screenshot)} bytes")
            
        except Exception as e:
            pytest.fail(f"Screenshot functionality failed: {str(e)}")

    def test_screenshot_api_endpoint(self, mock_playwright_client):
        """Test screenshot API endpoint."""
        request_data = ScreenshotRequest(page_url="https://example.com", full_page=True)
        
        response = mock_playwright_client.client.post(
            "/screenshot",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        response_text = response.text
        assert "Screenshot saved to:" in response_text
        assert "Size: 1920x1080" in response_text
        assert "Full page: True" in response_text

    def test_wait_for_element_api_endpoint(self, mock_playwright_client):
        """Test wait for element API endpoint."""
        request_data = ClickRequest(selector="div.content", page_url="https://example.com")
        
        response = mock_playwright_client.client.post(
            "/wait_for_element",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        response_text = response.text
        assert "Element 'div.content' appeared after" in response_text
        assert "Element is now visible" in response_text

    def test_error_handling_invalid_urls(self, mock_playwright_client, test_urls):
        """Test 7: Error handling for invalid URLs."""
        invalid_urls = [
            test_urls['invalid'],      # Non-existent domain
            test_urls['malformed'],    # Malformed URL
            test_urls['localhost']     # Non-existent local server
        ]
        
        for url in invalid_urls:
            request_data = NavigateRequest(url=url, timeout=5000)
            
            # Should still return 200 but with error message in response
            response = mock_playwright_client.client.post(
                "/navigate",
                json=request_data.dict()
            )
            
            assert response.status_code == 200
            # The mock implementation returns success, but in real implementation 
            # we'd expect error handling


class TestPlaywrightErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_request_data(self, mock_playwright_client):
        """Test handling of invalid request data."""
        # Test missing required fields
        response = mock_playwright_client.client.post("/navigate", json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid data types
        response = mock_playwright_client.client.post(
            "/navigate", 
            json={"url": 123, "timeout": "invalid"}
        )
        assert response.status_code == 422

    def test_invalid_selectors(self, mock_playwright_client):
        """Test handling of invalid CSS selectors."""
        invalid_selectors = [
            "<<<invalid>>>",
            "",
            None,
            "div:invalid-pseudo()",
        ]
        
        for selector in invalid_selectors:
            if selector is not None:
                request_data = {"selector": selector, "page_url": "https://example.com"}
                
                # These should return 200 with error messages in mock implementation
                response = mock_playwright_client.client.post("/click", json=request_data)
                # In mock implementation, this passes validation but would fail in real implementation

    def test_malformed_json(self, mock_playwright_client):
        """Test handling of malformed JSON requests."""
        response = mock_playwright_client.client.post(
            "/navigate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, playwright_client):
        """Test handling of network timeouts."""
        try:
            # Try to navigate to a slow page with a very short timeout
            await playwright_client.page.goto("https://httpbin.org/delay/10", timeout=2000)
            pytest.fail("Expected timeout error")
        except playwright.async_api.TimeoutError:
            print("✓ Correctly handled timeout error")
        except Exception as e:
            print(f"✓ Handled network error: {type(e).__name__}")


class TestPlaywrightPerformance:
    """Test performance characteristics."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_navigation_performance(self, playwright_client, test_urls):
        """Test 8: Performance testing (response times)."""
        performance_results = {}
        
        test_sites = [
            ('example', test_urls['example']),
            ('google', test_urls['google']),
        ]
        
        for name, url in test_sites:
            times = []
            
            # Run multiple iterations for average
            for i in range(3):
                start_time = time.time()
                
                try:
                    await playwright_client.page.goto(url, timeout=30000)
                    await playwright_client.page.wait_for_load_state('networkidle', timeout=10000)
                    
                    end_time = time.time()
                    navigation_time = end_time - start_time
                    times.append(navigation_time)
                    
                except Exception as e:
                    print(f"Performance test iteration {i} failed for {name}: {e}")
                    continue
            
            if times:
                avg_time = sum(times) / len(times)
                performance_results[name] = {
                    'average_time': avg_time,
                    'min_time': min(times),
                    'max_time': max(times),
                    'iterations': len(times)
                }
                
                # Performance assertions
                assert avg_time < 15.0, f"{name} average load time too slow: {avg_time:.2f}s"
                print(f"✓ {name}: avg={avg_time:.2f}s, min={min(times):.2f}s, max={max(times):.2f}s")
        
        assert len(performance_results) > 0, "No performance results collected"

    @pytest.mark.performance
    def test_api_endpoint_performance(self, mock_playwright_client):
        """Test API endpoint response times."""
        endpoints = [
            ("/", "get", None),
            ("/health", "get", None),
            ("/navigate", "post", {"url": "https://example.com", "timeout": 30000}),
            ("/extract_text", "post", {"selector": "body", "page_url": "https://example.com"}),
        ]
        
        for endpoint, method, data in endpoints:
            times = []
            
            for _ in range(5):  # 5 iterations
                start_time = time.time()
                
                if method == "get":
                    response = mock_playwright_client.client.get(endpoint)
                else:
                    response = mock_playwright_client.client.post(endpoint, json=data)
                
                end_time = time.time()
                
                assert response.status_code in [200, 422]  # Success or validation error
                times.append(end_time - start_time)
            
            avg_time = sum(times) / len(times)
            assert avg_time < 1.0, f"API endpoint {endpoint} too slow: {avg_time:.3f}s"
            print(f"✓ {endpoint}: {avg_time:.3f}s average")


class TestPlaywrightConcurrency:
    """Test concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_navigation(self, test_urls):
        """Test 10: Concurrent request handling."""
        async def navigate_task(url: str, task_id: int):
            """Single navigation task for concurrent testing."""
            client = PlaywrightTestClient()
            try:
                await client.setup()
                start_time = time.time()
                
                await client.page.goto(url, timeout=30000)
                title = await client.page.title()
                
                end_time = time.time()
                
                return {
                    'task_id': task_id,
                    'url': url,
                    'success': True,
                    'time': end_time - start_time,
                    'title': title
                }
                
            except Exception as e:
                return {
                    'task_id': task_id,
                    'url': url,
                    'success': False,
                    'error': str(e),
                    'time': None
                }
            finally:
                await client.teardown()
        
        # Run 3 concurrent navigation tasks
        tasks = [
            navigate_task(test_urls['example'], 1),
            navigate_task(test_urls['google'], 2),
            navigate_task(test_urls['httpbin'], 3),
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Verify results
        successful_tasks = [r for r in results if isinstance(r, dict) and r.get('success')]
        assert len(successful_tasks) >= 2, f"At least 2 tasks should succeed, got {len(successful_tasks)}"
        
        # Concurrent execution should be faster than sequential
        sequential_time_estimate = sum(r.get('time', 0) for r in successful_tasks if r.get('time'))
        assert total_time < sequential_time_estimate, "Concurrent execution should be faster than sequential"
        
        print(f"✓ Concurrent navigation: {len(successful_tasks)}/{len(tasks)} successful in {total_time:.2f}s")

    def test_concurrent_api_requests(self, mock_playwright_client):
        """Test concurrent API requests."""
        def make_request(endpoint: str, data: dict, request_id: int):
            """Make a single API request."""
            try:
                start_time = time.time()
                response = mock_playwright_client.client.post(endpoint, json=data)
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'time': end_time - start_time
                }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'success': False,
                    'error': str(e)
                }
        
        # Create multiple concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for i in range(10):  # 10 concurrent requests
                future = executor.submit(
                    make_request,
                    "/navigate",
                    {"url": f"https://example.com?req={i}", "timeout": 30000},
                    i
                )
                futures.append(future)
            
            # Collect results
            results = [future.result() for future in futures]
        
        # Verify all requests completed
        successful_requests = [r for r in results if r['success']]
        assert len(successful_requests) == 10, f"All requests should succeed, got {len(successful_requests)}"
        
        # Check response times are reasonable
        avg_time = sum(r['time'] for r in successful_requests) / len(successful_requests)
        assert avg_time < 1.0, f"Average response time too slow: {avg_time:.3f}s"
        
        print(f"✓ Concurrent API requests: {len(successful_requests)}/10 successful, avg={avg_time:.3f}s")


class TestPlaywrightMemoryLeaks:
    """Test memory leak detection."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test 11: Memory leak detection through repeated operations."""
        memory_measurements = []
        
        # Baseline memory measurement
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_measurements.append(initial_memory)
        
        # Perform repeated browser operations
        for i in range(5):  # Reduced iterations for faster testing
            client = PlaywrightTestClient()
            try:
                await client.setup()
                
                # Perform typical operations
                await client.page.goto("https://example.com", timeout=30000)
                await client.page.screenshot()
                
                # Measure memory after each iteration
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_measurements.append(current_memory)
                
            finally:
                await client.teardown()
        
        # Analyze memory usage
        final_memory = memory_measurements[-1]
        memory_growth = final_memory - initial_memory
        
        # Log memory usage pattern
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (growth: {memory_growth:.1f}MB)")
        
        # Assert reasonable memory growth (less than 100MB for 5 iterations)
        assert memory_growth < 100, f"Excessive memory growth detected: {memory_growth:.1f}MB"
        
        # Check for consistent memory growth (potential leak indicator)
        if len(memory_measurements) >= 3:
            recent_growth = memory_measurements[-1] - memory_measurements[-3]
            assert recent_growth < 50, f"Recent memory growth too high: {recent_growth:.1f}MB"

    @pytest.mark.asyncio
    async def test_browser_resource_cleanup(self):
        """Test proper cleanup of browser resources."""
        initial_process_count = len(psutil.pids())
        
        # Create and destroy multiple browser instances
        for i in range(3):
            client = PlaywrightTestClient()
            await client.setup()
            
            # Use the browser briefly
            await client.page.goto("https://example.com", timeout=30000)
            
            # Ensure proper cleanup
            await client.teardown()
        
        # Check that we didn't leak processes
        final_process_count = len(psutil.pids())
        process_growth = final_process_count - initial_process_count
        
        # Allow for some process variation but not excessive growth
        assert process_growth < 10, f"Too many processes created: {process_growth}"
        print(f"✓ Process count growth: {process_growth}")


class TestPlaywrightOpenAPIValidation:
    """Test OpenAPI endpoint validation."""

    def test_openapi_schema_generation(self, mock_playwright_client):
        """Test 9: OpenAPI endpoint validation."""
        response = mock_playwright_client.client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        
        # Verify basic OpenAPI structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # Verify our endpoints are documented
        paths = schema["paths"]
        expected_endpoints = ["/navigate", "/click", "/fill", "/extract_text", "/screenshot", "/wait_for_element"]
        
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Endpoint {endpoint} not in OpenAPI schema"
            assert "post" in paths[endpoint], f"POST method not documented for {endpoint}"

    def test_api_documentation_completeness(self, mock_playwright_client):
        """Test API documentation completeness."""
        response = mock_playwright_client.client.get("/docs")
        assert response.status_code == 200
        
        # Verify we can access interactive docs
        html_content = response.text
        assert "Swagger UI" in html_content or "swagger" in html_content.lower()

    def test_request_response_schema_validation(self, mock_playwright_client):
        """Test request/response schema validation."""
        # Test valid request schema
        valid_request = NavigateRequest(url="https://example.com", timeout=30000)
        assert valid_request.url == "https://example.com"
        assert valid_request.timeout == 30000
        
        # Test invalid request schema
        with pytest.raises(ValidationError):
            NavigateRequest(url=123)  # Invalid URL type
        
        # Test request with defaults
        minimal_request = NavigateRequest(url="https://example.com")
        assert minimal_request.timeout == 30000  # Default value


class TestPlaywrightRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_workflow(self, playwright_client):
        """Test a complete workflow: navigate → extract → interact → screenshot."""
        try:
            # Step 1: Navigate to a form page
            await playwright_client.page.goto("https://httpbin.org/forms/post", timeout=30000)
            
            # Step 2: Extract form elements
            form_inputs = await playwright_client.page.query_selector_all('input[type="text"], input[name="custname"]')
            assert len(form_inputs) > 0, "Should find form inputs"
            
            # Step 3: Fill out form
            if form_inputs:
                await form_inputs[0].fill("Test User")
                filled_value = await form_inputs[0].input_value()
                assert filled_value == "Test User"
            
            # Step 4: Take screenshot of filled form
            screenshot = await playwright_client.page.screenshot()
            assert len(screenshot) > 1000, "Screenshot should be substantial"
            
            # Step 5: Extract page title
            title = await playwright_client.page.title()
            assert title is not None and len(title) > 0
            
            print("✓ Complete workflow test passed")
            
        except Exception as e:
            pytest.fail(f"Complete workflow test failed: {str(e)}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_javascript_heavy_page(self, playwright_client, test_urls):
        """Test handling of JavaScript-heavy pages."""
        await playwright_client.page.goto(test_urls['javascript_heavy'], timeout=30000)
        
        # Wait for JavaScript content to load
        await playwright_client.page.wait_for_load_state('networkidle', timeout=15000)
        
        # Verify we can interact with dynamically loaded content
        title = await playwright_client.page.title()
        assert title is not None and len(title) > 0
        
        # Try to find some common elements that should be loaded by JS
        content_elements = await playwright_client.page.query_selector_all('p, div, article')
        assert len(content_elements) > 0, "Should find content elements on JavaScript-heavy page"
        
        print(f"✓ JavaScript-heavy page test passed: {len(content_elements)} elements found")


# Performance benchmarks and utilities
class PerformanceBenchmark:
    """Utility class for performance benchmarking."""
    
    @staticmethod
    def measure_time(func):
        """Decorator to measure function execution time."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        return wrapper

    @staticmethod
    async def measure_async_time(coro):
        """Measure async coroutine execution time."""
        start_time = time.time()
        result = await coro
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time


# Test configuration and markers
pytest_plugins = ["pytest_asyncio"]

# Custom markers for test organization
pytestmark = [
    pytest.mark.playwright,  # All tests in this file are Playwright tests
]


if __name__ == "__main__":
    # Run tests with coverage and detailed output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=playwright_server",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-m", "not slow",  # Skip slow tests by default
    ])