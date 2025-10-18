"""
Notification Management Utilities

Simple notification system for user alerts and messages.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages user notifications and alerts."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.notifications = []
        self.subscribers = {}
    
    def create_notification(self, user_id: str, title: str, message: str, 
                          notification_type: str = "info") -> Dict[str, Any]:
        """Create a new notification."""
        notification = {
            "id": f"notif_{len(self.notifications) + 1}",
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "created_at": datetime.now().isoformat(),
            "read": False
        }
        self.notifications.append(notification)
        return notification
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user."""
        user_notifications = [
            n for n in self.notifications if n["user_id"] == user_id
        ]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n["read"]]
        
        return sorted(user_notifications, key=lambda x: x["created_at"], reverse=True)
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        for notification in self.notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                return True
        return False
    
    def subscribe_user(self, user_id: str, event_types: List[str]) -> None:
        """Subscribe user to specific event types."""
        self.subscribers[user_id] = event_types
        logger.info(f"User {user_id} subscribed to events: {event_types}")
    
    def send_bulk_notification(self, user_ids: List[str], title: str, 
                              message: str, notification_type: str = "info") -> int:
        """Send notification to multiple users."""
        sent_count = 0
        for user_id in user_ids:
            self.create_notification(user_id, title, message, notification_type)
            sent_count += 1
        return sent_count
