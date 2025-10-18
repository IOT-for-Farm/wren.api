"""
Documentation Utilities

Helper functions for API documentation generation.
"""

from typing import Dict, List, Any
import inspect
from functools import wraps


def doc_route(path: str, methods: List[str] = None, summary: str = "", 
              description: str = ""):
    """
    Decorator to document API routes.
    
    Args:
        path: Route path
        methods: HTTP methods
        summary: Route summary
        description: Route description
    """
    if methods is None:
        methods = ["GET"]
    
    def decorator(func):
        func._doc_route = {
            "path": path,
            "methods": methods,
            "summary": summary,
            "description": description
        }
        return func
    return decorator


def extract_route_docs(func) -> Dict[str, Any]:
    """Extract documentation from a decorated function."""
    if hasattr(func, '_doc_route'):
        return func._doc_route
    return {}


def generate_route_summary(func) -> str:
    """Generate a summary from function docstring."""
    if func.__doc__:
        return func.__doc__.split('\n')[0].strip()
    return func.__name__.replace('_', ' ').title()


def validate_doc_schema(schema: Dict[str, Any]) -> bool:
    """Validate documentation schema structure."""
    required_fields = ["type", "properties"]
    return all(field in schema for field in required_fields)


def format_parameter_doc(param: Dict[str, Any]) -> str:
    """Format parameter documentation."""
    doc_parts = [f"**{param.get('name', 'Unknown')}**"]
    
    if param.get('type'):
        doc_parts.append(f"Type: {param['type']}")
    
    if param.get('required'):
        doc_parts.append("Required")
    else:
        doc_parts.append("Optional")
    
    if param.get('description'):
        doc_parts.append(f"Description: {param['description']}")
    
    return " - ".join(doc_parts)
