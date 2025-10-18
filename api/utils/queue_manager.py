"""
Queue Management Utilities

Simple queue management for batch processing.
"""

from typing import List, Any, Dict, Optional
from datetime import datetime
from collections import deque
import threading


class QueueManager:
    """Manages processing queues for batch operations."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize queue manager."""
        self.queues = {}
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def create_queue(self, queue_name: str) -> bool:
        """Create a new processing queue."""
        with self.lock:
            if queue_name in self.queues:
                return False
            
            self.queues[queue_name] = {
                "items": deque(maxlen=self.max_size),
                "created_at": datetime.now().isoformat(),
                "processed_count": 0
            }
            return True
    
    def add_to_queue(self, queue_name: str, item: Any) -> bool:
        """Add item to queue."""
        with self.lock:
            if queue_name not in self.queues:
                return False
            
            queue = self.queues[queue_name]
            if len(queue["items"]) >= self.max_size:
                return False
            
            queue["items"].append({
                "data": item,
                "added_at": datetime.now().isoformat()
            })
            return True
    
    def get_from_queue(self, queue_name: str) -> Optional[Any]:
        """Get next item from queue."""
        with self.lock:
            if queue_name not in self.queues:
                return None
            
            queue = self.queues[queue_name]
            if not queue["items"]:
                return None
            
            item = queue["items"].popleft()
            queue["processed_count"] += 1
            return item["data"]
    
    def get_queue_status(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a queue."""
        with self.lock:
            if queue_name not in self.queues:
                return None
            
            queue = self.queues[queue_name]
            return {
                "name": queue_name,
                "size": len(queue["items"]),
                "max_size": self.max_size,
                "processed_count": queue["processed_count"],
                "created_at": queue["created_at"]
            }
    
    def clear_queue(self, queue_name: str) -> bool:
        """Clear all items from queue."""
        with self.lock:
            if queue_name not in self.queues:
                return False
            
            self.queues[queue_name]["items"].clear()
            return True
    
    def list_queues(self) -> List[Dict[str, Any]]:
        """List all queues and their status."""
        with self.lock:
            return [self.get_queue_status(name) for name in self.queues]
