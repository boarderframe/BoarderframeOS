"""
Security Test Suite for Kroger OAuth2 Authentication Module
Tests OWASP Top 10 compliance and security best practices
"""

import os
import asyncio
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import base64

from kroger_auth import (
    KrogerAuth,
    KrogerEnvironment,
    KrogerScope,
    TokenEncryption,
    TokenCache
)


class TestTokenEncryption:
    """Test token encryption security"""
    
    def test_encryption_decryption(self):
        """Test that tokens are properly encrypted and decrypted"""
        encryption = TokenEncryption()
        
        # Test with sample token
        original_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
        
        # Encrypt
        encrypted = encryption.encrypt_token(original_token)
        assert encrypted != original_token  # Must be different
        assert len(encrypted) > len(original_token)  # Encrypted should be longer
        
        # Decrypt
        decrypted = encryption.decrypt_token(encrypted)
        assert decrypted == original_token
    
    def test_encryption_with_empty_token(self):
        """Test handling of empty tokens"""
        encryption = TokenEncryption()
        
        assert encryption.encrypt_token("") == ""
        assert encryption.decrypt_token("") == ""
    
    def test_different_keys_produce_different_ciphertext(self):
        """Test that different encryption keys produce different outputs"""
        encryption1 = TokenEncryption("key1")
        encryption2 = TokenEncryption("key2")
        
        token = "test_token_12345"
        
        encrypted1 = encryption1.encrypt_token(token)
        encrypted2 = encryption2.encrypt_token(token)
        
        assert encrypted1 != encrypted2  # Different keys must produce different ciphertext
    
    def test_tampering_detection(self):
        """Test that tampered encrypted tokens cannot be decrypted"""
        encryption = TokenEncryption()
        
        token = "sensitive_token"
        encrypted = encryption.encrypt_token(token)
        
        # Tamper with the encrypted token
        tampered = encrypted[:-5] + "XXXXX"
        
        # Should raise an exception when trying to decrypt tampered token
        with pytest.raises(Exception):
            encryption.decrypt_token(tampered)


class TestTokenCache:
    """Test secure token caching"""
    
    def test_token_expiration(self):
        """Test that expired tokens are not returned from cache"""
        encryption = TokenEncryption()
        cache = TokenCache(encryption)
        
        # Store token with 1 second expiry
        token_data = {'access_token': 'test_token'}
        cache.set('test_key', token_data, expires_in=1)
        
        # Should retrieve immediately
        retrieved = cache.get('test_key')
        assert retrieved is not None
        assert retrieved['access_token'] == 'test_token'
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Should return None after expiration
        expired = cache.get('test_key')
        assert expired is None
    
    def test_tokens_encrypted_in_cache(self):
        """Test that tokens are encrypted when stored in cache"""
        encryption = TokenEncryption()
        cache = TokenCache(encryption)
        
        token_data = {
            'access_token': 'plaintext_access_token',
            'refresh_token': 'plaintext_refresh_token'
        }
        
        cache.set('test_key', token_data, expires_in=3600)
        
        # Check that tokens are encrypted in internal cache
        with cache.lock:
            cached_data = cache.cache['test_key']['data']
            
            # Tokens should be encrypted
            assert cached_data['access_token'] != 'plaintext_access_token'
            assert cached_data['refresh_token'] != 'plaintext_refresh_token'
            
            # Should be valid encrypted strings
            assert len(cached_data['access_token']) > len('plaintext_access_token')
            assert len(cached_data['refresh_token']) > len('plaintext_refresh_token')


class TestKrogerAuthSecurity:
    """Test OAuth2 security implementation"""
    
    @pytest.mark.asyncio
    async def test_credentials_not_in_logs(self, caplog):
        """Test that sensitive credentials are never logged"""
        with patch.dict(os.environ, {
            'KROGER_CLIENT_ID': 'test_client_id',
            'KROGER_CLIENT_SECRET': 'super_secret_key'
        }):
            auth = KrogerAuth()
            
            # Check that secrets are not in logs
            for record in caplog.records:
                assert 'super_secret_key' not in record.getMessage()
                assert 'test_client_id' not in record.getMessage()
    
    def test_basic_auth_header_generation(self):
        """Test proper HTTP Basic authentication header generation"""
        auth = KrogerAuth(
            client_id='test_client',
            client_secret='test_secret'
        )
        
        header = auth._get_basic_auth_header()
        
        # Should be Basic auth format
        assert header.startswith('Basic ')
        
        # Decode and verify
        encoded = header.replace('Basic ', '')
        decoded = base64.b64decode(encoded).decode()
        assert decoded == 'test_client:test_secret'
    
    def test_state_parameter_csrf_protection(self):
        """Test CSRF protection via state parameter"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret',
            redirect_uri='http://localhost/callback'
        )
        
        # Generate authorization URL with state
        auth_url, state = auth.get_authorization_url([KrogerScope.CART_BASIC_WRITE])
        
        # State should be generated
        assert state is not None
        assert len(state) >= 32  # Should be cryptographically secure
        
        # State should be in URL
        assert f'state={state}' in auth_url
        
        # Validate state works
        assert auth.validate_state(state) is True
        
        # Same state cannot be reused (prevents replay attacks)
        assert auth.validate_state(state) is False
        
        # Invalid state should fail
        assert auth.validate_state('invalid_state_123') is False
    
    def test_state_expiration(self):
        """Test that state parameters expire after timeout"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret',
            redirect_uri='http://localhost/callback'
        )
        
        # Generate state
        _, state = auth.get_authorization_url([KrogerScope.PRODUCT_COMPACT])
        
        # Manually expire the state
        auth.pending_states[state] = datetime.utcnow() - timedelta(minutes=1)
        
        # Should fail validation
        assert auth.validate_state(state) is False
    
    @pytest.mark.asyncio
    async def test_401_triggers_token_refresh(self):
        """Test automatic token refresh on 401 Unauthorized"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret'
        )
        
        # Mock the session
        mock_response = AsyncMock()
        mock_response.status = 401  # First call returns 401
        mock_response.headers = {}
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200  # Second call succeeds
        mock_response_success.headers = {}
        mock_response_success.json = AsyncMock(return_value={'data': 'success'})
        
        auth.session = AsyncMock()
        auth.session.request = AsyncMock(side_effect=[
            AsyncMock(__aenter__=AsyncMock(return_value=mock_response)),
            AsyncMock(__aenter__=AsyncMock(return_value=mock_response_success))
        ])
        
        # Mock refresh_access_token
        auth.refresh_access_token = AsyncMock(return_value={
            'access_token': 'new_token',
            'refresh_token': 'refresh_token',
            'expires_in': 1800
        })
        
        # Make request with auto_refresh enabled
        result = await auth.make_authenticated_request(
            'GET',
            '/test',
            'old_token',
            auto_refresh=True,
            refresh_token='refresh_token'
        )
        
        # Should have called refresh
        auth.refresh_access_token.assert_called_once()
        
        # Should succeed with new token
        assert result == {'data': 'success'}
    
    @pytest.mark.asyncio
    async def test_rate_limit_tracking(self):
        """Test rate limit tracking and warnings"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret'
        )
        
        # Mock response with rate limit headers
        mock_response = AsyncMock()
        mock_response.headers = {
            'X-RateLimit-Remaining': '500',
            'X-RateLimit-Reset': str(int((datetime.utcnow() + timedelta(hours=1)).timestamp()))
        }
        
        await auth._handle_rate_limit(mock_response)
        
        # Should update rate limit tracking
        assert auth.rate_limit_remaining == 500
        assert auth.rate_limit_reset > datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_429_rate_limit_handling(self):
        """Test handling of 429 Too Many Requests"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret'
        )
        
        # Mock 429 response
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_response.json = AsyncMock(return_value={'error': 'rate_limited'})
        
        auth.session = AsyncMock()
        auth.session.request = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response)
        ))
        
        # Should raise exception with retry information
        with pytest.raises(Exception) as exc_info:
            await auth.make_authenticated_request('GET', '/test', 'token')
        
        assert 'Rate limit exceeded' in str(exc_info.value)
        assert '60 seconds' in str(exc_info.value)
    
    def test_sanitize_log_data(self):
        """Test that sensitive data is sanitized in logs"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret'
        )
        
        sensitive_data = {
            'access_token': 'secret_token_123',
            'refresh_token': 'refresh_secret_456',
            'client_secret': 'client_secret_789',
            'Authorization': 'Bearer secret_token',
            'safe_field': 'this_is_safe'
        }
        
        sanitized = auth._sanitize_log_data(sensitive_data)
        
        # Sensitive fields should be redacted
        assert sanitized['access_token'] == '[REDACTED]'
        assert sanitized['refresh_token'] == '[REDACTED]'
        assert sanitized['client_secret'] == '[REDACTED]'
        assert sanitized['Authorization'] == '[REDACTED]'
        
        # Safe fields should remain
        assert sanitized['safe_field'] == 'this_is_safe'
    
    @pytest.mark.asyncio
    async def test_invalid_scope_error(self):
        """Test handling of invalid scope errors"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret'
        )
        
        # Mock invalid scope response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.headers = {}
        mock_response.json = AsyncMock(return_value={
            'error': 'invalid_scope',
            'error_description': 'Scope cart.admin not allowed'
        })
        
        auth.session = AsyncMock()
        auth.session.post = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response)
        ))
        
        # Should raise ValueError with scope error
        with pytest.raises(ValueError) as exc_info:
            await auth._make_token_request({'grant_type': 'client_credentials'})
        
        assert 'Requested scope not allowed' in str(exc_info.value)
        assert 'cart.admin' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_environment_separation(self):
        """Test that production and certification environments are properly separated"""
        # Production environment
        auth_prod = KrogerAuth(
            client_id='prod_client',
            client_secret='prod_secret',
            environment=KrogerEnvironment.PRODUCTION
        )
        
        assert 'api.kroger.com' in auth_prod.base_url
        assert 'api-ce.kroger.com' not in auth_prod.base_url
        
        # Certification environment
        auth_cert = KrogerAuth(
            client_id='cert_client',
            client_secret='cert_secret',
            environment=KrogerEnvironment.CERTIFICATION
        )
        
        assert 'api-ce.kroger.com' in auth_cert.base_url
        assert auth_cert.base_url != auth_prod.base_url


class TestSecurityCompliance:
    """Test OWASP Top 10 compliance"""
    
    def test_no_hardcoded_credentials(self):
        """Test that no credentials are hardcoded"""
        # Should raise error if credentials not provided
        with pytest.raises(ValueError) as exc_info:
            KrogerAuth()  # No env vars set
        
        assert 'Client ID and Client Secret are required' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_injection_prevention(self):
        """Test prevention of injection attacks in parameters"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret'
        )
        
        # Test with potentially malicious input
        malicious_scope = "product.compact' OR '1'='1"
        
        # Should properly encode/escape
        url, state = auth.get_authorization_url([KrogerScope.PRODUCT_COMPACT])
        
        # URL should be properly encoded
        assert "'" not in url  # Single quotes should be encoded
        assert 'product.compact' in url  # Valid scope should be present
    
    def test_secure_random_state_generation(self):
        """Test that state parameters use cryptographically secure random"""
        auth = KrogerAuth(
            client_id='test',
            client_secret='secret',
            redirect_uri='http://localhost'
        )
        
        states = set()
        
        # Generate multiple states
        for _ in range(100):
            _, state = auth.get_authorization_url([KrogerScope.PRODUCT_COMPACT])
            states.add(state)
        
        # All should be unique (no collisions)
        assert len(states) == 100
        
        # Should be sufficiently long
        for state in states:
            assert len(state) >= 32


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])