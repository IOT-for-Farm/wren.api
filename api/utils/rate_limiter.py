"""
Rate Limiting Utilities

Simple rate limiting implementation for API endpoints.
"""

import time
from typing import Dict, Optional
from collections import defaultdict, deque


class RateLimiter:
    """Simple rate limiter using sliding window algorithm."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for key."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        return max(0, self.max_requests - len(self.requests[key]))
    
    def get_reset_time(self, key: str) -> Optional[float]:
        """Get time when rate limit resets."""
        if not self.requests[key]:
            return None
        
        oldest_request = self.requests[key][0]
        return oldest_request + self.window_seconds


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, capacity: int = 100, refill_rate: float = 1.0):
        """Initialize token bucket."""
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket."""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on time passed."""
        now = time.time()
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
