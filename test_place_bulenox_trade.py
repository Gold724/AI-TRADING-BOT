import os
import logging
from bulenox_ai_selenium import place_bulenox_trade
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_place_trade():
    """Test the place_bulenox_trade function"""
    try:
        # Define trade parameters
        symbol = "EURUSD"  # Example symbol
        side = "buy"       # buy or sell
        quantity = 0.01    # Minimal quantity for testing
        stop_loss = None   # Optional
        take_profit = None # Optional
        
        # Place trade
        logger.info(f"Testing place_bulenox_trade for {symbol} {side}")
        success = place_bulenox_trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            debug=True  # Enable debug mode for more logging
        )
        
        if success:
            logger.info("Trade placed successfully!")
        else:
            logger.error("Failed to place trade")
        
        return success
    except Exception as e:
        logger.exception(f"Trade test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_place_trade()
    if success:
        print("✅ Trade test passed!")
    else:
        print("❌ Trade test failed!")