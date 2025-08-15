#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_liveops.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.test_liveops")

# Ensure necessary directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Import TRAE components
try:
    from sentinel_decider import SentinelDecider, DeciderMode
    from liveops.stealth_executor import StealthExecutor
    from liveops.account_manager import AccountManager
    from liveops.heartbeat_monitor import HeartbeatMonitor
    from liveops.webhook_handler import WebhookHandler
    from liveops.signal_processor import SignalProcessor
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TRAE LiveOps Test")
    parser.add_argument(
        "--test", 
        type=str, 
        choices=["heartbeat", "webhook", "account", "executor", "signal", "all"],
        default="all",
        help="Test component to run"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/liveops_config.json",
        help="Path to configuration file"
    )
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Configuration file {config_path} not found, using defaults")
            return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def test_heartbeat_monitor():
    """Test the heartbeat monitor functionality."""
    logger.info("Testing HeartbeatMonitor...")
    
    try:
        # Initialize heartbeat monitor
        monitor = HeartbeatMonitor(interval=5, logs_dir="logs")
        
        # Register a test callback
        def test_callback():
            logger.info("Heartbeat callback executed")
        
        monitor.register_callback(test_callback)
        
        # Start the monitor
        result = monitor.start()
        logger.info(f"Monitor start result: {result}")
        
        # Wait for a few heartbeats
        logger.info("Waiting for heartbeats...")
        time.sleep(15)
        
        # Check health
        health = monitor.check_health()
        logger.info(f"Health check: {health}")
        
        # Stop the monitor
        result = monitor.stop()
        logger.info(f"Monitor stop result: {result}")
        
        logger.info("HeartbeatMonitor test completed successfully")
        return True
    except Exception as e:
        logger.error(f"HeartbeatMonitor test failed: {e}")
        return False


def test_webhook_handler():
    """Test the webhook handler functionality."""
    logger.info("Testing WebhookHandler...")
    
    try:
        # Initialize webhook handler
        handler = WebhookHandler(port=5001, signals_dir="data")
        
        # Start the handler
        result = handler.start()
        logger.info(f"Handler start result: {result}")
        
        # Simulate a signal
        test_signal = {
            "symbol": "EURUSD",
            "action": "BUY",
            "entry": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "source": "test"
        }
        
        # Add signal directly
        handler._save_signal(test_signal)
        
        # Get pending signals
        signals = handler.get_pending_signals()
        logger.info(f"Pending signals: {signals}")
        
        # Clear pending signals
        handler.clear_pending_signals()
        
        # Stop the handler
        result = handler.stop()
        logger.info(f"Handler stop result: {result}")
        
        logger.info("WebhookHandler test completed successfully")
        return True
    except Exception as e:
        logger.error(f"WebhookHandler test failed: {e}")
        return False


def test_account_manager(config: Dict[str, Any]):
    """Test the account manager functionality.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        bool: True if test passed, False otherwise
    """
    logger.info("Testing AccountManager...")
    
    try:
        # Initialize account manager
        manager = AccountManager(config=config)
        
        # Get active accounts
        accounts = manager.get_active_accounts()
        logger.info(f"Active accounts: {accounts}")
        
        # Test account operations
        if accounts:
            account_id = accounts[0]["account_id"]
            
            # Update account balance
            manager.update_account_balance(account_id, 10000.0)
            
            # Update open positions
            positions = [
                {
                    "symbol": "EURUSD",
                    "direction": "BUY",
                    "size": 0.1,
                    "entry_price": 1.1000,
                    "current_price": 1.1050,
                    "profit_loss": 50.0
                }
            ]
            manager.update_account_positions(account_id, positions)
            
            # Check daily loss
            result = manager.check_daily_loss_limit(account_id)
            logger.info(f"Daily loss check result: {result}")
            
            # Reset daily loss
            manager.reset_daily_loss(account_id)
        
        logger.info("AccountManager test completed successfully")
        return True
    except Exception as e:
        logger.error(f"AccountManager test failed: {e}")
        return False


def test_stealth_executor():
    """Test the stealth executor functionality."""
    logger.info("Testing StealthExecutor...")
    
    try:
        # Initialize stealth executor
        executor = StealthExecutor()
        
        # Test execution methods
        result = executor.test_connection("exness")
        logger.info(f"Connection test result: {result}")
        
        # Test dry run execution
        trade = {
            "account_id": "exness_test",
            "broker": "exness",
            "symbol": "EURUSD",
            "direction": "BUY",
            "size": 0.1,
            "entry_type": "MARKET",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100
        }
        
        result = executor.execute_trade(trade, dry_run=True)
        logger.info(f"Dry run execution result: {result}")
        
        logger.info("StealthExecutor test completed successfully")
        return True
    except Exception as e:
        logger.error(f"StealthExecutor test failed: {e}")
        return False


def test_signal_processor(config: Dict[str, Any]):
    """Test the signal processor functionality.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        bool: True if test passed, False otherwise
    """
    logger.info("Testing SignalProcessor...")
    
    try:
        # Initialize signal processor
        processor = SignalProcessor(signals_dir="data")
        
        # Add test signals
        test_signals = [
            {
                "id": f"test1_{int(time.time())}",
                "symbol": "EURUSD",
                "direction": "BUY",
                "strategy": "trend_following",
                "entry_price": 1.1000,
                "stop_loss": 1.0950,
                "take_profit": 1.1100,
                "confidence": 0.8,
                "source": "test1",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": f"test2_{int(time.time())}",
                "symbol": "GBPUSD",
                "direction": "SELL",
                "strategy": "breakout",
                "entry_price": 1.3000,
                "stop_loss": 1.3050,
                "take_profit": 1.2900,
                "confidence": 0.7,
                "source": "test2",
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": f"test3_{int(time.time())}",
                "symbol": "XAUUSD", # Gold
                "direction": "BUY",
                "strategy": "mean_reversion",
                "entry_price": 1900.00,
                "stop_loss": 1890.00,
                "take_profit": 1920.00,
                "confidence": 0.9,
                "source": "test3",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        for signal in test_signals:
            processor.add_signal(signal)
            
        # Process signals using the processor
        count = processor.process_pending_signals()
        logger.info(f"Processed {count} signals using processor")
        
        # Get processed signals
        processed = processor.get_processed_signals()
        logger.info(f"Processed signals: {len(processed)}")
        
        # Test direct processing with SentinelDecider
        logger.info("Testing direct signal processing with SentinelDecider...")
        
        # Initialize the sentinel decider
        decider = SentinelDecider(
            phase="10",
            liveops_mode=True,
            automated_trading=True,
            multi_account=True,
            passive_learning=True
        )
        
        # Process each signal directly
        for signal in test_signals:
            logger.info(f"Processing signal: {signal['id']} - {signal['symbol']} {signal['direction']}")
            result = decider.process_signal(signal)
            logger.info(f"Result: {result['status']}")
            
            if result['status'] == 'rejected':
                logger.info(f"Rejection reason: {result['reason']}")
            elif result['status'] == 'executed':
                for execution in result.get('execution_results', []):
                    logger.info(f"Execution on {execution['account_id']}: {execution['result'].get('status')}")
        
        logger.info("SignalProcessor test completed successfully")
        return True
    except Exception as e:
        logger.error(f"SignalProcessor test failed: {e}")
        return False


def main():
    """Main entry point for TRAE LiveOps Test."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Log startup information
    logger.info(f"Starting TRAE LiveOps Test - Component: {args.test}")
    
    # Run tests
    results = {}
    
    if args.test == "heartbeat" or args.test == "all":
        results["heartbeat"] = test_heartbeat_monitor()
    
    if args.test == "webhook" or args.test == "all":
        results["webhook"] = test_webhook_handler()
    
    if args.test == "account" or args.test == "all":
        results["account"] = test_account_manager(config)
    
    if args.test == "executor" or args.test == "all":
        results["executor"] = test_stealth_executor()
    
    if args.test == "signal" or args.test == "all":
        results["signal"] = test_signal_processor(config)
    
    # Print results
    logger.info("Test Results:")
    for component, result in results.items():
        logger.info(f"  {component}: {'PASS' if result else 'FAIL'}")
    
    # Overall result
    if all(results.values()):
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())