"""
Schema Tracking Utilities

Track and manage database schema changes.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class SchemaTracker:
    """Tracks database schema changes and versions."""
    
    def __init__(self):
        """Initialize schema tracker."""
        self.schema_history = []
        self.current_version = "0.0.0"
    
    def record_schema_change(self, change_type: str, table_name: str, 
                           details: Dict[str, Any]) -> None:
        """Record a schema change."""
        change = {
            "id": len(self.schema_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "type": change_type,
            "table": table_name,
            "details": details,
            "version": self.current_version
        }
        self.schema_history.append(change)
    
    def add_table(self, table_name: str, columns: List[Dict[str, str]]) -> None:
        """Record table creation."""
        self.record_schema_change("CREATE_TABLE", table_name, {
            "columns": columns,
            "action": "created"
        })
    
    def modify_table(self, table_name: str, changes: Dict[str, Any]) -> None:
        """Record table modification."""
        self.record_schema_change("ALTER_TABLE", table_name, {
            "changes": changes,
            "action": "modified"
        })
    
    def drop_table(self, table_name: str) -> None:
        """Record table deletion."""
        self.record_schema_change("DROP_TABLE", table_name, {
            "action": "dropped"
        })
    
    def get_schema_history(self) -> List[Dict[str, Any]]:
        """Get complete schema change history."""
        return self.schema_history.copy()
    
    def get_table_changes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get changes for specific table."""
        return [
            change for change in self.schema_history
            if change["table"] == table_name
        ]
    
    def export_schema_snapshot(self) -> Dict[str, Any]:
        """Export current schema state."""
        return {
            "version": self.current_version,
            "timestamp": datetime.now().isoformat(),
            "changes_count": len(self.schema_history),
            "history": self.schema_history
        }
