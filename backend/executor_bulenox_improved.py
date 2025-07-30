import os
import sys
import time
import json
import logging
import datetime
import traceback
import pickle
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Load environment variables
load_dotenv()

class BulenoxExecutor:
    def __init__(self):
        # Load credentials from environment variables
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        self.chrome_driver_path = os.getenv('CHROME_DRIVER_PATH', 'D:\\aibot\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')
        self.user_data_dir = os.getenv('CHROME_USER_DATA_DIR', 'C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data')
        self.profile_directory = os.getenv('CHROME_PROFILE_DIRECTORY', 'Profile 15')
        
        # Validate required credentials
        if not self.username or not self.password:
            raise ValueError("BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
        
        # Set up logging
        self.logger = self._setup_logging()
        
        # Create screenshots directory
        self.screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Session storage for cookies
        self.session_file = os.path.join(os.getcwd(), "logs", "bulenox_session.pkl")
        
        # Driver instance (will be initialized when needed)
        self.driver = None
        
        # Login URL
        self.login_url = "https://bulenox.com/member/login"
        
        # Success URL patterns (used to verify successful login)
        self.success_url_patterns = ["dashboard", "trading", "member/home", "account", "platform", "terminal", "market"]
        
        # Failure URL patterns (used to verify failed login)
        self.failure_url_patterns = ["login", "signin", "sign-in", "auth/login"]
    
    def _setup_logging(self):
        """Set up logging configuration"""
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger('bulenox_executor')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(os.path.join(log_dir, 'broker_login.log'))
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with multi-stage approach for reliability"""
        self.logger.info("Initializing Chrome WebDriver...")
        
        # Common Chrome options for all attempts
        common_options = Options()
        common_options.add_argument("--start-maximized")
        common_options.add_argument("--disable-extensions")
        common_options.add_argument("--disable-gpu")
        common_options.add_argument("--disable-infobars")
        common_options.add_argument("--disable-notifications")
        common_options.add_argument("--disable-popup-blocking")
        common_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        common_options.add_experimental_option("useAutomationExtension", False)
        
        # Try multiple initialization approaches
        driver = None
        max_retries = 3
        retry_count = 0
        
        while driver is None and retry_count < max_retries:
            retry_count += 1
            self.logger.info(f"Driver initialization attempt {retry_count}/{max_retries}")
            
            try:
                # APPROACH 1: Try with user profile for persistent cookies/session
                if os.path.exists(self.user_data_dir):
                    self.logger.info(f"Attempting to initialize with user profile: {self.profile_directory}")
                    profile_options = Options()
                    for arg in common_options.arguments:
                        profile_options.add_argument(arg)
                    for key, value in common_options.experimental_options.items():
                        profile_options.add_experimental_option(key, value)
                    
                    profile_options.add_argument(f"--user-data-dir={self.user_data_dir}")
                    profile_options.add_argument(f"--profile-directory={self.profile_directory}")
                    
                    try:
                        if os.path.exists(self.chrome_driver_path):
                            driver = webdriver.Chrome(service=Service(self.chrome_driver_path), options=profile_options)
                        else:
                            driver = webdriver.Chrome(options=profile_options)
                        self.logger.info("Successfully initialized Chrome with user profile")
                        break
                    except Exception as e:
                        self.logger.warning(f"Failed to initialize with user profile: {str(e)}")
                        # Continue to next approach
                
                # APPROACH 2: Try without user profile
                if driver is None:
                    self.logger.info("Attempting to initialize without user profile")
                    try:
                        if os.path.exists(self.chrome_driver_path):
                            driver = webdriver.Chrome(service=Service(self.chrome_driver_path), options=common_options)
                        else:
                            driver = webdriver.Chrome(options=common_options)
                        self.logger.info("Successfully initialized Chrome without user profile")
                        break
                    except Exception as e:
                        self.logger.warning(f"Failed to initialize without user profile: {str(e)}")
                        # Continue to next approach
                
                # APPROACH 3: Try with minimal options as last resort
                if driver is None:
                    self.logger.info("Attempting to initialize with minimal options")
                    minimal_options = Options()
                    minimal_options.add_argument("--start-maximized")
                    try:
                        if os.path.exists(self.chrome_driver_path):
                            driver = webdriver.Chrome(service=Service(self.chrome_driver_path), options=minimal_options)
                        else:
                            driver = webdriver.Chrome(options=minimal_options)
                        self.logger.info("Successfully initialized Chrome with minimal options")
                        break
                    except Exception as e:
                        self.logger.warning(f"Failed to initialize with minimal options: {str(e)}")
                        # Will retry on next iteration
            
            except Exception as e:
                self.logger.error(f"Unexpected error during driver initialization: {str(e)}")
            
            # Wait before retrying
            if driver is None and retry_count < max_retries:
                self.logger.info(f"Waiting 2 seconds before retry {retry_count + 1}...")
                time.sleep(2)
        
        if driver is None:
            self.logger.error(f"Failed to initialize Chrome WebDriver after {max_retries} attempts")
            raise WebDriverException(f"Failed to initialize Chrome WebDriver after {max_retries} attempts")
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        return driver
    
    def _save_cookies(self):
        """Save cookies for future sessions"""
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
                with open(self.session_file, 'wb') as f:
                    pickle.dump(cookies, f)
                self.logger.info(f"Saved {len(cookies)} cookies to {self.session_file}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to save cookies: {str(e)}")
        return False
    
    def _load_cookies(self):
        """Load cookies from previous sessions"""
        if not os.path.exists(self.session_file):
            self.logger.info(f"No session file found at {self.session_file}")
            return False
        
        try:
            with open(self.session_file, 'rb') as f:
                cookies = pickle.load(f)
            
            # Add cookies to driver
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    self.logger.warning(f"Could not add cookie {cookie.get('name')}: {str(e)}")
            
            self.logger.info(f"Loaded {len(cookies)} cookies from {self.session_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load cookies: {str(e)}")
            return False
    
    def _login(self):
        """Log in to Bulenox"""
        self.logger.info("Starting login process...")
        
        try:
            # Navigate to login page
            self.logger.info(f"Navigating to login page: {self.login_url}")
            self.driver.get(self.login_url)
            
            # Wait for page to load
            self.logger.info("Waiting for page to load...")
            time.sleep(2)
            
            # Log current page info
            current_url = self.driver.current_url
            page_title = self.driver.title
            self.logger.info(f"Current URL: {current_url}")
            self.logger.info(f"Page title: {page_title}")
            self.logger.info(f"Page source length: {len(self.driver.page_source)}")
            
            # Take initial screenshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            initial_screenshot = os.path.join(self.screenshots_dir, f"bulenox_initial_{timestamp}.png")
            self.driver.save_screenshot(initial_screenshot)
            self.logger.info(f"Initial page screenshot saved to: {initial_screenshot}")
            
            # Check if already logged in
            if any(pattern in current_url for pattern in self.success_url_patterns):
                self.logger.info("Already logged in with saved session")
                return True
            
            # Check for CAPTCHA
            try:
                captcha_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'captcha') or contains(@class, 'g-recaptcha')]")
                if captcha_elements:
                    self.logger.error(f"CAPTCHA detected on login page")
                    for element in captcha_elements:
                        self.logger.error(f"CAPTCHA element: {element.get_attribute('outerHTML')}")
            except Exception as e:
                self.logger.warning(f"Could not check for CAPTCHA: {str(e)}")
            
            # Find username field using multiple selectors
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
                    username_field = self.driver.find_element(by_method, selector)
                    self.logger.info(f"Found username field with selector: {by_method}={selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not username_field:
                self.logger.error("Username field not found")
                # Try to log all input fields for debugging
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    self.logger.info(f"Found {len(inputs)} input fields on page")
                    for i, input_field in enumerate(inputs):
                        try:
                            self.logger.info(f"Input {i+1}: type={input_field.get_attribute('type')}, name={input_field.get_attribute('name')}, id={input_field.get_attribute('id')}")
                        except:
                            pass
                except Exception as e:
                    self.logger.warning(f"Could not log input fields: {str(e)}")
                
                raise NoSuchElementException("Username field not found with any selector")
            
            # Find password field using multiple selectors
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
                    password_field = self.driver.find_element(by_method, selector)
                    self.logger.info(f"Found password field with selector: {by_method}={selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                self.logger.error("Password field not found")
                raise NoSuchElementException("Password field not found with any selector")
            
            # Find the login form and check for hidden fields
            try:
                form_element = username_field.find_element(By.XPATH, "./ancestor::form")
                self.logger.info(f"Found login form")
                form_action = form_element.get_attribute('action')
                form_method = form_element.get_attribute('method')
                self.logger.info(f"Form action: {form_action}, method: {form_method}")
                
                # Check for hidden fields in the form, especially login_attempt_id
                hidden_fields = form_element.find_elements(By.XPATH, ".//input[@type='hidden']")
                if hidden_fields:
                    self.logger.info(f"Found {len(hidden_fields)} hidden fields in login form")
                    for field in hidden_fields:
                        name = field.get_attribute('name')
                        value = field.get_attribute('value')
                        self.logger.info(f"Hidden field: name={name}, value={value}")
                        
                        # Special handling for login_attempt_id which might be needed for CSRF protection
                        if name == "login_attempt_id" or name == "csrf_token" or name == "_token":
                            self.logger.info(f"Found important security token: {name}={value}")
            except Exception as e:
                self.logger.warning(f"Could not check form details: {str(e)}")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            self.logger.info(f"Entered username: {self.username}")
            
            password_field.clear()
            password_field.send_keys(self.password)
            self.logger.info("Entered password")
            
            # Find submit button using multiple selectors
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
                    submit_button = self.driver.find_element(by_method, selector)
                    self.logger.info(f"Found submit button with selector: {by_method}={selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                self.logger.error("Submit button not found")
                # Try to log all buttons for debugging
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    self.logger.info(f"Found {len(buttons)} buttons on page")
                    for i, button in enumerate(buttons):
                        try:
                            self.logger.info(f"Button {i+1}: text='{button.text}', type={button.get_attribute('type')}")
                        except:
                            pass
                except Exception as e:
                    self.logger.warning(f"Could not log buttons: {str(e)}")
                
                raise NoSuchElementException("Submit button not found with any selector")
            
            # Take pre-submit screenshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_submit_screenshot = os.path.join(self.screenshots_dir, f"bulenox_pre_submit_{timestamp}.png")
            self.driver.save_screenshot(pre_submit_screenshot)
            self.logger.info(f"Pre-submit screenshot saved to: {pre_submit_screenshot}")
            
            # Check for error messages before submission
            try:
                error_elements = self.driver.find_elements(By.XPATH, 
                    "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@class, 'message') or contains(@class, 'notification')]"
                )
                for error in error_elements:
                    if error.is_displayed() and error.text.strip():
                        self.logger.warning(f"Pre-submission error message found: {error.text}")
            except Exception as e:
                self.logger.warning(f"Could not check for pre-submission error messages: {str(e)}")
            
            # Click the submit button
            try:
                submit_button.click()
                self.logger.info("Clicked submit button")
            except Exception as e:
                self.logger.error(f"Failed to click submit button: {e}")
                raise
            
            # Wait for form submission
            time.sleep(3)
            
            # Wait for login success or failure
            return self._wait_for_login_success()
            
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Take error screenshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            error_screenshot = os.path.join(self.screenshots_dir, f"bulenox_login_error_{timestamp}.png")
            try:
                self.driver.save_screenshot(error_screenshot)
                self.logger.info(f"Error screenshot saved to: {error_screenshot}")
            except Exception as screenshot_error:
                self.logger.error(f"Could not save error screenshot: {str(screenshot_error)}")
            
            return False
    
    def _wait_for_login_success(self):
        """Wait for login success or failure"""
        # Take immediate post-submit screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        post_submit_screenshot = os.path.join(self.screenshots_dir, f"bulenox_post_submit_{timestamp}.png")
        self.driver.save_screenshot(post_submit_screenshot)
        self.logger.info(f"Post-submit screenshot saved to: {post_submit_screenshot}")
        
        # Log post-submit state
        current_url = self.driver.current_url
        page_title = self.driver.title
        self.logger.info(f"Post-submit URL: {current_url}")
        self.logger.info(f"Post-submit title: {page_title}")
        
        # Wait for redirect with timeout
        wait_start = time.time()
        wait_timeout = 20  # seconds
        login_status = "unknown"
        
        while time.time() - wait_start < wait_timeout:
            current_url = self.driver.current_url
            
            # Check for success indicators
            if any(url_part in current_url for url_part in self.success_url_patterns):
                login_status = "success"
                self.logger.info(f"Login successful, redirected to: {current_url}")
                
                # Save cookies for future sessions
                self._save_cookies()
                
                # Take success screenshot
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                success_screenshot = os.path.join(self.screenshots_dir, f"bulenox_login_success_{timestamp}.png")
                self.driver.save_screenshot(success_screenshot)
                self.logger.info(f"Success screenshot saved to: {success_screenshot}")
                
                return True
            
            # Check for failure indicators
            if any(url_part in current_url for url_part in self.failure_url_patterns):
                # We're still on a login page, but let's wait a bit longer to see if it redirects
                self.logger.warning(f"Still on login page: {current_url}")
                
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@class, 'message') or contains(@class, 'notification')]"
                    )
                    for error in error_elements:
                        if error.is_displayed() and error.text.strip():
                            self.logger.error(f"Login error message: {error.text}")
                            login_status = "failed"
                except Exception as e:
                    self.logger.warning(f"Could not check for error messages: {str(e)}")
            
            # Wait before checking again
            time.sleep(1)
        
        # Final status check and screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_screenshot = os.path.join(self.screenshots_dir, f"bulenox_login_final_{timestamp}.png")
        self.driver.save_screenshot(final_screenshot)
        self.logger.info(f"Final login status screenshot saved to: {final_screenshot}")
        
        # Determine login success based on final URL and status
        if login_status == "success" or any(url_part in self.driver.current_url for url_part in self.success_url_patterns):
            self.logger.info("Login successful")
            return True
        elif login_status == "failed" or any(url_part in self.driver.current_url for url_part in self.failure_url_patterns):
            self.logger.error("Login failed - still on login page")
            
            # Take error screenshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            error_screenshot = os.path.join(self.screenshots_dir, f"bulenox_login_error_{timestamp}.png")
            self.driver.save_screenshot(error_screenshot)
            self.logger.info(f"Login error screenshot saved to: {error_screenshot}")
            
            return False
        else:
            self.logger.warning(f"Login result unclear - final URL: {self.driver.current_url}")
            return False
    
    def _place_trade(self, trade_data):
        """Place a trade on Bulenox"""
        self.logger.info("Attempting to place trade...")
        
        try:
            # Navigate to trading page
            trading_url = "https://bulenox.com/member/trading"
            self.logger.info(f"Navigating to trading page: {trading_url}")
            self.driver.get(trading_url)
            
            # Wait for trading interface to load
            self.logger.info("Waiting for trading interface to load...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'trading') or contains(@class, 'platform')]")),
                "Trading interface not found"
            )
            
            # Take screenshot of trading page
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            trading_screenshot = os.path.join(self.screenshots_dir, f"bulenox_trading_{timestamp}.png")
            self.driver.save_screenshot(trading_screenshot)
            self.logger.info(f"Trading page screenshot saved to: {trading_screenshot}")
            
            # TODO: Implement trade placement logic based on Bulenox's interface
            # This will need to be customized based on the actual trading interface
            
            self.logger.info("Trade placed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error placing trade: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Take error screenshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            error_screenshot = os.path.join(self.screenshots_dir, f"bulenox_trade_error_{timestamp}.png")
            try:
                self.driver.save_screenshot(error_screenshot)
                self.logger.info(f"Trade error screenshot saved to: {error_screenshot}")
            except Exception as screenshot_error:
                self.logger.error(f"Could not save trade error screenshot: {str(screenshot_error)}")
            
            return False
    
    def health(self):
        """Check if the executor is healthy by testing login"""
        self.logger.info("Performing health check...")
        
        try:
            # Initialize driver
            self.driver = self._init_driver()
            
            # Try to log in
            login_success = self._login()
            
            if login_success:
                self.logger.info("Health check passed - login successful")
                return True
            else:
                self.logger.error("Health check failed - login unsuccessful")
                return False
                
        except Exception as e:
            self.logger.error(f"Health check error: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
        finally:
            # Always close the driver
            self._close_driver()
    
    def execute_trade(self, trade_data):
        """Execute a trade on Bulenox"""
        self.logger.info(f"Executing trade: {json.dumps(trade_data)}")
        
        try:
            # Initialize driver
            self.driver = self._init_driver()
            
            # Try to log in
            login_success = self._login()
            
            if not login_success:
                self.logger.error("Cannot execute trade - login failed")
                return False
            
            # Place the trade
            trade_success = self._place_trade(trade_data)
            
            if trade_success:
                self.logger.info("Trade executed successfully")
                return True
            else:
                self.logger.error("Trade execution failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Trade execution error: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
        finally:
            # Always close the driver
            self._close_driver()
    
    def _close_driver(self):
        """Safely close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing WebDriver: {str(e)}")
            finally:
                self.driver = None

# For testing
if __name__ == "__main__":
    executor = BulenoxExecutor()
    health_result = executor.health()
    print(f"Health check result: {health_result}")