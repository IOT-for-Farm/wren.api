"""
Export Scheduler Utilities

Schedule and manage data export jobs.
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import threading
import time


class ExportScheduler:
    """Schedules and manages export jobs."""
    
    def __init__(self):
        """Initialize export scheduler."""
        self.jobs = {}
        self.running = False
        self.scheduler_thread = None
    
    def schedule_export(self, job_id: str, export_func: Callable, 
                       schedule_time: datetime, data: List[Dict[str, Any]], 
                       format_type: str = "json") -> str:
        """Schedule an export job."""
        job = {
            "id": job_id,
            "export_func": export_func,
            "schedule_time": schedule_time,
            "data": data,
            "format": format_type,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        self.jobs[job_id] = job
        return job_id
    
    def run_export_job(self, job_id: str) -> Dict[str, Any]:
        """Run a specific export job."""
        if job_id not in self.jobs:
            return {"error": "Job not found"}
        
        job = self.jobs[job_id]
        job["status"] = "running"
        job["started_at"] = datetime.now().isoformat()
        
        try:
            result = job["export_func"](job["data"], format_type=job["format"])
            job["status"] = "completed"
            job["result"] = result
            job["completed_at"] = datetime.now().isoformat()
        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)
            job["failed_at"] = datetime.now().isoformat()
        
        return job
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        return {
            "id": job["id"],
            "status": job["status"],
            "created_at": job["created_at"],
            "schedule_time": job["schedule_time"].isoformat()
        }
    
    def list_jobs(self, status: str = None) -> List[Dict[str, Any]]:
        """List all jobs, optionally filtered by status."""
        jobs = []
        for job in self.jobs.values():
            if status is None or job["status"] == status:
                jobs.append(self.get_job_status(job["id"]))
        return jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        if job_id in self.jobs and self.jobs[job_id]["status"] == "scheduled":
            self.jobs[job_id]["status"] = "cancelled"
            return True
        return False
