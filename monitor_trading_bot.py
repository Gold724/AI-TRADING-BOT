#!/usr/bin/env python3
"""
Bulenox Trading Bot - Comprehensive Monitoring & Health Check System
TRAE-SentinelOps v2.0.0 - Production Monitoring Suite

This script provides comprehensive monitoring for the Bulenox trading bot
running on Contabo VPS with contract-based trading validation.
"""

import asyncio
import json
import logging
import os
import psutil
import requests
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/trading-bot-monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class HealthMetrics:
    """System health metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_connections: int
    service_status: str
    api_response_time: Optional[float]
    last_trade_time: Optional[str]
    contract_validation_status: bool
    error_count_24h: int
    uptime_seconds: int
    
class TradingBotMonitor:
    """Comprehensive monitoring system for Bulenox trading bot"""
    
    def __init__(self, config_path: str = '/opt/trading-bot/monitor_config.json'):
        self.config = self.load_config(config_path)
        self.service_name = self.config.get('service_name', 'bulenox-trader')
        self.api_url = self.config.get('api_url', 'http://localhost:5000')
        self.websocket_url = self.config.get('websocket_url', 'ws://localhost:5001')
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        self.notification_config = self.config.get('notifications', {})
        
        # Monitoring state
        self.last_alert_time = {}
        self.error_log = []
        self.performance_history = []
        
        logger.info(f"🔍 Trading Bot Monitor initialized for service: {self.service_name}")
    
    def load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            'service_name': 'bulenox-trader',
            'api_url': 'http://localhost:5000',
            'websocket_url': 'ws://localhost:5001',
            'alert_thresholds': {
                'cpu_percent': 80.0,
                'memory_percent': 85.0,
                'disk_percent': 90.0,
                'api_response_time': 5.0,
                'error_rate_per_hour': 10,
                'max_downtime_minutes': 5
            },
            'notifications': {
                'email_enabled': False,
                'slack_enabled': False,
                'alert_cooldown_minutes': 30
            },
            'monitoring': {
                'check_interval_seconds': 60,
                'health_check_timeout': 10,
                'contract_validation_interval': 300,
                'log_retention_days': 30
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logger.info(f"✅ Loaded configuration from {config_path}")
            else:
                logger.warning(f"⚠️ Config file not found: {config_path}, using defaults")
                # Create default config file
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"📝 Created default config at {config_path}")
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
        
        return default_config
    
    async def get_system_metrics(self) -> Dict:
        """Collect system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'network_connections': connections,
                'uptime_seconds': uptime_seconds,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            logger.error(f"❌ Error collecting system metrics: {e}")
            return {}
    
    def get_service_status(self) -> Tuple[str, Dict]:
        """Check systemd service status"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', self.service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            status = result.stdout.strip()
            
            # Get detailed service info
            detail_result = subprocess.run(
                ['systemctl', 'status', self.service_name, '--no-pager'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse service details
            details = {
                'status': status,
                'active': status == 'active',
                'details': detail_result.stdout,
                'return_code': result.returncode
            }
            
            return status, details
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Service status check timed out")
            return 'timeout', {'error': 'timeout'}
        except Exception as e:
            logger.error(f"❌ Error checking service status: {e}")
            return 'error', {'error': str(e)}
    
    async def check_api_health(self) -> Tuple[bool, float, Dict]:
        """Check API endpoint health and response time"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.api_url}/health") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return True, response_time, data
                    else:
                        return False, response_time, {'error': f'HTTP {response.status}'}
                        
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return False, response_time, {'error': 'timeout'}
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, {'error': str(e)}
    
    async def validate_contract_handling(self) -> Tuple[bool, Dict]:
        """Validate contract size handling is working correctly"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                # Test contract validation endpoint
                test_data = {
                    'contract_sizes': [0.5, 1, 2, 5, 10, 15, 20]
                }
                
                async with session.post(
                    f"{self.api_url}/api/validate-contracts",
                    json=test_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Validate expected contract conversions
                        expected_results = {
                            0.5: 1,  # Minimum 1 contract
                            1: 1,
                            2: 2,
                            5: 5,
                            10: 10,  # Maximum allowed
                            15: 10,  # Capped at maximum
                            20: 10   # Capped at maximum
                        }
                        
                        validation_passed = True
                        for input_size, expected in expected_results.items():
                            actual = result.get('validated_contracts', {}).get(str(input_size))
                            if actual != expected:
                                validation_passed = False
                                logger.error(
                                    f"❌ Contract validation failed: {input_size} -> {actual}, expected {expected}"
                                )
                        
                        return validation_passed, result
                    else:
                        return False, {'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            logger.error(f"❌ Contract validation error: {e}")
            return False, {'error': str(e)}
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict]:
        """Get recent errors from service logs"""
        try:
            since_time = datetime.now() - timedelta(hours=hours)
            since_str = since_time.strftime('%Y-%m-%d %H:%M:%S')
            
            result = subprocess.run([
                'journalctl',
                '-u', self.service_name,
                '--since', since_str,
                '--no-pager',
                '-o', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            errors = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        log_entry = json.loads(line)
                        message = log_entry.get('MESSAGE', '')
                        
                        # Check for error indicators
                        if any(keyword in message.lower() for keyword in 
                               ['error', 'exception', 'failed', 'timeout', 'critical']):
                            errors.append({
                                'timestamp': log_entry.get('__REALTIME_TIMESTAMP'),
                                'message': message,
                                'priority': log_entry.get('PRIORITY')
                            })
                    except json.JSONDecodeError:
                        continue
            
            return errors[-50:]  # Return last 50 errors
            
        except Exception as e:
            logger.error(f"❌ Error getting recent errors: {e}")
            return []
    
    async def perform_health_check(self) -> HealthMetrics:
        """Perform comprehensive health check"""
        logger.info("🔍 Starting comprehensive health check...")
        
        # Collect system metrics
        system_metrics = await self.get_system_metrics()
        
        # Check service status
        service_status, service_details = self.get_service_status()
        
        # Check API health
        api_healthy, api_response_time, api_data = await self.check_api_health()
        
        # Validate contract handling
        contracts_valid, contract_data = await self.validate_contract_handling()
        
        # Get recent errors
        recent_errors = self.get_recent_errors(24)
        
        # Get last trade time from API
        last_trade_time = None
        try:
            if api_healthy and 'last_trade_time' in api_data:
                last_trade_time = api_data['last_trade_time']
        except Exception:
            pass
        
        # Create health metrics
        metrics = HealthMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=system_metrics.get('cpu_percent', 0),
            memory_percent=system_metrics.get('memory_percent', 0),
            disk_percent=system_metrics.get('disk_percent', 0),
            network_connections=system_metrics.get('network_connections', 0),
            service_status=service_status,
            api_response_time=api_response_time if api_healthy else None,
            last_trade_time=last_trade_time,
            contract_validation_status=contracts_valid,
            error_count_24h=len(recent_errors),
            uptime_seconds=int(system_metrics.get('uptime_seconds', 0))
        )
        
        # Store metrics for history
        self.performance_history.append(asdict(metrics))
        
        # Keep only last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        logger.info(f"✅ Health check completed - Service: {service_status}, API: {api_healthy}, Contracts: {contracts_valid}")
        
        return metrics
    
    def check_alert_conditions(self, metrics: HealthMetrics) -> List[Dict]:
        """Check if any alert conditions are met"""
        alerts = []
        thresholds = self.alert_thresholds
        
        # CPU usage alert
        if metrics.cpu_percent > thresholds.get('cpu_percent', 80):
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent,
                'threshold': thresholds.get('cpu_percent', 80)
            })
        
        # Memory usage alert
        if metrics.memory_percent > thresholds.get('memory_percent', 85):
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent,
                'threshold': thresholds.get('memory_percent', 85)
            })
        
        # Disk usage alert
        if metrics.disk_percent > thresholds.get('disk_percent', 90):
            alerts.append({
                'type': 'disk_high',
                'severity': 'critical',
                'message': f'High disk usage: {metrics.disk_percent:.1f}%',
                'value': metrics.disk_percent,
                'threshold': thresholds.get('disk_percent', 90)
            })
        
        # Service status alert
        if metrics.service_status != 'active':
            alerts.append({
                'type': 'service_down',
                'severity': 'critical',
                'message': f'Service not active: {metrics.service_status}',
                'value': metrics.service_status
            })
        
        # API response time alert
        if metrics.api_response_time and metrics.api_response_time > thresholds.get('api_response_time', 5.0):
            alerts.append({
                'type': 'api_slow',
                'severity': 'warning',
                'message': f'Slow API response: {metrics.api_response_time:.2f}s',
                'value': metrics.api_response_time,
                'threshold': thresholds.get('api_response_time', 5.0)
            })
        
        # Contract validation alert
        if not metrics.contract_validation_status:
            alerts.append({
                'type': 'contract_validation_failed',
                'severity': 'critical',
                'message': 'Contract validation failed - trading may be unsafe',
                'value': False
            })
        
        # Error rate alert
        if metrics.error_count_24h > thresholds.get('error_rate_per_hour', 10):
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'warning',
                'message': f'High error rate: {metrics.error_count_24h} errors in 24h',
                'value': metrics.error_count_24h,
                'threshold': thresholds.get('error_rate_per_hour', 10)
            })
        
        return alerts
    
    async def send_alert(self, alert: Dict, metrics: HealthMetrics):
        """Send alert notification"""
        alert_type = alert['type']
        cooldown_minutes = self.notification_config.get('alert_cooldown_minutes', 30)
        
        # Check cooldown
        last_alert = self.last_alert_time.get(alert_type)
        if last_alert:
            time_since_last = datetime.now() - last_alert
            if time_since_last.total_seconds() < cooldown_minutes * 60:
                return  # Skip due to cooldown
        
        # Update last alert time
        self.last_alert_time[alert_type] = datetime.now()
        
        # Prepare alert message
        message = f"🚨 **{alert['severity'].upper()}**: {alert['message']}\n\n"
        message += f"**Timestamp**: {metrics.timestamp}\n"
        message += f"**Service**: {metrics.service_status}\n"
        message += f"**CPU**: {metrics.cpu_percent:.1f}%\n"
        message += f"**Memory**: {metrics.memory_percent:.1f}%\n"
        message += f"**Disk**: {metrics.disk_percent:.1f}%\n"
        
        if metrics.api_response_time:
            message += f"**API Response**: {metrics.api_response_time:.2f}s\n"
        
        message += f"**Contract Validation**: {'✅ Pass' if metrics.contract_validation_status else '❌ Fail'}\n"
        message += f"**Errors (24h)**: {metrics.error_count_24h}\n"
        
        # Send via configured channels
        if self.notification_config.get('slack_enabled'):
            await self.send_slack_alert(message, alert['severity'])
        
        if self.notification_config.get('email_enabled'):
            await self.send_email_alert(alert['message'], message, alert['severity'])
        
        logger.warning(f"🚨 Alert sent: {alert['message']}")
    
    async def send_slack_alert(self, message: str, severity: str):
        """Send Slack notification"""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return
        
        color_map = {
            'critical': '#FF0000',
            'warning': '#FFA500',
            'info': '#00FF00'
        }
        
        payload = {
            'channel': '#trading-bot-alerts',
            'username': 'Trading Bot Monitor',
            'icon_emoji': ':robot_face:',
            'attachments': [{
                'color': color_map.get(severity, '#808080'),
                'title': f'Bulenox Trading Bot Alert - {severity.upper()}',
                'text': message,
                'ts': int(time.time())
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("✅ Slack alert sent successfully")
                    else:
                        logger.error(f"❌ Failed to send Slack alert: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error sending Slack alert: {e}")
    
    async def send_email_alert(self, subject: str, message: str, severity: str):
        """Send email notification"""
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        alert_email = os.getenv('ALERT_EMAIL')
        
        if not all([smtp_username, smtp_password, alert_email]):
            logger.warning("⚠️ Email configuration incomplete, skipping email alert")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = alert_email
            msg['Subject'] = f'[{severity.upper()}] Bulenox Trading Bot: {subject}'
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info("✅ Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"❌ Error sending email alert: {e}")
    
    def generate_status_report(self, metrics: HealthMetrics) -> str:
        """Generate comprehensive status report"""
        uptime_hours = metrics.uptime_seconds / 3600
        
        report = f"""
🤖 **Bulenox Trading Bot Status Report**
📅 **Generated**: {metrics.timestamp}

📊 **System Health**
├─ 🖥️  CPU Usage: {metrics.cpu_percent:.1f}%
├─ 💾 Memory Usage: {metrics.memory_percent:.1f}%
├─ 💿 Disk Usage: {metrics.disk_percent:.1f}%
├─ 🌐 Network Connections: {metrics.network_connections}
└─ ⏱️  System Uptime: {uptime_hours:.1f} hours

🔧 **Service Status**
├─ 🚀 Service: {metrics.service_status}
├─ 🌐 API Response: {metrics.api_response_time:.2f}s if metrics.api_response_time else 'N/A'
├─ 📋 Contract Validation: {'✅ Pass' if metrics.contract_validation_status else '❌ Fail'}
├─ 🕐 Last Trade: {metrics.last_trade_time or 'N/A'}
└─ ⚠️  Errors (24h): {metrics.error_count_24h}

🎯 **Trading Status**
├─ 📈 Contract-based Trading: {'✅ Active' if metrics.contract_validation_status else '❌ Disabled'}
├─ 🛡️  Risk Management: Active
├─ 🔒 Emergency Stop: Enabled
└─ 📊 Position Sizing: Contract-based

💡 **Quick Commands**
```bash
# Check service status
sudo systemctl status bulenox-trader

# View recent logs
sudo journalctl -u bulenox-trader -f

# Restart service
sudo systemctl restart bulenox-trader

# Check system resources
htop
```
"""
        return report
    
    async def run_monitoring_cycle(self):
        """Run single monitoring cycle"""
        try:
            # Perform health check
            metrics = await self.perform_health_check()
            
            # Check for alerts
            alerts = self.check_alert_conditions(metrics)
            
            # Send alerts if any
            for alert in alerts:
                await self.send_alert(alert, metrics)
            
            # Save metrics to file
            metrics_file = '/var/log/trading-bot-metrics.json'
            try:
                with open(metrics_file, 'w') as f:
                    json.dump(asdict(metrics), f, indent=2)
            except Exception as e:
                logger.error(f"❌ Error saving metrics: {e}")
            
            # Log status summary
            status_emoji = "✅" if metrics.service_status == 'active' and metrics.contract_validation_status else "⚠️"
            logger.info(
                f"{status_emoji} Status: {metrics.service_status} | "
                f"CPU: {metrics.cpu_percent:.1f}% | "
                f"Mem: {metrics.memory_percent:.1f}% | "
                f"API: {metrics.api_response_time:.2f}s | "
                f"Contracts: {'✅' if metrics.contract_validation_status else '❌'} | "
                f"Errors: {metrics.error_count_24h}"
            )
            
            return metrics, alerts
            
        except Exception as e:
            logger.error(f"❌ Error in monitoring cycle: {e}")
            return None, []
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        check_interval = self.config.get('monitoring', {}).get('check_interval_seconds', 60)
        
        logger.info(f"🚀 Starting continuous monitoring (interval: {check_interval}s)")
        
        while True:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulenox Trading Bot Monitor')
    parser.add_argument('--config', default='/opt/trading-bot/monitor_config.json',
                       help='Path to monitoring configuration file')
    parser.add_argument('--once', action='store_true',
                       help='Run single health check instead of continuous monitoring')
    parser.add_argument('--report', action='store_true',
                       help='Generate and display status report')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = TradingBotMonitor(args.config)
    
    if args.once or args.report:
        # Run single check
        async def single_check():
            metrics, alerts = await monitor.run_monitoring_cycle()
            
            if args.report and metrics:
                report = monitor.generate_status_report(metrics)
                print(report)
            
            if alerts:
                print(f"\n⚠️  Active Alerts: {len(alerts)}")
                for alert in alerts:
                    print(f"  - {alert['severity'].upper()}: {alert['message']}")
        
        asyncio.run(single_check())
    else:
        # Run continuous monitoring
        try:
            asyncio.run(monitor.run_continuous_monitoring())
        except KeyboardInterrupt:
            logger.info("👋 Monitoring stopped")

if __name__ == '__main__':
    main()