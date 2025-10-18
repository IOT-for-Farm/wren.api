"""
Kafka Event Consumer

High-performance Kafka consumer for processing business events
with integration to existing API services and models.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging
from kafka import KafkaConsumer
from kafka.errors import KafkaError, CommitFailedError
import threading
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

logger = logging.getLogger(__name__)


class ConsumerStatus(Enum):
    """Consumer status enumeration."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ConsumerConfig:
    """Consumer configuration."""
    bootstrap_servers: List[str]
    group_id: str
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 1000
    session_timeout_ms: int = 30000
    max_poll_records: int = 500
    fetch_min_bytes: int = 1
    fetch_max_wait_ms: int = 500
    max_partition_fetch_bytes: int = 1048576


@dataclass
class EventMessage:
    """Kafka event message structure."""
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Dict[str, Any]
    timestamp: datetime
    headers: Optional[Dict[str, Any]] = None


class KafkaEventConsumer:
    """High-performance Kafka consumer for business events."""
    
    def __init__(self, config: ConsumerConfig, 
                 event_handlers: Dict[str, Callable] = None):
        """Initialize Kafka consumer."""
        self.config = config
        self.consumer = None
        self.status = ConsumerStatus.STOPPED
        self.event_handlers = event_handlers or {}
        self.executor = ThreadPoolExecutor(max_workers=8)
        self._shutdown_event = threading.Event()
        self._consumption_stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "last_message_time": None,
            "start_time": None
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    def _initialize_consumer(self):
        """Initialize Kafka consumer."""
        try:
            consumer_config = {
                'bootstrap_servers': self.config.bootstrap_servers,
                'group_id': self.config.group_id,
                'auto_offset_reset': self.config.auto_offset_reset,
                'enable_auto_commit': self.config.enable_auto_commit,
                'auto_commit_interval_ms': self.config.auto_commit_interval_ms,
                'session_timeout_ms': self.config.session_timeout_ms,
                'max_poll_records': self.config.max_poll_records,
                'fetch_min_bytes': self.config.fetch_min_bytes,
                'fetch_max_wait_ms': self.config.fetch_max_wait_ms,
                'max_partition_fetch_bytes': self.config.max_partition_fetch_bytes,
                'key_deserializer': self._deserialize_key,
                'value_deserializer': self._deserialize_value,
                'consumer_timeout_ms': 1000,  # Timeout for polling
            }
            
            self.consumer = KafkaConsumer(**consumer_config)
            logger.info(f"Kafka consumer initialized for group: {self.config.group_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            raise
    
    def _deserialize_key(self, key: bytes) -> Optional[str]:
        """Deserialize message key."""
        return key.decode('utf-8') if key else None
    
    def _deserialize_value(self, value: bytes) -> Dict[str, Any]:
        """Deserialize message value from JSON."""
        try:
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to deserialize message value: {e}")
            return {}
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler for specific event type."""
        self.event_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    def register_topic_handler(self, topic: str, handler: Callable):
        """Register topic handler for specific topic."""
        self.event_handlers[f"topic:{topic}"] = handler
        logger.info(f"Registered handler for topic: {topic}")
    
    async def start_consuming(self, topics: List[str]):
        """Start consuming from specified topics."""
        if self.status == ConsumerStatus.RUNNING:
            logger.warning("Consumer is already running")
            return
        
        try:
            self.status = ConsumerStatus.STARTING
            self._initialize_consumer()
            
            # Subscribe to topics
            self.consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {topics}")
            
            self.status = ConsumerStatus.RUNNING
            self._consumption_stats["start_time"] = datetime.now()
            
            # Start consumption loop
            await self._consumption_loop()
            
        except Exception as e:
            self.status = ConsumerStatus.ERROR
            logger.error(f"Error starting consumer: {e}")
            raise
    
    async def _consumption_loop(self):
        """Main consumption loop."""
        logger.info("Starting consumption loop...")
        
        while not self._shutdown_event.is_set():
            try:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if message_batch:
                    # Process messages in parallel
                    tasks = []
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            task = asyncio.create_task(
                                self._process_message(message)
                            )
                            tasks.append(task)
                    
                    # Wait for all messages to be processed
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                
            except KafkaError as e:
                logger.error(f"Kafka error in consumption loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
            except Exception as e:
                logger.error(f"Unexpected error in consumption loop: {e}")
                await asyncio.sleep(1)
        
        logger.info("Consumption loop stopped")
    
    async def _process_message(self, message):
        """Process individual Kafka message."""
        try:
            # Create event message
            event_message = EventMessage(
                topic=message.topic,
                partition=message.partition,
                offset=message.offset,
                key=message.key,
                value=message.value,
                timestamp=datetime.fromtimestamp(message.timestamp / 1000) if message.timestamp else datetime.now(),
                headers=dict(message.headers) if message.headers else None
            )
            
            # Update stats
            self._consumption_stats["messages_processed"] += 1
            self._consumption_stats["last_message_time"] = datetime.now()
            
            # Process the message
            await self._handle_event_message(event_message)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._consumption_stats["messages_failed"] += 1
    
    async def _handle_event_message(self, event_message: EventMessage):
        """Handle event message with appropriate handler."""
        try:
            # Extract event type from message
            event_type = event_message.value.get('metadata', {}).get('event_type')
            
            # Try event type handler first
            if event_type and event_type in self.event_handlers:
                handler = self.event_handlers[event_type]
                await self._execute_handler(handler, event_message)
                return
            
            # Try topic handler
            topic_handler_key = f"topic:{event_message.topic}"
            if topic_handler_key in self.event_handlers:
                handler = self.event_handlers[topic_handler_key]
                await self._execute_handler(handler, event_message)
                return
            
            # Default handler
            if "default" in self.event_handlers:
                handler = self.event_handlers["default"]
                await self._execute_handler(handler, event_message)
                return
            
            logger.warning(f"No handler found for event: {event_type} in topic: {event_message.topic}")
            
        except Exception as e:
            logger.error(f"Error handling event message: {e}")
            raise
    
    async def _execute_handler(self, handler: Callable, event_message: EventMessage):
        """Execute event handler."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event_message)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, handler, event_message)
        except Exception as e:
            logger.error(f"Error executing handler: {e}")
            raise
    
    def stop(self):
        """Stop consumer gracefully."""
        if self.status != ConsumerStatus.RUNNING:
            logger.warning("Consumer is not running")
            return
        
        logger.info("Stopping consumer...")
        self.status = ConsumerStatus.STOPPING
        self._shutdown_event.set()
        
        # Wait for current processing to complete
        if self.consumer:
            self.consumer.close()
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        self.status = ConsumerStatus.STOPPED
        logger.info("Consumer stopped")
    
    def get_consumption_stats(self) -> Dict[str, Any]:
        """Get consumption statistics."""
        stats = self._consumption_stats.copy()
        stats["status"] = self.status.value
        stats["uptime_seconds"] = (
            (datetime.now() - stats["start_time"]).total_seconds()
            if stats["start_time"] else 0
        )
        return stats
    
    def get_consumer_metrics(self) -> Dict[str, Any]:
        """Get consumer performance metrics."""
        if not self.consumer:
            return {"error": "Consumer not initialized"}
        
        metrics = self.consumer.metrics()
        return {
            "consumer_metrics": metrics,
            "group_id": self.config.group_id,
            "bootstrap_servers": self.config.bootstrap_servers
        }
    
    def commit_offsets(self):
        """Manually commit offsets."""
        try:
            self.consumer.commit()
            logger.debug("Offsets committed successfully")
        except CommitFailedError as e:
            logger.error(f"Failed to commit offsets: {e}")
        except Exception as e:
            logger.error(f"Error committing offsets: {e}")
    
    def seek_to_beginning(self, topics: List[str] = None):
        """Seek to beginning of topic partitions."""
        try:
            if topics:
                partitions = []
                for topic in topics:
                    topic_partitions = self.consumer.partitions_for_topic(topic)
                    if topic_partitions:
                        for partition in topic_partitions:
                            from kafka import TopicPartition
                            partitions.append(TopicPartition(topic, partition))
                
                self.consumer.seek_to_beginning(*partitions)
            else:
                self.consumer.seek_to_beginning()
            
            logger.info(f"Seeked to beginning for topics: {topics or 'all'}")
        except Exception as e:
            logger.error(f"Error seeking to beginning: {e}")
    
    def seek_to_end(self, topics: List[str] = None):
        """Seek to end of topic partitions."""
        try:
            if topics:
                partitions = []
                for topic in topics:
                    topic_partitions = self.consumer.partitions_for_topic(topic)
                    if topic_partitions:
                        for partition in topic_partitions:
                            from kafka import TopicPartition
                            partitions.append(TopicPartition(topic, partition))
                
                self.consumer.seek_to_end(*partitions)
            else:
                self.consumer.seek_to_end()
            
            logger.info(f"Seeked to end for topics: {topics or 'all'}")
        except Exception as e:
            logger.error(f"Error seeking to end: {e}")


# Default event handlers for common business events
class DefaultEventHandlers:
    """Default event handlers for business events."""
    
    @staticmethod
    async def handle_user_events(event_message: EventMessage):
        """Handle user-related events."""
        logger.info(f"Processing user event: {event_message.value}")
        # Add user event processing logic here
    
    @staticmethod
    async def handle_product_events(event_message: EventMessage):
        """Handle product-related events."""
        logger.info(f"Processing product event: {event_message.value}")
        # Add product event processing logic here
    
    @staticmethod
    async def handle_order_events(event_message: EventMessage):
        """Handle order-related events."""
        logger.info(f"Processing order event: {event_message.value}")
        # Add order event processing logic here
    
    @staticmethod
    async def handle_sale_events(event_message: EventMessage):
        """Handle sale-related events."""
        logger.info(f"Processing sale event: {event_message.value}")
        # Add sale event processing logic here
    
    @staticmethod
    async def handle_payment_events(event_message: EventMessage):
        """Handle payment-related events."""
        logger.info(f"Processing payment event: {event_message.value}")
        # Add payment event processing logic here
