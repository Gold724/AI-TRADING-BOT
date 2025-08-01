# strategy_filter.py

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('strategy_filter')

# Load environment variables
load_dotenv()

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

def update_heartbeat_status(status, session_active=True):
    """
    Update the heartbeat status file with current status and timestamp
    
    Args:
        status (str): The current status message
        session_active (bool): Flag indicating if a trading session is active
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        
        # Write to heartbeat status file
        with open(HEARTBEAT_STATUS_FILE, 'w') as f:
            f.write(f"{status}\n{timestamp}\n{json.dumps({'session_active': session_active})}")
            
        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")

# Strategy configuration file path
STRATEGY_CONFIG_FILE = os.getenv('STRATEGY_CONFIG_FILE', 'strategy_config.json')

def load_strategy_config():
    """Load strategy configuration from file"""
    try:
        if os.path.exists(STRATEGY_CONFIG_FILE):
            with open(STRATEGY_CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Strategy config file {STRATEGY_CONFIG_FILE} not found. Using default configuration.")
            return {
                "enabled": True,
                "filters": {
                    "symbols": ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD"],
                    "directions": ["buy", "sell"],
                    "time_filter": {
                        "enabled": False,
                        "trading_hours": ["00:00-23:59"],
                        "trading_days": [0, 1, 2, 3, 4]  # Monday to Friday
                    },
                    "fibonacci_filter": {
                        "enabled": False,
                        "levels": [0.236, 0.382, 0.5, 0.618, 0.786]
                    }
                }
            }
    except Exception as e:
        logger.error(f"Error loading strategy config: {e}")
        return {"enabled": False}

def validate_signal(signal):
    """Validate a trading signal against strategy filters
    
    Args:
        signal (dict): The trading signal to validate
        
    Returns:
        bool: True if signal passes all filters, False otherwise
    """
    try:
        # Update heartbeat status
        update_heartbeat_status(f"🔍 Validating signal: {signal.get('symbol')} {signal.get('direction')}")
        
        # Load strategy configuration
        config = load_strategy_config()
        
        # Check if strategy filtering is enabled
        if not config.get("enabled", True):
            logger.info("Strategy filtering is disabled. All signals are valid.")
            update_heartbeat_status("✅ Strategy filtering disabled, signal accepted")
            return True
        
        filters = config.get("filters", {})
        
        # Symbol filter
        if "symbols" in filters and signal.get("symbol") not in filters["symbols"]:
            logger.info(f"Signal rejected: Symbol {signal.get('symbol')} not in allowed list {filters['symbols']}")
            update_heartbeat_status(f"❌ Signal rejected: Symbol {signal.get('symbol')} not allowed")
            return False
        
        # Direction filter (buy/sell)
        if "directions" in filters and signal.get("direction") not in filters["directions"]:
            logger.info(f"Signal rejected: Direction {signal.get('direction')} not in allowed list {filters['directions']}")
            update_heartbeat_status(f"❌ Signal rejected: Direction {signal.get('direction')} not allowed")
            return False
        
        # Time filter
        if filters.get("time_filter", {}).get("enabled", False):
            if not _check_time_filter(filters["time_filter"]):
                logger.info("Signal rejected: Outside of allowed trading hours or days")
                update_heartbeat_status("❌ Signal rejected: Outside trading hours")
                return False
        
        # Fibonacci filter
        if filters.get("fibonacci_filter", {}).get("enabled", False):
            if not _check_fibonacci_filter(signal, filters["fibonacci_filter"]):
                logger.info("Signal rejected: Does not match Fibonacci criteria")
                update_heartbeat_status("❌ Signal rejected: Does not match Fibonacci criteria")
                return False
        
        # All filters passed
        logger.info(f"Signal validated: {signal.get('symbol')} {signal.get('direction')}")
        update_heartbeat_status(f"✅ Signal validated: {signal.get('symbol')} {signal.get('direction')}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating signal: {e}")
        update_heartbeat_status(f"❌ Error validating signal: {str(e)[:50]}...")
        return False

def _check_time_filter(time_filter):
    """Check if current time is within allowed trading hours and days"""
    now = datetime.now()
    
    # Check trading days (0 = Monday, 6 = Sunday)
    if "trading_days" in time_filter and now.weekday() not in time_filter["trading_days"]:
        return False
    
    # Check trading hours
    if "trading_hours" in time_filter:
        current_time = now.strftime("%H:%M")
        for time_range in time_filter["trading_hours"]:
            start_time, end_time = time_range.split("-")
            if start_time <= current_time <= end_time:
                return True
        return False
    
    return True

def _check_fibonacci_filter(signal, fib_filter):
    """Check if signal matches Fibonacci criteria"""
    # This is a placeholder for actual Fibonacci analysis
    # In a real implementation, this would check if the price is near key Fibonacci levels
    
    # For now, we'll just check if the signal has a 'fib_level' property
    if "fib_level" in signal and signal["fib_level"] in fib_filter.get("levels", []):
        return True
    
    # If no specific Fibonacci data in signal, default to True
    return True

# For testing
if __name__ == "__main__":
    test_signal = {
        "symbol": "EURUSD",
        "direction": "buy",
        "price": 1.0750,
        "tp": 1.0800,
        "sl": 1.0700
    }
    
    result = validate_signal(test_signal)
    print(f"Signal validation result: {result}")