# executor_bulenox.py

import os
import json
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('executor_bulenox')

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

class BulenoxExecutor:
    def __init__(self, signal, session_id=None):
        self.signal = signal
        self.session_id = session_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # Create logs and screenshots directories
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        self.screenshots_dir = os.path.join(self.logs_dir, "screenshots")
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Log file for trade history
        self.trade_log_file = os.path.join(self.logs_dir, "trade_history.json")
        
        # Initialize trade history if file doesn't exist
        if not os.path.exists(self.trade_log_file):
            with open(self.trade_log_file, 'w') as f:
                json.dump([], f)

    def execute_trade(self, driver, debug=False):
        """Execute a trade on Bulenox platform
        
        Args:
            driver: Selenium WebDriver instance with active Bulenox session
            debug: Enable debug mode with additional logging and screenshots
            
        Returns:
            dict: Trade execution result
        """
        try:
            logger.info(f"Executing trade: {self.signal['symbol']} {self.signal.get('direction', 'buy')}")
            update_heartbeat_status(f"🔄 Executing trade: {self.signal['symbol']} {self.signal.get('direction', 'buy')}")
            
            # Navigate to trading platform if not already there
            if "trading" not in driver.current_url.lower():
                logger.info("Navigating to trading platform...")
                update_heartbeat_status("🔄 Navigating to trading platform...")
                driver.get("https://bulenox.projectx.com/trading")
                time.sleep(3)  # Wait for page to load
            
            # Take screenshot of initial state
            if debug:
                self._take_screenshot(driver, "pre_trade")
            
            # Select the symbol
            update_heartbeat_status(f"🔍 Selecting symbol: {self.signal['symbol']}")
            self._select_symbol(driver, self.signal['symbol'])
            
            # Set trade parameters
            update_heartbeat_status("⚙️ Setting trade parameters...")
            self._set_trade_parameters(driver)
            
            # Execute the trade
            update_heartbeat_status(f"🚀 Placing {self.signal.get('direction', 'buy')} order...")
            success = self._place_trade(driver)
            
            # Take screenshot of final state
            if debug:
                self._take_screenshot(driver, "post_trade")
            
            # Log the trade
            result = self._log_trade(success)
            
            if success:
                update_heartbeat_status(f"✅ Trade executed successfully: {self.signal['symbol']} {self.signal.get('direction', 'buy')}")
            else:
                update_heartbeat_status(f"❌ Trade execution failed: {self.signal['symbol']} {self.signal.get('direction', 'buy')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            update_heartbeat_status(f"❌ Error executing trade: {str(e)[:50]}...")
            self._take_screenshot(driver, "trade_error")
            
            # Log the failed trade
            result = self._log_trade(False, error=str(e))
            
            return result
    
    def _select_symbol(self, driver, symbol):
        """Select the trading symbol"""
        try:
            # Wait for the symbol search box to be available
            update_heartbeat_status(f"🔍 Searching for symbol: {symbol}")
            symbol_search = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Search Symbol']"))
            )
            
            # Clear and enter the symbol
            symbol_search.clear()
            symbol_search.send_keys(symbol)
            time.sleep(1)  # Wait for search results
            
            # Click on the first search result
            search_result = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".symbol-search-result"))
            )
            search_result.click()
            
            logger.info(f"Selected symbol: {symbol}")
            update_heartbeat_status(f"✅ Symbol selected: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error selecting symbol: {e}")
            update_heartbeat_status(f"❌ Error selecting symbol: {str(e)[:50]}...")
            return False
    
    def _set_trade_parameters(self, driver):
        """Set trade parameters (quantity, stop loss, take profit)"""
        try:
            # Set quantity
            quantity_input = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='quantity']")
            ))
            quantity_input.clear()
            quantity_input.send_keys(str(self.signal.get('quantity', 0.01)))
            
            # Set stop loss if provided
            if 'sl' in self.signal:
                sl_input = driver.find_element(By.CSS_SELECTOR, "input[name='stopLoss']")
                sl_input.clear()
                sl_input.send_keys(str(self.signal['sl']))
            
            # Set take profit if provided
            if 'tp' in self.signal:
                tp_input = driver.find_element(By.CSS_SELECTOR, "input[name='takeProfit']")
                tp_input.clear()
                tp_input.send_keys(str(self.signal['tp']))
            
            logger.info("Trade parameters set")
            update_heartbeat_status("✅ Trade parameters set successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting trade parameters: {e}")
            update_heartbeat_status(f"❌ Error setting trade parameters: {str(e)[:50]}...")
            return False
    
    def _place_trade(self, driver):
        """Place the trade"""
        try:
            # Determine which button to click based on trade direction
            direction = self.signal.get('direction', 'buy').lower()
            
            if direction == 'buy':
                button_selector = ".buy-button"
            elif direction == 'sell':
                button_selector = ".sell-button"
            else:
                logger.error(f"Unknown trade direction: {direction}")
                return False
            
            # Click the buy/sell button
            trade_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
            )
            trade_button.click()
            
            # Confirm the trade if confirmation dialog appears
            try:
                confirm_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".confirm-trade-button"))
                )
                confirm_button.click()
            except TimeoutException:
                # No confirmation dialog, which is fine
                pass
            
            # Wait for trade success message
            success_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".trade-success-message"))
            )
            
            logger.info(f"Trade placed successfully: {self.signal['symbol']} {direction}")
            update_heartbeat_status(f"✅ Trade placed successfully: {self.signal['symbol']} {direction}")
            return True
            
        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            update_heartbeat_status(f"❌ Error placing trade: {str(e)[:50]}...")
            return False
    
    def _take_screenshot(self, driver, name):
        """Take a screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{self.session_id}_{name}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    def _log_trade(self, success, error=None):
        """Log the trade to the trade history file"""
        try:
            # Load existing trade history
            with open(self.trade_log_file, 'r') as f:
                trade_history = json.load(f)
            
            # Create trade log entry
            trade_log = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "symbol": self.signal['symbol'],
                "direction": self.signal.get('direction', 'buy'),
                "quantity": self.signal.get('quantity', 0.01),
                "entry": self.signal.get('price', 'MARKET'),
                "tp": self.signal.get('tp'),
                "sl": self.signal.get('sl'),
                "success": success
            }
            
            # Add error message if provided
            if error:
                trade_log["error"] = error
            
            # Add to trade history
            trade_history.append(trade_log)
            
            # Save updated trade history
            with open(self.trade_log_file, 'w') as f:
                json.dump(trade_history, f, indent=2)
            
            logger.info(f"Trade logged: {self.signal['symbol']} {self.signal.get('direction', 'buy')}")
            
            return trade_log
            
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "symbol": self.signal['symbol'],
                "direction": self.signal.get('direction', 'buy'),
                "success": success,
                "error": str(e)
            }

def execute_trade(driver, signal, session_id=None, debug=False):
    """Execute a trade using the BulenoxExecutor
    
    Args:
        driver: Selenium WebDriver instance with active Bulenox session
        signal: Trading signal dictionary
        session_id: Session identifier
        debug: Enable debug mode
        
    Returns:
        dict: Trade execution result
    """
    update_heartbeat_status(f"🔄 Preparing to execute trade: {signal['symbol']} {signal.get('direction', 'buy')}")
    executor = BulenoxExecutor(signal, session_id)
    return executor.execute_trade(driver, debug)

# For testing
if __name__ == "__main__":
    from login_bulenox import login_bulenox_with_profile
    
    # Test signal
    test_signal = {
        "symbol": "EURUSD",
        "direction": "buy",
        "quantity": 0.01,
        "tp": 1.0800,
        "sl": 1.0700
    }
    
    # Login to Bulenox
    driver = login_bulenox_with_profile(debug=True)
    
    if driver:
        # Execute the trade
        result = execute_trade(driver, test_signal, debug=True)
        print(f"Trade execution result: {result}")
        
        # Close the driver
        driver.quit()
    else:
        print("Login failed. Cannot execute trade.")