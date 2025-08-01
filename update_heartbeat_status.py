#!/usr/bin/env python
"""
Heartbeat Status Updater

This script updates the heartbeat_status.txt file with the current status and timestamp.
It can be used for testing the heartbeat monitoring system.
"""

import os
import sys
import datetime
import argparse
from pathlib import Path

def update_heartbeat_status(status_message, log_dir="logs"):
    """
    Update the heartbeat_status.txt file with the provided status message and current timestamp.
    
    Args:
        status_message (str): The status message to write
        log_dir (str): Directory where logs are stored
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Path to heartbeat status file
    status_file = os.path.join(log_dir, "heartbeat_status.txt")
    
    # Current timestamp
    timestamp = datetime.datetime.now().isoformat()
    
    # Write status and timestamp to file
    with open(status_file, 'w') as f:
        f.write(f"{status_message}\n{timestamp}")
    
    print(f"Updated heartbeat status: {status_message}")
    print(f"Timestamp: {timestamp}")
    print(f"Status file: {status_file}")

def main():
    parser = argparse.ArgumentParser(description="Update the heartbeat status file")
    parser.add_argument(
        "status", 
        nargs="?",
        default="🔄 Waiting for signals...",
        help="Status message to write to the heartbeat status file"
    )
    parser.add_argument(
        "--log-dir", 
        default="logs",
        help="Directory where logs are stored"
    )
    
    args = parser.parse_args()
    update_heartbeat_status(args.status, args.log_dir)

if __name__ == "__main__":
    main()