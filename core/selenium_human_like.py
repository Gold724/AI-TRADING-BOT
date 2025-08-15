# core/selenium_human_like.py

import os
import time
import random
import logging
import json
from typing import Dict, Any, Optional, List, Tuple, Union
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("selenium_human.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("selenium_human")

# Constants
ACCOUNTS_CONFIG_FILE = os.path.join("config", "accounts_config.json")
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5

# Ensure directories exist
os.makedirs("config", exist_ok=True)


def load_accounts_config() -> Dict:
    """Load accounts configuration from file
    
    Returns:
        Dict: Accounts configuration
    """
    default_config = {
        "accounts": {
            "main_funded_01": {
                "broker": "example_broker",
                "login_url": "https://example.com/login",
                "username": "${MAIN_ACCOUNT_USERNAME}",
                "password": "${MAIN_ACCOUNT_PASSWORD}",
                "account_number": "12345678",
                "risk_level": "high",
                "max_lot_size": 1.0,
                "selectors": {
                    "username_field": "username",
                    "password_field": "password",
                    "login_button": "login-button"
                }
            },
            "backup_funded_02": {
                "broker": "example_broker",
                "login_url": "https://example.com/login",
                "username": "${BACKUP_ACCOUNT_USERNAME}",
                "password": "${BACKUP_ACCOUNT_PASSWORD}",
                "account_number": "87654321",
                "risk_level": "medium",
                "max_lot_size": 0.5,
                "selectors": {
                    "username_field": "username",
                    "password_field": "password",
                    "login_button": "login-button"
                }
            }
        },
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
        ],
        "proxy_settings": {
            "enabled": False,
            "proxies": [
                {
                    "host": "proxy1.example.com",
                    "port": 8080,
                    "username": "${PROXY_USERNAME}",
                    "password": "${PROXY_PASSWORD}"
                }
            ]
        },
        "stealth_settings": {
            "typing_speed": {
                "min_delay": 0.05,
                "max_delay": 0.2
            },
            "mouse_movement": {
                "enabled": True,
                "natural_curve": True
            },
            "page_load_wait": {
                "min_time": 1.0,
                "max_time": 3.0
            },
            "action_delays": {
                "min_time": 0.5,
                "max_time": 2.0
            }
        }
    }
    
    try:
        if os.path.exists(ACCOUNTS_CONFIG_FILE):
            with open(ACCOUNTS_CONFIG_FILE, "r") as f:
                return json.load(f)
        else:
            # Create default config file if it doesn't exist
            with open(ACCOUNTS_CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=4)
            return default_config
    except Exception as e:
        logger.error(f"Error loading accounts config: {e}")
        return default_config


def resolve_env_vars(value: str) -> str:
    """Resolve environment variables in a string
    
    Args:
        value (str): String with potential environment variables
    
    Returns:
        str: String with environment variables resolved
    """
    if not isinstance(value, str):
        return value
    
    if "${" in value and "}" in value:
        # Extract environment variable name
        env_var = value.split("${")
        if len(env_var) > 1:
            env_var = env_var[1].split("}")[0]
            env_value = os.environ.get(env_var, "")
            if env_value:
                return value.replace(f"${{{env_var}}}", env_value)
            else:
                logger.warning(f"Environment variable {env_var} not found")
    
    return value


def random_delay(min_time: float = 0.5, max_time: float = 2.0) -> None:
    """Wait for a random amount of time
    
    Args:
        min_time (float): Minimum wait time in seconds
        max_time (float): Maximum wait time in seconds
    """
    time.sleep(random.uniform(min_time, max_time))


def get_random_user_agent() -> str:
    """Get a random user agent from the configuration
    
    Returns:
        str: Random user agent string
    """
    config = load_accounts_config()
    user_agents = config.get("user_agents", [])
    
    if not user_agents:
        # Default user agent if none configured
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    return random.choice(user_agents)


def get_proxy_settings() -> Optional[Dict]:
    """Get proxy settings from the configuration
    
    Returns:
        Optional[Dict]: Proxy settings or None if disabled
    """
    config = load_accounts_config()
    proxy_settings = config.get("proxy_settings", {})
    
    if not proxy_settings.get("enabled", False):
        return None
    
    proxies = proxy_settings.get("proxies", [])
    if not proxies:
        return None
    
    # Select a random proxy
    proxy = random.choice(proxies)
    
    # Resolve environment variables
    for key in proxy:
        proxy[key] = resolve_env_vars(proxy[key])
    
    return proxy


def get_stealth_settings() -> Dict:
    """Get stealth settings from the configuration
    
    Returns:
        Dict: Stealth settings
    """
    config = load_accounts_config()
    return config.get("stealth_settings", {})


def get_account_config(account_name: str) -> Dict:
    """Get account configuration
    
    Args:
        account_name (str): Account name
    
    Returns:
        Dict: Account configuration
    """
    config = load_accounts_config()
    accounts = config.get("accounts", {})
    
    if account_name not in accounts:
        logger.error(f"Account {account_name} not found in configuration")
        raise ValueError(f"Account {account_name} not found in configuration")
    
    account_config = accounts[account_name]
    
    # Resolve environment variables
    for key in account_config:
        if isinstance(account_config[key], str):
            account_config[key] = resolve_env_vars(account_config[key])
    
    return account_config


def setup_chrome_driver(headless: bool = False) -> webdriver.Chrome:
    """Set up Chrome WebDriver with stealth settings
    
    Args:
        headless (bool): Whether to run in headless mode
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver
    """
    options = Options()
    
    # Set user agent
    options.add_argument(f"user-agent={get_random_user_agent()}")
    
    # Set window size
    options.add_argument("--window-size=1920,1080")
    
    # Disable automation flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Set headless mode if requested
    if headless:
        options.add_argument("--headless")
    
    # Add proxy if enabled
    proxy = get_proxy_settings()
    if proxy:
        proxy_string = f"{proxy['host']}:{proxy['port']}"
        if proxy.get("username") and proxy.get("password"):
            auth = f"{proxy['username']}:{proxy['password']}"
            options.add_argument(f"--proxy-server={proxy_string}")
            # Add proxy auth extension (simplified)
            # In a real implementation, you would create a proxy auth extension
        else:
            options.add_argument(f"--proxy-server={proxy_string}")
    
    # Create driver
    driver = webdriver.Chrome(options=options)
    
    # Execute CDP commands to make detection harder
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
        Object.defineProperty(navigator, 'plugins', {get: function() { return [1, 2, 3, 4, 5]; }})
        window.chrome = { runtime: {} }
        """
    })
    
    return driver


def human_like_type(element, text: str, min_delay: float = 0.05, max_delay: float = 0.2) -> None:
    """Type text into an element with human-like delays
    
    Args:
        element: WebElement to type into
        text (str): Text to type
        min_delay (float): Minimum delay between keystrokes
        max_delay (float): Maximum delay between keystrokes
    """
    # Clear the field first
    element.clear()
    random_delay(0.5, 1.0)
    
    # Type each character with random delay
    for char in text:
        element.send_keys(char)
        random_delay(min_delay, max_delay)


def human_like_click(driver, element) -> None:
    """Click an element with human-like behavior
    
    Args:
        driver: WebDriver instance
        element: WebElement to click
    """
    # Move to element with natural curve
    actions = ActionChains(driver)
    
    # Get stealth settings
    stealth_settings = get_stealth_settings()
    mouse_settings = stealth_settings.get("mouse_movement", {})
    natural_curve = mouse_settings.get("natural_curve", True)
    
    if natural_curve:
        # Create a natural curve by moving to intermediate points
        viewport_width = driver.execute_script("return window.innerWidth")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Get current mouse position (approximation)
        current_x = viewport_width // 2
        current_y = viewport_height // 2
        
        # Get element position
        element_x = element.location["x"] + (element.size["width"] // 2)
        element_y = element.location["y"] + (element.size["height"] // 2)
        
        # Create intermediate points for a curve
        points = []
        num_points = random.randint(3, 6)
        
        for i in range(num_points):
            # Progress along the path (0 to 1)
            t = (i + 1) / (num_points + 1)
            
            # Add some randomness to the curve
            offset_x = random.randint(-100, 100)
            offset_y = random.randint(-50, 50)
            
            # Calculate point on curve
            point_x = current_x + (element_x - current_x) * t + offset_x * (1 - t) * t
            point_y = current_y + (element_y - current_y) * t + offset_y * (1 - t) * t
            
            # Ensure point is within viewport
            point_x = max(0, min(viewport_width, point_x))
            point_y = max(0, min(viewport_height, point_y))
            
            points.append((point_x, point_y))
        
        # Move through intermediate points
        for point_x, point_y in points:
            actions.move_by_offset(point_x - current_x, point_y - current_y)
            current_x, current_y = point_x, point_y
            random_delay(0.05, 0.1)
        
        # Final move to element
        actions.move_to_element(element)
    else:
        # Simple move to element
        actions.move_to_element(element)
    
    # Perform the move
    actions.perform()
    random_delay(0.2, 0.5)
    
    # Click the element
    try:
        element.click()
    except (ElementClickInterceptedException, StaleElementReferenceException):
        # If direct click fails, try JavaScript click
        driver.execute_script("arguments[0].click();", element)


def wait_for_page_load(driver, timeout: float = 10.0) -> None:
    """Wait for page to load completely
    
    Args:
        driver: WebDriver instance
        timeout (float): Maximum time to wait in seconds
    """
    # Wait for document ready state
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    
    # Wait for jQuery (if present)
    jquery_ready = """
    return (typeof jQuery === 'undefined') || jQuery.active === 0;
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(jquery_ready)
        )
    except TimeoutException:
        # jQuery might not be present, or there might be long-running AJAX
        pass
    
    # Wait for Angular (if present)
    angular_ready = """
    return (typeof angular === 'undefined') || 
           (angular.element(document).injector() === undefined) || 
           (angular.element(document).injector().get('$http').pendingRequests.length === 0);
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(angular_ready)
        )
    except TimeoutException:
        # Angular might not be present
        pass
    
    # Additional random wait to simulate human behavior
    stealth_settings = get_stealth_settings()
    page_load_wait = stealth_settings.get("page_load_wait", {})
    min_time = page_load_wait.get("min_time", 1.0)
    max_time = page_load_wait.get("max_time", 3.0)
    random_delay(min_time, max_time)


def find_element_with_fallback(driver, selectors: List[Dict], timeout: float = 10.0):
    """Find an element using multiple selector strategies with fallback
    
    Args:
        driver: WebDriver instance
        selectors (List[Dict]): List of selector dictionaries with 'by' and 'value' keys
        timeout (float): Maximum time to wait in seconds
    
    Returns:
        WebElement: Found element
    
    Raises:
        NoSuchElementException: If element cannot be found with any selector
    """
    for selector in selectors:
        by = selector["by"]
        value = selector["value"]
        
        try:
            # Wait for element to be present and visible
            element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            continue
    
    # If we get here, none of the selectors worked
    raise NoSuchElementException(f"Could not find element with any of the selectors: {selectors}")


def perform_human_login(account_name: str, headless: bool = False, max_retries: int = MAX_RETRIES) -> webdriver.Chrome:
    """Perform a human-like login to a broker account
    
    Args:
        account_name (str): Account name from configuration
        headless (bool): Whether to run in headless mode
        max_retries (int): Maximum number of retry attempts
    
    Returns:
        webdriver.Chrome: WebDriver instance after successful login
    
    Raises:
        Exception: If login fails after max retries
    """
    # Get account configuration
    account_config = get_account_config(account_name)
    
    # Get stealth settings
    stealth_settings = get_stealth_settings()
    typing_speed = stealth_settings.get("typing_speed", {})
    min_typing_delay = typing_speed.get("min_delay", 0.05)
    max_typing_delay = typing_speed.get("max_delay", 0.2)
    
    # Get selectors
    selectors = account_config.get("selectors", {})
    username_selector = selectors.get("username_field", "username")
    password_selector = selectors.get("password_field", "password")
    login_button_selector = selectors.get("login_button", "login-button")
    
    # Initialize retry counter
    retry_count = 0
    backoff_time = 1.0
    
    while retry_count < max_retries:
        driver = None
        try:
            # Set up Chrome driver
            driver = setup_chrome_driver(headless)
            
            # Navigate to login page
            driver.get(account_config["login_url"])
            wait_for_page_load(driver)
            
            # Find username field with fallback selectors
            username_selectors = [
                {"by": By.ID, "value": username_selector},
                {"by": By.NAME, "value": username_selector},
                {"by": By.CSS_SELECTOR, "value": f"input[id*='{username_selector}'], input[name*='{username_selector}']"}
            ]
            username_field = find_element_with_fallback(driver, username_selectors)
            
            # Type username
            human_like_type(username_field, account_config["username"], min_typing_delay, max_typing_delay)
            random_delay(0.5, 1.5)
            
            # Find password field with fallback selectors
            password_selectors = [
                {"by": By.ID, "value": password_selector},
                {"by": By.NAME, "value": password_selector},
                {"by": By.CSS_SELECTOR, "value": f"input[type='password'], input[id*='{password_selector}'], input[name*='{password_selector}']"}
            ]
            password_field = find_element_with_fallback(driver, password_selectors)
            
            # Type password
            human_like_type(password_field, account_config["password"], min_typing_delay, max_typing_delay)
            random_delay(0.5, 1.5)
            
            # Find login button with fallback selectors
            login_button_selectors = [
                {"by": By.ID, "value": login_button_selector},
                {"by": By.NAME, "value": login_button_selector},
                {"by": By.CSS_SELECTOR, "value": f"button[type='submit'], input[type='submit'], button[id*='{login_button_selector}'], button[name*='{login_button_selector}']"}
            ]
            login_button = find_element_with_fallback(driver, login_button_selectors)
            
            # Click login button
            human_like_click(driver, login_button)
            
            # Wait for login to complete
            wait_for_page_load(driver)
            
            # Check if login was successful (this will depend on the broker's site)
            # For example, check for an element that only appears after successful login
            success_indicator = account_config.get("success_indicator", {})
            if success_indicator:
                indicator_selectors = [
                    {"by": By.CSS_SELECTOR, "value": success_indicator.get("css_selector", "")},
                    {"by": By.XPATH, "value": success_indicator.get("xpath", "")}
                ]
                
                try:
                    # Filter out empty selectors
                    valid_selectors = [s for s in indicator_selectors if s["value"]]
                    if valid_selectors:
                        find_element_with_fallback(driver, valid_selectors)
                    else:
                        # If no success indicators configured, assume success
                        pass
                except NoSuchElementException:
                    raise Exception("Login failed: Success indicator not found")
            
            logger.info(f"Successfully logged in to account {account_name}")
            return driver
        
        except Exception as e:
            retry_count += 1
            logger.warning(f"Login attempt {retry_count} failed: {str(e)}")
            
            if driver:
                driver.quit()
            
            if retry_count >= max_retries:
                logger.error(f"Login failed after {max_retries} attempts")
                raise Exception(f"Login failed after {max_retries} attempts: {str(e)}")
            
            # Exponential backoff
            backoff_time *= BACKOFF_FACTOR
            time.sleep(backoff_time)


def execute_trade(driver, signal: Dict, risk_level: float = 1.0) -> bool:
    """Execute a trade with human-like behavior
    
    Args:
        driver: WebDriver instance
        signal (Dict): Trade signal with details
        risk_level (float): Risk level multiplier (0.0 to 1.0)
    
    Returns:
        bool: True if trade was executed successfully, False otherwise
    """
    try:
        # Extract signal details
        symbol = signal.get("symbol", "")
        direction = signal.get("direction", "")
        lot_size = signal.get("lot_size", 0.01) * risk_level
        take_profit = signal.get("take_profit")
        stop_loss = signal.get("stop_loss")
        
        # Log trade details
        logger.info(f"Executing trade: {symbol} {direction} {lot_size} lots")
        
        # Navigate to trading page (this will depend on the broker's site)
        # For example:
        # driver.get("https://example.com/trading")
        # wait_for_page_load(driver)
        
        # The following is a generic implementation that would need to be
        # customized for each specific broker platform
        
        # Find and click on symbol search
        symbol_search_selectors = [
            {"by": By.CSS_SELECTOR, "value": "input[placeholder*='Search'], input[placeholder*='symbol']"},
            {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Search') or contains(@placeholder, 'symbol')]"},
        ]
        
        try:
            symbol_search = find_element_with_fallback(driver, symbol_search_selectors)
            human_like_click(driver, symbol_search)
            human_like_type(symbol_search, symbol)
            random_delay(0.5, 1.0)
            
            # Press Enter to select symbol
            symbol_search.send_keys(Keys.ENTER)
            random_delay(0.5, 1.0)
        except NoSuchElementException:
            logger.warning("Symbol search not found, trying alternative approach")
            # Alternative approach would be implemented here
        
        # Select buy/sell based on direction
        if direction.lower() in ["buy", "long"]:
            buy_button_selectors = [
                {"by": By.CSS_SELECTOR, "value": "button[data-action='buy'], .buy-button, button:contains('Buy')"},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Buy') or contains(@class, 'buy')]"},
            ]
            buy_button = find_element_with_fallback(driver, buy_button_selectors)
            human_like_click(driver, buy_button)
        elif direction.lower() in ["sell", "short"]:
            sell_button_selectors = [
                {"by": By.CSS_SELECTOR, "value": "button[data-action='sell'], .sell-button, button:contains('Sell')"},
                {"by": By.XPATH, "value": "//button[contains(text(), 'Sell') or contains(@class, 'sell')]"},
            ]
            sell_button = find_element_with_fallback(driver, sell_button_selectors)
            human_like_click(driver, sell_button)
        else:
            raise ValueError(f"Unknown direction: {direction}")
        
        random_delay(0.5, 1.0)
        
        # Set lot size
        lot_size_selectors = [
            {"by": By.CSS_SELECTOR, "value": "input[name='volume'], input[placeholder*='volume'], input[placeholder*='lot']"},
            {"by": By.XPATH, "value": "//input[contains(@placeholder, 'volume') or contains(@placeholder, 'lot')]"},
        ]
        lot_size_input = find_element_with_fallback(driver, lot_size_selectors)
        human_like_type(lot_size_input, str(lot_size))
        random_delay(0.5, 1.0)
        
        # Set take profit if provided
        if take_profit is not None:
            tp_selectors = [
                {"by": By.CSS_SELECTOR, "value": "input[name='takeProfit'], input[placeholder*='Take Profit']"},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Take Profit') or contains(@name, 'takeProfit')]"},
            ]
            try:
                tp_input = find_element_with_fallback(driver, tp_selectors)
                human_like_type(tp_input, str(take_profit))
                random_delay(0.5, 1.0)
            except NoSuchElementException:
                logger.warning("Take profit field not found")
        
        # Set stop loss if provided
        if stop_loss is not None:
            sl_selectors = [
                {"by": By.CSS_SELECTOR, "value": "input[name='stopLoss'], input[placeholder*='Stop Loss']"},
                {"by": By.XPATH, "value": "//input[contains(@placeholder, 'Stop Loss') or contains(@name, 'stopLoss')]"},
            ]
            try:
                sl_input = find_element_with_fallback(driver, sl_selectors)
                human_like_type(sl_input, str(stop_loss))
                random_delay(0.5, 1.0)
            except NoSuchElementException:
                logger.warning("Stop loss field not found")
        
        # Submit order
        submit_selectors = [
            {"by": By.CSS_SELECTOR, "value": "button[type='submit'], button.submit-button, button:contains('Submit'), button:contains('Place Order')"},
            {"by": By.XPATH, "value": "//button[contains(text(), 'Submit') or contains(text(), 'Place Order') or contains(@class, 'submit')]"},
        ]
        submit_button = find_element_with_fallback(driver, submit_selectors)
        human_like_click(driver, submit_button)
        
        # Wait for confirmation
        wait_for_page_load(driver)
        
        # Check for success confirmation
        confirmation_selectors = [
            {"by": By.CSS_SELECTOR, "value": ".success-message, .confirmation-message"},
            {"by": By.XPATH, "value": "//div[contains(@class, 'success') or contains(@class, 'confirmation')]"},
        ]
        
        try:
            find_element_with_fallback(driver, confirmation_selectors, timeout=5.0)
            logger.info(f"Trade executed successfully: {symbol} {direction} {lot_size} lots")
            return True
        except NoSuchElementException:
            # Check for error message
            error_selectors = [
                {"by": By.CSS_SELECTOR, "value": ".error-message, .alert-danger"},
                {"by": By.XPATH, "value": "//div[contains(@class, 'error') or contains(@class, 'alert-danger')]"},
            ]
            
            try:
                error_element = find_element_with_fallback(driver, error_selectors, timeout=2.0)
                error_message = error_element.text
                logger.error(f"Trade execution failed: {error_message}")
            except NoSuchElementException:
                logger.warning("Could not find confirmation or error message")
            
            return False
    
    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        return False


# For testing
if __name__ == "__main__":
    try:
        # Test login
        print("Testing human-like login...")
        driver = perform_human_login("main_funded_01", headless=False)
        
        # Test trade execution
        print("Testing trade execution...")
        test_signal = {
            "symbol": "EURUSD",
            "direction": "buy",
            "lot_size": 0.01,
            "take_profit": 1.1000,
            "stop_loss": 1.0900
        }
        
        success = execute_trade(driver, test_signal, risk_level=0.5)
        print(f"Trade execution {'successful' if success else 'failed'}")
        
        # Clean up
        driver.quit()
    
    except Exception as e:
        print(f"Test failed: {str(e)}")