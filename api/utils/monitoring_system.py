"""
Logging and Monitoring System for Wren API

This module provides comprehensive logging, monitoring, and observability
utilities for the Wren API.
"""

import time
import json
import threading
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import logging
import psutil
import os

from api.utils.loggers import create_logger

logger = create_logger(__name__)


@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


class MetricsCollector:
    """Metrics collection and aggregation"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.is_collecting = False
        self.collection_thread = None
    
    def start_collection(self, interval: int = 60):
        """Start metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_thread = threading.Thread(
            target=self._collect_metrics_loop,
            args=(interval,),
            daemon=True
        )
        self.collection_thread.start()
        logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join()
        logger.info("Metrics collection stopped")
    
    def _collect_metrics_loop(self, interval: int):
        """Metrics collection loop"""
        while self.is_collecting:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge("system.cpu.percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_gauge("system.memory.percent", memory.percent)
            self.record_gauge("system.memory.available", memory.available)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_gauge("system.disk.percent", disk.percent)
            self.record_gauge("system.disk.free", disk.free)
            
            # Process metrics
            process = psutil.Process(os.getpid())
            self.record_gauge("process.memory.percent", process.memory_percent())
            self.record_gauge("process.cpu.percent", process.cpu_percent())
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    def record_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Record counter metric"""
        self.counters[name] += value
        self.metrics[name].append(Metric(name, value, datetime.utcnow(), tags))
    
    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record gauge metric"""
        self.gauges[name] = value
        self.metrics[name].append(Metric(name, value, datetime.utcnow(), tags))
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record histogram metric"""
        self.histograms[name].append(value)
        self.metrics[name].append(Metric(name, value, datetime.utcnow(), tags))
    
    def get_metrics(self, name: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get metrics data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if name:
            metrics = [m for m in self.metrics[name] if m.timestamp >= cutoff_time]
            return {
                "name": name,
                "metrics": metrics,
                "count": len(metrics),
                "latest_value": metrics[-1].value if metrics else None
            }
        
        result = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {name: len(values) for name, values in self.histograms.items()},
            "total_metrics": sum(len(metrics) for metrics in self.metrics.values())
        }
        
        return result


class PerformanceMonitor:
    """Performance monitoring and profiling"""
    
    def __init__(self):
        self.performance_data = defaultdict(list)
        self.slow_operations = deque(maxlen=1000)
        self.operation_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "avg_time": 0})
    
    def start_timer(self, operation_name: str) -> str:
        """Start performance timer"""
        timer_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.performance_data[timer_id] = {
            "operation": operation_name,
            "start_time": time.time(),
            "end_time": None,
            "duration": None
        }
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End performance timer"""
        if timer_id not in self.performance_data:
            return 0
        
        end_time = time.time()
        start_time = self.performance_data[timer_id]["start_time"]
        duration = end_time - start_time
        
        self.performance_data[timer_id]["end_time"] = end_time
        self.performance_data[timer_id]["duration"] = duration
        
        # Update operation stats
        operation_name = self.performance_data[timer_id]["operation"]
        stats = self.operation_stats[operation_name]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["avg_time"] = stats["total_time"] / stats["count"]
        
        # Record slow operations
        if duration > 1.0:  # Operations taking more than 1 second
            self.slow_operations.append({
                "operation": operation_name,
                "duration": duration,
                "timestamp": datetime.utcnow()
            })
        
        return duration
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "operation_stats": dict(self.operation_stats),
            "slow_operations": list(self.slow_operations)[-10:],  # Last 10 slow operations
            "total_operations": sum(stats["count"] for stats in self.operation_stats.values()),
            "avg_operation_time": sum(stats["avg_time"] for stats in self.operation_stats.values()) / len(self.operation_stats) if self.operation_stats else 0
        }
    
    def get_slow_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slow operations"""
        return list(self.slow_operations)[-limit:]


class HealthChecker:
    """System health checking and monitoring"""
    
    def __init__(self):
        self.health_checks = {}
        self.health_status = {}
        self.last_check = {}
    
    def register_health_check(self, name: str, check_func: Callable):
        """Register health check function"""
        self.health_checks[name] = check_func
        logger.info(f"Health check registered: {name}")
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            "overall_status": "healthy",
            "checks": {},
            "timestamp": datetime.utcnow()
        }
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                check_result = check_func()
                end_time = time.time()
                
                if isinstance(check_result, dict):
                    status = check_result.get("status", "unknown")
                    message = check_result.get("message", "")
                else:
                    status = "healthy" if check_result else "unhealthy"
                    message = ""
                
                results["checks"][name] = {
                    "status": status,
                    "message": message,
                    "response_time": end_time - start_time,
                    "timestamp": datetime.utcnow()
                }
                
                if status != "healthy":
                    results["overall_status"] = "unhealthy"
                
                self.health_status[name] = results["checks"][name]
                self.last_check[name] = datetime.utcnow()
                
            except Exception as e:
                results["checks"][name] = {
                    "status": "error",
                    "message": str(e),
                    "response_time": 0,
                    "timestamp": datetime.utcnow()
                }
                results["overall_status"] = "unhealthy"
                logger.error(f"Health check '{name}' failed: {e}")
        
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "health_status": dict(self.health_status),
            "last_checks": dict(self.last_check),
            "registered_checks": list(self.health_checks.keys())
        }


class LogAggregator:
    """Log aggregation and analysis"""
    
    def __init__(self):
        self.logs = deque(maxlen=10000)
        self.log_levels = defaultdict(int)
        self.error_patterns = defaultdict(int)
    
    def add_log(self, level: str, message: str, source: str = "unknown"):
        """Add log entry"""
        log_entry = {
            "level": level,
            "message": message,
            "source": source,
            "timestamp": datetime.utcnow()
        }
        
        self.logs.append(log_entry)
        self.log_levels[level] += 1
        
        # Analyze error patterns
        if level in ["ERROR", "CRITICAL"]:
            # Simple error pattern detection
            error_key = message.split(":")[0] if ":" in message else message[:50]
            self.error_patterns[error_key] += 1
    
    def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get log summary"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_logs = [log for log in self.logs if log["timestamp"] >= cutoff_time]
        
        return {
            "total_logs": len(recent_logs),
            "log_levels": dict(self.log_levels),
            "error_patterns": dict(self.error_patterns),
            "recent_errors": [log for log in recent_logs if log["level"] in ["ERROR", "CRITICAL"]][-10:]
        }
    
    def get_logs(self, level: str = None, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs with filters"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        logs = [log for log in self.logs if log["timestamp"] >= cutoff_time]
        
        if level:
            logs = [log for log in logs if log["level"] == level]
        
        return logs[-limit:]


# Global monitoring system instances
def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector instance"""
    return MetricsCollector()

def get_performance_monitor() -> PerformanceMonitor:
    """Get performance monitor instance"""
    return PerformanceMonitor()

def get_health_checker() -> HealthChecker:
    """Get health checker instance"""
    return HealthChecker()

def get_log_aggregator() -> LogAggregator:
    """Get log aggregator instance"""
    return LogAggregator()
