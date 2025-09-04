"""
Test utility functions and helpers.
"""
import json
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, AsyncMock

from fastapi import status
from httpx import AsyncClient, Response
from sqlalchemy.orm import Session

# from app.schemas.mcp_server import MCPServerCreate, MCPServerStatus


class APITestHelper:
    """Helper class for API testing."""
    
    @staticmethod
    def assert_status_code(response: Response, expected_status: int) -> None:
        """Assert response status code with detailed error message."""
        if response.status_code != expected_status:
            try:
                error_detail = response.json()
            except json.JSONDecodeError:
                error_detail = response.text
            
            raise AssertionError(
                f"Expected status {expected_status}, got {response.status_code}. "
                f"Response: {error_detail}"
            )
    
    @staticmethod
    def assert_json_response(response: Response, expected_keys: List[str]) -> Dict[str, Any]:
        """Assert response is valid JSON and contains expected keys."""
        assert response.headers.get("content-type") == "application/json"
        data = response.json()
        
        for key in expected_keys:
            assert key in data, f"Missing key '{key}' in response: {data}"
        
        return data
    
    @staticmethod
    async def create_test_server(
        client: AsyncClient, 
        server_data: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Create a test MCP server via API."""
        response = await client.post("/api/v1/mcp-servers/", json=server_data, headers=headers)
        APITestHelper.assert_status_code(response, status.HTTP_201_CREATED)
        return response.json()
    
    @staticmethod
    async def delete_test_server(
        client: AsyncClient, 
        server_id: int, 
        headers: Dict[str, str]
    ) -> None:
        """Delete a test MCP server via API."""
        response = await client.delete(f"/api/v1/mcp-servers/{server_id}", headers=headers)
        APITestHelper.assert_status_code(response, status.HTTP_204_NO_CONTENT)


class DataFactory:
    """Factory for generating test data."""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random string of specified length."""
        return ''.join(random.choices(string.ascii_lowercase, k=length))
    
    @staticmethod
    def random_port() -> int:
        """Generate a random valid port number."""
        return random.randint(1024, 65535)
    
    @staticmethod
    def random_email() -> str:
        """Generate a random email address."""
        username = DataFactory.random_string(8)
        domain = DataFactory.random_string(6)
        return f"{username}@{domain}.com"
    
    @staticmethod
    def create_mcp_server_data(**overrides) -> Dict[str, Any]:
        """Create MCP server test data with optional overrides."""
        default_data = {
            "name": f"test-server-{DataFactory.random_string(6)}",
            "description": f"Test server {DataFactory.random_string(10)}",
            "host": "localhost",
            "port": DataFactory.random_port(),
            "protocol": "stdio",
            "command": "/usr/bin/python",
            "args": ["-m", "test_server"],
            "env": {"TEST_VAR": DataFactory.random_string(8)},
            "config": {"timeout": 30, "retries": 3}
        }
        default_data.update(overrides)
        return default_data
    
    @staticmethod
    def create_user_data(**overrides) -> Dict[str, Any]:
        """Create user test data with optional overrides."""
        default_data = {
            "email": DataFactory.random_email(),
            "username": DataFactory.random_string(8),
            "password": "TestPassword123!",
            "is_active": True,
            "is_superuser": False,
        }
        default_data.update(overrides)
        return default_data
    
    @staticmethod
    def create_multiple_servers(count: int, **common_overrides) -> List[Dict[str, Any]]:
        """Create multiple MCP server data entries."""
        servers = []
        for i in range(count):
            server_data = DataFactory.create_mcp_server_data(
                name=f"server-{i}-{DataFactory.random_string(4)}",
                port=DataFactory.random_port(),
                **common_overrides
            )
            servers.append(server_data)
        return servers


class MockFactory:
    """Factory for creating mock objects."""
    
    @staticmethod
    def create_mock_redis():
        """Create a mock Redis client."""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=False)
        mock_redis.expire = AsyncMock(return_value=True)
        return mock_redis
    
    @staticmethod
    def create_mock_mcp_client():
        """Create a mock MCP client."""
        mock_client = Mock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.send_request = AsyncMock()
        mock_client.list_tools = AsyncMock(return_value=[])
        mock_client.list_resources = AsyncMock(return_value=[])
        mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
        return mock_client
    
    @staticmethod
    def create_mock_db_session():
        """Create a mock database session."""
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        mock_session.refresh = Mock()
        mock_session.close = Mock()
        mock_session.query = Mock()
        return mock_session


class ValidationHelper:
    """Helper for data validation in tests."""
    
    @staticmethod
    def assert_datetime_recent(dt: datetime, tolerance_seconds: int = 60) -> None:
        """Assert that a datetime is recent within tolerance."""
        now = datetime.utcnow()
        diff = abs((now - dt).total_seconds())
        assert diff <= tolerance_seconds, f"Datetime {dt} is not recent (diff: {diff}s)"
    
    @staticmethod
    def assert_mcp_server_structure(server_data: Dict[str, Any]) -> None:
        """Assert that server data has the correct structure."""
        required_fields = ["id", "name", "host", "port", "protocol", "status", "created_at"]
        for field in required_fields:
            assert field in server_data, f"Missing required field: {field}"
        
        # Validate types
        assert isinstance(server_data["id"], int)
        assert isinstance(server_data["name"], str)
        assert isinstance(server_data["host"], str)
        assert isinstance(server_data["port"], int)
        assert isinstance(server_data["protocol"], str)
        # assert server_data["status"] in [status.value for status in MCPServerStatus]
    
    @staticmethod
    def assert_error_response(response_data: Dict[str, Any]) -> None:
        """Assert that response data has error structure."""
        assert "detail" in response_data, "Error response should contain 'detail' field"
        assert isinstance(response_data["detail"], str), "Error detail should be a string"


class SecurityTestHelper:
    """Helper for security testing."""
    
    @staticmethod
    def get_invalid_tokens() -> List[str]:
        """Get list of invalid tokens for testing."""
        return [
            "",  # Empty token
            "invalid-token",  # Invalid format
            "Bearer ",  # Empty Bearer token
            "Bearer invalid",  # Invalid token content
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",  # Invalid JWT
        ]
    
    @staticmethod
    def get_sql_injection_payloads() -> List[str]:
        """Get common SQL injection payloads for testing."""
        return [
            "'; DROP TABLE mcp_servers; --",
            "' OR '1'='1",
            "1; DELETE FROM users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1#",
        ]
    
    @staticmethod
    def get_xss_payloads() -> List[str]:
        """Get common XSS payloads for testing."""
        return [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<iframe src='javascript:alert(`xss`)'></iframe>",
        ]
    
    @staticmethod
    async def test_authentication_required(
        client: AsyncClient, 
        method: str, 
        url: str, 
        **kwargs
    ) -> None:
        """Test that an endpoint requires authentication."""
        response = await client.request(method, url, **kwargs)
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    async def test_authorization_required(
        client: AsyncClient, 
        method: str, 
        url: str, 
        headers: Dict[str, str],
        **kwargs
    ) -> None:
        """Test that an endpoint requires proper authorization."""
        response = await client.request(method, url, headers=headers, **kwargs)
        APITestHelper.assert_status_code(response, status.HTTP_403_FORBIDDEN)


class PerformanceTestHelper:
    """Helper for performance testing."""
    
    @staticmethod
    def time_function(func):
        """Decorator to time function execution."""
        import time
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            end = time.time()
            execution_time = end - start
            print(f"{func.__name__} took {execution_time:.3f} seconds")
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            execution_time = end - start
            print(f"{func.__name__} took {execution_time:.3f} seconds")
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    @staticmethod
    def assert_response_time(response_time: float, max_time: float) -> None:
        """Assert that response time is within acceptable limits."""
        assert response_time <= max_time, (
            f"Response time {response_time:.3f}s exceeds maximum {max_time}s"
        )


import asyncio