import os
import sys
import json
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

def load_trade_history(file_path):
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

def save_report(report, file_path):
    """
    Save report to a file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, 'w') as f:
            f.write(report)
        return True
    except Exception as e:
        print(f"Error saving report: {e}")
        return False

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

def calculate_pnl(trades):
    """
    Calculate profit and loss from trades
    """
    pnl = 0
    positions = {}
    
    for trade in trades:
        symbol = trade.get("symbol")
        side = trade.get("side")
        quantity = trade.get("quantity", 0)
        price = trade.get("price", 0)
        action = trade.get("action", "trade")
        
        # Skip trades without price
        if price == 0:
            continue
        
        # Initialize position if not exists
        if symbol not in positions:
            positions[symbol] = {
                "long": {"quantity": 0, "value": 0},
                "short": {"quantity": 0, "value": 0}
            }
        
        # Update position based on trade
        position_type = "long" if side.lower() == "buy" else "short"
        opposite_type = "short" if position_type == "long" else "long"
        
        if action == "entry" or action == "reentry":
            # Add to position
            current_quantity = positions[symbol][position_type]["quantity"]
            current_value = positions[symbol][position_type]["value"]
            
            new_quantity = current_quantity + quantity
            new_value = current_value + (quantity * price)
            
            positions[symbol][position_type]["quantity"] = new_quantity
            positions[symbol][position_type]["value"] = new_value
        
        elif action == "partial_exit" or action == "take_profit" or action == "stop_loss":
            # Remove from position and calculate PnL
            if positions[symbol][opposite_type]["quantity"] > 0:
                # Close opposite position
                exit_quantity = min(quantity, positions[symbol][opposite_type]["quantity"])
                avg_entry = positions[symbol][opposite_type]["value"] / positions[symbol][opposite_type]["quantity"]
                
                # Calculate PnL
                if opposite_type == "long":
                    trade_pnl = (price - avg_entry) * exit_quantity
                else:
                    trade_pnl = (avg_entry - price) * exit_quantity
                
                # Update position
                positions[symbol][opposite_type]["quantity"] -= exit_quantity
                positions[symbol][opposite_type]["value"] -= (avg_entry * exit_quantity)
                
                # Update total PnL
                pnl += trade_pnl
    
    return pnl

def generate_fibonacci_report(trade_history_file, output_file=None, include_visualization=True):
    """
    Generate a report of the Fibonacci strategy performance
    """
    # Load trade history
    trades = load_trade_history(trade_history_file)
    
    if not trades:
        print("No trades found. Please check the trade history file.")
        return False
    
    # Extract data
    timestamps = [parse_timestamp(trade.get("timestamp", "")) for trade in trades]
    symbols = [trade.get("symbol", "Unknown") for trade in trades]
    sides = [trade.get("side", "Unknown") for trade in trades]
    quantities = [trade.get("quantity", 0) for trade in trades]
    prices = [trade.get("price", 0) for trade in trades]
    actions = [trade.get("action", "trade") for trade in trades]
    fib_levels = [trade.get("fib_level", "Unknown") for trade in trades]
    successes = [trade.get("success", False) for trade in trades]
    
    # Calculate statistics
    total_trades = len(trades)
    unique_symbols = len(set(symbols))
    buy_trades = sides.count("buy")
    sell_trades = sides.count("sell")
    entry_trades = actions.count("entry")
    reentry_trades = actions.count("reentry")
    partial_exit_trades = actions.count("partial_exit")
    take_profit_trades = actions.count("take_profit")
    stop_loss_trades = actions.count("stop_loss")
    success_rate = sum(successes) / total_trades if total_trades > 0 else 0
    
    # Calculate PnL
    pnl = calculate_pnl(trades)
    
    # Generate report
    report = f"# Fibonacci Strategy Performance Report\n\n"
    report += f"## Overview\n\n"
    report += f"- **Report Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"- **Trade History File:** {trade_history_file}\n"
    report += f"- **Total Trades:** {total_trades}\n"
    report += f"- **Unique Symbols:** {unique_symbols}\n"
    report += f"- **Success Rate:** {success_rate * 100:.2f}%\n"
    report += f"- **Estimated PnL:** {pnl:.2f}\n\n"
    
    report += f"## Trade Statistics\n\n"
    report += f"- **Buy Trades:** {buy_trades}\n"
    report += f"- **Sell Trades:** {sell_trades}\n"
    report += f"- **Entry Trades:** {entry_trades}\n"
    report += f"- **Reentry Trades:** {reentry_trades}\n"
    report += f"- **Partial Exit Trades:** {partial_exit_trades}\n"
    report += f"- **Take Profit Trades:** {take_profit_trades}\n"
    report += f"- **Stop Loss Trades:** {stop_loss_trades}\n\n"
    
    # Fibonacci level statistics
    report += f"## Fibonacci Level Statistics\n\n"
    fib_level_counts = {}
    for level in fib_levels:
        if level != "Unknown":
            if level in fib_level_counts:
                fib_level_counts[level] += 1
            else:
                fib_level_counts[level] = 1
    
    if fib_level_counts:
        for level, count in sorted(fib_level_counts.items()):
            report += f"- **Level {level}:** {count} trades ({count / total_trades * 100:.2f}%)\n"
    else:
        report += f"- No Fibonacci level data available\n"
    
    report += f"\n## Symbol Statistics\n\n"
    symbol_counts = {}
    for symbol in symbols:
        if symbol in symbol_counts:
            symbol_counts[symbol] += 1
        else:
            symbol_counts[symbol] = 1
    
    for symbol, count in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{symbol}:** {count} trades ({count / total_trades * 100:.2f}%)\n"
    
    # Generate visualization if requested
    if include_visualization:
        # Create figure with subplots
        fig = plt.figure(figsize=(15, 10))
        fig.suptitle("Fibonacci Strategy Performance", fontsize=16)
        
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
        side_counts = {"buy": buy_trades, "sell": sell_trades}
        sides_sorted = sorted(side_counts.items(), key=lambda x: x[1], reverse=True)
        ax2.bar([x[0] for x in sides_sorted], [x[1] for x in sides_sorted], color=['green' if x[0].lower() == 'buy' else 'red' for x in sides_sorted])
        ax2.set_title("Trades by Side")
        ax2.set_xlabel("Side")
        ax2.set_ylabel("Count")
        
        # Plot 3: Trades by Action
        ax3 = plt.subplot(2, 3, 3)
        action_counts = {
            "entry": entry_trades,
            "reentry": reentry_trades,
            "partial_exit": partial_exit_trades,
            "take_profit": take_profit_trades,
            "stop_loss": stop_loss_trades
        }
        actions_sorted = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        ax3.bar([x[0] for x in actions_sorted], [x[1] for x in actions_sorted])
        ax3.set_title("Trades by Action")
        ax3.set_xlabel("Action")
        ax3.set_ylabel("Count")
        plt.xticks(rotation=45)
        
        # Plot 4: Trades by Fibonacci Level
        ax4 = plt.subplot(2, 3, 4)
        if fib_level_counts:
            fib_levels_sorted = sorted(fib_level_counts.items(), key=lambda x: float(x[0]) if x[0] != "Unknown" and x[0] != "initial" and x[0] != "stop_loss" and x[0] != "take_profit" else 0)
            ax4.bar([x[0] for x in fib_levels_sorted], [x[1] for x in fib_levels_sorted])
            ax4.set_title("Trades by Fibonacci Level")
            ax4.set_xlabel("Fibonacci Level")
            ax4.set_ylabel("Count")
        else:
            ax4.text(0.5, 0.5, "No Fibonacci Level Data", horizontalalignment='center', verticalalignment='center')
            ax4.set_title("Trades by Fibonacci Level")
        
        # Plot 5: Success vs Failure
        ax5 = plt.subplot(2, 3, 5)
        success_count = sum(successes)
        fail_count = total_trades - success_count
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
        
        # Save visualization
        if output_file:
            visualization_file = output_file.replace(".md", ".png")
            plt.savefig(visualization_file)
            report += f"\n## Visualization\n\n![Fibonacci Strategy Visualization]({os.path.basename(visualization_file)})\n"
            print(f"📊 Visualization saved to: {visualization_file}")
        else:
            plt.show()
    
    # Add trade list
    report += f"\n## Trade List\n\n"
    report += f"| # | Timestamp | Symbol | Side | Quantity | Price | Action | Fib Level | Success |\n"
    report += f"|---|-----------|--------|------|----------|-------|--------|-----------|---------|\n"
    
    for i, trade in enumerate(trades):
        timestamp = trade.get("timestamp", "")
        symbol = trade.get("symbol", "Unknown")
        side = trade.get("side", "Unknown")
        quantity = trade.get("quantity", 0)
        price = trade.get("price", 0)
        action = trade.get("action", "trade")
        fib_level = trade.get("fib_level", "Unknown")
        success = "✅" if trade.get("success", False) else "❌"
        
        report += f"| {i+1} | {timestamp} | {symbol} | {side} | {quantity} | {price} | {action} | {fib_level} | {success} |\n"
    
    # Save report
    if output_file:
        if save_report(report, output_file):
            print(f"📄 Report saved to: {output_file}")
            return True
        else:
            return False
    else:
        print(report)
        return True

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate Fibonacci Strategy Report")
    parser.add_argument("--file", type=str, default="logs/fibonacci_trades.json", help="Path to the trade history file")
    parser.add_argument("--output", type=str, help="Path to save the report (optional)")
    parser.add_argument("--no-viz", action="store_true", help="Disable visualization")
    
    args = parser.parse_args()
    
    # Generate default output file if not provided
    output_file = args.output
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"reports/fibonacci_report_{timestamp}.md"
    
    # Generate report
    generate_fibonacci_report(args.file, output_file, not args.no_viz)

if __name__ == "__main__":
    main()