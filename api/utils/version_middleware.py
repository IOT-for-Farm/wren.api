"""
API Version Middleware

FastAPI middleware for handling API versioning in requests.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .api_version_manager import APIVersionManager


class VersionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API versioning."""
    
    def __init__(self, app):
        super().__init__(app)
        self.version_manager = APIVersionManager()
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add version information."""
        # Extract version from header
        accept_header = request.headers.get("accept", "")
        version = self.version_manager.get_version_from_header(accept_header)
        
        # Add version to request state
        request.state.api_version = version
        
        # Check if version is supported
        if not self.version_manager.is_version_supported(version):
            return Response(
                content=f"Unsupported API version: {version}",
                status_code=400
            )
        
        response = await call_next(request)
        response.headers["X-API-Version"] = version
        return response
