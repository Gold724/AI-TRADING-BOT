import os
import sys
import time
import logging
import datetime
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Add the parent directory to sys.path to import the executor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.executor_bulenox import BulenoxExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bulenox_login_test.log')
    ]
)
logger = logging.getLogger('bulenox_login_test')

# Create screenshots directory if it doesn't exist
os.makedirs('screenshots', exist_ok=True)

def test_direct_login():
    """Test direct login to Bulenox using Selenium without the executor"""
    logger.info("[TEST] Starting direct login test")
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
        logger.info("[TEST] Initializing Chrome driver")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        
        # Navigate to login page
        login_url = "https://bulenox.com/member/login"
        logger.info(f"[TEST] Navigating to login page: {login_url}")
        driver.get(login_url)
        time.sleep(2)  # Wait for page to load
        
        # Log current page info
        logger.info(f"[TEST] Current URL: {driver.current_url}")
        logger.info(f"[TEST] Page title: {driver.title}")
        
        # Take screenshot of login page
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/direct_login_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"[TEST] Login page screenshot saved to: {screenshot_path}")
        
        # Check for CAPTCHA
        try:
            captcha_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha') or contains(@class, 'g-recaptcha')]")
            if captcha_elements:
                logger.error(f"[TEST] CAPTCHA detected on login page")
                for element in captcha_elements:
                    logger.error(f"[TEST] CAPTCHA element: {element.get_attribute('outerHTML')}")
        except Exception as e:
            logger.warning(f"[TEST] Could not check for CAPTCHA: {str(e)}")
        
        # Find username field
        username_field = None
        username_selectors = [
            (By.ID, "amember-login"),
            (By.NAME, "amember_login"),
            (By.ID, "email"),
            (By.NAME, "userName"),
            (By.NAME, "username"),
            (By.NAME, "user"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@placeholder='Username' or @placeholder='Email' or @placeholder='Login']")
        ]
        
        for by_method, selector in username_selectors:
            try:
                username_field = driver.find_element(by_method, selector)
                logger.info(f"[TEST] Found username field with selector: {by_method}={selector}")
                break
            except NoSuchElementException:
                continue
        
        if not username_field:
            logger.error("[TEST] Username field not found")
            return False
        
        # Find password field
        password_field = None
        password_selectors = [
            (By.ID, "amember-pass"),
            (By.NAME, "amember_pass"),
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.NAME, "pass"),
            (By.NAME, "pwd"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@type='password']")
        ]
        
        for by_method, selector in password_selectors:
            try:
                password_field = driver.find_element(by_method, selector)
                logger.info(f"[TEST] Found password field with selector: {by_method}={selector}")
                break
            except NoSuchElementException:
                continue
        
        if not password_field:
            logger.error("[TEST] Password field not found")
            return False
        
        # Find the login form
        try:
            form_element = username_field.find_element(By.XPATH, "./ancestor::form")
            logger.info(f"[TEST] Found login form")
            form_action = form_element.get_attribute('action')
            form_method = form_element.get_attribute('method')
            logger.info(f"[TEST] Form action: {form_action}, method: {form_method}")
            
            # Check for hidden fields in the form
            hidden_fields = form_element.find_elements(By.XPATH, ".//input[@type='hidden']")
            if hidden_fields:
                logger.info(f"[TEST] Found {len(hidden_fields)} hidden fields in login form")
                for field in hidden_fields:
                    name = field.get_attribute('name')
                    value = field.get_attribute('value')
                    logger.info(f"[TEST] Hidden field: name={name}, value={value}")
        except Exception as e:
            logger.warning(f"[TEST] Could not check form details: {str(e)}")
        
        # Get credentials from environment variables
        username = os.getenv('BULENOX_USERNAME')
        password = os.getenv('BULENOX_PASSWORD')
        
        if not username or not password:
            logger.error("[TEST] Missing credentials. Set BULENOX_USERNAME and BULENOX_PASSWORD environment variables.")
            return False
        
        # Enter credentials
        username_field.clear()
        username_field.send_keys(username)
        logger.info(f"[TEST] Entered username: {username}")
        
        password_field.clear()
        password_field.send_keys(password)
        logger.info("[TEST] Entered password")
        
        # Find submit button
        submit_button = None
        submit_selectors = [
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Login') or contains(text(), 'SIGN IN') or contains(text(), 'LOG IN')]"),
            (By.XPATH, "//input[contains(@value, 'Sign in') or contains(@value, 'Login')]"),
            (By.XPATH, "//form//button"),
            (By.CSS_SELECTOR, ".login-button"),
            (By.CSS_SELECTOR, ".btn-login"),
            (By.CSS_SELECTOR, ".btn-primary")
        ]
        
        for by_method, selector in submit_selectors:
            try:
                submit_button = driver.find_element(by_method, selector)
                logger.info(f"[TEST] Found submit button with selector: {by_method}={selector}")
                break
            except NoSuchElementException:
                continue
        
        if not submit_button:
            logger.error("[TEST] Submit button not found")
            return False
        
        # Take screenshot before clicking submit
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_submit_screenshot = f"screenshots/direct_pre_submit_{timestamp}.png"
        driver.save_screenshot(pre_submit_screenshot)
        logger.info(f"[TEST] Pre-submit screenshot saved to: {pre_submit_screenshot}")
        
        # Click the submit button
        submit_button.click()
        logger.info("[TEST] Clicked submit button")
        
        # Wait a moment for the form to submit
        time.sleep(3)
        
        # Take post-submit screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        post_submit_screenshot = f"screenshots/direct_post_submit_{timestamp}.png"
        driver.save_screenshot(post_submit_screenshot)
        logger.info(f"[TEST] Post-submit screenshot saved to: {post_submit_screenshot}")
        
        # Log post-submit state
        logger.info(f"[TEST] Post-submit URL: {driver.current_url}")
        logger.info(f"[TEST] Post-submit title: {driver.title}")
        
        # Check for success or failure
        success_url_patterns = ["dashboard", "trading", "member/home", "account", "platform", "terminal", "market"]
        failure_url_patterns = ["login", "signin", "sign-in", "auth/login"]
        
        # Wait for redirect with timeout
        wait_start = time.time()
        wait_timeout = 20  # seconds
        login_status = "unknown"
        
        while time.time() - wait_start < wait_timeout:
            current_url = driver.current_url
            
            # Check for success indicators
            if any(url_part in current_url for url_part in success_url_patterns):
                login_status = "success"
                logger.info(f"[TEST] Login successful, redirected to: {current_url}")
                break
            
            # Check for failure indicators
            if any(url_part in current_url for url_part in failure_url_patterns):
                # We're still on a login page, but let's wait a bit longer to see if it redirects
                logger.warning(f"[TEST] Still on login page: {current_url}")
                
                # Check for error messages
                try:
                    error_elements = driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@class, 'message') or contains(@class, 'notification')]"
                    )
                    for error in error_elements:
                        if error.is_displayed() and error.text.strip():
                            logger.error(f"[TEST] Login error message: {error.text}")
                            login_status = "failed"
                except Exception as e:
                    logger.warning(f"[TEST] Could not check for error messages: {str(e)}")
            
            # Wait before checking again
            time.sleep(1)
        
        # Final status check and screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = f"screenshots/direct_login_final_{timestamp}.png"
        driver.save_screenshot(final_screenshot)
        logger.info(f"[TEST] Final login status screenshot saved to: {final_screenshot}")
        
        # Determine login success based on final URL and status
        if login_status == "success" or any(url_part in driver.current_url for url_part in success_url_patterns):
            logger.info("[TEST] Direct login test PASSED")
            return True
        elif login_status == "failed" or any(url_part in driver.current_url for url_part in failure_url_patterns):
            logger.error("[TEST] Direct login test FAILED - still on login page")
            return False
        else:
            logger.warning(f"[TEST] Direct login test result UNCLEAR - final URL: {driver.current_url}")
            return not any(url_part in driver.current_url for url_part in failure_url_patterns)
    
    except Exception as e:
        logger.error(f"[TEST] Direct login test error: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    finally:
        if driver:
            driver.quit()

def test_executor_login():
    """Test login using the BulenoxExecutor class"""
    logger.info("[TEST] Starting executor login test")
    executor = None
    try:
        # Create executor instance
        executor = BulenoxExecutor()
        
        # Test health check (which tests login)
        result = executor.health()
        
        if result:
            logger.info("[TEST] Executor login test PASSED")
        else:
            logger.error("[TEST] Executor login test FAILED")
        
        return result
    except Exception as e:
        logger.error(f"[TEST] Executor login test error: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    finally:
        # The driver is created and closed within the health() method
        # No need to close it here
        pass

def test_cookie_based_login():
    """Test login using cookies from a previous session"""
    logger.info("[TEST] Starting cookie-based login test")
    driver = None
    try:
        # Set up Chrome options with user profile
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Use existing Chrome profile for persistent cookies/session
        user_data_dir = os.getenv('CHROME_USER_DATA_DIR', 'C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data')
        profile_directory = os.getenv('CHROME_PROFILE_DIRECTORY', 'Profile 15')
        
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={profile_directory}")
        
        # Initialize Chrome driver
        logger.info("[TEST] Initializing Chrome driver with user profile")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        
        # Navigate directly to a protected page
        protected_url = "https://bulenox.com/member/home"
        logger.info(f"[TEST] Navigating to protected page: {protected_url}")
        driver.get(protected_url)
        time.sleep(3)  # Wait for page to load
        
        # Log current page info
        logger.info(f"[TEST] Current URL: {driver.current_url}")
        logger.info(f"[TEST] Page title: {driver.title}")
        
        # Take screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/cookie_login_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"[TEST] Page screenshot saved to: {screenshot_path}")
        
        # Check if we're on a login page or a protected page
        if "login" in driver.current_url.lower():
            logger.error("[TEST] Cookie-based login test FAILED - redirected to login page")
            return False
        else:
            logger.info("[TEST] Cookie-based login test PASSED - already logged in")
            return True
    
    except Exception as e:
        logger.error(f"[TEST] Cookie-based login test error: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    logger.info("=== BULENOX LOGIN TEST SUITE ===\n")
    
    # Test cookie-based login first (least invasive)
    logger.info("\n=== TEST 1: COOKIE-BASED LOGIN ===\n")
    cookie_result = test_cookie_based_login()
    
    # Test direct login
    logger.info("\n=== TEST 2: DIRECT LOGIN ===\n")
    direct_result = test_direct_login()
    
    # Test executor login
    logger.info("\n=== TEST 3: EXECUTOR LOGIN ===\n")
    executor_result = test_executor_login()
    
    # Print summary
    logger.info("\n=== TEST RESULTS SUMMARY ===\n")
    logger.info(f"Cookie-based login: {'PASSED' if cookie_result else 'FAILED'}")
    logger.info(f"Direct login: {'PASSED' if direct_result else 'FAILED'}")
    logger.info(f"Executor login: {'PASSED' if executor_result else 'FAILED'}")
    
    if cookie_result or direct_result or executor_result:
        logger.info("\nAt least one login method PASSED")
        sys.exit(0)
    else:
        logger.error("\nAll login methods FAILED")
        sys.exit(1)