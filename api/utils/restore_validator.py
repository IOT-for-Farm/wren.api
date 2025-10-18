"""
Restore Validation Utilities

Validate backup integrity and restore operations.
"""

import os
import zipfile
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class RestoreValidator:
    """Validates backup integrity and restore operations."""
    
    def __init__(self):
        """Initialize restore validator."""
        self.required_files = ["backup_metadata.json"]
        self.supported_formats = [".zip"]
    
    def validate_backup(self, backup_path: str) -> Dict[str, Any]:
        """Validate backup file integrity."""
        if not os.path.exists(backup_path):
            return {"valid": False, "error": "Backup file not found"}
        
        if not any(backup_path.endswith(ext) for ext in self.supported_formats):
            return {"valid": False, "error": "Unsupported backup format"}
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Check if zip file is valid
                zipf.testzip()
                
                # Check for required files
                missing_files = []
                for required_file in self.required_files:
                    if required_file not in zipf.namelist():
                        missing_files.append(required_file)
                
                if missing_files:
                    return {
                        "valid": False,
                        "error": f"Missing required files: {missing_files}"
                    }
                
                # Validate metadata
                metadata_content = zipf.read("backup_metadata.json")
                metadata = json.loads(metadata_content.decode())
                
                return {
                    "valid": True,
                    "metadata": metadata,
                    "file_count": len(zipf.namelist()),
                    "total_size": sum(info.file_size for info in zipf.infolist())
                }
        
        except zipfile.BadZipFile:
            return {"valid": False, "error": "Corrupted backup file"}
        except json.JSONDecodeError:
            return {"valid": False, "error": "Invalid metadata format"}
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def validate_restore_environment(self, restore_path: str) -> Dict[str, Any]:
        """Validate restore environment."""
        issues = []
        
        if not os.path.exists(restore_path):
            issues.append("Restore path does not exist")
        elif not os.access(restore_path, os.W_OK):
            issues.append("No write permission to restore path")
        
        # Check available disk space (simplified check)
        if os.path.exists(restore_path):
            stat = os.statvfs(restore_path)
            free_space = stat.f_frsize * stat.f_bavail
            if free_space < 100 * 1024 * 1024:  # 100MB minimum
                issues.append("Insufficient disk space")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "restore_path": restore_path,
            "checked_at": datetime.now().isoformat()
        }
    
    def get_backup_compatibility(self, backup_path: str) -> Dict[str, Any]:
        """Check backup compatibility with current system."""
        validation_result = self.validate_backup(backup_path)
        
        if not validation_result["valid"]:
            return validation_result
        
        metadata = validation_result["metadata"]
        compatibility_issues = []
        
        # Check version compatibility
        backup_version = metadata.get("version", "unknown")
        if backup_version != "1.0":
            compatibility_issues.append(f"Backup version {backup_version} may not be compatible")
        
        # Check creation date
        created_at = metadata.get("created_at")
        if created_at:
            backup_date = datetime.fromisoformat(created_at)
            days_old = (datetime.now() - backup_date).days
            if days_old > 30:
                compatibility_issues.append(f"Backup is {days_old} days old")
        
        return {
            "compatible": len(compatibility_issues) == 0,
            "issues": compatibility_issues,
            "metadata": metadata,
            "checked_at": datetime.now().isoformat()
        }
    
    def estimate_restore_time(self, backup_path: str) -> Dict[str, Any]:
        """Estimate restore time based on backup size."""
        validation_result = self.validate_backup(backup_path)
        
        if not validation_result["valid"]:
            return {"error": "Invalid backup"}
        
        total_size = validation_result["total_size"]
        file_count = validation_result["file_count"]
        
        # Rough estimation (1MB per second for small files, slower for large files)
        estimated_seconds = max(10, total_size / (1024 * 1024))  # Minimum 10 seconds
        
        return {
            "estimated_seconds": int(estimated_seconds),
            "estimated_minutes": round(estimated_seconds / 60, 1),
            "total_size": total_size,
            "file_count": file_count
        }
