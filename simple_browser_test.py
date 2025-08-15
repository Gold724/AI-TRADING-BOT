import logging
import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simple_browser_test")

# Create screenshots directory
screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)


def take_screenshot(driver, name):
    """Take a screenshot"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)

        driver.save_screenshot(filepath)
        logger.info(f"Screenshot saved: {filepath}")
        print(f"Screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return None


def test_browser():
    """Test browser functionality"""
    logger.info("Starting browser test")
    print("Starting browser test...")
    
    driver = None
    try:
        # Set up Chrome options
        options = Options()
        options.add_argument("--start-maximized")
        
        # Initialize Chrome driver
        logger.info("Initializing Chrome driver")
        print("Initializing Chrome driver...")
        
        try:
            driver = webdriver.Chrome(options=options)
            print("Chrome initialized successfully using default method")
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            print("Trying with ChromeDriverManager...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("Chrome initialized successfully using ChromeDriverManager")

        # Navigate to a test page
        test_url = "https://www.google.com"
        logger.info(f"Navigating to test page: {test_url}")
        print(f"Navigating to test page: {test_url}")
        driver.get(test_url)
        time.sleep(2)  # Wait for page to load

        # Log current page info
        logger.info(f"Current URL: {driver.current_url}")
        print(f"Current URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")
        print(f"Page title: {driver.title}")

        # Take screenshot of test page
        take_screenshot(driver, "test_page")
        
        print("\nBrowser test successful!")
        print("Now trying to navigate to Bulenox...")
        
        # Try to navigate to Bulenox
        bulenox_url = "https://bulenox.projectx.com/login"
        logger.info(f"Navigating to Bulenox: {bulenox_url}")
        print(f"Navigating to Bulenox: {bulenox_url}")
        driver.get(bulenox_url)
        time.sleep(3)  # Wait for page to load
        
        # Log current page info
        logger.info(f"Current URL: {driver.current_url}")
        print(f"Current URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")
        print(f"Page title: {driver.title}")
        
        # Take screenshot of Bulenox page
        take_screenshot(driver, "bulenox_page")
        
        print("\nTest completed successfully!")
        print("Press Enter to close the browser...")
        input()
        
        return True
            
    except Exception as e:
        logger.error(f"Error during browser test: {e}")
        print(f"Error during browser test: {e}")
        return False
    finally:
        # Always close the browser
        if driver:
            logger.info("Closing browser")
            print("Closing browser...")
            driver.quit()


if __name__ == "__main__":
    result = test_browser()
    
    if result:
        print("Browser test PASSED")
        exit(0)
    else:
        print("Browser test FAILED")
        exit(1)