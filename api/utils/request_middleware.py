"""
Request Processing Middleware

Middleware utilities for request processing and enhancement.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Log request details and processing time."""
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
        
        return response


class RequestEnhancementMiddleware(BaseHTTPMiddleware):
    """Middleware to enhance request with additional data."""
    
    async def dispatch(self, request: Request, call_next):
        """Add request metadata and processing info."""
        # Add request ID
        request.state.request_id = f"req_{int(time.time() * 1000)}"
        
        # Add client IP
        request.state.client_ip = request.client.host if request.client else "unknown"
        
        # Add user agent
        request.state.user_agent = request.headers.get("user-agent", "unknown")
        
        # Add timestamp
        request.state.timestamp = time.time()
        
        response = await call_next(request)
        
        # Add response headers
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time"] = str(time.time() - request.state.timestamp)
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with configurable options."""
    
    def __init__(self, app, allow_origins: list = None, allow_methods: list = None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE"]
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS headers."""
        response = await call_next(request)
        
        origin = request.headers.get("origin")
        if origin in self.allow_origins or "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response
