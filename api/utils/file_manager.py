"""
File Management Utilities for Wren API

This module provides comprehensive file handling, media management,
and file processing utilities.
"""

import os
import uuid
import hashlib
from typing import Any, Dict, List, Optional, Union, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import mimetypes
import magic
from PIL import Image
import logging

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


class FileManager:
    """File management and processing utilities"""
    
    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or getattr(settings, 'UPLOAD_DIR', 'uploads')
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """Ensure upload directory exists"""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: BinaryIO, filename: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "file_info": {}
        }
        
        try:
            # Check file extension
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"File type {file_ext} not allowed")
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"File size {file_size} exceeds limit")
            
            # Get file info
            validation_result["file_info"] = {
                "filename": filename,
                "extension": file_ext,
                "size": file_size,
                "mime_type": mimetypes.guess_type(filename)[0]
            }
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            logger.error(f"File validation failed: {e}")
        
        return validation_result
    
    def save_file(self, file: BinaryIO, filename: str) -> Dict[str, Any]:
        """Save uploaded file"""
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_ext = Path(filename).suffix
            unique_filename = f"{file_id}{file_ext}"
            file_path = Path(self.upload_dir) / unique_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file.read())
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": unique_filename,
                "original_filename": filename,
                "file_path": str(file_path),
                "file_hash": file_hash,
                "size": file_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file by ID"""
        try:
            # Find file by ID
            for file_path in Path(self.upload_dir).glob(f"{file_id}.*"):
                file_path.unlink()
                logger.info(f"File deleted: {file_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            for file_path in Path(self.upload_dir).glob(f"{file_id}.*"):
                return {
                    "file_id": file_id,
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "created_at": datetime.fromtimestamp(file_path.stat().st_ctime),
                    "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_id}: {e}")
            return None


class MediaProcessor:
    """Media processing utilities"""
    
    def __init__(self):
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        self.thumbnail_sizes = [(150, 150), (300, 300), (600, 600)]
    
    def process_image(self, file_path: str) -> Dict[str, Any]:
        """Process and optimize image"""
        try:
            with Image.open(file_path) as img:
                # Get image info
                image_info = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height
                }
                
                # Generate thumbnails
                thumbnails = self._generate_thumbnails(img, file_path)
                
                return {
                    "success": True,
                    "image_info": image_info,
                    "thumbnails": thumbnails
                }
                
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_thumbnails(self, img: Image.Image, original_path: str) -> List[Dict[str, Any]]:
        """Generate image thumbnails"""
        thumbnails = []
        base_path = Path(original_path)
        
        for size in self.thumbnail_sizes:
            try:
                # Create thumbnail
                thumbnail = img.copy()
                thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumbnail_name = f"{base_path.stem}_thumb_{size[0]}x{size[1]}{base_path.suffix}"
                thumbnail_path = base_path.parent / thumbnail_name
                thumbnail.save(thumbnail_path, optimize=True, quality=85)
                
                thumbnails.append({
                    "size": size,
                    "filename": thumbnail_name,
                    "path": str(thumbnail_path),
                    "file_size": thumbnail_path.stat().st_size
                })
                
            except Exception as e:
                logger.error(f"Failed to generate thumbnail {size}: {e}")
        
        return thumbnails


# Global file management instances
def get_file_manager() -> FileManager:
    """Get file manager instance"""
    return FileManager()

def get_media_processor() -> MediaProcessor:
    """Get media processor instance"""
    return MediaProcessor()
