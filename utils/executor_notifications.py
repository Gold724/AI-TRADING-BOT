import os
from datetime import datetime

# Import the Slack notification function
try:
    from utils.slack_notifications import send_slack_prophetic
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False


def notify_login_success(session_id):
    """
    Send a notification for successful login.
    
    Args:
        session_id (str): The session identifier
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    if not SLACK_AVAILABLE:
        return False
        
    # Check if Slack notifications are enabled
    if not os.getenv("SLACK_WEBHOOK_URL"):
        return False
        
    return send_slack_prophetic(
        message_type="login_success",
        session_id=session_id
    )


def notify_login_failure(session_id):
    """
    Send a notification for failed login.
    
    Args:
        session_id (str): The session identifier
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    if not SLACK_AVAILABLE:
        return False
        
    # Check if Slack notifications are enabled
    if not os.getenv("SLACK_WEBHOOK_URL"):
        return False
        
    return send_slack_prophetic(
        message_type="login_fail",
        session_id=session_id
    )


def notify_trade_success(symbol, entry, direction, profit, session_id):
    """
    Send a notification for a successful trade with profit.
    
    Args:
        symbol (str): The trading symbol (e.g., 'EURUSD')
        entry (float): The entry price
        direction (str): The trade direction ('buy' or 'sell')
        profit (float): The profit amount
        session_id (str): The session identifier
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    if not SLACK_AVAILABLE:
        return False
        
    # Check if Slack notifications are enabled
    if not os.getenv("SLACK_WEBHOOK_URL"):
        return False
        
    return send_slack_prophetic(
        message_type="profit",
        symbol=symbol,
        entry=entry,
        direction=direction,
        profit=profit,
        session_id=session_id
    )


def notify_trade_failure(symbol, entry, direction, status, session_id):
    """
    Send a notification for a failed trade.
    
    Args:
        symbol (str): The trading symbol (e.g., 'EURUSD')
        entry (float): The entry price
        direction (str): The trade direction ('buy' or 'sell')
        status (str): The failure status or reason
        session_id (str): The session identifier
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    if not SLACK_AVAILABLE:
        return False
        
    # Check if Slack notifications are enabled
    if not os.getenv("SLACK_WEBHOOK_URL"):
        return False
        
    return send_slack_prophetic(
        message_type="fail",
        symbol=symbol,
        entry=entry,
        direction=direction,
        status=status,
        session_id=session_id
    )


def notify_custom(message, session_id=None):
    """
    Send a custom notification message.
    
    Args:
        message (str): The custom message to send
        session_id (str, optional): The session identifier
        
    Returns:
        bool: True if notification was sent, False otherwise
    """
    if not SLACK_AVAILABLE:
        return False
        
    # Check if Slack notifications are enabled
    if not os.getenv("SLACK_WEBHOOK_URL"):
        return False
        
    # If no session ID is provided, generate one
    if not session_id:
        session_id = f"SYSTEM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
    return send_slack_prophetic(
        message_type=message,
        session_id=session_id
    )