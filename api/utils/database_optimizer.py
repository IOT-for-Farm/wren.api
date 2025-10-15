"""
Database Optimization Utilities for Wren API

This module provides database query optimization, connection pooling,
and performance monitoring utilities to improve database performance
and reduce query execution times.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from contextlib import contextmanager
from sqlalchemy.orm import Session, Query
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from api.utils.loggers import create_logger
from api.db.database import get_db

logger = create_logger(__name__)


class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_pagination_query(
        query: Query,
        page: int,
        per_page: int,
        max_per_page: int = 100
    ) -> Query:
        """
        Optimize pagination queries with proper limits and offsets
        
        Args:
            query: SQLAlchemy query object
            page: Page number (1-based)
            per_page: Items per page
            max_per_page: Maximum allowed items per page
            
        Returns:
            Optimized query with pagination
        """
        # Validate and limit per_page
        per_page = min(per_page, max_per_page)
        per_page = max(1, per_page)
        
        # Validate page number
        page = max(1, page)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Apply pagination
        return query.offset(offset).limit(per_page)
    
    @staticmethod
    def add_query_hints(query: Query, hints: List[str]) -> Query:
        """
        Add database-specific query hints for optimization
        
        Args:
            query: SQLAlchemy query object
            hints: List of query hints
            
        Returns:
            Query with hints applied
        """
        # This is database-specific and would need to be adapted
        # based on the actual database being used (PostgreSQL, MySQL, etc.)
        for hint in hints:
            # Example for PostgreSQL
            if hint == "use_index":
                query = query.with_hint(text("/*+ USE_INDEX */"))
            elif hint == "parallel":
                query = query.with_hint(text("/*+ PARALLEL */"))
        
        return query
    
    @staticmethod
    def optimize_join_query(
        query: Query,
        eager_loads: List[str] = None,
        select_related: List[str] = None
    ) -> Query:
        """
        Optimize queries with joins using eager loading
        
        Args:
            query: SQLAlchemy query object
            eager_loads: List of relationships to eager load
            select_related: List of relationships to select_related
            
        Returns:
            Optimized query with proper joins
        """
        if eager_loads:
            for relationship in eager_loads:
                query = query.options(query.joinedload(relationship))
        
        if select_related:
            for relationship in select_related:
                query = query.options(query.selectinload(relationship))
        
        return query


class DatabasePerformanceMonitor:
    """Monitor database performance and query execution times"""
    
    def __init__(self):
        self.query_times = []
        self.slow_queries = []
        self.slow_query_threshold = 1.0  # 1 second
    
    def record_query_time(self, query: str, execution_time: float):
        """Record query execution time"""
        self.query_times.append({
            "query": query[:100],  # Truncate for storage
            "execution_time": execution_time,
            "timestamp": time.time()
        })
        
        if execution_time > self.slow_query_threshold:
            self.slow_queries.append({
                "query": query,
                "execution_time": execution_time,
                "timestamp": time.time()
            })
            logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        if not self.query_times:
            return {"total_queries": 0}
        
        execution_times = [q["execution_time"] for q in self.query_times]
        
        return {
            "total_queries": len(self.query_times),
            "average_execution_time": sum(execution_times) / len(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "slow_queries_count": len(self.slow_queries),
            "slow_query_threshold": self.slow_query_threshold
        }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        return sorted(
            self.slow_queries,
            key=lambda x: x["execution_time"],
            reverse=True
        )[:limit]


# Global performance monitor
db_performance_monitor = DatabasePerformanceMonitor()


def monitor_query_performance(func):
    """
    Decorator to monitor database query performance
    
    Args:
        func: Function that executes database queries
        
    Returns:
        Decorated function with performance monitoring
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record performance
            db_performance_monitor.record_query_time(
                f"{func.__name__}",
                execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query error in {func.__name__}: {e} (took {execution_time:.3f}s)")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record performance
            db_performance_monitor.record_query_time(
                f"{func.__name__}",
                execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query error in {func.__name__}: {e} (took {execution_time:.3f}s)")
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


@contextmanager
def optimized_db_session():
    """
    Context manager for optimized database sessions
    
    Provides a database session with optimized settings
    """
    db = next(get_db())
    try:
        # Set session options for better performance
        db.execute(text("SET SESSION query_cache_type = ON"))
        db.execute(text("SET SESSION query_cache_size = 268435456"))  # 256MB
        
        yield db
        
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


class ConnectionPoolManager:
    """Manage database connection pooling for better performance"""
    
    @staticmethod
    def configure_connection_pool(
        engine: Engine,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ) -> Engine:
        """
        Configure database connection pool for optimal performance
        
        Args:
            engine: SQLAlchemy engine
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum overflow connections
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Time to recycle connections
            
        Returns:
            Configured engine
        """
        # Configure connection pool
        engine.pool = QueuePool(
            engine.pool._creator,
            pool_size=pool_size,
            max_overflow=max_overflow,
            timeout=pool_timeout,
            recycle=pool_recycle,
            pre_ping=True  # Verify connections before use
        )
        
        logger.info(f"Connection pool configured: size={pool_size}, overflow={max_overflow}")
        return engine
    
    @staticmethod
    def get_pool_status(engine: Engine) -> Dict[str, Any]:
        """Get connection pool status"""
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }


def batch_process_queries(
    queries: List[Query],
    batch_size: int = 100,
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process multiple queries in batches for better performance
    
    Args:
        queries: List of SQLAlchemy queries
        batch_size: Number of queries per batch
        max_concurrent: Maximum concurrent batch processing
        
    Returns:
        List of query results
    """
    results = []
    
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]
        
        # Process batch
        batch_results = []
        for query in batch:
            try:
                result = query.all()
                batch_results.append(result)
            except SQLAlchemyError as e:
                logger.error(f"Batch query error: {e}")
                batch_results.append([])
        
        results.extend(batch_results)
    
    return results


class QueryCache:
    """Simple in-memory query result cache"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times = {}
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.access_times:
            return True
        
        return time.time() - self.access_times[key] > self.ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached query result"""
        if key in self.cache and not self._is_expired(key):
            self.access_times[key] = time.time()
            return self.cache[key]
        
        # Remove expired entry
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
        
        return None
    
    def set(self, key: str, value: Any):
        """Cache query result"""
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl
        }


# Global query cache instance
query_cache = QueryCache()
