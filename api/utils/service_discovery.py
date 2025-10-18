"""
Service Discovery Utilities

Simple service discovery and health checking.
"""

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """Discovers and monitors service health."""
    
    def __init__(self, health_check_interval: int = 30):
        """Initialize service discovery."""
        self.services = {}
        self.health_check_interval = health_check_interval
        self.last_health_check = {}
    
    def register_service(self, name: str, endpoints: List[str], 
                        health_check_path: str = "/health") -> None:
        """Register a service for discovery."""
        self.services[name] = {
            "endpoints": endpoints,
            "health_check_path": health_check_path,
            "status": "unknown",
            "last_check": None,
            "registered_at": datetime.now().isoformat()
        }
        logger.info(f"Registered service for discovery: {name}")
    
    def check_service_health(self, service_name: str) -> bool:
        """Check health of a specific service."""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        current_time = datetime.now()
        
        # Check if we need to perform health check
        last_check = self.last_health_check.get(service_name)
        if last_check and (current_time - last_check).seconds < self.health_check_interval:
            return service["status"] == "healthy"
        
        # Perform health check
        healthy = False
        for endpoint in service["endpoints"]:
            try:
                health_url = f"{endpoint}{service['health_check_path']}"
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    healthy = True
                    break
            except Exception as e:
                logger.warning(f"Health check failed for {endpoint}: {e}")
        
        # Update service status
        service["status"] = "healthy" if healthy else "unhealthy"
        service["last_check"] = current_time.isoformat()
        self.last_health_check[service_name] = current_time
        
        return healthy
    
    def get_healthy_services(self) -> Dict[str, List[str]]:
        """Get list of healthy services and their endpoints."""
        healthy_services = {}
        
        for service_name in self.services:
            if self.check_service_health(service_name):
                service = self.services[service_name]
                healthy_services[service_name] = service["endpoints"]
        
        return healthy_services
    
    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a service."""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        is_healthy = self.check_service_health(service_name)
        
        return {
            "name": service_name,
            "status": service["status"],
            "endpoints": service["endpoints"],
            "last_check": service["last_check"],
            "healthy": is_healthy
        }
    
    def discover_services(self) -> List[Dict[str, Any]]:
        """Discover all registered services."""
        services = []
        for service_name in self.services:
            status = self.get_service_status(service_name)
            if status:
                services.append(status)
        return services
