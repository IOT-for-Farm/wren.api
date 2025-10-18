"""
File Validation Utilities

Simple file validation helpers.
"""

import mimetypes
from typing import List, Dict


class FileValidator:
    """Validates file types and content."""
    
    def __init__(self):
        """Initialize validator."""
        self.image_types = ['image/jpeg', 'image/png', 'image/gif']
        self.document_types = ['application/pdf', 'text/plain']
    
    def get_file_type(self, filename: str) -> str:
        """Get MIME type for filename."""
        return mimetypes.guess_type(filename)[0] or 'unknown'
    
    def is_image(self, filename: str) -> bool:
        """Check if file is an image."""
        return self.get_file_type(filename) in self.image_types
    
    def is_document(self, filename: str) -> bool:
        """Check if file is a document."""
        return self.get_file_type(filename) in self.document_types
    
    def validate_extension(self, filename: str, allowed: List[str]) -> bool:
        """Validate file extension against allowed list."""
        ext = filename.split('.')[-1].lower()
        return ext in allowed
