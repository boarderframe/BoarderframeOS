"""
OAuth 2.0 Security Implementation with PKCE for Kroger API
Implements OAuth 2.0 authorization code flow with PKCE extension
"""

import os
import json
import base64
import hashlib
import secrets
import urllib.parse
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import asyncio
import aiohttp

from fastapi import HTTPException, Request, Response, status
from pydantic import BaseModel, Field, validator
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import redis

# ============================================================================
# OAUTH CONFIGURATION
# ============================================================================

@dataclass
class OAuthProvider:
    """OAuth provider configuration"""
    name: str
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    refresh_url: str
    revoke_url: Optional[str]
    scopes: List[str]
    redirect_uri: str
    uses_pkce: bool = True
    uses_state: bool = True
    token_endpoint_auth_method: str = "client_secret_post"  # or "client_secret_basic"

class OAuthConfig:
    """OAuth configuration for multiple providers"""
    
    PROVIDERS = {
        "kroger": OAuthProvider(
            name="kroger",
            client_id=os.environ.get("KROGER_CLIENT_ID", ""),
            client_secret=os.environ.get("KROGER_CLIENT_SECRET", ""),
            authorize_url="https://api.kroger.com/v1/connect/oauth2/authorize",
            token_url="https://api.kroger.com/v1/connect/oauth2/token",
            refresh_url="https://api.kroger.com/v1/connect/oauth2/token",
            revoke_url=None,
            scopes=["product.compact", "cart.basic:write"],
            redirect_uri=os.environ.get("KROGER_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback/kroger"),
            uses_pkce=True,
            uses_state=True,
            token_endpoint_auth_method="client_secret_basic"
        ),
        "github": OAuthProvider(
            name="github",
            client_id=os.environ.get("GITHUB_CLIENT_ID", ""),
            client_secret=os.environ.get("GITHUB_CLIENT_SECRET", ""),
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            refresh_url=None,
            revoke_url="https://api.github.com/applications/{client_id}/token",
            scopes=["user", "repo"],
            redirect_uri=os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback/github"),
            uses_pkce=False,
            uses_state=True,
            token_endpoint_auth_method="client_secret_post"
        )
    }

# ============================================================================
# PKCE (PROOF KEY FOR CODE EXCHANGE) IMPLEMENTATION
# ============================================================================

class PKCEManager:
    """Manages PKCE flow for OAuth 2.0"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.min_length = 43
        self.max_length = 128
    
    def generate_pkce_pair(self) -> Tuple[str, str]:
        """Generate PKCE code verifier and challenge"""
        # Generate code verifier (43-128 characters)
        verifier_length = secrets.randbelow(self.max_length - self.min_length + 1) + self.min_length
        verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(verifier_length * 3 // 4)
        ).decode('utf-8').rstrip('=')[:verifier_length]
        
        # Generate code challenge (SHA256)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return verifier, challenge
    
    def store_pkce_verifier(
        self,
        state: str,
        verifier: str,
        ttl: int = 600  # 10 minutes
    ):
        """Store PKCE verifier for later verification"""
        key = f"pkce:verifier:{state}"
        self.redis.setex(key, ttl, verifier)
    
    def retrieve_pkce_verifier(self, state: str) -> Optional[str]:
        """Retrieve and delete PKCE verifier"""
        key = f"pkce:verifier:{state}"
        verifier = self.redis.get(key)
        if verifier:
            self.redis.delete(key)
            return verifier.decode('utf-8')
        return None
    
    def validate_pkce(self, verifier: str, challenge: str) -> bool:
        """Validate PKCE verifier against challenge"""
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return secrets.compare_digest(expected_challenge, challenge)

# ============================================================================
# OAUTH STATE MANAGER
# ============================================================================

class OAuthStateManager:
    """Manages OAuth state parameter for CSRF protection"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cipher = self._initialize_cipher()
    
    def _initialize_cipher(self) -> Fernet:
        """Initialize encryption for state data"""
        master_key = os.environ.get("OAUTH_STATE_KEY", "change-me-in-production")
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'oauth-state-salt',
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def create_state(
        self,
        provider: str,
        user_id: Optional[str] = None,
        return_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create and store OAuth state"""
        state_id = secrets.token_urlsafe(32)
        
        state_data = {
            "provider": provider,
            "user_id": user_id,
            "return_url": return_url,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "nonce": secrets.token_urlsafe(16)
        }
        
        # Encrypt sensitive data
        encrypted_data = self.cipher.encrypt(
            json.dumps(state_data).encode()
        ).decode()
        
        # Store in Redis with TTL
        key = f"oauth:state:{state_id}"
        self.redis.setex(key, 600, encrypted_data)  # 10 minutes TTL
        
        return state_id
    
    def validate_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Validate and retrieve OAuth state"""
        key = f"oauth:state:{state}"
        encrypted_data = self.redis.get(key)
        
        if not encrypted_data:
            return None
        
        # Delete state (one-time use)
        self.redis.delete(key)
        
        try:
            # Decrypt data
            decrypted = self.cipher.decrypt(encrypted_data).decode()
            state_data = json.loads(decrypted)
            
            # Check expiration
            created_at = datetime.fromisoformat(state_data["created_at"])
            if datetime.now(timezone.utc) - created_at > timedelta(minutes=10):
                return None
            
            return state_data
            
        except Exception:
            return None

# ============================================================================
# OAUTH TOKEN MANAGER
# ============================================================================

class OAuthTokenManager:
    """Manages OAuth tokens with encryption and refresh"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cipher = self._initialize_cipher()
    
    def _initialize_cipher(self) -> Fernet:
        """Initialize encryption for tokens"""
        master_key = os.environ.get("OAUTH_TOKEN_KEY", "change-me-in-production")
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'oauth-token-salt',
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def store_tokens(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        token_type: str = "Bearer",
        scope: Optional[str] = None
    ) -> str:
        """Store OAuth tokens securely"""
        token_id = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = None
        if expires_in:
            expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            ).isoformat()
        
        token_data = {
            "user_id": user_id,
            "provider": provider,
            "access_token": self.cipher.encrypt(access_token.encode()).decode(),
            "token_type": token_type,
            "scope": scope,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if refresh_token:
            token_data["refresh_token"] = self.cipher.encrypt(
                refresh_token.encode()
            ).decode()
        
        # Store in Redis
        key = f"oauth:tokens:{provider}:{user_id}"
        self.redis.set(key, json.dumps(token_data))
        
        # Create index for user's tokens
        self.redis.sadd(f"oauth:user_tokens:{user_id}", f"{provider}:{token_id}")
        
        return token_id
    
    def get_tokens(
        self,
        user_id: str,
        provider: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt OAuth tokens"""
        key = f"oauth:tokens:{provider}:{user_id}"
        data = self.redis.get(key)
        
        if not data:
            return None
        
        token_data = json.loads(data)
        
        # Check expiration
        if token_data.get("expires_at"):
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                # Token expired, attempt refresh if possible
                if "refresh_token" in token_data:
                    return {
                        "expired": True,
                        "refresh_token": self.cipher.decrypt(
                            token_data["refresh_token"].encode()
                        ).decode()
                    }
                return None
        
        # Decrypt tokens
        result = {
            "access_token": self.cipher.decrypt(
                token_data["access_token"].encode()
            ).decode(),
            "token_type": token_data.get("token_type", "Bearer"),
            "scope": token_data.get("scope"),
            "expires_at": token_data.get("expires_at")
        }
        
        if "refresh_token" in token_data:
            result["refresh_token"] = self.cipher.decrypt(
                token_data["refresh_token"].encode()
            ).decode()
        
        return result
    
    def revoke_tokens(self, user_id: str, provider: str):
        """Revoke OAuth tokens"""
        # Delete tokens
        key = f"oauth:tokens:{provider}:{user_id}"
        self.redis.delete(key)
        
        # Remove from index
        self.redis.srem(f"oauth:user_tokens:{user_id}", f"{provider}:*")

# ============================================================================
# OAUTH FLOW MANAGER
# ============================================================================

class OAuthFlowManager:
    """Manages complete OAuth 2.0 flow with PKCE"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.pkce = PKCEManager(redis_client)
        self.state_manager = OAuthStateManager(redis_client)
        self.token_manager = OAuthTokenManager(redis_client)
        self.providers = OAuthConfig.PROVIDERS
    
    def initiate_authorization(
        self,
        provider_name: str,
        user_id: Optional[str] = None,
        return_url: Optional[str] = None,
        additional_scopes: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Initiate OAuth authorization flow"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        # Create state
        state = self.state_manager.create_state(
            provider_name,
            user_id,
            return_url
        )
        
        # Build authorization URL
        params = {
            "client_id": provider.client_id,
            "redirect_uri": provider.redirect_uri,
            "response_type": "code",
            "scope": " ".join(provider.scopes + (additional_scopes or []))
        }
        
        # Add state if supported
        if provider.uses_state:
            params["state"] = state
        
        # Add PKCE if supported
        if provider.uses_pkce:
            verifier, challenge = self.pkce.generate_pkce_pair()
            self.pkce.store_pkce_verifier(state, verifier)
            params["code_challenge"] = challenge
            params["code_challenge_method"] = "S256"
        
        # Build URL
        auth_url = f"{provider.authorize_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def handle_callback(
        self,
        provider_name: str,
        code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        # Validate state if provided
        state_data = None
        if state:
            state_data = self.state_manager.validate_state(state)
            if not state_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired state"
                )
        
        # Prepare token exchange request
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": provider.redirect_uri
        }
        
        # Add PKCE verifier if used
        if provider.uses_pkce and state:
            verifier = self.pkce.retrieve_pkce_verifier(state)
            if verifier:
                token_data["code_verifier"] = verifier
        
        # Add client credentials based on auth method
        headers = {"Accept": "application/json"}
        
        if provider.token_endpoint_auth_method == "client_secret_post":
            token_data["client_id"] = provider.client_id
            token_data["client_secret"] = provider.client_secret
        elif provider.token_endpoint_auth_method == "client_secret_basic":
            auth_string = base64.b64encode(
                f"{provider.client_id}:{provider.client_secret}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {auth_string}"
        
        # Exchange code for tokens
        async with aiohttp.ClientSession() as session:
            async with session.post(
                provider.token_url,
                data=token_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Token exchange failed: {error_text}"
                    )
                
                tokens = await response.json()
        
        # Store tokens
        user_id = state_data.get("user_id") if state_data else "anonymous"
        token_id = self.token_manager.store_tokens(
            user_id=user_id,
            provider=provider_name,
            access_token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens.get("expires_in"),
            token_type=tokens.get("token_type", "Bearer"),
            scope=tokens.get("scope")
        )
        
        return {
            "token_id": token_id,
            "provider": provider_name,
            "user_id": user_id,
            "return_url": state_data.get("return_url") if state_data else None,
            "scope": tokens.get("scope")
        }
    
    async def refresh_tokens(
        self,
        user_id: str,
        provider_name: str
    ) -> Dict[str, Any]:
        """Refresh OAuth tokens"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        if not provider.refresh_url:
            raise ValueError(f"Provider {provider_name} doesn't support token refresh")
        
        # Get current tokens
        current_tokens = self.token_manager.get_tokens(user_id, provider_name)
        if not current_tokens or "refresh_token" not in current_tokens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No refresh token available"
            )
        
        # Prepare refresh request
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": current_tokens["refresh_token"]
        }
        
        # Add client credentials
        headers = {"Accept": "application/json"}
        
        if provider.token_endpoint_auth_method == "client_secret_post":
            refresh_data["client_id"] = provider.client_id
            refresh_data["client_secret"] = provider.client_secret
        elif provider.token_endpoint_auth_method == "client_secret_basic":
            auth_string = base64.b64encode(
                f"{provider.client_id}:{provider.client_secret}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {auth_string}"
        
        # Refresh tokens
        async with aiohttp.ClientSession() as session:
            async with session.post(
                provider.refresh_url,
                data=refresh_data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Token refresh failed: {error_text}"
                    )
                
                new_tokens = await response.json()
        
        # Update stored tokens
        token_id = self.token_manager.store_tokens(
            user_id=user_id,
            provider=provider_name,
            access_token=new_tokens.get("access_token"),
            refresh_token=new_tokens.get("refresh_token", current_tokens["refresh_token"]),
            expires_in=new_tokens.get("expires_in"),
            token_type=new_tokens.get("token_type", "Bearer"),
            scope=new_tokens.get("scope")
        )
        
        return {
            "token_id": token_id,
            "access_token": new_tokens.get("access_token"),
            "expires_in": new_tokens.get("expires_in")
        }
    
    async def revoke_tokens(
        self,
        user_id: str,
        provider_name: str
    ) -> bool:
        """Revoke OAuth tokens"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        
        # Get current tokens
        current_tokens = self.token_manager.get_tokens(user_id, provider_name)
        if not current_tokens:
            return True  # Already revoked
        
        # Call provider's revoke endpoint if available
        if provider.revoke_url:
            headers = {"Accept": "application/json"}
            
            if provider_name == "github":
                # GitHub uses different revocation format
                revoke_url = provider.revoke_url.format(client_id=provider.client_id)
                auth_string = base64.b64encode(
                    f"{provider.client_id}:{provider.client_secret}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {auth_string}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.delete(
                        revoke_url,
                        headers=headers,
                        json={"access_token": current_tokens["access_token"]}
                    ) as response:
                        # GitHub returns 204 on success
                        if response.status not in [204, 200]:
                            return False
        
        # Remove from local storage
        self.token_manager.revoke_tokens(user_id, provider_name)
        
        return True

# ============================================================================
# OAUTH REQUEST HELPER
# ============================================================================

class OAuthRequestHelper:
    """Helper for making authenticated OAuth requests"""
    
    def __init__(self, token_manager: OAuthTokenManager):
        self.token_manager = token_manager
    
    async def make_authenticated_request(
        self,
        user_id: str,
        provider: str,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to OAuth provider's API"""
        # Get tokens
        tokens = self.token_manager.get_tokens(user_id, provider)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid tokens found"
            )
        
        # Check if expired
        if tokens.get("expired"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired, refresh required"
            )
        
        # Prepare headers
        request_headers = headers or {}
        request_headers["Authorization"] = f"{tokens['token_type']} {tokens['access_token']}"
        request_headers["Accept"] = "application/json"
        
        # Make request
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=request_headers,
                json=json_data,
                params=params
            ) as response:
                response_data = await response.json()
                
                if response.status == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token invalid or expired"
                    )
                
                if response.status >= 400:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"API request failed: {response_data}"
                    )
                
                return {
                    "status": response.status,
                    "data": response_data,
                    "headers": dict(response.headers)
                }

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'OAuthProvider',
    'OAuthConfig',
    'PKCEManager',
    'OAuthStateManager',
    'OAuthTokenManager',
    'OAuthFlowManager',
    'OAuthRequestHelper'
]