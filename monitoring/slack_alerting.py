#!/usr/bin/env python3
"""
AI Trading Sentinel - Slack Alerting System
Real-time notifications for critical trading events and system alerts
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from threading import Thread, Event
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class Alert:
    """Alert data structure"""
    title: str
    message: str
    severity: AlertSeverity
    service: str
    timestamp: datetime
    details: Dict[str, Any] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    runbook_url: Optional[str] = None

class SlackAlerting:
    """Slack alerting system for AI Trading Sentinel"""
    
    def __init__(self, webhook_url: str, channel: str = "#trading-alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.alert_queue = queue.Queue()
        self.stop_event = Event()
        self.worker_thread = None
        self.rate_limit_cache = {}
        self.last_alert_times = {}
        
        # Rate limiting configuration
        self.rate_limits = {
            AlertSeverity.EMERGENCY: timedelta(seconds=0),  # No rate limiting
            AlertSeverity.CRITICAL: timedelta(minutes=1),   # Max 1 per minute
            AlertSeverity.WARNING: timedelta(minutes=5),    # Max 1 per 5 minutes
            AlertSeverity.INFO: timedelta(minutes=15)       # Max 1 per 15 minutes
        }
        
        # Emoji mapping for different alert types
        self.severity_emojis = {
            AlertSeverity.INFO: ":information_source:",
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.CRITICAL: ":rotating_light:",
            AlertSeverity.EMERGENCY: ":fire:"
        }
        
        # Color mapping for Slack attachments
        self.severity_colors = {
            AlertSeverity.INFO: "#36a64f",      # Green
            AlertSeverity.WARNING: "#ffcc00",   # Yellow
            AlertSeverity.CRITICAL: "#ff6b6b", # Red
            AlertSeverity.EMERGENCY: "#8b0000"  # Dark red
        }
    
    def start(self):
        """Start the alerting worker thread"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_event.clear()
            self.worker_thread = Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            logger.info("Slack alerting system started")
    
    def stop(self):
        """Stop the alerting worker thread"""
        self.stop_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        logger.info("Slack alerting system stopped")
    
    def _worker(self):
        """Worker thread to process alert queue"""
        while not self.stop_event.is_set():
            try:
                # Get alert from queue with timeout
                alert = self.alert_queue.get(timeout=1)
                
                # Check rate limiting
                if self._should_send_alert(alert):
                    self._send_slack_message(alert)
                    self._update_rate_limit_cache(alert)
                else:
                    logger.debug(f"Alert rate limited: {alert.title}")
                
                self.alert_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing alert: {e}")
    
    def _should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent based on rate limiting"""
        alert_key = f"{alert.service}:{alert.title}"
        
        # Emergency alerts are never rate limited
        if alert.severity == AlertSeverity.EMERGENCY:
            return True
        
        # Check last alert time
        last_time = self.last_alert_times.get(alert_key)
        if last_time is None:
            return True
        
        time_since_last = alert.timestamp - last_time
        rate_limit = self.rate_limits.get(alert.severity, timedelta(minutes=5))
        
        return time_since_last >= rate_limit
    
    def _update_rate_limit_cache(self, alert: Alert):
        """Update rate limiting cache"""
        alert_key = f"{alert.service}:{alert.title}"
        self.last_alert_times[alert_key] = alert.timestamp
    
    def send_alert(self, alert: Alert):
        """Queue an alert for sending"""
        try:
            self.alert_queue.put(alert, timeout=1)
        except queue.Full:
            logger.error("Alert queue is full, dropping alert")
    
    def _send_slack_message(self, alert: Alert):
        """Send alert message to Slack"""
        try:
            payload = self._build_slack_payload(alert)
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Alert sent successfully: {alert.title}")
            else:
                logger.error(f"Failed to send alert: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
    
    def _build_slack_payload(self, alert: Alert) -> Dict:
        """Build Slack message payload"""
        emoji = self.severity_emojis.get(alert.severity, ":exclamation:")
        color = self.severity_colors.get(alert.severity, "#cccccc")
        
        # Build main message
        text = f"{emoji} *{alert.title}*"
        
        # Build attachment with details
        attachment = {
            "color": color,
            "fields": [
                {
                    "title": "Service",
                    "value": alert.service,
                    "short": True
                },
                {
                    "title": "Severity",
                    "value": alert.severity.value.upper(),
                    "short": True
                },
                {
                    "title": "Time",
                    "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "short": True
                }
            ],
            "text": alert.message,
            "footer": "AI Trading Sentinel",
            "ts": int(alert.timestamp.timestamp())
        }
        
        # Add metric information if available
        if alert.metric_value is not None:
            attachment["fields"].append({
                "title": "Current Value",
                "value": str(alert.metric_value),
                "short": True
            })
        
        if alert.threshold is not None:
            attachment["fields"].append({
                "title": "Threshold",
                "value": str(alert.threshold),
                "short": True
            })
        
        # Add runbook link if available
        if alert.runbook_url:
            attachment["actions"] = [
                {
                    "type": "button",
                    "text": "View Runbook",
                    "url": alert.runbook_url,
                    "style": "primary"
                }
            ]
        
        # Add additional details
        if alert.details:
            for key, value in alert.details.items():
                attachment["fields"].append({
                    "title": key.replace('_', ' ').title(),
                    "value": str(value),
                    "short": True
                })
        
        payload = {
            "channel": self.channel,
            "text": text,
            "attachments": [attachment],
            "username": "Trading Sentinel Bot",
            "icon_emoji": ":robot_face:"
        }
        
        return payload
    
    def send_trading_alert(self, 
                          alert_type: str, 
                          message: str, 
                          severity: AlertSeverity = AlertSeverity.INFO,
                          **kwargs):
        """Send trading-specific alert"""
        alert = Alert(
            title=f"Trading Alert: {alert_type}",
            message=message,
            severity=severity,
            service="trading-bot",
            timestamp=datetime.utcnow(),
            details=kwargs
        )
        self.send_alert(alert)
    
    def send_system_alert(self, 
                         alert_type: str, 
                         message: str, 
                         severity: AlertSeverity = AlertSeverity.WARNING,
                         **kwargs):
        """Send system-specific alert"""
        alert = Alert(
            title=f"System Alert: {alert_type}",
            message=message,
            severity=severity,
            service="system",
            timestamp=datetime.utcnow(),
            details=kwargs
        )
        self.send_alert(alert)
    
    def send_api_alert(self, 
                      alert_type: str, 
                      message: str, 
                      severity: AlertSeverity = AlertSeverity.WARNING,
                      **kwargs):
        """Send API-specific alert"""
        alert = Alert(
            title=f"API Alert: {alert_type}",
            message=message,
            severity=severity,
            service="api",
            timestamp=datetime.utcnow(),
            details=kwargs
        )
        self.send_alert(alert)
    
    def send_security_alert(self, 
                           alert_type: str, 
                           message: str, 
                           severity: AlertSeverity = AlertSeverity.CRITICAL,
                           **kwargs):
        """Send security-specific alert"""
        alert = Alert(
            title=f"Security Alert: {alert_type}",
            message=message,
            severity=severity,
            service="security",
            timestamp=datetime.utcnow(),
            details=kwargs
        )
        self.send_alert(alert)
    
    def send_performance_summary(self, 
                               daily_profit: float, 
                               total_trades: int, 
                               win_rate: float,
                               max_drawdown: float):
        """Send daily performance summary"""
        
        # Determine severity based on performance
        if daily_profit < -200:
            severity = AlertSeverity.CRITICAL
        elif daily_profit < 0:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO
        
        message = f"Daily trading summary: ${daily_profit:.2f} P&L, {total_trades} trades, {win_rate:.1f}% win rate"
        
        alert = Alert(
            title="Daily Performance Summary",
            message=message,
            severity=severity,
            service="trading-bot",
            timestamp=datetime.utcnow(),
            details={
                "daily_profit_usd": daily_profit,
                "total_trades": total_trades,
                "win_rate_percent": win_rate,
                "max_drawdown_percent": max_drawdown
            }
        )
        
        self.send_alert(alert)
    
    def send_deployment_notification(self, 
                                   deployment_status: str, 
                                   version: str = None,
                                   **kwargs):
        """Send deployment notification"""
        
        if deployment_status.lower() == "success":
            severity = AlertSeverity.INFO
            emoji = ":white_check_mark:"
        else:
            severity = AlertSeverity.WARNING
            emoji = ":x:"
        
        title = f"Deployment {deployment_status.title()}"
        message = f"AI Trading Sentinel deployment {deployment_status.lower()}"
        
        if version:
            message += f" (version: {version})"
        
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            service="deployment",
            timestamp=datetime.utcnow(),
            details=kwargs
        )
        
        self.send_alert(alert)

class PrometheusAlertReceiver:
    """Receive and process Prometheus alerts"""
    
    def __init__(self, slack_alerting: SlackAlerting):
        self.slack = slack_alerting
    
    def process_webhook(self, webhook_data: Dict) -> List[Alert]:
        """Process Prometheus webhook data"""
        alerts = []
        
        for alert_data in webhook_data.get('alerts', []):
            try:
                alert = self._parse_prometheus_alert(alert_data)
                if alert:
                    alerts.append(alert)
                    self.slack.send_alert(alert)
            except Exception as e:
                logger.error(f"Error parsing Prometheus alert: {e}")
        
        return alerts
    
    def _parse_prometheus_alert(self, alert_data: Dict) -> Optional[Alert]:
        """Parse individual Prometheus alert"""
        labels = alert_data.get('labels', {})
        annotations = alert_data.get('annotations', {})
        
        # Map Prometheus severity to our enum
        severity_map = {
            'info': AlertSeverity.INFO,
            'warning': AlertSeverity.WARNING,
            'critical': AlertSeverity.CRITICAL,
            'emergency': AlertSeverity.EMERGENCY
        }
        
        severity = severity_map.get(
            labels.get('severity', 'warning').lower(),
            AlertSeverity.WARNING
        )
        
        alert = Alert(
            title=labels.get('alertname', 'Unknown Alert'),
            message=annotations.get('description', annotations.get('summary', 'No description')),
            severity=severity,
            service=labels.get('service', labels.get('job', 'unknown')),
            timestamp=datetime.utcnow(),
            details={
                'instance': labels.get('instance'),
                'job': labels.get('job'),
                'prometheus_labels': labels
            },
            runbook_url=annotations.get('runbook_url')
        )
        
        return alert

def create_slack_alerting_from_env() -> SlackAlerting:
    """Create SlackAlerting instance from environment variables"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL environment variable is required")
    
    channel = os.getenv('SLACK_ALERT_CHANNEL', '#trading-alerts')
    
    slack_alerting = SlackAlerting(webhook_url, channel)
    slack_alerting.start()
    
    return slack_alerting

def main():
    """Main function for testing"""
    # Create alerting system
    slack = create_slack_alerting_from_env()
    
    # Send test alerts
    slack.send_trading_alert(
        "High Profit Trade",
        "Executed profitable scalping trade with 2.5% return",
        AlertSeverity.INFO,
        profit_usd=125.50,
        symbol="EUR/USD",
        entry_price=1.0850,
        exit_price=1.0875
    )
    
    slack.send_system_alert(
        "High CPU Usage",
        "CPU usage has exceeded 85% for the last 5 minutes",
        AlertSeverity.WARNING,
        cpu_usage_percent=87.3,
        instance="trading-server-01"
    )
    
    slack.send_security_alert(
        "Multiple Failed Logins",
        "Detected 15 failed login attempts from suspicious IP",
        AlertSeverity.CRITICAL,
        failed_attempts=15,
        source_ip="192.168.1.100",
        time_window="5 minutes"
    )
    
    # Wait for alerts to be sent
    time.sleep(5)
    
    # Stop alerting system
    slack.stop()

if __name__ == "__main__":
    main()