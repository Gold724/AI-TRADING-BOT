import os
import time
import json
import random
import logging
import datetime
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add the root directory to the Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the login function and executor
from login_bulenox import login_bulenox_with_profile

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "cloud_trade_executor.log")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("CLOUD_TRADE_EXECUTOR")

# Load environment variables
load_dotenv()

class CloudTradeExecutor:
    def __init__(self, account_id=None, session_id=None):
        self.account_id = account_id or os.getenv('BULENOX_ACCOUNT_ID', 'BX64883')
        self.session_id = session_id or f"{self.account_id}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Configure session-specific logging
        self.setup_session_logging()
        
        # Determine if we're running in headless mode (default to headless in cloud/Docker)
        self.headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        
        # Determine if we should take screenshots on failure
        self.screenshot_on_failure = os.getenv('SCREENSHOT_ON_FAILURE', 'true').lower() == 'true'
        
        # Set up screenshot directory
        self.screenshot_dir = os.path.join(log_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Futures symbol mapping
        self.futures_symbols = {
            "GBPUSD": "MBTQ25",  # British Pound futures
            "EURUSD": "6EU25",   # Euro FX futures
            "USDJPY": "6J25",    # Japanese Yen futures
            "ES": "ES25"         # E-mini S&P 500 futures
        }
        
        self.driver = None
        self.logger.info(f"CloudTradeExecutor initialized for account {self.account_id} with session {self.session_id}")
        self.logger.info(f"Running in {'headless' if self.headless else 'visible'} mode")
    
    def setup_session_logging(self):
        """Set up session-specific logging"""
        self.logger = logging.getLogger(f"CLOUD_TRADE_EXECUTOR_{self.session_id}")
        session_log_file = os.path.join(log_dir, f"{self.account_id}-session.log")
        
        # Add a file handler for this session
        file_handler = logging.FileHandler(session_log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Ensure we also log to the console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        
        self.logger.setLevel(logging.INFO)
    
    def login(self):
        """Login to Bulenox using the profile with enhanced profile management"""
        try:
            self.logger.info(f"Attempting to login to Bulenox for account {self.account_id}")
            
            # Use temp profile in cloud/Docker environments
            use_temp_profile = os.getenv('USE_TEMP_PROFILE', 'false').lower() == 'true'
            
            # Set API_MODE environment variable to prevent input prompt
            os.environ['API_MODE'] = 'true'
            
            # Get profile preference from environment variables with fallback mechanism
            preferred_profile = os.getenv('BULENOX_PROFILE_NAME', 'Profile 15')
            fallback_profiles = ['Profile 13', 'Profile 14']
            
            # Check if we have a profile failure history file
            profile_history_file = os.path.join(log_dir, "profile_login_history.json")
            profile_failures = {}
            
            # Load profile failure history if it exists
            if os.path.exists(profile_history_file):
                try:
                    with open(profile_history_file, 'r') as f:
                        profile_failures = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load profile history: {e}")
            
            # Enhanced profile management - Check if preferred profile has failed too many times
            failure_count = profile_failures.get(preferred_profile, {}).get('failures', 0)
            last_failure_time = profile_failures.get(preferred_profile, {}).get('last_failure')
            last_success_time = profile_failures.get(preferred_profile, {}).get('last_success')
            
            self.logger.info(f"Profile {preferred_profile} has {failure_count} recorded failures")
            if last_failure_time:
                self.logger.info(f"Last failure time: {last_failure_time}")
            if last_success_time:
                self.logger.info(f"Last success time: {last_success_time}")
            
            # If preferred profile has failed more than twice, try a fallback
            if failure_count > 2:
                self.logger.warning(f"Profile {preferred_profile} has failed {failure_count} times, trying fallback")
                
                # Always reset cookies for the failed profile
                try:
                    self.logger.info(f"Resetting cookies for {preferred_profile} to re-authenticate fresh")
                    # Set environment variable to indicate cookie reset is needed
                    os.environ['RESET_COOKIES'] = 'true'
                except Exception as e:
                    self.logger.error(f"Failed to set cookie reset flag: {e}")
                
                # Try fallback profiles in order of preference
                profile_switched = False
                for fallback in fallback_profiles:
                    fallback_failures = profile_failures.get(fallback, {}).get('failures', 0)
                    fallback_last_success = profile_failures.get(fallback, {}).get('last_success')
                    
                    # Check if fallback profile is viable (fewer than 3 failures and has successful login history)
                    if fallback_failures <= 2:
                        preferred_profile = fallback
                        self.logger.info(f"Switching to fallback profile: {fallback}")
                        profile_switched = True
                        break
                
                # If no viable fallback found, stick with original but reset cookies
                if not profile_switched:
                    self.logger.warning(f"No viable fallback profiles found. Using original profile {preferred_profile} with reset cookies")
                    # Force cookie reset for original profile
                    os.environ['RESET_COOKIES'] = 'true'
            
            # Set the chosen profile in environment variable
            os.environ['BULENOX_PROFILE_NAME'] = preferred_profile
            self.logger.info(f"Using profile: {preferred_profile}")
            
            # Call login function with parameters matching the root directory implementation
            self.driver = login_bulenox_with_profile(
                use_temp_profile=use_temp_profile,
                max_retries=3,
                debug_mode=True
            )
            
            # Update profile history based on login result
            if self.driver:
                self.logger.info(f"Login successful with profile {preferred_profile}")
                # Reset failure count for successful profile
                if preferred_profile in profile_failures:
                    profile_failures[preferred_profile]['failures'] = 0
                    profile_failures[preferred_profile]['last_success'] = datetime.datetime.now().isoformat()
                else:
                    profile_failures[preferred_profile] = {
                        'failures': 0,
                        'last_success': datetime.datetime.now().isoformat()
                    }
                # Take a screenshot of successful login
                self.take_screenshot("login_success")
                success = True
            else:
                self.logger.error(f"Login failed with profile {preferred_profile}")
                # Increment failure count
                if preferred_profile in profile_failures:
                    profile_failures[preferred_profile]['failures'] = profile_failures[preferred_profile].get('failures', 0) + 1
                else:
                    profile_failures[preferred_profile] = {
                        'failures': 1,
                        'last_failure': datetime.datetime.now().isoformat()
                    }
                success = False
            
            # Save updated profile history
            try:
                with open(profile_history_file, 'w') as f:
                    json.dump(profile_failures, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to save profile history: {e}")
            
            return success
        except Exception as e:
            self.logger.error(f"Login failed with exception: {e}")
            return False
    
    def take_screenshot(self, name_prefix):
        """Take a screenshot and save it to the screenshots directory"""
        if not self.driver:
            self.logger.warning("Cannot take screenshot: No driver available")
            return
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{name_prefix}_{self.account_id}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            self.logger.info(f"Screenshot saved to: {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
    
    def execute_trade(self, signal):
        """Execute a trade based on the provided signal with enhanced JavaScript assistance"""
        if not self.driver:
            self.logger.info("Driver not initialized, initializing now.")
            self.login()
            if not self.driver:
                self.logger.error("Failed to login. Cannot execute trade.")
                self._log_emotional_feedback(False)
                return False
        
        try:
            # Extract trade details from signal
            symbol = signal.get("symbol")
            side = signal.get("side", "buy").lower()
            quantity = signal.get("quantity", 1)
            stop_loss = signal.get("stop_loss")
            take_profit = signal.get("take_profit")
            
            # Map to futures symbol if applicable
            futures_symbol = self.futures_symbols.get(symbol, symbol)
            
            self.logger.info(f"Executing {side} trade for {quantity} {futures_symbol} (original: {symbol})")
            
            # Navigate to trade page
            trade_url = "https://bulenox.projectx.com/trade"
            self.logger.info(f"Navigating to: {trade_url}")
            
            try:
                self.driver.get(trade_url)
                self.logger.info("Successfully navigated to trade page")
                
                # Enhanced DOM Safety Measures - UI Load Detection
                self.logger.info("Waiting for UI to fully load using enhanced detection...")
                
                # First wait for basic page load
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Wait for unique markers like Order module using JavaScript
                try:
                    WebDriverWait(self.driver, 15).until(
                        lambda d: d.execute_script("return document.querySelector('.order-module') !== null")
                    )
                    self.logger.info("Order module detected in DOM via JavaScript")
                except Exception as e:
                    self.logger.warning(f"Order module not detected with JS: {e}, trying alternative selectors")
                    # Try alternative selectors if the order module isn't found
                    try:
                        WebDriverWait(self.driver, 15).until(
                            lambda d: d.execute_script(
                                "return (document.querySelector('.trade-form') !== null || "
                                "document.querySelector('.trading-panel') !== null || "
                                "document.querySelector('button:contains(\'BUY\')') !== null)"
                            )
                        )
                        self.logger.info("Alternative trading UI elements detected via JavaScript")
                    except Exception as alt_e:
                        self.logger.warning(f"Failed to detect trading UI elements via JavaScript: {alt_e}")
                        # Try traditional XPath as fallback
                        try:
                            WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'order-module') or contains(@class, 'trade-form') or contains(@class, 'trading-panel')]"))
                            )
                            self.logger.info("Trading UI elements detected via XPath")
                        except Exception as xpath_e:
                            self.logger.error(f"Failed to detect trading UI elements via XPath: {xpath_e}")
                            # Continue anyway, but log the issue
                
                # Check for "Time and Sales" tab as another indicator of UI readiness
                try:
                    # First try JavaScript detection
                    time_sales_present = self.driver.execute_script(
                        "return document.querySelector('*:contains(\'Time and Sales\')') !== null"
                    )
                    if time_sales_present:
                        self.logger.info("'Time and Sales' tab detected via JavaScript, UI appears fully loaded")
                    else:
                        # Try XPath as fallback
                        try:
                            time_sales_element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Time and Sales') or contains(@class, 'time-sales')]"))
                            )
                            self.logger.info("'Time and Sales' tab detected via XPath")
                        except Exception as ts_xpath_e:
                            self.logger.warning(f"'Time and Sales' tab not detected via XPath: {ts_xpath_e}")
                except Exception as e:
                    self.logger.warning(f"Could not check for 'Time and Sales' tab via JavaScript: {e}")
                
                # Take screenshot to see what we're working with
                self.take_screenshot("trade_page_loaded")
                
                # Check current URL
                current_url = self.driver.current_url
                self.logger.info(f"Current URL after navigation: {current_url}")
                
                # Get page title
                page_title = self.driver.title
                self.logger.info(f"Page title: {page_title}")
                
                # Use JavaScript to check for account balance (bonus feature)
                try:
                    # Try multiple approaches to find account balance
                    js_balance_checks = [
                        "return window.accountBalance || null",
                        "return document.querySelector('.account-balance, .balance, .account-value')?.textContent || null",
                        "return Array.from(document.querySelectorAll('*')).find(el => el.textContent.includes('Balance:'))?.textContent || null"
                    ]
                    
                    for js_check in js_balance_checks:
                        account_balance = self.driver.execute_script(js_check)
                        if account_balance:
                            self.logger.info(f"Account balance from JS: {account_balance}")
                            break
                    
                    if not account_balance:
                        self.logger.warning("Could not retrieve account balance via any JS method")
                except Exception as e:
                    self.logger.warning(f"Error retrieving account balance via JS: {e}")
                
                # Use JavaScript to check for last signal (bonus feature)
                try:
                    # Try multiple approaches to find last signal
                    js_signal_checks = [
                        "return window.lastSignal || null",
                        "return document.querySelector('.last-signal, .signal, .trade-signal')?.textContent || null",
                        "return Array.from(document.querySelectorAll('*')).find(el => el.textContent.includes('Signal:'))?.textContent || null"
                    ]
                    
                    for js_check in js_signal_checks:
                        last_signal = self.driver.execute_script(js_check)
                        if last_signal:
                            self.logger.info(f"Last signal from JS: {last_signal}")
                            break
                    
                    if not last_signal:
                        self.logger.warning("Could not retrieve last signal via any JS method")
                except Exception as e:
                    self.logger.warning(f"Error retrieving last signal via JS: {e}")
                
            except Exception as e:
                self.logger.error(f"Failed to navigate to trade page: {e}")
                self.take_screenshot("navigation_error")
                self.log_trade_status(signal, "failed", f"Navigation error: {str(e)}")
                self._log_emotional_feedback(False)
                return False
            
            # Execute the actual trade with enhanced button identification and JavaScript fallback
            try:
                # Find and interact with symbol input
                self.logger.info(f"Looking for symbol input to enter {futures_symbol}")
                
                # Try multiple selectors for symbol input
                symbol_input = None
                symbol_selectors = [
                    "//input[@type='text' and @placeholder='Symbol']",
                    "//div[contains(@class, 'symbol-search')]//input",
                    "//input[contains(@class, 'symbol')]"
                ]
                
                for selector in symbol_selectors:
                    try:
                        symbol_input = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        self.logger.info(f"Found symbol input using selector: {selector}")
                        break
                    except Exception:
                        continue
                
                if not symbol_input:
                    self.logger.error("Could not find symbol input field")
                    raise Exception("Symbol input field not found")
                
                # Clear and enter symbol with human-like typing
                symbol_input.clear()
                for char in futures_symbol:
                    symbol_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))  # Human-like typing delay
                
                self.logger.info(f"Entered symbol: {futures_symbol}")
                time.sleep(1)  # Wait for symbol to register
                
                # Try to select from dropdown if it appears
                try:
                    dropdown_item = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{futures_symbol}')]")),
                    )
                    dropdown_item.click()
                    self.logger.info("Selected symbol from dropdown")
                except Exception as e:
                    self.logger.warning(f"No dropdown selection needed or available: {e}")
                    # Press Enter as fallback
                    symbol_input.send_keys(Keys.ENTER)
                
                # Set quantity
                self.logger.info(f"Setting quantity to {quantity}")
                quantity_selectors = [
                    "//input[@type='number']",
                    "//input[contains(@placeholder, 'Qty') or contains(@placeholder, 'Quantity')]",
                    "//label[contains(text(), 'Quantity') or contains(text(), 'Qty')]/following::input"
                ]
                
                quantity_input = None
                for selector in quantity_selectors:
                    try:
                        quantity_input = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        self.logger.info(f"Found quantity input using selector: {selector}")
                        break
                    except Exception:
                        continue
                
                if quantity_input:
                    # Clear existing value and set new quantity
                    quantity_input.clear()
                    for char in str(quantity):
                        quantity_input.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))  # Human-like typing delay
                    self.logger.info(f"Set quantity to {quantity}")
                else:
                    self.logger.warning("Could not find quantity input, using default")
                
                # Set stop loss if provided
                if stop_loss:
                    self.logger.info(f"Setting stop loss to {stop_loss}")
                    stop_loss_selectors = [
                        "//input[contains(@placeholder, 'Stop') or contains(@placeholder, 'SL')]",
                        "//label[contains(text(), 'Stop Loss')]/following::input",
                        "//div[contains(text(), 'Stop Loss')]/following::input"
                    ]
                    
                    stop_loss_input = None
                    for selector in stop_loss_selectors:
                        try:
                            stop_loss_input = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            self.logger.info(f"Found stop loss input using selector: {selector}")
                            break
                        except Exception:
                            continue
                    
                    if stop_loss_input:
                        stop_loss_input.clear()
                        for char in str(stop_loss):
                            stop_loss_input.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.15))  # Human-like typing delay
                        self.logger.info(f"Set stop loss to {stop_loss}")
                    else:
                        self.logger.warning("Could not find stop loss input")
                
                # Set take profit if provided
                if take_profit:
                    self.logger.info(f"Setting take profit to {take_profit}")
                    take_profit_selectors = [
                        "//input[contains(@placeholder, 'Take Profit') or contains(@placeholder, 'TP')]",
                        "//label[contains(text(), 'Take Profit')]/following::input",
                        "//div[contains(text(), 'Take Profit')]/following::input"
                    ]
                    
                    take_profit_input = None
                    for selector in take_profit_selectors:
                        try:
                            take_profit_input = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            self.logger.info(f"Found take profit input using selector: {selector}")
                            break
                        except Exception:
                            continue
                    
                    if take_profit_input:
                        take_profit_input.clear()
                        for char in str(take_profit):
                            take_profit_input.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.15))  # Human-like typing delay
                        self.logger.info(f"Set take profit to {take_profit}")
                    else:
                        self.logger.warning("Could not find take profit input")
                
                # Click Buy/Sell button based on side with enhanced identification
                button_text = "BUY" if side.lower() == "buy" else "SELL"
                self.logger.info(f"Looking for {button_text} button")
                
                # Take a screenshot before clicking
                self.take_screenshot(f"before_{button_text.lower()}_click")
                
                # Count how many BUY or SELL buttons exist on the page
                all_buttons = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{button_text}')]")
                button_count = len(all_buttons)
                self.logger.info(f"Found {button_count} {button_text} buttons on the page")
                
                # Try to find the button
                button = None
                
                # First try to find button specifically within the left-side "Order" module
                try:
                    button = self.driver.find_element(By.XPATH, f"(//div[contains(@class, 'order-module') or contains(@class, 'trade-form')]//button[contains(text(), '{button_text}')])[1]")
                    self.logger.info(f"Found {button_text} button in Order module")
                except Exception:
                    self.logger.warning(f"Could not find {button_text} button in Order module")
                
                # If not found, try with sibling context using unique structures
                if not button:
                    try:
                        # Look for button near Order Type, Market, or input boxes
                        sibling_selectors = [
                            f"//label[text()='Order Type']/../..//button[contains(text(), '{button_text}')]",
                            f"//label[text()='Market']/../..//button[contains(text(), '{button_text}')]",
                            f"//input[@type='number']/../..//button[contains(text(), '{button_text}')]"
                        ]
                        
                        for selector in sibling_selectors:
                            try:
                                button = self.driver.find_element(By.XPATH, selector)
                                self.logger.info(f"Found {button_text} button with sibling context: {selector}")
                                break
                            except Exception:
                                continue
                    except Exception as e:
                        self.logger.warning(f"Error finding {button_text} button with sibling context: {e}")
                
                # If still not found, try by button index inside parent container
                if not button and button_count > 0:
                    try:
                        # Try to find the first button in the trading panel
                        button = self.driver.find_element(By.XPATH, f"(//button[contains(text(), '{button_text}')])[1]")
                        self.logger.info(f"Found {button_text} button by index")
                    except Exception:
                        self.logger.warning(f"Could not find {button_text} button by index")
                
                # If still not found, try by distinct button class or container proximity
                if not button:
                    try:
                        class_selectors = [
                            f"//button[contains(@class, 'buy-button') or contains(@class, 'sell-button')][contains(text(), '{button_text}')]",
                            f"//button[contains(@class, 'primary')][contains(text(), '{button_text}')]",
                            f"//div[contains(@class, 'trading-panel')]//button[contains(text(), '{button_text}')]"
                        ]
                        
                        for selector in class_selectors:
                            try:
                                button = self.driver.find_element(By.XPATH, selector)
                                self.logger.info(f"Found {button_text} button with class selector: {selector}")
                                break
                            except Exception:
                                continue
                    except Exception as e:
                        self.logger.warning(f"Error finding {button_text} button with class selectors: {e}")
                
                # If still not found, try a more generic approach
                if not button:
                    try:
                        button = self.driver.find_element(By.XPATH, f"//button[contains(., '{button_text}')]")
                        self.logger.info(f"Found {button_text} button with generic approach")
                    except Exception as e:
                        self.logger.error(f"Could not find {button_text} button with any approach: {e}")
                        raise Exception(f"{button_text} button not found")
                
                # Scroll the button into view using JavaScript
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", button)
                self.logger.info(f"Scrolled {button_text} button into view")
                time.sleep(0.5)  # Short wait after scrolling
                
                # Try standard click first
                try:
                    button.click()
                    self.logger.info(f"Clicked {button_text} button with standard click")
                except Exception as click_error:
                    self.logger.warning(f"Standard click failed: {click_error}. Trying JavaScript click...")
                    # Fallback to JavaScript click if standard click fails
                    try:
                        self.driver.execute_script("arguments[0].click();", button)
                        self.logger.info(f"Clicked {button_text} button with JavaScript click")
                    except Exception as js_error:
                        self.logger.error(f"JavaScript click also failed: {js_error}")
                        raise Exception(f"Failed to click {button_text} button: {js_error}")
                
                # Take a screenshot after clicking
                self.take_screenshot(f"after_{button_text.lower()}_click")
                
                # Wait for confirmation dialog if it appears
                try:
                    WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dialog') or contains(@class, 'modal')]")))
                    self.logger.info("Confirmation dialog appeared")
                    
                    # Find and click the confirm button
                    confirm_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm') or contains(text(), 'OK') or contains(text(), 'Yes')]")
                    try:
                        confirm_button.click()
                        self.logger.info("Clicked confirm button with standard click")
                    except Exception as confirm_click_error:
                        self.logger.warning(f"Standard confirm click failed: {confirm_click_error}. Trying JavaScript click...")
                        self.driver.execute_script("arguments[0].click();", confirm_button)
                        self.logger.info("Clicked confirm button with JavaScript click")
                except Exception as e:
                    self.logger.info(f"No confirmation dialog appeared or error handling it: {e}")
                
                # Wait for success message or trade to appear in history
                time.sleep(2)  # Short wait for UI to update
                
                # Log successful trade
                self.logger.info(f"Successfully executed {side} trade for {quantity} {futures_symbol}")
                self.log_trade_status(signal, "success", "Trade executed successfully")
                
                # Add emotional feedback for success
                self._log_emotional_feedback(True)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error during trade execution: {e}")
                self.take_screenshot("trade_execution_error")
                self.log_trade_status(signal, "failed", f"Trade execution error: {str(e)}")
                self._log_emotional_feedback(False)
                return False
            
        except Exception as e:
            self.logger.error(f"Error during trade execution: {e}")
            self.take_screenshot("trade_error")
            
            # Log trade to status.json
            self.log_trade_status(signal, "failed", str(e))
            
            # Add emotional feedback for failure
            self._log_emotional_feedback(False)
            
            return False
    
    def _log_emotional_feedback(self, success):
        """Add emotional intelligence layer to trade feedback"""
        if success:
            message = "🟢 Mountains were moved. You just claimed a new peak!"
        else:
            message = "🔴 Even stars collapse before becoming supernovae. Reset. Rise. Reload."
        
        self.logger.info(message)
        
        # Also save to a dedicated emotional feedback file for potential UI display
        try:
            feedback_file = os.path.join(log_dir, "emotional_feedback.json")
            
            # Load existing feedback if available
            try:
                with open(feedback_file, 'r') as f:
                    feedback_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                feedback_data = []
            
            # Add new feedback
            feedback_data.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "success": success,
                "message": message,
                "session_id": self.session_id
            })
            
            # Keep only the last 100 entries
            if len(feedback_data) > 100:
                feedback_data = feedback_data[-100:]
            
            # Save updated feedback
            with open(feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save emotional feedback: {e}")
    
    def log_trade_status(self, signal, status, error_message=None):
        """Log trade status to status.json"""
        status_file = os.path.join(log_dir, "status.json")
        
        # Create status entry
        status_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "account_id": self.account_id,
            "session_id": self.session_id,
            "signal": signal,
            "status": status
        }
        
        if error_message:
            status_entry["error"] = error_message
        
        # Load existing status file if it exists
        try:
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
            else:
                status_data = {"trades": []}
            
            # Add new entry
            status_data["trades"].append(status_entry)
            
            # Update last_update timestamp
            status_data["last_update"] = datetime.datetime.now().isoformat()
            
            # Write back to file
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            
            self.logger.info(f"Trade status logged to {status_file}")
        except Exception as e:
            self.logger.error(f"Failed to log trade status: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("Browser closed")

# Example usage
def main():
    # Parse command line arguments if needed
    import argparse
    parser = argparse.ArgumentParser(description='Execute trades on Bulenox')
    parser.add_argument('--account_id', type=str, help='Bulenox account ID')
    parser.add_argument('--signal', type=str, help='Trade signal in JSON format')
    parser.add_argument('--session_id', type=str, help='Session ID for logging')
    
    args = parser.parse_args()
    
    # Create executor
    executor = CloudTradeExecutor(
        account_id=args.account_id,
        session_id=args.session_id
    )
    
    # Login
    executor.login()
    if not executor.driver:
        logger.error("Failed to login to Bulenox. Exiting.")
        return False
    
    # Execute trade if signal provided
    if args.signal:
        try:
            signal = json.loads(args.signal)
            executor.execute_trade(signal)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON signal: {args.signal}")
    else:
        # Demo trade for testing
        demo_signal = {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1,
            "stop_loss": 50,
            "take_profit": 100
        }
        
        logger.info(f"Executing demo trade: {demo_signal}")
        executor.execute_trade(demo_signal)
    
    # Keep browser open for a few seconds to see the result
    time.sleep(5)
    
    # Close browser
    executor.close()
    
    return True

if __name__ == "__main__":
    main()