# agents/observer_agent.py

from typing import Dict, Any, List
import logging
from datetime import datetime
import os
import json
import re

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('observer_agent')

class ObserverAgent(BaseAgent):
    """Watches external factors (news, spikes, liquidity shifts)"""
    
    def __init__(self, agent_id: str = "observer", config: Dict[str, Any] = None):
        """Initialize the Observer agent
        
        Args:
            agent_id (str, optional): Unique identifier for this agent. Defaults to "observer".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id=agent_id, role="monitor", config=config)
        
        # Initialize with default config if none provided
        if config is None:
            config = {}
        
        # Configuration parameters
        self.news_impact_threshold = config.get("news_impact_threshold", 0.6)  # Threshold for significant news
        self.price_spike_threshold = config.get("price_spike_threshold", 1.5)  # Standard deviations for spike detection
        self.liquidity_threshold = config.get("liquidity_threshold", 0.5)  # Threshold for liquidity shifts
        
        # Keywords for news sentiment analysis
        self.bullish_keywords = config.get("bullish_keywords", [
            "rally", "surge", "jump", "gain", "rise", "soar", "boost", "growth", "recovery",
            "bullish", "optimistic", "positive", "upbeat", "strong", "outperform"
        ])
        
        self.bearish_keywords = config.get("bearish_keywords", [
            "drop", "fall", "decline", "slump", "plunge", "crash", "tumble", "bearish",
            "pessimistic", "negative", "weak", "underperform", "downgrade", "concern"
        ])
        
        # Internal state
        self.recent_news: List[Dict[str, Any]] = []
        self.recent_spikes: List[Dict[str, Any]] = []
        self.recent_liquidity_shifts: List[Dict[str, Any]] = []
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a trade action based on the provided context
        
        Args:
            context (Dict[str, Any]): Trading context including market data, signals, etc.
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Extract relevant data from context
        market_data = context.get("market_data", {})
        news_data = context.get("news_data", [])
        strategy = context.get("strategy", "unknown")
        
        # Update internal state with new data
        if news_data:
            self.process_news_data(news_data)
        
        if market_data:
            self.detect_price_spikes(market_data)
            self.detect_liquidity_shifts(market_data)
        
        # Default proposal
        proposal = {
            "action": "continue",
            "confidence": 50,
            "reason": "No significant external factors detected",
            "timestamp": datetime.now().isoformat(),
            "external_factors": []
        }
        
        # Check for significant news impact
        news_impact = self.analyze_news_impact()
        if abs(news_impact) > self.news_impact_threshold:
            factor = {
                "type": "news",
                "impact": news_impact,
                "description": f"Significant {'bullish' if news_impact > 0 else 'bearish'} news detected"
            }
            proposal["external_factors"].append(factor)
        
        # Check for price spikes
        if self.recent_spikes:
            latest_spike = self.recent_spikes[-1]
            factor = {
                "type": "price_spike",
                "impact": latest_spike["magnitude"],
                "direction": latest_spike["direction"],
                "description": f"Price spike of {latest_spike['magnitude']:.2f}% detected"
            }
            proposal["external_factors"].append(factor)
        
        # Check for liquidity shifts
        if self.recent_liquidity_shifts:
            latest_shift = self.recent_liquidity_shifts[-1]
            factor = {
                "type": "liquidity_shift",
                "impact": latest_shift["magnitude"],
                "description": f"Liquidity {'increase' if latest_shift['magnitude'] > 0 else 'decrease'} detected"
            }
            proposal["external_factors"].append(factor)
        
        # Make decision based on external factors
        if proposal["external_factors"]:
            # Calculate overall impact
            overall_impact = sum(factor["impact"] for factor in proposal["external_factors"])
            
            # Determine action based on impact
            if overall_impact > 0.8:
                proposal["action"] = "buy"
                proposal["confidence"] = 70
                proposal["reason"] = "Strong positive external factors detected"
            elif overall_impact > 0.4:
                proposal["action"] = "cautious_buy"
                proposal["confidence"] = 60
                proposal["reason"] = "Moderate positive external factors detected"
            elif overall_impact < -0.8:
                proposal["action"] = "sell"
                proposal["confidence"] = 70
                proposal["reason"] = "Strong negative external factors detected"
            elif overall_impact < -0.4:
                proposal["action"] = "cautious_sell"
                proposal["confidence"] = 60
                proposal["reason"] = "Moderate negative external factors detected"
            else:
                proposal["action"] = "hold"
                proposal["confidence"] = 55
                proposal["reason"] = "Mixed external factors detected"
            
            # Log external factors
            self.log_external_factors(proposal["external_factors"], strategy)
        
        return proposal
    
    def process_news_data(self, news_data: List[Dict[str, Any]]) -> None:
        """Process and store news data
        
        Args:
            news_data (List[Dict[str, Any]]): List of news items
        """
        # Add sentiment analysis to news data
        for news_item in news_data:
            if "sentiment" not in news_item:
                news_item["sentiment"] = self.analyze_news_sentiment(news_item.get("headline", "") + " " + news_item.get("summary", ""))
            
            # Add timestamp if not present
            if "timestamp" not in news_item:
                news_item["timestamp"] = datetime.now().isoformat()
            
            # Add to recent news
            self.recent_news.append(news_item)
        
        # Keep only recent news (last 24 hours)
        current_time = datetime.now()
        self.recent_news = [
            news for news in self.recent_news 
            if (current_time - datetime.fromisoformat(news["timestamp"])).total_seconds() < 86400
        ]
    
    def analyze_news_sentiment(self, text: str) -> float:
        """Analyze sentiment of news text
        
        Args:
            text (str): News text to analyze
            
        Returns:
            float: Sentiment score between -1.0 (bearish) and 1.0 (bullish)
        """
        text = text.lower()
        
        # Count bullish and bearish keywords
        bullish_count = sum(1 for keyword in self.bullish_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', text))
        bearish_count = sum(1 for keyword in self.bearish_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', text))
        
        # Calculate sentiment score
        total_count = bullish_count + bearish_count
        if total_count == 0:
            return 0.0
        
        return (bullish_count - bearish_count) / total_count
    
    def analyze_news_impact(self) -> float:
        """Analyze overall impact of recent news
        
        Returns:
            float: News impact score between -1.0 (bearish) and 1.0 (bullish)
        """
        if not self.recent_news:
            return 0.0
        
        # Calculate weighted average of news sentiment
        # More recent news has higher weight
        total_weight = 0.0
        weighted_sentiment = 0.0
        
        for i, news in enumerate(self.recent_news):
            # Weight decreases with age (most recent has highest weight)
            weight = 1.0 / (i + 1)
            sentiment = news.get("sentiment", 0.0)
            
            weighted_sentiment += sentiment * weight
            total_weight += weight
        
        return weighted_sentiment / total_weight if total_weight > 0 else 0.0
    
    def detect_price_spikes(self, market_data: Dict[str, Any]) -> None:
        """Detect price spikes in market data
        
        Args:
            market_data (Dict[str, Any]): Market data including price information
        """
        # Extract price data
        prices = market_data.get("prices", [])
        if not prices or len(prices) < 2:
            return
        
        # Calculate percentage change
        current_price = prices[-1]
        previous_price = prices[-2]
        pct_change = ((current_price - previous_price) / previous_price) * 100
        
        # Check if change exceeds threshold
        if abs(pct_change) > self.price_spike_threshold:
            spike = {
                "timestamp": datetime.now().isoformat(),
                "magnitude": pct_change,
                "direction": "up" if pct_change > 0 else "down",
                "price": current_price
            }
            
            self.recent_spikes.append(spike)
            logger.info(f"Detected price spike: {pct_change:.2f}% {'up' if pct_change > 0 else 'down'}")
        
        # Keep only recent spikes (last hour)
        current_time = datetime.now()
        self.recent_spikes = [
            spike for spike in self.recent_spikes 
            if (current_time - datetime.fromisoformat(spike["timestamp"])).total_seconds() < 3600
        ]
    
    def detect_liquidity_shifts(self, market_data: Dict[str, Any]) -> None:
        """Detect shifts in market liquidity
        
        Args:
            market_data (Dict[str, Any]): Market data including volume/liquidity information
        """
        # Extract volume data
        volumes = market_data.get("volumes", [])
        if not volumes or len(volumes) < 5:  # Need enough data points
            return
        
        # Calculate average volume for recent periods
        recent_avg = sum(volumes[-3:]) / 3
        previous_avg = sum(volumes[-8:-3]) / 5
        
        # Calculate percentage change in volume
        if previous_avg > 0:
            pct_change = ((recent_avg - previous_avg) / previous_avg) * 100
            
            # Check if change exceeds threshold
            if abs(pct_change) > self.liquidity_threshold * 100:
                shift = {
                    "timestamp": datetime.now().isoformat(),
                    "magnitude": pct_change / 100,  # Normalize to -1.0 to 1.0 range
                    "recent_volume": recent_avg,
                    "previous_volume": previous_avg
                }
                
                self.recent_liquidity_shifts.append(shift)
                logger.info(f"Detected liquidity shift: {pct_change:.2f}% {'increase' if pct_change > 0 else 'decrease'}")
        
        # Keep only recent shifts (last 2 hours)
        current_time = datetime.now()
        self.recent_liquidity_shifts = [
            shift for shift in self.recent_liquidity_shifts 
            if (current_time - datetime.fromisoformat(shift["timestamp"])).total_seconds() < 7200
        ]
    
    def log_external_factors(self, factors: List[Dict[str, Any]], strategy: str) -> None:
        """Log external factors to file
        
        Args:
            factors (List[Dict[str, Any]]): List of external factors
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
                "agent_id": self.agent_id,
                "factors": factors
            }
            
            # Append to log file
            with open("logs/external_factors.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging external factors: {e}")
    
    def is_specialized_for(self, context: Dict[str, Any]) -> bool:
        """Check if this agent is specialized for the given context
        
        Args:
            context (Dict[str, Any]): Trading context
            
        Returns:
            bool: True if agent is specialized for this context, False otherwise
        """
        # Observer specializes in external factors analysis
        return "news_data" in context or "market_data" in context