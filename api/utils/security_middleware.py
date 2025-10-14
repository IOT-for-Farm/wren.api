"""
Security Middleware for Wren API

This module provides comprehensive security middleware including rate limiting,
CORS handling, security headers, request validation, and threat detection.
"""

import time
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Callable
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp
import ipaddress
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import logging

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with sliding window"""
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        self.key_func = key_func or self._default_key_func
        
        # Store request timestamps for each client
        self.minute_requests = defaultdict(deque)
        self.hour_requests = defaultdict(deque)
        self.burst_requests = defaultdict(deque)
        
        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP"""
        # Try to get real IP from headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self):
        """Clean up old request timestamps"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        # Clean minute requests older than 1 minute
        minute_cutoff = current_time - 60
        for client_key in list(self.minute_requests.keys()):
            while self.minute_requests[client_key] and self.minute_requests[client_key][0] < minute_cutoff:
                self.minute_requests[client_key].popleft()
            if not self.minute_requests[client_key]:
                del self.minute_requests[client_key]
        
        # Clean hour requests older than 1 hour
        hour_cutoff = current_time - 3600
        for client_key in list(self.hour_requests.keys()):
            while self.hour_requests[client_key] and self.hour_requests[client_key][0] < hour_cutoff:
                self.hour_requests[client_key].popleft()
            if not self.hour_requests[client_key]:
                del self.hour_requests[client_key]
        
        # Clean burst requests older than 1 second
        burst_cutoff = current_time - 1
        for client_key in list(self.burst_requests.keys()):
            while self.burst_requests[client_key] and self.burst_requests[client_key][0] < burst_cutoff:
                self.burst_requests[client_key].popleft()
            if not self.burst_requests[client_key]:
                del self.burst_requests[client_key]
        
        self.last_cleanup = current_time
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with rate limiting"""
        self._cleanup_old_requests()
        
        client_key = self.key_func(request)
        current_time = time.time()
        
        # Check burst limit (requests per second)
        if len(self.burst_requests[client_key]) >= self.burst_limit:
            oldest_request = self.burst_requests[client_key][0]
            if current_time - oldest_request < 1:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Burst rate limit exceeded",
                        "retry_after": 1
                    },
                    headers={"Retry-After": "1"}
                )
        
        # Check minute limit
        if len(self.minute_requests[client_key]) >= self.requests_per_minute:
            oldest_request = self.minute_requests[client_key][0]
            if current_time - oldest_request < 60:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": 60 - int(current_time - oldest_request)
                    },
                    headers={"Retry-After": str(60 - int(current_time - oldest_request))}
                )
        
        # Check hour limit
        if len(self.hour_requests[client_key]) >= self.requests_per_hour:
            oldest_request = self.hour_requests[client_key][0]
            if current_time - oldest_request < 3600:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Hourly rate limit exceeded",
                        "retry_after": 3600 - int(current_time - oldest_request)
                    },
                    headers={"Retry-After": str(3600 - int(current_time - oldest_request))}
                )
        
        # Record request
        self.burst_requests[client_key].append(current_time)
        self.minute_requests[client_key].append(current_time)
        self.hour_requests[client_key].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - len(self.minute_requests[client_key])
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.requests_per_hour - len(self.hour_requests[client_key])
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
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
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.max_content_length = 10 * 1024 * 1024  # 10MB
        self.allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>'
        ]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Validate request before processing"""
        
        # Check HTTP method
        if request.method not in self.allowed_methods:
            return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={"error": "Method not allowed"}
            )
        
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Request entity too large"}
            )
        
        # Validate request path
        if self._is_dangerous_path(request.url.path):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid request path"}
            )
        
        # Check for dangerous patterns in headers
        for header_name, header_value in request.headers.items():
            if self._contains_dangerous_pattern(header_value):
                logger.warning(f"Dangerous pattern detected in header {header_name}: {header_value}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid request headers"}
                )
        
        response = await call_next(request)
        return response
    
    def _is_dangerous_path(self, path: str) -> bool:
        """Check if path contains dangerous patterns"""
        dangerous_paths = [
            r'\.\./',  # Directory traversal
            r'\.\.\\',  # Windows directory traversal
            r'\.\.%2f',  # URL encoded directory traversal
            r'\.\.%5c',  # URL encoded Windows directory traversal
            r'\.\.%252f',  # Double URL encoded
            r'\.\.%255c',  # Double URL encoded Windows
            r'null',  # Null byte
            r'%00',  # URL encoded null byte
        ]
        
        for pattern in dangerous_paths:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_dangerous_pattern(self, value: str) -> bool:
        """Check if value contains dangerous patterns"""
        for pattern in self.dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                return True
        
        return False


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist middleware for restricted endpoints"""
    
    def __init__(self, app: ASGIApp, whitelist: List[str] = None, restricted_paths: List[str] = None):
        super().__init__(app)
        self.whitelist = whitelist or []
        self.restricted_paths = restricted_paths or []
        self.whitelist_networks = []
        
        # Parse IP addresses and networks
        for ip in self.whitelist:
            try:
                self.whitelist_networks.append(ipaddress.ip_network(ip, strict=False))
            except ValueError:
                logger.warning(f"Invalid IP address or network in whitelist: {ip}")
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check IP whitelist for restricted paths"""
        
        # Check if path is restricted
        is_restricted = any(request.url.path.startswith(path) for path in self.restricted_paths)
        
        if is_restricted:
            client_ip = self._get_client_ip(request)
            
            if not self._is_ip_allowed(client_ip):
                logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Access denied from this IP address"}
                )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is in whitelist"""
        if not self.whitelist_networks:
            return True  # No whitelist means all IPs allowed
        
        try:
            client_ip = ipaddress.ip_address(ip)
            return any(client_ip in network for network in self.whitelist_networks)
        except ValueError:
            return False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests for security monitoring"""
    
    def __init__(self, app: ASGIApp, log_sensitive: bool = False):
        super().__init__(app)
        self.log_sensitive = log_sensitive
        self.sensitive_headers = {
            "authorization", "cookie", "x-api-key", "x-auth-token"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Log request details"""
        start_time = time.time()
        
        # Log request
        self._log_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        self._log_response(request, response, process_time)
        
        return response
    
    def _log_request(self, request: Request):
        """Log request details"""
        headers = dict(request.headers)
        
        # Remove sensitive headers
        if not self.log_sensitive:
            for header in self.sensitive_headers:
                if header in headers:
                    headers[header] = "[REDACTED]"
        
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": headers,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Request: {json.dumps(log_data)}")
    
    def _log_response(self, request: Request, response: Response, process_time: float):
        """Log response details"""
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
            "client_ip": request.client.host if request.client else "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Response: {json.dumps(log_data)}")


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    def __init__(self, app: ASGIApp, secret_key: str = None):
        super().__init__(app)
        self.secret_key = secret_key or "default-secret-key"
        self.exempt_methods = {"GET", "HEAD", "OPTIONS"}
        self.exempt_paths = {"/health", "/docs", "/openapi.json"}
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check CSRF token for state-changing requests"""
        
        # Skip CSRF check for exempt methods and paths
        if (request.method in self.exempt_methods or 
            request.url.path in self.exempt_paths):
            return await call_next(request)
        
        # Get CSRF token from header
        csrf_token = request.headers.get("X-CSRF-Token")
        
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF token required"}
            )
        
        # Validate CSRF token
        if not self._validate_csrf_token(csrf_token, request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Invalid CSRF token"}
            )
        
        return await call_next(request)
    
    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token"""
        try:
            # Simple token validation (in production, use proper CSRF library)
            expected_token = self._generate_csrf_token(request)
            return hmac.compare_digest(token, expected_token)
        except Exception:
            return False
    
    def _generate_csrf_token(self, request: Request) -> str:
        """Generate CSRF token"""
        # Simple token generation (in production, use proper CSRF library)
        data = f"{request.client.host}{self.secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()


def setup_security_middleware(app: FastAPI):
    """Setup comprehensive security middleware"""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, 'CORS_ORIGINS', ["*"]),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=getattr(settings, 'ALLOWED_HOSTS', ["*"])
    )
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request validation middleware
    app.add_middleware(RequestValidationMiddleware)
    
    # Add rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_limit=10
    )
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add CSRF protection middleware
    app.add_middleware(CSRFProtectionMiddleware)
    
    logger.info("Security middleware setup completed")
