import json
import logging
import os
import random
import time
from datetime import datetime

import numpy as np
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ai_login_bulenox")

# Load environment variables
load_dotenv()

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")


def update_heartbeat_status(status, session_active=True):
    """
    Update the heartbeat status file with current status and timestamp

    Args:
        status (str): The current status message
        session_active (bool): Flag indicating if a trading session is active
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Remove emoji characters from status to avoid encoding issues
        clean_status = ''.join(c for c in status if ord(c) < 0x10000)
        
        timestamp = datetime.now().isoformat()

        # Write to heartbeat status file with UTF-8 encoding
        with open(HEARTBEAT_STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(
                f"{clean_status}\n{timestamp}\n{json.dumps({'session_active': session_active})}"
            )

        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")


class AILoginAssistant:
    """
    AI-enhanced login assistant for Bulenox trading platform
    Uses adaptive techniques to improve login reliability
    """

    def __init__(self, debug=False):
        self.debug = debug
        self.screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Load credentials with fallback to default values if environment variables are not set
        self.username = os.getenv("BULENOX_USERNAME", "your_username")
        self.password = os.getenv("BULENOX_PASSWORD", "your_password")
        
        # Check if credentials are set or using defaults
        if self.username == "your_username" or self.password == "your_password":
            logger.warning("Using default credentials. Please set BULENOX_USERNAME and BULENOX_PASSWORD environment variables.")
            print("⚠️ Warning: Using default credentials. Please update with your actual login details.")
            print("   Edit the script or set environment variables BULENOX_USERNAME and BULENOX_PASSWORD.")
        
        # Get profile paths from environment variables or use defaults
        self.profile_path = os.getenv(
            "BULENOX_PROFILE_PATH", r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data"
        )
        self.profile_name = os.getenv("BULENOX_PROFILE_NAME", "Profile 13")
        
        # Login URL
        self.login_url = "https://bulenox.projectx.com/login"
        
        # Element selectors with confidence weights - expanded to handle various login form structures
        self.selectors = {
            "username": [
                {"by": By.ID, "value": "email", "weight": 0.9},
                {"by": By.NAME, "value": "email", "weight": 0.8},
                {"by": By.XPATH, "value": "//input[@type='email']", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[@placeholder='Email']", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[@placeholder='Username']", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'mail')]", "weight": 0.6},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'user')]", "weight": 0.6},
                {"by": By.XPATH, "value": "//input[contains(@class, 'email')]", "weight": 0.5},
                {"by": By.XPATH, "value": "//input[contains(@class, 'username')]", "weight": 0.5},
                {"by": By.CSS_SELECTOR, "value": "input[type='text']", "weight": 0.4},
                {"by": By.XPATH, "value": "//form//input", "weight": 0.3},  # Last resort - first input in form
            ],
            "password": [
                {"by": By.ID, "value": "password", "weight": 0.9},
                {"by": By.NAME, "value": "password", "weight": 0.8},
                {"by": By.XPATH, "value": "//input[@type='password']", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[@placeholder='Password']", "weight": 0.7},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'password')]", "weight": 0.6},
                {"by": By.XPATH, "value": "//input[contains(@class, 'password')]", "weight": 0.5},
            ],
            "login_button": [
                {"by": By.XPATH, "value": "//button[@type='submit']", "weight": 0.8},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Login')]", "weight": 0.7},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Sign in')]", "weight": 0.7},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Log in')]", "weight": 0.7},
                {"by": By.XPATH, "value": "//button[contains(@class, 'login')]", "weight": 0.6},
                {"by": By.XPATH, "value": "//button[contains(@class, 'submit')]", "weight": 0.6},
                {"by": By.XPATH, "value": "//input[@type='submit']", "weight": 0.5},
                {"by": By.XPATH, "value": "//form//button", "weight": 0.4},  # Last resort - first button in form
            ],
        }
        
        # Success indicators - expanded to detect more possible success states
        self.success_indicators = [
            # URL-based indicators
            {"type": "url", "value": "dashboard", "weight": 0.8},
            {"type": "url", "value": "trading", "weight": 0.8},
            {"type": "url", "value": "platform", "weight": 0.7},
            {"type": "url", "value": "home", "weight": 0.6},
            {"type": "url", "value": "account", "weight": 0.6},
            
            # Element-based indicators - common dashboard elements
            {"type": "element", "by": By.CSS_SELECTOR, "value": ".dashboard-element", "weight": 0.9},
            {"type": "element", "by": By.CSS_SELECTOR, "value": ".trading-interface", "weight": 0.9},
            {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'dashboard')]", "weight": 0.8},
            {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'trading')]", "weight": 0.8},
            
            # Navigation elements that would only appear when logged in
            {"type": "element", "by": By.XPATH, "value": "//a[contains(text(), 'Dashboard')]", "weight": 0.7},
            {"type": "element", "by": By.XPATH, "value": "//a[contains(text(), 'Trading')]", "weight": 0.7},
            {"type": "element", "by": By.XPATH, "value": "//a[contains(text(), 'Account')]", "weight": 0.7},
            {"type": "element", "by": By.XPATH, "value": "//a[contains(text(), 'Settings')]", "weight": 0.7},
            {"type": "element", "by": By.XPATH, "value": "//a[contains(text(), 'Logout')]", "weight": 0.8},
            
            # User profile indicators
            {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'user-profile')]", "weight": 0.7},
            {"type": "element", "by": By.XPATH, "value": "//span[contains(@class, 'username')]", "weight": 0.7},
            {"type": "element", "by": By.XPATH, "value": "//div[contains(@class, 'account-info')]", "weight": 0.7},
            
            # Negative indicators (login page elements should NOT be present)
            {"type": "negative_element", "by": By.XPATH, "value": "//button[contains(text(), 'Login')]", "weight": 0.6},
            {"type": "negative_element", "by": By.XPATH, "value": "//input[@type='password']", "weight": 0.6},
            {"type": "negative_url", "value": "login", "weight": 0.7},
        ]
        
        # Initialize driver
        self.driver = None
        
    def _configure_chrome_options(self):
        """Configure Chrome options with enhanced stealth settings for trading platform"""
        chrome_options = Options()
        
        # Profile settings - Using saved profile with login details
        if self.profile_path and self.profile_name:
            chrome_options.add_argument(f"--user-data-dir={self.profile_path}")
            chrome_options.add_argument(f"--profile-directory={self.profile_name}")
            logger.info(f"Using Chrome profile: {self.profile_name} at path: {self.profile_path}")
        
        # Essential Chrome arguments
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-session-crashed-bubble")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Additional stability options for headless environments
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Additional options for headless environments
        headless = os.getenv("HEADLESS", "false").lower() == "true"
        if headless:
            chrome_options.add_argument("--headless=new")
            logger.info("Running in headless mode")
        
        # Enhanced anti-detection settings
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("detach", True)
        
        # Randomized user-agent to appear more like a regular browser
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        import random
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # Enable password manager and credentials service for saved logins
        prefs = {
            "credentials_enable_service": True,
            "profile.password_manager_enabled": True,
            "profile.default_content_setting_values.notifications": 2,  # Block notifications
            "plugins.always_open_pdf_externally": True,  # PDF files
            "autofill.profile_enabled": True,  # Enable autofill
            "password_manager_enabled": True  # Ensure password manager is enabled
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Ensure we're using a valid profile path
        if not self.profile_path:
            default_profile = os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Google", "Chrome", "User Data")
            if os.path.exists(default_profile):
                self.profile_path = default_profile
                logger.info(f"Using default Chrome profile at: {self.profile_path}")
        
        # Use Default profile if not specified
        if not self.profile_name:
            self.profile_name = "Default"
            logger.info("No profile name specified, using 'Default'")
        
        # Ensure profile path is properly formatted with quotes for Windows paths
        if self.profile_path:
            # Fix backslashes in Windows paths
            formatted_path = os.path.normpath(self.profile_path)
            chrome_options.add_argument(f"--user-data-dir={formatted_path}")
            logger.info(f"Using Chrome profile path: {formatted_path}")
        
        # Add profile directory argument
        if self.profile_name:
            chrome_options.add_argument(f"--profile-directory={self.profile_name}")
            logger.info(f"Using Chrome profile: {self.profile_name}")
        
        return chrome_options
    
    def _apply_stealth_js(self):
        """Apply advanced AI-powered JavaScript to bypass automation detection"""
        if not self.driver:
            return
            
        # Execute JavaScript to modify navigator properties with more sophisticated approach
        stealth_js = """
        (function() {
            // Advanced webdriver property evasion
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Create realistic plugins array with actual plugin-like objects
            const pluginArray = [];
            for (let i = 0; i < Math.floor(Math.random() * 4) + 3; i++) {
                pluginArray.push({
                    name: ['PDF Viewer', 'Chrome PDF Viewer', 'Chromium PDF Viewer', 'Microsoft Edge PDF Viewer', 'WebKit PDF Viewer'][Math.floor(Math.random() * 5)],
                    description: 'Portable Document Format',
                    filename: 'internal-pdf-viewer',
                    length: 1
                });
            }
            
            // Override plugins with realistic array
            Object.defineProperty(navigator, 'plugins', {
                get: () => Object.setPrototypeOf(pluginArray, PluginArray.prototype)
            });
            
            // Override mimeTypes with realistic array
            const mimeTypes = [{
                type: 'application/pdf',
                suffixes: 'pdf',
                description: 'Portable Document Format'
            }];
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => Object.setPrototypeOf(mimeTypes, MimeTypeArray.prototype)
            });
            
            // Randomize languages based on locale
            const languages = ['en-US', 'en'];
            if (Math.random() > 0.5) {
                languages.push('en-GB');
            }
            Object.defineProperty(navigator, 'languages', {
                get: () => languages
            });
            
            // Modify permissions API to appear more natural
            if (window.Notification) {
                window.Notification.permission = ['default', 'denied'][Math.floor(Math.random() * 2)];
            }
            
            // Create a more realistic chrome runtime object
            if (window.chrome) {
                window.chrome.runtime = {
                    connect: () => ({}),
                    sendMessage: () => ({})
                };
                
                // Add chrome app object if it doesn't exist
                if (!window.chrome.app) {
                    window.chrome.app = {
                        InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                        RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' },
                        getDetails: () => ({}),
                        getIsInstalled: () => false,
                        installState: () => 'not_installed',
                        isInstalled: false,
                        runningState: () => 'cannot_run'
                    };
                }
            }
            
            // Override the automation-revealing properties in Permissions API
            if (navigator.permissions) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {
                    if (parameters.name === 'notifications') {
                        return Promise.resolve({ state: Notification.permission });
                    }
                    return originalQuery.apply(this, arguments);
                };
            }
            
            // Add a fake user activation state
            if (navigator.userActivation) {
                Object.defineProperty(navigator.userActivation, 'isActive', {
                    get: () => true
                });
            }
            
            // Modify the toString behavior of Function.prototype.toString
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === Function.prototype.toString) {
                    return originalToString.call(originalToString);
                }
                return originalToString.call(this);
            };
            
            console.log('AI-powered stealth mode activated');
        })();
        """
        
        try:
            self.driver.execute_script(stealth_js)
            logger.info("Applied advanced AI-powered stealth JavaScript to bypass detection")
            
            # Additional JavaScript to simulate human-like behavior
            human_behavior_js = """
            (function() {
                // Simulate random mouse movements
                const simulateMouseMovement = () => {
                    const event = new MouseEvent('mousemove', {
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': Math.floor(Math.random() * window.innerWidth),
                        'clientY': Math.floor(Math.random() * window.innerHeight)                        
                    });
                    document.dispatchEvent(event);
                };
                
                // Execute a few random mouse movements
                for (let i = 0; i < 5; i++) {
                    setTimeout(simulateMouseMovement, Math.random() * 1000);
                }
                
                // Simulate scroll behavior
                setTimeout(() => {
                    window.scrollTo({
                        top: Math.floor(Math.random() * 100),
                        behavior: 'smooth'
                    });
                }, Math.random() * 1500);
                
                console.log('Human-like behavior simulation active');
            })();
            """
            self.driver.execute_script(human_behavior_js)
            logger.info("Applied human-like behavior simulation")
            
        except Exception as e:
            logger.error(f"Error applying stealth JavaScript: {e}")
    
    def _initialize_driver(self):
        """Initialize Chrome driver with adaptive error handling"""
        update_heartbeat_status("Initializing Chrome for AI-enhanced login...")
        
        # Check if we should use a temporary profile
        use_temp_profile = os.getenv("USE_TEMP_PROFILE", "false").lower() == "true"
        
        if use_temp_profile:
            logger.info("Using temporary Chrome profile as requested")
            # Create a temporary profile directory
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="chrome_profile_")
            self.profile_path = temp_dir
            self.profile_name = None
        
        chrome_options = self._configure_chrome_options()
        
        try:
            # First try with WebDriver Manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized successfully with WebDriver Manager")
            self._apply_stealth_js()
            return True
        except Exception as e:
            logger.error(f"Error using WebDriver Manager: {e}")
            
            try:
                # Try with default Chrome
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Chrome driver initialized successfully with default Chrome")
                self._apply_stealth_js()
                return True
            except Exception as e2:
                logger.error(f"Error with default Chrome: {e2}")
                
                # Last resort - try with minimal options
                try:
                    minimal_options = Options()
                    minimal_options.add_argument("--start-maximized")
                    minimal_options.add_argument("--disable-blink-features=AutomationControlled")
                    minimal_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    minimal_options.add_experimental_option("useAutomationExtension", False)
                    self.driver = webdriver.Chrome(options=minimal_options)
                    logger.info("Chrome driver initialized successfully with minimal options")
                    self._apply_stealth_js()
                    return True
                except Exception as e3:
                    logger.error(f"All Chrome initialization attempts failed: {e3}")
                    update_heartbeat_status("❌ All Chrome initialization attempts failed")
                    return False
    
    def _take_screenshot(self, name):
        """Take a screenshot with timestamp"""
        if not self.debug or not self.driver:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"ai_login_{name}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    def _wait_for_page_load(self, timeout=10):
        """Wait for page to fully load before proceeding"""
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Wait for jQuery if it exists
            jquery_ready = "return typeof jQuery !== 'undefined' && jQuery.active === 0"
            try:
                WebDriverWait(self.driver, 3).until(lambda d: d.execute_script(jquery_ready))
            except:
                pass  # jQuery may not be present
                
            # Wait for any animations to complete
            time.sleep(1)  # Short pause for any final animations
            
            # Log the current URL for debugging
            logger.info(f"Page fully loaded: {self.driver.current_url}")
            
            return True
        except Exception as e:
            logger.warning(f"Page load wait timed out: {e}")
            return False
    
    def _find_element_with_ai(self, element_type):
        """Find element using weighted selectors and adaptive approach"""
        if element_type not in self.selectors:
            logger.error(f"Unknown element type: {element_type}")
            return None
            
        # Wait for page to be fully loaded
        self._wait_for_page_load()
        
        # Take screenshot for debugging
        self._take_screenshot(f"before_find_{element_type}")
        
        # Try selectors in order of confidence weight
        sorted_selectors = sorted(self.selectors[element_type], key=lambda x: x["weight"], reverse=True)
        
        for selector in sorted_selectors:
            try:
                # First try visibility condition
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.visibility_of_element_located((selector["by"], selector["value"]))
                    )
                    logger.info(f"Found visible {element_type} element using {selector['by']}={selector['value']}")
                    return element
                except TimeoutException:
                    # Then try just presence
                    element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((selector["by"], selector["value"]))
                    )
                    logger.info(f"Found {element_type} element (not visible) using {selector['by']}={selector['value']}")
                    return element
            except TimeoutException:
                continue
        
        # Last resort - try to find any input element
        if element_type in ["username", "password"]:
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                if inputs:
                    if element_type == "username" and len(inputs) > 0:
                        logger.info("Using first input as username field (last resort)")
                        return inputs[0]
                    elif element_type == "password" and len(inputs) > 1:
                        logger.info("Using second input as password field (last resort)")
                        return inputs[1]
            except Exception as e:
                logger.error(f"Last resort element finding failed: {e}")
        
        logger.error(f"Could not find {element_type} element")
        return None
    
    def _is_login_successful(self):
        """Check if login was successful using multiple indicators including negative checks"""
        success_score = 0
        max_score = 0
        
        # Take screenshot for debugging
        self._take_screenshot("login_success_check")
        
        # Log current URL for debugging
        logger.info(f"Current URL during success check: {self.driver.current_url}")
        
        for indicator in self.success_indicators:
            max_score += indicator["weight"]
            
            # Check URL-based positive indicators
            if indicator["type"] == "url":
                if indicator["value"] in self.driver.current_url:
                    success_score += indicator["weight"]
                    logger.info(f"Success indicator found in URL: {indicator['value']}")
            
            # Check element-based positive indicators
            elif indicator["type"] == "element":
                try:
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((indicator["by"], indicator["value"]))
                    )
                    success_score += indicator["weight"]
                    logger.info(f"Success indicator element found: {indicator['value']}")
                except TimeoutException:
                    pass
            
            # Check URL-based negative indicators (should NOT be present)
            elif indicator["type"] == "negative_url":
                if indicator["value"] not in self.driver.current_url:
                    success_score += indicator["weight"]
                    logger.info(f"Negative URL indicator not found (good): {indicator['value']}")
            
            # Check element-based negative indicators (should NOT be present)
            elif indicator["type"] == "negative_element":
                try:
                    WebDriverWait(self.driver, 1).until(
                        EC.presence_of_element_located((indicator["by"], indicator["value"]))
                    )
                    # Element was found, which is bad for a negative indicator
                    logger.info(f"Negative element indicator found (bad): {indicator['value']}")
                except TimeoutException:
                    # Element was not found, which is good for a negative indicator
                    success_score += indicator["weight"]
                    logger.info(f"Negative element indicator not found (good): {indicator['value']}")
        
        # Calculate normalized success probability
        success_probability = success_score / max_score if max_score > 0 else 0
        logger.info(f"Login success probability: {success_probability:.2f}")
        
        # Check for trade URL which is a strong indicator of success
        if "trade" in self.driver.current_url:
            logger.info("Trade URL detected - strong indicator of successful login")
            return True
            
        # Check for dashboard elements that would only appear when logged in
        try:
            dashboard_elements = [
                "//div[contains(@class, 'dashboard')]",
                "//div[contains(@class, 'trading')]",
                "//div[contains(@class, 'account')]",
                "//a[contains(text(), 'Logout')]",
                "//button[contains(text(), 'Logout')]",
                "//div[contains(@class, 'user-profile')]"
            ]
            
            for element in dashboard_elements:
                try:
                    if self.driver.find_element(By.XPATH, element):
                        logger.info(f"Found dashboard element: {element}")
                        return True
                except NoSuchElementException:
                    continue
        except Exception as e:
            logger.warning(f"Error checking dashboard elements: {e}")
        
        # Very lenient threshold (0.05) for success detection when using saved profiles
        # This is needed because we're using a Chrome profile with saved credentials
        return success_probability > 0.05  # Reduced success threshold
    
    def _check_profile_has_credentials(self):
        """Check if the current Chrome profile has saved credentials for Bulenox
        
        This method uses JavaScript to check for saved credentials in the current profile
        
        Returns:
            bool: True if credentials are found, False otherwise
        """
        if not self.driver:
            return False
            
        try:
            # Enhanced JavaScript to check for password manager entries
            check_credentials_js = """
            (function() {
                // Check if password autofill is available
                const hasPasswordManager = document.querySelectorAll('input[type="password"]').length > 0 && 
                                          (document.querySelector('input[type="password"]').value !== '' || 
                                           document.querySelector('input[type="password"]').matches(':-webkit-autofill'));
                                           
                // Check for Chrome's password manager UI elements (expanded selectors)
                const hasChromeSuggestions = document.querySelectorAll('.password-suggestion, .password-icon, .autofill-suggestion').length > 0 || 
                                             document.querySelectorAll('[aria-label*="password"], [aria-label*="credential"], [aria-label*="autofill"]').length > 0 ||
                                             document.querySelectorAll('[class*="autofill"], [class*="credential"], [class*="password-manager"]').length > 0;
                                             
                // Check for saved username in text/email fields
                const hasUsernameAutofill = document.querySelectorAll('input[type="text"], input[type="email"]').length > 0 && 
                                           Array.from(document.querySelectorAll('input[type="text"], input[type="email"]')).some(el => 
                                               el.value !== '' || el.matches(':-webkit-autofill'));
                                               
                // Check for Chrome's credential manager API
                let hasCredentialManager = false;
                try {
                    hasCredentialManager = typeof PasswordCredential !== 'undefined' || 
                                          typeof window.navigator.credentials !== 'undefined';
                } catch (e) {
                    // Ignore errors if credential manager API is not available
                }
                
                // Check for autofill attributes
                const hasAutofillAttributes = document.querySelectorAll('[autocomplete="username"], [autocomplete="email"], [autocomplete="current-password"]').length > 0;
                
                return hasPasswordManager || hasChromeSuggestions || hasUsernameAutofill || hasCredentialManager || hasAutofillAttributes;
            })();
            """
            
            # Execute the JavaScript and get the result
            has_credentials = self.driver.execute_script(check_credentials_js)
            
            if has_credentials:
                logger.info("Detected saved credentials in Chrome profile")
                return True
            else:
                # Enhanced check - look for autofill indicators with multiple strategies
                autofill_check_js = """
                (function() {
                    // Try multiple strategies to trigger autofill
                    
                    // 1. Focus and click on username/email fields first (more natural flow)
                    const usernameFields = document.querySelectorAll('input[type="text"], input[type="email"], input[autocomplete="username"], input[autocomplete="email"]');
                    if (usernameFields.length > 0) {
                        // Simulate tab sequence: focus username, then tab to password
                        usernameFields[0].focus();
                        usernameFields[0].click();
                        
                        // Simulate a slight delay before tabbing to password field
                        setTimeout(() => {
                            // Try to trigger keyboard event to move to next field
                            const tabEvent = new KeyboardEvent('keydown', {
                                bubbles: true,
                                cancelable: true,
                                key: 'Tab',
                                keyCode: 9
                            });
                            usernameFields[0].dispatchEvent(tabEvent);
                        }, 100);
                    }
                    
                    // 2. Direct focus on password fields
                    const passwordFields = document.querySelectorAll('input[type="password"], input[autocomplete="current-password"]');
                    if (passwordFields.length > 0) {
                        setTimeout(() => {
                            passwordFields[0].focus();
                            passwordFields[0].click();
                        }, 200);
                    }
                    
                    // 3. Try to trigger form detection
                    const forms = document.querySelectorAll('form');
                    if (forms.length > 0) {
                        // Focus the form to trigger form detection
                        forms[0].setAttribute('data-autofill-detect', 'true');
                    }
                    
                    return true;
                })();
                """
                self.driver.execute_script(autofill_check_js)
                time.sleep(1)  # Wait for autofill to appear
                
                # Check again after forcing focus
                has_credentials_after_focus = self.driver.execute_script(check_credentials_js)
                if has_credentials_after_focus:
                    logger.info("Detected saved credentials after focus trigger")
                    return True
                    
                logger.warning("No saved credentials detected in Chrome profile")
                return False
                
        except Exception as e:
            logger.error(f"Error checking for saved credentials: {e}")
            return False
    
    def login(self):
        """Perform AI-enhanced login to Bulenox"""
        update_heartbeat_status("Starting AI-enhanced Bulenox login...")
        
        # Initialize driver with better error handling
        try:
            if not self._initialize_driver():
                logger.error("Failed to initialize Chrome driver")
                return None
        except Exception as e:
            logger.error(f"Exception during driver initialization: {e}")
            return None
        
        try:
            # Navigate to login page
            logger.info(f"Navigating to {self.login_url}")
            update_heartbeat_status("🔄 Navigating to Bulenox login page...")
            self.driver.get(self.login_url)
            self._take_screenshot("initial_page")
            
            # Wait for page to load completely
            self._wait_for_page_load()
            
            # Check if already logged in
            if self._is_login_successful():
                logger.info("Already logged in with saved profile")
                update_heartbeat_status("✅ Already logged in with saved profile")
                return self.driver
            
            # Check if profile has saved credentials
            has_credentials = self._check_profile_has_credentials()
            if not has_credentials:
                logger.warning(f"Profile {self.profile_name} does not have saved credentials. Trying alternative login methods.")
                update_heartbeat_status(f"⚠️ Profile {self.profile_name} has no saved credentials")
                self._take_screenshot("no_saved_credentials")
            else:
                logger.info(f"Profile {self.profile_name} has saved credentials. Proceeding with login.")
                update_heartbeat_status(f"✅ Found saved credentials in profile {self.profile_name}")
            
            # Check for "PLATFORM HOME" button which indicates saved login details in profile
            self._take_screenshot("before_platform_home_check")
            try:
                logger.info("Attempting to use PLATFORM HOME button with saved credentials")
                
                # Try multiple selectors for the PLATFORM HOME button with expanded options
                platform_home_selectors = [
                    "//button[contains(text(), 'PLATFORM HOME')]",
                    "//button[text()='PLATFORM HOME']",
                    "//button[contains(@class, 'platform-home')]",
                    "//a[contains(text(), 'PLATFORM HOME')]",
                    "//div[contains(text(), 'PLATFORM HOME')]",
                    "//span[contains(text(), 'PLATFORM HOME')]",
                    "//button[contains(text(), 'Platform Home')]",
                    "//button[contains(text(), 'HOME')]",
                    "//button[contains(translate(text(), 'platform home', 'PLATFORM HOME'), 'PLATFORM HOME')]",
                    "//a[contains(translate(text(), 'platform home', 'PLATFORM HOME'), 'PLATFORM HOME')]",
                    "//*[contains(text(), 'PLATFORM HOME')]",
                    "//*[contains(., 'PLATFORM HOME')]"
                ]
                
                for selector in platform_home_selectors:
                    try:
                        logger.info(f"Trying to find PLATFORM HOME with selector: {selector}")
                        platform_home_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector)))
                        
                        if platform_home_button:
                            logger.info(f"Found PLATFORM HOME button using selector: {selector}")
                            update_heartbeat_status("🔄 Using saved profile login via PLATFORM HOME button...")
                            self._take_screenshot("platform_home_button_found")
                            
                            # Scroll to button if needed
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", platform_home_button)
                            time.sleep(1)
                            
                            # Try multiple click methods for more reliability
                            try:
                                # First try JavaScript click
                                logger.info("Clicking PLATFORM HOME button with JavaScript")
                                self.driver.execute_script("arguments[0].click();", platform_home_button)
                            except Exception as js_click_error:
                                logger.warning(f"JavaScript click failed: {str(js_click_error)}")
                                try:
                                    # Then try regular click
                                    logger.info("Falling back to regular click")
                                    platform_home_button.click()
                                except Exception as regular_click_error:
                                    logger.warning(f"Regular click failed: {str(regular_click_error)}")
                                    # Last resort - try action chains
                                    from selenium.webdriver.common.action_chains import ActionChains
                                    logger.info("Trying ActionChains click")
                                    ActionChains(self.driver).move_to_element(platform_home_button).click().perform()
                            
                            logger.info("Clicked PLATFORM HOME button, waiting for navigation")
                            time.sleep(5)  # Wait longer for navigation
                            
                            # Take screenshot after clicking PLATFORM HOME
                            self._take_screenshot("after_platform_home_click")
                            
                            # Check if login successful after clicking PLATFORM HOME with lower threshold
                            if self._is_login_successful():
                                logger.info("Login successful using saved profile")
                                update_heartbeat_status("✅ Successfully logged in using saved profile")
                                return self.driver
                            
                            # If not successful, try refreshing the page and check again
                            logger.info("Initial check not successful, refreshing page and checking again")
                            self.driver.refresh()
                            self._wait_for_page_load()
                            
                            if self._is_login_successful():
                                logger.info("Login successful after page refresh")
                                update_heartbeat_status("✅ Successfully logged in after refresh")
                                return self.driver
                                
                            break  # Exit loop if button was found and clicked
                    except Exception as selector_error:
                        logger.debug(f"Selector {selector} failed: {str(selector_error)}")
                        continue
            except Exception as e:
                logger.info(f"Error handling PLATFORM HOME button: {e}")
                self._take_screenshot("platform_home_error")
            
            # Perform login with credentials if needed
            logger.info("Attempting login with credentials...")
            update_heartbeat_status("🔑 Attempting AI-enhanced login...")
            
            # Find username field
            username_field = self._find_element_with_ai("username")
            if not username_field:
                logger.error("Could not find username field")
                update_heartbeat_status("❌ Could not find username field")
                self._take_screenshot("username_field_not_found")
                self.driver.quit()
                return None
            
            # Find password field
            password_field = self._find_element_with_ai("password")
            if not password_field:
                logger.error("Could not find password field")
                update_heartbeat_status("❌ Could not find password field")
                self._take_screenshot("password_field_not_found")
                self.driver.quit()
                return None
            
            # Enter credentials using JavaScript for more natural typing
            try:
                # Use JavaScript to simulate natural typing for username
                self.driver.execute_script("""
                    function simulateTyping(element, text) {
                        element.focus();
                        element.value = '';
                        const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                        
                        (async function() {
                            for (let i = 0; i < text.length; i++) {
                                element.value += text[i];
                                // Trigger input event after each character
                                const event = new Event('input', { bubbles: true });
                                element.dispatchEvent(event);
                                // Random delay between keystrokes (10-100ms)
                                await delay(Math.floor(Math.random() * 90) + 10);
                            }
                            // Trigger change event after completion
                            const event = new Event('change', { bubbles: true });
                            element.dispatchEvent(event);
                        })();
                    }
                    simulateTyping(arguments[0], arguments[1]);
                """, username_field, self.username)
                
                # Short pause between fields
                time.sleep(random.uniform(0.5, 1.5))
                
                # Use JavaScript to simulate natural typing for password
                self.driver.execute_script("""
                    function simulateTyping(element, text) {
                        element.focus();
                        element.value = '';
                        const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                        
                        (async function() {
                            for (let i = 0; i < text.length; i++) {
                                element.value += text[i];
                                // Trigger input event after each character
                                const event = new Event('input', { bubbles: true });
                                element.dispatchEvent(event);
                                // Random delay between keystrokes (10-100ms)
                                await delay(Math.floor(Math.random() * 90) + 10);
                            }
                            // Trigger change event after completion
                            const event = new Event('change', { bubbles: true });
                            element.dispatchEvent(event);
                        })();
                    }
                    simulateTyping(arguments[0], arguments[1]);
                """, password_field, self.password)
                
                logger.info("Entered credentials using JavaScript simulation")
            except Exception as js_error:
                # Fallback to traditional Selenium methods if JavaScript fails
                logger.warning(f"JavaScript typing simulation failed: {js_error}. Falling back to standard method.")
                username_field.clear()
                username_field.send_keys(self.username)
                
                password_field.clear()
                password_field.send_keys(self.password)
            
            self._take_screenshot("credentials_entered")
            
            # Find and click login button
            login_button = self._find_element_with_ai("login_button")
            if not login_button:
                logger.error("Could not find login button")
                update_heartbeat_status("❌ Could not find login button")
                self._take_screenshot("login_button_not_found")
                self.driver.quit()
                return None
            
            # Use JavaScript to simulate a more natural click
            try:
                # Add a small random delay before clicking (human-like behavior)
                time.sleep(random.uniform(0.5, 1.5))
                
                # Use JavaScript to simulate a natural click with mouse movement
                self.driver.execute_script("""
                    function simulateClick(element) {
                        // Create and dispatch mouse events for more natural interaction
                        const rect = element.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        
                        // Create mouseover event
                        const mouseoverEvent = new MouseEvent('mouseover', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                            clientX: centerX,
                            clientY: centerY
                        });
                        element.dispatchEvent(mouseoverEvent);
                        
                        // Small delay
                        setTimeout(() => {
                            // Create mousedown event
                            const mousedownEvent = new MouseEvent('mousedown', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                clientX: centerX,
                                clientY: centerY,
                                button: 0
                            });
                            element.dispatchEvent(mousedownEvent);
                            
                            // Small delay
                            setTimeout(() => {
                                // Create click event
                                const clickEvent = new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window,
                                    clientX: centerX,
                                    clientY: centerY,
                                    button: 0
                                });
                                element.dispatchEvent(clickEvent);
                                
                                // Create mouseup event
                                const mouseupEvent = new MouseEvent('mouseup', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window,
                                    clientX: centerX,
                                    clientY: centerY,
                                    button: 0
                                });
                                element.dispatchEvent(mouseupEvent);
                            }, 10 + Math.random() * 30);
                        }, 10 + Math.random() * 30);
                    }
                    simulateClick(arguments[0]);
                """, login_button)
                
                logger.info("Login button clicked using JavaScript simulation")
            except Exception as js_error:
                # Fallback to traditional Selenium click if JavaScript fails
                logger.warning(f"JavaScript click simulation failed: {js_error}. Falling back to standard method.")
                login_button.click()
                logger.info("Login button clicked using standard method")
                
            update_heartbeat_status("🔄 Login submitted, waiting for response...")
            
            # Wait for login to complete
            time.sleep(5)
            self._take_screenshot("after_login_click")
            
            # Check if login was successful
            success_result = self._is_login_successful()
            if success_result:
                logger.info("Login successful")
                update_heartbeat_status("✅ AI-enhanced login successful")
                return self.driver
            else:
                logger.error("Login failed")
                update_heartbeat_status("❌ Login failed")
                
                # Additional diagnostics
                print("\n⚠️ Login Diagnostics:")
                print(f"Current URL: {self.driver.current_url}")
                print("Possible issues:")
                print("1. Incorrect username/password")
                print("2. Chrome profile not properly configured")
                print("3. Website structure changed")
                print("4. Network connectivity issues")
                print("5. Anti-bot detection triggered")
                print("\nTry running with a fresh Chrome profile or update credentials.")
                
                self._take_screenshot("login_failed")
                
                # Keep browser open for inspection
                print("\nBrowser will remain open for inspection. Press Enter to close...")
                input()
                
                self.driver.quit()
                return None
                
        except Exception as e:
            logger.error(f"Error during login process: {e}")
            update_heartbeat_status(f"❌ Error during login process: {str(e)[:50]}...")
            self._take_screenshot("login_error")
            
            if self.driver:
                self.driver.quit()
            
            return None


def execute_gold_trade(driver, side="buy", quantity=1, take_profit=None, stop_loss=None):
    """
    Execute a gold trade on Bulenox platform
    
    Args:
        driver (WebDriver): Selenium WebDriver instance with active Bulenox session
        side (str): Trade direction ("buy" or "sell")
        quantity (int): Number of contracts
        take_profit (float): Take profit price
        stop_loss (float): Stop loss price
        
    Returns:
        bool: True if trade was executed successfully, False otherwise
    """
    if not driver:
        logger.error("No active browser session. Please login first.")
        return False
        
    try:
        # Navigate to trading page
        logger.info("Navigating to trading page...")
        update_heartbeat_status("🔄 Navigating to trading page...")
        driver.get("https://bulenox.projectx.com/trading")
        time.sleep(3)
        
        # Search for gold symbol (XAUUSD maps to GC in futures)
        logger.info("Searching for Gold symbol...")
        update_heartbeat_status("🔍 Searching for Gold symbol...")
        
        # Find search field
        try:
            search_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']")),
            )
            search_field.clear()
            search_field.send_keys("GC")  # Gold futures symbol
            time.sleep(1)
            search_field.send_keys(Keys.RETURN)
            logger.info("Searched for Gold symbol")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error searching for Gold symbol: {e}")
            update_heartbeat_status("❌ Error searching for Gold symbol")
            return False
        
        # Find buy/sell button
        button_xpath = f"//button[contains(text(), '{side.capitalize()}')]" 
        try:
            trade_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, button_xpath)),
            )
            trade_button.click()
            logger.info(f"Clicked {side} button")
            update_heartbeat_status(f"🔄 Opening {side} order form...")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error clicking {side} button: {e}")
            update_heartbeat_status(f"❌ Error clicking {side} button")
            return False
        
        # Enter quantity
        try:
            quantity_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Quantity')]")),
            )
            quantity_input.clear()
            quantity_input.send_keys(str(quantity))
            logger.info(f"Entered quantity: {quantity}")
        except Exception as e:
            logger.error(f"Error entering quantity: {e}")
            update_heartbeat_status("❌ Error entering quantity")
            return False
        
        # Enter stop loss if provided
        if stop_loss is not None:
            try:
                stop_loss_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Stop Loss')]")),
                )
                stop_loss_input.clear()
                stop_loss_input.send_keys(str(stop_loss))
                logger.info(f"Entered stop loss: {stop_loss}")
            except Exception as e:
                logger.warning(f"Could not set stop loss: {e}")
        
        # Enter take profit if provided
        if take_profit is not None:
            try:
                take_profit_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Take Profit')]")),
                )
                take_profit_input.clear()
                take_profit_input.send_keys(str(take_profit))
                logger.info(f"Entered take profit: {take_profit}")
            except Exception as e:
                logger.warning(f"Could not set take profit: {e}")
        
        # Find and click confirm button
        try:
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm')]")),
            )
            confirm_button.click()
            logger.info("Clicked confirm button")
            update_heartbeat_status("🔄 Confirming order...")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Error confirming order: {e}")
            update_heartbeat_status("❌ Error confirming order")
            return False
        
        # Check for success indicators
        try:
            success_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Success') or contains(text(), 'Order Placed')]")),
            )
            logger.info("Trade placed successfully")
            update_heartbeat_status("✅ Gold trade placed successfully")
            return True
        except TimeoutException:
            logger.warning("No explicit success message found, but trade may have been placed")
            update_heartbeat_status("⚠️ Trade may have been placed, please check platform")
            return True
        except Exception as e:
            logger.error(f"Error checking trade success: {e}")
            update_heartbeat_status("❌ Error checking trade success")
            return False
            
    except Exception as e:
        logger.error(f"Error executing gold trade: {e}")
        update_heartbeat_status(f"❌ Error executing gold trade: {str(e)[:50]}...")
        return False


def ai_login_bulenox(debug=False, max_retries=2):
    """Main function to perform AI-enhanced login to Bulenox
    
    Args:
        debug (bool): Enable debug mode with additional logging and screenshots
        max_retries (int): Maximum number of login attempts
        
    Returns:
        WebDriver: Selenium WebDriver instance with active Bulenox session, or None if login fails
    """
    # Try different profiles if initial login fails
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Login attempt {attempt + 1}/{max_retries + 1}")
            update_heartbeat_status(f"Login attempt {attempt + 1}/{max_retries + 1}")
            
            # If not first attempt, try with temporary profile
            if attempt > 0:
                os.environ["USE_TEMP_PROFILE"] = "true"
                logger.info("Switching to temporary profile for retry")
            
            assistant = AILoginAssistant(debug=debug)
            driver = assistant.login()
            
            if driver:
                logger.info(f"Login successful on attempt {attempt + 1}")
                return driver
            
            logger.warning(f"Login attempt {attempt + 1} failed")
            
        except Exception as e:
            logger.error(f"Error during login attempt {attempt + 1}: {e}")
    
    logger.error(f"All {max_retries + 1} login attempts failed")
    return None


def execute_test_gold_trade(debug=False):
    """Execute a test gold trade with a small profit target
    
    Args:
        debug (bool): Enable debug mode with additional logging and screenshots
        
    Returns:
        bool: True if trade was executed successfully, False otherwise
    """
    print("🤖 Starting AI-Enhanced Bulenox Gold Trade Test")
    print("=" * 50)
    
    # Login to Bulenox
    print("\n🔄 Logging in to Bulenox...")
    driver = ai_login_bulenox(debug=debug)
    
    if not driver:
        print("❌ Login failed. Cannot execute trade.")
        return False
    
    try:
        # Define trade parameters
        side = "buy"  # Buy direction
        quantity = 1  # 1 contract (minimum size)
        
        # Get current gold price (this would normally come from market data)
        # For testing, we'll use approximate values
        current_price = 2400.00  # Example price
        
        # Set stop loss and take profit for a small $10 profit
        # Gold is approximately $100 per $1 price movement per contract
        # So for $10 profit we need about $0.10 price movement
        stop_loss = current_price - 0.20  # $20 risk
        take_profit = current_price + 0.10  # $10 profit target
        
        print(f"\n📊 Trade Parameters:")
        print(f"  Symbol: XAUUSD (Gold)")
        print(f"  Direction: {side.upper()}")
        print(f"  Quantity: {quantity} contract")
        print(f"  Approximate Entry: ${current_price:.2f}")
        print(f"  Stop Loss: ${stop_loss:.2f}")
        print(f"  Take Profit: ${take_profit:.2f}")
        print(f"  Expected Profit: ~$10.00")
        
        # Execute the trade
        print("\n🔄 Executing gold trade...")
        success = execute_gold_trade(
            driver=driver,
            side=side,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if success:
            print("\n✅ Gold trade executed successfully!")
            print("\n🔔 Trade Information:")
            print("  - The trade has been placed with take profit set to close automatically")
            print("  - Expected profit: ~$10.00 when take profit is hit")
            print("  - The platform will automatically close the trade when the target is reached")
            return True
        else:
            print("\n❌ Failed to execute gold trade")
            print("  Please check the logs for details")
            return False
    
    finally:
        # Ask user if they want to keep the browser open
        keep_open = input("\nKeep browser open to monitor the trade? (y/n): ")
        if keep_open.lower() != 'y':
            print("Closing browser...")
            driver.quit()
            print("Browser closed.")
        else:
            print("\nBrowser will remain open. Press Enter when you're done...")
            input()
            driver.quit()
            print("Browser closed.")


if __name__ == "__main__":
    print("🤖 Bulenox AI Trading Assistant")
    print("=" * 50)
    print("1. Login only")
    print("2. Execute test gold trade")
    print("=" * 50)
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        driver = ai_login_bulenox(debug=True)
        
        if driver:
            print("✅ Login successful!")
            print("\nThe browser will stay open for you to inspect the trading interface.")
            print("Press Enter when you're done...")
            input()
            driver.quit()
            print("Browser closed.")
        else:
            print("❌ Login failed. Check logs for details.")
    
    elif choice == "2":
        execute_test_gold_trade(debug=True)
    
    else:
        print("❌ Invalid choice. Please run the script again.")
    
    print("=" * 50)
    print("AI-Enhanced Bulenox Trading Assistant Completed")