"""
Backup Management Utilities

Create and manage application backups.
"""

import os
import shutil
import json
import zipfile
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages application backups and restore operations."""
    
    def __init__(self, backup_dir: str = "backups"):
        """Initialize backup manager."""
        self.backup_dir = backup_dir
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self) -> None:
        """Ensure backup directory exists."""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, name: str, include_files: List[str] = None, 
                     include_database: bool = False) -> Dict[str, Any]:
        """Create a new backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_{timestamp}"
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files if specified
            if include_files:
                for file_path in include_files:
                    if os.path.exists(file_path):
                        zipf.write(file_path, os.path.basename(file_path))
            
            # Add database backup if requested
            if include_database:
                db_backup = self._create_database_backup()
                if db_backup:
                    zipf.write(db_backup, "database_backup.sql")
                    os.remove(db_backup)
            
            # Add backup metadata
            metadata = {
                "name": backup_name,
                "created_at": datetime.now().isoformat(),
                "files_included": include_files or [],
                "database_included": include_database,
                "version": "1.0"
            }
            
            zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
        
        logger.info(f"Created backup: {backup_name}")
        return {
            "backup_name": backup_name,
            "backup_path": backup_path,
            "size": os.path.getsize(backup_path),
            "created_at": metadata["created_at"]
        }
    
    def _create_database_backup(self) -> Optional[str]:
        """Create database backup (placeholder implementation)."""
        # This would typically use database-specific backup tools
        # For now, return None to indicate no database backup
        return None
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.zip'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    "name": filename.replace('.zip', ''),
                    "path": filepath,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def restore_backup(self, backup_name: str, restore_path: str = ".") -> Dict[str, Any]:
        """Restore from a backup."""
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        if not os.path.exists(backup_path):
            return {"success": False, "error": "Backup not found"}
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(restore_path)
            
            logger.info(f"Restored backup: {backup_name}")
            return {
                "success": True,
                "backup_name": backup_name,
                "restored_at": datetime.now().isoformat(),
                "restore_path": restore_path
            }
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup."""
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
            logger.info(f"Deleted backup: {backup_name}")
            return True
        
        return False
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific backup."""
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        if not os.path.exists(backup_path):
            return None
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if "backup_metadata.json" in zipf.namelist():
                    metadata_content = zipf.read("backup_metadata.json")
                    metadata = json.loads(metadata_content.decode())
                    
                    stat = os.stat(backup_path)
                    metadata.update({
                        "size": stat.st_size,
                        "file_created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                    
                    return metadata
        except Exception as e:
            logger.error(f"Error reading backup info: {e}")
        
        return None
