#!/usr/bin/env python3
"""
TradeBot Sentinel - Enhanced Stealth Version
Improved anti-detection measures for Bulenox trading automation

Enhancements:
- Advanced browser fingerprinting evasion
- Human-like timing and mouse movements
- Enhanced stealth configuration
- Better element detection strategies
- Improved error handling for detected automation
"""

import os
import sys
import json
import asyncio
import re
import subprocess
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse
import logging

# Auto-install dependencies
def ensure_dependencies():
    """Automatically install required dependencies"""
    required_packages = {
        'playwright': 'playwright',
        'playwright_stealth': 'playwright-stealth',
        'python-dotenv': 'python-dotenv',
        'curlconverter': 'curlconverter'
    }
    
    for module, package in required_packages.items():
        try:
            __import__(module.replace('-', '_'))
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            if package == 'playwright':
                subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])

ensure_dependencies()

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Request, Response
from playwright_stealth import stealth_async
from dotenv import load_dotenv

class EnhancedTradeBotSentinel:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Configuration
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        self.profile_path = os.getenv('BULENOX_PROFILE_PATH')
        self.profile_name = os.getenv('BULENOX_PROFILE_NAME', 'Default')
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        
        # Enhanced stealth settings
        self.human_delay_min = 800
        self.human_delay_max = 2500
        self.typing_delay_min = 50
        self.typing_delay_max = 200
        self.mouse_move_steps = 10
        
        # Logging setup
        self.setup_logging()
        
        # Network monitoring
        self.network_logs = []
        self.trade_requests = []
        
        # Enhanced selectors with more fallbacks
        self.selectors = self.get_enhanced_selectors()
        
    def setup_logging(self):
        """Setup enhanced logging with more detail"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tradebot_stealth.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_enhanced_selectors(self) -> Dict[str, List[str]]:
        """Enhanced selectors with more fallback options"""
        return {
            'username': [
                'input[name="username"]',
                'input[type="text"][placeholder*="username" i]',
                'input[type="text"][placeholder*="email" i]',
                'input[type="email"]',
                '#username', '#email', '#user',
                '.username-input', '.email-input',
                'input[data-testid*="username"]',
                'input[data-testid*="email"]',
                'input[autocomplete="username"]',
                'input[autocomplete="email"]'
            ],
            'password': [
                'input[name="password"]',
                'input[type="password"]',
                '#password', '#pass',
                '.password-input',
                'input[data-testid*="password"]',
                'input[autocomplete="current-password"]',
                'input[placeholder*="password" i]'
            ],
            'login_submit': [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign In")',
                'button:has-text("Login")',
                'button:has-text("Log In")',
                'button:has-text("Submit")',
                '.login-button', '.submit-button',
                '#login-btn', '#submit-btn',
                'button[data-testid*="login"]',
                'button[data-testid*="submit"]'
            ],
            'dashboard': [
                '.dashboard', '#dashboard',
                '.main-content', '.app-content',
                '[data-testid*="dashboard"]',
                '.trading-interface',
                '.user-dashboard',
                'main[role="main"]',
                '.content-wrapper'
            ]
        }
    
    async def human_delay(self, min_ms: int = None, max_ms: int = None):
        """Add human-like random delays"""
        min_delay = min_ms or self.human_delay_min
        max_delay = max_ms or self.human_delay_max
        delay = random.randint(min_delay, max_delay)
        await asyncio.sleep(delay / 1000)
        
    async def human_type(self, page: Page, selector: str, text: str):
        """Type text with human-like timing"""
        element = await page.wait_for_selector(selector, timeout=10000)
        await element.click()
        await self.human_delay(200, 500)
        
        # Clear existing text
        await element.fill('')
        await self.human_delay(100, 300)
        
        # Type with random delays
        for char in text:
            await element.type(char, delay=random.randint(self.typing_delay_min, self.typing_delay_max))
            
    async def human_click(self, page: Page, selector: str):
        """Click with human-like mouse movement"""
        element = await page.wait_for_selector(selector, timeout=10000)
        box = await element.bounding_box()
        
        if box:
            # Calculate click position with slight randomization
            x = box['x'] + box['width'] / 2 + random.randint(-5, 5)
            y = box['y'] + box['height'] / 2 + random.randint(-5, 5)
            
            # Move mouse in steps to simulate human movement
            current_pos = await page.evaluate('() => ({ x: 0, y: 0 })')
            steps = self.mouse_move_steps
            
            for i in range(steps):
                step_x = current_pos['x'] + (x - current_pos['x']) * (i + 1) / steps
                step_y = current_pos['y'] + (y - current_pos['y']) * (i + 1) / steps
                await page.mouse.move(step_x, step_y)
                await asyncio.sleep(random.randint(10, 30) / 1000)
            
            await self.human_delay(100, 300)
            await page.mouse.click(x, y)
        else:
            # Fallback to regular click
            await element.click()
            
    async def setup_enhanced_browser_context(self, playwright) -> tuple[Browser, BrowserContext, Page]:
        """Setup browser with enhanced anti-detection measures"""
        self.logger.info("[STEALTH] Setting up enhanced stealth browser...")
        
        # Enhanced launch arguments for better stealth
        launch_args = [
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--no-first-run',
            '--disable-default-apps',
            '--disable-dev-shm-usage',
            '--disable-extensions-except=/path/to/extension',
            '--disable-plugins-discovery',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-back-forward-cache',
            '--disable-ipc-flooding-protection',
            '--enable-features=NetworkService,NetworkServiceLogging',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--use-mock-keychain'
        ]
        
        browser = None
        context = None
        
        # Use Chrome profile if available
        if self.profile_path and os.path.exists(self.profile_path):
            profile_dir = os.path.join(self.profile_path, self.profile_name)
            if os.path.exists(profile_dir):
                self.logger.info(f"[PROFILE] Using Chrome profile: {profile_dir}")
                
                context = await playwright.chromium.launch_persistent_context(
                    user_data_dir=self.profile_path,
                    headless=self.headless,
                    args=launch_args + [f'--profile-directory={self.profile_name}'],
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                    geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )
                
                pages = context.pages
                if pages:
                    page = pages[0]
                else:
                    page = await context.new_page()
        
        # Fallback to fresh browser
        if context is None:
            self.logger.info("[BROWSER] Using fresh browser instance with enhanced stealth")
            
            browser = await playwright.chromium.launch(
                headless=self.headless,
                args=launch_args
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            page = await context.new_page()
        
        # Apply enhanced stealth measures
        await stealth_async(page)
        
        # Additional anti-detection scripts
        await page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Hide automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
        
        # Set network interceptors
        page.on('request', self._on_request)
        page.on('response', self._on_response)
        
        return browser, context, page
    
    async def enhanced_login(self, page: Page) -> bool:
        """Enhanced login with better stealth and error handling"""
        try:
            self.logger.info("[LOGIN] Starting enhanced stealth login process...")
            
            # Navigate to login page
            await page.goto('https://app.bulenox.projectx.com/login', wait_until='networkidle')
            await self.human_delay(2000, 4000)
            
            # Handle any modals or popups
            await self.handle_modals(page)
            
            # Find and fill username
            username_selector = await self.find_element_with_fallbacks(page, self.selectors['username'])
            if not username_selector:
                raise Exception("Could not find username field")
                
            self.logger.info("[LOGIN] Found username field, typing credentials...")
            await self.human_type(page, username_selector, self.username)
            await self.human_delay(500, 1000)
            
            # Find and fill password
            password_selector = await self.find_element_with_fallbacks(page, self.selectors['password'])
            if not password_selector:
                raise Exception("Could not find password field")
                
            await self.human_type(page, password_selector, self.password)
            await self.human_delay(1000, 2000)
            
            # Find and click submit button
            submit_selector = await self.find_element_with_fallbacks(page, self.selectors['login_submit'])
            if not submit_selector:
                raise Exception("Could not find submit button")
                
            self.logger.info("[LOGIN] Clicking submit button...")
            await self.human_click(page, submit_selector)
            
            # Wait for navigation with longer timeout
            await page.wait_for_load_state('networkidle', timeout=30000)
            await self.human_delay(3000, 5000)
            
            # Verify login success
            dashboard_selector = await self.find_element_with_fallbacks(page, self.selectors['dashboard'])
            if dashboard_selector:
                self.logger.info("[LOGIN] ✅ Login successful!")
                return True
            else:
                self.logger.warning("[LOGIN] ⚠️ Login may have failed - dashboard not found")
                return False
                
        except Exception as e:
            self.logger.error(f"[LOGIN] ❌ Login failed: {e}")
            await self.capture_screenshot(page, "login_failure")
            return False
    
    async def find_element_with_fallbacks(self, page: Page, selectors: List[str]) -> Optional[str]:
        """Find element using multiple fallback selectors with enhanced waiting"""
        for i, selector in enumerate(selectors):
            try:
                self.logger.debug(f"[SELECTOR] Trying selector {i+1}/{len(selectors)}: {selector}")
                await page.wait_for_selector(selector, timeout=5000)
                self.logger.debug(f"[SELECTOR] ✅ Found element with: {selector}")
                return selector
            except Exception:
                continue
                
        self.logger.warning(f"[SELECTOR] ❌ Could not find element with any of {len(selectors)} selectors")
        return None
    
    async def handle_modals(self, page: Page):
        """Handle various modals and popups"""
        modal_selectors = [
            '.modal', '.popup', '.overlay',
            '[role="dialog"]', '[role="alertdialog"]',
            '.time-sync-warning', '.cookie-banner'
        ]
        
        for selector in modal_selectors:
            try:
                if await page.is_visible(selector, timeout=1000):
                    self.logger.info(f"[MODAL] Found modal: {selector}")
                    
                    # Try to close it
                    close_selectors = [
                        f'{selector} button:has-text("Close")',
                        f'{selector} button:has-text("OK")',
                        f'{selector} button:has-text("Accept")',
                        f'{selector} .close', f'{selector} .dismiss'
                    ]
                    
                    for close_sel in close_selectors:
                        try:
                            if await page.is_visible(close_sel, timeout=1000):
                                await self.human_click(page, close_sel)
                                await self.human_delay(500, 1000)
                                break
                        except Exception:
                            continue
            except Exception:
                continue
    
    async def capture_screenshot(self, page: Page, name: str):
        """Capture screenshot for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            await page.screenshot(path=filename, full_page=True)
            self.logger.info(f"[SCREENSHOT] Saved: {filename}")
        except Exception as e:
            self.logger.error(f"[SCREENSHOT] Failed to capture: {e}")
    
    async def _on_request(self, request: Request):
        """Enhanced network request interceptor"""
        if request.method == 'POST':
            url = request.url
            self.logger.info(f"[POST] {url}")
            
            # Enhanced trade detection
            if await self._is_trade_request(request):
                self.logger.info("[TRADE] 🎯 Trade execution request detected!")
                await self._capture_trade_request(request)
    
    async def _on_response(self, response: Response):
        """Enhanced network response interceptor"""
        if response.request.method == 'POST':
            try:
                response_text = await response.text()
                if any(keyword in response_text.lower() for keyword in ['order', 'trade', 'execution', 'fill']):
                    self.logger.info(f"[RESPONSE] Trade-related response: {response.url}")
            except Exception:
                pass
    
    async def _is_trade_request(self, request: Request) -> bool:
        """Enhanced trade request detection"""
        url = request.url.lower()
        
        # Enhanced URL pattern matching
        trade_patterns = [
            'order', 'trade', 'buy', 'sell', 'execute', 'position',
            'submit', 'place', 'create', 'modify', 'cancel'
        ]
        
        if any(pattern in url for pattern in trade_patterns):
            return True
            
        # Enhanced POST data analysis
        try:
            post_data = request.post_data
            if post_data:
                data_lower = post_data.lower()
                trade_keywords = [
                    'symbol', 'amount', 'price', 'quantity', 'order_type',
                    'side', 'instrument', 'volume', 'lots', 'contracts'
                ]
                
                if any(keyword in data_lower for keyword in trade_keywords):
                    return True
                    
                # JSON analysis
                try:
                    json_data = json.loads(post_data)
                    if isinstance(json_data, dict):
                        keys = [k.lower() for k in json_data.keys()]
                        if any(keyword in ' '.join(keys) for keyword in trade_keywords):
                            return True
                except json.JSONDecodeError:
                    pass
                    
        except Exception:
            pass
            
        return False
    
    async def _capture_trade_request(self, request: Request):
        """Enhanced trade request capture"""
        try:
            headers = dict(request.headers)
            post_data = request.post_data or ''
            
            # Generate enhanced cURL command
            curl_parts = [f'curl -X POST "{request.url}"']
            
            # Add headers
            for key, value in headers.items():
                curl_parts.append(f'-H "{key}: {value}"')
            
            # Add data
            if post_data:
                curl_parts.append(f'--data-raw \'{post_data}\'')
            
            curl_command = ' \\
  '.join(curl_parts)
            
            # Save to file
            with open('trade_stealth.sh', 'w', encoding='utf-8') as f:
                f.write(curl_command)
            
            self.logger.info("[CAPTURE] ✅ Trade request saved to trade_stealth.sh")
            
            # Convert to Python
            await self._convert_to_python(curl_command)
            
        except Exception as e:
            self.logger.error(f"[CAPTURE] ❌ Failed to capture trade request: {e}")
    
    async def _convert_to_python(self, curl_command: str):
        """Convert cURL to Python with enhanced error handling"""
        try:
            # Manual conversion for better reliability
            python_code = self._manual_curl_to_python(curl_command)
            
            with open('trade_request_stealth.py', 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            self.logger.info("[CONVERT] ✅ Python code saved to trade_request_stealth.py")
            
        except Exception as e:
            self.logger.error(f"[CONVERT] ❌ Failed to convert to Python: {e}")
    
    def _manual_curl_to_python(self, curl_command: str) -> str:
        """Manual cURL to Python conversion"""
        lines = curl_command.split('\n')
        url = ''
        headers = {}
        data = ''
        
        for line in lines:
            line = line.strip().rstrip(' \\')
            
            if line.startswith('curl -X POST'):
                url = line.split('"')[1]
            elif line.startswith('-H'):
                header_content = line[3:].strip('"')
                if ':' in header_content:
                    key, value = header_content.split(':', 1)
                    headers[key.strip()] = value.strip()
            elif line.startswith('--data-raw'):
                data = line[11:].strip("'")
        
        python_template = f'''#!/usr/bin/env python3
"""
Generated Trade Request - Enhanced Stealth Version
Generated from captured network request
"""

import requests
import json
from datetime import datetime

def execute_trade_request():
    """Execute the captured trade request"""
    url = "{url}"
    
    headers = {json.dumps(headers, indent=8)}
    
    data = '''{data}'''
    
    try:
        print(f"[{{datetime.now()}}] Executing trade request...")
        print(f"URL: {{url}}")
        
        response = requests.post(url, headers=headers, data=data)
        
        print(f"Status Code: {{response.status_code}}")
        print(f"Response: {{response.text[:200]}}...")
        
        if response.status_code == 200:
            print("✅ Trade request executed successfully!")
        else:
            print(f"⚠️ Trade request returned status {{response.status_code}}")
            
        return response
        
    except Exception as e:
        print(f"❌ Error executing trade request: {{e}}")
        return None

if __name__ == "__main__":
    execute_trade_request()
'''
        
        return python_template
    
    async def run(self):
        """Main execution with enhanced error handling"""
        browser = None
        context = None
        
        try:
            self.logger.info("[START] 🚀 Enhanced TradeBot Sentinel starting...")
            
            # Validate credentials
            if not self.username or not self.password:
                raise Exception("Missing BULENOX_USERNAME or BULENOX_PASSWORD environment variables")
            
            async with async_playwright() as playwright:
                # Setup enhanced browser
                browser, context, page = await self.setup_enhanced_browser_context(playwright)
                
                # Enhanced login process
                login_success = await self.enhanced_login(page)
                
                if login_success:
                    self.logger.info("[SUCCESS] ✅ Enhanced stealth login completed successfully!")
                    self.logger.info("[MONITOR] 👁️ Network monitoring active - waiting for trade requests...")
                    
                    # Keep monitoring for trade requests
                    while True:
                        await asyncio.sleep(5)
                        
                        # Check if page is still active
                        try:
                            await page.evaluate('document.title')
                        except Exception:
                            self.logger.warning("[MONITOR] Page became inactive, reloading...")
                            await page.reload(wait_until='networkidle')
                            await self.human_delay(2000, 4000)
                else:
                    self.logger.error("[FAILED] ❌ Enhanced login failed")
                    
        except KeyboardInterrupt:
            self.logger.info("[STOP] 🛑 Stopped by user")
        except Exception as e:
            self.logger.error(f"[ERROR] ❌ Critical error: {e}")
        finally:
            # Cleanup
            try:
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except Exception:
                pass
            
            self.logger.info("[CLEANUP] 🧹 Browser cleanup completed")

if __name__ == "__main__":
    sentinel = EnhancedTradeBotSentinel()
    asyncio.run(sentinel.run())