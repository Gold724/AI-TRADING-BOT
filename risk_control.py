# risk_control.py

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Try to import the TradePerformanceEvaluator from trade_evaluator.py
try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def get_strategy_performance(self, strategy_name):
            return {}
        def get_risk_recommendation(self, strategy_name):
            return "maintain"
        def should_pause_trading(self):
            return False, "No pause conditions met"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("risk_control")

# Constants
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")
RISK_CONFIG_FILE = os.path.join("config", "risk_config.json")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)


class RiskController:
    """Controls risk parameters for trading strategies based on performance metrics"""

    def __init__(self, trade_history_file: str = TRADE_HISTORY_FILE, 
                 strategy_stats_file: str = STRATEGY_STATS_FILE,
                 risk_config_file: str = RISK_CONFIG_FILE):
        """Initialize the risk controller

        Args:
            trade_history_file (str): Path to the trade history file
            strategy_stats_file (str): Path to the strategy statistics file
            risk_config_file (str): Path to the risk configuration file
        """
        self.trade_history_file = trade_history_file
        self.strategy_stats_file = strategy_stats_file
        self.risk_config_file = risk_config_file
        self.evaluator = TradePerformanceEvaluator(trade_history_file, strategy_stats_file)
        self.risk_config = self.load_risk_config()
        
    def load_risk_config(self) -> Dict:
        """Load risk configuration from file

        Returns:
            Dict: Risk configuration
        """
        default_config = {
            "default": {
                "base_lot_size": 0.01,
                "base_risk_percent": 1.0,
                "max_risk_percent": 2.0,
                "min_risk_percent": 0.5,
                "risk_increment": 0.25,
                "max_daily_drawdown": 2.0,
                "max_consecutive_losses": 3,
                "win_rate_threshold": 60.0,
                "pause_duration_hours": 24
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
            
    def save_risk_config(self) -> bool:
        """Save risk configuration to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.risk_config_file, "w") as f:
                json.dump(self.risk_config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving risk config: {e}")
            return False
            
    def get_strategy_risk_config(self, strategy_name: str) -> Dict:
        """Get risk configuration for a specific strategy

        Args:
            strategy_name (str): Name of the strategy

        Returns:
            Dict: Risk configuration for the strategy
        """
        if strategy_name in self.risk_config:
            return self.risk_config[strategy_name]
        else:
            return self.risk_config["default"]
            
    def update_strategy_risk(self, strategy_name: str) -> Tuple[bool, str, Dict]:
        """Update risk parameters for a strategy based on performance

        Args:
            strategy_name (str): Name of the strategy

        Returns:
            Tuple[bool, str, Dict]: (success, message, updated_risk_config)
        """
        # Get strategy risk config
        if strategy_name not in self.risk_config:
            self.risk_config[strategy_name] = self.risk_config["default"].copy()
            
        risk_config = self.risk_config[strategy_name]
        
        # Get strategy performance
        performance = self.evaluator.get_strategy_performance(strategy_name)
        
        if not performance:
            return False, f"No performance data found for strategy '{strategy_name}'.", risk_config
            
        # Check if trading should be paused
        should_pause, pause_reason = self.evaluator.should_pause_trading()
        
        if should_pause:
            # Set pause timestamp
            risk_config["paused"] = True
            risk_config["pause_reason"] = pause_reason
            risk_config["pause_until"] = (datetime.utcnow() + 
                                       timedelta(hours=risk_config["pause_duration_hours"])).isoformat()
            
            # Save updated config
            self.save_risk_config()
            
            return True, f"Trading paused for strategy '{strategy_name}': {pause_reason}", risk_config
            
        # Check if strategy is currently paused
        if risk_config.get("paused", False):
            # Check if pause period has expired
            pause_until = datetime.fromisoformat(risk_config["pause_until"])
            
            if datetime.utcnow() < pause_until:
                # Still paused
                time_left = pause_until - datetime.utcnow()
                hours_left = time_left.total_seconds() / 3600
                
                return False, f"Strategy '{strategy_name}' is paused: {risk_config['pause_reason']}. "\
                       f"Resume in {hours_left:.1f} hours.", risk_config
            else:
                # Resume trading
                risk_config["paused"] = False
                risk_config["pause_reason"] = ""
                risk_config["pause_until"] = ""
                
                # Save updated config
                self.save_risk_config()
                
                return True, f"Trading resumed for strategy '{strategy_name}'.", risk_config
        
        # Get risk recommendation
        recommendation = self.evaluator.get_risk_recommendation(strategy_name)
        
        # Update risk parameters based on recommendation
        current_risk = risk_config["base_risk_percent"]
        risk_increment = risk_config["risk_increment"]
        max_risk = risk_config["max_risk_percent"]
        min_risk = risk_config["min_risk_percent"]
        
        if recommendation == "increase" and current_risk < max_risk:
            # Increase risk
            new_risk = min(current_risk + risk_increment, max_risk)
            risk_config["base_risk_percent"] = new_risk
            message = f"Increased risk for strategy '{strategy_name}' from {current_risk}% to {new_risk}%."
        elif recommendation == "decrease" and current_risk > min_risk:
            # Decrease risk
            new_risk = max(current_risk - risk_increment, min_risk)
            risk_config["base_risk_percent"] = new_risk
            message = f"Decreased risk for strategy '{strategy_name}' from {current_risk}% to {new_risk}%."
        else:
            # Maintain risk
            message = f"Maintained risk for strategy '{strategy_name}' at {current_risk}%."
            
        # Save updated config
        self.save_risk_config()
        
        return True, message, risk_config
    
    def get_lot_size(self, strategy_name: str, symbol: str, account_balance: float) -> float:
        """Calculate lot size based on risk parameters

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            account_balance (float): Account balance

        Returns:
            float: Calculated lot size
        """
        # Get strategy risk config
        risk_config = self.get_strategy_risk_config(strategy_name)
        
        # Check if strategy is paused
        if risk_config.get("paused", False):
            return 0.0
            
        # Calculate lot size based on risk percentage
        risk_percent = risk_config["base_risk_percent"]
        base_lot = risk_config["base_lot_size"]
        
        # Scale lot size based on account balance and risk percentage
        # This is a simple calculation; in a real system, you would consider
        # stop loss distance, pip value, etc.
        lot_size = base_lot * (account_balance / 10000.0) * (risk_percent / 1.0)
        
        # Round to standard lot sizes (0.01, 0.05, 0.1, etc.)
        # For micro lots (0.01)
        lot_size = round(lot_size * 100) / 100
        
        # Ensure minimum lot size
        lot_size = max(lot_size, 0.01)
        
        return lot_size
    
    def get_position_size(self, strategy_name: str, symbol: str, account_balance: float) -> float:
        """Calculate position size for futures/crypto trading

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            account_balance (float): Account balance

        Returns:
            float: Calculated position size
        """
        # Get strategy risk config
        risk_config = self.get_strategy_risk_config(strategy_name)
        
        # Check if strategy is paused
        if risk_config.get("paused", False):
            return 0.0
            
        # Calculate position size based on risk percentage
        risk_percent = risk_config["base_risk_percent"]
        
        # Calculate position size as percentage of account balance
        position_size = account_balance * (risk_percent / 100.0)
        
        return position_size
    
    def calculate_position_size(self, strategy_name: str, symbol: str, account_balance: float = 10000.0, 
                              risk_percent: float = None, entry_price: float = None, 
                              stop_loss: float = None) -> float:
        """Calculate position size with advanced risk parameters

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            account_balance (float): Account balance (default: 10000.0)
            risk_percent (float): Risk percentage override (optional)
            entry_price (float): Entry price for position sizing (optional)
            stop_loss (float): Stop loss price for position sizing (optional)

        Returns:
            float: Calculated position size
        """
        # Get strategy risk config
        risk_config = self.get_strategy_risk_config(strategy_name)
        
        # Check if strategy is paused
        if risk_config.get("paused", False):
            return 0.0
        
        # Use provided risk_percent or default from config
        risk_pct = risk_percent if risk_percent is not None else risk_config["base_risk_percent"]
        
        # If entry_price and stop_loss are provided, calculate position size based on risk amount
        if entry_price and stop_loss and entry_price != stop_loss:
            # Calculate risk amount in currency
            risk_amount = account_balance * (risk_pct / 100.0)
            
            # Calculate price difference (risk per unit)
            price_diff = abs(entry_price - stop_loss)
            
            # Calculate position size based on risk amount and price difference
            position_size = risk_amount / price_diff
            
            # Ensure minimum position size
            position_size = max(position_size, 0.01)
            
            return round(position_size, 2)
        else:
            # Fallback to percentage-based position sizing
            return self.get_position_size(strategy_name, symbol, account_balance)
    
    def is_trading_allowed(self, strategy_name: str) -> Tuple[bool, str]:
        """Check if trading is allowed for a strategy

        Args:
            strategy_name (str): Name of the strategy

        Returns:
            Tuple[bool, str]: (allowed, reason)
        """
        # Get strategy risk config
        risk_config = self.get_strategy_risk_config(strategy_name)
        
        # Check if strategy is paused
        if risk_config.get("paused", False):
            pause_until = datetime.fromisoformat(risk_config["pause_until"])
            
            if datetime.utcnow() < pause_until:
                # Still paused
                time_left = pause_until - datetime.utcnow()
                hours_left = time_left.total_seconds() / 3600
                
                return False, f"Strategy is paused: {risk_config['pause_reason']}. "\
                       f"Resume in {hours_left:.1f} hours."
            else:
                # Resume trading
                risk_config["paused"] = False
                risk_config["pause_reason"] = ""
                risk_config["pause_until"] = ""
                
                # Save updated config
                self.save_risk_config()
        
        # Check if trading should be paused
        should_pause, pause_reason = self.evaluator.should_pause_trading()
        
        if should_pause:
            # Set pause timestamp
            risk_config["paused"] = True
            risk_config["pause_reason"] = pause_reason
            risk_config["pause_until"] = (datetime.utcnow() + 
                                       timedelta(hours=risk_config["pause_duration_hours"])).isoformat()
            
            # Save updated config
            self.save_risk_config()
            
            return False, f"Trading paused: {pause_reason}"
        
        return True, "Trading allowed"


# Helper functions
def get_lot_size(strategy_name: str, symbol: str, account_balance: float) -> float:
    """Calculate lot size based on risk parameters (helper function)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Trading symbol
        account_balance (float): Account balance

    Returns:
        float: Calculated lot size
    """
    controller = RiskController()
    return controller.get_lot_size(strategy_name, symbol, account_balance)


def get_position_size(strategy_name: str, symbol: str, account_balance: float) -> float:
    """Calculate position size for futures/crypto trading (helper function)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Trading symbol
        account_balance (float): Account balance

    Returns:
        float: Calculated position size
    """
    controller = RiskController()
    return controller.get_position_size(strategy_name, symbol, account_balance)


def is_trading_allowed(strategy_name: str) -> Tuple[bool, str]:
    """Check if trading is allowed for a strategy (helper function)

    Args:
        strategy_name (str): Name of the strategy

    Returns:
        Tuple[bool, str]: (allowed, reason)
    """
    controller = RiskController()
    return controller.is_trading_allowed(strategy_name)


def update_strategy_risk(strategy_name: str) -> Tuple[bool, str, Dict]:
    """Update risk parameters for a strategy based on performance (helper function)

    Args:
        strategy_name (str): Name of the strategy

    Returns:
        Tuple[bool, str, Dict]: (success, message, updated_risk_config)
    """
    controller = RiskController()
    return controller.update_strategy_risk(strategy_name)


# For testing
if __name__ == "__main__":
    # Create risk controller
    controller = RiskController()
    
    # Test strategies
    strategies = ["fibonacci_retracement", "support_resistance", "trend_following"]
    
    for strategy in strategies:
        # Update risk parameters
        success, message, config = controller.update_strategy_risk(strategy)
        print(f"{strategy}: {message}")
        
        # Check if trading is allowed
        allowed, reason = controller.is_trading_allowed(strategy)
        print(f"{strategy} trading allowed: {allowed} - {reason}")
        
        # Calculate lot size
        lot_size = controller.get_lot_size(strategy, "EURUSD", 10000.0)
        print(f"{strategy} lot size: {lot_size}")
        
        # Calculate position size
        position_size = controller.get_position_size(strategy, "BTCUSDT", 10000.0)
        print(f"{strategy} position size: ${position_size:.2f}")
        
        print()