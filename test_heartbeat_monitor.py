#!/usr/bin/env python3
# test_heartbeat_monitor.py - Test script for the heartbeat monitoring system

import os
import time
import json
import random
import argparse
from datetime import datetime

# Status file path
STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

# Status templates with ASCII alternatives to emojis
STATUS_TEMPLATES = [
    "[OK] Heartbeat active - Login successful",
    "[OK] Heartbeat active - Trade executed successfully",
    "[WAIT] Heartbeat active - Signal validation in progress",
    "[WAIT] Heartbeat active - Login attempt in progress",
    "[WAIT] Heartbeat active - Waiting for signals",
    "[ERROR] Heartbeat error - Login failed",
    "[ERROR] Heartbeat error - Trade execution failed",
    "[RESTART] Heartbeat restarting - Triggered by monitor"
]

def update_status(status, session_active=None):
    """Update the heartbeat status file with the given status"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Determine session active state if not provided
    if session_active is None:
        if "Login successful" in status or "Trade executed" in status:
            session_active = True
        elif "Login failed" in status or "error" in status or "restarting" in status:
            session_active = False
        else:
            # Default to previous value if exists
            try:
                if os.path.exists(STATUS_FILE):
                    with open(STATUS_FILE, 'r') as f:
                        lines = f.read().strip().split('\n')
                        if len(lines) >= 3:
                            try:
                                session_data = json.loads(lines[2])
                                session_active = session_data.get("session_active", False)
                            except (json.JSONDecodeError, IndexError):
                                session_active = False
                else:
                    session_active = False
            except Exception:
                session_active = False
    
    # Write status to file
    try:
        with open(STATUS_FILE, 'w') as f:
            f.write(f"{status}\n")
            f.write(f"{datetime.now().isoformat()}\n")
            f.write(f"{{\"session_active\": {str(session_active).lower()}}}\n")
        print(f"Updated status: {status}")
        return True
    except Exception as e:
        print(f"Error updating status: {e}")
        return False

def simulate_normal_operation(duration_seconds=300, interval_seconds=10):
    """Simulate normal heartbeat operation with status updates"""
    print(f"Simulating normal operation for {duration_seconds} seconds...")
    
    start_time = time.time()
    end_time = start_time + duration_seconds
    
    # Initial status - waiting for signals
    update_status("[WAIT] Heartbeat active - Waiting for signals", False)
    
    while time.time() < end_time:
        # Simulate a trading cycle
        update_status("[WAIT] Heartbeat active - Signal validation in progress", False)
        time.sleep(interval_seconds)
        
        update_status("[WAIT] Heartbeat active - Login attempt in progress", False)
        time.sleep(interval_seconds)
        
        update_status("[OK] Heartbeat active - Login successful", True)
        time.sleep(interval_seconds)
        
        update_status("[WAIT] Heartbeat active - Trade execution in progress", True)
        time.sleep(interval_seconds)
        
        # 80% chance of successful trade, 20% chance of failure
        if random.random() < 0.8:
            update_status("[OK] Heartbeat active - Trade executed successfully", True)
        else:
            update_status("[ERROR] Heartbeat error - Trade execution failed", True)
        
        time.sleep(interval_seconds)
        
        # Back to waiting
        update_status("[WAIT] Heartbeat active - Waiting for signals", True)
        time.sleep(interval_seconds * 2)
    
    print("Normal operation simulation completed.")

def simulate_failure(failure_type="login", duration_seconds=60):
    """
    Simulate a heartbeat failure
    """
    print(f"Simulating {failure_type} failure for {duration_seconds} seconds...")
    
    if failure_type == "login":
        update_status("[WAIT] Heartbeat active - Login attempt in progress", False)
        time.sleep(5)
        update_status("[ERROR] Heartbeat error - Login failed", False)
    elif failure_type == "trade":
        update_status("[WAIT] Heartbeat active - Trade execution in progress", True)
        time.sleep(5)
        update_status("[ERROR] Heartbeat error - Trade execution failed", True)
    elif failure_type == "crash":
        update_status("[WAIT] Heartbeat active - Signal validation in progress", False)
        # Don't update status to simulate crash
    elif failure_type == "restart":
        update_status("[RESTART] Heartbeat restarting - Triggered by monitor", False)
    
    time.sleep(duration_seconds)
    print("Failure simulation completed.")

def simulate_recovery(duration_seconds=60, interval_seconds=5):
    """
    Simulate a recovery from failure
    """
    print(f"Simulating recovery for {duration_seconds} seconds...")
    
    # Start with error
    update_status("[ERROR] Heartbeat error - Login failed", False)
    time.sleep(interval_seconds)
    
    # Show restart
    update_status("[RESTART] Heartbeat restarting - Triggered by monitor", False)
    time.sleep(interval_seconds)
    
    # Show login attempt
    update_status("[WAIT] Heartbeat active - Login attempt in progress", False)
    time.sleep(interval_seconds)
    
    # Show success
    update_status("[OK] Heartbeat active - Login successful", True)
    time.sleep(interval_seconds)
    
    # Show waiting for signals
    update_status("[WAIT] Heartbeat active - Waiting for signals", True)
    
    # Continue normal operation
    remaining_time = duration_seconds - (interval_seconds * 5)
    if remaining_time > 0:
        time.sleep(remaining_time)
    
    print("Recovery simulation completed.")

def main():
    parser = argparse.ArgumentParser(description="Test the heartbeat monitoring system")
    parser.add_argument(
        "--mode", "-m", type=str, default="normal",
        choices=["normal", "login_failure", "trade_failure", "crash", "restart", "recovery"],
        help="Simulation mode"
    )
    parser.add_argument(
        "--duration", "-d", type=int, default=300,
        help="Duration of simulation in seconds"
    )
    parser.add_argument(
        "--interval", "-i", type=int, default=10,
        help="Interval between status updates in seconds"
    )
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the selected simulation
    if args.mode == "normal":
        simulate_normal_operation(args.duration, args.interval)
    elif args.mode == "login_failure":
        simulate_failure("login", args.duration)
    elif args.mode == "trade_failure":
        simulate_failure("trade", args.duration)
    elif args.mode == "crash":
        simulate_failure("crash", args.duration)
    elif args.mode == "restart":
        simulate_failure("restart", args.duration)
    elif args.mode == "recovery":
        simulate_recovery()

if __name__ == "__main__":
    main()