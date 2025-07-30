from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import os

try:
    # Setup Chrome options - without user profile for now
    options = Options()
    # Add some basic options to avoid crashes
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    
    # Initialize the driver
    print("Initializing Chrome driver...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Navigate to login page
    print("Navigating to Bulenox login page...")
    driver.get('https://bulenox.com/member/login')
    time.sleep(5)
    
    # Print current state
    print(f'Current URL: {driver.current_url}')
    print(f'Page title: {driver.title}')
    
    # Try to find the login form
    try:
        form = driver.find_element(By.TAG_NAME, 'form')
        print(f'Form found: {form.get_attribute("outerHTML")}')
    except Exception as e:
        print(f'Form error: {e}')
    
    # Try to find username and password fields
    try:
        username_selectors = [
            (By.ID, "email"),
            (By.NAME, "userName"),
            (By.NAME, "username"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.XPATH, "//input[@placeholder='Email' or @placeholder='Username' or @placeholder='Email/Username']")
        ]
        
        for by, selector in username_selectors:
            try:
                username_field = driver.find_element(by, selector)
                print(f"Username field found with selector: {by}, {selector}")
                print(f"Username field attributes: {username_field.get_attribute('outerHTML')}")
                break
            except:
                continue
        else:
            print("Username field not found with any selector")
        
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@placeholder='Password']")
        ]
        
        for by, selector in password_selectors:
            try:
                password_field = driver.find_element(by, selector)
                print(f"Password field found with selector: {by}, {selector}")
                print(f"Password field attributes: {password_field.get_attribute('outerHTML')}")
                break
            except:
                continue
        else:
            print("Password field not found with any selector")
            
        # Try to find submit button
        submit_selectors = [
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign in')]"),
            (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        ]
        
        for by, selector in submit_selectors:
            try:
                submit_button = driver.find_element(by, selector)
                print(f"Submit button found with selector: {by}, {selector}")
                print(f"Submit button attributes: {submit_button.get_attribute('outerHTML')}")
                break
            except:
                continue
        else:
            print("Submit button not found with any selector")
    
    except Exception as e:
        print(f'Error finding form elements: {e}')
    
    # Print page source excerpt
    print('\nPage source excerpt:')
    print(driver.page_source[:1000])
    
    # Save screenshot
    screenshot_path = 'login_diagnostic.png'
    driver.save_screenshot(screenshot_path)
    print(f'Screenshot saved to: {os.path.abspath(screenshot_path)}')

except Exception as e:
    print(f"Error during diagnosis: {e}")

finally:
    # Quit the driver
    try:
        driver.quit()
        print("Driver closed successfully")
    except Exception as e:
        print(f"Error closing driver: {e}")