#!/usr/bin/env python3
"""
Health Monitor for TradeBot Sentinel Pro Advanced

Provides comprehensive system health monitoring, performance tracking,
and status reporting for all system components.

Author: TradeBot Sentinel Team
Version: 2.0.0
License: MIT
"""

import asyncio
import psutil
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
import threading
import queue
import traceback


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Component health information"""
    name: str
    status: HealthStatus
    last_check: datetime
    response_time: float = 0.0
    error_count: int = 0
    uptime: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    uptime: float
    temperature: Optional[float] = None


@dataclass
class HealthAlert:
    """Health alert information"""
    component: str
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class HealthMonitor:
    """
    Comprehensive health monitoring system for TradeBot Sentinel Pro Advanced.
    
    Monitors system resources, component health, and provides alerting
    capabilities for performance issues and failures.
    """
    
    def __init__(self, check_interval: int = 30, alert_threshold: int = 3):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Health check interval in seconds
            alert_threshold: Number of consecutive failures before alert
        """
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Component registry
        self.components: Dict[str, ComponentHealth] = {}
        self.health_checks: Dict[str, Callable] = {}
        
        # Metrics storage
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        
        # Alert system
        self.alerts: List[HealthAlert] = []
        self.alert_callbacks: List[Callable] = []
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Performance tracking
        self.start_time = time.time()
        self.last_metrics_collection = time.time()
        
        # Initialize system monitoring
        self._initialize_system_monitoring()
    
    def _initialize_system_monitoring(self):
        """Initialize system-level monitoring"""
        try:
            # Get initial system info
            self.system_info = {
                'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown',
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total if hasattr(psutil.disk_usage('/'), 'total') else 0,
                'boot_time': psutil.boot_time()
            }
            
            self.logger.info(f"System monitoring initialized: {self.system_info}")
        except Exception as e:
            self.logger.error(f"Failed to initialize system monitoring: {e}")
            self.system_info = {}
    
    def register_component(self, name: str, health_check: Optional[Callable] = None):
        """
        Register a component for health monitoring.
        
        Args:
            name: Component name
            health_check: Optional health check function
        """
        self.components[name] = ComponentHealth(
            name=name,
            status=HealthStatus.UNKNOWN,
            last_check=datetime.now()
        )
        
        if health_check:
            self.health_checks[name] = health_check
        
        self.logger.info(f"Registered component: {name}")
    
    def unregister_component(self, name: str):
        """Unregister a component from monitoring"""
        if name in self.components:
            del self.components[name]
        if name in self.health_checks:
            del self.health_checks[name]
        
        self.logger.info(f"Unregistered component: {name}")
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    async def check_component_health(self, name: str) -> ComponentHealth:
        """
        Check health of a specific component.
        
        Args:
            name: Component name
        
        Returns:
            Component health information
        """
        if name not in self.components:
            raise ValueError(f"Component '{name}' not registered")
        
        component = self.components[name]
        start_time = time.time()
        
        try:
            # Run health check if available
            if name in self.health_checks:
                health_check = self.health_checks[name]
                
                if asyncio.iscoroutinefunction(health_check):
                    result = await health_check()
                else:
                    result = health_check()
                
                # Process health check result
                if isinstance(result, dict):
                    component.status = HealthStatus(result.get('status', 'unknown'))
                    component.details.update(result.get('details', {}))
                    component.metrics.update(result.get('metrics', {}))
                elif isinstance(result, bool):
                    component.status = HealthStatus.HEALTHY if result else HealthStatus.CRITICAL
                else:
                    component.status = HealthStatus.HEALTHY
            else:
                # Default health check - just mark as healthy if no errors
                component.status = HealthStatus.HEALTHY
            
            # Reset error count on successful check
            component.error_count = 0
            
        except Exception as e:
            component.status = HealthStatus.CRITICAL
            component.error_count += 1
            component.details['last_error'] = str(e)
            component.details['last_error_time'] = datetime.now().isoformat()
            
            self.logger.error(f"Health check failed for {name}: {e}")
            
            # Create alert if threshold exceeded
            if component.error_count >= self.alert_threshold:
                await self._create_alert(
                    component=name,
                    severity="critical",
                    message=f"Component {name} failed {component.error_count} consecutive health checks: {e}"
                )
        
        # Update timing information
        component.response_time = time.time() - start_time
        component.last_check = datetime.now()
        component.uptime = time.time() - self.start_time
        
        # Update component in registry
        self.components[name] = component
        
        return component
    
    async def check_all_components(self) -> Dict[str, ComponentHealth]:
        """Check health of all registered components"""
        results = {}
        
        for name in self.components.keys():
            try:
                results[name] = await self.check_component_health(name)
            except Exception as e:
                self.logger.error(f"Failed to check component {name}: {e}")
                results[name] = self.components[name]
                results[name].status = HealthStatus.CRITICAL
        
        return results
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            try:
                load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_average = [0.0, 0.0, 0.0]
            
            # System uptime
            uptime = time.time() - psutil.boot_time()
            
            # Temperature (if available)
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get first available temperature sensor
                    for sensor_name, sensor_list in temps.items():
                        if sensor_list:
                            temperature = sensor_list[0].current
                            break
            except (AttributeError, OSError):
                pass
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average,
                uptime=uptime,
                temperature=temperature
            )
            
            # Store in history
            self.metrics_history.append(metrics)
            
            # Limit history size
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            self.last_metrics_collection = time.time()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage=0.0,
                network_io={},
                process_count=0,
                load_average=[0.0, 0.0, 0.0],
                uptime=0.0
            )
    
    async def _create_alert(self, component: str, severity: str, message: str):
        """Create and process health alert"""
        alert = HealthAlert(
            component=component,
            severity=severity,
            message=message,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Limit alert history
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        self.logger.warning(f"Health alert: {alert.component} - {alert.message}")
        
        # Notify alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Collect current metrics
        current_metrics = self.collect_system_metrics()
        
        # Determine overall health
        component_statuses = [comp.status for comp in self.components.values()]
        
        if not component_statuses:
            overall_status = HealthStatus.UNKNOWN
        elif any(status == HealthStatus.CRITICAL for status in component_statuses):
            overall_status = HealthStatus.CRITICAL
        elif any(status == HealthStatus.WARNING for status in component_statuses):
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Count alerts by severity
        recent_alerts = [a for a in self.alerts if not a.resolved and 
                        (datetime.now() - a.timestamp).total_seconds() < 3600]
        
        alert_counts = {
            'critical': len([a for a in recent_alerts if a.severity == 'critical']),
            'warning': len([a for a in recent_alerts if a.severity == 'warning']),
            'info': len([a for a in recent_alerts if a.severity == 'info'])
        }
        
        return {
            'overall_status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - self.start_time,
            'components': {
                name: {
                    'status': comp.status.value,
                    'last_check': comp.last_check.isoformat(),
                    'response_time': comp.response_time,
                    'error_count': comp.error_count,
                    'uptime': comp.uptime
                } for name, comp in self.components.items()
            },
            'system_metrics': asdict(current_metrics),
            'alerts': alert_counts,
            'monitoring_active': self.is_monitoring
        }
    
    def get_component_details(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a component"""
        if name not in self.components:
            return None
        
        component = self.components[name]
        
        return {
            'name': component.name,
            'status': component.status.value,
            'last_check': component.last_check.isoformat(),
            'response_time': component.response_time,
            'error_count': component.error_count,
            'uptime': component.uptime,
            'memory_usage': component.memory_usage,
            'cpu_usage': component.cpu_usage,
            'details': component.details,
            'metrics': component.metrics,
            'recent_alerts': [
                {
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved
                }
                for alert in self.alerts
                if alert.component == name and 
                   (datetime.now() - alert.timestamp).total_seconds() < 86400  # Last 24 hours
            ]
        }
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {'error': 'No metrics available for specified period'}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_usage for m in recent_metrics) / len(recent_metrics)
        
        # Find peaks
        max_cpu = max(m.cpu_percent for m in recent_metrics)
        max_memory = max(m.memory_percent for m in recent_metrics)
        max_disk = max(m.disk_usage for m in recent_metrics)
        
        return {
            'period_hours': hours,
            'sample_count': len(recent_metrics),
            'averages': {
                'cpu_percent': round(avg_cpu, 2),
                'memory_percent': round(avg_memory, 2),
                'disk_usage': round(avg_disk, 2)
            },
            'peaks': {
                'cpu_percent': round(max_cpu, 2),
                'memory_percent': round(max_memory, 2),
                'disk_usage': round(max_disk, 2)
            },
            'current': asdict(recent_metrics[-1]) if recent_metrics else None
        }
    
    def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.is_monitoring:
            self.logger.warning("Health monitoring already active")
            return
        
        self.is_monitoring = True
        self.stop_event.clear()
        
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="HealthMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info(f"Health monitoring started (interval: {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop (runs in separate thread)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while not self.stop_event.is_set():
                try:
                    # Check all components
                    loop.run_until_complete(self.check_all_components())
                    
                    # Collect system metrics
                    self.collect_system_metrics()
                    
                    # Wait for next check
                    if self.stop_event.wait(self.check_interval):
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    self.logger.debug(traceback.format_exc())
                    
                    # Wait before retrying
                    if self.stop_event.wait(min(self.check_interval, 10)):
                        break
        
        finally:
            loop.close()
    
    def export_health_report(self, filepath: str):
        """Export comprehensive health report to file"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'system_status': self.get_system_status(),
                'component_details': {
                    name: self.get_component_details(name)
                    for name in self.components.keys()
                },
                'metrics_summary': self.get_metrics_summary(),
                'recent_alerts': [
                    {
                        'component': alert.component,
                        'severity': alert.severity,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat(),
                        'resolved': alert.resolved
                    }
                    for alert in self.alerts[-100:]  # Last 100 alerts
                ],
                'system_info': self.system_info
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Health report exported to: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export health report: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()


# Example health check functions
def example_database_health_check() -> Dict[str, Any]:
    """Example database health check"""
    try:
        # Simulate database connection check
        import time
        start_time = time.time()
        
        # Simulate query
        time.sleep(0.1)
        
        response_time = time.time() - start_time
        
        return {
            'status': 'healthy',
            'details': {
                'connection_pool_size': 10,
                'active_connections': 3,
                'query_response_time': response_time
            },
            'metrics': {
                'response_time_ms': response_time * 1000,
                'connection_count': 3
            }
        }
    except Exception as e:
        return {
            'status': 'critical',
            'details': {'error': str(e)}
        }


async def example_api_health_check() -> Dict[str, Any]:
    """Example API health check"""
    try:
        # Simulate API call
        await asyncio.sleep(0.05)
        
        return {
            'status': 'healthy',
            'details': {
                'endpoint': 'https://api.example.com/health',
                'status_code': 200
            },
            'metrics': {
                'response_time_ms': 50,
                'success_rate': 99.5
            }
        }
    except Exception as e:
        return {
            'status': 'critical',
            'details': {'error': str(e)}
        }


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_health_monitor():
        """Test health monitor functionality"""
        # Create health monitor
        monitor = HealthMonitor(check_interval=5)
        
        # Register components
        monitor.register_component("Database", example_database_health_check)
        monitor.register_component("API", example_api_health_check)
        monitor.register_component("FileSystem")
        
        # Add alert callback
        def alert_handler(alert):
            print(f"ALERT: {alert.component} - {alert.message}")
        
        monitor.add_alert_callback(alert_handler)
        
        # Start monitoring
        monitor.start_monitoring()
        
        try:
            # Let it run for a bit
            await asyncio.sleep(15)
            
            # Check system status
            status = monitor.get_system_status()
            print(f"System Status: {json.dumps(status, indent=2)}")
            
            # Get component details
            db_details = monitor.get_component_details("Database")
            print(f"Database Details: {json.dumps(db_details, indent=2)}")
            
            # Get metrics summary
            metrics = monitor.get_metrics_summary(hours=1)
            print(f"Metrics Summary: {json.dumps(metrics, indent=2)}")
            
            # Export health report
            monitor.export_health_report("health_report.json")
            
        finally:
            # Stop monitoring
            monitor.stop_monitoring()
    
    # Run test
    asyncio.run(test_health_monitor())
    print("Health monitor testing completed.")