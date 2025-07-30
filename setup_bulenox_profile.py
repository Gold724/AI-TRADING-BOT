from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_bulenox_profile():
    # Get credentials from environment variables
    username = os.getenv('BULENOX_USERNAME', 'BX64883-10')
    password = os.getenv('BULENOX_PASSWORD', '')
    
    # Configure Chrome options for a fresh instance
    chrome_options = Options()
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Create Chrome driver with a fresh instance
    print("🔄 Initializing fresh Chrome instance...")
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
            print("Trying with minimal options...")
            
            # Last resort - try with minimal options
            minimal_options = Options()
            minimal_options.add_argument("--start-maximized")
            driver = webdriver.Chrome(options=minimal_options)
    
    # Navigate to Bulenox login page
    driver.get("https://bulenox.projectx.com/login")

    print("✅ Opened Bulenox ProjectX login page in a fresh Chrome instance.")
    print("🔒 Please log in manually to Bulenox with these credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password if password else '********'}")
    print("")
    print("⚠️ Important instructions:")
    print("1. After logging in successfully, note which Chrome profile you're using")
    print("2. Update your .env file with the correct Chrome profile settings:")
    print("   BULENOX_PROFILE_PATH=C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data")
    print("   BULENOX_PROFILE_NAME=Profile X  (replace X with your profile number)")
    print("3. Restart the Flask server with: python backend/main.py")
    print("")
    print("⏳ The browser will stay open for 5 minutes to allow you to log in.")
    print("⏳ After logging in, you can close this script with Ctrl+C.")
    
    # Keep the browser open for 5 minutes to allow manual login
    try:
        time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        print("\n✅ Setup completed. Now update your .env file with the correct profile and restart the Flask server.")
    finally:
        driver.quit()

if __name__ == "__main__":
    setup_bulenox_profile()