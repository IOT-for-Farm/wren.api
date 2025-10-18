"""
Mock Services Utilities

Mock services for testing external dependencies.
"""

from typing import Dict, Any, Optional, Callable
import json
from datetime import datetime


class MockService:
    """Base class for mock services."""
    
    def __init__(self, name: str):
        """Initialize mock service."""
        self.name = name
        self.calls = []
        self.responses = {}
    
    def record_call(self, method: str, data: Dict[str, Any] = None) -> None:
        """Record a service call."""
        call = {
            "method": method,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.calls.append(call)
    
    def set_response(self, method: str, response: Any) -> None:
        """Set mock response for method."""
        self.responses[method] = response
    
    def get_response(self, method: str) -> Any:
        """Get mock response for method."""
        return self.responses.get(method, {"status": "success"})
    
    def get_call_count(self, method: str = None) -> int:
        """Get number of calls made."""
        if method:
            return len([call for call in self.calls if call["method"] == method])
        return len(self.calls)
    
    def reset(self) -> None:
        """Reset mock service state."""
        self.calls.clear()
        self.responses.clear()


class MockEmailService(MockService):
    """Mock email service for testing."""
    
    def __init__(self):
        super().__init__("email")
        self.sent_emails = []
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Mock email sending."""
        self.record_call("send_email", {"to": to, "subject": subject})
        
        email = {
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now().isoformat()
        }
        self.sent_emails.append(email)
        
        return self.get_response("send_email")
    
    def get_sent_emails(self) -> list:
        """Get list of sent emails."""
        return self.sent_emails.copy()


class MockDatabaseService(MockService):
    """Mock database service for testing."""
    
    def __init__(self):
        super().__init__("database")
        self.data = {}
    
    def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock database create operation."""
        self.record_call("create", {"table": table, "data": data})
        
        record_id = f"{table}_{len(self.data.get(table, [])) + 1}"
        record = {"id": record_id, **data}
        
        if table not in self.data:
            self.data[table] = []
        self.data[table].append(record)
        
        return self.get_response("create")
    
    def get_all(self, table: str) -> list:
        """Mock database get all operation."""
        self.record_call("get_all", {"table": table})
        return self.data.get(table, [])
