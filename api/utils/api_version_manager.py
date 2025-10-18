"""
API Version Management Utilities

Simple utilities for managing API versions and compatibility.
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class APIVersionManager:
    """Manages API versions and provides version-related utilities."""
    
    def __init__(self):
        """Initialize the API version manager."""
        self.versions = {
            "v1": {"status": "active", "release_date": datetime(2024, 1, 1)},
            "v2": {"status": "active", "release_date": datetime(2024, 6, 1)}
        }
        self.default_version = "v1"
    
    def get_version_from_header(self, accept_header: str) -> str:
        """Extract API version from Accept header."""
        if not accept_header:
            return self.default_version
            
        if "version=" in accept_header:
            try:
                return accept_header.split("version=")[1].split(";")[0].strip()
            except (IndexError, ValueError):
                pass
                
        return self.default_version
    
    def is_version_supported(self, version: str) -> bool:
        """Check if a version is supported."""
        return version in self.versions
    
    def get_supported_versions(self) -> List[str]:
        """Get list of all supported versions."""
        return list(self.versions.keys())
