"""
Data Export and Import System for Wren API

This module provides comprehensive data export, import, and migration
utilities for the Wren API.
"""

import json
import csv
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union, Callable, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class ExportFormat(Enum):
    """Export format enumeration"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    EXCEL = "excel"
    SQL = "sql"


class ImportFormat(Enum):
    """Import format enumeration"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    EXCEL = "excel"
    SQL = "sql"


@dataclass
class ExportConfig:
    """Export configuration"""
    format: ExportFormat
    include_metadata: bool = True
    compress: bool = False
    filter_fields: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    batch_size: int = 1000
    custom_transformer: Optional[Callable] = None


@dataclass
class ImportConfig:
    """Import configuration"""
    format: ImportFormat
    validate_data: bool = True
    skip_errors: bool = False
    batch_size: int = 1000
    custom_validator: Optional[Callable] = None
    custom_transformer: Optional[Callable] = None


class DataExporter:
    """Data export utilities"""
    
    def __init__(self):
        self.export_handlers = {
            ExportFormat.JSON: self._export_to_json,
            ExportFormat.CSV: self._export_to_csv,
            ExportFormat.XML: self._export_to_xml,
            ExportFormat.SQL: self._export_to_sql
        }
        self.export_history = []
    
    def export_data(self, data: List[Dict[str, Any]], config: ExportConfig, 
                   output_path: str) -> Dict[str, Any]:
        """Export data to specified format"""
        try:
            start_time = datetime.utcnow()
            
            # Apply filters and transformations
            filtered_data = self._apply_filters(data, config)
            transformed_data = self._apply_transformations(filtered_data, config)
            
            # Export to specified format
            if config.format in self.export_handlers:
                result = self.export_handlers[config.format](transformed_data, output_path, config)
            else:
                raise ValueError(f"Unsupported export format: {config.format}")
            
            # Record export history
            export_record = {
                "timestamp": start_time,
                "format": config.format.value,
                "output_path": output_path,
                "record_count": len(transformed_data),
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "status": "success"
            }
            self.export_history.append(export_record)
            
            logger.info(f"Data exported successfully: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "record_count": len(transformed_data),
                "format": config.format.value,
                "duration": export_record["duration"]
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "output_path": output_path
            }
    
    def _apply_filters(self, data: List[Dict[str, Any]], config: ExportConfig) -> List[Dict[str, Any]]:
        """Apply filters to data"""
        filtered_data = data
        
        # Apply field filters
        if config.filter_fields:
            filtered_data = [
                {field: record.get(field) for field in config.filter_fields if field in record}
                for record in filtered_data
            ]
        
        # Apply date range filter
        if config.date_range:
            start_date = config.date_range.get("start")
            end_date = config.date_range.get("end")
            
            if start_date or end_date:
                filtered_data = [
                    record for record in filtered_data
                    if self._is_in_date_range(record, start_date, end_date)
                ]
        
        return filtered_data
    
    def _apply_transformations(self, data: List[Dict[str, Any]], config: ExportConfig) -> List[Dict[str, Any]]:
        """Apply transformations to data"""
        if config.custom_transformer:
            return [config.custom_transformer(record) for record in data]
        return data
    
    def _is_in_date_range(self, record: Dict[str, Any], start_date: datetime, end_date: datetime) -> bool:
        """Check if record is in date range"""
        # Look for common date fields
        date_fields = ["created_at", "updated_at", "date", "timestamp"]
        
        for field in date_fields:
            if field in record:
                try:
                    record_date = datetime.fromisoformat(record[field].replace('Z', '+00:00'))
                    if start_date and record_date < start_date:
                        return False
                    if end_date and record_date > end_date:
                        return False
                    return True
                except (ValueError, TypeError):
                    continue
        
        return True  # Include if no date field found
    
    def _export_to_json(self, data: List[Dict[str, Any]], output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Export data to JSON format"""
        export_data = {
            "metadata": {
                "export_timestamp": datetime.utcnow().isoformat(),
                "record_count": len(data),
                "format": "json"
            } if config.include_metadata else None,
            "data": data
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return {"success": True}
    
    def _export_to_csv(self, data: List[Dict[str, Any]], output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Export data to CSV format"""
        if not data:
            return {"success": True}
        
        fieldnames = set()
        for record in data:
            fieldnames.update(record.keys())
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
            writer.writeheader()
            writer.writerows(data)
        
        return {"success": True}
    
    def _export_to_xml(self, data: List[Dict[str, Any]], output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Export data to XML format"""
        root = ET.Element("data")
        
        if config.include_metadata:
            metadata = ET.SubElement(root, "metadata")
            ET.SubElement(metadata, "export_timestamp").text = datetime.utcnow().isoformat()
            ET.SubElement(metadata, "record_count").text = str(len(data))
            ET.SubElement(metadata, "format").text = "xml"
        
        for record in data:
            record_elem = ET.SubElement(root, "record")
            for key, value in record.items():
                elem = ET.SubElement(record_elem, key)
                elem.text = str(value)
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        return {"success": True}
    
    def _export_to_sql(self, data: List[Dict[str, Any]], output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Export data to SQL format"""
        if not data:
            return {"success": True}
        
        # Get table name from config or use default
        table_name = config.metadata.get("table_name", "exported_data")
        
        sql_statements = []
        
        # Create table statement
        fieldnames = set()
        for record in data:
            fieldnames.update(record.keys())
        
        create_table = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        create_table += "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        for field in sorted(fieldnames):
            create_table += f"    {field} TEXT,\n"
        create_table = create_table.rstrip(",\n") + "\n);"
        sql_statements.append(create_table)
        
        # Insert statements
        for record in data:
            fields = list(record.keys())
            values = [str(record[field]) for field in fields]
            
            insert_sql = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({', '.join(['?' for _ in values])});"
            sql_statements.append(insert_sql)
        
        with open(output_path, 'w') as f:
            f.write("\n".join(sql_statements))
        
        return {"success": True}
    
    def get_export_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get export history"""
        return self.export_history[-limit:]


class DataImporter:
    """Data import utilities"""
    
    def __init__(self):
        self.import_handlers = {
            ImportFormat.JSON: self._import_from_json,
            ImportFormat.CSV: self._import_from_csv,
            ImportFormat.XML: self._import_from_xml,
            ImportFormat.SQL: self._import_from_sql
        }
        self.import_history = []
    
    def import_data(self, input_path: str, config: ImportConfig) -> Dict[str, Any]:
        """Import data from specified format"""
        try:
            start_time = datetime.utcnow()
            
            # Check if file exists
            if not Path(input_path).exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Import data
            if config.format in self.import_handlers:
                data = self.import_handlers[config.format](input_path, config)
            else:
                raise ValueError(f"Unsupported import format: {config.format}")
            
            # Validate data if required
            if config.validate_data:
                validation_result = self._validate_data(data, config)
                if not validation_result["valid"] and not config.skip_errors:
                    raise ValueError(f"Data validation failed: {validation_result['errors']}")
            
            # Apply transformations
            if config.custom_transformer:
                data = [config.custom_transformer(record) for record in data]
            
            # Record import history
            import_record = {
                "timestamp": start_time,
                "format": config.format.value,
                "input_path": input_path,
                "record_count": len(data),
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "status": "success"
            }
            self.import_history.append(import_record)
            
            logger.info(f"Data imported successfully: {input_path}")
            return {
                "success": True,
                "record_count": len(data),
                "format": config.format.value,
                "duration": import_record["duration"],
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "input_path": input_path
            }
    
    def _import_from_json(self, input_path: str, config: ImportConfig) -> List[Dict[str, Any]]:
        """Import data from JSON format"""
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, dict):
            if "data" in data:
                return data["data"]
            else:
                return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid JSON structure")
    
    def _import_from_csv(self, input_path: str, config: ImportConfig) -> List[Dict[str, Any]]:
        """Import data from CSV format"""
        data = []
        
        with open(input_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        
        return data
    
    def _import_from_xml(self, input_path: str, config: ImportConfig) -> List[Dict[str, Any]]:
        """Import data from XML format"""
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        data = []
        for record_elem in root.findall("record"):
            record = {}
            for child in record_elem:
                record[child.tag] = child.text
            data.append(record)
        
        return data
    
    def _import_from_sql(self, input_path: str, config: ImportConfig) -> List[Dict[str, Any]]:
        """Import data from SQL format"""
        # This is a simplified implementation
        # In practice, you would need a SQL parser
        with open(input_path, 'r') as f:
            sql_content = f.read()
        
        # Extract INSERT statements (simplified)
        data = []
        lines = sql_content.split('\n')
        
        for line in lines:
            if line.strip().upper().startswith('INSERT INTO'):
                # Parse INSERT statement (simplified)
                # This would need proper SQL parsing in production
                pass
        
        return data
    
    def _validate_data(self, data: List[Dict[str, Any]], config: ImportConfig) -> Dict[str, Any]:
        """Validate imported data"""
        errors = []
        
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                errors.append(f"Record {i} is not a dictionary")
                continue
            
            # Custom validation
            if config.custom_validator:
                try:
                    if not config.custom_validator(record):
                        errors.append(f"Record {i} failed custom validation")
                except Exception as e:
                    errors.append(f"Record {i} validation error: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "record_count": len(data)
        }
    
    def get_import_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get import history"""
        return self.import_history[-limit:]


class DataMigrationManager:
    """Data migration management"""
    
    def __init__(self):
        self.migration_history = []
        self.migration_scripts = {}
    
    def register_migration(self, version: str, script: Callable):
        """Register migration script"""
        self.migration_scripts[version] = script
        logger.info(f"Migration script registered for version: {version}")
    
    def run_migration(self, version: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run migration script"""
        if version not in self.migration_scripts:
            return {
                "success": False,
                "error": f"Migration script not found for version: {version}"
            }
        
        try:
            start_time = datetime.utcnow()
            
            script = self.migration_scripts[version]
            migrated_data = script(data)
            
            # Record migration
            migration_record = {
                "version": version,
                "timestamp": start_time,
                "record_count": len(migrated_data),
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "status": "success"
            }
            self.migration_history.append(migration_record)
            
            logger.info(f"Migration completed for version: {version}")
            return {
                "success": True,
                "migrated_data": migrated_data,
                "record_count": len(migrated_data),
                "duration": migration_record["duration"]
            }
            
        except Exception as e:
            logger.error(f"Migration failed for version {version}: {e}")
            return {
                "success": False,
                "error": str(e),
                "version": version
            }
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        return self.migration_history


# Global data export and import instances
def get_data_exporter() -> DataExporter:
    """Get data exporter instance"""
    return DataExporter()

def get_data_importer() -> DataImporter:
    """Get data importer instance"""
    return DataImporter()

def get_migration_manager() -> DataMigrationManager:
    """Get migration manager instance"""
    return DataMigrationManager()
