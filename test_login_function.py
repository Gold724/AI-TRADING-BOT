import logging
import os
import sys
import time
from datetime import datetime

# Add parent directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from login_bulenox import login_bulenox_with_profile, update_heartbeat_status

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_login_function")


def custom_update_status(status):
    """Custom status update function that avoids emoji characters"""
    # Remove emoji characters that cause encoding issues
    status = status.replace('✅', '[SUCCESS]')
    status = status.replace('❌', '[FAILED]')
    status = status.replace('⚠️', '[WARNING]')
    status = status.replace('🔄', '[PROCESSING]')
    status = status.replace('🔑', '[AUTH]')
    
    logger.info(status)
    
    # Only call the original function if it's safe (no emoji)
    try:
        update_heartbeat_status(status)
    except Exception as e:
        logger.warning(f"Could not update heartbeat status: {e}")


def test_login(manual_login=False):
    """
    Test the login_bulenox_with_profile function
    
    This function:
    1. Attempts to log into Bulenox using a saved Chrome profile
    2. Verifies if login was successful
    3. Takes a screenshot of the dashboard if login is successful
    4. Closes the browser
    
    Args:
        manual_login (bool): If True, will prompt user to manually log in
    """
    logger.info("Starting login test")
    custom_update_status("[PROCESSING] Starting login test...")
    
    # Attempt to login with debug mode enabled for screenshots
    driver = login_bulenox_with_profile(debug=True)
    
    # If manual login is enabled, give the user time to log in manually
    if manual_login and driver:
        logger.info("Manual login mode enabled")
        print("\n==== MANUAL LOGIN REQUIRED ====\n")
        print("Please log in manually with your credentials")
        print("Username: Use your Bulenox username")
        print("Password: Use your Bulenox password")
        print("\nWaiting 30 seconds for manual login to complete...")
        time.sleep(30)  # Give user time to log in manually
    
    if driver:
        try:
            # Verify we're on the dashboard or trading page
            current_url = driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            # Check if we're logged in by looking for expected URL patterns
            if any(pattern in current_url for pattern in ["dashboard", "trading", "member/home"]):
                logger.info("✅ Login successful - Verified by URL")
                custom_update_status("[SUCCESS] Login successful - Verified by URL")
                
                # Take a screenshot of the dashboard
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshots_dir, f"dashboard_{timestamp}.png")
                
                driver.save_screenshot(screenshot_path)
                logger.info(f"Dashboard screenshot saved to: {screenshot_path}")
                
                # Wait a moment to view the dashboard
                logger.info("Waiting 5 seconds to view the dashboard...")
                time.sleep(5)
                
                return True
            else:
                logger.error("[FAILED] Login appears to have failed - Unexpected URL")
                custom_update_status("[FAILED] Login appears to have failed - Unexpected URL")
                return False
                
        except Exception as e:
            logger.error(f"Error during login verification: {e}")
            custom_update_status(f"[FAILED] Error during login verification: {str(e)[:50]}...")
            return False
        finally:
            # Always close the browser
            logger.info("Closing browser")
            driver.quit()
    else:
        logger.error("[FAILED] Login failed - No driver returned")
        custom_update_status("[FAILED] Login failed - No driver returned")
        return False


if __name__ == "__main__":
    # Check for command line arguments
    manual_mode = False
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['-m', '--manual', 'manual']:
        manual_mode = True
        print("Running in manual login mode")
    
    result = test_login(manual_login=manual_mode)
    
    if result:
        print("[SUCCESS] Login test PASSED")
        exit(0)
    else:
        print("[FAILED] Login test FAILED")
        print("\nTry running with manual login mode: python test_login_function.py --manual")
        exit(1)