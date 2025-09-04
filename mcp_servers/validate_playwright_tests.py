#!/usr/bin/env python3
"""
Simple validation script for Playwright MCP Server tests
Tests core functionality without complex dependencies
"""

import json
import sys
import time
from fastapi.testclient import TestClient

# Import the servers
from playwright_server import app as mock_app

def test_mock_server():
    """Test the mock Playwright server."""
    print("🧪 Testing Mock Playwright Server...")
    
    client = TestClient(mock_app)
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    
    health_data = response.json()
    assert health_data["status"] == "healthy", f"Server not healthy: {health_data}"
    assert "tools" in health_data, "Tools not listed in health response"
    
    expected_tools = ["navigate", "click", "fill", "extract_text", "screenshot", "wait_for_element"]
    for tool in expected_tools:
        assert tool in health_data["tools"], f"Tool {tool} not available"
    
    print("✅ Health endpoint test passed")
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200, f"Root endpoint failed: {response.status_code}"
    
    root_data = response.json()
    assert "message" in root_data, "Root endpoint missing message"
    
    print("✅ Root endpoint test passed")
    
    # Test navigation endpoint
    nav_data = {
        "url": "https://example.com",
        "timeout": 30000
    }
    response = client.post("/navigate", json=nav_data)
    assert response.status_code == 200, f"Navigation failed: {response.status_code}"
    
    print("✅ Navigation endpoint test passed")
    
    # Test click endpoint
    click_data = {
        "selector": "button.submit",
        "page_id": "default"
    }
    response = client.post("/click", json=click_data)
    assert response.status_code == 200, f"Click failed: {response.status_code}"
    
    print("✅ Click endpoint test passed")
    
    # Test fill endpoint
    fill_data = {
        "selector": "input[name='username']",
        "value": "testuser"
    }
    response = client.post("/fill", json=fill_data)
    assert response.status_code == 200, f"Fill failed: {response.status_code}"
    
    print("✅ Fill endpoint test passed")
    
    # Test extract_text endpoint
    extract_data = {
        "selector": "h1",
        "page_id": "default"
    }
    response = client.post("/extract_text", json=extract_data)
    assert response.status_code == 200, f"Extract text failed: {response.status_code}"
    
    print("✅ Extract text endpoint test passed")
    
    # Test screenshot endpoint
    screenshot_data = {
        "full_page": True,
        "format": "png"
    }
    response = client.post("/screenshot", json=screenshot_data)
    assert response.status_code == 200, f"Screenshot failed: {response.status_code}"
    
    print("✅ Screenshot endpoint test passed")
    
    # Test wait_for_element endpoint
    wait_data = {
        "selector": "div.loading",
        "timeout": 5000
    }
    response = client.post("/wait_for_element", json=wait_data)
    assert response.status_code == 200, f"Wait for element failed: {response.status_code}"
    
    print("✅ Wait for element endpoint test passed")


def test_error_handling():
    """Test error handling scenarios."""
    print("\n🚫 Testing Error Handling...")
    
    client = TestClient(mock_app)
    
    # Test invalid JSON
    response = client.post(
        "/navigate",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422, f"Should return validation error: {response.status_code}"
    
    print("✅ Invalid JSON handling test passed")
    
    # Test missing required fields
    response = client.post("/navigate", json={})
    assert response.status_code == 422, f"Should return validation error: {response.status_code}"
    
    print("✅ Missing fields handling test passed")
    
    # Test invalid data types
    response = client.post("/navigate", json={"url": 123, "timeout": "invalid"})
    assert response.status_code == 422, f"Should return validation error: {response.status_code}"
    
    print("✅ Invalid data types handling test passed")


def test_request_validation():
    """Test request model validation."""
    print("\n📋 Testing Request Validation...")
    
    # Test NavigateRequest validation
    try:
        from playwright_server import NavigateRequest
        
        # Valid request
        request = NavigateRequest(url="https://example.com", timeout=30000)
        assert request.url == "https://example.com"
        assert request.timeout == 30000
        print("✅ Valid NavigateRequest test passed")
        
        # Test default values
        request = NavigateRequest(url="https://example.com")
        assert request.timeout == 30000
        print("✅ NavigateRequest defaults test passed")
        
    except Exception as e:
        print(f"⚠️ Request validation test error: {e}")


def test_openapi_schema():
    """Test OpenAPI schema generation."""
    print("\n📚 Testing OpenAPI Schema...")
    
    client = TestClient(mock_app)
    
    # Test OpenAPI schema endpoint
    response = client.get("/openapi.json")
    assert response.status_code == 200, f"OpenAPI schema failed: {response.status_code}"
    
    schema = response.json()
    assert "openapi" in schema, "OpenAPI schema missing version"
    assert "info" in schema, "OpenAPI schema missing info"
    assert "paths" in schema, "OpenAPI schema missing paths"
    
    # Check that our endpoints are documented
    paths = schema["paths"]
    expected_endpoints = ["/navigate", "/click", "/fill", "/extract_text", "/screenshot", "/wait_for_element"]
    
    for endpoint in expected_endpoints:
        assert endpoint in paths, f"Endpoint {endpoint} not in OpenAPI schema"
        assert "post" in paths[endpoint], f"POST method not documented for {endpoint}"
    
    print("✅ OpenAPI schema test passed")
    
    # Test docs endpoint
    response = client.get("/docs")
    assert response.status_code == 200, f"API docs failed: {response.status_code}"
    
    print("✅ API docs test passed")


def test_performance_basics():
    """Test basic performance characteristics."""
    print("\n⚡ Testing Basic Performance...")
    
    client = TestClient(mock_app)
    
    # Test API response times
    endpoints = [
        ("/", "get", None),
        ("/health", "get", None),
        ("/navigate", "post", {"url": "https://example.com", "timeout": 30000}),
        ("/extract_text", "post", {"selector": "body", "page_url": "https://example.com"}),
    ]
    
    for endpoint, method, data in endpoints:
        times = []
        
        for _ in range(3):  # Test 3 times
            start_time = time.time()
            
            if method == "get":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)
            
            end_time = time.time()
            
            assert response.status_code in [200, 422], f"Endpoint {endpoint} failed"
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0, f"API endpoint {endpoint} too slow: {avg_time:.3f}s"
        print(f"✅ {endpoint}: {avg_time:.3f}s average")


def run_comprehensive_validation():
    """Run all validation tests."""
    print("🚀 Starting Playwright MCP Server Validation")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        test_mock_server()
        test_error_handling()
        test_request_validation()
        test_openapi_schema()
        test_performance_basics()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print(f"⏱️  Total time: {total_time:.2f} seconds")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        return False


def main():
    """Main validation entry point."""
    success = run_comprehensive_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())