# test_phase6_multi_agent.py

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_phase6_multi_agent')

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the SentinelDecider and other required modules
from ai_components.sentinel_decider import SentinelDecider


def create_test_signal() -> Dict[str, Any]:
    """Create a test trading signal for the multi-agent system"""
    return {
        "pair": "BTC/USD",
        "strategy": "trend_following_v1",
        "trade_type": "LONG",
        "entry_price": 50000,
        "stop_loss": 49000,
        "take_profit": 52000,
        "confidence": 85,
        "indicators": {
            "rsi": 65,
            "macd": "bullish",
            "ema_cross": True
        },
        "news_sentiment": "positive",
        "timestamp": datetime.now().isoformat(),
        "volume": 1000,
        "volatility": 0.0012,
        "type": "entry"
    }


def test_multi_agent_system():
    """Test the multi-agent system for Phase 6"""
    logger.info("Starting Phase 6 Multi-Agent Strategy Governance test")
    
    # Initialize the SentinelDecider with Phase 6
    try:
        decider = SentinelDecider(phase="6")
        logger.info("SentinelDecider initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SentinelDecider: {e}")
        return False
    
    # Create a test signal
    signal = create_test_signal()
    
    # Get a decision from the multi-agent system
    try:
        logger.info("Requesting decision from multi-agent system...")
        decision = decider.decide_trade(signal)
        logger.info(f"Decision received: {json.dumps(decision, indent=2)}")
        
        # Basic validation of decision
        if isinstance(decision, dict) and "action" in decision:
            logger.info(f"Decision action: {decision['action']}")
            logger.info("Phase 6 Multi-Agent Strategy Governance test completed successfully")
            return True
        else:
            logger.error(f"Invalid decision format: {decision}")
            return False
    except Exception as e:
        logger.error(f"Error getting decision: {e}")
        return False


def main():
    """Main function to run the test"""
    try:
        result = test_multi_agent_system()
        if result:
            logger.info("✅ All tests passed!")
            return 0
        else:
            logger.error("❌ Tests failed!")
            return 1
    except Exception as e:
        logger.exception(f"Error during test: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())