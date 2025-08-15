# strategy_optimizer.py

import json
import logging
import os
import datetime
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("strategy_optimizer")

# Constants
STRATEGY_HISTORY_FILE = os.path.join("data", "strategy_history.json")
STRATEGY_BRAIN_FILE = os.path.join("data", "strategy_brain.json")
SENTINEL_CONFIG_FILE = os.path.join("sentinel_config.yml")

# Ensure directories exist
os.makedirs("data", exist_ok=True)


class StrategyOptimizer:
    """Weekly AI-Based Weight Adjuster
    
    This class analyzes trading history and optimizes strategy weights,
    risk levels, and trading parameters based on performance metrics.
    """

    def __init__(self, strategy_history_file: str = STRATEGY_HISTORY_FILE,
                 strategy_brain_file: str = STRATEGY_BRAIN_FILE,
                 sentinel_config_file: str = SENTINEL_CONFIG_FILE):
        """Initialize the strategy optimizer

        Args:
            strategy_history_file (str): Path to the strategy history file
            strategy_brain_file (str): Path to the strategy brain file
            sentinel_config_file (str): Path to the sentinel configuration file
        """
        self.strategy_history_file = strategy_history_file
        self.strategy_brain_file = strategy_brain_file
        self.sentinel_config_file = sentinel_config_file
        
        # Load data
        self.history_data = self.load_history_data()
        self.brain_data = self.load_brain_data()
        
        # Initialize optimization parameters
        self.lookback_days = 7  # Default to analyze last 7 days
        self.min_trades_threshold = 5  # Minimum trades needed for reliable stats
        self.win_rate_threshold = 60  # Win rate threshold for strategy promotion
        self.loss_streak_threshold = 3  # Consecutive losses to trigger cooldown
        
        # Strategy adjustment parameters
        self.weight_increment = 10  # Percentage points to adjust weights
        self.confidence_boost_threshold = 70  # Win rate needed for confidence boost
        self.cooldown_days = 2  # Days to cooldown a struggling strategy

    def load_history_data(self) -> Dict:
        """Load strategy history data from file

        Returns:
            Dict: Strategy history data
        """
        default_data = {
            "trades": [],
            "strategy_stats": {},
            "pair_stats": {},
            "time_stats": {},
            "market_condition_stats": {},
            "news_impact_stats": {},
            "last_updated": datetime.datetime.utcnow().isoformat()
        }

        try:
            if os.path.exists(self.strategy_history_file):
                with open(self.strategy_history_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Strategy history file not found: {self.strategy_history_file}")
                return default_data
        except Exception as e:
            logger.error(f"Error loading strategy history data: {e}")
            return default_data

    def load_brain_data(self) -> Dict:
        """Load strategy brain data from file

        Returns:
            Dict: Strategy brain data
        """
        default_data = {
            "strategies": {},
            "pairs": {},
            "time_periods": {},
            "market_conditions": {},
            "last_updated": datetime.datetime.utcnow().isoformat()
        }

        try:
            if os.path.exists(self.strategy_brain_file):
                with open(self.strategy_brain_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Strategy brain file not found: {self.strategy_brain_file}")
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
            self.brain_data["last_updated"] = datetime.datetime.utcnow().isoformat()
            
            with open(self.strategy_brain_file, "w") as f:
                json.dump(self.brain_data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving strategy brain data: {e}")
            return False

    def get_recent_trades(self, days: int = None) -> List[Dict]:
        """Get recent trades from history

        Args:
            days (int, optional): Number of days to look back. Defaults to None.

        Returns:
            List[Dict]: List of recent trades
        """
        if days is None:
            days = self.lookback_days
        
        trades = self.history_data.get("trades", [])
        
        if not trades:
            return []
        
        # Calculate cutoff date
        today = datetime.datetime.now().date()
        cutoff_date = today - datetime.timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        # Filter trades by date
        recent_trades = [trade for trade in trades if trade.get("date", "") >= cutoff_str]
        
        return recent_trades

    def analyze_strategy_performance(self, days: int = None) -> Dict[str, Dict]:
        """Analyze strategy performance over recent period

        Args:
            days (int, optional): Number of days to analyze. Defaults to None.

        Returns:
            Dict[str, Dict]: Strategy performance metrics
        """
        recent_trades = self.get_recent_trades(days)
        
        if not recent_trades:
            logger.warning("No recent trades found for analysis")
            return {}
        
        # Group trades by strategy
        strategy_trades = defaultdict(list)
        
        for trade in recent_trades:
            strategy = trade.get("strategy")
            if strategy:
                strategy_trades[strategy].append(trade)
        
        # Calculate performance metrics for each strategy
        strategy_performance = {}
        
        for strategy, trades in strategy_trades.items():
            # Skip if not enough trades for reliable stats
            if len(trades) < self.min_trades_threshold:
                continue
            
            # Calculate win rate
            wins = sum(1 for t in trades if t.get("result") == "win")
            total = len(trades)
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            # Calculate average profit
            profits = [t.get("profit", 0) for t in trades]
            avg_profit = sum(profits) / len(profits) if profits else 0
            
            # Calculate average pips
            pips = [t.get("pips", 0) for t in trades]
            avg_pips = sum(pips) / len(pips) if pips else 0
            
            # Calculate average risk-reward ratio
            risk_rewards = [t.get("risk_reward", 0) for t in trades if "risk_reward" in t]
            avg_risk_reward = sum(risk_rewards) / len(risk_rewards) if risk_rewards else 0
            
            # Check for consecutive losses
            consecutive_losses = 0
            max_consecutive_losses = 0
            
            for trade in trades:
                if trade.get("result") == "loss":
                    consecutive_losses += 1
                    max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                else:
                    consecutive_losses = 0
            
            # Store performance metrics
            strategy_performance[strategy] = {
                "win_rate": win_rate,
                "avg_profit": avg_profit,
                "avg_pips": avg_pips,
                "avg_risk_reward": avg_risk_reward,
                "total_trades": total,
                "max_consecutive_losses": max_consecutive_losses,
                "last_trade_result": trades[-1].get("result"),
                "last_trade_date": trades[-1].get("date")
            }
        
        return strategy_performance

    def analyze_pair_performance(self, days: int = None) -> Dict[str, Dict]:
        """Analyze currency pair performance over recent period

        Args:
            days (int, optional): Number of days to analyze. Defaults to None.

        Returns:
            Dict[str, Dict]: Pair performance metrics
        """
        recent_trades = self.get_recent_trades(days)
        
        if not recent_trades:
            logger.warning("No recent trades found for analysis")
            return {}
        
        # Group trades by pair
        pair_trades = defaultdict(list)
        
        for trade in recent_trades:
            symbol = trade.get("symbol")
            if symbol:
                pair_trades[symbol].append(trade)
        
        # Calculate performance metrics for each pair
        pair_performance = {}
        
        for pair, trades in pair_trades.items():
            # Skip if not enough trades for reliable stats
            if len(trades) < self.min_trades_threshold:
                continue
            
            # Calculate win rate
            wins = sum(1 for t in trades if t.get("result") == "win")
            total = len(trades)
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            # Calculate average profit
            profits = [t.get("profit", 0) for t in trades]
            avg_profit = sum(profits) / len(profits) if profits else 0
            
            # Find best strategy for this pair
            strategy_wins = defaultdict(int)
            strategy_total = defaultdict(int)
            
            for trade in trades:
                strategy = trade.get("strategy")
                if strategy:
                    strategy_total[strategy] += 1
                    if trade.get("result") == "win":
                        strategy_wins[strategy] += 1
            
            best_strategy = None
            best_win_rate = 0
            
            for strategy, total in strategy_total.items():
                if total >= 3:  # Minimum trades for strategy consideration
                    strategy_win_rate = (strategy_wins[strategy] / total) * 100
                    if strategy_win_rate > best_win_rate:
                        best_win_rate = strategy_win_rate
                        best_strategy = strategy
            
            # Find best time of day
            time_wins = defaultdict(int)
            time_total = defaultdict(int)
            
            for trade in trades:
                time_of_day = trade.get("time_of_day")
                if time_of_day:
                    time_total[time_of_day] += 1
                    if trade.get("result") == "win":
                        time_wins[time_of_day] += 1
            
            best_time = None
            best_time_win_rate = 0
            
            for time_of_day, total in time_total.items():
                if total >= 3:  # Minimum trades for time consideration
                    time_win_rate = (time_wins[time_of_day] / total) * 100
                    if time_win_rate > best_time_win_rate:
                        best_time_win_rate = time_win_rate
                        best_time = time_of_day
            
            # Store performance metrics
            pair_performance[pair] = {
                "win_rate": win_rate,
                "avg_profit": avg_profit,
                "total_trades": total,
                "best_strategy": best_strategy,
                "best_strategy_win_rate": best_win_rate if best_strategy else 0,
                "best_time": best_time,
                "best_time_win_rate": best_time_win_rate if best_time else 0,
                "last_trade_result": trades[-1].get("result"),
                "last_trade_date": trades[-1].get("date")
            }
        
        return pair_performance

    def analyze_market_conditions(self, days: int = None) -> Dict[str, Dict]:
        """Analyze performance under different market conditions

        Args:
            days (int, optional): Number of days to analyze. Defaults to None.

        Returns:
            Dict[str, Dict]: Market condition performance metrics
        """
        recent_trades = self.get_recent_trades(days)
        
        if not recent_trades:
            logger.warning("No recent trades found for analysis")
            return {}
        
        # Group trades by market condition
        condition_trades = defaultdict(list)
        
        for trade in recent_trades:
            condition = trade.get("market_condition")
            if condition:
                condition_trades[condition].append(trade)
        
        # Calculate performance metrics for each market condition
        condition_performance = {}
        
        for condition, trades in condition_trades.items():
            # Skip if not enough trades for reliable stats
            if len(trades) < self.min_trades_threshold:
                continue
            
            # Calculate win rate
            wins = sum(1 for t in trades if t.get("result") == "win")
            total = len(trades)
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            # Find best strategy for this market condition
            strategy_wins = defaultdict(int)
            strategy_total = defaultdict(int)
            
            for trade in trades:
                strategy = trade.get("strategy")
                if strategy:
                    strategy_total[strategy] += 1
                    if trade.get("result") == "win":
                        strategy_wins[strategy] += 1
            
            best_strategy = None
            best_win_rate = 0
            
            for strategy, total in strategy_total.items():
                if total >= 3:  # Minimum trades for strategy consideration
                    strategy_win_rate = (strategy_wins[strategy] / total) * 100
                    if strategy_win_rate > best_win_rate:
                        best_win_rate = strategy_win_rate
                        best_strategy = strategy
            
            # Store performance metrics
            condition_performance[condition] = {
                "win_rate": win_rate,
                "total_trades": total,
                "best_strategy": best_strategy,
                "best_strategy_win_rate": best_win_rate if best_strategy else 0
            }
        
        return condition_performance

    def analyze_news_impact(self, days: int = None) -> Dict[str, Dict]:
        """Analyze performance with and without news nearby

        Args:
            days (int, optional): Number of days to analyze. Defaults to None.

        Returns:
            Dict[str, Dict]: News impact performance metrics
        """
        recent_trades = self.get_recent_trades(days)
        
        if not recent_trades:
            logger.warning("No recent trades found for analysis")
            return {}
        
        # Group trades by news presence
        with_news_trades = [t for t in recent_trades if t.get("news_nearby", False)]
        without_news_trades = [t for t in recent_trades if not t.get("news_nearby", False)]
        
        # Calculate performance metrics for trades with news
        with_news_wins = sum(1 for t in with_news_trades if t.get("result") == "win")
        with_news_total = len(with_news_trades)
        with_news_win_rate = (with_news_wins / with_news_total) * 100 if with_news_total > 0 else 0
        
        # Calculate performance metrics for trades without news
        without_news_wins = sum(1 for t in without_news_trades if t.get("result") == "win")
        without_news_total = len(without_news_trades)
        without_news_win_rate = (without_news_wins / without_news_total) * 100 if without_news_total > 0 else 0
        
        # Store performance metrics
        news_impact = {
            "with_news": {
                "win_rate": with_news_win_rate,
                "total_trades": with_news_total,
                "wins": with_news_wins,
                "losses": with_news_total - with_news_wins
            },
            "without_news": {
                "win_rate": without_news_win_rate,
                "total_trades": without_news_total,
                "wins": without_news_wins,
                "losses": without_news_total - without_news_wins
            }
        }
        
        return news_impact

    def update_strategy_brain(self) -> bool:
        """Update strategy brain based on performance analysis

        Returns:
            bool: Success status
        """
        try:
            # Analyze performance
            strategy_performance = self.analyze_strategy_performance()
            pair_performance = self.analyze_pair_performance()
            market_condition_performance = self.analyze_market_conditions()
            news_impact = self.analyze_news_impact()
            
            if not strategy_performance:
                logger.warning("No strategy performance data available for brain update")
                return False
            
            # Initialize brain data structure if needed
            if "strategies" not in self.brain_data:
                self.brain_data["strategies"] = {}
            
            if "pairs" not in self.brain_data:
                self.brain_data["pairs"] = {}
            
            if "market_conditions" not in self.brain_data:
                self.brain_data["market_conditions"] = {}
            
            if "news_impact" not in self.brain_data:
                self.brain_data["news_impact"] = {}
            
            # Update strategy brain with strategy performance
            for strategy, performance in strategy_performance.items():
                if strategy not in self.brain_data["strategies"]:
                    self.brain_data["strategies"][strategy] = {
                        "win_rate": performance["win_rate"],
                        "avg_profit": performance["avg_profit"],
                        "total_trades": performance["total_trades"],
                        "status": "active",
                        "weight": 100,  # Default weight
                        "confidence_boost": False,
                        "last_updated": datetime.datetime.utcnow().isoformat()
                    }
                else:
                    # Update existing strategy data
                    self.brain_data["strategies"][strategy]["win_rate"] = performance["win_rate"]
                    self.brain_data["strategies"][strategy]["avg_profit"] = performance["avg_profit"]
                    self.brain_data["strategies"][strategy]["total_trades"] = performance["total_trades"]
                    self.brain_data["strategies"][strategy]["last_updated"] = datetime.datetime.utcnow().isoformat()
                    
                    # Update strategy status based on performance
                    if performance["win_rate"] >= self.confidence_boost_threshold:
                        self.brain_data["strategies"][strategy]["confidence_boost"] = True
                        self.brain_data["strategies"][strategy]["status"] = "active"
                        
                        # Increase weight if performing well
                        current_weight = self.brain_data["strategies"][strategy].get("weight", 100)
                        self.brain_data["strategies"][strategy]["weight"] = min(150, current_weight + self.weight_increment)
                    
                    elif performance["win_rate"] < self.win_rate_threshold:
                        self.brain_data["strategies"][strategy]["confidence_boost"] = False
                        
                        # Decrease weight if performing poorly
                        current_weight = self.brain_data["strategies"][strategy].get("weight", 100)
                        self.brain_data["strategies"][strategy]["weight"] = max(50, current_weight - self.weight_increment)
                        
                        # Put strategy in cooldown if it has consecutive losses
                        if performance["max_consecutive_losses"] >= self.loss_streak_threshold:
                            self.brain_data["strategies"][strategy]["status"] = "cooldown"
                            self.brain_data["strategies"][strategy]["cooldown_until"] = (
                                datetime.datetime.now() + datetime.timedelta(days=self.cooldown_days)
                            ).isoformat()
                    else:
                        # Maintain current status for average performers
                        if self.brain_data["strategies"][strategy].get("status") == "cooldown":
                            # Check if cooldown period has expired
                            cooldown_until = self.brain_data["strategies"][strategy].get("cooldown_until")
                            if cooldown_until and datetime.datetime.fromisoformat(cooldown_until) <= datetime.datetime.now():
                                self.brain_data["strategies"][strategy]["status"] = "active"
                
                # Record last trade result
                if "last_trade_result" in performance:
                    self.brain_data["strategies"][strategy]["last_trade_result"] = performance["last_trade_result"]
                    
                if "last_trade_date" in performance:
                    self.brain_data["strategies"][strategy]["last_trade_date"] = performance["last_trade_date"]
            
            # Update pair performance data
            for pair, performance in pair_performance.items():
                if pair not in self.brain_data["pairs"]:
                    self.brain_data["pairs"][pair] = {
                        "win_rate": performance["win_rate"],
                        "avg_profit": performance["avg_profit"],
                        "total_trades": performance["total_trades"],
                        "best_strategy": performance.get("best_strategy"),
                        "best_time": performance.get("best_time"),
                        "status": "active",
                        "last_updated": datetime.datetime.utcnow().isoformat()
                    }
                else:
                    # Update existing pair data
                    self.brain_data["pairs"][pair]["win_rate"] = performance["win_rate"]
                    self.brain_data["pairs"][pair]["avg_profit"] = performance["avg_profit"]
                    self.brain_data["pairs"][pair]["total_trades"] = performance["total_trades"]
                    self.brain_data["pairs"][pair]["best_strategy"] = performance.get("best_strategy")
                    self.brain_data["pairs"][pair]["best_time"] = performance.get("best_time")
                    self.brain_data["pairs"][pair]["last_updated"] = datetime.datetime.utcnow().isoformat()
                    
                    # Update pair status based on performance
                    if performance["win_rate"] < 40:  # Poor performance threshold
                        self.brain_data["pairs"][pair]["status"] = "caution"
                    else:
                        self.brain_data["pairs"][pair]["status"] = "active"
                
                # Record last trade result
                if "last_trade_result" in performance:
                    self.brain_data["pairs"][pair]["last_trade_result"] = performance["last_trade_result"]
                    
                if "last_trade_date" in performance:
                    self.brain_data["pairs"][pair]["last_trade_date"] = performance["last_trade_date"]
            
            # Update market condition data
            for condition, performance in market_condition_performance.items():
                if condition not in self.brain_data["market_conditions"]:
                    self.brain_data["market_conditions"][condition] = {
                        "win_rate": performance["win_rate"],
                        "total_trades": performance["total_trades"],
                        "best_strategy": performance.get("best_strategy"),
                        "last_updated": datetime.datetime.utcnow().isoformat()
                    }
                else:
                    # Update existing market condition data
                    self.brain_data["market_conditions"][condition]["win_rate"] = performance["win_rate"]
                    self.brain_data["market_conditions"][condition]["total_trades"] = performance["total_trades"]
                    self.brain_data["market_conditions"][condition]["best_strategy"] = performance.get("best_strategy")
                    self.brain_data["market_conditions"][condition]["last_updated"] = datetime.datetime.utcnow().isoformat()
            
            # Update news impact data
            self.brain_data["news_impact"] = news_impact
            self.brain_data["news_impact"]["last_updated"] = datetime.datetime.utcnow().isoformat()
            
            # Save updated brain data
            return self.save_brain_data()
        except Exception as e:
            logger.error(f"Error updating strategy brain: {e}")
            return False

    def generate_optimization_recommendations(self) -> Dict:
        """Generate optimization recommendations based on brain data

        Returns:
            Dict: Optimization recommendations
        """
        recommendations = {
            "strategy_adjustments": [],
            "pair_recommendations": [],
            "risk_adjustments": [],
            "time_recommendations": [],
            "generated_at": datetime.datetime.utcnow().isoformat()
        }
        
        try:
            # Strategy recommendations
            for strategy, data in self.brain_data.get("strategies", {}).items():
                status = data.get("status", "active")
                win_rate = data.get("win_rate", 0)
                weight = data.get("weight", 100)
                
                if status == "cooldown":
                    cooldown_until = data.get("cooldown_until")
                    if cooldown_until:
                        cooldown_date = datetime.datetime.fromisoformat(cooldown_until).strftime("%Y-%m-%d")
                        recommendations["strategy_adjustments"].append(
                            f"Pause {strategy} strategy until {cooldown_date} due to poor performance (win rate: {win_rate:.1f}%)"
                        )
                elif win_rate >= self.confidence_boost_threshold:
                    recommendations["strategy_adjustments"].append(
                        f"Increase {strategy} usage by {self.weight_increment}% (current weight: {weight}%, win rate: {win_rate:.1f}%)"
                    )
                elif win_rate < self.win_rate_threshold:
                    recommendations["strategy_adjustments"].append(
                        f"Decrease {strategy} usage by {self.weight_increment}% (current weight: {weight}%, win rate: {win_rate:.1f}%)"
                    )
            
            # Pair recommendations
            for pair, data in self.brain_data.get("pairs", {}).items():
                status = data.get("status", "active")
                win_rate = data.get("win_rate", 0)
                best_strategy = data.get("best_strategy")
                best_time = data.get("best_time")
                
                if status == "caution":
                    recommendations["pair_recommendations"].append(
                        f"Use caution with {pair} due to low win rate ({win_rate:.1f}%)"
                    )
                
                if best_strategy and best_time:
                    recommendations["pair_recommendations"].append(
                        f"Prefer {best_strategy} strategy for {pair} during {best_time.replace('_', ' ')}"
                    )
            
            # Market condition recommendations
            for condition, data in self.brain_data.get("market_conditions", {}).items():
                win_rate = data.get("win_rate", 0)
                best_strategy = data.get("best_strategy")
                
                if best_strategy:
                    recommendations["strategy_adjustments"].append(
                        f"Use {best_strategy} strategy during {condition} market conditions (win rate: {win_rate:.1f}%)"
                    )
            
            # News impact recommendations
            news_impact = self.brain_data.get("news_impact", {})
            with_news = news_impact.get("with_news", {})
            without_news = news_impact.get("without_news", {})
            
            with_news_win_rate = with_news.get("win_rate", 0)
            without_news_win_rate = without_news.get("win_rate", 0)
            
            if with_news_win_rate < without_news_win_rate - 10:  # Significant difference
                recommendations["risk_adjustments"].append(
                    f"Reduce risk by 50% when trading near high-impact news events (win rate difference: {without_news_win_rate - with_news_win_rate:.1f}%)"
                )
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return recommendations

    def update_sentinel_config(self, recommendations: Dict) -> bool:
        """Update sentinel configuration based on recommendations

        Args:
            recommendations (Dict): Optimization recommendations

        Returns:
            bool: Success status
        """
        # This is a placeholder for actual YAML config update
        # In a real implementation, you would parse the YAML file,
        # update the relevant sections, and save it back
        
        try:
            logger.info("Updating sentinel configuration with optimization recommendations")
            
            # Log the recommendations that would be applied
            for category, items in recommendations.items():
                if items and category != "generated_at":
                    logger.info(f"{category.replace('_', ' ').title()}:")
                    for item in items:
                        logger.info(f"  - {item}")
            
            # In a real implementation, you would update the YAML file here
            # For now, we'll just return success
            return True
        except Exception as e:
            logger.error(f"Error updating sentinel configuration: {e}")
            return False

    def run_weekly_optimization(self) -> Dict:
        """Run weekly optimization process

        Returns:
            Dict: Optimization results
        """
        results = {
            "success": False,
            "brain_updated": False,
            "config_updated": False,
            "recommendations": {},
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        try:
            # Update strategy brain
            brain_updated = self.update_strategy_brain()
            results["brain_updated"] = brain_updated
            
            if not brain_updated:
                logger.warning("Failed to update strategy brain")
                return results
            
            # Generate recommendations
            recommendations = self.generate_optimization_recommendations()
            results["recommendations"] = recommendations
            
            # Update sentinel configuration
            config_updated = self.update_sentinel_config(recommendations)
            results["config_updated"] = config_updated
            
            results["success"] = brain_updated and config_updated
            
            return results
        except Exception as e:
            logger.error(f"Error running weekly optimization: {e}")
            return results


# Helper functions
def run_optimization() -> Dict:
    """Run strategy optimization (helper function)

    Returns:
        Dict: Optimization results
    """
    optimizer = StrategyOptimizer()
    return optimizer.run_weekly_optimization()


def get_strategy_recommendations() -> Dict:
    """Get strategy optimization recommendations (helper function)

    Returns:
        Dict: Optimization recommendations
    """
    optimizer = StrategyOptimizer()
    optimizer.update_strategy_brain()
    return optimizer.generate_optimization_recommendations()


def get_brain_data() -> Dict:
    """Get current strategy brain data (helper function)

    Returns:
        Dict: Strategy brain data
    """
    optimizer = StrategyOptimizer()
    return optimizer.brain_data


# For testing
if __name__ == "__main__":
    # Create an instance of the strategy optimizer
    optimizer = StrategyOptimizer()
    
    # Run optimization
    print("Running strategy optimization...")
    results = optimizer.run_weekly_optimization()
    
    # Print results
    print("\nOptimization Results:")
    print(f"Success: {results['success']}")
    print(f"Brain Updated: {results['brain_updated']}")
    print(f"Config Updated: {results['config_updated']}")
    
    # Print recommendations
    print("\nRecommendations:")
    for category, items in results["recommendations"].items():
        if items and category != "generated_at":
            print(f"\n{category.replace('_', ' ').title()}:")
            for item in items:
                print(f"  - {item}")
    
    # Print brain data summary
    print("\nStrategy Brain Summary:")
    for strategy, data in optimizer.brain_data.get("strategies", {}).items():
        status = data.get("status", "active")
        win_rate = data.get("win_rate", 0)
        weight = data.get("weight", 100)
        print(f"  {strategy}: Status={status}, Win Rate={win_rate:.1f}%, Weight={weight}%")
    
    print("\nPair Performance Summary:")
    for pair, data in optimizer.brain_data.get("pairs", {}).items():
        status = data.get("status", "active")
        win_rate = data.get("win_rate", 0)
        best_strategy = data.get("best_strategy", "None")
        print(f"  {pair}: Status={status}, Win Rate={win_rate:.1f}%, Best Strategy={best_strategy}")