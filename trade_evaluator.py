# trade_evaluator.py

import json
import logging
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("trade_evaluator")

# Constants
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)


class TradePerformanceEvaluator:
    """Evaluates trading performance and provides feedback for strategy optimization"""

    def __init__(self, trade_history_file: str = TRADE_HISTORY_FILE, 
                 strategy_stats_file: str = STRATEGY_STATS_FILE):
        """Initialize the trade evaluator

        Args:
            trade_history_file (str): Path to the trade history file
            strategy_stats_file (str): Path to the strategy statistics file
        """
        self.trade_history_file = trade_history_file
        self.strategy_stats_file = strategy_stats_file
        self.trade_history = self.load_trade_history()
        self.strategy_stats = self.load_strategy_stats()

    def load_trade_history(self) -> List[Dict]:
        """Load trade history from file or create empty history

        Returns:
            List[Dict]: List of trade records
        """
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, "r") as f:
                    return json.load(f)
            else:
                logger.info(f"Trade history file {self.trade_history_file} not found. Creating new history.")
                return []
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return []

    def load_strategy_stats(self) -> Dict:
        """Load strategy statistics from file or create empty stats

        Returns:
            Dict: Strategy statistics
        """
        try:
            if os.path.exists(self.strategy_stats_file):
                with open(self.strategy_stats_file, "r") as f:
                    return json.load(f)
            else:
                logger.info(f"Strategy stats file {self.strategy_stats_file} not found. Creating new stats.")
                return {}
        except Exception as e:
            logger.error(f"Error loading strategy stats: {e}")
            return {}

    def save_trade_history(self) -> bool:
        """Save trade history to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.trade_history_file, "w") as f:
                json.dump(self.trade_history, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving trade history: {e}")
            return False

    def save_strategy_stats(self) -> bool:
        """Save strategy statistics to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.strategy_stats_file, "w") as f:
                json.dump(self.strategy_stats, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy stats: {e}")
            return False

    def record_trade(self, strategy_name: str, symbol: str, direction: str, 
                     entry_price: float, exit_price: float, profit_loss: float,
                     lot_size: float, news_avoided: bool, market_condition: str,
                     entry_time: Optional[str] = None, exit_time: Optional[str] = None,
                     trade_duration: Optional[float] = None, tags: Optional[List[str]] = None) -> Dict:
        """Record a trade and update strategy statistics

        Args:
            strategy_name (str): Name of the trading strategy
            symbol (str): Trading symbol/pair
            direction (str): Trade direction ('buy' or 'sell')
            entry_price (float): Entry price
            exit_price (float): Exit price
            profit_loss (float): Profit or loss amount
            lot_size (float): Lot size or contract size
            news_avoided (bool): Whether news filtering was active
            market_condition (str): Market condition during trade
            entry_time (Optional[str]): Entry time (ISO format)
            exit_time (Optional[str]): Exit time (ISO format)
            trade_duration (Optional[float]): Trade duration in minutes
            tags (Optional[List[str]]): List of tags for the trade

        Returns:
            Dict: The recorded trade
        """
        # Create trade record
        trade = {
            "strategy": strategy_name,
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "profit_loss": profit_loss,
            "lot_size": lot_size,
            "news_avoided": news_avoided,
            "market_condition": market_condition,
            "entry_time": entry_time or datetime.utcnow().isoformat(),
            "exit_time": exit_time,
            "trade_duration": trade_duration,
            "tags": tags or [],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to trade history
        self.trade_history.append(trade)
        self.save_trade_history()

        # Update strategy statistics
        self.update_strategy_stats(trade)

        return trade

    def update_strategy_stats(self, trade: Dict) -> None:
        """Update strategy statistics based on a new trade

        Args:
            trade (Dict): Trade record
        """
        strategy_name = trade["strategy"]

        # Initialize strategy stats if not exists
        if strategy_name not in self.strategy_stats:
            self.strategy_stats[strategy_name] = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_profit_loss": 0.0,
                "win_rate": 0.0,
                "average_profit": 0.0,
                "average_loss": 0.0,
                "profit_factor": 0.0,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0,
                "trades_with_news_avoided": 0,
                "trades_by_market_condition": {},
                "last_50_trades": [],
                "confidence_score": 50.0  # Default confidence score
            }

        stats = self.strategy_stats[strategy_name]

        # Update basic counts
        stats["total_trades"] += 1
        profit_loss = trade["profit_loss"]
        stats["total_profit_loss"] += profit_loss

        # Update win/loss counts and streaks
        if profit_loss > 0:
            stats["winning_trades"] += 1
            stats["consecutive_wins"] += 1
            stats["consecutive_losses"] = 0
            if stats["consecutive_wins"] > stats["max_consecutive_wins"]:
                stats["max_consecutive_wins"] = stats["consecutive_wins"]
        else:
            stats["losing_trades"] += 1
            stats["consecutive_losses"] += 1
            stats["consecutive_wins"] = 0
            if stats["consecutive_losses"] > stats["max_consecutive_losses"]:
                stats["max_consecutive_losses"] = stats["consecutive_losses"]

        # Update win rate
        stats["win_rate"] = (stats["winning_trades"] / stats["total_trades"]) * 100

        # Update news avoided count
        if trade["news_avoided"]:
            stats["trades_with_news_avoided"] += 1

        # Update market condition stats
        market_condition = trade["market_condition"]
        if market_condition not in stats["trades_by_market_condition"]:
            stats["trades_by_market_condition"][market_condition] = {
                "count": 0,
                "wins": 0,
                "losses": 0,
                "profit_loss": 0.0
            }

        condition_stats = stats["trades_by_market_condition"][market_condition]
        condition_stats["count"] += 1
        condition_stats["profit_loss"] += profit_loss
        if profit_loss > 0:
            condition_stats["wins"] += 1
        else:
            condition_stats["losses"] += 1

        # Update last 50 trades list
        stats["last_50_trades"].append({
            "profit_loss": profit_loss,
            "news_avoided": trade["news_avoided"],
            "market_condition": market_condition
        })

        # Keep only the last 50 trades
        if len(stats["last_50_trades"]) > 50:
            stats["last_50_trades"] = stats["last_50_trades"][-50:]

        # Calculate average profit and loss
        winning_trades = [t for t in self.trade_history if t["strategy"] == strategy_name and t["profit_loss"] > 0]
        losing_trades = [t for t in self.trade_history if t["strategy"] == strategy_name and t["profit_loss"] <= 0]

        if winning_trades:
            stats["average_profit"] = sum(t["profit_loss"] for t in winning_trades) / len(winning_trades)
        if losing_trades:
            stats["average_loss"] = sum(t["profit_loss"] for t in losing_trades) / len(losing_trades)

        # Calculate profit factor
        total_profit = sum(t["profit_loss"] for t in winning_trades)
        total_loss = abs(sum(t["profit_loss"] for t in losing_trades))
        if total_loss > 0:
            stats["profit_factor"] = total_profit / total_loss
        else:
            stats["profit_factor"] = total_profit if total_profit > 0 else 0

        # Update confidence score
        self.update_confidence_score(strategy_name)

        # Save updated stats
        self.save_strategy_stats()

    def update_confidence_score(self, strategy_name: str) -> float:
        """Update and return the confidence score for a strategy

        Args:
            strategy_name (str): Name of the trading strategy

        Returns:
            float: Updated confidence score (0-100)
        """
        if strategy_name not in self.strategy_stats:
            return 50.0  # Default score for unknown strategy

        stats = self.strategy_stats[strategy_name]

        # Base score on win rate (0-50 points)
        win_rate_score = min(50, stats["win_rate"])

        # Profit factor contribution (0-20 points)
        profit_factor = stats["profit_factor"]
        if profit_factor >= 2.0:
            profit_factor_score = 20
        elif profit_factor >= 1.5:
            profit_factor_score = 15
        elif profit_factor >= 1.0:
            profit_factor_score = 10
        else:
            profit_factor_score = 0

        # Recent performance (last 10 trades) (0-20 points)
        recent_trades = stats["last_50_trades"][-10:] if len(stats["last_50_trades"]) >= 10 else stats["last_50_trades"]
        if recent_trades:
            recent_win_rate = len([t for t in recent_trades if t["profit_loss"] > 0]) / len(recent_trades) * 100
            recent_score = min(20, recent_win_rate / 5)  # Max 20 points for 100% win rate
        else:
            recent_score = 0

        # Consistency factor (0-10 points)
        # Penalize for long losing streaks
        consistency_score = 10 - min(10, stats["max_consecutive_losses"])

        # Calculate final confidence score
        confidence_score = win_rate_score + profit_factor_score + recent_score + consistency_score
        
        # Update the stored confidence score
        stats["confidence_score"] = confidence_score
        self.save_strategy_stats()

        return confidence_score

    def get_strategy_performance(self, strategy_name: str) -> Dict:
        """Get performance metrics for a specific strategy

        Args:
            strategy_name (str): Name of the trading strategy

        Returns:
            Dict: Strategy performance metrics
        """
        if strategy_name not in self.strategy_stats:
            return {"error": f"Strategy '{strategy_name}' not found"}

        return self.strategy_stats[strategy_name]

    def get_all_strategies_performance(self) -> Dict:
        """Get performance metrics for all strategies

        Returns:
            Dict: Performance metrics for all strategies
        """
        return self.strategy_stats

    def get_risk_recommendation(self, strategy_name: str) -> Dict:
        """Get risk management recommendations for a strategy

        Args:
            strategy_name (str): Name of the trading strategy

        Returns:
            Dict: Risk management recommendations
        """
        if strategy_name not in self.strategy_stats:
            return {
                "action": "maintain",
                "reason": f"Strategy '{strategy_name}' not found"
            }

        stats = self.strategy_stats[strategy_name]

        # Check for high win rate over last 50 trades
        last_50_win_rate = 0
        if stats["last_50_trades"]:
            wins = len([t for t in stats["last_50_trades"] if t["profit_loss"] > 0])
            last_50_win_rate = (wins / len(stats["last_50_trades"])) * 100

        # Check for consecutive losses
        consecutive_losses = stats["consecutive_losses"]

        # Make recommendation
        if last_50_win_rate > 60 and stats["total_trades"] >= 50:
            return {
                "action": "increase",
                "reason": f"Win rate over last 50 trades is {last_50_win_rate:.1f}%",
                "suggested_adjustment": 1.2  # Increase risk by 20%
            }
        elif consecutive_losses >= 3:
            return {
                "action": "decrease",
                "reason": f"Currently on a {consecutive_losses} trade losing streak",
                "suggested_adjustment": 0.5  # Decrease risk by 50%
            }
        else:
            return {
                "action": "maintain",
                "reason": "Current performance is within acceptable parameters"
            }

    def calculate_daily_drawdown(self, date: Optional[str] = None) -> float:
        """Calculate the drawdown for a specific day

        Args:
            date (Optional[str]): Date in ISO format (YYYY-MM-DD). Defaults to today.

        Returns:
            float: Daily drawdown percentage
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        # Filter trades for the specified date
        daily_trades = [t for t in self.trade_history if t["entry_time"].startswith(date)]

        if not daily_trades:
            return 0.0

        # Calculate total profit/loss for the day
        total_pnl = sum(t["profit_loss"] for t in daily_trades)

        # Calculate drawdown as percentage of negative P&L relative to account size
        # Note: This is a simplified calculation. In a real system, you would use the actual account balance.
        account_size = 10000.0  # Placeholder for account size
        drawdown_percentage = abs(min(0, total_pnl)) / account_size * 100

        return drawdown_percentage

    def should_pause_trading(self) -> Tuple[bool, str]:
        """Determine if trading should be paused based on risk metrics

        Returns:
            Tuple[bool, str]: (should_pause, reason)
        """
        # Check daily drawdown
        daily_drawdown = self.calculate_daily_drawdown()
        if daily_drawdown > 2.0:
            return True, f"Daily drawdown of {daily_drawdown:.2f}% exceeds 2% threshold"

        # Check for excessive consecutive losses across all strategies
        for strategy_name, stats in self.strategy_stats.items():
            if stats["consecutive_losses"] >= 5:
                return True, f"Strategy '{strategy_name}' has {stats['consecutive_losses']} consecutive losses"

        return False, "No risk thresholds exceeded"


# Helper functions
def record_trade(strategy_name: str, symbol: str, direction: str, 
                entry_price: float, exit_price: float, profit_loss: float,
                lot_size: float, news_avoided: bool, market_condition: str,
                entry_time: Optional[str] = None, exit_time: Optional[str] = None) -> Dict:
    """Record a trade and update strategy statistics (helper function)

    Args:
        strategy_name (str): Name of the trading strategy
        symbol (str): Trading symbol/pair
        direction (str): Trade direction ('buy' or 'sell')
        entry_price (float): Entry price
        exit_price (float): Exit price
        profit_loss (float): Profit or loss amount
        lot_size (float): Lot size or contract size
        news_avoided (bool): Whether news filtering was active
        market_condition (str): Market condition during trade
        entry_time (Optional[str]): Entry time (ISO format)
        exit_time (Optional[str]): Exit time (ISO format)

    Returns:
        Dict: The recorded trade
    """
    evaluator = TradePerformanceEvaluator()
    return evaluator.record_trade(
        strategy_name=strategy_name,
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        exit_price=exit_price,
        profit_loss=profit_loss,
        lot_size=lot_size,
        news_avoided=news_avoided,
        market_condition=market_condition,
        entry_time=entry_time,
        exit_time=exit_time
    )


def get_risk_recommendation(strategy_name: str) -> Dict:
    """Get risk management recommendations for a strategy (helper function)

    Args:
        strategy_name (str): Name of the trading strategy

    Returns:
        Dict: Risk management recommendations
    """
    evaluator = TradePerformanceEvaluator()
    return evaluator.get_risk_recommendation(strategy_name)


def should_pause_trading() -> Tuple[bool, str]:
    """Determine if trading should be paused based on risk metrics (helper function)

    Returns:
        Tuple[bool, str]: (should_pause, reason)
    """
    evaluator = TradePerformanceEvaluator()
    return evaluator.should_pause_trading()


# For testing
if __name__ == "__main__":
    # Create an instance of the evaluator
    evaluator = TradePerformanceEvaluator()
    
    # Record some test trades
    print("Recording test trades...")
    
    # Winning trade for Strategy A
    evaluator.record_trade(
        strategy_name="Strategy_A",
        symbol="EURUSD",
        direction="buy",
        entry_price=1.1000,
        exit_price=1.1050,
        profit_loss=50.0,
        lot_size=0.1,
        news_avoided=True,
        market_condition="trending"
    )
    
    # Losing trade for Strategy A
    evaluator.record_trade(
        strategy_name="Strategy_A",
        symbol="EURUSD",
        direction="buy",
        entry_price=1.1000,
        exit_price=1.0950,
        profit_loss=-50.0,
        lot_size=0.1,
        news_avoided=False,
        market_condition="ranging"
    )
    
    # Winning trade for Strategy B
    evaluator.record_trade(
        strategy_name="Strategy_B",
        symbol="GBPUSD",
        direction="sell",
        entry_price=1.3000,
        exit_price=1.2950,
        profit_loss=50.0,
        lot_size=0.1,
        news_avoided=True,
        market_condition="trending"
    )
    
    # Get performance metrics
    print("\nStrategy A Performance:")
    strategy_a_performance = evaluator.get_strategy_performance("Strategy_A")
    print(f"Total Trades: {strategy_a_performance['total_trades']}")
    print(f"Win Rate: {strategy_a_performance['win_rate']:.2f}%")
    print(f"Confidence Score: {strategy_a_performance['confidence_score']:.2f}")
    
    print("\nStrategy B Performance:")
    strategy_b_performance = evaluator.get_strategy_performance("Strategy_B")
    print(f"Total Trades: {strategy_b_performance['total_trades']}")
    print(f"Win Rate: {strategy_b_performance['win_rate']:.2f}%")
    print(f"Confidence Score: {strategy_b_performance['confidence_score']:.2f}")
    
    # Get risk recommendations
    print("\nRisk Recommendations:")
    risk_rec_a = evaluator.get_risk_recommendation("Strategy_A")
    print(f"Strategy A: {risk_rec_a['action']} - {risk_rec_a['reason']}")
    
    risk_rec_b = evaluator.get_risk_recommendation("Strategy_B")
    print(f"Strategy B: {risk_rec_b['action']} - {risk_rec_b['reason']}")
    
    # Check if trading should be paused
    should_pause, reason = evaluator.should_pause_trading()
    print(f"\nShould pause trading: {should_pause}")
    if should_pause:
        print(f"Reason: {reason}")