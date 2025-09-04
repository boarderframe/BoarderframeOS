"""
Kroger OAuth2 Authentication Module
Secure implementation for Kroger API authentication with OAuth2 support

Security Features:
- Client Credentials Grant for server-to-server authentication
- Authorization Code Grant for user-specific operations  
- Automatic token refresh with retry logic
- Secure credential storage via environment variables
- Token encryption at rest using Fernet
- Rate limit compliance with exponential backoff
- Comprehensive error handling for OAuth-specific scenarios
"""

import os
import json
import time
import base64
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from urllib.parse import urlencode, parse_qs, urlparse
from threading import Lock
import hashlib

import aiohttp
import asyncio
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

# Configure logging with security considerations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security configuration
BLOCKED_LOG_FIELDS = ['access_token', 'refresh_token', 'client_secret', 'Authorization']


class KrogerEnvironment(Enum):
    """Kroger API environments"""
    PRODUCTION = "https://api.kroger.com/v1"
    CERTIFICATION = "https://api-ce.kroger.com/v1"


class KrogerScope(Enum):
    """Available OAuth2 scopes for Kroger API"""
    PRODUCT_COMPACT = "product.compact"  # Read-only access to products and locations
    CART_BASIC_WRITE = "cart.basic:write"  # Read/write access to cart
    PROFILE_COMPACT = "profile.compact"  # Read access to user profile/loyalty


class TokenEncryption:
    """Handles encryption and decryption of OAuth tokens at rest"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize token encryption with a master key"""
        if encryption_key:
            self.master_key = encryption_key.encode()
        else:
            # Generate from environment or use a secure default
            env_key = os.getenv('KROGER_ENCRYPTION_KEY')
            if not env_key:
                # In production, this should be a securely generated and stored key
                logger.warning("No encryption key found in environment. Using generated key.")
                env_key = Fernet.generate_key().decode()
            self.master_key = env_key.encode()
        
        # Derive encryption key from master key using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'kroger-oauth-salt',  # In production, use unique salt per deployment
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key[:32]))
        self.cipher = Fernet(key)
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage"""
        if not token:
            return token
        
        try:
            encrypted = self.cipher.encrypt(token.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Token encryption failed: {str(e)}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token"""
        if not encrypted_token:
            return encrypted_token
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Token decryption failed: {str(e)}")
            raise


class TokenCache:
    """Thread-safe in-memory token cache with automatic expiry"""
    
    def __init__(self, encryption: TokenEncryption):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
        self.encryption = encryption
    
    def set(self, key: str, token_data: Dict[str, Any], expires_in: int):
        """Store token with expiration time"""
        with self.lock:
            # Encrypt sensitive tokens before caching
            if 'access_token' in token_data:
                token_data['access_token'] = self.encryption.encrypt_token(
                    token_data['access_token']
                )
            if 'refresh_token' in token_data:
                token_data['refresh_token'] = self.encryption.encrypt_token(
                    token_data['refresh_token']
                )
            
            self.cache[key] = {
                'data': token_data,
                'expires_at': datetime.utcnow() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early
            }
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve token if not expired"""
        with self.lock:
            if key not in self.cache:
                return None
            
            cached = self.cache[key]
            if datetime.utcnow() >= cached['expires_at']:
                del self.cache[key]
                return None
            
            # Decrypt tokens before returning
            token_data = cached['data'].copy()
            if 'access_token' in token_data:
                token_data['access_token'] = self.encryption.decrypt_token(
                    token_data['access_token']
                )
            if 'refresh_token' in token_data:
                token_data['refresh_token'] = self.encryption.decrypt_token(
                    token_data['refresh_token']
                )
            
            return token_data
    
    def clear(self, key: str):
        """Remove token from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]


class KrogerAuth:
    """
    Secure OAuth2 authentication handler for Kroger API
    
    Implements:
    - Client Credentials Grant for server-to-server authentication
    - Authorization Code Grant for user-specific operations
    - Automatic token refresh with retry logic
    - Rate limit compliance
    - Comprehensive error handling
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        environment: KrogerEnvironment = KrogerEnvironment.PRODUCTION,
        encryption_key: Optional[str] = None
    ):
        """
        Initialize Kroger OAuth2 authentication
        
        Args:
            client_id: Kroger API client ID (defaults to env var KROGER_CLIENT_ID)
            client_secret: Kroger API client secret (defaults to env var KROGER_CLIENT_SECRET)
            redirect_uri: OAuth2 redirect URI for user authorization (defaults to env var KROGER_REDIRECT_URI)
            environment: API environment (production or certification)
            encryption_key: Master key for token encryption
        """
        # Load credentials from environment if not provided
        self.client_id = client_id or os.getenv('KROGER_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('KROGER_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.getenv('KROGER_REDIRECT_URI')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID and Client Secret are required. Set via parameters or environment variables.")
        
        # Security: Never log credentials
        logger.info(f"Initializing Kroger OAuth2 for environment: {environment.name}")
        
        self.environment = environment
        self.base_url = environment.value
        self.token_url = f"{self.base_url}/connect/oauth2/token"
        self.authorize_url = f"{self.base_url}/connect/oauth2/authorize"
        
        # Initialize security components
        self.encryption = TokenEncryption(encryption_key)
        self.token_cache = TokenCache(self.encryption)
        
        # Rate limiting configuration
        self.rate_limit_remaining = 10000  # Daily limit for products API
        self.rate_limit_reset = datetime.utcnow() + timedelta(days=1)
        
        # Session for connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        
        # State parameter for CSRF protection in OAuth flow
        self.pending_states: Dict[str, datetime] = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def initialize_session(self):
        """Initialize aiohttp session with security headers"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'KrogerMCPServer/1.0',
                    'Accept': 'application/json'
                }
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_basic_auth_header(self) -> str:
        """Generate HTTP Basic Authentication header"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from logs"""
        sanitized = data.copy()
        for field in BLOCKED_LOG_FIELDS:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        return sanitized
    
    async def _handle_rate_limit(self, response: aiohttp.ClientResponse):
        """Handle rate limit headers and update tracking"""
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        
        if 'X-RateLimit-Reset' in response.headers:
            reset_timestamp = int(response.headers['X-RateLimit-Reset'])
            self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
        
        # Log warning if approaching limit
        if self.rate_limit_remaining < 1000:
            logger.warning(f"Approaching rate limit: {self.rate_limit_remaining} requests remaining")
    
    async def _make_token_request(
        self,
        data: Dict[str, str],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make a token request with retry logic and error handling
        
        Args:
            data: Form data for token request
            max_retries: Maximum number of retry attempts
            
        Returns:
            Token response data
            
        Raises:
            Exception: On authentication failure after retries
        """
        if not self.session:
            await self.initialize_session()
        
        headers = {
            'Authorization': self._get_basic_auth_header(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        for attempt in range(max_retries):
            try:
                async with self.session.post(
                    self.token_url,
                    data=urlencode(data),
                    headers=headers
                ) as response:
                    await self._handle_rate_limit(response)
                    
                    response_data = await response.json()
                    
                    if response.status == 200:
                        logger.info("Token request successful")
                        return response_data
                    
                    # Handle specific OAuth2 errors
                    if response.status == 400:
                        error = response_data.get('error', 'invalid_request')
                        error_desc = response_data.get('error_description', 'Bad request')
                        
                        if error == 'invalid_grant':
                            logger.error(f"Invalid grant: {error_desc}")
                            raise ValueError(f"Invalid authorization code or refresh token: {error_desc}")
                        elif error == 'invalid_scope':
                            logger.error(f"Invalid scope: {error_desc}")
                            raise ValueError(f"Requested scope not allowed: {error_desc}")
                        else:
                            logger.error(f"OAuth error: {error} - {error_desc}")
                            raise ValueError(f"OAuth2 error: {error} - {error_desc}")
                    
                    elif response.status == 401:
                        logger.error("Invalid client credentials")
                        raise ValueError("Invalid client ID or secret")
                    
                    elif response.status == 403:
                        logger.error("Access forbidden - check app permissions")
                        raise PermissionError("Application not authorized for requested scope")
                    
                    elif response.status == 429:
                        # Rate limited - wait before retry
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                        await asyncio.sleep(min(retry_after, 300))  # Max 5 min wait
                        continue
                    
                    elif response.status >= 500:
                        # Server error - retry with exponential backoff
                        wait_time = 2 ** attempt
                        logger.warning(f"Server error {response.status}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        logger.error(f"Unexpected response: {response.status}")
                        raise Exception(f"Unexpected response: {response.status} - {response_data}")
                        
            except aiohttp.ClientError as e:
                logger.error(f"Network error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        raise Exception(f"Failed to obtain token after {max_retries} attempts")
    
    async def get_client_credentials_token(
        self,
        scope: KrogerScope = KrogerScope.PRODUCT_COMPACT
    ) -> str:
        """
        Obtain access token using Client Credentials Grant
        Used for server-to-server authentication (no user context)
        
        Args:
            scope: OAuth2 scope for the token
            
        Returns:
            Access token string
        """
        cache_key = f"client_{scope.value}"
        
        # Check cache first
        cached_token = self.token_cache.get(cache_key)
        if cached_token:
            logger.info("Using cached client credentials token")
            return cached_token['access_token']
        
        logger.info(f"Requesting new client credentials token with scope: {scope.value}")
        
        data = {
            'grant_type': 'client_credentials',
            'scope': scope.value
        }
        
        response_data = await self._make_token_request(data)
        
        # Cache the token
        expires_in = response_data.get('expires_in', 1800)  # Default 30 min
        self.token_cache.set(cache_key, response_data, expires_in)
        
        return response_data['access_token']
    
    def get_authorization_url(
        self,
        scopes: list[KrogerScope],
        state: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate authorization URL for user consent
        
        Args:
            scopes: List of OAuth2 scopes to request
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, state)
        """
        if not self.redirect_uri:
            raise ValueError("Redirect URI required for authorization code flow")
        
        # Generate state for CSRF protection if not provided
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Store state with expiration (15 minutes)
        self.pending_states[state] = datetime.utcnow() + timedelta(minutes=15)
        
        # Clean up expired states
        current_time = datetime.utcnow()
        expired_states = [s for s, exp in self.pending_states.items() if current_time > exp]
        for expired_state in expired_states:
            del self.pending_states[expired_state]
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scope.value for scope in scopes),
            'state': state
        }
        
        auth_url = f"{self.authorize_url}?{urlencode(params)}"
        logger.info(f"Generated authorization URL for scopes: {[s.value for s in scopes]}")
        
        return auth_url, state
    
    def validate_state(self, state: str) -> bool:
        """
        Validate state parameter to prevent CSRF attacks
        
        Args:
            state: State parameter from callback
            
        Returns:
            True if valid, False otherwise
        """
        if state not in self.pending_states:
            logger.warning("Invalid or expired state parameter")
            return False
        
        # Check if state has expired
        if datetime.utcnow() > self.pending_states[state]:
            logger.warning("State parameter has expired")
            del self.pending_states[state]
            return False
        
        # State is valid - remove it to prevent reuse
        del self.pending_states[state]
        return True
    
    async def exchange_authorization_code(
        self,
        code: str,
        state: str,
        scopes: list[KrogerScope]
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            code: Authorization code from callback
            state: State parameter from callback
            scopes: List of scopes that were requested
            
        Returns:
            Dictionary with access_token, refresh_token, and metadata
        """
        # Validate state for CSRF protection
        if not self.validate_state(state):
            raise ValueError("Invalid or expired state parameter - possible CSRF attack")
        
        if not self.redirect_uri:
            raise ValueError("Redirect URI required for authorization code exchange")
        
        logger.info("Exchanging authorization code for tokens")
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scope.value for scope in scopes)
        }
        
        response_data = await self._make_token_request(data)
        
        # Cache the tokens
        cache_key = f"user_{hashlib.sha256(code.encode()).hexdigest()[:16]}"
        expires_in = response_data.get('expires_in', 1800)
        self.token_cache.set(cache_key, response_data, expires_in)
        
        return {
            'access_token': response_data['access_token'],
            'refresh_token': response_data.get('refresh_token'),
            'expires_in': expires_in,
            'scope': response_data.get('scope'),
            'token_type': response_data.get('token_type', 'Bearer')
        }
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        scopes: Optional[list[KrogerScope]] = None
    ) -> Dict[str, Any]:
        """
        Refresh an expired access token using refresh token
        
        Args:
            refresh_token: Refresh token from previous authorization
            scopes: Optional list of scopes (uses original if not specified)
            
        Returns:
            Dictionary with new access_token and metadata
        """
        logger.info("Refreshing access token")
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        # Include scopes if specified
        if scopes:
            data['scope'] = ' '.join(scope.value for scope in scopes)
        
        try:
            response_data = await self._make_token_request(data)
            
            # Cache the new tokens
            cache_key = f"refresh_{hashlib.sha256(refresh_token.encode()).hexdigest()[:16]}"
            expires_in = response_data.get('expires_in', 1800)
            self.token_cache.set(cache_key, response_data, expires_in)
            
            return {
                'access_token': response_data['access_token'],
                'refresh_token': response_data.get('refresh_token', refresh_token),  # May return same refresh token
                'expires_in': expires_in,
                'scope': response_data.get('scope'),
                'token_type': response_data.get('token_type', 'Bearer')
            }
            
        except ValueError as e:
            if 'invalid_grant' in str(e):
                logger.error("Refresh token has expired or been revoked")
                # Clear any cached tokens for this refresh token
                cache_key = f"refresh_{hashlib.sha256(refresh_token.encode()).hexdigest()[:16]}"
                self.token_cache.clear(cache_key)
                raise ValueError("Refresh token expired. User must re-authenticate.")
            raise
    
    async def make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        auto_refresh: bool = True,
        refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request with automatic token refresh
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            access_token: Access token for authorization
            json_data: Optional JSON body data
            params: Optional query parameters
            auto_refresh: Whether to automatically refresh on 401
            refresh_token: Refresh token for auto-refresh
            
        Returns:
            Response JSON data
        """
        if not self.session:
            await self.initialize_session()
        
        url = f"{self.base_url}{endpoint}"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        max_retries = 2 if auto_refresh and refresh_token else 1
        
        for attempt in range(max_retries):
            try:
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    json=json_data,
                    params=params
                ) as response:
                    await self._handle_rate_limit(response)
                    
                    # Handle 401 Unauthorized
                    if response.status == 401 and attempt == 0 and auto_refresh and refresh_token:
                        logger.info("Access token expired, attempting refresh...")
                        try:
                            new_tokens = await self.refresh_access_token(refresh_token)
                            access_token = new_tokens['access_token']
                            headers['Authorization'] = f'Bearer {access_token}'
                            continue  # Retry with new token
                        except Exception as e:
                            logger.error(f"Token refresh failed: {str(e)}")
                            raise
                    
                    # Check for other errors
                    if response.status == 403:
                        error_data = await response.json()
                        raise PermissionError(f"Insufficient scope for operation: {error_data}")
                    
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        raise Exception(f"Rate limit exceeded. Retry after {retry_after} seconds")
                    
                    if response.status >= 400:
                        error_data = await response.json()
                        raise Exception(f"API error {response.status}: {error_data}")
                    
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {str(e)}")
                raise
        
        raise Exception("Request failed after retries")
    
    def clear_token_cache(self, cache_key: Optional[str] = None):
        """
        Clear token cache
        
        Args:
            cache_key: Specific cache key to clear, or None to clear all
        """
        if cache_key:
            self.token_cache.clear(cache_key)
            logger.info(f"Cleared token cache for key: {cache_key}")
        else:
            self.token_cache.cache.clear()
            logger.info("Cleared entire token cache")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            'remaining': self.rate_limit_remaining,
            'reset_at': self.rate_limit_reset.isoformat(),
            'reset_in_seconds': max(0, (self.rate_limit_reset - datetime.utcnow()).total_seconds())
        }


# Example usage and testing
async def example_usage():
    """Example usage of the Kroger OAuth2 authentication module"""
    
    # Initialize with environment variables
    async with KrogerAuth(environment=KrogerEnvironment.CERTIFICATION) as auth:
        
        # Example 1: Get client credentials token for product search
        try:
            product_token = await auth.get_client_credentials_token(KrogerScope.PRODUCT_COMPACT)
            print(f"Got product access token: {product_token[:20]}...")
            
            # Make authenticated request
            products = await auth.make_authenticated_request(
                'GET',
                '/products',
                product_token,
                params={'filter.term': 'milk', 'filter.limit': '5'}
            )
            print(f"Found {len(products.get('data', []))} products")
            
        except Exception as e:
            print(f"Client credentials error: {e}")
        
        # Example 2: User authorization flow
        try:
            # Generate authorization URL
            auth_url, state = auth.get_authorization_url([
                KrogerScope.CART_BASIC_WRITE,
                KrogerScope.PROFILE_COMPACT
            ])
            print(f"Authorization URL: {auth_url}")
            print(f"State parameter: {state}")
            
            # After user authorizes and is redirected back with code...
            # mock_code = "abc123"  # This would come from the redirect
            # tokens = await auth.exchange_authorization_code(
            #     mock_code, state, [KrogerScope.CART_BASIC_WRITE]
            # )
            # print(f"User tokens obtained: {tokens}")
            
        except Exception as e:
            print(f"Authorization error: {e}")
        
        # Check rate limit status
        rate_status = auth.get_rate_limit_status()
        print(f"Rate limit status: {rate_status}")


if __name__ == "__main__":
    # Run example if executed directly
    asyncio.run(example_usage())