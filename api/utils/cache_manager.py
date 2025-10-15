"""
Cache Management System for Wren API

This module provides a comprehensive caching system using Redis for improved
performance and reduced database load. It includes decorators for automatic
caching, cache invalidation strategies, and performance monitoring.
"""

import json
import hashlib
import time
from typing import Any, Optional, Dict, List, Callable, Union
from functools import wraps
from datetime import datetime, timedelta
import logging

try:
    import redis
    from redis.exceptions import RedisError, ConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


class CacheManager:
    """Centralized cache management system"""
    
    def __init__(self):
        self.redis_client = None
        self.cache_enabled = False
        self.default_ttl = 3600  # 1 hour default TTL
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, caching disabled")
            return
        
        try:
            # Try to get Redis configuration from settings
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info("Redis cache initialized successfully")
            
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.cache_enabled = False
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments"""
        # Create a hash of the arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache_enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.cache_enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except (RedisError, TypeError) as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.cache_enabled:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.cache_enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except RedisError as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
        
        return 0
    
    def invalidate_organization_cache(self, organization_id: str):
        """Invalidate all cache entries for an organization"""
        patterns = [
            f"org:{organization_id}:*",
            f"products:org:{organization_id}:*",
            f"users:org:{organization_id}:*",
            f"categories:org:{organization_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.delete_pattern(pattern)
        
        logger.info(f"Invalidated {total_deleted} cache entries for organization {organization_id}")
        return total_deleted
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache_enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except RedisError as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


# Global cache manager instance
cache_manager = CacheManager()


def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None,
    invalidate_on: Optional[List[str]] = None
):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Custom function to generate cache key
        invalidate_on: List of parameter names that should invalidate cache
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_cache_key(prefix, *args, **kwargs)
            
            # Check cache first
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}, executing function")
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Cache the result
                cache_manager.set(cache_key, result, ttl)
                
                logger.debug(f"Function executed in {execution_time:.3f}s, result cached")
                return result
                
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_cache_key(prefix, *args, **kwargs)
            
            # Check cache first
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}, executing function")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Cache the result
                cache_manager.set(cache_key, result, ttl)
                
                logger.debug(f"Function executed in {execution_time:.3f}s, result cached")
                return result
                
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {e}")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_invalidate(patterns: List[str]):
    """
    Decorator to invalidate cache patterns after function execution
    
    Args:
        patterns: List of cache key patterns to invalidate
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache patterns
            for pattern in patterns:
                cache_manager.delete_pattern(pattern)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache patterns
            for pattern in patterns:
                cache_manager.delete_pattern(pattern)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CacheMetrics:
    """Cache performance metrics collector"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_requests = 0
    
    def record_hit(self):
        self.hits += 1
        self.total_requests += 1
    
    def record_miss(self):
        self.misses += 1
        self.total_requests += 1
    
    def record_error(self):
        self.errors += 1
        self.total_requests += 1
    
    def get_stats(self) -> Dict[str, Any]:
        hit_rate = (self.hits / self.total_requests * 100) if self.total_requests > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_rate": round(hit_rate, 2)
        }


# Global metrics instance
cache_metrics = CacheMetrics()
