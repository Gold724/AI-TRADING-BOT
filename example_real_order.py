#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example Real Order Execution

This script demonstrates how to use the login_executor_connector.py module
to execute real orders on the Bulenox trading platform.
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime

from dotenv import load_dotenv

from login_executor_connector import BulenoxConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/real_order_example.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("real_order_example")

# Create necessary directories
os.makedirs("logs", exist_ok=True)

# Load environment variables
load_dotenv()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Example Real Order Execution")
    parser.add_argument(
        "--symbol",
        type=str,
        default="EURUSD",
        help="Trading symbol"
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
        help="Take profit level"
    )
    parser.add_argument(
        "--sl",
        type=float,
        help="Stop loss level"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--profile",
        type=int,
        default=13,
        help="Chrome profile index (13-15 recommended)"
    )
    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Print banner
    print("\n" + "=" * 80)
    print("🚀 AI Trading Sentinel - Real Order Example")
    print("=" * 80)
    
    # Create signal from arguments
    signal = {
        "symbol": args.symbol,
        "direction": args.direction,
        "quantity": args.quantity,
    }
    
    # Add optional parameters if provided
    if args.tp is not None:
        signal["tp"] = args.tp
    if args.sl is not None:
        signal["sl"] = args.sl
    
    # Print signal
    print(f"\n📊 Trade Signal:")
    print(json.dumps(signal, indent=2))
    
    # Create connector
    print(f"\n🔄 Creating Bulenox connector with Profile {args.profile}...")
    connector = BulenoxConnector(debug=args.debug, profile_index=args.profile)
    
    # Login
    print("\n🔑 Logging in to Bulenox...")
    login_success = connector.login()
    
    if login_success:
        print("\n✅ Login successful!")
        
        # Execute trade
        print(f"\n🚀 Executing {args.direction.upper()} order for {args.symbol}...")
        result = connector.execute_trade(signal)
        
        # Print result
        print("\n📝 Trade execution result:")
        print(json.dumps(result, indent=2))
        
        # Logout
        print("\n🔄 Logging out...")
        connector.logout()
        print("\n✅ Logged out successfully!")
    else:
        print("\n❌ Login failed! Cannot execute trade.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()