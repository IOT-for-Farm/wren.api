"""
Security Utilities

Security helpers for authentication and authorization.
"""

import hashlib
import secrets
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class SecurityUtils:
    """Security utility functions for authentication and data protection."""
    
    def __init__(self):
        """Initialize security utilities."""
        self.password_pattern = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        )
    
    def hash_password(self, password: str, salt: str = None) -> Dict[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        salted_password = password + salt
        hashed = hashlib.sha256(salted_password.encode()).hexdigest()
        
        return {
            "hash": hashed,
            "salt": salt
        }
    
    def verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """Verify password against hash."""
        salted_password = password + salt
        computed_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        return computed_hash == hash_value
    
    def generate_token(self, length: int = 32) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(length)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        if not password:
            return {"valid": False, "errors": ["Password is required"]}
        
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain number")
        
        if not re.search(r'[@$!%*?&]', password):
            errors.append("Password must contain special character")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def sanitize_input(self, input_string: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not isinstance(input_string, str):
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';]', '', input_string)
        return sanitized.strip()
    
    def check_permissions(self, user_roles: list, required_roles: list) -> bool:
        """Check if user has required permissions."""
        return any(role in user_roles for role in required_roles)
