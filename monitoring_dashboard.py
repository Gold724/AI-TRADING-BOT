#!/usr/bin/env python3
"""
AI Trading Sentinel - Production Monitoring Dashboard
TRAE-SentinelOps: Real-time monitoring and control interface

Provides:
- Real-time system metrics and health status
- Service control (start/stop/restart)
- Trading bot monitoring and control
- Alert management and notifications
- Performance analytics and reporting
- Emergency controls and safety measures
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import psutil
import redis
import sqlite3
from flask import Flask, render_template, jsonify, request, websocket
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.health_monitor import HealthMonitor
from monitoring_system import MonitoringSystem
from enhanced_monitoring_service import EnhancedMonitoringService

class ProductionDashboard:
    """Production monitoring dashboard for AI Trading Sentinel"""
    
    def __init__(self, config_dir: str = "/etc/trae-sentinel"):
        self.config_dir = Path(config_dir)
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
        
        # Enable CORS for development
        CORS(self.app)
        
        # Initialize SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize monitoring components
        self.health_monitor = None
        self.monitoring_system = None
        self.enhanced_monitor = None
        
        # Dashboard state
        self.dashboard_state = {
            'system_status': 'unknown',
            'trading_status': 'stopped',
            'last_update': None,
            'alerts': [],
            'metrics': {},
            'services': {}
        }
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.load_configuration()
        
        # Initialize monitoring
        self.initialize_monitoring()
        
        # Setup routes
        self.setup_routes()
        
        # Setup WebSocket handlers
        self.setup_websocket_handlers()
        
        # Start background tasks
        self.start_background_tasks()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("/var/log/trae-sentinel")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "dashboard.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def load_configuration(self):
        """Load dashboard configuration"""
        try:
            # Load environment variables
            env_file = self.config_dir / ".env"
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
            
            # Load monitoring configuration
            monitoring_config_file = self.config_dir / "monitoring_config.json"
            if monitoring_config_file.exists():
                with open(monitoring_config_file) as f:
                    self.monitoring_config = json.load(f)
            else:
                self.monitoring_config = self.get_default_monitoring_config()
            
            # Load alert configuration
            alert_config_file = self.config_dir / "alert_config.json"
            if alert_config_file.exists():
                with open(alert_config_file) as f:
                    self.alert_config = json.load(f)
            else:
                self.alert_config = self.get_default_alert_config()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            # Use default configurations
            self.monitoring_config = self.get_default_monitoring_config()
            self.alert_config = self.get_default_alert_config()
    
    def get_default_monitoring_config(self) -> Dict:
        """Get default monitoring configuration"""
        return {
            "system_thresholds": {
                "cpu_warning": 70,
                "cpu_critical": 90,
                "memory_warning": 80,
                "memory_critical": 95,
                "disk_warning": 85,
                "disk_critical": 95
            },
            "service_urls": {
                "backend": "http://localhost:5000/api/health",
                "frontend": "http://localhost:3000",
                "redis": "redis://localhost:6379"
            },
            "update_interval": 5,
            "alert_cooldown": 300
        }
    
    def get_default_alert_config(self) -> Dict:
        """Get default alert configuration"""
        return {
            "notifications": {
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channels": {
                        "critical": "#alerts-critical",
                        "warning": "#alerts-warning",
                        "info": "#alerts-info"
                    }
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                }
            }
        }
    
    def initialize_monitoring(self):
        """Initialize monitoring components"""
        try:
            # Initialize health monitor
            self.health_monitor = HealthMonitor(
                check_interval=self.monitoring_config.get("update_interval", 5)
            )
            
            # Initialize monitoring system
            self.monitoring_system = MonitoringSystem(
                config_file=str(self.config_dir / "monitoring_config.json")
            )
            
            # Initialize enhanced monitoring service
            self.enhanced_monitor = EnhancedMonitoringService(
                config_dir=str(self.config_dir)
            )
            
            self.logger.info("Monitoring components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing monitoring: {e}")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get current system status"""
            return jsonify(self.get_system_status())
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get system metrics"""
            return jsonify(self.get_system_metrics())
        
        @self.app.route('/api/services')
        def get_services():
            """Get service status"""
            return jsonify(self.get_service_status())
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get current alerts"""
            return jsonify(self.get_current_alerts())
        
        @self.app.route('/api/trading/status')
        def get_trading_status():
            """Get trading bot status"""
            return jsonify(self.get_trading_bot_status())
        
        @self.app.route('/api/trading/control', methods=['POST'])
        def control_trading():
            """Control trading bot (start/stop/restart)"""
            action = request.json.get('action')
            return jsonify(self.control_trading_bot(action))
        
        @self.app.route('/api/services/control', methods=['POST'])
        def control_service():
            """Control system services"""
            service = request.json.get('service')
            action = request.json.get('action')
            return jsonify(self.control_system_service(service, action))
        
        @self.app.route('/api/logs/<service>')
        def get_logs(service):
            """Get service logs"""
            lines = request.args.get('lines', 100, type=int)
            return jsonify(self.get_service_logs(service, lines))
        
        @self.app.route('/api/emergency/stop', methods=['POST'])
        def emergency_stop():
            """Emergency stop all trading activities"""
            return jsonify(self.emergency_stop_all())
    
    def setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.logger.info("Client connected to dashboard")
            emit('status_update', self.dashboard_state)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.logger.info("Client disconnected from dashboard")
        
        @self.socketio.on('request_update')
        def handle_update_request():
            """Handle manual update request"""
            self.update_dashboard_state()
            emit('status_update', self.dashboard_state)
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        
        @self.socketio.on('connect')
        def start_monitoring():
            """Start monitoring when first client connects"""
            if not hasattr(self, '_monitoring_task'):
                self._monitoring_task = self.socketio.start_background_task(
                    target=self.monitoring_loop
                )
    
    def monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                self.update_dashboard_state()
                self.socketio.emit('status_update', self.dashboard_state)
                self.socketio.sleep(self.monitoring_config.get("update_interval", 5))
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self.socketio.sleep(10)
    
    def update_dashboard_state(self):
        """Update dashboard state with current system information"""
        try:
            # Update system status
            self.dashboard_state['system_status'] = self.get_overall_system_status()
            
            # Update trading status
            self.dashboard_state['trading_status'] = self.get_trading_bot_status()['status']
            
            # Update metrics
            self.dashboard_state['metrics'] = self.get_system_metrics()
            
            # Update services
            self.dashboard_state['services'] = self.get_service_status()
            
            # Update alerts
            self.dashboard_state['alerts'] = self.get_current_alerts()
            
            # Update timestamp
            self.dashboard_state['last_update'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard state: {e}")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'overall_status': self.get_overall_system_status(),
            'uptime': self.get_system_uptime(),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_metrics(self) -> Dict:
        """Get system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'status': self.get_metric_status(cpu_percent, 'cpu')
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'status': self.get_metric_status(memory.percent, 'memory')
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100,
                    'status': self.get_metric_status((disk.used / disk.total) * 100, 'disk')
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_metric_status(self, value: float, metric_type: str) -> str:
        """Get status based on metric value and thresholds"""
        thresholds = self.monitoring_config['system_thresholds']
        
        warning_threshold = thresholds.get(f"{metric_type}_warning", 70)
        critical_threshold = thresholds.get(f"{metric_type}_critical", 90)
        
        if value >= critical_threshold:
            return 'critical'
        elif value >= warning_threshold:
            return 'warning'
        else:
            return 'healthy'
    
    def get_service_status(self) -> Dict:
        """Get status of all monitored services"""
        services = {}
        
        # System services
        system_services = [
            'trae-enhanced-monitor.service',
            'trae-backend.service',
            'trae-trading-bot.service',
            'nginx',
            'redis-server'
        ]
        
        for service in system_services:
            services[service] = self.get_systemd_service_status(service)
        
        # Application services
        app_services = self.monitoring_config.get('service_urls', {})
        for service, url in app_services.items():
            services[f"app_{service}"] = self.check_service_health(url)
        
        return services
    
    def get_systemd_service_status(self, service_name: str) -> Dict:
        """Get systemd service status"""
        try:
            import subprocess
            
            # Check if service is active
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            
            is_active = result.returncode == 0
            
            # Get service status details
            status_result = subprocess.run(
                ['systemctl', 'status', service_name, '--no-pager', '-l'],
                capture_output=True,
                text=True
            )
            
            return {
                'status': 'active' if is_active else 'inactive',
                'enabled': self.is_service_enabled(service_name),
                'details': status_result.stdout if status_result.returncode == 0 else 'Service not found'
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'enabled': False,
                'details': f'Error checking service: {e}'
            }
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if systemd service is enabled"""
        try:
            import subprocess
            result = subprocess.run(
                ['systemctl', 'is-enabled', service_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def check_service_health(self, url: str) -> Dict:
        """Check application service health via HTTP"""
        try:
            import requests
            response = requests.get(url, timeout=5)
            
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'status': 'unreachable',
                'error': str(e)
            }
    
    def get_current_alerts(self) -> List[Dict]:
        """Get current system alerts"""
        alerts = []
        
        # Check system metrics for alerts
        metrics = self.get_system_metrics()
        
        for metric_type, metric_data in metrics.items():
            if isinstance(metric_data, dict) and 'status' in metric_data:
                if metric_data['status'] in ['warning', 'critical']:
                    alerts.append({
                        'type': 'system',
                        'severity': metric_data['status'],
                        'message': f"{metric_type.upper()} usage is {metric_data.get('percent', 0):.1f}%",
                        'timestamp': datetime.now().isoformat(),
                        'metric': metric_type
                    })
        
        # Check service alerts
        services = self.get_service_status()
        for service_name, service_data in services.items():
            if service_data.get('status') not in ['active', 'healthy']:
                alerts.append({
                    'type': 'service',
                    'severity': 'critical' if 'trading' in service_name else 'warning',
                    'message': f"Service {service_name} is {service_data.get('status', 'unknown')}",
                    'timestamp': datetime.now().isoformat(),
                    'service': service_name
                })
        
        return alerts
    
    def get_trading_bot_status(self) -> Dict:
        """Get trading bot status and statistics"""
        try:
            # Check if trading bot service is running
            service_status = self.get_systemd_service_status('trae-trading-bot.service')
            
            # Try to get trading statistics from database
            stats = self.get_trading_statistics()
            
            return {
                'status': service_status['status'],
                'enabled': service_status['enabled'],
                'statistics': stats,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e),
                'last_update': datetime.now().isoformat()
            }
    
    def get_trading_statistics(self) -> Dict:
        """Get trading statistics from database"""
        try:
            db_path = "/var/lib/trae-sentinel/trading_bot.db"
            if not os.path.exists(db_path):
                return {'error': 'Database not found'}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get basic statistics
            stats = {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'total_profit_loss': 0.0,
                'last_trade_time': None
            }
            
            # Query trade statistics (adjust based on your database schema)
            try:
                cursor.execute("SELECT COUNT(*) FROM trades")
                stats['total_trades'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'success'")
                stats['successful_trades'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'failed'")
                stats['failed_trades'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(profit_loss) FROM trades WHERE profit_loss IS NOT NULL")
                result = cursor.fetchone()[0]
                stats['total_profit_loss'] = result if result else 0.0
                
                cursor.execute("SELECT MAX(timestamp) FROM trades")
                stats['last_trade_time'] = cursor.fetchone()[0]
                
            except sqlite3.OperationalError:
                # Tables might not exist yet
                pass
            
            conn.close()
            return stats
            
        except Exception as e:
            return {'error': f'Database error: {e}'}
    
    def control_trading_bot(self, action: str) -> Dict:
        """Control trading bot (start/stop/restart)"""
        try:
            import subprocess
            
            service_name = 'trae-trading-bot.service'
            
            if action == 'start':
                result = subprocess.run(['systemctl', 'start', service_name], capture_output=True, text=True)
            elif action == 'stop':
                result = subprocess.run(['systemctl', 'stop', service_name], capture_output=True, text=True)
            elif action == 'restart':
                result = subprocess.run(['systemctl', 'restart', service_name], capture_output=True, text=True)
            else:
                return {'success': False, 'error': f'Invalid action: {action}'}
            
            success = result.returncode == 0
            
            return {
                'success': success,
                'action': action,
                'message': f'Trading bot {action} {"successful" if success else "failed"}',
                'output': result.stdout if success else result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def control_system_service(self, service: str, action: str) -> Dict:
        """Control system service"""
        try:
            import subprocess
            
            # Validate service name for security
            allowed_services = [
                'trae-enhanced-monitor.service',
                'trae-backend.service',
                'nginx',
                'redis-server'
            ]
            
            if service not in allowed_services:
                return {'success': False, 'error': f'Service {service} not allowed'}
            
            if action not in ['start', 'stop', 'restart', 'reload']:
                return {'success': False, 'error': f'Invalid action: {action}'}
            
            result = subprocess.run(['systemctl', action, service], capture_output=True, text=True)
            success = result.returncode == 0
            
            return {
                'success': success,
                'service': service,
                'action': action,
                'message': f'Service {service} {action} {"successful" if success else "failed"}',
                'output': result.stdout if success else result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_service_logs(self, service: str, lines: int = 100) -> Dict:
        """Get service logs"""
        try:
            import subprocess
            
            # Map service names to log files or systemd units
            log_mapping = {
                'trading-bot': 'trae-trading-bot.service',
                'backend': 'trae-backend.service',
                'monitor': 'trae-enhanced-monitor.service',
                'nginx': 'nginx.service',
                'redis': 'redis-server.service'
            }
            
            if service in log_mapping:
                # Get systemd logs
                result = subprocess.run(
                    ['journalctl', '-u', log_mapping[service], '-n', str(lines), '--no-pager'],
                    capture_output=True,
                    text=True
                )
            else:
                # Try to get from log file
                log_file = f"/var/log/trae-sentinel/{service}.log"
                if os.path.exists(log_file):
                    result = subprocess.run(
                        ['tail', '-n', str(lines), log_file],
                        capture_output=True,
                        text=True
                    )
                else:
                    return {'success': False, 'error': f'Log source not found for {service}'}
            
            return {
                'success': result.returncode == 0,
                'logs': result.stdout if result.returncode == 0 else result.stderr,
                'service': service,
                'lines': lines
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def emergency_stop_all(self) -> Dict:
        """Emergency stop all trading activities"""
        try:
            import subprocess
            
            results = []
            
            # Stop trading bot
            result = subprocess.run(['systemctl', 'stop', 'trae-trading-bot.service'], capture_output=True, text=True)
            results.append({
                'service': 'trae-trading-bot.service',
                'success': result.returncode == 0,
                'output': result.stdout if result.returncode == 0 else result.stderr
            })
            
            # Kill any remaining trading processes
            try:
                subprocess.run(['pkill', '-f', 'trading_bot'], capture_output=True)
                subprocess.run(['pkill', '-f', 'bulenox'], capture_output=True)
            except:
                pass
            
            # Log emergency stop
            self.logger.critical("EMERGENCY STOP ACTIVATED - All trading activities stopped")
            
            return {
                'success': True,
                'message': 'Emergency stop completed',
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_overall_system_status(self) -> str:
        """Get overall system health status"""
        try:
            # Check critical metrics
            metrics = self.get_system_metrics()
            
            critical_issues = 0
            warning_issues = 0
            
            for metric_type, metric_data in metrics.items():
                if isinstance(metric_data, dict) and 'status' in metric_data:
                    if metric_data['status'] == 'critical':
                        critical_issues += 1
                    elif metric_data['status'] == 'warning':
                        warning_issues += 1
            
            # Check critical services
            services = self.get_service_status()
            critical_services_down = 0
            
            critical_service_names = ['trae-backend.service', 'nginx', 'redis-server']
            for service_name in critical_service_names:
                if services.get(service_name, {}).get('status') != 'active':
                    critical_services_down += 1
            
            # Determine overall status
            if critical_issues > 0 or critical_services_down > 0:
                return 'critical'
            elif warning_issues > 0:
                return 'warning'
            else:
                return 'healthy'
                
        except Exception as e:
            self.logger.error(f"Error determining system status: {e}")
            return 'unknown'
    
    def get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            
            uptime_timedelta = timedelta(seconds=uptime_seconds)
            days = uptime_timedelta.days
            hours, remainder = divmod(uptime_timedelta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            return f"{days}d {hours}h {minutes}m"
        except:
            return "Unknown"
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Run the dashboard server"""
        self.logger.info(f"Starting Production Dashboard on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Production Dashboard')
    parser.add_argument('--config-dir', default='/etc/trae-sentinel', help='Configuration directory')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run dashboard
    dashboard = ProductionDashboard(config_dir=args.config_dir)
    dashboard.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()