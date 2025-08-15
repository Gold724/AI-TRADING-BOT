# backtest_engine.py

import json
import logging
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from pathlib import Path
import random

# Try to import from other modules
try:
    from strategy_manager import StrategyManager
except ImportError:
    # Define a minimal version if the import fails
    class StrategyManager:
        def get_enabled_strategies(self):
            return []
        def get_strategy_config(self, strategy_name):
            return {}

try:
    from risk_control import RiskController
except ImportError:
    # Define a minimal version if the import fails
    class RiskController:
        def get_position_size(self, strategy_name, symbol, confidence):
            return 0.01

try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def record_trade(self, trade_data):
            pass

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backtest_engine")

# Constants
BACKTEST_DIR = os.path.join("data", "backtest")
HISTORICAL_DATA_DIR = os.path.join("data", "historical")
BACKTEST_RESULTS_DIR = os.path.join(BACKTEST_DIR, "results")
BACKTEST_CHARTS_DIR = os.path.join(BACKTEST_DIR, "charts")

# Ensure directories exist
os.makedirs(BACKTEST_DIR, exist_ok=True)
os.makedirs(HISTORICAL_DATA_DIR, exist_ok=True)
os.makedirs(BACKTEST_RESULTS_DIR, exist_ok=True)
os.makedirs(BACKTEST_CHARTS_DIR, exist_ok=True)


class BacktestEngine:
    """Engine for backtesting trading strategies with historical data"""

    def __init__(self, historical_data_dir: str = HISTORICAL_DATA_DIR,
                 backtest_results_dir: str = BACKTEST_RESULTS_DIR,
                 backtest_charts_dir: str = BACKTEST_CHARTS_DIR):
        """Initialize the backtest engine

        Args:
            historical_data_dir (str): Directory containing historical price data
            backtest_results_dir (str): Directory to save backtest results
            backtest_charts_dir (str): Directory to save backtest charts
        """
        self.historical_data_dir = historical_data_dir
        self.backtest_results_dir = backtest_results_dir
        self.backtest_charts_dir = backtest_charts_dir
        
        # Initialize components
        self.strategy_manager = StrategyManager()
        self.risk_controller = RiskController()
        self.evaluator = TradePerformanceEvaluator()
        
        # Initialize backtest state
        self.historical_data = {}
        self.backtest_results = {}
        self.current_equity = 10000.0  # Default starting equity
        self.trades = []
        
    def load_historical_data(self, symbol: str, timeframe: str = "H1",
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """Load historical price data for a symbol

        Args:
            symbol (str): Symbol to load data for (e.g., "EURUSD")
            timeframe (str): Timeframe of the data (e.g., "M1", "H1", "D1")
            start_date (Optional[str]): Start date in YYYY-MM-DD format
            end_date (Optional[str]): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: Historical price data
        """
        try:
            # Construct file path
            file_path = os.path.join(self.historical_data_dir, f"{symbol}_{timeframe}.csv")
            
            if not os.path.exists(file_path):
                logger.error(f"Historical data file not found: {file_path}")
                return pd.DataFrame()
                
            # Load data
            data = pd.read_csv(file_path)
            
            # Convert timestamp to datetime
            if "timestamp" in data.columns:
                data["timestamp"] = pd.to_datetime(data["timestamp"])
            elif "time" in data.columns:
                data["timestamp"] = pd.to_datetime(data["time"])
                data = data.drop(columns=["time"])
            else:
                # Try to find a datetime column
                datetime_cols = [col for col in data.columns if "time" in col.lower() or "date" in col.lower()]
                if datetime_cols:
                    data["timestamp"] = pd.to_datetime(data[datetime_cols[0]])
                    if datetime_cols[0] != "timestamp":
                        data = data.drop(columns=[datetime_cols[0]])
                else:
                    logger.warning(f"No timestamp column found in {file_path}")
                    data["timestamp"] = pd.date_range(start="2020-01-01", periods=len(data), freq="H")
            
            # Set timestamp as index
            data = data.set_index("timestamp")
            
            # Filter by date range if provided
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
                
            # Ensure OHLC columns exist
            required_columns = ["open", "high", "low", "close"]
            for col in required_columns:
                if col not in data.columns:
                    # Try to find column with similar name
                    similar_cols = [c for c in data.columns if col.lower() in c.lower()]
                    if similar_cols:
                        data[col] = data[similar_cols[0]]
                    else:
                        logger.warning(f"Column {col} not found in {file_path}")
                        # For testing, create synthetic data
                        if col == "open":
                            data[col] = np.random.normal(100, 1, size=len(data))
                        elif col == "high":
                            data[col] = data["open"] * (1 + np.random.uniform(0, 0.01, size=len(data)))
                        elif col == "low":
                            data[col] = data["open"] * (1 - np.random.uniform(0, 0.01, size=len(data)))
                        elif col == "close":
                            data[col] = data["open"] * (1 + np.random.normal(0, 0.005, size=len(data)))
            
            # Store data
            self.historical_data[f"{symbol}_{timeframe}"] = data
            
            return data
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
            
    def generate_synthetic_data(self, symbol: str, timeframe: str = "H1",
                              start_date: str = "2020-01-01",
                              end_date: str = "2020-12-31",
                              initial_price: float = 100.0,
                              volatility: float = 0.01,
                              trend: float = 0.0001,
                              save: bool = True) -> pd.DataFrame:
        """Generate synthetic price data for testing

        Args:
            symbol (str): Symbol to generate data for
            timeframe (str): Timeframe of the data
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            initial_price (float): Initial price
            volatility (float): Price volatility
            trend (float): Price trend (positive for uptrend, negative for downtrend)
            save (bool): Whether to save the generated data

        Returns:
            pd.DataFrame: Synthetic price data
        """
        try:
            # Generate date range
            if timeframe == "M1":
                freq = "1min"
            elif timeframe == "M5":
                freq = "5min"
            elif timeframe == "M15":
                freq = "15min"
            elif timeframe == "M30":
                freq = "30min"
            elif timeframe == "H1":
                freq = "1H"
            elif timeframe == "H4":
                freq = "4H"
            elif timeframe == "D1":
                freq = "1D"
            else:
                freq = "1H"
                
            # Create date range
            date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
            
            # Generate price data
            np.random.seed(42)  # For reproducibility
            prices = [initial_price]
            for i in range(1, len(date_range)):
                # Add random walk with drift
                price = prices[-1] * (1 + np.random.normal(trend, volatility))
                prices.append(price)
                
            # Create DataFrame
            data = pd.DataFrame(index=date_range)
            data["open"] = prices
            data["high"] = data["open"] * (1 + np.random.uniform(0, volatility, size=len(data)))
            data["low"] = data["open"] * (1 - np.random.uniform(0, volatility, size=len(data)))
            data["close"] = data["open"] * (1 + np.random.normal(trend, volatility / 2, size=len(data)))
            data["volume"] = np.random.lognormal(10, 1, size=len(data))
            
            # Ensure high is always highest and low is always lowest
            data["high"] = np.maximum(data["high"], np.maximum(data["open"], data["close"]))
            data["low"] = np.minimum(data["low"], np.minimum(data["open"], data["close"]))
            
            # Save data if requested
            if save:
                file_path = os.path.join(self.historical_data_dir, f"{symbol}_{timeframe}.csv")
                data.to_csv(file_path)
                logger.info(f"Saved synthetic data to {file_path}")
                
            # Store data
            self.historical_data[f"{symbol}_{timeframe}"] = data
            
            return data
        except Exception as e:
            logger.error(f"Error generating synthetic data: {e}")
            return pd.DataFrame()
            
    def run_strategy_backtest(self, strategy_name: str, symbol: str, timeframe: str,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            initial_equity: float = 10000.0,
                            position_size: Optional[float] = None,
                            commission: float = 0.0,
                            slippage: float = 0.0) -> Dict:
        """Run a backtest for a specific strategy

        Args:
            strategy_name (str): Name of the strategy to backtest
            symbol (str): Symbol to backtest on
            timeframe (str): Timeframe to backtest on
            start_date (Optional[str]): Start date for backtest
            end_date (Optional[str]): End date for backtest
            initial_equity (float): Initial equity for backtest
            position_size (Optional[float]): Fixed position size (if None, use risk controller)
            commission (float): Commission per trade (in percentage)
            slippage (float): Slippage per trade (in percentage)

        Returns:
            Dict: Backtest results
        """
        try:
            # Load strategy configuration
            strategy_config = self.strategy_manager.get_strategy_config(strategy_name)
            if not strategy_config:
                logger.error(f"Strategy configuration not found for {strategy_name}")
                return {}
                
            # Load historical data
            data_key = f"{symbol}_{timeframe}"
            if data_key not in self.historical_data:
                data = self.load_historical_data(symbol, timeframe, start_date, end_date)
                if data.empty:
                    logger.error(f"No historical data available for {symbol} {timeframe}")
                    return {}
            else:
                data = self.historical_data[data_key]
                
            # Filter by date range if provided
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]
                
            # Initialize backtest state
            self.current_equity = initial_equity
            self.trades = []
            equity_curve = [initial_equity]
            timestamps = [data.index[0]]
            open_positions = []
            
            # Define strategy function (placeholder for actual strategy implementation)
            # In a real implementation, this would be loaded dynamically based on strategy_name
            def strategy_function(candle_data, position_size_pct):
                # Simple example strategy: buy if close > open, sell if close < open
                signal = None
                confidence = 0.5  # Default confidence
                
                if candle_data["close"] > candle_data["open"]:
                    signal = "buy"
                    # Higher confidence if price is significantly higher
                    confidence = min(0.9, 0.5 + (candle_data["close"] - candle_data["open"]) / candle_data["open"] * 10)
                elif candle_data["close"] < candle_data["open"]:
                    signal = "sell"
                    # Higher confidence if price is significantly lower
                    confidence = min(0.9, 0.5 + (candle_data["open"] - candle_data["close"]) / candle_data["open"] * 10)
                    
                return signal, confidence
                
            # Run backtest
            for i in range(1, len(data)):
                current_candle = data.iloc[i]
                previous_candle = data.iloc[i-1]
                
                # Get current timestamp
                current_time = data.index[i]
                
                # Execute strategy
                signal, confidence = strategy_function(current_candle, position_size)
                
                # Process open positions
                for pos in open_positions[:]:  # Use a copy for iteration while removing items
                    # Check if position should be closed
                    if (pos["type"] == "buy" and signal == "sell") or \
                       (pos["type"] == "sell" and signal == "buy") or \
                       (current_time - pos["open_time"]).total_seconds() / 3600 >= 24:  # Close after 24 hours
                        
                        # Calculate profit/loss
                        if pos["type"] == "buy":
                            profit_pct = (current_candle["close"] - pos["open_price"]) / pos["open_price"]
                        else:  # sell
                            profit_pct = (pos["open_price"] - current_candle["close"]) / pos["open_price"]
                            
                        # Apply commission and slippage
                        profit_pct -= commission + slippage
                        
                        # Calculate profit in currency
                        profit_amount = pos["position_size"] * profit_pct
                        
                        # Update equity
                        self.current_equity += profit_amount
                        
                        # Record trade
                        trade = {
                            "strategy": strategy_name,
                            "symbol": symbol,
                            "type": pos["type"],
                            "open_time": pos["open_time"],
                            "close_time": current_time,
                            "open_price": pos["open_price"],
                            "close_price": current_candle["close"],
                            "position_size": pos["position_size"],
                            "profit_loss": profit_amount,
                            "profit_loss_pct": profit_pct * 100,
                            "confidence": pos["confidence"],
                            "market_condition": "backtest"
                        }
                        
                        self.trades.append(trade)
                        
                        # Remove position
                        open_positions.remove(pos)
                
                # Open new position if signal is generated
                if signal and len(open_positions) < 1:  # Limit to 1 open position
                    # Calculate position size
                    if position_size is None:
                        # Use risk controller
                        pos_size_pct = self.risk_controller.get_position_size(strategy_name, symbol, confidence)
                    else:
                        pos_size_pct = position_size
                        
                    # Calculate position size in currency
                    pos_size = self.current_equity * pos_size_pct
                    
                    # Open position
                    position = {
                        "type": signal,
                        "open_time": current_time,
                        "open_price": current_candle["close"],
                        "position_size": pos_size,
                        "confidence": confidence
                    }
                    
                    open_positions.append(position)
                
                # Update equity curve
                equity_curve.append(self.current_equity)
                timestamps.append(current_time)
            
            # Close any remaining open positions at the end of the backtest
            for pos in open_positions:
                # Calculate profit/loss
                if pos["type"] == "buy":
                    profit_pct = (data.iloc[-1]["close"] - pos["open_price"]) / pos["open_price"]
                else:  # sell
                    profit_pct = (pos["open_price"] - data.iloc[-1]["close"]) / pos["open_price"]
                    
                # Apply commission and slippage
                profit_pct -= commission + slippage
                
                # Calculate profit in currency
                profit_amount = pos["position_size"] * profit_pct
                
                # Update equity
                self.current_equity += profit_amount
                
                # Record trade
                trade = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "type": pos["type"],
                    "open_time": pos["open_time"],
                    "close_time": data.index[-1],
                    "open_price": pos["open_price"],
                    "close_price": data.iloc[-1]["close"],
                    "position_size": pos["position_size"],
                    "profit_loss": profit_amount,
                    "profit_loss_pct": profit_pct * 100,
                    "confidence": pos["confidence"],
                    "market_condition": "backtest"
                }
                
                self.trades.append(trade)
            
            # Calculate backtest metrics
            backtest_results = self.calculate_backtest_metrics(equity_curve, timestamps, self.trades)
            
            # Add backtest parameters
            backtest_results["parameters"] = {
                "strategy": strategy_name,
                "symbol": symbol,
                "timeframe": timeframe,
                "start_date": str(data.index[0]),
                "end_date": str(data.index[-1]),
                "initial_equity": initial_equity,
                "position_size": position_size,
                "commission": commission,
                "slippage": slippage
            }
            
            # Save backtest results
            self.backtest_results[f"{strategy_name}_{symbol}_{timeframe}"] = backtest_results
            
            # Save results to file
            self.save_backtest_results(strategy_name, symbol, timeframe, backtest_results)
            
            # Generate charts
            self.generate_backtest_charts(strategy_name, symbol, timeframe, equity_curve, timestamps, self.trades)
            
            return backtest_results
        except Exception as e:
            logger.error(f"Error running strategy backtest: {e}")
            return {}
            
    def calculate_backtest_metrics(self, equity_curve: List[float], 
                                 timestamps: List[datetime],
                                 trades: List[Dict]) -> Dict:
        """Calculate backtest performance metrics

        Args:
            equity_curve (List[float]): Equity curve
            timestamps (List[datetime]): Timestamps for equity curve
            trades (List[Dict]): List of trades

        Returns:
            Dict: Backtest metrics
        """
        try:
            # Create equity curve DataFrame
            equity_df = pd.DataFrame({"equity": equity_curve, "timestamp": timestamps})
            equity_df = equity_df.set_index("timestamp")
            
            # Calculate returns
            equity_df["returns"] = equity_df["equity"].pct_change()
            
            # Calculate metrics
            metrics = {}
            
            # Basic metrics
            metrics["initial_equity"] = equity_curve[0]
            metrics["final_equity"] = equity_curve[-1]
            metrics["absolute_return"] = equity_curve[-1] - equity_curve[0]
            metrics["percent_return"] = (equity_curve[-1] / equity_curve[0] - 1) * 100
            metrics["trade_count"] = len(trades)
            
            # Win/loss metrics
            if trades:
                winning_trades = [t for t in trades if t["profit_loss"] > 0]
                losing_trades = [t for t in trades if t["profit_loss"] <= 0]
                
                metrics["winning_trades"] = len(winning_trades)
                metrics["losing_trades"] = len(losing_trades)
                metrics["win_rate"] = len(winning_trades) / len(trades) * 100 if trades else 0
                
                # Profit metrics
                if winning_trades:
                    metrics["avg_win"] = sum(t["profit_loss"] for t in winning_trades) / len(winning_trades)
                    metrics["max_win"] = max(t["profit_loss"] for t in winning_trades)
                else:
                    metrics["avg_win"] = 0
                    metrics["max_win"] = 0
                    
                if losing_trades:
                    metrics["avg_loss"] = sum(t["profit_loss"] for t in losing_trades) / len(losing_trades)
                    metrics["max_loss"] = min(t["profit_loss"] for t in losing_trades)
                else:
                    metrics["avg_loss"] = 0
                    metrics["max_loss"] = 0
                    
                # Profit factor
                total_profit = sum(t["profit_loss"] for t in winning_trades)
                total_loss = abs(sum(t["profit_loss"] for t in losing_trades))
                metrics["profit_factor"] = total_profit / total_loss if total_loss > 0 else float("inf")
                
                # Expectancy
                metrics["expectancy"] = (metrics["win_rate"] / 100 * metrics["avg_win"]) + \
                                      ((1 - metrics["win_rate"] / 100) * metrics["avg_loss"])
                                      
                # Average trade
                metrics["avg_trade"] = sum(t["profit_loss"] for t in trades) / len(trades)
                
                # Average holding time
                holding_times = [(t["close_time"] - t["open_time"]).total_seconds() / 3600 for t in trades]  # in hours
                metrics["avg_holding_time"] = sum(holding_times) / len(holding_times) if holding_times else 0
            else:
                # No trades
                metrics["winning_trades"] = 0
                metrics["losing_trades"] = 0
                metrics["win_rate"] = 0
                metrics["avg_win"] = 0
                metrics["max_win"] = 0
                metrics["avg_loss"] = 0
                metrics["max_loss"] = 0
                metrics["profit_factor"] = 0
                metrics["expectancy"] = 0
                metrics["avg_trade"] = 0
                metrics["avg_holding_time"] = 0
            
            # Drawdown metrics
            equity_df["peak"] = equity_df["equity"].cummax()
            equity_df["drawdown"] = (equity_df["equity"] - equity_df["peak"]) / equity_df["peak"] * 100
            
            metrics["max_drawdown"] = abs(equity_df["drawdown"].min())
            metrics["max_drawdown_date"] = str(equity_df["drawdown"].idxmin())
            
            # Calculate drawdown duration
            is_in_drawdown = equity_df["equity"] < equity_df["peak"]
            drawdown_periods = []
            current_period = None
            
            for i, (idx, in_dd) in enumerate(is_in_drawdown.items()):
                if in_dd and current_period is None:
                    current_period = {"start": idx}
                elif not in_dd and current_period is not None:
                    current_period["end"] = idx
                    drawdown_periods.append(current_period)
                    current_period = None
                    
            if current_period is not None:
                current_period["end"] = equity_df.index[-1]
                drawdown_periods.append(current_period)
                
            if drawdown_periods:
                drawdown_durations = [(p["end"] - p["start"]).total_seconds() / (24 * 3600) for p in drawdown_periods]  # in days
                metrics["max_drawdown_duration"] = max(drawdown_durations)
                metrics["avg_drawdown_duration"] = sum(drawdown_durations) / len(drawdown_durations)
            else:
                metrics["max_drawdown_duration"] = 0
                metrics["avg_drawdown_duration"] = 0
            
            # Risk-adjusted return metrics
            if len(equity_df) > 1:
                # Annualized return
                days = (equity_df.index[-1] - equity_df.index[0]).total_seconds() / (24 * 3600)
                metrics["annualized_return"] = ((equity_curve[-1] / equity_curve[0]) ** (365 / days) - 1) * 100 if days > 0 else 0
                
                # Sharpe ratio (assuming risk-free rate of 0%)
                daily_returns = equity_df["returns"].dropna()
                if len(daily_returns) > 0 and daily_returns.std() > 0:
                    metrics["sharpe_ratio"] = (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)  # Annualized
                else:
                    metrics["sharpe_ratio"] = 0
                    
                # Sortino ratio (downside deviation)
                negative_returns = daily_returns[daily_returns < 0]
                if len(negative_returns) > 0 and negative_returns.std() > 0:
                    metrics["sortino_ratio"] = (daily_returns.mean() / negative_returns.std()) * (252 ** 0.5)  # Annualized
                else:
                    metrics["sortino_ratio"] = 0
                    
                # Calmar ratio
                if metrics["max_drawdown"] > 0:
                    metrics["calmar_ratio"] = metrics["annualized_return"] / metrics["max_drawdown"]
                else:
                    metrics["calmar_ratio"] = 0
            else:
                metrics["annualized_return"] = 0
                metrics["sharpe_ratio"] = 0
                metrics["sortino_ratio"] = 0
                metrics["calmar_ratio"] = 0
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating backtest metrics: {e}")
            return {}
            
    def save_backtest_results(self, strategy_name: str, symbol: str, 
                            timeframe: str, results: Dict) -> bool:
        """Save backtest results to file

        Args:
            strategy_name (str): Strategy name
            symbol (str): Symbol
            timeframe (str): Timeframe
            results (Dict): Backtest results

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{strategy_name}_{symbol}_{timeframe}_{timestamp}.json"
            file_path = os.path.join(self.backtest_results_dir, filename)
            
            # Save results
            with open(file_path, "w") as f:
                # Convert datetime objects to strings
                results_copy = results.copy()
                if "trades" in results_copy:
                    for trade in results_copy["trades"]:
                        if isinstance(trade["open_time"], datetime):
                            trade["open_time"] = trade["open_time"].isoformat()
                        if isinstance(trade["close_time"], datetime):
                            trade["close_time"] = trade["close_time"].isoformat()
                
                json.dump(results_copy, f, indent=4)
                
            logger.info(f"Saved backtest results to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")
            return False
            
    def generate_backtest_charts(self, strategy_name: str, symbol: str, 
                               timeframe: str, equity_curve: List[float],
                               timestamps: List[datetime], trades: List[Dict]) -> bool:
        """Generate charts for backtest results

        Args:
            strategy_name (str): Strategy name
            symbol (str): Symbol
            timeframe (str): Timeframe
            equity_curve (List[float]): Equity curve
            timestamps (List[datetime]): Timestamps for equity curve
            trades (List[Dict]): List of trades

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Set up plot style
            plt.style.use("seaborn-v0_8-darkgrid")
            
            # Create equity curve chart
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps, equity_curve, label="Equity Curve")
            plt.title(f"Equity Curve - {strategy_name} on {symbol} ({timeframe})")
            plt.xlabel("Date")
            plt.ylabel("Equity")
            plt.grid(True)
            plt.legend()
            
            # Add trade markers
            for trade in trades:
                if trade["profit_loss"] > 0:
                    color = "green"
                    marker = "^"
                else:
                    color = "red"
                    marker = "v"
                    
                # Find closest timestamp in equity curve
                close_time = trade["close_time"]
                if isinstance(close_time, str):
                    close_time = datetime.fromisoformat(close_time)
                    
                # Find index of closest timestamp
                closest_idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - close_time))
                
                plt.scatter(timestamps[closest_idx], equity_curve[closest_idx], color=color, marker=marker, s=50)
            
            # Save chart
            equity_chart_path = os.path.join(self.backtest_charts_dir, f"equity_{strategy_name}_{symbol}_{timeframe}_{timestamp}.png")
            plt.savefig(equity_chart_path)
            plt.close()
            
            # Create drawdown chart
            equity_df = pd.DataFrame({"equity": equity_curve, "timestamp": timestamps})
            equity_df = equity_df.set_index("timestamp")
            equity_df["peak"] = equity_df["equity"].cummax()
            equity_df["drawdown"] = (equity_df["equity"] - equity_df["peak"]) / equity_df["peak"] * 100
            
            plt.figure(figsize=(12, 6))
            plt.fill_between(equity_df.index, equity_df["drawdown"], 0, color="red", alpha=0.3)
            plt.plot(equity_df.index, equity_df["drawdown"], color="red", label="Drawdown")
            plt.title(f"Drawdown - {strategy_name} on {symbol} ({timeframe})")
            plt.xlabel("Date")
            plt.ylabel("Drawdown (%)")
            plt.grid(True)
            plt.legend()
            
            # Save chart
            drawdown_chart_path = os.path.join(self.backtest_charts_dir, f"drawdown_{strategy_name}_{symbol}_{timeframe}_{timestamp}.png")
            plt.savefig(drawdown_chart_path)
            plt.close()
            
            # Create trade distribution chart
            if trades:
                # Extract profit/loss from trades
                profits = [t["profit_loss"] for t in trades]
                
                plt.figure(figsize=(12, 6))
                plt.hist(profits, bins=20, alpha=0.7, color="blue")
                plt.axvline(x=0, color="red", linestyle="--")
                plt.title(f"Trade Profit/Loss Distribution - {strategy_name} on {symbol} ({timeframe})")
                plt.xlabel("Profit/Loss")
                plt.ylabel("Frequency")
                plt.grid(True)
                
                # Save chart
                distribution_chart_path = os.path.join(self.backtest_charts_dir, f"distribution_{strategy_name}_{symbol}_{timeframe}_{timestamp}.png")
                plt.savefig(distribution_chart_path)
                plt.close()
                
                # Create monthly returns heatmap
                if len(equity_df) > 30:  # Only if we have enough data
                    # Calculate daily returns
                    equity_df["daily_return"] = equity_df["equity"].pct_change() * 100
                    
                    # Resample to monthly returns
                    monthly_returns = equity_df["daily_return"].resample("M").apply(lambda x: (1 + x / 100).prod() - 1) * 100
                    monthly_returns = monthly_returns.to_frame()
                    
                    # Create pivot table for heatmap
                    monthly_returns["year"] = monthly_returns.index.year
                    monthly_returns["month"] = monthly_returns.index.month
                    
                    # Only proceed if we have enough months
                    if len(monthly_returns) > 1:
                        pivot_table = monthly_returns.pivot_table(
                            values="daily_return", index="year", columns="month", aggfunc="sum"
                        )
                        
                        plt.figure(figsize=(12, 6))
                        sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="RdYlGn", center=0)
                        plt.title(f"Monthly Returns (%) - {strategy_name} on {symbol} ({timeframe})")
                        plt.xlabel("Month")
                        plt.ylabel("Year")
                        
                        # Save chart
                        monthly_chart_path = os.path.join(self.backtest_charts_dir, f"monthly_{strategy_name}_{symbol}_{timeframe}_{timestamp}.png")
                        plt.savefig(monthly_chart_path)
                        plt.close()
            
            logger.info(f"Generated backtest charts for {strategy_name} on {symbol} ({timeframe})")
            return True
        except Exception as e:
            logger.error(f"Error generating backtest charts: {e}")
            return False
            
    def run_monte_carlo_simulation(self, strategy_name: str, symbol: str, timeframe: str,
                                 num_simulations: int = 1000,
                                 confidence_level: float = 0.95) -> Dict:
        """Run Monte Carlo simulation on backtest results

        Args:
            strategy_name (str): Strategy name
            symbol (str): Symbol
            timeframe (str): Timeframe
            num_simulations (int): Number of simulations to run
            confidence_level (float): Confidence level for results

        Returns:
            Dict: Monte Carlo simulation results
        """
        try:
            # Get backtest results
            backtest_key = f"{strategy_name}_{symbol}_{timeframe}"
            if backtest_key not in self.backtest_results:
                logger.error(f"No backtest results found for {backtest_key}")
                return {}
                
            backtest_results = self.backtest_results[backtest_key]
            
            # Get trades
            trades = self.trades
            if not trades:
                logger.error(f"No trades found for {backtest_key}")
                return {}
                
            # Extract trade returns
            trade_returns = [t["profit_loss_pct"] / 100 for t in trades]  # Convert to decimal
            
            # Run simulations
            simulation_results = []
            initial_equity = backtest_results["parameters"]["initial_equity"]
            
            for _ in range(num_simulations):
                # Shuffle trade returns
                shuffled_returns = random.sample(trade_returns, len(trade_returns))
                
                # Calculate equity curve
                equity = initial_equity
                equity_curve = [equity]
                
                for ret in shuffled_returns:
                    equity *= (1 + ret)
                    equity_curve.append(equity)
                    
                # Calculate metrics
                final_equity = equity_curve[-1]
                total_return = (final_equity / initial_equity - 1) * 100
                
                # Calculate drawdown
                peak = initial_equity
                drawdown = 0
                
                for eq in equity_curve:
                    if eq > peak:
                        peak = eq
                    dd = (peak - eq) / peak * 100
                    drawdown = max(drawdown, dd)
                    
                simulation_results.append({
                    "final_equity": final_equity,
                    "total_return": total_return,
                    "max_drawdown": drawdown
                })
            
            # Calculate statistics
            final_equities = [r["final_equity"] for r in simulation_results]
            total_returns = [r["total_return"] for r in simulation_results]
            max_drawdowns = [r["max_drawdown"] for r in simulation_results]
            
            # Sort results
            final_equities.sort()
            total_returns.sort()
            max_drawdowns.sort()
            
            # Calculate confidence intervals
            lower_idx = int((1 - confidence_level) / 2 * num_simulations)
            upper_idx = int((1 + confidence_level) / 2 * num_simulations)
            
            # Ensure indices are within bounds
            lower_idx = max(0, lower_idx)
            upper_idx = min(num_simulations - 1, upper_idx)
            
            # Calculate results
            monte_carlo_results = {
                "num_simulations": num_simulations,
                "confidence_level": confidence_level,
                "equity": {
                    "mean": sum(final_equities) / num_simulations,
                    "median": final_equities[num_simulations // 2],
                    "min": min(final_equities),
                    "max": max(final_equities),
                    "lower_bound": final_equities[lower_idx],
                    "upper_bound": final_equities[upper_idx]
                },
                "return": {
                    "mean": sum(total_returns) / num_simulations,
                    "median": total_returns[num_simulations // 2],
                    "min": min(total_returns),
                    "max": max(total_returns),
                    "lower_bound": total_returns[lower_idx],
                    "upper_bound": total_returns[upper_idx]
                },
                "drawdown": {
                    "mean": sum(max_drawdowns) / num_simulations,
                    "median": max_drawdowns[num_simulations // 2],
                    "min": min(max_drawdowns),
                    "max": max(max_drawdowns),
                    "lower_bound": max_drawdowns[lower_idx],
                    "upper_bound": max_drawdowns[upper_idx]
                }
            }
            
            # Generate Monte Carlo charts
            self.generate_monte_carlo_charts(strategy_name, symbol, timeframe, simulation_results, confidence_level)
            
            return monte_carlo_results
        except Exception as e:
            logger.error(f"Error running Monte Carlo simulation: {e}")
            return {}
            
    def generate_monte_carlo_charts(self, strategy_name: str, symbol: str, 
                                  timeframe: str, simulation_results: List[Dict],
                                  confidence_level: float) -> bool:
        """Generate charts for Monte Carlo simulation results

        Args:
            strategy_name (str): Strategy name
            symbol (str): Symbol
            timeframe (str): Timeframe
            simulation_results (List[Dict]): Simulation results
            confidence_level (float): Confidence level

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Set up plot style
            plt.style.use("seaborn-v0_8-darkgrid")
            
            # Create histogram of final equity
            plt.figure(figsize=(12, 6))
            final_equities = [r["final_equity"] for r in simulation_results]
            plt.hist(final_equities, bins=50, alpha=0.7, color="blue")
            plt.axvline(x=sum(final_equities) / len(final_equities), color="red", linestyle="--", label="Mean")
            plt.title(f"Monte Carlo Simulation - Final Equity Distribution\n{strategy_name} on {symbol} ({timeframe})")
            plt.xlabel("Final Equity")
            plt.ylabel("Frequency")
            plt.grid(True)
            plt.legend()
            
            # Save chart
            equity_chart_path = os.path.join(self.backtest_charts_dir, f"mc_equity_{strategy_name}_{symbol}_{timeframe}_{timestamp}.png")
            plt.savefig(equity_chart_path)
            plt.close()
            
            # Create histogram of max drawdown
            plt.figure(figsize=(12, 6))
            max_drawdowns = [r["max_drawdown"] for r in simulation_results]
            plt.hist(max_drawdowns, bins=50, alpha=0.7, color="red")
            plt.axvline(x=sum(max_drawdowns) / len(max_drawdowns), color="blue", linestyle="--", label="Mean")
            plt.title(f"Monte Carlo Simulation - Max Drawdown Distribution\n{strategy_name} on {symbol} ({timeframe})")
            plt.xlabel("Max Drawdown (%)")
            plt.ylabel("Frequency")
            plt.grid(True)
            plt.legend()
            
            # Save chart
            drawdown_chart_path = os.path.join(self.backtest_charts_dir, f"mc_drawdown_{strategy_name}_{symbol}_{timeframe}_{timestamp}.png")
            plt.savefig(drawdown_chart_path)
            plt.close()
            
            # Create scatter plot of return vs drawdown
            plt.figure(figsize=(12, 6))
            returns = [r["total_return"] for r in simulation_results]
            plt.scatter(max_drawdowns, returns, alpha=0.5)
            plt.title(f"Monte Carlo Simulation - Return vs Drawdown\n{strategy_name} on {symbol} ({timeframe})")
            plt.xlabel("Max Drawdown (%)")
            plt.ylabel("Total Return (%)")
            plt.grid(True)
            
            # Save chart
            scatter_chart_path = os.path.join(self.backtest_charts_dir, f"mc_scatter_{strategy_name}_{symbol}_{timeframe}_{timestamp}.png")
            plt.savefig(scatter_chart_path)
            plt.close()
            
            logger.info(f"Generated Monte Carlo charts for {strategy_name} on {symbol} ({timeframe})")
            return True
        except Exception as e:
            logger.error(f"Error generating Monte Carlo charts: {e}")
            return False
            
    def optimize_strategy_parameters(self, strategy_name: str, symbol: str, timeframe: str,
                                   parameters: Dict[str, List[Any]],
                                   optimization_metric: str = "profit_factor",
                                   num_tests: int = 10) -> Dict:
        """Optimize strategy parameters using grid search

        Args:
            strategy_name (str): Strategy name
            symbol (str): Symbol
            timeframe (str): Timeframe
            parameters (Dict[str, List[Any]]): Parameters to optimize and their possible values
            optimization_metric (str): Metric to optimize for
            num_tests (int): Number of top parameter sets to test

        Returns:
            Dict: Optimization results
        """
        # This is a placeholder for actual parameter optimization
        # In a real implementation, this would run backtests with different parameter combinations
        return {}


# Helper functions
def calculate_sharpe_ratio(strategy_name: str, symbol: str, timeframe: str,
                       risk_free_rate: float = 0.0,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> float:
    """Calculate the Sharpe ratio for a strategy

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Symbol to calculate for
        timeframe (str): Timeframe to calculate for
        risk_free_rate (float): Annual risk-free rate (default: 0.0)
        start_date (Optional[str]): Start date for calculation
        end_date (Optional[str]): End date for calculation

    Returns:
        float: Sharpe ratio
    """
    engine = BacktestEngine()
    
    # Run backtest to get results
    results = engine.run_strategy_backtest(
        strategy_name, symbol, timeframe, start_date, end_date
    )
    
    # Check if backtest was successful
    if not results or "sharpe_ratio" not in results:
        logger.error(f"Failed to calculate Sharpe ratio for {strategy_name} on {symbol} ({timeframe})")
        return 0.0
    
    # Return Sharpe ratio
    return results["sharpe_ratio"]

def calculate_sortino_ratio(strategy_name: str, symbol: str, timeframe: str,
                         risk_free_rate: float = 0.0,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> float:
    """Calculate the Sortino ratio for a strategy

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Symbol to calculate for
        timeframe (str): Timeframe to calculate for
        risk_free_rate (float): Annual risk-free rate (default: 0.0)
        start_date (Optional[str]): Start date for calculation
        end_date (Optional[str]): End date for calculation

    Returns:
        float: Sortino ratio
    """
    engine = BacktestEngine()
    
    # Run backtest to get results
    results = engine.run_strategy_backtest(
        strategy_name, symbol, timeframe, start_date, end_date
    )
    
    # Check if backtest was successful
    if not results or "sortino_ratio" not in results:
        logger.error(f"Failed to calculate Sortino ratio for {strategy_name} on {symbol} ({timeframe})")
        return 0.0
    
    # Return Sortino ratio
    return results["sortino_ratio"]

def calculate_calmar_ratio(strategy_name: str, symbol: str, timeframe: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> float:
    """Calculate the Calmar ratio for a strategy (annualized return / maximum drawdown)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Symbol to calculate for
        timeframe (str): Timeframe to calculate for
        start_date (Optional[str]): Start date for calculation
        end_date (Optional[str]): End date for calculation

    Returns:
        float: Calmar ratio
    """
    engine = BacktestEngine()
    
    # Run backtest to get results
    results = engine.run_strategy_backtest(
        strategy_name, symbol, timeframe, start_date, end_date
    )
    
    # Check if backtest was successful
    if not results:
        logger.error(f"Failed to calculate Calmar ratio for {strategy_name} on {symbol} ({timeframe})")
        return 0.0
    
    # Get annualized return and max drawdown
    annualized_return = results.get("annualized_return", 0.0)
    max_drawdown = results.get("max_drawdown", 0.0)
    
    # Calculate Calmar ratio
    if max_drawdown > 0:
        calmar_ratio = annualized_return / max_drawdown
    else:
        # If no drawdown, return a high value (but not infinity)
        calmar_ratio = 100.0 if annualized_return > 0 else 0.0
    
    return calmar_ratio

def calculate_recovery_factor(strategy_name: str, symbol: str, timeframe: str,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> float:
    """Calculate the recovery factor for a strategy (net profit / max drawdown)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Symbol to calculate for
        timeframe (str): Timeframe to calculate for
        start_date (Optional[str]): Start date for calculation
        end_date (Optional[str]): End date for calculation

    Returns:
        float: Recovery factor (net profit / max drawdown)
    """
    engine = BacktestEngine()
    
    # Run backtest to get results
    results = engine.run_strategy_backtest(
        strategy_name, symbol, timeframe, start_date, end_date
    )
    
    # Check if backtest was successful
    if not results or "metrics" not in results:
        logger.error(f"Failed to calculate recovery factor for {strategy_name} on {symbol} ({timeframe})")
        return 0.0
    
    # Extract metrics
    metrics = results["metrics"]
    
    # Calculate recovery factor
    net_profit = metrics.get("net_profit", 0.0)
    max_drawdown_pct = metrics.get("max_drawdown_percent", 0.0)
    
    # Avoid division by zero
    if max_drawdown_pct == 0.0:
        return 0.0
    
    recovery_factor = abs(net_profit / max_drawdown_pct) if max_drawdown_pct != 0 else 0.0
    
    return recovery_factor

def calculate_max_consecutive_losses(strategy_name: str, symbol: str, timeframe: str,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> int:
    """Calculate the maximum consecutive losses for a strategy

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Symbol to calculate for
        timeframe (str): Timeframe to calculate for
        start_date (Optional[str]): Start date for calculation
        end_date (Optional[str]): End date for calculation

    Returns:
        int: Maximum consecutive losses
    """
    engine = BacktestEngine()
    
    # Run backtest to get results
    results = engine.run_strategy_backtest(
        strategy_name, symbol, timeframe, start_date, end_date
    )
    
    # Check if backtest was successful and has trades
    if not results or "trades" not in results or not results["trades"]:
        logger.error(f"Failed to calculate max consecutive losses for {strategy_name} on {symbol} ({timeframe})")
        return 0
    
    # Extract trade results
    trades = results["trades"]
    
    # Calculate consecutive losses
    max_consecutive = 0
    current_consecutive = 0
    
    for trade in trades:
        if trade["profit_loss"] <= 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive

def run_backtest(strategy_name: str, symbol: str, timeframe: str,
                start_date: Optional[str] = None,
                end_date: Optional[str] = None,
                initial_equity: float = 10000.0,
                position_size: Optional[float] = None) -> Dict:
    """Run a backtest for a strategy (helper function)

    Args:
        strategy_name (str): Name of the strategy to backtest
        symbol (str): Symbol to backtest on
        timeframe (str): Timeframe to backtest on
        start_date (Optional[str]): Start date for backtest
        end_date (Optional[str]): End date for backtest
        initial_equity (float): Initial equity for backtest
        position_size (Optional[float]): Fixed position size

    Returns:
        Dict: Backtest results
    """
    engine = BacktestEngine()
    return engine.run_strategy_backtest(
        strategy_name, symbol, timeframe, start_date, end_date, initial_equity, position_size
    )


def generate_synthetic_data(symbol: str, timeframe: str = "H1",
                          start_date: str = "2020-01-01",
                          end_date: str = "2020-12-31") -> bool:
    """Generate synthetic price data for testing (helper function)

    Args:
        symbol (str): Symbol to generate data for
        timeframe (str): Timeframe of the data
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format

    Returns:
        bool: True if successful, False otherwise
    """
    engine = BacktestEngine()
    data = engine.generate_synthetic_data(symbol, timeframe, start_date, end_date)
    return not data.empty


def compare_strategies(strategies: List[str], symbol: str, timeframe: str,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> pd.DataFrame:
    """Compare multiple strategies based on performance metrics

    Args:
        strategies (List[str]): List of strategy names to compare
        symbol (str): Symbol to backtest on
        timeframe (str): Timeframe to backtest on
        start_date (Optional[str]): Start date for backtest
        end_date (Optional[str]): End date for backtest

    Returns:
        pd.DataFrame: Comparison of strategy performance metrics
    """
    engine = BacktestEngine()
    comparison_data = []
    
    for strategy_name in strategies:
        # Run backtest
        results = engine.run_strategy_backtest(
            strategy_name, symbol, timeframe, start_date, end_date
        )
        
        if not results:
            logger.error(f"Failed to get results for {strategy_name}")
            continue
            
        # Extract key metrics
        metrics = {
            "strategy": strategy_name,
            "total_return": results.get("percent_return", 0),
            "sharpe_ratio": results.get("sharpe_ratio", 0),
            "sortino_ratio": results.get("sortino_ratio", 0),
            "calmar_ratio": results.get("calmar_ratio", 0),
            "recovery_factor": calculate_recovery_factor(strategy_name, symbol, timeframe, start_date, end_date),
            "max_drawdown": results.get("max_drawdown", 0),
            "win_rate": results.get("win_rate", 0),
            "profit_factor": results.get("profit_factor", 0),
            "max_consecutive_losses": calculate_max_consecutive_losses(strategy_name, symbol, timeframe, start_date, end_date),
            "trade_count": results.get("trade_count", 0)
        }
        
        comparison_data.append(metrics)
    
    # Create DataFrame
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        df = df.set_index("strategy")
        return df
    else:
        return pd.DataFrame()


def visualize_strategy_comparison(strategies: List[str], symbol: str, timeframe: str,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               metrics_to_plot: Optional[List[str]] = None,
                               save_path: Optional[str] = None) -> None:
    """Visualize comparison of multiple strategies using a radar chart

    Args:
        strategies (List[str]): List of strategy names to compare
        symbol (str): Symbol to backtest on
        timeframe (str): Timeframe to backtest on
        start_date (Optional[str]): Start date for backtest
        end_date (Optional[str]): End date for backtest
        metrics_to_plot (Optional[List[str]]): List of metrics to include in the radar chart
            (defaults to total_return, sharpe_ratio, sortino_ratio, calmar_ratio, recovery_factor, win_rate, profit_factor)
        save_path (Optional[str]): Path to save the chart (if None, display only)
    """
    try:
        # Get comparison data
        comparison_df = compare_strategies(strategies, symbol, timeframe, start_date, end_date)
        
        if comparison_df.empty:
            logger.error("No data available for strategy comparison")
            return
            
        # Select metrics for radar chart
        if metrics_to_plot is None:
            metrics_to_plot = ["total_return", "sharpe_ratio", "sortino_ratio", "calmar_ratio", 
                          "recovery_factor", "win_rate", "profit_factor"]
        
        # Filter to available metrics
        metrics = [m for m in metrics_to_plot if m in comparison_df.columns]
        
        if not metrics:
            logger.error("No metrics available for radar chart")
            return
            
        # Normalize data for radar chart (0-1 scale)
        radar_df = comparison_df[metrics].copy()
        for col in radar_df.columns:
            if radar_df[col].min() < 0:
                # Handle negative values
                min_val = radar_df[col].min()
                max_val = radar_df[col].max()
                radar_df[col] = (radar_df[col] - min_val) / (max_val - min_val) if max_val > min_val else 0
            else:
                # For positive values
                max_val = radar_df[col].max()
                radar_df[col] = radar_df[col] / max_val if max_val > 0 else 0
        
        # Create radar chart
        num_metrics = len(metrics)
        angles = np.linspace(0, 2*np.pi, num_metrics, endpoint=False).tolist()
        angles += angles[:1]  # Close the loop
        
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
        
        # Add metric labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics)
        
        # Plot each strategy
        for strategy in radar_df.index:
            values = radar_df.loc[strategy].values.tolist()
            values += values[:1]  # Close the loop
            ax.plot(angles, values, linewidth=2, label=strategy)
            ax.fill(angles, values, alpha=0.1)
        
        ax.set_title(f"Strategy Comparison - {symbol} ({timeframe})")
        plt.legend(loc='upper right')
        
        # Save or display
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved strategy comparison chart to {save_path}")
        else:
            plt.tight_layout()
            plt.show()
            
    except Exception as e:
        logger.error(f"Error visualizing strategy comparison: {e}")


# For testing
if __name__ == "__main__":
    # Create backtest engine
    engine = BacktestEngine()
    
    # Generate synthetic data for multiple symbols
    print("Generating synthetic data...")
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    for symbol in symbols:
        engine.generate_synthetic_data(symbol, "H1", "2020-01-01", "2020-12-31")
    
    # Define test strategies
    strategies = ["trend_following", "mean_reversion", "breakout"]
    
    # Run backtest for a single strategy
    print("\nRunning backtest for trend_following strategy...")
    results = engine.run_strategy_backtest(
        "trend_following", "EURUSD", "H1", 
        start_date="2020-01-01", end_date="2020-12-31",
        initial_equity=10000.0, position_size=0.01
    )
    
    # Print backtest metrics
    print("\nBacktest Metrics:")
    for key, value in results.items():
        if key != "parameters":
            print(f"{key}: {value}")
    
    # Calculate and print risk metrics
    print("\nRisk Metrics:")
    sharpe = calculate_sharpe_ratio("trend_following", "EURUSD", "H1")
    sortino = calculate_sortino_ratio("trend_following", "EURUSD", "H1")
    calmar = calculate_calmar_ratio("trend_following", "EURUSD", "H1")
    recovery = calculate_recovery_factor("trend_following", "EURUSD", "H1")
    max_cons_losses = calculate_max_consecutive_losses("trend_following", "EURUSD", "H1")
    
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Sortino Ratio: {sortino:.2f}")
    print(f"Calmar Ratio: {calmar:.2f}")
    print(f"Recovery Factor: {recovery:.2f}")
    print(f"Maximum Consecutive Losses: {max_cons_losses}")
    
    # Run Monte Carlo simulation
    print("\nRunning Monte Carlo simulation...")
    mc_results = engine.run_monte_carlo_simulation("trend_following", "EURUSD", "H1")
    
    # Print Monte Carlo results
    print("\nMonte Carlo Results:")
    print(f"Mean Final Equity: {mc_results['equity']['mean']:.2f}")
    print(f"Mean Return: {mc_results['return']['mean']:.2f}%")
    print(f"Mean Max Drawdown: {mc_results['drawdown']['mean']:.2f}%")
    print(f"95% Confidence Interval for Final Equity: [{mc_results['equity']['lower_bound']:.2f}, {mc_results['equity']['upper_bound']:.2f}]")
    
    # Example of strategy comparison
    print("\nComparing strategies...")
    comparison_df = compare_strategies(strategies, "EURUSD", "H1")
    print("\nStrategy Comparison:")
    print(comparison_df)
    
    # Example of strategy visualization
    print("\nGenerating strategy comparison visualization...")
    chart_path = os.path.join(BACKTEST_CHARTS_DIR, "strategy_comparison.png")
    visualize_strategy_comparison(strategies, "EURUSD", "H1", save_path=chart_path)
    print(f"Strategy comparison chart saved to {chart_path}")
    
    print("\nBacktesting complete!")
    print(f"Results saved to {BACKTEST_RESULTS_DIR}")
    print(f"Charts saved to {BACKTEST_CHARTS_DIR}")