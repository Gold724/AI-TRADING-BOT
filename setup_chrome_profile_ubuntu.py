#!/usr/bin/env python3

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

def setup_chrome_profile():
    """Set up Chrome profile for automated trading in Ubuntu environment"""
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    bulenox_username = os.getenv('BULENOX_USERNAME')
    bulenox_password = os.getenv('BULENOX_PASSWORD')
    
    if not bulenox_username or not bulenox_password:
        print("Error: BULENOX_USERNAME and BULENOX_PASSWORD must be set in .env file")
        return False
    
    # Set up Chrome options for Ubuntu
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    
    # Use a temporary profile directory
    temp_profile_dir = os.path.join(os.getcwd(), "temp_chrome_profile")
    os.makedirs(temp_profile_dir, exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
    
    # Set up headless mode for server environment
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Create driver
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("Chrome driver initialized successfully")
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        return False
    
    try:
        # Navigate to login page
        print("Navigating to login page...")
        driver.get("https://bulenox.projectx.com/login")
        
        # Wait for login form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        
        # Enter credentials
        print("Entering credentials...")
        driver.find_element(By.ID, "email").send_keys(bulenox_username)
        driver.find_element(By.ID, "password").send_keys(bulenox_password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for login to complete
        WebDriverWait(driver, 10).until(
            EC.url_contains("dashboard")
        )
        
        print("Login successful!")
        
        # Save screenshot for verification
        screenshot_dir = "logs/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        driver.save_screenshot(f"{screenshot_dir}/login_success_ubuntu.png")
        
        # Wait a moment for cookies to be saved
        time.sleep(5)
        
        print(f"Chrome profile created successfully at {temp_profile_dir}")
        return True
        
    except Exception as e:
        print(f"Error during login process: {e}")
        # Save screenshot of error
        screenshot_dir = "logs/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        driver.save_screenshot(f"{screenshot_dir}/login_error_ubuntu.png")
        return False
    
    finally:
        driver.quit()

if __name__ == "__main__":
    print("Setting up Chrome profile for Ubuntu environment...")
    success = setup_chrome_profile()
    if success:
        print("Chrome profile setup completed successfully!")
    else:
        print("Chrome profile setup failed!")