"""
Authentication Middleware

FastAPI middleware for authentication and authorization.
"""

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Optional
import jwt
from datetime import datetime, timedelta


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""
    
    def __init__(self, app, secret_key: str, algorithm: str = "HS256"):
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.excluded_paths = ["/docs", "/openapi.json", "/health"]
    
    async def dispatch(self, request: Request, call_next):
        """Process authentication for requests."""
        # Skip auth for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Get token from header
        token = self._extract_token(request)
        if not token:
            return Response(
                content="Authentication required",
                status_code=401
            )
        
        # Validate token
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            request.state.user_id = payload.get("user_id")
            request.state.user_roles = payload.get("roles", [])
        except jwt.ExpiredSignatureError:
            return Response(
                content="Token expired",
                status_code=401
            )
        except jwt.InvalidTokenError:
            return Response(
                content="Invalid token",
                status_code=401
            )
        
        response = await call_next(request)
        return response
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None


class RoleMiddleware(BaseHTTPMiddleware):
    """Middleware for role-based access control."""
    
    def __init__(self, app, required_roles: List[str] = None):
        super().__init__(app)
        self.required_roles = required_roles or []
    
    async def dispatch(self, request: Request, call_next):
        """Check user roles for authorization."""
        if not hasattr(request.state, 'user_roles'):
            return Response(
                content="Authentication required",
                status_code=401
            )
        
        user_roles = getattr(request.state, 'user_roles', [])
        if not any(role in user_roles for role in self.required_roles):
            return Response(
                content="Insufficient permissions",
                status_code=403
            )
        
        return await call_next(request)
