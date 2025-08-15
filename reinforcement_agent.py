# reinforcement_agent.py

import json
import logging
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('reinforcement_agent')

# Ensure log directories exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Constants
RL_DECISIONS_FILE = os.path.join(LOGS_DIR, "rl_agent_decisions.json")
REGIME_LABELS_FILE = os.path.join(DATA_DIR, "regime_labels.json")
MARKET_REGIME_LOG = os.path.join(LOGS_DIR, "market_regime.log")

# Market regime types
class MarketRegime:
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"

class ReinforcementAgent:
    def __init__(self, config_file=None):
        self.config_file = config_file or os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                     "config", "reinforcement_config.json")
        
        # Default configuration
        self.config = {
            "regime_awareness": True,
            "reinforcement_learning": True,
            "reward_threshold": 1.2,  # Profit factor threshold for reward
            "penalty_threshold": 0.8,  # Profit factor threshold for penalty
            "ema_short": 50,
            "ema_long": 200,
            "atr_period": 14,
            "atr_threshold": 0.0015,  # ATR threshold for regime detection
            "regime_reevaluation_hours": 2,
            "min_trades_for_signal": 20
        }
        
        # Load configuration if exists
        self.load_config()
        
        # Initialize Q-learning parameters
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.2
        
        # Current state tracking
        self.current_regime = MarketRegime.UNKNOWN
        self.last_regime_change = datetime.now()
        self.win_streak = 0
        self.loss_streak = 0
        self.volatility_index = 0.0
        
        # Strategy performance tracking
        self.strategy_performance = {}
        self.strategy_trades_count = {}
        
        # Load existing data if available
        self.load_regime_labels()
        self.load_rl_decisions()
        
        logger.info("Reinforcement Agent initialized")
    
    def load_config(self) -> None:
        """Load agent configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
            else:
                # Create default config file
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=4)
                logger.info(f"Created default configuration at {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def load_regime_labels(self) -> None:
        """Load market regime labels from file"""
        try:
            if os.path.exists(REGIME_LABELS_FILE):
                with open(REGIME_LABELS_FILE, 'r') as f:
                    regime_data = json.load(f)
                    # Process historical regime data if needed
                    if regime_data and isinstance(regime_data, list) and len(regime_data) > 0:
                        latest = regime_data[-1]
                        if 'regime' in latest:
                            self.current_regime = latest['regime']
                            logger.info(f"Loaded current regime: {self.current_regime}")
        except Exception as e:
            logger.error(f"Error loading regime labels: {e}")
    
    def load_rl_decisions(self) -> None:
        """Load reinforcement learning decisions from file"""
        try:
            if os.path.exists(RL_DECISIONS_FILE):
                with open(RL_DECISIONS_FILE, 'r') as f:
                    decisions = json.load(f)
                    # Process historical decisions if needed
                    if decisions and isinstance(decisions, list) and len(decisions) > 0:
                        # Initialize Q-table from past decisions
                        for decision in decisions:
                            if all(k in decision for k in ['state', 'action', 'reward']):
                                state = decision['state']
                                action = decision['action']
                                reward = decision['reward']
                                
                                if state not in self.q_table:
                                    self.q_table[state] = {}
                                
                                if action not in self.q_table[state]:
                                    self.q_table[state][action] = 0
                                
                                # Update Q-value based on historical data
                                self.q_table[state][action] += self.learning_rate * reward
        except Exception as e:
            logger.error(f"Error loading RL decisions: {e}")
    
    def detect_market_regime(self, ema_short: float, ema_long: float, atr: float, 
                            atr_change: float) -> str:
        """Detect market regime based on technical indicators
        
        Args:
            ema_short: Short-term EMA value (e.g., 50-period)
            ema_long: Long-term EMA value (e.g., 200-period)
            atr: Average True Range value
            atr_change: Percentage change in ATR
            
        Returns:
            str: Market regime (bullish, bearish, sideways)
        """
        # Bullish regime: Short EMA above Long EMA + rising ATR
        if ema_short > ema_long and atr_change > 0:
            return MarketRegime.BULLISH
        
        # Bearish regime: Short EMA below Long EMA + rising ATR
        elif ema_short < ema_long and atr_change > 0:
            return MarketRegime.BEARISH
        
        # Sideways regime: ATR below threshold, EMAs close
        elif atr < self.config["atr_threshold"] or abs(ema_short - ema_long) / ema_long < 0.01:
            return MarketRegime.SIDEWAYS
        
        # Default to current regime if no clear signal
        else:
            return self.current_regime
    
    def update_market_regime(self, ema_short: float, ema_long: float, atr: float, 
                            atr_change: float) -> bool:
        """Update the current market regime and log changes
        
        Args:
            ema_short: Short-term EMA value
            ema_long: Long-term EMA value
            atr: Average True Range value
            atr_change: Percentage change in ATR
            
        Returns:
            bool: True if regime changed, False otherwise
        """
        # Check if it's time to reevaluate the regime
        now = datetime.now()
        hours_since_last_change = (now - self.last_regime_change).total_seconds() / 3600
        
        if hours_since_last_change < self.config["regime_reevaluation_hours"] and self.current_regime != MarketRegime.UNKNOWN:
            return False
        
        # Detect new regime
        new_regime = self.detect_market_regime(ema_short, ema_long, atr, atr_change)
        
        # If regime changed, log it and update state
        if new_regime != self.current_regime:
            self.last_regime_change = now
            old_regime = self.current_regime
            self.current_regime = new_regime
            
            # Log regime change
            logger.info(f"Market regime changed from {old_regime} to {new_regime}")
            with open(MARKET_REGIME_LOG, 'a') as f:
                f.write(f"{now.isoformat()} - Regime changed from {old_regime} to {new_regime}\n")
            
            # Save to regime labels file
            self.save_regime_label(new_regime)
            
            # Send alert (placeholder for integration with notification system)
            self.send_regime_change_alert(old_regime, new_regime)
            
            return True
        
        return False
    
    def save_regime_label(self, regime: str) -> None:
        """Save current regime label to file
        
        Args:
            regime: Current market regime
        """
        try:
            # Load existing labels if available
            labels = []
            if os.path.exists(REGIME_LABELS_FILE):
                with open(REGIME_LABELS_FILE, 'r') as f:
                    labels = json.load(f)
            
            # Add new label
            labels.append({
                "timestamp": datetime.now().isoformat(),
                "regime": regime,
                "indicators": {
                    "ema_short": self.config["ema_short"],
                    "ema_long": self.config["ema_long"],
                    "atr_period": self.config["atr_period"]
                }
            })
            
            # Save updated labels
            with open(REGIME_LABELS_FILE, 'w') as f:
                json.dump(labels, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving regime label: {e}")
    
    def send_regime_change_alert(self, old_regime: str, new_regime: str) -> None:
        """Send alert when regime changes (placeholder for notification integration)
        
        Args:
            old_regime: Previous market regime
            new_regime: New market regime
        """
        # Placeholder for integration with Slack or other notification systems
        logger.info(f"ALERT: Market regime changed from {old_regime} to {new_regime}")
        # TODO: Implement actual notification logic
    
    def get_state_key(self) -> str:
        """Generate a key representing the current state for Q-learning
        
        Returns:
            str: State key for Q-table lookup
        """
        # Combine regime, win/loss streak, and volatility into a state key
        win_streak_bin = min(5, self.win_streak)  # Cap at 5 for simplicity
        loss_streak_bin = min(5, self.loss_streak)  # Cap at 5 for simplicity
        
        # Discretize volatility into 3 levels (low, medium, high)
        if self.volatility_index < 0.1:
            vol_level = "low"
        elif self.volatility_index < 0.2:
            vol_level = "medium"
        else:
            vol_level = "high"
        
        return f"{self.current_regime}_{win_streak_bin}_{loss_streak_bin}_{vol_level}"
    
    def get_actions_for_regime(self) -> List[str]:
        """Get available actions based on current market regime
        
        Returns:
            List[str]: List of available actions
        """
        # Common actions for all regimes
        actions = ["increase", "decrease", "pause"]
        
        # Add regime-specific actions
        if self.current_regime == MarketRegime.BULLISH:
            actions.extend(["use_breakout", "use_momentum"])
        elif self.current_regime == MarketRegime.BEARISH:
            actions.extend(["use_pullback", "use_mean_reversion"])
        elif self.current_regime == MarketRegime.SIDEWAYS:
            actions.extend(["use_scalping", "use_high_rrr"])
        
        return actions
    
    def choose_action(self, strategy_name: str) -> str:
        """Choose an action for a strategy using Q-learning with exploration
        
        Args:
            strategy_name: Name of the strategy to choose action for
            
        Returns:
            str: Selected action
        """
        state_key = self.get_state_key()
        available_actions = self.get_actions_for_regime()
        
        # Initialize state in Q-table if not exists
        if state_key not in self.q_table:
            self.q_table[state_key] = {action: 0.0 for action in available_actions}
        
        # Exploration: random action
        if np.random.random() < self.exploration_rate:
            return np.random.choice(available_actions)
        
        # Exploitation: best known action
        q_values = self.q_table[state_key]
        max_q = max(q_values.values())
        best_actions = [action for action, q_value in q_values.items() if q_value == max_q]
        
        return np.random.choice(best_actions)  # Random choice among best actions
    
    def update_q_value(self, state: str, action: str, reward: float, next_state: str) -> None:
        """Update Q-value using Q-learning formula
        
        Args:
            state: Current state key
            action: Action taken
            reward: Reward received
            next_state: Next state key
        """
        # Initialize states if not in Q-table
        if state not in self.q_table:
            available_actions = self.get_actions_for_regime()
            self.q_table[state] = {action: 0.0 for action in available_actions}
        
        if next_state not in self.q_table:
            available_actions = self.get_actions_for_regime()
            self.q_table[next_state] = {action: 0.0 for action in available_actions}
        
        # Get max Q-value for next state
        max_next_q = max(self.q_table[next_state].values())
        
        # Update Q-value using Q-learning formula
        current_q = self.q_table[state][action]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action] = new_q
    
    def record_trade_result(self, strategy_name: str, profit: float, 
                           trade_time: datetime = None) -> None:
        """Record trade result and update strategy performance
        
        Args:
            strategy_name: Name of the strategy
            profit: Profit/loss from the trade
            trade_time: Time of the trade (default: current time)
        """
        if trade_time is None:
            trade_time = datetime.now()
        
        # Initialize strategy tracking if not exists
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = []
        
        if strategy_name not in self.strategy_trades_count:
            self.strategy_trades_count[strategy_name] = 0
        
        # Record trade result
        self.strategy_performance[strategy_name].append({
            "timestamp": trade_time.isoformat(),
            "profit": profit,
            "regime": self.current_regime
        })
        
        # Update trade count
        self.strategy_trades_count[strategy_name] += 1
        
        # Update win/loss streaks
        if profit > 0:
            self.win_streak += 1
            self.loss_streak = 0
        else:
            self.loss_streak += 1
            self.win_streak = 0
        
        # Check if we have enough trades to evaluate performance
        if self.strategy_trades_count[strategy_name] >= self.config["min_trades_for_signal"]:
            self.evaluate_strategy_performance(strategy_name)
    
    def evaluate_strategy_performance(self, strategy_name: str) -> None:
        """Evaluate strategy performance and apply reinforcement learning
        
        Args:
            strategy_name: Name of the strategy to evaluate
        """
        # Get recent trades for the strategy
        recent_trades = self.strategy_performance[strategy_name][-self.config["min_trades_for_signal"]:]  
        
        # Calculate profit factor
        total_profit = sum(trade["profit"] for trade in recent_trades if trade["profit"] > 0)
        total_loss = abs(sum(trade["profit"] for trade in recent_trades if trade["profit"] < 0))
        
        profit_factor = total_profit / total_loss if total_loss > 0 else total_profit
        
        # Determine reward/penalty
        reward = 0.0
        action = None
        
        if profit_factor >= self.config["reward_threshold"]:
            # Reward signal
            reward = 1.0
            action = "increase"
            logger.info(f"Strategy {strategy_name} rewarded with profit factor {profit_factor:.2f}")
        elif profit_factor <= self.config["penalty_threshold"]:
            # Penalty signal
            reward = -1.0
            action = "decrease"
            logger.info(f"Strategy {strategy_name} penalized with profit factor {profit_factor:.2f}")
        else:
            # Neutral signal
            reward = 0.0
            action = "maintain"
        
        # Apply reinforcement learning
        if action:
            current_state = self.get_state_key()
            
            # Record decision
            self.record_rl_decision(strategy_name, current_state, action, reward, profit_factor)
            
            # Update Q-values (simplified, using same state for next_state as we don't know future state yet)
            self.update_q_value(current_state, action, reward, current_state)
            
            # Reset trade count for this strategy
            self.strategy_trades_count[strategy_name] = 0
    
    def record_rl_decision(self, strategy_name: str, state: str, action: str, 
                          reward: float, profit_factor: float) -> None:
        """Record reinforcement learning decision to file
        
        Args:
            strategy_name: Name of the strategy
            state: Current state key
            action: Action taken
            reward: Reward value
            profit_factor: Calculated profit factor
        """
        try:
            # Load existing decisions if available
            decisions = []
            if os.path.exists(RL_DECISIONS_FILE):
                with open(RL_DECISIONS_FILE, 'r') as f:
                    decisions = json.load(f)
            
            # Add new decision
            decisions.append({
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy_name,
                "state": state,
                "action": action,
                "reward": reward,
                "profit_factor": profit_factor,
                "regime": self.current_regime,
                "win_streak": self.win_streak,
                "loss_streak": self.loss_streak,
                "volatility_index": self.volatility_index
            })
            
            # Save updated decisions
            with open(RL_DECISIONS_FILE, 'w') as f:
                json.dump(decisions, f, indent=4)
        except Exception as e:
            logger.error(f"Error recording RL decision: {e}")
    
    def get_strategy_recommendations(self) -> Dict[str, Dict]:
        """Get strategy recommendations based on current market regime
        
        Returns:
            Dict: Strategy recommendations with weights and actions
        """
        recommendations = {}
        
        # Default strategy mappings based on regime
        if self.current_regime == MarketRegime.BULLISH:
            recommendations = {
                "breakout": {"weight": 0.4, "action": "increase"},
                "momentum": {"weight": 0.4, "action": "increase"},
                "mean_reversion": {"weight": 0.1, "action": "decrease"},
                "scalping": {"weight": 0.1, "action": "maintain"}
            }
        elif self.current_regime == MarketRegime.BEARISH:
            recommendations = {
                "pullback": {"weight": 0.4, "action": "increase"},
                "mean_reversion": {"weight": 0.4, "action": "increase"},
                "breakout": {"weight": 0.1, "action": "decrease"},
                "momentum": {"weight": 0.1, "action": "decrease"}
            }
        elif self.current_regime == MarketRegime.SIDEWAYS:
            recommendations = {
                "scalping": {"weight": 0.4, "action": "increase"},
                "high_rrr": {"weight": 0.4, "action": "increase"},
                "breakout": {"weight": 0.1, "action": "decrease"},
                "momentum": {"weight": 0.1, "action": "decrease"}
            }
        else:  # UNKNOWN regime
            recommendations = {
                "breakout": {"weight": 0.25, "action": "maintain"},
                "momentum": {"weight": 0.25, "action": "maintain"},
                "mean_reversion": {"weight": 0.25, "action": "maintain"},
                "scalping": {"weight": 0.25, "action": "maintain"}
            }
        
        # Apply RL-based adjustments if available
        if self.config["reinforcement_learning"]:
            state_key = self.get_state_key()
            if state_key in self.q_table:
                for strategy_name in recommendations.keys():
                    # Choose action based on Q-learning
                    rl_action = self.choose_action(strategy_name)
                    
                    # Apply RL-based action
                    if rl_action == "increase":
                        recommendations[strategy_name]["weight"] = min(0.6, recommendations[strategy_name]["weight"] * 1.5)
                        recommendations[strategy_name]["action"] = "increase"
                    elif rl_action == "decrease":
                        recommendations[strategy_name]["weight"] = max(0.05, recommendations[strategy_name]["weight"] * 0.5)
                        recommendations[strategy_name]["action"] = "decrease"
                    elif rl_action == "pause":
                        recommendations[strategy_name]["weight"] = 0.0
                        recommendations[strategy_name]["action"] = "pause"
                    
                    # Apply regime-specific strategy selection
                    if rl_action.startswith("use_"):
                        strategy_type = rl_action.replace("use_", "")
                        if strategy_type in recommendations:
                            recommendations[strategy_type]["weight"] = max(0.4, recommendations[strategy_type]["weight"])
                            recommendations[strategy_type]["action"] = "increase"
        
        # Normalize weights to sum to 1.0
        total_weight = sum(rec["weight"] for rec in recommendations.values())
        if total_weight > 0:
            for strategy in recommendations:
                recommendations[strategy]["weight"] /= total_weight
        
        return recommendations
    
    def update_volatility_index(self, atr: float, atr_avg: float) -> None:
        """Update volatility index based on ATR
        
        Args:
            atr: Current ATR value
            atr_avg: Average ATR over a longer period
        """
        # Calculate normalized volatility index (0.0 to 1.0)
        if atr_avg > 0:
            self.volatility_index = min(1.0, atr / atr_avg)
        else:
            self.volatility_index = 0.5  # Default if no historical data

# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = ReinforcementAgent()
    
    # Example: Update market regime
    ema_50 = 1.2345  # Example value
    ema_200 = 1.2300  # Example value
    atr = 0.0020  # Example value
    atr_change = 0.05  # Example value (5% increase)
    
    regime_changed = agent.update_market_regime(ema_50, ema_200, atr, atr_change)
    print(f"Current regime: {agent.current_regime}, Changed: {regime_changed}")
    
    # Example: Record trade results
    agent.record_trade_result("breakout", 50.0)  # Profitable trade
    agent.record_trade_result("breakout", -20.0)  # Losing trade
    
    # Example: Get strategy recommendations
    recommendations = agent.get_strategy_recommendations()
    print("Strategy recommendations:")
    for strategy, details in recommendations.items():
        print(f"  {strategy}: weight={details['weight']:.2f}, action={details['action']}")