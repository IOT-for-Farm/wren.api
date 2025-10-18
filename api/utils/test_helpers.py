"""
Testing Infrastructure Utilities

Helper functions and utilities for testing.
"""

import json
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestHelpers:
    """Collection of testing helper functions."""
    
    def __init__(self, app: FastAPI):
        """Initialize test helpers with FastAPI app."""
        self.app = app
        self.client = TestClient(app)
    
    def make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and return response data."""
        response = getattr(self.client, method.lower())(url, **kwargs)
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else None,
            "headers": dict(response.headers)
        }
    
    def assert_response_status(self, response: Dict[str, Any], expected_status: int) -> bool:
        """Assert response has expected status code."""
        return response["status_code"] == expected_status
    
    def assert_response_contains(self, response: Dict[str, Any], key: str, value: Any = None) -> bool:
        """Assert response data contains key (and optionally value)."""
        if not response["data"]:
            return False
        
        if key not in response["data"]:
            return False
        
        if value is not None:
            return response["data"][key] == value
        
        return True
    
    def create_test_data(self, data_type: str, **kwargs) -> Dict[str, Any]:
        """Create test data for different types."""
        test_data = {
            "user": {
                "name": kwargs.get("name", "Test User"),
                "email": kwargs.get("email", "test@example.com"),
                "age": kwargs.get("age", 25)
            },
            "product": {
                "name": kwargs.get("name", "Test Product"),
                "price": kwargs.get("price", 99.99),
                "category": kwargs.get("category", "electronics")
            }
        }
        
        return test_data.get(data_type, {})
    
    def validate_json_response(self, response: Dict[str, Any]) -> bool:
        """Validate response is valid JSON."""
        try:
            if response["data"]:
                json.dumps(response["data"])
            return True
        except (TypeError, ValueError):
            return False
