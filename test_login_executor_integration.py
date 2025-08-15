#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Login and Executor Integration

This script tests the integration between the AI-enhanced login functionality
and the trade executor for the Bulenox platform.
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime

from dotenv import load_dotenv

from login_executor_connector import BulenoxConnector, update_heartbeat_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("integration_test")

# Create necessary directories
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)

# Load environment variables
load_dotenv()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Login and Executor Integration")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--profile",
        type=int,
        default=int(os.getenv("BULENOX_PROFILE_INDEX", "13")),
        help="Chrome profile index (13-15 recommended)"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="EURUSD",
        help="Symbol to test with"
    )
    parser.add_argument(
        "--direction",
        type=str,
        choices=["buy", "sell"],
        default="buy",
        help="Trade direction"
    )
    parser.add_argument(
        "--quantity",
        type=float,
        default=0.01,
        help="Trade quantity"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the trade (default is dry run)"
    )
    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Print banner
    print("\n" + "=" * 80)
    print("🔍 AI Trading Sentinel - Login & Executor Integration Test")
    print("=" * 80 + "\n")
    
    # Update heartbeat status
    update_heartbeat_status("🔄 Starting integration test", session_active=True)
    
    # Create connector
    print(f"Creating connector with Profile {args.profile}...")
    connector = BulenoxConnector(debug=args.debug, profile_index=args.profile)
    
    # Login
    print("\nAttempting login with retry logic...")
    login_success = connector.login(max_retries=3)
    
    if login_success:
        print("\n✅ Login successful!")
        
        # Create test signal
        signal = {
            "symbol": args.symbol,
            "direction": args.direction,
            "quantity": args.quantity,
            "tp": None,  # No take profit for test
            "sl": None   # No stop loss for test
        }
        
        print(f"\nTest signal: {json.dumps(signal, indent=2)}")
        
        if args.execute:
            # Execute trade
            print(f"\n🚀 Executing {args.direction.upper()} order for {args.symbol}...")
            result = connector.execute_trade(signal)
            
            # Print result
            print(f"\nTrade execution result: {json.dumps(result, indent=2)}")
        else:
            print("\n⚠️ Dry run mode - not executing actual trade")
            print("Use --execute flag to perform actual trade execution")
        
        # Logout
        print("\nLogging out...")
        connector.logout()
        print("✅ Logged out successfully!")
    else:
        print("\n❌ Login failed after multiple attempts!")
    
    print("\n" + "=" * 80)
    print("Integration test completed")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()