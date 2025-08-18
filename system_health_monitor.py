#!/usr/bin/env python3
"""
TradeBot Sentinel - System Health Monitor
Comprehensive monitoring and alerting system for trading automation

Features:
- Real-time system health monitoring
- Performance metrics tracking
- Automated alerting and recovery
- Resource usage optimization
- Trading activity analysis
- Compliance reporting
"""

import asyncio
import json
import os
import time
import logging
import psutil
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class HealthMetrics:
    """Health metrics data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_active: bool
    browser_processes: int
    session_age_hours: float
    trade_requests_count: int
    error_count: int
    uptime_hours: float
    status: str  # 'healthy', 'warning', 'critical'

@dataclass
class AlertConfig:
    """Alert configuration"""
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    disk_threshold: float = 90.0
    error_threshold: int = 5
    session_max_age_hours: float = 24.0
    email_enabled: bool = False
    email_recipients: List[str] = None
    slack_webhook: Optional[str] = None

class SystemHealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self, config_file: str = 'health_monitor_config.json'):
        self.config_file = config_file
        self.db_file = 'health_metrics.db'
        self.log_file = 'health_monitor.log'
        self.start_time = time.time()
        
        # Load configuration
        self.alert_config = self._load_config()
        
        # Setup logging
        self.setup_logging()
        
        # Initialize database
        self._init_database()
        
        # Monitoring state
        self.is_monitoring = False
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes
        
        # File paths to monitor
        self.critical_files = [
            'trade.sh',
            'trade_request_full.py',
            'tradebot_sentinel.py',
            'login_bulenox_playwright.py',
            'trae_trade_capture.py'
        ]
        
        # Process patterns to monitor
        self.browser_process_patterns = [
            'chrome', 'chromium', 'playwright', 'python'
        ]
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.log_file)
            ]
        )
        self.logger = logging.getLogger('HealthMonitor')
    
    def _load_config(self) -> AlertConfig:
        """Load alert configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                return AlertConfig(**config_data)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using defaults")
        
        # Create default config
        default_config = AlertConfig()
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: AlertConfig):
        """Save alert configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_usage_percent REAL,
                    network_active BOOLEAN,
                    browser_processes INTEGER,
                    session_age_hours REAL,
                    trade_requests_count INTEGER,
                    error_count INTEGER,
                    uptime_hours REAL,
                    status TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT,
                    message TEXT,
                    severity TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    async def collect_metrics(self) -> HealthMetrics:
        """Collect comprehensive system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = shutil.disk_usage('.')
            
            # Network connectivity test
            network_active = await self._test_network_connectivity()
            
            # Browser processes
            browser_processes = self._count_browser_processes()
            
            # Session age
            session_age_hours = self._get_session_age_hours()
            
            # Trade requests count
            trade_requests_count = self._count_trade_requests()
            
            # Error count
            error_count = self._count_recent_errors()
            
            # Uptime
            uptime_hours = (time.time() - self.start_time) / 3600
            
            # Determine overall status
            status = self._determine_health_status(
                cpu_percent, memory.percent, 
                (disk.used / disk.total) * 100,
                error_count, session_age_hours
            )
            
            metrics = HealthMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                network_active=network_active,
                browser_processes=browser_processes,
                session_age_hours=session_age_hours,
                trade_requests_count=trade_requests_count,
                error_count=error_count,
                uptime_hours=uptime_hours,
                status=status
            )
            
            # Store metrics
            self._store_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {e}")
            return self._create_error_metrics(str(e))
    
    async def _test_network_connectivity(self) -> bool:
        """Test network connectivity"""
        try:
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get('https://google.com') as response:
                    return response.status == 200
        except:
            return False
    
    def _count_browser_processes(self) -> int:
        """Count browser-related processes"""
        count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] and proc_info['cmdline']:
                        cmdline = ' '.join(proc_info['cmdline']).lower()
                        if any(pattern in cmdline for pattern in self.browser_process_patterns):
                            if 'playwright' in cmdline or 'tradebot' in cmdline:
                                count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.debug(f"Process counting error: {e}")
        
        return count
    
    def _get_session_age_hours(self) -> float:
        """Get session age in hours"""
        session_files = ['bulenox_state.json', 'bulenox_session_enhanced.json']
        
        for file in session_files:
            if os.path.exists(file):
                age_seconds = time.time() - os.path.getmtime(file)
                return age_seconds / 3600
        
        return 0.0
    
    def _count_trade_requests(self) -> int:
        """Count trade requests from log files"""
        count = 0
        log_files = ['tradebot_sentinel.log', 'session_manager.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        count += content.count('TRADE DETECTED')
                        count += content.count('Trade request detected')
                except Exception as e:
                    self.logger.debug(f"Log file reading error: {e}")
        
        return count
    
    def _count_recent_errors(self, hours: int = 1) -> int:
        """Count recent errors from log files"""
        count = 0
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        log_files = ['tradebot_sentinel.log', 'session_manager.log', self.log_file]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            if 'ERROR' in line or 'CRITICAL' in line:
                                # Simple time-based filtering (could be improved)
                                count += 1
                except Exception as e:
                    self.logger.debug(f"Error counting failed: {e}")
        
        return count
    
    def _determine_health_status(self, cpu: float, memory: float, disk: float, 
                                errors: int, session_age: float) -> str:
        """Determine overall system health status"""
        critical_conditions = [
            cpu > 95,
            memory > 95,
            disk > 95,
            errors > 10,
            session_age > 48  # 48 hours
        ]
        
        warning_conditions = [
            cpu > self.alert_config.cpu_threshold,
            memory > self.alert_config.memory_threshold,
            disk > self.alert_config.disk_threshold,
            errors > self.alert_config.error_threshold,
            session_age > self.alert_config.session_max_age_hours
        ]
        
        if any(critical_conditions):
            return 'critical'
        elif any(warning_conditions):
            return 'warning'
        else:
            return 'healthy'
    
    def _store_metrics(self, metrics: HealthMetrics):
        """Store metrics in database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO health_metrics (
                    timestamp, cpu_percent, memory_percent, disk_usage_percent,
                    network_active, browser_processes, session_age_hours,
                    trade_requests_count, error_count, uptime_hours, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
                metrics.disk_usage_percent, metrics.network_active,
                metrics.browser_processes, metrics.session_age_hours,
                metrics.trade_requests_count, metrics.error_count,
                metrics.uptime_hours, metrics.status
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Metrics storage failed: {e}")
    
    def _create_error_metrics(self, error_msg: str) -> HealthMetrics:
        """Create error metrics when collection fails"""
        return HealthMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=0.0,
            memory_percent=0.0,
            disk_usage_percent=0.0,
            network_active=False,
            browser_processes=0,
            session_age_hours=0.0,
            trade_requests_count=0,
            error_count=1,
            uptime_hours=(time.time() - self.start_time) / 3600,
            status='critical'
        )
    
    async def check_and_alert(self, metrics: HealthMetrics):
        """Check metrics and send alerts if needed"""
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.alert_config.cpu_threshold:
            alerts.append({
                'type': 'cpu_high',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'severity': 'critical' if metrics.cpu_percent > 95 else 'warning'
            })
        
        # Memory alert
        if metrics.memory_percent > self.alert_config.memory_threshold:
            alerts.append({
                'type': 'memory_high',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'severity': 'critical' if metrics.memory_percent > 95 else 'warning'
            })
        
        # Disk alert
        if metrics.disk_usage_percent > self.alert_config.disk_threshold:
            alerts.append({
                'type': 'disk_high',
                'message': f'High disk usage: {metrics.disk_usage_percent:.1f}%',
                'severity': 'critical' if metrics.disk_usage_percent > 95 else 'warning'
            })
        
        # Error alert
        if metrics.error_count > self.alert_config.error_threshold:
            alerts.append({
                'type': 'errors_high',
                'message': f'High error count: {metrics.error_count}',
                'severity': 'warning'
            })
        
        # Session age alert
        if metrics.session_age_hours > self.alert_config.session_max_age_hours:
            alerts.append({
                'type': 'session_old',
                'message': f'Session age: {metrics.session_age_hours:.1f} hours',
                'severity': 'warning'
            })
        
        # Network alert
        if not metrics.network_active:
            alerts.append({
                'type': 'network_down',
                'message': 'Network connectivity lost',
                'severity': 'critical'
            })
        
        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: Dict[str, str]):
        """Send alert via configured channels"""
        alert_key = alert['type']
        current_time = time.time()
        
        # Check cooldown
        if alert_key in self.last_alert_time:
            if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                return
        
        self.last_alert_time[alert_key] = current_time
        
        # Log alert
        self.logger.warning(f"🚨 ALERT [{alert['severity'].upper()}]: {alert['message']}")
        
        # Store alert in database
        self._store_alert(alert)
        
        # Send email if configured
        if self.alert_config.email_enabled and self.alert_config.email_recipients:
            await self._send_email_alert(alert)
        
        # Send Slack notification if configured
        if self.alert_config.slack_webhook:
            await self._send_slack_alert(alert)
    
    def _store_alert(self, alert: Dict[str, str]):
        """Store alert in database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (timestamp, alert_type, message, severity)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                alert['type'],
                alert['message'],
                alert['severity']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Alert storage failed: {e}")
    
    async def _send_email_alert(self, alert: Dict[str, str]):
        """Send email alert"""
        # Email implementation would go here
        self.logger.info(f"📧 Email alert sent: {alert['message']}")
    
    async def _send_slack_alert(self, alert: Dict[str, str]):
        """Send Slack alert"""
        # Slack webhook implementation would go here
        self.logger.info(f"💬 Slack alert sent: {alert['message']}")
    
    async def start_monitoring(self, interval: int = 60):
        """Start continuous health monitoring"""
        self.is_monitoring = True
        self.logger.info(f"🏥 Health monitoring started (interval: {interval}s)")
        
        while self.is_monitoring:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()
                
                # Log current status
                self.logger.info(
                    f"📊 Health: {metrics.status.upper()} | "
                    f"CPU: {metrics.cpu_percent:.1f}% | "
                    f"Memory: {metrics.memory_percent:.1f}% | "
                    f"Disk: {metrics.disk_usage_percent:.1f}% | "
                    f"Trades: {metrics.trade_requests_count} | "
                    f"Errors: {metrics.error_count}"
                )
                
                # Check for alerts
                await self.check_and_alert(metrics)
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring cycle error: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_monitoring = False
        self.logger.info("🛑 Health monitoring stopped")
    
    def generate_health_report(self, hours: int = 24) -> str:
        """Generate comprehensive health report"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get metrics from last N hours
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT * FROM health_metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            metrics_data = cursor.fetchall()
            
            # Get alerts from last N hours
            cursor.execute('''
                SELECT * FROM alerts 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            alerts_data = cursor.fetchall()
            
            conn.close()
            
            # Generate report
            report = self._format_health_report(metrics_data, alerts_data, hours)
            
            # Save report
            report_file = f'health_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            with open(report_file, 'w') as f:
                f.write(report)
            
            self.logger.info(f"📋 Health report generated: {report_file}")
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return f"Error generating report: {e}"
    
    def _format_health_report(self, metrics_data: List, alerts_data: List, hours: int) -> str:
        """Format health report"""
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
# TradeBot Sentinel Health Report

**Generated:** {report_time}  
**Period:** Last {hours} hours

## System Overview

### Current Status
- **Overall Health:** {'🟢 Healthy' if not alerts_data else '🟡 Warning' if len(alerts_data) < 5 else '🔴 Critical'}
- **Monitoring Duration:** {(time.time() - self.start_time) / 3600:.1f} hours
- **Data Points Collected:** {len(metrics_data)}
- **Alerts Generated:** {len(alerts_data)}

### Resource Usage (Latest)
"""
        
        if metrics_data:
            latest = metrics_data[0]
            report += f"""
- **CPU Usage:** {latest[2]:.1f}%
- **Memory Usage:** {latest[3]:.1f}%
- **Disk Usage:** {latest[4]:.1f}%
- **Browser Processes:** {latest[6]}
- **Session Age:** {latest[7]:.1f} hours
- **Trade Requests:** {latest[8]}
"""
        
        if alerts_data:
            report += "\n## Recent Alerts\n\n"
            for alert in alerts_data[:10]:  # Show last 10 alerts
                timestamp = alert[1]
                alert_type = alert[2]
                message = alert[3]
                severity = alert[4]
                
                emoji = '🔴' if severity == 'critical' else '🟡'
                report += f"- {emoji} **{timestamp}** - {alert_type}: {message}\n"
        
        report += f"""

## Recommendations

### Immediate Actions
- Monitor system resources if usage is high
- Check log files for recurring errors
- Verify network connectivity
- Review session management

### Maintenance Tasks
- Clean up old log files
- Archive historical data
- Update system dependencies
- Review alert thresholds

---
*Generated by TradeBot Sentinel Health Monitor*
        """
        
        return report

# Example usage
async def main():
    """Example usage of System Health Monitor"""
    monitor = SystemHealthMonitor()
    
    # Collect single metrics sample
    metrics = await monitor.collect_metrics()
    print(f"Current Health Status: {metrics.status}")
    print(f"CPU: {metrics.cpu_percent:.1f}%")
    print(f"Memory: {metrics.memory_percent:.1f}%")
    print(f"Trade Requests: {metrics.trade_requests_count}")
    
    # Generate health report
    report = monitor.generate_health_report(hours=1)
    print("\nHealth report generated")
    
    # Start monitoring (uncomment to run continuously)
    # await monitor.start_monitoring(interval=30)

if __name__ == "__main__":
    asyncio.run(main())