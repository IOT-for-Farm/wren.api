"""
Performance Tracking Utilities

Track and analyze application performance metrics.
"""

import time
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict, deque


class PerformanceTracker:
    """Tracks application performance metrics."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize performance tracker."""
        self.max_history = max_history
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history))
        self.active_timers = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.active_timers[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing and record duration."""
        if operation not in self.active_timers:
            return 0.0
        
        duration = time.time() - self.active_timers[operation]
        self.record_metric(f"{operation}_duration", duration)
        del self.active_timers[operation]
        return duration
    
    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric."""
        metric_data = {
            "value": value,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat()
        }
        self.metrics_history[name].append(metric_data)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_metric_summary(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a metric."""
        if metric_name not in self.metrics_history:
            return None
        
        values = [m["value"] for m in self.metrics_history[metric_name]]
        if not values:
            return None
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else None
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.get_system_metrics(),
            "metric_summaries": {}
        }
        
        for metric_name in self.metrics_history:
            summary = self.get_metric_summary(metric_name)
            if summary:
                report["metric_summaries"][metric_name] = summary
        
        return report
