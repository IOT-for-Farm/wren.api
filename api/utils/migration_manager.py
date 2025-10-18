"""
Database Migration Manager

Utilities for managing database schema migrations.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations and schema changes."""
    
    def __init__(self, migrations_dir: str = "migrations"):
        """Initialize migration manager."""
        self.migrations_dir = migrations_dir
        self.migrations = []
        self._load_migrations()
    
    def _load_migrations(self) -> None:
        """Load available migrations from directory."""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            return
        
        migration_files = [f for f in os.listdir(self.migrations_dir) 
                         if f.endswith('.py') and f.startswith('migration_')]
        
        for file in sorted(migration_files):
            migration_info = {
                "file": file,
                "name": file.replace('.py', ''),
                "path": os.path.join(self.migrations_dir, file)
            }
            self.migrations.append(migration_info)
    
    def create_migration(self, name: str, description: str = "") -> str:
        """Create a new migration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"migration_{timestamp}_{name}.py"
        filepath = os.path.join(self.migrations_dir, filename)
        
        template = f'''"""
Migration: {name}
Description: {description}
Created: {datetime.now().isoformat()}
"""

def up():
    """Apply migration."""
    pass

def down():
    """Rollback migration."""
    pass
'''
        
        with open(filepath, 'w') as f:
            f.write(template)
        
        logger.info(f"Created migration: {filename}")
        return filepath
    
    def get_migration_status(self) -> List[Dict[str, Any]]:
        """Get status of all migrations."""
        status = []
        for migration in self.migrations:
            status.append({
                "name": migration["name"],
                "file": migration["file"],
                "applied": False,  # Would check against database
                "created": os.path.getctime(migration["path"])
            })
        return status
    
    def validate_migration(self, filepath: str) -> bool:
        """Validate migration file structure."""
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        required_functions = ['def up():', 'def down():']
        return all(func in content for func in required_functions)
