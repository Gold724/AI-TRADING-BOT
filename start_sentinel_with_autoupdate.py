#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI Trading Sentinel Launcher with Auto-Update Support

This script launches the AI Trading Sentinel heartbeat with support for
automatic restarts after GitHub updates. It monitors the exit code of the
heartbeat process and restarts it if it exits with code 42, which indicates
that an update has been applied and a restart is needed.
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"sentinel_launcher_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('sentinel_launcher')

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def run_sentinel():
    """
    Run the AI Trading Sentinel heartbeat and handle restarts
    """
    restart_count = 0
    max_restarts = 10  # Maximum number of restarts to prevent infinite loops
    restart_delay = 5  # Seconds to wait before restarting
    
    while restart_count < max_restarts:
        logger.info(f"Starting AI Trading Sentinel (restart count: {restart_count})")
        
        # Prepare the command to run the heartbeat
        cmd = [sys.executable, "heartbeat.py"]
        
        # Add any command line arguments passed to this script
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        
        # Run the heartbeat process
        process = subprocess.Popen(cmd)
        
        try:
            # Wait for the process to complete
            exit_code = process.wait()
            
            # Check if the process exited with the restart code (42)
            if exit_code == 42:
                logger.info("Sentinel exited with restart code 42 (update applied)")
                restart_count += 1
                
                # Wait before restarting
                logger.info(f"Waiting {restart_delay} seconds before restart...")
                time.sleep(restart_delay)
                
                # Continue the loop to restart
                continue
            elif exit_code == 0:
                # Normal exit
                logger.info("Sentinel exited normally with code 0")
                break
            else:
                # Error exit
                logger.error(f"Sentinel exited with error code {exit_code}")
                break
        
        except KeyboardInterrupt:
            # Handle Ctrl+C
            logger.info("Keyboard interrupt detected, terminating Sentinel...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            break
    
    if restart_count >= max_restarts:
        logger.warning(f"Maximum restart count ({max_restarts}) reached. Exiting.")

if __name__ == "__main__":
    try:
        run_sentinel()
    except Exception as e:
        logger.exception(f"Unhandled exception in launcher: {e}")
        sys.exit(1)