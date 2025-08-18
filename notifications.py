#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradeBot Sentinel - Enhanced Notification System
Telegram & Email notifications for trade alerts and system errors
"""

import os
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional, Any
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.config = {
            # Telegram settings
            'telegram_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'telegram_enabled': os.getenv('TELEGRAM_ENABLED', 'False').lower() == 'true',
            
            # Email settings
            'email_enabled': os.getenv('EMAIL_ENABLED', 'False').lower() == 'true',
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'email_user': os.getenv('EMAIL_USERNAME', ''),
            'email_password': os.getenv('EMAIL_PASSWORD', ''),
            'email_from': os.getenv('EMAIL_FROM', ''),
            'email_to': os.getenv('EMAIL_TO', ''),
            
            # Notification preferences
            'notify_trades': os.getenv('NOTIFY_TRADE_ALERTS', 'True').lower() == 'true',
            'notify_errors': os.getenv('NOTIFY_ERROR_ALERTS', 'True').lower() == 'true',
            'notify_limits': os.getenv('NOTIFY_RISK_ALERTS', 'True').lower() == 'true',
            'notify_system': os.getenv('NOTIFY_SYSTEM_STATUS', 'True').lower() == 'true',
        }
        
    async def send_trade_alert(self, trade_data: Dict[str, Any]):
        """Send trade detection alert"""
        if not self.config['notify_trades']:
            return
            
        symbol = trade_data.get('symbol', 'Unknown')
        amount = trade_data.get('amount', 'Unknown')
        price = trade_data.get('price', 'Unknown')
        side = trade_data.get('side', 'Unknown')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        title = "🎯 TRADE DETECTED"
        message = f"""
{title}

📊 Symbol: {symbol}
💰 Amount: {amount}
💵 Price: {price}
📈 Side: {side}
⏰ Time: {timestamp}

🔗 Platform: Bulenox
🤖 TradeBot Sentinel Pro
        """.strip()
        
        await self._send_notification(title, message, 'trade')
        
    async def send_error_alert(self, error_type: str, error_message: str, screenshot_path: Optional[str] = None):
        """Send error alert"""
        if not self.config['notify_errors']:
            return
            
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        title = "❌ TRADEBOT ERROR"
        message = f"""
{title}

🚨 Type: {error_type}
📝 Message: {error_message}
⏰ Time: {timestamp}

🤖 TradeBot Sentinel Pro
        """.strip()
        
        if screenshot_path:
            message += f"\n📸 Screenshot: {screenshot_path}"
            
        await self._send_notification(title, message, 'error')
        
    async def send_risk_limit_alert(self, limit_type: str, current_value: float, limit_value: float):
        """Send risk management limit alert"""
        if not self.config['notify_limits']:
            return
            
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        title = "⚠️ RISK LIMIT REACHED"
        message = f"""
{title}

🛡️ Limit Type: {limit_type}
📊 Current: {current_value}
🚫 Limit: {limit_value}
⏰ Time: {timestamp}

🔒 Trading suspended for safety
🤖 TradeBot Sentinel Pro
        """.strip()
        
        await self._send_notification(title, message, 'risk')
        
    async def send_system_status(self, status: str, details: Dict[str, Any]):
        """Send system status update"""
        if not self.config['notify_system']:
            return
            
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        title = f"🤖 SYSTEM STATUS: {status.upper()}"
        message = f"""
{title}

⏰ Time: {timestamp}
📊 Daily Trades: {details.get('daily_trades', 0)}
💰 Daily PnL: {details.get('daily_pnl', 'N/A')}
🔄 Uptime: {details.get('uptime', 'N/A')}
🌐 Status: {status}

🤖 TradeBot Sentinel Pro
        """.strip()
        
        await self._send_notification(title, message, 'system')
        
    async def _send_notification(self, title: str, message: str, notification_type: str):
        """Send notification via all enabled channels"""
        try:
            # Send Telegram notification
            if self.config['telegram_enabled']:
                await self._send_telegram(message)
                
            # Send Email notification
            if self.config['email_enabled']:
                await self._send_email(title, message)
                
            logger.info(f"✅ Notification sent: {notification_type}")
            
        except Exception as e:
            logger.error(f"❌ Notification failed: {e}")
            
    async def _send_telegram(self, message: str):
        """Send Telegram message"""
        if not self.config['telegram_token'] or not self.config['telegram_chat_id']:
            return
            
        url = f"https://api.telegram.org/bot{self.config['telegram_token']}/sendMessage"
        data = {
            'chat_id': self.config['telegram_chat_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        
    async def _send_email(self, subject: str, message: str):
        """Send email notification"""
        if not all([self.config['email_user'], self.config['email_password'], self.config['email_to'], self.config['email_from']]):
            return
            
        msg = MIMEMultipart()
        msg['From'] = self.config['email_from']
        msg['To'] = self.config['email_to']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
        server.starttls()
        server.login(self.config['email_user'], self.config['email_password'])
        
        text = msg.as_string()
        server.sendmail(self.config['email_from'], self.config['email_to'], text)
        server.quit()
        
    def test_notifications(self):
        """Test all notification channels"""
        import asyncio
        
        async def run_tests():
            print("🧪 Testing notification channels...")
            
            # Test trade alert
            test_trade = {
                'symbol': 'BTCUSDT',
                'amount': '0.001',
                'price': '45000',
                'side': 'BUY'
            }
            await self.send_trade_alert(test_trade)
            
            # Test error alert
            await self.send_error_alert('Login Failed', 'Unable to locate username field')
            
            # Test risk limit alert
            await self.send_risk_limit_alert('Daily Loss Limit', 500.0, 1000.0)
            
            # Test system status
            status_details = {
                'daily_trades': 5,
                'daily_pnl': '+$250.50',
                'uptime': '2h 30m'
            }
            await self.send_system_status('ACTIVE', status_details)
            
            print("✅ Notification tests completed")
            
        asyncio.run(run_tests())

if __name__ == "__main__":
    # Test notifications
    notifier = NotificationManager()
    notifier.test_notifications()