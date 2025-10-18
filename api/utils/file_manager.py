"""
File Management Utilities

Simple file handling and validation utilities.
"""

import os
import hashlib
from typing import Dict, List, Optional
from pathlib import Path


class FileManager:
    """Manages file operations with validation."""
    
    def __init__(self, upload_dir: str = "uploads", max_size: int = 10 * 1024 * 1024):
        """Initialize file manager."""
        self.upload_dir = Path(upload_dir)
        self.max_size = max_size
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.txt'}
        self.upload_dir.mkdir(exist_ok=True)
    
    def validate_file(self, filename: str, size: int) -> Dict[str, any]:
        """Validate file before upload."""
        errors = []
        ext = Path(filename).suffix.lower()
        
        if ext not in self.allowed_extensions:
            errors.append(f"File type {ext} not allowed")
        if size > self.max_size:
            errors.append(f"File size exceeds limit")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def save_file(self, file_data: bytes, filename: str) -> Dict[str, str]:
        """Save uploaded file with unique naming."""
        file_hash = hashlib.md5(file_data).hexdigest()
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{file_hash[:8]}{ext}"
        file_path = self.upload_dir / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        return {"filename": unique_filename, "path": str(file_path)}
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file."""
        file_path = self.upload_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False
