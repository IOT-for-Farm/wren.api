"""
Environment Variable Loader

Utilities for loading and validating environment variables.
"""

import os
from typing import Any, Dict, List, Optional
from functools import wraps


def load_env_file(filepath: str) -> Dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars


def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable with validation."""
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    
    return value


def get_env_list(key: str, separator: str = ",", default: List[str] = None) -> List[str]:
    """Get environment variable as list."""
    if default is None:
        default = []
    
    value = os.getenv(key)
    if not value:
        return default
    
    return [item.strip() for item in value.split(separator) if item.strip()]


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean."""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def validate_required_env(required_vars: List[str]) -> None:
    """Validate that all required environment variables are set."""
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def env_required(*vars):
    """Decorator to ensure environment variables are set."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            validate_required_env(list(vars))
            return func(*args, **kwargs)
        return wrapper
    return decorator
