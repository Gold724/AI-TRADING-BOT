# agents/watcher_agent.py

from typing import Dict, Any, List
import logging
from datetime import datetime
import numpy as np

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('watcher_agent')

class WatcherAgent(BaseAgent):
    """Evaluates trade history and flags volatility clusters"""
    
    def __init__(self, agent_id: str = "watcher", config: Dict[str, Any] = None):
        """Initialize the Watcher agent
        
        Args:
            agent_id (str, optional): Unique identifier for this agent. Defaults to "watcher".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id=agent_id, role="analyst", config=config)
        
        # Initialize with default config if none provided
        if config is None:
            config = {}
        
        # Configuration parameters
        self.volatility_threshold = config.get("volatility_threshold", 1.5)  # Standard deviations above mean
        self.history_window = config.get("history_window", 50)  # Number of trades to analyze
        self.min_trades_required = config.get("min_trades_required", 10)  # Minimum trades needed for analysis
        
        # Internal state
        self.trade_history: List[Dict[str, Any]] = []
        self.volatility_history: List[float] = []
        self.anomaly_scores: List[float] = []
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a trade action based on the provided context
        
        Args:
            context (Dict[str, Any]): Trading context including market data, signals, etc.
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Extract relevant data from context
        market_data = context.get("market_data", {})
        strategy = context.get("strategy", "unknown")
        trade_history = context.get("trade_history", [])
        
        # Update internal trade history
        if trade_history:
            self.update_trade_history(trade_history)
        
        # Default proposal
        proposal = {
            "action": "hold",
            "confidence": 50,
            "reason": "Insufficient data for volatility analysis",
            "timestamp": datetime.now().isoformat(),
            "anomaly_score": 0.0
        }
        
        # Check if we have enough trade history for analysis
        if len(self.trade_history) < self.min_trades_required:
            return proposal
        
        # Calculate current volatility
        current_volatility = self.calculate_volatility()
        self.volatility_history.append(current_volatility)
        
        # Calculate anomaly score
        anomaly_score = self.calculate_anomaly_score(current_volatility)
        self.anomaly_scores.append(anomaly_score)
        proposal["anomaly_score"] = anomaly_score
        
        # Make decision based on volatility and anomaly score
        if anomaly_score > 0.8:
            proposal["action"] = "halt"
            proposal["confidence"] = 90
            proposal["reason"] = f"Critical volatility anomaly detected (score: {anomaly_score:.2f}). Recommend halting trading."
        elif anomaly_score > 0.6:
            proposal["action"] = "reduce_risk"
            proposal["confidence"] = 75
            proposal["reason"] = f"High volatility anomaly detected (score: {anomaly_score:.2f}). Recommend reducing position sizes."
        elif anomaly_score > 0.4:
            proposal["action"] = "caution"
            proposal["confidence"] = 65
            proposal["reason"] = f"Elevated volatility detected (score: {anomaly_score:.2f}). Proceed with caution."
        else:
            # Check recent performance trend
            recent_performance = self.analyze_recent_performance()
            if recent_performance > 0.6:
                proposal["action"] = "continue"
                proposal["confidence"] = 70
                proposal["reason"] = f"Normal volatility with positive performance trend. Continue current strategy."
            elif recent_performance < 0.4:
                proposal["action"] = "review"
                proposal["confidence"] = 60
                proposal["reason"] = f"Normal volatility but negative performance trend. Review strategy parameters."
            else:
                proposal["action"] = "hold"
                proposal["confidence"] = 55
                proposal["reason"] = f"Normal market conditions. No significant volatility anomalies detected."
        
        # Log anomaly score if significant
        if anomaly_score > 0.4:
            self.log_anomaly_score(anomaly_score, strategy)
        
        return proposal
    
    def update_trade_history(self, new_trades: List[Dict[str, Any]]) -> None:
        """Update the internal trade history
        
        Args:
            new_trades (List[Dict[str, Any]]): New trades to add to history
        """
        # Add new trades to history
        self.trade_history.extend(new_trades)
        
        # Keep only the most recent trades within the history window
        if len(self.trade_history) > self.history_window:
            self.trade_history = self.trade_history[-self.history_window:]
    
    def calculate_volatility(self) -> float:
        """Calculate current market volatility based on trade history
        
        Returns:
            float: Volatility measure
        """
        if not self.trade_history or len(self.trade_history) < 2:
            return 0.0
        
        # Extract price changes from trade history
        price_changes = []
        for i in range(1, len(self.trade_history)):
            current_price = self.trade_history[i].get("price", 0)
            previous_price = self.trade_history[i-1].get("price", 0)
            if current_price > 0 and previous_price > 0:
                price_change_pct = abs((current_price - previous_price) / previous_price) * 100
                price_changes.append(price_change_pct)
        
        if not price_changes:
            return 0.0
        
        # Calculate volatility as standard deviation of price changes
        return np.std(price_changes)
    
    def calculate_anomaly_score(self, current_volatility: float) -> float:
        """Calculate anomaly score based on current volatility compared to historical
        
        Args:
            current_volatility (float): Current volatility measure
            
        Returns:
            float: Anomaly score between 0.0 and 1.0
        """
        if not self.volatility_history or current_volatility == 0:
            return 0.0
        
        # Calculate mean and standard deviation of historical volatility
        hist_mean = np.mean(self.volatility_history)
        hist_std = np.std(self.volatility_history) if len(self.volatility_history) > 1 else hist_mean
        
        # Avoid division by zero
        if hist_std == 0:
            hist_std = 0.001
        
        # Calculate z-score
        z_score = (current_volatility - hist_mean) / hist_std
        
        # Convert to anomaly score between 0 and 1
        # Using sigmoid function to bound the score
        anomaly_score = 1 / (1 + np.exp(-z_score + self.volatility_threshold))
        
        return min(max(anomaly_score, 0.0), 1.0)  # Ensure score is between 0 and 1
    
    def analyze_recent_performance(self) -> float:
        """Analyze recent trading performance
        
        Returns:
            float: Performance score between 0.0 and 1.0
        """
        if not self.trade_history:
            return 0.5  # Neutral score if no history
        
        # Get recent trades (last 30% of history)
        recent_count = max(int(len(self.trade_history) * 0.3), 1)
        recent_trades = self.trade_history[-recent_count:]
        
        # Count profitable trades
        profitable_count = sum(1 for trade in recent_trades if trade.get("profit", 0) > 0)
        
        # Calculate win rate
        win_rate = profitable_count / len(recent_trades) if recent_trades else 0.5
        
        return win_rate
    
    def log_anomaly_score(self, score: float, strategy: str) -> None:
        """Log anomaly score to file
        
        Args:
            score (float): Anomaly score
            strategy (str): Strategy name
        """
        try:
            import os
            import json
            from datetime import datetime
            
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Prepare log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy,
                "anomaly_score": score,
                "agent_id": self.agent_id
            }
            
            # Append to log file
            with open("logs/anomaly_scores.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging anomaly score: {e}")
    
    def is_specialized_for(self, context: Dict[str, Any]) -> bool:
        """Check if this agent is specialized for the given context
        
        Args:
            context (Dict[str, Any]): Trading context
            
        Returns:
            bool: True if agent is specialized for this context, False otherwise
        """
        # Watcher specializes in volatility analysis and anomaly detection
        return "trade_history" in context or "volatility" in context.get("indicators", {})