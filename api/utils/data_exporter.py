"""
Data Export Utilities

Utilities for exporting data in various formats.
"""

import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import io


class DataExporter:
    """Exports data in various formats."""
    
    def __init__(self):
        """Initialize data exporter."""
        self.supported_formats = ["json", "csv", "xml"]
    
    def export_to_json(self, data: List[Dict[str, Any]], 
                      filename: str = None) -> str:
        """Export data to JSON format."""
        if filename is None:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "record_count": len(data),
            "data": data
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename
    
    def export_to_csv(self, data: List[Dict[str, Any]], 
                     filename: str = None) -> str:
        """Export data to CSV format."""
        if not data:
            return None
        
        if filename is None:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Get all fieldnames from first record
        fieldnames = list(data[0].keys()) if data else []
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return filename
    
    def export_to_xml(self, data: List[Dict[str, Any]], 
                      filename: str = None, root_name: str = "data") -> str:
        """Export data to XML format."""
        if filename is None:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        
        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<{root_name}>\n'
        xml_content += f'  <exported_at>{datetime.now().isoformat()}</exported_at>\n'
        xml_content += f'  <record_count>{len(data)}</record_count>\n'
        xml_content += '  <records>\n'
        
        for i, record in enumerate(data):
            xml_content += f'    <record_{i}>\n'
            for key, value in record.items():
                xml_content += f'      <{key}>{value}</{key}>\n'
            xml_content += f'    </record_{i}>\n'
        
        xml_content += '  </records>\n'
        xml_content += f'</{root_name}>\n'
        
        with open(filename, 'w') as f:
            f.write(xml_content)
        
        return filename
    
    def get_export_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of data to be exported."""
        if not data:
            return {"record_count": 0, "fields": []}
        
        fields = list(data[0].keys()) if data else []
        return {
            "record_count": len(data),
            "fields": fields,
            "exported_at": datetime.now().isoformat()
        }
