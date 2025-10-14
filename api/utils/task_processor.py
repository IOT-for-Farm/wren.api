"""
Background Task Processing for Wren API

This module provides comprehensive background task processing, job queues,
and asynchronous task management utilities.
"""

import asyncio
import uuid
import time
from typing import Any, Dict, List, Optional, Union, Callable, Type
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from api.utils.loggers import create_logger

logger = create_logger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """Task data structure"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """Task queue implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.tasks = []
        self.task_index = {}
        self.is_running = False
        self.workers = []
        self.max_workers = 4
    
    def add_task(self, task: Task) -> bool:
        """Add task to queue"""
        if len(self.tasks) >= self.max_size:
            logger.warning("Task queue is full")
            return False
        
        self.tasks.append(task)
        self.task_index[task.id] = task
        
        # Sort by priority
        self.tasks.sort(key=lambda t: t.priority.value, reverse=True)
        
        logger.info(f"Task added to queue: {task.id}")
        return True
    
    def get_next_task(self) -> Optional[Task]:
        """Get next task from queue"""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: str = None):
        """Update task status"""
        if task_id in self.task_index:
            task = self.task_index[task_id]
            task.status = status
            
            if status == TaskStatus.RUNNING:
                task.started_at = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.utcnow()
            
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            
            logger.info(f"Task {task_id} status updated to {status.value}")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.task_index.get(task_id)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        status_counts = {}
        for task in self.tasks:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "status_counts": status_counts,
            "max_size": self.max_size,
            "is_running": self.is_running
        }


class TaskWorker:
    """Task worker implementation"""
    
    def __init__(self, worker_id: str, queue: TaskQueue):
        self.worker_id = worker_id
        self.queue = queue
        self.is_running = False
        self.current_task = None
    
    async def start(self):
        """Start worker"""
        self.is_running = True
        logger.info(f"Worker {self.worker_id} started")
        
        while self.is_running:
            task = self.queue.get_next_task()
            
            if task is None:
                await asyncio.sleep(1)
                continue
            
            await self._execute_task(task)
    
    async def _execute_task(self, task: Task):
        """Execute task"""
        self.current_task = task
        self.queue.update_task_status(task.id, TaskStatus.RUNNING)
        
        try:
            # Execute task
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            self.queue.update_task_status(task.id, TaskStatus.COMPLETED, result=result)
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task {task.id} failed: {error_msg}")
            
            # Check if should retry
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                self.queue.update_task_status(task.id, TaskStatus.RETRYING)
                logger.info(f"Task {task.id} retrying ({task.retry_count}/{task.max_retries})")
            else:
                self.queue.update_task_status(task.id, TaskStatus.FAILED, error=error_msg)
        
        finally:
            self.current_task = None
    
    def stop(self):
        """Stop worker"""
        self.is_running = False
        logger.info(f"Worker {self.worker_id} stopped")


class TaskManager:
    """Task management system"""
    
    def __init__(self, max_workers: int = 4):
        self.queue = TaskQueue()
        self.workers = []
        self.max_workers = max_workers
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def start(self):
        """Start task manager"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Create and start workers
        for i in range(self.max_workers):
            worker = TaskWorker(f"worker-{i}", self.queue)
            self.workers.append(worker)
            asyncio.create_task(worker.start())
        
        logger.info(f"Task manager started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop task manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop all workers
        for worker in self.workers:
            worker.stop()
        
        # Wait for workers to finish
        await asyncio.gather(*[worker.start() for worker in self.workers], return_exceptions=True)
        
        self.executor.shutdown(wait=True)
        logger.info("Task manager stopped")
    
    def submit_task(self, name: str, func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL, 
                   max_retries: int = 3, timeout: Optional[int] = None, **kwargs) -> str:
        """Submit task for execution"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        if self.queue.add_task(task):
            return task_id
        else:
            raise Exception("Failed to add task to queue")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = self.queue.get_task(task_id)
        if task is None:
            return None
        
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "error": task.error
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel task"""
        task = self.queue.get_task(task_id)
        if task is None or task.status not in [TaskStatus.PENDING, TaskStatus.RETRYING]:
            return False
        
        self.queue.update_task_status(task_id, TaskStatus.CANCELLED)
        logger.info(f"Task {task_id} cancelled")
        return True
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get task manager statistics"""
        queue_stats = self.queue.get_queue_stats()
        
        return {
            "is_running": self.is_running,
            "max_workers": self.max_workers,
            "active_workers": len([w for w in self.workers if w.is_running]),
            "queue_stats": queue_stats
        }


class ScheduledTaskManager:
    """Scheduled task management"""
    
    def __init__(self):
        self.scheduled_tasks = {}
        self.is_running = False
    
    async def start(self):
        """Start scheduled task manager"""
        self.is_running = True
        logger.info("Scheduled task manager started")
        
        while self.is_running:
            await self._check_scheduled_tasks()
            await asyncio.sleep(60)  # Check every minute
    
    def _check_scheduled_tasks(self):
        """Check for scheduled tasks to execute"""
        current_time = datetime.utcnow()
        
        for task_id, task_info in self.scheduled_tasks.items():
            if task_info["next_run"] <= current_time:
                # Execute scheduled task
                asyncio.create_task(self._execute_scheduled_task(task_id, task_info))
    
    async def _execute_scheduled_task(self, task_id: str, task_info: Dict[str, Any]):
        """Execute scheduled task"""
        try:
            await task_info["func"](*task_info["args"], **task_info["kwargs"])
            
            # Schedule next run
            if task_info["interval"]:
                task_info["next_run"] = datetime.utcnow() + task_info["interval"]
            else:
                # One-time task, remove it
                del self.scheduled_tasks[task_id]
                
        except Exception as e:
            logger.error(f"Scheduled task {task_id} failed: {e}")
    
    def schedule_task(self, task_id: str, func: Callable, interval: Optional[timedelta] = None,
                     delay: Optional[timedelta] = None, *args, **kwargs):
        """Schedule task for execution"""
        next_run = datetime.utcnow()
        if delay:
            next_run += delay
        
        self.scheduled_tasks[task_id] = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "interval": interval,
            "next_run": next_run
        }
        
        logger.info(f"Task {task_id} scheduled")
    
    def cancel_scheduled_task(self, task_id: str) -> bool:
        """Cancel scheduled task"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"Scheduled task {task_id} cancelled")
            return True
        return False


# Global task processing instances
def get_task_manager(max_workers: int = 4) -> TaskManager:
    """Get task manager instance"""
    return TaskManager(max_workers)

def get_scheduled_task_manager() -> ScheduledTaskManager:
    """Get scheduled task manager instance"""
    return ScheduledTaskManager()
