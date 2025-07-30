import os
import time
import random
import json
import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_executor import BaseExecutor

class StealthExecutor(BaseExecutor):
    """
    StealthExecutor for automated trading with anti-detection features
    """
    
    def __init__(self, signal, stopLoss=None, takeProfit=None, stealth_level=2):
        """
        Initialize StealthExecutor with stealth features
        
        Args:
            signal: Trade signal dictionary with symbol, side, quantity
            stopLoss: Optional stop loss price
            takeProfit: Optional take profit price
            stealth_level: Level of stealth (1-3, where 3 is most stealthy)
        """
        super().__init__(signal, stopLoss, takeProfit)
        # Load environment variables
        load_dotenv()
        
        # Get credentials from environment variables
        self.username = os.getenv('BROKER_USERNAME')
        self.password = os.getenv('BROKER_PASSWORD')
        self.broker_url = os.getenv('BROKER_URL')
        
        # Get Chrome profile settings
        self.profile_path = os.getenv('BULENOX_PROFILE_PATH')
        self.profile_name = os.getenv('BULENOX_PROFILE_NAME')
        
        # Debug output for URL
        print(f"Broker URL: {self.broker_url}")
        print(f"Using Chrome profile: {self.profile_path}/{self.profile_name}")
        
        # Ensure broker_url is a string
        if self.broker_url is None:
            self.broker_url = "https://bulenox.com/login"
            print(f"Using default broker URL: {self.broker_url}")
        
        # Stealth settings
        self.stealth_level = min(max(stealth_level, 1), 3)  # Ensure between 1-3
        self.user_agent = self._get_random_user_agent()
        self.proxy = os.getenv('PROXY_SERVER')
        
        # Set screenshot directory
        self.screenshot_dir = os.path.join(os.getcwd(), "logs/screenshots")
        # Check if screenshots directory exists and create it if it doesn't
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir, exist_ok=True)
            print(f"Created screenshot directory: {self.screenshot_dir}")
        else:
            print(f"Using existing screenshot directory: {self.screenshot_dir}")
        self.log_file = "logs/stealth_trades.json"
        
        # Ensure log directories exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def _get_random_user_agent(self):
        """
        Return a random user agent to avoid fingerprinting
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        return random.choice(user_agents)
    
    def _save_screenshot(self, driver, name):
        """
        Save a screenshot with error handling and print the path
        
        Args:
            driver: Selenium WebDriver instance
            name: Name for the screenshot file
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.screenshot_dir}/{name}_{timestamp}.png"
            driver.save_screenshot(filename)
            print(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving screenshot {name}: {e}")
            return None
            
    def _init_driver(self):
        """
        Initialize Chrome driver with stealth features and user profile
        """
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use existing Chrome profile if available
        if self.profile_path and self.profile_name:
            user_data_dir = self.profile_path
            profile = self.profile_name
            print(f"Using Chrome profile: {user_data_dir} with profile: {profile}")
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument(f"--profile-directory={profile}")
            # Add experimental options to avoid detection
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
        else:
            # Stealth options if not using profile
            chrome_options.add_argument(f"user-agent={self.user_agent}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Add proxy if available and stealth level is high
            if self.proxy and self.stealth_level >= 2:
                chrome_options.add_argument(f'--proxy-server={self.proxy}')
        
        # Higher stealth levels
        if self.stealth_level >= 3 and not (self.profile_path and self.profile_name):
            # Randomize window size slightly
            width = random.randint(1200, 1400)
            height = random.randint(800, 900)
            chrome_options.add_argument(f"--window-size={width},{height}")
            
            # Add additional privacy options
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins-discovery")
        
        try:
            # Get chromedriver path from environment variable
            chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
            
            # Check if chromedriver path exists
            if chromedriver_path and os.path.exists(chromedriver_path):
                print(f"Using chromedriver at: {chromedriver_path}")
                # Set the path in the service object for newer Selenium versions
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                print("Chromedriver path not found or invalid. Using default chromedriver.")
                driver = webdriver.Chrome(options=chrome_options)
            
            # Execute CDP commands to add additional stealth
            if self.stealth_level >= 2 and not (self.profile_path and self.profile_name):
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
                    """
                })
            
            return driver
        except Exception as e:
            print(f"Error initializing driver: {e}")
            # Fallback to basic options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            try:
                # Try to use default chromedriver with service
                return webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                print(f"Failed to initialize driver with fallback options: {e2}")
                raise Exception(f"Could not initialize Chrome driver: {e2}")
    
    def _humanlike_typing(self, element, text):
        """
        Type text like a human with random delays between keystrokes
        """
        for char in text:
            element.send_keys(char)
            # Random delay between keystrokes
            time.sleep(random.uniform(0.05, 0.2))
    
    def _humanlike_movement(self, driver, element):
        """
        Move to element like a human with curved path and variable speed
        Simplified to avoid 'move target out of bounds' errors
        """
        try:
            # Simple direct movement to element with a single action
            actions = ActionChains(driver)
            actions.move_to_element(element)
            actions.pause(random.uniform(0.1, 0.3))
            actions.perform()
            return True
        except Exception as e:
            print(f"Humanlike movement error: {e}")
            # Fallback to JavaScript scrolling if movement fails
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(random.uniform(0.3, 0.7))
                return True
            except Exception as e2:
                print(f"Fallback scrolling error: {e2}")
                return False
    
    def _login(self, driver):
        """
        Login to broker with stealth features
        """
        try:
            # Ensure broker_url is a string
            if not isinstance(self.broker_url, str):
                print(f"Invalid broker URL type: {type(self.broker_url)}")
                self.broker_url = "https://bulenox.com/member/login"
                print(f"Using default broker URL: {self.broker_url}")
            
            # Navigate to broker URL
            print(f"Navigating to broker URL: {self.broker_url}")
            driver.get(self.broker_url)
            
            # Take screenshot after navigation
            self._save_screenshot(driver, "login_navigation")
            
            # Random delay before starting login
            time.sleep(random.uniform(1.0, 3.0))
            
            # Check if already logged in
            if any(pattern in driver.current_url for pattern in ["dashboard", "trading", "member", "account", "platform", "terminal"]):
                if "login" not in driver.current_url and "signin" not in driver.current_url:
                    print(f"Already logged in - detected from URL: {driver.current_url}")
                    return True
                    
            # Specialized approach for Bulenox login
            if "bulenox.com" in driver.current_url:
                try:
                    print("Using specialized approach for Bulenox login")
                    # Save screenshot of initial page
                    self._save_screenshot(driver, "bulenox_initial_page")
                    
                    # First try: Direct JavaScript injection to find and fill login form
                    js_login = """
                    (function() {
                        // Find all input fields
                        var inputs = document.querySelectorAll('input');
                        var usernameField = null;
                        var passwordField = null;
                        var submitButton = null;
                        var loginForm = null;
                        
                        // Log what we find for debugging
                        console.log('Found ' + inputs.length + ' input fields');
                        
                        // Find username and password fields
                        for (var i = 0; i < inputs.length; i++) {
                            var inputType = inputs[i].type || '';
                            var inputId = inputs[i].id || '';
                            var inputName = inputs[i].name || '';
                            console.log('Input #' + i + ': type=' + inputType + ', id=' + inputId + ', name=' + inputName);
                            
                            if ((inputType === 'text' || inputType === 'email') && !usernameField) {
                                usernameField = inputs[i];
                                console.log('Found username field: ' + inputId);
                            }
                            if (inputType === 'password' && !passwordField) {
                                passwordField = inputs[i];
                                console.log('Found password field: ' + inputId);
                            }
                        }
                        
                        // If we didn't find fields by type, try by position (first two inputs)
                        if ((!usernameField || !passwordField) && inputs.length >= 2) {
                            usernameField = inputs[0];
                            passwordField = inputs[1];
                            console.log('Using first two inputs as username/password fields');
                        }
                        
                        // Find login form
                        if (usernameField) {
                            loginForm = usernameField.closest('form');
                        } else if (passwordField) {
                            loginForm = passwordField.closest('form');
                        }
                        
                        // Find submit button
                        if (loginForm) {
                            // First try: button with type=submit inside the form
                            submitButton = loginForm.querySelector('button[type="submit"]');
                            if (!submitButton) {
                                submitButton = loginForm.querySelector('input[type="submit"]');
                            }
                        }
                        
                        // Second try: any button with login-related text
                        if (!submitButton) {
                            var buttons = document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {
                                var btnText = buttons[i].textContent.toLowerCase();
                                if (btnText.includes('login') || btnText.includes('sign in') || btnText.includes('log in')) {
                                    submitButton = buttons[i];
                                    console.log('Found login button by text: ' + btnText);
                                    break;
                                }
                            }
                        }
                        
                        // Third try: first button in the form
                        if (!submitButton && loginForm) {
                            var formButtons = loginForm.querySelectorAll('button');
                            if (formButtons.length > 0) {
                                submitButton = formButtons[0];
                                console.log('Using first button in form');
                            }
                        }
                        
                        // Fill in credentials if fields found
                        if (usernameField && passwordField) {
                            // Clear fields first
                            usernameField.value = '';
                            passwordField.value = '';
                            
                            // Set values
                            usernameField.value = arguments[0];
                            passwordField.value = arguments[1];
                            
                            // Trigger input events to ensure any listeners are notified
                            var event = new Event('input', { bubbles: true });
                            usernameField.dispatchEvent(event);
                            passwordField.dispatchEvent(event);
                            
                            // Submit form
                            if (submitButton) {
                                submitButton.click();
                                return 'Form submitted with button click';
                            } else if (loginForm) {
                                loginForm.submit();
                                return 'Form submitted directly';
                            } else {
                                // Last resort: try to submit by pressing Enter in password field
                                var keyEvent = new KeyboardEvent('keypress', {
                                    key: 'Enter',
                                    code: 'Enter',
                                    keyCode: 13,
                                    which: 13,
                                    bubbles: true
                                });
                                passwordField.dispatchEvent(keyEvent);
                                return 'Attempted submission with Enter key';
                            }
                        }
                        
                        return 'Login fields not found or could not be filled';
                    })
                    """
                    
                    result = driver.execute_script(js_login, self.username, self.password)
                    print(f"JavaScript login result: {result}")
                    
                    # Wait for login to complete
                    time.sleep(5)
                    self._save_screenshot(driver, "bulenox_js_login_attempt")
                    
                    # Check if login was successful
                    if any(pattern in driver.current_url for pattern in ["dashboard", "trading", "member", "account", "platform", "terminal"]):
                        if "login" not in driver.current_url and "signin" not in driver.current_url:
                            print(f"JavaScript login successful - detected from URL: {driver.current_url}")
                            self._save_screenshot(driver, "bulenox_login_success")
                            return True
                    
                    # If JavaScript approach didn't work, try a more direct approach
                    print("JavaScript login approach didn't succeed, trying direct form submission")
                    
                    # Try a more direct approach with explicit element IDs
                    try:
                        # Refresh the page to ensure we have a clean state
                        driver.refresh()
                        time.sleep(3)
                        
                        # Try to find elements by explicit XPath
                        username_xpath = "//input[@type='text' or @type='email'][1]"
                        password_xpath = "//input[@type='password'][1]"
                        submit_xpath = "//button[@type='submit' or contains(text(), 'Login') or contains(text(), 'Sign In')][1]"
                        
                        username_field = driver.find_element(By.XPATH, username_xpath)
                        password_field = driver.find_element(By.XPATH, password_xpath)
                        
                        # Clear and fill fields
                        username_field.clear()
                        self._humanlike_typing(username_field, self.username)
                        time.sleep(0.5)
                        
                        password_field.clear()
                        self._humanlike_typing(password_field, self.password)
                        time.sleep(0.5)
                        
                        self._save_screenshot(driver, "bulenox_direct_pre_submit")
                        
                        # Try to find and click submit button
                        try:
                            submit_button = driver.find_element(By.XPATH, submit_xpath)
                            submit_button.click()
                            print("Clicked submit button directly")
                        except:
                            # If button not found, try submitting with Enter key
                            print("Submit button not found, trying Enter key")
                            password_field.send_keys(Keys.RETURN)
                        
                        time.sleep(5)
                        self._save_screenshot(driver, "bulenox_direct_post_submit")
                        
                        # Check if login was successful
                        if any(pattern in driver.current_url for pattern in ["dashboard", "trading", "member", "account", "platform", "terminal"]):
                            if "login" not in driver.current_url and "signin" not in driver.current_url:
                                print(f"Direct login successful - detected from URL: {driver.current_url}")
                                self._save_screenshot(driver, "bulenox_login_success")
                                return True
                    except Exception as e:
                        print(f"Direct login approach error: {str(e)}")
                except Exception as e:
                    print(f"Bulenox specialized login approach error: {str(e)}")
                    # Continue with regular approach
            
            # If using Chrome profile, we might already be logged in
            # Check for trading elements or account info that would indicate we're logged in
            if self.profile_path and self.profile_name:
                try:
                    # Wait a bit for the page to fully load
                    time.sleep(random.uniform(3.0, 5.0))
                    
                    # Check if we're on a page that requires login
                    if "login" not in driver.current_url and "sign-in" not in driver.current_url:
                        print(f"Not on login page, current URL: {driver.current_url}")
                        # Try to find elements that would only be visible when logged in
                        account_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'account') or contains(@class, 'user') or contains(@class, 'profile')]")
                        if len(account_elements) > 0:
                            print(f"Already logged in via Chrome profile - found {len(account_elements)} account elements")
                            return True
                    
                    # Check if cookies indicate we're logged in
                    cookies = driver.get_cookies()
                    auth_cookies = [cookie for cookie in cookies if 'auth' in cookie.get('name', '').lower() or 'session' in cookie.get('name', '').lower()]
                    if auth_cookies:
                        print(f"Found authentication cookies: {[c.get('name') for c in auth_cookies]}")
                        # Try navigating to dashboard or trading page
                        try:
                            dashboard_url = self.broker_url.replace("login", "dashboard")
                            print(f"Attempting to navigate to dashboard: {dashboard_url}")
                            driver.get(dashboard_url)
                            time.sleep(3)
                            if "login" not in driver.current_url:
                                print("Successfully navigated to dashboard - already logged in")
                                return True
                        except Exception as e:
                            print(f"Error navigating to dashboard: {e}")
                except Exception as e:
                    print(f"Error checking login status: {e}")
            
            # Print page title and URL for debugging
            print(f"Page title: {driver.title}")
            print(f"Current URL: {driver.current_url}")
            print(f"Page source snippet: {driver.page_source[:200]}...")
            
            # Wait for login form with random additional time
            wait_time = 15 + random.uniform(0, 5)
            print(f"Waiting for login form for {wait_time} seconds...")
            
            # Try multiple locator strategies for the login form
            login_form_found = False
            login_form_locators = [
                (By.ID, "amember-login"),
                (By.NAME, "amember_login"),
                (By.XPATH, "//input[@type='text'][@name='amember_login']"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'login')]"),
                (By.XPATH, "//input[@type='text' and contains(@name, 'login')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Username')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Email')]"),
                (By.XPATH, "//form//input[@type='text'][1]")
            ]
            
            for locator_type, locator_value in login_form_locators:
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((locator_type, locator_value))
                    )
                    print(f"Login form found using locator: {locator_type}={locator_value}")
                    login_form_found = True
                    break
                except:
                    continue
            
            if not login_form_found:
                print("Login form not found using standard locators. Taking screenshot...")
                self._save_screenshot(driver, "login_form_not_found")
                print(f"Page source: {driver.page_source[:500]}...")
                
                # Try to find any input fields as a last resort
                try:
                    print("Trying to find any input fields as a last resort...")
                    input_fields = driver.find_elements(By.XPATH, "//input")
                    if len(input_fields) >= 2:
                        print(f"Found {len(input_fields)} input fields, will attempt to use them")
                        login_form_found = True
                    else:
                        raise Exception("Not enough input fields found")
                except Exception as e:
                    print(f"Last resort locator failed: {e}")
                    raise Exception("Login form not found")
            
            # Get login elements using multiple strategies
            email_field = None
            password_field = None
            login_button = None
            
            # Try multiple locator strategies for username/email field
            username_locators = [
                (By.ID, "amember-login"),
                (By.NAME, "amember_login"),
                (By.XPATH, "//input[@type='text'][@name='amember_login']"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'login')]"),
                (By.XPATH, "//input[@type='text' and contains(@name, 'login')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Username')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Email')]"),
                (By.XPATH, "//form//input[@type='text'][1]")
            ]
            
            for locator_type, locator_value in username_locators:
                try:
                    email_field = driver.find_element(locator_type, locator_value)
                    print(f"Found username field using: {locator_type}={locator_value}")
                    break
                except:
                    continue
            
            # Try multiple locator strategies for password field
            password_locators = [
                (By.ID, "amember-pass"),
                (By.NAME, "amember_pass"),
                (By.XPATH, "//input[@type='password'][@name='amember_pass']"),
                (By.XPATH, "//input[@type='password' and contains(@id, 'pass')]"),
                (By.XPATH, "//input[@type='password' and contains(@name, 'pass')]"),
                (By.XPATH, "//input[@type='password' and contains(@placeholder, 'Password')]"),
                (By.XPATH, "//form//input[@type='password'][1]")
            ]
            
            for locator_type, locator_value in password_locators:
                try:
                    password_field = driver.find_element(locator_type, locator_value)
                    print(f"Found password field using: {locator_type}={locator_value}")
                    break
                except:
                    continue
            
            # Try multiple locator strategies for login button
            button_locators = [
                (By.XPATH, "//input[@type='submit'][@value='Login']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                (By.XPATH, "//button[contains(@class, 'login')]"),
                (By.XPATH, "//input[contains(@class, 'login')]"),
                (By.XPATH, "//form//button[1]"),
                (By.XPATH, "//form//input[@type='submit'][1]")
            ]
            
            for locator_type, locator_value in button_locators:
                try:
                    login_button = driver.find_element(locator_type, locator_value)
                    print(f"Found login button using: {locator_type}={locator_value}")
                    break
                except:
                    continue
            
            # Check if all elements were found
            if not email_field or not password_field or not login_button:
                print("Failed to find all login elements")
                self._save_screenshot(driver, "login_element_not_found")
                
                # Try to find any input fields as a last resort
            try:
                print("Trying to find login elements as a last resort...")
                input_fields = driver.find_elements(By.XPATH, "//input")
                if len(input_fields) >= 2:
                    # Assume first text/email input is username, first password input is password
                    if not email_field:
                        for i, field in enumerate(input_fields):
                            field_type = field.get_attribute("type")
                            field_id = field.get_attribute("id") or ""
                            field_name = field.get_attribute("name") or ""
                            field_class = field.get_attribute("class") or ""
                            
                            print(f"Input #{i+1}: type={field_type}, id={field_id}, name={field_name}, class={field_class}")
                            
                            if field.get_attribute("type") in ["text", "email"]:
                                email_field = field
                                print(f"Found username field as input #{i+1}")
                                break
                    
                    if not password_field:
                        for i, field in enumerate(input_fields):
                            if field.get_attribute("type") == "password":
                                password_field = field
                                print(f"Found password field as input #{i+1}")
                                break
                    
                    if not login_button:
                        # Try to find any button or input[type=submit]
                        buttons = driver.find_elements(By.XPATH, "//button | //input[@type='submit']")
                        for i, button in enumerate(buttons):
                            button_text = button.text.lower()
                            button_type = button.get_attribute("type") or ""
                            button_id = button.get_attribute("id") or ""
                            button_class = button.get_attribute("class") or ""
                            
                            print(f"Button #{i+1}: text={button.text}, type={button_type}, id={button_id}, class={button_class}")
                            
                            if ("login" in button_text or "sign in" in button_text or "log in" in button_text or 
                                button_type == "submit" or "login" in button_id.lower() or "submit" in button_id.lower()):
                                login_button = button
                                print(f"Found login button with text: {button.text}")
                                break
                            elif i == 0 and buttons:  # If no better match, use first button
                                login_button = buttons[0]
                                print("Using first button as login button")
                
                # If we still can't find elements, try a more aggressive approach for Bulenox
                if (not email_field or not password_field or not login_button) and "bulenox.com" in driver.current_url:
                    print("Trying aggressive element finding for Bulenox")
                    # Try to find elements by their position on the page
                    all_inputs = driver.find_elements(By.TAG_NAME, "input")
                    if len(all_inputs) >= 2:
                        # Assume first input is username, second is password
                        if not email_field and all_inputs[0].get_attribute("type") != "password":
                            email_field = all_inputs[0]
                            print("Found username field by position")
                        if not password_field:
                            for inp in all_inputs:
                                if inp.get_attribute("type") == "password":
                                    password_field = inp
                                    print("Found password field by type")
                                    break
                        
                        # Find the closest button
                        all_buttons = driver.find_elements(By.TAG_NAME, "button")
                        if all_buttons and not login_button:
                            login_button = all_buttons[0]  # Assume first button is login
                            print("Found login button by position")
                
                if not email_field or not password_field or not login_button:
                    raise Exception("Could not find all required login elements")
            except Exception as e:
                print(f"Last resort element finding failed: {e}")
                raise
            
            print("All login elements found")
            
            # Print credentials for debugging (masked)
            print(f"Using username: {self.username[:3]}{'*' * (len(self.username) - 3)}")
            print(f"Using password: {'*' * len(self.password)}")
            
            # Basic login approach (more reliable)
            try:
                # Clear fields first
                email_field.clear()
                password_field.clear()
                
                # Type credentials with humanlike typing if stealth level is high
                if self.stealth_level >= 2:
                    self._humanlike_typing(email_field, self.username)
                    time.sleep(random.uniform(0.5, 1.0))
                    self._humanlike_typing(password_field, self.password)
                else:
                    # Type credentials directly
                    email_field.send_keys(self.username)
                    time.sleep(random.uniform(0.3, 0.7))
                    password_field.send_keys(self.password)
                time.sleep(random.uniform(0.3, 0.7))
                
                # Try clicking the button normally first
                try:
                    login_button.click()
                    print("Login button clicked normally")
                except Exception as click_e:
                    print(f"Normal click failed: {click_e}, trying JavaScript click")
                    # Click login button using JavaScript (most reliable)
                    driver.execute_script("arguments[0].click();", login_button)
                    print("Login form submitted using JavaScript")
            except Exception as e:
                print(f"Basic login failed: {e}")
                self._save_screenshot(driver, "login_basic_failed")
                
                # Try fallback login method with dynamic element finding
                try:
                    print("Trying fallback login method...")
                    # Create a JavaScript string with proper escaping
                    js_login = f"""
                    (function() {{
                      var emailField = document.querySelector('input[type="text"][name*="login"], input[type="email"], input[id*="login"], input[name*="email"], form input[type="text"]:first-of-type');
                      var passwordField = document.querySelector('input[type="password"]');
                      var submitButton = document.querySelector('input[type="submit"], button[type="submit"], button.login, form button');
                      
                      if (emailField && passwordField) {{
                        emailField.value = "{self.username}";
                        passwordField.value = "{self.password}";
                        
                        if (submitButton) {{
                          submitButton.click();
                          return "Button clicked";
                        }} else if (document.forms.length > 0) {{
                          var form = document.forms[0];
                          form.submit();
                          return "Form submitted";
                        }}
                      }}
                      
                      return "Login elements not found";
                    }})()
                    """
                    
                    driver.execute_script(js_login)
                    print("Fallback login script executed")
                except Exception as e2:
                    print(f"Fallback login failed: {e2}")
                    return False
            
            # Wait for login completion with enhanced detection
            wait_time = 45  # Extended timeout (seconds)
            print(f"Waiting for login to complete for {wait_time} seconds...")
            try:
                # Store the initial URL for comparison
                initial_url = driver.current_url
                print(f"Initial URL before login: {initial_url}")
                
                # Define success indicators
                success_url_patterns = ["dashboard", "trading", "account", "home", "platform", "terminal", "member"]
                success_element_patterns = [
                    "//a[contains(@href, 'account') or contains(@href, 'user') or contains(@href, 'profile') or contains(@href, 'logout')]",
                    "//div[contains(@class, 'account') or contains(@class, 'user')]",
                    "//span[contains(text(), 'Account') or contains(text(), 'Balance')]",
                    "//button[contains(text(), 'Logout') or contains(text(), 'Sign out')]",
                    "//a[contains(text(), 'Logout') or contains(text(), 'Sign out')]",
                    "//div[contains(@class, 'dashboard')]",
                    "//div[contains(@class, 'member-dashboard')]"
                ]
                
                # Define error indicators
                error_patterns = [
                    "//div[contains(@class, 'error') or contains(@class, 'alert') or contains(@class, 'notification')]",
                    "//p[contains(@class, 'error') or contains(text(), 'incorrect') or contains(text(), 'failed')]",
                    "//span[contains(@class, 'error') or contains(text(), 'incorrect') or contains(text(), 'failed')]"
                ]
                
                # Wait for URL to change or dashboard element to appear
                start_time = time.time()
                login_success = False
                
                while time.time() - start_time < wait_time:
                    try:
                        current_url = driver.current_url
                        print(f"Current URL: {current_url}")
                        
                        # Check if URL changed from initial login page
                        if current_url != initial_url and not "login" in current_url.lower():
                            print("URL changed from login page")
                            
                            # Check for success URL patterns
                            for pattern in success_url_patterns:
                                if pattern in current_url.lower():
                                    print(f"Login successful - redirected to URL containing '{pattern}'")
                                    login_success = True
                                    break
                        
                        # If URL check found success, break the main loop
                        if login_success:
                            break
                        
                        # Check for success elements
                        for xpath in success_element_patterns:
                            try:
                                elements = driver.find_elements(By.XPATH, xpath)
                                if elements and any(e.is_displayed() for e in elements):
                                    print(f"Login successful - found element matching: {xpath}")
                                    login_success = True
                                    break
                            except Exception as e:
                                print(f"Error checking success element {xpath}: {e}")
                        
                        # If element check found success, break the main loop
                        if login_success:
                            break
                        
                        # Check for authentication cookies
                        cookies = driver.get_cookies()
                        auth_cookies = [c for c in cookies if any(auth_term in c['name'].lower() 
                                                                for auth_term in ['auth', 'session', 'token', 'logged', 'user'])]
                        if auth_cookies:
                            print(f"Found {len(auth_cookies)} authentication-related cookies")
                            # If we have auth cookies but still on login page, try navigating to dashboard
                            if "login" in current_url.lower():
                                try:
                                    # Try to navigate to a dashboard or home page
                                    driver.get(driver.current_url.split('/login')[0] + '/dashboard')
                                    time.sleep(2)
                                    if "login" not in driver.current_url.lower():
                                        print("Successfully navigated to dashboard after finding auth cookies")
                                        login_success = True
                                        break
                                except:
                                    pass
                        
                        # Check for error messages
                        for xpath in error_patterns:
                            try:
                                error_elements = driver.find_elements(By.XPATH, xpath)
                                for error in error_elements:
                                    if error.is_displayed() and error.text.strip():
                                        error_text = error.text.strip()
                                        print(f"Login error detected: {error_text}")
                                        self._save_screenshot(driver, "login_error")
                                        
                                        # Check if it's a temporary error that might resolve with retry
                                        temporary_errors = ["temporary", "try again", "timeout", "busy", "maintenance"]
                                        if any(temp in error_text.lower() for temp in temporary_errors):
                                            print("Detected temporary error, will continue waiting")
                                        else:
                                            return False
                            except Exception as e:
                                print(f"Error checking error elements {xpath}: {e}")
                    except Exception as e:
                        print(f"Error during login completion check: {e}")
                    
                    # Check page title for additional clues
                    try:
                        page_title = driver.title
                        print(f"Current page title: {page_title}")
                        
                        # Check if title indicates success
                        success_title_terms = ["dashboard", "trading", "platform", "account", "terminal"]
                        if any(term in page_title.lower() for term in success_title_terms):
                            print(f"Login successful - page title indicates success: {page_title}")
                            login_success = True
                            break
                    except Exception as e:
                        print(f"Error checking page title: {e}")
                    
                    time.sleep(1)
                
                if not login_success:
                    print("Login timed out without success or error")
                    self._save_screenshot(driver, "login_error")
                    
                    # As a last resort, check if we're not on a login page anymore
                    if initial_url != driver.current_url and "login" not in driver.current_url.lower():
                        print("URL changed from login page and not on login page - assuming success")
                        login_success = True
                
                print(f"Login completed with result: {login_success}")
                return login_success
            
            except Exception as e:
                print(f"Error waiting for login completion: {e}")
                self._save_screenshot(driver, "login_error")
                return False
        
        except Exception as e:
            print(f"Login exception: {e}")
            self._save_screenshot(driver, "login_exception")
            return False
    
    def _place_trade(self, driver):
        """
        Place a trade with stealth features
        """
        try:
            # Navigate to trading page
            trading_url = self.broker_url.replace("login", "trading")
            driver.get(trading_url)
            
            # Wait for trading interface to load
            wait_time = 10 + random.uniform(0, 2)
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.ID, "symbol"))
            )
            
            # Take screenshot of trading page
            self._save_screenshot(driver, "trading_page")
            
            # Get trading elements
            symbol_input = driver.find_element(By.ID, "symbol")
            quantity_input = driver.find_element(By.ID, "quantity")
            
            # Enter symbol with stealth features
            if self.stealth_level >= 2:
                self._humanlike_movement(driver, symbol_input)
                symbol_input.clear()
                self._humanlike_typing(symbol_input, self.signal["symbol"])
                
                # Select symbol from dropdown if needed
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{self.signal['symbol']}')]"))
                    )
                    symbol_option = driver.find_element(By.XPATH, f"//div[contains(text(), '{self.signal['symbol']}')]")
                    self._humanlike_movement(driver, symbol_option)
                    symbol_option.click()
                except (TimeoutException, NoSuchElementException):
                    # Symbol might be directly accepted without dropdown
                    pass
            else:
                symbol_input.clear()
                symbol_input.send_keys(self.signal["symbol"])
            
            # Random pause between inputs
            time.sleep(random.uniform(0.5, 1.5))
            
            # Enter quantity with stealth features
            if self.stealth_level >= 2:
                self._humanlike_movement(driver, quantity_input)
                quantity_input.clear()
                self._humanlike_typing(quantity_input, str(self.signal["quantity"]))
            else:
                quantity_input.clear()
                quantity_input.send_keys(str(self.signal["quantity"]))
            
            # Enter stop loss if provided
            if self.stopLoss:
                sl_input = driver.find_element(By.ID, "stopLoss")
                if self.stealth_level >= 2:
                    self._humanlike_movement(driver, sl_input)
                    sl_input.clear()
                    self._humanlike_typing(sl_input, str(self.stopLoss))
                else:
                    sl_input.clear()
                    sl_input.send_keys(str(self.stopLoss))
            
            # Enter take profit if provided
            if self.takeProfit:
                tp_input = driver.find_element(By.ID, "takeProfit")
                if self.stealth_level >= 2:
                    self._humanlike_movement(driver, tp_input)
                    tp_input.clear()
                    self._humanlike_typing(tp_input, str(self.takeProfit))
                else:
                    tp_input.clear()
                    tp_input.send_keys(str(self.takeProfit))
            
            # Random pause before clicking buy/sell
            time.sleep(random.uniform(0.5, 1.5))
            
            # Click buy or sell button
            button_id = "buyButton" if self.signal["side"].lower() == "buy" else "sellButton"
            trade_button = driver.find_element(By.ID, button_id)
            
            if self.stealth_level >= 2:
                self._humanlike_movement(driver, trade_button)
            
            trade_button.click()
            
            # Handle confirmation dialog if present
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "confirmButton"))
                )
                confirm_button = driver.find_element(By.ID, "confirmButton")
                
                if self.stealth_level >= 2:
                    self._humanlike_movement(driver, confirm_button)
                
                confirm_button.click()
            except (TimeoutException, NoSuchElementException):
                # No confirmation dialog
                pass
            
            # Wait for trade confirmation
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Trade executed successfully')]"))
            )
            
            # Take screenshot of confirmation
            self._save_screenshot(driver, "trade_success")
            
            return True
        except Exception as e:
            print(f"Trade error: {e}")
            self._save_screenshot(driver, "stealth_trade_error")
            return False
    
    def _log_trade(self, success):
        """
        Log trade details to JSON file
        """
        try:
            # Load existing trades
            try:
                with open(self.log_file, "r") as f:
                    trades = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                trades = []
            
            # Add new trade
            trade_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "symbol": self.signal["symbol"],
                "side": self.signal["side"],
                "quantity": self.signal["quantity"],
                "stopLoss": self.stopLoss,
                "takeProfit": self.takeProfit,
                "stealth_level": self.stealth_level,
                "success": success
            }
            trades.append(trade_record)
            
            # Save updated trades
            with open(self.log_file, "w") as f:
                json.dump(trades, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error logging trade: {e}")
            return False
    
    def execute_trade(self):
        """
        Execute a trade with stealth features
        """
        driver = None
        success = False
        
        try:
            # Initialize driver with stealth features
            driver = self._init_driver()
            
            # Random delay before starting
            time.sleep(random.uniform(1.0, 3.0))
            
            # Login to broker
            if not self._login(driver):
                raise Exception("Failed to login to broker")
            
            # Random delay between login and trade
            time.sleep(random.uniform(2.0, 5.0))
            
            # Place the trade
            success = self._place_trade(driver)
            
            # Log the trade
            self._log_trade(success)
            
            return success
        except Exception as e:
            print(f"Trade execution failed: {e}")
            self._log_trade(False)
            return False
        finally:
            if driver:
                # Random delay before quitting
                time.sleep(random.uniform(1.0, 2.0))
                driver.quit()
    
    def health(self):
        """
        Check if the executor is healthy
        """
        try:
            driver = self._init_driver()
            login_success = self._login(driver)
            driver.quit()
            return login_success
        except Exception as e:
            print(f"Health check failed: {e}")
            return False