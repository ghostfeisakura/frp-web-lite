#!/usr/bin/env python3
"""
Resource Guardian for FRP Web Control Panel
Monitors and manages resources on lightweight servers (2-core 0.5GB RAM)
"""

import os
import sys
import time
import psutil
import subprocess
import json
import signal
from datetime import datetime, timedelta

class ResourceGuardian:
    def __init__(self, config_file='/opt/frp-web-control/guardian_config.json'):
        self.config = self.load_config(config_file)
        self.service_name = self.config.get('service_name', 'frp-web-lite')
        self.memory_limit_mb = self.config.get('memory_limit_mb', 400)
        self.cpu_limit_percent = self.config.get('cpu_limit_percent', 80)
        self.check_interval = self.config.get('check_interval', 30)
        self.restart_cooldown = self.config.get('restart_cooldown', 300)  # 5 minutes
        
        self.last_restart = None
        self.restart_count = 0
        self.log_file = '/var/log/frp-web-guardian.log'
        
    def load_config(self, config_file):
        """Load configuration from file"""
        default_config = {
            'service_name': 'frp-web-lite',
            'memory_limit_mb': 400,
            'cpu_limit_percent': 80,
            'check_interval': 30,
            'restart_cooldown': 300,
            'max_restarts_per_hour': 3,
            'enable_auto_restart': True,
            'enable_memory_cleanup': True
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            self.log(f"Error loading config: {e}, using defaults")
        
        return default_config
    
    def log(self, message, level='INFO'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except:
            pass  # Fail silently if can't write to log
    
    def get_service_pid(self):
        """Get PID of the service"""
        try:
            result = subprocess.run(
                ['systemctl', 'show', '--property', 'MainPID', '--value', self.service_name],
                capture_output=True, text=True, timeout=10
            )
            pid = int(result.stdout.strip())
            return pid if pid > 0 else None
        except:
            return None
    
    def get_process_stats(self, pid):
        """Get process statistics"""
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=1)
            
            return {
                'memory_mb': memory_info.rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'cpu_percent': cpu_percent,
                'num_threads': process.num_threads(),
                'status': process.status()
            }
        except psutil.NoSuchProcess:
            return None
        except Exception as e:
            self.log(f"Error getting process stats: {e}", 'ERROR')
            return None
    
    def get_system_stats(self):
        """Get system-wide statistics"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            return {
                'memory_total_mb': memory.total / 1024 / 1024,
                'memory_available_mb': memory.available / 1024 / 1024,
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024,
                'disk_percent': (disk.used / disk.total) * 100
            }
        except Exception as e:
            self.log(f"Error getting system stats: {e}", 'ERROR')
            return None
    
    def should_restart_service(self, process_stats):
        """Determine if service should be restarted"""
        if not self.config.get('enable_auto_restart', True):
            return False, "Auto-restart disabled"
        
        # Check restart cooldown
        if self.last_restart:
            time_since_restart = datetime.now() - self.last_restart
            if time_since_restart.total_seconds() < self.restart_cooldown:
                return False, f"Restart cooldown active ({self.restart_cooldown - time_since_restart.total_seconds():.0f}s remaining)"
        
        # Check restart frequency
        if self.restart_count >= self.config.get('max_restarts_per_hour', 3):
            return False, "Maximum restarts per hour reached"
        
        # Check memory usage
        if process_stats['memory_mb'] > self.memory_limit_mb:
            return True, f"Memory usage ({process_stats['memory_mb']:.1f}MB) exceeds limit ({self.memory_limit_mb}MB)"
        
        # Check CPU usage (sustained high usage)
        if process_stats['cpu_percent'] > self.cpu_limit_percent:
            return True, f"CPU usage ({process_stats['cpu_percent']:.1f}%) exceeds limit ({self.cpu_limit_percent}%)"
        
        return False, "All metrics within limits"
    
    def restart_service(self, reason):
        """Restart the service"""
        self.log(f"Restarting service: {reason}", 'WARNING')
        
        try:
            # Attempt graceful restart
            result = subprocess.run(
                ['systemctl', 'restart', self.service_name],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                self.last_restart = datetime.now()
                self.restart_count += 1
                self.log("Service restarted successfully", 'INFO')
                return True
            else:
                self.log(f"Service restart failed: {result.stderr}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"Error restarting service: {e}", 'ERROR')
            return False
    
    def cleanup_memory(self):
        """Perform system memory cleanup"""
        if not self.config.get('enable_memory_cleanup', True):
            return
        
        try:
            # Clear page cache, dentries and inodes
            subprocess.run(['sync'], timeout=10)
            subprocess.run(['echo', '3'], stdout=open('/proc/sys/vm/drop_caches', 'w'), timeout=10)
            self.log("Memory cleanup performed", 'INFO')
        except Exception as e:
            self.log(f"Memory cleanup failed: {e}", 'ERROR')
    
    def check_service_health(self):
        """Check service health and take action if needed"""
        pid = self.get_service_pid()
        
        if not pid:
            self.log("Service not running, attempting to start", 'WARNING')
            try:
                subprocess.run(['systemctl', 'start', self.service_name], timeout=30)
                self.log("Service start attempted", 'INFO')
            except Exception as e:
                self.log(f"Failed to start service: {e}", 'ERROR')
            return
        
        process_stats = self.get_process_stats(pid)
        if not process_stats:
            self.log("Could not get process statistics", 'ERROR')
            return
        
        system_stats = self.get_system_stats()
        
        # Log current stats
        self.log(
            f"Stats - Memory: {process_stats['memory_mb']:.1f}MB "
            f"({process_stats['memory_percent']:.1f}%), "
            f"CPU: {process_stats['cpu_percent']:.1f}%, "
            f"Threads: {process_stats['num_threads']}, "
            f"System Memory: {system_stats['memory_percent']:.1f}% if system_stats else 'N/A'}"
        )
        
        # Check if restart is needed
        should_restart, reason = self.should_restart_service(process_stats)
        
        if should_restart:
            self.restart_service(reason)
        
        # Perform memory cleanup if system memory is high
        if system_stats and system_stats['memory_percent'] > 85:
            self.cleanup_memory()
    
    def reset_restart_counter(self):
        """Reset restart counter every hour"""
        self.restart_count = 0
        self.log("Restart counter reset", 'INFO')
    
    def run_daemon(self):
        """Run as daemon process"""
        self.log(f"Resource Guardian started for service: {self.service_name}", 'INFO')
        self.log(f"Memory limit: {self.memory_limit_mb}MB, CPU limit: {self.cpu_limit_percent}%", 'INFO')
        
        last_counter_reset = datetime.now()
        
        try:
            while True:
                # Reset restart counter every hour
                if datetime.now() - last_counter_reset > timedelta(hours=1):
                    self.reset_restart_counter()
                    last_counter_reset = datetime.now()
                
                # Check service health
                self.check_service_health()
                
                # Wait for next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.log("Resource Guardian stopped by user", 'INFO')
        except Exception as e:
            self.log(f"Resource Guardian error: {e}", 'ERROR')
            sys.exit(1)

def create_default_config():
    """Create default configuration file"""
    config = {
        "service_name": "frp-web-lite",
        "memory_limit_mb": 400,
        "cpu_limit_percent": 80,
        "check_interval": 30,
        "restart_cooldown": 300,
        "max_restarts_per_hour": 3,
        "enable_auto_restart": True,
        "enable_memory_cleanup": True
    }
    
    config_file = '/opt/frp-web-control/guardian_config.json'
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Default configuration created: {config_file}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'create-config':
            create_default_config()
            return
        elif sys.argv[1] == 'check-once':
            guardian = ResourceGuardian()
            guardian.check_service_health()
            return
    
    # Run as daemon
    guardian = ResourceGuardian()
    guardian.run_daemon()

if __name__ == '__main__':
    main()
