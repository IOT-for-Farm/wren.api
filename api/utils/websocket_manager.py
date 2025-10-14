"""
WebSocket and Real-time Communication for Wren API

This module provides comprehensive WebSocket management, real-time communication,
and event broadcasting utilities.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Union, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"


class ConnectionStatus(Enum):
    """Connection status enumeration"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    id: str
    type: MessageType
    content: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sender_id: Optional[str] = None
    recipient_id: Optional[str] = None
    room: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketConnection:
    """WebSocket connection information"""
    id: str
    websocket: Any
    user_id: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebSocketManager:
    """WebSocket connection management"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.room_connections: Dict[str, Set[str]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.connection_handlers: Dict[str, Callable] = {}
        self.heartbeat_interval = 30
        self.max_connections = 1000
    
    def add_connection(self, websocket: Any, user_id: Optional[str] = None) -> str:
        """Add WebSocket connection"""
        if len(self.connections) >= self.max_connections:
            raise Exception("Maximum connections reached")
        
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket,
            user_id=user_id
        )
        
        self.connections[connection_id] = connection
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connection added: {connection_id}")
        return connection_id
    
    def remove_connection(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            
            # Remove from user connections
            if connection.user_id and connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]
            
            # Remove from rooms
            for room in connection.rooms:
                if room in self.room_connections:
                    self.room_connections[room].discard(connection_id)
                    if not self.room_connections[room]:
                        del self.room_connections[room]
            
            del self.connections[connection_id]
            logger.info(f"WebSocket connection removed: {connection_id}")
    
    def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """Get connections for user"""
        connection_ids = self.user_connections.get(user_id, set())
        return [self.connections[cid] for cid in connection_ids if cid in self.connections]
    
    def join_room(self, connection_id: str, room: str):
        """Join connection to room"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.rooms.add(room)
            
            if room not in self.room_connections:
                self.room_connections[room] = set()
            self.room_connections[room].add(connection_id)
            
            logger.info(f"Connection {connection_id} joined room {room}")
    
    def leave_room(self, connection_id: str, room: str):
        """Remove connection from room"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.rooms.discard(room)
            
            if room in self.room_connections:
                self.room_connections[room].discard(connection_id)
                if not self.room_connections[room]:
                    del self.room_connections[room]
            
            logger.info(f"Connection {connection_id} left room {room}")
    
    def get_room_connections(self, room: str) -> List[WebSocketConnection]:
        """Get connections in room"""
        connection_ids = self.room_connections.get(room, set())
        return [self.connections[cid] for cid in connection_ids if cid in self.connections]
    
    async def send_message(self, connection_id: str, message: WebSocketMessage):
        """Send message to specific connection"""
        connection = self.get_connection(connection_id)
        if connection and connection.status == ConnectionStatus.CONNECTED:
            try:
                if message.type == MessageType.JSON:
                    content = json.dumps(message.content)
                else:
                    content = str(message.content)
                
                await connection.websocket.send_text(content)
                connection.last_activity = datetime.utcnow()
                logger.debug(f"Message sent to connection {connection_id}")
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                connection.status = ConnectionStatus.ERROR
    
    async def broadcast_to_room(self, room: str, message: WebSocketMessage):
        """Broadcast message to all connections in room"""
        connections = self.get_room_connections(room)
        for connection in connections:
            await self.send_message(connection.id, message)
    
    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage):
        """Broadcast message to all connections of user"""
        connections = self.get_user_connections(user_id)
        for connection in connections:
            await self.send_message(connection.id, message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connections"""
        for connection_id in list(self.connections.keys()):
            await self.send_message(connection_id, message)
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register message handler"""
        self.message_handlers[message_type] = handler
        logger.info(f"Message handler registered for type: {message_type}")
    
    def register_connection_handler(self, event_type: str, handler: Callable):
        """Register connection event handler"""
        self.connection_handlers[event_type] = handler
        logger.info(f"Connection handler registered for event: {event_type}")
    
    async def handle_message(self, connection_id: str, message_data: str):
        """Handle incoming message"""
        try:
            # Try to parse as JSON
            try:
                data = json.loads(message_data)
                message_type = data.get("type", "text")
                content = data.get("content", data)
            except json.JSONDecodeError:
                message_type = "text"
                content = message_data
            
            # Create message object
            message = WebSocketMessage(
                id=str(uuid.uuid4()),
                type=MessageType(message_type),
                content=content,
                sender_id=connection_id
            )
            
            # Call registered handler
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](connection_id, message)
            
            # Update connection activity
            if connection_id in self.connections:
                self.connections[connection_id].last_activity = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
    
    async def start_heartbeat(self):
        """Start heartbeat monitoring"""
        while True:
            try:
                current_time = datetime.utcnow()
                timeout_connections = []
                
                for connection_id, connection in self.connections.items():
                    if (current_time - connection.last_activity).seconds > self.heartbeat_interval * 2:
                        timeout_connections.append(connection_id)
                
                # Remove timeout connections
                for connection_id in timeout_connections:
                    logger.warning(f"Connection {connection_id} timed out")
                    await self.close_connection(connection_id)
                
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def close_connection(self, connection_id: str):
        """Close WebSocket connection"""
        connection = self.get_connection(connection_id)
        if connection:
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")
            finally:
                self.remove_connection(connection_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.connections),
            "total_users": len(self.user_connections),
            "total_rooms": len(self.room_connections),
            "max_connections": self.max_connections,
            "connection_status": {
                status.value: len([c for c in self.connections.values() if c.status == status])
                for status in ConnectionStatus
            }
        }


class EventBroadcaster:
    """Event broadcasting system"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Subscribed to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from event type"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                logger.info(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                pass
    
    async def broadcast_event(self, event_type: str, data: Any, target_room: str = None, 
                            target_user: str = None):
        """Broadcast event"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Create WebSocket message
        message = WebSocketMessage(
            id=str(uuid.uuid4()),
            type=MessageType.JSON,
            content=event
        )
        
        # Broadcast based on target
        if target_room:
            await self.websocket_manager.broadcast_to_room(target_room, message)
        elif target_user:
            await self.websocket_manager.broadcast_to_user(target_user, message)
        else:
            await self.websocket_manager.broadcast_to_all(message)
        
        # Call event handlers
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {event_type}: {e}")
        
        logger.info(f"Event broadcasted: {event_type}")
    
    def get_event_history(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        
        return events[-limit:]


class RealTimeManager:
    """Real-time communication manager"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.event_broadcaster = EventBroadcaster(self.websocket_manager)
        self.is_running = False
    
    async def start(self):
        """Start real-time manager"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start heartbeat
        asyncio.create_task(self.websocket_manager.start_heartbeat())
        
        logger.info("Real-time manager started")
    
    async def stop(self):
        """Stop real-time manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Close all connections
        for connection_id in list(self.websocket_manager.connections.keys()):
            await self.websocket_manager.close_connection(connection_id)
        
        logger.info("Real-time manager stopped")
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return {
            "is_running": self.is_running,
            "websocket_stats": self.websocket_manager.get_connection_stats(),
            "event_handlers": len(self.event_broadcaster.event_handlers),
            "event_history": len(self.event_broadcaster.event_history)
        }


# Global WebSocket and real-time instances
def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance"""
    return WebSocketManager()

def get_event_broadcaster(websocket_manager: WebSocketManager) -> EventBroadcaster:
    """Get event broadcaster instance"""
    return EventBroadcaster(websocket_manager)

def get_real_time_manager() -> RealTimeManager:
    """Get real-time manager instance"""
    return RealTimeManager()
