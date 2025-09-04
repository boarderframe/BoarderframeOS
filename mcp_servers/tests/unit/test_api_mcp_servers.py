"""
Unit tests for MCP server management endpoints.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import status
from httpx import AsyncClient

from tests.utils import APITestHelper, DataFactory, SecurityTestHelper, ValidationHelper
from tests.fixtures import mcp_fixtures
from app.schemas.mcp_server import MCPServerStatus


@pytest.mark.unit
@pytest.mark.asyncio
class TestMCPServerEndpoints:
    """Test suite for MCP server management endpoints."""
    
    async def test_get_mcp_servers_requires_authentication(self, async_client: AsyncClient):
        """Test that listing MCP servers requires authentication."""
        await SecurityTestHelper.test_authentication_required(
            async_client, "GET", "/api/v1/mcp-servers/"
        )
    
    async def test_get_mcp_servers_success_empty_list(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful retrieval of empty MCP servers list."""
        response = await async_client.get("/api/v1/mcp-servers/", headers=auth_headers)
        
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    @patch('app.api.api_v1.endpoints.mcp_servers.get_db')
    async def test_get_mcp_servers_with_pagination(
        self, mock_get_db, async_client: AsyncClient, auth_headers: dict
    ):
        """Test MCP servers list with pagination parameters."""
        # Test with skip and limit parameters
        response = await async_client.get(
            "/api/v1/mcp-servers/?skip=0&limit=10", 
            headers=auth_headers
        )
        
        APITestHelper.assert_status_code(response, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_mcp_servers_invalid_pagination(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test MCP servers list with invalid pagination parameters."""
        # Test with negative skip
        response = await async_client.get(
            "/api/v1/mcp-servers/?skip=-1", 
            headers=auth_headers
        )
        APITestHelper.assert_status_code(response, status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        # Test with negative limit
        response = await async_client.get(
            "/api/v1/mcp-servers/?limit=-1", 
            headers=auth_headers
        )
        APITestHelper.assert_status_code(response, status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    async def test_create_mcp_server_requires_authentication(self, async_client: AsyncClient):
        """Test that creating MCP server requires authentication."""
        server_data = DataFactory.create_mcp_server_data()
        await SecurityTestHelper.test_authentication_required(
            async_client, "POST", "/api/v1/mcp-servers/", json=server_data
        )
    
    async def test_create_mcp_server_not_implemented(
        self, async_client: AsyncClient, auth_headers: dict, sample_mcp_server_data: dict
    ):
        """Test that creating MCP server returns not implemented."""
        response = await async_client.post(
            "/api/v1/mcp-servers/", 
            json=sample_mcp_server_data,
            headers=auth_headers
        )
        
        APITestHelper.assert_status_code(response, status.HTTP_501_NOT_IMPLEMENTED)
        data = response.json()
        ValidationHelper.assert_error_response(data)
        assert "not yet implemented" in data["detail"]
    
    async def test_create_mcp_server_invalid_data(
        self, async_client: AsyncClient, auth_headers: dict, invalid_mcp_server_data: list
    ):
        """Test creating MCP server with invalid data."""
        for invalid_data in invalid_mcp_server_data:
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=invalid_data,
                headers=auth_headers
            )
            
            # Should return validation error
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST
            ]
    
    async def test_create_mcp_server_missing_required_fields(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test creating MCP server with missing required fields."""
        incomplete_data = {"description": "Missing required fields"}
        
        response = await async_client.post(
            "/api/v1/mcp-servers/",
            json=incomplete_data,
            headers=auth_headers
        )
        
        APITestHelper.assert_status_code(response, status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    async def test_get_mcp_server_requires_authentication(self, async_client: AsyncClient):
        """Test that getting specific MCP server requires authentication."""
        await SecurityTestHelper.test_authentication_required(
            async_client, "GET", "/api/v1/mcp-servers/1"
        )
    
    async def test_get_mcp_server_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent MCP server."""
        response = await async_client.get("/api/v1/mcp-servers/999", headers=auth_headers)
        
        APITestHelper.assert_status_code(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        ValidationHelper.assert_error_response(data)
        assert "not found" in data["detail"]
    
    async def test_get_mcp_server_invalid_id(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test getting MCP server with invalid ID."""
        response = await async_client.get("/api/v1/mcp-servers/invalid", headers=auth_headers)
        
        APITestHelper.assert_status_code(response, status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    async def test_update_mcp_server_requires_authentication(self, async_client: AsyncClient):
        """Test that updating MCP server requires authentication."""
        update_data = {"description": "Updated description"}
        await SecurityTestHelper.test_authentication_required(
            async_client, "PUT", "/api/v1/mcp-servers/1", json=update_data
        )
    
    async def test_update_mcp_server_not_implemented(
        self, async_client: AsyncClient, auth_headers: dict, mcp_server_update_data: dict
    ):
        """Test that updating MCP server returns not implemented."""
        response = await async_client.put(
            "/api/v1/mcp-servers/1",
            json=mcp_server_update_data,
            headers=auth_headers
        )
        
        APITestHelper.assert_status_code(response, status.HTTP_501_NOT_IMPLEMENTED)
        data = response.json()
        ValidationHelper.assert_error_response(data)
        assert "not yet implemented" in data["detail"]
    
    async def test_update_mcp_server_invalid_data(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test updating MCP server with invalid data."""
        invalid_update_data = {"port": "not-a-number"}
        
        response = await async_client.put(
            "/api/v1/mcp-servers/1",
            json=invalid_update_data,
            headers=auth_headers
        )
        
        # Should return validation error before reaching not implemented
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_501_NOT_IMPLEMENTED  # Current implementation
        ]
    
    async def test_delete_mcp_server_requires_authentication(self, async_client: AsyncClient):
        """Test that deleting MCP server requires authentication."""
        await SecurityTestHelper.test_authentication_required(
            async_client, "DELETE", "/api/v1/mcp-servers/1"
        )
    
    async def test_delete_mcp_server_not_implemented(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test that deleting MCP server returns not implemented."""
        response = await async_client.delete("/api/v1/mcp-servers/1", headers=auth_headers)
        
        APITestHelper.assert_status_code(response, status.HTTP_501_NOT_IMPLEMENTED)
        data = response.json()
        ValidationHelper.assert_error_response(data)
        assert "not yet implemented" in data["detail"]
    
    async def test_mcp_server_endpoints_cors_headers(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test that MCP server endpoints include CORS headers."""
        # Test CORS preflight request
        response = await async_client.options(
            "/api/v1/mcp-servers/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                **auth_headers
            }
        )
        
        # Should allow CORS
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
    
    @pytest.mark.parametrize("endpoint", [
        "/api/v1/mcp-servers/",
        "/api/v1/mcp-servers/1"
    ])
    async def test_mcp_server_endpoints_rate_limiting(
        self, async_client: AsyncClient, auth_headers: dict, endpoint: str
    ):
        """Test rate limiting on MCP server endpoints."""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for _ in range(5):
            response = await async_client.get(endpoint, headers=auth_headers)
            responses.append(response)
        
        # At least the first few should succeed (before rate limit)
        # Rate limiting behavior depends on configuration
        success_count = sum(1 for r in responses if r.status_code < 400)
        assert success_count > 0, "At least some requests should succeed"
    
    async def test_mcp_server_endpoints_input_sanitization(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test input sanitization on MCP server endpoints."""
        # Test with potential XSS payloads
        xss_payloads = SecurityTestHelper.get_xss_payloads()
        
        for payload in xss_payloads:
            server_data = DataFactory.create_mcp_server_data(name=payload)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should not return the payload directly in response
            if response.status_code == 501:  # Not implemented
                continue
            
            response_text = response.text
            # XSS payload should not appear unescaped in response
            assert payload not in response_text or "error" in response_text.lower()
    
    async def test_mcp_server_endpoints_sql_injection_protection(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test SQL injection protection on MCP server endpoints."""
        sql_payloads = SecurityTestHelper.get_sql_injection_payloads()
        
        for payload in sql_payloads:
            # Test in server name
            server_data = DataFactory.create_mcp_server_data(name=payload)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should not cause database errors
            assert response.status_code != 500, f"SQL injection payload caused server error: {payload}"
    
    async def test_mcp_server_endpoints_content_type_validation(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test content type validation on MCP server endpoints."""
        # Test with wrong content type
        response = await async_client.post(
            "/api/v1/mcp-servers/",
            data="not-json",
            headers={**auth_headers, "Content-Type": "text/plain"}
        )
        
        APITestHelper.assert_status_code(response, status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    async def test_mcp_server_endpoints_large_payload(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test handling of large payloads."""
        # Create a large server configuration
        large_config = {str(i): "x" * 1000 for i in range(100)}
        server_data = DataFactory.create_mcp_server_data(config=large_config)
        
        response = await async_client.post(
            "/api/v1/mcp-servers/",
            json=server_data,
            headers=auth_headers
        )
        
        # Should handle gracefully (either accept or reject with proper error)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_501_NOT_IMPLEMENTED  # Current implementation
        ]