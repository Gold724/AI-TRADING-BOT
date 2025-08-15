#!/usr/bin/env python
# Dynamic Risk Engine - Evolves risk parameters based on trade history

import json
import logging
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("dynamic_risk_engine")

# Constants
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
RISK_CONFIG_FILE = os.path.join("config", "risk_config.json")
RISK_HISTORY_FILE = os.path.join("data", "risk_history.json")

class DynamicRiskEngine:
    """Engine that dynamically adjusts risk parameters based on trading history"""
    
    def __init__(self, 
                 trade_history_file: str = TRADE_HISTORY_FILE,
                 risk_config_file: str = RISK_CONFIG_FILE,
                 risk_history_file: str = RISK_HISTORY_FILE):
        """Initialize the dynamic risk engine
        
        Args:
            trade_history_file (str): Path to the trade history file
            risk_config_file (str): Path to the risk configuration file
            risk_history_file (str): Path to the risk history file
        """
        self.trade_history_file = trade_history_file
        self.risk_config_file = risk_config_file
        self.risk_history_file = risk_history_file
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(trade_history_file), exist_ok=True)
        os.makedirs(os.path.dirname(risk_config_file), exist_ok=True)
        os.makedirs(os.path.dirname(risk_history_file), exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize risk history if file doesn't exist
        if not os.path.exists(risk_history_file):
            self.initialize_risk_history()
        
        logger.info("Dynamic Risk Engine initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load the risk configuration
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            if os.path.exists(self.risk_config_file):
                with open(self.risk_config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    "base_risk_percentage": 2.0,  # Base risk per trade as percentage of account
                    "max_risk_percentage": 5.0,  # Maximum risk per trade
                    "min_risk_percentage": 0.5,  # Minimum risk per trade
                    "max_daily_risk": 10.0,     # Maximum daily risk as percentage of account
                    "max_open_trades": 5,       # Maximum number of concurrent open trades
                    "drawdown_protection": {
                        "enabled": True,
                        "max_drawdown": 15.0,   # Maximum drawdown percentage before risk reduction
                        "recovery_factor": 0.5   # Factor to reduce risk during drawdown recovery
                    },
                    "volatility_adjustment": {
                        "enabled": True,
                        "factor": 0.8           # Factor to adjust risk based on volatility
                    },
                    "winning_streak": {
                        "enabled": True,
                        "threshold": 3,          # Number of consecutive wins to increase risk
                        "increase_factor": 1.2   # Factor to increase risk after winning streak
                    },
                    "losing_streak": {
                        "enabled": True,
                        "threshold": 2,          # Number of consecutive losses to decrease risk
                        "decrease_factor": 0.8   # Factor to decrease risk after losing streak
                    },
                    "time_based_adjustment": {
                        "enabled": True,
                        "high_risk_hours": [9, 10, 11, 14, 15],  # Hours with higher risk tolerance (market open/close)
                        "high_risk_factor": 1.1,                 # Factor to increase risk during high risk hours
                        "low_risk_hours": [12, 13],              # Hours with lower risk tolerance (lunch hours)
                        "low_risk_factor": 0.9                  # Factor to decrease risk during low risk hours
                    },
                    "adaptation_rate": 0.1      # Rate at which risk parameters adapt to new data
                }
                
                # Save default configuration
                with open(self.risk_config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def initialize_risk_history(self) -> None:
        """Initialize risk history"""
        try:
            default_history = {
                "risk_adjustments": [],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.risk_history_file, 'w') as f:
                json.dump(default_history, f, indent=4)
            
            logger.info("Initialized risk history")
        except Exception as e:
            logger.error(f"Error initializing risk history: {e}")
    
    def load_trade_history(self) -> List[Dict[str, Any]]:
        """Load trade history
        
        Returns:
            List[Dict[str, Any]]: List of historical trades
        """
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return []
    
    def load_risk_history(self) -> Dict[str, Any]:
        """Load risk history
        
        Returns:
            Dict[str, Any]: Risk history
        """
        try:
            if os.path.exists(self.risk_history_file):
                with open(self.risk_history_file, 'r') as f:
                    return json.load(f)
            return {"risk_adjustments": [], "last_updated": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Error loading risk history: {e}")
            return {"risk_adjustments": [], "last_updated": datetime.now().isoformat()}
    
    def calculate_dynamic_risk(self, strategy: str, symbol: str, 
                             account_balance: float) -> Dict[str, Any]:
        """Calculate dynamic risk parameters based on trading history
        
        Args:
            strategy (str): Trading strategy name
            symbol (str): Trading symbol
            account_balance (float): Current account balance
            
        Returns:
            Dict[str, Any]: Dynamic risk parameters
        """
        try:
            # Load trade history
            trade_history = self.load_trade_history()
            
            # Start with base risk
            risk_percentage = self.config["base_risk_percentage"]
            position_size = account_balance * (risk_percentage / 100)
            
            # Apply drawdown protection if enabled
            if self.config["drawdown_protection"]["enabled"]:
                drawdown = self.calculate_drawdown(trade_history)
                if drawdown > self.config["drawdown_protection"]["max_drawdown"]:
                    risk_percentage *= self.config["drawdown_protection"]["recovery_factor"]
                    logger.info(f"Reducing risk due to drawdown of {drawdown:.2f}%")
            
            # Apply volatility adjustment if enabled
            if self.config["volatility_adjustment"]["enabled"]:
                volatility = self.calculate_volatility(trade_history, symbol)
                volatility_factor = self.calculate_volatility_factor(volatility)
                risk_percentage *= volatility_factor
                logger.info(f"Adjusting risk by factor {volatility_factor:.2f} due to volatility")
            
            # Apply streak-based adjustments
            if self.config["winning_streak"]["enabled"] or self.config["losing_streak"]["enabled"]:
                streak_factor = self.calculate_streak_factor(trade_history, strategy, symbol)
                risk_percentage *= streak_factor
                logger.info(f"Adjusting risk by factor {streak_factor:.2f} due to streak")
            
            # Apply time-based adjustment if enabled
            if self.config["time_based_adjustment"]["enabled"]:
                time_factor = self.calculate_time_factor()
                risk_percentage *= time_factor
                logger.info(f"Adjusting risk by factor {time_factor:.2f} due to time of day")
            
            # Ensure risk is within bounds
            risk_percentage = max(self.config["min_risk_percentage"], 
                                min(self.config["max_risk_percentage"], risk_percentage))
            
            # Calculate position size based on risk percentage
            position_size = account_balance * (risk_percentage / 100)
            
            # Check daily risk limit
            daily_risk_used = self.calculate_daily_risk_used(trade_history, account_balance)
            daily_risk_remaining = self.config["max_daily_risk"] - daily_risk_used
            
            if daily_risk_remaining < risk_percentage:
                logger.warning(f"Daily risk limit reached. Adjusting risk from {risk_percentage:.2f}% to {daily_risk_remaining:.2f}%")
                risk_percentage = max(0, daily_risk_remaining)
                position_size = account_balance * (risk_percentage / 100)
            
            # Record risk adjustment
            self.record_risk_adjustment(strategy, symbol, risk_percentage, position_size)
            
            return {
                "risk_percentage": risk_percentage,
                "position_size": position_size,
                "max_open_trades": self.config["max_open_trades"],
                "daily_risk_used": daily_risk_used,
                "daily_risk_remaining": daily_risk_remaining
            }
        except Exception as e:
            logger.error(f"Error calculating dynamic risk: {e}")
            # Return default risk parameters
            return {
                "risk_percentage": self.config["base_risk_percentage"],
                "position_size": account_balance * (self.config["base_risk_percentage"] / 100),
                "max_open_trades": self.config["max_open_trades"],
                "daily_risk_used": 0,
                "daily_risk_remaining": self.config["max_daily_risk"]
            }
    
    def calculate_drawdown(self, trade_history: List[Dict[str, Any]]) -> float:
        """Calculate current drawdown from peak balance
        
        Args:
            trade_history (List[Dict[str, Any]]): List of historical trades
            
        Returns:
            float: Current drawdown percentage
        """
        if not trade_history:
            return 0.0
        
        # Extract balance history from trades
        balance_history = []
        for trade in trade_history:
            if "balance_after" in trade:
                balance_history.append(trade["balance_after"])
        
        if not balance_history:
            return 0.0
        
        # Calculate peak balance and current balance
        peak_balance = max(balance_history)
        current_balance = balance_history[-1]
        
        # Calculate drawdown percentage
        if peak_balance > 0:
            drawdown = (peak_balance - current_balance) / peak_balance * 100
            return drawdown
        
        return 0.0
    
    def calculate_volatility(self, trade_history: List[Dict[str, Any]], symbol: str) -> float:
        """Calculate recent market volatility based on trade history
        
        Args:
            trade_history (List[Dict[str, Any]]): List of historical trades
            symbol (str): Trading symbol
            
        Returns:
            float: Volatility measure
        """
        # Filter trades for this symbol
        symbol_trades = [trade for trade in trade_history if trade.get("symbol") == symbol]
        
        # Get recent trades (last 20 or all if less than 20)
        recent_trades = symbol_trades[-20:] if len(symbol_trades) > 20 else symbol_trades
        
        if len(recent_trades) < 2:
            return 1.0  # Default volatility if not enough data
        
        # Extract profit percentages
        profit_percentages = []
        for trade in recent_trades:
            if "profit_percentage" in trade:
                profit_percentages.append(trade["profit_percentage"])
            elif "profit" in trade and "entry_price" in trade and trade["entry_price"] > 0:
                profit_percentage = (trade["profit"] / trade["entry_price"]) * 100
                profit_percentages.append(profit_percentage)
        
        if len(profit_percentages) < 2:
            return 1.0  # Default volatility if not enough data
        
        # Calculate standard deviation of profit percentages as volatility measure
        volatility = np.std(profit_percentages)
        return volatility
    
    def calculate_volatility_factor(self, volatility: float) -> float:
        """Calculate risk adjustment factor based on volatility
        
        Args:
            volatility (float): Volatility measure
            
        Returns:
            float: Risk adjustment factor
        """
        # Higher volatility should reduce risk
        base_volatility = 2.0  # Baseline volatility
        
        if volatility <= base_volatility:
            return 1.0  # No adjustment for normal volatility
        
        # Calculate adjustment factor (inverse relationship with volatility)
        factor = base_volatility / volatility
        factor = max(0.5, min(1.0, factor))  # Limit factor between 0.5 and 1.0
        
        return factor * self.config["volatility_adjustment"]["factor"]
    
    def calculate_streak_factor(self, trade_history: List[Dict[str, Any]], 
                               strategy: str, symbol: str) -> float:
        """Calculate risk adjustment factor based on winning/losing streaks
        
        Args:
            trade_history (List[Dict[str, Any]]): List of historical trades
            strategy (str): Trading strategy name
            symbol (str): Trading symbol
            
        Returns:
            float: Risk adjustment factor
        """
        # Filter trades for this strategy and symbol
        filtered_trades = [trade for trade in trade_history 
                          if trade.get("strategy") == strategy 
                          and trade.get("symbol") == symbol]
        
        if not filtered_trades:
            return 1.0  # No adjustment if no trades
        
        # Get recent trades (last 10 or all if less than 10)
        recent_trades = filtered_trades[-10:] if len(filtered_trades) > 10 else filtered_trades
        
        # Count consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        
        for trade in reversed(recent_trades):
            if trade.get("win", False):
                consecutive_wins += 1
                consecutive_losses = 0
            else:
                consecutive_losses += 1
                consecutive_wins = 0
            
            # Stop counting once streak is broken
            if consecutive_wins > 0 and consecutive_losses > 0:
                break
        
        # Apply winning streak adjustment
        if self.config["winning_streak"]["enabled"] and consecutive_wins >= self.config["winning_streak"]["threshold"]:
            return self.config["winning_streak"]["increase_factor"]
        
        # Apply losing streak adjustment
        if self.config["losing_streak"]["enabled"] and consecutive_losses >= self.config["losing_streak"]["threshold"]:
            return self.config["losing_streak"]["decrease_factor"]
        
        return 1.0  # No adjustment if no streak
    
    def calculate_time_factor(self) -> float:
        """Calculate risk adjustment factor based on time of day
        
        Returns:
            float: Risk adjustment factor
        """
        current_hour = datetime.now().hour
        
        # Check if current hour is in high risk hours
        if current_hour in self.config["time_based_adjustment"]["high_risk_hours"]:
            return self.config["time_based_adjustment"]["high_risk_factor"]
        
        # Check if current hour is in low risk hours
        if current_hour in self.config["time_based_adjustment"]["low_risk_hours"]:
            return self.config["time_based_adjustment"]["low_risk_factor"]
        
        return 1.0  # No adjustment for normal hours
    
    def calculate_daily_risk_used(self, trade_history: List[Dict[str, Any]], 
                                 account_balance: float) -> float:
        """Calculate daily risk used as percentage of account
        
        Args:
            trade_history (List[Dict[str, Any]]): List of historical trades
            account_balance (float): Current account balance
            
        Returns:
            float: Daily risk used percentage
        """
        # Get today's date
        today = datetime.now().date()
        
        # Filter trades for today
        today_trades = []
        for trade in trade_history:
            if "timestamp" in trade:
                try:
                    trade_date = datetime.fromisoformat(trade["timestamp"]).date()
                    if trade_date == today:
                        today_trades.append(trade)
                except (ValueError, TypeError):
                    pass
        
        # Calculate total risk used today
        total_risk = 0.0
        for trade in today_trades:
            if "risk_percentage" in trade:
                total_risk += trade["risk_percentage"]
            elif "risk_amount" in trade and account_balance > 0:
                risk_percentage = (trade["risk_amount"] / account_balance) * 100
                total_risk += risk_percentage
        
        return total_risk
    
    def record_risk_adjustment(self, strategy: str, symbol: str, 
                             risk_percentage: float, position_size: float) -> None:
        """Record risk adjustment in history
        
        Args:
            strategy (str): Trading strategy name
            symbol (str): Trading symbol
            risk_percentage (float): Risk percentage
            position_size (float): Position size
        """
        try:
            # Load risk history
            risk_history = self.load_risk_history()
            
            # Add new adjustment
            risk_history["risk_adjustments"].append({
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy,
                "symbol": symbol,
                "risk_percentage": risk_percentage,
                "position_size": position_size
            })
            
            # Keep only the last 1000 adjustments
            if len(risk_history["risk_adjustments"]) > 1000:
                risk_history["risk_adjustments"] = risk_history["risk_adjustments"][-1000:]
            
            # Update last updated timestamp
            risk_history["last_updated"] = datetime.now().isoformat()
            
            # Save updated history
            with open(self.risk_history_file, 'w') as f:
                json.dump(risk_history, f, indent=4)
            
            logger.info(f"Recorded risk adjustment for {strategy} on {symbol}: {risk_percentage:.2f}%")
        except Exception as e:
            logger.error(f"Error recording risk adjustment: {e}")
    
    def update_risk_config(self, performance_metrics: Dict[str, Any]) -> None:
        """Update risk configuration based on performance metrics
        
        Args:
            performance_metrics (Dict[str, Any]): Performance metrics
        """
        try:
            # Load current config
            config = self.load_config()
            
            # Extract performance metrics
            win_rate = performance_metrics.get("win_rate", 50)
            profit_factor = performance_metrics.get("profit_factor", 1.0)
            drawdown = performance_metrics.get("drawdown", 0.0)
            volatility = performance_metrics.get("volatility", 1.0)
            
            # Adjust base risk percentage based on performance
            if win_rate > 60 and profit_factor > 1.5 and drawdown < 10:
                # Good performance, gradually increase base risk
                config["base_risk_percentage"] += config["adaptation_rate"]
                logger.info(f"Increasing base risk to {config['base_risk_percentage']:.2f}% due to good performance")
            elif win_rate < 40 or profit_factor < 1.0 or drawdown > 15:
                # Poor performance, gradually decrease base risk
                config["base_risk_percentage"] -= config["adaptation_rate"]
                logger.info(f"Decreasing base risk to {config['base_risk_percentage']:.2f}% due to poor performance")
            
            # Ensure base risk is within bounds
            config["base_risk_percentage"] = max(config["min_risk_percentage"], 
                                             min(config["max_risk_percentage"], config["base_risk_percentage"]))
            
            # Adjust drawdown protection based on actual drawdown
            if drawdown > config["drawdown_protection"]["max_drawdown"]:
                # Increase drawdown protection
                config["drawdown_protection"]["recovery_factor"] -= 0.05
                config["drawdown_protection"]["recovery_factor"] = max(0.3, config["drawdown_protection"]["recovery_factor"])
                logger.info(f"Increasing drawdown protection, recovery factor: {config['drawdown_protection']['recovery_factor']:.2f}")
            
            # Adjust volatility factor based on actual volatility
            if volatility > 3.0:
                # Increase volatility protection
                config["volatility_adjustment"]["factor"] -= 0.05
                config["volatility_adjustment"]["factor"] = max(0.5, config["volatility_adjustment"]["factor"])
                logger.info(f"Increasing volatility protection, factor: {config['volatility_adjustment']['factor']:.2f}")
            
            # Save updated config
            with open(self.risk_config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Update instance config
            self.config = config
            
            logger.info("Updated risk configuration based on performance metrics")
        except Exception as e:
            logger.error(f"Error updating risk configuration: {e}")
    
    def generate_risk_report(self) -> Dict[str, Any]:
        """Generate a risk management report
        
        Returns:
            Dict[str, Any]: Risk report data
        """
        try:
            # Load trade history and risk history
            trade_history = self.load_trade_history()
            risk_history = self.load_risk_history()
            
            # Calculate overall risk metrics
            avg_risk_percentage = 0.0
            risk_adjustments = risk_history.get("risk_adjustments", [])
            
            if risk_adjustments:
                # Get recent adjustments (last 100 or all if less than 100)
                recent_adjustments = risk_adjustments[-100:] if len(risk_adjustments) > 100 else risk_adjustments
                avg_risk_percentage = sum(adj.get("risk_percentage", 0) for adj in recent_adjustments) / len(recent_adjustments)
            
            # Calculate risk by strategy
            strategy_risk = {}
            for adjustment in risk_adjustments:
                strategy = adjustment.get("strategy")
                if strategy:
                    if strategy not in strategy_risk:
                        strategy_risk[strategy] = {
                            "adjustments": [],
                            "avg_risk": 0.0
                        }
                    
                    strategy_risk[strategy]["adjustments"].append(adjustment)
            
            # Calculate average risk by strategy
            for strategy, data in strategy_risk.items():
                adjustments = data["adjustments"]
                if adjustments:
                    # Get recent adjustments (last 20 or all if less than 20)
                    recent_adjustments = adjustments[-20:] if len(adjustments) > 20 else adjustments
                    data["avg_risk"] = sum(adj.get("risk_percentage", 0) for adj in recent_adjustments) / len(recent_adjustments)
            
            # Calculate drawdown
            drawdown = self.calculate_drawdown(trade_history)
            
            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "overall": {
                    "avg_risk_percentage": avg_risk_percentage,
                    "current_drawdown": drawdown,
                    "base_risk_percentage": self.config["base_risk_percentage"],
                    "max_daily_risk": self.config["max_daily_risk"]
                },
                "strategies": {},
                "risk_shifts": self.identify_risk_shifts(risk_adjustments),
                "recommendations": self.generate_risk_recommendations(drawdown, strategy_risk)
            }
            
            # Add strategy-specific data
            for strategy, data in strategy_risk.items():
                report["strategies"][strategy] = {
                    "avg_risk_percentage": data["avg_risk"],
                    "risk_trend": self.calculate_risk_trend(data["adjustments"])
                }
            
            return report
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def identify_risk_shifts(self, risk_adjustments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify significant shifts in risk parameters
        
        Args:
            risk_adjustments (List[Dict[str, Any]]): List of risk adjustments
            
        Returns:
            List[Dict[str, Any]]: List of significant risk shifts
        """
        shifts = []
        
        if len(risk_adjustments) < 10:
            return shifts
        
        # Group adjustments by strategy and symbol
        grouped_adjustments = {}
        for adjustment in risk_adjustments:
            key = f"{adjustment.get('strategy')}_{adjustment.get('symbol')}"
            if key not in grouped_adjustments:
                grouped_adjustments[key] = []
            grouped_adjustments[key].append(adjustment)
        
        # Identify shifts for each strategy-symbol combination
        for key, adjustments in grouped_adjustments.items():
            if len(adjustments) < 10:
                continue
            
            # Calculate moving averages
            window_size = 5
            for i in range(window_size, len(adjustments)):
                prev_window = adjustments[i-window_size:i]
                current = adjustments[i]
                
                prev_avg_risk = sum(adj.get("risk_percentage", 0) for adj in prev_window) / window_size
                current_risk = current.get("risk_percentage", 0)
                
                # Check for significant shift (more than 20% change)
                if abs(current_risk - prev_avg_risk) / prev_avg_risk > 0.2:
                    strategy = current.get("strategy", "")
                    symbol = current.get("symbol", "")
                    timestamp = current.get("timestamp", "")
                    
                    shifts.append({
                        "timestamp": timestamp,
                        "strategy": strategy,
                        "symbol": symbol,
                        "previous_risk": prev_avg_risk,
                        "new_risk": current_risk,
                        "change_percentage": ((current_risk - prev_avg_risk) / prev_avg_risk) * 100
                    })
        
        # Sort shifts by timestamp (most recent first)
        shifts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Return the 5 most recent shifts
        return shifts[:5]
    
    def calculate_risk_trend(self, adjustments: List[Dict[str, Any]]) -> str:
        """Calculate the trend in risk adjustments
        
        Args:
            adjustments (List[Dict[str, Any]]): List of risk adjustments
            
        Returns:
            str: Trend description (increasing, decreasing, stable)
        """
        if len(adjustments) < 5:
            return "insufficient data"
        
        # Get the 5 most recent adjustments
        recent_adjustments = sorted(adjustments, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
        
        # Extract risk percentages
        risk_percentages = [adj.get("risk_percentage", 0) for adj in recent_adjustments]
        
        # Calculate trend
        if len(risk_percentages) < 2:
            return "stable"
        
        # Simple linear regression slope
        x = list(range(len(risk_percentages)))
        y = risk_percentages
        n = len(x)
        
        if n < 2:
            return "stable"
        
        slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2)
        
        # Determine trend based on slope
        if abs(slope) < 0.05:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def generate_risk_recommendations(self, drawdown: float, 
                                     strategy_risk: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate risk management recommendations
        
        Args:
            drawdown (float): Current drawdown percentage
            strategy_risk (Dict[str, Dict[str, Any]]): Risk data by strategy
            
        Returns:
            List[str]: Risk recommendations
        """
        recommendations = []
        
        # Drawdown recommendations
        if drawdown > 15:
            recommendations.append(f"High drawdown detected ({drawdown:.2f}%). Consider reducing overall risk exposure.")
        elif drawdown > 10:
            recommendations.append(f"Moderate drawdown detected ({drawdown:.2f}%). Monitor closely and prepare risk reduction plan.")
        
        # Strategy-specific recommendations
        high_risk_strategies = []
        for strategy, data in strategy_risk.items():
            avg_risk = data.get("avg_risk", 0)
            if avg_risk > self.config["base_risk_percentage"] * 1.5:
                high_risk_strategies.append((strategy, avg_risk))
        
        if high_risk_strategies:
            for strategy, risk in high_risk_strategies:
                recommendations.append(f"Strategy '{strategy}' has high risk exposure ({risk:.2f}%). Consider rebalancing.")
        
        # General recommendations
        recommendations.append("Regularly review and update stop-loss levels based on current volatility.")
        recommendations.append("Consider correlation between open positions to avoid overexposure to single market factors.")
        
        return recommendations


# For testing
if __name__ == "__main__":
    # Create risk engine
    risk_engine = DynamicRiskEngine()
    
    # Test dynamic risk calculation
    risk_params = risk_engine.calculate_dynamic_risk(
        strategy="moving_average_crossover",
        symbol="EURUSD",
        account_balance=10000.0
    )
    
    print("\nDynamic Risk Parameters:")
    print(f"Risk Percentage: {risk_params['risk_percentage']:.2f}%")
    print(f"Position Size: ${risk_params['position_size']:.2f}")
    print(f"Max Open Trades: {risk_params['max_open_trades']}")
    print(f"Daily Risk Used: {risk_params['daily_risk_used']:.2f}%")
    print(f"Daily Risk Remaining: {risk_params['daily_risk_remaining']:.2f}%")
    
    # Generate risk report
    report = risk_engine.generate_risk_report()
    
    print("\nRisk Report:")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Average Risk: {report['overall']['avg_risk_percentage']:.2f}%")
    print(f"Current Drawdown: {report['overall']['current_drawdown']:.2f}%")
    
    print("Risk Recommendations:")
    for rec in report['recommendations']:
        print(f"- {rec}")