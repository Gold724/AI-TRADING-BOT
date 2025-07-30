#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Webhook Example Script

This script demonstrates how to use the webhook infrastructure of the AI Trading Sentinel system.
It includes examples for both standard and stealth trade webhooks, as well as Slack notifications.

Usage:
    python webhook_example.py
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')


def send_standard_trade_webhook(account_id, symbol, side, entry, quantity, stop_loss=None, take_profit=None):
    """
    Send a standard trade webhook to execute a trade.
    
    Args:
        account_id (str): The broker account ID
        symbol (str): The trading symbol (e.g., 'EURUSD', 'XAUUSD')
        side (str): The trade direction ('buy' or 'sell')
        entry (float): The entry price
        quantity (float): The trade quantity
        stop_loss (float, optional): The stop loss price
        take_profit (float, optional): The take profit price
        
    Returns:
        dict: The response from the webhook endpoint
    """
    url = f"{API_BASE_URL}/api/webhook"
    headers = {"Content-Type": "application/json"}
    
    # Prepare the payload
    payload = {
        "account_id": account_id,
        "signal": {
            "symbol": symbol,
            "side": side,
            "entry": entry,
            "quantity": quantity
        }
    }
    
    # Add optional parameters if provided
    if stop_loss:
        payload["signal"]["stop_loss"] = stop_loss
    
    if take_profit:
        payload["signal"]["take_profit"] = take_profit
    
    # Send the webhook request
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending standard trade webhook: {e}")
        return None


def send_stealth_trade_webhook(broker, symbol, side, quantity, stop_loss=None, take_profit=None, stealth_level=2):
    """
    Send a stealth trade webhook to execute a trade with human-like behavior.
    
    Args:
        broker (str): The broker name (e.g., 'bulenox', 'exness')
        symbol (str): The trading symbol (e.g., 'EURUSD', 'XAUUSD')
        side (str): The trade direction ('buy' or 'sell')
        quantity (float): The trade quantity
        stop_loss (float, optional): The stop loss price
        take_profit (float, optional): The take profit price
        stealth_level (int, optional): The stealth level (1-3, default: 2)
        
    Returns:
        dict: The response from the webhook endpoint
    """
    url = f"{API_BASE_URL}/api/trade/stealth"
    headers = {"Content-Type": "application/json"}
    
    # Prepare the payload
    payload = {
        "broker": broker,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "stealth_level": stealth_level
    }
    
    # Add optional parameters if provided
    if stop_loss:
        payload["stopLoss"] = stop_loss
    
    if take_profit:
        payload["takeProfit"] = take_profit
    
    # Send the webhook request
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending stealth trade webhook: {e}")
        return None


def send_slack_notification(message, emoji=":chart_with_upwards_trend:", channel="#trading"):
    """
    Send a notification to Slack.
    
    Args:
        message (str): The message to send
        emoji (str, optional): The emoji to use (default: ":chart_with_upwards_trend:")
        channel (str, optional): The Slack channel (default: "#trading")
        
    Returns:
        bool: True if the notification was sent successfully, False otherwise
    """
    if not SLACK_WEBHOOK_URL:
        print("Slack webhook URL not configured. Skipping notification.")
        return False
    
    payload = {
        "channel": channel,
        "username": "Trading Sentinel",
        "text": message,
        "icon_emoji": emoji
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for HTTP errors
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending Slack notification: {e}")
        return False


def main():
    """
    Main function to demonstrate webhook usage.
    """
    print("AI Trading Sentinel - Webhook Example")
    print("====================================\n")
    
    # Example 1: Standard Trade Webhook
    print("Example 1: Sending a standard trade webhook...")
    standard_response = send_standard_trade_webhook(
        account_id="BX64883",
        symbol="EURUSD",
        side="buy",
        entry=1.1000,
        quantity=0.01,
        stop_loss=1.0950,
        take_profit=1.1050
    )
    
    if standard_response:
        print(f"Standard trade webhook response: {json.dumps(standard_response, indent=2)}\n")
        # Send a Slack notification for the standard trade
        send_slack_notification(
            message="🚀 Standard trade executed: BUY EURUSD @ 1.1000",
            emoji=":chart_with_upwards_trend:"
        )
    
    # Wait a moment before sending the next webhook
    time.sleep(2)
    
    # Example 2: Stealth Trade Webhook
    print("Example 2: Sending a stealth trade webhook...")
    stealth_response = send_stealth_trade_webhook(
        broker="bulenox",
        symbol="XAUUSD",
        side="buy",
        quantity=0.01,
        stop_loss=2350,
        take_profit=2400,
        stealth_level=2
    )
    
    if stealth_response:
        print(f"Stealth trade webhook response: {json.dumps(stealth_response, indent=2)}\n")
        # Send a Slack notification for the stealth trade
        send_slack_notification(
            message="🥷 Stealth trade executed: BUY XAUUSD @ market price",
            emoji=":ninja:"
        )
    
    print("\nWebhook examples completed.")


if __name__ == "__main__":
    main()