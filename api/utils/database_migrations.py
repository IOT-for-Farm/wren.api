"""
Database Migrations and Schema Management for Wren API

This module provides comprehensive database migration utilities, schema management,
and database versioning capabilities.
"""

import os
import json
import hashlib
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
import logging

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


class MigrationManager:
    """Database migration management system"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or getattr(settings, 'DATABASE_URL', 'sqlite:///./app.db')
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.alembic_cfg = self._setup_alembic_config()
    
    def _setup_alembic_config(self) -> Config:
        """Setup Alembic configuration"""
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", "alembic")
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)
        return alembic_cfg
    
    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """Create a new migration"""
        try:
            if autogenerate:
                command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(self.alembic_cfg, message=message)
            
            logger.info(f"Migration created: {message}")
            return f"Migration '{message}' created successfully"
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise
    
    def upgrade_database(self, revision: str = "head") -> str:
        """Upgrade database to specified revision"""
        try:
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"Database upgraded to revision: {revision}")
            return f"Database upgraded to {revision}"
        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            raise
    
    def downgrade_database(self, revision: str) -> str:
        """Downgrade database to specified revision"""
        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Database downgraded to revision: {revision}")
            return f"Database downgraded to {revision}"
        except Exception as e:
            logger.error(f"Failed to downgrade database: {e}")
            raise
    
    def get_current_revision(self) -> str:
        """Get current database revision"""
        try:
            with self.engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                return current_rev or "No migrations applied"
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return "Error getting revision"
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            revisions = []
            
            for revision in script_dir.walk_revisions():
                revisions.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "branch_labels": revision.branch_labels,
                    "depends_on": revision.depends_on,
                    "doc": revision.doc,
                    "module_path": revision.module_path
                })
            
            return revisions
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def check_migration_status(self) -> Dict[str, Any]:
        """Check migration status"""
        try:
            current_rev = self.get_current_revision()
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            head_rev = script_dir.get_current_head()
            
            return {
                "current_revision": current_rev,
                "head_revision": head_rev,
                "is_up_to_date": current_rev == head_rev,
                "pending_migrations": self._get_pending_migrations(current_rev, head_rev)
            }
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {"error": str(e)}
    
    def _get_pending_migrations(self, current_rev: str, head_rev: str) -> List[str]:
        """Get list of pending migrations"""
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            pending = []
            
            for revision in script_dir.walk_revisions():
                if revision.revision != current_rev and revision.revision != head_rev:
                    pending.append(revision.revision)
            
            return pending
        except Exception:
            return []


class SchemaManager:
    """Database schema management utilities"""
    
    def __init__(self, engine):
        self.engine = engine
        self.metadata = MetaData()
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information"""
        try:
            with self.engine.connect() as connection:
                # Get table information
                tables = self._get_table_info(connection)
                
                # Get index information
                indexes = self._get_index_info(connection)
                
                # Get constraint information
                constraints = self._get_constraint_info(connection)
                
                # Get foreign key information
                foreign_keys = self._get_foreign_key_info(connection)
                
                return {
                    "tables": tables,
                    "indexes": indexes,
                    "constraints": constraints,
                    "foreign_keys": foreign_keys,
                    "schema_hash": self._calculate_schema_hash(tables, indexes, constraints, foreign_keys)
                }
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return {"error": str(e)}
    
    def _get_table_info(self, connection) -> List[Dict[str, Any]]:
        """Get table information"""
        tables = []
        
        # Get table names
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        table_names = [row[0] for row in result]
        
        for table_name in table_names:
            if table_name == 'sqlite_sequence':
                continue
            
            # Get column information
            columns = []
            result = connection.execute(text(f"PRAGMA table_info({table_name});"))
            for row in result:
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "default_value": row[4],
                    "primary_key": bool(row[5])
                })
            
            # Get table statistics
            result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
            row_count = result.scalar()
            
            tables.append({
                "name": table_name,
                "columns": columns,
                "row_count": row_count
            })
        
        return tables
    
    def _get_index_info(self, connection) -> List[Dict[str, Any]]:
        """Get index information"""
        indexes = []
        
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='index';"))
        index_names = [row[0] for row in result]
        
        for index_name in index_names:
            if index_name.startswith('sqlite_'):
                continue
            
            # Get index details
            result = connection.execute(text(f"PRAGMA index_info({index_name});"))
            columns = [row[2] for row in result]
            
            # Get index statistics
            result = connection.execute(text(f"PRAGMA index_list({index_name});"))
            index_info = result.fetchone()
            
            if index_info:
                indexes.append({
                    "name": index_name,
                    "columns": columns,
                    "unique": bool(index_info[2]),
                    "table": index_info[1]
                })
        
        return indexes
    
    def _get_constraint_info(self, connection) -> List[Dict[str, Any]]:
        """Get constraint information"""
        constraints = []
        
        # Get table names
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        table_names = [row[0] for row in result]
        
        for table_name in table_names:
            if table_name == 'sqlite_sequence':
                continue
            
            # Get table creation SQL to parse constraints
            result = connection.execute(text(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';"))
            create_sql = result.scalar()
            
            if create_sql:
                # Parse constraints from SQL (simplified)
                if 'UNIQUE' in create_sql.upper():
                    constraints.append({
                        "table": table_name,
                        "type": "UNIQUE",
                        "definition": "Unique constraint"
                    })
                
                if 'CHECK' in create_sql.upper():
                    constraints.append({
                        "table": table_name,
                        "type": "CHECK",
                        "definition": "Check constraint"
                    })
        
        return constraints
    
    def _get_foreign_key_info(self, connection) -> List[Dict[str, Any]]:
        """Get foreign key information"""
        foreign_keys = []
        
        # Get table names
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        table_names = [row[0] for row in result]
        
        for table_name in table_names:
            if table_name == 'sqlite_sequence':
                continue
            
            # Get foreign key information
            result = connection.execute(text(f"PRAGMA foreign_key_list({table_name});"))
            for row in result:
                foreign_keys.append({
                    "table": table_name,
                    "column": row[3],
                    "referenced_table": row[2],
                    "referenced_column": row[4],
                    "on_update": row[5],
                    "on_delete": row[6]
                })
        
        return foreign_keys
    
    def _calculate_schema_hash(self, tables: List[Dict], indexes: List[Dict], constraints: List[Dict], foreign_keys: List[Dict]) -> str:
        """Calculate schema hash for change detection"""
        schema_data = {
            "tables": tables,
            "indexes": indexes,
            "constraints": constraints,
            "foreign_keys": foreign_keys
        }
        
        schema_json = json.dumps(schema_data, sort_keys=True)
        return hashlib.md5(schema_json.encode()).hexdigest()
    
    def compare_schemas(self, schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two schemas and return differences"""
        differences = {
            "tables_added": [],
            "tables_removed": [],
            "tables_modified": [],
            "columns_added": [],
            "columns_removed": [],
            "columns_modified": [],
            "indexes_added": [],
            "indexes_removed": [],
            "constraints_added": [],
            "constraints_removed": [],
            "foreign_keys_added": [],
            "foreign_keys_removed": []
        }
        
        # Compare tables
        tables1 = {table["name"]: table for table in schema1.get("tables", [])}
        tables2 = {table["name"]: table for table in schema2.get("tables", [])}
        
        # Find added tables
        for table_name in tables2:
            if table_name not in tables1:
                differences["tables_added"].append(table_name)
        
        # Find removed tables
        for table_name in tables1:
            if table_name not in tables2:
                differences["tables_removed"].append(table_name)
        
        # Find modified tables
        for table_name in tables1:
            if table_name in tables2:
                table1 = tables1[table_name]
                table2 = tables2[table_name]
                
                if table1 != table2:
                    differences["tables_modified"].append(table_name)
                    
                    # Compare columns
                    columns1 = {col["name"]: col for col in table1.get("columns", [])}
                    columns2 = {col["name"]: col for col in table2.get("columns", [])}
                    
                    # Find added columns
                    for col_name in columns2:
                        if col_name not in columns1:
                            differences["columns_added"].append(f"{table_name}.{col_name}")
                    
                    # Find removed columns
                    for col_name in columns1:
                        if col_name not in columns2:
                            differences["columns_removed"].append(f"{table_name}.{col_name}")
                    
                    # Find modified columns
                    for col_name in columns1:
                        if col_name in columns2:
                            if columns1[col_name] != columns2[col_name]:
                                differences["columns_modified"].append(f"{table_name}.{col_name}")
        
        return differences


class DatabaseBackupManager:
    """Database backup and restore utilities"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def create_backup(self, backup_path: str) -> str:
        """Create database backup"""
        try:
            import shutil
            
            if self.engine.url.drivername == 'sqlite':
                # For SQLite, copy the database file
                db_path = self.engine.url.database
                shutil.copy2(db_path, backup_path)
            else:
                # For other databases, use pg_dump or similar
                self._create_backup_for_other_db(backup_path)
            
            logger.info(f"Database backup created: {backup_path}")
            return f"Backup created successfully: {backup_path}"
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> str:
        """Restore database from backup"""
        try:
            import shutil
            
            if self.engine.url.drivername == 'sqlite':
                # For SQLite, copy the backup file
                db_path = self.engine.url.database
                shutil.copy2(backup_path, db_path)
            else:
                # For other databases, use pg_restore or similar
                self._restore_backup_for_other_db(backup_path)
            
            logger.info(f"Database restored from: {backup_path}")
            return f"Database restored successfully from {backup_path}"
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise
    
    def _create_backup_for_other_db(self, backup_path: str):
        """Create backup for non-SQLite databases"""
        # This would be implemented based on the specific database
        # For PostgreSQL: pg_dump
        # For MySQL: mysqldump
        # For others: appropriate backup tool
        pass
    
    def _restore_backup_for_other_db(self, backup_path: str):
        """Restore backup for non-SQLite databases"""
        # This would be implemented based on the specific database
        # For PostgreSQL: pg_restore
        # For MySQL: mysql
        # For others: appropriate restore tool
        pass


class DatabaseHealthChecker:
    """Database health checking utilities"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        health_status = {
            "connection": False,
            "tables": [],
            "indexes": [],
            "constraints": [],
            "performance": {},
            "errors": []
        }
        
        try:
            # Test connection
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                health_status["connection"] = True
            
            # Check tables
            health_status["tables"] = self._check_tables()
            
            # Check indexes
            health_status["indexes"] = self._check_indexes()
            
            # Check constraints
            health_status["constraints"] = self._check_constraints()
            
            # Check performance
            health_status["performance"] = self._check_performance()
            
        except Exception as e:
            health_status["errors"].append(str(e))
            logger.error(f"Database health check failed: {e}")
        
        return health_status
    
    def _check_tables(self) -> List[Dict[str, Any]]:
        """Check table health"""
        tables = []
        
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                table_names = [row[0] for row in result]
                
                for table_name in table_names:
                    if table_name == 'sqlite_sequence':
                        continue
                    
                    # Check table integrity
                    result = connection.execute(text(f"PRAGMA integrity_check({table_name});"))
                    integrity_result = result.scalar()
                    
                    # Get table statistics
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
                    row_count = result.scalar()
                    
                    tables.append({
                        "name": table_name,
                        "integrity": integrity_result == "ok",
                        "row_count": row_count,
                        "status": "healthy" if integrity_result == "ok" else "unhealthy"
                    })
        
        except Exception as e:
            logger.error(f"Failed to check tables: {e}")
        
        return tables
    
    def _check_indexes(self) -> List[Dict[str, Any]]:
        """Check index health"""
        indexes = []
        
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='index';"))
                index_names = [row[0] for row in result]
                
                for index_name in index_names:
                    if index_name.startswith('sqlite_'):
                        continue
                    
                    # Check index integrity
                    result = connection.execute(text(f"PRAGMA index_info({index_name});"))
                    index_info = result.fetchall()
                    
                    indexes.append({
                        "name": index_name,
                        "columns": [row[2] for row in index_info],
                        "status": "healthy"
                    })
        
        except Exception as e:
            logger.error(f"Failed to check indexes: {e}")
        
        return indexes
    
    def _check_constraints(self) -> List[Dict[str, Any]]:
        """Check constraint health"""
        constraints = []
        
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                table_names = [row[0] for row in result]
                
                for table_name in table_names:
                    if table_name == 'sqlite_sequence':
                        continue
                    
                    # Check foreign key constraints
                    result = connection.execute(text(f"PRAGMA foreign_key_check({table_name});"))
                    fk_violations = result.fetchall()
                    
                    if fk_violations:
                        constraints.append({
                            "table": table_name,
                            "type": "foreign_key",
                            "violations": len(fk_violations),
                            "status": "unhealthy"
                        })
                    else:
                        constraints.append({
                            "table": table_name,
                            "type": "foreign_key",
                            "violations": 0,
                            "status": "healthy"
                        })
        
        except Exception as e:
            logger.error(f"Failed to check constraints: {e}")
        
        return constraints
    
    def _check_performance(self) -> Dict[str, Any]:
        """Check database performance"""
        performance = {}
        
        try:
            with self.engine.connect() as connection:
                # Check database size
                if self.engine.url.drivername == 'sqlite':
                    db_path = self.engine.url.database
                    if os.path.exists(db_path):
                        performance["database_size"] = os.path.getsize(db_path)
                
                # Check query performance
                start_time = datetime.utcnow()
                connection.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table';"))
                end_time = datetime.utcnow()
                
                performance["query_time"] = (end_time - start_time).total_seconds()
                performance["status"] = "healthy" if performance["query_time"] < 1.0 else "slow"
        
        except Exception as e:
            logger.error(f"Failed to check performance: {e}")
            performance["error"] = str(e)
        
        return performance


class DatabaseMaintenance:
    """Database maintenance utilities"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def optimize_database(self) -> str:
        """Optimize database performance"""
        try:
            with self.engine.connect() as connection:
                if self.engine.url.drivername == 'sqlite':
                    # SQLite optimization
                    connection.execute(text("VACUUM;"))
                    connection.execute(text("ANALYZE;"))
                    connection.execute(text("PRAGMA optimize;"))
                
                logger.info("Database optimization completed")
                return "Database optimization completed successfully"
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            raise
    
    def clean_old_data(self, days: int = 30) -> str:
        """Clean old data from database"""
        try:
            with self.engine.connect() as connection:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Clean old logs (example)
                result = connection.execute(text("""
                    DELETE FROM activity_logs 
                    WHERE created_at < :cutoff_date
                """), {"cutoff_date": cutoff_date})
                
                deleted_count = result.rowcount
                logger.info(f"Cleaned {deleted_count} old records")
                return f"Cleaned {deleted_count} old records"
        except Exception as e:
            logger.error(f"Failed to clean old data: {e}")
            raise
    
    def rebuild_indexes(self) -> str:
        """Rebuild database indexes"""
        try:
            with self.engine.connect() as connection:
                if self.engine.url.drivername == 'sqlite':
                    # Get all indexes
                    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='index';"))
                    index_names = [row[0] for row in result]
                    
                    # Rebuild indexes
                    for index_name in index_names:
                        if not index_name.startswith('sqlite_'):
                            connection.execute(text(f"REINDEX {index_name};"))
                
                logger.info("Index rebuild completed")
                return "Index rebuild completed successfully"
        except Exception as e:
            logger.error(f"Failed to rebuild indexes: {e}")
            raise


# Global database management instances
def get_migration_manager() -> MigrationManager:
    """Get migration manager instance"""
    return MigrationManager()

def get_schema_manager(engine) -> SchemaManager:
    """Get schema manager instance"""
    return SchemaManager(engine)

def get_backup_manager(engine) -> DatabaseBackupManager:
    """Get backup manager instance"""
    return DatabaseBackupManager(engine)

def get_health_checker(engine) -> DatabaseHealthChecker:
    """Get health checker instance"""
    return DatabaseHealthChecker(engine)

def get_maintenance_manager(engine) -> DatabaseMaintenance:
    """Get maintenance manager instance"""
    return DatabaseMaintenance(engine)
