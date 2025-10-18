"""
Batch Processing Utilities

Process large datasets in batches for better performance.
"""

from typing import List, Any, Callable, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processes data in batches for better performance."""
    
    def __init__(self, batch_size: int = 100):
        """Initialize batch processor."""
        self.batch_size = batch_size
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = None
    
    def process_batches(self, data: List[Any], processor_func: Callable, 
                       progress_callback: Callable = None) -> Dict[str, Any]:
        """Process data in batches."""
        self.start_time = datetime.now()
        self.processed_count = 0
        self.failed_count = 0
        
        total_items = len(data)
        batches = self._create_batches(data)
        
        logger.info(f"Processing {total_items} items in {len(batches)} batches")
        
        for i, batch in enumerate(batches):
            try:
                result = processor_func(batch)
                self.processed_count += len(batch)
                
                if progress_callback:
                    progress_callback(i + 1, len(batches), result)
                
                logger.info(f"Processed batch {i + 1}/{len(batches)}")
            except Exception as e:
                self.failed_count += len(batch)
                logger.error(f"Batch {i + 1} failed: {e}")
        
        return self._get_processing_summary()
    
    def _create_batches(self, data: List[Any]) -> List[List[Any]]:
        """Split data into batches."""
        batches = []
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def _get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of processing results."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "total_processed": self.processed_count,
            "total_failed": self.failed_count,
            "success_rate": self.processed_count / (self.processed_count + self.failed_count) if (self.processed_count + self.failed_count) > 0 else 0,
            "duration_seconds": duration,
            "processed_at": end_time.isoformat()
        }
    
    def process_with_retry(self, data: List[Any], processor_func: Callable, 
                          max_retries: int = 3) -> Dict[str, Any]:
        """Process data with retry logic for failed items."""
        successful = []
        failed = []
        
        for item in data:
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    result = processor_func([item])
                    successful.append(item)
                    success = True
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        failed.append({"item": item, "error": str(e)})
                        logger.error(f"Item failed after {max_retries} retries: {e}")
        
        return {
            "successful": successful,
            "failed": failed,
            "success_count": len(successful),
            "failure_count": len(failed)
        }
