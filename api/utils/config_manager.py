"""
Configuration Management for Wren API

This module provides comprehensive configuration management, environment
handling, and configuration validation utilities.
"""

import os
import json
import yaml
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


@dataclass
class ConfigSection:
    """Configuration section"""
    name: str
    values: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """Configuration management system"""
    
    def __init__(self):
        self.config_sections = {}
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.config_files = []
        self.validators = {}
    
    def add_config_section(self, section: ConfigSection):
        """Add configuration section"""
        self.config_sections[section.name] = section
        logger.info(f"Configuration section added: {section.name}")
    
    def get_config(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value"""
        if section not in self.config_sections:
            logger.warning(f"Configuration section not found: {section}")
            return default
        
        config_section = self.config_sections[section]
        
        if key is None:
            return config_section.values
        
        # Check environment variable first
        env_key = f"{section.upper()}_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value)
        
        # Check configuration values
        if key in config_section.values:
            return config_section.values[key]
        
        # Check defaults
        if key in config_section.defaults:
            return config_section.defaults[key]
        
        return default
    
    def set_config(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if section not in self.config_sections:
            self.config_sections[section] = ConfigSection(name=section)
        
        self.config_sections[section].values[key] = value
        logger.info(f"Configuration set: {section}.{key}")
    
    def load_from_file(self, file_path: str):
        """Load configuration from file"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
            elif file_path.suffix.lower() in ['.yml', '.yaml']:
                with open(file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            else:
                logger.error(f"Unsupported configuration file format: {file_path.suffix}")
                return
            
            # Load configuration sections
            for section_name, section_data in config_data.items():
                if section_name not in self.config_sections:
                    self.config_sections[section_name] = ConfigSection(name=section_name)
                
                self.config_sections[section_name].values.update(section_data)
            
            self.config_files.append(str(file_path))
            logger.info(f"Configuration loaded from: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")
    
    def save_to_file(self, file_path: str, format: str = "json"):
        """Save configuration to file"""
        try:
            config_data = {}
            
            for section_name, section in self.config_sections.items():
                config_data[section_name] = section.values
            
            file_path = Path(file_path)
            
            if format.lower() == 'json':
                with open(file_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
            elif format.lower() in ['yml', 'yaml']:
                with open(file_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            else:
                logger.error(f"Unsupported configuration format: {format}")
                return
            
            logger.info(f"Configuration saved to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {file_path}: {e}")
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate configuration"""
        validation_errors = {}
        
        for section_name, section in self.config_sections.items():
            section_errors = []
            
            # Check required fields
            for required_field in section.required:
                if required_field not in section.values:
                    section_errors.append(f"Required field missing: {required_field}")
            
            # Run custom validators
            if section_name in self.validators:
                validator = self.validators[section_name]
                try:
                    validator(section.values)
                except Exception as e:
                    section_errors.append(f"Validation error: {str(e)}")
            
            if section_errors:
                validation_errors[section_name] = section_errors
        
        return validation_errors
    
    def register_validator(self, section: str, validator: callable):
        """Register configuration validator"""
        self.validators[section] = validator
        logger.info(f"Validator registered for section: {section}")
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        env_config = {}
        
        for section_name, section in self.config_sections.items():
            env_section = {}
            
            for key, value in section.values.items():
                env_key = f"{section_name.upper()}_{key.upper()}"
                env_value = os.getenv(env_key)
                
                if env_value is not None:
                    env_section[key] = self._parse_env_value(env_value)
                else:
                    env_section[key] = value
            
            env_config[section_name] = env_section
        
        return env_config
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value"""
        # Try to parse as JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try to parse as boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def reload_configuration(self):
        """Reload configuration from files"""
        for file_path in self.config_files:
            self.load_from_file(file_path)
        logger.info("Configuration reloaded")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "environment": self.environment,
            "sections": list(self.config_sections.keys()),
            "config_files": self.config_files,
            "validators": list(self.validators.keys())
        }


class EnvironmentManager:
    """Environment management utilities"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.environment_configs = {
            "development": {
                "debug": True,
                "log_level": "DEBUG",
                "database_url": "sqlite:///./dev.db"
            },
            "staging": {
                "debug": False,
                "log_level": "INFO",
                "database_url": "postgresql://staging:password@localhost/wren_staging"
            },
            "production": {
                "debug": False,
                "log_level": "WARNING",
                "database_url": "postgresql://prod:password@localhost/wren_prod"
            }
        }
    
    def get_environment(self) -> str:
        """Get current environment"""
        return self.environment
    
    def is_development(self) -> bool:
        """Check if in development environment"""
        return self.environment == "development"
    
    def is_staging(self) -> bool:
        """Check if in staging environment"""
        return self.environment == "staging"
    
    def is_production(self) -> bool:
        """Check if in production environment"""
        return self.environment == "production"
    
    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        return self.environment_configs.get(self.environment, {})
    
    def set_environment(self, environment: str):
        """Set environment"""
        if environment in self.environment_configs:
            self.environment = environment
            os.environ["ENVIRONMENT"] = environment
            logger.info(f"Environment set to: {environment}")
        else:
            logger.error(f"Invalid environment: {environment}")


class SecretManager:
    """Secret management utilities"""
    
    def __init__(self):
        self.secrets = {}
        self.secret_files = []
    
    def load_secrets_from_file(self, file_path: str):
        """Load secrets from file"""
        try:
            with open(file_path, 'r') as f:
                secrets_data = json.load(f)
            
            self.secrets.update(secrets_data)
            self.secret_files.append(file_path)
            logger.info(f"Secrets loaded from: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load secrets from {file_path}: {e}")
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get secret value"""
        # Check environment variable first
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return env_value
        
        # Check loaded secrets
        return self.secrets.get(key, default)
    
    def set_secret(self, key: str, value: Any):
        """Set secret value"""
        self.secrets[key] = value
        logger.info(f"Secret set: {key}")
    
    def mask_secret(self, value: str) -> str:
        """Mask secret value for logging"""
        if len(value) <= 4:
            return "*" * len(value)
        return value[:2] + "*" * (len(value) - 4) + value[-2:]


# Global configuration instances
def get_config_manager() -> ConfigurationManager:
    """Get configuration manager instance"""
    return ConfigurationManager()

def get_environment_manager() -> EnvironmentManager:
    """Get environment manager instance"""
    return EnvironmentManager()

def get_secret_manager() -> SecretManager:
    """Get secret manager instance"""
    return SecretManager()
