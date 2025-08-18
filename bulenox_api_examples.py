#!/usr/bin/env python3
# Bulenox API Examples using Python requests

import requests
import json
import os
from pprint import pprint

# Base URL for the API
BASE_URL = "http://localhost:5000"

# Get API key from environment or set directly
API_KEY = os.environ.get("BULENOX_API_KEY", "your_api_key_here")

# Common headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_health():
    """Check if the Bulenox API is running"""
    response = requests.get(f"{BASE_URL}/api/health")
    return response.json()

def login(debug=True):
    """Login to Bulenox"""
    payload = {"debug": debug}
    response = requests.post(
        f"{BASE_URL}/api/login",
        headers=headers,
        json=payload
    )
    return response.json()

def execute_trade(symbol="EURUSD", direction="buy", quantity=0.01, 
                 take_profit=1.0800, stop_loss=1.0700, debug=True):
    """Execute a trade on Bulenox"""
    payload = {
        "symbol": symbol,
        "direction": direction,
        "quantity": quantity,
        "tp": take_profit,
        "sl": stop_loss,
        "debug": debug
    }
    response = requests.post(
        f"{BASE_URL}/api/trade",
        headers=headers,
        json=payload
    )
    return response.json()

def send_webhook_signal(account_id="BX64883", symbol="EURUSD", side="buy", 
                       quantity=0.01, stop_loss=None, take_profit=None):
    """Send a trading signal via webhook"""
    signal = {
        "symbol": symbol,
        "side": side,
        "quantity": quantity
    }
    
    if stop_loss:
        signal["stopLoss"] = stop_loss
    if take_profit:
        signal["takeProfit"] = take_profit
        
    payload = {
        "account_id": account_id,
        "signal": signal
    }
    
    response = requests.post(
        f"{BASE_URL}/api/webhook",
        headers=headers,
        json=payload
    )
    return response.json()

def logout():
    """Logout from Bulenox"""
    response = requests.post(
        f"{BASE_URL}/api/logout",
        headers=headers
    )
    return response.json()

# Example usage
if __name__ == "__main__":
    print("Testing Bulenox API Health...")
    try:
        health_result = test_health()
        pprint(health_result)
        
        print("\nThe following functions are available but commented out for safety:")
        print("- login()")
        print("- execute_trade()")
        print("- send_webhook_signal()")
        print("- logout()")
        
        print("\nTo use these functions, uncomment the examples below or call them directly.")
        print("Remember to set your API key at the top of the script or in the BULENOX_API_KEY environment variable.")
        
        # Uncomment to test these functions
        # print("\nLogging into Bulenox...")
        # login_result = login()
        # pprint(login_result)
        
        # print("\nExecuting a trade...")
        # trade_result = execute_trade(symbol="EURUSD", direction="buy", quantity=0.01)
        # pprint(trade_result)
        
        # print("\nSending a webhook signal...")
        # webhook_result = send_webhook_signal(symbol="BTCUSDT", side="buy", quantity=0.001)
        # pprint(webhook_result)
        
        # print("\nLogging out...")
        # logout_result = logout()
        # pprint(logout_result)
        
    except Exception as e:
        print(f"Error: {e}")