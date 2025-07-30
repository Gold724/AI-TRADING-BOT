import os
import sys
import json
import time
import random
import argparse
from datetime import datetime

# Fibonacci levels and take profit percentages
FIB_LEVELS = [0.382, 0.5, 0.618, 0.705, 0.786]
TP_PERCENTAGES = [0.3, 0.2, 0.2, 0.2, 0.1]  # Partial exits

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

def save_trade_history(trades, file_path="logs/simulated_fibonacci_trades.json"):
    """
    Save trade history to a JSON file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(trades, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving trade history: {e}")
        return False

def calculate_fib_targets(fib_low, fib_high, is_long):
    """
    Calculate Fibonacci targets based on the range
    """
    fib_targets = []
    for level in FIB_LEVELS:
        target = fib_low + (fib_high - fib_low) * level if is_long else fib_high - (fib_high - fib_low) * level
        fib_targets.append(round(target, 2))
    return fib_targets

def get_simulated_price(entry, fib_low, fib_high, is_long, time_elapsed, volatility=0.2):
    """
    Simulate price movement based on time elapsed and volatility
    """
    # Calculate price range
    price_range = abs(fib_high - fib_low)
    
    # Calculate price movement based on time elapsed and volatility
    max_movement = price_range * volatility * (time_elapsed / 100)
    movement = random.uniform(-max_movement, max_movement * (1.5 if is_long else -1.5))
    
    # Calculate current price
    current_price = entry + movement
    
    # Add some noise
    noise = random.uniform(-price_range * 0.01, price_range * 0.01)
    current_price += noise
    
    return round(current_price, 2)

def price_rejects_and_retests(current_price, target, is_long, probability=0.3):
    """
    Simulate price rejection and retest based on probability
    """
    return random.random() < probability

def simulate_fibonacci_strategy(signal, max_time=300, interval=5, output_file="logs/simulated_fibonacci_trades.json"):
    """
    Simulate the Fibonacci strategy with a sample signal
    """
    # Extract parameters
    symbol = signal.get("symbol")
    side = signal.get("side")
    quantity = signal.get("quantity")
    entry = signal.get("entry")
    fib_low = signal.get("fib_low")
    fib_high = signal.get("fib_high")
    stop_loss = signal.get("stopLoss")
    take_profit = signal.get("takeProfit")
    
    # Determine direction
    is_long = side.lower() == "buy"
    direction = signal.get("direction", "long" if is_long else "short")
    
    # Calculate Fibonacci targets
    fib_targets = calculate_fib_targets(fib_low, fib_high, is_long)
    
    print(f"\n🧠 Simulating Fibonacci Strategy for {symbol} {side}")
    print(f"📊 Entry: {entry}, Fib Low: {fib_low}, Fib High: {fib_high}")
    print(f"🎯 Fibonacci Targets: {fib_targets}")
    print(f"📈 Take Profit Percentages: {TP_PERCENTAGES}")
    
    # Initialize simulation
    start_time = time.time()
    elapsed_time = 0
    executed_levels = [False] * len(fib_targets)
    remaining_quantity = quantity
    trade_history = []
    reentry_count = 0
    
    # Log initial trade
    initial_trade = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": entry,
        "action": "entry",
        "fib_level": "initial",
        "success": True
    }
    trade_history.append(initial_trade)
    print(f"\n⏱️ {elapsed_time}s: Initial {side} of {quantity} {symbol} at {entry}")
    
    # Simulation loop
    try:
        while elapsed_time < max_time and remaining_quantity > 0:
            # Update elapsed time
            elapsed_time = time.time() - start_time
            
            # Get simulated price
            current_price = get_simulated_price(entry, fib_low, fib_high, is_long, elapsed_time)
            
            # Check for stop loss
            if stop_loss and ((is_long and current_price <= stop_loss) or (not is_long and current_price >= stop_loss)):
                # Log stop loss
                stop_loss_trade = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "side": "sell" if is_long else "buy",
                    "quantity": remaining_quantity,
                    "price": stop_loss,
                    "action": "stop_loss",
                    "fib_level": "stop_loss",
                    "success": True
                }
                trade_history.append(stop_loss_trade)
                print(f"\n⏱️ {elapsed_time:.1f}s: ❌ Stop Loss triggered at {stop_loss}")
                remaining_quantity = 0
                break
            
            # Check for take profit
            if take_profit and ((is_long and current_price >= take_profit) or (not is_long and current_price <= take_profit)):
                # Log take profit
                take_profit_trade = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "side": "sell" if is_long else "buy",
                    "quantity": remaining_quantity,
                    "price": take_profit,
                    "action": "take_profit",
                    "fib_level": "take_profit",
                    "success": True
                }
                trade_history.append(take_profit_trade)
                print(f"\n⏱️ {elapsed_time:.1f}s: ✅ Take Profit triggered at {take_profit}")
                remaining_quantity = 0
                break
            
            # Check for Fibonacci targets
            for i, target in enumerate(fib_targets):
                if executed_levels[i]:
                    continue
                
                # Check if price reached target
                if (is_long and current_price >= target) or (not is_long and current_price <= target):
                    # Calculate partial quantity
                    partial_quantity = round(quantity * TP_PERCENTAGES[i], 2)
                    if partial_quantity > remaining_quantity:
                        partial_quantity = remaining_quantity
                    
                    # Log partial exit
                    partial_exit_trade = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "symbol": symbol,
                        "side": "sell" if is_long else "buy",
                        "quantity": partial_quantity,
                        "price": target,
                        "action": "partial_exit",
                        "fib_level": str(FIB_LEVELS[i]),
                        "success": True
                    }
                    trade_history.append(partial_exit_trade)
                    print(f"\n⏱️ {elapsed_time:.1f}s: 🔒 Partial exit of {partial_quantity} at Fib {FIB_LEVELS[i]} ({target})")
                    
                    # Update remaining quantity
                    remaining_quantity -= partial_quantity
                    executed_levels[i] = True
                    
                    # Check for reentry
                    if remaining_quantity > 0 and price_rejects_and_retests(current_price, target, is_long):
                        # Calculate reentry quantity
                        reentry_quantity = round(partial_quantity * 0.5, 2)
                        reentry_count += 1
                        
                        # Log reentry
                        reentry_trade = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "symbol": symbol,
                            "side": side,
                            "quantity": reentry_quantity,
                            "price": target,
                            "action": "reentry",
                            "fib_level": str(FIB_LEVELS[i]),
                            "success": True
                        }
                        trade_history.append(reentry_trade)
                        print(f"\n⏱️ {elapsed_time:.1f}s: ♻️ Reentry of {reentry_quantity} at Fib {FIB_LEVELS[i]} ({target})")
                        
                        # Update remaining quantity
                        remaining_quantity += reentry_quantity
            
            # Print current status every 10 seconds
            if int(elapsed_time) % 10 == 0 and int(elapsed_time) > 0:
                print(f"⏱️ {elapsed_time:.1f}s: 🔍 Current price: {current_price}, Remaining: {remaining_quantity}")
            
            # Sleep for the interval
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n⏹️ Simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
    finally:
        # Save trade history
        if save_trade_history(trade_history, output_file):
            print(f"\n📁 Trade history saved to: {output_file}")
        
        # Print summary
        print(f"\n📊 Simulation Summary:")
        print(f"  - Symbol: {symbol}")
        print(f"  - Side: {side}")
        print(f"  - Initial Quantity: {quantity}")
        print(f"  - Remaining Quantity: {remaining_quantity}")
        print(f"  - Executed Levels: {sum(executed_levels)} of {len(fib_targets)}")
        print(f"  - Reentry Count: {reentry_count}")
        print(f"  - Total Trades: {len(trade_history)}")
        print(f"  - Elapsed Time: {elapsed_time:.2f} seconds")
        
        return trade_history

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Simulate Fibonacci Strategy")
    parser.add_argument("--index", type=int, default=0, help="Index of the signal to use from the signals file")
    parser.add_argument("--file", type=str, default="sample_fibonacci_signals.json", help="Path to the signals file")
    parser.add_argument("--time", type=int, default=300, help="Maximum simulation time in seconds")
    parser.add_argument("--interval", type=int, default=5, help="Simulation interval in seconds")
    parser.add_argument("--output", type=str, default="logs/simulated_fibonacci_trades.json", help="Path to save the trade history")
    parser.add_argument("--list", action="store_true", help="List all available signals")
    
    args = parser.parse_args()
    
    # Load signals
    signals = load_signals(args.file)
    
    if not signals:
        print("No signals found. Please check the signals file.")
        return
    
    # List signals if requested
    if args.list:
        print(f"\nAvailable Signals ({len(signals)}):\n")
        for i, signal in enumerate(signals):
            print(f"[{i}] {signal.get('symbol')} {signal.get('side')} - {signal.get('description')}")
        print("\nRun with: python simulate_fibonacci_strategy.py --index <signal_index>")
        return
    
    # Validate signal index
    if args.index < 0 or args.index >= len(signals):
        print(f"Invalid signal index. Please choose an index between 0 and {len(signals)-1}")
        return
    
    # Get signal
    signal = signals[args.index]
    
    # Simulate strategy
    simulate_fibonacci_strategy(signal, args.time, args.interval, args.output)

if __name__ == "__main__":
    main()