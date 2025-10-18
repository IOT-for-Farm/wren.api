"""
Cache Management Utilities

Simple in-memory cache manager for API response caching.
"""

from typing import Any, Optional, Dict
import time
import threading
from datetime import datetime, timedelta


class CacheManager:
    """Simple in-memory cache manager with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache manager with default TTL in seconds."""
        self.cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if time.time() > entry['expires_at']:
                del self.cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self.lock:
            expires_at = time.time() + (ttl or self.default_ttl)
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count."""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time > entry['expires_at']
            ]
            for key in expired_keys:
                del self.cache[key]
            return len(expired_keys)
