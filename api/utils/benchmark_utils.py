"""
Benchmark Utilities

Utilities for benchmarking and performance testing.
"""

import time
from typing import Callable, Any, Dict, List
from functools import wraps
from .performance_tracker import PerformanceTracker


class BenchmarkUtils:
    """Utilities for benchmarking functions and operations."""
    
    def __init__(self):
        """Initialize benchmark utilities."""
        self.tracker = PerformanceTracker()
    
    def benchmark_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Benchmark a function execution."""
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "function": func.__name__,
            "duration": duration,
            "success": success,
            "result": result,
            "error": error,
            "timestamp": time.time()
        }
    
    def benchmark_multiple(self, func: Callable, iterations: int, *args, **kwargs) -> Dict[str, Any]:
        """Benchmark function multiple times."""
        results = []
        
        for i in range(iterations):
            result = self.benchmark_function(func, *args, **kwargs)
            results.append(result)
        
        durations = [r["duration"] for r in results if r["success"]]
        success_count = sum(1 for r in results if r["success"])
        
        return {
            "iterations": iterations,
            "success_count": success_count,
            "success_rate": success_count / iterations,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "results": results
        }
    
    def benchmark_decorator(self, iterations: int = 1):
        """Decorator to benchmark function execution."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if iterations == 1:
                    return self.benchmark_function(func, *args, **kwargs)
                else:
                    return self.benchmark_multiple(func, iterations, *args, **kwargs)
            return wrapper
        return decorator
    
    def compare_functions(self, functions: List[Callable], *args, **kwargs) -> Dict[str, Any]:
        """Compare performance of multiple functions."""
        results = {}
        
        for func in functions:
            benchmark_result = self.benchmark_function(func, *args, **kwargs)
            results[func.__name__] = benchmark_result
        
        # Find fastest function
        fastest = min(results.items(), key=lambda x: x[1]["duration"])
        
        return {
            "results": results,
            "fastest": fastest[0],
            "fastest_duration": fastest[1]["duration"]
        }
