# weekly_report.py

import argparse
import json
import logging
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Try to import the TradePerformanceEvaluator from trade_evaluator.py
try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def get_all_strategies_performance(self):
            return {}
        
        def get_strategy_performance(self, strategy_name):
            return {}

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("weekly_report")

# Constants
REPORT_DIR = os.path.join("reports")
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")

# Ensure directories exist
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)


class WeeklyReportGenerator:
    """Generates comprehensive weekly trading performance reports"""

    def __init__(self, trade_history_file: str = TRADE_HISTORY_FILE, 
                 strategy_stats_file: str = STRATEGY_STATS_FILE,
                 report_dir: str = REPORT_DIR):
        """Initialize the weekly report generator

        Args:
            trade_history_file (str): Path to the trade history file
            strategy_stats_file (str): Path to the strategy statistics file
            report_dir (str): Directory to save reports
        """
        self.trade_history_file = trade_history_file
        self.strategy_stats_file = strategy_stats_file
        self.report_dir = report_dir
        self.evaluator = TradePerformanceEvaluator(trade_history_file, strategy_stats_file)
        
    def load_trade_history(self) -> List[Dict]:
        """Load trade history from file

        Returns:
            List[Dict]: List of trade records
        """
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Trade history file {self.trade_history_file} not found.")
                return []
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return []

    def get_weekly_trades(self, start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> List[Dict]:
        """Get trades for a specific week

        Args:
            start_date (Optional[datetime]): Start date of the week. Defaults to last week.
            end_date (Optional[datetime]): End date of the week. Defaults to today.

        Returns:
            List[Dict]: List of trades for the week
        """
        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=7)
            
        # Format dates as strings for comparison
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # Load trade history
        trades = self.load_trade_history()
        
        # Filter trades for the week
        weekly_trades = []
        for trade in trades:
            # Get trade timestamp
            timestamp = trade.get("timestamp", "")
            if not timestamp:
                timestamp = trade.get("entry_time", "")
                
            # Skip trades without timestamp
            if not timestamp:
                continue
                
            # Extract date part only
            trade_date = timestamp.split("T")[0] if "T" in timestamp else timestamp.split(" ")[0]
            
            # Check if trade is within the week
            if start_str <= trade_date <= end_str:
                weekly_trades.append(trade)
                
        return weekly_trades

    def calculate_weekly_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate metrics for the weekly trades

        Args:
            trades (List[Dict]): List of trades for the week

        Returns:
            Dict: Weekly metrics
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit_loss": 0.0,
                "avg_profit_loss": 0.0,
                "news_avoided_count": 0,
                "strategies": {},
                "symbols": {},
                "market_conditions": {}
            }
            
        # Initialize metrics
        metrics = {
            "total_trades": len(trades),
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_profit_loss": 0.0,
            "avg_profit_loss": 0.0,
            "news_avoided_count": 0,
            "strategies": {},
            "symbols": {},
            "market_conditions": {}
        }
        
        # Calculate metrics
        for trade in trades:
            # Get profit/loss
            profit_loss = trade.get("profit_loss", 0.0)
            metrics["total_profit_loss"] += profit_loss
            
            # Count wins/losses
            if profit_loss > 0:
                metrics["winning_trades"] += 1
            else:
                metrics["losing_trades"] += 1
                
            # Count news avoided
            if trade.get("news_avoided", False):
                metrics["news_avoided_count"] += 1
                
            # Count by strategy
            strategy = trade.get("strategy", "Unknown")
            if strategy not in metrics["strategies"]:
                metrics["strategies"][strategy] = {
                    "count": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_profit_loss": 0.0
                }
                
            metrics["strategies"][strategy]["count"] += 1
            metrics["strategies"][strategy]["total_profit_loss"] += profit_loss
            if profit_loss > 0:
                metrics["strategies"][strategy]["winning_trades"] += 1
            else:
                metrics["strategies"][strategy]["losing_trades"] += 1
                
            # Count by symbol
            symbol = trade.get("symbol", "Unknown")
            if symbol not in metrics["symbols"]:
                metrics["symbols"][symbol] = {
                    "count": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_profit_loss": 0.0
                }
                
            metrics["symbols"][symbol]["count"] += 1
            metrics["symbols"][symbol]["total_profit_loss"] += profit_loss
            if profit_loss > 0:
                metrics["symbols"][symbol]["winning_trades"] += 1
            else:
                metrics["symbols"][symbol]["losing_trades"] += 1
                
            # Count by market condition
            market_condition = trade.get("market_condition", "Unknown")
            if market_condition not in metrics["market_conditions"]:
                metrics["market_conditions"][market_condition] = {
                    "count": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_profit_loss": 0.0
                }
                
            metrics["market_conditions"][market_condition]["count"] += 1
            metrics["market_conditions"][market_condition]["total_profit_loss"] += profit_loss
            if profit_loss > 0:
                metrics["market_conditions"][market_condition]["winning_trades"] += 1
            else:
                metrics["market_conditions"][market_condition]["losing_trades"] += 1
        
        # Calculate win rate
        if metrics["total_trades"] > 0:
            metrics["win_rate"] = (metrics["winning_trades"] / metrics["total_trades"]) * 100
            metrics["avg_profit_loss"] = metrics["total_profit_loss"] / metrics["total_trades"]
            
        # Calculate win rates for strategies, symbols, and market conditions
        for category in ["strategies", "symbols", "market_conditions"]:
            for key, value in metrics[category].items():
                if value["count"] > 0:
                    value["win_rate"] = (value["winning_trades"] / value["count"]) * 100
                    value["avg_profit_loss"] = value["total_profit_loss"] / value["count"]
        
        return metrics

    def generate_suggestions(self, metrics: Dict) -> List[str]:
        """Generate suggestions based on weekly metrics

        Args:
            metrics (Dict): Weekly metrics

        Returns:
            List[str]: List of suggestions
        """
        suggestions = []
        
        # Check if there are enough trades for meaningful suggestions
        if metrics["total_trades"] < 5:
            suggestions.append("Not enough trades this week for meaningful suggestions. Consider increasing trading frequency.")
            return suggestions
            
        # Check overall win rate
        if metrics["win_rate"] < 40:
            suggestions.append(f"Overall win rate is low ({metrics['win_rate']:.1f}%). Consider reviewing your trading strategies.")
        elif metrics["win_rate"] > 60:
            suggestions.append(f"Strong overall win rate ({metrics['win_rate']:.1f}%). Consider increasing position sizes.")
            
        # Check profit/loss
        if metrics["total_profit_loss"] < 0:
            suggestions.append(f"Negative overall P&L (${metrics['total_profit_loss']:.2f}). Focus on cutting losses earlier.")
        
        # Check strategies
        best_strategy = None
        worst_strategy = None
        best_win_rate = 0
        worst_win_rate = 100
        
        for strategy, stats in metrics["strategies"].items():
            if stats["count"] >= 3:  # Only consider strategies with at least 3 trades
                if stats["win_rate"] > best_win_rate:
                    best_win_rate = stats["win_rate"]
                    best_strategy = strategy
                if stats["win_rate"] < worst_win_rate:
                    worst_win_rate = stats["win_rate"]
                    worst_strategy = strategy
        
        if best_strategy and best_win_rate > 60:
            suggestions.append(f"Strategy '{best_strategy}' performed well with {best_win_rate:.1f}% win rate. Consider allocating more capital.")
        if worst_strategy and worst_win_rate < 40:
            suggestions.append(f"Strategy '{worst_strategy}' underperformed with {worst_win_rate:.1f}% win rate. Consider reviewing or pausing.")
            
        # Check symbols
        best_symbol = None
        worst_symbol = None
        best_symbol_pnl = float('-inf')
        worst_symbol_pnl = float('inf')
        
        for symbol, stats in metrics["symbols"].items():
            if stats["count"] >= 3:  # Only consider symbols with at least 3 trades
                if stats["total_profit_loss"] > best_symbol_pnl:
                    best_symbol_pnl = stats["total_profit_loss"]
                    best_symbol = symbol
                if stats["total_profit_loss"] < worst_symbol_pnl:
                    worst_symbol_pnl = stats["total_profit_loss"]
                    worst_symbol = symbol
        
        if best_symbol and best_symbol_pnl > 0:
            suggestions.append(f"Symbol '{best_symbol}' was most profitable (${best_symbol_pnl:.2f}). Consider increasing exposure.")
        if worst_symbol and worst_symbol_pnl < 0:
            suggestions.append(f"Symbol '{worst_symbol}' was least profitable (${worst_symbol_pnl:.2f}). Consider reducing exposure.")
            
        # Check market conditions
        best_condition = None
        worst_condition = None
        best_condition_win_rate = 0
        worst_condition_win_rate = 100
        
        for condition, stats in metrics["market_conditions"].items():
            if stats["count"] >= 3:  # Only consider conditions with at least 3 trades
                if stats["win_rate"] > best_condition_win_rate:
                    best_condition_win_rate = stats["win_rate"]
                    best_condition = condition
                if stats["win_rate"] < worst_condition_win_rate:
                    worst_condition_win_rate = stats["win_rate"]
                    worst_condition = condition
        
        if best_condition and best_condition_win_rate > 60:
            suggestions.append(f"Performance was strong in '{best_condition}' markets ({best_condition_win_rate:.1f}% win rate). Focus on these conditions.")
        if worst_condition and worst_condition_win_rate < 40:
            suggestions.append(f"Performance was weak in '{worst_condition}' markets ({worst_condition_win_rate:.1f}% win rate). Consider avoiding these conditions.")
            
        # Check news avoidance
        news_avoided_pct = (metrics["news_avoided_count"] / metrics["total_trades"]) * 100 if metrics["total_trades"] > 0 else 0
        if news_avoided_pct > 30:
            suggestions.append(f"High percentage of trades ({news_avoided_pct:.1f}%) avoided news. News filter is working well.")
        elif news_avoided_pct < 10:
            suggestions.append(f"Low percentage of trades ({news_avoided_pct:.1f}%) avoided news. Consider reviewing news filter settings.")
            
        return suggestions

    def generate_charts(self, trades: List[Dict], output_dir: str) -> Dict[str, str]:
        """Generate charts for the weekly report

        Args:
            trades (List[Dict]): List of trades for the week
            output_dir (str): Directory to save charts

        Returns:
            Dict[str, str]: Dictionary of chart file paths
        """
        if not trades:
            return {}
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert trades to DataFrame for easier analysis
        df = pd.DataFrame(trades)
        
        # Initialize chart paths
        chart_paths = {}
        
        # Set Seaborn style
        sns.set(style="whitegrid")
        
        # 1. Daily P&L chart
        try:
            if "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"]).dt.date
            elif "entry_time" in df.columns:
                df["date"] = pd.to_datetime(df["entry_time"]).dt.date
            else:
                df["date"] = pd.to_datetime("today").date()
                
            daily_pnl = df.groupby("date")["profit_loss"].sum().reset_index()
            
            plt.figure(figsize=(10, 6))
            plt.bar(daily_pnl["date"].astype(str), daily_pnl["profit_loss"], 
                   color=["green" if x > 0 else "red" for x in daily_pnl["profit_loss"]])
            plt.title("Daily Profit/Loss")
            plt.xlabel("Date")
            plt.ylabel("Profit/Loss")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart
            daily_pnl_path = os.path.join(output_dir, "daily_pnl.png")
            plt.savefig(daily_pnl_path)
            plt.close()
            
            chart_paths["daily_pnl"] = daily_pnl_path
        except Exception as e:
            logger.error(f"Error generating daily P&L chart: {e}")
        
        # 2. Strategy performance chart
        try:
            if "strategy" in df.columns:
                strategy_pnl = df.groupby("strategy")["profit_loss"].agg(["sum", "count"]).reset_index()
                strategy_pnl = strategy_pnl.sort_values("sum", ascending=False)
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(strategy_pnl["strategy"], strategy_pnl["sum"], 
                       color=["green" if x > 0 else "red" for x in strategy_pnl["sum"]])
                plt.title("Strategy Performance")
                plt.xlabel("Strategy")
                plt.ylabel("Profit/Loss")
                plt.xticks(rotation=45)
                
                # Add trade count labels
                for bar, count in zip(bars, strategy_pnl["count"]):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            f"n={count}", ha="center", va="bottom")
                
                plt.tight_layout()
                
                # Save chart
                strategy_path = os.path.join(output_dir, "strategy_performance.png")
                plt.savefig(strategy_path)
                plt.close()
                
                chart_paths["strategy_performance"] = strategy_path
        except Exception as e:
            logger.error(f"Error generating strategy performance chart: {e}")
        
        # 3. Symbol performance chart
        try:
            if "symbol" in df.columns:
                symbol_pnl = df.groupby("symbol")["profit_loss"].agg(["sum", "count"]).reset_index()
                symbol_pnl = symbol_pnl.sort_values("sum", ascending=False)
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(symbol_pnl["symbol"], symbol_pnl["sum"], 
                       color=["green" if x > 0 else "red" for x in symbol_pnl["sum"]])
                plt.title("Symbol Performance")
                plt.xlabel("Symbol")
                plt.ylabel("Profit/Loss")
                plt.xticks(rotation=45)
                
                # Add trade count labels
                for bar, count in zip(bars, symbol_pnl["count"]):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            f"n={count}", ha="center", va="bottom")
                
                plt.tight_layout()
                
                # Save chart
                symbol_path = os.path.join(output_dir, "symbol_performance.png")
                plt.savefig(symbol_path)
                plt.close()
                
                chart_paths["symbol_performance"] = symbol_path
        except Exception as e:
            logger.error(f"Error generating symbol performance chart: {e}")
        
        # 4. Market condition performance chart
        try:
            if "market_condition" in df.columns:
                condition_pnl = df.groupby("market_condition")["profit_loss"].agg(["sum", "count"]).reset_index()
                condition_pnl = condition_pnl.sort_values("sum", ascending=False)
                
                plt.figure(figsize=(10, 6))
                bars = plt.bar(condition_pnl["market_condition"], condition_pnl["sum"], 
                       color=["green" if x > 0 else "red" for x in condition_pnl["sum"]])
                plt.title("Market Condition Performance")
                plt.xlabel("Market Condition")
                plt.ylabel("Profit/Loss")
                plt.xticks(rotation=45)
                
                # Add trade count labels
                for bar, count in zip(bars, condition_pnl["count"]):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            f"n={count}", ha="center", va="bottom")
                
                plt.tight_layout()
                
                # Save chart
                condition_path = os.path.join(output_dir, "market_condition_performance.png")
                plt.savefig(condition_path)
                plt.close()
                
                chart_paths["market_condition_performance"] = condition_path
        except Exception as e:
            logger.error(f"Error generating market condition performance chart: {e}")
        
        # 5. News avoidance impact chart
        try:
            if "news_avoided" in df.columns:
                news_pnl = df.groupby("news_avoided")["profit_loss"].agg(["mean", "count"]).reset_index()
                
                plt.figure(figsize=(8, 6))
                bars = plt.bar(["News Not Avoided", "News Avoided"], 
                       news_pnl["mean"], 
                       color=["blue", "orange"])
                plt.title("Impact of News Avoidance on Average P&L")
                plt.xlabel("News Avoidance")
                plt.ylabel("Average Profit/Loss")
                
                # Add trade count labels
                for bar, count in zip(bars, news_pnl["count"]):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            f"n={count}", ha="center", va="bottom")
                
                plt.tight_layout()
                
                # Save chart
                news_path = os.path.join(output_dir, "news_avoidance_impact.png")
                plt.savefig(news_path)
                plt.close()
                
                chart_paths["news_avoidance_impact"] = news_path
        except Exception as e:
            logger.error(f"Error generating news avoidance impact chart: {e}")
        
        return chart_paths

    def generate_html_report(self, metrics: Dict, suggestions: List[str], 
                           chart_paths: Dict[str, str], start_date: datetime, 
                           end_date: datetime, output_file: str) -> bool:
        """Generate HTML report

        Args:
            metrics (Dict): Weekly metrics
            suggestions (List[str]): List of suggestions
            chart_paths (Dict[str, str]): Dictionary of chart file paths
            start_date (datetime): Start date of the week
            end_date (datetime): End date of the week
            output_file (str): Output file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format dates
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            # Create HTML content
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Weekly Trading Report: {start_str} to {end_str}</title>
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
                    .suggestions {{ background-color: #f0f8ff; padding: 15px; border-left: 5px solid #3498db; margin: 20px 0; }}
                    .suggestion-item {{ margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Weekly Trading Report</h1>
                    <h2>{start_str} to {end_str}</h2>
                    
                    <div class="metrics-container">
                        <div class="metric-box">
                            <div class="metric-value">{metrics['total_trades']}</div>
                            <div class="metric-label">Total Trades</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value">{metrics['winning_trades']}</div>
                            <div class="metric-label">Winning Trades</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value">{metrics['losing_trades']}</div>
                            <div class="metric-label">Losing Trades</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value {"positive" if metrics['win_rate'] >= 50 else "negative"}">{metrics['win_rate']:.1f}%</div>
                            <div class="metric-label">Win Rate</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value {"positive" if metrics['total_profit_loss'] > 0 else "negative"}">${metrics['total_profit_loss']:.2f}</div>
                            <div class="metric-label">Total P&L</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value">{metrics['news_avoided_count']}</div>
                            <div class="metric-label">Trades with News Avoided</div>
                        </div>
                    </div>
            """
            
            # Add charts if available
            for chart_name, chart_path in chart_paths.items():
                # Convert absolute path to relative path for HTML
                rel_path = os.path.relpath(chart_path, os.path.dirname(output_file))
                html += f"""
                    <div class="chart-container">
                        <h3>{chart_name.replace('_', ' ').title()}</h3>
                        <img src="{rel_path}" alt="{chart_name}" style="max-width: 100%;">
                    </div>
                """
            
            # Add strategy performance table
            if metrics["strategies"]:
                html += f"""
                    <h2>Strategy Performance</h2>
                    <table>
                        <tr>
                            <th>Strategy</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>P&L</th>
                            <th>Avg P&L</th>
                        </tr>
                """
                
                for strategy, stats in sorted(metrics["strategies"].items(), key=lambda x: x[1]["total_profit_loss"], reverse=True):
                    win_rate = stats.get("win_rate", 0)
                    avg_pnl = stats.get("avg_profit_loss", 0)
                    html += f"""
                        <tr>
                            <td>{strategy}</td>
                            <td>{stats['count']}</td>
                            <td class="{"positive" if win_rate >= 50 else "negative"}">{win_rate:.1f}%</td>
                            <td class="{"positive" if stats['total_profit_loss'] > 0 else "negative"}">${stats['total_profit_loss']:.2f}</td>
                            <td class="{"positive" if avg_pnl > 0 else "negative"}">${avg_pnl:.2f}</td>
                        </tr>
                    """
                    
                html += "</table>"
            
            # Add symbol performance table
            if metrics["symbols"]:
                html += f"""
                    <h2>Symbol Performance</h2>
                    <table>
                        <tr>
                            <th>Symbol</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>P&L</th>
                            <th>Avg P&L</th>
                        </tr>
                """
                
                for symbol, stats in sorted(metrics["symbols"].items(), key=lambda x: x[1]["total_profit_loss"], reverse=True):
                    win_rate = stats.get("win_rate", 0)
                    avg_pnl = stats.get("avg_profit_loss", 0)
                    html += f"""
                        <tr>
                            <td>{symbol}</td>
                            <td>{stats['count']}</td>
                            <td class="{"positive" if win_rate >= 50 else "negative"}">{win_rate:.1f}%</td>
                            <td class="{"positive" if stats['total_profit_loss'] > 0 else "negative"}">${stats['total_profit_loss']:.2f}</td>
                            <td class="{"positive" if avg_pnl > 0 else "negative"}">${avg_pnl:.2f}</td>
                        </tr>
                    """
                    
                html += "</table>"
            
            # Add market condition performance table
            if metrics["market_conditions"]:
                html += f"""
                    <h2>Market Condition Performance</h2>
                    <table>
                        <tr>
                            <th>Market Condition</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>P&L</th>
                            <th>Avg P&L</th>
                        </tr>
                """
                
                for condition, stats in sorted(metrics["market_conditions"].items(), key=lambda x: x[1]["total_profit_loss"], reverse=True):
                    win_rate = stats.get("win_rate", 0)
                    avg_pnl = stats.get("avg_profit_loss", 0)
                    html += f"""
                        <tr>
                            <td>{condition}</td>
                            <td>{stats['count']}</td>
                            <td class="{"positive" if win_rate >= 50 else "negative"}">{win_rate:.1f}%</td>
                            <td class="{"positive" if stats['total_profit_loss'] > 0 else "negative"}">${stats['total_profit_loss']:.2f}</td>
                            <td class="{"positive" if avg_pnl > 0 else "negative"}">${avg_pnl:.2f}</td>
                        </tr>
                    """
                    
                html += "</table>"
            
            # Add suggestions
            if suggestions:
                html += f"""
                    <h2>Suggestions for Next Week</h2>
                    <div class="suggestions">
                """
                
                for suggestion in suggestions:
                    html += f"""
                        <div class="suggestion-item">• {suggestion}</div>
                    """
                    
                html += "</div>"
            
            # Close HTML
            html += f"""
                </div>
            </body>
            </html>
            """
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write HTML to file
            with open(output_file, "w") as f:
                f.write(html)
                
            return True
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return False

    def generate_markdown_report(self, metrics: Dict, suggestions: List[str], 
                               start_date: datetime, end_date: datetime, 
                               output_file: str) -> bool:
        """Generate Markdown report

        Args:
            metrics (Dict): Weekly metrics
            suggestions (List[str]): List of suggestions
            start_date (datetime): Start date of the week
            end_date (datetime): End date of the week
            output_file (str): Output file path

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format dates
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            # Create Markdown content
            md = f"# Weekly Trading Report: {start_str} to {end_str}\n\n"
            
            # Add summary
            md += "## Summary\n\n"
            md += f"- **Total Trades:** {metrics['total_trades']}\n"
            md += f"- **Winning Trades:** {metrics['winning_trades']}\n"
            md += f"- **Losing Trades:** {metrics['losing_trades']}\n"
            md += f"- **Win Rate:** {metrics['win_rate']:.1f}%\n"
            md += f"- **Total P&L:** ${metrics['total_profit_loss']:.2f}\n"
            md += f"- **Trades with News Avoided:** {metrics['news_avoided_count']}\n\n"
            
            # Add strategy performance
            if metrics["strategies"]:
                md += "## Strategy Performance\n\n"
                md += "| Strategy | Trades | Win Rate | P&L | Avg P&L |\n"
                md += "|----------|--------|---------|-----|---------|\n"
                
                for strategy, stats in sorted(metrics["strategies"].items(), key=lambda x: x[1]["total_profit_loss"], reverse=True):
                    win_rate = stats.get("win_rate", 0)
                    avg_pnl = stats.get("avg_profit_loss", 0)
                    md += f"| {strategy} | {stats['count']} | {win_rate:.1f}% | ${stats['total_profit_loss']:.2f} | ${avg_pnl:.2f} |\n"
                    
                md += "\n"
            
            # Add symbol performance
            if metrics["symbols"]:
                md += "## Symbol Performance\n\n"
                md += "| Symbol | Trades | Win Rate | P&L | Avg P&L |\n"
                md += "|--------|--------|---------|-----|---------|\n"
                
                for symbol, stats in sorted(metrics["symbols"].items(), key=lambda x: x[1]["total_profit_loss"], reverse=True):
                    win_rate = stats.get("win_rate", 0)
                    avg_pnl = stats.get("avg_profit_loss", 0)
                    md += f"| {symbol} | {stats['count']} | {win_rate:.1f}% | ${stats['total_profit_loss']:.2f} | ${avg_pnl:.2f} |\n"
                    
                md += "\n"
            
            # Add market condition performance
            if metrics["market_conditions"]:
                md += "## Market Condition Performance\n\n"
                md += "| Market Condition | Trades | Win Rate | P&L | Avg P&L |\n"
                md += "|-----------------|--------|---------|-----|---------|\n"
                
                for condition, stats in sorted(metrics["market_conditions"].items(), key=lambda x: x[1]["total_profit_loss"], reverse=True):
                    win_rate = stats.get("win_rate", 0)
                    avg_pnl = stats.get("avg_profit_loss", 0)
                    md += f"| {condition} | {stats['count']} | {win_rate:.1f}% | ${stats['total_profit_loss']:.2f} | ${avg_pnl:.2f} |\n"
                    
                md += "\n"
            
            # Add suggestions
            if suggestions:
                md += "## Suggestions for Next Week\n\n"
                
                for suggestion in suggestions:
                    md += f"- {suggestion}\n"
                    
                md += "\n"
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write Markdown to file
            with open(output_file, "w") as f:
                f.write(md)
                
            return True
        except Exception as e:
            logger.error(f"Error generating Markdown report: {e}")
            return False

    def generate_weekly_report(self, start_date: Optional[datetime] = None, 
                             end_date: Optional[datetime] = None, 
                             output_format: str = "html") -> Tuple[bool, str]:
        """Generate weekly report

        Args:
            start_date (Optional[datetime]): Start date of the week. Defaults to last week.
            end_date (Optional[datetime]): End date of the week. Defaults to today.
            output_format (str): Output format ("html" or "markdown"). Defaults to "html".

        Returns:
            Tuple[bool, str]: (success, output_file_path)
        """
        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=7)
            
        # Format dates for file name
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # Get weekly trades
        weekly_trades = self.get_weekly_trades(start_date, end_date)
        
        if not weekly_trades:
            logger.warning("No trades found for the specified week.")
            return False, ""
            
        # Calculate metrics
        metrics = self.calculate_weekly_metrics(weekly_trades)
        
        # Generate suggestions
        suggestions = self.generate_suggestions(metrics)
        
        # Create output directory
        report_dir = os.path.join(self.report_dir, f"weekly_{start_str}_to_{end_str}")
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate charts
        chart_paths = self.generate_charts(weekly_trades, report_dir)
        
        # Generate report
        if output_format.lower() == "html":
            output_file = os.path.join(report_dir, "weekly_report.html")
            success = self.generate_html_report(metrics, suggestions, chart_paths, start_date, end_date, output_file)
        else:  # Markdown
            output_file = os.path.join(report_dir, "weekly_report.md")
            success = self.generate_markdown_report(metrics, suggestions, start_date, end_date, output_file)
            
        if success:
            logger.info(f"Weekly report generated successfully: {output_file}")
            return True, output_file
        else:
            logger.error("Failed to generate weekly report.")
            return False, ""


# Helper functions
def generate_weekly_report(start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None, 
                         output_format: str = "html") -> Tuple[bool, str]:
    """Generate weekly report (helper function)

    Args:
        start_date (Optional[datetime]): Start date of the week. Defaults to last week.
        end_date (Optional[datetime]): End date of the week. Defaults to today.
        output_format (str): Output format ("html" or "markdown"). Defaults to "html".

    Returns:
        Tuple[bool, str]: (success, output_file_path)
    """
    generator = WeeklyReportGenerator()
    return generator.generate_weekly_report(start_date, end_date, output_format)


# Command-line interface
def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description="Generate weekly trading performance report")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--format", type=str, choices=["html", "markdown"], default="html", help="Output format")
    parser.add_argument("--trade-history", type=str, help="Path to trade history file")
    parser.add_argument("--strategy-stats", type=str, help="Path to strategy stats file")
    parser.add_argument("--output-dir", type=str, help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid start date format. Use YYYY-MM-DD.")
            return 1
            
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid end date format. Use YYYY-MM-DD.")
            return 1
    
    # Create generator with custom paths if provided
    generator_kwargs = {}
    
    if args.trade_history:
        generator_kwargs["trade_history_file"] = args.trade_history
    if args.strategy_stats:
        generator_kwargs["strategy_stats_file"] = args.strategy_stats
    if args.output_dir:
        generator_kwargs["report_dir"] = args.output_dir
        
    generator = WeeklyReportGenerator(**generator_kwargs)
    
    # Generate report
    success, output_file = generator.generate_weekly_report(start_date, end_date, args.format)
    
    if success:
        print(f"Weekly report generated successfully: {output_file}")
        return 0
    else:
        print("Failed to generate weekly report.")
        return 1


# For testing
if __name__ == "__main__":
    sys.exit(main())