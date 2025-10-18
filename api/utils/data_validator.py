"""
Data Validation Utilities

Simple data validation and serialization utilities.
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class DataValidator:
    """Validates and sanitizes data inputs."""
    
    def __init__(self):
        """Initialize data validator."""
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        return bool(self.email_pattern.match(email)) if email else False
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        return bool(self.phone_pattern.match(phone)) if phone else False
    
    def validate_required(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate required fields are present."""
        missing = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing.append(field)
        return missing
    
    def sanitize_string(self, value: str, max_length: int = 255) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return ""
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\']', '', value)
        return sanitized[:max_length].strip()
    
    def validate_length(self, value: str, min_len: int = 0, max_len: int = 255) -> bool:
        """Validate string length."""
        if not isinstance(value, str):
            return False
        return min_len <= len(value) <= max_len
    
    def validate_numeric_range(self, value: Union[int, float], 
                              min_val: Union[int, float] = None, 
                              max_val: Union[int, float] = None) -> bool:
        """Validate numeric value is within range."""
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True
