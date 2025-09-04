"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Any, Union, Optional
import base64
import secrets
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def verify_token(token: str) -> Union[str, None]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        return payload.get("sub")
    except jwt.JWTError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current user from JWT token.
    This is a simplified version - in production, you'd fetch from database.
    """
    token = credentials.credentials
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In production, fetch user from database
    # For now, return a mock user
    return {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "is_active": True,
        "is_superuser": True
    }


class ConfigurationEncryption:
    """Handles encryption and decryption of sensitive configuration data."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption with master key."""
        if master_key:
            self.master_key = master_key.encode()
        else:
            # Generate from settings or environment
            self.master_key = getattr(settings, 'ENCRYPTION_KEY', 'default-key-change-in-production').encode()
        
        # Derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable-salt',  # In production, use random salt per config
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not data:
            return data
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            # Log error in production
            return f"encryption_error:{data}"  # Fallback for development
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not encrypted_data:
            return encrypted_data
        
        # Handle development fallback
        if encrypted_data.startswith('encryption_error:'):
            return encrypted_data.replace('encryption_error:', '')
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            # Log error in production
            return encrypted_data  # Return as-is if decryption fails


# Global encryption instance
config_encryption = ConfigurationEncryption()


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive configuration data."""
    return config_encryption.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive configuration data."""
    return config_encryption.decrypt(encrypted_data)


def sanitize_path(path: str) -> str:
    """
    Sanitize file system paths to prevent traversal attacks.
    """
    # Remove path traversal attempts
    sanitized = path.replace('..', '').replace('//', '/')
    
    # Remove leading/trailing whitespace and slashes
    sanitized = sanitized.strip().strip('/')
    
    # Ensure absolute path
    if not sanitized.startswith('/'):
        sanitized = '/' + sanitized
    
    return sanitized


def validate_safe_path(path: str, allowed_roots: list = None) -> bool:
    """
    Validate that a path is safe to access.
    """
    blocked_paths = [
        '/etc', '/root', '/sys', '/proc', 
        '/dev', '/boot', '/var/log'
    ]
    
    sanitized = sanitize_path(path)
    
    # Check against blocked paths
    for blocked in blocked_paths:
        if sanitized.startswith(blocked):
            return False
    
    # Check against allowed roots if specified
    if allowed_roots:
        is_allowed = False
        for root in allowed_roots:
            if sanitized.startswith(sanitize_path(root)):
                is_allowed = True
                break
        if not is_allowed:
            return False
    
    return True


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(api_key) == hashed_key