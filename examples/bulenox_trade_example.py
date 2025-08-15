#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bulenox Trade Example

This example demonstrates how to use the login_executor_connector
to execute trades on the Bulenox platform with enhanced login capabilities.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from login_executor_connector import BulenoxConnector, update_heartbeat_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("../logs/bulenox_example.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bulenox_example")

# Create necessary directories
os.makedirs("../logs", exist_ok=True)
os.makedirs("../logs/screenshots", exist_ok=True)

# Load environment variables
load_dotenv()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Bulenox Trade Example")
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
        help="Symbol to trade"
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
        "--tp",
        type=float,
        help="Take profit level (optional)"
    )
    parser.add_argument(
        "--sl",
        type=float,
        help="Stop loss level (optional)"
    )
    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Print banner
    print("\n" + "=" * 80)
    print("🚀 AI Trading Sentinel - Bulenox Trade Example")
    print("=" * 80 + "\n")
    
    # Update heartbeat status
    update_heartbeat_status("🔄 Starting Bulenox trade example", session_active=True)
    
    # Create connector
    print(f"Creating connector with Profile {args.profile}...")
    connector = BulenoxConnector(debug=args.debug, profile_index=args.profile)
    
    try:
        # Login
        print("\nAttempting login with retry logic...")
        login_success = connector.login(max_retries=3)
        
        if login_success:
            print("\n✅ Login successful!")
            
            # Create trade signal
            signal = {
                "symbol": args.symbol,
                "direction": args.direction,
                "quantity": args.quantity,
                "tp": args.tp,
                "sl": args.sl
            }
            
            print(f"\nTrade signal: {json.dumps(signal, indent=2)}")
            
            # Execute trade
            print(f"\n🚀 Executing {args.direction.upper()} order for {args.symbol}...")
            result = connector.execute_trade(signal)
            
            # Print result
            print(f"\nTrade execution result: {json.dumps(result, indent=2)}")
            
            # Wait for a moment to see the result
            time.sleep(5)
        else:
            print("\n❌ Login failed after multiple attempts!")
    finally:
        # Always attempt to logout
        if hasattr(connector, 'driver') and connector.driver:
            print("\nLogging out...")
            connector.logout()
            print("✅ Logged out successfully!")
    
    print("\n" + "=" * 80)
    print("Example completed")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()