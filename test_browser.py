from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from dotenv import load_dotenv
import time

def test_browser():
    # Load environment variables
    load_dotenv()
    
    # Get broker URL from environment variables
    broker_url = os.getenv('BROKER_URL')
    print(f"Testing navigation to: {broker_url}")
    
    # Basic Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Initialize Chrome driver
        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to broker URL
        print(f"Navigating to {broker_url}...")
        driver.get(broker_url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Get current URL
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        # Take screenshot
        screenshot_path = "browser_test.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Close driver
        driver.quit()
        print("Test completed successfully.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Browser Navigation")
    print("========================\n")
    test_browser()