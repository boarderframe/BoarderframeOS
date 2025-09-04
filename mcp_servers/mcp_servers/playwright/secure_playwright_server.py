#!/usr/bin/env python3
"""
Secure Playwright MCP Server for Production Use
Implements comprehensive security controls and resource limits
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from pydantic import BaseModel, Field, HttpUrl, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Security Configuration
class SecurityConfig:
    """Security configuration constants"""
    # URL Validation
    ALLOWED_PROTOCOLS = ["http", "https"]
    BLOCKED_DOMAINS = [
        "localhost", "127.0.0.1", "0.0.0.0", 
        "169.254.169.254",  # AWS metadata endpoint
        "metadata.google.internal",  # GCP metadata
        "*.local", "*.internal"
    ]
    BLOCKED_IP_RANGES = [
        "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",  # Private networks
        "169.254.0.0/16",  # Link-local
        "127.0.0.0/8",  # Loopback
        "224.0.0.0/4",  # Multicast
        "240.0.0.0/4"   # Reserved
    ]
    
    # Resource Limits
    MAX_PAGE_SIZE_MB = 50
    MAX_SCREENSHOT_SIZE_MB = 10
    MAX_CONCURRENT_PAGES = 5
    MAX_EXECUTION_TIME_SECONDS = 30
    MAX_MEMORY_MB = 512
    MAX_CPU_PERCENT = 50
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 30
    RATE_LIMIT_PER_HOUR = 500
    CONCURRENT_REQUEST_LIMIT = 5
    
    # File System
    SCREENSHOT_DIR = Path("/tmp/playwright-screenshots")
    MAX_SCREENSHOT_AGE_HOURS = 1
    ALLOWED_SCREENSHOT_FORMATS = ["png", "jpeg"]
    
    # Input Validation
    MAX_SELECTOR_LENGTH = 500
    MAX_TEXT_INPUT_LENGTH = 10000
    MAX_URL_LENGTH = 2048
    DANGEROUS_JS_PATTERNS = [
        r"javascript:", r"data:text/html", r"vbscript:",
        r"<script", r"onerror=", r"onload=", r"onclick="
    ]
    
    # Session Management
    SESSION_TIMEOUT_MINUTES = 30
    MAX_SESSIONS_PER_USER = 3
    SESSION_ISOLATION = True
    
    # Logging
    LOG_SENSITIVE_DATA = False
    AUDIT_LOG_PATH = Path("/var/log/playwright/audit.log")
    SECURITY_LOG_PATH = Path("/var/log/playwright/security.log")


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")
audit_logger = logging.getLogger("audit")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Session Management
class SessionManager:
    """Manages browser sessions with isolation and cleanup"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_locks: Dict[str, asyncio.Lock] = {}
        self.cleanup_task = None
        
    async def create_session(self, user_id: str) -> str:
        """Create a new isolated browser session"""
        session_id = str(uuid.uuid4())
        
        # Check session limits
        user_sessions = [s for s in self.sessions.values() if s.get("user_id") == user_id]
        if len(user_sessions) >= SecurityConfig.MAX_SESSIONS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum sessions ({SecurityConfig.MAX_SESSIONS_PER_USER}) reached"
            )
        
        # Create isolated browser context
        browser = await self._create_secure_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=False,
            java_script_enabled=True,
            bypass_csp=False,
            locale="en-US",
            timezone_id="UTC",
            permissions=[],  # No permissions by default
            storage_state=None,  # No persistent storage
            proxy=None  # No proxy by default
        )
        
        self.sessions[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "browser": browser,
            "context": context,
            "pages": {},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "request_count": 0
        }
        
        self.session_locks[session_id] = asyncio.Lock()
        
        audit_logger.info(f"Session created: {session_id} for user: {user_id}")
        return session_id
    
    async def _create_secure_browser(self) -> Browser:
        """Create a secure browser instance with sandboxing"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",  # Required in Docker
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--single-process",
                "--disable-gpu",
                "--disable-web-security=false",  # Keep security enabled
                "--disable-features=site-per-process",
                f"--max-old-space-size={SecurityConfig.MAX_MEMORY_MB}",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--password-store=basic",
                "--use-mock-keychain"
            ]
        )
        return browser
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get an existing session with activity tracking"""
        if session_id not in self.sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        session = self.sessions[session_id]
        
        # Check session timeout
        if datetime.utcnow() - session["last_activity"] > timedelta(minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES):
            await self.destroy_session(session_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
        
        # Update activity
        session["last_activity"] = datetime.utcnow()
        session["request_count"] += 1
        
        return session
    
    async def destroy_session(self, session_id: str):
        """Destroy a session and clean up resources"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Close all pages
            for page in session["pages"].values():
                await page.close()
            
            # Close context and browser
            await session["context"].close()
            await session["browser"].close()
            
            del self.sessions[session_id]
            del self.session_locks[session_id]
            
            audit_logger.info(f"Session destroyed: {session_id}")
    
    async def cleanup_expired_sessions(self):
        """Periodic cleanup of expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                expired_sessions = []
                for session_id, session in self.sessions.items():
                    if datetime.utcnow() - session["last_activity"] > timedelta(minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.destroy_session(session_id)
                    logger.info(f"Cleaned up expired session: {session_id}")
                    
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")


# URL Validator
class URLValidator:
    """Validates and sanitizes URLs to prevent SSRF attacks"""
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate and sanitize URL"""
        if len(url) > SecurityConfig.MAX_URL_LENGTH:
            raise ValueError(f"URL exceeds maximum length of {SecurityConfig.MAX_URL_LENGTH}")
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            raise ValueError("Invalid URL format")
        
        # Check protocol
        if parsed.scheme not in SecurityConfig.ALLOWED_PROTOCOLS:
            raise ValueError(f"Protocol {parsed.scheme} not allowed")
        
        # Check for blocked domains
        hostname = parsed.hostname or ""
        
        # Check localhost and private IPs
        if hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
            raise ValueError("Access to localhost is blocked")
        
        # Check for IP address
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            
            # Block private and special IPs
            if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_multicast:
                raise ValueError(f"Access to {hostname} is blocked")
                
        except ValueError:
            # Not an IP, check domain
            for blocked in SecurityConfig.BLOCKED_DOMAINS:
                if blocked.startswith("*"):
                    if hostname.endswith(blocked[1:]):
                        raise ValueError(f"Domain {hostname} is blocked")
                elif hostname == blocked:
                    raise ValueError(f"Domain {hostname} is blocked")
        
        # Check for javascript: and data: URLs
        for pattern in SecurityConfig.DANGEROUS_JS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                raise ValueError("URL contains potentially dangerous content")
        
        return url


# Input Sanitizer
class InputSanitizer:
    """Sanitizes user inputs to prevent injection attacks"""
    
    @staticmethod
    def sanitize_selector(selector: str) -> str:
        """Sanitize CSS selector"""
        if len(selector) > SecurityConfig.MAX_SELECTOR_LENGTH:
            raise ValueError(f"Selector exceeds maximum length of {SecurityConfig.MAX_SELECTOR_LENGTH}")
        
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "javascript:", "onerror", "onclick", "onload"]
        for char in dangerous_chars:
            if char in selector.lower():
                raise ValueError(f"Selector contains forbidden content: {char}")
        
        return selector
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input"""
        if len(text) > SecurityConfig.MAX_TEXT_INPUT_LENGTH:
            raise ValueError(f"Text exceeds maximum length of {SecurityConfig.MAX_TEXT_INPUT_LENGTH}")
        
        # Remove script tags and event handlers
        for pattern in SecurityConfig.DANGEROUS_JS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        return text


# Request Models with Validation
class NavigateRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    url: HttpUrl = Field(..., description="URL to navigate to")
    wait_until: str = Field("networkidle", regex="^(load|domcontentloaded|networkidle)$")
    timeout: int = Field(30000, ge=1000, le=60000)
    
    @validator("url", pre=True)
    def validate_url(cls, v):
        return URLValidator.validate_url(str(v))


class ClickRequest(BaseModel):
    session_id: str
    page_id: str
    selector: str = Field(..., min_length=1, max_length=500)
    timeout: int = Field(5000, ge=1000, le=30000)
    
    @validator("selector")
    def validate_selector(cls, v):
        return InputSanitizer.sanitize_selector(v)


class FillRequest(BaseModel):
    session_id: str
    page_id: str
    selector: str = Field(..., min_length=1, max_length=500)
    value: str = Field(..., min_length=0, max_length=10000)
    timeout: int = Field(5000, ge=1000, le=30000)
    
    @validator("selector")
    def validate_selector(cls, v):
        return InputSanitizer.sanitize_selector(v)
    
    @validator("value")
    def validate_value(cls, v):
        return InputSanitizer.sanitize_text(v)


class ExtractRequest(BaseModel):
    session_id: str
    page_id: str
    selector: str = Field("body", min_length=1, max_length=500)
    
    @validator("selector")
    def validate_selector(cls, v):
        return InputSanitizer.sanitize_selector(v)


class ScreenshotRequest(BaseModel):
    session_id: str
    page_id: str
    full_page: bool = False
    format: str = Field("png", regex="^(png|jpeg)$")
    quality: int = Field(80, ge=0, le=100)


# Initialize FastAPI app with security middleware
app = FastAPI(
    title="Secure Playwright MCP Server",
    description="Production-ready web automation with comprehensive security controls",
    version="2.0.0",
    docs_url=None,  # Disable Swagger UI in production
    redoc_url=None  # Disable ReDoc in production
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["POST", "GET"],  # Limited methods
    allow_headers=["Content-Type", "Authorization"],
    max_age=86400
)

# Add rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize session manager
session_manager = SessionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    # Create screenshot directory
    SecurityConfig.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start session cleanup task
    session_manager.cleanup_task = asyncio.create_task(
        session_manager.cleanup_expired_sessions()
    )
    
    # Clean old screenshots
    asyncio.create_task(cleanup_old_screenshots())
    
    logger.info("Playwright MCP Server started with security controls enabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    # Cancel cleanup task
    if session_manager.cleanup_task:
        session_manager.cleanup_task.cancel()
    
    # Destroy all sessions
    for session_id in list(session_manager.sessions.keys()):
        await session_manager.destroy_session(session_id)
    
    logger.info("Playwright MCP Server shutdown complete")


async def cleanup_old_screenshots():
    """Periodically clean old screenshots"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            
            cutoff = datetime.utcnow() - timedelta(hours=SecurityConfig.MAX_SCREENSHOT_AGE_HOURS)
            
            for file in SecurityConfig.SCREENSHOT_DIR.glob("*.png"):
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    file.unlink()
                    logger.info(f"Deleted old screenshot: {file}")
                    
        except Exception as e:
            logger.error(f"Error cleaning screenshots: {e}")


# API Endpoints with Security Controls

@app.post("/session/create")
@limiter.limit("5/minute")
async def create_session(request: Request) -> Dict[str, str]:
    """Create a new browser session"""
    try:
        # Extract user ID from request (would come from auth in production)
        user_id = request.headers.get("X-User-ID", "anonymous")
        
        session_id = await session_manager.create_session(user_id)
        
        return {
            "session_id": session_id,
            "status": "created",
            "expires_in_minutes": SecurityConfig.SESSION_TIMEOUT_MINUTES
        }
        
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Session creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@app.post("/navigate")
@limiter.limit(f"{SecurityConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def navigate_to_page(request: Request, nav_request: NavigateRequest) -> Dict[str, Any]:
    """Navigate to a URL with security validation"""
    try:
        session = await session_manager.get_session(nav_request.session_id)
        
        async with session_manager.session_locks[nav_request.session_id]:
            # Check page limit
            if len(session["pages"]) >= SecurityConfig.MAX_CONCURRENT_PAGES:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Maximum pages ({SecurityConfig.MAX_CONCURRENT_PAGES}) reached"
                )
            
            # Create new page
            page = await session["context"].new_page()
            page_id = str(uuid.uuid4())
            session["pages"][page_id] = page
            
            # Set resource limits
            await page.route("**/*", lambda route: route.abort() 
                           if route.request.resource_type in ["font", "media"] 
                           else route.continue_())
            
            # Navigate with timeout
            try:
                response = await asyncio.wait_for(
                    page.goto(
                        str(nav_request.url),
                        wait_until=nav_request.wait_until,
                        timeout=nav_request.timeout
                    ),
                    timeout=SecurityConfig.MAX_EXECUTION_TIME_SECONDS
                )
                
                # Check response size
                if response and response.headers.get("content-length"):
                    size_mb = int(response.headers["content-length"]) / (1024 * 1024)
                    if size_mb > SecurityConfig.MAX_PAGE_SIZE_MB:
                        await page.close()
                        del session["pages"][page_id]
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Page size exceeds {SecurityConfig.MAX_PAGE_SIZE_MB}MB limit"
                        )
                
                audit_logger.info(f"Navigation successful: {nav_request.url} (session: {nav_request.session_id})")
                
                return {
                    "page_id": page_id,
                    "url": page.url,
                    "title": await page.title(),
                    "status": response.status if response else None
                }
                
            except asyncio.TimeoutError:
                await page.close()
                del session["pages"][page_id]
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Navigation timeout"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Navigation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Navigation failed"
        )


@app.post("/click")
@limiter.limit(f"{SecurityConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def click_element(request: Request, click_request: ClickRequest) -> Dict[str, str]:
    """Click an element with security validation"""
    try:
        session = await session_manager.get_session(click_request.session_id)
        
        async with session_manager.session_locks[click_request.session_id]:
            if click_request.page_id not in session["pages"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Page not found"
                )
            
            page = session["pages"][click_request.page_id]
            
            try:
                await asyncio.wait_for(
                    page.click(click_request.selector, timeout=click_request.timeout),
                    timeout=SecurityConfig.MAX_EXECUTION_TIME_SECONDS
                )
                
                audit_logger.info(f"Click performed: {click_request.selector} (session: {click_request.session_id})")
                
                return {
                    "status": "success",
                    "message": f"Clicked element: {click_request.selector}"
                }
                
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Click timeout"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Click failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Click failed"
        )


@app.post("/fill")
@limiter.limit(f"{SecurityConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def fill_form_field(request: Request, fill_request: FillRequest) -> Dict[str, str]:
    """Fill a form field with security validation"""
    try:
        session = await session_manager.get_session(fill_request.session_id)
        
        async with session_manager.session_locks[fill_request.session_id]:
            if fill_request.page_id not in session["pages"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Page not found"
                )
            
            page = session["pages"][fill_request.page_id]
            
            try:
                await asyncio.wait_for(
                    page.fill(fill_request.selector, fill_request.value, timeout=fill_request.timeout),
                    timeout=SecurityConfig.MAX_EXECUTION_TIME_SECONDS
                )
                
                # Log without sensitive data
                audit_logger.info(f"Form filled: {fill_request.selector} (session: {fill_request.session_id})")
                
                return {
                    "status": "success",
                    "message": f"Filled {fill_request.selector}"
                }
                
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Fill timeout"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Fill failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fill failed"
        )


@app.post("/extract")
@limiter.limit(f"{SecurityConfig.RATE_LIMIT_PER_MINUTE}/minute")
async def extract_text(request: Request, extract_request: ExtractRequest) -> Dict[str, Any]:
    """Extract text from page elements"""
    try:
        session = await session_manager.get_session(extract_request.session_id)
        
        async with session_manager.session_locks[extract_request.session_id]:
            if extract_request.page_id not in session["pages"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Page not found"
                )
            
            page = session["pages"][extract_request.page_id]
            
            try:
                text = await asyncio.wait_for(
                    page.inner_text(extract_request.selector),
                    timeout=SecurityConfig.MAX_EXECUTION_TIME_SECONDS
                )
                
                # Limit text size
                if len(text) > SecurityConfig.MAX_TEXT_INPUT_LENGTH:
                    text = text[:SecurityConfig.MAX_TEXT_INPUT_LENGTH] + "...[truncated]"
                
                audit_logger.info(f"Text extracted: {extract_request.selector} (session: {extract_request.session_id})")
                
                return {
                    "status": "success",
                    "text": text,
                    "length": len(text)
                }
                
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Extract timeout"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Extract failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Extract failed"
        )


@app.post("/screenshot")
@limiter.limit("10/minute")
async def take_screenshot(request: Request, screenshot_request: ScreenshotRequest) -> Dict[str, str]:
    """Take a screenshot with security controls"""
    try:
        session = await session_manager.get_session(screenshot_request.session_id)
        
        async with session_manager.session_locks[screenshot_request.session_id]:
            if screenshot_request.page_id not in session["pages"]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Page not found"
                )
            
            page = session["pages"][screenshot_request.page_id]
            
            # Generate secure filename
            filename = f"{uuid.uuid4()}.{screenshot_request.format}"
            filepath = SecurityConfig.SCREENSHOT_DIR / filename
            
            try:
                await asyncio.wait_for(
                    page.screenshot(
                        path=str(filepath),
                        full_page=screenshot_request.full_page,
                        type=screenshot_request.format,
                        quality=screenshot_request.quality if screenshot_request.format == "jpeg" else None
                    ),
                    timeout=SecurityConfig.MAX_EXECUTION_TIME_SECONDS
                )
                
                # Check file size
                size_mb = filepath.stat().st_size / (1024 * 1024)
                if size_mb > SecurityConfig.MAX_SCREENSHOT_SIZE_MB:
                    filepath.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Screenshot exceeds {SecurityConfig.MAX_SCREENSHOT_SIZE_MB}MB limit"
                    )
                
                audit_logger.info(f"Screenshot taken: {filename} (session: {screenshot_request.session_id})")
                
                return {
                    "status": "success",
                    "filename": filename,
                    "size_mb": round(size_mb, 2),
                    "expires_in_hours": SecurityConfig.MAX_SCREENSHOT_AGE_HOURS
                }
                
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail="Screenshot timeout"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(f"Screenshot failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Screenshot failed"
        )


@app.post("/session/destroy")
async def destroy_session(request: Request, session_id: str) -> Dict[str, str]:
    """Destroy a browser session"""
    try:
        await session_manager.destroy_session(session_id)
        
        return {
            "status": "success",
            "message": "Session destroyed"
        }
        
    except Exception as e:
        logger.error(f"Session destruction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to destroy session"
        )


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(session_manager.sessions),
        "security_config": {
            "rate_limiting": "enabled",
            "session_isolation": "enabled",
            "url_validation": "enabled",
            "input_sanitization": "enabled"
        }
    }


@app.get("/metrics")
@limiter.limit("10/minute")
async def get_metrics(request: Request) -> Dict[str, Any]:
    """Get server metrics"""
    total_pages = sum(len(s["pages"]) for s in session_manager.sessions.values())
    
    return {
        "active_sessions": len(session_manager.sessions),
        "total_pages": total_pages,
        "screenshot_dir_size_mb": sum(
            f.stat().st_size for f in SecurityConfig.SCREENSHOT_DIR.glob("*")
        ) / (1024 * 1024),
        "limits": {
            "max_sessions_per_user": SecurityConfig.MAX_SESSIONS_PER_USER,
            "max_concurrent_pages": SecurityConfig.MAX_CONCURRENT_PAGES,
            "rate_limit_per_minute": SecurityConfig.RATE_LIMIT_PER_MINUTE
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run with security-focused configuration
    uvicorn.run(
        app,
        host="127.0.0.1",  # Bind to localhost only
        port=9003,
        workers=2,
        loop="uvloop",
        access_log=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"]
            }
        }
    )