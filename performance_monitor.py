#!/usr/bin/env python3
"""
Performance Monitor for FRP Web Control Panel
Monitors memory usage and system performance on lightweight servers
"""

import os
import psutil
import time
import json
from datetime import datetime

class PerformanceMonitor:
    def __init__(self, memory_limit_mb=400):  # 400MB limit for 0.5GB server
        self.memory_limit = memory_limit_mb * 1024 * 1024  # Convert to bytes
        self.start_time = time.time()
        self.stats = {
            'memory_usage': [],
            'cpu_usage': [],
            'warnings': []
        }
    
    def get_current_memory(self):
        """Get current memory usage of the process"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except:
            return 0
    
    def get_system_stats(self):
        """Get system-wide statistics"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return None
    
    def check_memory_usage(self):
        """Check if memory usage is within limits"""
        current_memory = self.get_current_memory()
        
        if current_memory > self.memory_limit:
            warning = {
                'type': 'memory_warning',
                'message': f'Memory usage ({current_memory / 1024 / 1024:.1f}MB) exceeds limit ({self.memory_limit / 1024 / 1024:.1f}MB)',
                'timestamp': datetime.now().isoformat(),
                'memory_mb': current_memory / 1024 / 1024
            }
            self.stats['warnings'].append(warning)
            return False
        
        return True
    
    def log_stats(self):
        """Log current performance statistics"""
        system_stats = self.get_system_stats()
        if system_stats:
            self.stats['memory_usage'].append(system_stats['memory_percent'])
            self.stats['cpu_usage'].append(system_stats['cpu_percent'])
            
            # Keep only last 100 entries to save memory
            if len(self.stats['memory_usage']) > 100:
                self.stats['memory_usage'] = self.stats['memory_usage'][-50:]
                self.stats['cpu_usage'] = self.stats['cpu_usage'][-50:]
    
    def get_performance_report(self):
        """Generate performance report"""
        uptime = time.time() - self.start_time
        current_memory = self.get_current_memory()
        system_stats = self.get_system_stats()
        
        report = {
            'uptime_seconds': uptime,
            'uptime_formatted': f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m",
            'current_memory_mb': current_memory / 1024 / 1024,
            'memory_limit_mb': self.memory_limit / 1024 / 1024,
            'memory_usage_ok': current_memory < self.memory_limit,
            'system_stats': system_stats,
            'warnings_count': len(self.stats['warnings']),
            'recent_warnings': self.stats['warnings'][-5:] if self.stats['warnings'] else []
        }
        
        if self.stats['memory_usage']:
            report['avg_memory_percent'] = sum(self.stats['memory_usage']) / len(self.stats['memory_usage'])
            report['avg_cpu_percent'] = sum(self.stats['cpu_usage']) / len(self.stats['cpu_usage'])
        
        return report
    
    def optimize_memory(self):
        """Perform memory optimization"""
        import gc
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear any large caches if they exist
        try:
            from functools import lru_cache
            # Clear LRU caches (if any are defined in the main app)
            for obj in gc.get_objects():
                if hasattr(obj, 'cache_clear'):
                    obj.cache_clear()
        except:
            pass
        
        return {
            'garbage_collected': collected,
            'memory_after_gc': self.get_current_memory() / 1024 / 1024
        }

# Global monitor instance
monitor = PerformanceMonitor()

def get_monitor():
    """Get the global monitor instance"""
    return monitor

def memory_usage_decorator(func):
    """Decorator to monitor memory usage of functions"""
    def wrapper(*args, **kwargs):
        memory_before = monitor.get_current_memory()
        result = func(*args, **kwargs)
        memory_after = monitor.get_current_memory()
        
        memory_diff = memory_after - memory_before
        if memory_diff > 10 * 1024 * 1024:  # More than 10MB increase
            monitor.stats['warnings'].append({
                'type': 'function_memory_warning',
                'function': func.__name__,
                'memory_increase_mb': memory_diff / 1024 / 1024,
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    return wrapper

def lightweight_cache(maxsize=32, ttl=300):
    """Lightweight caching decorator with TTL"""
    def decorator(func):
        cache = {}
        
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return result
                else:
                    del cache[key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            
            # Limit cache size
            if len(cache) > maxsize:
                # Remove oldest entries
                oldest_keys = sorted(cache.keys(), key=lambda k: cache[k][1])[:len(cache) - maxsize + 1]
                for old_key in oldest_keys:
                    del cache[old_key]
            
            return result
        
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'maxsize': maxsize,
            'ttl': ttl
        }
        
        return wrapper
    return decorator

if __name__ == '__main__':
    # Test the performance monitor
    print("Performance Monitor Test")
    print("=" * 30)
    
    # Log some stats
    for i in range(5):
        monitor.log_stats()
        time.sleep(1)
    
    # Generate report
    report = monitor.get_performance_report()
    print(json.dumps(report, indent=2))
    
    # Test memory optimization
    print("\nMemory Optimization:")
    optimization_result = monitor.optimize_memory()
    print(json.dumps(optimization_result, indent=2))
