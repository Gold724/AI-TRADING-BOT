#!/usr/bin/env python3
"""
Production Monitoring Dashboard for Bulenox Trading Bot
Real-time monitoring, alerting, and performance tracking
"""

import asyncio
import json
import time
import logging
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import smtplib
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/trading-bot/monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    load_average: List[float]
    uptime_seconds: int

@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    timestamp: str
    active_positions: int
    total_trades_today: int
    profit_loss_today: float
    win_rate_today: float
    largest_position_size: float
    risk_exposure_percent: float
    last_trade_time: str
    contract_validation_errors: int

@dataclass
class ServiceStatus:
    """Service health status"""
    timestamp: str
    bot_service_running: bool
    api_service_running: bool
    nginx_running: bool
    database_accessible: bool
    bulenox_login_status: bool
    api_response_time_ms: float
    last_heartbeat: str

@dataclass
class Alert:
    """Alert information"""
    timestamp: str
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'system', 'trading', 'service'
    message: str
    resolved: bool = False
    resolution_time: Optional[str] = None

class MonitoringDatabase:
    """SQLite database for storing monitoring data"""
    
    def __init__(self, db_path: str = '/var/log/trading-bot/monitoring.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize monitoring database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    network_sent INTEGER,
                    network_recv INTEGER,
                    load_average TEXT,
                    uptime_seconds INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS trading_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    active_positions INTEGER,
                    total_trades_today INTEGER,
                    profit_loss_today REAL,
                    win_rate_today REAL,
                    largest_position_size REAL,
                    risk_exposure_percent REAL,
                    last_trade_time TEXT,
                    contract_validation_errors INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS service_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    bot_service_running BOOLEAN,
                    api_service_running BOOLEAN,
                    nginx_running BOOLEAN,
                    database_accessible BOOLEAN,
                    bulenox_login_status BOOLEAN,
                    api_response_time_ms REAL,
                    last_heartbeat TEXT
                );
                
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_time TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_trading_timestamp ON trading_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_service_timestamp ON service_status(timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
            """)
    
    def store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO system_metrics 
                (timestamp, cpu_percent, memory_percent, disk_percent, 
                 network_sent, network_recv, load_average, uptime_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
                metrics.disk_percent, metrics.network_sent, metrics.network_recv,
                json.dumps(metrics.load_average), metrics.uptime_seconds
            ))
    
    def store_trading_metrics(self, metrics: TradingMetrics):
        """Store trading metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO trading_metrics 
                (timestamp, active_positions, total_trades_today, profit_loss_today,
                 win_rate_today, largest_position_size, risk_exposure_percent,
                 last_trade_time, contract_validation_errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp, metrics.active_positions, metrics.total_trades_today,
                metrics.profit_loss_today, metrics.win_rate_today, metrics.largest_position_size,
                metrics.risk_exposure_percent, metrics.last_trade_time, metrics.contract_validation_errors
            ))
    
    def store_service_status(self, status: ServiceStatus):
        """Store service status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO service_status 
                (timestamp, bot_service_running, api_service_running, nginx_running,
                 database_accessible, bulenox_login_status, api_response_time_ms, last_heartbeat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                status.timestamp, status.bot_service_running, status.api_service_running,
                status.nginx_running, status.database_accessible, status.bulenox_login_status,
                status.api_response_time_ms, status.last_heartbeat
            ))
    
    def store_alert(self, alert: Alert):
        """Store alert"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alerts (timestamp, severity, category, message, resolved, resolution_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert.timestamp, alert.severity, alert.category, alert.message,
                alert.resolved, alert.resolution_time
            ))

class ProductionMonitor:
    """Main production monitoring class"""
    
    def __init__(self, config_file: str = '/opt/trading-bot/.env'):
        self.config = self.load_config(config_file)
        self.db = MonitoringDatabase()
        self.alert_thresholds = {
            'cpu_critical': 90.0,
            'cpu_warning': 80.0,
            'memory_critical': 95.0,
            'memory_warning': 85.0,
            'disk_critical': 95.0,
            'disk_warning': 90.0,
            'api_response_critical': 5000.0,  # 5 seconds
            'api_response_warning': 2000.0,   # 2 seconds
            'max_position_size': 10.0,
            'max_risk_exposure': 20.0,
            'max_daily_loss': 100.0
        }
        self.last_alerts = {}
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from environment file"""
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value.strip('"\'')
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_file}")
        return config
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network
            network = psutil.net_io_counters()
            
            # Load average
            load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Uptime
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk_percent,
                network_sent=network.bytes_sent,
                network_recv=network.bytes_recv,
                load_average=load_avg,
                uptime_seconds=int(uptime)
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def collect_trading_metrics(self) -> TradingMetrics:
        """Collect trading performance metrics"""
        try:
            # Make API call to get trading data
            api_url = self.config.get('API_URL', 'http://localhost:5000')
            response = requests.get(f"{api_url}/api/trading/metrics", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return TradingMetrics(
                    timestamp=datetime.now().isoformat(),
                    active_positions=data.get('active_positions', 0),
                    total_trades_today=data.get('total_trades_today', 0),
                    profit_loss_today=data.get('profit_loss_today', 0.0),
                    win_rate_today=data.get('win_rate_today', 0.0),
                    largest_position_size=data.get('largest_position_size', 0.0),
                    risk_exposure_percent=data.get('risk_exposure_percent', 0.0),
                    last_trade_time=data.get('last_trade_time', ''),
                    contract_validation_errors=data.get('contract_validation_errors', 0)
                )
            else:
                logger.warning(f"Trading API returned status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error collecting trading metrics: {e}")
            return None
    
    def collect_service_status(self) -> ServiceStatus:
        """Collect service health status"""
        try:
            # Check systemd services
            import subprocess
            
            def check_service(service_name):
                try:
                    result = subprocess.run(
                        ['systemctl', 'is-active', service_name],
                        capture_output=True, text=True, timeout=5
                    )
                    return result.stdout.strip() == 'active'
                except:
                    return False
            
            # Check API response time
            api_response_time = 0.0
            try:
                api_url = self.config.get('API_URL', 'http://localhost:5000')
                start_time = time.time()
                response = requests.get(f"{api_url}/api/health", timeout=10)
                api_response_time = (time.time() - start_time) * 1000
            except:
                api_response_time = 99999.0  # Indicate failure
            
            # Check Bulenox login status
            bulenox_status = False
            try:
                response = requests.get(f"{api_url}/api/bulenox/status", timeout=10)
                if response.status_code == 200:
                    bulenox_status = response.json().get('logged_in', False)
            except:
                pass
            
            return ServiceStatus(
                timestamp=datetime.now().isoformat(),
                bot_service_running=check_service('bulenox-trader'),
                api_service_running=check_service('bulenox-api'),
                nginx_running=check_service('nginx'),
                database_accessible=True,  # If we got here, DB is accessible
                bulenox_login_status=bulenox_status,
                api_response_time_ms=api_response_time,
                last_heartbeat=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error collecting service status: {e}")
            return None
    
    def check_alerts(self, system_metrics: SystemMetrics, trading_metrics: TradingMetrics, 
                    service_status: ServiceStatus):
        """Check for alert conditions and send notifications"""
        alerts = []
        
        # System alerts
        if system_metrics:
            if system_metrics.cpu_percent > self.alert_thresholds['cpu_critical']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='system',
                    message=f"Critical CPU usage: {system_metrics.cpu_percent:.1f}%"
                ))
            elif system_metrics.cpu_percent > self.alert_thresholds['cpu_warning']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='warning',
                    category='system',
                    message=f"High CPU usage: {system_metrics.cpu_percent:.1f}%"
                ))
            
            if system_metrics.memory_percent > self.alert_thresholds['memory_critical']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='system',
                    message=f"Critical memory usage: {system_metrics.memory_percent:.1f}%"
                ))
            
            if system_metrics.disk_percent > self.alert_thresholds['disk_critical']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='system',
                    message=f"Critical disk usage: {system_metrics.disk_percent:.1f}%"
                ))
        
        # Trading alerts
        if trading_metrics:
            if trading_metrics.largest_position_size > self.alert_thresholds['max_position_size']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='warning',
                    category='trading',
                    message=f"Large position size: {trading_metrics.largest_position_size} contracts"
                ))
            
            if trading_metrics.risk_exposure_percent > self.alert_thresholds['max_risk_exposure']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='trading',
                    message=f"High risk exposure: {trading_metrics.risk_exposure_percent:.1f}%"
                ))
            
            if trading_metrics.profit_loss_today < -self.alert_thresholds['max_daily_loss']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='trading',
                    message=f"Daily loss limit exceeded: ${trading_metrics.profit_loss_today:.2f}"
                ))
        
        # Service alerts
        if service_status:
            if not service_status.bot_service_running:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='service',
                    message="Trading bot service is not running"
                ))
            
            if not service_status.bulenox_login_status:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='service',
                    message="Bulenox login failed - trading disabled"
                ))
            
            if service_status.api_response_time_ms > self.alert_thresholds['api_response_critical']:
                alerts.append(Alert(
                    timestamp=datetime.now().isoformat(),
                    severity='critical',
                    category='service',
                    message=f"API response time critical: {service_status.api_response_time_ms:.0f}ms"
                ))
        
        # Store and send alerts
        for alert in alerts:
            self.db.store_alert(alert)
            self.send_alert_notification(alert)
    
    def send_alert_notification(self, alert: Alert):
        """Send alert notification via email/Slack"""
        try:
            # Prevent spam - only send same alert once per hour
            alert_key = f"{alert.category}_{alert.message}"
            now = datetime.now()
            
            if alert_key in self.last_alerts:
                if now - self.last_alerts[alert_key] < timedelta(hours=1):
                    return
            
            self.last_alerts[alert_key] = now
            
            # Send email notification
            if 'ALERT_EMAIL' in self.config:
                self.send_email_alert(alert)
            
            # Send Slack notification
            if 'SLACK_WEBHOOK_URL' in self.config:
                self.send_slack_alert(alert)
                
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
    
    def send_email_alert(self, alert: Alert):
        """Send email alert"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.config.get('SMTP_FROM', 'bot@trading-system.com')
            msg['To'] = self.config['ALERT_EMAIL']
            msg['Subject'] = f"[{alert.severity.upper()}] Trading Bot Alert - {alert.category}"
            
            body = f"""
            Alert Details:
            Timestamp: {alert.timestamp}
            Severity: {alert.severity}
            Category: {alert.category}
            Message: {alert.message}
            
            Please check the trading bot dashboard for more details.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.get('SMTP_HOST', 'localhost'), 
                                 int(self.config.get('SMTP_PORT', 587)))
            server.starttls()
            if 'SMTP_USER' in self.config:
                server.login(self.config['SMTP_USER'], self.config['SMTP_PASS'])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def send_slack_alert(self, alert: Alert):
        """Send Slack alert"""
        try:
            webhook_url = self.config['SLACK_WEBHOOK_URL']
            
            color = {
                'critical': '#FF0000',
                'warning': '#FFA500',
                'info': '#00FF00'
            }.get(alert.severity, '#808080')
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': f"Trading Bot Alert - {alert.severity.upper()}",
                    'fields': [
                        {'title': 'Category', 'value': alert.category, 'short': True},
                        {'title': 'Timestamp', 'value': alert.timestamp, 'short': True},
                        {'title': 'Message', 'value': alert.message, 'short': False}
                    ]
                }]
            }
            
            requests.post(webhook_url, json=payload, timeout=10)
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def generate_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        try:
            system_metrics = self.collect_system_metrics()
            trading_metrics = self.collect_trading_metrics()
            service_status = self.collect_service_status()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'system': asdict(system_metrics) if system_metrics else None,
                'trading': asdict(trading_metrics) if trading_metrics else None,
                'services': asdict(service_status) if service_status else None,
                'overall_health': 'healthy'
            }
            
            # Determine overall health
            if service_status and not service_status.bot_service_running:
                report['overall_health'] = 'critical'
            elif system_metrics and (system_metrics.cpu_percent > 90 or system_metrics.memory_percent > 95):
                report['overall_health'] = 'warning'
            elif trading_metrics and trading_metrics.profit_loss_today < -100:
                report['overall_health'] = 'warning'
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
            return {'error': str(e)}
    
    async def run_monitoring_loop(self, interval: int = 60):
        """Main monitoring loop"""
        logger.info(f"Starting production monitoring loop (interval: {interval}s)")
        
        while True:
            try:
                # Collect metrics
                system_metrics = self.collect_system_metrics()
                trading_metrics = self.collect_trading_metrics()
                service_status = self.collect_service_status()
                
                # Store metrics
                if system_metrics:
                    self.db.store_system_metrics(system_metrics)
                if trading_metrics:
                    self.db.store_trading_metrics(trading_metrics)
                if service_status:
                    self.db.store_service_status(service_status)
                
                # Check for alerts
                self.check_alerts(system_metrics, trading_metrics, service_status)
                
                # Log status
                logger.info(f"Monitoring cycle completed - System: {system_metrics.cpu_percent:.1f}% CPU, "
                           f"Trading: {trading_metrics.active_positions if trading_metrics else 0} positions, "
                           f"Services: {'OK' if service_status and service_status.bot_service_running else 'ERROR'}")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(interval)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Monitoring Dashboard')
    parser.add_argument('--config', default='/opt/trading-bot/.env', help='Configuration file')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--report', action='store_true', help='Generate status report')
    
    args = parser.parse_args()
    
    monitor = ProductionMonitor(args.config)
    
    if args.report:
        # Generate and print status report
        report = monitor.generate_status_report()
        print(json.dumps(report, indent=2))
    elif args.daemon:
        # Run monitoring loop
        asyncio.run(monitor.run_monitoring_loop(args.interval))
    else:
        # Single monitoring cycle
        system_metrics = monitor.collect_system_metrics()
        trading_metrics = monitor.collect_trading_metrics()
        service_status = monitor.collect_service_status()
        
        print("=== System Metrics ===")
        if system_metrics:
            print(f"CPU: {system_metrics.cpu_percent:.1f}%")
            print(f"Memory: {system_metrics.memory_percent:.1f}%")
            print(f"Disk: {system_metrics.disk_percent:.1f}%")
        
        print("\n=== Trading Metrics ===")
        if trading_metrics:
            print(f"Active Positions: {trading_metrics.active_positions}")
            print(f"P&L Today: ${trading_metrics.profit_loss_today:.2f}")
            print(f"Win Rate: {trading_metrics.win_rate_today:.1f}%")
        
        print("\n=== Service Status ===")
        if service_status:
            print(f"Bot Service: {'Running' if service_status.bot_service_running else 'Stopped'}")
            print(f"API Service: {'Running' if service_status.api_service_running else 'Stopped'}")
            print(f"Bulenox Login: {'OK' if service_status.bulenox_login_status else 'Failed'}")
            print(f"API Response: {service_status.api_response_time_ms:.0f}ms")

if __name__ == '__main__':
    main()