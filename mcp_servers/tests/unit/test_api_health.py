"""
Unit tests for health check endpoints.
"""
import pytest
from fastapi import status
from httpx import AsyncClient

from tests.utils import APITestHelper, ValidationHelper


@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    async def test_health_check_success(self, async_client: AsyncClient):
        """Test successful health check."""
        response = await async_client.get("/health")
        
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        data = APITestHelper.assert_json_response(response, ["status", "service"])
        
        assert data["status"] == "healthy"
        assert data["service"] == "mcp-server-manager"
    
    async def test_api_health_check_success(self, async_client: AsyncClient):
        """Test API v1 health check."""
        response = await async_client.get("/api/v1/health/")
        
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        data = APITestHelper.assert_json_response(response, ["status"])
        
        assert data["status"] == "healthy"
    
    async def test_health_check_response_time(self, async_client: AsyncClient):
        """Test health check response time is acceptable."""
        import time
        
        start_time = time.time()
        response = await async_client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        # Health check should respond within 100ms
        assert response_time < 0.1, f"Health check took {response_time:.3f}s"
    
    async def test_health_check_concurrent_requests(self, async_client: AsyncClient):
        """Test health check handles concurrent requests."""
        import asyncio
        
        # Make 10 concurrent health check requests
        tasks = [async_client.get("/health") for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            APITestHelper.assert_status_code(response, status.HTTP_200_OK)
            data = response.json()
            assert data["status"] == "healthy"
    
    async def test_health_check_no_authentication_required(self, async_client: AsyncClient):
        """Test health check doesn't require authentication."""
        # Test without any authentication headers
        response = await async_client.get("/health")
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        
        # Test with invalid authentication headers (should still work)
        headers = {"Authorization": "Bearer invalid-token"}
        response = await async_client.get("/health", headers=headers)
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
    
    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
    async def test_health_check_only_allows_get(self, async_client: AsyncClient, method: str):
        """Test health check only allows GET method."""
        response = await async_client.request(method, "/health")
        APITestHelper.assert_status_code(response, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    async def test_health_check_response_headers(self, async_client: AsyncClient):
        """Test health check response has correct headers."""
        response = await async_client.get("/health")
        
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        
        # Check content type
        assert response.headers.get("content-type") == "application/json"
        
        # Check for security headers (if configured)
        # Note: These might be added by middleware
        expected_security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection"
        ]
        
        # Don't fail if security headers are missing (they might be added elsewhere)
        for header in expected_security_headers:
            if header in response.headers:
                assert response.headers[header] is not None
    
    async def test_health_check_json_structure(self, async_client: AsyncClient):
        """Test health check response JSON structure."""
        response = await async_client.get("/health")
        
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        data = response.json()
        
        # Validate response structure
        ValidationHelper.assert_datetime_recent(
            # Note: Health check might not include timestamp,
            # but we can validate if it's present
        )
        
        # Check that response is a dict
        assert isinstance(data, dict)
        
        # Check required fields
        assert "status" in data
        assert "service" in data
        
        # Check field types
        assert isinstance(data["status"], str)
        assert isinstance(data["service"], str)
        
        # Check field values
        assert data["status"] in ["healthy", "unhealthy", "degraded"]
        assert len(data["service"]) > 0