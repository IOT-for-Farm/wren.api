"""
OpenAPI Documentation Enhancements for Wren API

This module provides comprehensive OpenAPI documentation enhancements including
custom schemas, response models, error documentation, and interactive API
documentation features.
"""

from typing import Any, Dict, List, Optional, Union, Type
from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, create_model
from enum import Enum
import json
from datetime import datetime

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class APIResponseStatus(str, Enum):
    """Standard API response statuses"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class APIErrorCode(str, Enum):
    """Standard API error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class StandardResponseModel(BaseModel):
    """Standard API response model"""
    status_code: int = Field(..., description="HTTP status code")
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: str = Field(..., description="Unique request identifier")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponseModel(StandardResponseModel):
    """Success response model"""
    data: Optional[Union[Dict[str, Any], List[Any]]] = Field(None, description="Response data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ErrorResponseModel(StandardResponseModel):
    """Error response model"""
    error: Dict[str, Any] = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "status_code": 400,
                "success": False,
                "message": "Validation failed",
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req_123456789",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "details": {
                        "field_errors": {
                            "email": ["Invalid email format"],
                            "password": ["Password must be at least 8 characters"]
                        }
                    }
                }
            }
        }


class PaginationModel(BaseModel):
    """Pagination metadata model"""
    current_page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    next_page: Optional[str] = Field(None, description="URL for next page")
    previous_page: Optional[str] = Field(None, description="URL for previous page")
    first_page: str = Field(..., description="URL for first page")
    last_page: Optional[str] = Field(None, description="URL for last page")
    page_range: Dict[str, int] = Field(..., description="Current page range")


class PaginatedResponseModel(SuccessResponseModel):
    """Paginated response model"""
    pagination: PaginationModel = Field(..., description="Pagination metadata")


class APIEndpointInfo(BaseModel):
    """API endpoint information model"""
    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    summary: str = Field(..., description="Endpoint summary")
    description: str = Field(..., description="Detailed description")
    tags: List[str] = Field(..., description="Endpoint tags")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="Endpoint parameters")
    responses: Dict[str, Any] = Field(default_factory=dict, description="Response schemas")
    security: List[Dict[str, Any]] = Field(default_factory=list, description="Security requirements")


class OpenAPIEnhancer:
    """OpenAPI documentation enhancer"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.custom_schemas = {}
        self.endpoint_docs = {}
    
    def add_custom_schema(self, name: str, schema: Type[BaseModel]):
        """Add custom schema to OpenAPI documentation"""
        self.custom_schemas[name] = schema
        logger.info(f"Added custom schema: {name}")
    
    def add_endpoint_documentation(self, endpoint_info: APIEndpointInfo):
        """Add detailed endpoint documentation"""
        self.endpoint_docs[f"{endpoint_info.method.upper()}:{endpoint_info.path}"] = endpoint_info
        logger.info(f"Added endpoint documentation: {endpoint_info.method} {endpoint_info.path}")
    
    def enhance_openapi_schema(self) -> Dict[str, Any]:
        """Generate enhanced OpenAPI schema"""
        if self.app.openapi_schema:
            return self.app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Wren API",
            version="1.0.0",
            description="""
            # Wren API Documentation
            
            A comprehensive business management API providing endpoints for:
            - User and organization management
            - Product and inventory management
            - Order and payment processing
            - Content and template management
            - Analytics and reporting
            
            ## Authentication
            
            The API uses JWT tokens for authentication. Include the token in the Authorization header:
            ```
            Authorization: Bearer <your-token>
            ```
            
            ## Rate Limiting
            
            API requests are rate limited to ensure fair usage:
            - 1000 requests per hour for authenticated users
            - 100 requests per hour for unauthenticated users
            
            ## Error Handling
            
            All errors follow a consistent format with detailed error codes and messages.
            """,
            routes=self.app.routes,
        )
        
        # Add custom schemas
        for name, schema in self.custom_schemas.items():
            openapi_schema["components"]["schemas"][name] = schema.schema()
        
        # Add enhanced endpoint documentation
        self._enhance_endpoint_docs(openapi_schema)
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for API authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for programmatic access"
            }
        }
        
        # Add global security
        openapi_schema["security"] = [
            {"BearerAuth": []},
            {"ApiKeyAuth": []}
        ]
        
        # Add server information
        openapi_schema["servers"] = [
            {
                "url": "https://api.wren.com/v1",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.wren.com/v1",
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000/api/v1",
                "description": "Development server"
            }
        ]
        
        # Add contact information
        openapi_schema["info"]["contact"] = {
            "name": "Wren API Support",
            "email": "api-support@wren.com",
            "url": "https://docs.wren.com/support"
        }
        
        # Add license information
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
        
        # Add external documentation
        openapi_schema["externalDocs"] = {
            "description": "Wren API Documentation",
            "url": "https://docs.wren.com"
        }
        
        self.app.openapi_schema = openapi_schema
        return openapi_schema
    
    def _enhance_endpoint_docs(self, openapi_schema: Dict[str, Any]):
        """Enhance endpoint documentation with custom details"""
        for path, path_item in openapi_schema["paths"].items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "patch", "delete"]:
                    endpoint_key = f"{method.upper()}:{path}"
                    
                    if endpoint_key in self.endpoint_docs:
                        endpoint_info = self.endpoint_docs[endpoint_key]
                        
                        # Enhance operation details
                        operation["summary"] = endpoint_info.summary
                        operation["description"] = endpoint_info.description
                        operation["tags"] = endpoint_info.tags
                        
                        # Add parameters
                        if endpoint_info.parameters:
                            operation["parameters"] = endpoint_info.parameters
                        
                        # Add security requirements
                        if endpoint_info.security:
                            operation["security"] = endpoint_info.security
                        
                        # Add response examples
                        self._add_response_examples(operation, endpoint_info)
    
    def _add_response_examples(self, operation: Dict[str, Any], endpoint_info: APIEndpointInfo):
        """Add response examples to operation"""
        for status_code, response_schema in operation.get("responses", {}).items():
            if status_code == "200":
                response_schema["examples"] = {
                    "success": {
                        "summary": "Successful response",
                        "value": {
                            "status_code": 200,
                            "success": True,
                            "message": "Operation completed successfully",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "request_id": "req_123456789",
                            "data": {}
                        }
                    }
                }
            elif status_code == "400":
                response_schema["examples"] = {
                    "validation_error": {
                        "summary": "Validation error",
                        "value": {
                            "status_code": 400,
                            "success": False,
                            "message": "Validation failed",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "request_id": "req_123456789",
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "details": {
                                    "field_errors": {
                                        "field_name": ["Error message"]
                                    }
                                }
                            }
                        }
                    }
                }
            elif status_code == "401":
                response_schema["examples"] = {
                    "unauthorized": {
                        "summary": "Unauthorized",
                        "value": {
                            "status_code": 401,
                            "success": False,
                            "message": "Authentication required",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "request_id": "req_123456789",
                            "error": {
                                "code": "AUTHENTICATION_ERROR",
                                "details": {
                                    "message": "Invalid or missing authentication token"
                                }
                            }
                        }
                    }
                }


class APIDocumentationGenerator:
    """Generate comprehensive API documentation"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.enhancer = OpenAPIEnhancer(app)
    
    def generate_endpoint_documentation(self) -> Dict[str, Any]:
        """Generate comprehensive endpoint documentation"""
        documentation = {
            "endpoints": [],
            "categories": {},
            "authentication": self._get_auth_docs(),
            "error_codes": self._get_error_codes_docs(),
            "rate_limiting": self._get_rate_limiting_docs()
        }
        
        # Group endpoints by category
        for route in self.app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method.upper() != 'HEAD':
                        endpoint_doc = {
                            "path": route.path,
                            "method": method.upper(),
                            "summary": getattr(route, 'summary', ''),
                            "description": getattr(route, 'description', ''),
                            "tags": getattr(route, 'tags', []),
                            "parameters": self._extract_parameters(route),
                            "responses": self._extract_responses(route)
                        }
                        
                        documentation["endpoints"].append(endpoint_doc)
                        
                        # Categorize by tags
                        for tag in endpoint_doc["tags"]:
                            if tag not in documentation["categories"]:
                                documentation["categories"][tag] = []
                            documentation["categories"][tag].append(endpoint_doc)
        
        return documentation
    
    def _get_auth_docs(self) -> Dict[str, Any]:
        """Get authentication documentation"""
        return {
            "methods": [
                {
                    "type": "JWT Bearer Token",
                    "description": "Include JWT token in Authorization header",
                    "example": "Authorization: Bearer <token>",
                    "required": True
                },
                {
                    "type": "API Key",
                    "description": "Include API key in X-API-Key header",
                    "example": "X-API-Key: <api-key>",
                    "required": False
                }
            ],
            "token_refresh": {
                "endpoint": "/auth/refresh",
                "description": "Refresh expired JWT tokens"
            }
        }
    
    def _get_error_codes_docs(self) -> Dict[str, Any]:
        """Get error codes documentation"""
        return {
            "VALIDATION_ERROR": {
                "status_code": 422,
                "description": "Request validation failed",
                "example": "Invalid email format"
            },
            "AUTHENTICATION_ERROR": {
                "status_code": 401,
                "description": "Authentication required or failed",
                "example": "Invalid or missing token"
            },
            "AUTHORIZATION_ERROR": {
                "status_code": 403,
                "description": "Insufficient permissions",
                "example": "Access denied to resource"
            },
            "NOT_FOUND": {
                "status_code": 404,
                "description": "Resource not found",
                "example": "User with ID 123 not found"
            },
            "CONFLICT": {
                "status_code": 409,
                "description": "Resource conflict",
                "example": "Email already exists"
            },
            "RATE_LIMIT_EXCEEDED": {
                "status_code": 429,
                "description": "Rate limit exceeded",
                "example": "Too many requests, please try again later"
            },
            "INTERNAL_ERROR": {
                "status_code": 500,
                "description": "Internal server error",
                "example": "An unexpected error occurred"
            }
        }
    
    def _get_rate_limiting_docs(self) -> Dict[str, Any]:
        """Get rate limiting documentation"""
        return {
            "limits": {
                "authenticated": {
                    "requests_per_hour": 1000,
                    "requests_per_minute": 100
                },
                "unauthenticated": {
                    "requests_per_hour": 100,
                    "requests_per_minute": 10
                }
            },
            "headers": {
                "X-RateLimit-Limit": "Request limit per time window",
                "X-RateLimit-Remaining": "Remaining requests in current window",
                "X-RateLimit-Reset": "Time when the rate limit resets"
            }
        }
    
    def _extract_parameters(self, route) -> List[Dict[str, Any]]:
        """Extract parameters from route"""
        parameters = []
        
        if hasattr(route, 'dependant') and route.dependant:
            for param in route.dependant.query_params:
                parameters.append({
                    "name": param.name,
                    "type": str(param.annotation),
                    "required": param.is_required,
                    "description": getattr(param, 'description', ''),
                    "in": "query"
                })
        
        return parameters
    
    def _extract_responses(self, route) -> Dict[str, Any]:
        """Extract response schemas from route"""
        responses = {}
        
        if hasattr(route, 'response_model'):
            responses["200"] = {
                "description": "Successful response",
                "schema": str(route.response_model)
            }
        
        return responses


def create_dynamic_response_model(
    data_model: Type[BaseModel],
    include_pagination: bool = False,
    include_metadata: bool = False
) -> Type[BaseModel]:
    """
    Create dynamic response model based on data model
    
    Args:
        data_model: The data model to wrap
        include_pagination: Whether to include pagination
        include_metadata: Whether to include metadata
        
    Returns:
        Dynamic response model
    """
    fields = {
        "status_code": (int, Field(..., description="HTTP status code")),
        "success": (bool, Field(..., description="Success status")),
        "message": (str, Field(..., description="Response message")),
        "timestamp": (datetime, Field(default_factory=datetime.utcnow)),
        "request_id": (str, Field(..., description="Request ID"))
    }
    
    if include_pagination:
        fields["pagination"] = (PaginationModel, Field(..., description="Pagination metadata"))
        fields["data"] = (List[data_model], Field(..., description="Response data"))
    else:
        fields["data"] = (data_model, Field(..., description="Response data"))
    
    if include_metadata:
        fields["metadata"] = (Optional[Dict[str, Any]], Field(None, description="Additional metadata"))
    
    return create_model(
        f"{data_model.__name__}Response",
        **fields
    )


def add_api_documentation_enhancements(app: FastAPI):
    """Add comprehensive API documentation enhancements"""
    enhancer = OpenAPIEnhancer(app)
    generator = APIDocumentationGenerator(app)
    
    # Add custom schemas
    enhancer.add_custom_schema("StandardResponse", StandardResponseModel)
    enhancer.add_custom_schema("SuccessResponse", SuccessResponseModel)
    enhancer.add_custom_schema("ErrorResponse", ErrorResponseModel)
    enhancer.add_custom_schema("PaginatedResponse", PaginatedResponseModel)
    enhancer.add_custom_schema("Pagination", PaginationModel)
    
    # Generate enhanced OpenAPI schema
    app.openapi = enhancer.enhance_openapi_schema
    
    # Add documentation endpoint
    @app.get("/docs/api-documentation", tags=["Documentation"])
    async def get_api_documentation():
        """Get comprehensive API documentation"""
        return generator.generate_endpoint_documentation()
    
    logger.info("API documentation enhancements added successfully")