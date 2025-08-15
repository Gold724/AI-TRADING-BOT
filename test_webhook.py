#!/usr/bin/env python
# test_webhook.py - Test webhook to connect Trae.ai signals to Bulenox trade flow

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("webhook_test")

# Load environment variables
load_dotenv()

# Default API URL
DEFAULT_API_URL = "http://localhost:5000"

# Get API key from environment
API_KEY = os.getenv("API_KEY", "your_api_key_here")


def send_webhook(api_url, endpoint, payload, api_key=None):
    """Send a webhook to the specified endpoint"""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    headers["Content-Type"] = "application/json"
    
    url = f"{api_url}{endpoint}"
    logger.info(f"Sending webhook to: {url}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            logger.error(f"Error response: {response.text}")
            return {"status": "error", "message": response.text}
    
    except Exception as e:
        logger.error(f"Error sending webhook: {e}")
        return {"status": "error", "message": str(e)}


def test_health(api_url, api_key=None):
    """Test the health endpoint"""
    logger.info("Testing health endpoint...")
    
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(f"{api_url}/api/health", headers=headers)
        logger.info(f"Health check status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info(f"Health check response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            logger.error(f"Health check error: {response.text}")
            return {"status": "error", "message": response.text}
    
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        return {"status": "error", "message": str(e)}


def test_login(api_url, api_key=None, debug=True):
    """Test the login endpoint"""
    logger.info("Testing login endpoint...")
    
    payload = {"debug": debug}
    return send_webhook(api_url, "/api/login", payload, api_key)


def test_trade(api_url, api_key=None, debug=True):
    """Test the trade endpoint with a sample trade"""
    logger.info("Testing trade endpoint...")
    
    # Sample trade payload
    payload = {
        "symbol": "EURUSD",
        "direction": "buy",
        "quantity": 0.01,
        "tp": 1.0800,
        "sl": 1.0700,
        "debug": debug
    }
    
    return send_webhook(api_url, "/api/trade", payload, api_key)


def test_stealth_trade(api_url, api_key=None):
    """Test the stealth trade endpoint"""
    logger.info("Testing stealth trade endpoint...")
    
    return send_webhook(api_url, "/api/trade/stealth", {}, api_key)


def test_logout(api_url, api_key=None):
    """Test the logout endpoint"""
    logger.info("Testing logout endpoint...")
    
    return send_webhook(api_url, "/api/logout", {}, api_key)


def simulate_trae_ai_signal(api_url, api_key=None, debug=True):
    """Simulate a complete Trae.ai signal flow"""
    logger.info("\n==== Simulating Trae.ai Signal Flow ====\n")
    
    # Step 1: Check health
    health_result = test_health(api_url, api_key)
    if health_result.get("status") != "success":
        logger.error("Health check failed. Aborting signal flow.")
        return {"status": "error", "message": "Health check failed"}
    
    # Step 2: Login
    login_result = test_login(api_url, api_key, debug)
    if login_result.get("status") != "success":
        logger.error("Login failed. Aborting signal flow.")
        return {"status": "error", "message": "Login failed"}
    
    # Step 3: Execute trade
    trade_result = test_trade(api_url, api_key, debug)
    
    # Step 4: Logout (optional based on your design)
    if os.getenv("AUTO_LOGOUT", "False").lower() == "true":
        logout_result = test_logout(api_url, api_key)
        if logout_result.get("status") != "success":
            logger.warning("Logout failed, but trade may have succeeded.")
    
    return trade_result


def main():
    """Main function to parse arguments and run tests"""
    parser = argparse.ArgumentParser(description="Test webhook for Trae.ai signals to Bulenox trade flow")
    parser.add_argument(
        "--url", 
        default=os.getenv("API_URL", DEFAULT_API_URL),
        help=f"API URL (default: {DEFAULT_API_URL})"
    )
    parser.add_argument(
        "--key", 
        default=API_KEY,
        help="API key for authentication"
    )
    parser.add_argument(
        "--test", 
        choices=["health", "login", "trade", "stealth", "logout", "flow"],
        default="flow",
        help="Test to run (default: flow)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    print("=========================================")
    print("   Trae.ai to Bulenox Webhook Test   ")
    print("=========================================")
    print(f"API URL: {args.url}")
    print(f"Test: {args.test}")
    print(f"Debug: {args.debug}")
    print("\n")
    
    # Run the selected test
    if args.test == "health":
        result = test_health(args.url, args.key)
    elif args.test == "login":
        result = test_login(args.url, args.key, args.debug)
    elif args.test == "trade":
        result = test_trade(args.url, args.key, args.debug)
    elif args.test == "stealth":
        result = test_stealth_trade(args.url, args.key)
    elif args.test == "logout":
        result = test_logout(args.url, args.key)
    elif args.test == "flow":
        result = simulate_trae_ai_signal(args.url, args.key, args.debug)
    
    print("\nTest Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()