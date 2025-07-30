import os
import json
import time
import random
import datetime
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from utils.executor_stealth import StealthExecutor
from dotenv import load_dotenv

class FibonacciExecutor(StealthExecutor):
    def __init__(self, signal, stopLoss=None, takeProfit=None, stealth_level=2):
        """
        Initialize FibonacciExecutor with Fibonacci retracement strategy
        
        Args:
            signal: Trade signal dictionary with symbol, side, quantity, entry, fib_low, fib_high
            stopLoss: Optional stop loss price
            takeProfit: Optional take profit price
            stealth_level: Level of stealth (1-3, where 3 is most stealthy)
        """
        # Initialize parent class
        super().__init__(signal, stopLoss, takeProfit, stealth_level)
        
        # Fibonacci specific settings
        self.fib_levels = [0.382, 0.5, 0.618, 0.705, 0.786]
        self.tp_percentages = [0.3, 0.2, 0.2, 0.2, 0.1]  # Partial exits
        
        # Set log file for Fibonacci trades
        self.log_file = "logs/fibonacci_trades.json"
        
        # Ensure required fields are present
        self._validate_signal()
        
        # Calculate Fibonacci targets
        self.fib_targets = self._calculate_fib_targets()
        
        # Initialize tracking variables
        self.executed_levels = [False] * len(self.fib_levels)
        self.current_position_size = float(self.signal["quantity"])
        self.entry_price = float(self.signal["entry"])
        
    def _validate_signal(self):
        """
        Validate that the signal contains all required fields for Fibonacci strategy
        """
        required_fields = ["symbol", "side", "quantity", "entry", "fib_low", "fib_high"]
        for field in required_fields:
            if field not in self.signal:
                raise ValueError(f"Missing required field in signal: {field}")
        
        # Convert numeric values to float
        for field in ["entry", "fib_low", "fib_high", "quantity"]:
            self.signal[field] = float(self.signal[field])
        
        # Validate direction
        if "direction" in self.signal:
            self.signal["side"] = "buy" if self.signal["direction"].lower() == "long" else "sell"
    
    def _calculate_fib_targets(self):
        """
        Calculate Fibonacci target levels based on fib_low and fib_high
        """
        fib_low = self.signal["fib_low"]
        fib_high = self.signal["fib_high"]
        is_long = self.signal["side"].lower() == "buy"
        
        fib_targets = []
        for level in self.fib_levels:
            if is_long:
                target = fib_low + (fib_high - fib_low) * level
            else:
                target = fib_high - (fib_high - fib_low) * level
            fib_targets.append(round(target, 2))
        
        return fib_targets
    
    def _get_current_price(self, driver):
        """
        Get the current price from the trading interface
        """
        try:
            # Wait for price element to be present
            price_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'current-price')]")),
                message="Current price element not found"
            )
            
            # Extract price value
            price_text = price_element.text.strip()
            # Remove any non-numeric characters except decimal point
            price_text = ''.join(c for c in price_text if c.isdigit() or c == '.')
            return float(price_text)
        except Exception as e:
            print(f"Error getting current price: {e}")
            # Fallback to entry price if can't get current price
            return self.entry_price
    
    def _close_partial_position(self, driver, percent):
        """
        Close a partial position at a Fibonacci target level
        """
        try:
            # Calculate quantity to close
            close_quantity = round(self.current_position_size * percent, 2)
            
            # Navigate to positions page
            driver.get(f"{self.broker_url}/positions")
            time.sleep(random.uniform(1.0, 2.0))
            
            # Wait for positions table to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'positions-table')]")),
                message="Positions table did not load in time"
            )
            
            # Find position row for our symbol
            position_row = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'position-row') and contains(., '{self.signal['symbol']}')]")),
                message=f"Position for {self.signal['symbol']} not found"
            )
            
            # Click on the position to open details
            if self.stealth_level >= 2:
                self._humanlike_movement(driver, position_row)
            position_row.click()
            
            # Wait for position details panel
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'position-details')]")),
                message="Position details panel did not appear"
            )
            
            # Find partial close input
            quantity_input = driver.find_element(By.XPATH, "//input[@placeholder='Quantity']")
            
            if self.stealth_level >= 2:
                self._humanlike_movement(driver, quantity_input)
                quantity_input.clear()
                self._humanlike_typing(quantity_input, str(close_quantity))
            else:
                quantity_input.clear()
                quantity_input.send_keys(str(close_quantity))
            
            # Find and click close button
            close_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Close Position')]")
            
            if self.stealth_level >= 2:
                self._humanlike_movement(driver, close_button)
            close_button.click()
            
            # Wait for confirmation dialog
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'confirmation-dialog')]")),
                message="Confirmation dialog did not appear"
            )
            
            # Find and click confirm button
            confirm_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
            
            if self.stealth_level >= 2:
                self._humanlike_movement(driver, confirm_button)
            confirm_button.click()
            
            # Update current position size
            self.current_position_size -= close_quantity
            
            # Take screenshot for record
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"{self.screenshot_dir}/fibonacci_partial_close_{timestamp}.png")
            
            print(f"🔒 Closed {percent * 100:.0f}% of position ({close_quantity} units)")
            return True
        except Exception as e:
            print(f"Error closing partial position: {e}")
            # Take screenshot of the error state
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"{self.screenshot_dir}/fibonacci_close_error_{timestamp}.png")
            return False
    
    def _price_rejects_and_retests(self, current_price, target_level):
        """
        Determine if price has rejected from and is now retesting a Fibonacci level
        """
        # This is a simplified implementation
        # In a real system, you would analyze price action more thoroughly
        is_long = self.signal["side"].lower() == "buy"
        
        # For longs, price should have gone above target and then pulled back to it
        # For shorts, price should have gone below target and then pulled back to it
        price_diff = abs(current_price - target_level)
        price_threshold = target_level * 0.001  # 0.1% threshold
        
        # If price is within threshold of the target level, consider it a retest
        return price_diff < price_threshold
    
    def _regenerate_signal_from_current(self, driver, last_tp_level):
        """
        Generate a new signal for reentry after a pullback
        """
        current_price = self._get_current_price(driver)
        is_long = self.signal["side"].lower() == "buy"
        
        # Create a new signal based on current conditions
        new_signal = self.signal.copy()
        
        # Adjust quantity for the new position
        new_signal["quantity"] = self.current_position_size
        
        # Use the last TP level as a new reference point
        if is_long:
            # For longs, the last TP becomes the new entry
            new_signal["entry"] = last_tp_level
            # Adjust fib_low to be slightly below current price
            new_signal["fib_low"] = current_price * 0.995
            # Adjust fib_high to be a projection above
            new_signal["fib_high"] = last_tp_level + (last_tp_level - new_signal["fib_low"])
        else:
            # For shorts, the last TP becomes the new entry
            new_signal["entry"] = last_tp_level
            # Adjust fib_high to be slightly above current price
            new_signal["fib_high"] = current_price * 1.005
            # Adjust fib_low to be a projection below
            new_signal["fib_low"] = last_tp_level - (new_signal["fib_high"] - last_tp_level)
        
        print(f"♻️ Regenerating new signal after pullback...")
        print(f"🎯 New Entry: {new_signal['entry']}, Direction: {'Long' if is_long else 'Short'}")
        print(f"📌 New Fib Range: {new_signal['fib_low']} - {new_signal['fib_high']}")
        
        return new_signal
    
    def _monitor_and_execute_fibonacci_strategy(self, driver):
        """
        Monitor price and execute the Fibonacci strategy
        """
        try:
            # Navigate to trading page
            driver.get(f"{self.broker_url}/trading")
            time.sleep(random.uniform(2.0, 4.0))
            
            # Wait for trading interface to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'trading-interface')]")),
                message="Trading interface did not load in time"
            )
            
            # Initial trade placement
            success = self._place_trade(driver)
            if not success:
                return False
            
            # Log initial trade
            self._log_trade(success)
            
            # Print Fibonacci targets
            is_long = self.signal["side"].lower() == "buy"
            print(f"🎯 Entry: {self.entry_price}, Direction: {'Long' if is_long else 'Short'}")
            print(f"📌 Fib Targets: {self.fib_targets}")
            
            # Monitor loop
            monitoring_duration = 60 * 60  # 1 hour in seconds
            start_time = time.time()
            check_interval = 30  # seconds between price checks
            
            while time.time() - start_time < monitoring_duration:
                # Get current price
                current_price = self._get_current_price(driver)
                print(f"🔍 Price Check: {current_price}")
                
                # Check each Fibonacci target
                for i, target in enumerate(self.fib_targets):
                    if self.executed_levels[i]:
                        continue
                    
                    # Check if price has reached target
                    if (is_long and current_price >= target) or (not is_long and current_price <= target):
                        # Close partial position at this target
                        close_success = self._close_partial_position(driver, self.tp_percentages[i])
                        if close_success:
                            self.executed_levels[i] = True
                
                # Check for retest opportunities if we've hit at least one target
                if any(self.executed_levels):
                    # Find the last hit target level
                    last_tp_index = max(i for i, hit in enumerate(self.executed_levels) if hit)
                    last_tp_level = self.fib_targets[last_tp_index]
                    
                    # Check if price is retesting this level
                    if self._price_rejects_and_retests(current_price, last_tp_level):
                        # Generate new signal for reentry
                        new_signal = self._regenerate_signal_from_current(driver, last_tp_level)
                        
                        # Update current signal and recalculate targets
                        self.signal = new_signal
                        self.fib_targets = self._calculate_fib_targets()
                        self.executed_levels = [False] * len(self.fib_levels)
                        
                        # Execute new trade
                        success = self._place_trade(driver)
                        if success:
                            self._log_trade(success)
                
                # Wait before next check
                time.sleep(check_interval)
            
            return True
        except Exception as e:
            print(f"Error in Fibonacci strategy execution: {e}")
            # Take screenshot of the error state
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"{self.screenshot_dir}/fibonacci_strategy_error_{timestamp}.png")
            return False
    
    def execute_trade(self):
        """
        Execute the Fibonacci retracement strategy with Selenium-based trade execution
        """
        driver = None
        success = False
        
        try:
            # Initialize driver with stealth features
            driver = self._init_driver()
            
            # Random delay before starting
            time.sleep(random.uniform(1.0, 3.0))
            
            # Login to broker
            if not self._login(driver):
                raise Exception("Failed to login to broker")
            
            # Random delay between login and trade
            time.sleep(random.uniform(2.0, 5.0))
            
            # Navigate to trading page
            driver.get(f"{self.broker_url}/trading")
            
            # Wait for trading interface to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'trading-interface') or contains(@id, 'trade')]") ),
                message="Trading interface did not load in time"
            )
            
            # Input symbol
            symbol_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='symbol' or contains(@placeholder, 'Symbol')]") )
            )
            symbol_input.clear()
            symbol_input.send_keys(self.signal.get('symbol'))
            time.sleep(random.uniform(0.5, 1.0))
            
            # Select buy or sell
            side = self.signal.get('side').lower()
            if side == 'buy':
                buy_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Buy') or contains(@class, 'buy')]" )
                buy_button.click()
            elif side == 'sell':
                sell_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sell') or contains(@class, 'sell')]" )
                sell_button.click()
            else:
                raise Exception(f"Invalid trade side: {side}")
            time.sleep(random.uniform(0.5, 1.0))
            
            # Input quantity
            quantity_input = driver.find_element(By.XPATH, "//input[@name='quantity' or contains(@placeholder, 'Quantity')]" )
            quantity_input.clear()
            quantity_input.send_keys(str(self.signal.get('quantity')))
            time.sleep(random.uniform(0.5, 1.0))
            
            # Input entry price if applicable
            entry_price = self.signal.get('entry')
            if entry_price:
                entry_input = driver.find_element(By.XPATH, "//input[@name='entry' or contains(@placeholder, 'Entry')]" )
                entry_input.clear()
                entry_input.send_keys(str(entry_price))
                time.sleep(random.uniform(0.5, 1.0))
            
            # Input stop loss if set
            stop_loss = self.stopLoss
            if stop_loss:
                stop_loss_input = driver.find_element(By.XPATH, "//input[@name='stopLoss' or contains(@placeholder, 'Stop Loss')]" )
                stop_loss_input.clear()
                stop_loss_input.send_keys(str(stop_loss))
                time.sleep(random.uniform(0.5, 1.0))
            
            # Input take profit if set
            take_profit = self.takeProfit
            if take_profit:
                take_profit_input = driver.find_element(By.XPATH, "//input[@name='takeProfit' or contains(@placeholder, 'Take Profit')]" )
                take_profit_input.clear()
                take_profit_input.send_keys(str(take_profit))
                time.sleep(random.uniform(0.5, 1.0))
            
            # Place the trade
            place_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Place Trade') or contains(text(), 'Submit')]" )
            place_button.click()
            
            # Wait for confirmation or success message
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'success') or contains(text(), 'Order placed')]") )
            )
            
            # Log success
            self._log_trade(True)
            success = True
        except Exception as e:
            self._log_trade(False, str(e))
            success = False
            
            # Take screenshot on failure
            if driver:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"logs/fibonacci_trade_failure_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
        finally:
            if driver:
                driver.quit()
        return success