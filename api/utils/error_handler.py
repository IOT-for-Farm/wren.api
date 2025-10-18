"""
Enhanced Error Handling Utilities

Centralized error handling and recovery mechanisms.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
import traceback


class ErrorHandler:
    """Centralized error handling with logging and recovery."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
    
    def handle_exception(self, exception: Exception, context: str = "") -> Dict[str, Any]:
        """Handle and log exceptions with context."""
        error_info = {
            "error_type": type(exception).__name__,
            "message": str(exception),
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc()
        }
        
        # Log the error
        self.logger.error(f"Exception in {context}: {exception}")
        
        # Track error frequency
        error_key = f"{type(exception).__name__}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        return error_info
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        return self.error_counts.copy()
    
    def should_retry(self, exception: Exception, retry_count: int, max_retries: int = 3) -> bool:
        """Determine if operation should be retried."""
        if retry_count >= max_retries:
            return False
        
        # Retry on specific exception types
        retryable_errors = (ConnectionError, TimeoutError, OSError)
        return isinstance(exception, retryable_errors)
    
    def format_error_response(self, error_info: Dict[str, Any], include_traceback: bool = False) -> Dict[str, Any]:
        """Format error for API response."""
        response = {
            "error": error_info["error_type"],
            "message": error_info["message"],
            "timestamp": error_info["timestamp"]
        }
        
        if include_traceback:
            response["traceback"] = error_info["traceback"]
        
        return response
