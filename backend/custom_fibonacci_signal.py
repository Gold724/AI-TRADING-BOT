import os
import sys
import json
import argparse
from utils.executor_fibonacci import FibonacciExecutor

def run_custom_fibonacci_signal(symbol, side, quantity, entry, fib_low, fib_high, stop_loss=None, take_profit=None, stealth_level=2):
    """
    Run the Fibonacci strategy with a custom signal
    """
    # Create signal dictionary
    signal = {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "entry": entry,
        "fib_low": fib_low,
        "fib_high": fib_high,
        "direction": "long" if side.lower() == "buy" else "short"
    }
    
    print(f"\n🧠 Running Fibonacci Strategy with custom signal: {json.dumps(signal, indent=2)}")
    
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
    success = executor.execute_trade()
    
    # Print result
    if success:
        print("\n✅ Fibonacci strategy executed successfully!")
    else:
        print("\n❌ Fibonacci strategy execution failed!")
    
    return success

def save_custom_signal(signal, file_path="custom_fibonacci_signals.json"):
    """
    Save custom signal to a JSON file
    """
    # Load existing signals if file exists
    signals = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                signals = json.load(f)
        except:
            signals = []
    
    # Add new signal
    signals.append(signal)
    
    # Save signals
    try:
        with open(file_path, 'w') as f:
            json.dump(signals, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving custom signal: {e}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Fibonacci Strategy with a custom signal")
    parser.add_argument("--symbol", type=str, required=True, help="Trading symbol")
    parser.add_argument("--side", type=str, required=True, choices=["buy", "sell"], help="Trade side (buy/sell)")
    parser.add_argument("--quantity", type=float, required=True, help="Trade quantity")
    parser.add_argument("--entry", type=float, required=True, help="Entry price")
    parser.add_argument("--fib_low", type=float, required=True, help="Fibonacci low price")
    parser.add_argument("--fib_high", type=float, required=True, help="Fibonacci high price")
    parser.add_argument("--stop_loss", type=float, help="Stop loss price")
    parser.add_argument("--take_profit", type=float, help="Take profit price")
    parser.add_argument("--stealth_level", type=int, default=2, choices=[1, 2, 3], help="Stealth level (1-3)")
    parser.add_argument("--save", action="store_true", help="Save custom signal to file")
    parser.add_argument("--description", type=str, help="Description of the custom signal")
    
    args = parser.parse_args()
    
    # Create signal dictionary
    signal = {
        "symbol": args.symbol,
        "side": args.side,
        "quantity": args.quantity,
        "entry": args.entry,
        "fib_low": args.fib_low,
        "fib_high": args.fib_high,
        "direction": "long" if args.side.lower() == "buy" else "short",
        "stealth_level": args.stealth_level
    }
    
    # Add optional parameters
    if args.stop_loss is not None:
        signal["stopLoss"] = args.stop_loss
    
    if args.take_profit is not None:
        signal["takeProfit"] = args.take_profit
    
    if args.description is not None:
        signal["description"] = args.description
    else:
        signal["description"] = f"{args.symbol} {args.side.upper()} at {args.entry} with Fibonacci range {args.fib_low}-{args.fib_high}"
    
    # Save signal if requested
    if args.save:
        if save_custom_signal(signal):
            print(f"\n💾 Custom signal saved to custom_fibonacci_signals.json")
    
    # Run strategy
    run_custom_fibonacci_signal(
        symbol=args.symbol,
        side=args.side,
        quantity=args.quantity,
        entry=args.entry,
        fib_low=args.fib_low,
        fib_high=args.fib_high,
        stop_loss=args.stop_loss,
        take_profit=args.take_profit,
        stealth_level=args.stealth_level
    )

if __name__ == "__main__":
    main()