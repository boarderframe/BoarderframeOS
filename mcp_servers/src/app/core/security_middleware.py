"""
FastAPI Security Middleware Integration for MCP-UI System
Comprehensive middleware stack with OWASP compliance
"""

import time
import uuid
import json
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp
import redis

from app.core.enhanced_security import (
    SecurityConfig,
    EnhancedJWTManager,
    RBACEnforcer,
    SessionManager,
    XSSProtection,
    CSRFProtection,
    RateLimiter,
    InputValidator,
    Permission
)

logger = logging.getLogger(__name__)

# ============================================================================
# COMPREHENSIVE SECURITY MIDDLEWARE STACK
# ============================================================================

class SecurityMiddlewareStack:
    """Orchestrates all security middleware components"""
    
    def __init__(self, app: ASGIApp, redis_client: redis.Redis):
        self.app = app
        self.redis = redis_client
        self.config = SecurityConfig()
        
        # Initialize security components
        self.jwt_manager = EnhancedJWTManager(redis_client)
        self.rbac = RBACEnforcer()
        self.session_manager = SessionManager(redis_client)
        self.rate_limiter = RateLimiter(redis_client)
        self.csrf = CSRFProtection()
        
        # Configure middleware stack (order matters!)
        self._configure_middleware_stack()
    
    def _configure_middleware_stack(self):
        """Configure middleware in correct order"""
        # 1. Request ID and correlation
        self.app = RequestCorrelationMiddleware(self.app)
        
        # 2. Security headers (early in pipeline)
        from app.core.enhanced_security import SecurityHeadersMiddleware
        self.app = SecurityHeadersMiddleware(self.app, self.config)
        
        # 3. Rate limiting (before auth to prevent brute force)
        self.app = RateLimitMiddleware(self.app, self.rate_limiter)
        
        # 4. Request validation and sanitization
        self.app = RequestValidationMiddleware(self.app)
        
        # 5. Authentication
        self.app = JWTAuthMiddleware(self.app, self.jwt_manager, self.session_manager)
        
        # 6. CSRF protection
        self.app = CSRFMiddleware(self.app, self.csrf)
        
        # 7. Authorization (RBAC)
        self.app = RBACMiddleware(self.app, self.rbac)
        
        # 8. Audit logging
        self.app = AuditLoggingMiddleware(self.app, self.redis)
        
        # 9. Response sanitization
        self.app = ResponseSanitizationMiddleware(self.app)

# ============================================================================
# REQUEST CORRELATION MIDDLEWARE
# ============================================================================

class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Adds correlation ID for request tracking"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Add request timestamp
        request.state.request_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Add processing time
        processing_time = time.time() - request.state.request_time
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
        
        return response

# ============================================================================
# RATE LIMIT MIDDLEWARE
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting with multiple strategies"""
    
    def __init__(self, app: ASGIApp, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        
        # Exempt paths from rate limiting
        self.exempt_paths = {
            "/health",
            "/api/v1/docs",
            "/api/v1/openapi.json",
            "/api/v1/redoc"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Determine identifier (IP or user ID)
        identifier = self._get_identifier(request)
        
        # Check rate limits
        minute_check = self.rate_limiter.check_rate_limit(identifier, "minute")
        hour_check = self.rate_limiter.check_rate_limit(identifier, "hour")
        
        # If exceeded, return 429
        if minute_check["exceeded"] or hour_check["exceeded"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(minute_check["limit"]),
                    "X-RateLimit-Remaining": str(minute_check["remaining"]),
                    "X-RateLimit-Reset": str(minute_check["reset_in"]),
                    "Retry-After": str(minute_check["reset_in"])
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(minute_check["limit"])
        response.headers["X-RateLimit-Remaining"] = str(minute_check["remaining"])
        response.headers["X-RateLimit-Reset"] = str(minute_check["reset_in"])
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting"""
        # Try to get user ID from request state
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id')}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"

# ============================================================================
# REQUEST VALIDATION MIDDLEWARE
# ============================================================================

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validates and sanitizes incoming requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.max_body_size = 10 * 1024 * 1024  # 10MB
        self.validator = InputValidator()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request body too large"
            )
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").lower()
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"
            ]
            
            if not any(ct in content_type for ct in allowed_types):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported media type"
                )
        
        # Store raw body for later validation
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            request.state.raw_body = body
            
            # Validate JSON structure if applicable
            if "application/json" in request.headers.get("content-type", ""):
                try:
                    json_body = json.loads(body)
                    # Sanitize JSON data
                    sanitized = XSSProtection.sanitize_json(json_body)
                    request.state.sanitized_json = sanitized
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON"
                    )
        
        return await call_next(request)

# ============================================================================
# JWT AUTHENTICATION MIDDLEWARE
# ============================================================================

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT authentication with session validation"""
    
    def __init__(
        self,
        app: ASGIApp,
        jwt_manager: EnhancedJWTManager,
        session_manager: SessionManager
    ):
        super().__init__(app)
        self.jwt_manager = jwt_manager
        self.session_manager = session_manager
        
        # Public endpoints that don't require auth
        self.public_paths = {
            "/health",
            "/api/v1/docs",
            "/api/v1/openapi.json",
            "/api/v1/redoc",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/forgot-password"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip auth for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)
        
        # Extract token from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header.replace("Bearer ", "")
        
        # Verify JWT token
        payload = self.jwt_manager.verify_token(token, "access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate session if session-based auth is enabled
        session_id = request.cookies.get("session_id")
        if session_id:
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("User-Agent", "")
            
            session = self.session_manager.validate_session(
                session_id,
                client_ip,
                user_agent
            )
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )
            
            # Ensure session user matches JWT user
            if session["user_id"] != payload["sub"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session user mismatch"
                )
        
        # Store user info in request state
        request.state.user = {
            "id": payload["sub"],
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "metadata": payload.get("metadata", {})
        }
        
        return await call_next(request)

# ============================================================================
# CSRF MIDDLEWARE
# ============================================================================

class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing operations"""
    
    def __init__(self, app: ASGIApp, csrf: CSRFProtection):
        super().__init__(app)
        self.csrf = csrf
        
        # Methods that require CSRF protection
        self.protected_methods = {"POST", "PUT", "PATCH", "DELETE"}
        
        # Paths exempt from CSRF
        self.exempt_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip CSRF for GET, HEAD, OPTIONS
        if request.method not in self.protected_methods:
            return await call_next(request)
        
        # Skip for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Validate CSRF token
        csrf_header = request.headers.get("X-CSRF-Token")
        csrf_cookie = request.cookies.get("csrf_token")
        
        if not self.csrf.validate_csrf_token(csrf_header, csrf_cookie):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed"
            )
        
        # Process request
        response = await call_next(request)
        
        # Set new CSRF token for next request
        if request.method == "GET" and request.url.path not in self.exempt_paths:
            new_token = self.csrf.generate_csrf_token()
            cookie_params = self.csrf.get_csrf_cookie_params()
            response.set_cookie(value=new_token, **cookie_params)
        
        return response

# ============================================================================
# RBAC MIDDLEWARE
# ============================================================================

class RBACMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware"""
    
    def __init__(self, app: ASGIApp, rbac: RBACEnforcer):
        super().__init__(app)
        self.rbac = rbac
        
        # Path to permission mapping
        self.permission_map = {
            # Server endpoints
            ("GET", "/api/v1/servers"): Permission.SERVER_VIEW,
            ("POST", "/api/v1/servers"): Permission.SERVER_CREATE,
            ("PUT", "/api/v1/servers"): Permission.SERVER_UPDATE,
            ("DELETE", "/api/v1/servers"): Permission.SERVER_DELETE,
            ("POST", "/api/v1/servers/execute"): Permission.SERVER_EXECUTE,
            
            # Configuration endpoints
            ("GET", "/api/v1/config"): Permission.CONFIG_VIEW,
            ("PUT", "/api/v1/config"): Permission.CONFIG_UPDATE,
            ("DELETE", "/api/v1/config"): Permission.CONFIG_DELETE,
            
            # User endpoints
            ("GET", "/api/v1/users"): Permission.USER_VIEW,
            ("POST", "/api/v1/users"): Permission.USER_CREATE,
            ("PUT", "/api/v1/users"): Permission.USER_UPDATE,
            ("DELETE", "/api/v1/users"): Permission.USER_DELETE,
            
            # Admin endpoints
            ("GET", "/api/v1/audit"): Permission.AUDIT_VIEW,
            ("GET", "/api/v1/metrics"): Permission.METRICS_VIEW,
            ("POST", "/api/v1/security"): Permission.SECURITY_MANAGE
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip if no user in request state
        if not hasattr(request.state, "user"):
            return await call_next(request)
        
        # Get required permission for endpoint
        path_key = (request.method, self._normalize_path(request.url.path))
        required_permission = self.permission_map.get(path_key)
        
        if required_permission:
            # Check if user has permission
            user_roles = request.state.user.get("roles", [])
            
            if not self.rbac.check_permission(user_roles, required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {required_permission.value}"
                )
            
            # Store effective permissions in request state
            request.state.user["effective_permissions"] = list(
                self.rbac.get_effective_permissions(user_roles)
            )
        
        return await call_next(request)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for permission checking"""
        # Remove trailing slashes and IDs
        path = path.rstrip("/")
        
        # Replace UUIDs and numeric IDs with placeholder
        import re
        path = re.sub(r'/[a-f0-9-]{36}', '', path)  # UUID
        path = re.sub(r'/\d+', '', path)  # Numeric ID
        
        return path

# ============================================================================
# AUDIT LOGGING MIDDLEWARE
# ============================================================================

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive audit logging for compliance"""
    
    def __init__(self, app: ASGIApp, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        
        # Actions that require audit logging
        self.auditable_methods = {"POST", "PUT", "PATCH", "DELETE"}
        
        # Sensitive paths that always require logging
        self.sensitive_paths = {
            "/api/v1/auth",
            "/api/v1/users",
            "/api/v1/security",
            "/api/v1/config"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Determine if request should be audited
        should_audit = (
            request.method in self.auditable_methods or
            any(request.url.path.startswith(path) for path in self.sensitive_paths)
        )
        
        if should_audit:
            # Capture request details
            audit_entry = self._create_audit_entry(request)
            
            try:
                # Process request
                response = await call_next(request)
                
                # Update audit entry with response
                audit_entry["response"] = {
                    "status_code": response.status_code,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Log success
                audit_entry["result"] = "success"
                
            except Exception as e:
                # Log failure
                audit_entry["result"] = "failure"
                audit_entry["error"] = str(e)
                response = Response(
                    content=json.dumps({"detail": "Internal server error"}),
                    status_code=500,
                    media_type="application/json"
                )
            
            # Store audit log
            self._store_audit_log(audit_entry)
            
            return response
        
        return await call_next(request)
    
    def _create_audit_entry(self, request: Request) -> Dict[str, Any]:
        """Create audit log entry"""
        user_info = getattr(request.state, "user", {})
        
        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": getattr(request.state, "correlation_id", None),
            "user": {
                "id": user_info.get("id", "anonymous"),
                "roles": user_info.get("roles", [])
            },
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("User-Agent", "")
            }
        }
    
    def _store_audit_log(self, entry: Dict[str, Any]):
        """Store audit log entry"""
        # Store in Redis with TTL based on config
        key = f"audit:{entry['id']}"
        ttl = SecurityConfig().AUDIT_LOG_RETENTION_DAYS * 86400
        
        self.redis.setex(
            key,
            ttl,
            json.dumps(entry)
        )
        
        # Add to audit index by date
        date_key = f"audit:index:{entry['timestamp'][:10]}"
        self.redis.sadd(date_key, entry['id'])
        self.redis.expire(date_key, ttl)
        
        # Log to system logger
        logger.info(f"Audit log: {json.dumps(entry)}")

# ============================================================================
# RESPONSE SANITIZATION MIDDLEWARE
# ============================================================================

class ResponseSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitizes response data to prevent XSS"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Only process JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                # Parse and sanitize JSON
                data = json.loads(body)
                sanitized = XSSProtection.sanitize_json(data)
                
                # Create new response with sanitized data
                return Response(
                    content=json.dumps(sanitized),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json"
                )
            except json.JSONDecodeError:
                # Return original response if not valid JSON
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
        
        return response

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'SecurityMiddlewareStack',
    'RequestCorrelationMiddleware',
    'RateLimitMiddleware',
    'RequestValidationMiddleware',
    'JWTAuthMiddleware',
    'CSRFMiddleware',
    'RBACMiddleware',
    'AuditLoggingMiddleware',
    'ResponseSanitizationMiddleware'
]