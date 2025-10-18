"""
API Gateway Router

Simple API gateway routing and request forwarding utilities.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GatewayRouter:
    """Routes requests to appropriate services."""
    
    def __init__(self):
        """Initialize gateway router."""
        self.routes = {}
        self.services = {}
        self.load_balancer = RoundRobinBalancer()
    
    def register_service(self, name: str, endpoints: List[str], health_check: str = None) -> None:
        """Register a service with the gateway."""
        self.services[name] = {
            "endpoints": endpoints,
            "health_check": health_check,
            "active": True,
            "registered_at": datetime.now().isoformat()
        }
        logger.info(f"Registered service: {name}")
    
    def add_route(self, path: str, service: str, methods: List[str] = None) -> None:
        """Add a route to the gateway."""
        if methods is None:
            methods = ["GET"]
        
        self.routes[path] = {
            "service": service,
            "methods": methods,
            "created_at": datetime.now().isoformat()
        }
        logger.info(f"Added route: {path} -> {service}")
    
    def get_service_endpoint(self, service_name: str) -> Optional[str]:
        """Get an active endpoint for a service."""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        if not service["active"]:
            return None
        
        return self.load_balancer.select_endpoint(service["endpoints"])
    
    def route_request(self, path: str, method: str) -> Dict[str, Any]:
        """Route a request to the appropriate service."""
        if path not in self.routes:
            return {"error": "Route not found", "status": 404}
        
        route = self.routes[path]
        if method not in route["methods"]:
            return {"error": "Method not allowed", "status": 405}
        
        service_name = route["service"]
        endpoint = self.get_service_endpoint(service_name)
        
        if not endpoint:
            return {"error": "Service unavailable", "status": 503}
        
        return {
            "service": service_name,
            "endpoint": endpoint,
            "status": 200
        }
    
    def get_route_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get information about a route."""
        if path not in self.routes:
            return None
        
        route = self.routes[path]
        service_name = route["service"]
        service_info = self.services.get(service_name, {})
        
        return {
            "path": path,
            "service": service_name,
            "methods": route["methods"],
            "endpoints": service_info.get("endpoints", []),
            "active": service_info.get("active", False)
        }


class RoundRobinBalancer:
    """Simple round-robin load balancer."""
    
    def __init__(self):
        """Initialize load balancer."""
        self.current_index = 0
    
    def select_endpoint(self, endpoints: List[str]) -> str:
        """Select next endpoint using round-robin."""
        if not endpoints:
            return None
        
        endpoint = endpoints[self.current_index]
        self.current_index = (self.current_index + 1) % len(endpoints)
        return endpoint
