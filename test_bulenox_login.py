#!/usr/bin/env python3
"""
Test script for Bulenox login functionality
"""

import os
import time
import random
import logging
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_bulenox_login")

# Load environment variables
load_dotenv()

# Target URL
TARGET_URL = os.getenv("BROKER_URL", "https://bulenox.projectx.com/login")

# Test credentials
TEST_USERNAME = os.getenv("BULENOX_USERNAME", "user1@example.com")
TEST_PASSWORD = os.getenv("BULENOX_PASSWORD", "password1")

def random_user_agent():
    """
    Generate a random user agent string.
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

def create_driver(headless=False):
    """
    Create and configure a Chrome driver with undetected-chromedriver.
    """
    try:
        # Random user agent
        ua = random_user_agent()
        
        # Configure Chrome options
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Set headless mode if enabled
        if headless:
            options.add_argument("--headless=new")
        
        # Set user agent
        options.add_argument(f"--user-agent={ua}")
        
        # Set a random window size
        w = random.choice([1200, 1366, 1440, 1600, 1920])
        h = random.choice([700, 768, 800, 900, 1080])
        options.add_argument(f"--window-size={w},{h}")
        
        # Create driver with undetected-chromedriver
        logger.info("Creating Chrome driver with undetected-chromedriver")
        try:
            driver = uc.Chrome(options=options)
        except Exception as e:
            logger.warning(f"Error with undetected-chromedriver: {e}")
            # Try with version_main parameter - create new options to avoid reuse error
            logger.info("Trying with version_main parameter")
            new_options = uc.ChromeOptions()
            new_options.add_argument("--no-sandbox")
            new_options.add_argument("--disable-dev-shm-usage")
            new_options.add_argument("--disable-extensions")
            new_options.add_argument("--disable-infobars")
            new_options.add_argument("--disable-blink-features=AutomationControlled")
            if headless:
                new_options.add_argument("--headless=new")
            new_options.add_argument(f"--user-agent={ua}")
            new_options.add_argument(f"--window-size={w},{h}")
            driver = uc.Chrome(options=new_options, version_main=138)  # Specify the Chrome version
        
        # Apply stealth patches
        try:
            patch = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.navigator.chrome = {runtime: {}};
            window.navigator.permissions = {query: () => Promise.resolve({state: 'granted'})};
            """
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": patch})
        except Exception as e:
            logger.debug(f"Could not apply stealth patch: {e}")
        
        return driver
          
    except Exception as e:
        logger.error(f"Error creating Chrome driver: {e}")
        return None

def test_login():
    """
    Test the login functionality.
    """
    driver = None
    try:
        # Create driver
        driver = create_driver(headless=False)
        if not driver:
            logger.error("Failed to create driver")
            return False
        
        # Navigate to login page
        logger.info(f"Navigating to {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # Wait for page to load
        time.sleep(5)
        
        # Take screenshot of the login page
        logger.info("Taking screenshot of login page")
        driver.save_screenshot("login_page.png")
        
        # Save page source for debugging
        with open("login_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("Saved page source to login_page.html")
        
        # Print page title
        logger.info(f"Page title: {driver.title}")
        
        # Find all input fields
        input_fields = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"Found {len(input_fields)} input fields")
        
        for i, field in enumerate(input_fields):
            field_type = field.get_attribute("type")
            field_id = field.get_attribute("id")
            field_name = field.get_attribute("name")
            field_placeholder = field.get_attribute("placeholder")
            logger.info(f"Input field {i+1}: type={field_type}, id={field_id}, name={field_name}, placeholder={field_placeholder}")
        
        # Find all buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"Found {len(buttons)} buttons")
        
        for i, button in enumerate(buttons):
            button_text = button.text
            button_type = button.get_attribute("type")
            logger.info(f"Button {i+1}: text={button_text}, type={button_type}")
        
        # Try to find username field
        username_field = None
        username_selectors = [
            "//input[@id=':r0:']",
            "//input[@name='userName']",
            "//input[@type='text']",
            "//input[@id='username']",
            "//input[@name='username']",
            "//input[@id='email']",
            "//input[@name='email']",
            "//input[@id='user']",
            "//input[@name='user']",
            "//input[@id='login']",
            "//input[@name='login']",
            "//input[@type='email']",
            "//input[@placeholder='Email' or @placeholder='Username' or @placeholder='Email or Username']"
        ]
        
        for selector in username_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    username_field = elements[0]
                    logger.info(f"Found username field with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Error finding username field with selector {selector}: {e}")
        
        if not username_field:
            logger.error("Could not find username field")
            return False
        
        # Try to find password field
        password_field = None
        password_selectors = [
            "//input[@id=':r1:']",
            "//input[@name='password']",
            "//input[@id='password']",
            "//input[@name='pass']",
            "//input[@id='pass']",
            "//input[@type='password']",
            "//input[@placeholder='Password']"
        ]
        
        for selector in password_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    password_field = elements[0]
                    logger.info(f"Found password field with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Error finding password field with selector {selector}: {e}")
        
        if not password_field:
            logger.error("Could not find password field")
            return False
        
        # Enter credentials
        logger.info(f"Entering username: {TEST_USERNAME}")
        username_field.clear()
        username_field.send_keys(TEST_USERNAME)
        
        logger.info(f"Entering password: {TEST_PASSWORD}")
        password_field.clear()
        password_field.send_keys(TEST_PASSWORD)
        
        # Find login button
        login_button = None
        login_button_selectors = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Log in')]",
            "//input[@value='Login' or @value='Sign in' or @value='Log in']",
            "//a[contains(text(), 'Login') or contains(text(), 'Sign in') or contains(text(), 'Log in')]"
        ]
        
        for selector in login_button_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    login_button = elements[0]
                    logger.info(f"Found login button with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Error finding login button with selector {selector}: {e}")
        
        if not login_button:
            logger.error("Could not find login button")
            return False
        
        # Take screenshot before clicking login
        driver.save_screenshot("before_login.png")
        
        # Click login button
        logger.info("Clicking login button")
        login_button.click()
        
        # Wait for login to complete
        time.sleep(5)
        
        # Take screenshot after login
        driver.save_screenshot("after_login.png")
        
        # Check if login was successful
        current_url = driver.current_url
        logger.info(f"Current URL after login: {current_url}")
        
        # Simple check: if we're no longer on the login page, assume success
        if TARGET_URL not in current_url:
            logger.info("Login successful")
            return True
        else:
            logger.error("Login failed - still on login page")
            return False
        
    except Exception as e:
        logger.error(f"Error during login test: {e}")
        return False
        
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    result = test_login()
    logger.info(f"Login test {'succeeded' if result else 'failed'}")