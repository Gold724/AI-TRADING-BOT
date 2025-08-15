# agents/sentinel_agent.py

from typing import Dict, Any
import logging
from datetime import datetime

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sentinel_agent')

class SentinelAgent(BaseAgent):
    """Core executor and logic router for the multi-agent system"""
    
    def __init__(self, agent_id: str = "sentinel", config: Dict[str, Any] = None):
        """Initialize the Sentinel agent
        
        Args:
            agent_id (str, optional): Unique identifier for this agent. Defaults to "sentinel".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id=agent_id, role="core", config=config)
        self.last_decisions = []
        self.max_history = 20
    
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
        indicators = context.get("indicators", {})
        
        # Default proposal
        proposal = {
            "action": "hold",
            "confidence": 50,
            "reason": "Insufficient data for decision",
            "timestamp": datetime.now().isoformat()
        }
        
        # Analyze market data and indicators
        if market_data and indicators:
            # Determine trend direction
            trend_direction = indicators.get("trend_direction", "neutral")
            momentum = indicators.get("momentum", "neutral")
            
            # Make decision based on trend and momentum
            if trend_direction == "up" and momentum == "increasing":
                proposal["action"] = "buy"
                proposal["confidence"] = 75
                proposal["reason"] = f"Strong uptrend with increasing momentum in {strategy} strategy"
            elif trend_direction == "down" and momentum == "increasing":
                proposal["action"] = "sell"
                proposal["confidence"] = 75
                proposal["reason"] = f"Strong downtrend with increasing momentum in {strategy} strategy"
            elif trend_direction == "up" and momentum == "decreasing":
                proposal["action"] = "buy"
                proposal["confidence"] = 60
                proposal["reason"] = f"Uptrend with decreasing momentum in {strategy} strategy"
            elif trend_direction == "down" and momentum == "decreasing":
                proposal["action"] = "sell"
                proposal["confidence"] = 60
                proposal["reason"] = f"Downtrend with decreasing momentum in {strategy} strategy"
            else:
                proposal["action"] = "hold"
                proposal["confidence"] = 65
                proposal["reason"] = f"Unclear trend or momentum in {strategy} strategy"
        
        # Store decision in history
        self.last_decisions.append(proposal)
        if len(self.last_decisions) > self.max_history:
            self.last_decisions.pop(0)
        
        return proposal
    
    def is_specialized_for(self, context: Dict[str, Any]) -> bool:
        """Check if this agent is specialized for the given context
        
        Args:
            context (Dict[str, Any]): Trading context
            
        Returns:
            bool: True if agent is specialized for this context, False otherwise
        """
        # Sentinel is a core agent and participates in all decisions
        return True