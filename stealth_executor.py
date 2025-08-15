# stealth_executor.py
# AI-driven stealth execution system for TRAE trading platform
# Implements human-like browser automation with AI decision making
# and news-aware trade execution

import logging
import time
import json
import os
import argparse
import sys
import random
from datetime import datetime

# Import AI components
from ai_components.sentinel_decider import decide_trade
from ai_components.news_guard import NewsGuard
from ai_components.risk_control import get_risk_level
from core.selenium_human_like import perform_human_login, execute_trade

# Create instances for function access
news_guard = NewsGuard()
is_news_soon = news_guard.is_news_soon
should_modify_trade = news_guard.should_modify_trade

# Configure logging
log_dir = "execution_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"stealth_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("stealth_executor")

# Constants
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5
MIN_CONFIDENCE = 60


def log_execution(signal, status, account=None, error=None):
    """Log execution details to file and console
    
    Args:
        signal (dict): Trade signal
        status (str): Execution status
        account (str, optional): Account used for execution
        error (str, optional): Error message if any
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "pair": signal.get("pair", "unknown"),
        "direction": signal.get("direction", "unknown"),
        "status": status,
        "account": account,
        "error": error
    }
    
    logger.info(f"Trade execution: {json.dumps(log_entry)}")
    
    # Save to execution log file
    execution_log_file = os.path.join(log_dir, "execution_history.json")
    try:
        if os.path.exists(execution_log_file):
            with open(execution_log_file, "r") as f:
                execution_log = json.load(f)
        else:
            execution_log = []
        
        execution_log.append(log_entry)
        
        with open(execution_log_file, "w") as f:
            json.dump(execution_log, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save execution log: {e}")


def notify_slack(message, webhook_url=None):
    """Send notification to Slack
    
    Args:
        message (str): Message to send
        webhook_url (str, optional): Slack webhook URL
    """
    if not webhook_url:
        # Try to get webhook URL from environment variable
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("Slack webhook URL not provided, skipping notification")
        return
    
    try:
        import requests
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to send Slack notification: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")


def stealth_trade(signal, min_confidence=MIN_CONFIDENCE, max_retries=MAX_RETRIES, notify=True):
    """Execute trade using stealth mode with AI components
    
    Args:
        signal (dict): Trade signal with pair, direction, etc.
        min_confidence (int): Minimum confidence level to execute trade
        max_retries (int): Maximum number of retries on failure
        notify (bool): Whether to send notifications
    
    Returns:
        str: Execution status
    """
    # Check for high-impact news
    if is_news_soon(signal['pair']):
        message = f"High-impact news detected for {signal['pair']}. Aborting trade."
        logger.warning(message)
        if notify:
            notify_slack(message)
        log_execution(signal, "aborted_news")
        return "aborted_news"
    
    # Check if trade should be modified due to news
    modified_signal = signal.copy()
    if should_modify_trade(signal['pair']):
        logger.info(f"Modifying trade for {signal['pair']} due to upcoming news")
        # Reduce lot size or adjust take profit/stop loss
        if "lot_size" in modified_signal:
            modified_signal["lot_size"] = modified_signal["lot_size"] * 0.5
            logger.info(f"Reduced lot size to {modified_signal['lot_size']} due to news")
    
    # Get AI decision for trade routing
    decision = decide_trade(modified_signal)
    if decision['confidence'] < min_confidence:
        message = f"Confidence too low ({decision['confidence']}%). Minimum required: {min_confidence}%. Skipping trade."
        logger.info(message)
        if notify:
            notify_slack(message)
        log_execution(modified_signal, "low_confidence")
        return "low_confidence"
    
    # Get risk level based on strategy performance
    risk = get_risk_level(modified_signal.get('pair', ''), modified_signal.get('strategy', 'default'))
    account = decision['assigned_account']
    
    if not account:
        message = "No suitable account found for trade execution. Aborting."
        logger.warning(message)
        if notify:
            notify_slack(message)
        log_execution(modified_signal, "no_account")
        return "no_account"
    
    # Execute trade with retries
    retry_count = 0
    last_error = None
    browser = None
    
    while retry_count < max_retries:
        try:
            # Log attempt
            logger.info(f"Attempt {retry_count + 1}/{max_retries} to execute trade on {account}")
            
            # Perform human-like login
            browser = perform_human_login(account)
            
            # Execute trade with human-like behavior
            execute_trade(browser, modified_signal, risk)
            
            # Log success
            message = f"Trade successful on {account} for {modified_signal['pair']} {modified_signal['direction']}"
            logger.info(message)
            if notify:
                notify_slack(message)
            log_execution(modified_signal, "success", account)
            
            # Close browser
            if browser:
                try:
                    browser.quit()
                except:
                    pass
            
            return "success"
        
        except Exception as e:
            last_error = str(e)
            logger.error(f"Trade execution failed: {last_error}")
            
            # Close browser if open
            if browser:
                try:
                    browser.quit()
                except:
                    pass
            
            # Increment retry counter
            retry_count += 1
            
            if retry_count < max_retries:
                # Calculate backoff time
                backoff_time = (BACKOFF_FACTOR ** retry_count) * (1 + random.random())
                logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
    
    # All retries failed
    message = f"All {max_retries} attempts failed for {modified_signal['pair']} {modified_signal['direction']}. Last error: {last_error}"
    logger.error(message)
    if notify:
        notify_slack(message)
    log_execution(modified_signal, "fail", account, last_error)
    
    return "fail"


def parse_arguments():
    """Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="TRAE AI Stealth Execution System")
    
    # Mode and risk settings
    parser.add_argument("--mode", choices=["stealth", "normal"], default="stealth",
                        help="Execution mode (stealth or normal)")
    parser.add_argument("--risk", choices=["low", "medium", "high", "auto"], default="auto",
                        help="Risk level for trade execution")
    
    # Filtering and decision making
    parser.add_argument("--filter", choices=["news", "none"], default="news",
                        help="Filter trades based on news events")
    parser.add_argument("--decider", choices=["ai", "manual"], default="ai",
                        help="Decision maker for trade routing")
    
    # Confidence threshold
    parser.add_argument("--confidence-min", type=int, default=MIN_CONFIDENCE,
                        help="Minimum confidence level to execute trade (0-100)")
    
    # Signal file or manual input
    parser.add_argument("--signal-file", type=str,
                        help="JSON file containing trade signal")
    parser.add_argument("--pair", type=str,
                        help="Trading pair (e.g., EURUSD)")
    parser.add_argument("--direction", choices=["buy", "sell"],
                        help="Trade direction")
    parser.add_argument("--lot-size", type=float, default=0.01,
                        help="Lot size for trade")
    
    # Notification settings
    parser.add_argument("--notify", action="store_true", default=True,
                        help="Send notifications")
    parser.add_argument("--slack-webhook", type=str,
                        help="Slack webhook URL for notifications")
    
    # Debug mode
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args()


def main():
    """Main entry point for command line execution"""
    args = parse_arguments()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Set Slack webhook URL if provided
    if args.slack_webhook:
        os.environ["SLACK_WEBHOOK_URL"] = args.slack_webhook
    
    # Get trade signal
    signal = None
    
    if args.signal_file:
        # Load signal from file
        try:
            with open(args.signal_file, "r") as f:
                signal = json.load(f)
            logger.info(f"Loaded signal from {args.signal_file}")
        except Exception as e:
            logger.error(f"Failed to load signal from {args.signal_file}: {e}")
            return 1
    elif args.pair and args.direction:
        # Create signal from command line arguments
        signal = {
            "pair": args.pair,
            "direction": args.direction,
            "lot_size": args.lot_size,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Created signal from command line arguments: {json.dumps(signal)}")
    else:
        logger.error("No trade signal provided. Use --signal-file or --pair and --direction")
        return 1
    
    # Execute trade
    logger.info(f"Executing trade in {args.mode} mode with {args.risk} risk")
    result = stealth_trade(
        signal=signal,
        min_confidence=args.confidence_min,
        notify=args.notify
    )
    
    logger.info(f"Trade execution result: {result}")
    
    # Return exit code based on result
    if result == "success":
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())