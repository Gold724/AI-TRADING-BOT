from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv

def login_bulenox_with_profile():
    # Load environment variables
    load_dotenv()
    
    # Get profile paths from environment variables or use defaults
    profile_path = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data")
    profile_name = os.getenv('BULENOX_PROFILE_NAME', "Profile 13")
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH', r"D:\aibot\chromedriver-win64\chromedriver-win64\chromedriver.exe")

    try:
        # Try to use the specified chromedriver path if available
        if os.path.exists(chromedriver_path):
            chrome_service = Service(executable_path=chromedriver_path)
            chrome_options = Options()
        else:
            # Otherwise use WebDriver Manager
            chrome_options = Options()
            chrome_service = None

        # Configure Chrome options
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument(f"--profile-directory={profile_name}")
        chrome_options.add_argument("--disable-session-crashed-bubble")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_experimental_option("detach", True)

        # Initialize driver
        if chrome_service:
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)

        # Open Bulenox
        driver.get("https://bulenox.projectx.com/login")
        print(f"✅ Loaded Bulenox login page using Chrome profile: {profile_name}")

        input("🔒 Press Enter to close browser...")
    except Exception as e:
        print(f"Error initializing Chrome: {e}")
        print("Trying alternative approach...")
        
        try:
            # Try with WebDriver Manager
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Open Bulenox
            driver.get("https://bulenox.projectx.com/login")
            print(f"✅ Loaded Bulenox login page using Chrome profile: {profile_name}")

            input("🔒 Press Enter to close browser...")
        except Exception as e2:
            print(f"Error with alternative approach: {e2}")
            return
    finally:
        if 'driver' in locals() and driver:
            driver.quit()

if __name__ == "__main__":
    login_bulenox_with_profile()
