"""
Data Validation and Serialization for Wren API

This module provides comprehensive data validation, serialization,
and data transformation utilities.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union, Type, Callable
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ValidationError, validator
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class DataValidator:
    """Data validation utilities"""
    
    def __init__(self):
        self.validation_rules = {}
        self.custom_validators = {}
    
    def add_validation_rule(self, field_name: str, rule: Dict[str, Any]):
        """Add validation rule for a field"""
        self.validation_rules[field_name] = rule
        logger.info(f"Validation rule added for {field_name}")
    
    def validate_field(self, field_name: str, value: Any) -> Dict[str, Any]:
        """Validate a single field"""
        result = {
            "is_valid": True,
            "errors": [],
            "value": value
        }
        
        if field_name not in self.validation_rules:
            return result
        
        rule = self.validation_rules[field_name]
        
        # Check required
        if rule.get("required", False) and (value is None or value == ""):
            result["is_valid"] = False
            result["errors"].append(f"{field_name} is required")
            return result
        
        # Check type
        if "type" in rule:
            if not self._validate_type(value, rule["type"]):
                result["is_valid"] = False
                result["errors"].append(f"{field_name} must be of type {rule['type']}")
        
        # Check min/max length
        if "min_length" in rule and len(str(value)) < rule["min_length"]:
            result["is_valid"] = False
            result["errors"].append(f"{field_name} must be at least {rule['min_length']} characters")
        
        if "max_length" in rule and len(str(value)) > rule["max_length"]:
            result["is_valid"] = False
            result["errors"].append(f"{field_name} must be at most {rule['max_length']} characters")
        
        # Check min/max value
        if "min_value" in rule and isinstance(value, (int, float)) and value < rule["min_value"]:
            result["is_valid"] = False
            result["errors"].append(f"{field_name} must be at least {rule['min_value']}")
        
        if "max_value" in rule and isinstance(value, (int, float)) and value > rule["max_value"]:
            result["is_valid"] = False
            result["errors"].append(f"{field_name} must be at most {rule['max_value']}")
        
        # Check pattern
        if "pattern" in rule and not re.match(rule["pattern"], str(value)):
            result["is_valid"] = False
            result["errors"].append(f"{field_name} format is invalid")
        
        # Check custom validator
        if "custom_validator" in rule:
            custom_validator = self.custom_validators.get(rule["custom_validator"])
            if custom_validator:
                try:
                    if not custom_validator(value):
                        result["is_valid"] = False
                        result["errors"].append(f"{field_name} validation failed")
                except Exception as e:
                    result["is_valid"] = False
                    result["errors"].append(f"{field_name} validation error: {str(e)}")
        
        return result
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "date": date,
            "datetime": datetime,
            "time": time,
            "decimal": Decimal,
            "list": list,
            "dict": dict
        }
        
        if expected_type in type_mapping:
            return isinstance(value, type_mapping[expected_type])
        
        return True
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate entire data object"""
        result = {
            "is_valid": True,
            "errors": [],
            "field_errors": {}
        }
        
        for field_name, value in data.items():
            field_result = self.validate_field(field_name, value)
            
            if not field_result["is_valid"]:
                result["is_valid"] = False
                result["field_errors"][field_name] = field_result["errors"]
                result["errors"].extend(field_result["errors"])
        
        return result
    
    def register_custom_validator(self, name: str, validator_func: Callable):
        """Register custom validator function"""
        self.custom_validators[name] = validator_func
        logger.info(f"Custom validator registered: {name}")


class DataSerializer:
    """Data serialization utilities"""
    
    def __init__(self):
        self.serializers = {}
        self.deserializers = {}
    
    def register_serializer(self, data_type: Type, serializer_func: Callable):
        """Register serializer for data type"""
        self.serializers[data_type] = serializer_func
        logger.info(f"Serializer registered for {data_type}")
    
    def register_deserializer(self, data_type: Type, deserializer_func: Callable):
        """Register deserializer for data type"""
        self.deserializers[data_type] = deserializer_func
        logger.info(f"Deserializer registered for {data_type}")
    
    def serialize(self, data: Any) -> Any:
        """Serialize data"""
        if isinstance(data, dict):
            return {key: self.serialize(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.serialize(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, date):
            return data.isoformat()
        elif isinstance(data, time):
            return data.isoformat()
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, Enum):
            return data.value
        elif hasattr(data, '__dict__'):
            return self.serialize(data.__dict__)
        else:
            return data
    
    def deserialize(self, data: Any, target_type: Type = None) -> Any:
        """Deserialize data"""
        if target_type and target_type in self.deserializers:
            return self.deserializers[target_type](data)
        
        if isinstance(data, dict):
            return {key: self.deserialize(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.deserialize(item) for item in data]
        elif isinstance(data, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(data.replace('Z', '+00:00'))
            except ValueError:
                pass
            
            # Try to parse as date
            try:
                return datetime.strptime(data, '%Y-%m-%d').date()
            except ValueError:
                pass
            
            # Try to parse as time
            try:
                return datetime.strptime(data, '%H:%M:%S').time()
            except ValueError:
                pass
            
            return data
        else:
            return data
    
    def to_json(self, data: Any) -> str:
        """Convert data to JSON string"""
        try:
            serialized_data = self.serialize(data)
            return json.dumps(serialized_data, indent=2, default=str)
        except Exception as e:
            logger.error(f"JSON serialization failed: {e}")
            raise
    
    def from_json(self, json_str: str) -> Any:
        """Convert JSON string to data"""
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"JSON deserialization failed: {e}")
            raise


class DataTransformer:
    """Data transformation utilities"""
    
    def __init__(self):
        self.transformers = {}
    
    def register_transformer(self, name: str, transformer_func: Callable):
        """Register data transformer"""
        self.transformers[name] = transformer_func
        logger.info(f"Transformer registered: {name}")
    
    def transform(self, data: Any, transformer_name: str) -> Any:
        """Transform data using registered transformer"""
        if transformer_name not in self.transformers:
            raise ValueError(f"Transformer '{transformer_name}' not found")
        
        try:
            return self.transformers[transformer_name](data)
        except Exception as e:
            logger.error(f"Data transformation failed: {e}")
            raise
    
    def transform_dict(self, data: Dict[str, Any], field_transformations: Dict[str, str]) -> Dict[str, Any]:
        """Transform dictionary fields"""
        result = {}
        
        for field_name, value in data.items():
            if field_name in field_transformations:
                transformer_name = field_transformations[field_name]
                result[field_name] = self.transform(value, transformer_name)
            else:
                result[field_name] = value
        
        return result


# Global data validation and serialization instances
def get_data_validator() -> DataValidator:
    """Get data validator instance"""
    return DataValidator()

def get_data_serializer() -> DataSerializer:
    """Get data serializer instance"""
    return DataSerializer()

def get_data_transformer() -> DataTransformer:
    """Get data transformer instance"""
    return DataTransformer()
