#!/usr/bin/env python3
"""
AI Trading Sentinel - Advanced Health Monitor
Provides comprehensive health monitoring, automated recovery, and alerting.
"""

import asyncio
import aiohttp
import json
import logging
import os
import smtplib
import subprocess
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import redis
import psycopg2
from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway

# Configuration
CONFIG = {
    'check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '60')),
    'max_retries': int(os.getenv('HEALTH_MAX_RETRIES', '3')),
    'timeout': int(os.getenv('HEALTH_TIMEOUT', '30')),
    'log_file': os.getenv('HEALTH_LOG_FILE', '/var/log/health-monitor.log'),
    'alert_email': os.getenv('ALERT_EMAIL', 'admin@localhost'),
    'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'smtp_user': os.getenv('SMTP_USER', ''),
    'smtp_password': os.getenv('SMTP_PASSWORD', ''),
    'slack_webhook': os.getenv('SLACK_WEBHOOK_URL', ''),
    'prometheus_gateway': os.getenv('PROMETHEUS_PUSHGATEWAY', 'localhost:9091'),
    'docker_compose_file': '/opt/ai-trading-sentinel/docker-compose.prod.yml',
    'services': {
        'backend': {'url': 'http://localhost:8000/health', 'critical': True},
        'frontend': {'url': 'http://localhost:3000', 'critical': True},
        'postgres': {'host': 'localhost', 'port': 5432, 'critical': True},
        'redis': {'host': 'localhost', 'port': 6379, 'critical': True},
        'prometheus': {'url': 'http://localhost:9090/-/healthy', 'critical': False},
        'grafana': {'url': 'http://localhost:3000/api/health', 'critical': False},
        'alertmanager': {'url': 'http://localhost:9093/-/healthy', 'critical': False},
        'loki': {'url': 'http://localhost:3100/ready', 'critical': False},
        'nginx': {'url': 'http://localhost:80', 'critical': True}
    }
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
registry = CollectorRegistry()
health_status = Gauge('service_health_status', 'Service health status (1=healthy, 0=unhealthy)', ['service'], registry=registry)
response_time = Gauge('service_response_time_seconds', 'Service response time in seconds', ['service'], registry=registry)
restart_counter = Counter('service_restart_total', 'Total number of service restarts', ['service'], registry=registry)
system_cpu = Gauge('system_cpu_percent', 'System CPU usage percentage', registry=registry)
system_memory = Gauge('system_memory_percent', 'System memory usage percentage', registry=registry)
system_disk = Gauge('system_disk_percent', 'System disk usage percentage', ['mount'], registry=registry)

class HealthMonitor:
    def __init__(self):
        self.failed_checks = {}
        self.last_alert_time = {}
        self.alert_cooldown = timedelta(minutes=15)
        
    async def check_http_service(self, service_name: str, url: str) -> Tuple[bool, float]:
        """Check HTTP service health and measure response time."""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=CONFIG['timeout'])) as session:
                async with session.get(url) as response:
                    response_time_val = time.time() - start_time
                    is_healthy = response.status == 200
                    response_time.labels(service=service_name).set(response_time_val)
                    return is_healthy, response_time_val
        except Exception as e:
            response_time_val = time.time() - start_time
            logger.error(f"HTTP check failed for {service_name}: {e}")
            response_time.labels(service=service_name).set(response_time_val)
            return False, response_time_val
    
    def check_postgres(self) -> bool:
        """Check PostgreSQL database connectivity."""
        try:
            conn = psycopg2.connect(
                host=CONFIG['services']['postgres']['host'],
                port=CONFIG['services']['postgres']['port'],
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                database=os.getenv('POSTGRES_DB', 'trading_sentinel'),
                connect_timeout=CONFIG['timeout']
            )
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL check failed: {e}")
            return False
    
    def check_redis(self) -> bool:
        """Check Redis connectivity."""
        try:
            r = redis.Redis(
                host=CONFIG['services']['redis']['host'],
                port=CONFIG['services']['redis']['port'],
                password=os.getenv('REDIS_PASSWORD', ''),
                socket_timeout=CONFIG['timeout']
            )
            r.ping()
            return True
        except Exception as e:
            logger.error(f"Redis check failed: {e}")
            return False
    
    def collect_system_metrics(self):
        """Collect system-level metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        system_memory.set(memory.percent)
        
        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                system_disk.labels(mount=partition.mountpoint).set(usage.percent)
            except PermissionError:
                continue
    
    async def check_service_health(self, service_name: str, config: Dict) -> bool:
        """Check individual service health."""
        if 'url' in config:
            is_healthy, _ = await self.check_http_service(service_name, config['url'])
        elif service_name == 'postgres':
            is_healthy = self.check_postgres()
        elif service_name == 'redis':
            is_healthy = self.check_redis()
        else:
            logger.warning(f"Unknown service type for {service_name}")
            return False
        
        # Update Prometheus metrics
        health_status.labels(service=service_name).set(1 if is_healthy else 0)
        
        return is_healthy
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a Docker service."""
        try:
            cmd = [
                'docker-compose',
                '-f', CONFIG['docker_compose_file'],
                'restart', service_name
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"Successfully restarted {service_name}")
                restart_counter.labels(service=service_name).inc()
                return True
            else:
                logger.error(f"Failed to restart {service_name}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error restarting {service_name}: {e}")
            return False
    
    async def send_slack_alert(self, message: str):
        """Send alert to Slack."""
        if not CONFIG['slack_webhook']:
            return
        
        try:
            payload = {
                'text': f"🚨 AI Trading Sentinel Alert",
                'attachments': [{
                    'color': 'danger',
                    'fields': [{
                        'title': 'Alert Details',
                        'value': message,
                        'short': False
                    }],
                    'footer': 'Health Monitor',
                    'ts': int(time.time())
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(CONFIG['slack_webhook'], json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack alert sent successfully")
                    else:
                        logger.error(f"Failed to send Slack alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def send_email_alert(self, subject: str, message: str):
        """Send email alert."""
        if not CONFIG['alert_email']:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = CONFIG['smtp_user'] or 'health-monitor@localhost'
            msg['To'] = CONFIG['alert_email']
            msg['Subject'] = f"[AI Trading Sentinel] {subject}"
            
            body = f"""
            AI Trading Sentinel Health Monitor Alert
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            {message}
            
            Please check the system status and take appropriate action.
            
            ---
            AI Trading Sentinel Health Monitor
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(CONFIG['smtp_server'], CONFIG['smtp_port'])
            if CONFIG['smtp_user'] and CONFIG['smtp_password']:
                server.starttls()
                server.login(CONFIG['smtp_user'], CONFIG['smtp_password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent to {CONFIG['alert_email']}")
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    async def send_alert(self, service_name: str, message: str):
        """Send alert via multiple channels with cooldown."""
        now = datetime.now()
        last_alert = self.last_alert_time.get(service_name)
        
        if last_alert and (now - last_alert) < self.alert_cooldown:
            return  # Skip alert due to cooldown
        
        self.last_alert_time[service_name] = now
        
        # Send alerts
        await self.send_slack_alert(message)
        self.send_email_alert(f"Service Alert: {service_name}", message)
        
        logger.warning(f"Alert sent for {service_name}: {message}")
    
    def push_metrics_to_prometheus(self):
        """Push metrics to Prometheus Pushgateway."""
        try:
            push_to_gateway(
                CONFIG['prometheus_gateway'],
                job='health-monitor',
                registry=registry
            )
        except Exception as e:
            logger.error(f"Failed to push metrics to Prometheus: {e}")
    
    async def run_health_checks(self):
        """Run all health checks and handle failures."""
        logger.info("Starting health check cycle")
        
        # Collect system metrics
        self.collect_system_metrics()
        
        # Check all services
        for service_name, service_config in CONFIG['services'].items():
            try:
                is_healthy = await self.check_service_health(service_name, service_config)
                
                if is_healthy:
                    if service_name in self.failed_checks:
                        # Service recovered
                        logger.info(f"✓ {service_name} has recovered")
                        await self.send_alert(
                            service_name,
                            f"Service {service_name} has recovered and is now healthy."
                        )
                        del self.failed_checks[service_name]
                    else:
                        logger.debug(f"✓ {service_name} is healthy")
                else:
                    # Service is unhealthy
                    if service_name not in self.failed_checks:
                        self.failed_checks[service_name] = 1
                    else:
                        self.failed_checks[service_name] += 1
                    
                    logger.error(f"✗ {service_name} is unhealthy (attempt {self.failed_checks[service_name]})")
                    
                    # Try to restart if max retries reached and service is critical
                    if (self.failed_checks[service_name] >= CONFIG['max_retries'] and 
                        service_config.get('critical', False)):
                        
                        logger.info(f"Attempting to restart {service_name}")
                        restart_success = self.restart_service(service_name)
                        
                        if restart_success:
                            await self.send_alert(
                                service_name,
                                f"Critical service {service_name} was unhealthy and has been restarted."
                            )
                            # Reset failure count after restart
                            self.failed_checks[service_name] = 0
                        else:
                            await self.send_alert(
                                service_name,
                                f"CRITICAL: Failed to restart {service_name}. Manual intervention required!"
                            )
                    elif self.failed_checks[service_name] == 1:
                        # First failure - send initial alert
                        await self.send_alert(
                            service_name,
                            f"Service {service_name} is unhealthy. Monitoring for recovery..."
                        )
                        
            except Exception as e:
                logger.error(f"Error checking {service_name}: {e}")
        
        # Push metrics to Prometheus
        self.push_metrics_to_prometheus()
        
        logger.info("Health check cycle completed")
    
    async def run(self):
        """Main monitoring loop."""
        logger.info("AI Trading Sentinel Health Monitor started")
        
        while True:
            try:
                await self.run_health_checks()
                await asyncio.sleep(CONFIG['check_interval'])
            except KeyboardInterrupt:
                logger.info("Health monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in health monitor: {e}")
                await asyncio.sleep(CONFIG['check_interval'])

def main():
    """Main entry point."""
    # Ensure log directory exists
    log_dir = Path(CONFIG['log_file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create and run health monitor
    monitor = HealthMonitor()
    
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        logger.info("Health monitor stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())