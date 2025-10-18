"""
Retry Decorator Utilities

Decorators for automatic retry logic with exponential backoff.
"""

from functools import wraps
from typing import Callable, Any, Optional
import time
import logging
from .error_handler import ErrorHandler

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0, exceptions: tuple = None):
    """
    Decorator to retry function on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to retry on
    """
    if exceptions is None:
        exceptions = (Exception,)
    
    def decorator(func: Callable) -> Callable:
        error_handler = ErrorHandler()
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    if not error_handler.should_retry(e, attempt, max_retries):
                        raise
                    
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            return None
        return wrapper
    return decorator


def circuit_breaker(failure_threshold: int = 5, timeout: float = 60.0):
    """
    Circuit breaker decorator to prevent cascading failures.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Time to wait before attempting to close circuit
    """
    def decorator(func: Callable) -> Callable:
        failures = 0
        last_failure_time = None
        circuit_open = False
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal failures, last_failure_time, circuit_open
            
            # Check if circuit should be closed
            if circuit_open and last_failure_time:
                if time.time() - last_failure_time > timeout:
                    circuit_open = False
                    failures = 0
            
            # If circuit is open, fail fast
            if circuit_open:
                raise Exception("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                failures = 0  # Reset on success
                return result
            except Exception as e:
                failures += 1
                last_failure_time = time.time()
                
                if failures >= failure_threshold:
                    circuit_open = True
                    logger.error(f"Circuit breaker opened for {func.__name__}")
                
                raise
        
        return wrapper
    return decorator
