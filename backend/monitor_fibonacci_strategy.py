import os
import sys
import json
import time
import argparse
from datetime import datetime

def load_trade_history(file_path="logs/fibonacci_trades.json"):
    """
    Load trade history from the logs file
    """
    try:
        with open(file_path, 'r') as f:
            history = json.load(f)
        return history
    except FileNotFoundError:
        print(f"Trade history file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Invalid JSON in trade history file: {file_path}")
        return []
    except Exception as e:
        print(f"Error loading trade history: {e}")
        return []

def monitor_fibonacci_strategy(interval=10, max_time=3600, history_file="logs/fibonacci_trades.json"):
    """
    Monitor the Fibonacci strategy execution by watching the trade history file
    """
    print(f"\n🔍 Monitoring Fibonacci strategy execution...")
    print(f"📁 Watching file: {history_file}")
    print(f"⏱️ Checking every {interval} seconds for {max_time} seconds")
    print("\nPress Ctrl+C to stop monitoring\n")
    
    start_time = time.time()
    last_trade_count = 0
    last_check_time = start_time
    
    try:
        while time.time() - start_time < max_time:
            # Load trade history
            trades = load_trade_history(history_file)
            current_time = time.time()
            
            # Check for new trades
            if len(trades) > last_trade_count:
                new_trades = trades[last_trade_count:]
                for trade in new_trades:
                    # Format trade information
                    timestamp = trade.get("timestamp", "Unknown")
                    symbol = trade.get("symbol", "Unknown")
                    side = trade.get("side", "Unknown")
                    quantity = trade.get("quantity", "Unknown")
                    success = trade.get("success", False)
                    fib_level = trade.get("fib_level", "Unknown")
                    action = trade.get("action", "trade")
                    
                    # Print trade information
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] New {action}: {symbol} {side} {quantity}")
                    print(f"  - Fibonacci Level: {fib_level}")
                    print(f"  - Status: {'✅ Success' if success else '❌ Failed'}")
                    print(f"  - Timestamp: {timestamp}")
                    print()
                
                # Update last trade count
                last_trade_count = len(trades)
            else:
                # Print status update every minute
                if current_time - last_check_time >= 60:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring... ({len(trades)} trades so far)")
                    last_check_time = current_time
            
            # Sleep for the specified interval
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
    finally:
        # Print summary
        elapsed_time = time.time() - start_time
        trades = load_trade_history(history_file)
        print(f"\n📊 Monitoring Summary:")
        print(f"  - Elapsed Time: {elapsed_time:.2f} seconds")
        print(f"  - Total Trades: {len(trades)}")
        print(f"  - Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Monitor Fibonacci Strategy Execution")
    parser.add_argument("--interval", type=int, default=10, help="Check interval in seconds")
    parser.add_argument("--time", type=int, default=3600, help="Maximum monitoring time in seconds")
    parser.add_argument("--file", type=str, default="logs/fibonacci_trades.json", help="Path to the trade history file")
    
    args = parser.parse_args()
    
    # Monitor strategy
    monitor_fibonacci_strategy(args.interval, args.time, args.file)

if __name__ == "__main__":
    main()