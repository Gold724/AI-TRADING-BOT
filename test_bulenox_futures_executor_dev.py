import os
import json
import time
import datetime
from dotenv import load_dotenv

# Set DEV_MODE environment variable
os.environ["DEV_MODE"] = "true"

# Import after setting DEV_MODE
import sys
sys.path.append('C:\\Users\\Admin\\Downloads\\ai-trading-sentinel')
from backend.executor_bulenox_futures import BulenoxFuturesExecutor

def test_bulenox_futures_executor_dev():
    # Load environment variables
    load_dotenv()
    
    print("Running in DEV_MODE: No actual trades will be executed")
    
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
        mode = "Evaluation" if executor._detect_trading_mode() else "Funded"
        print(f"Mode: {mode}")
        
        # Test mapping a symbol
        original_symbol = test_signal["symbol"]
        mapped_symbol = executor._map_to_futures_symbol(original_symbol)
        print(f"\nMapped {original_symbol} to {mapped_symbol}")
        
        # Execute the trade
        print("\nExecuting test trade...")
        print("NOTE: This will simulate a trade but NOT actually execute it in DEV_MODE.")
        print("Press Ctrl+C within 5 seconds to cancel...")
        
        try:
            for i in range(5, 0, -1):
                print(f"Starting in {i}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nTest cancelled by user.")
            return False
        
        # Execute the trade
        result = executor.execute_trade()
        
        # Display the result
        print("\nTrade Execution Result:")
        print(json.dumps(result, indent=2))
        
        # Check if trade was successful
        if result.get("status") == "success":
            print("\n✅ Test trade executed successfully!")
            print("Check the logs/screenshots directory for visual confirmation.")
        else:
            print(f"\n❌ Test trade failed: {result.get('message')}")
            print("Check the logs/screenshots directory for error details.")
        
        # Test health check
        print("\nTesting health check...")
        health_status = executor.health()
        print(f"Executor health: {'PASSED' if health_status else 'FAILED'}")
        
        print("\nTest completed successfully!")
        return True
    except Exception as e:
        print(f"\nError during test: {e}")
        return False

def test_all_futures_symbols():
    print("Testing all supported futures symbols")
    
    # List of symbols to test
    symbols = ["GBPUSD", "EURUSD", "USDJPY", "ES"]
    
    results = {}
    
    for symbol in symbols:
        print(f"\n\nTesting {symbol}...")
        print("=" * 40)
        
        # Create a test signal
        test_signal = {
            "symbol": symbol,
            "side": "buy",
            "quantity": 1,
            "price": None,
            "type": "MARKET"
        }
        
        try:
            # Initialize the executor
            executor = BulenoxFuturesExecutor(test_signal)
            
            # Map the symbol
            mapped_symbol = executor._map_to_futures_symbol(symbol)
            print(f"Mapped {symbol} to {mapped_symbol}")
            
            # Store the result
            results[symbol] = {
                "mapped_to": mapped_symbol,
                "status": "success"
            }
        except Exception as e:
            print(f"Error testing {symbol}: {e}")
            results[symbol] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Print summary
    print("\n\nTest Summary:")
    print("=" * 40)
    for symbol, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        if result["status"] == "success":
            print(f"{status_icon} {symbol} -> {result['mapped_to']}")
        else:
            print(f"{status_icon} {symbol}: {result['error']}")
    
    return all(result["status"] == "success" for result in results.values())

if __name__ == "__main__":
    print("AI Trading Sentinel - Bulenox Futures Executor Test (DEV MODE)")
    print("===========================================================\n")
    
    import sys
    
    # Determine which test to run
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        test_all_futures_symbols()
    else:
        test_bulenox_futures_executor_dev()