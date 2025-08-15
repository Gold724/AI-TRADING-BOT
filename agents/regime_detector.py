# regime_detector.py

from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime
import os
import numpy as np
from enum import Enum

from agents.base_agent import BaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('regime_detector')

class MarketRegime(Enum):
    """Enum for different market regimes"""
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    UNKNOWN = "unknown"

class RegimeDetector(BaseAgent):
    """Agent specialized in detecting market regimes and conditions"""
    
    def __init__(self, agent_id: str = "regime_detector", config: Dict[str, Any] = None):
        """Initialize the regime detector agent
        
        Args:
            agent_id (str, optional): Agent identifier. Defaults to "regime_detector".
            config (Dict[str, Any], optional): Configuration parameters. Defaults to None.
        """
        super().__init__(agent_id, "analysis", config)
        
        # Default regime detection parameters
        self.regime_params = {
            "lookback_periods": 20,  # Number of periods to analyze
            "volatility_threshold": 1.5,  # Threshold for high volatility
            "trend_threshold": 0.6,  # Threshold for trend strength
            "range_threshold": 0.3,  # Threshold for ranging market
            "breakout_threshold": 2.0,  # Threshold for breakout detection
        }
        
        # Override with config if provided
        if config and 'regime_params' in config:
            self.regime_params.update(config['regime_params'])
        
        # Track the current regime
        self.current_regime = MarketRegime.UNKNOWN
        self.regime_duration = 0
    
    def propose_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect market regime and propose appropriate strategy
        
        Args:
            context (Dict[str, Any]): Trading context with market data
            
        Returns:
            Dict[str, Any]: Trade proposal with action, confidence, and reasoning
        """
        # Default response
        proposal = {
            "action": "hold",
            "confidence": 50,
            "reason": "Insufficient data for regime detection",
            "veto": False,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "regime": MarketRegime.UNKNOWN.value
        }
        
        # Check if we have the required data
        if not context or 'market_data' not in context:
            return proposal
        
        market_data = context['market_data']
        
        # Extract price data
        if 'prices' not in market_data or len(market_data['prices']) < self.regime_params['lookback_periods']:
            return proposal
        
        prices = market_data['prices'][-self.regime_params['lookback_periods']:]
        
        # Detect current market regime
        regime, confidence, metrics = self._detect_regime(prices)
        
        # Update regime tracking
        if regime == self.current_regime:
            self.regime_duration += 1
        else:
            self.current_regime = regime
            self.regime_duration = 1
        
        # Determine action based on regime
        action, action_confidence, reason = self._get_regime_action(regime, metrics)
        
        # Prepare proposal
        proposal["action"] = action
        proposal["confidence"] = min(100, max(0, int(confidence * action_confidence)))
        proposal["reason"] = f"Detected {regime.value} regime ({self.regime_duration} periods): {reason}"
        proposal["regime"] = regime.value
        
        # Add regime metrics to context for other agents
        if 'regime_info' not in context:
            context['regime_info'] = {}
        
        context['regime_info'] = {
            "regime": regime.value,
            "confidence": confidence,
            "duration": self.regime_duration,
            "metrics": metrics
        }
        
        return proposal
    
    def _detect_regime(self, prices: List[float]) -> Tuple[MarketRegime, float, Dict[str, float]]:
        """Detect the current market regime based on price action
        
        Args:
            prices (List[float]): Historical prices
            
        Returns:
            Tuple[MarketRegime, float, Dict[str, float]]: 
                Detected regime, confidence level, and metrics
        """
        # Calculate key metrics
        returns = np.diff(prices) / prices[:-1]
        
        # Trend metrics
        price_change = (prices[-1] / prices[0]) - 1
        linear_regression = self._calculate_linear_regression(prices)
        trend_strength = abs(linear_regression['slope']) / np.mean(prices) * len(prices)
        trend_direction = np.sign(linear_regression['slope'])
        r_squared = linear_regression['r_squared']
        
        # Volatility metrics
        volatility = np.std(returns) * np.sqrt(len(returns))
        avg_volatility = np.mean(np.abs(returns))
        recent_volatility = np.std(returns[-5:]) * np.sqrt(5) if len(returns) >= 5 else volatility
        volatility_ratio = recent_volatility / volatility if volatility > 0 else 1.0
        
        # Range metrics
        price_range = (np.max(prices) - np.min(prices)) / np.mean(prices)
        upper_band = np.mean(prices) + 2 * np.std(prices)
        lower_band = np.mean(prices) - 2 * np.std(prices)
        in_range = np.mean((prices > lower_band) & (prices < upper_band))
        
        # Breakout metrics
        recent_max = np.max(prices[-5:]) if len(prices) >= 5 else np.max(prices)
        recent_min = np.min(prices[-5:]) if len(prices) >= 5 else np.min(prices)
        historical_max = np.max(prices[:-5]) if len(prices) >= 5 else np.max(prices)
        historical_min = np.min(prices[:-5]) if len(prices) >= 5 else np.min(prices)
        
        breakout_up = recent_max > historical_max * (1 + self.regime_params['breakout_threshold'] * avg_volatility)
        breakout_down = recent_min < historical_min * (1 - self.regime_params['breakout_threshold'] * avg_volatility)
        
        # Reversal metrics
        price_direction = np.sign(prices[-1] - prices[-2]) if len(prices) >= 2 else 0
        trend_reversal = (trend_direction * price_direction) < 0
        
        # Compile metrics
        metrics = {
            "price_change": price_change,
            "trend_strength": trend_strength,
            "trend_direction": trend_direction,
            "r_squared": r_squared,
            "volatility": volatility,
            "volatility_ratio": volatility_ratio,
            "price_range": price_range,
            "in_range": in_range,
            "breakout_up": breakout_up,
            "breakout_down": breakout_down,
            "trend_reversal": trend_reversal
        }
        
        # Determine regime
        if breakout_up or breakout_down:
            regime = MarketRegime.BREAKOUT
            confidence = 0.8 + 0.2 * (volatility_ratio - 1) if volatility_ratio > 1 else 0.8
        elif volatility > self.regime_params['volatility_threshold']:
            regime = MarketRegime.VOLATILE
            confidence = 0.7 + 0.3 * (volatility / self.regime_params['volatility_threshold'] - 1)
        elif trend_strength > self.regime_params['trend_threshold'] and r_squared > 0.7:
            if trend_direction > 0:
                regime = MarketRegime.TRENDING_BULLISH
            else:
                regime = MarketRegime.TRENDING_BEARISH
            confidence = 0.6 + 0.4 * r_squared
        elif in_range > self.regime_params['range_threshold']:
            regime = MarketRegime.RANGING
            confidence = 0.5 + 0.5 * in_range
        elif trend_reversal:
            regime = MarketRegime.REVERSAL
            confidence = 0.6 + 0.4 * (1 - r_squared)
        else:
            # Default to unknown if no clear regime is detected
            regime = MarketRegime.UNKNOWN
            confidence = 0.5
        
        return regime, min(1.0, max(0.0, confidence)), metrics
    
    def _calculate_linear_regression(self, prices: List[float]) -> Dict[str, float]:
        """Calculate linear regression for price series
        
        Args:
            prices (List[float]): Historical prices
            
        Returns:
            Dict[str, float]: Linear regression metrics
        """
        x = np.arange(len(prices))
        y = np.array(prices)
        
        # Calculate slope and intercept
        n = len(x)
        xy_sum = np.sum(x * y)
        x_sum = np.sum(x)
        y_sum = np.sum(y)
        x_squared_sum = np.sum(x ** 2)
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum ** 2)
        intercept = (y_sum - slope * x_sum) / n
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_total = np.sum((y - np.mean(y)) ** 2)
        ss_residual = np.sum((y - y_pred) ** 2)
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        
        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared
        }
    
    def _get_regime_action(self, regime: MarketRegime, metrics: Dict[str, float]) -> Tuple[str, float, str]:
        """Determine appropriate action based on detected regime
        
        Args:
            regime (MarketRegime): Detected market regime
            metrics (Dict[str, float]): Regime detection metrics
            
        Returns:
            Tuple[str, float, str]: Action, confidence, and reason
        """
        if regime == MarketRegime.TRENDING_BULLISH:
            return "buy", 0.8, "Strong bullish trend detected"
        
        elif regime == MarketRegime.TRENDING_BEARISH:
            return "sell", 0.8, "Strong bearish trend detected"
        
        elif regime == MarketRegime.RANGING:
            # In ranging markets, suggest mean reversion strategies
            if metrics["price_change"] > 0 and metrics["price_change"] > metrics["volatility"]:
                return "sell", 0.6, "Range-bound market near upper bound"
            elif metrics["price_change"] < 0 and abs(metrics["price_change"]) > metrics["volatility"]:
                return "buy", 0.6, "Range-bound market near lower bound"
            else:
                return "hold", 0.5, "Range-bound market in middle zone"
        
        elif regime == MarketRegime.VOLATILE:
            return "hold", 0.7, "High volatility detected, reducing exposure"
        
        elif regime == MarketRegime.BREAKOUT:
            if metrics["breakout_up"]:
                return "buy", 0.7, "Bullish breakout detected"
            elif metrics["breakout_down"]:
                return "sell", 0.7, "Bearish breakdown detected"
            else:
                return "hold", 0.5, "Potential breakout, direction unclear"
        
        elif regime == MarketRegime.REVERSAL:
            if metrics["trend_direction"] > 0:  # Previous trend was up
                return "sell", 0.6, "Potential trend reversal from bullish to bearish"
            else:  # Previous trend was down
                return "buy", 0.6, "Potential trend reversal from bearish to bullish"
        
        else:  # UNKNOWN
            return "hold", 0.5, "No clear market regime detected"