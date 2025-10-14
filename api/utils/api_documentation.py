"""
API Documentation Utilities for Wren API

This module provides utilities for generating comprehensive API documentation,
including endpoint documentation, schema generation, and interactive documentation
features.
"""

from typing import Any, Dict, List, Optional, Union, Type, Callable
from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, create_model
from jinja2 import Template
import json
import yaml
from datetime import datetime
from pathlib import Path

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class EndpointDocumentation(BaseModel):
    """Endpoint documentation model"""
    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    summary: str = Field(..., description="Brief description")
    description: str = Field(..., description="Detailed description")
    tags: List[str] = Field(default_factory=list, description="Endpoint tags")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="Parameters")
    request_body: Optional[Dict[str, Any]] = Field(None, description="Request body schema")
    responses: Dict[str, Any] = Field(default_factory=dict, description="Response schemas")
    examples: Dict[str, Any] = Field(default_factory=dict, description="Request/response examples")
    security: List[Dict[str, Any]] = Field(default_factory=list, description="Security requirements")
    rate_limits: Optional[Dict[str, Any]] = Field(None, description="Rate limiting information")
    deprecated: bool = Field(False, description="Whether endpoint is deprecated")


class APIDocumentationBuilder:
    """Builder for comprehensive API documentation"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.endpoints: List[EndpointDocumentation] = []
        self.schemas: Dict[str, Any] = {}
        self.tags: Dict[str, Any] = {}
    
    def add_endpoint(self, endpoint: EndpointDocumentation):
        """Add endpoint documentation"""
        self.endpoints.append(endpoint)
        logger.info(f"Added endpoint documentation: {endpoint.method} {endpoint.path}")
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add custom schema"""
        self.schemas[name] = schema
        logger.info(f"Added schema: {name}")
    
    def add_tag(self, name: str, description: str, external_docs: Optional[Dict[str, str]] = None):
        """Add tag documentation"""
        self.tags[name] = {
            "description": description,
            "externalDocs": external_docs
        }
        logger.info(f"Added tag: {name}")
    
    def generate_markdown_docs(self) -> str:
        """Generate Markdown documentation"""
        template = Template("""
# Wren API Documentation

## Overview

The Wren API provides comprehensive business management capabilities including user management, product catalog, order processing, and analytics.

## Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

## Base URL

- Production: `https://api.wren.com/v1`
- Staging: `https://staging-api.wren.com/v1`
- Development: `http://localhost:8000/api/v1`

## Rate Limiting

- Authenticated users: 1000 requests/hour
- Unauthenticated users: 100 requests/hour

## Error Handling

All errors follow a consistent format:

```json
{
  "status_code": 400,
  "success": false,
  "message": "Error description",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_123456789",
  "error": {
    "code": "ERROR_CODE",
    "details": {}
  }
}
```

## Endpoints

{% for tag_name, tag_info in tags.items() %}
### {{ tag_name }}

{{ tag_info.description }}

{% for endpoint in endpoints %}
{% if tag_name in endpoint.tags %}
#### {{ endpoint.method.upper() }} {{ endpoint.path }}

{{ endpoint.description }}

**Summary:** {{ endpoint.summary }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}) - {{ param.description }}
  - Required: {{ param.required }}
  - In: {{ param.in }}
{% endfor %}
{% endif %}

{% if endpoint.request_body %}
**Request Body:**
```json
{{ endpoint.request_body | tojson(indent=2) }}
```
{% endif %}

**Responses:**
{% for status_code, response in endpoint.responses.items() %}
- `{{ status_code }}`: {{ response.description }}
{% endfor %}

{% if endpoint.examples %}
**Examples:**
{% for example_name, example_data in endpoint.examples.items() %}
**{{ example_name }}:**
```json
{{ example_data | tojson(indent=2) }}
```
{% endfor %}
{% endif %}

{% if endpoint.rate_limits %}
**Rate Limits:**
- {{ endpoint.rate_limits.requests_per_hour }} requests per hour
- {{ endpoint.rate_limits.requests_per_minute }} requests per minute
{% endif %}

{% if endpoint.deprecated %}
⚠️ **Deprecated**: This endpoint is deprecated and will be removed in a future version.
{% endif %}

---
{% endif %}
{% endfor %}
{% endfor %}

## Schemas

{% for schema_name, schema_def in schemas.items() %}
### {{ schema_name }}

```json
{{ schema_def | tojson(indent=2) }}
```

{% endfor %}

## SDKs and Libraries

- **Python**: `pip install wren-api-client`
- **JavaScript**: `npm install @wren/api-client`
- **PHP**: `composer require wren/api-client`
- **Ruby**: `gem install wren-api-client`

## Support

For API support, please contact:
- Email: api-support@wren.com
- Documentation: https://docs.wren.com
- GitHub Issues: https://github.com/wren/api/issues
        """)
        
        return template.render(
            endpoints=self.endpoints,
            schemas=self.schemas,
            tags=self.tags
        )
    
    def generate_postman_collection(self) -> Dict[str, Any]:
        """Generate Postman collection"""
        collection = {
            "info": {
                "name": "Wren API",
                "description": "Complete Wren API collection",
                "version": "1.0.0",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{auth_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "https://api.wren.com/v1",
                    "type": "string"
                },
                {
                    "key": "auth_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Group endpoints by tags
        tag_groups = {}
        for endpoint in self.endpoints:
            for tag in endpoint.tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(endpoint)
        
        # Create Postman items
        for tag_name, endpoints in tag_groups.items():
            tag_item = {
                "name": tag_name,
                "item": []
            }
            
            for endpoint in endpoints:
                item = {
                    "name": f"{endpoint.method.upper()} {endpoint.path}",
                    "request": {
                        "method": endpoint.method.upper(),
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "url": {
                            "raw": "{{base_url}}{{endpoint.path}}",
                            "host": ["{{base_url}}"],
                            "path": endpoint.path.split('/')[1:]
                        },
                        "description": endpoint.description
                    },
                    "response": []
                }
                
                # Add parameters
                if endpoint.parameters:
                    item["request"]["url"]["query"] = []
                    for param in endpoint.parameters:
                        if param.get("in") == "query":
                            item["request"]["url"]["query"].append({
                                "key": param["name"],
                                "value": "",
                                "description": param.get("description", "")
                            })
                
                # Add request body
                if endpoint.request_body:
                    item["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(endpoint.request_body, indent=2),
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
                
                tag_item["item"].append(item)
            
            collection["item"].append(tag_item)
        
        return collection
    
    def generate_insomnia_collection(self) -> Dict[str, Any]:
        """Generate Insomnia collection"""
        collection = {
            "_type": "export",
            "__export_format": 4,
            "__export_date": datetime.utcnow().isoformat(),
            "__export_source": "wren-api-docs",
            "resources": []
        }
        
        # Create workspace
        workspace = {
            "_id": "wrk_wren_api",
            "_type": "workspace",
            "name": "Wren API",
            "description": "Wren API workspace"
        }
        collection["resources"].append(workspace)
        
        # Create environment
        environment = {
            "_id": "env_wren_api",
            "_type": "environment",
            "name": "Wren API Environment",
            "data": {
                "base_url": "https://api.wren.com/v1",
                "auth_token": ""
            },
            "dataPropertyOrder": {
                "&": ["base_url", "auth_token"]
            },
            "color": None,
            "isPrivate": False,
            "parentId": "wrk_wren_api"
        }
        collection["resources"].append(environment)
        
        # Create requests
        for endpoint in self.endpoints:
            request = {
                "_id": f"req_{endpoint.method}_{endpoint.path.replace('/', '_')}",
                "_type": "request",
                "name": f"{endpoint.method.upper()} {endpoint.path}",
                "description": endpoint.description,
                "url": "{{ _.base_url }}{{ endpoint.path }}",
                "method": endpoint.method.upper(),
                "body": {},
                "parameters": [],
                "headers": [
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "authentication": {
                    "type": "bearer",
                    "token": "{{ _.auth_token }}"
                },
                "parentId": "wrk_wren_api"
            }
            
            # Add parameters
            for param in endpoint.parameters:
                if param.get("in") == "query":
                    request["parameters"].append({
                        "name": param["name"],
                        "value": "",
                        "description": param.get("description", "")
                    })
            
            # Add request body
            if endpoint.request_body:
                request["body"] = {
                    "mimeType": "application/json",
                    "text": json.dumps(endpoint.request_body, indent=2)
                }
            
            collection["resources"].append(request)
        
        return collection


class InteractiveDocumentation:
    """Interactive documentation features"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.builder = APIDocumentationBuilder(app)
    
    def add_documentation_endpoints(self):
        """Add documentation endpoints to the app"""
        
        @self.app.get("/docs/markdown", response_class=HTMLResponse, tags=["Documentation"])
        async def get_markdown_docs():
            """Get API documentation in Markdown format"""
            markdown_content = self.builder.generate_markdown_docs()
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Wren API Documentation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    h1, h2, h3 {{ color: #333; }}
                </style>
            </head>
            <body>
                {markdown_content.replace(chr(10), '<br>')}
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/docs/postman", tags=["Documentation"])
        async def get_postman_collection():
            """Get Postman collection for API"""
            return self.builder.generate_postman_collection()
        
        @self.app.get("/docs/insomnia", tags=["Documentation"])
        async def get_insomnia_collection():
            """Get Insomnia collection for API"""
            return self.builder.generate_insomnia_collection()
        
        @self.app.get("/docs/schemas", tags=["Documentation"])
        async def get_api_schemas():
            """Get all API schemas"""
            return self.builder.schemas
        
        @self.app.get("/docs/endpoints", tags=["Documentation"])
        async def get_endpoints():
            """Get all endpoint documentation"""
            return [endpoint.dict() for endpoint in self.builder.endpoints]
        
        logger.info("Interactive documentation endpoints added")


class SchemaGenerator:
    """Generate API schemas from models"""
    
    @staticmethod
    def generate_schema_from_model(model: Type[BaseModel]) -> Dict[str, Any]:
        """Generate JSON schema from Pydantic model"""
        return model.schema()
    
    @staticmethod
    def generate_schema_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON schema from dictionary"""
        # This is a simplified implementation
        # In practice, you'd use a library like jsonschema
        return {
            "type": "object",
            "properties": {
                key: {"type": type(value).__name__}
                for key, value in data.items()
            }
        }
    
    @staticmethod
    def create_example_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create example data from JSON schema"""
        example = {}
        
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                prop_type = prop_schema.get("type", "string")
                
                if prop_type == "string":
                    example[prop_name] = f"example_{prop_name}"
                elif prop_type == "integer":
                    example[prop_name] = 1
                elif prop_type == "number":
                    example[prop_name] = 1.0
                elif prop_type == "boolean":
                    example[prop_name] = True
                elif prop_type == "array":
                    example[prop_name] = []
                elif prop_type == "object":
                    example[prop_name] = {}
        
        return example


def setup_api_documentation(app: FastAPI):
    """Setup comprehensive API documentation"""
    interactive_docs = InteractiveDocumentation(app)
    interactive_docs.add_documentation_endpoints()
    
    # Add common tags
    interactive_docs.builder.add_tag(
        "Authentication",
        "User authentication and authorization endpoints"
    )
    interactive_docs.builder.add_tag(
        "Users",
        "User management and profile operations"
    )
    interactive_docs.builder.add_tag(
        "Organizations",
        "Organization management and settings"
    )
    interactive_docs.builder.add_tag(
        "Products",
        "Product catalog and inventory management"
    )
    interactive_docs.builder.add_tag(
        "Orders",
        "Order processing and management"
    )
    interactive_docs.builder.add_tag(
        "Payments",
        "Payment processing and transactions"
    )
    interactive_docs.builder.add_tag(
        "Analytics",
        "Analytics and reporting endpoints"
    )
    interactive_docs.builder.add_tag(
        "Documentation",
        "API documentation and schema endpoints"
    )
    
    logger.info("API documentation setup completed")
