#!/usr/bin/env python
# execute_gold_trade.py - Script to log into Bulenox and execute a gold futures trade

import os
import time
from datetime import datetime

# Import AI-powered login functionality
from ai_login_bulenox import ai_login_bulenox, update_heartbeat_status

# Import news filter for contract size adjustment
from news_filter import NewsAwareFilter, get_dynamic_contract_size

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)

# Main function to execute a gold futures trade
def execute_gold_trade():
    print("=== Bulenox Gold Futures Trade Execution ===\n")
    
    # Update status
    update_heartbeat_status("🔄 Initializing gold futures trade session...")
    
    # Define trade parameters
    trade_signal = {
        "symbol": "XAUUSD",  # Gold futures
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
    update_heartbeat_status("🔐 Logging into Bulenox...")
    
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
        update_heartbeat_status("❌ Login failed. Cannot execute trade.")
        return
    
    # Step 2: Execute the trade
    try:
        print("\nNavigating to trading platform...")
        update_heartbeat_status("🔄 Navigating to trading platform...")
        
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
        
        # For demonstration purposes, we'll just print the trade details
        # In a real implementation, you would use the BulenoxExecutor class
        # to actually place the trade
        print("\nTrade details:")
        for key, value in trade_signal.items():
            print(f"  {key}: {value}")
        
        print("\nThis is a demonstration - no actual trade will be executed.")
        print("To execute a real trade, use the BulenoxExecutor class from executor_bulenox.py")
        
        update_heartbeat_status("✅ Trade demonstration completed")
        
    except Exception as e:
        print(f"Error during trade execution: {e}")
        update_heartbeat_status(f"❌ Error during trade execution: {str(e)[:50]}...")
    finally:
        # Close the driver
        print("\nClosing browser...")
        driver.quit()

# Run the script
if __name__ == "__main__":
    execute_gold_trade()
    print("\n=== Trade Execution Complete ===")