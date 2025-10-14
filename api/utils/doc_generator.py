"""
API Documentation Generator for Wren API

This module provides comprehensive API documentation generation,
OpenAPI specification creation, and documentation utilities.
"""

import json
import inspect
from typing import Any, Dict, List, Optional, Union, Type, Callable
from datetime import datetime
from pathlib import Path
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class APIDocumentationGenerator:
    """API documentation generator"""
    
    def __init__(self):
        self.endpoints = {}
        self.schemas = {}
        self.tags = {}
        self.info = {
            "title": "Wren API",
            "version": "1.0.0",
            "description": "Comprehensive API for Wren application",
            "contact": {
                "name": "API Support",
                "email": "support@wren.com"
            }
        }
    
    def add_endpoint(self, endpoint: Dict[str, Any]):
        """Add API endpoint documentation"""
        path = endpoint.get("path", "")
        method = endpoint.get("method", "GET").upper()
        
        if path not in self.endpoints:
            self.endpoints[path] = {}
        
        self.endpoints[path][method] = endpoint
        logger.info(f"Endpoint documented: {method} {path}")
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add schema definition"""
        self.schemas[name] = schema
        logger.info(f"Schema added: {name}")
    
    def add_tag(self, name: str, description: str):
        """Add API tag"""
        self.tags[name] = {
            "name": name,
            "description": description
        }
        logger.info(f"Tag added: {name}")
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI specification"""
        openapi_spec = {
            "openapi": "3.0.0",
            "info": self.info,
            "servers": [
                {
                    "url": "https://api.wren.com/v1",
                    "description": "Production server"
                },
                {
                    "url": "https://staging-api.wren.com/v1",
                    "description": "Staging server"
                }
            ],
            "tags": list(self.tags.values()),
            "paths": self._generate_paths(),
            "components": {
                "schemas": self.schemas,
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            },
            "security": [
                {
                    "bearerAuth": []
                }
            ]
        }
        
        return openapi_spec
    
    def _generate_paths(self) -> Dict[str, Any]:
        """Generate paths section"""
        paths = {}
        
        for path, methods in self.endpoints.items():
            paths[path] = {}
            
            for method, endpoint in methods.items():
                paths[path][method.lower()] = {
                    "summary": endpoint.get("summary", ""),
                    "description": endpoint.get("description", ""),
                    "tags": endpoint.get("tags", []),
                    "parameters": endpoint.get("parameters", []),
                    "requestBody": endpoint.get("requestBody"),
                    "responses": endpoint.get("responses", {}),
                    "security": endpoint.get("security", [])
                }
        
        return paths
    
    def save_openapi_spec(self, file_path: str):
        """Save OpenAPI specification to file"""
        spec = self.generate_openapi_spec()
        
        with open(file_path, 'w') as f:
            json.dump(spec, f, indent=2)
        
        logger.info(f"OpenAPI specification saved to {file_path}")
    
    def generate_markdown_docs(self) -> str:
        """Generate Markdown documentation"""
        markdown = f"# {self.info['title']}\n\n"
        markdown += f"**Version:** {self.info['version']}\n\n"
        markdown += f"**Description:** {self.info['description']}\n\n"
        
        # Add tags section
        if self.tags:
            markdown += "## API Tags\n\n"
            for tag in self.tags.values():
                markdown += f"- **{tag['name']}**: {tag['description']}\n"
            markdown += "\n"
        
        # Add endpoints section
        markdown += "## API Endpoints\n\n"
        
        for path, methods in self.endpoints.items():
            markdown += f"### {path}\n\n"
            
            for method, endpoint in methods.items():
                markdown += f"#### {method.upper()} {path}\n\n"
                markdown += f"**Summary:** {endpoint.get('summary', '')}\n\n"
                markdown += f"**Description:** {endpoint.get('description', '')}\n\n"
                
                # Add parameters
                if endpoint.get("parameters"):
                    markdown += "**Parameters:**\n\n"
                    for param in endpoint["parameters"]:
                        markdown += f"- `{param.get('name', '')}` ({param.get('in', '')}): {param.get('description', '')}\n"
                    markdown += "\n"
                
                # Add responses
                if endpoint.get("responses"):
                    markdown += "**Responses:**\n\n"
                    for status_code, response in endpoint["responses"].items():
                        markdown += f"- `{status_code}`: {response.get('description', '')}\n"
                    markdown += "\n"
                
                markdown += "---\n\n"
        
        return markdown
    
    def save_markdown_docs(self, file_path: str):
        """Save Markdown documentation to file"""
        markdown = self.generate_markdown_docs()
        
        with open(file_path, 'w') as f:
            f.write(markdown)
        
        logger.info(f"Markdown documentation saved to {file_path}")


class SchemaGenerator:
    """Schema generation utilities"""
    
    def __init__(self):
        self.schemas = {}
    
    def generate_schema_from_model(self, model_class: Type) -> Dict[str, Any]:
        """Generate schema from model class"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Get model fields
        if hasattr(model_class, '__fields__'):
            for field_name, field_info in model_class.__fields__.items():
                field_schema = self._get_field_schema(field_info)
                schema["properties"][field_name] = field_schema
                
                if field_info.is_required():
                    schema["required"].append(field_name)
        
        return schema
    
    def _get_field_schema(self, field_info) -> Dict[str, Any]:
        """Get schema for field"""
        field_type = field_info.type_
        
        if field_type == str:
            return {"type": "string"}
        elif field_type == int:
            return {"type": "integer"}
        elif field_type == float:
            return {"type": "number"}
        elif field_type == bool:
            return {"type": "boolean"}
        elif field_type == list:
            return {"type": "array", "items": {"type": "string"}}
        elif field_type == dict:
            return {"type": "object"}
        else:
            return {"type": "string"}
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add schema definition"""
        self.schemas[name] = schema
        logger.info(f"Schema added: {name}")
    
    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get schema by name"""
        return self.schemas.get(name)
    
    def get_all_schemas(self) -> Dict[str, Any]:
        """Get all schemas"""
        return dict(self.schemas)


class DocumentationBuilder:
    """Documentation builder utilities"""
    
    def __init__(self):
        self.doc_generator = APIDocumentationGenerator()
        self.schema_generator = SchemaGenerator()
    
    def build_from_routes(self, routes: List[Dict[str, Any]]):
        """Build documentation from route definitions"""
        for route in routes:
            self.doc_generator.add_endpoint(route)
    
    def build_from_models(self, models: List[Type]):
        """Build documentation from model classes"""
        for model in models:
            schema = self.schema_generator.generate_schema_from_model(model)
            self.schema_generator.add_schema(model.__name__, schema)
    
    def generate_complete_docs(self, output_dir: str):
        """Generate complete documentation"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate OpenAPI spec
        openapi_file = output_path / "openapi.json"
        self.doc_generator.save_openapi_spec(str(openapi_file))
        
        # Generate Markdown docs
        markdown_file = output_path / "README.md"
        self.doc_generator.save_markdown_docs(str(markdown_file))
        
        # Generate schemas
        schemas_file = output_path / "schemas.json"
        with open(schemas_file, 'w') as f:
            json.dump(self.schema_generator.get_all_schemas(), f, indent=2)
        
        logger.info(f"Complete documentation generated in {output_dir}")


# Global documentation instances
def get_doc_generator() -> APIDocumentationGenerator:
    """Get API documentation generator instance"""
    return APIDocumentationGenerator()

def get_schema_generator() -> SchemaGenerator:
    """Get schema generator instance"""
    return SchemaGenerator()

def get_doc_builder() -> DocumentationBuilder:
    """Get documentation builder instance"""
    return DocumentationBuilder()
