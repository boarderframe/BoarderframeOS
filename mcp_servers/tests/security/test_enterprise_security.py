"""
Enterprise Security Test Suite for MCP-UI System
Comprehensive security testing following OWASP guidelines
"""

import pytest
import asyncio
import json
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

import jwt
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from redis import Redis
import fakeredis

# Import security modules
from src.app.core.enhanced_security import (
    SecurityConfig,
    EnhancedJWTManager,
    Permission,
    RBACEnforcer,
    MFAManager,
    SessionManager,
    XSSProtection,
    CSRFProtection,
    SecurityHeadersMiddleware,
    InputValidator,
    RateLimiter,
    APIKeyManager,
    SecurePostMessageHandler
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def redis_client():
    """Mock Redis client"""
    return fakeredis.FakeRedis(decode_responses=False)

@pytest.fixture
def security_config():
    """Security configuration"""
    return SecurityConfig()

@pytest.fixture
def jwt_manager(redis_client):
    """JWT manager instance"""
    return EnhancedJWTManager(redis_client)

@pytest.fixture
def rbac_enforcer():
    """RBAC enforcer instance"""
    return RBACEnforcer()

@pytest.fixture
def mfa_manager(redis_client):
    """MFA manager instance"""
    return MFAManager(redis_client)

@pytest.fixture
def session_manager(redis_client):
    """Session manager instance"""
    return SessionManager(redis_client)

@pytest.fixture
def rate_limiter(redis_client):
    """Rate limiter instance"""
    return RateLimiter(redis_client)

@pytest.fixture
def api_key_manager(redis_client):
    """API key manager instance"""
    return APIKeyManager(redis_client)

@pytest.fixture
def test_app():
    """Test FastAPI application"""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    return app

@pytest.fixture
def test_client(test_app):
    """Test client"""
    return TestClient(test_app)

# ============================================================================
# JWT TESTS
# ============================================================================

class TestEnhancedJWTManager:
    """Test JWT functionality with RSA keys"""
    
    def test_create_token_pair(self, jwt_manager):
        """Test creating access and refresh token pair"""
        tokens = jwt_manager.create_token_pair(
            user_id="user123",
            roles=["developer"],
            permissions=["server:view", "server:create"],
            metadata={"email": "test@example.com"}
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "Bearer"
        assert "expires_in" in tokens
    
    def test_verify_valid_token(self, jwt_manager):
        """Test verifying a valid token"""
        tokens = jwt_manager.create_token_pair(
            user_id="user123",
            roles=["admin"],
            permissions=["system:admin"]
        )
        
        payload = jwt_manager.verify_token(tokens["access_token"], "access")
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["roles"] == ["admin"]
        assert payload["permissions"] == ["system:admin"]
    
    def test_verify_expired_token(self, jwt_manager):
        """Test verifying an expired token"""
        # Create token with short expiry
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now(timezone.utc) - timedelta(hours=1)
            tokens = jwt_manager.create_token_pair(
                user_id="user123",
                roles=["viewer"],
                permissions=[]
            )
        
        payload = jwt_manager.verify_token(tokens["access_token"], "access")
        assert payload is None
    
    def test_revoke_token(self, jwt_manager, redis_client):
        """Test token revocation"""
        tokens = jwt_manager.create_token_pair(
            user_id="user123",
            roles=["developer"],
            permissions=[]
        )
        
        # Extract JTI from token
        payload = jwt_manager.verify_token(tokens["access_token"], "access")
        jti = payload["jti"]
        
        # Revoke token
        jwt_manager.revoke_token(jti)
        
        # Verify token is blacklisted
        assert redis_client.exists(f"jwt:blacklist:{jti}")
        
        # Token should no longer be valid
        payload = jwt_manager.verify_token(tokens["access_token"], "access")
        assert payload is None
    
    def test_key_rotation(self, jwt_manager, redis_client):
        """Test RSA key rotation"""
        # Get initial version
        initial_version = redis_client.get("jwt:current_version")
        
        # Rotate keys
        jwt_manager._rotate_keys()
        
        # Check new version
        new_version = redis_client.get("jwt:current_version")
        assert new_version != initial_version
        
        # Verify new keys exist
        assert redis_client.exists(f"jwt:private_key:{new_version.decode()}")
        assert redis_client.exists(f"jwt:public_key:{new_version.decode()}")

# ============================================================================
# RBAC TESTS
# ============================================================================

class TestRBACEnforcer:
    """Test role-based access control"""
    
    def test_check_permission_granted(self, rbac_enforcer):
        """Test permission check when granted"""
        has_permission = rbac_enforcer.check_permission(
            user_roles=["developer"],
            required_permission=Permission.SERVER_CREATE
        )
        assert has_permission is True
    
    def test_check_permission_denied(self, rbac_enforcer):
        """Test permission check when denied"""
        has_permission = rbac_enforcer.check_permission(
            user_roles=["viewer"],
            required_permission=Permission.SERVER_DELETE
        )
        assert has_permission is False
    
    def test_super_admin_bypass(self, rbac_enforcer):
        """Test super admin bypasses all permission checks"""
        has_permission = rbac_enforcer.check_permission(
            user_roles=["super_admin"],
            required_permission=Permission.SERVER_DELETE
        )
        assert has_permission is True
    
    def test_role_inheritance(self, rbac_enforcer):
        """Test role inheritance"""
        permissions = rbac_enforcer.get_effective_permissions(["security_admin"])
        
        # Should have both security_admin and inherited admin permissions
        assert Permission.SECURITY_MANAGE in permissions
        assert Permission.SERVER_DELETE in permissions  # From admin role
    
    def test_get_highest_priority_role(self, rbac_enforcer):
        """Test getting highest priority role"""
        highest = rbac_enforcer.get_highest_priority_role(
            ["viewer", "developer", "admin"]
        )
        assert highest == "admin"  # Admin has priority 20, lowest number

# ============================================================================
# MFA TESTS
# ============================================================================

class TestMFAManager:
    """Test multi-factor authentication"""
    
    def test_setup_totp(self, mfa_manager):
        """Test TOTP setup"""
        result = mfa_manager.setup_totp(
            user_id="user123",
            user_email="test@example.com"
        )
        
        assert "secret" in result
        assert "qr_code" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == SecurityConfig.MFA_BACKUP_CODES_COUNT
        assert result["qr_code"].startswith("data:image/png;base64,")
    
    def test_verify_valid_totp(self, mfa_manager):
        """Test verifying valid TOTP token"""
        import pyotp
        
        # Setup TOTP
        result = mfa_manager.setup_totp(
            user_id="user123",
            user_email="test@example.com"
        )
        
        # Generate valid token
        totp = pyotp.TOTP(result["secret"])
        token = totp.now()
        
        # Verify token
        is_valid = mfa_manager.verify_totp("user123", token)
        assert is_valid is True
    
    def test_verify_invalid_totp(self, mfa_manager):
        """Test verifying invalid TOTP token"""
        # Setup TOTP
        mfa_manager.setup_totp(
            user_id="user123",
            user_email="test@example.com"
        )
        
        # Verify invalid token
        is_valid = mfa_manager.verify_totp("user123", "000000")
        assert is_valid is False
    
    def test_backup_codes(self, mfa_manager):
        """Test backup code verification"""
        # Setup TOTP
        result = mfa_manager.setup_totp(
            user_id="user123",
            user_email="test@example.com"
        )
        
        backup_code = result["backup_codes"][0]
        
        # Verify backup code
        is_valid = mfa_manager.verify_backup_code("user123", backup_code)
        assert is_valid is True
        
        # Code should be consumed (one-time use)
        is_valid_again = mfa_manager.verify_backup_code("user123", backup_code)
        assert is_valid_again is False

# ============================================================================
# SESSION MANAGEMENT TESTS
# ============================================================================

class TestSessionManager:
    """Test session management"""
    
    def test_create_session(self, session_manager):
        """Test session creation"""
        session_id = session_manager.create_session(
            user_id="user123",
            user_data={"email": "test@example.com"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            roles=["developer"]
        )
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
    
    def test_validate_valid_session(self, session_manager):
        """Test validating a valid session"""
        session_id = session_manager.create_session(
            user_id="user123",
            user_data={"email": "test@example.com"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            roles=["admin"]
        )
        
        session = session_manager.validate_session(
            session_id=session_id,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert session is not None
        assert session["user_id"] == "user123"
        assert session["roles"] == ["admin"]
    
    def test_session_hijacking_detection(self, session_manager):
        """Test session hijacking detection"""
        session_id = session_manager.create_session(
            user_id="user123",
            user_data={"email": "test@example.com"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            roles=["developer"]
        )
        
        # Attempt validation from different IP
        session = session_manager.validate_session(
            session_id=session_id,
            ip_address="10.0.0.1",  # Different IP
            user_agent="Mozilla/5.0"
        )
        
        assert session is None  # Should be rejected
    
    def test_session_timeout(self, session_manager):
        """Test session idle timeout"""
        with patch('datetime.datetime') as mock_datetime:
            # Create session
            now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = now
            mock_datetime.fromisoformat = datetime.fromisoformat
            
            session_id = session_manager.create_session(
                user_id="user123",
                user_data={},
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                roles=["viewer"]
            )
            
            # Fast forward past idle timeout
            mock_datetime.now.return_value = now + timedelta(minutes=20)
            
            session = session_manager.validate_session(
                session_id=session_id,
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0"
            )
            
            assert session is None  # Should be expired
    
    def test_terminate_all_sessions(self, session_manager, redis_client):
        """Test terminating all user sessions"""
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_id = session_manager.create_session(
                user_id="user123",
                user_data={},
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                roles=["developer"]
            )
            session_ids.append(session_id)
        
        # Terminate all sessions
        session_manager.terminate_all_user_sessions("user123")
        
        # Verify all sessions are terminated
        for session_id in session_ids:
            assert not redis_client.exists(f"session:{session_id}")

# ============================================================================
# XSS PROTECTION TESTS
# ============================================================================

class TestXSSProtection:
    """Test XSS protection"""
    
    def test_sanitize_html(self):
        """Test HTML sanitization"""
        dangerous_html = '<script>alert("XSS")</script><p>Safe content</p>'
        sanitized = XSSProtection.sanitize_html(dangerous_html)
        
        assert '<script>' not in sanitized
        assert 'alert' not in sanitized
        assert '<p>Safe content</p>' in sanitized
    
    def test_escape_javascript(self):
        """Test JavaScript escaping"""
        dangerous_js = '"; alert("XSS"); //'
        escaped = XSSProtection.escape_javascript(dangerous_js)
        
        assert '"' not in escaped or '\\"' in escaped
        assert ';' not in escaped or '\\u003B' in escaped
    
    def test_validate_url(self):
        """Test URL validation"""
        # Valid URLs
        assert XSSProtection.validate_url("https://example.com")
        assert XSSProtection.validate_url("http://localhost:3000")
        
        # Invalid URLs
        assert not XSSProtection.validate_url("javascript:alert('XSS')")
        assert not XSSProtection.validate_url("data:text/html,<script>alert('XSS')</script>")
        assert not XSSProtection.validate_url("vbscript:msgbox('XSS')")
    
    def test_sanitize_json(self):
        """Test JSON sanitization"""
        dangerous_json = {
            "name": "<script>alert('XSS')</script>",
            "data": {
                "html": "<img src=x onerror=alert('XSS')>"
            },
            "items": ["<script>evil()</script>", "safe text"]
        }
        
        sanitized = XSSProtection.sanitize_json(dangerous_json)
        
        assert '<script>' not in json.dumps(sanitized)
        assert 'onerror' not in json.dumps(sanitized)

# ============================================================================
# CSRF PROTECTION TESTS
# ============================================================================

class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_generate_csrf_token(self):
        """Test CSRF token generation"""
        csrf = CSRFProtection()
        token = csrf.generate_csrf_token()
        
        assert token is not None
        assert len(token) >= 32
    
    def test_validate_matching_tokens(self):
        """Test validating matching CSRF tokens"""
        csrf = CSRFProtection()
        token = csrf.generate_csrf_token()
        
        is_valid = csrf.validate_csrf_token(
            token_header=token,
            token_cookie=token
        )
        
        assert is_valid is True
    
    def test_validate_mismatched_tokens(self):
        """Test validating mismatched CSRF tokens"""
        csrf = CSRFProtection()
        
        is_valid = csrf.validate_csrf_token(
            token_header="token1",
            token_cookie="token2"
        )
        
        assert is_valid is False
    
    def test_csrf_cookie_params(self):
        """Test CSRF cookie parameters"""
        csrf = CSRFProtection()
        params = csrf.get_csrf_cookie_params()
        
        assert params["httponly"] is False  # Must be readable by JS
        assert params["secure"] is True
        assert params["samesite"] == "strict"

# ============================================================================
# INPUT VALIDATION TESTS
# ============================================================================

class TestInputValidator:
    """Test input validation"""
    
    def test_validate_email(self):
        """Test email validation"""
        # Valid emails
        assert InputValidator.validate_email("user@example.com")
        assert InputValidator.validate_email("user.name+tag@example.co.uk")
        
        # Invalid emails
        assert not InputValidator.validate_email("invalid")
        assert not InputValidator.validate_email("@example.com")
        assert not InputValidator.validate_email("user@")
    
    def test_validate_username(self):
        """Test username validation"""
        # Valid usernames
        assert InputValidator.validate_username("user123")
        assert InputValidator.validate_username("user_name")
        assert InputValidator.validate_username("user-name")
        
        # Invalid usernames
        assert not InputValidator.validate_username("u")  # Too short
        assert not InputValidator.validate_username("user@name")  # Invalid char
        assert not InputValidator.validate_username("a" * 21)  # Too long
    
    def test_validate_password(self):
        """Test password validation"""
        # Strong password
        result = InputValidator.validate_password("SecureP@ssw0rd123!")
        assert result["valid"] is True
        assert result["strength"] > 80
        
        # Weak password
        result = InputValidator.validate_password("password")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        
        # Common password
        result = InputValidator.validate_password("admin")
        assert result["valid"] is False
        assert any("common" in err.lower() for err in result["errors"])
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Path traversal attempt
        sanitized = InputValidator.sanitize_filename("../../etc/passwd")
        assert "/" not in sanitized
        assert ".." not in sanitized
        
        # Special characters
        sanitized = InputValidator.sanitize_filename("file<script>.txt")
        assert "<" not in sanitized
        assert ">" not in sanitized
    
    def test_validate_path(self):
        """Test path validation"""
        # Valid paths
        assert InputValidator.validate_path("/home/user/file.txt")
        
        # Invalid paths
        assert not InputValidator.validate_path("/etc/passwd")
        assert not InputValidator.validate_path("../../../etc/passwd")
        assert not InputValidator.validate_path("/root/.ssh/id_rsa")
    
    def test_validate_ip_address(self):
        """Test IP address validation"""
        # Valid IPs
        assert InputValidator.validate_ip_address("192.168.1.1")
        assert InputValidator.validate_ip_address("::1")
        assert InputValidator.validate_ip_address("2001:db8::1")
        
        # Invalid IPs
        assert not InputValidator.validate_ip_address("256.256.256.256")
        assert not InputValidator.validate_ip_address("not.an.ip.address")

# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

class TestRateLimiter:
    """Test rate limiting"""
    
    def test_rate_limit_per_minute(self, rate_limiter):
        """Test per-minute rate limiting"""
        identifier = "user123"
        
        # Make requests up to limit
        for i in range(SecurityConfig.RATE_LIMIT_PER_MINUTE):
            result = rate_limiter.check_rate_limit(identifier, "minute")
            assert result["exceeded"] is False
        
        # Next request should exceed
        result = rate_limiter.check_rate_limit(identifier, "minute")
        assert result["exceeded"] is True
        assert result["remaining"] == 0
    
    def test_failed_login_tracking(self, rate_limiter):
        """Test failed login attempt tracking"""
        identifier = "user123"
        
        # Record failed attempts
        for i in range(SecurityConfig.MAX_FAILED_LOGIN_ATTEMPTS - 1):
            rate_limiter.record_failed_login(identifier)
            result = rate_limiter.check_failed_login(identifier)
            assert result["locked"] is False
        
        # Next attempt should trigger lock
        rate_limiter.record_failed_login(identifier)
        result = rate_limiter.check_failed_login(identifier)
        assert result["locked"] is True
        
        # Check account is locked
        assert rate_limiter.is_account_locked(identifier) is True
    
    def test_clear_failed_logins(self, rate_limiter):
        """Test clearing failed login attempts"""
        identifier = "user123"
        
        # Record some failed attempts
        for i in range(3):
            rate_limiter.record_failed_login(identifier)
        
        # Clear attempts
        rate_limiter.clear_failed_logins(identifier)
        
        # Check cleared
        result = rate_limiter.check_failed_login(identifier)
        assert result["attempts"] == 0
        assert result["locked"] is False

# ============================================================================
# API KEY MANAGEMENT TESTS
# ============================================================================

class TestAPIKeyManager:
    """Test API key management"""
    
    def test_create_api_key(self, api_key_manager):
        """Test API key creation"""
        result = api_key_manager.create_api_key(
            name="Test API Key",
            scopes=["read", "write"],
            expires_in_days=30
        )
        
        assert "key_id" in result
        assert "api_key" in result
        assert "expires_at" in result
        assert len(result["api_key"]) >= 32
    
    def test_validate_valid_api_key(self, api_key_manager):
        """Test validating a valid API key"""
        result = api_key_manager.create_api_key(
            name="Test Key",
            scopes=["read"],
            expires_in_days=30
        )
        
        key_data = api_key_manager.validate_api_key(result["api_key"])
        
        assert key_data is not None
        assert key_data["name"] == "Test Key"
        assert key_data["scopes"] == ["read"]
    
    def test_validate_invalid_api_key(self, api_key_manager):
        """Test validating an invalid API key"""
        key_data = api_key_manager.validate_api_key("invalid_key_12345")
        assert key_data is None
    
    def test_revoke_api_key(self, api_key_manager, redis_client):
        """Test API key revocation"""
        result = api_key_manager.create_api_key(
            name="Test Key",
            scopes=["read"],
            expires_in_days=30
        )
        
        # Revoke key
        api_key_manager.revoke_api_key(result["key_id"])
        
        # Key should no longer be valid
        key_data = api_key_manager.validate_api_key(result["api_key"])
        assert key_data is None
    
    def test_store_external_api_key(self, api_key_manager):
        """Test storing external API keys"""
        key_id = api_key_manager.store_external_api_key(
            service="kroger",
            key_name="Production API",
            api_key="test_api_key_123",
            api_secret="test_api_secret_456"
        )
        
        assert key_id is not None
        
        # Retrieve key
        credentials = api_key_manager.retrieve_external_api_key("kroger", key_id)
        assert credentials["api_key"] == "test_api_key_123"
        assert credentials["api_secret"] == "test_api_secret_456"

# ============================================================================
# SECURE POSTMESSAGE TESTS
# ============================================================================

class TestSecurePostMessageHandler:
    """Test secure PostMessage handling"""
    
    def test_validate_trusted_origin(self):
        """Test validating trusted origin"""
        handler = SecurePostMessageHandler(["https://trusted.com"])
        
        message = {
            "type": "test",
            "payload": "data",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "nonce": "unique123",
            "signature": "sig"
        }
        
        # Mock signature verification
        with patch.object(handler, '_verify_signature', return_value=True):
            is_valid = handler.validate_message(message, "https://trusted.com")
            assert is_valid is True
            
            is_invalid = handler.validate_message(message, "https://untrusted.com")
            assert is_invalid is False
    
    def test_replay_attack_prevention(self):
        """Test replay attack prevention"""
        handler = SecurePostMessageHandler(["https://trusted.com"])
        
        message = {
            "type": "test",
            "payload": "data",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "nonce": "unique123",
            "signature": "sig"
        }
        
        with patch.object(handler, '_verify_signature', return_value=True):
            # First message should be valid
            is_valid = handler.validate_message(message, "https://trusted.com")
            assert is_valid is True
            
            # Replay should be rejected
            is_valid = handler.validate_message(message, "https://trusted.com")
            assert is_valid is False
    
    def test_timestamp_validation(self):
        """Test message timestamp validation"""
        handler = SecurePostMessageHandler(["https://trusted.com"])
        
        # Old message
        old_message = {
            "type": "test",
            "payload": "data",
            "timestamp": int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000),
            "nonce": "unique123",
            "signature": "sig"
        }
        
        with patch.object(handler, '_verify_signature', return_value=True):
            is_valid = handler.validate_message(old_message, "https://trusted.com")
            assert is_valid is False

# ============================================================================
# SECURITY HEADERS TESTS
# ============================================================================

class TestSecurityHeaders:
    """Test security headers middleware"""
    
    @pytest.mark.asyncio
    async def test_security_headers_applied(self, test_client):
        """Test that security headers are applied"""
        response = test_client.get("/health")
        
        # Check critical security headers
        assert "Content-Security-Policy" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-XSS-Protection" in response.headers
        
    @pytest.mark.asyncio
    async def test_csp_nonce_generation(self, test_app):
        """Test CSP nonce generation"""
        @test_app.get("/test")
        async def test_endpoint(request):
            return {"nonce": request.state.csp_nonce}
        
        client = TestClient(test_app)
        response = client.get("/test")
        
        # Check nonce was generated
        data = response.json()
        assert "nonce" in data
        assert len(data["nonce"]) > 0
        
        # Check nonce is in CSP header
        csp = response.headers.get("Content-Security-Policy", "")
        assert f"nonce-{data['nonce']}" in csp

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSecurityIntegration:
    """Integration tests for security components"""
    
    @pytest.mark.asyncio
    async def test_full_authentication_flow(
        self,
        jwt_manager,
        session_manager,
        mfa_manager,
        rate_limiter
    ):
        """Test complete authentication flow"""
        user_id = "user123"
        ip_address = "192.168.1.1"
        user_agent = "Mozilla/5.0"
        
        # 1. Check rate limit
        rate_check = rate_limiter.check_rate_limit(f"login:{ip_address}", "minute")
        assert rate_check["exceeded"] is False
        
        # 2. Setup MFA
        mfa_result = mfa_manager.setup_totp(user_id, "user@example.com")
        
        # 3. Verify MFA
        import pyotp
        totp = pyotp.TOTP(mfa_result["secret"])
        mfa_valid = mfa_manager.verify_totp(user_id, totp.now())
        assert mfa_valid is True
        
        # 4. Create tokens
        tokens = jwt_manager.create_token_pair(
            user_id=user_id,
            roles=["developer"],
            permissions=["server:view", "server:create"]
        )
        
        # 5. Create session
        session_id = session_manager.create_session(
            user_id=user_id,
            user_data={"email": "user@example.com"},
            ip_address=ip_address,
            user_agent=user_agent,
            roles=["developer"]
        )
        
        # 6. Validate session
        session = session_manager.validate_session(
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        assert session is not None
        assert session["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_api_security_chain(
        self,
        api_key_manager,
        rate_limiter,
        rbac_enforcer
    ):
        """Test API security chain"""
        # 1. Create API key
        api_key_result = api_key_manager.create_api_key(
            name="Integration Test",
            scopes=["server:view", "server:execute"],
            expires_in_days=1
        )
        
        # 2. Validate API key
        key_data = api_key_manager.validate_api_key(api_key_result["api_key"])
        assert key_data is not None
        
        # 3. Check rate limit
        rate_check = rate_limiter.check_rate_limit(
            f"api:{api_key_result['key_id']}",
            "minute"
        )
        assert rate_check["exceeded"] is False
        
        # 4. Check permissions
        has_permission = rbac_enforcer.check_permission(
            user_roles=["developer"],
            required_permission=Permission.SERVER_EXECUTE
        )
        assert has_permission is True

# ============================================================================
# PENETRATION TEST SIMULATIONS
# ============================================================================

class TestPenetrationSimulations:
    """Simulated penetration testing"""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM passwords --"
        ]
        
        for payload in dangerous_inputs:
            # Input should be sanitized
            sanitized = XSSProtection.sanitize_html(payload)
            assert "DROP TABLE" not in sanitized
            assert "UNION SELECT" not in sanitized
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            sanitized = XSSProtection.sanitize_html(payload)
            assert "<script>" not in sanitized
            assert "onerror" not in sanitized
            assert "javascript:" not in sanitized
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        traversal_attempts = [
            "../../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for attempt in traversal_attempts:
            is_valid = InputValidator.validate_path(attempt)
            assert is_valid is False
    
    def test_brute_force_protection(self, rate_limiter):
        """Test brute force attack protection"""
        attacker_ip = "10.0.0.1"
        
        # Simulate rapid login attempts
        for i in range(10):
            rate_limiter.record_failed_login(attacker_ip)
        
        # Check if account is locked
        result = rate_limiter.check_failed_login(attacker_ip)
        assert result["locked"] is True
        assert rate_limiter.is_account_locked(attacker_ip) is True

# ============================================================================
# COMPLIANCE TESTS
# ============================================================================

class TestCompliance:
    """Test compliance with security standards"""
    
    def test_password_policy_compliance(self):
        """Test password policy meets standards"""
        config = SecurityConfig()
        
        # NIST SP 800-63B compliance
        assert config.MIN_PASSWORD_LENGTH >= 8
        assert config.PASSWORD_HISTORY_COUNT >= 3
        
        # Test password complexity
        strong_password = "MyS3cur3P@ssw0rd!"
        result = InputValidator.validate_password(strong_password)
        assert result["valid"] is True
        assert result["strength"] >= 70
    
    def test_session_management_compliance(self):
        """Test session management compliance"""
        config = SecurityConfig()
        
        # OWASP recommendations
        assert config.SESSION_TIMEOUT_MINUTES <= 30
        assert config.SESSION_ABSOLUTE_TIMEOUT_HOURS <= 12
        assert config.SESSION_IDLE_TIMEOUT_MINUTES <= 20
    
    def test_encryption_compliance(self):
        """Test encryption standards compliance"""
        config = SecurityConfig()
        
        # Encryption strength
        assert config.ENCRYPTION_KEY_LENGTH >= 32
        assert config.PBKDF2_ITERATIONS >= 100000
        
        # JWT using RSA
        assert SecurityConfig.JWT_ALGORITHM == "RS256"
    
    def test_audit_logging_compliance(self):
        """Test audit logging compliance"""
        config = SecurityConfig()
        
        # Retention requirements
        assert config.AUDIT_LOG_RETENTION_DAYS >= 2555  # 7 years for SOC2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.app.core.enhanced_security"])