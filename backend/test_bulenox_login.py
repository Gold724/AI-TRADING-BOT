import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import datetime

# Load environment variables for credentials
from dotenv import load_dotenv
load_dotenv()

BULENOX_USERNAME = os.getenv('BULENOX_USERNAME')
BULENOX_PASSWORD = os.getenv('BULENOX_PASSWORD')

PROFILE_PATH = os.getenv('BULENOX_PROFILE_PATH', os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"))
PROFILE_NAME = os.getenv('BULENOX_PROFILE_NAME', "Profile 15")

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)


def save_screenshot(driver, name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(path)
    print(f"Screenshot saved to {path}")


def main():
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    options.add_argument(f"--profile-directory={PROFILE_NAME}")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-session-crashed-bubble')

    driver = uc.Chrome(options=options)
    driver.maximize_window()

    try:
        driver.get("https://bulenox.projectx.com/login")
        print("Loaded Bulenox login page")
        save_screenshot(driver, "bulenox_login_page")

        # Wait for username/email field
        username_selectors = [
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.ID, "username"),
            (By.NAME, "username"),
            (By.XPATH, "//input[@placeholder='Email']"),
            (By.XPATH, "//input[@placeholder='Username']")
        ]

        username_field = None
        for by, selector in username_selectors:
            try:
                username_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                print(f"Found username field with {by}={selector}")
                break
            except:
                continue

        if not username_field:
            print("Username field not found")
            save_screenshot(driver, "bulenox_username_not_found")
            return

        username_field.clear()
        username_field.send_keys(BULENOX_USERNAME)

        # Wait for password field
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.XPATH, "//input[@type='password']"),
            (By.XPATH, "//input[@placeholder='Password']")
        ]

        password_field = None
        for by, selector in password_selectors:
            try:
                password_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                print(f"Found password field with {by}={selector}")
                break
            except:
                continue

        if not password_field:
            print("Password field not found")
            save_screenshot(driver, "bulenox_password_not_found")
            return

        password_field.clear()
        password_field.send_keys(BULENOX_PASSWORD)

        # Find and click login button
        login_button_selectors = [
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign In')]"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[contains(@class, 'login') or contains(@class, 'submit')]")
        ]

        login_button = None
        for by, selector in login_button_selectors:
            try:
                login_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                print(f"Found login button with {by}={selector}")
                break
            except:
                continue

        if not login_button:
            print("Login button not found")
            save_screenshot(driver, "bulenox_login_button_not_found")
            return

        login_button.click()
        print("Clicked login button")

        # Wait for dashboard or error
        try:
            WebDriverWait(driver, 15).until(
                lambda d: 'dashboard' in d.current_url or 'login' not in d.current_url
            )
            print("Login appears successful")
            save_screenshot(driver, "bulenox_dashboard")
        except:
            print("Login may have failed or timed out")
            save_screenshot(driver, "bulenox_login_failed")

    finally:
        input("Press Enter to close browser...")
        driver.quit()


if __name__ == '__main__':
    main()