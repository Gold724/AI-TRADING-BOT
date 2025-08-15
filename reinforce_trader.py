# reinforce_trader.py

import json
import logging
import os
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reinforce_trader")

# Constants
Q_TABLE_FILE = os.path.join("data", "q_table.json")
RL_CONFIG_FILE = os.path.join("config", "rl_config.json")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)


class ReinforceTrader:
    """Lightweight Reinforcement Learner for Trading Decisions
    
    This class implements a Q-learning based reinforcement learning system
    that learns optimal trading actions based on state (strategy, pair, time, etc.)
    and rewards (profit per trade).
    """

    def __init__(self, q_table_file: str = Q_TABLE_FILE, rl_config_file: str = RL_CONFIG_FILE):
        """Initialize the reinforcement trader

        Args:
            q_table_file (str): Path to the Q-table file
            rl_config_file (str): Path to the RL configuration file
        """
        self.q_table_file = q_table_file
        self.rl_config_file = rl_config_file
        self.config = self.load_config()
        self.q_table = self.load_q_table()
        
        # Define state space components
        self.strategies = self.config["strategies"]
        self.pairs = self.config["pairs"]
        self.time_segments = self.config["time_segments"]
        self.confidence_levels = self.config["confidence_levels"]
        self.news_levels = self.config["news_levels"]
        
        # Define action space
        self.actions = self.config["actions"]
        
        # Learning parameters
        self.alpha = self.config["learning_rate"]  # Learning rate
        self.gamma = self.config["discount_factor"]  # Discount factor
        self.epsilon = self.config["exploration_rate"]  # Exploration rate
        self.min_epsilon = self.config["min_exploration_rate"]  # Minimum exploration rate
        self.epsilon_decay = self.config["exploration_decay"]  # Exploration decay rate

    def load_config(self) -> Dict:
        """Load RL configuration from file

        Returns:
            Dict: RL configuration
        """
        default_config = {
            "learning_rate": 0.1,
            "discount_factor": 0.9,
            "exploration_rate": 0.3,
            "min_exploration_rate": 0.01,
            "exploration_decay": 0.995,
            "strategies": ["FVG", "OTE", "Cypher", "SMC", "ICT"],
            "pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP"],
            "time_segments": ["asian", "london", "new_york", "overlap"],
            "confidence_levels": ["low", "medium", "high", "very_high"],
            "news_levels": ["none", "low", "medium", "high"],
            "actions": ["trade", "skip", "reduce_risk", "switch_strategy"],
            "reward_scaling": {
                "win": 1.0,
                "loss": -1.0,
                "breakeven": 0.0
            },
            "profit_scaling_factor": 0.01  # Scale profit/loss to reward
        }

        try:
            if os.path.exists(self.rl_config_file):
                with open(self.rl_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.rl_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading RL config: {e}")
            return default_config

    def save_config(self) -> bool:
        """Save RL configuration to file

        Returns:
            bool: Success status
        """
        try:
            with open(self.rl_config_file, "w") as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving RL config: {e}")
            return False

    def load_q_table(self) -> Dict:
        """Load Q-table from file

        Returns:
            Dict: Q-table
        """
        try:
            if os.path.exists(self.q_table_file):
                with open(self.q_table_file, "r") as f:
                    return json.load(f)
            else:
                # Create empty Q-table if file doesn't exist
                q_table = {}
                with open(self.q_table_file, "w") as f:
                    json.dump(q_table, f, indent=4)
                return q_table
        except Exception as e:
            logger.error(f"Error loading Q-table: {e}")
            return {}

    def save_q_table(self) -> bool:
        """Save Q-table to file

        Returns:
            bool: Success status
        """
        try:
            with open(self.q_table_file, "w") as f:
                json.dump(self.q_table, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving Q-table: {e}")
            return False

    def get_state_key(self, state: Dict) -> str:
        """Convert state dictionary to a string key for Q-table

        Args:
            state (Dict): State dictionary with strategy, pair, time, confidence, news_level

        Returns:
            str: State key string
        """
        # Validate state components
        strategy = state.get("strategy", "unknown")
        pair = state.get("pair", "unknown")
        time_segment = state.get("time_segment", "unknown")
        confidence = state.get("confidence", "unknown")
        news_level = state.get("news_level", "unknown")
        
        # Create state key
        return f"{strategy}|{pair}|{time_segment}|{confidence}|{news_level}"

    def get_time_segment(self, timestamp: Optional[datetime] = None) -> str:
        """Get the current trading session time segment

        Args:
            timestamp (Optional[datetime], optional): Timestamp to check. Defaults to None (current time).

        Returns:
            str: Time segment (asian, london, new_york, overlap)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Convert to UTC hour
        hour = timestamp.hour
        
        # Define trading sessions in UTC
        if 0 <= hour < 8:  # Asian session: 00:00-08:00 UTC
            return "asian"
        elif 8 <= hour < 12:  # London session (pre-overlap): 08:00-12:00 UTC
            return "london"
        elif 12 <= hour < 16:  # Overlap session: 12:00-16:00 UTC
            return "overlap"
        else:  # New York session (post-overlap): 16:00-00:00 UTC
            return "new_york"

    def get_confidence_level(self, confidence_score: int) -> str:
        """Convert numerical confidence score to categorical level

        Args:
            confidence_score (int): Confidence score (0-100)

        Returns:
            str: Confidence level (low, medium, high, very_high)
        """
        if confidence_score < 40:
            return "low"
        elif confidence_score < 60:
            return "medium"
        elif confidence_score < 80:
            return "high"
        else:
            return "very_high"

    def get_news_level(self, news_impact: Optional[str] = None) -> str:
        """Convert news impact to categorical level

        Args:
            news_impact (Optional[str], optional): News impact. Defaults to None.

        Returns:
            str: News level (none, low, medium, high)
        """
        if news_impact is None:
            return "none"
        elif news_impact.lower() in ["low", "minor"]:
            return "low"
        elif news_impact.lower() in ["medium", "moderate"]:
            return "medium"
        elif news_impact.lower() in ["high", "major"]:
            return "high"
        else:
            return "none"

    def get_q_values(self, state_key: str) -> Dict[str, float]:
        """Get Q-values for a given state

        Args:
            state_key (str): State key string

        Returns:
            Dict[str, float]: Q-values for each action
        """
        # Initialize Q-values if state is not in Q-table
        if state_key not in self.q_table:
            self.q_table[state_key] = {action: 0.0 for action in self.actions}
        
        return self.q_table[state_key]

    def choose_action(self, state: Dict, explore: bool = True) -> str:
        """Choose an action based on current state

        Args:
            state (Dict): Current state
            explore (bool, optional): Whether to use exploration. Defaults to True.

        Returns:
            str: Chosen action
        """
        state_key = self.get_state_key(state)
        q_values = self.get_q_values(state_key)
        
        # Exploration: random action with probability epsilon
        if explore and random.random() < self.epsilon:
            return random.choice(self.actions)
        
        # Exploitation: choose best action
        # If multiple actions have the same max Q-value, choose randomly among them
        max_q = max(q_values.values())
        best_actions = [action for action, q_value in q_values.items() if q_value == max_q]
        
        return random.choice(best_actions)

    def update_q_table(self, state: Dict, action: str, reward: float, next_state: Dict) -> None:
        """Update Q-table using Q-learning algorithm

        Args:
            state (Dict): Current state
            action (str): Action taken
            reward (float): Reward received
            next_state (Dict): Next state
        """
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)
        
        # Get current Q-value
        q_values = self.get_q_values(state_key)
        current_q = q_values[action]
        
        # Get max Q-value for next state
        next_q_values = self.get_q_values(next_state_key)
        max_next_q = max(next_q_values.values())
        
        # Q-learning update formula: Q(s,a) = Q(s,a) + α * [r + γ * max(Q(s',a')) - Q(s,a)]
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        
        # Update Q-value
        self.q_table[state_key][action] = new_q
        
        # Save Q-table
        self.save_q_table()
        
        # Decay exploration rate
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def calculate_reward(self, result: str, profit_loss: float = 0.0) -> float:
        """Calculate reward based on trade result and profit/loss

        Args:
            result (str): Trade result ('win', 'loss', 'breakeven')
            profit_loss (float, optional): Profit or loss amount. Defaults to 0.0.

        Returns:
            float: Calculated reward
        """
        # Base reward from result
        base_reward = self.config["reward_scaling"].get(result.lower(), 0.0)
        
        # Add scaled profit/loss component
        profit_component = profit_loss * self.config["profit_scaling_factor"]
        
        return base_reward + profit_component

    def learn_from_trade(self, pre_trade_state: Dict, action: str, result: str, 
                         profit_loss: float, post_trade_state: Dict) -> float:
        """Learn from a completed trade

        Args:
            pre_trade_state (Dict): State before trade
            action (str): Action taken
            result (str): Trade result ('win', 'loss', 'breakeven')
            profit_loss (float): Profit or loss amount
            post_trade_state (Dict): State after trade

        Returns:
            float: Calculated reward
        """
        # Calculate reward
        reward = self.calculate_reward(result, profit_loss)
        
        # Update Q-table
        self.update_q_table(pre_trade_state, action, reward, post_trade_state)
        
        return reward

    def get_state_from_trade_data(self, trade_data: Dict) -> Dict:
        """Convert trade data to state dictionary

        Args:
            trade_data (Dict): Trade data

        Returns:
            Dict: State dictionary
        """
        # Extract data from trade record
        strategy = trade_data.get("strategy", "unknown")
        pair = trade_data.get("symbol", "unknown")
        
        # Get time segment from trade timestamp
        timestamp = datetime.fromisoformat(trade_data.get("date", datetime.utcnow().isoformat()))
        time_segment = self.get_time_segment(timestamp)
        
        # Get confidence level
        confidence_score = trade_data.get("confidence", 50)
        confidence = self.get_confidence_level(confidence_score)
        
        # Get news level
        news_nearby = trade_data.get("news_nearby", False)
        news_impact = trade_data.get("news_impact", None)
        news_level = self.get_news_level(news_impact) if news_nearby else "none"
        
        return {
            "strategy": strategy,
            "pair": pair,
            "time_segment": time_segment,
            "confidence": confidence,
            "news_level": news_level
        }

    def learn_from_history(self, trade_history: List[Dict]) -> Dict:
        """Learn from historical trade data

        Args:
            trade_history (List[Dict]): List of historical trades

        Returns:
            Dict: Learning statistics
        """
        if not trade_history:
            return {"error": "No trade history provided"}
        
        # Sort trades by date
        sorted_trades = sorted(trade_history, key=lambda x: x.get("date", ""))
        
        stats = {
            "trades_processed": 0,
            "total_reward": 0.0,
            "actions": {action: 0 for action in self.actions}
        }
        
        # Process each trade
        for i, trade in enumerate(sorted_trades):
            # Skip if missing essential data
            if not all(k in trade for k in ["strategy", "symbol", "result"]):
                continue
            
            # Get pre-trade state
            pre_trade_state = self.get_state_from_trade_data(trade)
            
            # For historical data, assume the action was "trade"
            action = "trade"
            
            # Get post-trade state (use next trade if available, otherwise use same state)
            post_trade_state = pre_trade_state
            if i < len(sorted_trades) - 1:
                post_trade_state = self.get_state_from_trade_data(sorted_trades[i + 1])
            
            # Get trade result and profit/loss
            result = trade.get("result", "unknown")
            profit_loss = trade.get("profit_loss", 0.0)
            
            # Learn from this trade
            reward = self.learn_from_trade(
                pre_trade_state, action, result, profit_loss, post_trade_state
            )
            
            # Update statistics
            stats["trades_processed"] += 1
            stats["total_reward"] += reward
            stats["actions"][action] += 1
        
        # Calculate average reward
        if stats["trades_processed"] > 0:
            stats["average_reward"] = stats["total_reward"] / stats["trades_processed"]
        else:
            stats["average_reward"] = 0.0
        
        return stats

    def get_action_probabilities(self, state: Dict) -> Dict[str, float]:
        """Get probability distribution over actions for a given state

        Args:
            state (Dict): Current state

        Returns:
            Dict[str, float]: Probability for each action
        """
        state_key = self.get_state_key(state)
        q_values = self.get_q_values(state_key)
        
        # Convert Q-values to probabilities using softmax
        q_list = [q_values[a] for a in self.actions]
        max_q = max(q_list)  # Subtract max for numerical stability
        exp_q = [np.exp(q - max_q) for q in q_list]
        sum_exp_q = sum(exp_q)
        
        # Calculate probabilities
        probabilities = {}
        for i, action in enumerate(self.actions):
            if sum_exp_q > 0:
                probabilities[action] = exp_q[i] / sum_exp_q
            else:
                probabilities[action] = 1.0 / len(self.actions)  # Uniform if all Q-values are equal
        
        return probabilities

    def get_best_action_for_state(self, state: Dict) -> Tuple[str, float]:
        """Get the best action for a given state

        Args:
            state (Dict): Current state

        Returns:
            Tuple[str, float]: Best action and its Q-value
        """
        state_key = self.get_state_key(state)
        q_values = self.get_q_values(state_key)
        
        # Find action with highest Q-value
        best_action = max(q_values.items(), key=lambda x: x[1])
        
        return best_action

    def get_best_strategy_for_conditions(self, pair: str, time_segment: Optional[str] = None, 
                                        news_level: str = "none") -> List[Tuple[str, float]]:
        """Get the best strategy for given market conditions

        Args:
            pair (str): Currency pair
            time_segment (Optional[str], optional): Time segment. Defaults to None (current time).
            news_level (str, optional): News level. Defaults to "none".

        Returns:
            List[Tuple[str, float]]: Strategies ranked by expected value
        """
        if time_segment is None:
            time_segment = self.get_time_segment()
        
        # Collect expected values for each strategy
        strategy_values = []
        
        for strategy in self.strategies:
            # Check high confidence scenario
            state = {
                "strategy": strategy,
                "pair": pair,
                "time_segment": time_segment,
                "confidence": "high",
                "news_level": news_level
            }
            
            state_key = self.get_state_key(state)
            q_values = self.get_q_values(state_key)
            
            # Get expected value for "trade" action
            expected_value = q_values.get("trade", 0.0)
            
            strategy_values.append((strategy, expected_value))
        
        # Sort by expected value (descending)
        strategy_values.sort(key=lambda x: x[1], reverse=True)
        
        return strategy_values

    def get_best_time_for_strategy(self, strategy: str, pair: str) -> List[Tuple[str, float]]:
        """Get the best time segment for a given strategy and pair

        Args:
            strategy (str): Strategy name
            pair (str): Currency pair

        Returns:
            List[Tuple[str, float]]: Time segments ranked by expected value
        """
        # Collect expected values for each time segment
        time_values = []
        
        for time_segment in self.time_segments:
            # Check high confidence scenario
            state = {
                "strategy": strategy,
                "pair": pair,
                "time_segment": time_segment,
                "confidence": "high",
                "news_level": "none"
            }
            
            state_key = self.get_state_key(state)
            q_values = self.get_q_values(state_key)
            
            # Get expected value for "trade" action
            expected_value = q_values.get("trade", 0.0)
            
            time_values.append((time_segment, expected_value))
        
        # Sort by expected value (descending)
        time_values.sort(key=lambda x: x[1], reverse=True)
        
        return time_values

    def get_best_pairs_for_strategy(self, strategy: str) -> List[Tuple[str, float]]:
        """Get the best currency pairs for a given strategy

        Args:
            strategy (str): Strategy name

        Returns:
            List[Tuple[str, float]]: Currency pairs ranked by expected value
        """
        # Collect expected values for each pair
        pair_values = []
        
        for pair in self.pairs:
            # Check high confidence scenario
            state = {
                "strategy": strategy,
                "pair": pair,
                "time_segment": self.get_time_segment(),
                "confidence": "high",
                "news_level": "none"
            }
            
            state_key = self.get_state_key(state)
            q_values = self.get_q_values(state_key)
            
            # Get expected value for "trade" action
            expected_value = q_values.get("trade", 0.0)
            
            pair_values.append((pair, expected_value))
        
        # Sort by expected value (descending)
        pair_values.sort(key=lambda x: x[1], reverse=True)
        
        return pair_values

    def get_news_impact_analysis(self) -> Dict:
        """Analyze the impact of news on different strategies

        Returns:
            Dict: News impact analysis
        """
        analysis = {}
        
        for strategy in self.strategies:
            strategy_analysis = {}
            
            for news_level in self.news_levels:
                # Skip "none" level
                if news_level == "none":
                    continue
                
                # Collect expected values across pairs and time segments
                values = []
                
                for pair in self.pairs:
                    for time_segment in self.time_segments:
                        state = {
                            "strategy": strategy,
                            "pair": pair,
                            "time_segment": time_segment,
                            "confidence": "high",
                            "news_level": news_level
                        }
                        
                        state_key = self.get_state_key(state)
                        q_values = self.get_q_values(state_key)
                        
                        # Get expected value for "trade" action
                        expected_value = q_values.get("trade", 0.0)
                        values.append(expected_value)
                
                # Calculate average expected value
                avg_value = sum(values) / len(values) if values else 0.0
                
                # Compare with "none" news level
                none_values = []
                for pair in self.pairs:
                    for time_segment in self.time_segments:
                        state = {
                            "strategy": strategy,
                            "pair": pair,
                            "time_segment": time_segment,
                            "confidence": "high",
                            "news_level": "none"
                        }
                        
                        state_key = self.get_state_key(state)
                        q_values = self.get_q_values(state_key)
                        
                        # Get expected value for "trade" action
                        expected_value = q_values.get("trade", 0.0)
                        none_values.append(expected_value)
                
                avg_none_value = sum(none_values) / len(none_values) if none_values else 0.0
                
                # Calculate impact
                impact = avg_value - avg_none_value
                
                strategy_analysis[news_level] = {
                    "average_value": avg_value,
                    "compared_to_no_news": impact,
                    "recommendation": "avoid" if impact < -0.2 else "caution" if impact < 0 else "neutral"
                }
            
            analysis[strategy] = strategy_analysis
        
        return analysis

    def generate_recommendations(self) -> Dict:
        """Generate trading recommendations based on learned Q-values

        Returns:
            Dict: Trading recommendations
        """
        recommendations = {
            "best_strategy_pairs": [],
            "best_trading_times": [],
            "news_recommendations": [],
            "general_advice": []
        }
        
        # Find best strategy-pair combinations
        all_pair_values = []
        for strategy in self.strategies:
            pair_values = self.get_best_pairs_for_strategy(strategy)
            if pair_values:
                best_pair, best_value = pair_values[0]
                all_pair_values.append((strategy, best_pair, best_value))
        
        # Sort by expected value
        all_pair_values.sort(key=lambda x: x[2], reverse=True)
        
        # Add top recommendations
        for strategy, pair, value in all_pair_values[:3]:
            if value > 0:
                recommendations["best_strategy_pairs"].append({
                    "strategy": strategy,
                    "pair": pair,
                    "expected_value": value
                })
        
        # Find best trading times for top strategies
        for strategy, _, _ in all_pair_values[:2]:
            for pair in self.pairs[:3]:  # Check top 3 pairs
                time_values = self.get_best_time_for_strategy(strategy, pair)
                if time_values and time_values[0][1] > 0:
                    best_time, best_value = time_values[0]
                    recommendations["best_trading_times"].append({
                        "strategy": strategy,
                        "pair": pair,
                        "best_time": best_time,
                        "expected_value": best_value
                    })
        
        # Generate news recommendations
        news_impact = self.get_news_impact_analysis()
        for strategy, analysis in news_impact.items():
            for news_level, data in analysis.items():
                if data["recommendation"] == "avoid":
                    recommendations["news_recommendations"].append({
                        "advice": f"Avoid {strategy} during {news_level} news",
                        "impact": data["compared_to_no_news"]
                    })
        
        # Generate general advice
        # Find strategies that consistently perform well
        consistent_strategies = []
        for strategy in self.strategies:
            positive_count = 0
            total_count = 0
            
            for pair in self.pairs:
                for time_segment in self.time_segments:
                    state = {
                        "strategy": strategy,
                        "pair": pair,
                        "time_segment": time_segment,
                        "confidence": "high",
                        "news_level": "none"
                    }
                    
                    state_key = self.get_state_key(state)
                    q_values = self.get_q_values(state_key)
                    
                    # Get expected value for "trade" action
                    expected_value = q_values.get("trade", 0.0)
                    
                    if expected_value > 0.2:
                        positive_count += 1
                    total_count += 1
            
            if total_count > 0 and (positive_count / total_count) > 0.7:
                consistent_strategies.append(strategy)
        
        if consistent_strategies:
            recommendations["general_advice"].append({
                "advice": f"Increase use of {', '.join(consistent_strategies)}",
                "reason": "These strategies show consistent positive results"
            })
        
        # Find pairs to avoid
        pairs_to_avoid = []
        for pair in self.pairs:
            negative_count = 0
            total_count = 0
            
            for strategy in self.strategies:
                for time_segment in self.time_segments:
                    state = {
                        "strategy": strategy,
                        "pair": pair,
                        "time_segment": time_segment,
                        "confidence": "high",
                        "news_level": "none"
                    }
                    
                    state_key = self.get_state_key(state)
                    q_values = self.get_q_values(state_key)
                    
                    # Get expected value for "trade" action
                    expected_value = q_values.get("trade", 0.0)
                    
                    if expected_value < -0.2:
                        negative_count += 1
                    total_count += 1
            
            if total_count > 0 and (negative_count / total_count) > 0.5:
                pairs_to_avoid.append(pair)
        
        if pairs_to_avoid:
            recommendations["general_advice"].append({
                "advice": f"Reduce trading on {', '.join(pairs_to_avoid)}",
                "reason": "These pairs show consistently negative results"
            })
        
        return recommendations


# Helper functions
def get_recommended_action(state: Dict) -> str:
    """Get recommended action for a given state (helper function)

    Args:
        state (Dict): Current state

    Returns:
        str: Recommended action
    """
    trader = ReinforceTrader()
    return trader.choose_action(state, explore=False)


def learn_from_trade_history(trade_history: List[Dict]) -> Dict:
    """Learn from trade history (helper function)

    Args:
        trade_history (List[Dict]): List of historical trades

    Returns:
        Dict: Learning statistics
    """
    trader = ReinforceTrader()
    return trader.learn_from_history(trade_history)


def get_trading_recommendations() -> Dict:
    """Get trading recommendations (helper function)

    Returns:
        Dict: Trading recommendations
    """
    trader = ReinforceTrader()
    return trader.generate_recommendations()


# For testing
if __name__ == "__main__":
    # Create an instance of the reinforcement trader
    trader = ReinforceTrader()
    
    # Generate some test trades
    print("Generating test trades...")
    
    # Define test trades
    test_trades = [
        {
            "date": (datetime.utcnow() - timedelta(days=10)).isoformat(),
            "symbol": "EURUSD",
            "strategy": "FVG",
            "confidence": 75,
            "news_nearby": False,
            "result": "win",
            "profit_loss": 50.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=9)).isoformat(),
            "symbol": "EURUSD",
            "strategy": "FVG",
            "confidence": 65,
            "news_nearby": True,
            "news_impact": "medium",
            "result": "loss",
            "profit_loss": -30.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=8)).isoformat(),
            "symbol": "GBPUSD",
            "strategy": "FVG",
            "confidence": 60,
            "news_nearby": False,
            "result": "loss",
            "profit_loss": -25.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "symbol": "EURUSD",
            "strategy": "OTE",
            "confidence": 80,
            "news_nearby": False,
            "result": "win",
            "profit_loss": 45.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=6)).isoformat(),
            "symbol": "GBPUSD",
            "strategy": "OTE",
            "confidence": 75,
            "news_nearby": False,
            "result": "win",
            "profit_loss": 35.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            "symbol": "USDJPY",
            "strategy": "OTE",
            "confidence": 70,
            "news_nearby": True,
            "news_impact": "low",
            "result": "win",
            "profit_loss": 30.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=4)).isoformat(),
            "symbol": "EURUSD",
            "strategy": "Cypher",
            "confidence": 65,
            "news_nearby": False,
            "result": "loss",
            "profit_loss": -20.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            "symbol": "GBPUSD",
            "strategy": "Cypher",
            "confidence": 70,
            "news_nearby": False,
            "result": "win",
            "profit_loss": 25.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "symbol": "USDJPY",
            "strategy": "Cypher",
            "confidence": 60,
            "news_nearby": True,
            "news_impact": "high",
            "result": "loss",
            "profit_loss": -30.0
        },
        {
            "date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "symbol": "EURUSD",
            "strategy": "OTE",
            "confidence": 85,
            "news_nearby": False,
            "result": "win",
            "profit_loss": 55.0
        }
    ]
    
    # Learn from test trades
    print("Learning from test trades...")
    stats = trader.learn_from_history(test_trades)
    
    print(f"Processed {stats['trades_processed']} trades")
    print(f"Total reward: {stats['total_reward']:.2f}")
    print(f"Average reward: {stats['average_reward']:.2f}")
    
    # Test action selection
    print("\nTesting action selection...")
    
    test_states = [
        {
            "strategy": "OTE",
            "pair": "EURUSD",
            "time_segment": "london",
            "confidence": "high",
            "news_level": "none"
        },
        {
            "strategy": "FVG",
            "pair": "GBPUSD",
            "time_segment": "asian",
            "confidence": "medium",
            "news_level": "none"
        },
        {
            "strategy": "Cypher",
            "pair": "USDJPY",
            "time_segment": "overlap",
            "confidence": "high",
            "news_level": "high"
        }
    ]
    
    for i, state in enumerate(test_states, 1):
        action = trader.choose_action(state, explore=False)
        probs = trader.get_action_probabilities(state)
        
        print(f"\nState {i}:")
        print(f"  Strategy: {state['strategy']}")
        print(f"  Pair: {state['pair']}")
        print(f"  Time: {state['time_segment']}")
        print(f"  Confidence: {state['confidence']}")
        print(f"  News Level: {state['news_level']}")
        print(f"  Recommended Action: {action}")
        print(f"  Action Probabilities:")
        for a, p in probs.items():
            print(f"    {a}: {p:.2f}")
    
    # Get best strategies for current conditions
    print("\nBest strategies for EURUSD:")
    strategies = trader.get_best_strategy_for_conditions("EURUSD")
    
    for strategy, value in strategies:
        print(f"  {strategy}: {value:.2f}")
    
    # Get best time for OTE strategy on EURUSD
    print("\nBest time for OTE on EURUSD:")
    times = trader.get_best_time_for_strategy("OTE", "EURUSD")
    
    for time_segment, value in times:
        print(f"  {time_segment}: {value:.2f}")
    
    # Get best pairs for OTE strategy
    print("\nBest pairs for OTE strategy:")
    pairs = trader.get_best_pairs_for_strategy("OTE")
    
    for pair, value in pairs:
        print(f"  {pair}: {value:.2f}")
    
    # Generate recommendations
    print("\nTrading Recommendations:")
    recommendations = trader.generate_recommendations()
    
    if recommendations["best_strategy_pairs"]:
        print("\nBest Strategy-Pair Combinations:")
        for rec in recommendations["best_strategy_pairs"]:
            print(f"  {rec['strategy']} on {rec['pair']} (Expected Value: {rec['expected_value']:.2f})")
    
    if recommendations["best_trading_times"]:
        print("\nBest Trading Times:")
        for rec in recommendations["best_trading_times"]:
            print(f"  {rec['strategy']} on {rec['pair']} during {rec['best_time']} session (Expected Value: {rec['expected_value']:.2f})")
    
    if recommendations["news_recommendations"]:
        print("\nNews Recommendations:")
        for rec in recommendations["news_recommendations"]:
            print(f"  {rec['advice']} (Impact: {rec['impact']:.2f})")
    
    if recommendations["general_advice"]:
        print("\nGeneral Advice:")
        for rec in recommendations["general_advice"]:
            print(f"  {rec['advice']}")
            print(f"    Reason: {rec['reason']}")