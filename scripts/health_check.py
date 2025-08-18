#!/usr/bin/env python3
"""
AI Trading Sentinel - Production Health Check Script
Comprehensive monitoring for 24/7 operations on Contabo VPS

Usage:
    python health_check.py [--interval 60] [--config config.json] [--alert]
"""

import os
import sys
import json
import time
import psutil
import requests
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import argparse
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class HealthMetrics:
    """Health check metrics data structure"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    docker_status: bool
    api_status: bool
    database_status: bool
    redis_status: bool
    trading_bot_status: bool
    last_trade_time: Optional[datetime]
    error_count: int
    uptime_seconds: int

class HealthChecker:
    """Comprehensive health monitoring system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.start_time = datetime.now()
        self.alert_history = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or environment"""
        default_config = {
            "thresholds": {
                "cpu_percent": 80.0,
                "memory_percent": 85.0,
                "disk_percent": 90.0,
                "error_rate": 10,
                "response_time_ms": 5000
            },
            "endpoints": {
                "api_health": "http://localhost:8000/health",
                "api_status": "http://localhost:8000/api/status",
                "frontend": "http://localhost/health",
                "prometheus": "http://localhost:9090/-/healthy",
                "grafana": "http://localhost:3000/api/health"
            },
            "services": {
                "docker_compose_file": "/opt/ai-trading-sentinel/docker-compose.yml",
                "log_directory": "/var/log/ai-trading-sentinel",
                "data_directory": "/var/lib/ai-trading-sentinel"
            },
            "notifications": {
                "email_enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
                "telegram_enabled": os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
                "slack_enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true"
            },
            "intervals": {
                "check_interval": 60,
                "alert_cooldown": 300,
                "log_retention_days": 30
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = Path(self.config["services"]["log_directory"])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "health_check.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    def check_system_resources(self) -> Dict[str, float]:
        """Check system CPU, memory, and disk usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv
            }
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return {}
    
    def check_docker_services(self) -> Dict[str, bool]:
        """Check Docker container status"""
        try:
            compose_file = self.config["services"]["docker_compose_file"]
            
            # Check if docker-compose is running
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "ps", "-q"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {"docker_compose": False}
            
            # Get detailed container status
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            services = {}
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container = json.loads(line)
                            service_name = container.get("Service", "unknown")
                            state = container.get("State", "unknown")
                            services[service_name] = state == "running"
                        except json.JSONDecodeError:
                            continue
            
            return services
            
        except Exception as e:
            self.logger.error(f"Error checking Docker services: {e}")
            return {"docker_error": False}
    
    def check_api_endpoints(self) -> Dict[str, Dict[str, any]]:
        """Check API endpoint health and response times"""
        results = {}
        
        for endpoint_name, url in self.config["endpoints"].items():
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                results[endpoint_name] = {
                    "status": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "content_length": len(response.content)
                }
                
                # Check for specific health indicators
                if endpoint_name == "api_status":
                    try:
                        data = response.json()
                        results[endpoint_name]["bot_status"] = data.get("bot_running", False)
                        results[endpoint_name]["last_trade"] = data.get("last_trade_time")
                    except:
                        pass
                        
            except requests.RequestException as e:
                results[endpoint_name] = {
                    "status": False,
                    "error": str(e),
                    "response_time_ms": None
                }
            except Exception as e:
                self.logger.error(f"Error checking endpoint {endpoint_name}: {e}")
                results[endpoint_name] = {
                    "status": False,
                    "error": f"Unexpected error: {e}"
                }
        
        return results
    
    def check_log_files(self) -> Dict[str, any]:
        """Check log files for errors and size"""
        log_dir = Path(self.config["services"]["log_directory"])
        
        if not log_dir.exists():
            return {"log_directory_exists": False}
        
        results = {
            "log_directory_exists": True,
            "log_files": {},
            "recent_errors": 0,
            "total_log_size_mb": 0
        }
        
        try:
            # Check all log files
            for log_file in log_dir.glob("*.log"):
                file_size = log_file.stat().st_size
                results["total_log_size_mb"] += file_size / (1024 * 1024)
                
                results["log_files"][log_file.name] = {
                    "size_mb": file_size / (1024 * 1024),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime)
                }
                
                # Check for recent errors (last 5 minutes)
                if log_file.name in ["trading_bot.log", "api.log", "error.log"]:
                    try:
                        with open(log_file, 'r') as f:
                            # Read last 1000 lines for recent errors
                            lines = f.readlines()[-1000:]
                            recent_time = datetime.now() - timedelta(minutes=5)
                            
                            for line in lines:
                                if "ERROR" in line or "CRITICAL" in line:
                                    # Simple timestamp parsing
                                    if recent_time.strftime("%Y-%m-%d %H:%M") in line:
                                        results["recent_errors"] += 1
                    except Exception:
                        pass
        
        except Exception as e:
            self.logger.error(f"Error checking log files: {e}")
            results["error"] = str(e)
        
        return results
    
    def check_database_connections(self) -> Dict[str, bool]:
        """Check database connectivity"""
        results = {}
        
        # Check PostgreSQL
        try:
            import psycopg2
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                results["postgresql"] = True
            else:
                results["postgresql"] = None  # Not configured
        except Exception as e:
            results["postgresql"] = False
            self.logger.warning(f"PostgreSQL check failed: {e}")
        
        # Check Redis
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            r.ping()
            results["redis"] = True
        except Exception as e:
            results["redis"] = False
            self.logger.warning(f"Redis check failed: {e}")
        
        return results
    
    def generate_health_report(self) -> HealthMetrics:
        """Generate comprehensive health report"""
        self.logger.info("Starting health check...")
        
        # Collect all metrics
        system_resources = self.check_system_resources()
        docker_services = self.check_docker_services()
        api_endpoints = self.check_api_endpoints()
        log_status = self.check_log_files()
        db_status = self.check_database_connections()
        
        # Create health metrics
        metrics = HealthMetrics(
            timestamp=datetime.now(),
            cpu_percent=system_resources.get("cpu_percent", 0),
            memory_percent=system_resources.get("memory_percent", 0),
            disk_percent=system_resources.get("disk_percent", 0),
            network_io={
                "bytes_sent": system_resources.get("network_bytes_sent", 0),
                "bytes_recv": system_resources.get("network_bytes_recv", 0)
            },
            process_count=len(psutil.pids()),
            docker_status=any(docker_services.values()),
            api_status=api_endpoints.get("api_health", {}).get("status", False),
            database_status=db_status.get("postgresql", False),
            redis_status=db_status.get("redis", False),
            trading_bot_status=docker_services.get("trading-sentinel", False),
            last_trade_time=None,  # Would need to parse from API response
            error_count=log_status.get("recent_errors", 0),
            uptime_seconds=int((datetime.now() - self.start_time).total_seconds())
        )
        
        # Log summary
        self.logger.info(f"Health Check Summary:")
        self.logger.info(f"  CPU: {metrics.cpu_percent:.1f}%")
        self.logger.info(f"  Memory: {metrics.memory_percent:.1f}%")
        self.logger.info(f"  Disk: {metrics.disk_percent:.1f}%")
        self.logger.info(f"  Docker: {'✓' if metrics.docker_status else '✗'}")
        self.logger.info(f"  API: {'✓' if metrics.api_status else '✗'}")
        self.logger.info(f"  Trading Bot: {'✓' if metrics.trading_bot_status else '✗'}")
        self.logger.info(f"  Recent Errors: {metrics.error_count}")
        
        return metrics
    
    def check_thresholds(self, metrics: HealthMetrics) -> List[str]:
        """Check if any thresholds are exceeded"""
        alerts = []
        thresholds = self.config["thresholds"]
        
        if metrics.cpu_percent > thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_percent > thresholds["disk_percent"]:
            alerts.append(f"High disk usage: {metrics.disk_percent:.1f}%")
        
        if not metrics.docker_status:
            alerts.append("Docker services are not running")
        
        if not metrics.api_status:
            alerts.append("API health check failed")
        
        if not metrics.trading_bot_status:
            alerts.append("Trading bot is not running")
        
        if metrics.error_count > thresholds["error_rate"]:
            alerts.append(f"High error rate: {metrics.error_count} errors in last 5 minutes")
        
        return alerts
    
    def send_alert(self, alerts: List[str], metrics: HealthMetrics):
        """Send alerts via configured channels"""
        if not alerts:
            return
        
        # Check alert cooldown
        now = datetime.now()
        cooldown = timedelta(seconds=self.config["intervals"]["alert_cooldown"])
        
        # Filter out recent alerts
        new_alerts = []
        for alert in alerts:
            recent_alert = any(
                alert == hist_alert and (now - hist_time) < cooldown
                for hist_alert, hist_time in self.alert_history
            )
            if not recent_alert:
                new_alerts.append(alert)
                self.alert_history.append((alert, now))
        
        if not new_alerts:
            return
        
        # Clean old alert history
        self.alert_history = [
            (alert, alert_time) for alert, alert_time in self.alert_history
            if (now - alert_time) < cooldown * 2
        ]
        
        alert_message = f"🚨 AI Trading Sentinel Alert\n\n"
        alert_message += f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        alert_message += "Issues detected:\n"
        for alert in new_alerts:
            alert_message += f"• {alert}\n"
        
        alert_message += f"\nSystem Status:\n"
        alert_message += f"• CPU: {metrics.cpu_percent:.1f}%\n"
        alert_message += f"• Memory: {metrics.memory_percent:.1f}%\n"
        alert_message += f"• Disk: {metrics.disk_percent:.1f}%\n"
        alert_message += f"• Uptime: {metrics.uptime_seconds // 3600}h {(metrics.uptime_seconds % 3600) // 60}m\n"
        
        self.logger.warning(f"Sending alerts: {new_alerts}")
        
        # Send via configured channels
        if self.config["notifications"]["email_enabled"]:
            self._send_email_alert(alert_message)
        
        if self.config["notifications"]["telegram_enabled"]:
            self._send_telegram_alert(alert_message)
        
        if self.config["notifications"]["slack_enabled"]:
            self._send_slack_alert(alert_message)
    
    def _send_email_alert(self, message: str):
        """Send email alert"""
        try:
            smtp_server = os.getenv("EMAIL_SMTP_SERVER")
            smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
            username = os.getenv("EMAIL_USERNAME")
            password = os.getenv("EMAIL_PASSWORD")
            from_email = os.getenv("EMAIL_FROM")
            to_email = os.getenv("EMAIL_TO")
            
            if not all([smtp_server, username, password, from_email, to_email]):
                self.logger.warning("Email configuration incomplete")
                return
            
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = "AI Trading Sentinel Alert"
            msg.attach(MimeText(message, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email alert sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def _send_telegram_alert(self, message: str):
        """Send Telegram alert"""
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            
            if not bot_token or not chat_id:
                self.logger.warning("Telegram configuration incomplete")
                return
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Telegram alert sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
    
    def _send_slack_alert(self, message: str):
        """Send Slack alert"""
        try:
            webhook_url = os.getenv("SLACK_WEBHOOK_URL")
            
            if not webhook_url:
                self.logger.warning("Slack webhook URL not configured")
                return
            
            data = {
                "text": "AI Trading Sentinel Alert",
                "attachments": [{
                    "color": "danger",
                    "text": message,
                    "ts": int(time.time())
                }]
            }
            
            response = requests.post(webhook_url, json=data, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Slack alert sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
    
    def run_continuous_monitoring(self, interval: int = 60):
        """Run continuous health monitoring"""
        self.logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        
        try:
            while True:
                metrics = self.generate_health_report()
                alerts = self.check_thresholds(metrics)
                
                if alerts:
                    self.send_alert(alerts, metrics)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            raise

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Health Check")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--alert", action="store_true", help="Enable alerting")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    # Initialize health checker
    checker = HealthChecker(args.config)
    
    if args.once:
        # Run single health check
        metrics = checker.generate_health_report()
        alerts = checker.check_thresholds(metrics)
        
        if alerts:
            print("\n⚠️  Alerts:")
            for alert in alerts:
                print(f"  • {alert}")
            
            if args.alert:
                checker.send_alert(alerts, metrics)
        else:
            print("\n✅ All systems healthy")
        
        # Exit with appropriate code
        sys.exit(1 if alerts else 0)
    else:
        # Run continuous monitoring
        checker.run_continuous_monitoring(args.interval)

if __name__ == "__main__":
    main()