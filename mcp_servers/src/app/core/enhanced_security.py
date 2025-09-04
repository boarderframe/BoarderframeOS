"""
Enhanced Security Implementation for MCP-UI System
Enterprise-grade security controls with OWASP compliance
"""

import os
import re
import secrets
import hashlib
import json
import uuid
import ipaddress
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Union
from enum import Enum
import base64

from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, validator
import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import pyotp
import qrcode
from io import BytesIO
from redis import Redis
import bleach
from urllib.parse import urlparse

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

class SecurityConfig:
    """Central security configuration"""
    
    # JWT Configuration
    JWT_ALGORITHM = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES = 30
    SESSION_ABSOLUTE_TIMEOUT_HOURS = 8
    SESSION_IDLE_TIMEOUT_MINUTES = 15
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_PER_HOUR = 1000
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES = 30
    
    # Password Policy
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    PASSWORD_HISTORY_COUNT = 5
    PASSWORD_EXPIRY_DAYS = 90
    
    # MFA Configuration
    MFA_ISSUER = "MCP-UI System"
    MFA_BACKUP_CODES_COUNT = 10
    TOTP_VALID_WINDOW = 1
    
    # Security Headers
    HSTS_MAX_AGE = 31536000
    CSP_REPORT_URI = "https://csp-reporter.mcp-ui.com/report"
    
    # Encryption
    ENCRYPTION_KEY_LENGTH = 32
    SALT_LENGTH = 16
    PBKDF2_ITERATIONS = 100000
    
    # Audit
    AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years
    
    # Blocked Paths
    BLOCKED_PATHS = [
        '/etc', '/root', '/sys', '/proc', 
        '/dev', '/boot', '/var/log', '/.env'
    ]
    
    # Allowed File Extensions
    ALLOWED_EXTENSIONS = {
        '.txt', '.pdf', '.png', '.jpg', '.jpeg', 
        '.gif', '.csv', '.json', '.xml'
    }

# ============================================================================
# ENHANCED JWT MANAGER WITH RSA
# ============================================================================

class EnhancedJWTManager:
    """Enterprise-grade JWT management with key rotation"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.config = SecurityConfig()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialize or rotate RSA key pairs"""
        current_version = self.redis.get("jwt:current_version")
        if not current_version:
            self._rotate_keys()
    
    def _rotate_keys(self):
        """Generate and store new RSA key pair"""
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Store with version
        version = datetime.now(timezone.utc).isoformat()
        self.redis.set(f"jwt:private_key:{version}", private_pem, ex=86400 * 60)
        self.redis.set(f"jwt:public_key:{version}", public_pem, ex=86400 * 60)
        self.redis.set("jwt:current_version", version)
    
    def create_token_pair(
        self, 
        user_id: str, 
        roles: List[str],
        permissions: List[str],
        metadata: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """Create access and refresh token pair"""
        now = datetime.now(timezone.utc)
        jti_access = str(uuid.uuid4())
        jti_refresh = str(uuid.uuid4())
        family_id = str(uuid.uuid4())
        
        # Access token claims
        access_claims = {
            "sub": user_id,
            "type": "access",
            "roles": roles,
            "permissions": permissions,
            "iat": now,
            "exp": now + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": jti_access,
            "metadata": metadata or {}
        }
        
        # Refresh token claims
        refresh_claims = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": jti_refresh,
            "family": family_id
        }
        
        # Get current private key
        version = self.redis.get("jwt:current_version").decode()
        private_key = self.redis.get(f"jwt:private_key:{version}")
        
        # Create tokens
        access_token = jwt.encode(
            access_claims, 
            private_key, 
            algorithm=self.config.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_claims,
            private_key,
            algorithm=self.config.JWT_ALGORITHM
        )
        
        # Track tokens
        self.redis.set(f"jwt:access:{jti_access}", user_id, ex=900)
        self.redis.set(f"jwt:refresh:{jti_refresh}", family_id, ex=604800)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            # Get current public key
            version = self.redis.get("jwt:current_version").decode()
            public_key = self.redis.get(f"jwt:public_key:{version}")
            
            # Verify token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.config.JWT_ALGORITHM]
            )
            
            # Validate token type
            if payload.get("type") != token_type:
                return None
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if self.redis.exists(f"jwt:blacklist:{jti}"):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, jti: str):
        """Revoke a token by JTI"""
        self.redis.set(f"jwt:blacklist:{jti}", "1", ex=86400 * 30)

# ============================================================================
# RBAC IMPLEMENTATION
# ============================================================================

class Permission(str, Enum):
    """System permissions following principle of least privilege"""
    # Server permissions
    SERVER_VIEW = "server:view"
    SERVER_CREATE = "server:create"
    SERVER_UPDATE = "server:update"
    SERVER_DELETE = "server:delete"
    SERVER_EXECUTE = "server:execute"
    
    # Configuration permissions
    CONFIG_VIEW = "config:view"
    CONFIG_UPDATE = "config:update"
    CONFIG_DELETE = "config:delete"
    
    # User permissions
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    AUDIT_VIEW = "audit:view"
    METRICS_VIEW = "metrics:view"
    SECURITY_MANAGE = "security:manage"

class Role(BaseModel):
    """Role definition with inheritance"""
    name: str
    description: str
    permissions: Set[Permission]
    inherits: Optional[List[str]] = None
    priority: int = 100  # Lower number = higher priority

# Predefined roles
SYSTEM_ROLES = {
    "viewer": Role(
        name="viewer",
        description="Read-only access to resources",
        permissions={
            Permission.SERVER_VIEW,
            Permission.CONFIG_VIEW,
            Permission.METRICS_VIEW
        },
        priority=100
    ),
    "operator": Role(
        name="operator",
        description="Can execute server operations",
        permissions={
            Permission.SERVER_VIEW,
            Permission.SERVER_EXECUTE,
            Permission.CONFIG_VIEW,
            Permission.METRICS_VIEW
        },
        priority=80
    ),
    "developer": Role(
        name="developer",
        description="Full server management except deletion",
        permissions={
            Permission.SERVER_VIEW,
            Permission.SERVER_CREATE,
            Permission.SERVER_UPDATE,
            Permission.SERVER_EXECUTE,
            Permission.CONFIG_VIEW,
            Permission.CONFIG_UPDATE,
            Permission.METRICS_VIEW
        },
        priority=60
    ),
    "admin": Role(
        name="admin",
        description="Full administrative access",
        permissions={
            Permission.SERVER_VIEW,
            Permission.SERVER_CREATE,
            Permission.SERVER_UPDATE,
            Permission.SERVER_DELETE,
            Permission.SERVER_EXECUTE,
            Permission.CONFIG_VIEW,
            Permission.CONFIG_UPDATE,
            Permission.CONFIG_DELETE,
            Permission.USER_VIEW,
            Permission.USER_UPDATE,
            Permission.AUDIT_VIEW,
            Permission.METRICS_VIEW
        },
        priority=20
    ),
    "security_admin": Role(
        name="security_admin",
        description="Security administration",
        permissions={
            Permission.SECURITY_MANAGE,
            Permission.AUDIT_VIEW,
            Permission.USER_VIEW,
            Permission.USER_UPDATE
        },
        inherits=["admin"],
        priority=10
    ),
    "super_admin": Role(
        name="super_admin",
        description="Unrestricted system access",
        permissions={Permission.SYSTEM_ADMIN},
        inherits=["security_admin"],
        priority=1
    )
}

class RBACEnforcer:
    """Role-based access control enforcement"""
    
    def __init__(self):
        self.roles = SYSTEM_ROLES
        self._compile_permissions()
    
    def _compile_permissions(self):
        """Compile inherited permissions"""
        for role in self.roles.values():
            if role.inherits:
                for parent_role_name in role.inherits:
                    parent_role = self.roles.get(parent_role_name)
                    if parent_role:
                        role.permissions.update(parent_role.permissions)
    
    def check_permission(
        self,
        user_roles: List[str],
        required_permission: Permission
    ) -> bool:
        """Check if user has required permission"""
        # Super admin bypass
        if "super_admin" in user_roles:
            return True
        
        # Check each role
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and required_permission in role.permissions:
                return True
        
        return False
    
    def get_effective_permissions(self, user_roles: List[str]) -> Set[Permission]:
        """Get all effective permissions for user"""
        permissions = set()
        
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        
        return permissions
    
    def get_highest_priority_role(self, user_roles: List[str]) -> Optional[str]:
        """Get the highest priority role for a user"""
        highest_role = None
        highest_priority = float('inf')
        
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and role.priority < highest_priority:
                highest_priority = role.priority
                highest_role = role_name
        
        return highest_role

# ============================================================================
# MFA IMPLEMENTATION
# ============================================================================

class MFAManager:
    """Multi-factor authentication with TOTP and backup codes"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.config = SecurityConfig()
    
    def setup_totp(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """Setup TOTP for user"""
        # Generate secret
        secret = pyotp.random_base32()
        
        # Encrypt and store secret
        encrypted_secret = self._encrypt_secret(secret)
        self.redis.set(f"mfa:totp:{user_id}", encrypted_secret)
        
        # Generate provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.config.MFA_ISSUER
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        qr_code_base64 = base64.b64encode(buf.getvalue()).decode()
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes(user_id)
        
        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_base64}",
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri
        }
    
    def verify_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        encrypted_secret = self.redis.get(f"mfa:totp:{user_id}")
        if not encrypted_secret:
            return False
        
        secret = self._decrypt_secret(encrypted_secret)
        totp = pyotp.TOTP(secret)
        
        # Verify with time window for clock drift
        return totp.verify(token, valid_window=self.config.TOTP_VALID_WINDOW)
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume backup code"""
        # Hash the provided code
        hashed_code = hashlib.sha256(code.encode()).hexdigest()
        
        # Check if exists
        if self.redis.sismember(f"mfa:backup:{user_id}", hashed_code):
            # Consume the code (one-time use)
            self.redis.srem(f"mfa:backup:{user_id}", hashed_code)
            return True
        
        return False
    
    def _generate_backup_codes(self, user_id: str) -> List[str]:
        """Generate backup codes"""
        codes = []
        
        # Clear existing codes
        self.redis.delete(f"mfa:backup:{user_id}")
        
        for _ in range(self.config.MFA_BACKUP_CODES_COUNT):
            # Generate code
            code = secrets.token_hex(4).upper()
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
            
            # Store hashed version
            hashed = hashlib.sha256(formatted_code.encode()).hexdigest()
            self.redis.sadd(f"mfa:backup:{user_id}", hashed)
        
        return codes
    
    def _encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret"""
        # In production, use proper key management
        key = os.environ.get("MFA_ENCRYPTION_KEY", "default-key-change-me").encode()
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'mfa-salt',
            iterations=self.config.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        encryption_key = base64.urlsafe_b64encode(kdf.derive(key))
        cipher = Fernet(encryption_key)
        return cipher.encrypt(secret.encode()).decode()
    
    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt TOTP secret"""
        key = os.environ.get("MFA_ENCRYPTION_KEY", "default-key-change-me").encode()
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'mfa-salt',
            iterations=self.config.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        encryption_key = base64.urlsafe_b64encode(kdf.derive(key))
        cipher = Fernet(encryption_key)
        return cipher.decrypt(encrypted_secret.encode()).decode()

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Secure session management with fingerprinting"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.config = SecurityConfig()
    
    def create_session(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        ip_address: str,
        user_agent: str,
        roles: List[str]
    ) -> str:
        """Create new session with security context"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_data": user_data,
            "roles": roles,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "fingerprint": self._generate_fingerprint(ip_address, user_agent)
        }
        
        # Store session
        self.redis.setex(
            f"session:{session_id}",
            self.config.SESSION_TIMEOUT_MINUTES * 60,
            json.dumps(session_data)
        )
        
        # Track active sessions
        self.redis.sadd(f"user:sessions:{user_id}", session_id)
        
        return session_id
    
    def validate_session(
        self,
        session_id: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[Dict[str, Any]]:
        """Validate session with security checks"""
        # Get session
        session_data = self.redis.get(f"session:{session_id}")
        if not session_data:
            return None
        
        session = json.loads(session_data)
        
        # Verify fingerprint (detect session hijacking)
        current_fingerprint = self._generate_fingerprint(ip_address, user_agent)
        if session.get("fingerprint") != current_fingerprint:
            # Possible session hijacking - terminate session
            self.terminate_session(session_id)
            self._log_security_event(
                "SESSION_HIJACK_ATTEMPT",
                session.get("user_id"),
                {"session_id": session_id, "ip": ip_address}
            )
            return None
        
        # Check absolute timeout
        created_at = datetime.fromisoformat(session["created_at"])
        if datetime.now(timezone.utc) - created_at > timedelta(
            hours=self.config.SESSION_ABSOLUTE_TIMEOUT_HOURS
        ):
            self.terminate_session(session_id)
            return None
        
        # Check idle timeout
        last_activity = datetime.fromisoformat(session["last_activity"])
        if datetime.now(timezone.utc) - last_activity > timedelta(
            minutes=self.config.SESSION_IDLE_TIMEOUT_MINUTES
        ):
            self.terminate_session(session_id)
            return None
        
        # Update last activity
        session["last_activity"] = datetime.now(timezone.utc).isoformat()
        self.redis.setex(
            f"session:{session_id}",
            self.config.SESSION_TIMEOUT_MINUTES * 60,
            json.dumps(session)
        )
        
        return session
    
    def terminate_session(self, session_id: str):
        """Terminate a session"""
        session_data = self.redis.get(f"session:{session_id}")
        if session_data:
            session = json.loads(session_data)
            user_id = session.get("user_id")
            
            # Remove from active sessions
            self.redis.srem(f"user:sessions:{user_id}", session_id)
            
            # Delete session
            self.redis.delete(f"session:{session_id}")
    
    def terminate_all_user_sessions(self, user_id: str):
        """Terminate all sessions for a user"""
        session_ids = self.redis.smembers(f"user:sessions:{user_id}")
        for session_id in session_ids:
            self.redis.delete(f"session:{session_id.decode()}")
        self.redis.delete(f"user:sessions:{user_id}")
    
    def _generate_fingerprint(self, ip_address: str, user_agent: str) -> str:
        """Generate session fingerprint"""
        # Include more entropy for better fingerprinting
        data = f"{ip_address}:{user_agent}:{self.config.MFA_ISSUER}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _log_security_event(self, event_type: str, user_id: str, data: Dict):
        """Log security event"""
        # Implementation would log to audit system
        pass

# ============================================================================
# XSS AND CSRF PROTECTION
# ============================================================================

class XSSProtection:
    """XSS prevention and content sanitization"""
    
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'a',
        'ul', 'ol', 'li', 'code', 'pre', 'blockquote'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'target'],
        'code': ['class']
    }
    
    ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
    
    @classmethod
    def sanitize_html(cls, content: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        if not content:
            return content
        
        return bleach.clean(
            content,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            protocols=cls.ALLOWED_PROTOCOLS,
            strip=True
        )
    
    @classmethod
    def escape_javascript(cls, content: str) -> str:
        """Escape content for JavaScript context"""
        if not content:
            return content
        
        # Escape special characters
        escapes = {
            '\\': '\\\\',
            '"': '\\"',
            "'": "\\'",
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '<': '\\u003C',
            '>': '\\u003E',
            '&': '\\u0026',
            '=': '\\u003D',
            '-': '\\u002D',
            ';': '\\u003B',
            '`': '\\u0060',
            '\u2028': '\\u2028',
            '\u2029': '\\u2029'
        }
        
        for char, escape in escapes.items():
            content = content.replace(char, escape)
        
        return content
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL to prevent javascript: and data: URIs"""
        if not url:
            return False
        
        parsed = urlparse(url)
        
        # Check protocol
        if parsed.scheme not in cls.ALLOWED_PROTOCOLS:
            return False
        
        # Check for javascript: or data: URLs
        if url.lower().startswith(('javascript:', 'data:', 'vbscript:')):
            return False
        
        return True
    
    @classmethod
    def sanitize_json(cls, data: Any) -> Any:
        """Sanitize JSON data recursively"""
        if isinstance(data, str):
            return cls.sanitize_html(data)
        elif isinstance(data, dict):
            return {key: cls.sanitize_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_json(item) for item in data]
        else:
            return data

class CSRFProtection:
    """CSRF protection with double-submit cookies"""
    
    def __init__(self):
        self.config = SecurityConfig()
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(
        self,
        token_header: str,
        token_cookie: str
    ) -> bool:
        """Validate CSRF token using double-submit pattern"""
        if not token_header or not token_cookie:
            return False
        
        # Tokens must match
        if token_header != token_cookie:
            return False
        
        # Additional validation can be added here
        return True
    
    def get_csrf_cookie_params(self) -> Dict[str, Any]:
        """Get CSRF cookie parameters"""
        return {
            "key": "csrf_token",
            "httponly": False,  # Must be readable by JavaScript
            "secure": True,
            "samesite": "strict",
            "path": "/",
            "max_age": 3600
        }

# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Comprehensive security headers middleware"""
    
    def __init__(self, app, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
    
    async def dispatch(self, request: Request, call_next):
        # Generate CSP nonce
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response, nonce)
        
        return response
    
    def _add_security_headers(self, response: Response, nonce: str):
        """Add all security headers"""
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' https://trusted-cdn.com",
            "style-src 'self' 'unsafe-inline' https://trusted-cdn.com",
            "img-src 'self' data: https:",
            "font-src 'self' https://trusted-cdn.com",
            "connect-src 'self' https://api.mcp-ui.com wss://ws.mcp-ui.com",
            "frame-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "media-src 'self'",
            "worker-src 'self' blob:",
            "manifest-src 'self'",
            "upgrade-insecure-requests",
            "block-all-mixed-content",
            f"report-uri {self.config.CSP_REPORT_URI}"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Strict Transport Security
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self.config.HSTS_MAX_AGE}; "
            "includeSubDomains; preload"
        )
        
        # Other security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (Feature Policy)
        permissions = [
            "camera=()",
            "microphone=()",
            "geolocation=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "autoplay=()",
            "fullscreen=(self)",
            "encrypted-media=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Remove server identification headers
        headers_to_remove = ["server", "x-powered-by", "x-aspnet-version"]
        for header in headers_to_remove:
            if header in response.headers:
                del response.headers[header]

# ============================================================================
# INPUT VALIDATION AND SANITIZATION
# ============================================================================

class InputValidator:
    """Comprehensive input validation"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username"""
        # Alphanumeric, underscore, hyphen, 3-20 characters
        pattern = r'^[a-zA-Z0-9_-]{3,20}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password against policy"""
        config = SecurityConfig()
        errors = []
        
        if len(password) < config.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters")
        
        if config.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letter")
        
        if config.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase letter")
        
        if config.REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain number")
        
        if config.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain special character")
        
        # Check for common passwords
        common_passwords = ['password', '123456', 'admin', 'letmein']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": InputValidator._calculate_password_strength(password)
        }
    
    @staticmethod
    def _calculate_password_strength(password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length
        score += min(30, len(password) * 2)
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 20
        
        # Entropy bonus
        unique_chars = len(set(password))
        score += min(20, unique_chars)
        
        return min(100, score)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
        
        return filename
    
    @staticmethod
    def validate_path(path: str) -> bool:
        """Validate file path for security"""
        config = SecurityConfig()
        
        # Normalize path
        normalized = os.path.normpath(path)
        
        # Check for path traversal
        if '..' in normalized:
            return False
        
        # Check against blocked paths
        for blocked in config.BLOCKED_PATHS:
            if normalized.startswith(blocked):
                return False
        
        return True
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.config = SecurityConfig()
    
    def check_rate_limit(
        self,
        identifier: str,
        limit_type: str = "minute"
    ) -> Dict[str, Any]:
        """Check if rate limit exceeded"""
        if limit_type == "minute":
            window = 60
            limit = self.config.RATE_LIMIT_PER_MINUTE
        elif limit_type == "hour":
            window = 3600
            limit = self.config.RATE_LIMIT_PER_HOUR
        else:
            raise ValueError(f"Unknown limit type: {limit_type}")
        
        key = f"rate_limit:{limit_type}:{identifier}"
        
        # Increment counter
        current = self.redis.incr(key)
        
        # Set expiry on first request
        if current == 1:
            self.redis.expire(key, window)
        
        # Check limit
        exceeded = current > limit
        
        return {
            "exceeded": exceeded,
            "limit": limit,
            "remaining": max(0, limit - current),
            "reset_in": self.redis.ttl(key)
        }
    
    def check_failed_login(self, identifier: str) -> Dict[str, Any]:
        """Check failed login attempts"""
        key = f"failed_login:{identifier}"
        
        # Get current count
        attempts = self.redis.get(key)
        attempts = int(attempts) if attempts else 0
        
        # Check if account should be locked
        locked = attempts >= self.config.MAX_FAILED_LOGIN_ATTEMPTS
        
        if locked:
            # Set lockout
            lockout_key = f"account_locked:{identifier}"
            self.redis.setex(
                lockout_key,
                self.config.ACCOUNT_LOCKOUT_DURATION_MINUTES * 60,
                "1"
            )
        
        return {
            "attempts": attempts,
            "locked": locked,
            "max_attempts": self.config.MAX_FAILED_LOGIN_ATTEMPTS,
            "lockout_duration": self.config.ACCOUNT_LOCKOUT_DURATION_MINUTES
        }
    
    def record_failed_login(self, identifier: str):
        """Record failed login attempt"""
        key = f"failed_login:{identifier}"
        self.redis.incr(key)
        self.redis.expire(key, 3600)  # Reset after 1 hour
    
    def clear_failed_logins(self, identifier: str):
        """Clear failed login attempts after successful login"""
        self.redis.delete(f"failed_login:{identifier}")
        self.redis.delete(f"account_locked:{identifier}")
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked"""
        return self.redis.exists(f"account_locked:{identifier}") > 0

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

class APIKeyManager:
    """Secure API key management for external integrations"""
    
    def __init__(self, redis_client: Redis, vault_client=None):
        self.redis = redis_client
        self.vault = vault_client
        self.config = SecurityConfig()
        self.cipher = self._initialize_cipher()
    
    def _initialize_cipher(self) -> Fernet:
        """Initialize encryption cipher"""
        master_key = os.environ.get("MASTER_ENCRYPTION_KEY", "change-me-in-production")
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'api-key-salt',
            iterations=self.config.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def create_api_key(
        self,
        name: str,
        scopes: List[str],
        expires_in_days: int = 365
    ) -> Dict[str, str]:
        """Create new API key"""
        # Generate key
        api_key = secrets.token_urlsafe(32)
        key_id = str(uuid.uuid4())
        
        # Hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store key metadata
        key_data = {
            "id": key_id,
            "name": name,
            "hash": key_hash,
            "scopes": scopes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            ).isoformat()
        }
        
        # Store in Redis
        self.redis.set(
            f"api_key:{key_id}",
            json.dumps(key_data),
            ex=expires_in_days * 86400
        )
        
        # Also store hash -> id mapping for quick lookup
        self.redis.set(
            f"api_key_hash:{key_hash}",
            key_id,
            ex=expires_in_days * 86400
        )
        
        return {
            "key_id": key_id,
            "api_key": api_key,
            "expires_at": key_data["expires_at"]
        }
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key"""
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Look up key ID
        key_id = self.redis.get(f"api_key_hash:{key_hash}")
        if not key_id:
            return None
        
        # Get key data
        key_data = self.redis.get(f"api_key:{key_id.decode()}")
        if not key_data:
            return None
        
        data = json.loads(key_data)
        
        # Check expiration
        expires_at = datetime.fromisoformat(data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            return None
        
        return data
    
    def revoke_api_key(self, key_id: str):
        """Revoke API key"""
        # Get key data
        key_data = self.redis.get(f"api_key:{key_id}")
        if key_data:
            data = json.loads(key_data)
            # Delete both key and hash mapping
            self.redis.delete(f"api_key:{key_id}")
            self.redis.delete(f"api_key_hash:{data['hash']}")
    
    def store_external_api_key(
        self,
        service: str,
        key_name: str,
        api_key: str,
        api_secret: str = None
    ) -> str:
        """Store encrypted external API key (e.g., Kroger)"""
        key_id = str(uuid.uuid4())
        
        # Encrypt credentials
        encrypted_data = {
            "service": service,
            "key_name": key_name,
            "api_key": self.cipher.encrypt(api_key.encode()).decode(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if api_secret:
            encrypted_data["api_secret"] = self.cipher.encrypt(api_secret.encode()).decode()
        
        # Store in Redis (or Vault in production)
        self.redis.set(
            f"external_api:{service}:{key_id}",
            json.dumps(encrypted_data)
        )
        
        return key_id
    
    def retrieve_external_api_key(
        self,
        service: str,
        key_id: str
    ) -> Optional[Dict[str, str]]:
        """Retrieve and decrypt external API key"""
        # Get encrypted data
        data = self.redis.get(f"external_api:{service}:{key_id}")
        if not data:
            return None
        
        encrypted_data = json.loads(data)
        
        # Decrypt credentials
        result = {
            "service": encrypted_data["service"],
            "key_name": encrypted_data["key_name"],
            "api_key": self.cipher.decrypt(
                encrypted_data["api_key"].encode()
            ).decode()
        }
        
        if "api_secret" in encrypted_data:
            result["api_secret"] = self.cipher.decrypt(
                encrypted_data["api_secret"].encode()
            ).decode()
        
        return result

# ============================================================================
# SECURE POSTMESSAGE HANDLER
# ============================================================================

class SecurePostMessageHandler:
    """Secure PostMessage implementation for iframe communication"""
    
    def __init__(self, trusted_origins: List[str]):
        self.trusted_origins = set(trusted_origins)
        self.processed_nonces = set()
        self.message_timeout = 30000  # 30 seconds
    
    def validate_message(self, message: Dict[str, Any], origin: str) -> bool:
        """Validate incoming postMessage"""
        # Check origin
        if origin not in self.trusted_origins:
            return False
        
        # Check required fields
        required_fields = ["type", "payload", "timestamp", "nonce", "signature"]
        if not all(field in message for field in required_fields):
            return False
        
        # Check timestamp (prevent replay attacks)
        try:
            timestamp = int(message["timestamp"])
            age = int(datetime.now().timestamp() * 1000) - timestamp
            if age > self.message_timeout:
                return False
        except (ValueError, TypeError):
            return False
        
        # Check nonce (prevent duplicate processing)
        nonce = message["nonce"]
        if nonce in self.processed_nonces:
            return False
        self.processed_nonces.add(nonce)
        
        # Verify signature
        if not self._verify_signature(message):
            return False
        
        return True
    
    def create_message(
        self,
        message_type: str,
        payload: Any,
        target_origin: str
    ) -> Dict[str, Any]:
        """Create secure postMessage"""
        if target_origin not in self.trusted_origins:
            raise ValueError(f"Untrusted target origin: {target_origin}")
        
        message = {
            "type": message_type,
            "payload": payload,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "nonce": str(uuid.uuid4()),
            "origin": "mcp-ui"
        }
        
        # Add signature
        message["signature"] = self._sign_message(message)
        
        return message
    
    def _sign_message(self, message: Dict[str, Any]) -> str:
        """Sign message for integrity"""
        # Create signing string
        signing_data = json.dumps(
            {k: v for k, v in message.items() if k != "signature"},
            sort_keys=True
        )
        
        # Sign with HMAC
        secret = os.environ.get("POSTMESSAGE_SECRET", "change-me").encode()
        signature = hashlib.sha256(
            secret + signing_data.encode()
        ).hexdigest()
        
        return signature
    
    def _verify_signature(self, message: Dict[str, Any]) -> bool:
        """Verify message signature"""
        provided_signature = message.get("signature")
        if not provided_signature:
            return False
        
        # Recreate signature
        expected_signature = self._sign_message(
            {k: v for k, v in message.items() if k != "signature"}
        )
        
        # Constant-time comparison
        return secrets.compare_digest(provided_signature, expected_signature)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'SecurityConfig',
    'EnhancedJWTManager',
    'Permission',
    'Role',
    'SYSTEM_ROLES',
    'RBACEnforcer',
    'MFAManager',
    'SessionManager',
    'XSSProtection',
    'CSRFProtection',
    'SecurityHeadersMiddleware',
    'InputValidator',
    'RateLimiter',
    'APIKeyManager',
    'SecurePostMessageHandler'
]