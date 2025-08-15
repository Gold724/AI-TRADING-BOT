# strategy_manager.py

import json
import logging
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

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

# Try to import the RiskController from risk_control.py
try:
    from risk_control import RiskController, is_trading_allowed
except ImportError:
    # Define minimal versions if the import fails
    class RiskController:
        def is_trading_allowed(self, strategy_name):
            return True, ""
    
    def is_trading_allowed(strategy_name):
        return True, ""

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("strategy_manager")

# Constants
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")
STRATEGY_CONFIG_FILE = os.path.join("config", "strategy_config.json")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)


class StrategyManager:
    """Manages multiple trading strategies with A/B testing capabilities"""

    def __init__(self, trade_history_file: str = TRADE_HISTORY_FILE, 
                 strategy_stats_file: str = STRATEGY_STATS_FILE,
                 strategy_config_file: str = STRATEGY_CONFIG_FILE):
        """Initialize the strategy manager

        Args:
            trade_history_file (str): Path to the trade history file
            strategy_stats_file (str): Path to the strategy statistics file
            strategy_config_file (str): Path to the strategy configuration file
        """
        self.trade_history_file = trade_history_file
        self.strategy_stats_file = strategy_stats_file
        self.strategy_config_file = strategy_config_file
        self.evaluator = TradePerformanceEvaluator(trade_history_file, strategy_stats_file)
        self.risk_controller = RiskController(trade_history_file, strategy_stats_file)
        self.strategy_config = self.load_strategy_config()
        
    def load_strategy_config(self) -> Dict:
        """Load strategy configuration from file

        Returns:
            Dict: Strategy configuration
        """
        default_config = {
            "strategies": {
                "fibonacci_retracement": {
                    "enabled": True,
                    "weight": 1.0,
                    "description": "Fibonacci retracement strategy",
                    "parameters": {
                        "retracement_levels": [0.236, 0.382, 0.5, 0.618, 0.786],
                        "timeframes": ["1h", "4h", "1d"]
                    },
                    "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
                },
                "support_resistance": {
                    "enabled": True,
                    "weight": 1.0,
                    "description": "Support and resistance strategy",
                    "parameters": {
                        "lookback_periods": 20,
                        "timeframes": ["1h", "4h"]
                    },
                    "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
                },
                "trend_following": {
                    "enabled": True,
                    "weight": 1.0,
                    "description": "Trend following strategy",
                    "parameters": {
                        "fast_ema": 12,
                        "slow_ema": 26,
                        "timeframes": ["1h", "4h"]
                    },
                    "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
                }
            },
            "ab_testing": {
                "enabled": True,
                "auto_adjust_weights": True,
                "evaluation_period_days": 7,
                "min_trades_for_evaluation": 10
            },
            "capital_allocation": {
                "total_capital": 10000.0,
                "max_allocation_percent": 80.0,
                "reserve_percent": 20.0
            }
        }
        
        try:
            if os.path.exists(self.strategy_config_file):
                with open(self.strategy_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.strategy_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading strategy config: {e}")
            return default_config
            
    def save_strategy_config(self) -> bool:
        """Save strategy configuration to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.strategy_config_file, "w") as f:
                json.dump(self.strategy_config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy config: {e}")
            return False
            
    def get_enabled_strategies(self) -> List[str]:
        """Get list of enabled strategies

        Returns:
            List[str]: List of enabled strategy names
        """
        enabled_strategies = []
        
        for strategy_name, strategy_config in self.strategy_config["strategies"].items():
            if strategy_config.get("enabled", False):
                enabled_strategies.append(strategy_name)
                
        return enabled_strategies
        
    def get_strategy_config(self, strategy_name: str) -> Dict:
        """Get configuration for a specific strategy

        Args:
            strategy_name (str): Name of the strategy

        Returns:
            Dict: Strategy configuration
        """
        if strategy_name in self.strategy_config["strategies"]:
            return self.strategy_config["strategies"][strategy_name]
        else:
            return {}
            
    def update_strategy_weights(self) -> bool:
        """Update strategy weights based on performance

        Returns:
            bool: True if weights were updated, False otherwise
        """
        if not self.strategy_config["ab_testing"]["auto_adjust_weights"]:
            return False
            
        # Get performance for all strategies
        all_performance = self.evaluator.get_all_strategies_performance()
        
        if not all_performance:
            return False
            
        # Calculate weights based on win rate and profit factor
        total_score = 0.0
        strategy_scores = {}
        
        for strategy_name, strategy_config in self.strategy_config["strategies"].items():
            if not strategy_config.get("enabled", False):
                continue
                
            if strategy_name not in all_performance:
                continue
                
            performance = all_performance[strategy_name]
            
            # Check if strategy has enough trades for evaluation
            min_trades = self.strategy_config["ab_testing"]["min_trades_for_evaluation"]
            if performance.get("total_trades", 0) < min_trades:
                continue
                
            # Calculate score based on win rate and profit factor
            win_rate = performance.get("win_rate", 0.0)
            profit_factor = performance.get("profit_factor", 0.0)
            
            # Simple scoring formula: win_rate * profit_factor
            score = (win_rate / 100.0) * profit_factor
            
            # Ensure minimum score
            score = max(score, 0.1)
            
            strategy_scores[strategy_name] = score
            total_score += score
            
        # Update weights if we have scores
        if total_score > 0:
            for strategy_name, score in strategy_scores.items():
                # Calculate normalized weight
                weight = score / total_score
                
                # Update strategy weight
                self.strategy_config["strategies"][strategy_name]["weight"] = weight
                
            # Save updated config
            self.save_strategy_config()
            
            return True
            
        return False
        
    def allocate_capital(self) -> Dict[str, float]:
        """Allocate capital across strategies based on weights

        Returns:
            Dict[str, float]: Dictionary of strategy allocations
        """
        # Get total capital and allocation percentage
        total_capital = self.strategy_config["capital_allocation"]["total_capital"]
        max_allocation_percent = self.strategy_config["capital_allocation"]["max_allocation_percent"]
        
        # Calculate available capital
        available_capital = total_capital * (max_allocation_percent / 100.0)
        
        # Get enabled strategies and their weights
        enabled_strategies = []
        total_weight = 0.0
        
        for strategy_name, strategy_config in self.strategy_config["strategies"].items():
            if strategy_config.get("enabled", False):
                # Check if trading is allowed for this strategy
                allowed, _ = self.risk_controller.is_trading_allowed(strategy_name)
                
                if allowed:
                    enabled_strategies.append(strategy_name)
                    total_weight += strategy_config.get("weight", 1.0)
        
        # Allocate capital based on weights
        allocations = {}
        
        if total_weight > 0:
            for strategy_name in enabled_strategies:
                weight = self.strategy_config["strategies"][strategy_name].get("weight", 1.0)
                allocation = (weight / total_weight) * available_capital
                allocations[strategy_name] = allocation
        
        return allocations
        
    def select_strategy_for_execution(self) -> Optional[str]:
        """Select a strategy for execution based on weights

        Returns:
            Optional[str]: Selected strategy name, or None if no strategies are available
        """
        # Get enabled strategies and their weights
        strategies = []
        weights = []
        
        for strategy_name, strategy_config in self.strategy_config["strategies"].items():
            if strategy_config.get("enabled", False):
                # Check if trading is allowed for this strategy
                allowed, _ = self.risk_controller.is_trading_allowed(strategy_name)
                
                if allowed:
                    strategies.append(strategy_name)
                    weights.append(strategy_config.get("weight", 1.0))
        
        if not strategies:
            return None
            
        # Select strategy based on weights
        selected_strategy = random.choices(strategies, weights=weights, k=1)[0]
        
        return selected_strategy
        
    def get_strategy_symbols(self, strategy_name: str) -> List[str]:
        """Get list of symbols for a specific strategy

        Args:
            strategy_name (str): Name of the strategy

        Returns:
            List[str]: List of symbols
        """
        if strategy_name in self.strategy_config["strategies"]:
            return self.strategy_config["strategies"][strategy_name].get("symbols", [])
        else:
            return []
            
    def select_symbol_for_strategy(self, strategy_name: str) -> Optional[str]:
        """Select a symbol for a specific strategy

        Args:
            strategy_name (str): Name of the strategy

        Returns:
            Optional[str]: Selected symbol, or None if no symbols are available
        """
        symbols = self.get_strategy_symbols(strategy_name)
        
        if not symbols:
            return None
            
        # Select random symbol
        selected_symbol = random.choice(symbols)
        
        return selected_symbol
        
    def get_strategy_parameters(self, strategy_name: str) -> Dict:
        """Get parameters for a specific strategy

        Args:
            strategy_name (str): Name of the strategy

        Returns:
            Dict: Strategy parameters
        """
        if strategy_name in self.strategy_config["strategies"]:
            return self.strategy_config["strategies"][strategy_name].get("parameters", {})
        else:
            return {}
            
    def record_ab_test_result(self, strategy_name: str, symbol: str, 
                            profit_loss: float, win: bool, 
                            market_condition: str, news_avoided: bool) -> bool:
        """Record A/B test result

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            profit_loss (float): Profit or loss amount
            win (bool): Whether the trade was a win
            market_condition (str): Market condition during the trade
            news_avoided (bool): Whether news was avoided

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Record trade in evaluator
            self.evaluator.record_trade(
                strategy_name=strategy_name,
                symbol=symbol,
                profit_loss=profit_loss,
                win=win,
                market_condition=market_condition,
                news_avoided=news_avoided
            )
            
            # Update strategy weights if needed
            if self.strategy_config["ab_testing"]["auto_adjust_weights"]:
                self.update_strategy_weights()
                
            return True
        except Exception as e:
            logger.error(f"Error recording A/B test result: {e}")
            return False
            
    def get_ab_testing_stats(self) -> Dict:
        """Get A/B testing statistics

        Returns:
            Dict: A/B testing statistics
        """
        stats = {
            "strategies": {},
            "total_trades": 0,
            "total_profit_loss": 0.0,
            "best_strategy": "",
            "best_win_rate": 0.0,
            "best_profit_factor": 0.0
        }
        
        # Get performance for all strategies
        all_performance = self.evaluator.get_all_strategies_performance()
        
        if not all_performance:
            return stats
            
        # Compile statistics
        best_win_rate = 0.0
        best_profit_factor = 0.0
        best_strategy = ""
        
        for strategy_name, performance in all_performance.items():
            # Skip strategies with no trades
            if performance.get("total_trades", 0) == 0:
                continue
                
            # Add strategy stats
            stats["strategies"][strategy_name] = {
                "total_trades": performance.get("total_trades", 0),
                "win_rate": performance.get("win_rate", 0.0),
                "profit_loss": performance.get("total_profit_loss", 0.0),
                "profit_factor": performance.get("profit_factor", 0.0),
                "weight": self.strategy_config["strategies"].get(strategy_name, {}).get("weight", 0.0)
            }
            
            # Update totals
            stats["total_trades"] += performance.get("total_trades", 0)
            stats["total_profit_loss"] += performance.get("total_profit_loss", 0.0)
            
            # Check if this is the best strategy
            win_rate = performance.get("win_rate", 0.0)
            profit_factor = performance.get("profit_factor", 0.0)
            
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_strategy = strategy_name
                
            if profit_factor > best_profit_factor:
                best_profit_factor = profit_factor
        
        # Set best strategy info
        stats["best_strategy"] = best_strategy
        stats["best_win_rate"] = best_win_rate
        stats["best_profit_factor"] = best_profit_factor
        
        return stats


# Helper functions
def select_strategy_for_execution() -> Optional[str]:
    """Select a strategy for execution based on weights (helper function)

    Returns:
        Optional[str]: Selected strategy name, or None if no strategies are available
    """
    manager = StrategyManager()
    return manager.select_strategy_for_execution()


def select_symbol_for_strategy(strategy_name: str) -> Optional[str]:
    """Select a symbol for a specific strategy (helper function)

    Args:
        strategy_name (str): Name of the strategy

    Returns:
        Optional[str]: Selected symbol, or None if no symbols are available
    """
    manager = StrategyManager()
    return manager.select_symbol_for_strategy(strategy_name)


def get_strategy_parameters(strategy_name: str) -> Dict:
    """Get parameters for a specific strategy (helper function)

    Args:
        strategy_name (str): Name of the strategy

    Returns:
        Dict: Strategy parameters
    """
    manager = StrategyManager()
    return manager.get_strategy_parameters(strategy_name)


def record_ab_test_result(strategy_name: str, symbol: str, profit_loss: float, 
                        win: bool, market_condition: str, news_avoided: bool) -> bool:
    """Record A/B test result (helper function)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Trading symbol
        profit_loss (float): Profit or loss amount
        win (bool): Whether the trade was a win
        market_condition (str): Market condition during the trade
        news_avoided (bool): Whether news was avoided

    Returns:
        bool: True if successful, False otherwise
    """
    manager = StrategyManager()
    return manager.record_ab_test_result(
        strategy_name=strategy_name,
        symbol=symbol,
        profit_loss=profit_loss,
        win=win,
        market_condition=market_condition,
        news_avoided=news_avoided
    )


def get_ab_testing_stats() -> Dict:
    """Get A/B testing statistics (helper function)

    Returns:
        Dict: A/B testing statistics
    """
    manager = StrategyManager()
    return manager.get_ab_testing_stats()


# For testing
if __name__ == "__main__":
    # Create strategy manager
    manager = StrategyManager()
    
    # Print enabled strategies
    enabled_strategies = manager.get_enabled_strategies()
    print(f"Enabled strategies: {enabled_strategies}")
    
    # Allocate capital
    allocations = manager.allocate_capital()
    print("\nCapital allocations:")
    for strategy, allocation in allocations.items():
        print(f"  {strategy}: ${allocation:.2f}")
    
    # Select strategy and symbol
    selected_strategy = manager.select_strategy_for_execution()
    if selected_strategy:
        selected_symbol = manager.select_symbol_for_strategy(selected_strategy)
        parameters = manager.get_strategy_parameters(selected_strategy)
        
        print(f"\nSelected strategy: {selected_strategy}")
        print(f"Selected symbol: {selected_symbol}")
        print(f"Strategy parameters: {parameters}")
    
    # Get A/B testing stats
    ab_stats = manager.get_ab_testing_stats()
    print(f"\nA/B testing stats: {ab_stats}")