#!/usr/bin/env python3
"""
TradeBot Sentinel — Expert Automation Agent for Bulenox ProjectX Trading Platform
================================================================================

Specialized Playwright automation agent for interacting with Bulenox ProjectX's trading platform.
Designed for secure login, robust trading functionality, network request interception,
and comprehensive error handling with detailed logging and screenshot capture.

Features:
1. Secure login using environment variables BULENOX_USERNAME and BULENOX_PASSWORD
2. Robust fallback selectors if exact selectors fail
3. Time Sync Warning modal detection and handling during login
4. Dashboard confirmation with multiple selector strategies and retries
5. Trading page navigation and readiness verification
6. Order placement with exact selectors, DOM fallback, and generic selectors
7. Network interceptor for POST requests with trade execution detection
8. Automatic cURL command generation and Python requests conversion
9. Screenshot capture on critical failures for debugging
10. Verbose console logging at every step for traceability
11. Element wait retries (up to 3 times with 2 seconds delay)

Usage:
    python tradebot_sentinel_bulenox_automation.py [--headless] [--debug]
    
Environment Variables Required:
    BULENOX_USERNAME - Your Bulenox login username
    BULENOX_PASSWORD - Your Bulenox login password

Author: TradeBot Sentinel AI
Version: 1.0.0 Professional
"""

import asyncio
import json
import os
import subprocess
import sys
import random
import math
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Request
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip install playwright")
    print("   Then run: playwright install chromium")
    sys.exit(1)

try:
    import curlconverter
except ImportError:
    print("[WARNING] curlconverter not installed. Run: pip install curlconverter")
    print("   This is required for automatic Python code generation.")
    curlconverter = None

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradebot_sentinel_bulenox.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradeBotSentinel:
    """
    Expert automation agent for Bulenox ProjectX trading platform.
    Handles secure login, trading operations, and network request interception.
    """
    
    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.intercepted_requests: List[Dict] = []
        self.trade_requests: List[Dict] = []
        
        # Bulenox credentials from environment
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            logger.error("[CRITICAL] BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
            sys.exit(1)
            
        logger.info(f"[INIT] TradeBot Sentinel initialized - Headless: {headless}, Debug: {debug}")
        logger.info(f"[INIT] Username configured: {self.username[:3]}***")
    
    async def setup_browser(self) -> bool:
        """
        Initialize browser with enhanced anti-detection measures for Bulenox automation.
        """
        try:
            playwright = await async_playwright().start()
            
            # Randomize viewport slightly to avoid detection
            width = 1920 + random.randint(-50, 50)
            height = 1080 + random.randint(-50, 50)
            
            # Enhanced stealth browser arguments with additional evasion
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection',
                    f'--window-size={width},{height}',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-javascript-harmony-shipping',
                    '--disable-webgl',
                    '--disable-webgl2',
                    '--disable-accelerated-2d-canvas',
                    '--disable-reading-from-canvas',
                    '--disable-background-networking',
                    '--enable-features=NetworkService,NetworkServiceLogging',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-default-apps',
                    '--disable-extensions-http-throttling',
                    '--disable-features=TranslateUI',
                    '--disable-hang-monitor',
                    '--disable-notifications',
                    '--disable-popup-blocking',
                    '--disable-prompt-on-repost',
                    '--disable-speech-api',
                    '--disable-web-resources',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--log-level=3',
                    '--silent-debugger-extension-api',
                    '--test-type=webdriver',
                    '--disable-bundled-ppapi-flash',
                    '--disable-plugins-discovery',
                    '--disable-pepper-3d',
                    '--disable-permissions-api',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-throttling',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # Create persistent user data directory for more human-like behavior
            user_data_dir = Path.home() / '.bulenox_automation_data'
            user_data_dir.mkdir(exist_ok=True)
            
            # Load or create persistent storage state
            storage_file = user_data_dir / 'storage_state.json'
            storage_state = None
            if storage_file.exists():
                try:
                    with open(storage_file, 'r') as f:
                        storage_state = json.load(f)
                except Exception:
                    pass
            
            # Enhanced stealth context with realistic browser fingerprint
            self.context = await self.browser.new_context(
                viewport={'width': width, 'height': height},
                user_agent=self.get_random_user_agent(),
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                storage_state=storage_state,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'DNT': '1',
                    'sec-ch-ua': '"Chromium";v="120", "Not_A Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-arch': '"x86"',
                    'sec-ch-ua-bitness': '"64"',
                    'sec-ch-ua-full-version': '"120.0.0.0"',
                    'sec-ch-ua-full-version-list': '"Chromium";v="120.0.0.0", "Not_A Brand";v="24.0.0.0"'
                },
                record_video_dir=None,
                record_har_path=None,
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False,
                color_scheme='light',
                reduced_motion='no-preference',
                forced_colors='none'
            )
            
            # Add random delays to appear more human-like
            await asyncio.sleep(random.uniform(1.5, 3.5))
            
            # Create page and setup network interception
            self.page = await self.context.new_page()
            
            # Inject enhanced anti-detection script immediately after page creation
            await self.inject_anti_detection_script()
            
            # Execute anti-detection scripts to evade automation detection
            await self.page.add_init_script("""
                // Disable webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override plugins and languages to appear more natural
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock chrome runtime if not present
                if (!window.chrome) {
                    window.chrome = {
                        runtime: {},
                        loadTimes: () => ({}),
                        csi: () => ({})
                    };
                }
                
                // Override permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mock webgl vendor and renderer
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter(parameter);
                };
                
                // Add random mouse movements and human-like behavior
                const randomDelay = () => new Promise(resolve => setTimeout(resolve, Math.random() * 100 + 50));
                
                // Mock user activity
                window.addEventListener('mousemove', async () => {
                    await randomDelay();
                });
                
                // Remove automation indicators from window
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                console.log('Anti-detection scripts loaded successfully');
            """)
            
            # Add human-like mouse movements and delays
            await self.page.mouse.move(random.randint(100, 300), random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            await self.setup_network_interception()
            
            logger.info("[SUCCESS] Browser setup completed with enhanced anti-detection measures")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Browser setup failed: {e}")
            await self.capture_screenshot("browser_setup_error")
            return False
    
    async def setup_network_interception(self):
        """
        Setup network request interception to capture trade execution requests.
        """
        async def handle_request(request: Request):
            try:
                # Log all POST requests
                if request.method == 'POST':
                    url = request.url
                    headers = request.headers
                    
                    # Capture request data
                    request_data = {
                        'timestamp': datetime.now().isoformat(),
                        'method': request.method,
                        'url': url,
                        'headers': dict(headers),
                        'post_data': None
                    }
                    
                    # Try to get POST data
                    try:
                        post_data = request.post_data
                        if post_data:
                            request_data['post_data'] = post_data
                            
                            # Check if this looks like a trade execution request
                            if self.is_trade_request(url, post_data, headers):
                                logger.info(f"[TRADE DETECTED] Trade execution request intercepted: {url}")
                                self.trade_requests.append(request_data)
                                await self.save_curl_command(request_data)
                                await self.convert_to_python(request_data)
                    except Exception as e:
                        logger.debug(f"[DEBUG] Could not capture POST data: {e}")
                    
                    self.intercepted_requests.append(request_data)
                    logger.debug(f"[NETWORK] POST request logged: {url}")
                    
            except Exception as e:
                logger.error(f"[ERROR] Request interception failed: {e}")
        
        # Setup request interception
        self.page.on('request', handle_request)
        logger.info("[SUCCESS] Network interception setup completed")
    
    def is_trade_request(self, url: str, post_data: str, headers: Dict) -> bool:
        """
        Detect if a request is a trade execution request by analyzing URL, data, and headers.
        """
        try:
            # URL patterns that indicate trading
            trade_url_patterns = [
                'trade', 'order', 'position', 'buy', 'sell', 'execute',
                'submit', 'place', 'create', 'open', 'close'
            ]
            
            # Check URL for trade-related keywords
            url_lower = url.lower()
            url_contains_trade = any(pattern in url_lower for pattern in trade_url_patterns)
            
            # Check POST data for trade-related content
            data_contains_trade = False
            if post_data:
                post_data_lower = post_data.lower()
                trade_data_patterns = [
                    'symbol', 'amount', 'price', 'quantity', 'volume',
                    'order', 'trade', 'buy', 'sell', 'position',
                    'instrument', 'asset', 'market', 'execution'
                ]
                data_contains_trade = any(pattern in post_data_lower for pattern in trade_data_patterns)
                
                # Also check if it's JSON with trade-like structure
                try:
                    json_data = json.loads(post_data)
                    if isinstance(json_data, dict):
                        json_keys = [key.lower() for key in json_data.keys()]
                        data_contains_trade = data_contains_trade or any(
                            pattern in ' '.join(json_keys) for pattern in trade_data_patterns
                        )
                except:
                    pass
            
            # Content-Type check for API calls
            content_type = headers.get('content-type', '').lower()
            is_api_call = 'application/json' in content_type or 'application/x-www-form-urlencoded' in content_type
            
            # Final determination
            is_trade = (url_contains_trade or data_contains_trade) and is_api_call
            
            if is_trade:
                logger.info(f"[TRADE DETECTION] URL match: {url_contains_trade}, Data match: {data_contains_trade}, API: {is_api_call}")
            
            return is_trade
            
        except Exception as e:
            logger.error(f"[ERROR] Trade detection failed: {e}")
            return False
    
    async def save_curl_command(self, request_data: Dict):
        """
        Save intercepted trade request as cURL command to trade.sh file.
        """
        try:
            url = request_data['url']
            headers = request_data['headers']
            post_data = request_data.get('post_data', '')
            
            # Build cURL command
            curl_parts = ['curl', '-X', 'POST']
            
            # Add headers
            for key, value in headers.items():
                if key.lower() not in ['host', 'content-length']:
                    curl_parts.extend(['-H', f'"{key}: {value}"'])
            
            # Add POST data
            if post_data:
                curl_parts.extend(['-d', f"'{post_data}'"])
            
            # Add URL
            curl_parts.append(f"'{url}'")
            
            # Join command
            curl_command = ' '.join(curl_parts)
            
            # Save to file
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write('#!/bin/bash\n')
                f.write(f'# Trade execution cURL command\n')
                f.write(f'# Generated: {datetime.now().isoformat()}\n')
                f.write(f'# URL: {url}\n\n')
                f.write(curl_command)
                f.write('\n')
            
            logger.info("[SUCCESS] cURL command saved to trade.sh")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to save cURL command: {e}")
    
    async def convert_to_python(self, request_data: Dict):
        """
        Convert cURL command to Python requests code using curlconverter.
        """
        try:
            if not curlconverter:
                logger.warning("[WARNING] curlconverter not available, skipping Python conversion")
                return
            
            # Read the cURL command
            if not os.path.exists('trade.sh'):
                logger.error("[ERROR] trade.sh file not found for conversion")
                return
            
            with open('trade.sh', 'r', encoding='utf-8') as f:
                curl_content = f.read()
            
            # Extract the actual curl command (skip comments)
            curl_lines = [line for line in curl_content.split('\n') if line.strip() and not line.startswith('#')]
            if not curl_lines:
                logger.error("[ERROR] No valid cURL command found in trade.sh")
                return
            
            curl_command = ' '.join(curl_lines)
            
            # Convert to Python
            try:
                python_code = curlconverter.to_python(curl_command)
                
                # Enhance the Python code with additional imports and error handling
                enhanced_code = f'''#!/usr/bin/env python3
"""
Trade Execution Request - Auto-generated from cURL
Generated: {datetime.now().isoformat()}
Original URL: {request_data['url']}
"""

import requests
import json
from datetime import datetime

def execute_trade_request():
    """
    Execute the intercepted trade request.
    """
    try:
        print(f"[INFO] Executing trade request at {{datetime.now()}}")
        
{python_code}
        
        print(f"[SUCCESS] Trade request executed successfully")
        print(f"[RESPONSE] Status: {{response.status_code}}")
        print(f"[RESPONSE] Content: {{response.text[:500]}}...")
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Trade request failed: {{e}}")
        return None

if __name__ == "__main__":
    result = execute_trade_request()
    if result:
        print("Trade execution completed")
    else:
        print("Trade execution failed")
'''
                
                # Save enhanced Python code
                with open('trade_request_full.py', 'w', encoding='utf-8') as f:
                    f.write(enhanced_code)
                
                logger.info("[SUCCESS] Python requests code saved to trade_request_full.py")
                
            except Exception as e:
                logger.error(f"[ERROR] cURL to Python conversion failed: {e}")
                
        except Exception as e:
            logger.error(f"[ERROR] Python conversion process failed: {e}")
    
    async def capture_screenshot(self, name: str, description: str = ""):
        """
        Capture screenshot for debugging purposes.
        """
        try:
            if not self.page:
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{name}_{timestamp}.png"
            
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"[SCREENSHOT] Captured: {filename} - {description}")
            
        except Exception as e:
            logger.error(f"[ERROR] Screenshot capture failed: {e}")
    
    async def human_like_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """
        Add human-like delay between actions.
        """
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def human_click(self, selector: str, timeout: int = 10000) -> bool:
        """
        Perform human-like click with random offset and delay.
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if not element:
                return False
            
            # Get element bounds for random click position
            box = await element.bounding_box()
            if box:
                # Click at random position within element
                x = box['x'] + random.randint(5, int(box['width'] - 5))
                y = box['y'] + random.randint(5, int(box['height'] - 5))
                
                await self.page.mouse.click(x, y)
                await self.human_like_delay(100, 500)
                return True
            else:
                await element.click()
                await self.human_like_delay(100, 500)
                return True
                
        except Exception as e:
            logger.debug(f"[DEBUG] Click failed for selector {selector}: {e}")
            return False
    
    async def human_type(self, selector: str, text: str, timeout: int = 10000) -> bool:
        """
        Perform human-like typing with random delays.
        """
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if not element:
                return False
            
            await element.click()
            await self.human_like_delay(100, 300)
            
            # Clear existing content
            await element.fill('')
            await self.human_like_delay(50, 150)
            
            # Type character by character with random delays
            for char in text:
                await element.type(char)
                await asyncio.sleep(random.randint(50, 150) / 1000)
            
            await self.human_like_delay(100, 300)
            return True
            
        except Exception as e:
            logger.debug(f"[DEBUG] Typing failed for selector {selector}: {e}")
            return False
    
    async def wait_for_element_with_retry(self, selectors: List[str], timeout: int = 10000, retries: int = 3) -> Optional[str]:
        """
        Wait for any of the provided selectors with retry logic.
        """
        for attempt in range(retries):
            logger.info(f"[ATTEMPT] Element wait attempt {attempt + 1}/{retries}")
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=timeout // retries)
                    if element and await element.is_visible():
                        logger.info(f"[SUCCESS] Found element: {selector}")
                        return selector
                except Exception:
                    continue
            
            if attempt < retries - 1:
                logger.info(f"[RETRY] Waiting 2 seconds before retry...")
                await asyncio.sleep(2)
        
        logger.error(f"[ERROR] No elements found after {retries} attempts")
        return None
    
    async def handle_time_sync_warning(self) -> bool:
        """
        Detect and handle Time Sync Warning modals during login.
        """
        try:
            time_sync_selectors = [
                # Modal selectors
                '.modal:has-text("Time Sync")',
                '.modal:has-text("time sync")',
                '.modal:has-text("TIME SYNC")',
                '.dialog:has-text("Time Sync")',
                '.popup:has-text("Time Sync")',
                # Button selectors
                'button:has-text("OK")',
                'button:has-text("Close")',
                'button:has-text("Continue")',
                'button:has-text("Dismiss")',
                # Generic modal close buttons
                '.modal-close',
                '.close-button',
                '[data-dismiss="modal"]',
                '.btn-close'
            ]
            
            for selector in time_sync_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        logger.info(f"[TIME SYNC] Found time sync warning, dismissing: {selector}")
                        await self.human_click(selector)
                        await self.human_like_delay(500, 1000)
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"[ERROR] Time sync warning handling failed: {e}")
            return False
    
    async def login_to_bulenox(self) -> bool:
        """
        Perform secure login to Bulenox with enhanced anti-detection measures and human-like behavior.
        """
        try:
            logger.info("[LOGIN] Starting Bulenox login process with enhanced stealth...")
            
            # Add initial random delay to appear more natural
            await self.human_like_delay(1000, 2500)
            
            # Navigate to Bulenox login page
            bulenox_urls = [
                'https://bulenox.projectx.com/login'
            ]
            
            login_success = False
            for url in bulenox_urls:
                try:
                    logger.info(f"[LOGIN] Attempting login at: {url}")
                    
                    # Navigate with human-like mouse movements before page load
                    await self.page.mouse.move(random.randint(400, 800), random.randint(200, 400))
                    await asyncio.sleep(random.uniform(0.5, 1.2))
                    
                    await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    
                    # Wait for page to fully load with human-like timing
                    await self.human_like_delay(2500, 4000)
                    
                    # Simulate natural reading behavior - move mouse around page
                    for _ in range(random.randint(2, 4)):
                        await self.page.mouse.move(
                            random.randint(200, 1000), 
                            random.randint(200, 600)
                        )
                        await asyncio.sleep(random.uniform(0.3, 0.8))
                    
                    # Check for time sync warning
                    await self.handle_time_sync_warning()
                    
                    # Look for login form
                    username_selectors = [
                        'input[name="username"]',
                        'input[name="email"]',
                        'input[name="login"]',
                        'input[type="email"]',
                        'input[placeholder*="username"]',
                        'input[placeholder*="email"]',
                        'input[id*="username"]',
                        'input[id*="email"]',
                        'input[id*="login"]',
                        '#username',
                        '#email',
                        '#login',
                        '.username-input',
                        '.email-input',
                        '.login-input'
                    ]
                    
                    username_selector = await self.wait_for_element_with_retry(username_selectors, timeout=10000)
                    if username_selector:
                        logger.info(f"[LOGIN] Found username field: {username_selector}")
                        
                        # Enter username
                        if await self.human_type(username_selector, self.username):
                            logger.info("[LOGIN] Username entered successfully")
                            
                            # Find password field
                            password_selectors = [
                                'input[name="password"]',
                                'input[type="password"]',
                                'input[placeholder*="password"]',
                                'input[id*="password"]',
                                '#password',
                                '.password-input'
                            ]
                            
                            password_selector = await self.wait_for_element_with_retry(password_selectors, timeout=5000)
                            if password_selector:
                                logger.info(f"[LOGIN] Found password field: {password_selector}")
                                
                                # Enter password
                                if await self.human_type(password_selector, self.password):
                                    logger.info("[LOGIN] Password entered successfully")
                                    
                                    # Find and click submit button
                                    submit_selectors = [
                                        'button[type="submit"]',
                                        'input[type="submit"]',
                                        'button:has-text("Login")',
                                        'button:has-text("Sign In")',
                                        'button:has-text("Log In")',
                                        'button:has-text("Submit")',
                                        '.login-button',
                                        '.submit-button',
                                        '#login-button',
                                        '#submit-button',
                                        '[data-testid*="login"]',
                                        '[data-testid*="submit"]'
                                    ]
                                    
                                    submit_selector = await self.wait_for_element_with_retry(submit_selectors, timeout=5000)
                                    if submit_selector:
                                        logger.info(f"[LOGIN] Found submit button: {submit_selector}")
                                        
                                        await self.capture_screenshot("before_login_submit", "Before clicking login button")
                                        
                                        if await self.human_click(submit_selector):
                                            logger.info("[LOGIN] Submit button clicked")
                                            
                                            # Wait for login to complete
                                            await self.human_like_delay(3000, 5000)
                                            
                                            # Check for time sync warning after login
                                            await self.handle_time_sync_warning()
                                            
                                            # Verify login success
                                            if await self.confirm_login_success():
                                                login_success = True
                                                break
                    
                    if not login_success:
                        await self.capture_screenshot(f"login_failed_{url.replace('https://', '').replace('/', '_')}", f"Login failed at {url}")
                        
                except Exception as e:
                    logger.error(f"[ERROR] Login attempt failed for {url}: {e}")
                    continue
            
            if login_success:
                logger.info("[SUCCESS] Login completed successfully")
                await self.capture_screenshot("login_success", "Successful login")
                return True
            else:
                logger.error("[ERROR] All login attempts failed")
                await self.capture_screenshot("login_all_failed", "All login attempts failed")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Login process failed: {e}")
            await self.capture_screenshot("login_exception", f"Login exception: {e}")
            return False
    
    async def confirm_login_success(self) -> bool:
        """
        Confirm login success by waiting for dashboard selectors with retries.
        """
        try:
            logger.info("[VERIFY] Confirming login success...")
            
            dashboard_selectors = [
                # Dashboard indicators
                '.dashboard',
                '#dashboard',
                '.main-dashboard',
                '.user-dashboard',
                '.trading-dashboard',
                # Navigation elements
                '.navbar',
                '.nav-menu',
                '.main-nav',
                '.header-nav',
                # User account indicators
                '.user-menu',
                '.account-menu',
                '.profile-menu',
                '.user-info',
                '.account-info',
                # Trading interface elements
                '.trading-interface',
                '.trade-panel',
                '.market-data',
                '.portfolio',
                # Content areas
                '.main-content',
                '.app-content',
                '.content-wrapper',
                'main[role="main"]',
                # Generic success indicators
                '[data-testid*="dashboard"]',
                '[data-testid*="main"]',
                '[class*="dashboard"]',
                '[class*="main"]'
            ]
            
            success_selector = await self.wait_for_element_with_retry(dashboard_selectors, timeout=15000, retries=3)
            
            if success_selector:
                logger.info(f"[SUCCESS] Login confirmed - found dashboard element: {success_selector}")
                return True
            else:
                logger.error("[ERROR] Login confirmation failed - no dashboard elements found")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Login confirmation failed: {e}")
            return False
    
    async def navigate_to_trading(self) -> bool:
        """
        Navigate to trading page if not already there.
        """
        try:
            logger.info("[NAVIGATION] Navigating to trading page...")
            
            # Check if already on trading page
            if await self.confirm_trading_page():
                logger.info("[SUCCESS] Already on trading page")
                return True
            
            # Look for trading navigation links
            trading_nav_selectors = [
                # Text-based navigation
                'a:has-text("Trading")',
                'a:has-text("Trade")',
                'a:has-text("Markets")',
                'button:has-text("Trading")',
                'button:has-text("Trade")',
                'button:has-text("Markets")',
                # Class and ID selectors
                '.nav-trading',
                '.trading-nav',
                '.trade-nav',
                '#trading-link',
                '#trade-link',
                '[data-testid="trading-nav"]',
                '[data-testid="trade-nav"]',
                # Generic navigation patterns
                'nav a:has-text("Trading")',
                'nav button:has-text("Trading")',
                '.navbar a:has-text("Trading")',
                '.menu a:has-text("Trading")',
                '.sidebar a:has-text("Trading")',
                # Fallback patterns
                '[class*="trading"]',
                '[class*="trade"]',
                '[id*="trading"]',
                '[id*="trade"]'
            ]
            
            nav_selector = await self.wait_for_element_with_retry(trading_nav_selectors, timeout=10000)
            
            if nav_selector:
                logger.info(f"[NAVIGATION] Found trading navigation: {nav_selector}")
                
                if await self.human_click(nav_selector):
                    logger.info("[NAVIGATION] Trading navigation clicked")
                    await self.human_like_delay(2000, 3000)
                    
                    # Confirm trading page loaded
                    return await self.confirm_trading_page()
            
            logger.error("[ERROR] Could not find trading navigation")
            return False
            
        except Exception as e:
            logger.error(f"[ERROR] Navigation to trading failed: {e}")
            await self.capture_screenshot("navigation_error", f"Navigation error: {e}")
            return False
    
    async def confirm_trading_page(self) -> bool:
        """
        Confirm trading page readiness by waiting for trading interface selectors.
        """
        try:
            logger.info("[VERIFY] Confirming trading page readiness...")
            
            trading_selectors = [
                # Trading interface elements
                '.trading-interface',
                '.trade-panel',
                '.order-panel',
                '.buy-sell-panel',
                '.trading-form',
                '.order-form',
                # Market data elements
                '.market-data',
                '.price-feed',
                '.ticker',
                '.chart',
                '.trading-chart',
                # Order book elements
                '.order-book',
                '.depth-chart',
                '.market-depth',
                # Trading buttons
                'button:has-text("Buy")',
                'button:has-text("Sell")',
                'button:has-text("Order")',
                # Input fields
                'input[placeholder*="amount"]',
                'input[placeholder*="price"]',
                'input[placeholder*="quantity"]',
                # Text-based detection
                'text="Buy"',
                'text="Sell"',
                'text="Order"',
                'text="Price"',
                'text="Amount"',
                # Fallback selectors
                'form',
                'table',
                'canvas'
            ]
            
            trading_selector = await self.wait_for_element_with_retry(trading_selectors, timeout=15000, retries=3)
            
            if trading_selector:
                logger.info(f"[SUCCESS] Trading page confirmed - found element: {trading_selector}")
                return True
            else:
                logger.error("[ERROR] Trading page confirmation failed")
                await self.capture_screenshot("trading_page_not_found", "Trading page elements not found")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Trading page confirmation failed: {e}")
            return False
    
    async def place_trade_order(self, symbol: str = "GOLD", amount: float = 0.01, order_type: str = "BUY") -> bool:
        """
        Attempt to place a trade order using exact selectors, then fallback strategies.
        """
        try:
            logger.info(f"[TRADE] Attempting to place {order_type} order for {symbol} - Amount: {amount}")
            
            # Strategy 1: Try ORDER tab selectors
            order_tab_selectors = [
                'button:has-text("ORDER")',
                'tab:has-text("ORDER")',
                '.order-tab',
                '#order-tab',
                '[data-tab="order"]',
                '[data-testid="order-tab"]'
            ]
            
            order_tab_found = False
            for selector in order_tab_selectors:
                try:
                    if await self.human_click(selector, timeout=3000):
                        logger.info(f"[TRADE] ORDER tab clicked: {selector}")
                        order_tab_found = True
                        await self.human_like_delay(1000, 2000)
                        break
                except Exception:
                    continue
            
            # Strategy 2: Try DOM tab if ORDER tab not found
            if not order_tab_found:
                logger.info("[TRADE] ORDER tab not found, trying DOM tab...")
                dom_tab_selectors = [
                    'button:has-text("DOM")',
                    'tab:has-text("DOM")',
                    '.dom-tab',
                    '#dom-tab',
                    '[data-tab="dom"]',
                    '[data-testid="dom-tab"]'
                ]
                
                for selector in dom_tab_selectors:
                    try:
                        if await self.human_click(selector, timeout=3000):
                            logger.info(f"[TRADE] DOM tab clicked: {selector}")
                            await self.human_like_delay(1000, 2000)
                            break
                    except Exception:
                        continue
            
            # Strategy 3: Fill order form
            await self.fill_order_form(symbol, amount, order_type)
            
            # Strategy 4: Submit order
            return await self.submit_order(order_type)
            
        except Exception as e:
            logger.error(f"[ERROR] Trade order placement failed: {e}")
            await self.capture_screenshot("trade_order_error", f"Trade order error: {e}")
            return False
    
    async def fill_order_form(self, symbol: str, amount: float, order_type: str) -> bool:
        """
        Fill the order form with trade details.
        """
        try:
            logger.info(f"[TRADE] Filling order form - Symbol: {symbol}, Amount: {amount}, Type: {order_type}")
            
            # Symbol/Instrument selection
            symbol_selectors = [
                'select[name="symbol"]',
                'select[name="instrument"]',
                'input[name="symbol"]',
                'input[name="instrument"]',
                '.symbol-select',
                '.instrument-select',
                '#symbol',
                '#instrument'
            ]
            
            for selector in symbol_selectors:
                try:
                    if await self.human_type(selector, symbol, timeout=3000):
                        logger.info(f"[TRADE] Symbol entered: {selector}")
                        break
                except Exception:
                    continue
            
            # Amount/Quantity input
            amount_selectors = [
                'input[name="amount"]',
                'input[name="quantity"]',
                'input[name="volume"]',
                'input[name="size"]',
                'input[placeholder*="amount"]',
                'input[placeholder*="quantity"]',
                '.amount-input',
                '.quantity-input',
                '#amount',
                '#quantity'
            ]
            
            for selector in amount_selectors:
                try:
                    if await self.human_type(selector, str(amount), timeout=3000):
                        logger.info(f"[TRADE] Amount entered: {selector}")
                        break
                except Exception:
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Order form filling failed: {e}")
            return False
    
    async def submit_order(self, order_type: str) -> bool:
        """
        Submit the trade order using various button selectors.
        """
        try:
            logger.info(f"[TRADE] Submitting {order_type} order...")
            
            # Order type specific buttons
            if order_type.upper() == "BUY":
                submit_selectors = [
                    'button:has-text("BUY")',
                    'button:has-text("Buy")',
                    'button:has-text("buy")',
                    '.buy-button',
                    '#buy-button',
                    '[data-testid="buy-button"]',
                    'button[type="submit"]:has-text("Buy")',
                    'input[type="submit"][value*="Buy"]'
                ]
            else:
                submit_selectors = [
                    'button:has-text("SELL")',
                    'button:has-text("Sell")',
                    'button:has-text("sell")',
                    '.sell-button',
                    '#sell-button',
                    '[data-testid="sell-button"]',
                    'button[type="submit"]:has-text("Sell")',
                    'input[type="submit"][value*="Sell"]'
                ]
            
            # Generic submit buttons as fallback
            submit_selectors.extend([
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Place Order")',
                'button:has-text("Execute")',
                '.submit-button',
                '.order-submit',
                '#submit-order'
            ])
            
            submit_selector = await self.wait_for_element_with_retry(submit_selectors, timeout=10000)
            
            if submit_selector:
                logger.info(f"[TRADE] Found submit button: {submit_selector}")
                
                await self.capture_screenshot("before_order_submit", f"Before submitting {order_type} order")
                
                if await self.human_click(submit_selector):
                    logger.info(f"[SUCCESS] {order_type} order submitted successfully")
                    await self.human_like_delay(2000, 3000)
                    
                    await self.capture_screenshot("after_order_submit", f"After submitting {order_type} order")
                    return True
            
            logger.error("[ERROR] Could not find submit button")
            return False
            
        except Exception as e:
            logger.error(f"[ERROR] Order submission failed: {e}")
            return False
    
    async def run_automation(self) -> bool:
        """
        Main automation workflow.
        """
        try:
            logger.info("[START] TradeBot Sentinel automation starting...")
            
            # Step 1: Setup browser
            if not await self.setup_browser():
                logger.error("[CRITICAL] Browser setup failed")
                return False
            
            # Step 2: Login to Bulenox
            if not await self.login_to_bulenox():
                logger.error("[CRITICAL] Login failed")
                return False
            
            # Step 3: Navigate to trading page
            if not await self.navigate_to_trading():
                logger.error("[CRITICAL] Trading navigation failed")
                return False
            
            # Step 4: Place a test trade order
            if not await self.place_trade_order("GOLD", 0.01, "BUY"):
                logger.warning("[WARNING] Trade order placement failed, but continuing...")
            
            # Step 5: Keep the session alive to monitor for trade requests
            logger.info("[MONITOR] Monitoring for trade execution requests...")
            logger.info("[INFO] Press Ctrl+C to stop monitoring")
            
            # Monitor for trade requests for a specified duration
            monitor_duration = 300  # 5 minutes
            start_time = datetime.now()
            
            while (datetime.now() - start_time).seconds < monitor_duration:
                await asyncio.sleep(5)
                
                # Log current status
                if len(self.trade_requests) > 0:
                    logger.info(f"[STATUS] Captured {len(self.trade_requests)} trade requests")
                
                # Check for new trade requests
                if len(self.trade_requests) > 0:
                    latest_request = self.trade_requests[-1]
                    logger.info(f"[LATEST] Latest trade request: {latest_request['url']}")
            
            logger.info(f"[COMPLETE] Monitoring completed. Total trade requests captured: {len(self.trade_requests)}")
            return True
            
        except KeyboardInterrupt:
            logger.info("[INTERRUPT] Monitoring stopped by user")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Automation failed: {e}")
            await self.capture_screenshot("automation_error", f"Automation error: {e}")
            return False
        finally:
            await self.cleanup()
    
    def get_random_user_agent(self) -> str:
        """Generate a realistic Chrome user agent with version variations."""
        chrome_versions = [
            "120.0.0.0", "119.0.0.0", "118.0.0.0", "117.0.0.0", "116.0.0.0"
        ]
        version = random.choice(chrome_versions)
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"

    async def inject_anti_detection_script(self):
        """Inject sophisticated anti-detection JavaScript to bypass Chrome automation detection."""
        anti_detection_script = """
        // Override navigator properties to remove automation indicators
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Remove automation flags from user agent
        Object.defineProperty(navigator, 'userAgent', {
            get: () => navigator.userAgent.replace(/HeadlessChrome/g, 'Chrome'),
        });
        
        // Override plugins to appear like a real browser
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {
                        type: "application/x-google-chrome-pdf",
                        suffixes: "pdf",
                        description: "Portable Document Format",
                        enabledPlugin: Plugin
                    },
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {
                        type: "application/pdf",
                        suffixes: "pdf",
                        description: "",
                        enabledPlugin: Plugin
                    },
                    description: "",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                }
            ],
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Override webdriver chrome
        delete window.chrome;
        window.chrome = {
            runtime: {},
            loadTimes: function() {
                return {
                    commitLoadTime: performance.timing.domContentLoadedEventStart / 1000,
                    connectionInfo: 'h2',
                    finishDocumentLoadTime: performance.timing.loadEventStart / 1000,
                    finishLoadTime: performance.timing.loadEventEnd / 1000,
                    firstPaintAfterLoadTime: 0,
                    firstPaintTime: performance.timing.domContentLoadedEventStart / 1000,
                    navigationStart: performance.timing.navigationStart / 1000,
                    npnNegotiatedProtocol: 'h2',
                    requestTime: performance.timing.requestStart / 1000,
                    startLoadTime: performance.timing.responseStart / 1000,
                    wasAlternateProtocolAvailable: false,
                    wasFetchedViaSpdy: true,
                    wasNpnNegotiated: true
                };
            },
            csi: function() {
                return {
                    onloadT: Date.now(),
                    pageT: Date.now() - performance.timing.navigationStart,
                    startE: performance.timing.navigationStart,
                    tran: 15
                };
            }
        };
        
        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock WebGL vendor and renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter(parameter);
        };
        
        // Add random mouse movements
        function addRandomMouseMovement() {
            const move = () => {
                const x = Math.floor(Math.random() * window.innerWidth);
                const y = Math.floor(Math.random() * window.innerHeight);
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                document.dispatchEvent(event);
            };
            
            // Add random movements every 2-5 seconds
            setInterval(move, Math.random() * 3000 + 2000);
        }
        
        // Override screen properties
        Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
        
        // Remove automation indicators from window
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        // Override console.debug to prevent automation logs
        const originalDebug = console.debug;
        console.debug = function(...args) {
            if (args[0] && args[0].includes && args[0].includes('DevTools')) {
                return;
            }
            return originalDebug.apply(console, args);
        };
        
        // Add random delays to appear more human-like
        setTimeout(addRandomMouseMovement, 1000);
        
        // Override Date.now to add slight randomization
        const originalNow = Date.now;
        let offset = 0;
        Date.now = function() {
            if (Math.random() < 0.1) {
                offset += Math.floor(Math.random() * 10) - 5;
            }
            return originalNow() + offset;
        };
        """
        
        await self.page.add_init_script(anti_detection_script)
        logger.info("[STEALTH] Anti-detection script injected successfully")

    async def save_storage_state(self):
        """Save browser storage state to maintain session persistence."""
        try:
            if self.context:
                user_data_dir = Path.home() / '.bulenox_automation_data'
                storage_file = user_data_dir / 'storage_state.json'
                await self.context.storage_state(path=str(storage_file))
                logger.info("[STORAGE] Storage state saved for session persistence")
        except Exception as e:
            logger.error(f"[ERROR] Failed to save storage state: {e}")

    async def cleanup(self):
        """
        Clean up browser resources.
        """
        try:
            logger.info("[CLEANUP] Cleaning up browser resources...")
            
            # Save storage state before cleanup
            await self.save_storage_state()
            
            if self.context:
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            logger.info("[CLEANUP] Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"[ERROR] Cleanup failed: {e}")

def main():
    """
    Main entry point for TradeBot Sentinel.
    """
    parser = argparse.ArgumentParser(description='TradeBot Sentinel - Bulenox Trading Automation')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (default: False)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (default: False)')
    
    args = parser.parse_args()
    
    # Create and run the automation
    sentinel = TradeBotSentinel(headless=args.headless, debug=args.debug)
    
    try:
        # Run the automation
        result = asyncio.run(sentinel.run_automation())
        
        if result:
            print("\n" + "="*60)
            print("🎯 TRADEBOT SENTINEL AUTOMATION COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"📊 Total requests intercepted: {len(sentinel.intercepted_requests)}")
            print(f"💰 Trade requests captured: {len(sentinel.trade_requests)}")
            
            if len(sentinel.trade_requests) > 0:
                print("\n📁 Generated Files:")
                print("   ├── trade.sh (cURL command)")
                print("   └── trade_request_full.py (Python requests code)")
                
                print("\n🔍 Trade Requests Summary:")
                for i, req in enumerate(sentinel.trade_requests, 1):
                    print(f"   {i}. {req['timestamp']} - {req['url']}")
            
            print("\n✅ Automation completed successfully!")
        else:
            print("\n" + "="*60)
            print("❌ TRADEBOT SENTINEL AUTOMATION FAILED")
            print("="*60)
            print("Check the logs for detailed error information.")
            
    except KeyboardInterrupt:
        print("\n🛑 Automation interrupted by user")
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        logger.error(f"[CRITICAL] Main execution failed: {e}")

if __name__ == "__main__":
    main()