#!/usr/bin/env python
# Slack notification script for Trae AI Trading Sentinel

import argparse
import json
import sys
import requests
from datetime import datetime

def send_notification(webhook_url, message, status="info"):
    """
    Send a notification to Slack
    
    Args:
        webhook_url (str): Slack webhook URL
        message (str): Message to send
        status (str): Status of the message (info, success, error)
    """
    # Set color based on status
    color = {
        "success": "good",
        "error": "danger",
        "info": "#0000FF"
    }.get(status, "#0000FF")
    
    # Create payload
    payload = {
        "attachments": [
            {
                "fallback": message,
                "color": color,
                "text": message,
                "fields": [
                    {
                        "title": "Environment",
                        "value": "Production",
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "short": True
                    }
                ]
            }
        ]
    }
    
    # Send request
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        print(f"Slack notification sent: {message}")
        return True
    except Exception as e:
        print(f"Failed to send Slack notification: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Send notifications to Slack")
    parser.add_argument(
        "--webhook-url", 
        required=True, 
        help="Slack webhook URL"
    )
    parser.add_argument(
        "--message", 
        required=True, 
        help="Message to send"
    )
    parser.add_argument(
        "--status", 
        choices=["info", "success", "error"], 
        default="info",
        help="Status of the message"
    )
    
    args = parser.parse_args()
    success = send_notification(args.webhook_url, args.message, args.status)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()