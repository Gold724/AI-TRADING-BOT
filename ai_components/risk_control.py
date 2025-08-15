# ai_components/risk_control.py

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import random

# Function to get risk level for external imports
def get_risk_level(pair: str, strategy: str = "default") -> str:
    """Get risk level for a pair and strategy
    
    Args:
        pair (str): Currency pair
        strategy (str): Strategy name
    
    Returns:
        str: Risk level (low, medium, high)
    """
    # Create a risk controller instance
    controller = RiskController()
    
    # Get risk multiplier
    multiplier = controller.get_risk_multiplier(pair, strategy)
    
    # Determine risk level based on multiplier
    if multiplier <= 0.7:
        return "low"
    elif multiplier <= 1.2:
        return "medium"
    else:
        return "high"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_components.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("risk_control")

# Constants
RISK_CONFIG_FILE = os.path.join("config", "risk_config.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)


class RiskController:
    """AI-enhanced risk management for trading strategies"""
    
    def __init__(self, risk_config_file: str = RISK_CONFIG_FILE,
                 strategy_stats_file: str = STRATEGY_STATS_FILE,
                 trade_history_file: str = TRADE_HISTORY_FILE):
        """Initialize the risk controller
        
        Args:
            risk_config_file (str): Path to the risk configuration file
            strategy_stats_file (str): Path to the strategy statistics file
            trade_history_file (str): Path to the trade history file
        """
        self.risk_config_file = risk_config_file
        self.strategy_stats_file = strategy_stats_file
        self.trade_history_file = trade_history_file
        
        self.risk_config = self.load_risk_config()
        self.strategy_stats = self.load_strategy_stats()
        self.trade_history = self.load_trade_history()
    
    def load_risk_config(self) -> Dict:
        """Load risk configuration from file
        
        Returns:
            Dict: Risk configuration
        """
        default_config = {
            "global": {
                "max_daily_loss": 5.0,  # Maximum daily loss as percentage of account
                "max_position_size": 2.0,  # Maximum position size as percentage of account
                "default_risk_per_trade": 1.0,  # Default risk per trade as percentage of account
                "max_open_positions": 5,  # Maximum number of open positions
                "max_correlation_exposure": 10.0,  # Maximum exposure to correlated assets
                "drawdown_reduction_threshold": 5.0,  # Drawdown threshold for risk reduction
                "drawdown_reduction_factor": 0.5,  # Risk reduction factor during drawdown
                "volatility_adjustment": True,  # Whether to adjust risk based on volatility
                "news_impact_adjustment": True,  # Whether to adjust risk based on news impact
                "performance_based_adjustment": True,  # Whether to adjust risk based on performance
                "risk_levels": {
                    "low": 0.5,  # Multiplier for low risk
                    "medium": 1.0,  # Multiplier for medium risk
                    "high": 1.5  # Multiplier for high risk
                }
            },
            "strategies": {
                "default": {
                    "risk_per_trade": 1.0,  # Risk per trade as percentage of account
                    "max_daily_trades": 10,  # Maximum number of trades per day
                    "min_win_rate": 40.0,  # Minimum win rate to maintain normal risk
                    "target_win_rate": 55.0,  # Target win rate for normal risk
                    "risk_adjustment_factor": 0.1,  # Risk adjustment factor per 1% win rate deviation
                    "max_consecutive_losses": 3,  # Maximum consecutive losses before risk reduction
                    "consecutive_loss_factor": 0.7,  # Risk reduction factor after consecutive losses
                    "recovery_trades": 2,  # Number of successful trades to recover normal risk
                    "symbols": {},  # Symbol-specific risk settings
                    "pairs": {}  # Pair-specific risk settings
                }
            },
            "market_conditions": {
                "high_volatility": {
                    "risk_multiplier": 0.7  # Risk multiplier during high volatility
                },
                "low_volatility": {
                    "risk_multiplier": 1.2  # Risk multiplier during low volatility
                },
                "trending": {
                    "risk_multiplier": 1.1  # Risk multiplier during trending market
                },
                "ranging": {
                    "risk_multiplier": 0.9  # Risk multiplier during ranging market
                },
                "high_liquidity": {
                    "risk_multiplier": 1.1  # Risk multiplier during high liquidity
                },
                "low_liquidity": {
                    "risk_multiplier": 0.8  # Risk multiplier during low liquidity
                }
            }
        }
        
        try:
            if os.path.exists(self.risk_config_file):
                with open(self.risk_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.risk_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading risk config: {e}")
            return default_config
    
    def load_strategy_stats(self) -> Dict:
        """Load strategy statistics from file
        
        Returns:
            Dict: Strategy statistics
        """
        default_stats = {
            "default": {
                "win_rate": 50.0,
                "profit_factor": 1.5,
                "average_win": 1.0,
                "average_loss": 1.0,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        try:
            if os.path.exists(self.strategy_stats_file):
                with open(self.strategy_stats_file, "r") as f:
                    return json.load(f)
            else:
                # Create default stats file if it doesn't exist
                with open(self.strategy_stats_file, "w") as f:
                    json.dump(default_stats, f, indent=4)
                return default_stats
        except Exception as e:
            logger.error(f"Error loading strategy stats: {e}")
            return default_stats
    
    def get_risk_multiplier(self, pair: str, strategy: str = "default") -> float:
        """Get risk multiplier for a pair and strategy
        
        Args:
            pair (str): Currency pair
            strategy (str): Strategy name
        
        Returns:
            float: Risk multiplier
        """
        # Default multiplier
        multiplier = 1.0
        
        # Get strategy settings
        strategy_config = self.risk_config.get("strategies", {}).get(strategy, {})
        if not strategy_config:
            strategy_config = self.risk_config.get("strategies", {}).get("default", {})
        
        # Get strategy stats
        strategy_stats = self.strategy_stats.get(strategy, {})
        if not strategy_stats:
            strategy_stats = self.strategy_stats.get("default", {})
        
        # Adjust based on win rate
        win_rate = strategy_stats.get("win_rate", 50.0)
        target_win_rate = strategy_config.get("target_win_rate", 55.0)
        min_win_rate = strategy_config.get("min_win_rate", 40.0)
        risk_adjustment_factor = strategy_config.get("risk_adjustment_factor", 0.1)
        
        if win_rate < min_win_rate:
            # Reduce risk for poor performance
            multiplier *= 0.5
        else:
            # Adjust based on win rate deviation from target
            win_rate_deviation = win_rate - target_win_rate
            multiplier *= (1.0 + (win_rate_deviation * risk_adjustment_factor / 100.0))
        
        # Adjust based on consecutive losses
        consecutive_losses = strategy_stats.get("consecutive_losses", 0)
        max_consecutive_losses = strategy_config.get("max_consecutive_losses", 3)
        consecutive_loss_factor = strategy_config.get("consecutive_loss_factor", 0.7)
        
        if consecutive_losses >= max_consecutive_losses:
            multiplier *= consecutive_loss_factor
        
        # Check for pair-specific settings
        pair_settings = strategy_config.get("pairs", {}).get(pair, {})
        if pair_settings:
            pair_multiplier = pair_settings.get("risk_multiplier", 1.0)
            multiplier *= pair_multiplier
        
        # Apply global risk level settings
        risk_levels = self.risk_config.get("global", {}).get("risk_levels", {})
        
        # Determine current market condition (simplified)
        # In a real implementation, this would analyze market data
        market_condition = random.choice(["high_volatility", "low_volatility", "trending", "ranging"])
        
        # Apply market condition multiplier
        market_multiplier = self.risk_config.get("market_conditions", {}).get(market_condition, {}).get("risk_multiplier", 1.0)
        multiplier *= market_multiplier
        
        # Ensure multiplier is within reasonable bounds
        multiplier = max(0.1, min(multiplier, 2.0))
        
        return multiplier
        
    def load_trade_history(self) -> Dict:
        """Load trade history from file
        
        Returns:
            Dict: Trade history
        """
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, "r") as f:
                    return json.load(f)
            else:
                # Create empty trade history file if it doesn't exist
                with open(self.trade_history_file, "w") as f:
                    json.dump([], f, indent=4)
                return []
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return []
    
    def save_risk_config(self) -> bool:
        """Save risk configuration to file
        
        Returns:
            bool: Success status
        """
        try:
            with open(self.risk_config_file, "w") as f:
                json.dump(self.risk_config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving risk config: {e}")
            return False
    
    def save_strategy_stats(self) -> bool:
        """Save strategy statistics to file
        
        Returns:
            bool: Success status
        """
        try:
            # Update last_updated timestamp
            for strategy in self.strategy_stats:
                self.strategy_stats[strategy]["last_updated"] = datetime.now().isoformat()
            
            with open(self.strategy_stats_file, "w") as f:
                json.dump(self.strategy_stats, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy stats: {e}")
            return False
    
    def save_trade_history(self) -> bool:
        """Save trade history to file
        
        Returns:
            bool: Success status
        """
        try:
            with open(self.trade_history_file, "w") as f:
                json.dump(self.trade_history, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving trade history: {e}")
            return False
    
    def update_strategy_stats(self, strategy_name: str, trade_result: Dict) -> bool:
        """Update strategy statistics based on trade result
        
        Args:
            strategy_name (str): Strategy name
            trade_result (Dict): Trade result with profit/loss
        
        Returns:
            bool: Success status
        """
        try:
            # Ensure strategy exists in stats
            if strategy_name not in self.strategy_stats:
                self.strategy_stats[strategy_name] = {
                    "win_rate": 50.0,
                    "profit_factor": 1.5,
                    "average_win": 1.0,
                    "average_loss": 1.0,
                    "consecutive_wins": 0,
                    "consecutive_losses": 0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "last_updated": datetime.now().isoformat()
                }
            
            # Extract trade details
            profit = trade_result.get("profit", 0.0)
            is_win = profit > 0
            
            # Update stats
            stats = self.strategy_stats[strategy_name]
            stats["total_trades"] += 1
            
            if is_win:
                stats["winning_trades"] += 1
                stats["consecutive_wins"] += 1
                stats["consecutive_losses"] = 0
                
                # Update average win
                if stats["winning_trades"] > 1:
                    stats["average_win"] = ((stats["average_win"] * (stats["winning_trades"] - 1)) + profit) / stats["winning_trades"]
                else:
                    stats["average_win"] = profit
            else:
                stats["losing_trades"] += 1
                stats["consecutive_losses"] += 1
                stats["consecutive_wins"] = 0
                
                # Update average loss
                if stats["losing_trades"] > 1:
                    stats["average_loss"] = ((stats["average_loss"] * (stats["losing_trades"] - 1)) + abs(profit)) / stats["losing_trades"]
                else:
                    stats["average_loss"] = abs(profit)
            
            # Update win rate
            stats["win_rate"] = (stats["winning_trades"] / stats["total_trades"]) * 100.0
            
            # Update profit factor
            if stats["losing_trades"] > 0 and stats["winning_trades"] > 0:
                stats["profit_factor"] = (stats["average_win"] * stats["winning_trades"]) / (stats["average_loss"] * stats["losing_trades"])
            
            # Add trade to history
            trade_record = trade_result.copy()
            trade_record["strategy"] = strategy_name
            trade_record["timestamp"] = datetime.now().isoformat()
            self.trade_history.append(trade_record)
            
            # Save updated stats and history
            self.save_strategy_stats()
            self.save_trade_history()
            
            return True
        except Exception as e:
            logger.error(f"Error updating strategy stats: {e}")
            return False
    
    def get_strategy_risk_multiplier(self, strategy_name: str) -> float:
        """Get risk multiplier for a strategy based on performance
        
        Args:
            strategy_name (str): Strategy name
        
        Returns:
            float: Risk multiplier
        """
        # Use default strategy if specified strategy not found
        if strategy_name not in self.strategy_stats:
            strategy_name = "default"
        
        # Get strategy stats
        stats = self.strategy_stats[strategy_name]
        
        # Get strategy risk settings
        strategy_config = self.risk_config.get("strategies", {}).get(strategy_name)
        if not strategy_config:
            strategy_config = self.risk_config.get("strategies", {}).get("default", {})
        
        # Initialize multiplier
        multiplier = 1.0
        
        # Check if performance-based adjustment is enabled
        if self.risk_config.get("global", {}).get("performance_based_adjustment", True):
            # Adjust based on win rate
            min_win_rate = strategy_config.get("min_win_rate", 40.0)
            target_win_rate = strategy_config.get("target_win_rate", 55.0)
            adjustment_factor = strategy_config.get("risk_adjustment_factor", 0.1)
            
            win_rate = stats.get("win_rate", 50.0)
            
            if win_rate < min_win_rate:
                # Reduce risk for poor performance
                win_rate_diff = min_win_rate - win_rate
                multiplier *= max(0.5, 1.0 - (win_rate_diff * adjustment_factor / 100.0))
            elif win_rate > target_win_rate:
                # Increase risk for good performance
                win_rate_diff = win_rate - target_win_rate
                multiplier *= min(1.5, 1.0 + (win_rate_diff * adjustment_factor / 100.0))
        
        # Check for consecutive losses
        max_consecutive_losses = strategy_config.get("max_consecutive_losses", 3)
        consecutive_loss_factor = strategy_config.get("consecutive_loss_factor", 0.7)
        
        if stats.get("consecutive_losses", 0) >= max_consecutive_losses:
            multiplier *= consecutive_loss_factor
        
        return multiplier
    
    def get_market_condition_multiplier(self, symbol: str) -> float:
        """Get risk multiplier based on market conditions
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            float: Risk multiplier
        """
        # This is a simplified implementation
        # In a real system, you would analyze market conditions
        # such as volatility, trend strength, liquidity, etc.
        
        # For now, we'll use a random market condition for demonstration
        market_conditions = ["high_volatility", "low_volatility", "trending", "ranging", "high_liquidity", "low_liquidity"]
        condition = random.choice(market_conditions)
        
        # Get multiplier for the condition
        multiplier = self.risk_config.get("market_conditions", {}).get(condition, {}).get("risk_multiplier", 1.0)
        
        logger.info(f"Market condition for {symbol}: {condition}, multiplier: {multiplier}")
        
        return multiplier
    
    def get_symbol_risk_multiplier(self, symbol: str, strategy_name: str = "default") -> float:
        """Get risk multiplier for a specific symbol
        
        Args:
            symbol (str): Trading symbol
            strategy_name (str): Strategy name
        
        Returns:
            float: Risk multiplier
        """
        # Use default strategy if specified strategy not found
        if strategy_name not in self.risk_config.get("strategies", {}):
            strategy_name = "default"
        
        # Get strategy config
        strategy_config = self.risk_config.get("strategies", {}).get(strategy_name, {})
        
        # Check for symbol-specific settings
        symbol_config = strategy_config.get("symbols", {}).get(symbol, {})
        if symbol_config:
            return symbol_config.get("risk_multiplier", 1.0)
        
        # Check for pair-specific settings
        for pair, pair_config in strategy_config.get("pairs", {}).items():
            if pair in symbol:
                return pair_config.get("risk_multiplier", 1.0)
        
        return 1.0
    
    def calculate_risk_level(self, symbol: str, strategy_name: str = "default") -> float:
        """Calculate overall risk level for a trade
        
        Args:
            symbol (str): Trading symbol
            strategy_name (str): Strategy name
        
        Returns:
            float: Risk level (0.0 to 1.0)
        """
        # Get base risk multipliers
        strategy_multiplier = self.get_strategy_risk_multiplier(strategy_name)
        market_multiplier = self.get_market_condition_multiplier(symbol)
        symbol_multiplier = self.get_symbol_risk_multiplier(symbol, strategy_name)
        
        # Calculate combined multiplier
        combined_multiplier = strategy_multiplier * market_multiplier * symbol_multiplier
        
        # Apply global limits
        global_config = self.risk_config.get("global", {})
        min_multiplier = 0.1  # Minimum 10% of normal risk
        max_multiplier = global_config.get("risk_levels", {}).get("high", 1.5)  # Maximum is high risk level
        
        # Ensure multiplier is within bounds
        bounded_multiplier = max(min_multiplier, min(max_multiplier, combined_multiplier))
        
        logger.info(f"Risk calculation for {symbol} using {strategy_name} strategy:")
        logger.info(f"  Strategy multiplier: {strategy_multiplier}")
        logger.info(f"  Market multiplier: {market_multiplier}")
        logger.info(f"  Symbol multiplier: {symbol_multiplier}")
        logger.info(f"  Combined multiplier: {combined_multiplier}")
        logger.info(f"  Final risk level: {bounded_multiplier}")
        
        return bounded_multiplier
    
    def is_trading_allowed(self, symbol: str, strategy_name: str = "default") -> Tuple[bool, str]:
        """Check if trading is allowed based on risk rules
        
        Args:
            symbol (str): Trading symbol
            strategy_name (str): Strategy name
        
        Returns:
            Tuple[bool, str]: (allowed, reason)
        """
        # Check daily loss limit
        daily_loss = self.calculate_daily_loss()
        max_daily_loss = self.risk_config.get("global", {}).get("max_daily_loss", 5.0)
        
        if daily_loss >= max_daily_loss:
            return False, f"Daily loss limit reached: {daily_loss:.2f}% (max: {max_daily_loss:.2f}%)"
        
        # Check maximum open positions
        open_positions = self.count_open_positions()
        max_open_positions = self.risk_config.get("global", {}).get("max_open_positions", 5)
        
        if open_positions >= max_open_positions:
            return False, f"Maximum open positions reached: {open_positions} (max: {max_open_positions})"
        
        # Check maximum daily trades for strategy
        daily_trades = self.count_daily_trades(strategy_name)
        strategy_config = self.risk_config.get("strategies", {}).get(strategy_name)
        if not strategy_config:
            strategy_config = self.risk_config.get("strategies", {}).get("default", {})
        
        max_daily_trades = strategy_config.get("max_daily_trades", 10)
        
        if daily_trades >= max_daily_trades:
            return False, f"Maximum daily trades reached for strategy {strategy_name}: {daily_trades} (max: {max_daily_trades})"
        
        return True, "Trading allowed"
    
    def calculate_daily_loss(self) -> float:
        """Calculate total loss for the current day as percentage of account
        
        Returns:
            float: Daily loss percentage
        """
        # Get today's date
        today = datetime.now().date()
        
        # Filter trades for today
        today_trades = []
        for trade in self.trade_history:
            trade_date = datetime.fromisoformat(trade.get("timestamp", "")).date()
            if trade_date == today:
                today_trades.append(trade)
        
        # Calculate total loss
        total_loss = 0.0
        for trade in today_trades:
            profit = trade.get("profit", 0.0)
            if profit < 0:
                total_loss += abs(profit)
        
        return total_loss
    
    def count_open_positions(self) -> int:
        """Count current open positions
        
        Returns:
            int: Number of open positions
        """
        # This is a simplified implementation
        # In a real system, you would query the broker API
        # to get the actual number of open positions
        
        # For now, we'll count recent trades that are marked as open
        open_count = 0
        for trade in self.trade_history:
            if trade.get("status") == "open":
                open_count += 1
        
        return open_count
    
    def count_daily_trades(self, strategy_name: str) -> int:
        """Count trades for the current day for a specific strategy
        
        Args:
            strategy_name (str): Strategy name
        
        Returns:
            int: Number of trades
        """
        # Get today's date
        today = datetime.now().date()
        
        # Count trades for today and strategy
        count = 0
        for trade in self.trade_history:
            trade_date = datetime.fromisoformat(trade.get("timestamp", "")).date()
            trade_strategy = trade.get("strategy", "default")
            
            if trade_date == today and trade_strategy == strategy_name:
                count += 1
        
        return count


# Helper functions for external use
def get_risk_level(symbol: str = "", strategy_name: str = "default") -> float:
    """Get risk level for a trade (helper function)
    
    Args:
        symbol (str): Trading symbol
        strategy_name (str): Strategy name
    
    Returns:
        float: Risk level (0.0 to 1.0)
    """
    risk_controller = RiskController()
    return risk_controller.calculate_risk_level(symbol, strategy_name)


# For testing
if __name__ == "__main__":
    # Create risk controller
    risk_controller = RiskController()
    
    # Test symbols
    test_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    
    # Test risk levels
    print("Testing risk levels:")
    for symbol in test_symbols:
        risk_level = risk_controller.calculate_risk_level(symbol)
        allowed, reason = risk_controller.is_trading_allowed(symbol)
        
        print(f"\n{symbol}:")
        print(f"  Risk level: {risk_level:.2f}")
        print(f"  Trading allowed: {allowed}")
        print(f"  Reason: {reason}")
    
    # Test updating strategy stats
    print("\nTesting strategy stats update:")
    test_trade = {
        "symbol": "EURUSD",
        "direction": "buy",
        "lot_size": 0.01,
        "entry_price": 1.1000,
        "exit_price": 1.1050,
        "profit": 50.0,
        "pips": 50,
        "status": "closed"
    }
    
    success = risk_controller.update_strategy_stats("test_strategy", test_trade)
    print(f"Update success: {success}")
    
    # Show updated stats
    if "test_strategy" in risk_controller.strategy_stats:
        stats = risk_controller.strategy_stats["test_strategy"]
        print("\nUpdated strategy stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")