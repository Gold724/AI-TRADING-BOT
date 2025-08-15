# ai_evolution_system.py

import json
import logging
import os
import datetime
from typing import Dict, List, Any, Optional

# Import the AI Strategy Evolution System components
from strategy_brain import StrategyBrain, get_strategy_recommendation
from reinforce_trader import ReinforceTrader, get_reinforcement_action
from sentiment_sensor import SentimentSensor, adjust_confidence
from strategy_optimizer import StrategyOptimizer, run_optimization

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ai_evolution_system")


class AIEvolutionSystem:
    """AI Strategy Evolution System (SE-Layer)
    
    This class integrates all components of the AI Strategy Evolution System:
    - strategy_brain.py: Memory and strategy evolver
    - reinforce_trader.py: Reinforcement learning for trade decisions
    - sentiment_sensor.py: Real-time news and sentiment analysis
    - strategy_optimizer.py: Weekly AI-based weight adjuster
    
    It provides a unified interface for the Sentinel trading system to leverage
    the AI-powered strategy evolution capabilities.
    """

    def __init__(self):
        """Initialize the AI Evolution System"""
        # Initialize components
        self.strategy_brain = StrategyBrain()
        self.reinforce_trader = ReinforceTrader()
        self.sentiment_sensor = SentimentSensor()
        self.strategy_optimizer = StrategyOptimizer()
        
        logger.info("AI Strategy Evolution System initialized")

    def evaluate_trade_opportunity(self, strategy: str, pair: str, 
                                  confidence: int, market_condition: str,
                                  time_of_day: str) -> Dict:
        """Evaluate a trade opportunity using the AI Evolution System

        Args:
            strategy (str): Trading strategy name
            pair (str): Currency pair
            confidence (int): Base confidence score (0-100)
            market_condition (str): Current market condition
            time_of_day (str): Current trading session

        Returns:
            Dict: Evaluation results with adjusted confidence and recommendations
        """
        try:
            logger.info(f"Evaluating trade opportunity: {strategy} on {pair} with confidence {confidence}")
            
            # Step 1: Get strategy recommendation from strategy brain
            brain_recommendation = self.strategy_brain.get_strategy_recommendation(
                strategy, pair, market_condition
            )
            
            # Step 2: Adjust confidence based on sentiment data
            adjusted_confidence, sentiment_reason = self.sentiment_sensor.adjust_confidence(
                pair, confidence
            )
            
            # Step 3: Get reinforcement learning action recommendation
            rl_action, rl_confidence = self.reinforce_trader.get_action(
                strategy, pair, time_of_day, adjusted_confidence, 
                self.sentiment_sensor.get_news_level(pair)
            )
            
            # Step 4: Combine all insights for final decision
            brain_weight = brain_recommendation.get("weight", 100) / 100
            brain_confidence_boost = brain_recommendation.get("confidence_boost", False)
            
            # Apply brain weight to adjusted confidence
            weighted_confidence = adjusted_confidence * brain_weight
            
            # Apply confidence boost if applicable
            if brain_confidence_boost:
                weighted_confidence = min(100, weighted_confidence * 1.1)  # 10% boost
            
            # Final confidence is average of weighted confidence and RL confidence
            final_confidence = int((weighted_confidence + rl_confidence) / 2)
            
            # Determine if trade should proceed based on RL action
            proceed_with_trade = rl_action in ["trade", "reduce_risk"]
            
            # Determine risk level
            if rl_action == "reduce_risk":
                risk_level = "reduced"
            else:
                risk_level = "normal"
            
            # Compile evaluation results
            evaluation = {
                "strategy": strategy,
                "pair": pair,
                "original_confidence": confidence,
                "adjusted_confidence": adjusted_confidence,
                "final_confidence": final_confidence,
                "proceed_with_trade": proceed_with_trade,
                "risk_level": risk_level,
                "sentiment_reason": sentiment_reason,
                "brain_recommendation": brain_recommendation,
                "rl_action": rl_action,
                "rl_confidence": rl_confidence,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            
            logger.info(f"Trade evaluation complete: {proceed_with_trade}, confidence: {final_confidence}")
            return evaluation
        
        except Exception as e:
            logger.error(f"Error evaluating trade opportunity: {e}")
            # Return a safe default with original confidence
            return {
                "strategy": strategy,
                "pair": pair,
                "original_confidence": confidence,
                "adjusted_confidence": confidence,
                "final_confidence": confidence,
                "proceed_with_trade": True,  # Default to proceeding
                "risk_level": "normal",
                "error": str(e),
                "timestamp": datetime.datetime.utcnow().isoformat()
            }

    def record_trade_result(self, trade_data: Dict) -> bool:
        """Record trade result for learning and optimization

        Args:
            trade_data (Dict): Trade data including result

        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Recording trade result: {trade_data.get('result')} for {trade_data.get('symbol')}")
            
            # Step 1: Record in strategy brain
            self.strategy_brain.record_trade(trade_data)
            
            # Step 2: Update reinforcement learning model
            self.reinforce_trader.update_q_table(
                trade_data.get("strategy"),
                trade_data.get("symbol"),
                trade_data.get("time_of_day"),
                trade_data.get("confidence", 0),
                trade_data.get("news_nearby", False),
                trade_data.get("result") == "win",
                trade_data.get("profit", 0)
            )
            
            # Step 3: Save reinforcement learning model
            self.reinforce_trader.save_q_table()
            
            return True
        
        except Exception as e:
            logger.error(f"Error recording trade result: {e}")
            return False

    def run_weekly_optimization(self) -> Dict:
        """Run weekly optimization of strategies

        Returns:
            Dict: Optimization results
        """
        try:
            logger.info("Running weekly strategy optimization")
            
            # Run strategy optimizer
            optimization_results = self.strategy_optimizer.run_weekly_optimization()
            
            # Update strategy brain with new weights
            if optimization_results.get("brain_updated", False):
                self.strategy_brain.load_strategy_data()  # Reload from updated file
            
            return optimization_results
        
        except Exception as e:
            logger.error(f"Error running weekly optimization: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.datetime.utcnow().isoformat()
            }

    def get_sentiment_summary(self) -> Dict:
        """Get current market sentiment summary

        Returns:
            Dict: Sentiment summary
        """
        try:
            return self.sentiment_sensor.get_sentiment_summary()
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return {}

    def get_upcoming_events(self, hours: int = 24) -> List[Dict]:
        """Get upcoming economic events

        Args:
            hours (int, optional): Hours to look ahead. Defaults to 24.

        Returns:
            List[Dict]: List of upcoming events
        """
        try:
            return self.sentiment_sensor.get_upcoming_events(hours)
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []

    def get_strategy_performance(self) -> Dict:
        """Get strategy performance metrics

        Returns:
            Dict: Strategy performance data
        """
        try:
            return self.strategy_brain.get_strategy_stats()
        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return {}

    def get_pair_performance(self) -> Dict:
        """Get currency pair performance metrics

        Returns:
            Dict: Pair performance data
        """
        try:
            return self.strategy_brain.get_pair_stats()
        except Exception as e:
            logger.error(f"Error getting pair performance: {e}")
            return {}


# Helper functions
def evaluate_trade(strategy: str, pair: str, confidence: int, 
                  market_condition: str, time_of_day: str) -> Dict:
    """Evaluate a trade opportunity (helper function)

    Args:
        strategy (str): Trading strategy name
        pair (str): Currency pair
        confidence (int): Base confidence score (0-100)
        market_condition (str): Current market condition
        time_of_day (str): Current trading session

    Returns:
        Dict: Evaluation results
    """
    ai_system = AIEvolutionSystem()
    return ai_system.evaluate_trade_opportunity(
        strategy, pair, confidence, market_condition, time_of_day
    )


def record_trade(trade_data: Dict) -> bool:
    """Record trade result (helper function)

    Args:
        trade_data (Dict): Trade data

    Returns:
        bool: Success status
    """
    ai_system = AIEvolutionSystem()
    return ai_system.record_trade_result(trade_data)


def optimize_strategies() -> Dict:
    """Run strategy optimization (helper function)

    Returns:
        Dict: Optimization results
    """
    ai_system = AIEvolutionSystem()
    return ai_system.run_weekly_optimization()


# For testing
if __name__ == "__main__":
    # Create an instance of the AI Evolution System
    ai_system = AIEvolutionSystem()
    
    # Test trade evaluation
    print("Testing trade evaluation...")
    evaluation = ai_system.evaluate_trade_opportunity(
        strategy="OTE",
        pair="EURUSD",
        confidence=75,
        market_condition="trending",
        time_of_day="london_open"
    )
    
    # Print evaluation results
    print("\nTrade Evaluation Results:")
    print(f"Strategy: {evaluation['strategy']}")
    print(f"Pair: {evaluation['pair']}")
    print(f"Original Confidence: {evaluation['original_confidence']}")
    print(f"Adjusted Confidence: {evaluation['adjusted_confidence']}")
    print(f"Final Confidence: {evaluation['final_confidence']}")
    print(f"Proceed with Trade: {evaluation['proceed_with_trade']}")
    print(f"Risk Level: {evaluation['risk_level']}")
    print(f"Sentiment Reason: {evaluation['sentiment_reason']}")
    print(f"RL Action: {evaluation['rl_action']}")
    
    # Test recording a trade result
    print("\nTesting trade recording...")
    trade_data = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "symbol": "EURUSD",
        "strategy": "OTE",
        "confidence": 80,
        "news_nearby": False,
        "result": "win",
        "pips": 15.5,
        "profit": 155.0,
        "entry_price": 1.0950,
        "exit_price": 1.1105,
        "direction": "long",
        "risk_reward": 3.1,
        "market_condition": "trending",
        "time_of_day": "london_open",
        "trade_duration_minutes": 240
    }
    
    success = ai_system.record_trade_result(trade_data)
    print(f"Trade recording success: {success}")
    
    # Test sentiment summary
    print("\nTesting sentiment summary...")
    sentiment = ai_system.get_sentiment_summary()
    
    print("Sentiment Summary:")
    print(f"Bullish Pairs: {', '.join(sentiment.get('bullish_pairs', []))}")
    print(f"Bearish Pairs: {', '.join(sentiment.get('bearish_pairs', []))}")
    print(f"High Volatility Pairs: {', '.join(sentiment.get('high_volatility_pairs', []))}")
    
    # Test upcoming events
    print("\nTesting upcoming events...")
    events = ai_system.get_upcoming_events(hours=12)
    
    print("Upcoming Events (next 12 hours):")
    for event in events[:3]:  # Show first 3 events
        print(f"  {event.get('time')} - {event.get('currency')} {event.get('event')} (Impact: {event.get('impact')})")
    
    # Test strategy optimization
    print("\nTesting strategy optimization...")
    optimization = ai_system.run_weekly_optimization()
    
    print("Optimization Results:")
    print(f"Success: {optimization.get('success', False)}")
    
    # Print some recommendations
    recommendations = optimization.get('recommendations', {})
    strategy_adjustments = recommendations.get('strategy_adjustments', [])
    
    if strategy_adjustments:
        print("\nStrategy Adjustment Recommendations:")
        for adjustment in strategy_adjustments[:3]:  # Show first 3 adjustments
            print(f"  - {adjustment}")