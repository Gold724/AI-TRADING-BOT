from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def login_bulenox_with_profile():
    # Get profile paths from environment variables or use defaults
    profile_path = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data")
    profile_name = os.getenv('BULENOX_PROFILE_NAME', "Profile 13")
    
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
    
    # Create Chrome driver without specifying service path (uses WebDriver Manager)
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
    driver.get("https://bulenox.projectx.com/login")

    print("✅ Opened Bulenox ProjectX login using Chrome profile.")
    input("🔒 Press Enter to close browser...")
    driver.quit()

if __name__ == "__main__":
    login_bulenox_with_profile()
