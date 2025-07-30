import os
import sys
import json
import argparse
import time
from utils.executor_fibonacci import FibonacciExecutor

def load_signals(file_path):
    """
    Load sample signals from JSON file
    """
    try:
        with open(file_path, 'r') as f:
            signals = json.load(f)
        return signals
    except Exception as e:
        print(f"Error loading signals: {e}")
        return []

def run_fibonacci_strategy(signal_index=0, signals_file="sample_fibonacci_signals.json"):
    """
    Run the Fibonacci strategy with a sample signal
    """
    # Load signals
    signals = load_signals(signals_file)
    
    if not signals:
        print("No signals found. Please check the signals file.")
        return False
    
    # Validate signal index
    if signal_index < 0 or signal_index >= len(signals):
        print(f"Invalid signal index. Please choose an index between 0 and {len(signals)-1}")
        return False
    
    # Get signal
    signal = signals[signal_index]
    
    print(f"\n🧠 Running Fibonacci Strategy with signal: {json.dumps(signal, indent=2)}")
    
    # Extract parameters
    symbol = signal.get("symbol")
    side = signal.get("side")
    quantity = signal.get("quantity")
    entry = signal.get("entry")
    fib_low = signal.get("fib_low")
    fib_high = signal.get("fib_high")
    stop_loss = signal.get("stopLoss")
    take_profit = signal.get("takeProfit")
    stealth_level = signal.get("stealth_level", 2)
    
    # Validate required parameters
    if not all([symbol, side, quantity, entry, fib_low, fib_high]):
        print("Missing required parameters in signal.")
        return False
    
    # Create executor
    executor = FibonacciExecutor(
        signal=signal,
        stopLoss=stop_loss,
        takeProfit=take_profit,
        stealth_level=stealth_level
    )
    
    # Calculate and display Fibonacci targets
    print(f"\n📊 Fibonacci Levels: {executor.fib_levels}")
    print(f"🎯 Fibonacci Targets: {executor.fib_targets}")
    print(f"📈 Take Profit Percentages: {executor.tp_percentages}")
    
    # Execute trade
    print("\n🚀 Executing Fibonacci strategy...")
    start_time = time.time()
    success = executor.execute_trade()
    end_time = time.time()
    
    # Print result
    if success:
        print(f"\n✅ Fibonacci strategy executed successfully in {end_time - start_time:.2f} seconds!")
    else:
        print(f"\n❌ Fibonacci strategy execution failed after {end_time - start_time:.2f} seconds!")
    
    return success

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Fibonacci Strategy with a sample signal")
    parser.add_argument("--index", type=int, default=0, help="Index of the signal to use from the signals file")
    parser.add_argument("--file", type=str, default="sample_fibonacci_signals.json", help="Path to the signals file")
    parser.add_argument("--list", action="store_true", help="List all available signals")
    
    args = parser.parse_args()
    
    # List signals if requested
    if args.list:
        signals = load_signals(args.file)
        if signals:
            print(f"\nAvailable Signals ({len(signals)}):\n")
            for i, signal in enumerate(signals):
                print(f"[{i}] {signal.get('symbol')} {signal.get('side')} - {signal.get('description')}")
            print("\nRun with: python run_fibonacci_strategy.py --index <signal_index>")
        return
    
    # Run strategy
    run_fibonacci_strategy(args.index, args.file)

if __name__ == "__main__":
    main()