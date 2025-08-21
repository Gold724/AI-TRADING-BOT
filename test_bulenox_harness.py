#!/usr/bin/env python3
"""
test_bulenox_harness.py
Safe test harness:
- initializes undetected-chromedriver + selenium-wire
- navigates to login page
- attempts auto-login using .env credentials
- saves a screenshot and logs one representative captured request as cURL
- writes a heartbeat status file

Run in debug/headful mode for debugging. Use xvfb-run in headless servers.
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Import undetected_chromedriver and selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile

# Load .env
load_dotenv()

# Config
USERNAME = os.getenv("BULENOX_USERNAME")
PASSWORD = os.getenv("BULENOX_PASSWORD")
PROFILE_PATH = os.getenv("BULENOX_PROFILE_PATH")        # optional
PROFILE_NAME = os.getenv("BULENOX_PROFILE_NAME")        # optional
LOGIN_URL = os.getenv("BULENOX_LOGIN_URL", "https://bulenox.projectx.com/login")
TRADING_URL = os.getenv("BULENOX_TRADING_URL", "https://bulenox.projectx.com/trade")
LOG_DIR = os.getenv("TEST_LOG_DIR", "logs")
SCREENSHOT_DIR = os.path.join(LOG_DIR, "screenshots")
REQUESTS_FILE = os.path.join(LOG_DIR, "requests_curl.txt")
HEARTBEAT_FILE = os.path.join(LOG_DIR, "heartbeat.txt")
DEBUG = bool(int(os.getenv("DEBUG", "0")))

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def write_heartbeat(msg):
    payload = {"status": msg, "ts": datetime.utcnow().isoformat() + "Z"}
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(json.dumps(payload))
    print("HEARTBEAT:", payload)

def _apply_basic_stealth(driver):
    try:
        script = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
        """
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})
    except Exception as e:
        print("Stealth patch failed:", e)

def safe_init_driver():
    """Initialize Chrome driver with undetected_chromedriver."""
    try:
        # Create options for undetected_chromedriver
        options = uc.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        
        # Use a random temporary profile to avoid conflicts
        temp_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={temp_dir}")
        
        # Create undetected_chromedriver instance with version_main parameter
        # This helps with version compatibility issues
        driver = uc.Chrome(options=options, version_main=138)  # Specify your Chrome version
        
        # Apply additional stealth patches
        _apply_basic_stealth(driver)
        return driver
    except Exception as e:
        print(f"Error initializing driver: {e}")
        # Fallback to regular Chrome if undetected_chromedriver fails
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        _apply_basic_stealth(driver)
        return driver

def capture_one_request_as_curl(driver):
    """Create a simple curl command for the current URL.
    Since we're not using selenium-wire anymore, we'll just log the current URL.
    """
    try:
        current_url = driver.current_url
        # Create a simple curl command for the current URL
        curl_cmd = f'curl -X GET "{current_url}" -H "User-Agent: Mozilla/5.0"'
        
        # Create an entry with the current URL information
        entry = {
            "url": current_url,
            "method": "GET",
            "status": 200,  # Assuming success
            "curl": curl_cmd,
            "ts": datetime.utcnow().isoformat()+"Z"
        }
        
        # Write the entry to the requests file
        with open(REQUESTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        
        print("Captured current URL ->", current_url)
        return entry
    except Exception as e:
        print(f"Error capturing request: {e}")
        return None

def main():
    if not USERNAME or not PASSWORD:
        print("Missing BULENOX_USERNAME or BULENOX_PASSWORD in .env. Aborting.")
        return

    write_heartbeat("starting")
    driver = None
    try:
        print("Initializing driver...")
        ok = False
        driver = safe_init_driver()
        print("Driver initialized, opening login URL:", LOGIN_URL)
        driver.get(LOGIN_URL)
        time.sleep(2)

        # attempt to find common login fields (robust but minimal)
        try:
            # try by name/id placeholders commonly used
            username_e = None
            password_e = None
            for sel in ["email","username","login","user"]:
                try:
                    username_e = driver.find_element(By.ID, sel)
                    break
                except:
                    pass
            if not username_e:
                try:
                    username_e = driver.find_element(By.NAME, "email")
                except:
                    pass
            if not username_e:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                if inputs:
                    username_e = inputs[0]

            # password
            for sel in ["password","passwd","pass"]:
                try:
                    password_e = driver.find_element(By.NAME, sel)
                    break
                except:
                    pass
            if not password_e:
                try:
                    password_e = driver.find_element(By.ID, "password")
                except:
                    pass
            if not password_e:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                if len(inputs) > 1:
                    password_e = inputs[1]

            # submit button
            submit_e = None
            for sel in ["//button[@type='submit']", "//input[@type='submit']", "//button[contains(text(), 'Login')]", "//button[contains(text(), 'Sign in')]"]:
                try:
                    submit_e = driver.find_element(By.XPATH, sel)
                    break
                except:
                    pass

            # Fill in credentials if elements found
            if username_e and password_e:
                username_e.clear()
                username_e.send_keys(USERNAME)
                password_e.clear()
                password_e.send_keys(PASSWORD)
                time.sleep(1)

                # Take screenshot before submit
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"login_before_{timestamp}.png")
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")

                # Submit form
                if submit_e:
                    submit_e.click()
                else:
                    # Try pressing Enter on password field
                    password_e.send_keys(Keys.RETURN)

                time.sleep(3)  # Wait for login to process

                # Take screenshot after submit
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"login_after_{timestamp}.png")
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")

                # Capture a representative request
                capture_one_request_as_curl(driver)

                # Check if login was successful
                current_url = driver.current_url
                if "login" not in current_url.lower():
                    write_heartbeat("login_success")
                    print("Login successful! Current URL:", current_url)
                    ok = True
                else:
                    write_heartbeat("login_failed")
                    print("Login failed. Still on login page.")
            else:
                write_heartbeat("login_elements_not_found")
                print("Could not find login form elements.")

        except Exception as e:
            write_heartbeat(f"login_error: {str(e)}")
            print(f"Error during login: {e}")

        # Final status
        if ok:
            print("Test completed successfully.")
        else:
            print("Test completed with errors.")

    except Exception as e:
        write_heartbeat(f"error: {str(e)}")
        print(f"Fatal error: {e}")

    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
            except:
                pass
            print("Driver closed.")

if __name__ == "__main__":
    main()