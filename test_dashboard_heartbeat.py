#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Dashboard Heartbeat Integration

This script tests the dashboard heartbeat integration by simulating
login status updates and verifying the heartbeat file is properly updated.
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime

from login_executor_connector import update_heartbeat_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/heartbeat_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("heartbeat_test")

# Create necessary directories
os.makedirs("logs", exist_ok=True)

# Constants
HEARTBEAT_STATUS_FILE = "logs/heartbeat_status.txt"
DASHBOARD_HEARTBEAT_FILE = "logs/dashboard_heartbeat.json"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Dashboard Heartbeat Integration")
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval between status updates in seconds"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of status updates to perform"
    )
    return parser.parse_args()


def verify_heartbeat_files():
    """Verify that both heartbeat files exist and contain valid data."""
    # Check text file
    if os.path.exists(HEARTBEAT_STATUS_FILE):
        with open(HEARTBEAT_STATUS_FILE, "r") as f:
            text_content = f.read().strip()
            logger.info(f"Heartbeat status file content: {text_content}")
    else:
        logger.error(f"Heartbeat status file not found: {HEARTBEAT_STATUS_FILE}")
        return False
    
    # Check JSON file
    if os.path.exists(DASHBOARD_HEARTBEAT_FILE):
        try:
            with open(DASHBOARD_HEARTBEAT_FILE, "r") as f:
                json_content = json.load(f)
                logger.info(f"Dashboard heartbeat file content: {json.dumps(json_content, indent=2)}")
                
                # Verify required fields
                required_fields = ["timestamp", "status", "message", "session_id"]
                for field in required_fields:
                    if field not in json_content:
                        logger.error(f"Missing required field in dashboard heartbeat: {field}")
                        return False
                
                return True
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in dashboard heartbeat file: {DASHBOARD_HEARTBEAT_FILE}")
            return False
    else:
        logger.error(f"Dashboard heartbeat file not found: {DASHBOARD_HEARTBEAT_FILE}")
        return False


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Print banner
    print("\n" + "=" * 80)
    print("🔍 AI Trading Sentinel - Dashboard Heartbeat Test")
    print("=" * 80 + "\n")
    
    # Simulate status updates
    statuses = [
        ("🔄 Initializing AI-powered login to Bulenox...", False),
        ("⏳ Attempting login with profile 13...", False),
        ("✅ Successfully logged in to Bulenox with AI-powered login", True),
        ("🔄 Executing trade: EURUSD buy", True),
        ("✅ Trade executed successfully", True)
    ]
    
    # Limit to requested iterations
    statuses = statuses[:args.iterations]
    
    # Update status at specified interval
    for i, (message, session_active) in enumerate(statuses):
        print(f"\nUpdate {i+1}/{len(statuses)}: {message}")
        update_heartbeat_status(message, session_active=session_active)
        
        # Verify files after update
        if verify_heartbeat_files():
            print("✅ Heartbeat files verified successfully")
        else:
            print("❌ Heartbeat file verification failed")
        
        # Wait for next update
        if i < len(statuses) - 1:
            print(f"Waiting {args.interval} seconds...")
            time.sleep(args.interval)
    
    print("\n" + "=" * 80)
    print("Dashboard heartbeat test completed")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()