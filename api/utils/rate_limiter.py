"""
API Rate Limiting and Throttling for Wren API

This module provides comprehensive rate limiting, throttling, and
API usage monitoring utilities.
"""

import time
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int
    window: int  # in seconds
    burst: int = 0


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.rate_limits = {}
        self.request_counts = defaultdict(lambda: defaultdict(deque))
        self.blocked_ips = set()
        self.blocked_until = {}
    
    def add_rate_limit(self, key: str, rate_limit: RateLimit):
        """Add rate limit for a key"""
        self.rate_limits[key] = rate_limit
        logger.info(f"Rate limit added for {key}: {rate_limit.requests}/{rate_limit.window}s")
    
    def is_allowed(self, key: str, identifier: str = "default") -> Dict[str, Any]:
        """Check if request is allowed"""
        if key not in self.rate_limits:
            return {"allowed": True, "remaining": 0, "reset_time": 0}
        
        rate_limit = self.rate_limits[key]
        now = time.time()
        
        # Clean old requests
        self._clean_old_requests(key, identifier, now, rate_limit.window)
        
        # Check if blocked
        if identifier in self.blocked_until:
            if now < self.blocked_until[identifier]:
                return {
                    "allowed": False,
                    "reason": "blocked",
                    "blocked_until": self.blocked_until[identifier],
                    "remaining": 0,
                    "reset_time": now + rate_limit.window
                }
            else:
                del self.blocked_until[identifier]
        
        # Check rate limit
        current_requests = len(self.request_counts[key][identifier])
        
        if current_requests >= rate_limit.requests:
            # Check burst limit
            if rate_limit.burst > 0 and current_requests < rate_limit.requests + rate_limit.burst:
                # Allow burst request
                self.request_counts[key][identifier].append(now)
                return {
                    "allowed": True,
                    "remaining": rate_limit.requests + rate_limit.burst - current_requests - 1,
                    "reset_time": now + rate_limit.window,
                    "burst_used": True
                }
            else:
                # Rate limit exceeded
                return {
                    "allowed": False,
                    "reason": "rate_limit_exceeded",
                    "remaining": 0,
                    "reset_time": now + rate_limit.window
                }
        
        # Allow request
        self.request_counts[key][identifier].append(now)
        
        return {
            "allowed": True,
            "remaining": rate_limit.requests - current_requests - 1,
            "reset_time": now + rate_limit.window
        }
    
    def _clean_old_requests(self, key: str, identifier: str, now: float, window: int):
        """Clean old requests from the queue"""
        cutoff_time = now - window
        requests = self.request_counts[key][identifier]
        
        while requests and requests[0] < cutoff_time:
            requests.popleft()
    
    def block_identifier(self, identifier: str, duration: int = 3600):
        """Block identifier for specified duration"""
        self.blocked_until[identifier] = time.time() + duration
        logger.warning(f"Blocked {identifier} for {duration} seconds")
    
    def unblock_identifier(self, identifier: str):
        """Unblock identifier"""
        if identifier in self.blocked_until:
            del self.blocked_until[identifier]
            logger.info(f"Unblocked {identifier}")
    
    def get_stats(self, key: str = None) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        if key:
            return {
                "key": key,
                "rate_limit": self.rate_limits.get(key),
                "active_identifiers": len(self.request_counts[key]),
                "blocked_count": len([i for i in self.blocked_until.keys() if i.startswith(key)])
            }
        
        return {
            "total_rate_limits": len(self.rate_limits),
            "total_blocked": len(self.blocked_until),
            "active_identifiers": sum(len(identifiers) for identifiers in self.request_counts.values())
        }


class Throttler:
    """Request throttling implementation"""
    
    def __init__(self):
        self.throttle_configs = {}
        self.request_times = defaultdict(list)
    
    def add_throttle_config(self, key: str, max_requests: int, time_window: int):
        """Add throttle configuration"""
        self.throttle_configs[key] = {
            "max_requests": max_requests,
            "time_window": time_window
        }
        logger.info(f"Throttle config added for {key}: {max_requests}/{time_window}s")
    
    def should_throttle(self, key: str, identifier: str = "default") -> bool:
        """Check if request should be throttled"""
        if key not in self.throttle_configs:
            return False
        
        config = self.throttle_configs[key]
        now = time.time()
        
        # Clean old requests
        self._clean_old_requests(key, identifier, now, config["time_window"])
        
        # Check throttle limit
        current_requests = len(self.request_times[key][identifier])
        
        if current_requests >= config["max_requests"]:
            return True
        
        # Record request
        self.request_times[key][identifier].append(now)
        return False
    
    def _clean_old_requests(self, key: str, identifier: str, now: float, time_window: int):
        """Clean old requests"""
        cutoff_time = now - time_window
        requests = self.request_times[key][identifier]
        
        while requests and requests[0] < cutoff_time:
            requests.pop(0)
    
    def get_throttle_stats(self, key: str = None) -> Dict[str, Any]:
        """Get throttle statistics"""
        if key:
            return {
                "key": key,
                "config": self.throttle_configs.get(key),
                "active_identifiers": len(self.request_times[key])
            }
        
        return {
            "total_configs": len(self.throttle_configs),
            "active_identifiers": sum(len(identifiers) for identifiers in self.request_times.values())
        }


class APIMonitor:
    """API usage monitoring"""
    
    def __init__(self):
        self.api_calls = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {"calls": 0, "errors": 0, "avg_time": 0})
        self.user_stats = defaultdict(lambda: {"calls": 0, "last_call": None})
    
    def record_api_call(self, endpoint: str, user_id: str = None, response_time: float = 0, error: bool = False):
        """Record API call"""
        self.api_calls[endpoint] += 1
        
        if user_id:
            self.user_stats[user_id]["calls"] += 1
            self.user_stats[user_id]["last_call"] = datetime.utcnow()
        
        # Update endpoint stats
        stats = self.endpoint_stats[endpoint]
        stats["calls"] += 1
        if error:
            stats["errors"] += 1
        
        # Update average response time
        if response_time > 0:
            stats["avg_time"] = (stats["avg_time"] + response_time) / 2
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API statistics"""
        return {
            "total_calls": sum(self.api_calls.values()),
            "unique_endpoints": len(self.api_calls),
            "top_endpoints": sorted(self.api_calls.items(), key=lambda x: x[1], reverse=True)[:10],
            "endpoint_stats": dict(self.endpoint_stats),
            "user_stats": dict(self.user_stats)
        }
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific statistics"""
        return self.user_stats.get(user_id, {"calls": 0, "last_call": None})


# Global rate limiting and monitoring instances
def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    return RateLimiter()

def get_throttler() -> Throttler:
    """Get throttler instance"""
    return Throttler()

def get_api_monitor() -> APIMonitor:
    """Get API monitor instance"""
    return APIMonitor()
