import logging
import os
import sys
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("direct_login_test")

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
        return filepath
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return None


def test_direct_login():
    """Test direct login to Bulenox"""
    logger.info("Starting direct login test")
    
    driver = None
    try:
        # Set up Chrome options
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Initialize Chrome driver
        logger.info("Initializing Chrome driver")
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            logger.error(f"Error initializing Chrome driver: {e}")
            logger.info("Trying with ChromeDriverManager...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

        driver.set_page_load_timeout(30)

        # Navigate to login page
        login_url = "https://bulenox.projectx.com/login"
        logger.info(f"Navigating to login page: {login_url}")
        driver.get(login_url)
        time.sleep(2)  # Wait for page to load

        # Log current page info
        logger.info(f"Current URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")

        # Take screenshot of login page
        take_screenshot(driver, "login_page")

        # Check if we need manual login
        print("\n==== MANUAL LOGIN REQUIRED ====\n")
        print("Please log in manually with your credentials")
        print("Username: Use your Bulenox username")
        print("Password: Use your Bulenox password")
        print("\nWaiting 30 seconds for manual login to complete...")
        
        # Wait for manual login
        time.sleep(30)
        
        # Take screenshot after login attempt
        take_screenshot(driver, "after_login")
        
        # Check current URL
        current_url = driver.current_url
        logger.info(f"Current URL after login: {current_url}")
        
        # Check if login was successful
        if "login" not in current_url.lower():
            logger.info("[SUCCESS] Login successful - Verified by URL")
            print("\n[SUCCESS] Login successful!\n")
            
            # Wait a moment to view the dashboard
            print("Waiting 5 seconds to view the dashboard...")
            time.sleep(5)
            
            return True
        else:
            logger.error("[FAILED] Login appears to have failed - Still on login page")
            print("\n[FAILED] Login appears to have failed - Still on login page\n")
            return False
            
    except Exception as e:
        logger.error(f"Error during login test: {e}")
        return False
    finally:
        # Always close the browser
        if driver:
            logger.info("Closing browser")
            driver.quit()


if __name__ == "__main__":
    result = test_direct_login()
    
    if result:
        print("[SUCCESS] Login test PASSED")
        exit(0)
    else:
        print("[FAILED] Login test FAILED")
        exit(1)