# strategy_brain.py

import json
import logging
import os
import random
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
        def get_recent_trades(self, limit=10):
            return []

# Try to import the NewsGuard from news_guard.py
try:
    from news_guard import NewsGuard
except ImportError:
    # Define a minimal version if the import fails
    class NewsGuard:
        def is_affected_by_news(self, currency_pair):
            return False, None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("strategy_brain")

# Constants
STRATEGY_BRAIN_FILE = os.path.join("data", "strategy_brain.json")
STRATEGY_HISTORY_FILE = os.path.join("data", "strategy_history.json")
BRAIN_CONFIG_FILE = os.path.join("config", "brain_config.json")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)


class StrategyBrain:
    """TRAE's Memory + Strategy Evolver
    
    This class is responsible for storing and analyzing past trade signals,
    outcomes, news context, and risk levels. It learns from past trades to
    optimize future strategy selection and parameters.
    """

    def __init__(self, strategy_brain_file: str = STRATEGY_BRAIN_FILE,
                 strategy_history_file: str = STRATEGY_HISTORY_FILE,
                 brain_config_file: str = BRAIN_CONFIG_FILE):
        """Initialize the strategy brain

        Args:
            strategy_brain_file (str): Path to the strategy brain file
            strategy_history_file (str): Path to the strategy history file
            brain_config_file (str): Path to the brain configuration file
        """
        self.strategy_brain_file = strategy_brain_file
        self.strategy_history_file = strategy_history_file
        self.brain_config_file = brain_config_file
        self.evaluator = TradePerformanceEvaluator()
        self.news_guard = NewsGuard()
        self.brain_data = self.load_brain_data()
        self.strategy_history = self.load_strategy_history()
        self.brain_config = self.load_brain_config()

    def load_brain_data(self) -> Dict:
        """Load strategy brain data from file

        Returns:
            Dict: Strategy brain data
        """
        default_data = {
            "strategies": {},
            "last_updated": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        try:
            if os.path.exists(self.strategy_brain_file):
                with open(self.strategy_brain_file, "r") as f:
                    return json.load(f)
            else:
                # Create default brain data file if it doesn't exist
                with open(self.strategy_brain_file, "w") as f:
                    json.dump(default_data, f, indent=4)
                return default_data
        except Exception as e:
            logger.error(f"Error loading strategy brain data: {e}")
            return default_data

    def save_brain_data(self) -> bool:
        """Save strategy brain data to file

        Returns:
            bool: Success status
        """
        try:
            # Update last updated timestamp
            self.brain_data["last_updated"] = datetime.utcnow().isoformat()
            
            with open(self.strategy_brain_file, "w") as f:
                json.dump(self.brain_data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy brain data: {e}")
            return False

    def load_strategy_history(self) -> List[Dict]:
        """Load strategy history from file

        Returns:
            List[Dict]: Strategy history
        """
        try:
            if os.path.exists(self.strategy_history_file):
                with open(self.strategy_history_file, "r") as f:
                    return json.load(f)
            else:
                # Create empty history file if it doesn't exist
                with open(self.strategy_history_file, "w") as f:
                    json.dump([], f, indent=4)
                return []
        except Exception as e:
            logger.error(f"Error loading strategy history: {e}")
            return []

    def save_strategy_history(self) -> bool:
        """Save strategy history to file

        Returns:
            bool: Success status
        """
        try:
            with open(self.strategy_history_file, "w") as f:
                json.dump(self.strategy_history, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy history: {e}")
            return False

    def load_brain_config(self) -> Dict:
        """Load brain configuration from file

        Returns:
            Dict: Brain configuration
        """
        default_config = {
            "learning_rate": 0.1,
            "memory_window_days": 30,
            "cooldown_period_days": 3,
            "min_trades_for_analysis": 10,
            "confidence_threshold": 60,
            "strategy_weights": {
                "win_rate": 0.5,
                "profit_factor": 0.3,
                "recency": 0.2
            },
            "status_thresholds": {
                "active": 65,  # Win rate % to keep active
                "cooldown": 45,  # Win rate % to put in cooldown
                "paused": 35    # Win rate % to pause
            },
            "reactivation": {
                "cooldown_days": 3,
                "paused_days": 7
            }
        }

        try:
            if os.path.exists(self.brain_config_file):
                with open(self.brain_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.brain_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading brain config: {e}")
            return default_config

    def save_brain_config(self) -> bool:
        """Save brain configuration to file

        Returns:
            bool: Success status
        """
        try:
            with open(self.brain_config_file, "w") as f:
                json.dump(self.brain_config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving brain config: {e}")
            return False

    def record_trade(self, strategy: str, symbol: str, result: str, 
                     confidence: int, news_nearby: bool, 
                     profit_loss: float = 0.0, tags: List[str] = None) -> bool:
        """Record a trade in the strategy history

        Args:
            strategy (str): Strategy name
            symbol (str): Trading symbol
            result (str): Trade result ('win', 'loss', 'breakeven')
            confidence (int): Confidence score (0-100)
            news_nearby (bool): Whether news was nearby
            profit_loss (float, optional): Profit or loss amount. Defaults to 0.0.
            tags (List[str], optional): List of tags. Defaults to None.

        Returns:
            bool: Success status
        """
        try:
            # Create trade record
            trade = {
                "date": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "strategy": strategy,
                "confidence": confidence,
                "news_nearby": news_nearby,
                "result": result.lower(),
                "profit_loss": profit_loss,
                "tags": tags or []
            }

            # Add to strategy history
            self.strategy_history.append(trade)
            self.save_strategy_history()

            # Update brain data
            self.update_strategy_brain(trade)

            return True
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
            return False

    def update_strategy_brain(self, trade: Dict) -> bool:
        """Update strategy brain with new trade data

        Args:
            trade (Dict): Trade record

        Returns:
            bool: Success status
        """
        try:
            strategy_name = trade["strategy"]
            result = trade["result"]
            
            # Initialize strategy data if it doesn't exist
            if strategy_name not in self.brain_data["strategies"]:
                self.brain_data["strategies"][strategy_name] = {
                    "win_rate": 0,
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "breakeven": 0,
                    "last_win": None,
                    "last_loss": None,
                    "status": "active",
                    "confidence_boost": False,
                    "symbols": {},
                    "news_performance": {
                        "with_news": {"trades": 0, "wins": 0},
                        "without_news": {"trades": 0, "wins": 0}
                    }
                }
            
            strategy = self.brain_data["strategies"][strategy_name]
            
            # Update basic counts
            strategy["total_trades"] += 1
            
            if result == "win":
                strategy["wins"] += 1
                strategy["last_win"] = trade["date"]
            elif result == "loss":
                strategy["losses"] += 1
                strategy["last_loss"] = trade["date"]
            else:  # breakeven
                strategy["breakeven"] += 1
            
            # Update win rate
            if strategy["total_trades"] > 0:
                strategy["win_rate"] = int((strategy["wins"] / strategy["total_trades"]) * 100)
            
            # Update symbol data
            symbol = trade["symbol"]
            if symbol not in strategy["symbols"]:
                strategy["symbols"][symbol] = {
                    "trades": 0,
                    "wins": 0,
                    "win_rate": 0
                }
            
            strategy["symbols"][symbol]["trades"] += 1
            if result == "win":
                strategy["symbols"][symbol]["wins"] += 1
            
            # Update symbol win rate
            if strategy["symbols"][symbol]["trades"] > 0:
                strategy["symbols"][symbol]["win_rate"] = int(
                    (strategy["symbols"][symbol]["wins"] / strategy["symbols"][symbol]["trades"]) * 100
                )
            
            # Update news performance
            news_key = "with_news" if trade["news_nearby"] else "without_news"
            strategy["news_performance"][news_key]["trades"] += 1
            if result == "win":
                strategy["news_performance"][news_key]["wins"] += 1
            
            # Update strategy status based on win rate
            self.update_strategy_status(strategy_name)
            
            # Save updated brain data
            return self.save_brain_data()
        except Exception as e:
            logger.error(f"Error updating strategy brain: {e}")
            return False

    def update_strategy_status(self, strategy_name: str) -> str:
        """Update strategy status based on performance

        Args:
            strategy_name (str): Strategy name

        Returns:
            str: Updated status
        """
        try:
            if strategy_name not in self.brain_data["strategies"]:
                return "unknown"
            
            strategy = self.brain_data["strategies"][strategy_name]
            thresholds = self.brain_config["status_thresholds"]
            
            # Need minimum trades for analysis
            if strategy["total_trades"] < self.brain_config["min_trades_for_analysis"]:
                return strategy["status"]
            
            # Check if strategy is in cooldown or paused and should be reactivated
            if strategy["status"] in ["cooldown", "paused"]:
                last_loss_date = strategy["last_loss"]
                if last_loss_date:
                    days_since_loss = (datetime.utcnow() - datetime.fromisoformat(last_loss_date)).days
                    
                    if strategy["status"] == "cooldown" and days_since_loss >= self.brain_config["reactivation"]["cooldown_days"]:
                        strategy["status"] = "active"
                        logger.info(f"Strategy '{strategy_name}' reactivated from cooldown after {days_since_loss} days")
                    elif strategy["status"] == "paused" and days_since_loss >= self.brain_config["reactivation"]["paused_days"]:
                        strategy["status"] = "cooldown"
                        logger.info(f"Strategy '{strategy_name}' moved from paused to cooldown after {days_since_loss} days")
            
            # Update status based on win rate
            win_rate = strategy["win_rate"]
            
            if win_rate >= thresholds["active"]:
                if strategy["status"] != "active":
                    logger.info(f"Strategy '{strategy_name}' activated with {win_rate}% win rate")
                strategy["status"] = "active"
                # Add confidence boost for high win rate
                strategy["confidence_boost"] = win_rate >= (thresholds["active"] + 10)
            elif win_rate >= thresholds["cooldown"]:
                if strategy["status"] == "active":
                    logger.info(f"Strategy '{strategy_name}' put in cooldown with {win_rate}% win rate")
                strategy["status"] = "cooldown"
                strategy["confidence_boost"] = False
            else:  # win_rate < thresholds["paused"]
                if strategy["status"] != "paused":
                    logger.info(f"Strategy '{strategy_name}' paused with {win_rate}% win rate")
                strategy["status"] = "paused"
                strategy["confidence_boost"] = False
            
            # Save updated brain data
            self.save_brain_data()
            
            return strategy["status"]
        except Exception as e:
            logger.error(f"Error updating strategy status: {e}")
            return "unknown"

    def get_strategy_status(self, strategy_name: str) -> Dict:
        """Get the current status and metrics for a strategy

        Args:
            strategy_name (str): Strategy name

        Returns:
            Dict: Strategy status and metrics
        """
        try:
            if strategy_name not in self.brain_data["strategies"]:
                return {
                    "status": "unknown",
                    "win_rate": 0,
                    "confidence_boost": False,
                    "message": f"Strategy '{strategy_name}' not found in brain data"
                }
            
            strategy = self.brain_data["strategies"][strategy_name]
            
            # Get best performing symbol
            best_symbol = None
            best_win_rate = 0
            
            for symbol, data in strategy["symbols"].items():
                if data["trades"] >= 5 and data["win_rate"] > best_win_rate:
                    best_symbol = symbol
                    best_win_rate = data["win_rate"]
            
            # Check news performance
            news_impact = "neutral"
            with_news = strategy["news_performance"]["with_news"]
            without_news = strategy["news_performance"]["without_news"]
            
            if with_news["trades"] >= 5 and without_news["trades"] >= 5:
                with_news_win_rate = (with_news["wins"] / with_news["trades"]) * 100 if with_news["trades"] > 0 else 0
                without_news_win_rate = (without_news["wins"] / without_news["trades"]) * 100 if without_news["trades"] > 0 else 0
                
                if with_news_win_rate > without_news_win_rate + 10:
                    news_impact = "positive"
                elif without_news_win_rate > with_news_win_rate + 10:
                    news_impact = "negative"
            
            return {
                "status": strategy["status"],
                "win_rate": strategy["win_rate"],
                "total_trades": strategy["total_trades"],
                "wins": strategy["wins"],
                "losses": strategy["losses"],
                "confidence_boost": strategy["confidence_boost"],
                "best_symbol": best_symbol,
                "best_symbol_win_rate": best_win_rate if best_symbol else 0,
                "news_impact": news_impact,
                "last_win": strategy["last_win"],
                "last_loss": strategy["last_loss"]
            }
        except Exception as e:
            logger.error(f"Error getting strategy status: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }

    def get_all_strategies_status(self) -> Dict:
        """Get status for all strategies

        Returns:
            Dict: Status for all strategies
        """
        result = {}
        
        for strategy_name in self.brain_data["strategies"]:
            result[strategy_name] = self.get_strategy_status(strategy_name)
        
        return result

    def adjust_confidence(self, strategy_name: str, base_confidence: int) -> int:
        """Adjust confidence score based on strategy brain data

        Args:
            strategy_name (str): Strategy name
            base_confidence (int): Base confidence score (0-100)

        Returns:
            int: Adjusted confidence score
        """
        try:
            if strategy_name not in self.brain_data["strategies"]:
                return base_confidence
            
            strategy = self.brain_data["strategies"][strategy_name]
            
            # Apply status-based adjustments
            if strategy["status"] == "active":
                confidence_multiplier = 1.0
            elif strategy["status"] == "cooldown":
                confidence_multiplier = 0.7
            else:  # paused
                confidence_multiplier = 0.4
            
            # Apply confidence boost if applicable
            if strategy["confidence_boost"]:
                confidence_multiplier += 0.2
            
            # Calculate adjusted confidence
            adjusted_confidence = int(base_confidence * confidence_multiplier)
            
            # Ensure confidence is within bounds
            adjusted_confidence = max(0, min(100, adjusted_confidence))
            
            return adjusted_confidence
        except Exception as e:
            logger.error(f"Error adjusting confidence: {e}")
            return base_confidence

    def get_recommended_strategies(self, top_n: int = 3) -> List[Dict]:
        """Get top recommended strategies based on performance

        Args:
            top_n (int, optional): Number of strategies to return. Defaults to 3.

        Returns:
            List[Dict]: Top recommended strategies
        """
        try:
            # Filter for active strategies with minimum trades
            eligible_strategies = [
                (name, data) for name, data in self.brain_data["strategies"].items()
                if data["status"] == "active" and data["total_trades"] >= self.brain_config["min_trades_for_analysis"]
            ]
            
            # Sort by win rate (descending)
            eligible_strategies.sort(key=lambda x: x[1]["win_rate"], reverse=True)
            
            # Get top N strategies
            recommendations = []
            for name, data in eligible_strategies[:top_n]:
                # Get best symbol for this strategy
                best_symbol = None
                best_win_rate = 0
                
                for symbol, symbol_data in data["symbols"].items():
                    if symbol_data["trades"] >= 3 and symbol_data["win_rate"] > best_win_rate:
                        best_symbol = symbol
                        best_win_rate = symbol_data["win_rate"]
                
                recommendations.append({
                    "strategy": name,
                    "win_rate": data["win_rate"],
                    "confidence_boost": data["confidence_boost"],
                    "best_symbol": best_symbol,
                    "best_symbol_win_rate": best_win_rate if best_symbol else 0
                })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting recommended strategies: {e}")
            return []

    def analyze_recent_performance(self, days: int = 7) -> Dict:
        """Analyze recent trading performance

        Args:
            days (int, optional): Number of days to analyze. Defaults to 7.

        Returns:
            Dict: Performance analysis
        """
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Filter recent trades
            recent_trades = [trade for trade in self.strategy_history if trade["date"] >= cutoff_date]
            
            if not recent_trades:
                return {
                    "message": f"No trades found in the last {days} days",
                    "strategies": {},
                    "symbols": {},
                    "overall_win_rate": 0
                }
            
            # Analyze by strategy
            strategies = {}
            for trade in recent_trades:
                strategy_name = trade["strategy"]
                if strategy_name not in strategies:
                    strategies[strategy_name] = {
                        "trades": 0,
                        "wins": 0,
                        "win_rate": 0,
                        "profit_loss": 0.0
                    }
                
                strategies[strategy_name]["trades"] += 1
                if trade["result"] == "win":
                    strategies[strategy_name]["wins"] += 1
                strategies[strategy_name]["profit_loss"] += trade.get("profit_loss", 0.0)
            
            # Calculate win rates
            for strategy_name, data in strategies.items():
                if data["trades"] > 0:
                    data["win_rate"] = int((data["wins"] / data["trades"]) * 100)
            
            # Analyze by symbol
            symbols = {}
            for trade in recent_trades:
                symbol = trade["symbol"]
                if symbol not in symbols:
                    symbols[symbol] = {
                        "trades": 0,
                        "wins": 0,
                        "win_rate": 0,
                        "profit_loss": 0.0
                    }
                
                symbols[symbol]["trades"] += 1
                if trade["result"] == "win":
                    symbols[symbol]["wins"] += 1
                symbols[symbol]["profit_loss"] += trade.get("profit_loss", 0.0)
            
            # Calculate win rates
            for symbol, data in symbols.items():
                if data["trades"] > 0:
                    data["win_rate"] = int((data["wins"] / data["trades"]) * 100)
            
            # Calculate overall win rate
            total_trades = len(recent_trades)
            total_wins = sum(1 for trade in recent_trades if trade["result"] == "win")
            overall_win_rate = int((total_wins / total_trades) * 100) if total_trades > 0 else 0
            
            return {
                "total_trades": total_trades,
                "total_wins": total_wins,
                "overall_win_rate": overall_win_rate,
                "strategies": strategies,
                "symbols": symbols
            }
        except Exception as e:
            logger.error(f"Error analyzing recent performance: {e}")
            return {
                "error": str(e)
            }


# Helper functions
def get_strategy_status(strategy_name: str) -> Dict:
    """Get the current status and metrics for a strategy (helper function)

    Args:
        strategy_name (str): Strategy name

    Returns:
        Dict: Strategy status and metrics
    """
    brain = StrategyBrain()
    return brain.get_strategy_status(strategy_name)


def adjust_confidence(strategy_name: str, base_confidence: int) -> int:
    """Adjust confidence score based on strategy brain data (helper function)

    Args:
        strategy_name (str): Strategy name
        base_confidence (int): Base confidence score (0-100)

    Returns:
        int: Adjusted confidence score
    """
    brain = StrategyBrain()
    return brain.adjust_confidence(strategy_name, base_confidence)


def get_recommended_strategies(top_n: int = 3) -> List[Dict]:
    """Get top recommended strategies based on performance (helper function)

    Args:
        top_n (int, optional): Number of strategies to return. Defaults to 3.

    Returns:
        List[Dict]: Top recommended strategies
    """
    brain = StrategyBrain()
    return brain.get_recommended_strategies(top_n)


# For testing
if __name__ == "__main__":
    # Create an instance of the strategy brain
    brain = StrategyBrain()
    
    # Record some test trades
    print("Recording test trades...")
    
    # FVG strategy trades
    brain.record_trade(
        strategy="FVG",
        symbol="EURUSD",
        result="win",
        confidence=75,
        news_nearby=False,
        profit_loss=50.0
    )
    
    brain.record_trade(
        strategy="FVG",
        symbol="EURUSD",
        result="loss",
        confidence=65,
        news_nearby=True,
        profit_loss=-30.0
    )
    
    brain.record_trade(
        strategy="FVG",
        symbol="GBPUSD",
        result="loss",
        confidence=60,
        news_nearby=False,
        profit_loss=-25.0
    )
    
    # OTE strategy trades
    brain.record_trade(
        strategy="OTE",
        symbol="EURUSD",
        result="win",
        confidence=80,
        news_nearby=False,
        profit_loss=45.0
    )
    
    brain.record_trade(
        strategy="OTE",
        symbol="GBPUSD",
        result="win",
        confidence=75,
        news_nearby=False,
        profit_loss=35.0
    )
    
    brain.record_trade(
        strategy="OTE",
        symbol="USDJPY",
        result="win",
        confidence=70,
        news_nearby=True,
        profit_loss=30.0
    )
    
    # Cypher strategy trades
    brain.record_trade(
        strategy="Cypher",
        symbol="EURUSD",
        result="loss",
        confidence=65,
        news_nearby=False,
        profit_loss=-20.0
    )
    
    brain.record_trade(
        strategy="Cypher",
        symbol="GBPUSD",
        result="win",
        confidence=70,
        news_nearby=False,
        profit_loss=25.0
    )
    
    brain.record_trade(
        strategy="Cypher",
        symbol="USDJPY",
        result="loss",
        confidence=60,
        news_nearby=True,
        profit_loss=-30.0
    )
    
    # Get strategy statuses
    print("\nStrategy Statuses:")
    statuses = brain.get_all_strategies_status()
    
    for strategy_name, status in statuses.items():
        print(f"\n{strategy_name}:")
        print(f"  Status: {status['status']}")
        print(f"  Win Rate: {status['win_rate']}%")
        print(f"  Total Trades: {status['total_trades']}")
        print(f"  Confidence Boost: {status['confidence_boost']}")
        if status['best_symbol']:
            print(f"  Best Symbol: {status['best_symbol']} ({status['best_symbol_win_rate']}% win rate)")
        print(f"  News Impact: {status['news_impact']}")
    
    # Test confidence adjustment
    print("\nConfidence Adjustment Test:")
    base_confidence = 70
    
    for strategy_name in ["FVG", "OTE", "Cypher"]:
        adjusted = brain.adjust_confidence(strategy_name, base_confidence)
        print(f"  {strategy_name}: {base_confidence} -> {adjusted}")
    
    # Get recommended strategies
    print("\nRecommended Strategies:")
    recommendations = brain.get_recommended_strategies()
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['strategy']} (Win Rate: {rec['win_rate']}%)")
        if rec['best_symbol']:
            print(f"     Best Symbol: {rec['best_symbol']} ({rec['best_symbol_win_rate']}% win rate)")
    
    # Analyze recent performance
    print("\nRecent Performance Analysis:")
    analysis = brain.analyze_recent_performance()
    
    print(f"  Total Trades: {analysis['total_trades']}")
    print(f"  Overall Win Rate: {analysis['overall_win_rate']}%")
    
    print("\n  Strategy Performance:")
    for strategy_name, data in analysis['strategies'].items():
        print(f"    {strategy_name}: {data['win_rate']}% win rate ({data['wins']}/{data['trades']})")
    
    print("\n  Symbol Performance:")
    for symbol, data in analysis['symbols'].items():
        print(f"    {symbol}: {data['win_rate']}% win rate ({data['wins']}/{data['trades']})")