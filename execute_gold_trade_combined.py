#!/usr/bin/env python
# execute_gold_trade_combined.py - Script to log into Bulenox and execute a gold trade

import os
import sys
import time
import json
from datetime import datetime

# Import login functionality
from login_bulenox import login_bulenox_with_profile, update_heartbeat_status

# Import news filter for contract size adjustment
from news_filter import NewsAwareFilter, get_dynamic_contract_size

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)

# Function to log trade details
def log_trade(trade_data, success, error=None):
    """Log the trade to a JSON file"""
    try:
        # Create trade log file if it doesn't exist
        trade_log_file = os.path.join("logs", "trade_log.json")
        
        # Initialize trade history
        trade_history = []
        
        # Load existing trade history if file exists
        if os.path.exists(trade_log_file):
            try:
                with open(trade_log_file, "r") as f:
                    content = f.read()
                    if content.strip():
                        trade_history = json.loads(content)
                    # If the file exists but is empty or invalid JSON, initialize with empty list
                    if not isinstance(trade_history, list):
                        trade_history = []
            except json.JSONDecodeError:
                # If the file contains invalid JSON, initialize with empty list
                trade_history = []
        
        # Create trade log entry
        trade_log = {
            "timestamp": datetime.now().isoformat(),
            "symbol": trade_data["symbol"],
            "direction": trade_data.get("direction", "buy"),
            "quantity": trade_data.get("quantity", 1),
            "entry_price": trade_data.get("entry_price", "MARKET"),
            "take_profit": trade_data.get("take_profit"),
            "stop_loss": trade_data.get("stop_loss"),
            "success": success,
        }
        
        # Add error message if provided
        if error:
            trade_log["error"] = error
        
        # Add to trade history
        trade_history.append(trade_log)
        
        # Save updated trade history
        with open(trade_log_file, "w") as f:
            json.dump(trade_history, f, indent=2)
        
        print(f"Trade logged: {trade_data['symbol']} {trade_data.get('direction', 'buy')}")
        
    except Exception as e:
        print(f"Error logging trade: {e}")

# Main function to execute a gold trade
def execute_gold_trade_combined():
    print("=== Bulenox Gold Trade Execution ===\n")
    
    # Update status
    try:
        update_heartbeat_status("🔄 Initializing gold trade session...")
    except Exception as e:
        print(f"Error updating status: {e}")
    
    # Define trade parameters
    trade_signal = {
        "symbol": "XAUUSD",  # Gold
        "direction": "buy",
        "entry_price": 2395.50,
        "take_profit": 2405.50,
        "stop_loss": 2387.50,
        "quantity": 1,  # Base contract size
        # Add aliases for executor compatibility
        "tp": 2405.50,
        "sl": 2387.50,
        "price": 2395.50,
    }
    
    # Initialize news filter to adjust contract size
    news_filter = NewsAwareFilter()
    
    # Check if it's safe to trade
    is_safe, reason = news_filter.is_safe_to_trade(trade_signal["symbol"])
    
    print(f"Safe to trade {trade_signal['symbol']}: {'Yes' if is_safe else 'No'}")
    if not is_safe:
        print(f"Reason: {reason}")
        print("Proceeding anyway for demonstration purposes...")
    
    # Get risk level and adjust contract size
    risk_level = news_filter.get_event_risk(trade_signal["symbol"])
    original_quantity = trade_signal["quantity"]
    adjusted_quantity = get_dynamic_contract_size(trade_signal["symbol"], original_quantity)
    
    print(f"Risk level: {risk_level}")
    print(f"Original contract size: {original_quantity}")
    print(f"Adjusted contract size: {adjusted_quantity}")
    
    # Update trade signal with adjusted quantity
    trade_signal["quantity"] = adjusted_quantity
    
    # Step 1: Login to Bulenox
    print("\nAttempting to login to Bulenox...")
    try:
        update_heartbeat_status("🔑 Logging into Bulenox...")
    except Exception as e:
        print(f"Error updating status: {e}")
    
    # Try login up to 3 times
    driver = None
    login_attempts = 0
    max_login_attempts = 3
    
    while driver is None and login_attempts < max_login_attempts:
        login_attempts += 1
        print(f"Login attempt {login_attempts}/{max_login_attempts}")
        
        try:
            driver = login_bulenox_with_profile(debug=True)
            
            if driver:
                print("Login successful")
                break
            else:
                print(f"Login attempt {login_attempts} failed")
                if login_attempts < max_login_attempts:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
        except Exception as e:
            print(f"Error during login attempt {login_attempts}: {e}")
            if login_attempts < max_login_attempts:
                print("Retrying in 5 seconds...")
                time.sleep(5)
    
    if not driver:
        print("All login attempts failed. Cannot execute trade.")
        try:
            update_heartbeat_status("❌ Login failed. Cannot execute trade.")
        except Exception as e:
            print(f"Error updating status: {e}")
        log_trade(trade_signal, False, "Login failed")
        return
    
    # Step 2: Execute the trade
    try:
        print("\nNavigating to trading platform...")
        try:
            update_heartbeat_status("🔄 Navigating to trading platform...")
        except Exception as e:
            print(f"Error updating status: {e}")
        
        # Navigate to trading page
        driver.get("https://bulenox.projectx.com/trading")
        time.sleep(3)  # Wait for page to load
        
        # Take screenshot of trading page
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trading_screenshot = os.path.join(
            "logs/screenshots", f"bulenox_trading_{timestamp}.png"
        )
        driver.save_screenshot(trading_screenshot)
        print(f"Trading page screenshot saved to: {trading_screenshot}")
        
        # Display trade details
        print("\nTrade details:")
        for key, value in trade_signal.items():
            print(f"  {key}: {value}")
        
        # In a real implementation, you would execute the trade
        # For demonstration purposes, we'll just simulate the trade execution
        print("\nThis is a demonstration - no actual trade will be executed.")
        print("To execute a real trade, use the BulenoxExecutor class from executor_bulenox.py")
        
        # Simulate successful trade for logging
        log_trade(trade_signal, True)
        try:
            update_heartbeat_status("✅ Trade demonstration completed")
        except Exception as e:
            print(f"Error updating status: {e}")
        
    except Exception as e:
        print(f"Error during trade execution: {e}")
        try:
            update_heartbeat_status(f"❌ Error during trade execution: {str(e)[:50]}...")
        except Exception as status_e:
            print(f"Error updating status: {status_e}")
        log_trade(trade_signal, False, str(e))
    finally:
        # Close the driver
        print("\nClosing browser...")
        driver.quit()

# Run the script
if __name__ == "__main__":
    execute_gold_trade_combined()
    print("\n=== Trade Execution Complete ===\n")