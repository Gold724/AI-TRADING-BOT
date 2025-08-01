import os
import time
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

def kill_existing_chrome():
    """Kill all existing Chrome processes to avoid conflicts"""
    print("🔄 Checking for existing Chrome processes...")
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
                killed_count += 1
                print(f"   Killed Chrome process: {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed_count > 0:
        print(f"✅ Killed {killed_count} Chrome processes")
        time.sleep(2)  # Wait for processes to fully terminate
    else:
        print("✅ No existing Chrome processes found")

def test_bulenox_selenium_improved():
    # Load environment variables
    load_dotenv()
    
    # Kill existing Chrome processes first
    kill_existing_chrome()
    
    # Get credentials
    username = os.getenv('BULENOX_USERNAME')
    password = os.getenv('BULENOX_PASSWORD')
    
    # Get profile paths from environment variables
    profile_path = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data")
    profile_name = os.getenv('BULENOX_PROFILE_NAME', "Profile 15")
    
    print(f"🔄 Configuration:")
    print(f"   Username: {username}")
    print(f"   Profile Path: {profile_path}")
    print(f"   Profile Name: {profile_name}")
    
    # Configure Chrome options with improved settings
    chrome_options = Options()
    
    # Essential Chrome arguments
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Faster loading
    chrome_options.add_argument("--disable-javascript")  # Prevent conflicts
    
    # Profile settings
    if profile_path and profile_name:
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument(f"--profile-directory={profile_name}")
        print(f"✅ Using Chrome profile: {profile_name}")
    
    # Anti-detection settings
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    # Preferences to avoid popups
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = None
    try:
        print("🔄 Initializing Chrome driver...")
        
        # Try with ChromeDriver from environment variable first
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
        if chromedriver_path and os.path.exists(chromedriver_path):
            print(f"✅ Using ChromeDriver from: {chromedriver_path}")
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Fallback to WebDriver Manager
            print("🔄 Using WebDriver Manager...")
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Chrome driver initialized successfully")
        
        # Navigate to Bulenox login page
        print("🔄 Navigating to Bulenox ProjectX...")
        driver.get("https://bulenox.projectx.com/login")
        
        # Wait for page to load
        time.sleep(5)
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        # Take initial screenshot
        screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        initial_screenshot = os.path.join(screenshot_dir, "bulenox_initial_load.png")
        driver.save_screenshot(initial_screenshot)
        print(f"📸 Initial screenshot: {initial_screenshot}")
        
        # Check if already logged in
        if "dashboard" in current_url or "trading" in current_url:
            print("✅ Already logged in with saved profile!")
            
            # Try to navigate to trading page
            print("🔄 Testing navigation to trading page...")
            driver.get("https://bulenox.projectx.com/trading")
            time.sleep(3)
            
            trading_screenshot = os.path.join(screenshot_dir, "bulenox_trading_page.png")
            driver.save_screenshot(trading_screenshot)
            print(f"📸 Trading page screenshot: {trading_screenshot}")
            
        else:
            print("🔒 Not logged in automatically. Attempting login...")
            
            try:
                # Wait for login form elements
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                password_field = driver.find_element(By.ID, "password")
                
                print("✅ Login form detected")
                
                # Clear and enter credentials
                email_field.clear()
                email_field.send_keys(username)
                
                password_field.clear()
                password_field.send_keys(password)
                
                # Take screenshot before login
                pre_login_screenshot = os.path.join(screenshot_dir, "bulenox_pre_login.png")
                driver.save_screenshot(pre_login_screenshot)
                print(f"📸 Pre-login screenshot: {pre_login_screenshot}")
                
                # Find and click login button
                login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                
                print("🔄 Login submitted, waiting for response...")
                
                # Wait for login to complete (either success or error)
                time.sleep(5)
                
                # Take screenshot after login attempt
                post_login_screenshot = os.path.join(screenshot_dir, "bulenox_post_login.png")
                driver.save_screenshot(post_login_screenshot)
                print(f"📸 Post-login screenshot: {post_login_screenshot}")
                
                # Check if login was successful
                current_url = driver.current_url
                if "dashboard" in current_url or "trading" in current_url:
                    print("✅ Login successful!")
                else:
                    print("❌ Login may have failed. Check screenshots for details.")
                    
            except Exception as e:
                print(f"❌ Error during login process: {e}")
                
                error_screenshot = os.path.join(screenshot_dir, "bulenox_login_error.png")
                driver.save_screenshot(error_screenshot)
                print(f"📸 Error screenshot: {error_screenshot}")
        
        # Keep browser open for manual inspection
        print("\n" + "="*50)
        print("🔍 MANUAL INSPECTION TIME")
        print("="*50)
        print("The browser will stay open for you to:")
        print("1. Check if login was successful")
        print("2. Manually complete login if needed")
        print("3. Navigate around the platform")
        print("4. Test trading interface")
        print("="*50)
        
        input("Press Enter when you're done inspecting...")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        if driver:
            error_screenshot = os.path.join(screenshot_dir, "bulenox_critical_error.png")
            driver.save_screenshot(error_screenshot)
            print(f"📸 Critical error screenshot: {error_screenshot}")
    
    finally:
        if driver:
            print("🔄 Closing browser...")
            driver.quit()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("🚀 Starting Bulenox Selenium Test (Improved)")
    print("="*50)
    test_bulenox_selenium_improved()
    print("="*50)
    print("✅ Test completed")