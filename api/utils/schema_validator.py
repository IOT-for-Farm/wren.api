"""
Schema Validation Utilities

JSON schema validation and data structure validation.
"""

from typing import Any, Dict, List, Optional
import json


class SchemaValidator:
    """Validates data against JSON schemas."""
    
    def __init__(self):
        """Initialize schema validator."""
        self.schemas = {}
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a JSON schema."""
        self.schemas[name] = schema
    
    def validate_against_schema(self, data: Any, schema_name: str) -> Dict[str, Any]:
        """Validate data against registered schema."""
        if schema_name not in self.schemas:
            return {"valid": False, "error": f"Schema '{schema_name}' not found"}
        
        schema = self.schemas[schema_name]
        errors = self._validate_object(data, schema)
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _validate_object(self, data: Any, schema: Dict[str, Any]) -> List[str]:
        """Validate object against schema."""
        errors = []
        
        if "type" in schema:
            if not self._validate_type(data, schema["type"]):
                errors.append(f"Expected {schema['type']}, got {type(data).__name__}")
        
        if "required" in schema and isinstance(data, dict):
            for field in schema["required"]:
                if field not in data:
                    errors.append(f"Required field '{field}' is missing")
        
        if "properties" in schema and isinstance(data, dict):
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    prop_errors = self._validate_object(data[prop], prop_schema)
                    errors.extend([f"{prop}.{error}" for error in prop_errors])
        
        return errors
    
    def _validate_type(self, data: Any, expected_type: str) -> bool:
        """Validate data type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        
        return isinstance(data, expected)
