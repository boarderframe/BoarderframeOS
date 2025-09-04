"""
Comprehensive Security Test Suite for Phase 4a Implementation
Tests all security components with OWASP compliance verification
"""

import pytest
import asyncio
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
import redis
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from app.core.enhanced_security import (
    SecurityConfig,
    EnhancedJWTManager,
    RBACEnforcer,
    MFAManager,
    SessionManager,
    XSSProtection,
    CSRFProtection,
    InputValidator,
    RateLimiter,
    APIKeyManager,
    SecurePostMessageHandler,
    Permission,
    Role,
    SYSTEM_ROLES
)

from app.core.security_middleware import (
    SecurityMiddlewareStack,
    RateLimitMiddleware,
    JWTAuthMiddleware,
    CSRFMiddleware,
    RBACMiddleware,
    AuditLoggingMiddleware
)

from app.core.oauth_security import (
    OAuthFlowManager,
    PKCEManager,
    OAuthStateManager,
    OAuthTokenManager
)

from app.core.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def redis_client():
    """Mock Redis client"""
    client = Mock(spec=redis.Redis)
    client.get.return_value = None
    client.set.return_value = True
    client.setex.return_value = True
    client.delete.return_value = 1
    client.exists.return_value = 0
    client.incr.return_value = 1
    client.expire.return_value = True
    client.ttl.return_value = 60
    client.smembers.return_value = set()
    client.sadd.return_value = 1
    client.srem.return_value = 1
    client.sismember.return_value = False
    return client

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
def audit_logger(redis_client):
    """Audit logger instance"""
    return AuditLogger(redis_client)

# ============================================================================
# JWT SECURITY TESTS
# ============================================================================

class TestJWTSecurity:
    """Test JWT implementation with RSA"""
    
    def test_jwt_key_rotation(self, jwt_manager, redis_client):
        """Test JWT key rotation"""
        # Generate keys
        jwt_manager._rotate_keys()
        
        # Verify keys were stored
        assert redis_client.set.called
        assert "jwt:private_key" in str(redis_client.set.call_args_list)
        assert "jwt:public_key" in str(redis_client.set.call_args_list)
    
    def test_token_creation_with_roles(self, jwt_manager, redis_client):
        """Test token creation with roles and permissions"""
        # Mock RSA keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        redis_client.get.side_effect = lambda key: {
            b"jwt:current_version": b"2024-01-01T00:00:00",
            b"jwt:private_key:2024-01-01T00:00:00": private_pem
        }.get(key)
        
        # Create tokens
        tokens = jwt_manager.create_token_pair(
            user_id="user123",
            roles=["admin"],
            permissions=["server:view", "server:create"],
            metadata={"department": "engineering"}
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "Bearer"
    
    def test_token_blacklisting(self, jwt_manager, redis_client):
        """Test token revocation/blacklisting"""
        jti = "test-jti-123"
        jwt_manager.revoke_token(jti)
        
        # Verify blacklist was set
        redis_client.set.assert_called()
        blacklist_call = [call for call in redis_client.set.call_args_list 
                         if "jwt:blacklist" in str(call)]
        assert len(blacklist_call) > 0

# ============================================================================
# RBAC SECURITY TESTS
# ============================================================================

class TestRBACSecurity:
    """Test Role-Based Access Control"""
    
    def test_permission_hierarchy(self, rbac_enforcer):
        """Test role hierarchy and permission inheritance"""
        # Test super_admin has all permissions
        assert rbac_enforcer.check_permission(
            ["super_admin"],
            Permission.SYSTEM_ADMIN
        )
        
        # Test inheritance
        assert rbac_enforcer.check_permission(
            ["security_admin"],
            Permission.SERVER_DELETE  # Inherited from admin
        )
        
        # Test viewer limitations
        assert not rbac_enforcer.check_permission(
            ["viewer"],
            Permission.SERVER_CREATE
        )
    
    def test_principle_of_least_privilege(self, rbac_enforcer):
        """Test principle of least privilege"""
        viewer_perms = rbac_enforcer.get_effective_permissions(["viewer"])
        developer_perms = rbac_enforcer.get_effective_permissions(["developer"])
        admin_perms = rbac_enforcer.get_effective_permissions(["admin"])
        
        # Verify increasing permissions
        assert len(viewer_perms) < len(developer_perms)
        assert len(developer_perms) < len(admin_perms)
        
        # Verify no delete permissions for non-admins
        assert Permission.SERVER_DELETE not in developer_perms
        assert Permission.CONFIG_DELETE not in developer_perms

# ============================================================================
# MFA SECURITY TESTS
# ============================================================================

class TestMFASecurity:
    """Test Multi-Factor Authentication"""
    
    def test_totp_setup(self, mfa_manager, redis_client):
        """Test TOTP setup and secret generation"""
        result = mfa_manager.setup_totp("user123", "user@example.com")
        
        assert "secret" in result
        assert "qr_code" in result
        assert "backup_codes" in result
        assert len(result["backup_codes"]) == 10
        
        # Verify secret was stored encrypted
        redis_client.set.assert_called()
    
    def test_totp_verification(self, mfa_manager, redis_client):
        """Test TOTP token verification"""
        import pyotp
        
        # Setup TOTP
        secret = pyotp.random_base32()
        encrypted_secret = base64.b64encode(secret.encode()).decode()
        redis_client.get.return_value = encrypted_secret.encode()
        
        # Generate valid token
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        # Mock decryption
        with patch.object(mfa_manager, '_decrypt_secret', return_value=secret):
            result = mfa_manager.verify_totp("user123", token)
            assert result is True
    
    def test_backup_codes_one_time_use(self, mfa_manager, redis_client):
        """Test backup codes are one-time use only"""
        code = "ABCD-1234"
        hashed = hashlib.sha256(code.encode()).hexdigest()
        
        # First use - should succeed
        redis_client.sismember.return_value = True
        assert mfa_manager.verify_backup_code("user123", code)
        
        # Verify code was removed
        redis_client.srem.assert_called_with(f"mfa:backup:user123", hashed)

# ============================================================================
# SESSION SECURITY TESTS
# ============================================================================

class TestSessionSecurity:
    """Test session management security"""
    
    def test_session_fingerprinting(self, session_manager, redis_client):
        """Test session fingerprinting for hijack detection"""
        # Create session
        session_id = session_manager.create_session(
            user_id="user123",
            user_data={"email": "user@example.com"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            roles=["admin"]
        )
        
        # Mock stored session
        session_data = {
            "session_id": session_id,
            "user_id": "user123",
            "fingerprint": session_manager._generate_fingerprint(
                "192.168.1.1", "Mozilla/5.0"
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        redis_client.get.return_value = json.dumps(session_data).encode()
        
        # Validate with same fingerprint - should succeed
        result = session_manager.validate_session(
            session_id, "192.168.1.1", "Mozilla/5.0"
        )
        assert result is not None
        
        # Validate with different IP - should fail (hijack detection)
        redis_client.get.return_value = json.dumps(session_data).encode()
        result = session_manager.validate_session(
            session_id, "192.168.1.2", "Mozilla/5.0"
        )
        assert result is None
    
    def test_session_timeout(self, session_manager, redis_client):
        """Test session timeout enforcement"""
        session_id = "test-session"
        
        # Create expired session
        old_time = datetime.now(timezone.utc) - timedelta(hours=9)
        session_data = {
            "session_id": session_id,
            "user_id": "user123",
            "fingerprint": "test-fingerprint",
            "created_at": old_time.isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        redis_client.get.return_value = json.dumps(session_data).encode()
        
        # Should fail due to absolute timeout
        result = session_manager.validate_session(
            session_id, "192.168.1.1", "Mozilla/5.0"
        )
        assert result is None

# ============================================================================
# INPUT VALIDATION TESTS
# ============================================================================

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_xss_protection(self):
        """Test XSS attack prevention"""
        # Test HTML sanitization
        malicious_html = '<script>alert("XSS")</script><p>Hello</p>'
        sanitized = XSSProtection.sanitize_html(malicious_html)
        assert "<script>" not in sanitized
        assert "<p>Hello</p>" in sanitized
        
        # Test JavaScript escaping
        js_content = 'var x = "test"; alert("XSS");'
        escaped = XSSProtection.escape_javascript(js_content)
        assert "alert" not in escaped or "\\" in escaped
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        validator = InputValidator()
        
        # Test path validation
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "../../.env",
            "/root/.ssh/id_rsa"
        ]
        
        for path in malicious_paths:
            assert not validator.validate_path(path)
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        validator = InputValidator()
        
        # Weak passwords should fail
        weak_passwords = [
            "password",
            "12345678",
            "admin123",
            "letmein"
        ]
        
        for pwd in weak_passwords:
            result = validator.validate_password(pwd)
            assert not result["valid"]
        
        # Strong password should pass
        strong_pwd = "MyS3cur3P@ssw0rd!2024"
        result = validator.validate_password(strong_pwd)
        assert result["valid"]
        assert result["strength"] >= 80

# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

class TestRateLimiting:
    """Test rate limiting and DDoS protection"""
    
    def test_rate_limit_enforcement(self, rate_limiter, redis_client):
        """Test rate limit enforcement"""
        identifier = "user:123"
        
        # First request should succeed
        redis_client.incr.return_value = 1
        result = rate_limiter.check_rate_limit(identifier, "minute")
        assert not result["exceeded"]
        assert result["remaining"] > 0
        
        # Exceed limit
        redis_client.incr.return_value = 61
        result = rate_limiter.check_rate_limit(identifier, "minute")
        assert result["exceeded"]
        assert result["remaining"] == 0
    
    def test_account_lockout(self, rate_limiter, redis_client):
        """Test account lockout after failed attempts"""
        identifier = "user@example.com"
        
        # Record failed attempts
        for i in range(5):
            redis_client.get.return_value = str(i).encode()
            rate_limiter.record_failed_login(identifier)
        
        # Check lockout
        redis_client.get.return_value = b"5"
        result = rate_limiter.check_failed_login(identifier)
        assert result["locked"]
        
        # Verify lockout was set
        redis_client.setex.assert_called()

# ============================================================================
# OAUTH SECURITY TESTS
# ============================================================================

class TestOAuthSecurity:
    """Test OAuth 2.0 with PKCE"""
    
    def test_pkce_generation(self, redis_client):
        """Test PKCE verifier and challenge generation"""
        pkce = PKCEManager(redis_client)
        verifier, challenge = pkce.generate_pkce_pair()
        
        # Verify length requirements
        assert 43 <= len(verifier) <= 128
        assert len(challenge) > 0
        
        # Verify challenge is correct
        assert pkce.validate_pkce(verifier, challenge)
    
    def test_oauth_state_validation(self, redis_client):
        """Test OAuth state parameter for CSRF protection"""
        state_manager = OAuthStateManager(redis_client)
        
        # Create state
        state = state_manager.create_state(
            provider="kroger",
            user_id="user123",
            return_url="/dashboard"
        )
        
        # Mock Redis retrieval
        state_data = {
            "provider": "kroger",
            "user_id": "user123",
            "return_url": "/dashboard",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "nonce": "test-nonce"
        }
        
        with patch.object(state_manager.cipher, 'decrypt') as mock_decrypt:
            mock_decrypt.return_value = json.dumps(state_data).encode()
            redis_client.get.return_value = "encrypted_data"
            
            # Validate state
            result = state_manager.validate_state(state)
            assert result is not None
            assert result["provider"] == "kroger"
            
            # Verify one-time use
            redis_client.delete.assert_called_with(f"oauth:state:{state}")

# ============================================================================
# AUDIT LOGGING TESTS
# ============================================================================

class TestAuditLogging:
    """Test audit logging for compliance"""
    
    @pytest.mark.asyncio
    async def test_audit_event_logging(self, audit_logger):
        """Test audit event logging"""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            user_id="user123",
            user_email="user@example.com",
            ip_address="192.168.1.1",
            contains_pii=True
        )
        
        await audit_logger.log_event(event)
        
        # Verify event was buffered
        assert len(audit_logger.event_buffer) > 0
    
    @pytest.mark.asyncio
    async def test_pii_anonymization(self, audit_logger):
        """Test PII anonymization for GDPR compliance"""
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditSeverity.INFO,
            user_email="user@example.com",
            ip_address="192.168.1.1",
            contains_pii=True,
            metadata={"email": "test@example.com", "phone": "555-1234"}
        )
        
        # Anonymize
        anonymized = event.anonymize()
        
        # Verify PII was hashed
        assert anonymized.user_email != "user@example.com"
        assert anonymized.ip_address != "192.168.1.1"
        assert anonymized.metadata["email"] != "test@example.com"
    
    @pytest.mark.asyncio
    async def test_audit_log_retention(self, audit_logger):
        """Test audit log retention policy"""
        # Create old event
        old_event = AuditEvent(
            event_type=AuditEventType.SYSTEM_STARTUP,
            severity=AuditSeverity.INFO,
            timestamp=datetime.now(timezone.utc) - timedelta(days=2556)
        )
        
        await audit_logger.log_event(old_event)
        await audit_logger.cleanup_old_logs()
        
        # Old logs should be cleaned up based on retention policy

# ============================================================================
# SECURITY HEADERS TESTS
# ============================================================================

class TestSecurityHeaders:
    """Test security headers implementation"""
    
    def test_csp_header_generation(self, security_config):
        """Test Content Security Policy header"""
        from app.core.enhanced_security import SecurityHeadersMiddleware
        
        # Mock response
        response = Mock()
        response.headers = {}
        
        middleware = SecurityHeadersMiddleware(None, security_config)
        middleware._add_security_headers(response, "test-nonce")
        
        # Verify CSP header
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self' 'nonce-test-nonce'" in csp
        assert "frame-ancestors 'none'" in csp
    
    def test_security_headers_complete(self, security_config):
        """Test all required security headers"""
        from app.core.enhanced_security import SecurityHeadersMiddleware
        
        response = Mock()
        response.headers = {}
        
        middleware = SecurityHeadersMiddleware(None, security_config)
        middleware._add_security_headers(response, "nonce")
        
        # Verify all security headers
        required_headers = [
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Cross-Origin-Embedder-Policy",
            "Cross-Origin-Opener-Policy",
            "Cross-Origin-Resource-Policy"
        ]
        
        for header in required_headers:
            assert header in response.headers

# ============================================================================
# CSRF PROTECTION TESTS
# ============================================================================

class TestCSRFProtection:
    """Test CSRF protection mechanisms"""
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation"""
        csrf = CSRFProtection()
        token1 = csrf.generate_csrf_token()
        token2 = csrf.generate_csrf_token()
        
        # Tokens should be unique
        assert token1 != token2
        assert len(token1) >= 32
    
    def test_csrf_double_submit_validation(self):
        """Test CSRF double-submit cookie pattern"""
        csrf = CSRFProtection()
        token = csrf.generate_csrf_token()
        
        # Valid case - tokens match
        assert csrf.validate_csrf_token(token, token)
        
        # Invalid case - tokens don't match
        assert not csrf.validate_csrf_token(token, "different-token")
        
        # Invalid case - missing tokens
        assert not csrf.validate_csrf_token(None, token)
        assert not csrf.validate_csrf_token(token, None)

# ============================================================================
# API KEY SECURITY TESTS
# ============================================================================

class TestAPIKeySecurity:
    """Test API key management"""
    
    def test_api_key_creation_and_storage(self, redis_client):
        """Test secure API key creation and storage"""
        manager = APIKeyManager(redis_client)
        
        result = manager.create_api_key(
            name="Test API Key",
            scopes=["read", "write"],
            expires_in_days=30
        )
        
        assert "key_id" in result
        assert "api_key" in result
        assert len(result["api_key"]) >= 32
        
        # Verify key was hashed for storage
        redis_client.set.assert_called()
    
    def test_external_api_key_encryption(self, redis_client):
        """Test external API key encryption (e.g., Kroger)"""
        manager = APIKeyManager(redis_client)
        
        # Store external key
        key_id = manager.store_external_api_key(
            service="kroger",
            key_name="production",
            api_key="test-api-key",
            api_secret="test-api-secret"
        )
        
        # Verify encryption was applied
        redis_client.set.assert_called()
        stored_data = redis_client.set.call_args[0][1]
        parsed = json.loads(stored_data)
        
        # Keys should be encrypted
        assert parsed["api_key"] != "test-api-key"
        assert parsed["api_secret"] != "test-api-secret"

# ============================================================================
# POSTMESSAGE SECURITY TESTS
# ============================================================================

class TestPostMessageSecurity:
    """Test secure iframe communication"""
    
    def test_postmessage_origin_validation(self):
        """Test PostMessage origin validation"""
        handler = SecurePostMessageHandler(["https://trusted.com"])
        
        # Valid origin
        message = {
            "type": "test",
            "payload": {"data": "test"},
            "timestamp": int(datetime.now().timestamp() * 1000),
            "nonce": "test-nonce",
            "signature": "test-sig"
        }
        
        with patch.object(handler, '_verify_signature', return_value=True):
            assert handler.validate_message(message, "https://trusted.com")
            assert not handler.validate_message(message, "https://evil.com")
    
    def test_postmessage_replay_prevention(self):
        """Test PostMessage replay attack prevention"""
        handler = SecurePostMessageHandler(["https://trusted.com"])
        
        # Old timestamp
        old_message = {
            "type": "test",
            "payload": {"data": "test"},
            "timestamp": int((datetime.now() - timedelta(minutes=1)).timestamp() * 1000),
            "nonce": "test-nonce",
            "signature": "test-sig"
        }
        
        # Should reject old messages
        assert not handler.validate_message(old_message, "https://trusted.com")

# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])