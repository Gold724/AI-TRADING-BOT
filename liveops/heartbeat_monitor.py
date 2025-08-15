import os
import json
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

class HeartbeatMonitor:
    """Heartbeat monitor for ensuring 24/7 operation.
    
    This class provides monitoring capabilities to ensure the system is running
    continuously and can recover from failures.
    """
    
    def __init__(self, interval: int = 60, logs_dir: str = "logs"):
        """Initialize the heartbeat monitor.
        
        Args:
            interval (int, optional): Heartbeat interval in seconds. Defaults to 60.
            logs_dir (str, optional): Directory for logs. Defaults to "logs".
        """
        self.logger = logging.getLogger("trae.heartbeat_monitor")
        self.logs_dir = logs_dir
        self.interval = interval
        self.running = False
        self.thread = None
        self.callbacks = []
        
        # Ensure logs directory exists
        os.makedirs(logs_dir, exist_ok=True)
        
        self.logger.info(f"Heartbeat monitor initialized with {interval}s interval")
    
    def start(self) -> bool:
        """Start the heartbeat monitor.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Heartbeat monitor already running")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("Heartbeat monitor started")
        return True
    
    def stop(self) -> bool:
        """Stop the heartbeat monitor.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            self.logger.warning("Heartbeat monitor not running")
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        
        self.logger.info("Heartbeat monitor stopped")
        return True
    
    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback function to be called on each heartbeat.
        
        Args:
            callback (Callable[[], None]): Callback function
        """
        self.callbacks.append(callback)
        self.logger.info(f"Registered new heartbeat callback (total: {len(self.callbacks)})")
    
    def _heartbeat_loop(self) -> None:
        """Main heartbeat loop."""
        while self.running:
            try:
                # Record heartbeat
                self._record_heartbeat()
                
                # Execute callbacks
                for callback in self.callbacks:
                    try:
                        callback()
                    except Exception as e:
                        self.logger.error(f"Error in heartbeat callback: {e}")
                
                # Sleep until next interval
                time.sleep(self.interval)
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(5)  # Short sleep on error before retrying
    
    def _record_heartbeat(self) -> None:
        """Record a heartbeat in the logs."""
        try:
            # Create heartbeat record
            heartbeat = {
                "timestamp": datetime.now().isoformat(),
                "status": "alive"
            }
            
            # Add system info
            heartbeat["system_info"] = {
                "memory_usage": self._get_memory_usage(),
                "cpu_usage": self._get_cpu_usage(),
                "uptime": self._get_uptime()
            }
            
            # Load existing heartbeats
            heartbeats_file = os.path.join(self.logs_dir, "heartbeats.json")
            heartbeats = []
            
            if os.path.exists(heartbeats_file):
                try:
                    with open(heartbeats_file, "r") as f:
                        heartbeats = json.load(f)
                except json.JSONDecodeError:
                    heartbeats = []
            
            # Add new heartbeat record
            heartbeats.append(heartbeat)
            
            # Keep only the last 1000 heartbeats to avoid file growth
            if len(heartbeats) > 1000:
                heartbeats = heartbeats[-1000:]
            
            # Save updated heartbeats
            with open(heartbeats_file, "w") as f:
                json.dump(heartbeats, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error recording heartbeat: {e}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage.
        
        Returns:
            float: Memory usage percentage
        """
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage.
        
        Returns:
            float: CPU usage percentage
        """
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
            return 0.0
    
    def _get_uptime(self) -> int:
        """Get system uptime in seconds.
        
        Returns:
            int: Uptime in seconds
        """
        try:
            import psutil
            return int(time.time() - psutil.boot_time())
        except ImportError:
            return 0
        except Exception as e:
            self.logger.error(f"Error getting uptime: {e}")
            return 0
    
    def check_health(self) -> Dict[str, Any]:
        """Check system health.
        
        Returns:
            Dict[str, Any]: Health status
        """
        try:
            # Get system info
            memory_usage = self._get_memory_usage()
            cpu_usage = self._get_cpu_usage()
            uptime = self._get_uptime()
            
            # Check if memory usage is too high
            memory_warning = memory_usage > 90.0
            
            # Check if CPU usage is too high
            cpu_warning = cpu_usage > 90.0
            
            # Overall health status
            status = "healthy"
            if memory_warning or cpu_warning:
                status = "warning"
            
            return {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "memory_usage": memory_usage,
                "memory_warning": memory_warning,
                "cpu_usage": cpu_usage,
                "cpu_warning": cpu_warning,
                "uptime": uptime,
                "uptime_hours": round(uptime / 3600, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error checking health: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }