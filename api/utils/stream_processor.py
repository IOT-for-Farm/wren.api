"""
Stream Processor

Real-time stream processing for Kafka events with analytics,
aggregation, and business intelligence integration.
"""

import asyncio
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import logging
from enum import Enum

from .kafka_consumer import EventMessage
from .kafka_producer import EventType, KafkaEventProducer

logger = logging.getLogger(__name__)


class ProcessingWindow(Enum):
    """Processing window types."""
    TUMBLING = "tumbling"
    SLIDING = "sliding"
    SESSION = "session"


class AggregationType(Enum):
    """Aggregation types."""
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    DISTINCT = "distinct"


@dataclass
class StreamWindow:
    """Stream processing window configuration."""
    window_type: ProcessingWindow
    duration_seconds: int
    slide_seconds: Optional[int] = None
    max_events: Optional[int] = None


@dataclass
class AggregationConfig:
    """Aggregation configuration."""
    field: str
    aggregation_type: AggregationType
    group_by: Optional[List[str]] = None
    filter_conditions: Optional[Dict[str, Any]] = None


@dataclass
class StreamMetrics:
    """Stream processing metrics."""
    events_processed: int = 0
    events_aggregated: int = 0
    windows_processed: int = 0
    processing_errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_event_time: Optional[datetime] = None
    avg_processing_time_ms: float = 0.0


class StreamProcessor:
    """Real-time stream processor for Kafka events."""
    
    def __init__(self, kafka_producer: KafkaEventProducer = None):
        """Initialize stream processor."""
        self.kafka_producer = kafka_producer
        self.metrics = StreamMetrics()
        self.windows = {}  # Active processing windows
        self.aggregations = {}  # Aggregation configurations
        self.event_buffers = defaultdict(deque)  # Event buffers by window
        self.processing_tasks = set()  # Active processing tasks
        
        # Register default aggregations
        self._register_default_aggregations()
    
    def _register_default_aggregations(self):
        """Register default aggregation configurations."""
        # User activity aggregations
        self.aggregations["user_activity_hourly"] = {
            "window": StreamWindow(ProcessingWindow.TUMBLING, 3600),  # 1 hour
            "aggregations": [
                AggregationConfig("user_id", AggregationType.COUNT, ["organization_id"]),
                AggregationConfig("event_type", AggregationType.DISTINCT, ["organization_id"])
            ]
        }
        
        # Order analytics aggregations
        self.aggregations["order_analytics_daily"] = {
            "window": StreamWindow(ProcessingWindow.TUMBLING, 86400),  # 24 hours
            "aggregations": [
                AggregationConfig("total_amount", AggregationType.SUM, ["organization_id"]),
                AggregationConfig("total_amount", AggregationType.AVG, ["organization_id"]),
                AggregationConfig("order_id", AggregationType.COUNT, ["organization_id"])
            ]
        }
        
        # Product performance aggregations
        self.aggregations["product_performance_hourly"] = {
            "window": StreamWindow(ProcessingWindow.SLIDING, 3600, 300),  # 1 hour sliding, 5 min slide
            "aggregations": [
                AggregationConfig("product_id", AggregationType.COUNT, ["organization_id"]),
                AggregationConfig("sale_amount", AggregationType.SUM, ["product_id"])
            ]
        }
        
        # Payment analytics aggregations
        self.aggregations["payment_analytics_realtime"] = {
            "window": StreamWindow(ProcessingWindow.TUMBLING, 300),  # 5 minutes
            "aggregations": [
                AggregationConfig("amount", AggregationType.SUM, ["organization_id"]),
                AggregationConfig("amount", AggregationType.AVG, ["organization_id"]),
                AggregationConfig("payment_id", AggregationType.COUNT, ["organization_id"])
            ]
        }
    
    async def process_event(self, event_message: EventMessage):
        """Process incoming event for stream analytics."""
        try:
            self.metrics.events_processed += 1
            self.metrics.last_event_time = datetime.now()
            
            # Extract event data
            event_data = event_message.value.get('data', {})
            event_type = event_message.value.get('metadata', {}).get('event_type', 'unknown')
            organization_id = event_data.get('organization_id')
            
            # Process event for each active aggregation
            for agg_name, agg_config in self.aggregations.items():
                await self._process_event_for_aggregation(
                    agg_name, agg_config, event_message, event_data, event_type, organization_id
                )
            
            # Update processing time
            self._update_processing_metrics()
            
        except Exception as e:
            logger.error(f"Error processing event for stream analytics: {e}")
            self.metrics.processing_errors += 1
    
    async def _process_event_for_aggregation(self, agg_name: str, agg_config: Dict[str, Any],
                                           event_message: EventMessage, event_data: Dict[str, Any],
                                           event_type: str, organization_id: str):
        """Process event for specific aggregation."""
        window_config = agg_config["window"]
        aggregations = agg_config["aggregations"]
        
        # Check if event matches aggregation criteria
        if not self._event_matches_criteria(event_type, event_data, aggregations):
            return
        
        # Add event to window buffer
        window_key = f"{agg_name}_{organization_id or 'global'}"
        self.event_buffers[window_key].append({
            "event_message": event_message,
            "event_data": event_data,
            "event_type": event_type,
            "timestamp": datetime.now(),
            "organization_id": organization_id
        })
        
        # Check if window should be processed
        if self._should_process_window(window_key, window_config):
            await self._process_window(agg_name, window_key, aggregations)
    
    def _event_matches_criteria(self, event_type: str, event_data: Dict[str, Any],
                               aggregations: List[AggregationConfig]) -> bool:
        """Check if event matches aggregation criteria."""
        # Simple criteria matching - can be extended
        for agg in aggregations:
            if agg.field in event_data:
                return True
        return False
    
    def _should_process_window(self, window_key: str, window_config: StreamWindow) -> bool:
        """Check if window should be processed."""
        buffer = self.event_buffers[window_key]
        
        if not buffer:
            return False
        
        # Check time-based criteria
        if window_config.window_type == ProcessingWindow.TUMBLING:
            first_event_time = buffer[0]["timestamp"]
            return (datetime.now() - first_event_time).total_seconds() >= window_config.duration_seconds
        
        elif window_config.window_type == ProcessingWindow.SLIDING:
            # Process every slide_seconds
            if window_config.slide_seconds:
                last_processed = getattr(self, f"_last_processed_{window_key}", datetime.min)
                return (datetime.now() - last_processed).total_seconds() >= window_config.slide_seconds
        
        elif window_config.window_type == ProcessingWindow.SESSION:
            # Process when session ends (no events for session_timeout)
            if buffer:
                last_event_time = buffer[-1]["timestamp"]
                return (datetime.now() - last_event_time).total_seconds() >= window_config.duration_seconds
        
        # Check event count criteria
        if window_config.max_events and len(buffer) >= window_config.max_events:
            return True
        
        return False
    
    async def _process_window(self, agg_name: str, window_key: str, aggregations: List[AggregationConfig]):
        """Process window and generate aggregations."""
        try:
            buffer = self.event_buffers[window_key]
            if not buffer:
                return
            
            # Extract events from buffer
            events = list(buffer)
            buffer.clear()
            
            # Generate aggregations
            aggregation_results = {}
            for agg_config in aggregations:
                result = await self._generate_aggregation(events, agg_config)
                aggregation_results[agg_config.field] = result
            
            # Create aggregation event
            await self._publish_aggregation_event(agg_name, window_key, aggregation_results, events)
            
            # Update metrics
            self.metrics.windows_processed += 1
            self.metrics.events_aggregated += len(events)
            
            # Mark window as processed
            setattr(self, f"_last_processed_{window_key}", datetime.now())
            
            logger.info(f"Processed window {agg_name}: {len(events)} events, {len(aggregation_results)} aggregations")
            
        except Exception as e:
            logger.error(f"Error processing window {agg_name}: {e}")
            self.metrics.processing_errors += 1
    
    async def _generate_aggregation(self, events: List[Dict[str, Any]], 
                                  agg_config: AggregationConfig) -> Dict[str, Any]:
        """Generate aggregation result."""
        field = agg_config.field
        agg_type = agg_config.aggregation_type
        group_by = agg_config.group_by or []
        
        # Filter events if needed
        filtered_events = events
        if agg_config.filter_conditions:
            filtered_events = self._filter_events(events, agg_config.filter_conditions)
        
        if not filtered_events:
            return {"value": 0, "count": 0, "groups": {}}
        
        # Extract values for aggregation
        values = []
        for event in filtered_events:
            value = event["event_data"].get(field)
            if value is not None:
                values.append(value)
        
        if not values:
            return {"value": 0, "count": 0, "groups": {}}
        
        # Generate aggregation result
        result = {"count": len(values)}
        
        if agg_type == AggregationType.COUNT:
            result["value"] = len(values)
        elif agg_type == AggregationType.SUM:
            result["value"] = sum(values)
        elif agg_type == AggregationType.AVG:
            result["value"] = sum(values) / len(values)
        elif agg_type == AggregationType.MIN:
            result["value"] = min(values)
        elif agg_type == AggregationType.MAX:
            result["value"] = max(values)
        elif agg_type == AggregationType.DISTINCT:
            result["value"] = len(set(values))
        
        # Group by analysis
        if group_by:
            groups = defaultdict(list)
            for event in filtered_events:
                group_key = tuple(event["event_data"].get(gb, "unknown") for gb in group_by)
                groups[group_key].append(event["event_data"].get(field))
            
            result["groups"] = {}
            for group_key, group_values in groups.items():
                group_result = {"count": len(group_values)}
                if group_values:
                    if agg_type == AggregationType.SUM:
                        group_result["value"] = sum(group_values)
                    elif agg_type == AggregationType.AVG:
                        group_result["value"] = sum(group_values) / len(group_values)
                    elif agg_type == AggregationType.COUNT:
                        group_result["value"] = len(group_values)
                    elif agg_type == AggregationType.MIN:
                        group_result["value"] = min(group_values)
                    elif agg_type == AggregationType.MAX:
                        group_result["value"] = max(group_values)
                    elif agg_type == AggregationType.DISTINCT:
                        group_result["value"] = len(set(group_values))
                
                result["groups"][str(group_key)] = group_result
        
        return result
    
    def _filter_events(self, events: List[Dict[str, Any]], 
                      filter_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter events based on conditions."""
        filtered = []
        for event in events:
            event_data = event["event_data"]
            matches = True
            
            for field, expected_value in filter_conditions.items():
                if event_data.get(field) != expected_value:
                    matches = False
                    break
            
            if matches:
                filtered.append(event)
        
        return filtered
    
    async def _publish_aggregation_event(self, agg_name: str, window_key: str,
                                      aggregation_results: Dict[str, Any],
                                      events: List[Dict[str, Any]]):
        """Publish aggregation results as event."""
        if not self.kafka_producer:
            logger.warning("No Kafka producer available for publishing aggregation results")
            return
        
        # Create aggregation event data
        event_data = {
            "aggregation_name": agg_name,
            "window_key": window_key,
            "results": aggregation_results,
            "event_count": len(events),
            "processed_at": datetime.now().isoformat(),
            "window_start": events[0]["timestamp"].isoformat() if events else None,
            "window_end": events[-1]["timestamp"].isoformat() if events else None
        }
        
        # Extract organization_id from events
        organization_id = None
        if events:
            organization_id = events[0].get("organization_id")
        
        # Publish aggregation event
        await self.kafka_producer.publish_event(
            event_type=EventType.USER_CREATED,  # Use appropriate event type
            data=event_data,
            topic="analytics_aggregations",
            organization_id=organization_id
        )
        
        logger.info(f"Published aggregation event for {agg_name}: {len(aggregation_results)} results")
    
    def _update_processing_metrics(self):
        """Update processing time metrics."""
        # Simple moving average calculation
        current_time = datetime.now()
        if hasattr(self, '_last_processing_time'):
            processing_time = (current_time - self._last_processing_time).total_seconds() * 1000
            # Update moving average
            alpha = 0.1  # Smoothing factor
            self.metrics.avg_processing_time_ms = (
                alpha * processing_time + 
                (1 - alpha) * self.metrics.avg_processing_time_ms
            )
        
        self._last_processing_time = current_time
    
    def register_aggregation(self, name: str, window_config: StreamWindow,
                           aggregations: List[AggregationConfig]):
        """Register custom aggregation configuration."""
        self.aggregations[name] = {
            "window": window_config,
            "aggregations": aggregations
        }
        logger.info(f"Registered custom aggregation: {name}")
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get stream processing metrics."""
        uptime = (datetime.now() - self.metrics.start_time).total_seconds()
        return {
            "events_processed": self.metrics.events_processed,
            "events_aggregated": self.metrics.events_aggregated,
            "windows_processed": self.metrics.windows_processed,
            "processing_errors": self.metrics.processing_errors,
            "uptime_seconds": uptime,
            "events_per_second": self.metrics.events_processed / uptime if uptime > 0 else 0,
            "avg_processing_time_ms": self.metrics.avg_processing_time_ms,
            "last_event_time": self.metrics.last_event_time.isoformat() if self.metrics.last_event_time else None,
            "active_windows": len(self.windows),
            "active_buffers": len(self.event_buffers)
        }
    
    def get_aggregation_results(self, agg_name: str) -> Dict[str, Any]:
        """Get recent aggregation results."""
        # This would typically query a results store
        # For now, return basic info
        return {
            "aggregation_name": agg_name,
            "status": "active" if agg_name in self.aggregations else "inactive",
            "last_processed": getattr(self, f"_last_processed_{agg_name}", None)
        }
    
    async def process_historical_events(self, events: List[EventMessage], 
                                      agg_name: str) -> Dict[str, Any]:
        """Process historical events for aggregation."""
        if agg_name not in self.aggregations:
            raise ValueError(f"Aggregation {agg_name} not found")
        
        agg_config = self.aggregations[agg_name]
        aggregations = agg_config["aggregations"]
        
        # Convert to internal format
        internal_events = []
        for event_msg in events:
            event_data = event_msg.value.get('data', {})
            event_type = event_msg.value.get('metadata', {}).get('event_type', 'unknown')
            organization_id = event_data.get('organization_id')
            
            internal_events.append({
                "event_message": event_msg,
                "event_data": event_data,
                "event_type": event_type,
                "timestamp": datetime.now(),
                "organization_id": organization_id
            })
        
        # Generate aggregations
        aggregation_results = {}
        for agg_config_item in aggregations:
            result = await self._generate_aggregation(internal_events, agg_config_item)
            aggregation_results[agg_config_item.field] = result
        
        return {
            "aggregation_name": agg_name,
            "event_count": len(internal_events),
            "results": aggregation_results,
            "processed_at": datetime.now().isoformat()
        }
    
    def cleanup_expired_windows(self, max_age_seconds: int = 3600):
        """Cleanup expired windows and buffers."""
        current_time = datetime.now()
        expired_windows = []
        
        for window_key, buffer in self.event_buffers.items():
            if buffer:
                oldest_event = buffer[0]["timestamp"]
                if (current_time - oldest_event).total_seconds() > max_age_seconds:
                    expired_windows.append(window_key)
        
        for window_key in expired_windows:
            del self.event_buffers[window_key]
            logger.info(f"Cleaned up expired window: {window_key}")
        
        return len(expired_windows)
