"""
Notification System and Event Handling for Wren API

This module provides comprehensive notification management, event handling,
and real-time communication utilities.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


class NotificationType(Enum):
    """Notification types"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Notification data structure"""
    id: str
    type: NotificationType
    recipient: str
    subject: str
    message: str
    priority: NotificationPriority
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class NotificationManager:
    """Notification management system"""
    
    def __init__(self):
        self.notifications = []
        self.event_handlers = {}
        self.notification_queue = asyncio.Queue()
        self.is_running = False
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Event handler registered for {event_type}")
    
    def unregister_event_handler(self, event_type: str, handler: Callable):
        """Unregister event handler"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                logger.info(f"Event handler unregistered for {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type}")
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Event handler error for {event_type}: {e}")
    
    def create_notification(
        self,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None
    ) -> Notification:
        """Create new notification"""
        notification = Notification(
            id=str(uuid.uuid4()),
            type=notification_type,
            recipient=recipient,
            subject=subject,
            message=message,
            priority=priority,
            data=data,
            scheduled_at=scheduled_at
        )
        
        self.notifications.append(notification)
        logger.info(f"Notification created: {notification.id}")
        
        return notification
    
    async def send_notification(self, notification: Notification) -> bool:
        """Send notification"""
        try:
            # Add to queue for processing
            await self.notification_queue.put(notification)
            
            # Emit notification event
            await self.emit_event("notification_sent", {
                "notification_id": notification.id,
                "type": notification.type.value,
                "recipient": notification.recipient
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {e}")
            return False
    
    async def process_notifications(self):
        """Process notification queue"""
        self.is_running = True
        
        while self.is_running:
            try:
                # Get notification from queue
                notification = await asyncio.wait_for(
                    self.notification_queue.get(), 
                    timeout=1.0
                )
                
                # Process notification based on type
                success = await self._process_notification(notification)
                
                if success:
                    logger.info(f"Notification processed: {notification.id}")
                else:
                    logger.error(f"Failed to process notification: {notification.id}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Notification processing error: {e}")
    
    async def _process_notification(self, notification: Notification) -> bool:
        """Process individual notification"""
        try:
            if notification.type == NotificationType.EMAIL:
                return await self._send_email(notification)
            elif notification.type == NotificationType.SMS:
                return await self._send_sms(notification)
            elif notification.type == NotificationType.PUSH:
                return await self._send_push(notification)
            elif notification.type == NotificationType.IN_APP:
                return await self._send_in_app(notification)
            elif notification.type == NotificationType.WEBHOOK:
                return await self._send_webhook(notification)
            else:
                logger.error(f"Unknown notification type: {notification.type}")
                return False
                
        except Exception as e:
            logger.error(f"Notification processing failed: {e}")
            return False
    
    async def _send_email(self, notification: Notification) -> bool:
        """Send email notification"""
        # Implement email sending logic
        logger.info(f"Sending email to {notification.recipient}: {notification.subject}")
        return True
    
    async def _send_sms(self, notification: Notification) -> bool:
        """Send SMS notification"""
        # Implement SMS sending logic
        logger.info(f"Sending SMS to {notification.recipient}: {notification.message}")
        return True
    
    async def _send_push(self, notification: Notification) -> bool:
        """Send push notification"""
        # Implement push notification logic
        logger.info(f"Sending push notification to {notification.recipient}")
        return True
    
    async def _send_in_app(self, notification: Notification) -> bool:
        """Send in-app notification"""
        # Implement in-app notification logic
        logger.info(f"Sending in-app notification to {notification.recipient}")
        return True
    
    async def _send_webhook(self, notification: Notification) -> bool:
        """Send webhook notification"""
        # Implement webhook sending logic
        logger.info(f"Sending webhook to {notification.recipient}")
        return True
    
    def get_notifications(self, recipient: str = None, limit: int = 50) -> List[Notification]:
        """Get notifications"""
        notifications = self.notifications
        
        if recipient:
            notifications = [n for n in notifications if n.recipient == recipient]
        
        return notifications[-limit:]
    
    def stop_processing(self):
        """Stop notification processing"""
        self.is_running = False
        logger.info("Notification processing stopped")


class EventManager:
    """Event management system"""
    
    def __init__(self):
        self.events = []
        self.event_handlers = {}
    
    def register_handler(self, event_name: str, handler: Callable):
        """Register event handler"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    async def trigger_event(self, event_name: str, data: Dict[str, Any]):
        """Trigger event"""
        event = {
            "id": str(uuid.uuid4()),
            "name": event_name,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        
        self.events.append(event)
        
        # Call registered handlers
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
    
    def get_events(self, event_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events"""
        events = self.events
        
        if event_name:
            events = [e for e in events if e["name"] == event_name]
        
        return events[-limit:]


# Global notification and event management instances
def get_notification_manager() -> NotificationManager:
    """Get notification manager instance"""
    return NotificationManager()

def get_event_manager() -> EventManager:
    """Get event manager instance"""
    return EventManager()
