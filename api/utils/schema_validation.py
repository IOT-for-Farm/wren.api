"""
Schema Validation and Management for Wren API

This module provides comprehensive schema validation, data integrity checking,
and schema evolution utilities for the Wren API database.
"""

import json
import hashlib
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.inspection import inspect
from pydantic import BaseModel, Field, validator
import logging

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)


class SchemaValidator:
    """Database schema validation utilities"""
    
    def __init__(self, engine):
        self.engine = engine
        self.metadata = MetaData()
    
    def validate_schema_integrity(self) -> Dict[str, Any]:
        """Validate database schema integrity"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "tables": {},
            "constraints": {},
            "indexes": {},
            "foreign_keys": {}
        }
        
        try:
            with self.engine.connect() as connection:
                # Validate tables
                validation_result["tables"] = self._validate_tables(connection)
                
                # Validate constraints
                validation_result["constraints"] = self._validate_constraints(connection)
                
                # Validate indexes
                validation_result["indexes"] = self._validate_indexes(connection)
                
                # Validate foreign keys
                validation_result["foreign_keys"] = self._validate_foreign_keys(connection)
                
                # Check for errors
                if validation_result["errors"]:
                    validation_result["is_valid"] = False
                
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Schema validation failed: {str(e)}")
            logger.error(f"Schema validation failed: {e}")
        
        return validation_result
    
    def _validate_tables(self, connection) -> Dict[str, Any]:
        """Validate table structure"""
        tables_validation = {
            "valid": [],
            "invalid": [],
            "missing": []
        }
        
        try:
            # Get expected tables from models
            expected_tables = self._get_expected_tables()
            
            # Get actual tables from database
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            actual_tables = [row[0] for row in result]
            
            # Check for missing tables
            for expected_table in expected_tables:
                if expected_table not in actual_tables:
                    tables_validation["missing"].append(expected_table)
            
            # Validate existing tables
            for table_name in actual_tables:
                if table_name == 'sqlite_sequence':
                    continue
                
                if self._validate_table_structure(connection, table_name):
                    tables_validation["valid"].append(table_name)
                else:
                    tables_validation["invalid"].append(table_name)
        
        except Exception as e:
            logger.error(f"Failed to validate tables: {e}")
        
        return tables_validation
    
    def _validate_table_structure(self, connection, table_name: str) -> bool:
        """Validate individual table structure"""
        try:
            # Check table integrity
            result = connection.execute(text(f"PRAGMA integrity_check({table_name});"))
            integrity_result = result.scalar()
            
            if integrity_result != "ok":
                return False
            
            # Check table structure
            result = connection.execute(text(f"PRAGMA table_info({table_name});"))
            columns = result.fetchall()
            
            if not columns:
                return False
            
            # Validate column types and constraints
            for column in columns:
                if not self._validate_column(column):
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to validate table {table_name}: {e}")
            return False
    
    def _validate_column(self, column) -> bool:
        """Validate column structure"""
        try:
            # Check if column has valid type
            if not column[2]:  # type
                return False
            
            # Check if column has valid name
            if not column[1]:  # name
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to validate column: {e}")
            return False
    
    def _validate_constraints(self, connection) -> Dict[str, Any]:
        """Validate database constraints"""
        constraints_validation = {
            "valid": [],
            "invalid": [],
            "violations": []
        }
        
        try:
            # Get table names
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            table_names = [row[0] for row in result]
            
            for table_name in table_names:
                if table_name == 'sqlite_sequence':
                    continue
                
                # Check foreign key constraints
                result = connection.execute(text(f"PRAGMA foreign_key_check({table_name});"))
                fk_violations = result.fetchall()
                
                if fk_violations:
                    constraints_validation["violations"].extend([
                        {
                            "table": table_name,
                            "type": "foreign_key",
                            "violation": str(violation)
                        }
                        for violation in fk_violations
                    ])
                else:
                    constraints_validation["valid"].append(table_name)
        
        except Exception as e:
            logger.error(f"Failed to validate constraints: {e}")
        
        return constraints_validation
    
    def _validate_indexes(self, connection) -> Dict[str, Any]:
        """Validate database indexes"""
        indexes_validation = {
            "valid": [],
            "invalid": [],
            "missing": []
        }
        
        try:
            # Get expected indexes
            expected_indexes = self._get_expected_indexes()
            
            # Get actual indexes
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='index';"))
            actual_indexes = [row[0] for row in result]
            
            # Check for missing indexes
            for expected_index in expected_indexes:
                if expected_index not in actual_indexes:
                    indexes_validation["missing"].append(expected_index)
            
            # Validate existing indexes
            for index_name in actual_indexes:
                if index_name.startswith('sqlite_'):
                    continue
                
                if self._validate_index_structure(connection, index_name):
                    indexes_validation["valid"].append(index_name)
                else:
                    indexes_validation["invalid"].append(index_name)
        
        except Exception as e:
            logger.error(f"Failed to validate indexes: {e}")
        
        return indexes_validation
    
    def _validate_index_structure(self, connection, index_name: str) -> bool:
        """Validate individual index structure"""
        try:
            # Check index info
            result = connection.execute(text(f"PRAGMA index_info({index_name});"))
            index_info = result.fetchall()
            
            if not index_info:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to validate index {index_name}: {e}")
            return False
    
    def _validate_foreign_keys(self, connection) -> Dict[str, Any]:
        """Validate foreign key relationships"""
        fk_validation = {
            "valid": [],
            "invalid": [],
            "orphaned": []
        }
        
        try:
            # Get table names
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            table_names = [row[0] for row in result]
            
            for table_name in table_names:
                if table_name == 'sqlite_sequence':
                    continue
                
                # Get foreign key info
                result = connection.execute(text(f"PRAGMA foreign_key_list({table_name});"))
                fk_info = result.fetchall()
                
                for fk in fk_info:
                    if self._validate_foreign_key(connection, table_name, fk):
                        fk_validation["valid"].append(f"{table_name}.{fk[3]}")
                    else:
                        fk_validation["invalid"].append(f"{table_name}.{fk[3]}")
        
        except Exception as e:
            logger.error(f"Failed to validate foreign keys: {e}")
        
        return fk_validation
    
    def _validate_foreign_key(self, connection, table_name: str, fk_info) -> bool:
        """Validate individual foreign key"""
        try:
            referenced_table = fk_info[2]
            referenced_column = fk_info[4]
            
            # Check if referenced table exists
            result = connection.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{referenced_table}';"))
            if not result.fetchone():
                return False
            
            # Check if referenced column exists
            result = connection.execute(text(f"PRAGMA table_info({referenced_table});"))
            columns = [row[1] for row in result]
            
            if referenced_column not in columns:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to validate foreign key: {e}")
            return False
    
    def _get_expected_tables(self) -> List[str]:
        """Get list of expected tables from models"""
        # This would be populated based on your actual models
        expected_tables = [
            "users",
            "organizations",
            "products",
            "customers",
            "vendors",
            "invoices",
            "orders",
            "payments",
            "categories",
            "tags",
            "files",
            "activity_logs"
        ]
        return expected_tables
    
    def _get_expected_indexes(self) -> List[str]:
        """Get list of expected indexes"""
        # This would be populated based on your actual indexes
        expected_indexes = [
            "ix_users_email",
            "ix_users_username",
            "ix_organizations_slug",
            "ix_products_slug",
            "ix_products_organization_id",
            "ix_customers_email",
            "ix_vendors_company_name",
            "ix_invoices_invoice_number",
            "ix_orders_order_number",
            "ix_payments_transaction_id"
        ]
        return expected_indexes


class DataIntegrityChecker:
    """Data integrity checking utilities"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity across all tables"""
        integrity_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "tables": {},
            "relationships": {},
            "constraints": {}
        }
        
        try:
            with self.engine.connect() as connection:
                # Check table data integrity
                integrity_result["tables"] = self._check_table_data_integrity(connection)
                
                # Check relationship integrity
                integrity_result["relationships"] = self._check_relationship_integrity(connection)
                
                # Check constraint integrity
                integrity_result["constraints"] = self._check_constraint_integrity(connection)
                
                # Check for errors
                if integrity_result["errors"]:
                    integrity_result["is_valid"] = False
                
        except Exception as e:
            integrity_result["is_valid"] = False
            integrity_result["errors"].append(f"Data integrity check failed: {str(e)}")
            logger.error(f"Data integrity check failed: {e}")
        
        return integrity_result
    
    def _check_table_data_integrity(self, connection) -> Dict[str, Any]:
        """Check data integrity for each table"""
        tables_integrity = {}
        
        try:
            # Get table names
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            table_names = [row[0] for row in result]
            
            for table_name in table_names:
                if table_name == 'sqlite_sequence':
                    continue
                
                table_integrity = {
                    "row_count": 0,
                    "null_violations": [],
                    "duplicate_violations": [],
                    "type_violations": [],
                    "is_valid": True
                }
                
                # Get row count
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
                table_integrity["row_count"] = result.scalar()
                
                # Check for null violations in required fields
                table_integrity["null_violations"] = self._check_null_violations(connection, table_name)
                
                # Check for duplicate violations
                table_integrity["duplicate_violations"] = self._check_duplicate_violations(connection, table_name)
                
                # Check for type violations
                table_integrity["type_violations"] = self._check_type_violations(connection, table_name)
                
                # Determine if table is valid
                if (table_integrity["null_violations"] or 
                    table_integrity["duplicate_violations"] or 
                    table_integrity["type_violations"]):
                    table_integrity["is_valid"] = False
                
                tables_integrity[table_name] = table_integrity
        
        except Exception as e:
            logger.error(f"Failed to check table data integrity: {e}")
        
        return tables_integrity
    
    def _check_null_violations(self, connection, table_name: str) -> List[Dict[str, Any]]:
        """Check for null violations in required fields"""
        violations = []
        
        try:
            # Get table info
            result = connection.execute(text(f"PRAGMA table_info({table_name});"))
            columns = result.fetchall()
            
            for column in columns:
                column_name = column[1]
                is_nullable = not column[3]  # not_null flag
                
                if not is_nullable:
                    # Check for null values
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL;"))
                    null_count = result.scalar()
                    
                    if null_count > 0:
                        violations.append({
                            "column": column_name,
                            "null_count": null_count,
                            "type": "null_violation"
                        })
        
        except Exception as e:
            logger.error(f"Failed to check null violations for {table_name}: {e}")
        
        return violations
    
    def _check_duplicate_violations(self, connection, table_name: str) -> List[Dict[str, Any]]:
        """Check for duplicate violations in unique fields"""
        violations = []
        
        try:
            # Get table info
            result = connection.execute(text(f"PRAGMA table_info({table_name});"))
            columns = result.fetchall()
            
            for column in columns:
                column_name = column[1]
                is_primary_key = column[5]  # primary key flag
                
                if is_primary_key:
                    # Check for duplicate primary keys
                    result = connection.execute(text(f"SELECT {column_name}, COUNT(*) FROM {table_name} GROUP BY {column_name} HAVING COUNT(*) > 1;"))
                    duplicates = result.fetchall()
                    
                    if duplicates:
                        violations.append({
                            "column": column_name,
                            "duplicate_count": len(duplicates),
                            "type": "duplicate_violation"
                        })
        
        except Exception as e:
            logger.error(f"Failed to check duplicate violations for {table_name}: {e}")
        
        return violations
    
    def _check_type_violations(self, connection, table_name: str) -> List[Dict[str, Any]]:
        """Check for type violations"""
        violations = []
        
        try:
            # Get table info
            result = connection.execute(text(f"PRAGMA table_info({table_name});"))
            columns = result.fetchall()
            
            for column in columns:
                column_name = column[1]
                column_type = column[2]
                
                # Check for type violations based on column type
                if column_type.upper() == 'INTEGER':
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NOT NULL AND {column_name} != CAST({column_name} AS INTEGER);"))
                    type_violations = result.scalar()
                    
                    if type_violations > 0:
                        violations.append({
                            "column": column_name,
                            "expected_type": "INTEGER",
                            "violation_count": type_violations,
                            "type": "type_violation"
                        })
        
        except Exception as e:
            logger.error(f"Failed to check type violations for {table_name}: {e}")
        
        return violations
    
    def _check_relationship_integrity(self, connection) -> Dict[str, Any]:
        """Check relationship integrity"""
        relationship_integrity = {
            "valid": [],
            "invalid": [],
            "orphaned": []
        }
        
        try:
            # Get table names
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            table_names = [row[0] for row in result]
            
            for table_name in table_names:
                if table_name == 'sqlite_sequence':
                    continue
                
                # Check foreign key relationships
                result = connection.execute(text(f"PRAGMA foreign_key_list({table_name});"))
                fk_info = result.fetchall()
                
                for fk in fk_info:
                    if self._check_foreign_key_integrity(connection, table_name, fk):
                        relationship_integrity["valid"].append(f"{table_name}.{fk[3]}")
                    else:
                        relationship_integrity["invalid"].append(f"{table_name}.{fk[3]}")
        
        except Exception as e:
            logger.error(f"Failed to check relationship integrity: {e}")
        
        return relationship_integrity
    
    def _check_foreign_key_integrity(self, connection, table_name: str, fk_info) -> bool:
        """Check individual foreign key integrity"""
        try:
            referenced_table = fk_info[2]
            referenced_column = fk_info[4]
            local_column = fk_info[3]
            
            # Check for orphaned records
            result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name} t1 LEFT JOIN {referenced_table} t2 ON t1.{local_column} = t2.{referenced_column} WHERE t1.{local_column} IS NOT NULL AND t2.{referenced_column} IS NULL;"))
            orphaned_count = result.scalar()
            
            return orphaned_count == 0
        
        except Exception as e:
            logger.error(f"Failed to check foreign key integrity: {e}")
            return False
    
    def _check_constraint_integrity(self, connection) -> Dict[str, Any]:
        """Check constraint integrity"""
        constraint_integrity = {
            "valid": [],
            "invalid": [],
            "violations": []
        }
        
        try:
            # Get table names
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            table_names = [row[0] for row in result]
            
            for table_name in table_names:
                if table_name == 'sqlite_sequence':
                    continue
                
                # Check foreign key constraints
                result = connection.execute(text(f"PRAGMA foreign_key_check({table_name});"))
                fk_violations = result.fetchall()
                
                if fk_violations:
                    constraint_integrity["violations"].extend([
                        {
                            "table": table_name,
                            "type": "foreign_key",
                            "violation": str(violation)
                        }
                        for violation in fk_violations
                    ])
                else:
                    constraint_integrity["valid"].append(table_name)
        
        except Exception as e:
            logger.error(f"Failed to check constraint integrity: {e}")
        
        return constraint_integrity


class SchemaEvolution:
    """Schema evolution and migration utilities"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def analyze_schema_changes(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze schema changes between versions"""
        changes = {
            "breaking_changes": [],
            "non_breaking_changes": [],
            "additions": [],
            "removals": [],
            "modifications": [],
            "migration_required": False
        }
        
        try:
            # Compare tables
            old_tables = {table["name"]: table for table in old_schema.get("tables", [])}
            new_tables = {table["name"]: table for table in new_schema.get("tables", [])}
            
            # Find added tables
            for table_name in new_tables:
                if table_name not in old_tables:
                    changes["additions"].append(f"Table: {table_name}")
                    changes["non_breaking_changes"].append(f"Added table: {table_name}")
            
            # Find removed tables
            for table_name in old_tables:
                if table_name not in new_tables:
                    changes["removals"].append(f"Table: {table_name}")
                    changes["breaking_changes"].append(f"Removed table: {table_name}")
                    changes["migration_required"] = True
            
            # Find modified tables
            for table_name in old_tables:
                if table_name in new_tables:
                    table_changes = self._compare_tables(old_tables[table_name], new_tables[table_name])
                    if table_changes:
                        changes["modifications"].extend(table_changes)
                        if any(change.get("breaking", False) for change in table_changes):
                            changes["migration_required"] = True
            
            # Compare indexes
            old_indexes = {index["name"]: index for index in old_schema.get("indexes", [])}
            new_indexes = {index["name"]: index for index in new_schema.get("indexes", [])}
            
            # Find added indexes
            for index_name in new_indexes:
                if index_name not in old_indexes:
                    changes["additions"].append(f"Index: {index_name}")
                    changes["non_breaking_changes"].append(f"Added index: {index_name}")
            
            # Find removed indexes
            for index_name in old_indexes:
                if index_name not in new_indexes:
                    changes["removals"].append(f"Index: {index_name}")
                    changes["breaking_changes"].append(f"Removed index: {index_name}")
                    changes["migration_required"] = True
        
        except Exception as e:
            logger.error(f"Failed to analyze schema changes: {e}")
            changes["error"] = str(e)
        
        return changes
    
    def _compare_tables(self, old_table: Dict[str, Any], new_table: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare two table schemas"""
        changes = []
        
        try:
            # Compare columns
            old_columns = {col["name"]: col for col in old_table.get("columns", [])}
            new_columns = {col["name"]: col for col in new_table.get("columns", [])}
            
            # Find added columns
            for col_name in new_columns:
                if col_name not in old_columns:
                    changes.append({
                        "type": "column_added",
                        "table": old_table["name"],
                        "column": col_name,
                        "breaking": False
                    })
            
            # Find removed columns
            for col_name in old_columns:
                if col_name not in new_columns:
                    changes.append({
                        "type": "column_removed",
                        "table": old_table["name"],
                        "column": col_name,
                        "breaking": True
                    })
            
            # Find modified columns
            for col_name in old_columns:
                if col_name in new_columns:
                    if old_columns[col_name] != new_columns[col_name]:
                        changes.append({
                            "type": "column_modified",
                            "table": old_table["name"],
                            "column": col_name,
                            "breaking": self._is_breaking_column_change(old_columns[col_name], new_columns[col_name])
                        })
        
        except Exception as e:
            logger.error(f"Failed to compare tables: {e}")
        
        return changes
    
    def _is_breaking_column_change(self, old_column: Dict[str, Any], new_column: Dict[str, Any]) -> bool:
        """Check if column change is breaking"""
        # Type changes are breaking
        if old_column.get("type") != new_column.get("type"):
            return True
        
        # Adding NOT NULL constraint is breaking
        if not old_column.get("not_null") and new_column.get("not_null"):
            return True
        
        # Removing default value is breaking
        if old_column.get("default_value") and not new_column.get("default_value"):
            return True
        
        return False
    
    def generate_migration_script(self, changes: Dict[str, Any]) -> str:
        """Generate migration script for schema changes"""
        migration_script = "-- Migration script generated automatically\n"
        migration_script += f"-- Generated at: {datetime.utcnow().isoformat()}\n\n"
        
        try:
            # Handle table additions
            for addition in changes.get("additions", []):
                if addition.startswith("Table:"):
                    table_name = addition.replace("Table:", "").strip()
                    migration_script += f"-- Add table: {table_name}\n"
                    migration_script += f"CREATE TABLE {table_name} (\n"
                    migration_script += "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                    migration_script += "    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n"
                    migration_script += "    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP\n"
                    migration_script += ");\n\n"
            
            # Handle table removals
            for removal in changes.get("removals", []):
                if removal.startswith("Table:"):
                    table_name = removal.replace("Table:", "").strip()
                    migration_script += f"-- Remove table: {table_name}\n"
                    migration_script += f"DROP TABLE IF EXISTS {table_name};\n\n"
            
            # Handle column additions
            for modification in changes.get("modifications", []):
                if modification["type"] == "column_added":
                    migration_script += f"-- Add column: {modification['table']}.{modification['column']}\n"
                    migration_script += f"ALTER TABLE {modification['table']} ADD COLUMN {modification['column']} TEXT;\n\n"
                
                elif modification["type"] == "column_removed":
                    migration_script += f"-- Remove column: {modification['table']}.{modification['column']}\n"
                    migration_script += f"-- Note: SQLite doesn't support DROP COLUMN directly\n"
                    migration_script += f"-- Manual migration required for {modification['table']}.{modification['column']}\n\n"
                
                elif modification["type"] == "column_modified":
                    migration_script += f"-- Modify column: {modification['table']}.{modification['column']}\n"
                    migration_script += f"-- Note: SQLite doesn't support ALTER COLUMN directly\n"
                    migration_script += f"-- Manual migration required for {modification['table']}.{modification['column']}\n\n"
            
            # Handle index additions
            for addition in changes.get("additions", []):
                if addition.startswith("Index:"):
                    index_name = addition.replace("Index:", "").strip()
                    migration_script += f"-- Add index: {index_name}\n"
                    migration_script += f"CREATE INDEX {index_name} ON table_name (column_name);\n\n"
            
            # Handle index removals
            for removal in changes.get("removals", []):
                if removal.startswith("Index:"):
                    index_name = removal.replace("Index:", "").strip()
                    migration_script += f"-- Remove index: {index_name}\n"
                    migration_script += f"DROP INDEX IF EXISTS {index_name};\n\n"
        
        except Exception as e:
            logger.error(f"Failed to generate migration script: {e}")
            migration_script += f"-- Error generating migration script: {str(e)}\n"
        
        return migration_script


# Global schema management instances
def get_schema_validator(engine) -> SchemaValidator:
    """Get schema validator instance"""
    return SchemaValidator(engine)

def get_data_integrity_checker(engine) -> DataIntegrityChecker:
    """Get data integrity checker instance"""
    return DataIntegrityChecker(engine)

def get_schema_evolution(engine) -> SchemaEvolution:
    """Get schema evolution instance"""
    return SchemaEvolution(engine)
