#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dashboard Heartbeat Monitor

This script monitors the heartbeat status of the Bulenox integration
and updates a dashboard with the current status.

Enhanced to support the login_executor_connector.py module for real orders.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/heartbeat_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("heartbeat_monitor")

# Create necessary directories
os.makedirs("logs", exist_ok=True)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Dashboard Heartbeat Monitor")
    parser.add_argument(
        "--interval", 
        type=int, 
        default=int(os.getenv("HEARTBEAT_INTERVAL", "60")),
        help="Heartbeat check interval in seconds"
    )
    parser.add_argument(
        "--dashboard-url", 
        type=str, 
        default=os.getenv("DASHBOARD_URL", "http://localhost:5000/api/heartbeat"),
        help="Dashboard API URL"
    )
    parser.add_argument(
        "--api-key", 
        type=str, 
        default=os.getenv("API_KEY", ""),
        help="API key for dashboard authentication"
    )
    return parser.parse_args()


def get_heartbeat_status():
    """Get the current heartbeat status."""
    heartbeat_file = "logs/heartbeat_status.txt"
    dashboard_heartbeat = "logs/dashboard_heartbeat.json"
    
    # First check the dashboard heartbeat file (from login_executor_connector)
    if os.path.exists(dashboard_heartbeat):
        try:
            with open(dashboard_heartbeat, "r") as f:
                heartbeat_data = json.load(f)
            
            # Calculate time since last update
            last_update = datetime.fromisoformat(heartbeat_data["timestamp"])
            now = datetime.now()
            time_diff = (now - last_update).total_seconds()
            
            # If update is recent (less than 5 minutes old)
            if time_diff < 300:
                return heartbeat_data["status"].upper()
        except Exception as e:
            logger.error(f"Error reading dashboard heartbeat: {e}")
    
    # Fall back to regular heartbeat file
    if not os.path.exists(heartbeat_file):
        return "UNKNOWN"
    
    try:
        with open(heartbeat_file, "r") as f:
            status = f.read().strip()
        return status
    except Exception as e:
        logger.error(f"Error reading heartbeat status: {e}")
        return "ERROR"


def update_dashboard(status, dashboard_url, api_key=None):
    """Update the dashboard with the current heartbeat status."""
    try:
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key
        
        data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "source": "bulenox_integration"
        }
        
        response = requests.post(
            dashboard_url,
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Dashboard updated successfully: {status}")
            return True
        else:
            logger.error(f"Failed to update dashboard: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        return False


def main():
    """Main entry point for the heartbeat monitor."""
    args = parse_arguments()
    
    logger.info("Starting Dashboard Heartbeat Monitor")
    logger.info(f"Heartbeat interval: {args.interval} seconds")
    logger.info(f"Dashboard URL: {args.dashboard_url}")
    
    try:
        while True:
            # Get current status
            status = get_heartbeat_status()
            logger.info(f"Current heartbeat status: {status}")
            
            # Update dashboard
            update_dashboard(status, args.dashboard_url, args.api_key)
            
            # Sleep until next check
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        logger.info("Dashboard Heartbeat Monitor shutting down")


if __name__ == "__main__":
    main()