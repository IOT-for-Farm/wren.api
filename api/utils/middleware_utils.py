"""
Middleware Utility Functions

Helper functions for middleware configuration and management.
"""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI
from .request_middleware import RequestLoggingMiddleware, RequestEnhancementMiddleware, CORSMiddleware


def setup_middleware_stack(app: FastAPI, config: Dict[str, Any] = None) -> None:
    """Setup complete middleware stack for the application."""
    if config is None:
        config = {}
    
    # Request enhancement (should be first)
    app.add_middleware(RequestEnhancementMiddleware)
    
    # Request logging
    if config.get("enable_logging", True):
        app.add_middleware(RequestLoggingMiddleware)
    
    # CORS
    if config.get("enable_cors", True):
        cors_config = config.get("cors", {})
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_config.get("origins", ["*"]),
            allow_methods=cors_config.get("methods", ["GET", "POST", "PUT", "DELETE"])
        )


def create_middleware_config(
    enable_logging: bool = True,
    enable_cors: bool = True,
    cors_origins: List[str] = None,
    cors_methods: List[str] = None
) -> Dict[str, Any]:
    """Create middleware configuration dictionary."""
    if cors_origins is None:
        cors_origins = ["*"]
    if cors_methods is None:
        cors_methods = ["GET", "POST", "PUT", "DELETE"]
    
    return {
        "enable_logging": enable_logging,
        "enable_cors": enable_cors,
        "cors": {
            "origins": cors_origins,
            "methods": cors_methods
        }
    }


def get_middleware_info(app: FastAPI) -> List[Dict[str, Any]]:
    """Get information about configured middleware."""
    middleware_info = []
    
    for middleware in app.user_middleware:
        info = {
            "class": middleware.cls.__name__,
            "options": middleware.options,
            "position": len(middleware_info)
        }
        middleware_info.append(info)
    
    return middleware_info
