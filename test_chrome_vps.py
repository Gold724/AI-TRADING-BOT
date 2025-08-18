#!/usr/bin/env python3
# Simple script to test if Chrome is working properly on the VPS

import os
import sys
import time
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Error: Required packages not installed. Please run:")
    print("pip install selenium webdriver-manager")
    sys.exit(1)

def test_chrome():
    print(f"\n[{datetime.now()}] Starting Chrome test...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Initialize Chrome driver
        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Test navigation
        print("Navigating to Google...")
        driver.get("https://www.google.com")
        print(f"Page title: {driver.title}")
        
        # Take screenshot
        screenshot_path = "chrome_test_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {os.path.abspath(screenshot_path)}")
        
        # Print Chrome version
        print(f"Chrome version: {driver.capabilities['browserVersion']}")
        print(f"ChromeDriver version: {driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]}")
        
        # Close driver
        driver.quit()
        print(f"[{datetime.now()}] Chrome test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"[{datetime.now()}] Chrome test failed!")
        return False

if __name__ == "__main__":
    success = test_chrome()
    sys.exit(0 if success else 1)