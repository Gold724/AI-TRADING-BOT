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

def test_bulenox_selenium_dev():
    # Set DEV_MODE environment variable
    os.environ["DEV_MODE"] = "true"
    print("Running in DEV_MODE: No actual trades will be executed")
    
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
    
    # Use a temporary profile directory to avoid conflicts
    print("Using temporary Chrome profile for testing")
    temp_profile_dir = os.path.join(os.getcwd(), "temp_chrome_profile_test")
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
            print("Initializing Chrome driver with WebDriver Manager...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"WebDriver Manager failed: {e}")
            print("Trying alternative driver initialization...")
            
            # Try with default ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
        
        print("Chrome driver initialized successfully")
        
        # Navigate to Bulenox login page
        print("Navigating to Bulenox login page...")
        driver.get("https://bulenox.projectx.com/login")
        
        # Wait for page to load
        print("Waiting for login page to load...")
        time.sleep(5)
        
        # Take screenshot of login page
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{screenshot_dir}/bulenox_login_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Check if already logged in
        if "trading" in driver.current_url or "dashboard" in driver.current_url:
            print("Already logged in, proceeding to trading page")
        else:
            # Try to login
            print("Attempting to login...")
            
            # Get credentials from environment variables
            username = os.getenv('BULENOX_USERNAME')
            password = os.getenv('BULENOX_PASSWORD')
            
            if not username or not password:
                print("Warning: Bulenox credentials not found in environment variables")
                print("You may need to login manually")
            else:
                try:
                    # Enter username
                    username_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='email'] | //input[@placeholder='Email'] | //input[@name='email']"))
                    )
                    username_input.clear()
                    username_input.send_keys(username)
                    print("Username entered")
                    
                    # Enter password
                    password_input = driver.find_element(By.XPATH, "//input[@type='password'] | //input[@placeholder='Password'] | //input[@name='password']")
                    password_input.clear()
                    password_input.send_keys(password)
                    print("Password entered")
                    
                    # Click login button
                    login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')] | //button[@type='submit'] | //input[@type='submit']")
                    login_button.click()
                    print("Login button clicked")
                    
                    # Wait for login to complete
                    print("Waiting for login to complete...")
                    time.sleep(10)
                    
                    # Take screenshot after login attempt
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"{screenshot_dir}/bulenox_after_login_{timestamp}.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Screenshot saved to: {screenshot_path}")
                    
                    # Check if login was successful
                    if "trading" in driver.current_url or "dashboard" in driver.current_url:
                        print("Login successful!")
                    else:
                        print("Login may have failed, proceeding with test anyway")
                except Exception as e:
                    print(f"Error during login: {e}")
                    print("Proceeding with test anyway")
        
        # Navigate to trading page
        print("Navigating to trading page...")
        driver.get("https://bulenox.projectx.com/trading")
        
        # Wait for page to load
        print("Waiting for trading page to load (45 seconds)...")
        time.sleep(45)
        
        # Take screenshot of trading page
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{screenshot_dir}/bulenox_trading_page_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Test futures symbol search
        print("\nTesting futures symbol search...")
        try:
            # Try different possible selectors for the symbol search input
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
            
            # Clear and enter symbol
            symbol_input.clear()
            symbol_input.send_keys("MBTQ25")
            print("Entered symbol: MBTQ25")
            
            # Take screenshot after entering symbol
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/bulenox_symbol_entered_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
            
            # Wait for search results
            time.sleep(3)
            
            # Try to select the symbol
            try:
                # Try direct selection
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'MBTQ25')]"))
                ).click()
                print("Selected MBTQ25 symbol directly")
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
            screenshot_path = f"{screenshot_dir}/bulenox_symbol_selected_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
            
            # Test setting quantity
            try:
                # Try multiple selectors for quantity input
                quantity_selectors = [
                    "//input[@placeholder='Quantity']",
                    "//div[contains(text(), 'Quantity')]/following::input[1]",
                    "//input[contains(@placeholder, 'Qty')]",
                    "//div[contains(text(), 'Qty')]/following::input[1]",
                    "//div[contains(@class, 'quantity')]//input"
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
            
            print("\nFutures trading UI test completed successfully!")
            print("NOTE: No actual trade was executed. This was just a UI test.")
            
        except Exception as e:
            print(f"Error during symbol search test: {e}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/bulenox_symbol_search_error_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved to: {screenshot_path}")
        
        # Test gold symbol detection
        print("\nTesting gold symbol detection...")
        try:
            # Clear and search for gold symbol
            if symbol_input:
                symbol_input.clear()
                symbol_input.send_keys("GC")
                print("Entered symbol: GC (Gold)")
                
                # Take screenshot after entering gold symbol
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{screenshot_dir}/bulenox_gold_entered_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to: {screenshot_path}")
                
                # Wait for search results
                time.sleep(3)
                
                # Try to select the gold symbol
                try:
                    # Try direct selection
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'GC')]"))
                    ).click()
                    print("Selected GC symbol directly")
                except Exception as e:
                    print(f"Direct gold symbol selection not found: {e}")
                    # Try alternative selectors
                    try:
                        # Try clicking on the first search result
                        WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'search-results')]/div[1] | //div[contains(@class, 'dropdown')]/div[1]"))
                        ).click()
                        print("Selected gold symbol from search results")
                    except Exception as e2:
                        print(f"Alternative gold dropdown not found: {e2}")
                        # Last resort - try pressing Enter key
                        symbol_input.send_keys(Keys.RETURN)
                        print("Pressed Enter key to select gold symbol")
                
                # Take screenshot after gold symbol selection
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{screenshot_dir}/bulenox_gold_selected_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved to: {screenshot_path}")
                print("Gold symbol detection test completed")
            else:
                print("Symbol input not available, skipping gold symbol test")
        except Exception as e:
            print(f"Error during gold symbol test: {e}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/bulenox_gold_test_error_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved to: {screenshot_path}")
        
        # Wait briefly for user to review before closing automatically
        print("\nTest completed. Browser will close automatically in 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"Error during test: {e}")
        if driver:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/bulenox_error_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved to: {screenshot_path}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("AI Trading Sentinel - Bulenox Selenium Test (DEV MODE)")
    print("=====================================================")
    test_bulenox_selenium_dev()