"""
Enhanced Error Handling and Validation Utilities

This module provides comprehensive error handling, validation, and response
standardization for the Wren API. It includes custom exception classes,
validation decorators, and standardized error responses.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API Error class for custom exceptions"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 400, 
        error_code: str = None,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERROR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Custom validation error with detailed field information"""
    
    def __init__(
        self, 
        message: str = "Validation failed",
        field_errors: Dict[str, List[str]] = None,
        details: Dict[str, Any] = None
    ):
        self.field_errors = field_errors or {}
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={**details or {}, "field_errors": self.field_errors}
        )


class BusinessLogicError(APIError):
    """Error for business logic violations"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "BUSINESS_LOGIC_ERROR",
        details: Dict[str, Any] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details=details
        )


class ResourceNotFoundError(APIError):
    """Error for resource not found scenarios"""
    
    def __init__(
        self, 
        resource_type: str = "Resource",
        resource_id: str = None,
        details: Dict[str, Any] = None
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={**details or {}, "resource_type": resource_type, "resource_id": resource_id}
        )


class PermissionError(APIError):
    """Error for permission/authorization failures"""
    
    def __init__(
        self, 
        message: str = "Insufficient permissions",
        required_permission: str = None,
        details: Dict[str, Any] = None
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PERMISSION_DENIED",
            details={**details or {}, "required_permission": required_permission}
        )


def create_error_response(
    error: Union[APIError, Exception],
    request: Request = None,
    include_traceback: bool = False
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        error: The exception or error to handle
        request: FastAPI request object for additional context
        include_traceback: Whether to include traceback in response (dev only)
    
    Returns:
        JSONResponse with standardized error format
    """
    
    if isinstance(error, APIError):
        status_code = error.status_code
        error_data = {
            "status_code": status_code,
            "success": False,
            "error": {
                "code": error.error_code,
                "message": error.message,
                "details": error.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    elif isinstance(error, ValidationError):
        status_code = 422
        error_data = {
            "status_code": status_code,
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "field_errors": error.errors() if hasattr(error, 'errors') else str(error),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
    elif isinstance(error, HTTPException):
        status_code = error.status_code
        error_data = {
            "status_code": status_code,
            "success": False,
            "error": {
                "code": f"HTTP_ERROR_{status_code}",
                "message": error.detail,
                "details": {"timestamp": datetime.utcnow().isoformat()}
            }
        }
    else:
        status_code = 500
        error_data = {
            "status_code": status_code,
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": type(error).__name__
                }
            }
        }
        
        if include_traceback:
            error_data["error"]["details"]["traceback"] = traceback.format_exc()
    
    # Add request context if available
    if request:
        error_data["error"]["details"]["request_id"] = getattr(request.state, "request_id", None)
        error_data["error"]["details"]["endpoint"] = f"{request.method} {request.url.path}"
    
    logger.error(f"API Error: {error_data}")
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(error_data)
    )


def validate_input(
    model_class: BaseModel = None,
    validate_required: bool = True,
    custom_validators: List[Callable] = None
):
    """
    Decorator for input validation with custom error handling
    
    Args:
        model_class: Pydantic model class for validation
        validate_required: Whether to validate required fields
        custom_validators: List of custom validation functions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Validate with Pydantic model if provided
                if model_class:
                    # Extract payload from kwargs (assuming it's the first non-db, non-entity arg)
                    for key, value in kwargs.items():
                        if key not in ['db', 'entity', 'request'] and hasattr(value, 'model_dump'):
                            try:
                                validated_data = model_class(**value.model_dump())
                                kwargs[key] = validated_data
                            except ValidationError as e:
                                field_errors = {}
                                for error in e.errors():
                                    field = error['loc'][0] if error['loc'] else 'unknown'
                                    if field not in field_errors:
                                        field_errors[field] = []
                                    field_errors[field].append(error['msg'])
                                
                                raise ValidationError(
                                    message="Input validation failed",
                                    field_errors=field_errors
                                )
                
                # Run custom validators
                if custom_validators:
                    for validator in custom_validators:
                        result = validator(*args, **kwargs)
                        if result is not None and not result:
                            raise ValidationError(
                                message=f"Custom validation failed: {validator.__name__}"
                            )
                
                return await func(*args, **kwargs)
                
            except APIError:
                raise  # Re-raise API errors as-is
            except Exception as e:
                logger.error(f"Validation error in {func.__name__}: {str(e)}")
                raise APIError(
                    message=f"Validation failed: {str(e)}",
                    status_code=400,
                    error_code="VALIDATION_ERROR"
                )
        
        return wrapper
    return decorator


def handle_database_errors(func):
    """
    Decorator to handle database-related errors consistently
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error in {func.__name__}: {str(e)}")
            raise BusinessLogicError(
                message="Data integrity violation. The operation conflicts with existing data.",
                error_code="INTEGRITY_ERROR",
                details={"constraint": str(e.orig) if hasattr(e, 'orig') else str(e)}
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise APIError(
                message="Database operation failed",
                status_code=500,
                error_code="DATABASE_ERROR",
                details={"error_type": type(e).__name__}
            )
    
    return wrapper


def validate_organization_access(organization_id_param: str = "organization_id"):
    """
    Decorator to validate organization access for endpoints
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract organization_id and entity from kwargs
            organization_id = kwargs.get(organization_id_param)
            entity = kwargs.get('entity')
            db = kwargs.get('db')
            
            if not organization_id:
                raise ValidationError(
                    message="Organization ID is required",
                    field_errors={organization_id_param: ["This field is required"]}
                )
            
            if not entity:
                raise PermissionError(
                    message="Authentication required",
                    required_permission="authenticated"
                )
            
            # Additional organization validation can be added here
            # For now, we'll let the existing AuthService handle it
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class ErrorHandler:
    """Centralized error handling class"""
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors"""
        field_errors = {}
        for err in error.errors():
            field = '.'.join(str(loc) for loc in err['loc'])
            if field not in field_errors:
                field_errors[field] = []
            field_errors[field].append(err['msg'])
        
        return create_error_response(
            ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )
        )
    
    @staticmethod
    def handle_business_logic_error(message: str, details: Dict = None) -> JSONResponse:
        """Handle business logic violations"""
        return create_error_response(
            BusinessLogicError(message=message, details=details)
        )
    
    @staticmethod
    def handle_resource_not_found(resource_type: str, resource_id: str = None) -> JSONResponse:
        """Handle resource not found errors"""
        return create_error_response(
            ResourceNotFoundError(resource_type=resource_type, resource_id=resource_id)
        )
    
    @staticmethod
    def handle_permission_error(message: str, required_permission: str = None) -> JSONResponse:
        """Handle permission errors"""
        return create_error_response(
            PermissionError(message=message, required_permission=required_permission)
        )
