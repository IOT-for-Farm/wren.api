"""
Configuration Management Utilities

Centralized configuration management with environment support.
"""

import os
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Application configuration container."""
    database_url: str
    redis_url: str
    secret_key: str
    debug: bool = False
    log_level: str = "INFO"
    api_version: str = "v1"
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        return cls(
            database_url=os.getenv("DATABASE_URL", "sqlite:///app.db"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            secret_key=os.getenv("SECRET_KEY", "default-secret-key"),
            debug=os.getenv("DEBUG", "False").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_version=os.getenv("API_VERSION", "v1")
        )


class ConfigManager:
    """Manages application configuration with validation."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config = Config.from_env()
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if not self.config.secret_key or self.config.secret_key == "default-secret-key":
            logger.warning("Using default secret key in production is not recommended")
        
        if self.config.debug and os.getenv("ENVIRONMENT") == "production":
            logger.warning("Debug mode enabled in production environment")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(self.config, key, default)
    
    def update(self, key: str, value: Any) -> None:
        """Update configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            logger.info(f"Configuration updated: {key} = {value}")
        else:
            logger.warning(f"Unknown configuration key: {key}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self.config, field.name)
            for field in self.config.__dataclass_fields__.values()
        }
