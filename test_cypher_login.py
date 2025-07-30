import os
import time
import logging
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from backend.executor_bulenox import BulenoxExecutor

# Load environment variables
load_dotenv()

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "cypher_test.log")),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("cypher_test")

def test_cypher_login():
    """Test the CYPHER login functionality with profile reuse"""
    logger.info("=== CYPHER LOGIN TEST STARTED ===")
    
    # Create screenshots directory if it doesn't exist
    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Test 1: Direct login with BulenoxExecutor
    logger.info("Test 1: Testing BulenoxExecutor login via health check")
    try:
        executor = BulenoxExecutor()
        health_result = executor.health()
        logger.info(f"Health check result: {'PASSED' if health_result else 'FAILED'}")
        
        if health_result:
            logger.info("✅ Test 1 PASSED: BulenoxExecutor login successful")
        else:
            logger.error("❌ Test 1 FAILED: BulenoxExecutor login failed")
    except Exception as e:
        logger.error(f"❌ Test 1 FAILED with exception: {str(e)}")
    
    # Test 2: Cookie persistence test
    logger.info("Test 2: Testing cookie persistence")
    try:
        # First login should create cookies
        executor1 = BulenoxExecutor()
        health_result1 = executor1.health()
        logger.info(f"First login result: {'PASSED' if health_result1 else 'FAILED'}")
        
        # Second login should use cookies
        logger.info("Creating second executor to test cookie reuse")
        executor2 = BulenoxExecutor()
        
        # Track time for cookie-based login
        start_time = time.time()
        health_result2 = executor2.health()
        end_time = time.time()
        login_time = end_time - start_time
        
        logger.info(f"Second login result: {'PASSED' if health_result2 else 'FAILED'}")
        logger.info(f"Login time with cookies: {login_time:.2f} seconds")
        
        if health_result2 and login_time < 10:  # Assuming cookie login should be faster
            logger.info("✅ Test 2 PASSED: Cookie persistence working")
        else:
            logger.warning("⚠️ Test 2 INCONCLUSIVE: Cookie login may not be working optimally")
    except Exception as e:
        logger.error(f"❌ Test 2 FAILED with exception: {str(e)}")
    
    # Test 3: Profile reuse test
    logger.info("Test 3: Testing Chrome profile reuse")
    try:
        # Get profile paths from environment or use defaults
        chrome_profile_path = os.getenv('BULENOX_PROFILE_PATH', 'C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data')
        chrome_profile_name = os.getenv('BULENOX_PROFILE_NAME', 'Profile 15')
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH', 'D:\\aibot\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')
        
        # Set up Chrome options with the profile
        options = Options()
        options.add_argument('--start-maximized')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-data-dir={chrome_profile_path}')
        options.add_argument(f'profile-directory={chrome_profile_name}')
        
        # Initialize the driver
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to Bulenox
        driver.get("https://bulenox.com/member/login")
        time.sleep(3)
        
        # Take screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshot_dir, f"profile_test_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")
        
        # Check if already logged in
        dashboard_urls = ["dashboard", "trading", "member/home", "account", "platform", "terminal", "market"]
        if any(url_part in driver.current_url for url_part in dashboard_urls):
            logger.info(f"Already logged in, current URL: {driver.current_url}")
            logger.info("✅ Test 3 PASSED: Chrome profile reuse successful")
        else:
            logger.warning(f"Not logged in automatically, current URL: {driver.current_url}")
            logger.warning("⚠️ Test 3 INCONCLUSIVE: Chrome profile may not contain login session")
        
        # Clean up
        driver.quit()
    except Exception as e:
        logger.error(f"❌ Test 3 FAILED with exception: {str(e)}")
    
    logger.info("=== CYPHER LOGIN TEST COMPLETED ===")

def test_trade_execution():
    """Test the trade execution functionality"""
    logger.info("=== CYPHER TRADE EXECUTION TEST STARTED ===")
    
    try:
        # Create a test signal
        test_signal = {
            'symbol': 'BTCUSD',
            'direction': 'BUY',
            'amount': 0.01  # Small amount for testing
        }
        
        # Initialize executor with the test signal
        executor = BulenoxExecutor(signal=test_signal, stopLoss=5, takeProfit=10)
        
        # Execute the trade
        result = executor.execute_trade()
        
        if result:
            logger.info("✅ Trade execution test PASSED")
        else:
            logger.error("❌ Trade execution test FAILED")
    except Exception as e:
        logger.error(f"❌ Trade execution test FAILED with exception: {str(e)}")
    
    logger.info("=== CYPHER TRADE EXECUTION TEST COMPLETED ===")

if __name__ == "__main__":
    print("CYPHER: Cybernetic Yield Protocol for Harmonized Entry & Routing")
    print("Running login tests...")
    test_cypher_login()
    
    # Uncomment to test trade execution
    # print("\nRunning trade execution test...")
    # test_trade_execution()