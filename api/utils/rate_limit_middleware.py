"""
Rate Limit Middleware

FastAPI middleware for rate limiting requests.
"""

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from .rate_limiter import RateLimiter
import time


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(max_requests, window_seconds)
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(client_id):
            reset_time = self.rate_limiter.get_reset_time(client_id)
            remaining = self.rate_limiter.get_remaining_requests(client_id)
            
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(self.rate_limiter.max_requests),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(int(reset_time)) if reset_time else "0"
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try to get real IP from headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"
