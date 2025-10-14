"""
API Middleware and Request Processing for Wren API

This module provides comprehensive middleware management, request processing,
and API pipeline utilities.
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Union, Callable, Type
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class MiddlewareType(Enum):
    """Middleware types"""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    LOGGING = "logging"
    CORS = "cors"
    RATE_LIMITING = "rate_limiting"


@dataclass
class RequestContext:
    """Request context information"""
    request_id: str
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    body: Any
    user_id: Optional[str] = None
    start_time: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ResponseContext:
    """Response context information"""
    status_code: int
    headers: Dict[str, str]
    body: Any
    processing_time: float
    request_id: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Middleware:
    """Base middleware class"""
    
    def __init__(self, name: str, middleware_type: MiddlewareType):
        self.name = name
        self.type = middleware_type
        self.enabled = True
        self.priority = 0
    
    async def process_request(self, context: RequestContext) -> Optional[ResponseContext]:
        """Process request - return ResponseContext to short-circuit"""
        return None
    
    async def process_response(self, context: ResponseContext) -> ResponseContext:
        """Process response"""
        return context
    
    async def process_error(self, error: Exception, context: RequestContext) -> Optional[ResponseContext]:
        """Process error - return ResponseContext to handle error"""
        return None


class MiddlewareManager:
    """Middleware management system"""
    
    def __init__(self):
        self.middlewares = {}
        self.middleware_chain = []
        self.request_processors = []
        self.response_processors = []
        self.error_processors = []
    
    def register_middleware(self, middleware: Middleware):
        """Register middleware"""
        self.middlewares[middleware.name] = middleware
        
        # Add to appropriate chain
        if middleware.type == MiddlewareType.REQUEST:
            self.request_processors.append(middleware)
        elif middleware.type == MiddlewareType.RESPONSE:
            self.response_processors.append(middleware)
        elif middleware.type == MiddlewareType.ERROR:
            self.error_processors.append(middleware)
        
        # Sort by priority
        self._sort_middleware_chains()
        
        logger.info(f"Middleware registered: {middleware.name}")
    
    def unregister_middleware(self, name: str):
        """Unregister middleware"""
        if name in self.middlewares:
            middleware = self.middlewares[name]
            
            # Remove from chains
            if middleware in self.request_processors:
                self.request_processors.remove(middleware)
            if middleware in self.response_processors:
                self.response_processors.remove(middleware)
            if middleware in self.error_processors:
                self.error_processors.remove(middleware)
            
            del self.middlewares[name]
            logger.info(f"Middleware unregistered: {name}")
    
    def _sort_middleware_chains(self):
        """Sort middleware chains by priority"""
        self.request_processors.sort(key=lambda m: m.priority, reverse=True)
        self.response_processors.sort(key=lambda m: m.priority)
        self.error_processors.sort(key=lambda m: m.priority, reverse=True)
    
    async def process_request(self, context: RequestContext) -> Optional[ResponseContext]:
        """Process request through middleware chain"""
        for middleware in self.request_processors:
            if not middleware.enabled:
                continue
            
            try:
                result = await middleware.process_request(context)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"Middleware {middleware.name} error: {e}")
                # Continue to next middleware
        
        return None
    
    async def process_response(self, context: ResponseContext) -> ResponseContext:
        """Process response through middleware chain"""
        for middleware in self.response_processors:
            if not middleware.enabled:
                continue
            
            try:
                context = await middleware.process_response(context)
            except Exception as e:
                logger.error(f"Middleware {middleware.name} error: {e}")
        
        return context
    
    async def process_error(self, error: Exception, context: RequestContext) -> Optional[ResponseContext]:
        """Process error through middleware chain"""
        for middleware in self.error_processors:
            if not middleware.enabled:
                continue
            
            try:
                result = await middleware.process_error(error, context)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"Error middleware {middleware.name} error: {e}")
        
        return None
    
    def get_middleware_status(self) -> Dict[str, Any]:
        """Get middleware status"""
        return {
            "total_middlewares": len(self.middlewares),
            "request_processors": len(self.request_processors),
            "response_processors": len(self.response_processors),
            "error_processors": len(self.error_processors),
            "middlewares": {
                name: {
                    "type": middleware.type.value,
                    "enabled": middleware.enabled,
                    "priority": middleware.priority
                }
                for name, middleware in self.middlewares.items()
            }
        }


class RequestProcessor:
    """Request processing utilities"""
    
    def __init__(self):
        self.request_handlers = {}
        self.request_validators = {}
        self.request_transformers = {}
    
    def register_handler(self, path: str, method: str, handler: Callable):
        """Register request handler"""
        key = f"{method.upper()}:{path}"
        self.request_handlers[key] = handler
        logger.info(f"Request handler registered: {key}")
    
    def register_validator(self, path: str, validator: Callable):
        """Register request validator"""
        self.request_validators[path] = validator
        logger.info(f"Request validator registered: {path}")
    
    def register_transformer(self, path: str, transformer: Callable):
        """Register request transformer"""
        self.request_transformers[path] = transformer
        logger.info(f"Request transformer registered: {path}")
    
    def get_handler(self, path: str, method: str) -> Optional[Callable]:
        """Get request handler"""
        key = f"{method.upper()}:{path}"
        return self.request_handlers.get(key)
    
    def validate_request(self, path: str, request_data: Any) -> bool:
        """Validate request"""
        if path in self.request_validators:
            try:
                return self.request_validators[path](request_data)
            except Exception as e:
                logger.error(f"Request validation error for {path}: {e}")
                return False
        return True
    
    def transform_request(self, path: str, request_data: Any) -> Any:
        """Transform request"""
        if path in self.request_transformers:
            try:
                return self.request_transformers[path](request_data)
            except Exception as e:
                logger.error(f"Request transformation error for {path}: {e}")
                return request_data
        return request_data


class ResponseProcessor:
    """Response processing utilities"""
    
    def __init__(self):
        self.response_formatters = {}
        self.response_serializers = {}
        self.response_headers = {}
    
    def register_formatter(self, content_type: str, formatter: Callable):
        """Register response formatter"""
        self.response_formatters[content_type] = formatter
        logger.info(f"Response formatter registered: {content_type}")
    
    def register_serializer(self, data_type: str, serializer: Callable):
        """Register response serializer"""
        self.response_serializers[data_type] = serializer
        logger.info(f"Response serializer registered: {data_type}")
    
    def set_default_headers(self, headers: Dict[str, str]):
        """Set default response headers"""
        self.response_headers.update(headers)
        logger.info("Default response headers set")
    
    def format_response(self, content_type: str, data: Any) -> Any:
        """Format response"""
        if content_type in self.response_formatters:
            try:
                return self.response_formatters[content_type](data)
            except Exception as e:
                logger.error(f"Response formatting error for {content_type}: {e}")
                return data
        return data
    
    def serialize_response(self, data_type: str, data: Any) -> Any:
        """Serialize response"""
        if data_type in self.response_serializers:
            try:
                return self.response_serializers[data_type](data)
            except Exception as e:
                logger.error(f"Response serialization error for {data_type}: {e}")
                return data
        return data


class APIPipeline:
    """API request/response pipeline"""
    
    def __init__(self):
        self.middleware_manager = MiddlewareManager()
        self.request_processor = RequestProcessor()
        self.response_processor = ResponseProcessor()
    
    async def process_api_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process API request through pipeline"""
        # Create request context
        context = RequestContext(
            request_id=str(uuid.uuid4()),
            method=request_data.get("method", "GET"),
            path=request_data.get("path", "/"),
            headers=request_data.get("headers", {}),
            query_params=request_data.get("query_params", {}),
            body=request_data.get("body")
        )
        
        try:
            # Process through request middleware
            response_context = await self.middleware_manager.process_request(context)
            
            if response_context is None:
                # Process request
                handler = self.request_processor.get_handler(context.path, context.method)
                if handler is None:
                    response_context = ResponseContext(
                        status_code=404,
                        headers={"Content-Type": "application/json"},
                        body={"error": "Not found"},
                        processing_time=0.0,
                        request_id=context.request_id
                    )
                else:
                    # Validate request
                    if not self.request_processor.validate_request(context.path, context.body):
                        response_context = ResponseContext(
                            status_code=400,
                            headers={"Content-Type": "application/json"},
                            body={"error": "Invalid request"},
                            processing_time=0.0,
                            request_id=context.request_id
                        )
                    else:
                        # Transform request
                        transformed_body = self.request_processor.transform_request(context.path, context.body)
                        
                        # Execute handler
                        start_time = time.time()
                        result = await handler(transformed_body)
                        processing_time = time.time() - start_time
                        
                        response_context = ResponseContext(
                            status_code=200,
                            headers={"Content-Type": "application/json"},
                            body=result,
                            processing_time=processing_time,
                            request_id=context.request_id
                        )
            
            # Process through response middleware
            response_context = await self.middleware_manager.process_response(response_context)
            
            return {
                "status_code": response_context.status_code,
                "headers": response_context.headers,
                "body": response_context.body,
                "processing_time": response_context.processing_time,
                "request_id": response_context.request_id
            }
            
        except Exception as e:
            # Process error through middleware
            error_response = await self.middleware_manager.process_error(e, context)
            
            if error_response is not None:
                return {
                    "status_code": error_response.status_code,
                    "headers": error_response.headers,
                    "body": error_response.body,
                    "processing_time": error_response.processing_time,
                    "request_id": error_response.request_id
                }
            else:
                # Default error response
                return {
                    "status_code": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": {"error": "Internal server error"},
                    "processing_time": 0.0,
                    "request_id": context.request_id
                }


# Global middleware and processing instances
def get_middleware_manager() -> MiddlewareManager:
    """Get middleware manager instance"""
    return MiddlewareManager()

def get_request_processor() -> RequestProcessor:
    """Get request processor instance"""
    return RequestProcessor()

def get_response_processor() -> ResponseProcessor:
    """Get response processor instance"""
    return ResponseProcessor()

def get_api_pipeline() -> APIPipeline:
    """Get API pipeline instance"""
    return APIPipeline()
