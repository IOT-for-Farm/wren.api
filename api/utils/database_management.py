"""
Database Management Utilities for Wren API

This module provides comprehensive database management utilities including
connection pooling, query optimization, and database administration tools.
"""

import os
import json
import time
import threading
from typing import Any, Dict, List, Optional, Union, Type, Callable
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy.engine import Engine
from sqlalchemy.inspection import inspect
import logging
from collections import defaultdict, deque
import psutil
import hashlib

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


class DatabaseConnectionManager:
    """Database connection management with pooling and monitoring"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or getattr(settings, 'DATABASE_URL', 'sqlite:///./app.db')
        self.engine = None
        self.SessionLocal = None
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "connection_errors": []
        }
        self._setup_engine()
    
    def _setup_engine(self):
        """Setup database engine with connection pooling"""
        try:
            # Configure connection pool based on database type
            if self.database_url.startswith('sqlite'):
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    pool_pre_ping=True,
                    echo=False
                )
            else:
                self.engine = create_engine(
                    self.database_url,
                    poolclass=QueuePool,
                    pool_size=20,
                    max_overflow=30,
                    pool_timeout=30,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    echo=False
                )
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Add connection event listeners
            self._add_connection_listeners()
            
            logger.info("Database connection manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup database engine: {e}")
            raise
    
    def _add_connection_listeners(self):
        """Add connection event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] += 1
            logger.debug("Database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            self.connection_stats["active_connections"] += 1
            logger.debug("Database connection checked out")
        
        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            self.connection_stats["active_connections"] -= 1
            logger.debug("Database connection checked in")
        
        @event.listens_for(self.engine, "disconnect")
        def on_disconnect(dbapi_connection, connection_record):
            self.connection_stats["active_connections"] -= 1
            logger.debug("Database connection disconnected")
    
    def get_session(self) -> Session:
        """Get database session"""
        try:
            return self.SessionLocal()
        except Exception as e:
            self.connection_stats["failed_connections"] += 1
            self.connection_stats["connection_errors"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
            logger.error(f"Failed to get database session: {e}")
            raise
    
    @contextmanager
    def get_session_context(self):
        """Get database session with context manager"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        pool = self.engine.pool
        return {
            "total_connections": self.connection_stats["total_connections"],
            "active_connections": self.connection_stats["active_connections"],
            "failed_connections": self.connection_stats["failed_connections"],
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "recent_errors": self.connection_stats["connection_errors"][-10:]  # Last 10 errors
        }
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close_all_connections(self):
        """Close all database connections"""
        try:
            self.engine.dispose()
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Failed to close database connections: {e}")


class QueryOptimizer:
    """Database query optimization utilities"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.query_cache = {}
        self.slow_queries = deque(maxlen=1000)
        self.query_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "avg_time": 0})
    
    def optimize_query(self, query: str, params: Dict[str, Any] = None) -> str:
        """Optimize SQL query"""
        try:
            # Basic query optimization
            optimized_query = query.strip()
            
            # Remove unnecessary whitespace
            optimized_query = " ".join(optimized_query.split())
            
            # Add query hints for better performance
            if "SELECT" in optimized_query.upper():
                optimized_query = self._add_select_hints(optimized_query)
            
            # Cache optimized query
            query_hash = hashlib.md5(optimized_query.encode()).hexdigest()
            self.query_cache[query_hash] = optimized_query
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"Failed to optimize query: {e}")
            return query
    
    def _add_select_hints(self, query: str) -> str:
        """Add performance hints to SELECT queries"""
        # This is a simplified implementation
        # In practice, you'd analyze the query and add appropriate hints
        
        if "ORDER BY" in query.upper() and "LIMIT" in query.upper():
            # Add index hint for ordered queries with limit
            pass
        
        if "WHERE" in query.upper():
            # Add index hint for filtered queries
            pass
        
        return query
    
    def analyze_query_performance(self, query: str, execution_time: float):
        """Analyze query performance"""
        try:
            # Record slow queries
            if execution_time > 1.0:  # Queries taking more than 1 second
                self.slow_queries.append({
                    "query": query[:200],  # Truncate for storage
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Update query statistics
            query_hash = hashlib.md5(query.encode()).hexdigest()
            stats = self.query_stats[query_hash]
            stats["count"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["count"]
            
        except Exception as e:
            logger.error(f"Failed to analyze query performance: {e}")
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slow queries"""
        return list(self.slow_queries)[-limit:]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        return {
            "total_queries": sum(stats["count"] for stats in self.query_stats.values()),
            "slow_queries": len(self.slow_queries),
            "unique_queries": len(self.query_stats),
            "avg_execution_time": sum(stats["avg_time"] for stats in self.query_stats.values()) / len(self.query_stats) if self.query_stats else 0
        }
    
    def suggest_indexes(self, query: str) -> List[str]:
        """Suggest indexes for query optimization"""
        suggestions = []
        
        try:
            # Analyze WHERE clauses
            if "WHERE" in query.upper():
                # Extract column names from WHERE clause
                # This is a simplified implementation
                suggestions.append("Consider adding indexes on columns used in WHERE clauses")
            
            # Analyze JOIN clauses
            if "JOIN" in query.upper():
                suggestions.append("Consider adding indexes on foreign key columns used in JOINs")
            
            # Analyze ORDER BY clauses
            if "ORDER BY" in query.upper():
                suggestions.append("Consider adding indexes on columns used in ORDER BY clauses")
            
        except Exception as e:
            logger.error(f"Failed to suggest indexes: {e}")
        
        return suggestions


class DatabaseMonitor:
    """Database monitoring and health checking"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.monitoring_data = deque(maxlen=1000)
        self.alert_thresholds = {
            "connection_errors": 10,
            "slow_queries": 5,
            "disk_usage": 90,
            "memory_usage": 80
        }
    
    def start_monitoring(self, interval: int = 60):
        """Start database monitoring"""
        def monitor_loop():
            while True:
                try:
                    health_data = self.check_database_health()
                    self.monitoring_data.append(health_data)
                    
                    # Check for alerts
                    self._check_alerts(health_data)
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Database monitoring error: {e}")
                    time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Database monitoring started")
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "connection_status": False,
            "query_performance": {},
            "resource_usage": {},
            "errors": []
        }
        
        try:
            # Check connection
            with self.engine.connect() as connection:
                start_time = time.time()
                connection.execute(text("SELECT 1"))
                end_time = time.time()
                
                health_data["connection_status"] = True
                health_data["query_performance"]["ping_time"] = end_time - start_time
            
            # Check resource usage
            health_data["resource_usage"] = self._get_resource_usage()
            
            # Check database size
            health_data["database_size"] = self._get_database_size()
            
        except Exception as e:
            health_data["errors"].append(str(e))
            logger.error(f"Database health check failed: {e}")
        
        return health_data
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_free": disk.free
            }
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return {}
    
    def _get_database_size(self) -> int:
        """Get database size in bytes"""
        try:
            if self.engine.url.drivername == 'sqlite':
                db_path = self.engine.url.database
                if os.path.exists(db_path):
                    return os.path.getsize(db_path)
            return 0
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return 0
    
    def _check_alerts(self, health_data: Dict[str, Any]):
        """Check for alert conditions"""
        try:
            # Check connection errors
            if not health_data["connection_status"]:
                self._send_alert("Database connection failed")
            
            # Check resource usage
            resource_usage = health_data.get("resource_usage", {})
            
            if resource_usage.get("memory_percent", 0) > self.alert_thresholds["memory_usage"]:
                self._send_alert(f"High memory usage: {resource_usage['memory_percent']}%")
            
            if resource_usage.get("disk_percent", 0) > self.alert_thresholds["disk_usage"]:
                self._send_alert(f"High disk usage: {resource_usage['disk_percent']}%")
            
            # Check query performance
            query_performance = health_data.get("query_performance", {})
            if query_performance.get("ping_time", 0) > 1.0:
                self._send_alert(f"Slow database response: {query_performance['ping_time']}s")
        
        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
    
    def _send_alert(self, message: str):
        """Send alert notification"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "severity": "warning"
        }
        
        logger.warning(f"Database Alert: {message}")
        # Here you would integrate with alerting systems (email, Slack, etc.)
    
    def get_monitoring_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get monitoring data for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            data for data in self.monitoring_data
            if datetime.fromisoformat(data["timestamp"]) >= cutoff_time
        ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get database health summary"""
        if not self.monitoring_data:
            return {"status": "no_data"}
        
        recent_data = list(self.monitoring_data)[-10:]  # Last 10 data points
        
        # Calculate averages
        avg_ping_time = sum(
            data.get("query_performance", {}).get("ping_time", 0)
            for data in recent_data
        ) / len(recent_data)
        
        avg_memory_usage = sum(
            data.get("resource_usage", {}).get("memory_percent", 0)
            for data in recent_data
        ) / len(recent_data)
        
        avg_cpu_usage = sum(
            data.get("resource_usage", {}).get("cpu_percent", 0)
            for data in recent_data
        ) / len(recent_data)
        
        # Check connection status
        connection_failures = sum(
            1 for data in recent_data
            if not data.get("connection_status", False)
        )
        
        return {
            "status": "healthy" if connection_failures == 0 else "unhealthy",
            "connection_failures": connection_failures,
            "avg_ping_time": avg_ping_time,
            "avg_memory_usage": avg_memory_usage,
            "avg_cpu_usage": avg_cpu_usage,
            "data_points": len(recent_data)
        }


class DatabaseAdministrator:
    """Database administration utilities"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information"""
        info = {
            "database_type": self.engine.url.drivername,
            "database_name": self.engine.url.database,
            "host": self.engine.url.host,
            "port": self.engine.url.port,
            "username": self.engine.url.username,
            "pool_info": {},
            "table_count": 0,
            "total_rows": 0,
            "database_size": 0
        }
        
        try:
            # Get pool information
            pool = self.engine.pool
            info["pool_info"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            # Get table information
            with self.engine.connect() as connection:
                if self.engine.url.drivername == 'sqlite':
                    # Get table count
                    result = connection.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table';"))
                    info["table_count"] = result.scalar()
                    
                    # Get total row count
                    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                    table_names = [row[0] for row in result]
                    
                    total_rows = 0
                    for table_name in table_names:
                        if table_name != 'sqlite_sequence':
                            result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
                            total_rows += result.scalar()
                    
                    info["total_rows"] = total_rows
                    
                    # Get database size
                    db_path = self.engine.url.database
                    if os.path.exists(db_path):
                        info["database_size"] = os.path.getsize(db_path)
        
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            info["error"] = str(e)
        
        return info
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance"""
        optimization_result = {
            "vacuum": False,
            "analyze": False,
            "reindex": False,
            "errors": []
        }
        
        try:
            with self.engine.connect() as connection:
                if self.engine.url.drivername == 'sqlite':
                    # Run VACUUM
                    connection.execute(text("VACUUM;"))
                    optimization_result["vacuum"] = True
                    
                    # Run ANALYZE
                    connection.execute(text("ANALYZE;"))
                    optimization_result["analyze"] = True
                    
                    # Reindex
                    connection.execute(text("REINDEX;"))
                    optimization_result["reindex"] = True
                    
                    logger.info("Database optimization completed")
        
        except Exception as e:
            optimization_result["errors"].append(str(e))
            logger.error(f"Database optimization failed: {e}")
        
        return optimization_result
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
        """Clean up old data from database"""
        cleanup_result = {
            "tables_cleaned": [],
            "rows_deleted": 0,
            "errors": []
        }
        
        try:
            with self.engine.connect() as connection:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Clean up old activity logs
                result = connection.execute(text("""
                    DELETE FROM activity_logs 
                    WHERE created_at < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                
                if result.rowcount > 0:
                    cleanup_result["tables_cleaned"].append("activity_logs")
                    cleanup_result["rows_deleted"] += result.rowcount
                
                # Clean up old sessions
                result = connection.execute(text("""
                    DELETE FROM user_sessions 
                    WHERE expires_at < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                
                if result.rowcount > 0:
                    cleanup_result["tables_cleaned"].append("user_sessions")
                    cleanup_result["rows_deleted"] += result.rowcount
                
                logger.info(f"Cleaned up {cleanup_result['rows_deleted']} old records")
        
        except Exception as e:
            cleanup_result["errors"].append(str(e))
            logger.error(f"Data cleanup failed: {e}")
        
        return cleanup_result
    
    def backup_database(self, backup_path: str) -> Dict[str, Any]:
        """Create database backup"""
        backup_result = {
            "success": False,
            "backup_path": backup_path,
            "backup_size": 0,
            "error": None
        }
        
        try:
            import shutil
            
            if self.engine.url.drivername == 'sqlite':
                # For SQLite, copy the database file
                db_path = self.engine.url.database
                shutil.copy2(db_path, backup_path)
                backup_result["backup_size"] = os.path.getsize(backup_path)
                backup_result["success"] = True
                
                logger.info(f"Database backup created: {backup_path}")
            else:
                backup_result["error"] = "Backup not implemented for this database type"
        
        except Exception as e:
            backup_result["error"] = str(e)
            logger.error(f"Database backup failed: {e}")
        
        return backup_result


# Global database management instances
def get_connection_manager() -> DatabaseConnectionManager:
    """Get database connection manager instance"""
    return DatabaseConnectionManager()

def get_query_optimizer(engine: Engine) -> QueryOptimizer:
    """Get query optimizer instance"""
    return QueryOptimizer(engine)

def get_database_monitor(engine: Engine) -> DatabaseMonitor:
    """Get database monitor instance"""
    return DatabaseMonitor(engine)

def get_database_administrator(engine: Engine) -> DatabaseAdministrator:
    """Get database administrator instance"""
    return DatabaseAdministrator(engine)
