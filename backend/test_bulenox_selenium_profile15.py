import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Use profile 15 explicitly
profile_path = os.getenv('BULENOX_PROFILE_PATH', r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data Profile 15")
profile_name = "Profile 15"

print(f"\u27F3 Opening Chrome with profile: {profile_name} from {profile_path}")

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

driver = webdriver.Chrome(options=chrome_options)

driver.get("https://www.bulenox.com")
# Keep the browser open for manual inspection
input("Press Enter to close the browser...")
driver.quit()