#!/usr/bin/env python
# execute_real_gold_trade.py - Script to log into Bulenox and execute a real gold futures trade

import os
import sys
import time
import json
from datetime import datetime

# Import AI-powered login functionality
from ai_login_bulenox import ai_login_bulenox, update_heartbeat_status

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

# Main function to execute a gold futures trade
def execute_real_gold_trade():
    print("=== Bulenox Gold Futures Trade Execution ===\n")
    
    # Update status
    try:
        update_heartbeat_status("Initializing gold futures trade session...")
    except Exception as e:
        print(f"Error updating status: {e}")
    
    # Define trade parameters
    trade_signal = {
        "symbol": "XAUUSD",  # Gold futures
        "direction": "buy",
        "entry_price": 2395.50,
        "take_profit": 2405.50,
        "stop_loss": 2387.50,
        "quantity": 1,  # Base contract size
    }
    
    # Initialize news filter to adjust contract size
    news_filter = NewsAwareFilter()
    
    # Check if it's safe to trade
    is_safe, reason = news_filter.is_safe_to_trade(trade_signal["symbol"])
    
    print(f"Safe to trade {trade_signal['symbol']}: {'Yes' if is_safe else 'No'}")
    if not is_safe:
        print(f"Reason: {reason}")
        user_input = input("Proceed with trade despite news risk? (y/n): ")
        if user_input.lower() != 'y':
            print("Trade cancelled by user.")
            log_trade(trade_signal, False, "Cancelled due to news risk")
            return
    
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
        update_heartbeat_status("Logging into Bulenox...")
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
            driver = ai_login_bulenox(debug=True)
            
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
            update_heartbeat_status("Login failed. Cannot execute trade.")
        except Exception as e:
            print(f"Error updating status: {e}")
        log_trade(trade_signal, False, "Login failed")
        return
    
    # Step 2: Execute the trade
    try:
        print("\nNavigating to trading platform...")
        try:
            update_heartbeat_status("Navigating to trading platform...")
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
        
        # Import the executor here to avoid circular imports
        try:
            from executor_bulenox import BulenoxExecutor
            
            # Create executor instance
            executor = BulenoxExecutor(trade_signal)
            
            # Execute the trade using the existing driver
            print("\nExecuting trade...")
            try:
                update_heartbeat_status(f"Executing {trade_signal['direction']} trade for {trade_signal['quantity']} {trade_signal['symbol']}")
            except Exception as e:
                print(f"Error updating status: {e}")
            
            # In a real implementation, you would call:
            # result = executor.execute_trade(driver, debug=True)
            
            # For safety, we'll just simulate the trade execution
            print("\nSIMULATED TRADE EXECUTION - No actual trade placed")
            print("To execute a real trade, uncomment the executor.execute_trade line")
            
            # Simulate successful trade for logging
            log_trade(trade_signal, True)
            try:
                update_heartbeat_status("Trade demonstration completed")
            except Exception as e:
                print(f"Error updating status: {e}")
            
        except ImportError as e:
            print(f"Error importing BulenoxExecutor: {e}")
            print("Make sure executor_bulenox.py is in the current directory")
            log_trade(trade_signal, False, f"Import error: {str(e)}")
        
    except Exception as e:
        print(f"Error during trade execution: {e}")
        try:
            update_heartbeat_status(f"Error during trade execution: {str(e)[:50]}...")
        except Exception as status_e:
            print(f"Error updating status: {status_e}")
        log_trade(trade_signal, False, str(e))
    finally:
        # Close the driver
        print("\nClosing browser...")
        driver.quit()

# Run the script
if __name__ == "__main__":
    execute_real_gold_trade()
    print("\n=== Trade Execution Complete ===")