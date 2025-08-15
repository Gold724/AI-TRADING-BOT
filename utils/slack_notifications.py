import os
from datetime import datetime

import requests


def send_slack_prophetic(
    message_type,
    symbol=None,
    entry=None,
    direction=None,
    status=None,
    profit=None,
    session_id=None,
):
    """
    Send a prophetic-style notification to Slack using the configured webhook URL.

    Args:
        message_type (str): Type of message ('profit', 'fail', 'login_success', 'login_fail', or custom)
        symbol (str, optional): Trading symbol (e.g., 'EURUSD')
        entry (float, optional): Entry price for the trade
        direction (str, optional): Trade direction ('buy' or 'sell')
        status (str, optional): Status message for failed trades
        profit (float, optional): Profit amount for successful trades
        session_id (str, optional): Unique session identifier

    Returns:
        bool: True if the notification was sent successfully, False otherwise
    """
    webhook = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook:
        print("Error: SLACK_WEBHOOK_URL environment variable not set")
        return False

    # Time of alert
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if message_type == "profit":
        message = f"""🌄 *PROFIT ALERT – DREAM IN MOTION* 🌕  
📈 *{symbol}* just moved like prophecy foretold.  
💥 *Direction:* `{direction.upper()}`  
💰 *Entry:* `{entry}` → *Profit:* `+${profit}`  
🧠 Session: `{session_id}`  
⏰ Time: {timestamp}  
_The Sentinel sees what others don't. Another seed becomes a tree._"""

    elif message_type == "fail":
        message = f"""🕳️ *TRADE FAILED – BUT NOT THE MISSION* 🕯️  
📉 Attempted trade on *{symbol}* `{direction}` at `{entry}` did not execute.  
🔁 Status: `{status}`  
🧠 Session: `{session_id}`  
⏰ Time: {timestamp}  
_Even the moon retreats before rising. Every glitch prepares the next miracle._"""

    elif message_type == "login_success":
        message = f"""🔓 *LOGIN SUCCESSFUL – SENTINEL IS AWAKE* 🌐  
🎯 Logged into Bulenox (ProjectX) under Session `{session_id}`  
⏰ Time: {timestamp}  
_The gates are open. The path to wealth has no traffic at 2AM._"""

    elif message_type == "login_fail":
        message = f"""🚪 *LOGIN FAILED – GATE TEMPORARILY CLOSED*  
❌ Could not access Bulenox platform for Session `{session_id}`  
⏰ Time: {timestamp}  
_The master re-attempts until the code bows. Patience is a weapon._"""

    else:
        message = f"""🔔 *AI Sentinel Alert*  
🧠 `{message_type}`  
⏰ Time: {timestamp}"""

    try:
        response = requests.post(webhook, json={"text": message})
        response.raise_for_status()
        print(f"Slack notification sent: {message_type}")
        return True
    except Exception as e:
        print("Slack alert failed:", e)
        return False
