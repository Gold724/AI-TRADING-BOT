#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for AI-powered Bulenox integration

This script tests the integration between ai_login_bulenox.py and executor_bulenox.py
by using the AI-powered BulenoxIntegration class from main.py.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_bulenox")

# Create necessary directories
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)

# Import BulenoxIntegration from main.py
try:
    from main import BulenoxIntegration
except ImportError as e:
    logger.error(f"Failed to import BulenoxIntegration from main.py: {e}")
    sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Bulenox Integration")
    parser.add_argument(
        "--debug", 
        action="store_true", 
        default=os.getenv("DEBUG", "false").lower() == "true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--dreamer", 
        action="store_true", 
        default=os.getenv("DREAMER_MODE", "true").lower() == "true",
        help="Enable dreamer mode (simulation)"
    )
    return parser.parse_args()


def create_test_signal():
    """Create a test trading signal."""
    return {
        "id": f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "symbol": "AAPL",
        "action": "BUY",
        "quantity": 1,
        "price": 150.0,
        "timestamp": datetime.now().isoformat(),
        "source": "test_integration",
        "test": True
    }


def test_login_and_execute():
    """Test AI-powered login and trade execution."""
    args = parse_arguments()
    
    logger.info("Starting AI-powered Bulenox integration test")
    logger.info(f"Debug mode: {'Enabled' if args.debug else 'Disabled'}")
    logger.info(f"Dreamer mode: {'Enabled' if args.dreamer else 'Disabled'}")
    
    # Initialize Bulenox integration with AI-powered login
    bulenox = BulenoxIntegration(debug=args.debug)
    
    try:
        # Test AI-powered login
        logger.info("Testing AI-powered login...")
        login_result = bulenox.login()
        
        if not login_result:
            logger.error("AI-powered login failed. Aborting test.")
            return False
        
        logger.info("AI-powered login successful!")
        
        # Test trade execution
        if not args.dreamer:
            logger.info("Testing trade execution...")
            signal = create_test_signal()
            
            try:
                trade_result = bulenox.execute_trade(signal)
                logger.info(f"Trade execution result: {trade_result}")
            except Exception as e:
                logger.error(f"Trade execution failed: {e}")
                return False
        else:
            logger.info("Dreamer mode enabled. Skipping actual trade execution.")
            logger.info("Simulating successful trade execution.")
        
        # Test logout
        logger.info("Testing logout...")
        logout_result = bulenox.logout()
        
        if not logout_result:
            logger.error("Logout failed.")
            return False
        
        logger.info("Logout successful!")
        
        logger.info("All tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        
        # Ensure we logout even if test fails
        if bulenox.driver:
            logger.info("Cleaning up: logging out...")
            bulenox.logout()
        
        return False


if __name__ == "__main__":
    success = test_login_and_execute()
    sys.exit(0 if success else 1)