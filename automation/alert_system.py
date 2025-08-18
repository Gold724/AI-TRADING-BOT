#!/usr/bin/env python3
"""
TradeBot Sentinel Pro - Alert System Module
Notification and reporting system for trade alerts and system events
"""

import asyncio
import json
import logging
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import os
import requests
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/alert_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Alert type enumeration"""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    INFO = "info"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Notification channel enumeration"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SMS = "sms"
    DISCORD = "discord"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: str
    type: AlertType
    title: str
    message: str
    source: str
    trade_id: Optional[str] = None
    symbol: Optional[str] = None
    amount: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    sent_channels: List[str] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.sent_channels is None:
            self.sent_channels = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class NotificationConfig:
    """Notification configuration"""
    channel: NotificationChannel
    enabled: bool
    config: Dict[str, Any]
    alert_types: List[AlertType]
    rate_limit: Optional[Dict[str, int]] = None  # {'max_per_hour': 10, 'max_per_day': 100}

@dataclass
class ReportConfig:
    """Report configuration"""
    name: str
    enabled: bool
    frequency: str  # 'hourly', 'daily', 'weekly', 'monthly'
    time: str  # '09:00' for daily, 'monday:09:00' for weekly
    channels: List[NotificationChannel]
    template: str
    include_charts: bool = False
    filters: Optional[Dict[str, Any]] = None

class AlertSystem:
    """Comprehensive alert and notification system"""
    
    def __init__(self, config_path: str = "automation/config/alerts.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.db_path = Path("logs/alerts.db")
        self.notification_configs: Dict[str, NotificationConfig] = {}
        self.report_configs: Dict[str, ReportConfig] = {}
        self.alert_queue: deque = deque()
        self.rate_limits: Dict[str, deque] = defaultdict(deque)
        self.running = False
        
        # Initialize database
        self.init_database()
        
        # Load notification configurations
        self.load_notification_configs()
        
        # Load report configurations
        self.load_report_configs()
        
        logger.info("AlertSystem initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load alert system configuration"""
        default_config = {
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": [],
                    "alert_types": ["success", "failure", "critical"],
                    "rate_limit": {"max_per_hour": 10, "max_per_day": 50}
                },
                "telegram": {
                    "enabled": False,
                    "bot_token": "",
                    "chat_ids": [],
                    "alert_types": ["success", "failure", "warning", "critical"],
                    "rate_limit": {"max_per_hour": 20, "max_per_day": 100}
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {},
                    "alert_types": ["success", "failure", "critical"],
                    "rate_limit": {"max_per_hour": 30, "max_per_day": 200}
                },
                "discord": {
                    "enabled": False,
                    "webhook_url": "",
                    "alert_types": ["success", "failure", "warning", "critical"],
                    "rate_limit": {"max_per_hour": 15, "max_per_day": 75}
                }
            },
            "reports": {
                "daily_summary": {
                    "enabled": True,
                    "frequency": "daily",
                    "time": "09:00",
                    "channels": ["email"],
                    "template": "daily_summary",
                    "include_charts": False
                },
                "weekly_performance": {
                    "enabled": True,
                    "frequency": "weekly",
                    "time": "monday:09:00",
                    "channels": ["email"],
                    "template": "weekly_performance",
                    "include_charts": True
                },
                "trade_execution_report": {
                    "enabled": True,
                    "frequency": "hourly",
                    "time": "00",
                    "channels": ["telegram"],
                    "template": "trade_execution",
                    "include_charts": False,
                    "filters": {"min_trades": 1}
                }
            },
            "alert_settings": {
                "max_queue_size": 1000,
                "retry_attempts": 3,
                "retry_delay_seconds": 60,
                "batch_size": 10,
                "processing_interval_seconds": 30
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Deep merge with default config
                    self._deep_merge(default_config, config)
                    logger.info(f"Alert configuration loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading alert config: {e}, using defaults")
        else:
            # Create default config file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Default alert configuration created at {self.config_path}")
        
        return default_config
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def init_database(self):
        """Initialize alerts database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        source TEXT NOT NULL,
                        trade_id TEXT,
                        symbol TEXT,
                        amount REAL,
                        metadata TEXT,
                        sent_channels TEXT,
                        retry_count INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS notifications_sent (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        FOREIGN KEY (alert_id) REFERENCES alerts (id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS reports_sent (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_name TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        report_data TEXT
                    )
                """)
                
                conn.commit()
                logger.info("Alerts database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing alerts database: {e}")
    
    def load_notification_configs(self):
        """Load notification configurations"""
        notifications_config = self.config.get('notifications', {})
        
        for channel_name, config in notifications_config.items():
            if config.get('enabled', False):
                try:
                    channel = NotificationChannel(channel_name)
                    alert_types = [AlertType(t) for t in config.get('alert_types', [])]
                    
                    notification_config = NotificationConfig(
                        channel=channel,
                        enabled=True,
                        config=config,
                        alert_types=alert_types,
                        rate_limit=config.get('rate_limit')
                    )
                    
                    self.notification_configs[channel_name] = notification_config
                    logger.info(f"Notification channel '{channel_name}' configured")
                    
                except Exception as e:
                    logger.error(f"Error configuring notification channel '{channel_name}': {e}")
    
    def load_report_configs(self):
        """Load report configurations"""
        reports_config = self.config.get('reports', {})
        
        for report_name, config in reports_config.items():
            if config.get('enabled', False):
                try:
                    channels = [NotificationChannel(c) for c in config.get('channels', [])]
                    
                    report_config = ReportConfig(
                        name=report_name,
                        enabled=True,
                        frequency=config.get('frequency', 'daily'),
                        time=config.get('time', '09:00'),
                        channels=channels,
                        template=config.get('template', 'default'),
                        include_charts=config.get('include_charts', False),
                        filters=config.get('filters')
                    )
                    
                    self.report_configs[report_name] = report_config
                    logger.info(f"Report '{report_name}' configured")
                    
                except Exception as e:
                    logger.error(f"Error configuring report '{report_name}': {e}")
    
    async def send_alert(self, alert_type: AlertType, title: str, message: str, 
                        source: str = "system", trade_id: Optional[str] = None,
                        symbol: Optional[str] = None, amount: Optional[float] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Send an alert through configured channels"""
        
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            type=alert_type,
            title=title,
            message=message,
            source=source,
            trade_id=trade_id,
            symbol=symbol,
            amount=amount,
            metadata=metadata or {}
        )
        
        # Store alert in database
        await self.store_alert(alert)
        
        # Add to processing queue
        self.alert_queue.append(alert)
        
        logger.info(f"Alert queued: {alert_type.value} - {title}")
        return alert_id
    
    async def store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alerts 
                    (id, timestamp, type, title, message, source, trade_id, symbol, amount, metadata, sent_channels, retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id,
                    alert.timestamp,
                    alert.type.value,
                    alert.title,
                    alert.message,
                    alert.source,
                    alert.trade_id,
                    alert.symbol,
                    alert.amount,
                    json.dumps(alert.metadata),
                    json.dumps(alert.sent_channels),
                    alert.retry_count
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def process_alert_queue(self):
        """Process alerts in the queue"""
        batch_size = self.config.get('alert_settings', {}).get('batch_size', 10)
        
        while self.alert_queue and len(self.alert_queue) > 0:
            # Process alerts in batches
            batch = []
            for _ in range(min(batch_size, len(self.alert_queue))):
                if self.alert_queue:
                    batch.append(self.alert_queue.popleft())
            
            # Process each alert in the batch
            for alert in batch:
                await self.process_single_alert(alert)
    
    async def process_single_alert(self, alert: Alert):
        """Process a single alert"""
        try:
            # Find applicable notification channels
            applicable_channels = []
            for channel_name, config in self.notification_configs.items():
                if alert.type in config.alert_types:
                    if self.check_rate_limit(channel_name, config.rate_limit):
                        applicable_channels.append((channel_name, config))
            
            # Send to each applicable channel
            for channel_name, config in applicable_channels:
                try:
                    success = await self.send_notification(alert, config)
                    
                    # Record notification attempt
                    await self.record_notification_attempt(
                        alert.id, channel_name, success, None if success else "Failed to send"
                    )
                    
                    if success:
                        alert.sent_channels.append(channel_name)
                        self.update_rate_limit(channel_name)
                        logger.info(f"Alert {alert.id} sent via {channel_name}")
                    else:
                        logger.error(f"Failed to send alert {alert.id} via {channel_name}")
                        
                except Exception as e:
                    logger.error(f"Error sending alert {alert.id} via {channel_name}: {e}")
                    await self.record_notification_attempt(
                        alert.id, channel_name, False, str(e)
                    )
            
            # Update alert in database
            await self.update_alert_status(alert)
            
        except Exception as e:
            logger.error(f"Error processing alert {alert.id}: {e}")
    
    async def send_notification(self, alert: Alert, config: NotificationConfig) -> bool:
        """Send notification via specific channel"""
        try:
            if config.channel == NotificationChannel.EMAIL:
                return await self.send_email_notification(alert, config)
            elif config.channel == NotificationChannel.TELEGRAM:
                return await self.send_telegram_notification(alert, config)
            elif config.channel == NotificationChannel.WEBHOOK:
                return await self.send_webhook_notification(alert, config)
            elif config.channel == NotificationChannel.DISCORD:
                return await self.send_discord_notification(alert, config)
            else:
                logger.warning(f"Unsupported notification channel: {config.channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending {config.channel.value} notification: {e}")
            return False
    
    async def send_email_notification(self, alert: Alert, config: NotificationConfig) -> bool:
        """Send email notification"""
        try:
            smtp_config = config.config
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_config['from_email']
            msg['To'] = ', '.join(smtp_config['to_emails'])
            msg['Subject'] = f"TradeBot Alert: {alert.title}"
            
            # Create email body
            body = self.format_alert_message(alert, 'email')
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    async def send_telegram_notification(self, alert: Alert, config: NotificationConfig) -> bool:
        """Send Telegram notification"""
        try:
            telegram_config = config.config
            bot_token = telegram_config['bot_token']
            chat_ids = telegram_config['chat_ids']
            
            message = self.format_alert_message(alert, 'telegram')
            
            success_count = 0
            for chat_id in chat_ids:
                try:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = {
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                    
                    response = requests.post(url, json=data, timeout=10)
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        logger.error(f"Telegram API error: {response.text}")
                        
                except Exception as e:
                    logger.error(f"Error sending to Telegram chat {chat_id}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False
    
    async def send_webhook_notification(self, alert: Alert, config: NotificationConfig) -> bool:
        """Send webhook notification"""
        try:
            webhook_config = config.config
            url = webhook_config['url']
            headers = webhook_config.get('headers', {})
            
            payload = {
                'alert': asdict(alert),
                'timestamp': datetime.now().isoformat(),
                'source': 'tradebot_sentinel_pro'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response.status_code < 400
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False
    
    async def send_discord_notification(self, alert: Alert, config: NotificationConfig) -> bool:
        """Send Discord notification"""
        try:
            discord_config = config.config
            webhook_url = discord_config['webhook_url']
            
            # Create Discord embed
            color_map = {
                AlertType.SUCCESS: 0x28a745,
                AlertType.FAILURE: 0xdc3545,
                AlertType.WARNING: 0xffc107,
                AlertType.INFO: 0x17a2b8,
                AlertType.CRITICAL: 0x6f42c1
            }
            
            embed = {
                'title': alert.title,
                'description': alert.message,
                'color': color_map.get(alert.type, 0x6c757d),
                'timestamp': alert.timestamp,
                'fields': []
            }
            
            if alert.symbol:
                embed['fields'].append({'name': 'Symbol', 'value': alert.symbol, 'inline': True})
            if alert.amount:
                embed['fields'].append({'name': 'Amount', 'value': f'${alert.amount:,.2f}', 'inline': True})
            if alert.trade_id:
                embed['fields'].append({'name': 'Trade ID', 'value': alert.trade_id, 'inline': True})
            
            payload = {
                'embeds': [embed],
                'username': 'TradeBot Sentinel Pro'
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code < 400
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False
    
    def format_alert_message(self, alert: Alert, format_type: str) -> str:
        """Format alert message for different channels"""
        if format_type == 'email':
            return f"""
            <html>
            <body>
                <h2>🤖 TradeBot Sentinel Pro Alert</h2>
                <p><strong>Type:</strong> {alert.type.value.upper()}</p>
                <p><strong>Time:</strong> {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Source:</strong> {alert.source}</p>
                <hr>
                <h3>{alert.title}</h3>
                <p>{alert.message}</p>
                {f'<p><strong>Symbol:</strong> {alert.symbol}</p>' if alert.symbol else ''}
                {f'<p><strong>Amount:</strong> ${alert.amount:,.2f}</p>' if alert.amount else ''}
                {f'<p><strong>Trade ID:</strong> {alert.trade_id}</p>' if alert.trade_id else ''}
                <hr>
                <p><small>Generated by TradeBot Sentinel Pro</small></p>
            </body>
            </html>
            """
        
        elif format_type == 'telegram':
            message = f"🤖 <b>TradeBot Alert</b>\n\n"
            message += f"<b>{alert.title}</b>\n"
            message += f"{alert.message}\n\n"
            message += f"<b>Type:</b> {alert.type.value.upper()}\n"
            message += f"<b>Time:</b> {datetime.fromisoformat(alert.timestamp).strftime('%H:%M:%S')}\n"
            if alert.symbol:
                message += f"<b>Symbol:</b> {alert.symbol}\n"
            if alert.amount:
                message += f"<b>Amount:</b> ${alert.amount:,.2f}\n"
            if alert.trade_id:
                message += f"<b>Trade ID:</b> {alert.trade_id}\n"
            return message
        
        else:
            # Plain text format
            message = f"TradeBot Alert: {alert.title}\n"
            message += f"Type: {alert.type.value.upper()}\n"
            message += f"Time: {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"Message: {alert.message}\n"
            if alert.symbol:
                message += f"Symbol: {alert.symbol}\n"
            if alert.amount:
                message += f"Amount: ${alert.amount:,.2f}\n"
            if alert.trade_id:
                message += f"Trade ID: {alert.trade_id}\n"
            return message
    
    def check_rate_limit(self, channel: str, rate_limit: Optional[Dict[str, int]]) -> bool:
        """Check if channel is within rate limits"""
        if not rate_limit:
            return True
        
        now = datetime.now()
        channel_history = self.rate_limits[channel]
        
        # Clean old entries
        while channel_history and (now - datetime.fromisoformat(channel_history[0])).total_seconds() > 3600:
            channel_history.popleft()
        
        # Check hourly limit
        if 'max_per_hour' in rate_limit:
            if len(channel_history) >= rate_limit['max_per_hour']:
                return False
        
        # Check daily limit
        if 'max_per_day' in rate_limit:
            daily_count = sum(1 for ts in channel_history 
                            if (now - datetime.fromisoformat(ts)).total_seconds() < 86400)
            if daily_count >= rate_limit['max_per_day']:
                return False
        
        return True
    
    def update_rate_limit(self, channel: str):
        """Update rate limit tracking for channel"""
        self.rate_limits[channel].append(datetime.now().isoformat())
    
    async def record_notification_attempt(self, alert_id: str, channel: str, 
                                        success: bool, error_message: Optional[str]):
        """Record notification attempt in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO notifications_sent 
                    (alert_id, channel, timestamp, success, error_message)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    alert_id,
                    channel,
                    datetime.now().isoformat(),
                    success,
                    error_message
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording notification attempt: {e}")
    
    async def update_alert_status(self, alert: Alert):
        """Update alert status in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET sent_channels = ?, retry_count = ?
                    WHERE id = ?
                """, (
                    json.dumps(alert.sent_channels),
                    alert.retry_count,
                    alert.id
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
    
    async def generate_report(self, report_name: str) -> Optional[Dict[str, Any]]:
        """Generate a report"""
        try:
            if report_name not in self.report_configs:
                logger.error(f"Report configuration not found: {report_name}")
                return None
            
            config = self.report_configs[report_name]
            
            # Generate report data based on template
            if config.template == 'daily_summary':
                return await self.generate_daily_summary_report()
            elif config.template == 'weekly_performance':
                return await self.generate_weekly_performance_report()
            elif config.template == 'trade_execution':
                return await self.generate_trade_execution_report(config.filters)
            else:
                logger.error(f"Unknown report template: {config.template}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating report {report_name}: {e}")
            return None
    
    async def generate_daily_summary_report(self) -> Dict[str, Any]:
        """Generate daily summary report"""
        try:
            today = datetime.now().date()
            
            # Get trade statistics
            with sqlite3.connect(Path("logs/trades.db")) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_trades,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_trades,
                        SUM(CASE WHEN status = 'success' THEN amount ELSE 0 END) as total_volume,
                        AVG(execution_time) as avg_execution_time
                    FROM trades 
                    WHERE date(timestamp) = date('now')
                """)
                
                trade_stats = cursor.fetchone()
            
            # Get alert statistics
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(CASE WHEN type = 'success' THEN 1 END) as success_alerts,
                        COUNT(CASE WHEN type = 'failure' THEN 1 END) as failure_alerts,
                        COUNT(CASE WHEN type = 'warning' THEN 1 END) as warning_alerts
                    FROM alerts 
                    WHERE date(timestamp) = date('now')
                """)
                
                alert_stats = cursor.fetchone()
            
            return {
                'report_type': 'daily_summary',
                'date': today.isoformat(),
                'trade_statistics': {
                    'total_trades': trade_stats[0] if trade_stats[0] else 0,
                    'successful_trades': trade_stats[1] if trade_stats[1] else 0,
                    'failed_trades': trade_stats[2] if trade_stats[2] else 0,
                    'success_rate': (trade_stats[1] / trade_stats[0] * 100) if trade_stats[0] and trade_stats[0] > 0 else 0,
                    'total_volume': trade_stats[3] if trade_stats[3] else 0.0,
                    'avg_execution_time': trade_stats[4] if trade_stats[4] else 0.0
                },
                'alert_statistics': {
                    'total_alerts': alert_stats[0] if alert_stats[0] else 0,
                    'success_alerts': alert_stats[1] if alert_stats[1] else 0,
                    'failure_alerts': alert_stats[2] if alert_stats[2] else 0,
                    'warning_alerts': alert_stats[3] if alert_stats[3] else 0
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating daily summary report: {e}")
            return None
    
    async def generate_weekly_performance_report(self) -> Dict[str, Any]:
        """Generate weekly performance report"""
        # Implementation for weekly performance report
        # This would include more detailed analytics, charts, etc.
        pass
    
    async def generate_trade_execution_report(self, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate trade execution report"""
        # Implementation for trade execution report
        # This would focus on recent trade executions
        pass
    
    async def start_alert_system(self):
        """Start the alert system"""
        self.running = True
        logger.info("Alert system started")
        
        # Start processing loop
        processing_interval = self.config.get('alert_settings', {}).get('processing_interval_seconds', 30)
        
        while self.running:
            try:
                await self.process_alert_queue()
                await asyncio.sleep(processing_interval)
                
            except KeyboardInterrupt:
                logger.info("Alert system interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in alert system loop: {e}")
                await asyncio.sleep(5)
    
    async def stop_alert_system(self):
        """Stop the alert system"""
        self.running = False
        logger.info("Alert system stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get alert system status"""
        return {
            'running': self.running,
            'queue_size': len(self.alert_queue),
            'notification_channels': list(self.notification_configs.keys()),
            'report_configs': list(self.report_configs.keys()),
            'rate_limits': {k: len(v) for k, v in self.rate_limits.items()}
        }

# Convenience functions for quick alerts
async def send_trade_success_alert(alert_system: AlertSystem, trade_id: str, 
                                 symbol: str, amount: float):
    """Send trade success alert"""
    await alert_system.send_alert(
        AlertType.SUCCESS,
        "Trade Executed Successfully",
        f"Trade {trade_id} for {symbol} executed successfully",
        source="trade_executor",
        trade_id=trade_id,
        symbol=symbol,
        amount=amount
    )

async def send_trade_failure_alert(alert_system: AlertSystem, trade_id: str, 
                                 symbol: str, amount: float, error: str):
    """Send trade failure alert"""
    await alert_system.send_alert(
        AlertType.FAILURE,
        "Trade Execution Failed",
        f"Trade {trade_id} for {symbol} failed: {error}",
        source="trade_executor",
        trade_id=trade_id,
        symbol=symbol,
        amount=amount,
        metadata={'error': error}
    )

async def send_system_alert(alert_system: AlertSystem, alert_type: AlertType, 
                          title: str, message: str):
    """Send system alert"""
    await alert_system.send_alert(
        alert_type,
        title,
        message,
        source="system"
    )