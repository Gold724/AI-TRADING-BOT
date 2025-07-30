import os
import time
import logging
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import the login function and executor
from login_bulenox import login_bulenox_with_profile
from backend.executor_bulenox import BulenoxExecutor

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("auto_trade_demo.log"),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("AUTO_TRADE_DEMO")

# Load environment variables
load_dotenv()

def execute_demo_trade():
    logger.info("Starting automated trade execution demo")
    
    # Create executor instance with headless mode based on environment
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    # Note: We're not passing profile_path as the login_bulenox_with_profile function 
    # reads it directly from environment variables
    executor = BulenoxExecutor(headless=headless)
    logger.info(f"BulenoxExecutor instance created (headless: {headless})")
    
    # Login to Bulenox
    login_success = executor.login()
    if not login_success:
        logger.error("Failed to login to Bulenox. Exiting.")
        return False
    
    logger.info("Successfully logged in to Bulenox")
    
    # Define trade parameters
    trade_url = "https://bulenox.projectx.com/trade"
    
    # Sample trade data (modify as needed for your specific case)
    trade_data = {
        "symbol": "EURUSD",  # Will be mapped to futures symbol 6EU25
        "quantity": "1",    # Number of contracts
        "stop_loss": "50",  # Stop loss in points
        "take_profit": "100" # Take profit in points
    }
    
    # Futures symbol mapping (from BulenoxFuturesExecutor)
    futures_symbols = {
        "GBPUSD": "MBTQ25",  # British Pound futures
        "EURUSD": "6EU25",   # Euro FX futures
        "USDJPY": "6J25",    # Japanese Yen futures
        "ES": "ES25"         # E-mini S&P 500 futures
    }
    
    # Map the symbol to its futures equivalent
    futures_symbol = futures_symbols.get(trade_data["symbol"], trade_data["symbol"])
    logger.info(f"Mapped {trade_data['symbol']} to futures symbol {futures_symbol}")
    
    # Define selectors for the trade form fields
    # These selectors are based on the BulenoxFuturesExecutor implementation
    selectors = {
        "symbol": ("xpath", f"//div[contains(@class, 'symbol-search')]//input"),
        "quantity": ("xpath", "//input[@name='quantity']"),
        "stop_loss": ("xpath", "//input[@name='stopLoss']"),
        "take_profit": ("xpath", "//input[@name='takeProfit']")
    }
    
    # Execute the trade
    try:
        logger.info(f"Attempting to execute trade: {trade_data} (Futures symbol: {futures_symbol})")
        
        # Navigate to trade page
        executor.driver.get(trade_url)
        logger.info("Navigated to trade page")
        
        # Wait for page to load
        wait = WebDriverWait(executor.driver, 15)
        
        # Wait for the trading interface to be visible
        wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'trading-interface')]")))  
        logger.info("Trading interface loaded")
        
        # Take screenshot of initial state
        os.makedirs("logs/screenshots", exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        executor.driver.save_screenshot(f"logs/screenshots/trade_start_{timestamp}.png")
        
        # Enter symbol
        try:
            symbol_input = wait.until(EC.element_to_be_clickable((By.XPATH, selectors["symbol"][1])))
            symbol_input.clear()
            symbol_input.send_keys(futures_symbol)
            time.sleep(1)  # Wait for symbol search results
            symbol_input.send_keys(Keys.ENTER)
            logger.info(f"Set symbol to {futures_symbol}")
        except Exception as e:
            logger.error(f"Error setting symbol: {e}")
            executor.driver.save_screenshot(f"logs/screenshots/symbol_error_{timestamp}.png")
        
        # Enter quantity
        try:
            quantity_input = wait.until(EC.element_to_be_clickable((By.XPATH, selectors["quantity"][1])))
            quantity_input.clear()
            quantity_input.send_keys(trade_data["quantity"])
            logger.info(f"Set quantity to {trade_data['quantity']}")
        except Exception as e:
            logger.error(f"Error setting quantity: {e}")
            executor.driver.save_screenshot(f"logs/screenshots/quantity_error_{timestamp}.png")
        
        # Enter stop loss if provided
        if trade_data.get("stop_loss"):
            try:
                sl_input = wait.until(EC.element_to_be_clickable((By.XPATH, selectors["stop_loss"][1])))
                sl_input.clear()
                sl_input.send_keys(trade_data["stop_loss"])
                logger.info(f"Set stop loss to {trade_data['stop_loss']}")
            except Exception as e:
                logger.error(f"Error setting stop loss: {e}")
                executor.driver.save_screenshot(f"logs/screenshots/sl_error_{timestamp}.png")
        
        # Enter take profit if provided
        if trade_data.get("take_profit"):
            try:
                tp_input = wait.until(EC.element_to_be_clickable((By.XPATH, selectors["take_profit"][1])))
                tp_input.clear()
                tp_input.send_keys(trade_data["take_profit"])
                logger.info(f"Set take profit to {trade_data['take_profit']}")
            except Exception as e:
                logger.error(f"Error setting take profit: {e}")
                executor.driver.save_screenshot(f"logs/screenshots/tp_error_{timestamp}.png")
        
        # Take screenshot before submitting
        executor.driver.save_screenshot(f"logs/screenshots/pre_submission_{timestamp}.png")
        logger.info("Saved pre-submission screenshot")
        
        # Find Buy or Sell button based on trade direction
        trade_side = trade_data.get("side", "buy").lower()
        button_text = "Buy" if trade_side == "buy" else "Sell"
        
        try:
            # Find and click the Buy/Sell button
            action_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, f"//button[contains(text(), '{button_text}')]")
            ))
            
            # Uncomment to actually execute the trade
            # action_button.click()
            logger.info(f"Found {button_text} button (not clicked - demo mode)")
            
            # Wait for confirmation (uncomment when actually executing trades)
            # confirmation = wait.until(EC.presence_of_element_located(
            #     (By.XPATH, "//div[contains(text(), 'Order placed') or contains(text(), 'Trade executed')]")
            # ))
            # logger.info(f"Trade confirmation received: {confirmation.text}")
            
            # Take screenshot after submitting (uncomment when actually executing trades)
            # executor.driver.save_screenshot(f"logs/screenshots/post_submission_{timestamp}.png")
        except Exception as e:
            logger.error(f"Error finding/clicking {button_text} button: {e}")
            executor.driver.save_screenshot(f"logs/screenshots/button_error_{timestamp}.png")
        
        logger.info("Trade execution demo completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during trade execution: {e}")
        # Take screenshot of error state
        executor.driver.save_screenshot("trade_error.png")
        logger.info("Saved error state screenshot")
        return False
    finally:
        # Keep browser open for 10 seconds to see the result
        time.sleep(10)
        # Close the browser
        executor.close()
        logger.info("Browser closed")

if __name__ == "__main__":
    execute_demo_trade()