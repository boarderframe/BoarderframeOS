"""
Authentication-related test fixtures.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch

from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.auth import User, TokenData


@pytest.fixture
def mock_jwt_token() -> str:
    """Create a mock JWT token for testing."""
    test_data = {"sub": "test-user-123", "email": "test@example.com"}
    return create_access_token(data=test_data)


@pytest.fixture
def expired_jwt_token() -> str:
    """Create an expired JWT token for testing."""
    test_data = {"sub": "test-user-123", "email": "test@example.com"}
    return create_access_token(data=test_data, expires_delta=timedelta(minutes=-1))


@pytest.fixture
def admin_jwt_token() -> str:
    """Create a JWT token for admin user."""
    test_data = {
        "sub": "admin-user-123", 
        "email": "admin@example.com",
        "is_superuser": True
    }
    return create_access_token(data=test_data)


@pytest.fixture
def user_credentials() -> Dict[str, str]:
    """Valid user credentials for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!"
    }


@pytest.fixture
def admin_credentials() -> Dict[str, str]:
    """Admin user credentials for testing."""
    return {
        "username": "admin",
        "email": "admin@example.com", 
        "password": "AdminPassword123!"
    }


@pytest.fixture
def password_hash() -> str:
    """Create a password hash for testing."""
    return get_password_hash("TestPassword123!")


@pytest.fixture
def mock_current_user() -> User:
    """Mock current user for dependency injection."""
    return User(
        id="test-user-123",
        email="test@example.com",
        username="testuser",
        is_active=True,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_current_admin() -> User:
    """Mock current admin user for dependency injection."""
    return User(
        id="admin-user-123",
        email="admin@example.com",
        username="admin",
        is_active=True,
        is_superuser=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_inactive_user() -> User:
    """Mock inactive user for testing."""
    return User(
        id="inactive-user-123",
        email="inactive@example.com",
        username="inactiveuser",
        is_active=False,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def auth_headers_factory():
    """Factory for creating authentication headers."""
    def _create_headers(user_id: str = "test-user-123", **token_data):
        default_data = {"sub": user_id}
        default_data.update(token_data)
        token = create_access_token(data=default_data)
        return {"Authorization": f"Bearer {token}"}
    return _create_headers


@pytest.fixture
def mock_token_data() -> TokenData:
    """Mock token data for testing."""
    return TokenData(
        sub="test-user-123",
        email="test@example.com",
        exp=datetime.utcnow() + timedelta(hours=1)
    )


@pytest.fixture
def invalid_tokens() -> list[str]:
    """List of invalid tokens for testing."""
    return [
        "",  # Empty token
        "invalid-token",  # Invalid format
        "Bearer ",  # Empty Bearer token
        "Bearer invalid",  # Invalid token content
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",  # Invalid JWT
        "Bearer " + "x" * 1000,  # Oversized token
    ]


@pytest.fixture
def login_data_valid() -> Dict[str, str]:
    """Valid login form data."""
    return {
        "username": "testuser",
        "password": "TestPassword123!"
    }


@pytest.fixture
def login_data_invalid() -> list[Dict[str, str]]:
    """List of invalid login data sets."""
    return [
        {"username": "", "password": ""},  # Empty credentials
        {"username": "testuser", "password": "wrong"},  # Wrong password
        {"username": "nonexistent", "password": "TestPassword123!"},  # Wrong username
        {"username": "testuser"},  # Missing password
        {"password": "TestPassword123!"},  # Missing username
    ]


@pytest.fixture
def registration_data_valid() -> Dict[str, Any]:
    """Valid user registration data."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "NewUserPassword123!",
        "full_name": "New User"
    }


@pytest.fixture
def registration_data_invalid() -> list[Dict[str, Any]]:
    """List of invalid registration data sets."""
    return [
        # Missing required fields
        {"email": "test@example.com"},
        {"username": "testuser"},
        {"password": "password123"},
        
        # Invalid email formats
        {"email": "invalid-email", "username": "user", "password": "Pass123!"},
        {"email": "", "username": "user", "password": "Pass123!"},
        
        # Invalid passwords
        {"email": "test@example.com", "username": "user", "password": "weak"},
        {"email": "test@example.com", "username": "user", "password": ""},
        
        # Invalid usernames
        {"email": "test@example.com", "username": "", "password": "Pass123!"},
        {"email": "test@example.com", "username": "a", "password": "Pass123!"},  # Too short
        {"email": "test@example.com", "username": "x" * 100, "password": "Pass123!"},  # Too long
    ]


@pytest.fixture
def oauth_token_data() -> Dict[str, Any]:
    """Mock OAuth token data."""
    return {
        "access_token": "mock-oauth-token",
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": "mock-refresh-token",
        "scope": "read write"
    }


@pytest.fixture
def oauth_user_info() -> Dict[str, Any]:
    """Mock OAuth user info."""
    return {
        "id": "oauth-user-123",
        "email": "oauth@example.com",
        "name": "OAuth User",
        "picture": "https://example.com/avatar.jpg",
        "verified_email": True
    }


@pytest.fixture
def mock_oauth_provider():
    """Mock OAuth provider for testing."""
    mock_provider = Mock()
    mock_provider.get_authorization_url.return_value = "https://oauth.example.com/auth"
    mock_provider.get_access_token.return_value = {
        "access_token": "mock-token",
        "token_type": "bearer"
    }
    mock_provider.get_user_info.return_value = {
        "id": "oauth-123",
        "email": "oauth@example.com"
    }
    return mock_provider


@pytest.fixture
def mock_password_reset_token() -> str:
    """Mock password reset token."""
    return "mock-reset-token-" + "x" * 32


@pytest.fixture
def password_update_data() -> Dict[str, str]:
    """Password update data for testing."""
    return {
        "current_password": "TestPassword123!",
        "new_password": "NewPassword456!",
        "confirm_password": "NewPassword456!"
    }


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing."""
    mock_limiter = Mock()
    mock_limiter.hit.return_value = True
    mock_limiter.reset.return_value = True
    mock_limiter.get_window_stats.return_value = {
        "hits": 5,
        "remaining": 15,
        "reset_time": datetime.utcnow() + timedelta(minutes=1)
    }
    return mock_limiter