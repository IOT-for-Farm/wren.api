"""
API Analytics and Metrics for Wren API

This module provides comprehensive API analytics, metrics collection,
and performance tracking utilities.
"""

import time
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


@dataclass
class APIMetric:
    """API metric data structure"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserMetric:
    """User metric data structure"""
    user_id: str
    action: str
    resource: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class APIAnalytics:
    """API analytics and metrics collection"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.api_metrics = deque(maxlen=max_metrics)
        self.user_metrics = deque(maxlen=max_metrics)
        self.endpoint_stats = defaultdict(lambda: {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "min_response_time": float('inf'),
            "max_response_time": 0.0,
            "unique_users": set(),
            "status_codes": defaultdict(int)
        })
        self.user_stats = defaultdict(lambda: {
            "total_requests": 0,
            "unique_endpoints": set(),
            "last_activity": None,
            "total_response_time": 0.0
        })
    
    def record_api_metric(self, metric: APIMetric):
        """Record API metric"""
        self.api_metrics.append(metric)
        
        # Update endpoint statistics
        endpoint_key = f"{metric.method}:{metric.endpoint}"
        stats = self.endpoint_stats[endpoint_key]
        
        stats["total_requests"] += 1
        stats["total_response_time"] += metric.response_time
        stats["min_response_time"] = min(stats["min_response_time"], metric.response_time)
        stats["max_response_time"] = max(stats["max_response_time"], metric.response_time)
        stats["status_codes"][metric.status_code] += 1
        
        if metric.user_id:
            stats["unique_users"].add(metric.user_id)
        
        if 200 <= metric.status_code < 300:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        # Update user statistics
        if metric.user_id:
            user_stats = self.user_stats[metric.user_id]
            user_stats["total_requests"] += 1
            user_stats["unique_endpoints"].add(endpoint_key)
            user_stats["last_activity"] = metric.timestamp
            user_stats["total_response_time"] += metric.response_time
        
        logger.debug(f"API metric recorded: {endpoint_key}")
    
    def record_user_metric(self, metric: UserMetric):
        """Record user metric"""
        self.user_metrics.append(metric)
        logger.debug(f"User metric recorded: {metric.user_id} - {metric.action}")
    
    def get_endpoint_analytics(self, endpoint: str = None, method: str = None, 
                              hours: int = 24) -> Dict[str, Any]:
        """Get endpoint analytics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if endpoint and method:
            endpoint_key = f"{method}:{endpoint}"
            stats = self.endpoint_stats.get(endpoint_key, {})
        else:
            # Aggregate all endpoints
            stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0.0,
                "min_response_time": float('inf'),
                "max_response_time": 0.0,
                "unique_users": set(),
                "status_codes": defaultdict(int)
            }
            
            for endpoint_stats in self.endpoint_stats.values():
                stats["total_requests"] += endpoint_stats["total_requests"]
                stats["successful_requests"] += endpoint_stats["successful_requests"]
                stats["failed_requests"] += endpoint_stats["failed_requests"]
                stats["total_response_time"] += endpoint_stats["total_response_time"]
                stats["min_response_time"] = min(stats["min_response_time"], endpoint_stats["min_response_time"])
                stats["max_response_time"] = max(stats["max_response_time"], endpoint_stats["max_response_time"])
                stats["unique_users"].update(endpoint_stats["unique_users"])
                
                for status_code, count in endpoint_stats["status_codes"].items():
                    stats["status_codes"][status_code] += count
        
        # Calculate derived metrics
        avg_response_time = stats["total_response_time"] / stats["total_requests"] if stats["total_requests"] > 0 else 0
        success_rate = stats["successful_requests"] / stats["total_requests"] if stats["total_requests"] > 0 else 0
        
        return {
            "endpoint": endpoint,
            "method": method,
            "total_requests": stats["total_requests"],
            "successful_requests": stats["successful_requests"],
            "failed_requests": stats["failed_requests"],
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "min_response_time": stats["min_response_time"] if stats["min_response_time"] != float('inf') else 0,
            "max_response_time": stats["max_response_time"],
            "unique_users": len(stats["unique_users"]),
            "status_codes": dict(stats["status_codes"])
        }
    
    def get_user_analytics(self, user_id: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get user analytics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        if user_id:
            user_stats = self.user_stats.get(user_id, {})
        else:
            # Aggregate all users
            user_stats = {
                "total_requests": 0,
                "unique_endpoints": set(),
                "last_activity": None,
                "total_response_time": 0.0
            }
            
            for stats in self.user_stats.values():
                user_stats["total_requests"] += stats["total_requests"]
                user_stats["unique_endpoints"].update(stats["unique_endpoints"])
                if stats["last_activity"]:
                    if user_stats["last_activity"] is None or stats["last_activity"] > user_stats["last_activity"]:
                        user_stats["last_activity"] = stats["last_activity"]
                user_stats["total_response_time"] += stats["total_response_time"]
        
        avg_response_time = user_stats["total_response_time"] / user_stats["total_requests"] if user_stats["total_requests"] > 0 else 0
        
        return {
            "user_id": user_id,
            "total_requests": user_stats["total_requests"],
            "unique_endpoints": len(user_stats["unique_endpoints"]),
            "avg_response_time": avg_response_time,
            "last_activity": user_stats["last_activity"].isoformat() if user_stats["last_activity"] else None
        }
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter metrics by time
        recent_metrics = [m for m in self.api_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics found for the specified time period"}
        
        # Calculate performance metrics
        response_times = [m.response_time for m in recent_metrics]
        status_codes = [m.status_code for m in recent_metrics]
        
        return {
            "total_requests": len(recent_metrics),
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
            "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)],
            "success_rate": len([s for s in status_codes if 200 <= s < 300]) / len(status_codes),
            "error_rate": len([s for s in status_codes if s >= 400]) / len(status_codes),
            "status_code_distribution": {code: status_codes.count(code) for code in set(status_codes)}
        }
    
    def get_top_endpoints(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """Get top endpoints by request count"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter and count requests
        endpoint_counts = defaultdict(int)
        for metric in self.api_metrics:
            if metric.timestamp >= cutoff_time:
                endpoint_key = f"{metric.method}:{metric.endpoint}"
                endpoint_counts[endpoint_key] += 1
        
        # Sort and return top endpoints
        top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                "endpoint": endpoint,
                "request_count": count,
                "analytics": self.get_endpoint_analytics(*endpoint.split(":", 1), hours)
            }
            for endpoint, count in top_endpoints
        ]
    
    def get_analytics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        return {
            "time_period_hours": hours,
            "performance_metrics": self.get_performance_metrics(hours),
            "top_endpoints": self.get_top_endpoints(5, hours),
            "user_analytics": self.get_user_analytics(hours=hours),
            "endpoint_analytics": self.get_endpoint_analytics(hours=hours)
        }


class MetricsExporter:
    """Metrics export utilities"""
    
    def __init__(self, analytics: APIAnalytics):
        self.analytics = analytics
    
    def export_to_json(self, hours: int = 24) -> str:
        """Export analytics to JSON"""
        summary = self.analytics.get_analytics_summary(hours)
        return json.dumps(summary, indent=2, default=str)
    
    def export_to_csv(self, hours: int = 24) -> str:
        """Export API metrics to CSV"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.analytics.api_metrics if m.timestamp >= cutoff_time]
        
        csv_lines = ["timestamp,endpoint,method,status_code,response_time,user_id,ip_address"]
        
        for metric in recent_metrics:
            csv_lines.append(
                f"{metric.timestamp.isoformat()},{metric.endpoint},{metric.method},"
                f"{metric.status_code},{metric.response_time},{metric.user_id or ''},{metric.ip_address or ''}"
            )
        
        return "\n".join(csv_lines)
    
    def export_user_metrics_to_csv(self, hours: int = 24) -> str:
        """Export user metrics to CSV"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.analytics.user_metrics if m.timestamp >= cutoff_time]
        
        csv_lines = ["timestamp,user_id,action,resource"]
        
        for metric in recent_metrics:
            csv_lines.append(
                f"{metric.timestamp.isoformat()},{metric.user_id},{metric.action},{metric.resource}"
            )
        
        return "\n".join(csv_lines)


class RealTimeAnalytics:
    """Real-time analytics and monitoring"""
    
    def __init__(self, analytics: APIAnalytics):
        self.analytics = analytics
        self.alert_thresholds = {
            "response_time": 2.0,  # seconds
            "error_rate": 0.1,     # 10%
            "request_rate": 1000   # requests per minute
        }
        self.alerts = []
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        current_alerts = []
        
        # Check response time
        recent_metrics = list(self.analytics.api_metrics)[-100:]  # Last 100 requests
        if recent_metrics:
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
            if avg_response_time > self.alert_thresholds["response_time"]:
                current_alerts.append({
                    "type": "high_response_time",
                    "message": f"Average response time is {avg_response_time:.2f}s",
                    "value": avg_response_time,
                    "threshold": self.alert_thresholds["response_time"]
                })
        
        # Check error rate
        if recent_metrics:
            error_count = len([m for m in recent_metrics if m.status_code >= 400])
            error_rate = error_count / len(recent_metrics)
            if error_rate > self.alert_thresholds["error_rate"]:
                current_alerts.append({
                    "type": "high_error_rate",
                    "message": f"Error rate is {error_rate:.2%}",
                    "value": error_rate,
                    "threshold": self.alert_thresholds["error_rate"]
                })
        
        return current_alerts
    
    def set_alert_threshold(self, alert_type: str, threshold: float):
        """Set alert threshold"""
        if alert_type in self.alert_thresholds:
            self.alert_thresholds[alert_type] = threshold
            logger.info(f"Alert threshold set for {alert_type}: {threshold}")


# Global analytics instances
def get_api_analytics(max_metrics: int = 10000) -> APIAnalytics:
    """Get API analytics instance"""
    return APIAnalytics(max_metrics)

def get_metrics_exporter(analytics: APIAnalytics) -> MetricsExporter:
    """Get metrics exporter instance"""
    return MetricsExporter(analytics)

def get_real_time_analytics(analytics: APIAnalytics) -> RealTimeAnalytics:
    """Get real-time analytics instance"""
    return RealTimeAnalytics(analytics)
