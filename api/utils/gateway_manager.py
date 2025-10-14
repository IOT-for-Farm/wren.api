"""
API Gateway and Load Balancing for Wren API

This module provides comprehensive API gateway functionality, load balancing,
and request routing utilities.
"""

import asyncio
import time
import random
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    IP_HASH = "ip_hash"


class ServerStatus(Enum):
    """Server status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    OVERLOADED = "overloaded"


@dataclass
class BackendServer:
    """Backend server configuration"""
    id: str
    host: str
    port: int
    weight: int = 1
    status: ServerStatus = ServerStatus.HEALTHY
    active_connections: int = 0
    total_requests: int = 0
    response_time: float = 0.0
    last_health_check: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Route:
    """API route configuration"""
    path: str
    methods: List[str]
    backend_servers: List[BackendServer]
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    timeout: int = 30
    retry_count: int = 3
    rate_limit: Optional[int] = None
    authentication_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class LoadBalancer:
    """Load balancer implementation"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.servers: List[BackendServer] = []
        self.current_index = 0
        self.server_weights: Dict[str, int] = {}
        self.server_connections: Dict[str, int] = {}
    
    def add_server(self, server: BackendServer):
        """Add backend server"""
        self.servers.append(server)
        self.server_weights[server.id] = server.weight
        self.server_connections[server.id] = 0
        logger.info(f"Backend server added: {server.host}:{server.port}")
    
    def remove_server(self, server_id: str):
        """Remove backend server"""
        self.servers = [s for s in self.servers if s.id != server_id]
        if server_id in self.server_weights:
            del self.server_weights[server_id]
        if server_id in self.server_connections:
            del self.server_connections[server_id]
        logger.info(f"Backend server removed: {server_id}")
    
    def get_next_server(self, client_ip: str = None) -> Optional[BackendServer]:
        """Get next server based on load balancing strategy"""
        healthy_servers = [s for s in self.servers if s.status == ServerStatus.HEALTHY]
        
        if not healthy_servers:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(healthy_servers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_servers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_selection(healthy_servers)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_selection(healthy_servers)
        elif self.strategy == LoadBalancingStrategy.IP_HASH:
            return self._ip_hash_selection(healthy_servers, client_ip)
        else:
            return healthy_servers[0]
    
    def _round_robin_selection(self, servers: List[BackendServer]) -> BackendServer:
        """Round robin server selection"""
        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server
    
    def _least_connections_selection(self, servers: List[BackendServer]) -> BackendServer:
        """Least connections server selection"""
        return min(servers, key=lambda s: s.active_connections)
    
    def _weighted_round_robin_selection(self, servers: List[BackendServer]) -> BackendServer:
        """Weighted round robin server selection"""
        total_weight = sum(s.weight for s in servers)
        if total_weight == 0:
            return servers[0]
        
        # Simple weighted selection
        weights = [s.weight for s in servers]
        selected_index = random.choices(range(len(servers)), weights=weights)[0]
        return servers[selected_index]
    
    def _random_selection(self, servers: List[BackendServer]) -> BackendServer:
        """Random server selection"""
        return random.choice(servers)
    
    def _ip_hash_selection(self, servers: List[BackendServer], client_ip: str) -> BackendServer:
        """IP hash server selection"""
        if not client_ip:
            return servers[0]
        
        hash_value = hash(client_ip) % len(servers)
        return servers[hash_value]
    
    def update_server_connections(self, server_id: str, delta: int):
        """Update server connection count"""
        if server_id in self.server_connections:
            self.server_connections[server_id] += delta
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "total_servers": len(self.servers),
            "healthy_servers": len([s for s in self.servers if s.status == ServerStatus.HEALTHY]),
            "unhealthy_servers": len([s for s in self.servers if s.status == ServerStatus.UNHEALTHY]),
            "total_connections": sum(self.server_connections.values()),
            "servers": [
                {
                    "id": s.id,
                    "host": s.host,
                    "port": s.port,
                    "status": s.status.value,
                    "active_connections": s.active_connections,
                    "weight": s.weight
                }
                for s in self.servers
            ]
        }


class HealthChecker:
    """Server health checking"""
    
    def __init__(self, check_interval: int = 30, timeout: int = 5):
        self.check_interval = check_interval
        self.timeout = timeout
        self.health_checks = {}
        self.is_running = False
    
    async def start_health_checks(self, load_balancer: LoadBalancer):
        """Start health checking for servers"""
        self.is_running = True
        logger.info("Health checker started")
        
        while self.is_running:
            try:
                await self._check_servers_health(load_balancer)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_servers_health(self, load_balancer: LoadBalancer):
        """Check health of all servers"""
        for server in load_balancer.servers:
            try:
                is_healthy = await self._check_server_health(server)
                
                if is_healthy and server.status != ServerStatus.HEALTHY:
                    server.status = ServerStatus.HEALTHY
                    logger.info(f"Server {server.id} is now healthy")
                elif not is_healthy and server.status == ServerStatus.HEALTHY:
                    server.status = ServerStatus.UNHEALTHY
                    logger.warning(f"Server {server.id} is now unhealthy")
                
                server.last_health_check = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Health check failed for server {server.id}: {e}")
                server.status = ServerStatus.UNHEALTHY
    
    async def _check_server_health(self, server: BackendServer) -> bool:
        """Check individual server health"""
        try:
            # Simple HTTP health check
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                url = f"http://{server.host}:{server.port}/health"
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def stop_health_checks(self):
        """Stop health checking"""
        self.is_running = False
        logger.info("Health checker stopped")


class APIGateway:
    """API Gateway implementation"""
    
    def __init__(self):
        self.routes: Dict[str, Route] = {}
        self.load_balancers: Dict[str, LoadBalancer] = {}
        self.health_checker = HealthChecker()
        self.rate_limiter = {}
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": []
        }
    
    def add_route(self, route: Route):
        """Add API route"""
        route_key = f"{route.path}:{':'.join(route.methods)}"
        self.routes[route_key] = route
        
        # Create load balancer for route
        self.load_balancers[route_key] = LoadBalancer(route.load_balancing_strategy)
        for server in route.backend_servers:
            self.load_balancers[route_key].add_server(server)
        
        logger.info(f"Route added: {route.path}")
    
    def remove_route(self, path: str, methods: List[str]):
        """Remove API route"""
        route_key = f"{path}:{':'.join(methods)}"
        if route_key in self.routes:
            del self.routes[route_key]
            if route_key in self.load_balancers:
                del self.load_balancers[route_key]
            logger.info(f"Route removed: {path}")
    
    def get_route(self, path: str, method: str) -> Optional[Route]:
        """Get route for path and method"""
        for route_key, route in self.routes.items():
            if route.path == path and method in route.methods:
                return route
        return None
    
    async def route_request(self, path: str, method: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to backend server"""
        route = self.get_route(path, method)
        if not route:
            return {
                "status_code": 404,
                "body": {"error": "Route not found"},
                "headers": {"Content-Type": "application/json"}
            }
        
        # Check rate limiting
        if route.rate_limit and not self._check_rate_limit(path, method):
            return {
                "status_code": 429,
                "body": {"error": "Rate limit exceeded"},
                "headers": {"Content-Type": "application/json"}
            }
        
        # Get backend server
        load_balancer = self.load_balancers[f"{path}:{':'.join(route.methods)}"]
        server = load_balancer.get_next_server(request_data.get("client_ip"))
        
        if not server:
            return {
                "status_code": 503,
                "body": {"error": "No healthy servers available"},
                "headers": {"Content-Type": "application/json"}
            }
        
        # Forward request to backend
        try:
            start_time = time.time()
            response = await self._forward_request(server, request_data)
            response_time = time.time() - start_time
            
            # Update statistics
            self._update_request_stats(response["status_code"], response_time)
            server.total_requests += 1
            server.response_time = (server.response_time + response_time) / 2
            
            return response
            
        except Exception as e:
            logger.error(f"Request forwarding failed: {e}")
            return {
                "status_code": 500,
                "body": {"error": "Internal server error"},
                "headers": {"Content-Type": "application/json"}
            }
    
    async def _forward_request(self, server: BackendServer, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to backend server"""
        import aiohttp
        
        url = f"http://{server.host}:{server.port}{request_data.get('path', '')}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request_data.get("method", "GET"),
                url=url,
                headers=request_data.get("headers", {}),
                json=request_data.get("body")
            ) as response:
                body = await response.text()
                
                return {
                    "status_code": response.status,
                    "body": body,
                    "headers": dict(response.headers)
                }
    
    def _check_rate_limit(self, path: str, method: str) -> bool:
        """Check rate limit for route"""
        # Simple rate limiting implementation
        key = f"{path}:{method}"
        current_time = time.time()
        
        if key not in self.rate_limiter:
            self.rate_limiter[key] = {"count": 0, "window_start": current_time}
        
        rate_data = self.rate_limiter[key]
        
        # Reset window if needed
        if current_time - rate_data["window_start"] > 60:  # 1 minute window
            rate_data["count"] = 0
            rate_data["window_start"] = current_time
        
        rate_data["count"] += 1
        
        # Check if limit exceeded (simplified)
        return rate_data["count"] <= 100  # 100 requests per minute
    
    def _update_request_stats(self, status_code: int, response_time: float):
        """Update request statistics"""
        self.request_stats["total_requests"] += 1
        
        if 200 <= status_code < 300:
            self.request_stats["successful_requests"] += 1
        else:
            self.request_stats["failed_requests"] += 1
        
        self.request_stats["response_times"].append(response_time)
        
        # Keep only last 1000 response times
        if len(self.request_stats["response_times"]) > 1000:
            self.request_stats["response_times"] = self.request_stats["response_times"][-1000:]
    
    async def start_health_checks(self):
        """Start health checking for all routes"""
        for route_key, load_balancer in self.load_balancers.items():
            asyncio.create_task(self.health_checker.start_health_checks(load_balancer))
    
    def get_gateway_stats(self) -> Dict[str, Any]:
        """Get gateway statistics"""
        return {
            "total_routes": len(self.routes),
            "request_stats": self.request_stats,
            "load_balancers": {
                route_key: lb.get_server_stats()
                for route_key, lb in self.load_balancers.items()
            }
        }


# Global gateway and load balancing instances
def get_load_balancer(strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN) -> LoadBalancer:
    """Get load balancer instance"""
    return LoadBalancer(strategy)

def get_health_checker(check_interval: int = 30, timeout: int = 5) -> HealthChecker:
    """Get health checker instance"""
    return HealthChecker(check_interval, timeout)

def get_api_gateway() -> APIGateway:
    """Get API gateway instance"""
    return APIGateway()
