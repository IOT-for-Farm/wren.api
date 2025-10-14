"""
Error Handling and Recovery for Wren API

This module provides comprehensive error handling, recovery mechanisms,
and error management utilities.
"""

import time
import traceback
from typing import Any, Dict, List, Optional, Union, Callable, Type
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """Error information structure"""
    error_id: str
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime
    context: Dict[str, Any] = None
    stack_trace: str = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class ErrorRecoveryManager:
    """Error recovery and handling system"""
    
    def __init__(self):
        self.error_handlers = {}
        self.recovery_strategies = {}
        self.error_history = []
        self.circuit_breakers = {}
        self.retry_configs = {}
    
    def register_error_handler(self, error_type: Type[Exception], handler: Callable):
        """Register error handler for specific exception type"""
        self.error_handlers[error_type] = handler
        logger.info(f"Error handler registered for {error_type.__name__}")
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register recovery strategy for error type"""
        self.recovery_strategies[error_type] = strategy
        logger.info(f"Recovery strategy registered for {error_type}")
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle error with recovery attempt"""
        error_info = self._create_error_info(error, context)
        
        # Log error
        logger.error(f"Error occurred: {error_info.message}", extra={
            "error_id": error_info.error_id,
            "error_type": error_info.error_type,
            "severity": error_info.severity.value,
            "context": error_info.context
        })
        
        # Attempt recovery
        recovery_successful = self._attempt_recovery(error_info)
        error_info.recovery_successful = recovery_successful
        
        # Store error history
        self.error_history.append(error_info)
        
        return error_info
    
    def _create_error_info(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Create error information"""
        error_id = f"ERR_{int(time.time() * 1000)}"
        
        return ErrorInfo(
            error_id=error_id,
            error_type=type(error).__name__,
            message=str(error),
            severity=self._determine_severity(error),
            timestamp=datetime.utcnow(),
            context=context or {},
            stack_trace=traceback.format_exc()
        )
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity"""
        error_type = type(error).__name__
        
        if error_type in ["SystemExit", "KeyboardInterrupt"]:
            return ErrorSeverity.CRITICAL
        elif error_type in ["ConnectionError", "TimeoutError"]:
            return ErrorSeverity.HIGH
        elif error_type in ["ValueError", "TypeError"]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt error recovery"""
        error_info.recovery_attempted = True
        
        if error_info.error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_info.error_type]
                result = strategy(error_info)
                logger.info(f"Recovery attempted for {error_info.error_id}: {result}")
                return result
            except Exception as e:
                logger.error(f"Recovery failed for {error_info.error_id}: {e}")
                return False
        
        return False
    
    def get_error_history(self, hours: int = 24) -> List[ErrorInfo]:
        """Get error history for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [error for error in self.error_history if error.timestamp >= cutoff_time]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_history:
            return {"total_errors": 0}
        
        error_types = {}
        severity_counts = {}
        recovery_stats = {"attempted": 0, "successful": 0}
        
        for error in self.error_history:
            # Count error types
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            # Count severity levels
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            # Count recovery attempts
            if error.recovery_attempted:
                recovery_stats["attempted"] += 1
                if error.recovery_successful:
                    recovery_stats["successful"] += 1
        
        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "severity_counts": severity_counts,
            "recovery_stats": recovery_stats,
            "recovery_rate": recovery_stats["successful"] / recovery_stats["attempted"] if recovery_stats["attempted"] > 0 else 0
        }


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


class RetryManager:
    """Retry mechanism with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Retry attempt {attempt + 1} after {delay}s delay")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {func.__name__}")
        
        raise last_exception
    
    def retry_with_callback(self, func: Callable, callback: Callable, *args, **kwargs) -> Any:
        """Execute function with retry and callback"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if callback(result):
                    return result
                else:
                    raise Exception("Callback validation failed")
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Retry attempt {attempt + 1} after {delay}s delay")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {func.__name__}")
        
        raise last_exception


class ErrorNotificationManager:
    """Error notification and alerting system"""
    
    def __init__(self):
        self.notification_handlers = {}
        self.alert_thresholds = {}
        self.notification_history = []
    
    def register_notification_handler(self, name: str, handler: Callable):
        """Register notification handler"""
        self.notification_handlers[name] = handler
        logger.info(f"Notification handler registered: {name}")
    
    def set_alert_threshold(self, error_type: str, threshold: int):
        """Set alert threshold for error type"""
        self.alert_thresholds[error_type] = threshold
        logger.info(f"Alert threshold set for {error_type}: {threshold}")
    
    def check_and_notify(self, error_info: ErrorInfo):
        """Check if notification should be sent and send if needed"""
        if self._should_notify(error_info):
            self._send_notification(error_info)
    
    def _should_notify(self, error_info: ErrorInfo) -> bool:
        """Check if notification should be sent"""
        # Check severity
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            return True
        
        # Check threshold
        if error_info.error_type in self.alert_thresholds:
            threshold = self.alert_thresholds[error_info.error_type]
            recent_errors = [e for e in self.notification_history 
                           if e.error_type == error_info.error_type 
                           and e.timestamp >= datetime.utcnow() - timedelta(hours=1)]
            
            if len(recent_errors) >= threshold:
                return True
        
        return False
    
    def _send_notification(self, error_info: ErrorInfo):
        """Send error notification"""
        notification = {
            "error_id": error_info.error_id,
            "error_type": error_info.error_type,
            "severity": error_info.severity.value,
            "message": error_info.message,
            "timestamp": error_info.timestamp,
            "context": error_info.context
        }
        
        # Send to all registered handlers
        for name, handler in self.notification_handlers.items():
            try:
                handler(notification)
                logger.info(f"Notification sent via {name}")
            except Exception as e:
                logger.error(f"Failed to send notification via {name}: {e}")
        
        self.notification_history.append(error_info)


# Global error handling instances
def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get error recovery manager instance"""
    return ErrorRecoveryManager()

def get_circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60) -> CircuitBreaker:
    """Get circuit breaker instance"""
    return CircuitBreaker(failure_threshold, recovery_timeout)

def get_retry_manager(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0) -> RetryManager:
    """Get retry manager instance"""
    return RetryManager(max_retries, base_delay, max_delay)

def get_error_notification_manager() -> ErrorNotificationManager:
    """Get error notification manager instance"""
    return ErrorNotificationManager()
