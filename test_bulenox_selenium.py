from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bulenox_selenium():
    # Get profile paths from environment variables or use defaults
    profile_path = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data")
    profile_name = os.getenv('BULENOX_PROFILE_NAME', "Profile 13")
    
    print(f"🔄 Using Chrome profile: {profile_name} from {profile_path}")
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument(f"--profile-directory={profile_name}")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Create Chrome driver
    print("🔄 Initializing Chrome with user profile...")
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
    
    # Navigate to Bulenox login page
    driver.get("https://bulenox.projectx.com/login")
    print("✅ Opened Bulenox ProjectX login page")
    
    # Check if already logged in
    time.sleep(3)  # Wait for page to load
    current_url = driver.current_url
    print(f"Current URL: {current_url}")
    
    if "dashboard" in current_url:
        print("✅ Already logged in with saved credentials!")
    else:
        print("⚠️ Not logged in automatically. Checking for login form...")
        try:
            # Wait for login form
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            print("🔒 Login form detected. Please log in manually or check your saved credentials.")
        except Exception as e:
            print(f"❌ Error detecting login form: {e}")
    
    # Take a screenshot for verification
    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, "bulenox_login_test.png")
    driver.save_screenshot(screenshot_path)
    print(f"📸 Screenshot saved to: {screenshot_path}")
    
    # Wait for user input before closing
    input("🔒 Press Enter to close browser...")
    driver.quit()

if __name__ == "__main__":
    test_bulenox_selenium()