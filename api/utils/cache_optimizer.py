"""
Caching and Performance Optimization for Wren API

This module provides comprehensive caching strategies, performance optimization,
and cache management utilities.
"""

import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class CacheStrategy:
    """Cache strategy implementation"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Check TTL
            if time.time() - self.timestamps[key] < self.ttl:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.timestamps[key]
        
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        # Remove if exists
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
        
        # Check size limit
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        # Add new item
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hit_rate": self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        # This would be implemented with hit/miss counters
        return 0.0


class CacheManager:
    """Cache management system"""
    
    def __init__(self):
        self.caches = {}
        self.default_ttl = 300
        self.default_max_size = 1000
    
    def create_cache(self, name: str, max_size: int = None, ttl: int = None) -> CacheStrategy:
        """Create new cache"""
        cache = CacheStrategy(
            max_size=max_size or self.default_max_size,
            ttl=ttl or self.default_ttl
        )
        self.caches[name] = cache
        logger.info(f"Cache created: {name}")
        return cache
    
    def get_cache(self, name: str) -> Optional[CacheStrategy]:
        """Get cache by name"""
        return self.caches.get(name)
    
    def delete_cache(self, name: str):
        """Delete cache"""
        if name in self.caches:
            del self.caches[name]
            logger.info(f"Cache deleted: {name}")
    
    def clear_all_caches(self):
        """Clear all caches"""
        for cache in self.caches.values():
            cache.clear()
        logger.info("All caches cleared")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        return {
            name: cache.get_stats()
            for name, cache in self.caches.items()
        }


class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.optimization_rules = {}
        self.performance_metrics = {}
    
    def add_optimization_rule(self, rule_name: str, rule_func: Callable):
        """Add optimization rule"""
        self.optimization_rules[rule_name] = rule_func
        logger.info(f"Optimization rule added: {rule_name}")
    
    def optimize_query(self, query: str) -> str:
        """Optimize database query"""
        optimized_query = query
        
        # Apply optimization rules
        for rule_name, rule_func in self.optimization_rules.items():
            try:
                optimized_query = rule_func(optimized_query)
            except Exception as e:
                logger.error(f"Optimization rule '{rule_name}' failed: {e}")
        
        return optimized_query
    
    def measure_performance(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Measure function performance"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        performance_data = {
            "execution_time": end_time - start_time,
            "memory_delta": end_memory - start_memory,
            "success": success,
            "error": error,
            "timestamp": datetime.utcnow()
        }
        
        return performance_data
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return dict(self.performance_metrics)


class CacheDecorator:
    """Cache decorator for functions"""
    
    def __init__(self, cache_name: str = "default", ttl: int = 300):
        self.cache_name = cache_name
        self.ttl = ttl
        self.cache_manager = CacheManager()
        
        # Create cache if it doesn't exist
        if not self.cache_manager.get_cache(cache_name):
            self.cache_manager.create_cache(cache_name, ttl=ttl)
    
    def __call__(self, func: Callable):
        """Decorator implementation"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self._generate_cache_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cache = self.cache_manager.get_cache(self.cache_name)
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        return wrapper
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key"""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()


class ResponseCache:
    """Response caching system"""
    
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}
    
    def get_cached_response(self, request_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        if request_key in self.cache:
            if time.time() - self.timestamps[request_key] < self.ttl:
                return self.cache[request_key]
            else:
                # Expired
                del self.cache[request_key]
                del self.timestamps[request_key]
        
        return None
    
    def cache_response(self, request_key: str, response: Dict[str, Any]):
        """Cache response"""
        self.cache[request_key] = response
        self.timestamps[request_key] = time.time()
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            # Invalidate entries matching pattern
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
                del self.timestamps[key]
        else:
            # Clear all cache
            self.cache.clear()
            self.timestamps.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "ttl": self.ttl,
            "entries": list(self.cache.keys())
        }


# Global caching and optimization instances
def get_cache_manager() -> CacheManager:
    """Get cache manager instance"""
    return CacheManager()

def get_performance_optimizer() -> PerformanceOptimizer:
    """Get performance optimizer instance"""
    return PerformanceOptimizer()

def get_response_cache(ttl: int = 300) -> ResponseCache:
    """Get response cache instance"""
    return ResponseCache(ttl)

def cached(cache_name: str = "default", ttl: int = 300):
    """Cache decorator"""
    return CacheDecorator(cache_name, ttl)
