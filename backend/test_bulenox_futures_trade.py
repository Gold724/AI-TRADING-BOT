import os
import json
import time
from datetime import datetime
from executor_bulenox_futures import BulenoxFuturesExecutor

def test_bulenox_futures_trade():
    print("AI Trading Sentinel - Bulenox Futures Trade Test (DEV MODE)")
    print("===========================================================\n")
    
    # Set DEV_MODE environment variable
    os.environ["DEV_MODE"] = "true"
    
    # Create a test signal
    symbol = "GBPUSD"  # Will be mapped to MBTQ25
    test_signal = {
        "symbol": symbol,
        "side": "buy",
        "quantity": 1,
        "price": None,
        "type": "MARKET"
    }
    
    # Set stop loss and take profit
    stop_loss = 1.25
    take_profit = 1.27
    
    print("Test Signal:")
    print(json.dumps(test_signal, indent=2))
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}\n")
    
    # Initialize the executor
    print("Initializing BulenoxFuturesExecutor...")
    executor = BulenoxFuturesExecutor()
    print("Executor initialized successfully\n")
    
    # Display futures symbol mapping
    print("Futures Symbol Mapping:")
    for key, value in executor.futures_symbol_map.items():
        print(f"{key} -> {value}")
    print()
    
    # Display gold symbols
    print("Gold Symbols:")
    for gold_symbol in executor.gold_symbols:
        print(f"- {gold_symbol}")
    print()
    
    # Display trading mode
    mode = executor._detect_trading_mode()
    print("Trading Mode:")
    print(f"Mode: {mode}\n")
    
    # Test symbol mapping
    futures_symbol = executor.futures_symbol_map.get(symbol, symbol)
    print(f"Mapped {symbol} to {futures_symbol}\n")
    
    # Execute a test trade
    print("Executing test trade...")
    try:
        result = executor.execute_trade(
            signal=test_signal,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        print("\nTrade Execution Result:")
        print(json.dumps(result, indent=2))
        
        # Check if trade was successful
        if result.get("status") == "success":
            print("\n✅ Test trade executed successfully!")
        else:
            print(f"\n❌ Test trade failed: {result.get('message')}")
            
    except Exception as e:
        print(f"\n❌ Error executing trade: {str(e)}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_bulenox_futures_trade()