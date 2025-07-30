import os
import time
import logging
import datetime
import pickle
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("BULENOX_TEST")

# Create screenshots directory if it doesn't exist
os.makedirs("screenshots", exist_ok=True)

# Session ID for tracking
session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def save_cookies(driver, path):
    """Save cookies to a file"""
    try:
        cookies = driver.get_cookies()
        with open(path, 'wb') as file:
            pickle.dump(cookies, file)
        logger.info(f"[{session_id}] Cookies saved to {path}")
        return True
    except Exception as e:
        logger.error(f"[{session_id}] Error saving cookies: {str(e)}")
        return False

def load_cookies(driver, path):
    """Load cookies from a file"""
    try:
        if not os.path.exists(path):
            logger.warning(f"[{session_id}] Cookie file {path} does not exist")
            return False
            
        with open(path, 'rb') as file:
            cookies = pickle.load(file)
            
        # Add cookies to driver
        for cookie in cookies:
            # Some cookies might cause issues, so we'll try each one separately
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"[{session_id}] Could not add cookie {cookie.get('name')}: {str(e)}")
                
        logger.info(f"[{session_id}] Cookies loaded from {path}")
        return True
    except Exception as e:
        logger.error(f"[{session_id}] Error loading cookies: {str(e)}")
        return False

def init_driver(use_profile=True, headless=False):
    """Initialize Chrome driver with multiple fallback options"""
    try:
        # First attempt: with user profile if requested
        if use_profile:
            try:
                logger.info(f"[{session_id}] Initializing Chrome driver with user profile")
                options = Options()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-infobars')
                options.add_argument('--disable-notifications')
                options.add_argument('--disable-popup-blocking')
                
                # Add user profile
                user_data_dir = os.getenv('CHROME_USER_DATA_DIR', 'C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data')
                profile = os.getenv('CHROME_PROFILE', 'Profile 15')
                options.add_argument(f'--user-data-dir={user_data_dir}')
                options.add_argument(f'--profile-directory={profile}')
                
                if headless:
                    options.add_argument('--headless=new')
                
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                driver.set_window_size(1366, 768)
                logger.info(f"[{session_id}] Chrome driver initialized successfully with profile")
                return driver
            except Exception as e:
                logger.error(f"[{session_id}] Profile-based driver init failed: {str(e)}")
                # Fall through to next attempt
        
        # Second attempt: without user profile
        try:
            logger.info(f"[{session_id}] Initializing Chrome driver without user profile")
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            
            if headless:
                options.add_argument('--headless=new')
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.set_window_size(1366, 768)
            logger.info(f"[{session_id}] Chrome driver initialized successfully without profile")
            return driver
        except Exception as e:
            logger.error(f"[{session_id}] Standard driver init failed: {str(e)}")
            # Fall through to last attempt
        
        # Last resort - try with absolute minimal options
        logger.info(f"[{session_id}] Initializing Chrome driver with minimal options")
        minimal_options = Options()
        minimal_options.add_argument('--no-sandbox')
        
        if headless:
            minimal_options.add_argument('--headless=new')
            
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=minimal_options)
        driver.set_window_size(1366, 768)
        logger.info(f"[{session_id}] Chrome driver initialized with minimal options")
        return driver
    except Exception as e:
        logger.error(f"[{session_id}] All driver initialization attempts failed: {str(e)}")
        return None

def login_with_cookies(driver, cookie_path="bulenox_cookies.pkl"):
    """Try to login using saved cookies"""
    try:
        # Get the broker URL from environment variables or use default
        broker_url = os.getenv('BROKER_URL', 'https://bulenox.com')
        logger.info(f"[{session_id}] Navigating to Bulenox main page: {broker_url}")
        driver.get(broker_url)
        
        # Load cookies
        if load_cookies(driver, cookie_path):
            # Refresh the page to apply cookies
            driver.refresh()
            time.sleep(3)
            
            # Check if we're logged in
            dashboard_urls = ["dashboard", "trading", "member/home", "account", "platform", "terminal", "market"]
            if any(url_part in driver.current_url for url_part in dashboard_urls):
                logger.info(f"[{session_id}] Successfully logged in with cookies (current URL: {driver.current_url})")
                return True
            else:
                logger.info(f"[{session_id}] Cookie login failed, current URL: {driver.current_url}")
                return False
        else:
            logger.info(f"[{session_id}] No cookies available or could not load cookies")
            return False
    except Exception as e:
        logger.error(f"[{session_id}] Error during cookie login: {str(e)}")
        return False

def login_with_form(driver):
    """Login using the login form"""
    try:
        # Get the broker URL from environment variables or use default
        broker_url = os.getenv('BROKER_URL', 'https://bulenox.com/member/login')
        logger.info(f"[{session_id}] Navigating to Bulenox login page: {broker_url}")
        driver.get(broker_url)
        
        # Take screenshot of login page
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/bulenox_login_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"[{session_id}] Login page screenshot saved to: {screenshot_path}")
        
        # Log current page information for debugging
        logger.info(f"[{session_id}] Current URL: {driver.current_url}")
        logger.info(f"[{session_id}] Page title: {driver.title}")
        
        # Get credentials from environment variables
        username = os.getenv('BULENOX_USERNAME')
        password = os.getenv('BULENOX_PASSWORD')
        
        if not username or not password:
            logger.error(f"[{session_id}] Missing Bulenox credentials in environment variables")
            return False
        
        logger.info(f"[{session_id}] Using username: {username}")
        
        # Wait for login form with selectors from our diagnostic script
        username_field = None
        username_selectors = [
            (By.ID, "amember-login"),  # From diagnostic script
            (By.NAME, "amember_login"),  # From diagnostic script
            (By.ID, "email"),
            (By.NAME, "userName"),
            (By.NAME, "username"),
            (By.NAME, "user"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@placeholder='Username' or @placeholder='Email' or @placeholder='Login']")
        ]
        
        logger.info(f"[{session_id}] Attempting to find username field with {len(username_selectors)} different selectors")
        for by_method, selector in username_selectors:
            try:
                username_field = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((by_method, selector))
                )
                logger.info(f"[{session_id}] Found username field with selector: {by_method}={selector}")
                break
            except TimeoutException:
                continue
        
        if not username_field:
            logger.error(f"[{session_id}] Login form not found with any selector")
            # Log the page source for debugging
            logger.error(f"[{session_id}] Page source excerpt: {driver.page_source[:500]}...")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            error_screenshot = f"screenshots/login_form_not_found_{timestamp}.png"
            driver.save_screenshot(error_screenshot)
            logger.error(f"[{session_id}] Login form not found screenshot saved to: {error_screenshot}")
            return False
        
        # Enter credentials
        try:
            # Username field already found above
            username_field.clear()
            username_field.send_keys(username)
            logger.info(f"[{session_id}] Entered username: {username}")
            
            # Find password field with expanded selectors
            password_field = None
            password_selectors = [
                (By.ID, "amember-pass"),  # From diagnostic script
                (By.NAME, "amember_pass"),  # From diagnostic script
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
                    logger.info(f"[{session_id}] Found password field with selector: {by_method}={selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                raise NoSuchElementException("Password field not found")
            
            password_field.clear()
            password_field.send_keys(password)
            logger.info(f"[{session_id}] Entered password")
            
            # Check for hidden fields that might be required for login
            try:
                hidden_fields = driver.find_elements(By.XPATH, "//input[@type='hidden']")
                
                if hidden_fields:
                    logger.info(f"[{session_id}] Found {len(hidden_fields)} hidden fields in login form")
                    for field in hidden_fields:
                        name = field.get_attribute('name')
                        value = field.get_attribute('value')
                        logger.info(f"[{session_id}] Hidden field: name={name}, value={value}")
            except Exception as e:
                logger.warning(f"[{session_id}] Could not check hidden fields: {str(e)}")
            
            # Find and click submit button with expanded selectors
            submit_button = None
            submit_selectors = [
                (By.XPATH, "//input[@type='submit']"),  # From diagnostic script
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
                    logger.info(f"[{session_id}] Found submit button with selector: {by_method}={selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                raise NoSuchElementException("Submit button not found")
            
            # Take screenshot before clicking submit
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_submit_screenshot = f"screenshots/bulenox_pre_submit_{timestamp}.png"
            driver.save_screenshot(pre_submit_screenshot)
            logger.info(f"[{session_id}] Pre-submit screenshot saved to: {pre_submit_screenshot}")
            
            # Click the submit button
            submit_button.click()
            logger.info(f"[{session_id}] Clicked submit button")
            
        except Exception as e:
            logger.error(f"[{session_id}] Error during login form interaction: {e}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            error_screenshot = f"screenshots/bulenox_login_error_{timestamp}.png"
            driver.save_screenshot(error_screenshot)
            logger.error(f"[{session_id}] Error screenshot saved to: {error_screenshot}")
            return False
        
        # Wait for login to complete with expanded dashboard URLs
        try:
            dashboard_urls = ["dashboard", "trading", "member/home", "account", "platform", "terminal", "market"]
            logger.info(f"[{session_id}] Waiting for redirect to any of these URLs: {dashboard_urls}")
            
            # Wait for redirect
            WebDriverWait(driver, 15).until(
                lambda d: any(url_part in d.current_url for url_part in dashboard_urls)
            )
            
            # Save cookies for future use
            save_cookies(driver, "bulenox_cookies.pkl")
            
            logger.info(f"[{session_id}] Successfully logged in to Bulenox (redirected to {driver.current_url})")
            return True
        except TimeoutException:
            # Check if we're on a different page that might indicate success
            current_url = driver.current_url
            if any(url_part in current_url for url_part in dashboard_urls):
                # Save cookies for future use
                save_cookies(driver, "bulenox_cookies.pkl")
                
                logger.info(f"[{session_id}] Successfully logged in to Bulenox (redirected to {current_url})")
                return True
            else:
                logger.error(f"[{session_id}] Login failed - unexpected redirect to {current_url}")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                error_screenshot = f"screenshots/bulenox_login_error_{timestamp}.png"
                driver.save_screenshot(error_screenshot)
                logger.error(f"[{session_id}] Error screenshot saved to: {error_screenshot}")
                
                # Check for error messages in the page
                try:
                    error_messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
                    if error_messages:
                        for error in error_messages:
                            logger.error(f"[{session_id}] Login error message found: {error.text}")
                except:
                    pass
                
                # Check if username and password fields still have our values
                try:
                    username_field = driver.find_element(By.ID, "amember-login")
                    password_field = driver.find_element(By.ID, "amember-pass")
                    
                    logger.info(f"[{session_id}] Username field value after submit: {username_field.get_attribute('value')}")
                    logger.info(f"[{session_id}] Password field value after submit: {password_field.get_attribute('value')}")
                except Exception as e:
                    logger.error(f"[{session_id}] Error checking form fields after submit: {str(e)}")
                
                return False
    except Exception as e:
        logger.error(f"[{session_id}] Login failed - {str(e)}")
        # Take a screenshot of the error
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        error_screenshot = f"screenshots/bulenox_login_error_{timestamp}.png"
        try:
            driver.save_screenshot(error_screenshot)
            logger.error(f"[{session_id}] Error screenshot saved to: {error_screenshot}")
        except:
            pass
        return False

def check_site_status():
    """Check if the Bulenox site is up and responding"""
    try:
        broker_url = os.getenv('BROKER_URL', 'https://bulenox.com')
        logger.info(f"[{session_id}] Checking site status: {broker_url}")
        
        response = requests.get(broker_url, timeout=10)
        status_code = response.status_code
        
        if status_code == 200:
            logger.info(f"[{session_id}] Site is up and responding with status code {status_code}")
            return True
        else:
            logger.warning(f"[{session_id}] Site responded with status code {status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"[{session_id}] Error checking site status: {str(e)}")
        return False

def main():
    """Main test function"""
    # First check if the site is up
    if not check_site_status():
        logger.error(f"[{session_id}] Bulenox site is not responding, aborting test")
        return 1
    
    driver = None
    try:
        # Initialize driver
        driver = init_driver(use_profile=False, headless=False)
        if not driver:
            logger.error(f"[{session_id}] Could not initialize driver")
            return 1
        
        # Try to login with cookies first
        if login_with_cookies(driver):
            logger.info(f"[{session_id}] Successfully logged in with cookies")
            return 0
        
        # If cookie login fails, try form login
        logger.info(f"[{session_id}] Cookie login failed, trying form login")
        if login_with_form(driver):
            logger.info(f"[{session_id}] Successfully logged in with form")
            return 0
        else:
            logger.error(f"[{session_id}] All login attempts failed")
            return 1
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error during test: {str(e)}")
        return 1
    finally:
        # Always close the driver
        if driver:
            try:
                driver.quit()
                logger.info(f"[{session_id}] Driver closed")
            except Exception as e:
                logger.error(f"[{session_id}] Error closing driver: {str(e)}")

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)