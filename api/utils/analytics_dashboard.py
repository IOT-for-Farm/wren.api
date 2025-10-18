"""
Analytics Dashboard Utilities

Generate analytics dashboards and reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .analytics_collector import AnalyticsCollector


class AnalyticsDashboard:
    """Generates analytics dashboards and reports."""
    
    def __init__(self, collector: AnalyticsCollector):
        """Initialize analytics dashboard."""
        self.collector = collector
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data."""
        return {
            "overview": self._get_overview_metrics(),
            "api_usage": self.collector.get_endpoint_stats(),
            "user_activity": self._get_user_activity_summary(),
            "performance": self._get_performance_metrics(),
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_overview_metrics(self) -> Dict[str, Any]:
        """Get overview metrics."""
        stats_24h = self.collector.get_usage_stats("24h")
        stats_7d = self.collector.get_usage_stats("7d")
        
        return {
            "events_24h": stats_24h["total_events"],
            "events_7d": stats_7d["total_events"],
            "unique_users_24h": stats_24h["unique_users"],
            "unique_users_7d": stats_7d["unique_users"],
            "top_events_24h": list(stats_24h["event_types"].keys())[:5]
        }
    
    def _get_user_activity_summary(self) -> Dict[str, Any]:
        """Get user activity summary."""
        all_users = set()
        active_users = set()
        
        for event in self.collector.events:
            if event["user_id"]:
                all_users.add(event["user_id"])
                if datetime.fromisoformat(event["timestamp"]) >= datetime.now() - timedelta(hours=24):
                    active_users.add(event["user_id"])
        
        return {
            "total_users": len(all_users),
            "active_users_24h": len(active_users),
            "activity_rate": len(active_users) / len(all_users) if all_users else 0
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        api_calls = [e for e in self.collector.events if e["type"] == "api_call"]
        response_times = [
            e["metadata"]["response_time"] for e in api_calls
            if e["metadata"].get("response_time")
        ]
        
        if not response_times:
            return {"avg_response_time": 0, "max_response_time": 0}
        
        return {
            "avg_response_time": sum(response_times) / len(response_times),
            "max_response_time": max(response_times),
            "min_response_time": min(response_times),
            "total_calls": len(api_calls)
        }
    
    def generate_report(self, report_type: str = "summary") -> Dict[str, Any]:
        """Generate specific type of report."""
        if report_type == "summary":
            return self.generate_dashboard_data()
        elif report_type == "usage":
            return self.collector.get_usage_stats("7d")
        elif report_type == "performance":
            return self._get_performance_metrics()
        else:
            return {"error": "Unknown report type"}
    
    def get_trend_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get trend data for the last N days."""
        trends = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            day_events = [
                e for e in self.collector.events
                if start_of_day <= datetime.fromisoformat(e["timestamp"]) < end_of_day
            ]
            
            trends.append({
                "date": start_of_day.strftime("%Y-%m-%d"),
                "events": len(day_events),
                "unique_users": len(set(e["user_id"] for e in day_events if e["user_id"]))
            })
        
        return list(reversed(trends))
