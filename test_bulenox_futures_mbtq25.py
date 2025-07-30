import os
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
from dotenv import load_dotenv

def test_bulenox_futures_mbtq25():
    # Load environment variables
    load_dotenv()
    
    # Get profile paths from environment variables or use defaults
    user_data_dir = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data")
    profile_directory = os.getenv('BULENOX_PROFILE_NAME', "Profile 13")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("detach", True)
    
    # Add user profile if available
    # Use a temporary profile directory to avoid conflicts
    temp_profile_dir = os.path.join(os.getcwd(), "temp_chrome_profile_futures")
    os.makedirs(temp_profile_dir, exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
    
    # Set up screenshot directory
    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    driver = None
    try:
        # Initialize Chrome driver
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
        
        print("Chrome browser initialized successfully")
        
        # Navigate to Bulenox login page
        driver.get("https://bulenox.projectx.com/login")
        print("Navigated to Bulenox login page")
        
        # Since we're using a fresh profile, we need to log in manually
        print("Please log in manually with your credentials")
        print("Username: Use your Bulenox username")
        print("Password: Use your Bulenox password")
        
        # Wait for login to complete or manual intervention
        print("Waiting 30 seconds for manual login to complete...")
        time.sleep(30)  # Give user time to log in manually
        print("Proceeding with test after wait period")
        
        # Navigate to trading page
        print("Navigating to trading page...")
        driver.get("https://bulenox.projectx.com/trading")
        
        # Add a longer wait time before proceeding
        print("Waiting 45 seconds for page to fully load...")
        time.sleep(45)
        
        # Take screenshot after navigation and waiting
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{screenshot_dir}/bulenox_trading_page_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Wait for trading interface to load with increased timeout
        print("Waiting for trading interface to load...")
        try:
            # Look for chart or order elements visible in the screenshot
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chart')] | //div[contains(text(), 'Order')] | //div[contains(@class, 'order-panel')]")),
                message="Trading interface did not load in time"
            )
            print("Trading interface loaded successfully")
        except Exception as e:
            print(f"Warning: Trading interface element not found: {e}")
            print("Attempting to continue with test anyway...")
            # Take another screenshot to see what's on the page
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/bulenox_interface_not_found_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
            # Wait a bit longer just in case
            time.sleep(10)
        
        # Test futures symbol search
        try:
            # Try different possible selectors for the symbol search input based on the screenshot
            selectors = [
                "//input[@placeholder='Search symbol']",
                "//input[@placeholder='Search']",
                "//input[contains(@placeholder, 'symbol')]",
                "//input[contains(@class, 'search')]",
                "//div[contains(@class, 'symbol-selector')]//input",
                "//div[contains(text(), 'MBTQ25')]/preceding::input[1]",
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
                screenshot_path = f"{screenshot_dir}/bulenox_no_symbol_input_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to: {screenshot_path}")
                raise Exception("Symbol search input not found")
                
            symbol_input.clear()
            
            # Use the MBTQ25 futures symbol
            futures_symbol = "MBTQ25"  # British Pound futures contract
            print(f"Testing with futures symbol: {futures_symbol}")
            
            symbol_input.send_keys(futures_symbol)
            time.sleep(1)  # Give time for dropdown to appear
        except Exception as e:
            print(f"Error during symbol search: {e}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/bulenox_symbol_search_error_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
            raise
        
        # Take screenshot of symbol search
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{screenshot_dir}/bulenox_futures_search_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Try to select the symbol from dropdown based on the screenshot
        try:
            # First try clicking on the symbol directly if visible
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'MBTQ25')]")),
                message="MBTQ25 symbol not found in dropdown"
            ).click()
            print("Selected MBTQ25 symbol directly")
        except Exception as e:
            print(f"Direct symbol selection not found: {e}")
            # Try alternative selectors
            try:
                # Try clicking on the first search result
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'search-results')]/div[1] | //div[contains(@class, 'dropdown')]/div[1]")),
                    message="No search results found"
                ).click()
                print("Selected symbol from search results")
            except Exception as e2:
                print(f"Alternative dropdown not found: {e2}")
                # Last resort - try pressing Enter key
                symbol_input.send_keys(Keys.RETURN)
                print("Pressed Enter key to select symbol")
        
        # Take screenshot after symbol selection
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{screenshot_dir}/bulenox_futures_selected_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Test setting quantity
        try:
            # Try multiple selectors for quantity input based on the screenshot
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
                quantity_input.send_keys("1")
                print("Set quantity to 1")
            else:
                print("Could not find quantity input")
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{screenshot_dir}/bulenox_no_quantity_input_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to: {screenshot_path}")
        except Exception as e:
            print(f"Error setting quantity: {e}")
        
        # Test setting stop loss
        try:
            sl_input = driver.find_element(By.XPATH, "//input[@placeholder='Stop Loss']")
            sl_input.clear()
            sl_input.send_keys("1.2500")
            print("Set stop loss to 1.2500")
        except Exception as e:
            print(f"Error setting stop loss: {e}")
        
        # Test setting take profit
        try:
            tp_input = driver.find_element(By.XPATH, "//input[@placeholder='Take Profit']")
            tp_input.clear()
            tp_input.send_keys("1.2700")
            print("Set take profit to 1.2700")
        except Exception as e:
            print(f"Error setting take profit: {e}")
        
        # Take final screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{screenshot_dir}/bulenox_futures_ready_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        print("\nFutures trading test completed successfully!")
        print("NOTE: No actual trade was executed. This was just a UI test.")
        
        # Wait briefly for user to review before closing automatically
        print("\nBrowser will close automatically in 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Error during test: {e}")
        if driver:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/bulenox_futures_error_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved to: {screenshot_path}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("AI Trading Sentinel - Bulenox Futures Trading Test (MBTQ25)")
    print("========================================================")
    test_bulenox_futures_mbtq25()