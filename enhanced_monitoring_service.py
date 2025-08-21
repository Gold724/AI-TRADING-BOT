#!/usr/bin/env python3
"""
AI Trading Sentinel - Enhanced 24/7 Monitoring Service
TRAE-SentinelOps: Production-ready monitoring with comprehensive alerting

Integrates:
- System health monitoring
- Trading bot status tracking
- Alert management with multiple channels
- Performance metrics collection
- Automated recovery procedures
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Import existing components
try:
    from utils.health_monitor import HealthMonitor, HealthStatus, ComponentHealth
    from scripts.alert_manager import AlertManager, AlertSeverity, AlertChannel
    from utils.slack_notifications import send_slack_prophetic
    from notifications import NotificationManager
    from monitoring_setup import TradingMonitor
except ImportError as e:
    print(f"Warning: Some components not available: {e}")
    # Create minimal fallback classes
    class HealthStatus(Enum):
        HEALTHY = "healthy"
        WARNING = "warning"
        CRITICAL = "critical"
        UNKNOWN = "unknown"
    
    class AlertSeverity(Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"
        EMERGENCY = "emergency"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EnhancedMonitoring')

@dataclass
class ServiceStatus:
    """Service status information"""
    name: str
    status: str
    uptime: float
    response_time: float
    last_check: datetime
    error_count: int = 0
    metadata: Dict[str, Any] = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    active_processes: int
    load_average: List[float]
    temperature: Optional[float] = None

class EnhancedMonitoringService:
    """Enhanced 24/7 monitoring service for AI Trading Sentinel"""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize enhanced monitoring service"""
        self.config_dir = Path(config_dir)
        self.running = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Load configurations
        self.load_configurations()
        
        # Initialize components
        self.initialize_components()
        
        # Monitoring state
        self.services = {}
        self.metrics_history = []
        self.alert_history = []
        self.last_health_check = None
        
        # Create required directories
        self.setup_directories()
        
        logger.info("Enhanced monitoring service initialized")
    
    def load_configurations(self):
        """Load monitoring and alert configurations"""
        try:
            # Load monitoring config
            monitoring_config_path = self.config_dir / "monitoring_config.json"
            if monitoring_config_path.exists():
                with open(monitoring_config_path, 'r') as f:
                    self.monitoring_config = json.load(f)
            else:
                self.monitoring_config = self.get_default_monitoring_config()
            
            # Load alert config
            alert_config_path = self.config_dir / "alert_config.json"
            if alert_config_path.exists():
                with open(alert_config_path, 'r') as f:
                    self.alert_config = json.load(f)
            else:
                self.alert_config = self.get_default_alert_config()
            
            logger.info("Configurations loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            self.monitoring_config = self.get_default_monitoring_config()
            self.alert_config = self.get_default_alert_config()
    
    def get_default_monitoring_config(self) -> Dict:
        """Get default monitoring configuration"""
        return {
            "monitoring": {
                "check_interval": 60,
                "metrics_save_interval": 300,
                "health_check_timeout": 30
            },
            "thresholds": {
                "system": {
                    "cpu_usage": 85.0,
                    "memory_usage": 90.0,
                    "disk_usage": 95.0
                },
                "services": {
                    "response_time": 5.0
                }
            },
            "services": {
                "backend": {
                    "url": "http://localhost:5000/api/health",
                    "enabled": True,
                    "critical": True
                },
                "trading_bot": {
                    "process_name": "python",
                    "script_name": "main.py",
                    "enabled": True,
                    "critical": True
                }
            }
        }
    
    def get_default_alert_config(self) -> Dict:
        """Get default alert configuration"""
        return {
            "notifications": {
                "slack": {
                    "enabled": True,
                    "webhook_url": os.getenv('SLACK_WEBHOOK_URL', '')
                },
                "email": {
                    "enabled": False
                }
            }
        }
    
    def initialize_components(self):
        """Initialize monitoring components"""
        try:
            # Initialize health monitor
            self.health_monitor = HealthMonitor(
                check_interval=self.monitoring_config['monitoring']['check_interval']
            )
            
            # Initialize alert manager
            self.alert_manager = AlertManager()
            
            # Initialize notification manager
            self.notification_manager = NotificationManager()
            
            # Initialize trading monitor
            self.trading_monitor = TradingMonitor()
            
            logger.info("All monitoring components initialized")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            # Create minimal fallback components
            self.health_monitor = None
            self.alert_manager = None
            self.notification_manager = None
            self.trading_monitor = None
    
    def setup_directories(self):
        """Create required directories"""
        directories = [
            'logs',
            'data/monitoring',
            'data/metrics',
            'data/alerts',
            'screenshots/monitoring'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'metrics': {},
            'alerts': []
        }
        
        try:
            # System metrics
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status['metrics'] = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100,
                'processes': len(psutil.pids())
            }
            
            # Check thresholds
            thresholds = self.monitoring_config['thresholds']['system']
            
            if cpu_percent > thresholds['cpu_usage']:
                health_status['alerts'].append({
                    'severity': 'warning',
                    'message': f'High CPU usage: {cpu_percent}%',
                    'component': 'system'
                })
                health_status['overall_status'] = 'warning'
            
            if memory.percent > thresholds['memory_usage']:
                health_status['alerts'].append({
                    'severity': 'warning',
                    'message': f'High memory usage: {memory.percent}%',
                    'component': 'system'
                })
                health_status['overall_status'] = 'warning'
            
            if (disk.used / disk.total) * 100 > thresholds['disk_usage']:
                health_status['alerts'].append({
                    'severity': 'critical',
                    'message': f'Low disk space: {(disk.used / disk.total) * 100:.1f}%',
                    'component': 'system'
                })
                health_status['overall_status'] = 'critical'
            
            # Check services
            for service_name, service_config in self.monitoring_config['services'].items():
                if not service_config.get('enabled', True):
                    continue
                
                service_status = await self.check_service_health(service_name, service_config)
                health_status['components'][service_name] = service_status
                
                if service_status['status'] != 'healthy' and service_config.get('critical', False):
                    health_status['overall_status'] = 'critical'
            
            # Use health monitor if available
            if self.health_monitor:
                try:
                    component_health = await self.health_monitor.check_all_components()
                    for name, health in component_health.items():
                        health_status['components'][name] = {
                            'status': health.status.value,
                            'response_time': health.response_time,
                            'error_count': health.error_count,
                            'last_check': health.last_check.isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error checking component health: {e}")
            
        except Exception as e:
            logger.error(f"Error in system health check: {e}")
            health_status['overall_status'] = 'unknown'
            health_status['alerts'].append({
                'severity': 'error',
                'message': f'Health check failed: {str(e)}',
                'component': 'monitoring'
            })
        
        self.last_health_check = health_status
        return health_status
    
    async def check_service_health(self, service_name: str, service_config: Dict) -> Dict[str, Any]:
        """Check individual service health"""
        service_status = {
            'name': service_name,
            'status': 'unknown',
            'response_time': 0.0,
            'last_check': datetime.now().isoformat(),
            'error': None
        }
        
        try:
            if 'url' in service_config:
                # HTTP service check
                import aiohttp
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        service_config['url'],
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response_time = time.time() - start_time
                        service_status['response_time'] = response_time
                        
                        if response.status == 200:
                            service_status['status'] = 'healthy'
                        else:
                            service_status['status'] = 'warning'
                            service_status['error'] = f'HTTP {response.status}'
            
            elif 'process_name' in service_config:
                # Process check
                import psutil
                
                process_found = False
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if (service_config['process_name'] in proc.info['name'] and
                            service_config.get('script_name', '') in ' '.join(proc.info['cmdline'] or [])):
                            process_found = True
                            service_status['status'] = 'healthy'
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not process_found:
                    service_status['status'] = 'critical'
                    service_status['error'] = 'Process not running'
        
        except Exception as e:
            service_status['status'] = 'critical'
            service_status['error'] = str(e)
        
        return service_status
    
    async def send_alert(self, alert_data: Dict[str, Any]):
        """Send alert through configured channels"""
        try:
            severity = alert_data.get('severity', 'info')
            title = alert_data.get('title', 'System Alert')
            message = alert_data.get('message', '')
            component = alert_data.get('component', 'unknown')
            
            # Send Slack notification if enabled
            if (self.alert_config['notifications']['slack']['enabled'] and
                self.alert_config['notifications']['slack']['webhook_url']):
                
                await self.send_slack_alert(severity, title, message, component)
            
            # Send email notification if enabled
            if self.alert_config['notifications']['email']['enabled']:
                await self.send_email_alert(severity, title, message, component)
            
            # Use alert manager if available
            if self.alert_manager:
                try:
                    alert_severity = getattr(AlertSeverity, severity.upper(), AlertSeverity.INFO)
                    self.alert_manager.send_alert(
                        title=title,
                        message=message,
                        severity=alert_severity,
                        source=component
                    )
                except Exception as e:
                    logger.error(f"Error using alert manager: {e}")
            
            # Log alert
            self.alert_history.append({
                'timestamp': datetime.now().isoformat(),
                'severity': severity,
                'title': title,
                'message': message,
                'component': component
            })
            
            logger.info(f"Alert sent: {severity} - {title}")
        
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def send_slack_alert(self, severity: str, title: str, message: str, component: str):
        """Send Slack alert"""
        try:
            # Use existing Slack notification function
            if severity in ['critical', 'emergency']:
                send_slack_prophetic('fail', status=f"{title}: {message}")
            else:
                send_slack_prophetic('custom', message_type=f"{severity.upper()}: {title}\n{message}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    async def send_email_alert(self, severity: str, title: str, message: str, component: str):
        """Send email alert"""
        try:
            if self.notification_manager:
                await self.notification_manager.send_error_alert(
                    error_type=f"{severity.upper()}: {component}",
                    error_message=f"{title}\n{message}"
                )
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    async def monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring loop")
        
        while not self.stop_event.is_set():
            try:
                # Perform health check
                health_status = await self.check_system_health()
                
                # Process alerts
                for alert in health_status.get('alerts', []):
                    await self.send_alert({
                        'severity': alert['severity'],
                        'title': f"{alert['component'].title()} Alert",
                        'message': alert['message'],
                        'component': alert['component']
                    })
                
                # Save metrics
                self.save_metrics(health_status)
                
                # Wait for next check
                await asyncio.sleep(self.monitoring_config['monitoring']['check_interval'])
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def save_metrics(self, health_status: Dict[str, Any]):
        """Save metrics to file"""
        try:
            metrics_file = Path('data/monitoring/metrics.jsonl')
            with open(metrics_file, 'a') as f:
                f.write(json.dumps(health_status) + '\n')
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def start_monitoring(self):
        """Start monitoring service"""
        if self.running:
            logger.warning("Monitoring service is already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # Start monitoring in separate thread
        self.monitor_thread = threading.Thread(
            target=lambda: asyncio.run(self.monitoring_loop()),
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("Enhanced monitoring service started")
    
    def stop_monitoring(self):
        """Stop monitoring service"""
        if not self.running:
            logger.warning("Monitoring service is not running")
            return
        
        self.running = False
        self.stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        logger.info("Enhanced monitoring service stopped")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            'service_status': {
                'running': self.running,
                'uptime': time.time() - (self.last_health_check or {}).get('timestamp', time.time()) if self.running else 0
            },
            'last_health_check': self.last_health_check,
            'recent_alerts': self.alert_history[-10:] if self.alert_history else [],
            'configuration': {
                'monitoring_interval': self.monitoring_config['monitoring']['check_interval'],
                'enabled_services': [name for name, config in self.monitoring_config['services'].items() if config.get('enabled', True)],
                'alert_channels': [channel for channel, config in self.alert_config['notifications'].items() if config.get('enabled', False)]
            }
        }

def main():
    """Main function for running the enhanced monitoring service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel - Enhanced Monitoring Service')
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--status', action='store_true', help='Show status report')
    
    args = parser.parse_args()
    
    # Initialize monitoring service
    monitoring_service = EnhancedMonitoringService(config_dir=args.config_dir)
    
    if args.status:
        # Show status report
        status = monitoring_service.get_status_report()
        print(json.dumps(status, indent=2, default=str))
        return
    
    try:
        # Start monitoring
        monitoring_service.start_monitoring()
        
        if args.daemon:
            # Run as daemon
            while True:
                time.sleep(60)
        else:
            # Interactive mode
            print("Enhanced monitoring service started. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping monitoring service...")
        monitoring_service.stop_monitoring()
        print("Monitoring service stopped.")
    
    except Exception as e:
        logger.error(f"Error running monitoring service: {e}")
        monitoring_service.stop_monitoring()
        sys.exit(1)

if __name__ == '__main__':
    main()