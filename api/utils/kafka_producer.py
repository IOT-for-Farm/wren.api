"""
Kafka Event Producer

High-performance Kafka producer for publishing business events
integrated with existing API models and services.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for business operations."""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_COMPLETED = "order.completed"
    ORDER_CANCELLED = "order.cancelled"
    SALE_CREATED = "sale.created"
    SALE_UPDATED = "sale.updated"
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    PAYMENT_CREATED = "payment.created"
    PAYMENT_PROCESSED = "payment.processed"
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    VENDOR_CREATED = "vendor.created"
    VENDOR_UPDATED = "vendor.updated"
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"


@dataclass
class EventMetadata:
    """Metadata for event publishing."""
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    version: str = "1.0"
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None


@dataclass
class BusinessEvent:
    """Business event structure."""
    metadata: EventMetadata
    data: Dict[str, Any]
    schema_version: str = "1.0"


class KafkaEventProducer:
    """High-performance Kafka producer for business events."""
    
    def __init__(self, bootstrap_servers: List[str] = None, 
                 client_id: str = "wren-api-producer",
                 max_block_ms: int = 10000,
                 retries: int = 3,
                 batch_size: int = 16384,
                 linger_ms: int = 10,
                 compression_type: str = "gzip"):
        """Initialize Kafka producer with optimized settings."""
        self.bootstrap_servers = bootstrap_servers or ["localhost:9092"]
        self.client_id = client_id
        self.producer = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
        
        # Producer configuration
        self.config = {
            'bootstrap_servers': self.bootstrap_servers,
            'client_id': self.client_id,
            'max_block_ms': max_block_ms,
            'retries': retries,
            'batch_size': batch_size,
            'linger_ms': linger_ms,
            'compression_type': compression_type,
            'key_serializer': self._serialize_key,
            'value_serializer': self._serialize_value,
            'acks': 'all',  # Wait for all replicas
            'enable_idempotence': True,  # Prevent duplicate messages
        }
        
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer."""
        try:
            self.producer = KafkaProducer(**self.config)
            logger.info(f"Kafka producer initialized with servers: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def _serialize_key(self, key: str) -> bytes:
        """Serialize message key."""
        return key.encode('utf-8') if key else None
    
    def _serialize_value(self, value: Dict[str, Any]) -> bytes:
        """Serialize message value to JSON."""
        return json.dumps(value, default=str).encode('utf-8')
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        return f"evt_{int(datetime.now().timestamp() * 1000)}_{id(self)}"
    
    def _create_event_metadata(self, event_type: EventType, 
                             correlation_id: str = None,
                             user_id: str = None,
                             organization_id: str = None) -> EventMetadata:
        """Create event metadata."""
        return EventMetadata(
            event_id=self._generate_event_id(),
            event_type=event_type,
            timestamp=datetime.now(),
            source="wren-api",
            correlation_id=correlation_id,
            user_id=user_id,
            organization_id=organization_id
        )
    
    async def publish_event(self, event_type: EventType, data: Dict[str, Any],
                          topic: str = None, key: str = None,
                          correlation_id: str = None,
                          user_id: str = None,
                          organization_id: str = None) -> bool:
        """Publish business event to Kafka."""
        try:
            # Create event metadata
            metadata = self._create_event_metadata(
                event_type, correlation_id, user_id, organization_id
            )
            
            # Create business event
            event = BusinessEvent(
                metadata=metadata,
                data=data
            )
            
            # Determine topic
            if not topic:
                topic = self._get_topic_for_event_type(event_type)
            
            # Determine partition key
            if not key:
                key = self._get_partition_key(event_type, data)
            
            # Serialize event
            event_dict = asdict(event)
            event_dict['metadata']['timestamp'] = event.metadata.timestamp.isoformat()
            event_dict['metadata']['event_type'] = event.metadata.event_type.value
            
            # Publish to Kafka
            future = self.producer.send(
                topic=topic,
                key=key,
                value=event_dict,
                partition=None  # Let Kafka decide partition
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Event published: {event_type.value} to {topic} "
                       f"[partition: {record_metadata.partition}, "
                       f"offset: {record_metadata.offset}]")
            
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing event {event_type.value}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing event {event_type.value}: {e}")
            return False
    
    def _get_topic_for_event_type(self, event_type: EventType) -> str:
        """Get appropriate topic for event type."""
        topic_mapping = {
            EventType.USER_CREATED: "users",
            EventType.USER_UPDATED: "users",
            EventType.USER_DELETED: "users",
            EventType.PRODUCT_CREATED: "products",
            EventType.PRODUCT_UPDATED: "products",
            EventType.PRODUCT_DELETED: "products",
            EventType.ORDER_CREATED: "orders",
            EventType.ORDER_UPDATED: "orders",
            EventType.ORDER_COMPLETED: "orders",
            EventType.ORDER_CANCELLED: "orders",
            EventType.SALE_CREATED: "sales",
            EventType.SALE_UPDATED: "sales",
            EventType.INVOICE_CREATED: "invoices",
            EventType.INVOICE_PAID: "invoices",
            EventType.PAYMENT_CREATED: "payments",
            EventType.PAYMENT_PROCESSED: "payments",
            EventType.CUSTOMER_CREATED: "customers",
            EventType.CUSTOMER_UPDATED: "customers",
            EventType.VENDOR_CREATED: "vendors",
            EventType.VENDOR_UPDATED: "vendors",
            EventType.ORGANIZATION_CREATED: "organizations",
            EventType.ORGANIZATION_UPDATED: "organizations",
        }
        return topic_mapping.get(event_type, "general")
    
    def _get_partition_key(self, event_type: EventType, data: Dict[str, Any]) -> str:
        """Get partition key for event."""
        # Use organization_id or user_id for partitioning
        if 'organization_id' in data:
            return str(data['organization_id'])
        elif 'user_id' in data:
            return str(data['user_id'])
        elif 'id' in data:
            return str(data['id'])
        else:
            return "default"
    
    async def publish_user_event(self, event_type: EventType, user_data: Dict[str, Any],
                               correlation_id: str = None) -> bool:
        """Publish user-related event."""
        return await self.publish_event(
            event_type=event_type,
            data=user_data,
            correlation_id=correlation_id,
            user_id=user_data.get('id'),
            organization_id=user_data.get('organization_id')
        )
    
    async def publish_product_event(self, event_type: EventType, product_data: Dict[str, Any],
                                  correlation_id: str = None) -> bool:
        """Publish product-related event."""
        return await self.publish_event(
            event_type=event_type,
            data=product_data,
            correlation_id=correlation_id,
            organization_id=product_data.get('organization_id')
        )
    
    async def publish_order_event(self, event_type: EventType, order_data: Dict[str, Any],
                                correlation_id: str = None) -> bool:
        """Publish order-related event."""
        return await self.publish_event(
            event_type=event_type,
            data=order_data,
            correlation_id=correlation_id,
            user_id=order_data.get('user_id'),
            organization_id=order_data.get('organization_id')
        )
    
    async def publish_sale_event(self, event_type: EventType, sale_data: Dict[str, Any],
                               correlation_id: str = None) -> bool:
        """Publish sale-related event."""
        return await self.publish_event(
            event_type=event_type,
            data=sale_data,
            correlation_id=correlation_id,
            user_id=sale_data.get('user_id'),
            organization_id=sale_data.get('organization_id')
        )
    
    async def publish_invoice_event(self, event_type: EventType, invoice_data: Dict[str, Any],
                                  correlation_id: str = None) -> bool:
        """Publish invoice-related event."""
        return await self.publish_event(
            event_type=event_type,
            data=invoice_data,
            correlation_id=correlation_id,
            user_id=invoice_data.get('user_id'),
            organization_id=invoice_data.get('organization_id')
        )
    
    async def publish_payment_event(self, event_type: EventType, payment_data: Dict[str, Any],
                                  correlation_id: str = None) -> bool:
        """Publish payment-related event."""
        return await self.publish_event(
            event_type=event_type,
            data=payment_data,
            correlation_id=correlation_id,
            user_id=payment_data.get('user_id'),
            organization_id=payment_data.get('organization_id')
        )
    
    async def publish_batch_events(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Publish multiple events in batch."""
        results = {"success": 0, "failed": 0}
        
        for event_data in events:
            try:
                success = await self.publish_event(**event_data)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Batch event failed: {e}")
                results["failed"] += 1
        
        logger.info(f"Batch publish completed: {results}")
        return results
    
    def get_producer_metrics(self) -> Dict[str, Any]:
        """Get producer performance metrics."""
        if not self.producer:
            return {"error": "Producer not initialized"}
        
        metrics = self.producer.metrics()
        return {
            "producer_metrics": metrics,
            "bootstrap_servers": self.bootstrap_servers,
            "client_id": self.client_id
        }
    
    def close(self):
        """Close producer and cleanup resources."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")
        
        if self.executor:
            self.executor.shutdown(wait=True)
