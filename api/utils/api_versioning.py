"""
API Versioning and Backward Compatibility for Wren API

This module provides comprehensive API versioning, backward compatibility,
and version management utilities.
"""

import re
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class VersionStrategy(Enum):
    """API versioning strategies"""
    URL_PATH = "url_path"
    HEADER = "header"
    QUERY_PARAM = "query_param"
    ACCEPT_HEADER = "accept_header"


@dataclass
class APIVersion:
    """API version information"""
    version: str
    release_date: datetime
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    is_stable: bool = True
    changelog: List[str] = None
    
    def __post_init__(self):
        if self.changelog is None:
            self.changelog = []


class VersionManager:
    """API version management system"""
    
    def __init__(self):
        self.versions = {}
        self.current_version = "v1"
        self.default_version = "v1"
        self.version_strategy = VersionStrategy.URL_PATH
        self.version_middleware = None
    
    def register_version(self, version: APIVersion):
        """Register API version"""
        self.versions[version.version] = version
        logger.info(f"API version registered: {version.version}")
    
    def get_version_info(self, version: str) -> Optional[APIVersion]:
        """Get version information"""
        return self.versions.get(version)
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported versions"""
        return list(self.versions.keys())
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported"""
        return version in self.versions
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated"""
        version_info = self.get_version_info(version)
        if not version_info:
            return False
        
        if version_info.deprecation_date:
            return datetime.utcnow() >= version_info.deprecation_date
        
        return False
    
    def is_version_sunset(self, version: str) -> bool:
        """Check if version is sunset"""
        version_info = self.get_version_info(version)
        if not version_info:
            return False
        
        if version_info.sunset_date:
            return datetime.utcnow() >= version_info.sunset_date
        
        return False
    
    def get_version_status(self, version: str) -> str:
        """Get version status"""
        if not self.is_version_supported(version):
            return "unsupported"
        
        if self.is_version_sunset(version):
            return "sunset"
        
        if self.is_version_deprecated(version):
            return "deprecated"
        
        return "supported"
    
    def set_current_version(self, version: str):
        """Set current API version"""
        if self.is_version_supported(version):
            self.current_version = version
            logger.info(f"Current API version set to: {version}")
        else:
            logger.error(f"Version {version} is not supported")
    
    def set_version_strategy(self, strategy: VersionStrategy):
        """Set versioning strategy"""
        self.version_strategy = strategy
        logger.info(f"Version strategy set to: {strategy.value}")


class BackwardCompatibilityManager:
    """Backward compatibility management"""
    
    def __init__(self):
        self.compatibility_rules = {}
        self.field_mappings = {}
        self.response_transformers = {}
    
    def add_compatibility_rule(self, from_version: str, to_version: str, rule: Dict[str, Any]):
        """Add backward compatibility rule"""
        key = f"{from_version}_to_{to_version}"
        self.compatibility_rules[key] = rule
        logger.info(f"Compatibility rule added: {key}")
    
    def add_field_mapping(self, version: str, field_mappings: Dict[str, str]):
        """Add field mapping for version"""
        self.field_mappings[version] = field_mappings
        logger.info(f"Field mappings added for version: {version}")
    
    def register_response_transformer(self, version: str, transformer: Callable):
        """Register response transformer for version"""
        self.response_transformers[version] = transformer
        logger.info(f"Response transformer registered for version: {version}")
    
    def transform_response(self, data: Any, from_version: str, to_version: str) -> Any:
        """Transform response for backward compatibility"""
        if from_version == to_version:
            return data
        
        # Apply field mappings
        if to_version in self.field_mappings:
            data = self._apply_field_mappings(data, self.field_mappings[to_version])
        
        # Apply response transformer
        if to_version in self.response_transformers:
            data = self.response_transformers[to_version](data)
        
        return data
    
    def _apply_field_mappings(self, data: Any, field_mappings: Dict[str, str]) -> Any:
        """Apply field mappings to data"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                new_key = field_mappings.get(key, key)
                result[new_key] = self._apply_field_mappings(value, field_mappings)
            return result
        elif isinstance(data, list):
            return [self._apply_field_mappings(item, field_mappings) for item in data]
        else:
            return data
    
    def validate_compatibility(self, from_version: str, to_version: str) -> bool:
        """Validate backward compatibility"""
        key = f"{from_version}_to_{to_version}"
        return key in self.compatibility_rules


class VersionHeaderManager:
    """Version header management"""
    
    def __init__(self):
        self.header_name = "API-Version"
        self.accept_header_pattern = r"application/vnd\.api\+json;version=(\d+)"
    
    def extract_version_from_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract version from headers"""
        # Check custom header
        if self.header_name in headers:
            return headers[self.header_name]
        
        # Check Accept header
        accept_header = headers.get("Accept", "")
        match = re.search(self.accept_header_pattern, accept_header)
        if match:
            return f"v{match.group(1)}"
        
        return None
    
    def add_version_header(self, response_headers: Dict[str, str], version: str):
        """Add version header to response"""
        response_headers[self.header_name] = version
        response_headers["API-Version-Supported"] = "true"
        
        # Add deprecation warning if applicable
        # This would be implemented based on version status
    
    def create_version_headers(self, version: str, status: str) -> Dict[str, str]:
        """Create version headers"""
        headers = {
            self.header_name: version,
            "API-Version-Status": status
        }
        
        if status == "deprecated":
            headers["API-Version-Deprecated"] = "true"
            headers["API-Version-Sunset-Date"] = "2024-12-31"  # Example
        
        return headers


class VersionRouter:
    """Version-based routing"""
    
    def __init__(self):
        self.version_routes = {}
        self.fallback_routes = {}
    
    def register_version_route(self, version: str, route: str, handler: Callable):
        """Register route for specific version"""
        if version not in self.version_routes:
            self.version_routes[version] = {}
        
        self.version_routes[version][route] = handler
        logger.info(f"Version route registered: {version}/{route}")
    
    def register_fallback_route(self, route: str, handler: Callable):
        """Register fallback route"""
        self.fallback_routes[route] = handler
        logger.info(f"Fallback route registered: {route}")
    
    def get_route_handler(self, version: str, route: str) -> Optional[Callable]:
        """Get route handler for version"""
        # Try version-specific route first
        if version in self.version_routes and route in self.version_routes[version]:
            return self.version_routes[version][route]
        
        # Fall back to default route
        if route in self.fallback_routes:
            return self.fallback_routes[route]
        
        return None
    
    def get_available_routes(self, version: str) -> List[str]:
        """Get available routes for version"""
        routes = []
        
        if version in self.version_routes:
            routes.extend(self.version_routes[version].keys())
        
        routes.extend(self.fallback_routes.keys())
        
        return list(set(routes))


# Global versioning instances
def get_version_manager() -> VersionManager:
    """Get version manager instance"""
    return VersionManager()

def get_compatibility_manager() -> BackwardCompatibilityManager:
    """Get backward compatibility manager instance"""
    return BackwardCompatibilityManager()

def get_version_header_manager() -> VersionHeaderManager:
    """Get version header manager instance"""
    return VersionHeaderManager()

def get_version_router() -> VersionRouter:
    """Get version router instance"""
    return VersionRouter()
