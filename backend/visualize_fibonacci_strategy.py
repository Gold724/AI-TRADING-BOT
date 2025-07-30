import os
import sys
import json
import argparse
import matplotlib.pyplot as plt
import numpy as np
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

def parse_timestamp(timestamp):
    """
    Parse timestamp string to datetime object
    """
    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except:
        try:
            return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        except:
            return datetime.now()

def visualize_fibonacci_strategy(history_file="logs/fibonacci_trades.json", output_file=None):
    """
    Visualize the Fibonacci strategy results
    """
    # Load trade history
    trades = load_trade_history(history_file)
    
    if not trades:
        print("No trades found. Please check the trade history file.")
        return
    
    print(f"\n📊 Visualizing Fibonacci strategy results...")
    print(f"📁 Trade history file: {history_file}")
    print(f"📈 Total trades: {len(trades)}")
    
    # Extract data
    timestamps = [parse_timestamp(trade.get("timestamp", "")) for trade in trades]
    symbols = [trade.get("symbol", "Unknown") for trade in trades]
    sides = [trade.get("side", "Unknown") for trade in trades]
    fib_levels = [trade.get("fib_level", "Unknown") for trade in trades]
    actions = [trade.get("action", "trade") for trade in trades]
    successes = [trade.get("success", False) for trade in trades]
    
    # Count trades by symbol
    symbol_counts = {}
    for symbol in symbols:
        if symbol in symbol_counts:
            symbol_counts[symbol] += 1
        else:
            symbol_counts[symbol] = 1
    
    # Count trades by side
    side_counts = {}
    for side in sides:
        if side in side_counts:
            side_counts[side] += 1
        else:
            side_counts[side] = 1
    
    # Count trades by action
    action_counts = {}
    for action in actions:
        if action in action_counts:
            action_counts[action] += 1
        else:
            action_counts[action] = 1
    
    # Count trades by Fibonacci level
    fib_level_counts = {}
    for level in fib_levels:
        if level != "Unknown":
            if level in fib_level_counts:
                fib_level_counts[level] += 1
            else:
                fib_level_counts[level] = 1
    
    # Count successful trades
    success_count = sum(successes)
    fail_count = len(successes) - success_count
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle("Fibonacci Strategy Visualization", fontsize=16)
    
    # Plot 1: Trades by Symbol
    ax1 = plt.subplot(2, 3, 1)
    symbols_sorted = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
    ax1.bar([x[0] for x in symbols_sorted], [x[1] for x in symbols_sorted])
    ax1.set_title("Trades by Symbol")
    ax1.set_xlabel("Symbol")
    ax1.set_ylabel("Count")
    plt.xticks(rotation=45)
    
    # Plot 2: Trades by Side
    ax2 = plt.subplot(2, 3, 2)
    sides_sorted = sorted(side_counts.items(), key=lambda x: x[1], reverse=True)
    ax2.bar([x[0] for x in sides_sorted], [x[1] for x in sides_sorted], color=['green' if x[0].lower() == 'buy' else 'red' for x in sides_sorted])
    ax2.set_title("Trades by Side")
    ax2.set_xlabel("Side")
    ax2.set_ylabel("Count")
    
    # Plot 3: Trades by Action
    ax3 = plt.subplot(2, 3, 3)
    actions_sorted = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
    ax3.bar([x[0] for x in actions_sorted], [x[1] for x in actions_sorted])
    ax3.set_title("Trades by Action")
    ax3.set_xlabel("Action")
    ax3.set_ylabel("Count")
    
    # Plot 4: Trades by Fibonacci Level
    ax4 = plt.subplot(2, 3, 4)
    if fib_level_counts:
        fib_levels_sorted = sorted(fib_level_counts.items(), key=lambda x: float(x[0]) if x[0] != "Unknown" else 0)
        ax4.bar([x[0] for x in fib_levels_sorted], [x[1] for x in fib_levels_sorted])
        ax4.set_title("Trades by Fibonacci Level")
        ax4.set_xlabel("Fibonacci Level")
        ax4.set_ylabel("Count")
    else:
        ax4.text(0.5, 0.5, "No Fibonacci Level Data", horizontalalignment='center', verticalalignment='center')
        ax4.set_title("Trades by Fibonacci Level")
    
    # Plot 5: Success vs Failure
    ax5 = plt.subplot(2, 3, 5)
    ax5.pie([success_count, fail_count], labels=["Success", "Failure"], autopct='%1.1f%%', colors=['green', 'red'])
    ax5.set_title("Trade Success Rate")
    
    # Plot 6: Trades Over Time
    ax6 = plt.subplot(2, 3, 6)
    if timestamps:
        # Create a timeline of trades
        ax6.plot(timestamps, range(len(timestamps)), marker='o')
        ax6.set_title("Trades Over Time")
        ax6.set_xlabel("Time")
        ax6.set_ylabel("Cumulative Trades")
        plt.xticks(rotation=45)
    else:
        ax6.text(0.5, 0.5, "No Timestamp Data", horizontalalignment='center', verticalalignment='center')
        ax6.set_title("Trades Over Time")
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save or show the figure
    if output_file:
        plt.savefig(output_file)
        print(f"📄 Visualization saved to: {output_file}")
    else:
        plt.show()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Visualize Fibonacci Strategy Results")
    parser.add_argument("--file", type=str, default="logs/fibonacci_trades.json", help="Path to the trade history file")
    parser.add_argument("--output", type=str, help="Path to save the visualization (optional)")
    
    args = parser.parse_args()
    
    # Visualize strategy
    visualize_fibonacci_strategy(args.file, args.output)

if __name__ == "__main__":
    main()