#!/usr/bin/env python
# execute_gold_scalping_trade.py - Script to execute a gold scalping trade using BulenoxFuturesExecutor

import os
import sys
import time
import json
from datetime import datetime

# Set DEV_MODE environment variable for safety
os.environ["DEV_MODE"] = "true"

# Import the BulenoxFuturesExecutor
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from executor_bulenox_futures import BulenoxFuturesExecutor

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)

# Function to log trade details
def log_trade_execution(result, trade_signal):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/gold_scalping_trade_{timestamp}.json"
    
    log_data = {
        "timestamp": timestamp,
        "trade_signal": trade_signal,
        "result": result
    }
    
    with open(log_file, "w") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"Trade execution logged to {log_file}")

# Main function to execute a gold scalping trade
def execute_gold_scalping_trade():
    print("=== Bulenox Gold Scalping Trade Execution ===\n")
    
    # Define trade parameters for scalping
    # Scalping typically uses tight stop loss and take profit levels
    trade_signal = {
        "symbol": "XAUUSD",  # Gold futures
        "side": "buy",
        "quantity": 1,  # Fixed contract size of 1 as requested
        "price": None,  # Market order
        "type": "MARKET",
    }
    
    # Get current gold price (this would normally come from market data)
    # For testing, we'll use approximate values
    current_price = 2400.00  # Example price
    
    # Set tight stop loss and take profit for scalping
    # Gold is approximately $100 per $1 price movement per contract
    # For scalping, we aim for small, quick profits with controlled risk
    stop_loss = current_price - 0.50  # $50 risk (0.5 points)
    take_profit = current_price + 0.30  # $30 profit target (0.3 points)
    
    print("Trade Signal:")
    print(json.dumps(trade_signal, indent=2))
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}\n")
    print(f"Risk: ${(current_price - stop_loss) * 100:.2f}")
    print(f"Reward: ${(take_profit - current_price) * 100:.2f}")
    print(f"Risk/Reward Ratio: 1:{((take_profit - current_price)/(current_price - stop_loss)):.2f}\n")
    
    try:
        # Initialize the executor
        print("Initializing BulenoxFuturesExecutor...")
        executor = BulenoxFuturesExecutor(trade_signal, stop_loss, take_profit)
        print("Executor initialized successfully\n")
        
        # Print futures symbol mapping
        print("Futures Symbol Mapping:")
        for symbol, futures_symbol in executor.futures_symbols.items():
            print(f"{symbol} -> {futures_symbol}")
        
        # Print gold symbols
        print("\nGold Symbols:")
        for symbol in executor.gold_symbols:
            print(f"- {symbol}")
        
        # Get trading mode
        print("\nTrading Mode:")
        mode = "Evaluation" if executor.evaluation_mode else "Live"
        print(f"Mode: {mode}\n")
        
        # Execute the trade
        print("Executing scalping trade...")
        start_time = time.time()
        result = executor.execute_trade()
        execution_time = time.time() - start_time
        
        # Print result
        print("\nTrade Execution Result:")
        print(json.dumps(result, indent=2))
        print(f"Execution Time: {execution_time:.2f} seconds")
        
        # Log the trade
        log_trade_execution(result, trade_signal)
        
        if result.get("status") == "success":
            print("\n✅ Gold scalping trade executed successfully!")
            print("The trade has been placed with take profit set to close automatically")
            print(f"Expected profit: ~${(take_profit - current_price) * 100:.2f} when take profit is hit")
        else:
            print("\n❌ Failed to execute gold scalping trade")
            print(f"Reason: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n❌ Error during trade execution: {e}")

# Run the script
if __name__ == "__main__":
    execute_gold_scalping_trade()
    print("\n=== Scalping Trade Execution Complete ===")