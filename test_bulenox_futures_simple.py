import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

def test_futures_trading():
    """Test futures trading on Bulenox with 6EU25 symbol"""
    load_dotenv()
    
    # Configuration
    username = os.getenv('BULENOX_USERNAME')
    password = os.getenv('BULENOX_PASSWORD')
    profile_path = os.getenv('BULENOX_PROFILE_PATH')
    profile_name = os.getenv('BULENOX_PROFILE_NAME')
    
    print(f"🔄 Testing Futures Trading on Bulenox")
    print(f"   Symbol: 6EU25 (Euro Futures)")
    print(f"   Profile: {profile_name}")
    
    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    if profile_path and profile_name:
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument(f"--profile-directory={profile_name}")
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        # Initialize driver
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
        if chromedriver_path and os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Chrome driver initialized")
        
        # Navigate to login page
        driver.get("https://bulenox.projectx.com/login")
        time.sleep(3)
        
        # Check if already logged in
        if "dashboard" not in driver.current_url:
            print("🔒 Logging in...")
            
            # Login
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            password_field = driver.find_element(By.ID, "password")
            
            email_field.send_keys(username)
            password_field.send_keys(password)
            
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login
            time.sleep(5)
        
        print("✅ Logged in successfully")
        
        # Navigate to trading page
        print("🔄 Navigating to trading page...")
        driver.get("https://bulenox.projectx.com/trading")
        time.sleep(5)
        
        # Take screenshot of trading page
        screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        trading_screenshot = os.path.join(screenshot_dir, "futures_trading_page.png")
        driver.save_screenshot(trading_screenshot)
        print(f"📸 Trading page screenshot: {trading_screenshot}")
        
        # Test symbol search for futures
        print("🔄 Testing futures symbol search (6EU25)...")
        
        try:
            # Look for symbol search input
            symbol_selectors = [
                "//input[@placeholder='Search symbol']",
                "//input[@placeholder='Symbol']",
                "//input[contains(@class, 'symbol')]",
                "//input[contains(@id, 'symbol')]"
            ]
            
            symbol_input = None
            for selector in symbol_selectors:
                try:
                    symbol_input = driver.find_element(By.XPATH, selector)
                    print(f"✅ Found symbol input with selector: {selector}")
                    break
                except:
                    continue
            
            if symbol_input:
                symbol_input.clear()
                symbol_input.send_keys("6EU25")
                time.sleep(2)
                
                # Try to select from dropdown
                try:
                    # Look for dropdown options
                    dropdown_selectors = [
                        "//div[contains(@class, 'dropdown')]//div[contains(text(), '6EU25')]",
                        "//div[contains(@class, 'option')]//div[contains(text(), '6EU25')]",
                        "//li[contains(text(), '6EU25')]"
                    ]
                    
                    for selector in dropdown_selectors:
                        try:
                            option = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            option.click()
                            print("✅ Selected 6EU25 from dropdown")
                            break
                        except:
                            continue
                    else:
                        # If no dropdown found, try pressing Enter
                        symbol_input.send_keys(Keys.RETURN)
                        print("✅ Pressed Enter to confirm symbol")
                        
                except Exception as e:
                    print(f"⚠️ Could not select from dropdown: {e}")
                
                # Take screenshot after symbol selection
                symbol_screenshot = os.path.join(screenshot_dir, "futures_symbol_selected.png")
                driver.save_screenshot(symbol_screenshot)
                print(f"📸 Symbol selection screenshot: {symbol_screenshot}")
                
            else:
                print("❌ Could not find symbol input field")
                
        except Exception as e:
            print(f"❌ Error testing symbol search: {e}")
        
        # Look for trading interface elements
        print("🔄 Analyzing trading interface...")
        
        # Check for common trading elements
        elements_to_check = [
            ("Quantity input", "//input[@placeholder='Quantity']"),
            ("Buy button", "//button[contains(text(), 'Buy')]"),
            ("Sell button", "//button[contains(text(), 'Sell')]"),
            ("Stop Loss input", "//input[@placeholder='Stop Loss']"),
            ("Take Profit input", "//input[@placeholder='Take Profit']")
        ]
        
        for element_name, xpath in elements_to_check:
            try:
                element = driver.find_element(By.XPATH, xpath)
                print(f"✅ Found {element_name}")
            except:
                print(f"❌ Could not find {element_name}")
        
        # Final screenshot
        final_screenshot = os.path.join(screenshot_dir, "futures_trading_final.png")
        driver.save_screenshot(final_screenshot)
        print(f"📸 Final screenshot: {final_screenshot}")
        
        print("\n" + "="*50)
        print("🔍 FUTURES TRADING TEST COMPLETE")
        print("="*50)
        print("Check the screenshots to verify:")
        print("1. Trading page loaded correctly")
        print("2. Symbol search works for 6EU25")
        print("3. Trading interface elements are present")
        print("="*50)
        
        input("Press Enter to close browser...")
        
    except Exception as e:
        print(f"❌ Error during futures trading test: {e}")
        if driver:
            error_screenshot = os.path.join(screenshot_dir, "futures_error.png")
            driver.save_screenshot(error_screenshot)
            print(f"📸 Error screenshot: {error_screenshot}")
    
    finally:
        if driver:
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    test_futures_trading()