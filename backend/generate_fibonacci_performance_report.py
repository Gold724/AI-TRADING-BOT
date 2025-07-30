#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fibonacci Strategy Performance Report Generator

This script analyzes the Fibonacci strategy trade history and generates a comprehensive
performance report including metrics, visualizations, and insights.

Usage:
    python generate_fibonacci_performance_report.py [--history_file HISTORY_FILE] [--output_dir OUTPUT_DIR]
"""

import os
import json
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import defaultdict, Counter


def load_trade_history(history_file):
    """Load trade history from JSON file"""
    if not os.path.exists(history_file):
        print(f"Error: History file '{history_file}' not found.")
        return []
    
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
        return history
    except Exception as e:
        print(f"Error loading history file: {e}")
        return []


def parse_timestamps(history):
    """Convert timestamp strings to datetime objects"""
    for trade in history:
        if "timestamp" in trade:
            try:
                trade["timestamp"] = datetime.fromisoformat(trade["timestamp"])
            except ValueError:
                # Handle timestamps without timezone info
                try:
                    trade["timestamp"] = datetime.fromisoformat(trade["timestamp"].split("+")[0])
                except:
                    print(f"Warning: Could not parse timestamp {trade['timestamp']}")
    return history


def create_trades_dataframe(history):
    """Convert trade history to pandas DataFrame for analysis"""
    if not history:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(history)
    
    # Ensure timestamp is datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Add derived columns
    if "price" in df.columns and "entry" in df.columns:
        # Calculate profit/loss percentage
        df["pl_pct"] = np.where(
            df["side"] == "long",
            (df["price"] - df["entry"]) / df["entry"] * 100,
            (df["entry"] - df["price"]) / df["entry"] * 100
        )
        
        # Calculate profit/loss amount (simplified)
        df["pl_amount"] = df["pl_pct"] * df["quantity"]
    
    return df


def calculate_position_metrics(df):
    """Calculate metrics for each position"""
    if df.empty:
        return pd.DataFrame()
    
    # Group trades by symbol and entry timestamp to identify positions
    positions = []
    
    # Get unique symbols
    symbols = df["symbol"].unique()
    
    for symbol in symbols:
        symbol_df = df[df["symbol"] == symbol].sort_values("timestamp")
        
        # Track open positions
        open_positions = []
        
        for _, trade in symbol_df.iterrows():
            if trade["action"] == "entry":
                # New position
                position = {
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "entry_time": trade["timestamp"],
                    "entry_price": trade["price"],
                    "initial_quantity": trade["quantity"],
                    "remaining_quantity": trade["quantity"],
                    "trades": [trade],
                    "status": "open",
                    "exit_time": None,
                    "exit_price": None,
                    "pl_pct": 0,
                    "pl_amount": 0,
                    "duration": None,
                    "max_favorable_excursion": 0,
                    "max_adverse_excursion": 0,
                    "fib_levels_hit": set([trade["fib_level"]]),
                }
                open_positions.append(position)
            
            elif trade["action"] == "re_entry":
                # Find the matching open position
                for pos in open_positions:
                    if pos["symbol"] == trade["symbol"] and pos["side"] == trade["side"] and pos["status"] == "open":
                        pos["remaining_quantity"] += trade["quantity"]
                        pos["trades"].append(trade)
                        pos["fib_levels_hit"].add(trade["fib_level"])
                        break
            
            elif trade["action"] in ["partial_exit", "take_profit", "stop_loss"]:
                # Find the matching open position
                for pos in open_positions:
                    if pos["symbol"] == trade["symbol"] and pos["side"] == trade["side"] and pos["status"] == "open":
                        pos["remaining_quantity"] -= trade["quantity"]
                        pos["trades"].append(trade)
                        pos["fib_levels_hit"].add(trade["fib_level"])
                        
                        # Calculate P/L for this exit
                        if pos["side"] == "long":
                            pl_pct = (trade["price"] - pos["entry_price"]) / pos["entry_price"] * 100
                        else:  # short
                            pl_pct = (pos["entry_price"] - trade["price"]) / pos["entry_price"] * 100
                        
                        pl_amount = pl_pct * trade["quantity"]
                        pos["pl_pct"] = (pos["pl_pct"] * (pos["initial_quantity"] - pos["remaining_quantity"] - trade["quantity"]) + pl_pct * trade["quantity"]) / (pos["initial_quantity"] - pos["remaining_quantity"])
                        pos["pl_amount"] += pl_amount
                        
                        # Update max excursions
                        pos["max_favorable_excursion"] = max(pos["max_favorable_excursion"], pl_pct if pl_pct > 0 else 0)
                        pos["max_adverse_excursion"] = min(pos["max_adverse_excursion"], pl_pct if pl_pct < 0 else 0)
                        
                        # Check if position is fully closed
                        if pos["remaining_quantity"] <= 0:
                            pos["status"] = "closed"
                            pos["exit_time"] = trade["timestamp"]
                            pos["exit_price"] = trade["price"]
                            pos["duration"] = (pos["exit_time"] - pos["entry_time"]).total_seconds() / 3600  # hours
                            positions.append(pos)
                            open_positions.remove(pos)
                        break
        
        # Add any remaining open positions
        positions.extend(open_positions)
    
    # Convert to DataFrame
    if positions:
        positions_df = pd.DataFrame(positions)
        positions_df["fib_levels_hit"] = positions_df["fib_levels_hit"].apply(lambda x: ", ".join(map(str, x)))
        return positions_df
    else:
        return pd.DataFrame()


def generate_summary_metrics(df, positions_df):
    """Generate summary metrics for the performance report"""
    metrics = {}
    
    if df.empty:
        return metrics
    
    # Basic trade metrics
    metrics["total_trades"] = len(df)
    metrics["successful_trades"] = len(df[df["status"] == "success"])
    metrics["success_rate"] = metrics["successful_trades"] / metrics["total_trades"] * 100 if metrics["total_trades"] > 0 else 0
    
    # Symbol metrics
    metrics["total_symbols"] = df["symbol"].nunique()
    metrics["symbols"] = df["symbol"].unique().tolist()
    symbol_counts = df["symbol"].value_counts()
    metrics["most_traded_symbol"] = symbol_counts.index[0] if not symbol_counts.empty else "None"
    metrics["most_traded_symbol_count"] = symbol_counts.iloc[0] if not symbol_counts.empty else 0
    
    # Side metrics
    metrics["long_trades"] = len(df[df["side"] == "long"])
    metrics["short_trades"] = len(df[df["side"] == "short"])
    
    # Action metrics
    action_counts = df["action"].value_counts()
    metrics["entry_count"] = action_counts.get("entry", 0)
    metrics["re_entry_count"] = action_counts.get("re_entry", 0)
    metrics["partial_exit_count"] = action_counts.get("partial_exit", 0)
    metrics["take_profit_count"] = action_counts.get("take_profit", 0)
    metrics["stop_loss_count"] = action_counts.get("stop_loss", 0)
    
    # Fibonacci level metrics
    fib_level_counts = df["fib_level"].value_counts()
    metrics["most_common_fib_level"] = fib_level_counts.index[0] if not fib_level_counts.empty else 0
    metrics["most_common_fib_level_count"] = fib_level_counts.iloc[0] if not fib_level_counts.empty else 0
    
    # Calculate average Fibonacci level
    metrics["avg_fib_level"] = df["fib_level"].mean() if "fib_level" in df.columns else 0
    
    # Position metrics
    if not positions_df.empty:
        metrics["total_positions"] = len(positions_df)
        metrics["closed_positions"] = len(positions_df[positions_df["status"] == "closed"])
        metrics["open_positions"] = len(positions_df[positions_df["status"] == "open"])
        
        # P/L metrics for closed positions
        closed_positions = positions_df[positions_df["status"] == "closed"]
        if not closed_positions.empty:
            metrics["avg_position_pl_pct"] = closed_positions["pl_pct"].mean()
            metrics["total_pl_amount"] = closed_positions["pl_amount"].sum()
            metrics["profitable_positions"] = len(closed_positions[closed_positions["pl_amount"] > 0])
            metrics["profit_factor"] = (
                closed_positions[closed_positions["pl_amount"] > 0]["pl_amount"].sum() / 
                abs(closed_positions[closed_positions["pl_amount"] < 0]["pl_amount"].sum())
                if abs(closed_positions[closed_positions["pl_amount"] < 0]["pl_amount"].sum()) > 0 else float('inf')
            )
            metrics["avg_duration_hours"] = closed_positions["duration"].mean()
            metrics["max_consecutive_wins"] = max_consecutive(closed_positions.sort_values("exit_time")["pl_amount"] > 0)
            metrics["max_consecutive_losses"] = max_consecutive(closed_positions.sort_values("exit_time")["pl_amount"] < 0)
    
    return metrics


def max_consecutive(series):
    """Calculate maximum consecutive True values in a series"""
    if series.empty:
        return 0
    
    max_count = 0
    current_count = 0
    
    for value in series:
        if value:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 0
    
    return max_count


def plot_trade_distribution(df, output_dir):
    """Plot trade distribution by symbol, side, and action"""
    if df.empty:
        return
    
    plt.figure(figsize=(12, 8))
    
    # Plot trade count by symbol
    plt.subplot(2, 2, 1)
    symbol_counts = df["symbol"].value_counts()
    sns.barplot(x=symbol_counts.index, y=symbol_counts.values)
    plt.title("Trade Count by Symbol")
    plt.xticks(rotation=45)
    plt.ylabel("Count")
    
    # Plot trade count by side
    plt.subplot(2, 2, 2)
    side_counts = df["side"].value_counts()
    sns.barplot(x=side_counts.index, y=side_counts.values)
    plt.title("Trade Count by Side")
    plt.ylabel("Count")
    
    # Plot trade count by action
    plt.subplot(2, 2, 3)
    action_counts = df["action"].value_counts()
    sns.barplot(x=action_counts.index, y=action_counts.values)
    plt.title("Trade Count by Action")
    plt.xticks(rotation=45)
    plt.ylabel("Count")
    
    # Plot trade count by Fibonacci level
    plt.subplot(2, 2, 4)
    fib_level_counts = df["fib_level"].value_counts().sort_index()
    sns.barplot(x=fib_level_counts.index, y=fib_level_counts.values)
    plt.title("Trade Count by Fibonacci Level")
    plt.xlabel("Fibonacci Level")
    plt.ylabel("Count")
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "trade_distribution.png"))
    plt.close()


def plot_performance_metrics(positions_df, output_dir):
    """Plot performance metrics for closed positions"""
    if positions_df.empty:
        return
    
    closed_positions = positions_df[positions_df["status"] == "closed"]
    if closed_positions.empty:
        return
    
    plt.figure(figsize=(12, 10))
    
    # Plot P/L distribution
    plt.subplot(2, 2, 1)
    sns.histplot(closed_positions["pl_pct"], kde=True)
    plt.title("P/L Distribution (%)")
    plt.xlabel("P/L (%)")
    plt.ylabel("Count")
    
    # Plot P/L by symbol
    plt.subplot(2, 2, 2)
    symbol_pl = closed_positions.groupby("symbol")["pl_amount"].sum().sort_values()
    colors = ['g' if x > 0 else 'r' for x in symbol_pl.values]
    sns.barplot(x=symbol_pl.index, y=symbol_pl.values, palette=colors)
    plt.title("Total P/L by Symbol")
    plt.xticks(rotation=45)
    plt.ylabel("P/L Amount")
    
    # Plot P/L by side
    plt.subplot(2, 2, 3)
    side_pl = closed_positions.groupby("side")["pl_amount"].sum()
    colors = ['g' if x > 0 else 'r' for x in side_pl.values]
    sns.barplot(x=side_pl.index, y=side_pl.values, palette=colors)
    plt.title("Total P/L by Side")
    plt.ylabel("P/L Amount")
    
    # Plot cumulative P/L over time
    plt.subplot(2, 2, 4)
    closed_positions_sorted = closed_positions.sort_values("exit_time")
    cumulative_pl = closed_positions_sorted["pl_amount"].cumsum()
    plt.plot(closed_positions_sorted["exit_time"], cumulative_pl)
    plt.title("Cumulative P/L Over Time")
    plt.xlabel("Exit Time")
    plt.ylabel("Cumulative P/L")
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "performance_metrics.png"))
    plt.close()


def plot_fibonacci_level_analysis(df, output_dir):
    """Plot analysis of Fibonacci levels"""
    if df.empty:
        return
    
    plt.figure(figsize=(12, 10))
    
    # Plot success rate by Fibonacci level
    plt.subplot(2, 2, 1)
    fib_success = df.groupby("fib_level")["status"].apply(lambda x: (x == "success").mean() * 100).sort_index()
    sns.barplot(x=fib_success.index, y=fib_success.values)
    plt.title("Success Rate by Fibonacci Level")
    plt.xlabel("Fibonacci Level")
    plt.ylabel("Success Rate (%)")
    
    # Plot trade count by Fibonacci level and side
    plt.subplot(2, 2, 2)
    fib_side = pd.crosstab(df["fib_level"], df["side"])
    fib_side.plot(kind="bar", stacked=True)
    plt.title("Trade Count by Fibonacci Level and Side")
    plt.xlabel("Fibonacci Level")
    plt.ylabel("Count")
    plt.legend(title="Side")
    
    # Plot trade count by Fibonacci level and action
    plt.subplot(2, 2, 3)
    fib_action = pd.crosstab(df["fib_level"], df["action"])
    fib_action.plot(kind="bar", stacked=True)
    plt.title("Trade Count by Fibonacci Level and Action")
    plt.xlabel("Fibonacci Level")
    plt.ylabel("Count")
    plt.legend(title="Action")
    
    # Plot average P/L by Fibonacci level
    plt.subplot(2, 2, 4)
    if "pl_pct" in df.columns:
        fib_pl = df.groupby("fib_level")["pl_pct"].mean().sort_index()
        colors = ['g' if x > 0 else 'r' for x in fib_pl.values]
        sns.barplot(x=fib_pl.index, y=fib_pl.values, palette=colors)
        plt.title("Average P/L by Fibonacci Level")
        plt.xlabel("Fibonacci Level")
        plt.ylabel("Average P/L (%)")
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fibonacci_level_analysis.png"))
    plt.close()


def generate_html_report(metrics, output_dir):
    """Generate HTML report with metrics and charts"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fibonacci Strategy Performance Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .metrics-container {{ display: flex; flex-wrap: wrap; }}
            .metric-box {{ background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin: 10px; flex: 1; min-width: 200px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
            .metric-label {{ font-size: 14px; color: #7f8c8d; }}
            .positive {{ color: #2ecc71; }}
            .negative {{ color: #e74c3c; }}
            .chart-container {{ margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Fibonacci Strategy Performance Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>Summary Metrics</h2>
            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('total_trades', 0)}</div>
                    <div class="metric-label">Total Trades</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('successful_trades', 0)}</div>
                    <div class="metric-label">Successful Trades</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('success_rate', 0):.2f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('total_symbols', 0)}</div>
                    <div class="metric-label">Total Symbols</div>
                </div>
            </div>
            
            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('long_trades', 0)}</div>
                    <div class="metric-label">Long Trades</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('short_trades', 0)}</div>
                    <div class="metric-label">Short Trades</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('most_traded_symbol', 'None')}</div>
                    <div class="metric-label">Most Traded Symbol</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('avg_fib_level', 0):.3f}</div>
                    <div class="metric-label">Avg Fibonacci Level</div>
                </div>
            </div>
    """
    
    # Add position metrics if available
    if "total_positions" in metrics:
        pl_class = "positive" if metrics.get("total_pl_amount", 0) > 0 else "negative"
        html_content += f"""
            <h2>Position Metrics</h2>
            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('total_positions', 0)}</div>
                    <div class="metric-label">Total Positions</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('closed_positions', 0)}</div>
                    <div class="metric-label">Closed Positions</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('open_positions', 0)}</div>
                    <div class="metric-label">Open Positions</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value {pl_class}">{metrics.get('total_pl_amount', 0):.2f}</div>
                    <div class="metric-label">Total P/L</div>
                </div>
            </div>
            
            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('avg_position_pl_pct', 0):.2f}%</div>
                    <div class="metric-label">Avg Position P/L</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('profit_factor', 0):.2f}</div>
                    <div class="metric-label">Profit Factor</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('max_consecutive_wins', 0)}</div>
                    <div class="metric-label">Max Consecutive Wins</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('max_consecutive_losses', 0)}</div>
                    <div class="metric-label">Max Consecutive Losses</div>
                </div>
            </div>
        """
    
    # Add action metrics
    html_content += f"""
            <h2>Action Metrics</h2>
            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('entry_count', 0)}</div>
                    <div class="metric-label">Entries</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('re_entry_count', 0)}</div>
                    <div class="metric-label">Re-entries</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('partial_exit_count', 0)}</div>
                    <div class="metric-label">Partial Exits</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('take_profit_count', 0)}</div>
                    <div class="metric-label">Take Profits</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('stop_loss_count', 0)}</div>
                    <div class="metric-label">Stop Losses</div>
                </div>
            </div>
            
            <h2>Fibonacci Level Metrics</h2>
            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('most_common_fib_level', 0)}</div>
                    <div class="metric-label">Most Common Level</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics.get('most_common_fib_level_count', 0)}</div>
                    <div class="metric-label">Count</div>
                </div>
            </div>
            
            <h2>Charts</h2>
            <div class="chart-container">
                <h3>Trade Distribution</h3>
                <img src="trade_distribution.png" alt="Trade Distribution" style="max-width: 100%;">
            </div>
            
            <div class="chart-container">
                <h3>Performance Metrics</h3>
                <img src="performance_metrics.png" alt="Performance Metrics" style="max-width: 100%;">
            </div>
            
            <div class="chart-container">
                <h3>Fibonacci Level Analysis</h3>
                <img src="fibonacci_level_analysis.png" alt="Fibonacci Level Analysis" style="max-width: 100%;">
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(os.path.join(output_dir, "fibonacci_performance_report.html"), "w") as f:
        f.write(html_content)


def generate_performance_report(history_file, output_dir):
    """Generate a comprehensive performance report for the Fibonacci strategy"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load and parse trade history
    history = load_trade_history(history_file)
    if not history:
        print("No trade history found. Exiting.")
        return
    
    history = parse_timestamps(history)
    
    # Create DataFrame for analysis
    df = create_trades_dataframe(history)
    if df.empty:
        print("Failed to create trades DataFrame. Exiting.")
        return
    
    # Calculate position metrics
    positions_df = calculate_position_metrics(df)
    
    # Generate summary metrics
    metrics = generate_summary_metrics(df, positions_df)
    
    # Generate charts
    plot_trade_distribution(df, output_dir)
    plot_performance_metrics(positions_df, output_dir)
    plot_fibonacci_level_analysis(df, output_dir)
    
    # Generate HTML report
    generate_html_report(metrics, output_dir)
    
    print(f"Performance report generated successfully in {output_dir}")
    print(f"Open {os.path.join(output_dir, 'fibonacci_performance_report.html')} to view the report")


def main():
    """Main function to parse arguments and generate report"""
    parser = argparse.ArgumentParser(description="Generate Fibonacci Strategy Performance Report")
    parser.add_argument(
        "--history_file",
        default="logs/fibonacci_trades.json",
        help="Path to the trade history JSON file"
    )
    parser.add_argument(
        "--output_dir",
        default="reports",
        help="Directory to save the report and charts"
    )
    
    args = parser.parse_args()
    generate_performance_report(args.history_file, args.output_dir)


if __name__ == "__main__":
    main()