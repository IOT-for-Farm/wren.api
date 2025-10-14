from typing import Optional, Dict, Any, List
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
import uuid


def success_response(
    status_code: int, 
    message: str, 
    data: Optional[dict | list] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
):
    """
    Returns a standardized JSON response for success responses
    
    Args:
        status_code: HTTP status code
        message: Success message
        data: Response data (optional)
        metadata: Additional metadata (optional)
        request_id: Request ID for tracking (optional)
    
    Returns:
        JSONResponse with standardized format
    """
    
    response_data = {
        "status_code": status_code,
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or str(uuid.uuid4())
    }
    
    if data is not None:
        response_data["data"] = data
    
    if metadata:
        response_data["metadata"] = metadata

    return JSONResponse(status_code=status_code, content=jsonable_encoder(response_data))


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    endpoint: str,
    message: str = "Items fetched successfully",
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Returns a standardized paginated response
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        per_page: Items per page
        endpoint: API endpoint for pagination links
        message: Success message
        metadata: Additional metadata
        request_id: Request ID for tracking
    
    Returns:
        JSONResponse with pagination data
    """
    
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    pagination_data = {
        "current_page": page,
        "per_page": per_page,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "next_page": f"{endpoint}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "previous_page": f"{endpoint}?page={page - 1}&per_page={per_page}" if page > 1 else None
    }
    
    response_data = {
        "status_code": 200,
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or str(uuid.uuid4()),
        "pagination": pagination_data,
        "data": items
    }
    
    if metadata:
        response_data["metadata"] = metadata
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response_data))


def created_response(
    message: str,
    data: Optional[dict] = None,
    location: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Returns a standardized response for created resources
    
    Args:
        message: Success message
        data: Created resource data
        location: Location header value (optional)
        metadata: Additional metadata
        request_id: Request ID for tracking
    
    Returns:
        JSONResponse with 201 status
    """
    
    response_data = {
        "status_code": 201,
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or str(uuid.uuid4())
    }
    
    if data is not None:
        response_data["data"] = data
    
    if metadata:
        response_data["metadata"] = metadata
    
    response = JSONResponse(status_code=201, content=jsonable_encoder(response_data))
    
    if location:
        response.headers["Location"] = location
    
    return response


def updated_response(
    message: str,
    data: Optional[dict] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Returns a standardized response for updated resources
    
    Args:
        message: Success message
        data: Updated resource data
        metadata: Additional metadata
        request_id: Request ID for tracking
    
    Returns:
        JSONResponse with 200 status
    """
    
    response_data = {
        "status_code": 200,
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or str(uuid.uuid4())
    }
    
    if data is not None:
        response_data["data"] = data
    
    if metadata:
        response_data["metadata"] = metadata
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response_data))


def deleted_response(
    message: str = "Resource deleted successfully",
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Returns a standardized response for deleted resources
    
    Args:
        message: Success message
        metadata: Additional metadata
        request_id: Request ID for tracking
    
    Returns:
        JSONResponse with 200 status
    """
    
    response_data = {
        "status_code": 200,
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or str(uuid.uuid4())
    }
    
    if metadata:
        response_data["metadata"] = metadata
    
    return JSONResponse(status_code=200, content=jsonable_encoder(response_data))


def validation_error_response(
    field_errors: Dict[str, List[str]],
    message: str = "Validation failed",
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Returns a standardized validation error response
    
    Args:
        field_errors: Dictionary of field names to error messages
        message: General error message
        request_id: Request ID for tracking
    
    Returns:
        JSONResponse with 422 status
    """
    
    response_data = {
        "status_code": 422,
        "success": False,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id or str(uuid.uuid4()),
        "error": {
            "code": "VALIDATION_ERROR",
            "field_errors": field_errors
        }
    }
    
    return JSONResponse(status_code=422, content=jsonable_encoder(response_data))
