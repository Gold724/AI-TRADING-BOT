import os
import time
import logging
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("BULENOX_DIAGNOSTIC")

def main():
    """Detailed diagnostic for Bulenox login"""
    driver = None
    try:
        # Initialize Chrome with minimal options
        logger.info("Initializing Chrome driver with minimal options")
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_window_size(1366, 768)
        logger.info("Chrome driver initialized successfully")
        
        # Get credentials from environment variables
        username = os.getenv('BULENOX_USERNAME')
        password = os.getenv('BULENOX_PASSWORD')
        
        if not username or not password:
            logger.error("Missing Bulenox credentials in environment variables")
            return 1
        
        logger.info(f"Using username: {username}")
        
        # Navigate to login page
        broker_url = os.getenv('BROKER_URL', 'https://bulenox.com/member/login')
        logger.info(f"Navigating to: {broker_url}")
        driver.get(broker_url)
        
        # Log current page information
        logger.info(f"Current URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")
        
        # Take screenshot of login page
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"diagnostic_login_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"Login page screenshot saved to: {screenshot_path}")
        
        # Wait for page to fully load
        time.sleep(2)
        
        # Log page source for debugging
        page_source = driver.page_source
        logger.info(f"Page source length: {len(page_source)} characters")
        
        # Check for any CAPTCHA elements
        captcha_elements = driver.find_elements(By.XPATH, "//*[contains(@id, 'captcha') or contains(@class, 'captcha') or contains(@name, 'captcha')]")
        if captcha_elements:
            logger.warning(f"Found {len(captcha_elements)} potential CAPTCHA elements")
            for i, elem in enumerate(captcha_elements):
                logger.warning(f"CAPTCHA element {i+1}: id={elem.get_attribute('id')}, class={elem.get_attribute('class')}, name={elem.get_attribute('name')}")
        
        # Try to find username field with diagnostic info
        username_field = None
        username_selectors = [
            (By.ID, "amember-login"),
            (By.NAME, "amember_login"),
            (By.ID, "email"),
            (By.NAME, "userName"),
            (By.NAME, "username"),
            (By.NAME, "user"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@placeholder='Username' or @placeholder='Email' or @placeholder='Login']")
        ]
        
        logger.info("Attempting to find username field with different selectors")
        for by_method, selector in username_selectors:
            try:
                element = driver.find_element(by_method, selector)
                logger.info(f"Found username field with selector: {by_method}={selector}")
                logger.info(f"Element attributes: id={element.get_attribute('id')}, name={element.get_attribute('name')}, type={element.get_attribute('type')}")
                username_field = element
                break
            except NoSuchElementException:
                logger.info(f"Selector not found: {by_method}={selector}")
        
        if not username_field:
            logger.error("Username field not found with any selector")
            # Log all form elements for debugging
            try:
                form_elements = driver.find_elements(By.XPATH, "//form//input")
                logger.info(f"Found {len(form_elements)} form input elements:")
                for i, elem in enumerate(form_elements):
                    logger.info(f"Form element {i+1}: id={elem.get_attribute('id')}, name={elem.get_attribute('name')}, type={elem.get_attribute('type')}")
            except:
                logger.error("Could not find any form elements")
            return 1
        
        # Enter username
        username_field.clear()
        username_field.send_keys(username)
        logger.info(f"Entered username: {username}")
        
        # Try to find password field with diagnostic info
        password_field = None
        password_selectors = [
            (By.ID, "amember-pass"),
            (By.NAME, "amember_pass"),
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.NAME, "pass"),
            (By.NAME, "pwd"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@type='password']")
        ]
        
        logger.info("Attempting to find password field with different selectors")
        for by_method, selector in password_selectors:
            try:
                element = driver.find_element(by_method, selector)
                logger.info(f"Found password field with selector: {by_method}={selector}")
                logger.info(f"Element attributes: id={element.get_attribute('id')}, name={element.get_attribute('name')}, type={element.get_attribute('type')}")
                password_field = element
                break
            except NoSuchElementException:
                logger.info(f"Selector not found: {by_method}={selector}")
        
        if not password_field:
            logger.error("Password field not found with any selector")
            return 1
        
        # Enter password
        password_field.clear()
        password_field.send_keys(password)
        logger.info("Entered password")
        
        # Try to find submit button with diagnostic info
        submit_button = None
        submit_selectors = [
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Login') or contains(text(), 'SIGN IN') or contains(text(), 'LOG IN')]"),
            (By.XPATH, "//input[contains(@value, 'Sign in') or contains(@value, 'Login')]"),
            (By.XPATH, "//form//button"),
            (By.CSS_SELECTOR, ".login-button"),
            (By.CSS_SELECTOR, ".btn-login"),
            (By.CSS_SELECTOR, ".btn-primary")
        ]
        
        logger.info("Attempting to find submit button with different selectors")
        for by_method, selector in submit_selectors:
            try:
                element = driver.find_element(by_method, selector)
                logger.info(f"Found submit button with selector: {by_method}={selector}")
                logger.info(f"Element attributes: id={element.get_attribute('id')}, name={element.get_attribute('name')}, type={element.get_attribute('type')}, value={element.get_attribute('value')}, text={element.text}")
                submit_button = element
                break
            except NoSuchElementException:
                logger.info(f"Selector not found: {by_method}={selector}")
        
        if not submit_button:
            logger.error("Submit button not found with any selector")
            return 1
        
        # Check for any error messages before submit
        try:
            error_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@class, 'message')]")
            if error_elements:
                logger.warning(f"Found {len(error_elements)} potential error elements before submit:")
                for i, elem in enumerate(error_elements):
                    logger.warning(f"Error element {i+1}: text={elem.text}, class={elem.get_attribute('class')}")
        except Exception as e:
            logger.error(f"Error checking for error messages before submit: {str(e)}")
        
        # Take screenshot before clicking submit
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_submit_screenshot = f"diagnostic_pre_submit_{timestamp}.png"
        driver.save_screenshot(pre_submit_screenshot)
        logger.info(f"Pre-submit screenshot saved to: {pre_submit_screenshot}")
        
        # Click the submit button
        submit_button.click()
        logger.info("Clicked submit button")
        
        # Wait for a moment to see what happens
        time.sleep(5)
        
        # Log current page information after submit
        logger.info(f"Post-submit URL: {driver.current_url}")
        logger.info(f"Post-submit page title: {driver.title}")
        
        # Check for error messages after submit
        try:
            # Look for error messages with various selectors
            error_selectors = [
                "//div[contains(@class, 'error')]",
                "//div[contains(@class, 'alert')]",
                "//div[contains(@class, 'message')]",
                "//p[contains(@class, 'error')]",
                "//span[contains(@class, 'error')]",
                "//div[@role='alert']",
                "//div[contains(text(), 'error') or contains(text(), 'invalid') or contains(text(), 'incorrect')]",
                "//p[contains(text(), 'error') or contains(text(), 'invalid') or contains(text(), 'incorrect')]",
                "//span[contains(text(), 'error') or contains(text(), 'invalid') or contains(text(), 'incorrect')]"
            ]
            
            for selector in error_selectors:
                error_elements = driver.find_elements(By.XPATH, selector)
                if error_elements:
                    logger.warning(f"Found {len(error_elements)} potential error elements with selector {selector}:")
                    for i, elem in enumerate(error_elements):
                        logger.warning(f"Error element {i+1}: text={elem.text}, class={elem.get_attribute('class')}")
        except Exception as e:
            logger.error(f"Error checking for error messages after submit: {str(e)}")
        
        # Take screenshot after submit
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        post_submit_screenshot = f"diagnostic_post_submit_{timestamp}.png"
        driver.save_screenshot(post_submit_screenshot)
        logger.info(f"Post-submit screenshot saved to: {post_submit_screenshot}")
        
        # Check if we're on a dashboard page
        dashboard_urls = ["dashboard", "trading", "member/home", "account", "platform", "terminal", "market"]
        if any(url_part in driver.current_url for url_part in dashboard_urls):
            logger.info(f"Successfully logged in (redirected to {driver.current_url})")
            return 0
        else:
            logger.error(f"Login failed - unexpected redirect to {driver.current_url}")
            
            # If we're still on the login page, check for form elements again
            if "login" in driver.current_url.lower():
                logger.info("Still on login page, checking form elements again")
                try:
                    # Check if username and password fields still have our values
                    username_field = driver.find_element(By.ID, "amember-login")
                    password_field = driver.find_element(By.ID, "amember-pass")
                    
                    logger.info(f"Username field value after submit: {username_field.get_attribute('value')}")
                    logger.info(f"Password field value after submit: {password_field.get_attribute('value')}")
                    
                    # Check if there are any hidden fields we might be missing
                    hidden_fields = driver.find_elements(By.XPATH, "//input[@type='hidden']")
                    logger.info(f"Found {len(hidden_fields)} hidden fields:")
                    for i, field in enumerate(hidden_fields):
                        logger.info(f"Hidden field {i+1}: name={field.get_attribute('name')}, value={field.get_attribute('value')}")
                except Exception as e:
                    logger.error(f"Error checking form elements after submit: {str(e)}")
            
            return 1
            
    except Exception as e:
        logger.error(f"Error during diagnostic: {str(e)}")
        return 1
    finally:
        # Always close the driver
        if driver:
            try:
                driver.quit()
                logger.info("Driver closed")
            except Exception as e:
                logger.error(f"Error closing driver: {str(e)}")

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)