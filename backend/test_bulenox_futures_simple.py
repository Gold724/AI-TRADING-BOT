import os
import json
from dotenv import load_dotenv

# Set DEV_MODE environment variable
os.environ['DEV_MODE'] = 'true'

from executor_bulenox_futures import BulenoxFuturesExecutor

def test_bulenox_futures_executor():
    # Load environment variables
    load_dotenv()
    
    # Create a test signal for GBPUSD which will be mapped to MBTQ25
    test_signal = {
        "symbol": "GBPUSD",  # This will be mapped to MBTQ25
        "side": "buy",
        "quantity": 1,
        "price": None,  # Market order
        "type": "MARKET"
    }
    
    # Create stop loss and take profit values
    stop_loss = 1.2500  # Adjust based on current market price
    take_profit = 1.2700  # Adjust based on current market price
    
    print("\nTest Signal:")
    print(json.dumps(test_signal, indent=2))
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}")
    
    try:
        # Initialize the executor
        print("\nInitializing BulenoxFuturesExecutor...")
        executor = BulenoxFuturesExecutor(test_signal, stop_loss, take_profit)
        print("Executor initialized successfully")
        
        # Print futures symbol mapping
        print("\nFutures Symbol Mapping:")
        for symbol, futures_symbol in executor.futures_symbols.items():
            print(f"{symbol} -> {futures_symbol}")
        
        # Print gold symbols
        print("\nGold Symbols:")
        for symbol in executor.gold_symbols:
            print(f"- {symbol}")
        
        # Get trading mode
        print("\nTrading Mode:")
        mode = "Evaluation" if executor.evaluation_mode else "Funded"
        print(f"Mode: {mode}")
        
        # Test mapping a symbol
        original_symbol = test_signal["symbol"]
        mapped_symbol = executor._map_to_futures_symbol(original_symbol)
        print(f"\nMapped {original_symbol} to {mapped_symbol}")
        
        print("\nTest completed successfully!")
        return True
    except Exception as e:
        print(f"\nError during test: {e}")
        return False

if __name__ == "__main__":
    print("AI Trading Sentinel - Bulenox Futures Executor Test (DEV MODE)")
    print("===========================================================")
    test_bulenox_futures_executor()