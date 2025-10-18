"""
Event Dispatcher Utilities

Simple event dispatching system for notifications.
"""

from typing import Dict, List, Callable, Any
import logging

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Dispatches events to registered handlers."""
    
    def __init__(self):
        """Initialize event dispatcher."""
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register event handler for specific event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for event: {event_type}")
    
    def dispatch(self, event_type: str, data: Dict[str, Any]) -> None:
        """Dispatch event to all registered handlers."""
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
    
    def unregister_handler(self, event_type: str, handler: Callable) -> bool:
        """Unregister event handler."""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            return True
        return False
    
    def get_handler_count(self, event_type: str) -> int:
        """Get number of handlers for event type."""
        return len(self.handlers.get(event_type, []))
