#!/usr/bin/env python3
"""
AI Trading Sentinel - Comprehensive Monitoring System
TRAE-SentinelOps: 24/7 health monitoring, alerting, and system oversight

This script monitors:
- Docker container health
- Service endpoints
- Redis connectivity
- Trading bot status
- System resources
- Log analysis
- Alert management
"""

import os
import sys
import time
import json
import logging
import requests
import redis
import docker
import smtplib
import psutil
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('SentinelMonitor')

@dataclass
class HealthStatus:
    """Health check result"""
    service: str
    healthy: bool
    message: str
    timestamp: datetime
    response_time: Optional[float] = None

class AlertManager:
    """Manages alert cooldowns and delivery"""
    
    def __init__(self):
        self.last_alerts = {}
        self.alert_cooldown = int(os.getenv('ALERT_COOLDOWN', 1800))  # 30 minutes
        
    def should_send_alert(self, alert_type: str) -> bool:
        """Check if alert should be sent based on cooldown"""
        now = datetime.now()
        last_alert = self.last_alerts.get(alert_type)
        
        if last_alert and (now - last_alert).seconds < self.alert_cooldown:
            return False
        
        self.last_alerts[alert_type] = now
        return True
    
    def send_email_alert(self, subject: str, message: str, alert_type: str = "warning") -> bool:
        """Send email alert with SMTP"""
        if not self.should_send_alert(alert_type):
            logger.info(f"Alert cooldown active for {alert_type}")
            return False
        
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USERNAME')
            smtp_pass = os.getenv('SMTP_PASSWORD')
            alert_email = os.getenv('EMAIL_ALERTS')
            
            if not all([smtp_server, smtp_user, smtp_pass, alert_email]):
                logger.warning("Email configuration incomplete")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = alert_email
            msg['Subject'] = f"[AI Trading Sentinel] {subject}"
            
            body = f"""
Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Alert Type: {alert_type.upper()}
Environment: {os.getenv('ENVIRONMENT', 'production')}

{message}

--
AI Trading Sentinel Monitoring System
Server: {os.getenv('HOSTNAME', 'unknown')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def send_slack_alert(self, message: str, severity: str = "warning") -> bool:
        """Send Slack webhook alert"""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            return False
        
        try:
            color_map = {
                'critical': 'danger',
                'warning': 'warning', 
                'info': 'good'
            }
            
            payload = {
                'text': f":warning: AI Trading Sentinel Alert",
                'attachments': [{
                    'color': color_map.get(severity, 'warning'),
                    'fields': [{
                        'title': 'Alert Details',
                        'value': message,
                        'short': False
                    }, {
                        'title': 'Environment',
                        'value': os.getenv('ENVIRONMENT', 'production'),
                        'short': True
                    }, {
                        'title': 'Server',
                        'value': os.getenv('HOSTNAME', 'unknown'),
                        'short': True
                    }],
                    'footer': 'AI Trading Sentinel Monitor',
                    'ts': int(time.time())
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Slack alert failed: {e}")
            return False

class SentinelMonitor:
    """Main monitoring class for AI Trading Sentinel"""
    
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379'))
        self.docker_client = docker.from_env()
        self.alert_manager = AlertManager()
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 300))  # 5 minutes
        self.health_history = []
        
        logger.info("SentinelMonitor initialized")
    
    def check_service_health(self, service_name: str, url: str, timeout: int = 10) -> HealthStatus:
        """Check if a service endpoint is responding"""
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return HealthStatus(
                    service=service_name,
                    healthy=True,
                    message=f"Service responding (HTTP {response.status_code})",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
            else:
                return HealthStatus(
                    service=service_name,
                    healthy=False,
                    message=f"Service returned HTTP {response.status_code}",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
                
        except requests.exceptions.Timeout:
            return HealthStatus(
                service=service_name,
                healthy=False,
                message=f"Service timeout after {timeout}s",
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthStatus(
                service=service_name,
                healthy=False,
                message=f"Service check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_container_status(self, container_name: str) -> HealthStatus:
        """Check if Docker container is running and healthy"""
        try:
            container = self.docker_client.containers.get(container_name)
            
            if container.status == 'running':
                # Check container health if health check is configured
                health = getattr(container.attrs.get('State', {}), 'Health', {})
                if health:
                    health_status = health.get('Status', 'unknown')
                    if health_status == 'healthy':
                        message = "Container running and healthy"
                        healthy = True
                    elif health_status == 'unhealthy':
                        message = "Container running but unhealthy"
                        healthy = False
                    else:
                        message = f"Container running, health status: {health_status}"
                        healthy = True
                else:
                    message = "Container running (no health check configured)"
                    healthy = True
            else:
                message = f"Container status: {container.status}"
                healthy = False
            
            return HealthStatus(
                service=f"container-{container_name}",
                healthy=healthy,
                message=message,
                timestamp=datetime.now()
            )
            
        except docker.errors.NotFound:
            return HealthStatus(
                service=f"container-{container_name}",
                healthy=False,
                message="Container not found",
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthStatus(
                service=f"container-{container_name}",
                healthy=False,
                message=f"Container check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_redis_health(self) -> HealthStatus:
        """Check Redis connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            self.redis_client.ping()
            
            # Test read/write operations
            test_key = 'monitor:health_test'
            test_value = str(int(time.time()))
            self.redis_client.setex(test_key, 60, test_value)
            retrieved_value = self.redis_client.get(test_key)
            
            response_time = time.time() - start_time
            
            if retrieved_value and retrieved_value.decode() == test_value:
                return HealthStatus(
                    service="redis",
                    healthy=True,
                    message="Redis connectivity and operations OK",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
            else:
                return HealthStatus(
                    service="redis",
                    healthy=False,
                    message="Redis read/write test failed",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
                
        except Exception as e:
            return HealthStatus(
                service="redis",
                healthy=False,
                message=f"Redis check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_trading_bot_status(self) -> HealthStatus:
        """Check trading bot status from Redis"""
        try:
            bot_status = self.redis_client.get('bot:status')
            
            if not bot_status:
                return HealthStatus(
                    service="trading-bot",
                    healthy=False,
                    message="No bot status found in Redis",
                    timestamp=datetime.now()
                )
            
            status_data = json.loads(bot_status)
            last_update_str = status_data.get('last_update')
            
            if not last_update_str:
                return HealthStatus(
                    service="trading-bot",
                    healthy=False,
                    message="Bot status missing timestamp",
                    timestamp=datetime.now()
                )
            
            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            time_since_update = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds()
            
            # Consider bot stale if no update in 10 minutes
            if time_since_update > 600:
                return HealthStatus(
                    service="trading-bot",
                    healthy=False,
                    message=f"Bot status stale ({int(time_since_update/60)} minutes old)",
                    timestamp=datetime.now()
                )
            
            bot_state = status_data.get('state', 'unknown')
            session_profit = status_data.get('session_profit', 0)
            
            return HealthStatus(
                service="trading-bot",
                healthy=True,
                message=f"Bot active, state: {bot_state}, profit: ${session_profit:.2f}",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return HealthStatus(
                service="trading-bot",
                healthy=False,
                message=f"Bot status check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def check_system_resources(self) -> HealthStatus:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            warnings = []
            
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 85:
                warnings.append(f"High memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 90:
                warnings.append(f"High disk usage: {disk.percent:.1f}%")
            
            if warnings:
                return HealthStatus(
                    service="system-resources",
                    healthy=False,
                    message="; ".join(warnings),
                    timestamp=datetime.now()
                )
            else:
                return HealthStatus(
                    service="system-resources",
                    healthy=True,
                    message=f"CPU: {cpu_percent:.1f}%, RAM: {memory.percent:.1f}%, Disk: {disk.percent:.1f}%",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return HealthStatus(
                service="system-resources",
                healthy=False,
                message=f"Resource check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def run_comprehensive_health_check(self) -> List[HealthStatus]:
        """Run all health checks and return results"""
        health_results = []
        
        # Check Docker containers
        containers = [
            'ai-trading-sentinel-tradebot-1',
            'ai-trading-sentinel-api-1', 
            'ai-trading-sentinel-redis-1',
            'ai-trading-sentinel-frontend-1',
            'ai-trading-sentinel-nginx-1'
        ]
        
        for container in containers:
            health_results.append(self.check_container_status(container))
        
        # Check service endpoints
        services = {
            'API Health': 'http://api:5000/health',
            'API Status': 'http://api:5000/api/status',
            'Frontend': 'http://frontend:3000'
        }
        
        for service_name, url in services.items():
            health_results.append(self.check_service_health(service_name, url))
        
        # Check Redis
        health_results.append(self.check_redis_health())
        
        # Check trading bot status
        health_results.append(self.check_trading_bot_status())
        
        # Check system resources
        health_results.append(self.check_system_resources())
        
        return health_results
    
    def process_health_results(self, health_results: List[HealthStatus]) -> Dict:
        """Process health check results and determine overall status"""
        healthy_count = sum(1 for result in health_results if result.healthy)
        total_count = len(health_results)
        
        critical_issues = []
        warnings = []
        
        for result in health_results:
            if not result.healthy:
                if 'container' in result.service or 'redis' in result.service:
                    critical_issues.append(f"{result.service}: {result.message}")
                else:
                    warnings.append(f"{result.service}: {result.message}")
        
        overall_status = {
            'timestamp': datetime.now().isoformat(),
            'healthy_services': healthy_count,
            'total_services': total_count,
            'health_percentage': (healthy_count / total_count) * 100,
            'status': 'healthy' if healthy_count == total_count else 'degraded' if critical_issues else 'warning',
            'critical_issues': critical_issues,
            'warnings': warnings,
            'details': [{
                'service': result.service,
                'healthy': result.healthy,
                'message': result.message,
                'response_time': result.response_time
            } for result in health_results]
        }
        
        return overall_status
    
    def send_alerts_if_needed(self, status: Dict):
        """Send alerts based on health status"""
        if status['critical_issues']:
            alert_message = "CRITICAL ISSUES DETECTED:\n\n" + "\n".join(f"• {issue}" for issue in status['critical_issues'])
            
            if status['warnings']:
                alert_message += "\n\nWARNINGS:\n" + "\n".join(f"• {warning}" for warning in status['warnings'])
            
            alert_message += f"\n\nOverall Health: {status['health_percentage']:.1f}% ({status['healthy_services']}/{status['total_services']} services healthy)"
            
            self.alert_manager.send_email_alert("CRITICAL: System Health Alert", alert_message, "critical")
            self.alert_manager.send_slack_alert(alert_message, "critical")
            
        elif status['warnings']:
            alert_message = "WARNINGS DETECTED:\n\n" + "\n".join(f"• {warning}" for warning in status['warnings'])
            alert_message += f"\n\nOverall Health: {status['health_percentage']:.1f}% ({status['healthy_services']}/{status['total_services']} services healthy)"
            
            self.alert_manager.send_email_alert("WARNING: System Health Alert", alert_message, "warning")
            self.alert_manager.send_slack_alert(alert_message, "warning")
    
    def store_health_data(self, status: Dict):
        """Store health data in Redis for API access"""
        try:
            # Store current status
            self.redis_client.setex('monitor:health', 3600, json.dumps(status))
            
            # Store in history (keep last 24 hours)
            history_key = f"monitor:history:{datetime.now().strftime('%Y%m%d%H')}"
            self.redis_client.lpush(history_key, json.dumps(status))
            self.redis_client.expire(history_key, 86400)  # 24 hours
            
            # Cleanup old history keys
            cutoff_time = datetime.now() - timedelta(days=2)
            old_key = f"monitor:history:{cutoff_time.strftime('%Y%m%d%H')}"
            self.redis_client.delete(old_key)
            
        except Exception as e:
            logger.error(f"Failed to store health data: {e}")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting AI Trading Sentinel Monitor (check interval: {self.check_interval}s)")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
        logger.info(f"Alert cooldown: {self.alert_manager.alert_cooldown}s")
        
        while True:
            try:
                logger.info("Running comprehensive health checks...")
                
                # Run health checks
                health_results = self.run_comprehensive_health_check()
                
                # Process results
                status = self.process_health_results(health_results)
                
                # Log status
                if status['status'] == 'healthy':
                    logger.info(f"✓ All systems healthy ({status['healthy_services']}/{status['total_services']} services)")
                else:
                    logger.warning(f"⚠ System status: {status['status']} ({status['healthy_services']}/{status['total_services']} services healthy)")
                    
                    if status['critical_issues']:
                        logger.error(f"Critical issues: {', '.join(status['critical_issues'])}")
                    
                    if status['warnings']:
                        logger.warning(f"Warnings: {', '.join(status['warnings'])}")
                
                # Send alerts if needed
                self.send_alerts_if_needed(status)
                
                # Store health data
                self.store_health_data(status)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                try:
                    self.alert_manager.send_email_alert(
                        "Monitor System Error", 
                        f"Monitor encountered an error: {str(e)}", 
                        "system"
                    )
                except:
                    pass  # Don't let alert failures crash the monitor
            
            # Sleep until next check
            time.sleep(self.check_interval)

def main():
    """Main entry point"""
    try:
        monitor = SentinelMonitor()
        monitor.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()