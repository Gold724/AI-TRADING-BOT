import os
import sys
import json
from dotenv import load_dotenv
from backend.executor_bulenox_futures import BulenoxFuturesExecutor

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
    
    # Initialize the executor
    executor = BulenoxFuturesExecutor(test_signal, stop_loss, take_profit)
    
    # Check executor health
    print("\nChecking executor health...")
    health_status = executor.health()
    print(f"Executor health: {'OK' if health_status else 'FAILED'}")
    
    if not health_status:
        print("Executor health check failed. Please check credentials and connection.")
        return False
    
    # Execute the trade
    print("\nExecuting test trade...")
    print("NOTE: This will simulate a trade but NOT actually execute it.")
    print("Press Ctrl+C within 5 seconds to cancel...")
    
    try:
        import time
        for i in range(5, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        return False
    
    # Execute the trade
    result = executor.execute_trade()
    
    if result:
        print("\n✅ Test completed successfully!")
        print("Check the logs/screenshots directory for visual confirmation.")
    else:
        print("\n❌ Test failed. Check the logs for details.")
    
    return result

def test_all_futures_symbols():
    # Test all available futures symbols
    symbols = [
        {"symbol": "GBPUSD", "futures": "MBTQ25"},  # British Pound futures
        {"symbol": "EURUSD", "futures": "6EU25"},   # Euro FX futures
        {"symbol": "USDJPY", "futures": "6J25"},    # Japanese Yen futures
        {"symbol": "ES", "futures": "ES25"}         # E-mini S&P 500 futures
    ]
    
    print("Available Futures Symbols for Testing:")
    for i, sym in enumerate(symbols, 1):
        print(f"{i}. {sym['symbol']} → {sym['futures']}")
    
    try:
        choice = input("\nSelect a symbol to test (1-4) or press Enter for GBPUSD/MBTQ25: ")
        if choice.strip() == "":
            choice = "1"
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(symbols):
            print("Invalid choice. Using GBPUSD/MBTQ25.")
            idx = 0
    except ValueError:
        print("Invalid input. Using GBPUSD/MBTQ25.")
        idx = 0
    
    # Create a test signal for the selected symbol
    test_signal = {
        "symbol": symbols[idx]["symbol"],
        "side": "buy",
        "quantity": 1,
        "price": None,  # Market order
        "type": "MARKET"
    }
    
    # Create stop loss and take profit values (placeholder values)
    stop_loss = 0.98  # Will be adjusted based on symbol
    take_profit = 1.02  # Will be adjusted based on symbol
    
    print(f"\nTesting with {test_signal['symbol']} → {symbols[idx]['futures']}")
    
    # Initialize the executor
    executor = BulenoxFuturesExecutor(test_signal, stop_loss, take_profit)
    
    # Execute the trade
    print("\nExecuting test trade...")
    print("NOTE: This will simulate a trade but NOT actually execute it.")
    print("Press Ctrl+C within 5 seconds to cancel...")
    
    try:
        import time
        for i in range(5, 0, -1):
            print(f"Starting in {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        return False
    
    # Execute the trade
    result = executor.execute_trade()
    
    if result:
        print("\n✅ Test completed successfully!")
        print("Check the logs/screenshots directory for visual confirmation.")
    else:
        print("\n❌ Test failed. Check the logs for details.")
    
    return result

if __name__ == "__main__":
    print("AI Trading Sentinel - Bulenox Futures Executor Test")
    print("====================================================")
    
    # Determine which test to run
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        test_all_futures_symbols()
    else:
        test_bulenox_futures_executor()