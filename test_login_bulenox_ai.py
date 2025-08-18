import os
import logging
from bulenox_ai_selenium import login_bulenox_ai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_login():
    """Test the login_bulenox_ai function"""
    try:
        # Log in
        logger.info("Starting login test")
        bulenox = login_bulenox_ai(
            debug=True  # Enable debug mode for more logging
        )
        
        # If we get here, login was successful
        logger.info("Login successful!")
        
        # Test navigation
        logger.info("Testing navigation")
        bulenox.navigate_to_trading()
        
        # Take a screenshot
        bulenox._take_screenshot("test_login_success")
        
        # Close the browser
        bulenox.close()
        
        return True
    except Exception as e:
        logger.exception(f"Login test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    if success:
        print("✅ Login test passed!")
    else:
        print("❌ Login test failed!")