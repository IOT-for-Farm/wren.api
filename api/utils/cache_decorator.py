"""
Cache Decorator Utilities

Decorators for automatic caching of function results.
"""

from functools import wraps
from typing import Callable, Any, Optional
from .cache_manager import CacheManager


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable) -> Callable:
        cache = CacheManager()
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def cache_invalidate(cache_manager: CacheManager, pattern: str = ""):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        cache_manager: Cache manager instance
        pattern: Pattern to match keys for invalidation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)
            
            # Invalidate cache entries matching pattern
            if pattern:
                keys_to_delete = [
                    key for key in cache_manager.cache.keys()
                    if pattern in key
                ]
                for key in keys_to_delete:
                    cache_manager.delete(key)
            
            return result
        return wrapper
    return decorator
