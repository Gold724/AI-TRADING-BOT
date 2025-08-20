#!/usr/bin/env python3
"""
AI Trading Sentinel - Monitoring & Alerting System
Comprehensive 24/7 monitoring for trading operations
"""

import os
import time
import json
import psutil
import requests
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    status: str
    response_time: float
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class TradingMonitor:
    """Comprehensive monitoring system for AI Trading Sentinel"""
    
    def __init__(self):
        self.load_config()
        self.setup_alerts()
        
    def load_config(self):
        """Load monitoring configuration"""
        self.config = {
            'services': {
                'backend': 'http://localhost:5000/api/health',
                'frontend': 'http://localhost:3000',
                'bulenox': 'http://localhost:5000/api/bulenox/status'
            },
            'thresholds': {
                'cpu_percent': 80,
                'memory_percent': 85,
                'disk_percent': 90,
                'response_time': 5.0
            },
            'alert_intervals': {
                'critical': 300,  # 5 minutes
                'warning': 900,   # 15 minutes
                'info': 3600      # 1 hour
            }
        }
        
        # Load email configuration
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_user': os.getenv('EMAIL_USER', 'edufyinc@gmail.com'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'alert_recipients': ['edufyinc@gmail.com']
        }
        
    def setup_alerts(self):
        """Initialize alert tracking"""
        self.last_alerts = {}
        self.alert_counts = {}
        
    def check_system_health(self) -> Dict[str, HealthCheck]:
        """Check overall system health"""
        health_checks = {}
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        health_checks['cpu'] = HealthCheck(
            service='cpu',
            status='healthy' if cpu_percent < self.config['thresholds']['cpu_percent'] else 'warning',
            response_time=cpu_percent,
            error=f"High CPU usage: {cpu_percent}%" if cpu_percent >= self.config['thresholds']['cpu_percent'] else None
        )
        
        # Memory Usage
        memory = psutil.virtual_memory()
        health_checks['memory'] = HealthCheck(
            service='memory',
            status='healthy' if memory.percent < self.config['thresholds']['memory_percent'] else 'warning',
            response_time=memory.percent,
            error=f"High memory usage: {memory.percent}%" if memory.percent >= self.config['thresholds']['memory_percent'] else None
        )
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        health_checks['disk'] = HealthCheck(
            service='disk',
            status='healthy' if disk_percent < self.config['thresholds']['disk_percent'] else 'critical',
            response_time=disk_percent,
            error=f"High disk usage: {disk_percent:.1f}%" if disk_percent >= self.config['thresholds']['disk_percent'] else None
        )
        
        return health_checks
        
    def check_service_health(self, service_name: str, url: str) -> HealthCheck:
        """Check individual service health"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = 'healthy' if response_time < self.config['thresholds']['response_time'] else 'warning'
                error = f"Slow response: {response_time:.2f}s" if response_time >= self.config['thresholds']['response_time'] else None
            else:
                status = 'critical'
                error = f"HTTP {response.status_code}"
                
            return HealthCheck(
                service=service_name,
                status=status,
                response_time=response_time,
                error=error
            )
            
        except requests.exceptions.RequestException as e:
            return HealthCheck(
                service=service_name,
                status='critical',
                response_time=0.0,
                error=f"Connection failed: {str(e)}"
            )
    
    def check_trading_status(self) -> HealthCheck:
        """Check trading bot status"""
        try:
            # Check if trading process is running
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'main.py' in cmdline or 'backend_main.py' in cmdline:
                        return HealthCheck(
                            service='trading_bot',
                            status='healthy',
                            response_time=0.0
                        )
            
            return HealthCheck(
                service='trading_bot',
                status='critical',
                response_time=0.0,
                error="Trading bot process not found"
            )
            
        except Exception as e:
            return HealthCheck(
                service='trading_bot',
                status='critical',
                response_time=0.0,
                error=f"Process check failed: {str(e)}"
            )
    
    def send_alert(self, health_check: HealthCheck, severity: str = 'warning'):
        """Send email alert"""
        if not self.email_config['email_password']:
            logging.warning("Email password not configured, skipping alert")
            return
            
        # Check if we should send this alert (rate limiting)
        alert_key = f"{health_check.service}_{severity}"
        now = datetime.now()
        
        if alert_key in self.last_alerts:
            time_since_last = (now - self.last_alerts[alert_key]).total_seconds()
            if time_since_last < self.config['alert_intervals'][severity]:
                return  # Skip this alert
        
        self.last_alerts[alert_key] = now
        self.alert_counts[alert_key] = self.alert_counts.get(alert_key, 0) + 1
        
        # Compose email
        subject = f"🚨 AI Trading Sentinel Alert - {health_check.service.upper()} {severity.upper()}"
        
        body = f"""
AI Trading Sentinel Monitoring Alert

Service: {health_check.service}
Status: {health_check.status}
Severity: {severity}
Timestamp: {health_check.timestamp}
Response Time: {health_check.response_time:.2f}s

Error Details:
{health_check.error or 'No specific error details'}

Alert Count: {self.alert_counts[alert_key]}

System Information:
- CPU Usage: {psutil.cpu_percent()}%
- Memory Usage: {psutil.virtual_memory().percent}%
- Disk Usage: {(psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100:.1f}%

Please check the system immediately.

---
AI Trading Sentinel Monitoring System
        """
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email_user']
            msg['To'] = ', '.join(self.email_config['alert_recipients'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email_user'], self.email_config['email_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['email_user'], self.email_config['alert_recipients'], text)
            server.quit()
            
            logging.info(f"Alert sent for {health_check.service}: {severity}")
            
        except Exception as e:
            logging.error(f"Failed to send alert: {str(e)}")
    
    def generate_health_report(self, health_checks: Dict[str, HealthCheck]) -> str:
        """Generate comprehensive health report"""
        report = []
        report.append("🏥 AI Trading Sentinel Health Report")
        report.append("=" * 50)
        report.append(f"📅 Generated: {datetime.now()}")
        report.append("")
        
        # Overall status
        critical_count = sum(1 for hc in health_checks.values() if hc.status == 'critical')
        warning_count = sum(1 for hc in health_checks.values() if hc.status == 'warning')
        healthy_count = sum(1 for hc in health_checks.values() if hc.status == 'healthy')
        
        if critical_count > 0:
            overall_status = "🔴 CRITICAL"
        elif warning_count > 0:
            overall_status = "🟡 WARNING"
        else:
            overall_status = "🟢 HEALTHY"
            
        report.append(f"Overall Status: {overall_status}")
        report.append(f"Services: {healthy_count} healthy, {warning_count} warning, {critical_count} critical")
        report.append("")
        
        # Individual service status
        for service, health_check in health_checks.items():
            status_icon = {
                'healthy': '🟢',
                'warning': '🟡',
                'critical': '🔴'
            }.get(health_check.status, '⚪')
            
            report.append(f"{status_icon} {service.upper()}: {health_check.status}")
            if health_check.error:
                report.append(f"   Error: {health_check.error}")
            report.append(f"   Response Time: {health_check.response_time:.2f}s")
            report.append("")
        
        return "\n".join(report)
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logging.info("🔍 Starting monitoring cycle...")
        
        # Collect all health checks
        health_checks = {}
        
        # System health
        health_checks.update(self.check_system_health())
        
        # Service health
        for service_name, url in self.config['services'].items():
            health_checks[service_name] = self.check_service_health(service_name, url)
        
        # Trading bot health
        health_checks['trading_bot'] = self.check_trading_status()
        
        # Generate report
        report = self.generate_health_report(health_checks)
        print(report)
        
        # Send alerts for critical and warning conditions
        for health_check in health_checks.values():
            if health_check.status == 'critical':
                self.send_alert(health_check, 'critical')
            elif health_check.status == 'warning':
                self.send_alert(health_check, 'warning')
        
        # Save health data
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'health_checks': {
                service: {
                    'status': hc.status,
                    'response_time': hc.response_time,
                    'error': hc.error
                }
                for service, hc in health_checks.items()
            }
        }
        
        with open('health_status.json', 'w') as f:
            json.dump(health_data, f, indent=2)
        
        logging.info("✅ Monitoring cycle completed")
        
    def run_continuous_monitoring(self, interval: int = 60):
        """Run continuous monitoring"""
        logging.info(f"🚀 Starting continuous monitoring (interval: {interval}s)")
        
        while True:
            try:
                self.run_monitoring_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                logging.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logging.error(f"❌ Monitoring error: {str(e)}")
                time.sleep(30)  # Wait before retrying

def main():
    """Main monitoring function"""
    monitor = TradingMonitor()
    
    # Run single check or continuous monitoring
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        monitor.run_continuous_monitoring()
    else:
        monitor.run_monitoring_cycle()

if __name__ == "__main__":
    main()