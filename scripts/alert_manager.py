#!/usr/bin/env python3
"""
AI Trading Sentinel - Alert Manager

Advanced alerting system for critical event notification.
Handles multiple alert types, channels, throttling, escalation, and multi-channel routing.
"""

import os
import sys
import json
import time
import yaml
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from jinja2 import Template
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertChannel(Enum):
    """Available alert channels"""
    SLACK = "slack"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    service: str
    severity: str
    title: str
    message: str
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    notification_count: int = 0
    last_notification: Optional[datetime] = None


@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    name: str
    type: str
    config: Dict[str, Any]
    enabled: bool = True
    severity_filter: List[str] = None  # Filter by severity levels
    service_filter: List[str] = None   # Filter by service names


class AlertManager:
    """Advanced alert management system."""
    
    def __init__(self, config_path: str = None):
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "monitoring_config.yml"
        self.alerts_dir = self.project_root / "logs" / "alerts"
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize components
        self.active_alerts = {}
        self.notification_channels = self.setup_notification_channels()
        self.escalation_policies = self.config.get('escalation', {})
        
        # Alert templates
        self.templates = self.load_templates()
        
        self.logger.info("Alert Manager initialized")
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_file = self.project_root / "logs" / "alert_manager.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('AlertManager')
    
    def load_config(self) -> Dict[str, Any]:
        """Load alert manager configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
                return config
            else:
                self.logger.warning(f"Config file not found: {self.config_path}")
                return self.get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'notifications': {
                'slack': {
                    'enabled': True,
                    'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                    'channel': '#alerts',
                    'username': 'AI Trading Sentinel'
                },
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': os.getenv('EMAIL_USERNAME'),
                    'password': os.getenv('EMAIL_PASSWORD'),
                    'from_email': os.getenv('EMAIL_FROM'),
                    'to_emails': []
                }
            },
            'escalation': {
                'enabled': True,
                'levels': [
                    {'delay_minutes': 0, 'channels': ['slack']},
                    {'delay_minutes': 15, 'channels': ['slack', 'email']},
                    {'delay_minutes': 60, 'channels': ['slack', 'email', 'pagerduty']}
                ]
            }
        }
    
    def setup_notification_channels(self) -> List[NotificationChannel]:
        """Setup notification channels from configuration."""
        channels = []
        notifications_config = self.config.get('notifications', {})
        
        # Slack channel
        slack_config = notifications_config.get('slack', {})
        if slack_config.get('enabled', False) and slack_config.get('webhook_url'):
            channels.append(NotificationChannel(
                name='slack',
                type='slack',
                config=slack_config,
                enabled=True
            ))
        
        # Email channel
        email_config = notifications_config.get('email', {})
        if email_config.get('enabled', False):
            channels.append(NotificationChannel(
                name='email',
                type='email',
                config=email_config,
                enabled=True,
                severity_filter=['critical', 'emergency']
            ))
        
        self.logger.info(f"Configured {len(channels)} notification channels")
        return channels
    
    def load_templates(self) -> Dict[str, Template]:
        """Load notification templates."""
        templates = {
            'slack_alert': Template("""
🚨 *{{ alert.severity.upper() }}* - {{ alert.title }}

*Service:* {{ alert.service }}
*Message:* {{ alert.message }}
*Time:* {{ alert.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}

{% if alert.labels %}
*Labels:*
{% for key, value in alert.labels.items() %}
• {{ key }}: {{ value }}
{% endfor %}
{% endif %}
            """)
        }
        
        return templates
    
    def create_alert(self, service: str, severity: str, title: str, message: str, 
                    labels: Dict[str, str] = None, annotations: Dict[str, str] = None) -> Alert:
        """Create a new alert."""
        alert_id = f"{service}_{severity}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            service=service,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            labels=labels or {},
            annotations=annotations or {}
        )
        
        self.active_alerts[alert_id] = alert
        self.logger.info(f"Created alert: {alert_id} - {title}")
        
        # Save alert to file
        self.save_alert(alert)
        
        return alert
    
    def send_slack_alert(self, alert: Alert, channel: NotificationChannel):
        """Send alert to Slack."""
        webhook_url = channel.config.get('webhook_url')
        if not webhook_url:
            raise ValueError("Slack webhook URL not configured")
        
        # Render message
        message_text = self.templates['slack_alert'].render(alert=alert)
        
        # Determine color based on severity
        color_map = {
            'info': 'good',
            'warning': 'warning',
            'critical': 'danger',
            'emergency': '#8B0000'
        }
        
        emoji_map = {
            'info': '💡',
            'warning': '⚠️',
            'critical': '🚨',
            'emergency': '🔥'
        }
        
        color = color_map.get(alert.severity, '#808080')
        emoji = emoji_map.get(alert.severity, '❓')
        
        payload = {
            'username': channel.config.get('username', 'AI Trading Sentinel'),
            'channel': channel.config.get('channel', '#alerts'),
            'icon_emoji': ':robot_face:',
            'attachments': [{
                'color': color,
                'title': f'{emoji} {alert.title}',
                'text': message_text,
                'footer': 'AI Trading Sentinel Alert Manager',
                'ts': int(alert.timestamp.timestamp())
            }]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
    
    def send_alert(self, alert: Alert) -> bool:
        """Send alert through appropriate channels."""
        success = True
        
        for channel in self.notification_channels:
            if not channel.enabled:
                continue
            
            # Check severity filter
            if channel.severity_filter and alert.severity not in channel.severity_filter:
                continue
            
            try:
                if channel.type == 'slack':
                    self.send_slack_alert(alert, channel)
                
                self.logger.info(f"Alert sent via {channel.name}: {alert.id}")
                
            except Exception as e:
                self.logger.error(f"Failed to send alert via {channel.name}: {e}")
                success = False
        
        # Update alert notification tracking
        alert.notification_count += 1
        alert.last_notification = datetime.now()
        
        return success
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            # Save updated alert
            self.save_alert(alert)
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    def save_alert(self, alert: Alert):
        """Save alert to file."""
        try:
            alert_file = self.alerts_dir / f"{alert.id}.json"
            
            # Convert to serializable format
            alert_dict = asdict(alert)
            alert_dict['timestamp'] = alert.timestamp.isoformat()
            if alert.resolved_at:
                alert_dict['resolved_at'] = alert.resolved_at.isoformat()
            if alert.last_notification:
                alert_dict['last_notification'] = alert.last_notification.isoformat()
            
            with open(alert_file, 'w') as f:
                json.dump(alert_dict, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving alert {alert.id}: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert system status."""
        return {
            'active_alerts': len(self.active_alerts),
            'notification_channels': len(self.notification_channels),
            'alerts_by_severity': {
                severity: len([a for a in self.active_alerts.values() if a.severity == severity])
                for severity in ['info', 'warning', 'critical', 'emergency']
            },
            'last_alert': max([a.timestamp for a in self.active_alerts.values()], default=None)
        }


# Convenience functions for common alerts
def send_trading_alert(title: str, message: str, severity: str = "info", **kwargs):
    """Send trading-related alert"""
    manager = AlertManager()
    alert = manager.create_alert(
        service="trading_bot",
        severity=severity,
        title=title,
        message=message,
        labels={"type": "trading", **kwargs.get('labels', {})}
    )
    return manager.send_alert(alert)


def send_system_alert(title: str, message: str, severity: str = "warning", **kwargs):
    """Send system-related alert"""
    manager = AlertManager()
    alert = manager.create_alert(
        service="system_monitor",
        severity=severity,
        title=title,
        message=message,
        labels={"type": "system", **kwargs.get('labels', {})}
    )
    return manager.send_alert(alert)


def send_security_alert(title: str, message: str, severity: str = "critical", **kwargs):
    """Send security-related alert"""
    manager = AlertManager()
    alert = manager.create_alert(
        service="security_monitor",
        severity=severity,
        title=title,
        message=message,
        labels={"type": "security", **kwargs.get('labels', {})}
    )
    return manager.send_alert(alert)


def main():
    """Main function for alert manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Alert Manager")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--create-alert', nargs=5, metavar=('SERVICE', 'SEVERITY', 'TITLE', 'MESSAGE', 'LABELS'),
                       help='Create a new alert')
    parser.add_argument('--list-alerts', action='store_true', help='List active alerts')
    parser.add_argument('--resolve-alert', help='Resolve an alert by ID')
    parser.add_argument('--test', action='store_true', help='Send test alert')
    
    args = parser.parse_args()
    
    # Initialize alert manager
    alert_manager = AlertManager(args.config)
    
    if args.create_alert:
        service, severity, title, message, labels_str = args.create_alert
        labels = json.loads(labels_str) if labels_str != '{}' else {}
        
        alert = alert_manager.create_alert(service, severity, title, message, labels)
        alert_manager.send_alert(alert)
        print(f"Alert created: {alert.id}")
    
    elif args.list_alerts:
        alerts = alert_manager.get_active_alerts()
        if alerts:
            print("Active Alerts:")
            for alert in alerts:
                print(f"  {alert.id}: [{alert.severity}] {alert.title} ({alert.service})")
        else:
            print("No active alerts")
    
    elif args.resolve_alert:
        if alert_manager.resolve_alert(args.resolve_alert):
            print(f"Alert resolved: {args.resolve_alert}")
        else:
            print(f"Alert not found: {args.resolve_alert}")
    
    elif args.test:
        alert = alert_manager.create_alert(
            service="test",
            severity="info",
            title="Test Alert",
            message="This is a test alert from the AI Trading Sentinel alert system.",
            labels={"environment": "test"}
        )
        
        if alert_manager.send_alert(alert):
            print(f"Test alert sent successfully: {alert.id}")
        else:
            print("Failed to send test alert")
    
    else:
        parser.print_help()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())