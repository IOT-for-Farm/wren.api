"""
API Documentation Generator

Utilities for generating API documentation from code.
"""

from typing import Dict, List, Any
import json
from datetime import datetime


class APIDocGenerator:
    """Generate API documentation from route definitions."""
    
    def __init__(self):
        """Initialize the documentation generator."""
        self.routes = []
        self.schemas = {}
    
    def add_route(self, path: str, methods: List[str], summary: str = "", 
                  description: str = "", parameters: List[Dict] = None) -> None:
        """Add a route to the documentation."""
        route_info = {
            "path": path,
            "methods": methods,
            "summary": summary,
            "description": description,
            "parameters": parameters or [],
            "added_at": datetime.now().isoformat()
        }
        self.routes.append(route_info)
    
    def add_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """Add a schema definition."""
        self.schemas[name] = schema
    
    def generate_openapi_spec(self, title: str = "API", version: str = "1.0.0") -> Dict:
        """Generate OpenAPI specification."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
                "description": "Auto-generated API documentation"
            },
            "paths": self._build_paths(),
            "components": {
                "schemas": self.schemas
            }
        }
    
    def _build_paths(self) -> Dict:
        """Build paths section for OpenAPI spec."""
        paths = {}
        for route in self.routes:
            if route["path"] not in paths:
                paths[route["path"]] = {}
            
            for method in route["methods"]:
                paths[route["path"]][method.lower()] = {
                    "summary": route["summary"],
                    "description": route["description"],
                    "parameters": route["parameters"]
                }
        return paths
    
    def export_to_json(self, filename: str) -> None:
        """Export documentation to JSON file."""
        spec = self.generate_openapi_spec()
        with open(filename, 'w') as f:
            json.dump(spec, f, indent=2)
