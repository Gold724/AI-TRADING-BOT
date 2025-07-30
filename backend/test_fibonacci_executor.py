import os
import sys
import json
import argparse
from utils.executor_fibonacci import FibonacciExecutor

def test_fibonacci_executor(symbol, side, quantity, entry, fib_low, fib_high, stop_loss=None, take_profit=None, stealth_level=2):
    """
    Test the FibonacciExecutor with a sample signal
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
    
    print(f"\nTesting FibonacciExecutor with signal: {json.dumps(signal, indent=2)}")
    
    # Create executor
    executor = FibonacciExecutor(
        signal=signal,
        stopLoss=stop_loss,
        takeProfit=take_profit,
        stealth_level=stealth_level
    )
    
    # Calculate and display Fibonacci targets
    print(f"\nFibonacci Levels: {executor.fib_levels}")
    print(f"Fibonacci Targets: {executor.fib_targets}")
    print(f"Take Profit Percentages: {executor.tp_percentages}")
    
    # Execute trade
    print("\nExecuting Fibonacci strategy...")
    success = executor.execute_trade()
    
    # Print result
    if success:
        print("\n✅ Fibonacci strategy executed successfully!")
    else:
        print("\n❌ Fibonacci strategy execution failed!")
    
    return success

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test FibonacciExecutor with a sample signal")
    parser.add_argument("--symbol", type=str, default="EURUSD", help="Trading symbol")
    parser.add_argument("--side", type=str, default="buy", choices=["buy", "sell"], help="Trade side (buy/sell)")
    parser.add_argument("--quantity", type=float, default=0.1, help="Trade quantity")
    parser.add_argument("--entry", type=float, default=1.0850, help="Entry price")
    parser.add_argument("--fib_low", type=float, default=1.0800, help="Fibonacci low price")
    parser.add_argument("--fib_high", type=float, default=1.0900, help="Fibonacci high price")
    parser.add_argument("--stop_loss", type=float, help="Stop loss price")
    parser.add_argument("--take_profit", type=float, help="Take profit price")
    parser.add_argument("--stealth_level", type=int, default=2, choices=[1, 2, 3], help="Stealth level (1-3)")
    
    args = parser.parse_args()
    
    # Test executor
    test_fibonacci_executor(
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