#!/usr/bin/env python3
"""
AI Trading Sentinel - Alert Manager
TRAE-SentinelOps: Critical event notification system for 24/7 reliability

Handles:
- Email alerts for critical failures
- Slack notifications for trading events
- SMS alerts for emergency situations
- Alert throttling and escalation
- Multi-channel notification routing
"""

import os
import sys
import json
import time
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from dataclasses import dataclass, asdict
from enum import Enum

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    DISCORD = "discord"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    message: str
    source: str
    tags: List[str]
    metadata: Dict[str, Any]
    channels: List[AlertChannel]
    acknowledged: bool = False
    resolved: bool = False
    escalated: bool = False

class AlertThrottler:
    """Prevents alert spam with intelligent throttling"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.alert_history = {}
        self.throttle_windows = {
            AlertSeverity.INFO: 300,      # 5 minutes
            AlertSeverity.WARNING: 180,   # 3 minutes
            AlertSeverity.ERROR: 60,      # 1 minute
            AlertSeverity.CRITICAL: 30,   # 30 seconds
            AlertSeverity.EMERGENCY: 0    # No throttling
        }
    
    def should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent based on throttling rules"""
        alert_key = f"{alert.source}:{alert.title}"
        current_time = datetime.now()
        
        # Emergency alerts always go through
        if alert.severity == AlertSeverity.EMERGENCY:
            return True
        
        # Check throttle window
        if alert_key in self.alert_history:
            last_sent = self.alert_history[alert_key]['last_sent']
            throttle_window = self.throttle_windows[alert.severity]
            
            if (current_time - last_sent).total_seconds() < throttle_window:
                # Update count but don't send
                self.alert_history[alert_key]['count'] += 1
                return False
        
        # Record this alert
        self.alert_history[alert_key] = {
            'last_sent': current_time,
            'count': 1,
            'severity': alert.severity
        }
        
        return True
    
    def get_throttled_summary(self) -> Dict:
        """Get summary of throttled alerts"""
        summary = {}
        current_time = datetime.now()
        
        for alert_key, data in self.alert_history.items():
            if data['count'] > 1:
                time_diff = (current_time - data['last_sent']).total_seconds()
                summary[alert_key] = {
                    'count': data['count'],
                    'severity': data['severity'].value,
                    'last_occurrence': data['last_sent'].isoformat(),
                    'minutes_ago': int(time_diff / 60)
                }
        
        return summary

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email', self.username)
        self.to_emails = config.get('to_emails', [])
    
    def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        try:
            if not self.username or not self.password:
                return False
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] AI Trading Sentinel: {alert.title}"
            
            # Email body
            body = self._format_email_body(alert)
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False
    
    def _format_email_body(self, alert: Alert) -> str:
        """Format alert as HTML email"""
        severity_colors = {
            AlertSeverity.INFO: '#17a2b8',
            AlertSeverity.WARNING: '#ffc107',
            AlertSeverity.ERROR: '#dc3545',
            AlertSeverity.CRITICAL: '#dc3545',
            AlertSeverity.EMERGENCY: '#6f42c1'
        }
        
        color = severity_colors.get(alert.severity, '#6c757d')
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="border-left: 4px solid {color}; padding-left: 20px; margin-bottom: 20px;">
                <h2 style="color: {color}; margin: 0;">{alert.title}</h2>
                <p style="color: #666; margin: 5px 0;">Severity: <strong>{alert.severity.value.upper()}</strong></p>
                <p style="color: #666; margin: 5px 0;">Source: <strong>{alert.source}</strong></p>
                <p style="color: #666; margin: 5px 0;">Time: <strong>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</strong></p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="margin-top: 0;">Message:</h3>
                <p style="white-space: pre-wrap;">{alert.message}</p>
            </div>
            
            {self._format_metadata_table(alert.metadata)}
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <p style="color: #6c757d; font-size: 12px; margin: 0;">
                    This alert was generated by AI Trading Sentinel monitoring system.<br>
                    Alert ID: {alert.id}
                </p>
            </div>
        </body>
        </html>
        """
    
    def _format_metadata_table(self, metadata: Dict) -> str:
        """Format metadata as HTML table"""
        if not metadata:
            return ""
        
        rows = ""
        for key, value in metadata.items():
            rows += f"<tr><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'><strong>{key}</strong></td><td style='padding: 8px; border-bottom: 1px solid #dee2e6;'>{value}</td></tr>"
        
        return f"""
        <div style="margin-bottom: 20px;">
            <h3>Additional Information:</h3>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #dee2e6;">
                {rows}
            </table>
        </div>
        """

class SlackNotifier:
    """Slack notification handler"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel', '#alerts')
        self.username = config.get('username', 'AI Trading Sentinel')
    
    def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        try:
            if not self.webhook_url:
                return False
            
            # Format Slack message
            payload = self._format_slack_payload(alert)
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False
    
    def _format_slack_payload(self, alert: Alert) -> Dict:
        """Format alert as Slack message"""
        severity_colors = {
            AlertSeverity.INFO: '#36a64f',
            AlertSeverity.WARNING: '#ffcc00',
            AlertSeverity.ERROR: '#ff0000',
            AlertSeverity.CRITICAL: '#ff0000',
            AlertSeverity.EMERGENCY: '#800080'
        }
        
        severity_emojis = {
            AlertSeverity.INFO: ':information_source:',
            AlertSeverity.WARNING: ':warning:',
            AlertSeverity.ERROR: ':x:',
            AlertSeverity.CRITICAL: ':rotating_light:',
            AlertSeverity.EMERGENCY: ':sos:'
        }
        
        color = severity_colors.get(alert.severity, '#808080')
        emoji = severity_emojis.get(alert.severity, ':bell:')
        
        # Build fields for metadata
        fields = []
        if alert.metadata:
            for key, value in list(alert.metadata.items())[:5]:  # Limit to 5 fields
                fields.append({
                    "title": key.replace('_', ' ').title(),
                    "value": str(value),
                    "short": True
                })
        
        return {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": ":robot_face:",
            "attachments": [{
                "color": color,
                "title": f"{emoji} {alert.title}",
                "text": alert.message,
                "fields": [
                    {
                        "title": "Severity",
                        "value": alert.severity.value.upper(),
                        "short": True
                    },
                    {
                        "title": "Source",
                        "value": alert.source,
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "short": True
                    }
                ] + fields,
                "footer": "AI Trading Sentinel",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": int(alert.timestamp.timestamp())
            }]
        }

class WebhookNotifier:
    """Generic webhook notification handler"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.webhook_urls = config.get('webhook_urls', [])
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
    
    def send_alert(self, alert: Alert) -> bool:
        """Send webhook alert"""
        success_count = 0
        
        for url in self.webhook_urls:
            try:
                payload = {
                    'alert_id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'message': alert.message,
                    'source': alert.source,
                    'tags': alert.tags,
                    'metadata': alert.metadata
                }
                
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code in [200, 201, 202]:
                    success_count += 1
                    
            except Exception as e:
                print(f"Webhook notification to {url} failed: {e}")
        
        return success_count > 0

class AlertManager:
    """Main alert management system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.throttler = AlertThrottler(self.config.get('throttling', {}))
        self.notifiers = self._initialize_notifiers()
        self.alert_log = Path(self.config.get('alert_log_path', '/app/logs/alerts.json'))
        self.alert_log.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load alert configuration"""
        default_config = {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': os.getenv('ALERT_EMAIL_USER'),
                'password': os.getenv('ALERT_EMAIL_PASS'),
                'to_emails': [os.getenv('ALERT_EMAIL_TO', '')]
            },
            'slack': {
                'enabled': False,
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                'channel': '#trading-alerts'
            },
            'webhook': {
                'enabled': False,
                'webhook_urls': []
            },
            'throttling': {
                'enabled': True
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge configs
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            except Exception as e:
                print(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _initialize_notifiers(self) -> Dict:
        """Initialize notification handlers"""
        notifiers = {}
        
        if self.config['email']['enabled']:
            notifiers[AlertChannel.EMAIL] = EmailNotifier(self.config['email'])
        
        if self.config['slack']['enabled']:
            notifiers[AlertChannel.SLACK] = SlackNotifier(self.config['slack'])
        
        if self.config['webhook']['enabled']:
            notifiers[AlertChannel.WEBHOOK] = WebhookNotifier(self.config['webhook'])
        
        return notifiers
    
    def send_alert(self, 
                   title: str,
                   message: str,
                   severity: AlertSeverity = AlertSeverity.INFO,
                   source: str = "unknown",
                   tags: List[str] = None,
                   metadata: Dict[str, Any] = None,
                   channels: List[AlertChannel] = None) -> str:
        """Send an alert through configured channels"""
        
        # Create alert object
        alert = Alert(
            id=f"{int(datetime.now().timestamp())}_{hash(title) % 10000}",
            timestamp=datetime.now(),
            severity=severity,
            title=title,
            message=message,
            source=source,
            tags=tags or [],
            metadata=metadata or {},
            channels=channels or [AlertChannel.EMAIL, AlertChannel.SLACK]
        )
        
        # Check throttling
        if self.config.get('throttling', {}).get('enabled', True):
            if not self.throttler.should_send_alert(alert):
                self._log_alert(alert, sent=False, reason="throttled")
                return alert.id
        
        # Send through configured channels
        results = {}
        for channel in alert.channels:
            if channel in self.notifiers:
                try:
                    success = self.notifiers[channel].send_alert(alert)
                    results[channel.value] = success
                except Exception as e:
                    results[channel.value] = False
                    print(f"Failed to send alert via {channel.value}: {e}")
        
        # Log alert
        self._log_alert(alert, sent=any(results.values()), results=results)
        
        return alert.id
    
    def _log_alert(self, alert: Alert, sent: bool, reason: str = None, results: Dict = None):
        """Log alert to file"""
        try:
            log_entry = {
                'alert_id': alert.id,
                'timestamp': alert.timestamp.isoformat(),
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'source': alert.source,
                'sent': sent,
                'reason': reason,
                'results': results or {}
            }
            
            # Append to log file
            with open(self.alert_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            print(f"Failed to log alert: {e}")
    
    def get_alert_summary(self, hours: int = 24) -> Dict:
        """Get summary of recent alerts"""
        try:
            if not self.alert_log.exists():
                return {'total': 0, 'by_severity': {}, 'by_source': {}}
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            summary = {
                'total': 0,
                'by_severity': {},
                'by_source': {},
                'throttled': self.throttler.get_throttled_summary()
            }
            
            with open(self.alert_log, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        
                        if entry_time >= cutoff_time:
                            summary['total'] += 1
                            
                            severity = entry['severity']
                            source = entry['source']
                            
                            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
                            summary['by_source'][source] = summary['by_source'].get(source, 0) + 1
                    
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            return summary
            
        except Exception as e:
            print(f"Failed to get alert summary: {e}")
            return {'error': str(e)}

# Convenience functions for common alerts
def send_trading_alert(title: str, message: str, severity: AlertSeverity = AlertSeverity.INFO, **kwargs):
    """Send trading-related alert"""
    manager = AlertManager()
    return manager.send_alert(
        title=title,
        message=message,
        severity=severity,
        source="trading_bot",
        tags=["trading"],
        **kwargs
    )

def send_system_alert(title: str, message: str, severity: AlertSeverity = AlertSeverity.WARNING, **kwargs):
    """Send system-related alert"""
    manager = AlertManager()
    return manager.send_alert(
        title=title,
        message=message,
        severity=severity,
        source="system_monitor",
        tags=["system"],
        **kwargs
    )

def send_security_alert(title: str, message: str, severity: AlertSeverity = AlertSeverity.CRITICAL, **kwargs):
    """Send security-related alert"""
    manager = AlertManager()
    return manager.send_alert(
        title=title,
        message=message,
        severity=severity,
        source="security_monitor",
        tags=["security"],
        **kwargs
    )

if __name__ == '__main__':
    # Test alert system
    manager = AlertManager()
    
    # Send test alert
    alert_id = manager.send_alert(
        title="Test Alert",
        message="This is a test alert from the AI Trading Sentinel alert system.",
        severity=AlertSeverity.INFO,
        source="test",
        metadata={
            "test_parameter": "test_value",
            "system_status": "operational"
        }
    )
    
    print(f"Test alert sent with ID: {alert_id}")
    
    # Print summary
    summary = manager.get_alert_summary()
    print(f"Alert summary: {json.dumps(summary, indent=2)}")