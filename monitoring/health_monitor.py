#!/usr/bin/env python3
"""
AI Trading Sentinel - Health Monitor
Continuous system health monitoring with auto-recovery capabilities
"""

import os
import sys
import time
import json
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class HealthMonitor:
    """Comprehensive system health monitoring and auto-recovery"""
    
    def __init__(self):
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.services = {
            'backend': {
                'name': 'trae-backend',
                'url': f"http://localhost:{self.config.get('API_PORT', 5000)}/api/health",
                'timeout': 10
            },
            'trading_bot': {
                'name': 'trae-trading-bot',
                'process_name': 'python',
                'process_args': 'main.py'
            }
        }
        self.alert_cooldown = {}
        self.restart_counts = {}
        self.last_health_check = datetime.now()
        
    def _load_config(self) -> Dict:
        """Load configuration from environment and .env file"""
        config = {}
        
        # Load from .env file if exists
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value.strip('"\'')
        
        # Override with environment variables
        config.update(os.environ)
        
        return config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = '/var/log/trae'
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger('health_monitor')
        logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(f'{log_dir}/health_monitor.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'status': 'healthy'
            }
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_service_status(self, service_name: str) -> Dict:
        """Check systemd service status"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_active = result.stdout.strip() == 'active'
            
            # Get detailed status
            status_result = subprocess.run(
                ['systemctl', 'status', service_name, '--no-pager', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                'service': service_name,
                'active': is_active,
                'status': result.stdout.strip(),
                'details': status_result.stdout,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'service': service_name,
                'active': False,
                'status': 'timeout',
                'error': 'Command timeout'
            }
        except Exception as e:
            return {
                'service': service_name,
                'active': False,
                'status': 'error',
                'error': str(e)
            }
    
    def check_api_health(self, url: str, timeout: int = 10) -> Dict:
        """Check API endpoint health"""
        try:
            response = requests.get(url, timeout=timeout)
            
            return {
                'url': url,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'healthy': response.status_code == 200,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
            }
        except requests.exceptions.Timeout:
            return {
                'url': url,
                'healthy': False,
                'error': 'timeout',
                'response_time': timeout
            }
        except requests.exceptions.ConnectionError:
            return {
                'url': url,
                'healthy': False,
                'error': 'connection_error'
            }
        except Exception as e:
            return {
                'url': url,
                'healthy': False,
                'error': str(e)
            }
    
    def check_process_health(self, process_name: str, process_args: str = None) -> Dict:
        """Check if specific process is running"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['name'] == process_name:
                        if process_args is None or any(process_args in arg for arg in proc.info['cmdline']):
                            processes.append({
                                'pid': proc.info['pid'],
                                'cmdline': ' '.join(proc.info['cmdline']),
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent']
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'process_name': process_name,
                'process_args': process_args,
                'running': len(processes) > 0,
                'count': len(processes),
                'processes': processes
            }
        except Exception as e:
            return {
                'process_name': process_name,
                'running': False,
                'error': str(e)
            }
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a systemd service"""
        try:
            # Check restart count to prevent restart loops
            current_time = datetime.now()
            if service_name not in self.restart_counts:
                self.restart_counts[service_name] = []
            
            # Remove restarts older than 1 hour
            self.restart_counts[service_name] = [
                restart_time for restart_time in self.restart_counts[service_name]
                if current_time - restart_time < timedelta(hours=1)
            ]
            
            # Check if too many restarts in the last hour
            if len(self.restart_counts[service_name]) >= 5:
                self.logger.error(f"Too many restarts for {service_name} in the last hour. Skipping restart.")
                return False
            
            self.logger.info(f"Restarting service: {service_name}")
            
            result = subprocess.run(
                ['systemctl', 'restart', service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.restart_counts[service_name].append(current_time)
                self.logger.info(f"Successfully restarted {service_name}")
                return True
            else:
                self.logger.error(f"Failed to restart {service_name}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting service {service_name}: {e}")
            return False
    
    def send_alert(self, subject: str, message: str, alert_type: str = 'error') -> bool:
        """Send alert via email or other notification methods"""
        try:
            # Check cooldown to prevent spam
            cooldown_key = f"{alert_type}_{subject}"
            current_time = datetime.now()
            
            if cooldown_key in self.alert_cooldown:
                if current_time - self.alert_cooldown[cooldown_key] < timedelta(minutes=30):
                    return False  # Skip alert due to cooldown
            
            self.alert_cooldown[cooldown_key] = current_time
            
            # Email notification
            if self.config.get('EMAIL_NOTIFICATIONS') == 'true':
                self._send_email_alert(subject, message)
            
            # Slack notification
            if self.config.get('SLACK_WEBHOOK_URL'):
                self._send_slack_alert(subject, message, alert_type)
            
            # Log the alert
            self.logger.warning(f"ALERT [{alert_type.upper()}]: {subject} - {message}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False
    
    def _send_email_alert(self, subject: str, message: str):
        """Send email alert"""
        try:
            smtp_server = self.config.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(self.config.get('SMTP_PORT', 587))
            email_user = self.config.get('EMAIL_USERNAME')
            email_pass = self.config.get('EMAIL_PASSWORD')
            email_to = self.config.get('ALERT_EMAIL', email_user)
            
            if not all([email_user, email_pass, email_to]):
                return
            
            msg = MimeMultipart()
            msg['From'] = email_user
            msg['To'] = email_to
            msg['Subject'] = f"[TRAE Alert] {subject}"
            
            body = f"""
            AI Trading Sentinel Alert
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Subject: {subject}
            
            Details:
            {message}
            
            --
            AI Trading Sentinel Health Monitor
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
    
    def _send_slack_alert(self, subject: str, message: str, alert_type: str):
        """Send Slack alert"""
        try:
            webhook_url = self.config.get('SLACK_WEBHOOK_URL')
            if not webhook_url:
                return
            
            color = {
                'error': '#ff0000',
                'warning': '#ffaa00',
                'info': '#00ff00'
            }.get(alert_type, '#cccccc')
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': f"🚨 TRAE Alert: {subject}",
                    'text': message,
                    'footer': 'AI Trading Sentinel Health Monitor',
                    'ts': int(datetime.now().timestamp())
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {e}")
    
    def run_health_check(self) -> Dict:
        """Run comprehensive health check"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        issues = []
        
        # Check system resources
        self.logger.info("Checking system resources...")
        system_check = self.check_system_resources()
        health_report['checks']['system'] = system_check
        
        if system_check.get('cpu_percent', 0) > 90:
            issues.append(f"High CPU usage: {system_check['cpu_percent']:.1f}%")
        
        if system_check.get('memory_percent', 0) > 90:
            issues.append(f"High memory usage: {system_check['memory_percent']:.1f}%")
        
        if system_check.get('disk_percent', 0) > 90:
            issues.append(f"High disk usage: {system_check['disk_percent']:.1f}%")
        
        # Check services
        for service_key, service_config in self.services.items():
            self.logger.info(f"Checking service: {service_config['name']}")
            
            service_check = self.check_service_status(service_config['name'])
            health_report['checks'][service_key] = service_check
            
            if not service_check.get('active', False):
                issues.append(f"Service {service_config['name']} is not active")
                
                # Attempt auto-restart
                if self.restart_service(service_config['name']):
                    self.send_alert(
                        f"Service Restarted: {service_config['name']}",
                        f"Service {service_config['name']} was down and has been automatically restarted.",
                        'warning'
                    )
                else:
                    self.send_alert(
                        f"Service Down: {service_config['name']}",
                        f"Service {service_config['name']} is down and restart failed.",
                        'error'
                    )
            
            # Check API health for backend
            if service_key == 'backend' and 'url' in service_config:
                api_check = self.check_api_health(service_config['url'], service_config.get('timeout', 10))
                health_report['checks'][f'{service_key}_api'] = api_check
                
                if not api_check.get('healthy', False):
                    issues.append(f"API endpoint {service_config['url']} is not healthy")
            
            # Check process health for trading bot
            if service_key == 'trading_bot' and 'process_name' in service_config:
                process_check = self.check_process_health(
                    service_config['process_name'],
                    service_config.get('process_args')
                )
                health_report['checks'][f'{service_key}_process'] = process_check
                
                if not process_check.get('running', False):
                    issues.append(f"Trading bot process is not running")
        
        # Set overall status
        if issues:
            health_report['overall_status'] = 'unhealthy'
            health_report['issues'] = issues
            
            # Send summary alert if there are critical issues
            critical_issues = [issue for issue in issues if 'down' in issue.lower() or 'not running' in issue.lower()]
            if critical_issues:
                self.send_alert(
                    "Critical System Issues Detected",
                    "\n".join(critical_issues),
                    'error'
                )
        
        self.last_health_check = datetime.now()
        return health_report
    
    def run_continuous_monitoring(self, check_interval: int = 60):
        """Run continuous health monitoring"""
        self.logger.info(f"Starting continuous health monitoring (interval: {check_interval}s)")
        
        while True:
            try:
                health_report = self.run_health_check()
                
                # Log summary
                status = health_report['overall_status']
                self.logger.info(f"Health check completed - Status: {status.upper()}")
                
                if status != 'healthy':
                    self.logger.warning(f"Issues detected: {', '.join(health_report.get('issues', []))}")
                
                # Save health report
                report_file = '/var/log/trae/health_report.json'
                with open(report_file, 'w') as f:
                    json.dump(health_report, f, indent=2)
                
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Health monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(check_interval)

def main():
    """Main entry point"""
    monitor = HealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run single health check
        report = monitor.run_health_check()
        print(json.dumps(report, indent=2))
    else:
        # Run continuous monitoring
        check_interval = int(os.environ.get('HEALTH_CHECK_INTERVAL', 60))
        monitor.run_continuous_monitoring(check_interval)

if __name__ == '__main__':
    main()