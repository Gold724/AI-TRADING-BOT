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
from webdriver_manager.chrome import ChromeDriverManager
from utils.base_executor import BaseExecutor
from dotenv import load_dotenv

class BulenoxExecutor(BaseExecutor):
    def __init__(self, signal, stopLoss=None, takeProfit=None):
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
        
        if self.user_data_dir and self.profile_directory:
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
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                
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
            return False
    
    def _place_trade(self, driver):
        """Place a trade on Bulenox platform"""
        try:
            # Navigate to trading page
            driver.get("https://bulenox.projectx.com/trading")
            
            # Wait for trading interface to load with longer timeout for futures trading
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'trading-interface')]")),
                message="Trading interface did not load in time"
            )
            
            # Select symbol
            symbol_input = driver.find_element(By.XPATH, "//input[@placeholder='Search symbol']")
            symbol_input.clear()
            
            # Format the symbol for futures if needed
            trading_symbol = self.signal["symbol"]
            print(f"Trading symbol: {trading_symbol}")
            
            symbol_input.send_keys(trading_symbol)
            time.sleep(1)  # Give time for dropdown to appear
            
            # Wait for and select the symbol from dropdown with more robust handling
            try:
                # First try the standard dropdown
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'symbol-dropdown')]/div[1]"))
                ).click()
            except Exception as e:
                print(f"Standard dropdown not found: {e}")
                # Try alternative selectors for futures trading interface
                try:
                    # Try clicking on the first search result
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'search-results')]/div[1]"))
                    ).click()
                except Exception as e2:
                    print(f"Alternative dropdown not found: {e2}")
                    # Last resort - try pressing Enter key
                    from selenium.webdriver.common.keys import Keys
                    symbol_input.send_keys(Keys.RETURN)
            
            # Take screenshot after symbol selection
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"{self.screenshot_dir}/bulenox_symbol_selection_{timestamp}.png")
            
            # Set quantity
            quantity_input = driver.find_element(By.XPATH, "//input[@placeholder='Quantity']")
            quantity_input.clear()
            quantity_input.send_keys(str(self.signal["quantity"]))
            
            # Set stop loss if provided
            if self.stopLoss:
                sl_input = driver.find_element(By.XPATH, "//input[@placeholder='Stop Loss']")
                sl_input.clear()
                sl_input.send_keys(str(self.stopLoss))
            
            # Set take profit if provided
            if self.takeProfit:
                tp_input = driver.find_element(By.XPATH, "//input[@placeholder='Take Profit']")
                tp_input.clear()
                tp_input.send_keys(str(self.takeProfit))
            
            # Click Buy or Sell button based on side
            try:
                if self.signal["side"].lower() == "buy":
                    # Try different possible selectors for Buy button
                    try:
                        driver.find_element(By.XPATH, "//button[contains(@class, 'buy-button')]").click()
                    except:
                        try:
                            driver.find_element(By.XPATH, "//button[text()='Buy']").click()
                        except:
                            driver.find_element(By.XPATH, "//button[contains(text(), 'Buy')]").click()
                else:
                    # Try different possible selectors for Sell button
                    try:
                        driver.find_element(By.XPATH, "//button[contains(@class, 'sell-button')]").click()
                    except:
                        try:
                            driver.find_element(By.XPATH, "//button[text()='Sell']").click()
                        except:
                            driver.find_element(By.XPATH, "//button[contains(text(), 'Sell')]").click()
            except Exception as e:
                print(f"Error clicking Buy/Sell button: {e}")
                # Take screenshot of the error state
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                driver.save_screenshot(f"{self.screenshot_dir}/bulenox_button_error_{timestamp}.png")
                raise
            
            # Wait for confirmation dialog and confirm
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'confirmation-dialog')]")),
                    message="Confirmation dialog did not appear"
                )
                
                # Try different possible selectors for Confirm button
                try:
                    driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]").click()
                except:
                    try:
                        driver.find_element(By.XPATH, "//button[text()='Confirm']").click()
                    except:
                        driver.find_element(By.XPATH, "//button[contains(@class, 'confirm-button')]").click()
            except Exception as e:
                print(f"Error with confirmation dialog: {e}")
                # Take screenshot of the error state
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                driver.save_screenshot(f"{self.screenshot_dir}/bulenox_confirm_error_{timestamp}.png")
                raise
            
            # Take screenshot for record
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.screenshot_dir}/bulenox_trade_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            
            print(f"Trade executed successfully: {self.signal['side']} {self.signal['quantity']} {self.signal['symbol']}")
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
            
            # Add new trade
            trade_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "symbol": self.signal["symbol"],
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
        """Execute a trade on Bulenox platform"""
        driver = None
        success = False
        
        try:
            driver = self._init_driver()
            
            # Login to Bulenox
            if not self._login(driver):
                raise Exception("Failed to login to Bulenox")
            
            # Place the trade
            success = self._place_trade(driver)
            
            # Log the trade
            self._log_trade(success)
            
            return success
        except Exception as e:
            print(f"Trade execution failed: {e}")
            self._log_trade(False)
            return False
        finally:
            if driver:
                driver.quit()
    
    def health(self):
        """Check if the executor is healthy"""
        try:
            driver = self._init_driver()
            login_success = self._login(driver)
            driver.quit()
            return login_success
        except Exception:
            return False