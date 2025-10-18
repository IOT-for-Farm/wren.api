"""
Webhook Validation Utilities

Validate webhook signatures and payloads.
"""

import hmac
import hashlib
from typing import Dict, Any, Optional
import json


class WebhookValidator:
    """Validates webhook signatures and payloads."""
    
    def __init__(self):
        """Initialize webhook validator."""
        self.supported_algorithms = ["sha256", "sha1"]
    
    def validate_signature(self, payload: str, signature: str, secret: str, 
                          algorithm: str = "sha256") -> bool:
        """Validate webhook signature."""
        if algorithm not in self.supported_algorithms:
            return False
        
        expected_signature = self._generate_signature(payload, secret, algorithm)
        return hmac.compare_digest(signature, expected_signature)
    
    def _generate_signature(self, payload: str, secret: str, algorithm: str) -> str:
        """Generate signature for payload."""
        hash_func = hashlib.sha256 if algorithm == "sha256" else hashlib.sha1
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hash_func
        ).hexdigest()
        return f"{algorithm}={signature}"
    
    def validate_payload_structure(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate webhook payload structure."""
        errors = []
        
        required_fields = ["event", "data", "timestamp"]
        for field in required_fields:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
        
        if "event" in payload and not isinstance(payload["event"], str):
            errors.append("Event must be a string")
        
        if "data" in payload and not isinstance(payload["data"], dict):
            errors.append("Data must be a dictionary")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def extract_event_type(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract event type from payload."""
        return payload.get("event")
    
    def extract_data(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract data from payload."""
        return payload.get("data")
    
    def is_valid_webhook_request(self, headers: Dict[str, str], 
                                payload: str, secret: str) -> bool:
        """Check if request is a valid webhook."""
        signature_header = headers.get("X-Webhook-Signature")
        if not signature_header:
            return False
        
        return self.validate_signature(payload, signature_header, secret)
