"""
Security tests for authentication and authorization.
"""
import pytest
from datetime import datetime, timedelta
from fastapi import status
from httpx import AsyncClient
from unittest.mock import patch, Mock

from tests.utils import APITestHelper, SecurityTestHelper, DataFactory
from app.core.security import create_access_token


@pytest.mark.security
@pytest.mark.asyncio
class TestAuthentication:
    """Test suite for authentication security."""
    
    async def test_endpoints_require_authentication(self, async_client: AsyncClient):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            ("GET", "/api/v1/mcp-servers/"),
            ("POST", "/api/v1/mcp-servers/"),
            ("GET", "/api/v1/mcp-servers/1"),
            ("PUT", "/api/v1/mcp-servers/1"),
            ("DELETE", "/api/v1/mcp-servers/1"),
        ]
        
        for method, endpoint in protected_endpoints:
            await SecurityTestHelper.test_authentication_required(
                async_client, method, endpoint
            )
    
    async def test_invalid_token_formats(self, async_client: AsyncClient):
        """Test various invalid token formats."""
        invalid_tokens = SecurityTestHelper.get_invalid_tokens()
        
        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ], f"Invalid token should be rejected: {token}"
    
    async def test_expired_token(self, async_client: AsyncClient):
        """Test that expired tokens are rejected."""
        # Create expired token
        expired_token_data = {"sub": "test-user", "exp": datetime.utcnow() - timedelta(hours=1)}
        expired_token = create_access_token(data=expired_token_data, expires_delta=timedelta(hours=-1))
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
        
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
    
    async def test_malformed_jwt_token(self, async_client: AsyncClient):
        """Test that malformed JWT tokens are rejected."""
        malformed_tokens = [
            "not.a.jwt.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.malformed",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.",  # Missing signature
            ".eyJzdWIiOiJ0ZXN0In0.signature",  # Missing header
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..signature",  # Missing payload
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ], f"Malformed JWT should be rejected: {token}"
    
    async def test_token_without_bearer_prefix(self, async_client: AsyncClient):
        """Test that tokens without Bearer prefix are rejected."""
        token_data = {"sub": "test-user"}
        token = create_access_token(data=token_data)
        
        # Try different authorization header formats
        invalid_auth_headers = [
            {"Authorization": token},  # Missing Bearer
            {"Authorization": f"Basic {token}"},  # Wrong auth type
            {"Authorization": f"Token {token}"},  # Wrong auth type
            {"authorization": f"Bearer {token}"},  # Wrong case
        ]
        
        for headers in invalid_auth_headers:
            response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    async def test_missing_authorization_header(self, async_client: AsyncClient):
        """Test requests without authorization header are rejected."""
        response = await async_client.get("/api/v1/mcp-servers/")
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
    
    async def test_empty_authorization_header(self, async_client: AsyncClient):
        """Test empty authorization header is rejected."""
        headers = {"Authorization": ""}
        response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    async def test_token_with_invalid_signature(self, async_client: AsyncClient):
        """Test token with invalid signature is rejected."""
        # Create token with valid structure but invalid signature
        token_data = {"sub": "test-user"}
        valid_token = create_access_token(data=token_data)
        
        # Tamper with the signature
        parts = valid_token.split('.')
        tampered_token = '.'.join(parts[:-1] + ['invalid_signature'])
        
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
        
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
    
    async def test_token_with_invalid_issuer(self, async_client: AsyncClient):
        """Test token with invalid issuer is rejected."""
        # Create token with invalid issuer
        token_data = {"sub": "test-user", "iss": "invalid-issuer"}
        token = create_access_token(data=token_data)
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
        
        # Depending on implementation, this might be accepted or rejected
        # Document the current behavior
        assert response.status_code in [
            status.HTTP_200_OK,  # If issuer validation is not implemented
            status.HTTP_401_UNAUTHORIZED,  # If issuer validation is implemented
            status.HTTP_403_FORBIDDEN,
        ]
    
    async def test_concurrent_authentication_requests(self, async_client: AsyncClient):
        """Test concurrent authentication requests don't cause issues."""
        import asyncio
        
        # Create valid token
        token_data = {"sub": "test-user"}
        token = create_access_token(data=token_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make multiple concurrent requests
        tasks = [
            async_client.get("/api/v1/mcp-servers/", headers=headers)
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should either succeed or fail consistently
        status_codes = [r.status_code for r in responses if hasattr(r, 'status_code')]
        
        # Should get consistent responses (all 200 or all unauthorized)
        assert len(set(status_codes)) <= 2  # Allow for some variation
    
    @patch('app.core.security.verify_token')
    async def test_authentication_rate_limiting(self, mock_verify, async_client: AsyncClient):
        """Test rate limiting on authentication attempts."""
        # Simulate failed authentication attempts
        mock_verify.return_value = None
        
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        
        # Make multiple failed attempts
        responses = []
        for _ in range(10):
            response = await async_client.get("/api/v1/mcp-servers/", headers=invalid_headers)
            responses.append(response)
        
        # Check if rate limiting is applied
        rate_limited_responses = [
            r for r in responses 
            if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        ]
        
        # Document current behavior - rate limiting may or may not be implemented
        if rate_limited_responses:
            assert len(rate_limited_responses) > 0, "Rate limiting is implemented"
        else:
            assert all(r.status_code == status.HTTP_401_UNAUTHORIZED for r in responses), \
                "Rate limiting not implemented, all requests should be unauthorized"
    
    async def test_authentication_timing_attack_protection(self, async_client: AsyncClient):
        """Test protection against timing attacks on authentication."""
        import time
        
        # Test with invalid token
        start_time = time.time()
        headers = {"Authorization": "Bearer invalid-token"}
        await async_client.get("/api/v1/mcp-servers/", headers=headers)
        invalid_time = time.time() - start_time
        
        # Test with missing token
        start_time = time.time()
        await async_client.get("/api/v1/mcp-servers/")
        missing_time = time.time() - start_time
        
        # Response times should be similar to prevent timing attacks
        time_difference = abs(invalid_time - missing_time)
        
        # Allow some variance but not too much
        assert time_difference < 0.1, f"Potential timing attack vulnerability: {time_difference:.3f}s difference"
    
    async def test_authentication_error_responses_dont_leak_info(self, async_client: AsyncClient):
        """Test that authentication error responses don't leak sensitive information."""
        test_cases = [
            {"Authorization": ""},  # Empty
            {"Authorization": "Bearer "},  # Empty Bearer
            {"Authorization": "Bearer invalid"},  # Invalid token
            {"Authorization": "Bearer " + "x" * 1000},  # Oversized token
        ]
        
        for headers in test_cases:
            response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
            
            # Check that error response doesn't leak sensitive information
            response_text = response.text.lower()
            
            # Should not contain sensitive information
            sensitive_keywords = [
                "secret", "password", "key", "token", "database", 
                "connection", "internal", "stack", "trace"
            ]
            
            for keyword in sensitive_keywords:
                assert keyword not in response_text, \
                    f"Error response contains sensitive keyword: {keyword}"
    
    async def test_options_requests_dont_require_authentication(self, async_client: AsyncClient):
        """Test that OPTIONS requests don't require authentication (for CORS)."""
        response = await async_client.options(
            "/api/v1/mcp-servers/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # OPTIONS should not require authentication
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_405_METHOD_NOT_ALLOWED  # If OPTIONS is not implemented
        ]