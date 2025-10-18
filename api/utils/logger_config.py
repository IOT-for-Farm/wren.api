"""
Logging Configuration Utilities

Enhanced logging configuration and monitoring setup.
"""

import logging
import sys
from typing import Dict, Any
from datetime import datetime


class LoggerConfig:
    """Configures application logging with structured output."""
    
    def __init__(self):
        """Initialize logger configuration."""
        self.loggers = {}
    
    def setup_logger(self, name: str, level: str = "INFO", 
                    format_string: str = None) -> logging.Logger:
        """Setup structured logger with custom formatting."""
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(format_string)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        self.loggers[name] = logger
        return logger
    
    def get_structured_logger(self, name: str) -> logging.Logger:
        """Get logger with structured JSON output."""
        logger = logging.getLogger(f"{name}_structured")
        if logger not in self.loggers:
            self.setup_logger(f"{name}_structured")
        return logger
    
    def log_structured(self, logger: logging.Logger, level: str, 
                      message: str, **kwargs) -> None:
        """Log structured data with additional context."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level.upper(),
            "message": message,
            **kwargs
        }
        
        getattr(logger, level.lower())(f"STRUCTURED: {log_data}")
    
    def setup_file_logging(self, logger_name: str, filename: str, 
                          level: str = "INFO") -> logging.Logger:
        """Setup file logging for specific logger."""
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))
        
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(getattr(logging, level.upper()))
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger
