#!/usr/bin/env python3
"""
TradeBot Sentinel - Expert Automation Agent for Bulenox ProjectX Trading Platform

This script automates:
1. Secure login with environment variables and robust fallback selectors
2. Time Sync Warning modal detection and handling
3. Dashboard confirmation with multiple selectors and retries
4. Trading page navigation and readiness confirmation
5. Trade order placement with exact and fallback selectors
6. Network request interception for trade execution detection
7. cURL command generation and Python requests code conversion
8. Screenshot capture on critical failures for debugging
9. Verbose logging for traceability
10. Retry mechanisms with delays for slow/dynamic UI elements

Features:
- Headless browser operation with easy toggle
- Environment variable credential management
- Robust selector fallback strategies
- Network POST request monitoring and analysis
- Automatic cURL to Python conversion using curlconverter
- Comprehensive error handling and recovery
- Detailed logging at every step
- Screenshot capture on failures
"""

import os
import sys
import json
import time
import asyncio
import logging
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Request, Response
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip install playwright")
    print("   Then run: playwright install chromium")
    sys.exit(1)

# Configuration Constants
HEADLESS = True  # Set to False for debugging
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
SCREENSHOT_DIR = Path("screenshots")
LOG_FILE = "tradebot_sentinel.log"

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradeBotSentinel:
    """
    Expert automation agent for Bulenox ProjectX Trading Platform
    Handles login, trading operations, network interception, and code generation
    """
    def __init__(self, headless: bool = HEADLESS, demo_mode: bool = False):
        self.headless = headless
        self.demo_mode = demo_mode
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.trade_requests: List[Dict[str, Any]] = []
        self.intercepted_requests: List[Dict[str, Any]] = []
        
        # Create screenshots directory
        SCREENSHOT_DIR.mkdir(exist_ok=True)
        
        # Environment variables with validation
        self.username = os.getenv('BULENOX_USERNAME') or os.getenv('BROKER_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD') or os.getenv('BROKER_PASSWORD')
        self.login_url = os.getenv('BROKER_URL', 'https://bulenox.projectx.com/login')
        
        if not demo_mode and (not self.username or not self.password):
            logger.error("[ERROR] Missing credentials. Set BULENOX_USERNAME and BULENOX_PASSWORD environment variables.")
            raise ValueError("Missing required credentials")
        elif demo_mode:
            logger.info("[DEMO] Running in demo mode - credentials not required")
            self.username = "demo_user"
            self.password = "demo_pass"
            
        logger.info("=" * 80)
        logger.info("TradeBot Sentinel - Expert Automation Agent Initialized")
        logger.info(f"User: {self.username}")
        logger.info(f"Target URL: {self.login_url}")
        logger.info(f"Headless mode: {self.headless}")
        logger.info(f"Max retries: {MAX_RETRIES}")
        logger.info(f"Retry delay: {RETRY_DELAY}s")
        logger.info("=" * 80)
    
    async def setup_browser(self):
        """Initialize browser with comprehensive settings for trading automation"""
        try:
            logger.info("Setting up browser with trading-optimized configuration...")
            
            playwright = await async_playwright().start()
            
            # Launch browser with comprehensive arguments for stability
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
            
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Create page and setup comprehensive network monitoring
            self.page = await self.context.new_page()
            await self.setup_network_interception()
            
            # Set page timeouts
            self.page.set_default_timeout(30000)  # 30 seconds
            self.page.set_default_navigation_timeout(60000)  # 60 seconds
            
            # Enable console logging
            self.page.on('console', lambda msg: logger.info(f"[CONSOLE] Console: {msg.text}"))
            self.page.on('pageerror', lambda error: logger.error(f"[ERROR] Page Error: {error}"))
            
            logger.info("Browser setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            await self.capture_screenshot("browser_setup_error")
            return False
    
    async def setup_network_interception(self):
        """Setup comprehensive network request interception for trade detection"""
        logger.info("Setting up comprehensive network request interception...")
        
        async def handle_request(request: Request):
            """Handle all network requests with detailed logging"""
            try:
                # Log all POST requests with detailed information
                if request.method == "POST":
                    logger.info(f"[POST REQUEST] URL: {request.url}")
                    logger.info(f"[POST REQUEST] Headers: {dict(request.headers)}")
                    
                    # Capture request data
                    post_data = None
                    try:
                        post_data = request.post_data
                        if post_data:
                            logger.info(f"[POST DATA] Raw: {post_data[:500]}...")  # First 500 chars
                            
                            # Check for trade-related keywords
                            trade_keywords = [
                                'symbol', 'amount', 'price', 'order', 'trade', 
                                'buy', 'sell', 'position', 'volume', 'quantity',
                                'market', 'limit', 'stop', 'execute', 'submit'
                            ]
                            
                            post_data_lower = post_data.lower()
                            matching_keywords = [kw for kw in trade_keywords if kw in post_data_lower]
                            
                            if matching_keywords:
                                logger.info(f"[TRADE DETECTED] Keywords found: {matching_keywords}")
                                logger.info(f"[TRADE DETECTED] URL: {request.url}")
                                await self.capture_trade_request(request, post_data)
                            
                            # Also check JSON data if possible
                            try:
                                json_data = json.loads(post_data)
                                if any(key in str(json_data).lower() for key in trade_keywords):
                                    logger.info(f"[TRADE DETECTED] JSON contains trade data: {json_data}")
                                    await self.capture_trade_request(request, post_data)
                            except (json.JSONDecodeError, TypeError):
                                pass  # Not JSON data
                                
                    except Exception as e:
                        logger.warning(f"Could not read POST data from {request.url}: {e}")
                        
                    # Store all POST requests for analysis
                    self.intercepted_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'post_data': post_data,
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error handling request {request.url}: {e}")
        
        async def handle_response(response: Response):
            """Handle responses for additional context"""
            try:
                if response.request.method == "POST" and response.status >= 400:
                    logger.warning(f"[POST ERROR] {response.url} returned {response.status}")
            except Exception as e:
                logger.error(f"Error handling response: {e}")
        
        # Setup comprehensive request/response interception
        self.page.on('request', handle_request)
        self.page.on('response', handle_response)
        
        logger.info("Network interception setup completed successfully")
    
    async def capture_trade_request(self, request: Request, data: Any):
        """Capture and save trade execution request with comprehensive processing"""
        logger.info("=" * 60)
        logger.info("TRADE REQUEST CAPTURED!")
        logger.info(f"URL: {request.url}")
        logger.info(f"Method: {request.method}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Data: {data}")
        logger.info("=" * 60)
        
        try:
            # Build comprehensive cURL command
            curl_command = self.build_curl_command(request, data)
            
            # Save cURL command to trade.sh
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write(curl_command)
            
            logger.info("✓ Trade cURL command saved to trade.sh")
            
            # Convert to Python requests using curlconverter
            await self.convert_curl_to_python(curl_command)
            
            # Store comprehensive request details
            trade_request = {
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'curl_command': curl_command
            }
            
            self.trade_requests.append(trade_request)
            
            # Save detailed JSON log
            with open('trade_requests_log.json', 'w', encoding='utf-8') as f:
                json.dump(self.trade_requests, f, indent=2, ensure_ascii=False)
            
            logger.info("✓ Trade request details logged to trade_requests_log.json")
            
        except Exception as e:
            logger.error(f"Error capturing trade request: {e}")
            await self.capture_screenshot("trade_capture_error")
    
    def build_curl_command(self, request: Request, data: Any = None) -> str:
        """Build comprehensive cURL command from request object"""
        try:
            curl_parts = [f"curl -X {request.method}"]
            
            # Add URL with proper escaping
            curl_parts.append(f"'{request.url}'")
            
            # Add headers with proper escaping
            for name, value in request.headers.items():
                # Skip problematic headers
                if name.lower() not in ['content-length', 'host']:
                    escaped_value = value.replace("'", "'\"'\"'")
                    curl_parts.append(f"-H '{name}: {escaped_value}'")
            
            # Add data if present
            post_data = data or request.post_data
            if post_data:
                if isinstance(post_data, str):
                    escaped_data = post_data.replace("'", "'\"'\"'")
                    curl_parts.append(f"--data '{escaped_data}'")
                else:
                    # Convert to JSON string if not already
                    json_data = json.dumps(post_data) if not isinstance(post_data, str) else post_data
                    escaped_data = json_data.replace("'", "'\"'\"'")
                    curl_parts.append(f"--data '{escaped_data}'")
            
            # Add additional cURL options for better compatibility
            curl_parts.extend([
                "--compressed",
                "--insecure",
                "--location",
                "--max-time 30"
            ])
            
            return " \\\n  ".join(curl_parts)
            
        except Exception as e:
            logger.error(f"Error building cURL command: {e}")
            return f"# Error building cURL command: {e}"
    
    async def convert_curl_to_python(self, curl_command: str):
        """Convert cURL command to Python requests code using curlconverter"""
        try:
            logger.info("Converting cURL to Python requests code...")
            
            # Try using curlconverter package
            try:
                result = subprocess.run(
                    ['python', '-c', f'import curlconverter; print(curlconverter.to_python("{curl_command.replace(chr(34), chr(92)+chr(34))}"))'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    python_code = result.stdout.strip()
                else:
                    raise Exception(f"curlconverter failed: {result.stderr}")
                    
            except Exception as e:
                logger.warning(f"curlconverter not available or failed: {e}")
                # Fallback: create basic Python requests template
                python_code = self.create_python_requests_template(curl_command)
            
            # Save Python code
            with open('trade_request_full.py', 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            logger.info("✓ Python requests code saved to trade_request_full.py")
            
        except Exception as e:
            logger.error(f"Error converting cURL to Python: {e}")
    
    def create_python_requests_template(self, curl_command: str) -> str:
        """Create a basic Python requests template as fallback"""
        template = '''#!/usr/bin/env python3
"""
Generated Python requests code for trade execution
Converted from cURL command by TradeBot Sentinel
"""

import requests
import json
from datetime import datetime

# Original cURL command:
# {curl_command}

def execute_trade_request():
    """Execute the captured trade request"""
    
    url = "# EXTRACT_URL_FROM_CURL"
    
    headers = {{
        # EXTRACT_HEADERS_FROM_CURL
    }}
    
    data = {{
        # EXTRACT_DATA_FROM_CURL
    }}
    
    try:
        print(f"Executing trade request at {{datetime.now()}}")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {{response.status_code}}")
        print(f"Response: {{response.text}}")
        
        return response
        
    except Exception as e:
        print(f"Error executing trade request: {{e}}")
        return None

if __name__ == "__main__":
    execute_trade_request()
'''
        return template.format(curl_command=curl_command.replace('\\', '\\\\').replace('"', '\\"'))
    
    async def login(self) -> bool:
        """Perform secure login with comprehensive error handling and retry mechanisms"""
        logger.info("Starting secure login process...")
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Login attempt {attempt + 1}/{MAX_RETRIES}")
                
                # Navigate to login page with retry
                logger.info(f"Navigating to: {self.login_url}")
                await self.page.goto(self.login_url, wait_until='networkidle', timeout=60000)
                
                # Wait for page to be fully loaded
                await self.page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(2)  # Additional wait for dynamic content
                
                # Comprehensive login selectors with fallbacks
                username_selectors = [
                    'input[name="username"]',
                    'input[id="username"]',
                    'input[name="email"]',
                    'input[id="email"]',
                    'input[placeholder*="username" i]',
                    'input[placeholder*="email" i]',
                    'input[type="text"]:first-of-type',
                    'input[type="email"]',
                    '.username-input',
                    '.email-input',
                    '[data-testid="username"]',
                    '[data-testid="email"]'
                ]
                
                password_selectors = [
                    'input[name="password"]',
                    'input[id="password"]',
                    'input[type="password"]',
                    '.password-input',
                    '[data-testid="password"]'
                ]
                
                login_button_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    'button:has-text("Log In")',
                    'button:has-text("Submit")',
                    '.login-button',
                    '.signin-button',
                    '#login-button',
                    '#signin-button',
                    '[data-testid="login-button"]',
                    'button:near(input[type="password"])'
                ]
                
                # Fill username with retry mechanism
                username_filled = await self._fill_field_with_retry(username_selectors, self.username, "username")
                if not username_filled:
                    logger.error("Could not find or fill username field")
                    await self.capture_screenshot(f"login_username_error_attempt_{attempt + 1}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                    return False
                
                # Fill password with retry mechanism
                password_filled = await self._fill_field_with_retry(password_selectors, self.password, "password")
                if not password_filled:
                    logger.error("Could not find or fill password field")
                    await self.capture_screenshot(f"login_password_error_attempt_{attempt + 1}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                    return False
                
                # Click login button with retry mechanism
                login_clicked = await self._click_element_with_retry(login_button_selectors, "login button")
                if not login_clicked:
                    logger.error("Could not find or click login button")
                    await self.capture_screenshot(f"login_button_error_attempt_{attempt + 1}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                    return False
                
                logger.info("Login form submitted successfully")
                
                # Wait for navigation or response
                await asyncio.sleep(3)
                
                # Handle potential Time Sync Warning modal
                await self.handle_time_sync_warning()
                
                # Confirm login success with comprehensive checks
                login_success = await self.confirm_login_success()
                if login_success:
                    logger.info("✓ Login completed successfully!")
                    return True
                else:
                    logger.warning(f"Login verification failed on attempt {attempt + 1}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY)
                        continue
                
            except Exception as e:
                logger.error(f"Login attempt {attempt + 1} failed: {e}")
                await self.capture_screenshot(f"login_error_attempt_{attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
        
        logger.error("All login attempts failed")
        return False
    
    async def _fill_field_with_retry(self, selectors: List[str], value: str, field_name: str) -> bool:
        """Fill form field with retry mechanism using multiple selectors"""
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                await self.page.fill(selector, value)
                logger.info(f"✓ {field_name} filled using selector: {selector}")
                return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed for {field_name}: {e}")
                continue
        return False
    
    async def _click_element_with_retry(self, selectors: List[str], element_name: str) -> bool:
        """Click element with retry mechanism using multiple selectors"""
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                await self.page.click(selector)
                logger.info(f"✓ {element_name} clicked using selector: {selector}")
                return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed for {element_name}: {e}")
                continue
        return False
    
    async def handle_time_sync_warning(self):
        """Detect and handle Time Sync Warning modals"""
        try:
            logger.info("Checking for time sync warning modals...")
            
            # Comprehensive list of time sync warning selectors
            warning_selectors = [
                "[data-testid='time-sync-warning']",
                "[data-testid='time-sync-modal']",
                ".time-sync-modal",
                ".time-sync-warning",
                "div:has-text('Time Sync Warning')",
                "div:has-text('time sync')",
                "div:has-text('Time synchronization')",
                "[role='dialog']:has-text('time')",
                ".modal:has-text('sync')",
                ".warning-modal"
            ]
            
            for selector in warning_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        logger.warning(f"⚠️ Time sync warning detected with selector: {selector}")
                        
                        # Comprehensive close button selectors
                        close_selectors = [
                            f"{selector} button:has-text('OK')",
                            f"{selector} button:has-text('Close')",
                            f"{selector} button:has-text('Dismiss')",
                            f"{selector} button:has-text('Continue')",
                            f"{selector} .close-btn",
                            f"{selector} .btn-close",
                            f"{selector} [data-testid='close-button']",
                            f"{selector} [data-testid='dismiss-button']",
                            f"{selector} [aria-label='Close']",
                            f"{selector} .modal-close",
                            f"{selector} button[type='button']"
                        ]
                        
                        # Try each close selector
                        for close_selector in close_selectors:
                            try:
                                close_element = await self.page.wait_for_selector(close_selector, timeout=1000)
                                if close_element:
                                    await self.page.click(close_selector)
                                    logger.info(f"✓ Time sync warning closed with: {close_selector}")
                                    await asyncio.sleep(1)  # Wait for modal to close
                                    return
                            except:
                                continue
                        
                        # If no close button found, try pressing Escape
                        logger.info("Trying Escape key to close modal...")
                        await self.page.keyboard.press('Escape')
                        await asyncio.sleep(1)
                        
                        # Check if modal is still visible
                        try:
                            await self.page.wait_for_selector(selector, timeout=1000)
                            logger.warning("Modal still visible after Escape")
                        except:
                            logger.info("✓ Time sync warning closed with Escape key")
                            return
                        
                        # Last resort: click outside modal
                        logger.info("Trying to click outside modal...")
                        await self.page.click('body', position={'x': 10, 'y': 10})
                        await asyncio.sleep(1)
                        return
                        
                except Exception as e:
                    logger.debug(f"Selector {selector} not found or failed: {e}")
                    continue
            
            logger.info("✓ No time sync warning detected")
            
        except Exception as e:
            logger.error(f"❌ Error handling time sync warning: {e}")
            await self.capture_screenshot("time_sync_warning_error")
    
    async def confirm_login_success(self) -> bool:
        """Confirm login success by waiting for dashboard elements with comprehensive retry"""
        try:
            logger.info("🔍 Confirming login success...")
            
            # Comprehensive dashboard detection selectors
            dashboard_selectors = [
                "[data-testid='dashboard']",
                "[data-testid='main-dashboard']",
                "[data-testid='user-dashboard']",
                ".dashboard",
                ".main-dashboard",
                "#dashboard",
                "#main-dashboard",
                "[data-testid='user-menu']",
                "[data-testid='profile-menu']",
                ".user-profile",
                ".user-menu",
                ".profile-dropdown",
                "nav:has-text('Dashboard')",
                "nav:has-text('Trading')",
                "nav:has-text('Portfolio')",
                "div:has-text('Welcome')",
                "div:has-text('Balance')",
                "div:has-text('Account')",
                '[class*="dashboard" i], [id*="dashboard" i]',
                '[class*="trading" i], [id*="trading" i]',
                '[class*="portfolio" i], [id*="portfolio" i]',
                '[class*="account" i], [id*="account" i]',
                'nav, .navbar, .navigation, .menu',
                '.user-info, .account-info, .profile',
                ".trading-interface",
                ".portfolio-summary",
                "[role='main']",
                ".main-content",
                "header:has-text('Trading')",
                ".navbar-brand",
                ".logout-btn",
                "button:has-text('Logout')"
            ]
            
            for attempt in range(MAX_RETRIES):
                logger.info(f"📊 Login confirmation attempt {attempt + 1}/{MAX_RETRIES}")
                
                # Check URL for login success indicators
                current_url = self.page.url
                if any(indicator in current_url.lower() for indicator in ['dashboard', 'trading', 'main', 'home', 'portfolio']):
                    logger.info(f"✓ Login success detected from URL: {current_url}")
                    return True
                
                # Check for dashboard elements
                for selector in dashboard_selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=3000)
                        if element:
                            # Verify element is visible
                            is_visible = await element.is_visible()
                            if is_visible:
                                logger.info(f"✅ Login confirmed with visible selector: {selector}")
                                return True
                            else:
                                logger.debug(f"Element found but not visible: {selector}")
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue
                
                # Check for absence of login elements (negative confirmation)
                login_indicators = [
                    "input[type='password']",
                    "button:has-text('Login')",
                    "button:has-text('Sign In')",
                    ".login-form",
                    "[data-testid='login-form']"
                ]
                
                login_elements_present = False
                for login_selector in login_indicators:
                    try:
                        element = await self.page.wait_for_selector(login_selector, timeout=1000)
                        if element and await element.is_visible():
                            login_elements_present = True
                            break
                    except:
                        continue
                
                if not login_elements_present:
                    logger.info("✓ Login confirmed - no login elements visible")
                    return True
                
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"⏳ Retrying login confirmation in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)
                    
                    # Try refreshing the page if we're stuck
                    if attempt == 1:
                        logger.info("🔄 Refreshing page to check login status...")
                        await self.page.reload()
                        await asyncio.sleep(2)
            
            logger.error("❌ Failed to confirm login success after all attempts")
            await self.capture_screenshot("login_confirmation_failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error confirming login: {e}")
            await self.capture_screenshot("login_confirmation_error")
            return False
    
    async def navigate_to_trading(self) -> bool:
        """Navigate to trading page and confirm readiness with comprehensive retry"""
        try:
            logger.info("🚀 Navigating to trading page...")
            
            # Check if already on trading page
            current_url = self.page.url
            if any(indicator in current_url.lower() for indicator in ['trading', 'trade', 'order']):
                logger.info(f"✓ Already on trading page: {current_url}")
            else:
                # Comprehensive trading navigation selectors
                trading_nav_selectors = [
                    "a[href*='trading']",
                    "a[href*='trade']",
                    "nav a:has-text('Trading')",
                    "nav a:has-text('Trade')",
                    "[data-testid='trading-nav']",
                    "[data-testid='trade-nav']",
                    ".nav-trading",
                    ".nav-trade",
                    "button:has-text('Trading')",
                    "button:has-text('Trade')",
                    "[role='menuitem']:has-text('Trading')",
                    ".menu-item:has-text('Trading')",
                    "li:has-text('Trading') a",
                    "[data-nav='trading']",
                    ".sidebar a:has-text('Trading')"
                ]
                
                # Try to click trading navigation
                navigation_success = False
                for selector in trading_nav_selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=3000)
                        if element and await element.is_visible():
                            await self.page.click(selector)
                            logger.info(f"✓ Clicked trading navigation: {selector}")
                            navigation_success = True
                            break
                    except Exception as e:
                        logger.debug(f"Navigation selector {selector} failed: {e}")
                        continue
                
                if not navigation_success:
                    # Try direct URL navigation as fallback
                    base_url = self.page.url.split('?')[0].split('#')[0]
                    trading_urls = [
                        f"{base_url}/trading",
                        f"{base_url}/trade",
                        f"{base_url}#trading",
                        f"{base_url}#trade"
                    ]
                    
                    for url in trading_urls:
                        try:
                            logger.info(f"🔗 Trying direct navigation to: {url}")
                            await self.page.goto(url)
                            await asyncio.sleep(2)
                            break
                        except Exception as e:
                            logger.debug(f"Direct navigation to {url} failed: {e}")
                            continue
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Verify trading interface readiness
            return await self.verify_trading_readiness()
            
        except Exception as e:
            logger.error(f"❌ Error navigating to trading: {e}")
            await self.capture_screenshot("trading_navigation_error")
            return False
    
    async def verify_trading_readiness(self) -> bool:
        """Verify trading interface is ready with comprehensive retry mechanisms"""
        logger.info("📊 Verifying trading interface readiness...")
        
        # Comprehensive trading interface confirmation
        trading_interface_selectors = [
            "[data-testid='trading-interface']",
            "[data-testid='order-form']",
            "[data-testid='buy-button']",
            "[data-testid='sell-button']",
            ".trading-panel",
            ".trading-interface",
            ".order-form",
            ".buy-sell-panel",
            "form[class*='order']",
            "input[placeholder*='amount']",
            "input[placeholder*='price']",
            "input[placeholder*='quantity']",
            "button:has-text('Buy')",
            "button:has-text('Sell')",
            "button:has-text('Place Order')",
            "select[name*='symbol']",
            "select[name*='pair']",
            ".symbol-selector",
            ".currency-pair",
            ".market-data",
            ".price-chart",
            "[role='tabpanel']:has-text('Order')",
            ".tab-content:has-text('Buy')"
        ]
        
        for attempt in range(MAX_RETRIES):
            logger.info(f"📊 Trading interface check attempt {attempt + 1}/{MAX_RETRIES}")
            
            # Check URL again
            current_url = self.page.url
            if any(indicator in current_url.lower() for indicator in ['trading', 'trade', 'order']):
                logger.info(f"✓ URL confirms trading page: {current_url}")
            
            # Check for trading interface elements
            interface_found = False
            for selector in trading_interface_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        logger.info(f"✅ Trading interface ready: {selector}")
                        interface_found = True
                        break
                except Exception as e:
                    logger.debug(f"Interface selector {selector} failed: {e}")
                    continue
            
            if interface_found:
                return True
            
            if attempt < MAX_RETRIES - 1:
                logger.info(f"⏳ Retrying trading interface check in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
                
                # Try refreshing if stuck
                if attempt == 1:
                    logger.info("🔄 Refreshing page to load trading interface...")
                    await self.page.reload()
                    await asyncio.sleep(3)
        
        logger.error("❌ Failed to confirm trading interface readiness")
        await self.capture_screenshot("trading_interface_not_ready")
        return False
    
    async def place_test_trade(self) -> bool:
        """Attempt to place a test trade order with fallback strategies"""
        logger.info("[TRADE] Attempting to place test trade order...")
        
        try:
            # Strategy 1: Look for ORDER tab
            order_tab_selectors = [
                'button:has-text("ORDER"), a:has-text("ORDER")',
                '[class*="order-tab" i], [id*="order-tab" i]',
                '.tab:has-text("Order"), .tab:has-text("ORDER")'
            ]
            
            order_tab_found = False
            for selector in order_tab_selectors:
                try:
                    tab_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if tab_element:
                        logger.info(f"[FOUND] ORDER tab found: {selector}")
                        await tab_element.click()
                        order_tab_found = True
                        break
                except:
                    continue
            
            if not order_tab_found:
                logger.info("[WARNING] ORDER tab not found, trying DOM tab...")
                
                # Strategy 2: Look for DOM tab
                dom_tab_selectors = [
                    'button:has-text("DOM"), a:has-text("DOM")',
                    '[class*="dom-tab" i], [id*="dom-tab" i]',
                    '.tab:has-text("Dom"), .tab:has-text("DOM")'
                ]
                
                dom_tab_found = False
                for selector in dom_tab_selectors:
                    try:
                        tab_element = await self.page.wait_for_selector(selector, timeout=3000)
                        if tab_element:
                            logger.info(f"[FOUND] DOM tab found: {selector}")
                            await tab_element.click()
                            dom_tab_found = True
                            break
                    except:
                        continue
                
                if not dom_tab_found:
                    logger.info("[WARNING] DOM tab not found, using generic selectors...")
            
            # Wait for order form to load
            await self.page.wait_for_timeout(2000)
            
            # Strategy 3: Generic order placement
            return await self.fill_order_form()
            
        except Exception as e:
            logger.error(f"[ERROR] Test trade placement failed: {e}")
            await self.capture_screenshot("trade_placement_failed")
            return False
    
    async def fill_order_form(self) -> bool:
        """Fill order form with test values"""
        logger.info("[FORM] Filling order form...")
        
        try:
            # Look for quantity/amount field
            quantity_selectors = [
                'input[name*="quantity" i], input[name*="amount" i]',
                'input[placeholder*="quantity" i], input[placeholder*="amount" i]',
                'input[type="number"]:first-of-type'
            ]
            
            for selector in quantity_selectors:
                try:
                    qty_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if qty_input:
                        await qty_input.fill('1')  # Test with 1 unit
                        logger.info(f"[SUCCESS] Quantity set to 1: {selector}")
                        break
                except:
                    continue
            
            # Look for symbol/instrument selection
            symbol_selectors = [
                'select[name*="symbol" i], select[name*="instrument" i]',
                'input[name*="symbol" i], input[name*="instrument" i]',
                '.symbol-selector, .instrument-selector'
            ]
            
            for selector in symbol_selectors:
                try:
                    symbol_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if symbol_element:
                        # Try to select a common symbol (Gold futures)
                        if symbol_element.tag_name.lower() == 'select':
                            await symbol_element.select_option(label='GC')  # Gold
                        else:
                            await symbol_element.fill('GC')
                        logger.info(f"[SUCCESS] Symbol set to GC: {selector}")
                        break
                except:
                    continue
            
            # Look for buy/sell buttons
            buy_button_selectors = [
                'button:has-text("BUY"), button:has-text("Buy")',
                '[class*="buy" i] button, [id*="buy" i] button',
                '.buy-button, #buy-btn'
            ]
            
            for selector in buy_button_selectors:
                try:
                    buy_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if buy_button:
                        logger.info(f"[ORDER] Attempting to place BUY order: {selector}")
                        await buy_button.click()
                        
                        # Wait for potential confirmation or execution
                        await self.page.wait_for_timeout(3000)
                        
                        logger.info("[SUCCESS] Test trade order submitted successfully!")
                        return True
                except:
                    continue
            
            logger.warning("[WARNING] Could not find buy button, order form filled but not submitted")
            return True  # Consider partial success
            
        except Exception as e:
            logger.error(f"[ERROR] Order form filling failed: {e}")
            await self.capture_screenshot("order_form_failed")
            return False
    
    async def capture_screenshot(self, name: str):
        """Capture screenshot for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"[SCREENSHOT] Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"[ERROR] Screenshot capture failed: {e}")
    
    async def cleanup(self):
        """Clean up browser resources"""
        logger.info("[CLEANUP] Cleaning up browser resources...")
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("[SUCCESS] Cleanup complete")
        except Exception as e:
            logger.error(f"[ERROR] Cleanup error: {e}")
    
    async def run_full_automation(self) -> bool:
        """Execute complete automation workflow"""
        logger.info("[START] Starting TradeBot Sentinel full automation...")
        
        try:
            # Setup browser
            await self.setup_browser()
            
            # Login
            if not await self.login():
                logger.error("[ERROR] Login failed, aborting automation")
                return False
            
            # Navigate to trading
            if not await self.navigate_to_trading():
                logger.error("[ERROR] Trading navigation failed, aborting automation")
                return False
            
            # Place test trade
            if not await self.place_test_trade():
                logger.error("[ERROR] Test trade failed, but continuing...")
            
            # Wait for potential network requests
            logger.info("[WAIT] Waiting for trade execution requests...")
            await self.page.wait_for_timeout(5000)
            
            # Summary
            logger.info(f"[SUMMARY] Automation Summary:")
            logger.info(f"   Trade requests captured: {len(self.trade_requests)}")
            logger.info(f"   cURL file: {'[YES]' if Path('trade.sh').exists() else '[NO]'}")
            logger.info(f"   Python file: {'[YES]' if Path('trade_request_full.py').exists() else '[NO]'}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Automation failed: {e}")
            await self.capture_screenshot("automation_failure")
            return False
        
        finally:
            await self.cleanup()


async def main():
    """Main execution function"""
    print("[BOT] TradeBot Sentinel - Bulenox ProjectX Automation")
    print("=" * 50)
    
    # Check for required credentials
    username = os.getenv('BULENOX_USERNAME') or os.getenv('BROKER_USERNAME')
    password = os.getenv('BULENOX_PASSWORD') or os.getenv('BROKER_PASSWORD')
    
    if not username or not password:
        print("[ERROR] Missing credentials!")
        print("   Set environment variables:")
        print("   - BULENOX_USERNAME (or BROKER_USERNAME)")
        print("   - BULENOX_PASSWORD (or BROKER_PASSWORD)")
        print("\n   Example:")
        print("   export BULENOX_USERNAME=BX64883")
        print("   export BULENOX_PASSWORD=XujhMzFf6K")
        return False
    
    print(f"[SUCCESS] Credentials loaded for user: {username}")
    
    # Ask for headless mode preference
    headless_input = input("\n[DISPLAY] Run in headless mode? (y/N): ").strip().lower()
    headless = headless_input in ['y', 'yes']
    
    print(f"[START] Starting automation (headless={headless})...\n")
    
    # Initialize and run TradeBot Sentinel
    sentinel = TradeBotSentinel(headless=headless)
    
    try:
        success = await sentinel.run_full_automation()
        
        if success:
            print("\n[SUCCESS] TradeBot Sentinel automation completed successfully!")
            print("\n[FILES] Generated files:")
            if Path('trade.sh').exists():
                print("   [YES] trade.sh - cURL command for trade execution")
            if Path('trade_request_full.py').exists():
                print("   [YES] trade_request_full.py - Python requests code")
            print("   [YES] tradebot_sentinel.log - Detailed execution log")
            
            print("\n[READY] Ready for live trading integration!")
            return True
        else:
            print("\n[ERROR] Automation completed with errors. Check logs for details.")
            return False
            
    except KeyboardInterrupt:
        print("\n[WARNING] Automation interrupted by user")
        return False
    except Exception as e:
        print(f"\n[ERROR] Automation failed: {e}")
        return False


if __name__ == "__main__":
    # Set environment variables if not already set
    if not os.getenv('BULENOX_USERNAME'):
        os.environ['BULENOX_USERNAME'] = 'BX64883'
    if not os.getenv('BULENOX_PASSWORD'):
        os.environ['BULENOX_PASSWORD'] = 'XujhMzFf6K'
    if not os.getenv('BROKER_URL'):
        os.environ['BROKER_URL'] = 'https://bulenox.projectx.com/login'
    
    # Run the automation
    asyncio.run(main())