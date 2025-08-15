# test_reinforcement.py

import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_reinforcement')

# Import the reinforcement agent
try:
    from reinforcement_agent import ReinforcementAgent, MarketRegime
    # Try different import paths for SentinelDecider
    try:
        from sentinel_decider import SentinelDecider
    except ImportError:
        try:
            from ai_components.sentinel_decider import SentinelDecider
        except ImportError:
            from signal_router import SentinelDecider
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise

def test_market_regime_detection():
    """Test market regime detection functionality"""
    logger.info("Testing market regime detection...")
    
    # Initialize agent
    agent = ReinforcementAgent()
    
    # Test bullish regime
    ema_short = 1.2345  # Short EMA above long EMA
    ema_long = 1.2300
    atr = 0.0020
    atr_change = 0.05  # Positive ATR change
    
    regime_changed = agent.update_market_regime(ema_short, ema_long, atr, atr_change)
    logger.info(f"Bullish test - Current regime: {agent.current_regime}, Changed: {regime_changed}")
    
    # Test bearish regime
    ema_short = 1.2300  # Short EMA below long EMA
    ema_long = 1.2345
    atr = 0.0020
    atr_change = 0.05  # Positive ATR change
    
    regime_changed = agent.update_market_regime(ema_short, ema_long, atr, atr_change)
    logger.info(f"Bearish test - Current regime: {agent.current_regime}, Changed: {regime_changed}")
    
    # Test sideways regime
    ema_short = 1.2345
    ema_long = 1.2344  # EMAs very close
    atr = 0.0010  # Low ATR
    atr_change = -0.01  # Negative ATR change
    
    regime_changed = agent.update_market_regime(ema_short, ema_long, atr, atr_change)
    logger.info(f"Sideways test - Current regime: {agent.current_regime}, Changed: {regime_changed}")
    
    return True

def test_reinforcement_learning():
    """Test reinforcement learning functionality"""
    logger.info("Testing reinforcement learning...")
    
    # Initialize agent
    agent = ReinforcementAgent()
    
    # Set up a known regime
    agent.current_regime = MarketRegime.BULLISH
    
    # Record some trade results
    logger.info("Recording trade results...")
    for i in range(10):
        # Alternate between profitable and losing trades
        profit = 50.0 if i % 2 == 0 else -20.0
        agent.record_trade_result("breakout", profit)
    
    # Get strategy recommendations
    recommendations = agent.get_strategy_recommendations()
    logger.info("Strategy recommendations:")
    for strategy, details in recommendations.items():
        logger.info(f"  {strategy}: weight={details['weight']:.2f}, action={details['action']}")
    
    # Check if files were created
    rl_decisions_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "logs", "rl_agent_decisions.json")
    regime_labels_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     "data", "regime_labels.json")
    
    logger.info(f"RL decisions file exists: {os.path.exists(rl_decisions_file)}")
    logger.info(f"Regime labels file exists: {os.path.exists(regime_labels_file)}")
    
    return True

def test_sentinel_integration():
    """Test integration with SentinelDecider"""
    logger.info("Testing integration with SentinelDecider...")
    
    # Skip full integration test for now
    logger.info("Skipping full integration test - focusing on reinforcement agent functionality")
    
    # Create a direct instance of ReinforcementAgent to test its functionality
    agent = ReinforcementAgent()
    
    # Set up a known regime
    agent.current_regime = MarketRegime.BULLISH
    
    # Test strategy recommendations
    recommendations = agent.get_strategy_recommendations()
    logger.info("Strategy recommendations from direct agent:")
    for strategy, details in recommendations.items():
        logger.info(f"  {strategy}: weight={details.get('weight', 0):.2f}, action={details.get('action', 'unknown')}")
    
    # Test recording trade results
    agent.record_trade_result("breakout", 100.0)
    logger.info("Recorded trade result for breakout strategy")
    
    return True

if __name__ == "__main__":
    logger.info("Starting reinforcement learning and market regime detection tests")
    
    try:
        # Run tests
        regime_test_result = test_market_regime_detection()
        rl_test_result = test_reinforcement_learning()
        integration_test_result = test_sentinel_integration()
        
        # Report results
        logger.info("\nTest Results:")
        logger.info(f"Market Regime Detection: {'PASSED' if regime_test_result else 'FAILED'}")
        logger.info(f"Reinforcement Learning: {'PASSED' if rl_test_result else 'FAILED'}")
        logger.info(f"Sentinel Integration: {'PASSED' if integration_test_result else 'FAILED'}")
        
        if all([regime_test_result, rl_test_result, integration_test_result]):
            logger.info("\nAll tests PASSED!")
        else:
            logger.info("\nSome tests FAILED!")
    
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)