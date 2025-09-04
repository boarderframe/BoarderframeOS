"""
Security Framework for MCP-UI
Authentication, authorization, rate limiting, and content validation
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import hashlib
import hmac
import re
import time
from collections import defaultdict, deque
import logging


# ============================================================================
# Security Configuration
# ============================================================================

class SecurityConfig(BaseModel):
    """Security configuration"""
    
    # Authentication
    auth_enabled: bool = Field(default=True)
    auth_type: str = Field(default="bearer")  # bearer, api_key, oauth2
    auth_header: str = Field(default="Authorization")
    
    # Token management
    max_token_budget: int = Field(default=10000)
    token_refresh_interval: int = Field(default=3600)
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    requests_per_minute: int = Field(default=60)
    requests_per_hour: int = Field(default=1000)
    burst_size: int = Field(default=10)
    
    # Content security
    content_validation_enabled: bool = Field(default=True)
    max_content_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_mime_types: List[str] = Field(
        default_factory=lambda: ["text/html", "text/plain", "application/json"]
    )
    
    # Path restrictions
    blocked_paths: List[str] = Field(
        default_factory=lambda: ["/etc", "/var", "/.env", "/proc"]
    )
    blocked_commands: List[str] = Field(
        default_factory=lambda: ["rm", "sudo", "chmod", "chown"]
    )
    
    # CORS settings
    cors_enabled: bool = Field(default=True)
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    allowed_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    
    # Session management
    session_timeout: int = Field(default=1800)  # 30 minutes
    max_sessions_per_user: int = Field(default=5)
    
    # Audit logging
    audit_enabled: bool = Field(default=True)
    audit_log_path: str = Field(default="/var/log/mcp/audit.log")


# ============================================================================
# Token Budget Manager
# ============================================================================

class TokenBudget:
    """Manage token consumption and budgets"""
    
    def __init__(self, max_budget: int):
        self.max_budget = max_budget
        self.consumed = 0
        self.history: deque = deque(maxlen=100)
        self.reset_time = datetime.now() + timedelta(hours=1)
    
    def consume(self, tokens: int) -> bool:
        """
        Consume tokens from budget
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if successful, False if would exceed budget
        """
        # Check for reset
        if datetime.now() >= self.reset_time:
            self.reset()
        
        if self.consumed + tokens > self.max_budget:
            return False
        
        self.consumed += tokens
        self.history.append({
            "timestamp": datetime.now(),
            "tokens": tokens,
            "remaining": self.max_budget - self.consumed
        })
        
        return True
    
    def get_remaining(self) -> int:
        """Get remaining token budget"""
        if datetime.now() >= self.reset_time:
            self.reset()
        return self.max_budget - self.consumed
    
    def reset(self):
        """Reset token budget"""
        self.consumed = 0
        self.reset_time = datetime.now() + timedelta(hours=1)


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.buckets: Dict[str, Dict[str, Any]] = defaultdict(self._create_bucket)
        self.logger = logging.getLogger(__name__)
    
    def _create_bucket(self) -> Dict[str, Any]:
        """Create a new token bucket"""
        return {
            "tokens": self.config.burst_size,
            "last_refill": time.time(),
            "minute_requests": deque(maxlen=60),
            "hour_requests": deque(maxlen=3600)
        }
    
    def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if request is within rate limits
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if within limits
        """
        if not self.config.rate_limit_enabled:
            return True
        
        bucket = self.buckets[client_id]
        now = time.time()
        
        # Refill tokens
        time_passed = now - bucket["last_refill"]
        tokens_to_add = time_passed * (self.config.requests_per_minute / 60)
        bucket["tokens"] = min(
            self.config.burst_size,
            bucket["tokens"] + tokens_to_add
        )
        bucket["last_refill"] = now
        
        # Check token availability
        if bucket["tokens"] < 1:
            self.logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False
        
        # Check minute/hour limits
        bucket["minute_requests"].append(now)
        bucket["hour_requests"].append(now)
        
        # Count recent requests
        minute_count = sum(1 for t in bucket["minute_requests"] if now - t < 60)
        hour_count = sum(1 for t in bucket["hour_requests"] if now - t < 3600)
        
        if minute_count > self.config.requests_per_minute:
            self.logger.warning(f"Minute rate limit exceeded for client: {client_id}")
            return False
        
        if hour_count > self.config.requests_per_hour:
            self.logger.warning(f"Hour rate limit exceeded for client: {client_id}")
            return False
        
        # Consume token
        bucket["tokens"] -= 1
        return True
    
    def get_limits_for_client(self, client_id: str) -> Dict[str, Any]:
        """Get current limits for a client"""
        bucket = self.buckets.get(client_id)
        if not bucket:
            return {
                "tokens_remaining": self.config.burst_size,
                "minute_remaining": self.config.requests_per_minute,
                "hour_remaining": self.config.requests_per_hour
            }
        
        now = time.time()
        minute_count = sum(1 for t in bucket["minute_requests"] if now - t < 60)
        hour_count = sum(1 for t in bucket["hour_requests"] if now - t < 3600)
        
        return {
            "tokens_remaining": int(bucket["tokens"]),
            "minute_remaining": self.config.requests_per_minute - minute_count,
            "hour_remaining": self.config.requests_per_hour - hour_count
        }


# ============================================================================
# Content Validator
# ============================================================================

class ContentValidator:
    """Validate and sanitize content"""
    
    # XSS patterns to block
    XSS_PATTERNS = [
        r'javascript:',
        r'on\w+\s*=',  # Event handlers
        r'<script[^>]*>',
        r'</script>',
        r'eval\s*\(',
        r'document\.write',
        r'window\.location',
        r'document\.cookie'
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r'\bUNION\b.*\bSELECT\b',
        r'\bDROP\b.*\bTABLE\b',
        r'\bINSERT\b.*\bINTO\b',
        r'\bDELETE\b.*\bFROM\b',
        r'--\s*$',  # SQL comment
        r'\bOR\b.*=.*'  # OR 1=1 style
    ]
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_content(self, content: str) -> bool:
        """
        Validate content for security issues
        
        Args:
            content: Content to validate
            
        Returns:
            True if content is safe
        """
        if not self.config.content_validation_enabled:
            return True
        
        # Check size
        if len(content) > self.config.max_content_size:
            self.logger.warning(f"Content exceeds max size: {len(content)}")
            return False
        
        # Check for XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                # Allow safe event handlers for MCP intents
                if "dispatchEvent" in content and "CustomEvent" in content:
                    continue
                self.logger.warning(f"XSS pattern detected: {pattern}")
                return False
        
        # Check for SQL injection (in string content)
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self.logger.warning(f"SQL injection pattern detected: {pattern}")
                return False
        
        # Check for blocked paths
        for path in self.config.blocked_paths:
            if path in content:
                self.logger.warning(f"Blocked path detected: {path}")
                return False
        
        # Check for blocked commands
        for command in self.config.blocked_commands:
            if re.search(rf'\b{command}\b', content):
                self.logger.warning(f"Blocked command detected: {command}")
                return False
        
        return True
    
    def sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML content
        
        Args:
            html: Raw HTML
            
        Returns:
            Sanitized HTML
        """
        # Basic sanitization
        sanitized = html
        
        # Remove script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.DOTALL)
        
        # Remove dangerous event handlers (except safe MCP ones)
        def replace_handler(match):
            if "dispatchEvent" in match.group(0):
                return match.group(0)
            return ""
        
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', replace_handler, sanitized)
        
        # Escape dangerous protocols
        sanitized = sanitized.replace("javascript:", "javascript&#58;")
        sanitized = sanitized.replace("data:text/html", "data&#58;text/html")
        
        return sanitized


# ============================================================================
# Authentication Manager
# ============================================================================

class AuthenticationManager:
    """Handle authentication and authorization"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.api_keys: Set[str] = set()
        self.logger = logging.getLogger(__name__)
    
    def validate_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]]
    ) -> bool:
        """
        Validate request authentication
        
        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            
        Returns:
            True if authenticated
        """
        if not self.config.auth_enabled:
            return True
        
        if not headers:
            return False
        
        auth_header = headers.get(self.config.auth_header)
        if not auth_header:
            self.logger.warning("Missing authentication header")
            return False
        
        if self.config.auth_type == "bearer":
            return self._validate_bearer_token(auth_header)
        elif self.config.auth_type == "api_key":
            return self._validate_api_key(auth_header)
        elif self.config.auth_type == "oauth2":
            return self._validate_oauth2_token(auth_header)
        
        return False
    
    def _validate_bearer_token(self, auth_header: str) -> bool:
        """Validate bearer token"""
        if not auth_header.startswith("Bearer "):
            return False
        
        token = auth_header[7:]
        
        # Check if token exists in sessions
        if token in self.sessions:
            session = self.sessions[token]
            
            # Check expiration
            if datetime.now() > session["expires"]:
                del self.sessions[token]
                return False
            
            # Update last activity
            session["last_activity"] = datetime.now()
            return True
        
        return False
    
    def _validate_api_key(self, auth_header: str) -> bool:
        """Validate API key"""
        if auth_header.startswith("Bearer "):
            key = auth_header[7:]
        else:
            key = auth_header
        
        return key in self.api_keys
    
    def _validate_oauth2_token(self, auth_header: str) -> bool:
        """Validate OAuth2 token (placeholder)"""
        # Implement OAuth2 validation based on your provider
        return True
    
    def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Create authentication session
        
        Args:
            user_id: User identifier
            metadata: Session metadata
            
        Returns:
            Session token
        """
        # Generate secure token
        token = hashlib.sha256(
            f"{user_id}-{datetime.now().isoformat()}-{id(self)}".encode()
        ).hexdigest()
        
        # Store session
        self.sessions[token] = {
            "user_id": user_id,
            "created": datetime.now(),
            "expires": datetime.now() + timedelta(seconds=self.config.session_timeout),
            "last_activity": datetime.now(),
            "metadata": metadata or {}
        }
        
        # Enforce max sessions per user
        user_sessions = [
            t for t, s in self.sessions.items()
            if s["user_id"] == user_id
        ]
        
        if len(user_sessions) > self.config.max_sessions_per_user:
            # Remove oldest sessions
            sorted_sessions = sorted(
                user_sessions,
                key=lambda t: self.sessions[t]["created"]
            )
            for token in sorted_sessions[:-self.config.max_sessions_per_user]:
                del self.sessions[token]
        
        return token
    
    def add_api_key(self, key: str):
        """Add API key"""
        self.api_keys.add(key)
    
    def revoke_api_key(self, key: str):
        """Revoke API key"""
        self.api_keys.discard(key)


# ============================================================================
# Security Manager
# ============================================================================

class SecurityManager:
    """Central security management"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.token_budget = TokenBudget(config.max_token_budget)
        self.rate_limiter = RateLimiter(config)
        self.content_validator = ContentValidator(config)
        self.auth_manager = AuthenticationManager(config)
        self.audit_logger = self._setup_audit_logger()
    
    def _setup_audit_logger(self) -> Optional[logging.Logger]:
        """Setup audit logger"""
        if not self.config.audit_enabled:
            return None
        
        logger = logging.getLogger("mcp.audit")
        handler = logging.FileHandler(self.config.audit_log_path)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    def validate_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]]
    ) -> bool:
        """Validate incoming request"""
        result = self.auth_manager.validate_request(method, path, headers)
        
        if self.audit_logger:
            client_id = headers.get("X-Client-Id", "unknown") if headers else "unknown"
            self.audit_logger.info(
                f"Request validation: method={method} path={path} "
                f"client={client_id} result={result}"
            )
        
        return result
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Check rate limit for client"""
        result = self.rate_limiter.check_rate_limit(client_id)
        
        if self.audit_logger and not result:
            self.audit_logger.warning(f"Rate limit exceeded: client={client_id}")
        
        return result
    
    def validate_content(self, content: str) -> bool:
        """Validate content security"""
        return self.content_validator.validate_content(content)
    
    def sanitize_content(self, content: str) -> str:
        """Sanitize content"""
        return self.content_validator.sanitize_html(content)
    
    def check_token_budget(self, tokens: int) -> bool:
        """Check token budget"""
        result = self.token_budget.consume(tokens)
        
        if self.audit_logger and not result:
            self.audit_logger.warning(
                f"Token budget exceeded: requested={tokens} "
                f"remaining={self.token_budget.get_remaining()}"
            )
        
        return result
    
    def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> str:
        """Create user session"""
        token = self.auth_manager.create_session(user_id, metadata)
        
        if self.audit_logger:
            self.audit_logger.info(f"Session created: user={user_id}")
        
        return token
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for responses"""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        }
        
        if self.config.cors_enabled:
            headers["Access-Control-Allow-Origin"] = ", ".join(self.config.allowed_origins)
            headers["Access-Control-Allow-Methods"] = ", ".join(self.config.allowed_methods)
            headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return headers