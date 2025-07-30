import os
import json
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from utils.base_executor import BaseExecutor
from dotenv import load_dotenv

class BulenoxFuturesExecutor(BaseExecutor):
    def __init__(self, signal, stopLoss=None, takeProfit=None, detect_symbol_on_init=False):
        super().__init__(signal, stopLoss, takeProfit)
        # Load environment variables
        load_dotenv()
        
        # Get credentials from environment variables
        self.bulenox_username = os.getenv('BULENOX_USERNAME')
        self.bulenox_password = os.getenv('BULENOX_PASSWORD')
        
        # Get profile paths from environment variables or use defaults
        self.user_data_dir = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data")
        self.profile_directory = os.getenv('BULENOX_PROFILE_NAME', "Profile 13")
        
        # Set screenshot directory
        self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.log_file = "logs/bulenox_trades.json"
        self.screenshot_dir = "logs/screenshots"
        
        # Ensure log directories exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Futures symbol mapping
        self.futures_symbols = {
            "GBPUSD": "MBTQ25",  # British Pound futures
            "EURUSD": "6EU25",   # Euro FX futures
            "USDJPY": "6J25",    # Japanese Yen futures
            "ES": "ES25"         # E-mini S&P 500 futures
        }
        
        # Gold symbol variants
        self.gold_symbols = ["GC", "MGC", "XAUUSD"]
        self.detected_gold_symbol = None
        self.gold_symbol_confirmed = False
        
        # Trading mode (Evaluation or Live)
        self.evaluation_mode = self._detect_trading_mode()
        
        # Optionally detect gold symbol during initialization
        if detect_symbol_on_init and signal["symbol"].upper() in self.gold_symbols:
            try:
                driver = self._init_driver()
                if self._login(driver):
                    self._detect_gold_symbol(driver)
                driver.quit()
            except Exception as e:
                print(f"Error detecting gold symbol during initialization: {e}")
                # Continue without failing - we'll try again during trade execution
    
    def _init_driver(self):
        """Initialize Chrome driver with user profile"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-session-crashed-bubble")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("detach", True)
        
        # Use the existing Chrome profile instead of a temporary one
        chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={self.profile_directory}")
        
        try:
            # First try with WebDriver Manager
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error using WebDriver Manager: {e}")
            print("Trying alternative approach...")
            
            # Try with explicit import of ChromeDriverManager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e2:
                print(f"Error with ChromeDriverManager: {e2}")
                print("Trying with default Chrome...")
                
                # Last resort - try with minimal options
                minimal_options = Options()
                minimal_options.add_argument("--start-maximized")
                driver = webdriver.Chrome(options=minimal_options)
            
        return driver
    
    def _login(self, driver):
        """Login to Bulenox if needed"""
        try:
            driver.get("https://bulenox.projectx.com/login")
            
            # Check if already logged in by looking for dashboard elements
            if "dashboard" in driver.current_url:
                print("Already logged in to Bulenox")
                return True
                
            # Wait for login form
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            
            # Enter credentials
            driver.find_element(By.ID, "email").send_keys(self.bulenox_username)
            driver.find_element(By.ID, "password").send_keys(self.bulenox_password)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            
            # Wait for login to complete
            WebDriverWait(driver, 10).until(
                EC.url_contains("dashboard")
            )
            
            print("Successfully logged in to Bulenox")
            return True
        except Exception as e:
            print(f"Login error: {e}")
            # Take screenshot of the error state
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"{self.screenshot_dir}/bulenox_login_error_{timestamp}.png")
            return False
    
    def _map_to_futures_symbol(self, symbol):
        """Map standard symbol to futures symbol"""
        if symbol in self.futures_symbols:
            return self.futures_symbols[symbol]
        
        # If this is a gold symbol and we have a confirmed gold symbol, use that
        if symbol.upper() in self.gold_symbols and self.detected_gold_symbol:
            return self.detected_gold_symbol
            
        return symbol  # Return original if no mapping exists
        
    def _detect_gold_symbol(self, driver):
        """Detect which gold symbol variant is available in the broker interface"""
        if self.gold_symbol_confirmed:
            print(f"Gold symbol already confirmed as {self.detected_gold_symbol}")
            return self.detected_gold_symbol
            
        print("🕵️ Sentinel is detecting available gold symbol variants...")
        
        # Navigate to trading page if not already there
        if "trading" not in driver.current_url:
            driver.get("https://bulenox.projectx.com/trading")
            time.sleep(3)  # Wait for page to load
        
        # Take screenshot before symbol detection
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{self.screenshot_dir}/gold_symbol_detection_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        
        # Try to find the symbol search input
        selectors = [
            "//input[@placeholder='Search symbol']",
            "//input[@placeholder='Search']",
            "//input[contains(@placeholder, 'symbol')]",
            "//input[contains(@class, 'search')]",
            "//div[contains(@class, 'symbol-selector')]//input",
            "//div[contains(@class, 'header')]//input"
        ]
        
        symbol_input = None
        for selector in selectors:
            try:
                symbol_input = driver.find_element(By.XPATH, selector)
                print(f"Found symbol input using selector: {selector}")
                break
            except Exception:
                continue
        
        if not symbol_input:
            print("Could not find symbol search input, taking screenshot of current page")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.screenshot_dir}/gold_symbol_input_not_found_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            raise Exception("Symbol search input not found")
        
        # Check each gold symbol variant
        for gold_symbol in self.gold_symbols:
            try:
                print(f"Checking availability of gold symbol: {gold_symbol}")
                symbol_input.clear()
                symbol_input.send_keys(gold_symbol)
                time.sleep(1)  # Give time for dropdown to appear
                
                # Take screenshot of search results
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{self.screenshot_dir}/gold_symbol_search_{gold_symbol}_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                
                # Check if symbol appears in dropdown
                try:
                    # Look for the symbol in dropdown results
                    dropdown_results = driver.find_elements(By.XPATH, 
                        f"//div[contains(text(), '{gold_symbol}')] | //div[contains(@class, 'search-results')]/div | //div[contains(@class, 'dropdown')]/div")
                    
                    if dropdown_results and len(dropdown_results) > 0:
                        print(f"🕵️ Sentinel has detected symbol: {gold_symbol}")
                        self.detected_gold_symbol = gold_symbol
                        self.gold_symbol_confirmed = True
                        
                        # Determine trading behavior based on detected symbol
                        if gold_symbol == "GC":
                            print("Standard gold futures detected. Using 1 contract max in Evaluation Mode.")
                        elif gold_symbol == "MGC":
                            print("Micro gold detected. Allowing scaling 1-3 contracts.")
                        elif gold_symbol == "XAUUSD":
                            print("XAUUSD detected. Using pip-based logic (CFD-style).")
                            
                        return gold_symbol
                except Exception as e:
                    print(f"Error checking dropdown for {gold_symbol}: {e}")
            except Exception as e:
                print(f"Error searching for {gold_symbol}: {e}")
        
        # If we get here, no gold symbol was found
        print("⚠️ Gold symbol not confirmed. Sentinel halted trading. Please check platform or preferences.")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{self.screenshot_dir}/gold_symbol_not_found_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        return None
    
    def _place_trade(self, driver):
        """Place a futures trade on Bulenox platform"""
        try:
            # Navigate to trading page
            driver.get("https://bulenox.projectx.com/trading")
            
            # Wait for trading interface to load with longer timeout for futures trading
            print("Waiting for trading interface to load...")
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chart')] | //div[contains(text(), 'Order')] | //div[contains(@class, 'order-panel')]"))
                )
                print("Trading interface loaded successfully")
            except Exception as e:
                print(f"Warning: Trading interface element not found: {e}")
                print("Attempting to continue with trade anyway...")
                # Take screenshot to see what's on the page
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{self.screenshot_dir}/bulenox_interface_not_found_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                # Wait a bit longer just in case
                time.sleep(10)
            
            # Try different possible selectors for the symbol search input
            selectors = [
                "//input[@placeholder='Search symbol']",
                "//input[@placeholder='Search']",
                "//input[contains(@placeholder, 'symbol')]",
                "//input[contains(@class, 'search')]",
                "//div[contains(@class, 'symbol-selector')]//input",
                "//div[contains(@class, 'header')]//input"
            ]
            
            symbol_input = None
            for selector in selectors:
                try:
                    symbol_input = driver.find_element(By.XPATH, selector)
                    print(f"Found symbol input using selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not symbol_input:
                print("Could not find symbol search input, taking screenshot of current page")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{self.screenshot_dir}/bulenox_no_symbol_input_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                raise Exception("Symbol search input not found")
            
            symbol_input.clear()
            
            # Map the symbol to futures symbol if needed
            trading_symbol = self._map_to_futures_symbol(self.signal["symbol"])
            print(f"Trading futures symbol: {trading_symbol}")
            
            symbol_input.send_keys(trading_symbol)
            time.sleep(1)  # Give time for dropdown to appear
            
            # Take screenshot of symbol search
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.screenshot_dir}/bulenox_symbol_search_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            
            # Try to select the symbol from dropdown
            try:
                # First try clicking on the symbol directly if visible
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{trading_symbol}')]"))
                ).click()
                print(f"Selected {trading_symbol} symbol directly")
            except Exception as e:
                print(f"Direct symbol selection not found: {e}")
                # Try alternative selectors
                try:
                    # Try clicking on the first search result
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'search-results')]/div[1] | //div[contains(@class, 'dropdown')]/div[1]"))
                    ).click()
                    print("Selected symbol from search results")
                except Exception as e2:
                    print(f"Alternative dropdown not found: {e2}")
                    # Last resort - try pressing Enter key
                    symbol_input.send_keys(Keys.RETURN)
                    print("Pressed Enter key to select symbol")
            
            # Take screenshot after symbol selection
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.screenshot_dir}/bulenox_symbol_selected_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            
            # Try multiple selectors for quantity input
            quantity_selectors = [
                "//input[@placeholder='Quantity']",
                "//div[contains(text(), 'Quantity')]/following::input[1]",
                "//div[contains(@class, 'order-panel')]//input[1]",
                "//input[contains(@class, 'quantity')]"
            ]
            
            quantity_input = None
            for selector in quantity_selectors:
                try:
                    quantity_input = driver.find_element(By.XPATH, selector)
                    print(f"Found quantity input using selector: {selector}")
                    break
                except Exception:
                    continue
            
            if quantity_input:
                quantity_input.clear()
                quantity_input.send_keys(str(self.signal["quantity"]))
                print(f"Set quantity to {self.signal['quantity']}")
            else:
                print("Could not find quantity input")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{self.screenshot_dir}/bulenox_no_quantity_input_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
            
            # Set stop loss if provided
            if self.stopLoss:
                try:
                    sl_input = driver.find_element(By.XPATH, "//input[@placeholder='Stop Loss']")
                    sl_input.clear()
                    sl_input.send_keys(str(self.stopLoss))
                    print(f"Set stop loss to {self.stopLoss}")
                except Exception as e:
                    print(f"Error setting stop loss: {e}")
            
            # Set take profit if provided
            if self.takeProfit:
                try:
                    tp_input = driver.find_element(By.XPATH, "//input[@placeholder='Take Profit']")
                    tp_input.clear()
                    tp_input.send_keys(str(self.takeProfit))
                    print(f"Set take profit to {self.takeProfit}")
                except Exception as e:
                    print(f"Error setting take profit: {e}")
            
            # Take screenshot before clicking Buy/Sell
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.screenshot_dir}/bulenox_pre_submit_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            
            # Click Buy or Sell button based on side
            try:
                if self.signal["side"].lower() == "buy":
                    # Try different possible selectors for Buy button
                    buy_selectors = [
                        "//button[contains(@class, 'buy-button')]",
                        "//button[text()='Buy']",
                        "//button[contains(text(), 'Buy')]",
                        "//div[contains(@class, 'buy')]/button"
                    ]
                    
                    for selector in buy_selectors:
                        try:
                            buy_button = driver.find_element(By.XPATH, selector)
                            buy_button.click()
                            print(f"Clicked Buy button using selector: {selector}")
                            break
                        except Exception:
                            continue
                else:
                    # Try different possible selectors for Sell button
                    sell_selectors = [
                        "//button[contains(@class, 'sell-button')]",
                        "//button[text()='Sell']",
                        "//button[contains(text(), 'Sell')]",
                        "//div[contains(@class, 'sell')]/button"
                    ]
                    
                    for selector in sell_selectors:
                        try:
                            sell_button = driver.find_element(By.XPATH, selector)
                            sell_button.click()
                            print(f"Clicked Sell button using selector: {selector}")
                            break
                        except Exception:
                            continue
            except Exception as e:
                print(f"Error clicking Buy/Sell button: {e}")
                # Take screenshot of the error state
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{self.screenshot_dir}/bulenox_button_error_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                raise
            
            # Wait for confirmation dialog and confirm
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'confirmation-dialog')] | //div[contains(@class, 'modal')] | //div[contains(text(), 'Confirm')]"))
                )
                
                # Try different possible selectors for Confirm button
                confirm_selectors = [
                    "//button[contains(text(), 'Confirm')]",
                    "//button[text()='Confirm']",
                    "//button[contains(@class, 'confirm-button')]",
                    "//div[contains(@class, 'modal')]//button[contains(text(), 'Confirm')]"
                ]
                
                for selector in confirm_selectors:
                    try:
                        confirm_button = driver.find_element(By.XPATH, selector)
                        confirm_button.click()
                        print(f"Clicked Confirm button using selector: {selector}")
                        break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Error with confirmation dialog: {e}")
                # Take screenshot of the error state
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{self.screenshot_dir}/bulenox_confirm_error_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                raise
            
            # Take screenshot for record
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.screenshot_dir}/bulenox_trade_success_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            
            print(f"Trade executed successfully: {self.signal['side']} {self.signal['quantity']} {trading_symbol}")
            return True
        except Exception as e:
            print(f"Error placing trade: {e}")
            return False
    
    def _log_trade(self, success):
        """Log trade details to JSON file"""
        try:
            # Load existing trades
            try:
                with open(self.log_file, "r") as f:
                    trades = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                trades = []
            
            # Map the symbol to futures symbol
            trading_symbol = self._map_to_futures_symbol(self.signal["symbol"])
            
            # Add new trade
            trade_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "original_symbol": self.signal["symbol"],
                "futures_symbol": trading_symbol,
                "side": self.signal["side"],
                "quantity": self.signal["quantity"],
                "stopLoss": self.stopLoss,
                "takeProfit": self.takeProfit,
                "success": success
            }
            trades.append(trade_record)
            
            # Save updated trades
            with open(self.log_file, "w") as f:
                json.dump(trades, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error logging trade: {e}")
            return False
    
    def execute_trade(self):
        """Execute a futures trade on Bulenox platform"""
        driver = None
        success = False
        result = {"status": "fail"}
        
        try:
            driver = self._init_driver()
            
            # Login to Bulenox
            if not self._login(driver):
                raise Exception("Failed to login to Bulenox")
            
            # Detect gold symbol if trading gold
            is_gold_trade = self.signal["symbol"].upper() in self.gold_symbols
            if is_gold_trade:
                detected_symbol = self._detect_gold_symbol(driver)
                if not detected_symbol:
                    print("⚠️ Gold symbol not confirmed. Sentinel halted trading. Please check platform or preferences.")
                    self._log_trade(False)
                    return {"status": "fail", "message": "Gold symbol not confirmed. Trading halted.", "gold_symbol_detected": False}
                
                # Apply gold-specific trading rules based on detected symbol
                # Use the detected trading mode (Evaluation or Live)
                
                original_quantity = float(self.signal["quantity"])
                adjusted_quantity = original_quantity
                quantity_adjusted = False
                
                mode_str = "Evaluation Mode" if self.evaluation_mode else "Live Mode"
                
                if detected_symbol == "GC" and self.evaluation_mode:
                    # Standard gold futures - use 1 contract max in Evaluation Mode
                    if original_quantity > 1:
                        print(f"🕵️ Sentinel has detected symbol: {detected_symbol}. Executing 1 contract under {mode_str}.")
                        self.signal["quantity"] = 1
                        adjusted_quantity = 1
                        quantity_adjusted = True
                    else:
                        print(f"🕵️ Sentinel has detected symbol: {detected_symbol}. Executing {original_quantity} contract under {mode_str}.")
                        
                elif detected_symbol == "MGC":
                    # Micro gold - allow scaling 1-3 contracts
                    if original_quantity > 3 and self.evaluation_mode:
                        print(f"🕵️ Sentinel has detected symbol: {detected_symbol}. Limiting to 3 contracts under {mode_str}.")
                        self.signal["quantity"] = 3
                        adjusted_quantity = 3
                        quantity_adjusted = True
                    else:
                        print(f"🕵️ Sentinel has detected symbol: {detected_symbol}. Executing {original_quantity} contracts under {mode_str}.")
                        
                elif detected_symbol == "XAUUSD":
                    # XAUUSD - use pip-based logic (CFD-style)
                    print(f"🕵️ Sentinel has detected symbol: {detected_symbol}. Using pip-based logic (CFD-style) under {mode_str}.")
                    # Any specific adjustments for XAUUSD would go here
                    pass
            
            # Place the trade
            success = self._place_trade(driver)
            
            # Log the trade
            self._log_trade(success)
            
            # Prepare detailed result
            result = {"status": "success" if success else "fail"}
            
            # Add gold-specific information if applicable
            if is_gold_trade and self.detected_gold_symbol:
                result.update({
                    "gold_symbol_detected": True,
                    "detected_symbol": self.detected_gold_symbol,
                    "original_quantity": original_quantity,
                    "adjusted_quantity": adjusted_quantity if quantity_adjusted else original_quantity,
                    "quantity_adjusted": quantity_adjusted,
                    "evaluation_mode": self.evaluation_mode
                })
            
            return result
        except Exception as e:
            error_message = str(e)
            print(f"Trade execution failed: {error_message}")
            self._log_trade(False)
            return {"status": "fail", "message": error_message}
        finally:
            if driver:
                driver.quit()
    
    def _detect_trading_mode(self):
        """Determine if we're in Evaluation Mode or Live Mode based on account phase"""
        try:
            # Default to Evaluation Mode for safety
            return True
            
            # In a real implementation, this would check account status
            # For example:
            # driver = self._init_driver()
            # self._login(driver)
            # account_info = driver.find_element(By.XPATH, "//div[contains(@class, 'account-info')]")
            # is_evaluation = "Evaluation" in account_info.text
            # driver.quit()
            # return is_evaluation
        except Exception as e:
            print(f"Error detecting trading mode: {e}")
            # Default to Evaluation Mode for safety
            return True
    
    def health(self):
        """Check if the executor is healthy"""
        try:
            driver = self._init_driver()
            login_success = self._login(driver)
            driver.quit()
            return login_success
        except Exception:
            return False