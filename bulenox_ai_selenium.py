import json
import logging
import os
import time
from datetime import datetime

import numpy as np
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bulenox_ai_selenium")

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
        with open(HEARTBEAT_STATUS_FILE, "w") as f:
            f.write(
                f"{status}\n{timestamp}\n{json.dumps({'session_active': session_active})}"
            )

        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")


class BulenoxAISelenium:
    """
    AI-enhanced Selenium automation for Bulenox trading platform
    Handles login, navigation, and trading operations with adaptive techniques
    """

    def __init__(self, debug=False):
        self.debug = debug
        self.screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Load credentials
        self.username = os.getenv("BULENOX_USERNAME")
        self.password = os.getenv("BULENOX_PASSWORD")
        
        # Get profile paths from environment variables or use defaults
        self.profile_path = os.getenv(
            "BULENOX_PROFILE_PATH", r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data"
        )
        self.profile_name = os.getenv("BULENOX_PROFILE_NAME", "Profile 13")
        
        # URLs - using actual URLs from login_bulenox.py# URLs
        self.login_url = "https://bulenox.projectx.com/login"
        self.trading_url = "https://bulenox.projectx.com/trading"
        
        # Element selectors with confidence weights - enhanced for better detection
        self.selectors = {
            "username": [
                {"by": By.ID, "value": "email", "weight": 0.9},
                {"by": By.NAME, "value": "email", "weight": 0.8},
                {"by": By.XPATH, "value": "//input[@type='email']", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Email')]", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@class, 'email')]", "weight": 0.6},
                {"by": By.CSS_SELECTOR, "value": "input[type='text']:first-of-type", "weight": 0.5},
                {"by": By.CSS_SELECTOR, "value": "form input:first-of-type", "weight": 0.4},
            ],
            "password": [
                {"by": By.ID, "value": "password", "weight": 0.9},
                {"by": By.NAME, "value": "password", "weight": 0.8},
                {"by": By.XPATH, "value": "//input[@type='password']", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Password')]", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@class, 'password')]", "weight": 0.6},
                {"by": By.CSS_SELECTOR, "value": "form input[type='password']", "weight": 0.5},
            ],
            "login_button": [
                {"by": By.XPATH, "value": "//button[@type='submit']", "weight": 0.9},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Login')]", "weight": 0.8},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Sign in')]", "weight": 0.8},
                {"by": By.XPATH, "value": "//button[contains(@class, 'login')]", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[@type='submit']", "weight": 0.6},
                {"by": By.CSS_SELECTOR, "value": "form button", "weight": 0.5},
                {"by": By.CSS_SELECTOR, "value": ".login-btn", "weight": 0.5},
            ],
            "symbol_search": [
                {"by": By.ID, "value": "symbol-search", "weight": 0.9},
                {"by": By.XPATH, "value": "//input[@placeholder='Search']", "weight": 0.7},
                {"by": By.CSS_SELECTOR, "value": ".symbol-search-input", "weight": 0.5},
            ],
            "buy_button": [
                {"by": By.XPATH, "value": "//button[contains(@class, 'buy-button')]", "weight": 0.9},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Buy')]", "weight": 0.7},
                {"by": By.CSS_SELECTOR, "value": ".buy-btn", "weight": 0.5},
            ],
            "sell_button": [
                {"by": By.XPATH, "value": "//button[contains(@class, 'sell-button')]", "weight": 0.9},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Sell')]", "weight": 0.7},
                {"by": By.CSS_SELECTOR, "value": ".sell-btn", "weight": 0.5},
            ],
            "quantity_input": [
                {"by": By.ID, "value": "quantity", "weight": 0.9},
                {"by": By.NAME, "value": "quantity", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Quantity')]", "weight": 0.5},
            ],
            "stop_loss_input": [
                {"by": By.ID, "value": "stop-loss", "weight": 0.9},
                {"by": By.NAME, "value": "stopLoss", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Stop Loss')]", "weight": 0.5},
            ],
            "take_profit_input": [
                {"by": By.ID, "value": "take-profit", "weight": 0.9},
                {"by": By.NAME, "value": "takeProfit", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Take Profit')]", "weight": 0.5},
            ],
            "confirm_button": [
                {"by": By.XPATH, "value": "//button[contains(text(), 'Confirm')]", "weight": 0.9},
                {"by": By.XPATH, "value": "//button[contains(@class, 'confirm-button')]", "weight": 0.7},
                {"by": By.CSS_SELECTOR, "value": ".confirm-btn", "weight": 0.5},
            ],
        }
        
        # Success indicators with enhanced login detection
        self.success_indicators = {
            "login": [
                # URL-based indicators
                {"type": "url", "value": "dashboard", "weight": 0.8},
                {"type": "url", "value": "trading", "weight": 0.8},
                {"type": "url", "value": "account", "weight": 0.7},
                {"type": "url", "value": "home", "weight": 0.6},
                
                # Element-based indicators
                {"type": "element", "by": By.CSS_SELECTOR, "value": ".dashboard-element", "weight": 0.9},
                {"type": "element", "by": By.CSS_SELECTOR, "value": ".trading-interface", "weight": 0.9},
                {"type": "element", "by": By.XPATH, "value": "//a[contains(text(), 'Logout')]", "weight": 0.8},
                {"type": "element", "by": By.XPATH, "value": "//button[contains(text(), 'Logout')]", "weight": 0.8},
                {"type": "element", "by": By.XPATH, "value": "//a[contains(@href, 'logout')]", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'user-profile')]", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//span[contains(@class, 'username')]", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'trading')]", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'chart')]", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(text(), 'Balance')]", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(text(), 'Account')]", "weight": 0.7},
            ],
            "trade": [
                {"type": "element", "by": By.XPATH, "value": "//div[contains(text(), 'Order Placed')]", "weight": 0.9},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(text(), 'Success')]", "weight": 0.8},
                {"type": "element", "by": By.CSS_SELECTOR, "value": ".order-success", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(text(), 'Confirmation')]", "weight": 0.7},
                {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'success')]", "weight": 0.6},
            ],
        }
        
        # Futures symbol mapping
        self.futures_symbols = {
            "GBPUSD": "MBTQ25",
            "EURUSD": "6EU25",
            "USDJPY": "6J25",
            "ES": "ES25",
            "XAUUSD": "GC",  # Gold futures
        }
        
        # Initialize driver
        self.driver = None
        
    def _configure_chrome_options(self):
        """Configure Chrome options with optimal settings for trading platform"""
        chrome_options = Options()
        
        # Profile settings
        if self.profile_path and self.profile_name:
            chrome_options.add_argument(f"--user-data-dir={self.profile_path}")
            chrome_options.add_argument(f"--profile-directory={self.profile_name}")
        
        # Essential Chrome arguments
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-session-crashed-bubble")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Anti-detection settings
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("detach", True)
        
        return chrome_options
    
    def _initialize_driver(self):
        """Initialize Chrome driver with adaptive error handling"""
        update_heartbeat_status("🔄 Initializing Chrome for AI-enhanced Bulenox automation...")
        chrome_options = self._configure_chrome_options()
        
        try:
            # First try with WebDriver Manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized successfully with WebDriver Manager")
            return True
        except Exception as e:
            logger.error(f"Error using WebDriver Manager: {e}")
            
            try:
                # Try with default Chrome
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Chrome driver initialized successfully with default Chrome")
                return True
            except Exception as e2:
                logger.error(f"Error with default Chrome: {e2}")
                
                # Last resort - try with minimal options
                try:
                    minimal_options = Options()
                    minimal_options.add_argument("--start-maximized")
                    self.driver = webdriver.Chrome(options=minimal_options)
                    logger.info("Chrome driver initialized successfully with minimal options")
                    return True
                except Exception as e3:
                    logger.error(f"All Chrome initialization attempts failed: {e3}")
                    update_heartbeat_status("❌ All Chrome initialization attempts failed")
                    return False
    
    def _take_screenshot(self, name):
        """Take a screenshot with timestamp"""
        if not self.debug or not self.driver:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"bulenox_ai_{name}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def _find_element_with_ai(self, element_type, timeout=10):
        """Find element using weighted selectors and adaptive approach with enhanced error handling"""
        if element_type not in self.selectors:
            logger.error(f"Unknown element type: {element_type}")
            return None
            
        # Take screenshot of current page for debugging
        if self.debug:
            self._take_screenshot(f"{element_type}_search")
            
        # Log page source for debugging
        logger.info(f"Searching for {element_type} element in page")
        
        # Try selectors in order of confidence weight
        sorted_selectors = sorted(self.selectors[element_type], key=lambda x: x["weight"], reverse=True)
        
        # First try presence_of_element_located
        for selector in sorted_selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((selector["by"], selector["value"]))
                )
                logger.info(f"Found {element_type} element using {selector['by']}={selector['value']}")
                return element
            except TimeoutException:
                logger.debug(f"Selector {selector['by']}={selector['value']} timed out")
                continue
            except Exception as e:
                logger.debug(f"Error with selector {selector['by']}={selector['value']}: {e}")
                continue
        
        # If presence_of_element_located failed, try find_element directly
        logger.info(f"Trying direct find_element approach for {element_type}")
        for selector in sorted_selectors:
            try:
                element = self.driver.find_element(selector["by"], selector["value"])
                logger.info(f"Found {element_type} element directly using {selector['by']}={selector['value']}")
                return element
            except NoSuchElementException:
                continue
            except Exception as e:
                logger.debug(f"Error with direct selector {selector['by']}={selector['value']}: {e}")
                continue
        
        # Last resort: try to find any input elements
        if element_type in ["username", "password"]:
            logger.info("Trying generic input element detection")
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                if element_type == "username" and len(inputs) > 0:
                    logger.info("Using first input element as username")
                    return inputs[0]
                elif element_type == "password" and len(inputs) > 1:
                    logger.info("Using second input element as password")
                    return inputs[1]
            except Exception as e:
                logger.debug(f"Error with generic input detection: {e}")
        
        # If all else fails, take a screenshot and log error
        if self.debug:
            self._take_screenshot(f"{element_type}_not_found")
        
        logger.error(f"Could not find {element_type} element")
        return None
    
    def _check_success(self, success_type):
        """Check if an operation was successful using multiple indicators"""
        if success_type not in self.success_indicators:
            logger.error(f"Unknown success type: {success_type}")
            return False
            
        success_score = 0
        max_score = 0
        
        # Log current URL for debugging
        current_url = self.driver.current_url
        logger.info(f"Checking {success_type} success, current URL: {current_url}")
        
        for indicator in self.success_indicators[success_type]:
            max_score += indicator["weight"]
            
            if indicator["type"] == "url":
                if indicator["value"] in current_url:
                    success_score += indicator["weight"]
                    logger.info(f"Success indicator found in URL: {indicator['value']}")
            
            elif indicator["type"] == "element":
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((indicator["by"], indicator["value"]))
                    )
                    success_score += indicator["weight"]
                    logger.info(f"Success indicator element found: {indicator['value']}")
                except TimeoutException:
                    pass
        
        # Calculate normalized success probability
        success_probability = success_score / max_score if max_score > 0 else 0
        logger.info(f"{success_type.capitalize()} success probability: {success_probability:.2f}")
        
        # If no indicators found but login form is gone, consider it a success for login
        if success_type == "login" and success_probability == 0:
            try:
                # Check if login form is no longer present
                username_field = self.driver.find_element(By.ID, "email")
                password_field = self.driver.find_element(By.ID, "password")
                # If both fields are still present, login probably failed
                logger.info("Login form still present, login likely failed")
            except NoSuchElementException:
                # If login form is gone but no success indicators found, might still be successful
                logger.info("Login form not found, considering login successful")
                self._take_screenshot("login_ambiguous")
                return True
        
        return success_probability > 0.5  # Success threshold
    
    def login(self):
        """Perform AI-enhanced login to Bulenox with improved error handling"""
        update_heartbeat_status("🚀 Starting AI-enhanced Bulenox login...")
        
        # Initialize driver
        if not self._initialize_driver():
            return False
        
        try:
            # Navigate to login page
            logger.info(f"Navigating to {self.login_url}")
            update_heartbeat_status("🔄 Navigating to Bulenox login page...")
            self.driver.get(self.login_url)
            self._take_screenshot("initial_page")
            
            # Wait for page to load
            time.sleep(3)
            
            # Log page title and URL for debugging
            logger.info(f"Current page title: {self.driver.title}")
            logger.info(f"Current URL: {self.driver.current_url}")
            
            # Check if already logged in
            if self._check_success("login"):
                logger.info("Already logged in with saved profile")
                update_heartbeat_status("✅ Already logged in with saved profile")
                return True
            
            # Perform login
            logger.info("Not logged in automatically. Attempting login...")
            update_heartbeat_status("🔑 Attempting AI-enhanced login...")
            
            # Wait for login form to be visible
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "form"))
                )
                logger.info("Login form detected")
            except:
                logger.info("No form tag found, continuing with element search")
            
            # Find username field
            username_field = self._find_element_with_ai("username")
            if not username_field:
                logger.error("Could not find username field")
                update_heartbeat_status("❌ Could not find username field")
                self._take_screenshot("username_field_not_found")
                
                # Try to find any input field as a fallback
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    if inputs:
                        logger.info(f"Found {len(inputs)} input elements, using first as username")
                        username_field = inputs[0]
                    else:
                        self.driver.quit()
                        self.driver = None
                        return False
                except Exception as e:
                    logger.error(f"Fallback input search failed: {e}")
                    self.driver.quit()
                    self.driver = None
                    return False
            
            # Ensure element is visible and clickable
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", username_field)
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='{username_field.get_attribute('id')}']"))) 
            except:
                logger.info("Could not scroll to username element, continuing anyway")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Find password field
            password_field = self._find_element_with_ai("password")
            if not password_field:
                logger.error("Could not find password field")
                update_heartbeat_status("❌ Could not find password field")
                self._take_screenshot("password_field_not_found")
                
                # Try to find any input field as a fallback
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    if len(inputs) > 1:
                        logger.info(f"Found {len(inputs)} input elements, using second as password")
                        password_field = inputs[1]
                    else:
                        self.driver.quit()
                        self.driver = None
                        return False
                except Exception as e:
                    logger.error(f"Fallback input search failed: {e}")
                    self.driver.quit()
                    self.driver = None
                    return False
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            self._take_screenshot("credentials_entered")
            
            # Find and click login button
            login_button = self._find_element_with_ai("login_button")
            if not login_button:
                logger.error("Could not find login button")
                update_heartbeat_status("❌ Could not find login button")
                self._take_screenshot("login_button_not_found")
                
                # Try to find any button as a fallback
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    if buttons:
                        logger.info(f"Found {len(buttons)} button elements, using first as login button")
                        login_button = buttons[0]
                    else:
                        # Try to find submit input
                        submit_inputs = self.driver.find_elements(By.XPATH, "//input[@type='submit']")
                        if submit_inputs:
                            login_button = submit_inputs[0]
                        else:
                            self.driver.quit()
                            self.driver = None
                            return False
                except Exception as e:
                    logger.error(f"Fallback button search failed: {e}")
                    self.driver.quit()
                    self.driver = None
                    return False
            
            # Ensure button is clickable
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='{login_button.get_attribute('id')}']"))) 
            except:
                logger.info("Could not scroll to login button, continuing anyway")
            
            login_button.click()
            logger.info("Login button clicked")
            update_heartbeat_status("🔄 Login submitted, waiting for response...")
            
            # Wait for login to complete
            time.sleep(5)
            self._take_screenshot("after_login_click")
            
            # Check if login was successful
            if self._check_success("login"):
                logger.info("Login successful")
                update_heartbeat_status("✅ AI-enhanced login successful")
                return True
            else:
                logger.error("Login failed")
                update_heartbeat_status("❌ Login failed")
                self._take_screenshot("login_failed")
                self.driver.quit()
                self.driver = None
                return False
                
        except Exception as e:
            logger.error(f"Error during login process: {e}")
            update_heartbeat_status(f"❌ Error during login process: {str(e)[:50]}...")
            self._take_screenshot("login_error")
            
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            return False
    
    def navigate_to_trading(self):
        """Navigate to the trading page"""
        if not self.driver:
            logger.error("Driver not initialized. Please login first.")
            return False
            
        try:
            logger.info("Navigating to trading page...")
            update_heartbeat_status("🔄 Navigating to trading page...")
            self.driver.get(self.trading_url)
            time.sleep(3)
            self._take_screenshot("trading_page")
            
            # Check if navigation was successful
            if "trading" in self.driver.current_url:
                logger.info("Successfully navigated to trading page")
                update_heartbeat_status("✅ Successfully navigated to trading page")
                return True
            else:
                logger.error("Failed to navigate to trading page")
                update_heartbeat_status("❌ Failed to navigate to trading page")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to trading page: {e}")
            update_heartbeat_status(f"❌ Error navigating to trading page: {str(e)[:50]}...")
            self._take_screenshot("navigation_error")
            return False
    
    def search_symbol(self, symbol):
        """Search for a trading symbol"""
        if not self.driver:
            logger.error("Driver not initialized. Please login first.")
            return False
            
        # Map symbol to futures symbol if needed
        futures_symbol = self.futures_symbols.get(symbol, symbol)
        logger.info(f"Mapping symbol {symbol} to futures symbol {futures_symbol}")
            
        try:
            # Find symbol search field
            search_field = self._find_element_with_ai("symbol_search")
            if not search_field:
                logger.error("Could not find symbol search field")
                update_heartbeat_status("❌ Could not find symbol search field")
                self._take_screenshot("symbol_search_not_found")
                return False
                
            # Clear and enter symbol
            search_field.clear()
            search_field.send_keys(futures_symbol)
            time.sleep(1)
            search_field.send_keys(Keys.RETURN)
            
            logger.info(f"Searched for symbol: {futures_symbol}")
            update_heartbeat_status(f"🔍 Searching for symbol: {futures_symbol}...")
            time.sleep(3)
            self._take_screenshot(f"symbol_search_{futures_symbol}")
            
            # Check if symbol was found (basic check)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{futures_symbol}')]")),
                )
                logger.info(f"Symbol {futures_symbol} found")
                update_heartbeat_status(f"✅ Symbol {futures_symbol} found")
                return True
            except TimeoutException:
                logger.warning(f"Symbol {futures_symbol} not explicitly found, but continuing")
                # Continue anyway as the symbol might still be selected
                return True
                
        except Exception as e:
            logger.error(f"Error searching for symbol: {e}")
            update_heartbeat_status(f"❌ Error searching for symbol: {str(e)[:50]}...")
            self._take_screenshot("symbol_search_error")
            return False
    
    def place_trade(self, symbol, side, quantity, stop_loss=None, take_profit=None):
        """Place a trade with the specified parameters"""
        if not self.driver:
            logger.error("Driver not initialized. Please login first.")
            return False
            
        try:
            # Navigate to trading page
            if not self.navigate_to_trading():
                return False
                
            # Search for symbol
            if not self.search_symbol(symbol):
                return False
                
            # Find buy/sell button based on side
            button_type = "buy_button" if side.lower() == "buy" else "sell_button"
            trade_button = self._find_element_with_ai(button_type)
            if not trade_button:
                logger.error(f"Could not find {side} button")
                update_heartbeat_status(f"❌ Could not find {side} button")
                self._take_screenshot(f"{side}_button_not_found")
                return False
                
            # Click buy/sell button to open order form
            trade_button.click()
            logger.info(f"Clicked {side} button")
            update_heartbeat_status(f"🔄 Opening {side} order form...")
            time.sleep(2)
            self._take_screenshot("order_form")
            
            # Enter quantity
            quantity_input = self._find_element_with_ai("quantity_input")
            if not quantity_input:
                logger.error("Could not find quantity input")
                update_heartbeat_status("❌ Could not find quantity input")
                self._take_screenshot("quantity_input_not_found")
                return False
                
            quantity_input.clear()
            quantity_input.send_keys(str(quantity))
            logger.info(f"Entered quantity: {quantity}")
            
            # Enter stop loss if provided
            if stop_loss is not None:
                stop_loss_input = self._find_element_with_ai("stop_loss_input")
                if stop_loss_input:
                    stop_loss_input.clear()
                    stop_loss_input.send_keys(str(stop_loss))
                    logger.info(f"Entered stop loss: {stop_loss}")
                else:
                    logger.warning("Could not find stop loss input, continuing without stop loss")
            
            # Enter take profit if provided
            if take_profit is not None:
                take_profit_input = self._find_element_with_ai("take_profit_input")
                if take_profit_input:
                    take_profit_input.clear()
                    take_profit_input.send_keys(str(take_profit))
                    logger.info(f"Entered take profit: {take_profit}")
                else:
                    logger.warning("Could not find take profit input, continuing without take profit")
            
            self._take_screenshot("order_details_entered")
            
            # Find and click confirm button
            confirm_button = self._find_element_with_ai("confirm_button")
            if not confirm_button:
                logger.error("Could not find confirm button")
                update_heartbeat_status("❌ Could not find confirm button")
                self._take_screenshot("confirm_button_not_found")
                return False
                
            confirm_button.click()
            logger.info("Clicked confirm button")
            update_heartbeat_status("🔄 Confirming order...")
            time.sleep(3)
            self._take_screenshot("order_confirmation")
            
            # Check if trade was successful
            if self._check_success("trade"):
                logger.info("Trade placed successfully")
                update_heartbeat_status("✅ Trade placed successfully")
                return True
            else:
                logger.error("Trade placement may have failed")
                update_heartbeat_status("⚠️ Trade placement may have failed, check platform")
                return False
                
        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            update_heartbeat_status(f"❌ Error placing trade: {str(e)[:50]}...")
            self._take_screenshot("trade_error")
            return False
    
    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
                update_heartbeat_status("✅ Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None


def login_bulenox_ai(debug=False):
    """Login to Bulenox using AI-enhanced Selenium
    
    Args:
        debug (bool): Enable debug mode with additional logging and screenshots
        
    Returns:
        BulenoxAISelenium: Initialized BulenoxAISelenium instance, or None if login fails
    """
    bulenox = BulenoxAISelenium(debug=debug)
    success = bulenox.login()
    
    if success:
        return bulenox
    else:
        return None


def place_bulenox_trade(symbol, side, quantity, stop_loss=None, take_profit=None, debug=False):
    """Place a trade on Bulenox using AI-enhanced Selenium
    
    Args:
        symbol (str): Trading symbol (e.g., "GBPUSD", "EURUSD", "XAUUSD")
        side (str): Trade direction ("buy" or "sell")
        quantity (int): Number of contracts
        stop_loss (float, optional): Stop loss price
        take_profit (float, optional): Take profit price
        debug (bool): Enable debug mode with additional logging and screenshots
        
    Returns:
        bool: True if trade was placed successfully, False otherwise
    """
    bulenox = login_bulenox_ai(debug=debug)
    
    if not bulenox:
        logger.error("Login failed, cannot place trade")
        return False
    
    try:
        success = bulenox.place_trade(symbol, side, quantity, stop_loss, take_profit)
        return success
    finally:
        bulenox.close()


if __name__ == "__main__":
    print("🤖 Bulenox AI Selenium Module")
    print("=" * 50)
    print("This module provides AI-enhanced Selenium automation for Bulenox trading platform.")
    print("It can be imported and used in other scripts.")
    print("\nExample usage:")
    print("  from bulenox_ai_selenium import login_bulenox_ai, place_bulenox_trade")
    print("  # Login only")
    print("  bulenox = login_bulenox_ai(debug=True)")
    print("  # Place trade")
    print("  place_bulenox_trade('GBPUSD', 'buy', 1, 1.2500, 1.2700, debug=True)")
    print("=" * 50)