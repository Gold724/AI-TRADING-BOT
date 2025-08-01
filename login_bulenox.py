from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('login_bulenox')

# Load environment variables
load_dotenv()

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")

def update_heartbeat_status(status, session_active=True):
    """
    Update the heartbeat status file with current status and timestamp
    
    Args:
        status (str): The current status message
        session_active (bool): Flag indicating if a trading session is active
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        
        # Write to heartbeat status file
        with open(HEARTBEAT_STATUS_FILE, 'w') as f:
            f.write(f"{status}\n{timestamp}\n{json.dumps({'session_active': session_active})}")
            
        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")

def login_bulenox_with_profile(debug=False):
    """Login to Bulenox using Chrome profile
    
    Args:
        debug (bool): Enable debug mode with additional logging and screenshots
        
    Returns:
        WebDriver: Selenium WebDriver instance with active Bulenox session, or None if login fails
    """
    # Update heartbeat status
    update_heartbeat_status("🔑 Initializing login process with Chrome profile...")
    # Get profile paths from environment variables or use defaults
    profile_path = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data")
    profile_name = os.getenv('BULENOX_PROFILE_NAME', "Profile 13")
    
    # Create screenshots directory if debug mode is enabled
    if debug:
        screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument(f"--profile-directory={profile_name}")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Create Chrome driver without specifying service path (uses WebDriver Manager)
    logger.info("Initializing Chrome with user profile...")
    update_heartbeat_status("🔄 Initializing Chrome with user profile...")
    driver = None
    
    try:
        # First try with WebDriver Manager
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        logger.error(f"Error using WebDriver Manager: {e}")
        logger.info("Trying alternative approach...")
        update_heartbeat_status("⚠️ Chrome initialization failed, trying alternative approach...")
        
        # Try with explicit import of ChromeDriverManager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e2:
            logger.error(f"Error with ChromeDriverManager: {e2}")
            logger.info("Trying with default Chrome...")
            update_heartbeat_status("⚠️ ChromeDriverManager failed, trying with default Chrome...")
            
            # Last resort - try with minimal options
            try:
                minimal_options = Options()
                minimal_options.add_argument("--start-maximized")
                driver = webdriver.Chrome(options=minimal_options)
            except Exception as e3:
                logger.error(f"All Chrome initialization attempts failed: {e3}")
                update_heartbeat_status("❌ All Chrome initialization attempts failed")
                return None
    
    # Navigate to Bulenox login page
    try:
        logger.info("Navigating to Bulenox login page...")
        update_heartbeat_status("🔄 Navigating to Bulenox login page...")
        driver.get("https://bulenox.projectx.com/login")
        
        # Take screenshot if debug mode is enabled
        if debug:
            _take_screenshot(driver, "login_page")
        
        # Wait for login page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
        )
        
        # Check if already logged in by looking for dashboard elements
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-element"))
            )
            logger.info("Already logged in to Bulenox")
            update_heartbeat_status("✅ Already logged in to Bulenox")
            return driver
        except TimeoutException:
            # Not logged in yet, which is expected
            pass
        
        # Check if login form is present
        try:
            login_form = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form"))
            )
            logger.info("Login form found, already authenticated via Chrome profile")
            update_heartbeat_status("🔑 Login form found, already authenticated via Chrome profile")
            
            # Take screenshot if debug mode is enabled
            if debug:
                _take_screenshot(driver, "authenticated_login")
            
            # Wait for dashboard to load after automatic login
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-element"))
                )
                logger.info("Successfully logged in to Bulenox")
                update_heartbeat_status("✅ Successfully logged in to Bulenox")
                return driver
            except TimeoutException:
                logger.warning("Timed out waiting for dashboard to load")
                update_heartbeat_status("⚠️ Timed out waiting for dashboard to load, but might still be logged in")
                # Continue anyway, as we might still be logged in
                return driver
                
        except TimeoutException:
            logger.error("Login form not found")
            update_heartbeat_status("❌ Login form not found")
            if debug:
                _take_screenshot(driver, "login_form_not_found")
            driver.quit()
            return None
            
    except Exception as e:
        logger.error(f"Error during login process: {e}")
        update_heartbeat_status(f"❌ Error during login process: {str(e)[:50]}...")
        if driver:
            if debug:
                _take_screenshot(driver, "login_error")
            driver.quit()
        return None

def _take_screenshot(driver, name):
    """Take a screenshot"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(os.getcwd(), "logs", "screenshots", filename)
        
        driver.save_screenshot(filepath)
        logger.info(f"Screenshot saved: {filepath}")
        
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")

if __name__ == "__main__":
    driver = login_bulenox_with_profile(debug=True)
    
    if driver:
        logger.info("Login successful. Press Enter to close browser...")
        input("🔒 Press Enter to close browser...")
        driver.quit()
    else:
        logger.error("Login failed.")
        print("❌ Login failed. Check logs for details.")
