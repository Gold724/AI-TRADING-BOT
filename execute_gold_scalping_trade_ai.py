#!/usr/bin/env python
# execute_gold_scalping_trade_ai.py - Script to execute a gold scalping trade using AI-enhanced login

import os
import sys
import time
import json
from datetime import datetime

# Set DEV_MODE environment variable for safety
os.environ["DEV_MODE"] = "true"

# Import the AI login module
from ai_login_bulenox import AILoginAssistant, execute_gold_trade

# Set a unique Chrome profile to avoid session conflicts
# Note: We'll handle this directly in the AILoginAssistant instance instead of using environment variables

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)

# Function to log trade details
def log_trade_execution(success, trade_params):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/gold_scalping_trade_ai_{timestamp}.json"
    
    log_data = {
        "timestamp": timestamp,
        "trade_params": trade_params,
        "success": success
    }
    
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"Trade execution logged to {log_file}")

# Main function to execute a gold scalping trade
def execute_gold_scalping_trade_ai():
    print("=== Bulenox Gold Scalping Trade Execution (AI-Enhanced) ===\n")
    
    # Define trade parameters for scalping
    # Scalping typically uses tight stop loss and take profit levels
    side = "buy"
    quantity = 1  # Fixed contract size of 1 as requested
    
    # Get current gold price (this would normally come from market data)
    # For testing, we'll use approximate values
    current_price = 2400.00  # Example price
    
    # Set tight stop loss and take profit for scalping
    # Gold is approximately $100 per $1 price movement per contract
    # For scalping, we aim for small, quick profits with controlled risk
    stop_loss = current_price - 0.50  # $50 risk (0.5 points)
    take_profit = current_price + 0.30  # $30 profit target (0.3 points)
    
    trade_params = {
        "symbol": "XAUUSD",  # Gold
        "side": side,
        "quantity": quantity,
        "current_price": current_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }
    
    print("Trade Parameters:")
    print(json.dumps(trade_params, indent=2))
    print(f"Risk: ${(current_price - stop_loss) * 100:.2f}")
    print(f"Reward: ${(take_profit - current_price) * 100:.2f}")
    print(f"Risk/Reward Ratio: 1:{((take_profit - current_price)/(current_price - stop_loss)):.2f}\n")
    
    try:
        # Login to Bulenox using AI-enhanced login with custom profile
        print("Logging in to Bulenox using AI-enhanced login...")
        
        # Create a custom login assistant with debug mode enabled
        # Generate a unique profile name using timestamp to avoid Chrome session conflicts
        unique_profile = f"gold_scalping_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        login_assistant = AILoginAssistant(debug=True)
        login_assistant.profile_name = unique_profile
        
        # Initialize the driver and login
        driver = login_assistant.login()
        
        if not driver:
            print("\n❌ Login failed. Cannot execute trade.")
            log_trade_execution(False, {**trade_params, "error": "Login failed"})
            return
        
        print("\n✅ Login successful!")
        
        # Execute the trade
        print("\nExecuting scalping trade...")
        start_time = time.time()
        
        success = execute_gold_trade(
            driver=driver,
            side=side,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        execution_time = time.time() - start_time
        
        # Log the trade
        log_trade_execution(success, trade_params)
        
        if success:
            print("\n✅ Gold scalping trade executed successfully!")
            print("The trade has been placed with take profit set to close automatically")
            print(f"Expected profit: ~${(take_profit - current_price) * 100:.2f} when take profit is hit")
        else:
            print("\n❌ Failed to execute gold scalping trade")
            print("Please check the logs for details")
        
        print(f"\nExecution Time: {execution_time:.2f} seconds")
        
        # Ask user if they want to keep the browser open
        keep_open = input("\nKeep browser open to monitor the trade? (y/n): ")
        if keep_open.lower() != 'y':
            print("Closing browser...")
            driver.quit()
            print("Browser closed.")
        else:
            print("\nBrowser will remain open. Press Enter when you're done...")
            input()
            driver.quit()
            print("Browser closed.")
    
    except Exception as e:
        print(f"\n❌ Error during trade execution: {e}")

# Run the script
if __name__ == "__main__":
    execute_gold_scalping_trade_ai()
    print("\n=== Scalping Trade Execution Complete ===")