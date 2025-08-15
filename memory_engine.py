# memory_engine.py

import json
import logging
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Try to import from other modules
try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def get_strategy_performance(self, strategy_name):
            return {}

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("memory_engine")

# Constants
MEMORY_DIR = os.path.join("data", "memory")
MARKET_MEMORY_FILE = os.path.join(MEMORY_DIR, "market_memory.json")
STRATEGY_MEMORY_FILE = os.path.join(MEMORY_DIR, "strategy_memory.json")
CONDITION_MEMORY_FILE = os.path.join(MEMORY_DIR, "condition_memory.json")
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")

# Ensure directories exist
os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)


class MemoryEngine:
    """Memory engine for tracking strategy performance across market conditions"""

    def __init__(self, trade_history_file: str = TRADE_HISTORY_FILE,
                 market_memory_file: str = MARKET_MEMORY_FILE,
                 strategy_memory_file: str = STRATEGY_MEMORY_FILE,
                 condition_memory_file: str = CONDITION_MEMORY_FILE):
        """Initialize the memory engine

        Args:
            trade_history_file (str): Path to the trade history file
            market_memory_file (str): Path to the market memory file
            strategy_memory_file (str): Path to the strategy memory file
            condition_memory_file (str): Path to the condition memory file
        """
        self.trade_history_file = trade_history_file
        self.market_memory_file = market_memory_file
        self.strategy_memory_file = strategy_memory_file
        self.condition_memory_file = condition_memory_file
        self.evaluator = TradePerformanceEvaluator(trade_history_file)
        
        # Load memory data
        self.market_memory = self.load_market_memory()
        self.strategy_memory = self.load_strategy_memory()
        self.condition_memory = self.load_condition_memory()
        
    def load_market_memory(self) -> Dict:
        """Load market memory from file

        Returns:
            Dict: Market memory data
        """
        default_memory = {
            "symbols": {},
            "correlations": {},
            "volatility_patterns": {},
            "news_impact": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            if os.path.exists(self.market_memory_file):
                with open(self.market_memory_file, "r") as f:
                    return json.load(f)
            else:
                # Create default memory file if it doesn't exist
                with open(self.market_memory_file, "w") as f:
                    json.dump(default_memory, f, indent=4)
                return default_memory
        except Exception as e:
            logger.error(f"Error loading market memory: {e}")
            return default_memory
            
    def load_strategy_memory(self) -> Dict:
        """Load strategy memory from file

        Returns:
            Dict: Strategy memory data
        """
        default_memory = {
            "strategies": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            if os.path.exists(self.strategy_memory_file):
                with open(self.strategy_memory_file, "r") as f:
                    return json.load(f)
            else:
                # Create default memory file if it doesn't exist
                with open(self.strategy_memory_file, "w") as f:
                    json.dump(default_memory, f, indent=4)
                return default_memory
        except Exception as e:
            logger.error(f"Error loading strategy memory: {e}")
            return default_memory
            
    def load_condition_memory(self) -> Dict:
        """Load condition memory from file

        Returns:
            Dict: Condition memory data
        """
        default_memory = {
            "conditions": {},
            "transitions": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            if os.path.exists(self.condition_memory_file):
                with open(self.condition_memory_file, "r") as f:
                    return json.load(f)
            else:
                # Create default memory file if it doesn't exist
                with open(self.condition_memory_file, "w") as f:
                    json.dump(default_memory, f, indent=4)
                return default_memory
        except Exception as e:
            logger.error(f"Error loading condition memory: {e}")
            return default_memory
            
    def save_market_memory(self) -> bool:
        """Save market memory to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update last updated timestamp
            self.market_memory["last_updated"] = datetime.utcnow().isoformat()
            
            with open(self.market_memory_file, "w") as f:
                json.dump(self.market_memory, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving market memory: {e}")
            return False
            
    def save_strategy_memory(self) -> bool:
        """Save strategy memory to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update last updated timestamp
            self.strategy_memory["last_updated"] = datetime.utcnow().isoformat()
            
            with open(self.strategy_memory_file, "w") as f:
                json.dump(self.strategy_memory, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy memory: {e}")
            return False
            
    def save_condition_memory(self) -> bool:
        """Save condition memory to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update last updated timestamp
            self.condition_memory["last_updated"] = datetime.utcnow().isoformat()
            
            with open(self.condition_memory_file, "w") as f:
                json.dump(self.condition_memory, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving condition memory: {e}")
            return False
            
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
            
    def update_market_memory(self, symbol: str, market_condition: str, 
                           volatility: float, news_impact: bool) -> bool:
        """Update market memory with new data

        Args:
            symbol (str): Trading symbol
            market_condition (str): Current market condition
            volatility (float): Current volatility
            news_impact (bool): Whether news impacted the market

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize symbol data if it doesn't exist
            if symbol not in self.market_memory["symbols"]:
                self.market_memory["symbols"][symbol] = {
                    "conditions": {},
                    "volatility": [],
                    "news_impact": {
                        "count": 0,
                        "last_impact": None
                    }
                }
                
            # Update market condition count
            if market_condition not in self.market_memory["symbols"][symbol]["conditions"]:
                self.market_memory["symbols"][symbol]["conditions"][market_condition] = 1
            else:
                self.market_memory["symbols"][symbol]["conditions"][market_condition] += 1
                
            # Update volatility (keep last 30 data points)
            self.market_memory["symbols"][symbol]["volatility"].append(volatility)
            if len(self.market_memory["symbols"][symbol]["volatility"]) > 30:
                self.market_memory["symbols"][symbol]["volatility"].pop(0)
                
            # Update news impact
            if news_impact:
                self.market_memory["symbols"][symbol]["news_impact"]["count"] += 1
                self.market_memory["symbols"][symbol]["news_impact"]["last_impact"] = datetime.utcnow().isoformat()
                
            # Save market memory
            return self.save_market_memory()
        except Exception as e:
            logger.error(f"Error updating market memory: {e}")
            return False
            
    def update_strategy_memory(self, strategy_name: str, symbol: str, 
                             market_condition: str, profit_loss: float, 
                             win: bool) -> bool:
        """Update strategy memory with new trade data

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            market_condition (str): Current market condition
            profit_loss (float): Profit or loss from the trade
            win (bool): Whether the trade was a win

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize strategy data if it doesn't exist
            if strategy_name not in self.strategy_memory["strategies"]:
                self.strategy_memory["strategies"][strategy_name] = {
                    "symbols": {},
                    "conditions": {},
                    "overall": {
                        "total_trades": 0,
                        "wins": 0,
                        "losses": 0,
                        "profit_loss": 0.0
                    }
                }
                
            # Update overall statistics
            self.strategy_memory["strategies"][strategy_name]["overall"]["total_trades"] += 1
            self.strategy_memory["strategies"][strategy_name]["overall"]["profit_loss"] += profit_loss
            
            if win:
                self.strategy_memory["strategies"][strategy_name]["overall"]["wins"] += 1
            else:
                self.strategy_memory["strategies"][strategy_name]["overall"]["losses"] += 1
                
            # Initialize symbol data if it doesn't exist
            if symbol not in self.strategy_memory["strategies"][strategy_name]["symbols"]:
                self.strategy_memory["strategies"][strategy_name]["symbols"][symbol] = {
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit_loss": 0.0,
                    "conditions": {}
                }
                
            # Update symbol statistics
            self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["total_trades"] += 1
            self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["profit_loss"] += profit_loss
            
            if win:
                self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["wins"] += 1
            else:
                self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["losses"] += 1
                
            # Initialize condition data if it doesn't exist
            if market_condition not in self.strategy_memory["strategies"][strategy_name]["conditions"]:
                self.strategy_memory["strategies"][strategy_name]["conditions"][market_condition] = {
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit_loss": 0.0
                }
                
            # Update condition statistics
            self.strategy_memory["strategies"][strategy_name]["conditions"][market_condition]["total_trades"] += 1
            self.strategy_memory["strategies"][strategy_name]["conditions"][market_condition]["profit_loss"] += profit_loss
            
            if win:
                self.strategy_memory["strategies"][strategy_name]["conditions"][market_condition]["wins"] += 1
            else:
                self.strategy_memory["strategies"][strategy_name]["conditions"][market_condition]["losses"] += 1
                
            # Initialize symbol-condition data if it doesn't exist
            if market_condition not in self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["conditions"]:
                self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["conditions"][market_condition] = {
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "profit_loss": 0.0
                }
                
            # Update symbol-condition statistics
            self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["conditions"][market_condition]["total_trades"] += 1
            self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["conditions"][market_condition]["profit_loss"] += profit_loss
            
            if win:
                self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["conditions"][market_condition]["wins"] += 1
            else:
                self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]["conditions"][market_condition]["losses"] += 1
                
            # Save strategy memory
            return self.save_strategy_memory()
        except Exception as e:
            logger.error(f"Error updating strategy memory: {e}")
            return False
            
    def update_condition_memory(self, prev_condition: Optional[str], 
                              current_condition: str) -> bool:
        """Update condition memory with new condition transition

        Args:
            prev_condition (Optional[str]): Previous market condition
            current_condition (str): Current market condition

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize condition data if it doesn't exist
            if current_condition not in self.condition_memory["conditions"]:
                self.condition_memory["conditions"][current_condition] = {
                    "count": 0,
                    "avg_duration": 0.0,
                    "last_seen": datetime.utcnow().isoformat()
                }
                
            # Update condition count
            self.condition_memory["conditions"][current_condition]["count"] += 1
            self.condition_memory["conditions"][current_condition]["last_seen"] = datetime.utcnow().isoformat()
            
            # Update transition if previous condition exists
            if prev_condition is not None:
                # Initialize transition data if it doesn't exist
                if prev_condition not in self.condition_memory["transitions"]:
                    self.condition_memory["transitions"][prev_condition] = {}
                    
                if current_condition not in self.condition_memory["transitions"][prev_condition]:
                    self.condition_memory["transitions"][prev_condition][current_condition] = 0
                    
                # Update transition count
                self.condition_memory["transitions"][prev_condition][current_condition] += 1
                
            # Save condition memory
            return self.save_condition_memory()
        except Exception as e:
            logger.error(f"Error updating condition memory: {e}")
            return False
            
    def record_trade(self, strategy_name: str, symbol: str, market_condition: str,
                    profit_loss: float, volatility: float = 0.0, 
                    news_impact: bool = False) -> bool:
        """Record a trade and update all memory components

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            market_condition (str): Current market condition
            profit_loss (float): Profit or loss from the trade
            volatility (float, optional): Current volatility. Defaults to 0.0.
            news_impact (bool, optional): Whether news impacted the market. Defaults to False.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine if trade was a win
            win = profit_loss > 0
            
            # Update market memory
            market_updated = self.update_market_memory(symbol, market_condition, volatility, news_impact)
            
            # Update strategy memory
            strategy_updated = self.update_strategy_memory(strategy_name, symbol, market_condition, profit_loss, win)
            
            # Get previous condition from last trade with this symbol
            prev_condition = None
            trades = self.load_trade_history()
            
            # Filter trades for this symbol and sort by timestamp (newest first)
            symbol_trades = [trade for trade in trades if trade.get("symbol") == symbol]
            symbol_trades.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Get previous condition if there are previous trades
            if symbol_trades and len(symbol_trades) > 1:
                prev_condition = symbol_trades[0].get("market_condition")
                
            # Update condition memory
            condition_updated = self.update_condition_memory(prev_condition, market_condition)
            
            return market_updated and strategy_updated and condition_updated
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
            return False
            
    def get_best_strategy_for_condition(self, market_condition: str, 
                                       symbol: Optional[str] = None) -> Tuple[str, float]:
        """Get the best strategy for a given market condition

        Args:
            market_condition (str): Current market condition
            symbol (Optional[str], optional): Trading symbol. Defaults to None.

        Returns:
            Tuple[str, float]: (best_strategy, win_rate)
        """
        best_strategy = None
        best_win_rate = 0.0
        
        # Iterate through strategies
        for strategy_name, strategy_data in self.strategy_memory["strategies"].items():
            # Check if strategy has data for this condition
            if market_condition in strategy_data["conditions"]:
                condition_data = strategy_data["conditions"][market_condition]
                
                # Calculate win rate
                total_trades = condition_data["total_trades"]
                wins = condition_data["wins"]
                
                if total_trades > 0:
                    win_rate = (wins / total_trades) * 100
                    
                    # Check if this is the best strategy so far
                    if win_rate > best_win_rate and total_trades >= 5:  # Require at least 5 trades
                        best_strategy = strategy_name
                        best_win_rate = win_rate
                        
        return best_strategy, best_win_rate
        
    def get_best_symbol_for_strategy(self, strategy_name: str, 
                                    market_condition: Optional[str] = None) -> Tuple[str, float]:
        """Get the best symbol for a given strategy

        Args:
            strategy_name (str): Name of the strategy
            market_condition (Optional[str], optional): Current market condition. Defaults to None.

        Returns:
            Tuple[str, float]: (best_symbol, win_rate)
        """
        best_symbol = None
        best_win_rate = 0.0
        
        # Check if strategy exists
        if strategy_name not in self.strategy_memory["strategies"]:
            return best_symbol, best_win_rate
            
        strategy_data = self.strategy_memory["strategies"][strategy_name]
        
        # Iterate through symbols
        for symbol, symbol_data in strategy_data["symbols"].items():
            # If market condition is specified, check symbol-condition data
            if market_condition is not None:
                if market_condition in symbol_data["conditions"]:
                    condition_data = symbol_data["conditions"][market_condition]
                    
                    # Calculate win rate
                    total_trades = condition_data["total_trades"]
                    wins = condition_data["wins"]
                    
                    if total_trades > 0:
                        win_rate = (wins / total_trades) * 100
                        
                        # Check if this is the best symbol so far
                        if win_rate > best_win_rate and total_trades >= 3:  # Require at least 3 trades
                            best_symbol = symbol
                            best_win_rate = win_rate
            else:
                # Calculate overall win rate for this symbol
                total_trades = symbol_data["total_trades"]
                wins = symbol_data["wins"]
                
                if total_trades > 0:
                    win_rate = (wins / total_trades) * 100
                    
                    # Check if this is the best symbol so far
                    if win_rate > best_win_rate and total_trades >= 5:  # Require at least 5 trades
                        best_symbol = symbol
                        best_win_rate = win_rate
                        
        return best_symbol, best_win_rate
        
    def predict_next_condition(self, current_condition: str) -> Tuple[str, float]:
        """Predict the next market condition based on transition probabilities

        Args:
            current_condition (str): Current market condition

        Returns:
            Tuple[str, float]: (predicted_condition, probability)
        """
        predicted_condition = None
        probability = 0.0
        
        # Check if current condition exists in transitions
        if current_condition in self.condition_memory["transitions"]:
            transitions = self.condition_memory["transitions"][current_condition]
            
            # Calculate total transitions from current condition
            total_transitions = sum(transitions.values())
            
            if total_transitions > 0:
                # Find the most likely next condition
                for next_condition, count in transitions.items():
                    next_probability = count / total_transitions
                    
                    if next_probability > probability:
                        predicted_condition = next_condition
                        probability = next_probability
                        
        return predicted_condition, probability
        
    def get_market_memory_for_symbol(self, symbol: str) -> Dict:
        """Get market memory for a specific symbol

        Args:
            symbol (str): Trading symbol

        Returns:
            Dict: Market memory for the symbol
        """
        if symbol in self.market_memory["symbols"]:
            return self.market_memory["symbols"][symbol]
        else:
            return {}
            
    def get_strategy_memory_for_symbol(self, strategy_name: str, symbol: str) -> Dict:
        """Get strategy memory for a specific symbol

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol

        Returns:
            Dict: Strategy memory for the symbol
        """
        if strategy_name in self.strategy_memory["strategies"]:
            if symbol in self.strategy_memory["strategies"][strategy_name]["symbols"]:
                return self.strategy_memory["strategies"][strategy_name]["symbols"][symbol]
                
        return {}
        
    def get_strategy_memory_for_condition(self, strategy_name: str, market_condition: str) -> Dict:
        """Get strategy memory for a specific market condition

        Args:
            strategy_name (str): Name of the strategy
            market_condition (str): Market condition

        Returns:
            Dict: Strategy memory for the market condition
        """
        if strategy_name in self.strategy_memory["strategies"]:
            if market_condition in self.strategy_memory["strategies"][strategy_name]["conditions"]:
                return self.strategy_memory["strategies"][strategy_name]["conditions"][market_condition]
                
        return {}
        
    def get_optimal_trade_parameters(self, strategy_name: str, symbol: str, 
                                   market_condition: str) -> Dict:
        """Get optimal trade parameters based on historical performance

        Args:
            strategy_name (str): Name of the strategy
            symbol (str): Trading symbol
            market_condition (str): Current market condition

        Returns:
            Dict: Optimal trade parameters
        """
        # Initialize default parameters
        params = {
            "confidence": 0.0,
            "recommended_strategy": strategy_name,
            "recommended_symbol": symbol,
            "risk_multiplier": 1.0,
            "expected_win_rate": 0.0,
            "expected_profit_factor": 0.0,
            "next_likely_condition": None,
            "condition_transition_probability": 0.0
        }
        
        # Get strategy memory for this symbol and condition
        symbol_memory = self.get_strategy_memory_for_symbol(strategy_name, symbol)
        condition_memory = self.get_strategy_memory_for_condition(strategy_name, market_condition)
        
        # Calculate confidence based on historical performance
        if symbol_memory and market_condition in symbol_memory.get("conditions", {}):
            # Get symbol-condition data
            symbol_condition_data = symbol_memory["conditions"][market_condition]
            
            # Calculate win rate and profit factor
            total_trades = symbol_condition_data["total_trades"]
            wins = symbol_condition_data["wins"]
            losses = symbol_condition_data["losses"]
            profit_loss = symbol_condition_data["profit_loss"]
            
            if total_trades > 0:
                win_rate = (wins / total_trades) * 100
                params["expected_win_rate"] = win_rate
                
                # Calculate profit factor if there are losses
                if losses > 0 and "profit_loss" in symbol_condition_data:
                    profit_factor = abs(profit_loss) / losses if losses > 0 else 0.0
                    params["expected_profit_factor"] = profit_factor
                    
                # Calculate confidence based on win rate and number of trades
                confidence = win_rate * min(1.0, total_trades / 10.0)  # Scale by number of trades up to 10
                params["confidence"] = confidence
                
                # Adjust risk multiplier based on win rate
                if win_rate >= 70:
                    params["risk_multiplier"] = 1.2  # Increase risk for high win rate
                elif win_rate >= 60:
                    params["risk_multiplier"] = 1.1
                elif win_rate <= 40:
                    params["risk_multiplier"] = 0.8  # Decrease risk for low win rate
                elif win_rate <= 30:
                    params["risk_multiplier"] = 0.7
        elif condition_memory:
            # Use overall condition data if symbol-specific data is not available
            total_trades = condition_memory["total_trades"]
            wins = condition_memory["wins"]
            
            if total_trades > 0:
                win_rate = (wins / total_trades) * 100
                params["expected_win_rate"] = win_rate
                
                # Calculate confidence based on win rate and number of trades
                confidence = win_rate * min(0.8, total_trades / 15.0)  # Scale by number of trades up to 15, max 80%
                params["confidence"] = confidence
                
                # Adjust risk multiplier based on win rate
                if win_rate >= 70:
                    params["risk_multiplier"] = 1.1  # Increase risk for high win rate
                elif win_rate <= 40:
                    params["risk_multiplier"] = 0.9  # Decrease risk for low win rate
        
        # Check if there's a better strategy for this condition
        best_strategy, best_win_rate = self.get_best_strategy_for_condition(market_condition)
        
        if best_strategy and best_strategy != strategy_name and best_win_rate > params["expected_win_rate"]:
            params["recommended_strategy"] = best_strategy
            
        # Check if there's a better symbol for this strategy and condition
        best_symbol, best_symbol_win_rate = self.get_best_symbol_for_strategy(strategy_name, market_condition)
        
        if best_symbol and best_symbol != symbol and best_symbol_win_rate > params["expected_win_rate"]:
            params["recommended_symbol"] = best_symbol
            
        # Predict next market condition
        next_condition, probability = self.predict_next_condition(market_condition)
        
        if next_condition:
            params["next_likely_condition"] = next_condition
            params["condition_transition_probability"] = probability
            
        return params


# Helper functions
def record_trade(strategy_name: str, symbol: str, market_condition: str,
                profit_loss: float, volatility: float = 0.0, 
                news_impact: bool = False) -> bool:
    """Record a trade and update memory (helper function)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Trading symbol
        market_condition (str): Current market condition
        profit_loss (float): Profit or loss from the trade
        volatility (float, optional): Current volatility. Defaults to 0.0.
        news_impact (bool, optional): Whether news impacted the market. Defaults to False.

    Returns:
        bool: True if successful, False otherwise
    """
    memory_engine = MemoryEngine()
    return memory_engine.record_trade(strategy_name, symbol, market_condition, profit_loss, volatility, news_impact)


def get_optimal_trade_parameters(strategy_name: str, symbol: str, market_condition: str) -> Dict:
    """Get optimal trade parameters based on historical performance (helper function)

    Args:
        strategy_name (str): Name of the strategy
        symbol (str): Trading symbol
        market_condition (str): Current market condition

    Returns:
        Dict: Optimal trade parameters
    """
    memory_engine = MemoryEngine()
    return memory_engine.get_optimal_trade_parameters(strategy_name, symbol, market_condition)


# For testing
if __name__ == "__main__":
    # Create memory engine
    memory_engine = MemoryEngine()
    
    # Test recording trades
    print("Recording test trades...")
    memory_engine.record_trade("fibonacci_retracement", "EURUSD", "trending", 50.0, 0.12, False)
    memory_engine.record_trade("fibonacci_retracement", "EURUSD", "trending", 30.0, 0.14, False)
    memory_engine.record_trade("fibonacci_retracement", "EURUSD", "ranging", -20.0, 0.08, False)
    memory_engine.record_trade("support_resistance", "GBPUSD", "ranging", 40.0, 0.09, False)
    memory_engine.record_trade("support_resistance", "GBPUSD", "ranging", 25.0, 0.10, False)
    memory_engine.record_trade("trend_following", "USDJPY", "trending", 60.0, 0.15, True)
    
    # Test getting optimal trade parameters
    print("\nGetting optimal trade parameters...")
    params = memory_engine.get_optimal_trade_parameters("fibonacci_retracement", "EURUSD", "trending")
    print(f"Optimal parameters for fibonacci_retracement on EURUSD in trending market:")
    for key, value in params.items():
        print(f"  {key}: {value}")
        
    # Test getting best strategy for condition
    print("\nGetting best strategy for condition...")
    best_strategy, win_rate = memory_engine.get_best_strategy_for_condition("trending")
    print(f"Best strategy for trending market: {best_strategy} with {win_rate:.1f}% win rate")
    
    # Test predicting next condition
    print("\nPredicting next market condition...")
    next_condition, probability = memory_engine.predict_next_condition("trending")
    print(f"Next likely condition after trending: {next_condition} with {probability:.1f} probability")