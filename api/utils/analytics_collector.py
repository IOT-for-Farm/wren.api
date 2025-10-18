"""
Analytics Collection Utilities

Collect and analyze API usage analytics.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json


class AnalyticsCollector:
    """Collects and analyzes API usage data."""
    
    def __init__(self):
        """Initialize analytics collector."""
        self.events = []
        self.metrics = defaultdict(list)
        self.user_activity = defaultdict(list)
    
    def track_event(self, event_type: str, user_id: str = None, 
                   metadata: Dict[str, Any] = None) -> None:
        """Track an analytics event."""
        event = {
            "type": event_type,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        self.events.append(event)
        
        # Update metrics
        self.metrics[event_type].append(event)
        if user_id:
            self.user_activity[user_id].append(event)
    
    def track_api_call(self, endpoint: str, method: str, user_id: str = None, 
                      response_time: float = None, status_code: int = None) -> None:
        """Track API call analytics."""
        self.track_event("api_call", user_id, {
            "endpoint": endpoint,
            "method": method,
            "response_time": response_time,
            "status_code": status_code
        })
    
    def get_usage_stats(self, time_period: str = "24h") -> Dict[str, Any]:
        """Get usage statistics for a time period."""
        now = datetime.now()
        
        if time_period == "24h":
            cutoff = now - timedelta(hours=24)
        elif time_period == "7d":
            cutoff = now - timedelta(days=7)
        elif time_period == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(hours=1)
        
        recent_events = [
            event for event in self.events
            if datetime.fromisoformat(event["timestamp"]) >= cutoff
        ]
        
        return {
            "period": time_period,
            "total_events": len(recent_events),
            "unique_users": len(set(e["user_id"] for e in recent_events if e["user_id"])),
            "event_types": dict(Counter(e["type"] for e in recent_events)),
            "generated_at": now.isoformat()
        }
    
    def get_endpoint_stats(self) -> Dict[str, Any]:
        """Get statistics for API endpoints."""
        api_calls = [e for e in self.events if e["type"] == "api_call"]
        
        endpoint_counts = Counter()
        method_counts = Counter()
        status_counts = Counter()
        response_times = []
        
        for call in api_calls:
            metadata = call["metadata"]
            endpoint_counts[metadata.get("endpoint", "unknown")] += 1
            method_counts[metadata.get("method", "unknown")] += 1
            status_counts[metadata.get("status_code", 0)] += 1
            
            if metadata.get("response_time"):
                response_times.append(metadata["response_time"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_calls": len(api_calls),
            "endpoint_counts": dict(endpoint_counts),
            "method_counts": dict(method_counts),
            "status_counts": dict(status_counts),
            "avg_response_time": avg_response_time,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_user_activity(self, user_id: str) -> List[Dict[str, Any]]:
        """Get activity history for a specific user."""
        return self.user_activity.get(user_id, [])
    
    def export_analytics(self, format_type: str = "json") -> str:
        """Export analytics data."""
        data = {
            "events": self.events,
            "metrics": dict(self.metrics),
            "user_activity": dict(self.user_activity),
            "exported_at": datetime.now().isoformat()
        }
        
        if format_type == "json":
            return json.dumps(data, indent=2)
        
        return str(data)
