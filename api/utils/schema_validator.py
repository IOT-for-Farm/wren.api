"""
Schema Validation Utilities for Wren API

This module provides comprehensive schema validation utilities including
custom validators, data sanitization, and validation error handling.
"""

from typing import Any, Dict, List, Optional, Union, Type, Callable
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.validators import str_validator
import re
import uuid
from datetime import datetime, date
from decimal import Decimal
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class SchemaValidator:
    """Comprehensive schema validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format", "email", "INVALID_EMAIL")
        return email.lower().strip()
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (7-15 digits)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValidationError("Invalid phone number length", "phone", "INVALID_PHONE")
        
        return digits_only
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> str:
        """Validate UUID format"""
        try:
            uuid.UUID(uuid_string)
            return uuid_string
        except ValueError:
            raise ValidationError("Invalid UUID format", "uuid", "INVALID_UUID")
    
    @staticmethod
    def validate_slug(slug: str) -> str:
        """Validate URL slug format"""
        slug_pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        if not re.match(slug_pattern, slug):
            raise ValidationError("Invalid slug format. Use lowercase letters, numbers, and hyphens only", "slug", "INVALID_SLUG")
        return slug
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long", "password", "WEAK_PASSWORD")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter", "password", "WEAK_PASSWORD")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter", "password", "WEAK_PASSWORD")
        
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit", "password", "WEAK_PASSWORD")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character", "password", "WEAK_PASSWORD")
        
        return password
    
    @staticmethod
    def validate_currency(amount: Union[str, float, Decimal]) -> Decimal:
        """Validate currency amount"""
        try:
            decimal_amount = Decimal(str(amount))
            if decimal_amount < 0:
                raise ValidationError("Currency amount cannot be negative", "amount", "NEGATIVE_AMOUNT")
            if decimal_amount > Decimal('999999.99'):
                raise ValidationError("Currency amount cannot exceed 999,999.99", "amount", "AMOUNT_TOO_LARGE")
            return decimal_amount
        except (ValueError, TypeError):
            raise ValidationError("Invalid currency amount format", "amount", "INVALID_AMOUNT")
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> tuple:
        """Validate date range"""
        if start_date > end_date:
            raise ValidationError("Start date cannot be after end date", "date_range", "INVALID_DATE_RANGE")
        return start_date, end_date
    
    @staticmethod
    def validate_json_string(json_string: str) -> str:
        """Validate JSON string format"""
        try:
            import json
            json.loads(json_string)
            return json_string
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format", "json", "INVALID_JSON")


class CustomValidators:
    """Collection of custom Pydantic validators"""
    
    @staticmethod
    def email_validator(cls, v):
        """Pydantic email validator"""
        return SchemaValidator.validate_email(v)
    
    @staticmethod
    def phone_validator(cls, v):
        """Pydantic phone validator"""
        return SchemaValidator.validate_phone(v)
    
    @staticmethod
    def uuid_validator(cls, v):
        """Pydantic UUID validator"""
        return SchemaValidator.validate_uuid(v)
    
    @staticmethod
    def slug_validator(cls, v):
        """Pydantic slug validator"""
        return SchemaValidator.validate_slug(v)
    
    @staticmethod
    def password_validator(cls, v):
        """Pydantic password validator"""
        return SchemaValidator.validate_password(v)
    
    @staticmethod
    def currency_validator(cls, v):
        """Pydantic currency validator"""
        return SchemaValidator.validate_currency(v)
    
    @staticmethod
    def json_string_validator(cls, v):
        """Pydantic JSON string validator"""
        return SchemaValidator.validate_json_string(v)


class SanitizedString(str):
    """Custom string type with sanitization"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValidationError("Value must be a string")
        
        # Basic sanitization
        sanitized = v.strip()
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return cls(sanitized)


class EmailString(str):
    """Custom email string type"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        return cls(SchemaValidator.validate_email(v))


class PhoneString(str):
    """Custom phone string type"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        return cls(SchemaValidator.validate_phone(v))


class SlugString(str):
    """Custom slug string type"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        return cls(SchemaValidator.validate_slug(v))


class CurrencyDecimal(Decimal):
    """Custom currency decimal type"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        return cls(SchemaValidator.validate_currency(v))


class BaseValidatedModel(BaseModel):
    """Base model with common validation features"""
    
    class Config:
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Sanitize string inputs"""
        if isinstance(v, str):
            return v.strip()
        return v
    
    @root_validator
    def validate_model(cls, values):
        """Root validator for model-level validation"""
        return values


class ValidationResult:
    """Validation result container"""
    
    def __init__(self, is_valid: bool = True, errors: List[Dict[str, Any]] = None, data: Any = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.data = data
    
    def add_error(self, field: str, message: str, code: str = None):
        """Add validation error"""
        self.errors.append({
            "field": field,
            "message": message,
            "code": code
        })
        self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "data": self.data
        }


class ModelValidator:
    """Model validation utilities"""
    
    @staticmethod
    def validate_model_data(model_class: Type[BaseModel], data: Dict[str, Any]) -> ValidationResult:
        """Validate data against a model"""
        try:
            validated_data = model_class(**data)
            return ValidationResult(is_valid=True, data=validated_data)
        except Exception as e:
            result = ValidationResult(is_valid=False)
            
            if hasattr(e, 'errors'):
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    result.add_error(field, error['msg'], error.get('type'))
            else:
                result.add_error('model', str(e))
            
            return result
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> ValidationResult:
        """Validate required fields"""
        result = ValidationResult()
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                result.add_error(field, f"Field '{field}' is required", "REQUIRED_FIELD")
        
        return result
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], field_types: Dict[str, Type]) -> ValidationResult:
        """Validate field types"""
        result = ValidationResult()
        
        for field, expected_type in field_types.items():
            if field in data:
                value = data[field]
                if not isinstance(value, expected_type):
                    result.add_error(
                        field, 
                        f"Field '{field}' must be of type {expected_type.__name__}", 
                        "INVALID_TYPE"
                    )
        
        return result
    
    @staticmethod
    def validate_field_ranges(
        data: Dict[str, Any], 
        field_ranges: Dict[str, Dict[str, Union[int, float]]]
    ) -> ValidationResult:
        """Validate field ranges"""
        result = ValidationResult()
        
        for field, range_config in field_ranges.items():
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    min_val = range_config.get('min')
                    max_val = range_config.get('max')
                    
                    if min_val is not None and value < min_val:
                        result.add_error(
                            field, 
                            f"Field '{field}' must be at least {min_val}", 
                            "VALUE_TOO_SMALL"
                        )
                    
                    if max_val is not None and value > max_val:
                        result.add_error(
                            field, 
                            f"Field '{field}' must be at most {max_val}", 
                            "VALUE_TOO_LARGE"
                        )
        
        return result


class DataSanitizer:
    """Data sanitization utilities"""
    
    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """Sanitize HTML content"""
        import html
        return html.escape(html_content)
    
    @staticmethod
    def sanitize_sql_input(input_string: str) -> str:
        """Sanitize SQL input (basic protection)"""
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
            r'(\'|\"|;|--|\/\*)',
        ]
        
        sanitized = input_string
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_file_path(file_path: str) -> str:
        """Sanitize file path"""
        # Remove directory traversal attempts
        sanitized = re.sub(r'\.\./', '', file_path)
        sanitized = re.sub(r'\.\.\\', '', sanitized)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_json_input(json_string: str) -> str:
        """Sanitize JSON input"""
        try:
            import json
            parsed = json.loads(json_string)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            return '{}'


def create_validated_field(
    field_type: Type,
    validators: List[Callable] = None,
    description: str = None
) -> Any:
    """Create a validated field with custom validators"""
    validators = validators or []
    
    def validate_value(v):
        for validator_func in validators:
            v = validator_func(v)
        return v
    
    return Field(
        ...,
        description=description,
        validator=validate_value
    )


def validate_and_sanitize_data(
    data: Dict[str, Any],
    validation_rules: Dict[str, Dict[str, Any]]
) -> ValidationResult:
    """Validate and sanitize data based on rules"""
    result = ValidationResult()
    sanitized_data = {}
    
    for field, rules in validation_rules.items():
        if field in data:
            value = data[field]
            
            # Apply sanitization
            if rules.get('sanitize'):
                sanitizer = rules['sanitize']
                if callable(sanitizer):
                    value = sanitizer(value)
            
            # Apply validation
            if rules.get('validate'):
                validator = rules['validate']
                if callable(validator):
                    try:
                        value = validator(value)
                    except ValidationError as e:
                        result.add_error(field, e.message, e.code)
                        continue
            
            # Check type
            if rules.get('type') and not isinstance(value, rules['type']):
                result.add_error(
                    field, 
                    f"Field '{field}' must be of type {rules['type'].__name__}", 
                    "INVALID_TYPE"
                )
                continue
            
            sanitized_data[field] = value
    
    if result.is_valid:
        result.data = sanitized_data
    
    return result
