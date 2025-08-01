# slack_reporter.py

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('slack_reporter')

# Load environment variables
load_dotenv()

# Slack webhook URL
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

def update_heartbeat_status(status, session_active=True):
    """
    Update the heartbeat status file with current status and timestamp
    
    Args:
        status (str): The current status message
        session_active (bool): Flag indicating if a trading session is active
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        
        # Write to heartbeat status file
        with open(HEARTBEAT_STATUS_FILE, 'w') as f:
            f.write(f"{status}\n{timestamp}\n{json.dumps({'session_active': session_active})}")
            
        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")

def send_slack_notification(message, notification_type=None, session_id=None, **kwargs):
    """Send a notification to Slack
    
    Args:
        message (str): The message to send
        notification_type (str, optional): Type of notification (login_success, login_failed, trade_executed, etc.)
        session_id (str, optional): The session identifier
        **kwargs: Additional parameters for specific notification types
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook URL not configured. Skipping notification.")
        return False
        
    # Update heartbeat status with the notification message
    update_heartbeat_status(f"📢 Sending notification: {notification_type or 'custom'}")
        
    try:
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format message based on type
        formatted_message = _format_message(message, notification_type, session_id, timestamp, **kwargs)
        
        # Send to Slack
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": formatted_message})
        response.raise_for_status()
        
        logger.info(f"Slack notification sent: {notification_type or 'custom'}")
        update_heartbeat_status(f"✅ Notification sent: {notification_type or 'custom'}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        update_heartbeat_status(f"❌ Failed to send notification: {str(e)[:50]}...")
        return False

def _format_message(message, notification_type, session_id, timestamp, **kwargs):
    """Format the message based on its type"""
    # Default session ID if not provided
    session_id = session_id or "UNKNOWN"
    
    # Format based on notification type
    if notification_type == "login_success":
        return f"""🔓 *LOGIN SUCCESSFUL – SENTINEL IS AWAKE* 🌐  
🎯 Logged into Bulenox (ProjectX) under Session `{session_id}`  
⏰ Time: {timestamp}  
_The gates are open. The path to wealth has no traffic at 2AM._"""
        
    elif notification_type == "login_failed":
        return f"""🚪 *LOGIN FAILED – GATE TEMPORARILY CLOSED*  
❌ Could not access Bulenox platform for Session `{session_id}`  
⏰ Time: {timestamp}  
_The master re-attempts until the code bows. Patience is a weapon._"""
        
    elif notification_type == "trade_executed":
        symbol = kwargs.get("symbol", "UNKNOWN")
        direction = kwargs.get("direction", "UNKNOWN")
        entry = kwargs.get("entry", "MARKET")
        tp = kwargs.get("tp", "None")
        sl = kwargs.get("sl", "None")
        
        return f"""🚀 *TRADE EXECUTED – WEALTH IN MOTION* 📈  
💹 {symbol} {direction.upper()} @ {entry}  
🛡️ Stop Loss: {sl}  
🎯 Take Profit: {tp}  
🔑 Session: `{session_id}`  
⏰ Time: {timestamp}  
_The universe conspires in your favor when you act with precision._"""
        
    elif notification_type == "trade_failed":
        symbol = kwargs.get("symbol", "UNKNOWN")
        direction = kwargs.get("direction", "UNKNOWN")
        reason = kwargs.get("reason", "Unknown error")
        
        return f"""⚠️ *TRADE FAILED – TEMPORARY SETBACK* ⚠️  
❌ {symbol} {direction.upper()} could not be executed  
📝 Reason: {reason}  
🔑 Session: `{session_id}`  
⏰ Time: {timestamp}  
_Obstacles are detours in the right direction. We adapt and overcome._"""
        
    elif notification_type == "profit":
        symbol = kwargs.get("symbol", "UNKNOWN")
        direction = kwargs.get("direction", "UNKNOWN")
        profit = kwargs.get("profit", 0)
        
        return f"""💰 *PROFIT SECURED – MANIFESTATION COMPLETE* 💰  
✅ {symbol} {direction.upper()} closed with ${profit:.2f} profit  
🔑 Session: `{session_id}`  
⏰ Time: {timestamp}  
_What you seek is seeking you. The universe rewards decisive action._"""
        
    elif notification_type == "loss":
        symbol = kwargs.get("symbol", "UNKNOWN")
        direction = kwargs.get("direction", "UNKNOWN")
        loss = kwargs.get("loss", 0)
        
        return f"""📉 *STOP LOSS HIT – CAPITAL PRESERVED* 🛡️  
⚠️ {symbol} {direction.upper()} closed with ${loss:.2f} loss  
🔑 Session: `{session_id}`  
⏰ Time: {timestamp}  
_The wise trader knows when to step back. This is but one battle in the war of wealth._"""
        
    else:
        # For custom messages
        return f"""🔔 *AI SENTINEL ALERT* 🤖  
📝 {message}  
🔑 Session: `{session_id}`  
⏰ Time: {timestamp}"""

# For testing
if __name__ == "__main__":
    # Test sending a notification
    test_session_id = "TEST-123"
    
    # Test login success notification
    send_slack_notification(
        "Login successful",
        notification_type="login_success",
        session_id=test_session_id
    )
    
    # Test trade executed notification
    send_slack_notification(
        "Trade executed",
        notification_type="trade_executed",
        session_id=test_session_id,
        symbol="EURUSD",
        direction="buy",
        entry=1.0750,
        tp=1.0800,
        sl=1.0700
    )
    
    # Test heartbeat status update
    update_heartbeat_status("🧪 Testing heartbeat status updates from slack_reporter.py")