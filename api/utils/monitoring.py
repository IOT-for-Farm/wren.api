"""
Monitoring Utilities

Simple application monitoring and metrics collection.
"""

import time
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime


class MetricsCollector:
    """Collects and stores application metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.timers = {}
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self.counters[name] += value
    
    def record_timer(self, name: str, duration: float) -> None:
        """Record a timing metric."""
        self.metrics[f"{name}_duration"].append({
            "value": duration,
            "timestamp": time.time()
        })
    
    def start_timer(self, name: str) -> None:
        """Start timing an operation."""
        self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """End timing and record duration."""
        if name not in self.timers:
            return 0.0
        
        duration = time.time() - self.timers[name]
        self.record_timer(name, duration)
        del self.timers[name]
        return duration
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        summary = {
            "counters": dict(self.counters),
            "timers": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate timer statistics
        for metric_name, values in self.metrics.items():
            if values:
                durations = [v["value"] for v in values]
                summary["timers"][metric_name] = {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations)
                }
        
        return summary
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.timers.clear()
