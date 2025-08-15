# trend_analyst.py

from typing import Dict, Any, List
import logging
from datetime import datetime
import os
import numpy as np

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trend_analyst')

class TrendAnalyst(BaseAgent):
    """Agent specialized in trend analysis and momentum indicators"""
    
    def __init__(self, agent_id: str = "trend_analyst", config: Dict[str, Any] = None):
        """Initialize the trend analyst agent
        
        Args:
            agent_id (str, optional): Agent identifier. Defaults to "trend_analyst".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id, "strategy", config)
        
        # Default indicator weights
        self.indicator_weights = {
            "ema_cross": 0.3,
            "macd": 0.25,
            "rsi": 0.2,
            "adx": 0.15,
            "volume": 0.1
        }
        
        # Override with config if provided
        if config and 'indicator_weights' in config:
            self.indicator_weights.update(config['indicator_weights'])
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Propose a trade based on trend analysis
        
        Args:
            context (Dict[str, Any]): Trading context with market data
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Default response
        proposal = {
            "action": "hold",
            "confidence": 0,
            "reason": "Insufficient data for trend analysis",
            "veto": False,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if we have the required data
        if not context or 'indicators' not in context:
            return proposal
        
        indicators = context['indicators']
        
        # Calculate trend score
        trend_score = 0
        signal_count = 0
        reasons = []
        
        # Check EMA crossover
        if 'ema_cross' in indicators:
            ema_signal = indicators['ema_cross']
            if ema_signal > 0:  # Bullish
                trend_score += self.indicator_weights['ema_cross']
                reasons.append("EMA crossover bullish")
            elif ema_signal < 0:  # Bearish
                trend_score -= self.indicator_weights['ema_cross']
                reasons.append("EMA crossover bearish")
            signal_count += 1
        
        # Check MACD
        if 'macd' in indicators:
            macd_signal = indicators['macd']
            if macd_signal > 0:  # Bullish
                trend_score += self.indicator_weights['macd']
                reasons.append("MACD bullish")
            elif macd_signal < 0:  # Bearish
                trend_score -= self.indicator_weights['macd']
                reasons.append("MACD bearish")
            signal_count += 1
        
        # Check RSI
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi > 70:  # Overbought
                trend_score -= self.indicator_weights['rsi']
                reasons.append("RSI overbought")
            elif rsi < 30:  # Oversold
                trend_score += self.indicator_weights['rsi']
                reasons.append("RSI oversold")
            signal_count += 1
        
        # Check ADX (trend strength)
        if 'adx' in indicators:
            adx = indicators['adx']
            if adx > 25:  # Strong trend
                # ADX doesn't indicate direction, just strengthens existing signals
                trend_score *= (1 + self.indicator_weights['adx'])
                reasons.append("ADX indicates strong trend")
            signal_count += 1
        
        # Check volume
        if 'volume' in indicators and 'avg_volume' in indicators:
            volume = indicators['volume']
            avg_volume = indicators['avg_volume']
            if volume > avg_volume * 1.5:  # High volume
                # High volume strengthens existing signals
                trend_score *= (1 + self.indicator_weights['volume'])
                reasons.append("High volume confirms trend")
            signal_count += 1
        
        # Normalize trend score to confidence percentage
        if signal_count > 0:
            # Convert trend score to confidence (0-100)
            confidence = min(100, max(0, 50 + trend_score * 50))
            
            # Determine action based on confidence
            if confidence >= 70:
                action = "buy"
            elif confidence <= 30:
                action = "sell"
            else:
                action = "hold"
            
            proposal["action"] = action
            proposal["confidence"] = confidence
            proposal["reason"] = ", ".join(reasons)
        
        return proposal
    
    def analyze_trend_strength(self, prices: List[float]) -> float:
        """Analyze the strength of a price trend
        
        Args:
            prices (List[float]): Historical prices
            
        Returns:
            float: Trend strength score (-1 to 1)
        """
        if len(prices) < 10:
            return 0
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Calculate trend metrics
        avg_return = np.mean(returns)
        consistency = np.sum(np.sign(returns) == np.sign(avg_return)) / len(returns)
        
        # Combine into trend strength score
        trend_strength = np.sign(avg_return) * consistency
        
        return trend_strength