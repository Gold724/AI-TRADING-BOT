#!/usr/bin/env python
# execute_gold_futures_trade.py - Script to execute a gold futures trade using BulenoxFuturesExecutor

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
def log_trade(trade_data, success, error=None):
    """Log the trade to a JSON file"""
    try:
        # Create trade log file if it doesn't exist
        trade_log_file = os.path.join("logs", "gold_futures_trade_log.json")
        
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
            "direction": trade_data.get("side", "buy"),
            "quantity": trade_data.get("quantity", 1),
            "entry_price": trade_data.get("price", "MARKET"),
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
        
        print(f"Trade logged: {trade_data['symbol']} {trade_data.get('side', 'buy')}")
        
    except Exception as e:
        print(f"Error logging trade: {e}")

# Main function to execute a gold futures trade
def execute_gold_futures_trade():
    print("=== Bulenox Gold Futures Trade Execution ===\n")
    
    # Define trade parameters
    trade_signal = {
        "symbol": "XAUUSD",  # Gold futures
        "side": "buy",
        "quantity": 1,
        "price": None,  # Market order
        "type": "MARKET",
    }
    
    # Set stop loss and take profit
    stop_loss = 2387.50
    take_profit = 2405.50
    
    print("Trade Signal:")
    print(json.dumps(trade_signal, indent=2))
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}\n")
    
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
        print("Executing trade...")
        result = executor.execute_trade()
        
        # Print result
        print("\nTrade Execution Result:")
        print(json.dumps(result, indent=2))
        
        # Log the trade
        log_trade(trade_signal, result.get("status") == "success", 
                 error=result.get("message") if result.get("status") != "success" else None)
        
    except Exception as e:
        print(f"Error during trade execution: {e}")
        log_trade(trade_signal, False, str(e))

# Run the script
if __name__ == "__main__":
    execute_gold_futures_trade()
    print("\n=== Trade Execution Complete ===\n")