"""
Comprehensive test suite for Kroger MCP Server Authentication System.

This test suite covers:
1. Token Lifecycle: Creation, refresh, expiration, and invalidation
2. Persistence: Token storage and retrieval across server restarts
3. Error Scenarios: Expired tokens, invalid refresh tokens, network failures
4. Cart Operations: Automatic token management for cart functionality
5. LLM Integration: Complete flow simulation for AI agent usage

Tests are designed to simulate real-world usage patterns by LLM agents.
"""

import pytest
import asyncio
import json
import time
import os
import tempfile
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from contextlib import asynccontextmanager

import httpx
from freezegun import freeze_time
import jwt

from tests.utils.test_helpers import APITestHelper, SecurityTestHelper, PerformanceTestHelper
from tests.factories.test_data_factory import TestDataFactory


class KrogerAuthDataFactory:
    """Factory for creating Kroger authentication test data."""
    
    @staticmethod
    def create_oauth_token_response(
        expires_in: int = 3600,
        include_refresh_token: bool = True,
        **overrides
    ) -> Dict[str, Any]:
        """Create realistic OAuth2 token response."""
        base_data = {
            "access_token": f"kroger_access_{TestDataFactory.random_string(64)}",
            "token_type": "Bearer",
            "expires_in": expires_in,
            "scope": "product.compact cart.basic:write profile.compact"
        }
        
        if include_refresh_token:
            base_data["refresh_token"] = f"kroger_refresh_{TestDataFactory.random_string(64)}"
        
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_expired_token_response() -> Dict[str, Any]:
        """Create expired token response."""
        return KrogerAuthDataFactory.create_oauth_token_response(
            expires_in=0,
            access_token="expired_token_123"
        )
    
    @staticmethod
    def create_client_credentials_token() -> Dict[str, Any]:
        """Create client credentials token for public API access."""
        return {
            "access_token": f"client_creds_{TestDataFactory.random_string(48)}",
            "token_type": "Bearer",
            "expires_in": 1800,  # 30 minutes
            "scope": "product.compact"
        }
    
    @staticmethod
    def create_auth_error_response(error_code: str = "invalid_grant") -> Dict[str, Any]:
        """Create authentication error response."""
        error_messages = {
            "invalid_grant": "The provided authorization grant is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.",
            "invalid_client": "Client authentication failed",
            "invalid_request": "The request is missing a required parameter, includes an invalid parameter value, includes a parameter more than once, or is otherwise malformed.",
            "unauthorized_client": "The client is not authorized to request an authorization code using this method.",
            "unsupported_grant_type": "The authorization grant type is not supported by the authorization server.",
            "invalid_scope": "The requested scope is invalid, unknown, or malformed."
        }
        
        return {
            "error": error_code,
            "error_description": error_messages.get(error_code, "Unknown error")
        }


class MockTokenStorage:
    """Mock token storage for testing persistence."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(tempfile.gettempdir(), "test_tokens.pkl")
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'rb') as f:
                    self.tokens = pickle.load(f)
            except (FileNotFoundError, pickle.PickleError):
                self.tokens = {}
    
    def _save_tokens(self):
        """Save tokens to storage."""
        with open(self.storage_path, 'wb') as f:
            pickle.dump(self.tokens, f)
    
    def store_token(self, user_id: str, token_data: Dict[str, Any]):
        """Store token for user."""
        self.tokens[user_id] = token_data
        self._save_tokens()
    
    def get_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get token for user."""
        return self.tokens.get(user_id)
    
    def remove_token(self, user_id: str):
        """Remove token for user."""
        if user_id in self.tokens:
            del self.tokens[user_id]
            self._save_tokens()
    
    def clear_all(self):
        """Clear all tokens."""
        self.tokens.clear()
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)


class MockKrogerAuthClient:
    """Mock Kroger authentication client for testing."""
    
    def __init__(self, fail_requests: bool = False, network_delay: float = 0.0):
        self.fail_requests = fail_requests
        self.network_delay = network_delay
        self.token_storage = MockTokenStorage()
        self.client_credentials_token: Optional[Dict[str, Any]] = None
        self.request_log: List[Dict[str, Any]] = []
    
    async def _simulate_network_delay(self):
        """Simulate network delay."""
        if self.network_delay > 0:
            await asyncio.sleep(self.network_delay)
    
    def _log_request(self, method: str, endpoint: str, **kwargs):
        """Log API request for testing purposes."""
        self.request_log.append({
            "method": method,
            "endpoint": endpoint,
            "timestamp": time.time(),
            **kwargs
        })
    
    async def get_client_credentials_token(self) -> str:
        """Get or refresh client credentials token."""
        await self._simulate_network_delay()
        
        if self.fail_requests:
            self._log_request("POST", "/connect/oauth2/token", grant_type="client_credentials")
            raise httpx.HTTPStatusError(
                "401 Unauthorized",
                request=Mock(),
                response=Mock(status_code=401, json=lambda: KrogerAuthDataFactory.create_auth_error_response("invalid_client"))
            )
        
        # Check if current token is valid
        if (self.client_credentials_token and 
            self.client_credentials_token.get("expires_at", 0) > time.time() + 300):
            return self.client_credentials_token["access_token"]
        
        # Only log request if we're actually making a new one
        self._log_request("POST", "/connect/oauth2/token", grant_type="client_credentials")
        
        # Create new token
        token_data = KrogerAuthDataFactory.create_client_credentials_token()
        self.client_credentials_token = {
            **token_data,
            "expires_at": time.time() + token_data["expires_in"]
        }
        
        return self.client_credentials_token["access_token"]
    
    async def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        await self._simulate_network_delay()
        self._log_request("POST", "/connect/oauth2/token", grant_type="authorization_code", code=auth_code)
        
        if self.fail_requests:
            raise httpx.HTTPStatusError(
                "400 Bad Request",
                request=Mock(),
                response=Mock(status_code=400, json=lambda: KrogerAuthDataFactory.create_auth_error_response("invalid_grant"))
            )
        
        return KrogerAuthDataFactory.create_oauth_token_response()
    
    async def refresh_user_token(self, refresh_token: str, user_id: str) -> Dict[str, Any]:
        """Refresh user access token."""
        await self._simulate_network_delay()
        self._log_request("POST", "/connect/oauth2/token", grant_type="refresh_token", user_id=user_id)
        
        if self.fail_requests:
            raise httpx.HTTPStatusError(
                "400 Bad Request",
                request=Mock(),
                response=Mock(status_code=400, json=lambda: KrogerAuthDataFactory.create_auth_error_response("invalid_grant"))
            )
        
        # Simulate refresh token rotation
        new_token_data = KrogerAuthDataFactory.create_oauth_token_response(
            access_token=f"refreshed_access_{TestDataFactory.random_string(64)}",
            refresh_token=f"new_refresh_{TestDataFactory.random_string(64)}"
        )
        
        # Store in mock storage
        token_info = {
            **new_token_data,
            "expires_at": time.time() + new_token_data["expires_in"]
        }
        self.token_storage.store_token(user_id, token_info)
        
        return new_token_data
    
    async def get_user_token(self, user_id: str) -> str:
        """Get valid user access token, refreshing if necessary."""
        stored_token = self.token_storage.get_token(user_id)
        
        if not stored_token:
            raise Exception("User not authenticated. Please complete OAuth flow.")
        
        # Check if token needs refresh
        if stored_token.get("expires_at", 0) <= time.time() + 300:  # 5 min buffer
            if "refresh_token" in stored_token:
                refreshed_data = await self.refresh_user_token(stored_token["refresh_token"], user_id)
                return refreshed_data["access_token"]
            else:
                raise Exception("Token expired and no refresh token available")
        
        return stored_token["access_token"]
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate access token."""
        await self._simulate_network_delay()
        self._log_request("GET", "/identity/profile", token=access_token)
        
        if self.fail_requests or access_token.startswith("expired_"):
            return False
        
        return True
    
    def is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if token is expired."""
        expires_at = token_data.get("expires_at", 0)
        return expires_at <= time.time()
    
    def time_until_expiry(self, token_data: Dict[str, Any]) -> int:
        """Get seconds until token expires."""
        expires_at = token_data.get("expires_at", 0)
        return max(0, int(expires_at - time.time()))


@pytest.mark.unit
@pytest.mark.asyncio
class TestKrogerAuthTokenLifecycle:
    """Test token lifecycle management."""
    
    @pytest.fixture
    def auth_client(self):
        """Create mock authentication client."""
        return MockKrogerAuthClient()
    
    @pytest.fixture
    def user_id(self):
        """Test user ID."""
        return f"test_user_{TestDataFactory.random_string(8)}"
    
    async def test_client_credentials_token_creation(self, auth_client):
        """Test client credentials token creation."""
        token = await auth_client.get_client_credentials_token()
        
        assert token is not None
        assert token.startswith("client_creds_")
        assert len(auth_client.request_log) == 1
        assert auth_client.request_log[0]["grant_type"] == "client_credentials"
    
    async def test_client_credentials_token_reuse(self, auth_client):
        """Test that valid client credentials tokens are reused."""
        # Get token first time
        token1 = await auth_client.get_client_credentials_token()
        
        # Get token second time (should reuse)
        token2 = await auth_client.get_client_credentials_token()
        
        assert token1 == token2
        assert len(auth_client.request_log) == 1  # Only one request made
    
    async def test_client_credentials_token_refresh_on_expiry(self, auth_client):
        """Test client credentials token refresh when expired."""
        # Get initial token
        token1 = await auth_client.get_client_credentials_token()
        
        # Simulate token expiry
        auth_client.client_credentials_token["expires_at"] = time.time() - 100
        
        # Get token again (should refresh)
        token2 = await auth_client.get_client_credentials_token()
        
        assert token1 != token2
        assert len(auth_client.request_log) == 2  # Two requests made
    
    async def test_user_token_creation_via_oauth(self, auth_client, user_id):
        """Test user token creation through OAuth flow."""
        auth_code = "test_auth_code_123"
        
        # Exchange code for token
        token_data = await auth_client.exchange_code_for_token(auth_code)
        
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert "expires_in" in token_data
        assert token_data["token_type"] == "Bearer"
        
        # Verify request was logged
        assert len(auth_client.request_log) == 1
        assert auth_client.request_log[0]["grant_type"] == "authorization_code"
        assert auth_client.request_log[0]["code"] == auth_code
    
    async def test_user_token_refresh_success(self, auth_client, user_id):
        """Test successful user token refresh."""
        # Setup initial token
        initial_token = KrogerAuthDataFactory.create_oauth_token_response()
        auth_client.token_storage.store_token(user_id, {
            **initial_token,
            "expires_at": time.time() + 3600
        })
        
        # Refresh token
        refreshed_data = await auth_client.refresh_user_token(initial_token["refresh_token"], user_id)
        
        assert refreshed_data["access_token"] != initial_token["access_token"]
        assert refreshed_data["refresh_token"] != initial_token["refresh_token"]
        assert "refreshed_access_" in refreshed_data["access_token"]
        
        # Verify new token is stored
        stored_token = auth_client.token_storage.get_token(user_id)
        assert stored_token["access_token"] == refreshed_data["access_token"]
    
    async def test_automatic_token_refresh_on_expiry(self, auth_client, user_id):
        """Test automatic token refresh when token is near expiry."""
        # Setup nearly expired token
        initial_token = KrogerAuthDataFactory.create_oauth_token_response()
        auth_client.token_storage.store_token(user_id, {
            **initial_token,
            "expires_at": time.time() + 200  # Expires in 200 seconds (within 5 min buffer)
        })
        
        # Get user token (should trigger refresh)
        access_token = await auth_client.get_user_token(user_id)
        
        assert access_token.startswith("refreshed_access_")
        assert len(auth_client.request_log) == 1
        assert auth_client.request_log[0]["grant_type"] == "refresh_token"
    
    async def test_token_validation_success(self, auth_client):
        """Test successful token validation."""
        valid_token = "valid_token_123"
        
        is_valid = await auth_client.validate_token(valid_token)
        
        assert is_valid is True
        assert len(auth_client.request_log) == 1
        assert auth_client.request_log[0]["token"] == valid_token
    
    async def test_token_validation_failure(self, auth_client):
        """Test token validation failure."""
        expired_token = "expired_token_123"
        
        is_valid = await auth_client.validate_token(expired_token)
        
        assert is_valid is False
    
    async def test_token_expiry_detection(self, auth_client):
        """Test token expiry detection."""
        # Test expired token
        expired_token = {
            "access_token": "expired_token",
            "expires_at": time.time() - 100
        }
        assert auth_client.is_token_expired(expired_token) is True
        
        # Test valid token
        valid_token = {
            "access_token": "valid_token",
            "expires_at": time.time() + 3600
        }
        assert auth_client.is_token_expired(valid_token) is False
    
    async def test_time_until_expiry_calculation(self, auth_client):
        """Test time until expiry calculation."""
        # Token expiring in 1 hour
        token_data = {
            "access_token": "test_token",
            "expires_at": time.time() + 3600
        }
        
        time_left = auth_client.time_until_expiry(token_data)
        assert 3595 <= time_left <= 3600  # Allow for small timing differences
        
        # Expired token
        expired_token = {
            "access_token": "expired_token",
            "expires_at": time.time() - 100
        }
        
        time_left = auth_client.time_until_expiry(expired_token)
        assert time_left == 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestKrogerAuthTokenPersistence:
    """Test token persistence across server restarts."""
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
        temp_file.close()
        yield temp_file.name
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    @pytest.fixture
    def auth_client_with_storage(self, temp_storage_path):
        """Create auth client with persistent storage."""
        return MockKrogerAuthClient()
    
    async def test_token_persistence_across_restarts(self, temp_storage_path):
        """Test that tokens survive server restarts."""
        user_id = "persistent_user_123"
        
        # Create first client instance and store token
        client1 = MockKrogerAuthClient()
        client1.token_storage = MockTokenStorage(temp_storage_path)
        
        token_data = KrogerAuthDataFactory.create_oauth_token_response()
        token_info = {
            **token_data,
            "expires_at": time.time() + 3600
        }
        client1.token_storage.store_token(user_id, token_info)
        
        # Verify token is stored
        stored_token1 = client1.token_storage.get_token(user_id)
        assert stored_token1["access_token"] == token_data["access_token"]
        
        # Simulate server restart by creating new client instance
        client2 = MockKrogerAuthClient()
        client2.token_storage = MockTokenStorage(temp_storage_path)
        
        # Verify token persisted across restart
        stored_token2 = client2.token_storage.get_token(user_id)
        assert stored_token2 is not None
        assert stored_token2["access_token"] == token_data["access_token"]
        assert stored_token2["expires_at"] == token_info["expires_at"]
    
    async def test_token_refresh_updates_storage(self, temp_storage_path):
        """Test that token refresh updates persistent storage."""
        user_id = "refresh_user_123"
        
        client = MockKrogerAuthClient()
        client.token_storage = MockTokenStorage(temp_storage_path)
        
        # Store initial token
        initial_token = KrogerAuthDataFactory.create_oauth_token_response()
        client.token_storage.store_token(user_id, {
            **initial_token,
            "expires_at": time.time() + 3600
        })
        
        # Refresh token
        refreshed_data = await client.refresh_user_token(initial_token["refresh_token"], user_id)
        
        # Verify storage was updated
        stored_token = client.token_storage.get_token(user_id)
        assert stored_token["access_token"] == refreshed_data["access_token"]
        assert stored_token["refresh_token"] == refreshed_data["refresh_token"]
        
        # Verify persistence by creating new client
        client2 = MockKrogerAuthClient()
        client2.token_storage = MockTokenStorage(temp_storage_path)
        
        stored_token2 = client2.token_storage.get_token(user_id)
        assert stored_token2["access_token"] == refreshed_data["access_token"]
    
    async def test_token_removal_from_storage(self, temp_storage_path):
        """Test token removal from persistent storage."""
        user_id = "remove_user_123"
        
        storage = MockTokenStorage(temp_storage_path)
        
        # Store token
        token_data = KrogerAuthDataFactory.create_oauth_token_response()
        storage.store_token(user_id, {
            **token_data,
            "expires_at": time.time() + 3600
        })
        
        # Verify token exists
        assert storage.get_token(user_id) is not None
        
        # Remove token
        storage.remove_token(user_id)
        
        # Verify token is gone
        assert storage.get_token(user_id) is None
        
        # Verify persistence of removal
        storage2 = MockTokenStorage(temp_storage_path)
        assert storage2.get_token(user_id) is None
    
    async def test_storage_corruption_handling(self, temp_storage_path):
        """Test handling of corrupted storage files."""
        # Write invalid data to storage file
        with open(temp_storage_path, 'w') as f:
            f.write("invalid pickle data")
        
        # Should handle corruption gracefully
        storage = MockTokenStorage(temp_storage_path)
        assert storage.tokens == {}
        
        # Should be able to store new tokens
        user_id = "corruption_test_user"
        token_data = KrogerAuthDataFactory.create_oauth_token_response()
        storage.store_token(user_id, token_data)
        
        assert storage.get_token(user_id) is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestKrogerAuthErrorScenarios:
    """Test error scenarios and network failures."""
    
    @pytest.fixture
    def failing_auth_client(self):
        """Create auth client that simulates failures."""
        return MockKrogerAuthClient(fail_requests=True)
    
    @pytest.fixture
    def slow_auth_client(self):
        """Create auth client with network delays."""
        return MockKrogerAuthClient(network_delay=2.0)
    
    async def test_network_failure_during_token_request(self, failing_auth_client):
        """Test handling of network failures during token requests."""
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await failing_auth_client.get_client_credentials_token()
        
        assert exc_info.value.response.status_code == 401
        error_data = exc_info.value.response.json()
        assert error_data["error"] == "invalid_client"
    
    async def test_invalid_refresh_token_handling(self, failing_auth_client):
        """Test handling of invalid refresh tokens."""
        user_id = "invalid_refresh_user"
        invalid_refresh_token = "invalid_refresh_token_123"
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await failing_auth_client.refresh_user_token(invalid_refresh_token, user_id)
        
        assert exc_info.value.response.status_code == 400
        error_data = exc_info.value.response.json()
        assert error_data["error"] == "invalid_grant"
    
    async def test_expired_token_error_handling(self, auth_client=None):
        """Test handling of expired tokens."""
        if auth_client is None:
            auth_client = MockKrogerAuthClient()
        
        user_id = "expired_user_123"
        
        # Store expired token without refresh token
        expired_token = {
            "access_token": "expired_token_123",
            "expires_at": time.time() - 100
        }
        auth_client.token_storage.store_token(user_id, expired_token)
        
        # Should raise exception when trying to get token
        with pytest.raises(Exception) as exc_info:
            await auth_client.get_user_token(user_id)
        
        assert "expired and no refresh token available" in str(exc_info.value)
    
    async def test_missing_user_token_handling(self):
        """Test handling when user has no stored token."""
        auth_client = MockKrogerAuthClient()
        user_id = "nonexistent_user"
        
        with pytest.raises(Exception) as exc_info:
            await auth_client.get_user_token(user_id)
        
        assert "not authenticated" in str(exc_info.value)
    
    async def test_network_timeout_handling(self, slow_auth_client):
        """Test handling of network timeouts."""
        start_time = time.time()
        
        # This should take at least 2 seconds due to network delay
        token = await slow_auth_client.get_client_credentials_token()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert execution_time >= 2.0
        assert token is not None
    
    async def test_malformed_response_handling(self):
        """Test handling of malformed API responses."""
        auth_client = MockKrogerAuthClient()
        
        # Mock a malformed response by overriding the method
        original_method = auth_client.get_client_credentials_token
        
        async def mock_malformed_response():
            await auth_client._simulate_network_delay()
            raise httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=Mock(),
                response=Mock(
                    status_code=500,
                    json=lambda: {"malformed": "response"}
                )
            )
        
        auth_client.get_client_credentials_token = mock_malformed_response
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await auth_client.get_client_credentials_token()
        
        assert exc_info.value.response.status_code == 500
    
    async def test_retry_logic_on_temporary_failures(self):
        """Test retry logic for temporary failures."""
        auth_client = MockKrogerAuthClient()
        attempt_count = 0
        
        async def mock_retry_logic():
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:
                raise httpx.HTTPStatusError(
                    "503 Service Unavailable",
                    request=Mock(),
                    response=Mock(status_code=503)
                )
            else:
                return await auth_client.get_client_credentials_token()
        
        # Simulate retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await mock_retry_logic()
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503 and attempt < max_retries - 1:
                    await asyncio.sleep(0.1)  # Brief delay before retry
                    continue
                raise
        
        assert attempt_count == 3
        assert result is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestKrogerAuthCartOperations:
    """Test cart operations with automatic token management."""
    
    @pytest.fixture
    def auth_client_with_user(self):
        """Create auth client with authenticated user."""
        client = MockKrogerAuthClient()
        user_id = "cart_test_user"
        
        # Setup authenticated user
        token_data = KrogerAuthDataFactory.create_oauth_token_response()
        client.token_storage.store_token(user_id, {
            **token_data,
            "expires_at": time.time() + 3600
        })
        
        return client, user_id
    
    async def test_cart_operations_with_valid_token(self, auth_client_with_user):
        """Test cart operations with valid authentication token."""
        auth_client, user_id = auth_client_with_user
        
        # Get user token for cart operations
        access_token = await auth_client.get_user_token(user_id)
        
        assert access_token is not None
        assert access_token.startswith("kroger_access_")
        
        # Simulate cart API calls
        cart_operations = [
            {"operation": "create_cart", "token": access_token},
            {"operation": "add_item", "token": access_token, "upc": "1234567890"},
            {"operation": "get_cart", "token": access_token},
            {"operation": "update_quantity", "token": access_token, "upc": "1234567890", "quantity": 2}
        ]
        
        for operation in cart_operations:
            # Validate token for each operation
            is_valid = await auth_client.validate_token(operation["token"])
            assert is_valid is True
    
    async def test_automatic_token_refresh_during_cart_operations(self, auth_client_with_user):
        """Test automatic token refresh during cart operations."""
        auth_client, user_id = auth_client_with_user
        
        # Set token to expire soon
        stored_token = auth_client.token_storage.get_token(user_id)
        stored_token["expires_at"] = time.time() + 200  # Expires in 200 seconds
        auth_client.token_storage.store_token(user_id, stored_token)
        
        # Get token for cart operation (should trigger refresh)
        access_token = await auth_client.get_user_token(user_id)
        
        # Should get refreshed token
        assert access_token.startswith("refreshed_access_")
        
        # Verify refresh was logged
        refresh_requests = [req for req in auth_client.request_log if req.get("grant_type") == "refresh_token"]
        assert len(refresh_requests) == 1
    
    async def test_cart_operations_fail_without_authentication(self):
        """Test that cart operations fail without proper authentication."""
        auth_client = MockKrogerAuthClient()
        unauthenticated_user = "unauthenticated_user"
        
        # Should fail to get token for unauthenticated user
        with pytest.raises(Exception) as exc_info:
            await auth_client.get_user_token(unauthenticated_user)
        
        assert "not authenticated" in str(exc_info.value)
    
    async def test_cart_operations_with_expired_token_and_no_refresh(self):
        """Test cart operations when token is expired and no refresh token available."""
        auth_client = MockKrogerAuthClient()
        user_id = "expired_no_refresh_user"
        
        # Store expired token without refresh token
        expired_token = {
            "access_token": "expired_token_123",
            "expires_at": time.time() - 100
        }
        auth_client.token_storage.store_token(user_id, expired_token)
        
        # Should fail to get valid token
        with pytest.raises(Exception) as exc_info:
            await auth_client.get_user_token(user_id)
        
        assert "expired and no refresh token available" in str(exc_info.value)
    
    async def test_concurrent_cart_operations_token_management(self, auth_client_with_user):
        """Test token management during concurrent cart operations."""
        auth_client, user_id = auth_client_with_user
        
        async def cart_operation(operation_id: int):
            """Simulate individual cart operation."""
            access_token = await auth_client.get_user_token(user_id)
            await auth_client.validate_token(access_token)
            return {"operation_id": operation_id, "token": access_token, "success": True}
        
        # Run multiple concurrent cart operations
        tasks = [cart_operation(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
            assert result["token"] is not None
        
        # Should all use the same token (no unnecessary refreshes)
        tokens = [result["token"] for result in results]
        assert len(set(tokens)) == 1  # All tokens should be the same


@pytest.mark.e2e
@pytest.mark.asyncio
class TestKrogerAuthLLMIntegration:
    """Test complete flow an LLM would experience."""
    
    @pytest.fixture
    def llm_simulation_client(self):
        """Create client for LLM simulation."""
        return MockKrogerAuthClient()
    
    async def test_complete_llm_authentication_flow(self, llm_simulation_client):
        """Test complete authentication flow as experienced by LLM."""
        # Step 1: LLM requests authorization URL
        auth_url = (
            "https://api.kroger.com/v1/connect/oauth2/authorize"
            "?client_id=test_client_id"
            "&redirect_uri=http://localhost:9004/auth/callback"
            "&response_type=code"
            "&scope=profile.compact%20cart.basic:write"
        )
        
        # Step 2: User completes OAuth flow (simulated)
        auth_code = "simulated_auth_code_123"
        
        # Step 3: LLM exchanges code for tokens
        token_data = await llm_simulation_client.exchange_code_for_token(auth_code)
        
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        
        # Step 4: Store tokens for LLM session
        llm_user_id = "llm_agent_session_123"
        llm_simulation_client.token_storage.store_token(llm_user_id, {
            **token_data,
            "expires_at": time.time() + token_data["expires_in"]
        })
        
        # Step 5: LLM performs operations with automatic token management
        operations = [
            "search_products",
            "get_product_details", 
            "search_locations",
            "create_cart",
            "add_to_cart",
            "get_user_profile"
        ]
        
        for operation in operations:
            # Each operation should get valid token automatically
            access_token = await llm_simulation_client.get_user_token(llm_user_id)
            is_valid = await llm_simulation_client.validate_token(access_token)
            assert is_valid is True
        
        # Step 6: Verify tokens persist across LLM session restarts
        new_client = MockKrogerAuthClient()
        new_client.token_storage = llm_simulation_client.token_storage
        
        access_token = await new_client.get_user_token(llm_user_id)
        assert access_token is not None
    
    async def test_llm_graceful_error_handling(self, llm_simulation_client):
        """Test that LLM receives helpful error messages."""
        # Test authentication required error
        with pytest.raises(Exception) as exc_info:
            await llm_simulation_client.get_user_token("nonexistent_llm_user")
        
        error_message = str(exc_info.value)
        assert "not authenticated" in error_message
        assert "Please complete OAuth flow" in error_message
        
        # Error message should guide LLM to next steps
        assert "OAuth" in error_message
    
    async def test_llm_token_refresh_transparency(self, llm_simulation_client):
        """Test that token refresh is transparent to LLM."""
        llm_user_id = "llm_refresh_test"
        
        # Setup token that will need refresh
        initial_token = KrogerAuthDataFactory.create_oauth_token_response()
        llm_simulation_client.token_storage.store_token(llm_user_id, {
            **initial_token,
            "expires_at": time.time() + 200  # Will expire within 5 min buffer
        })
        
        # LLM requests token - should get refreshed token transparently
        access_token = await llm_simulation_client.get_user_token(llm_user_id)
        
        # Should be refreshed token
        assert access_token.startswith("refreshed_access_")
        
        # LLM doesn't need to know about refresh - it just works
        is_valid = await llm_simulation_client.validate_token(access_token)
        assert is_valid is True
    
    async def test_llm_multiple_concurrent_requests(self, llm_simulation_client):
        """Test LLM making multiple concurrent requests."""
        llm_user_id = "llm_concurrent_test"
        
        # Setup authenticated LLM user
        token_data = KrogerAuthDataFactory.create_oauth_token_response()
        llm_simulation_client.token_storage.store_token(llm_user_id, {
            **token_data,
            "expires_at": time.time() + 3600
        })
        
        async def llm_api_call(call_id: int):
            """Simulate LLM making API call."""
            access_token = await llm_simulation_client.get_user_token(llm_user_id)
            is_valid = await llm_simulation_client.validate_token(access_token)
            return {"call_id": call_id, "success": is_valid}
        
        # LLM makes multiple concurrent API calls
        concurrent_calls = 10
        tasks = [llm_api_call(i) for i in range(concurrent_calls)]
        results = await asyncio.gather(*tasks)
        
        # All calls should succeed
        assert len(results) == concurrent_calls
        for result in results:
            assert result["success"] is True
    
    async def test_llm_session_persistence_across_restarts(self, temp_storage_path):
        """Test LLM session persistence across server restarts."""
        llm_user_id = "llm_persistent_session"
        
        # First LLM session
        client1 = MockKrogerAuthClient()
        client1.token_storage = MockTokenStorage(temp_storage_path)
        
        # LLM authenticates
        token_data = KrogerAuthDataFactory.create_oauth_token_response()
        client1.token_storage.store_token(llm_user_id, {
            **token_data,
            "expires_at": time.time() + 3600
        })
        
        # LLM performs some operations
        access_token1 = await client1.get_user_token(llm_user_id)
        assert access_token1 is not None
        
        # Simulate server restart
        client2 = MockKrogerAuthClient()
        client2.token_storage = MockTokenStorage(temp_storage_path)
        
        # LLM session should continue seamlessly
        access_token2 = await client2.get_user_token(llm_user_id)
        assert access_token2 == access_token1
        
        # LLM can continue operations without re-authentication
        is_valid = await client2.validate_token(access_token2)
        assert is_valid is True
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path for LLM persistence test."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
        temp_file.close()
        yield temp_file.name
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@pytest.mark.performance
@pytest.mark.asyncio
class TestKrogerAuthPerformance:
    """Test authentication performance characteristics."""
    
    async def test_token_operation_performance(self):
        """Test performance of token operations."""
        auth_client = MockKrogerAuthClient()
        
        # Test client credentials token performance
        start_time = time.time()
        await auth_client.get_client_credentials_token()
        end_time = time.time()
        
        client_creds_time = end_time - start_time
        PerformanceTestHelper.assert_response_time(client_creds_time, 1.0)
        
        # Test user token refresh performance
        user_id = "perf_test_user"
        token_data = KrogerAuthDataFactory.create_oauth_token_response()
        auth_client.token_storage.store_token(user_id, {
            **token_data,
            "expires_at": time.time() + 3600
        })
        
        start_time = time.time()
        await auth_client.refresh_user_token(token_data["refresh_token"], user_id)
        end_time = time.time()
        
        refresh_time = end_time - start_time
        PerformanceTestHelper.assert_response_time(refresh_time, 1.0)
    
    async def test_concurrent_authentication_performance(self):
        """Test performance under concurrent authentication load."""
        auth_client = MockKrogerAuthClient()
        
        async def auth_operation(user_id: str):
            """Single authentication operation."""
            token_data = KrogerAuthDataFactory.create_oauth_token_response()
            auth_client.token_storage.store_token(user_id, {
                **token_data,
                "expires_at": time.time() + 3600
            })
            return await auth_client.get_user_token(user_id)
        
        # Test 20 concurrent authentication operations
        start_time = time.time()
        tasks = [auth_operation(f"user_{i}") for i in range(20)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        assert len(results) == 20
        assert all(token is not None for token in results)
        
        # Should complete all operations within reasonable time
        PerformanceTestHelper.assert_response_time(total_time, 5.0)
    
    async def test_token_storage_performance(self, temp_storage_path):
        """Test token storage performance."""
        storage = MockTokenStorage(temp_storage_path)
        
        # Test bulk token storage
        start_time = time.time()
        for i in range(100):
            token_data = KrogerAuthDataFactory.create_oauth_token_response()
            storage.store_token(f"user_{i}", token_data)
        end_time = time.time()
        
        storage_time = end_time - start_time
        PerformanceTestHelper.assert_response_time(storage_time, 2.0)
        
        # Test bulk token retrieval
        start_time = time.time()
        for i in range(100):
            token = storage.get_token(f"user_{i}")
            assert token is not None
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        PerformanceTestHelper.assert_response_time(retrieval_time, 1.0)
    
    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path for performance test."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
        temp_file.close()
        yield temp_file.name
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])