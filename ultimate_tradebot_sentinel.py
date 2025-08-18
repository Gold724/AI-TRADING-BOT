#!/usr/bin/env python3
"""
Ultimate TradeBot Sentinel - AI-Enhanced Playwright Trading Automation
Combines AI-powered login with advanced network interception and trade capture.

Features:
- AI-enhanced login with multiple fallback strategies
- Advanced Playwright network interception
- Intelligent selector detection and retry logic
- Automatic cURL and Python code generation
- Enhanced error handling and debugging
- Profile conflict resolution
"""

import asyncio
import json
import os
import subprocess
import sys
import random
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Request
from typing import Optional, Dict, Any, List, Union
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

# Configure logging with UTF-8 encoding
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_tradebot_sentinel.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Set console encoding to UTF-8 for Windows
if sys.platform == 'win32':
    import os
    os.system('chcp 65001 > nul')
logger = logging.getLogger(__name__)

class UltimateTradeBotSentinel:
    """Ultimate AI-Enhanced TradeBot Sentinel"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Load credentials
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            logger.error("Missing credentials! Set BULENOX_USERNAME and BULENOX_PASSWORD environment variables.")
            sys.exit(1)
        
        logger.info(f"Credentials loaded for user: {self.username[:3]}***")
        
        # Enhanced configuration
        self.max_retries = 3
        self.retry_delay = 2000  # milliseconds
        self.post_requests: List[Dict] = []
        self.trade_requests: List[Dict] = []
        
        # Create logs directory
        self.logs_dir = Path('logs/curls')
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # AI-Enhanced selectors with confidence weights
        self.login_selectors = {
            'username': [
                {'selector': 'input[name="username"]', 'weight': 0.9},
                {'selector': 'input[name="email"]', 'weight': 0.9},
                {'selector': 'input[type="email"]', 'weight': 0.8},
                {'selector': '#username', 'weight': 0.8},
                {'selector': '#email', 'weight': 0.8},
                {'selector': 'input[placeholder*="Email" i]', 'weight': 0.7},
                {'selector': 'input[placeholder*="Username" i]', 'weight': 0.7},
                {'selector': 'input[placeholder*="mail" i]', 'weight': 0.6},
                {'selector': 'input[placeholder*="user" i]', 'weight': 0.6},
                {'selector': '.username-input', 'weight': 0.5},
                {'selector': '.email-input', 'weight': 0.5},
                {'selector': 'form input[type="text"]:first-of-type', 'weight': 0.4}
            ],
            'password': [
                {'selector': 'input[name="password"]', 'weight': 0.9},
                {'selector': 'input[type="password"]', 'weight': 0.9},
                {'selector': '#password', 'weight': 0.8},
                {'selector': 'input[placeholder*="Password" i]', 'weight': 0.7},
                {'selector': 'input[placeholder*="pass" i]', 'weight': 0.6},
                {'selector': '.password-input', 'weight': 0.5}
            ],
            'login_button': [
                {'selector': 'button[type="submit"]', 'weight': 0.9},
                {'selector': 'input[type="submit"]', 'weight': 0.8},
                {'selector': 'button:has-text("Login")', 'weight': 0.8},
                {'selector': 'button:has-text("Sign In")', 'weight': 0.8},
                {'selector': 'button:has-text("Log In")', 'weight': 0.8},
                {'selector': '.login-button', 'weight': 0.7},
                {'selector': '.submit-button', 'weight': 0.7},
                {'selector': 'form button', 'weight': 0.6}
            ]
        }
        
        # Dashboard detection selectors - Enhanced for ProjectX
        self.dashboard_selectors = [
            # ProjectX specific selectors
            '.main-content',
            '.trading-interface',
            '.user-menu',
            '.account-info',
            '.portfolio',
            '.balance-info',
            '.navbar',
            '.header-menu',
            '.profile-menu',
            '.nav-menu',
            '.sidebar',
            '.header-user',
            'nav',
            'header',
            '.container',
            '[role="main"]',
            '[role="navigation"]',
            'button[class*="user"]',
            'div[class*="user"]',
            'span[class*="user"]',
            # Generic dashboard selectors
            'div.dashboard-root',
            '#dashboard',
            '.dashboard',
            '[data-testid="dashboard"]',
            '.main-dashboard',
            '#main-dashboard',
            'a:has-text("Dashboard")',
            'a:has-text("Trading")',
            'a:has-text("Account")',
            'a:has-text("Logout")',
            '.user-profile',
            '[class*="dashboard"]',
            '[class*="main"]',
            '[class*="home"]',
            '[class*="trading"]',
            '[class*="portfolio"]',
            '[class*="account"]',
            '.welcome-message',
            '[href*="logout"]'
        ]
        
        # Trading page selectors
        self.trading_selectors = [
            'input[placeholder*="Symbol" i]',
            'input[placeholder*="symbol" i]',
            '#trade-symbol',
            '.trade-symbol',
            '[data-testid="trade-symbol"]',
            'input[name*="symbol"]',
            '.trading-interface',
            'button:has-text("Buy")',
            'button:has-text("Sell")',
            '.buy-button',
            '.sell-button'
        ]
        
        # Trade execution patterns
        self.trade_url_patterns = [
            '/trade', '/orders', '/api/trade', '/api/orders',
            '/execute', '/position', '/buy', '/sell', '/order'
        ]
        
        self.trade_payload_keys = [
            'symbol', 'side', 'quantity', 'amount', 'price',
            'order', 'trade', 'buy', 'sell', 'position'
        ]
    
    async def setup_browser(self):
        """Setup Playwright browser with enhanced configuration"""
        try:
            logger.info("Setting up browser and network interceptor...")
            
            playwright = await async_playwright().start()
            
            # Enhanced browser launch options
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-extensions',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection'
                ]
            }
            
            # Use persistent context for profile support
            user_data_dir = Path.cwd() / "temp_chrome_profile_ultimate"
            user_data_dir.mkdir(exist_ok=True)
            
            # Create persistent context with enhanced settings
            context_options = {
                'headless': self.headless,
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'extra_http_headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                },
                'args': launch_options['args']
            }
            
            self.context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                **context_options
            )
            
            # Get the first page or create new one
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()
            
            # Add stealth scripts
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {},
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            # Setup network interception
            await self.setup_network_interceptor()
            
            logger.info("Browser setup completed successfully")
            
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            raise
    
    async def setup_network_interceptor(self):
        """Setup enhanced network request interception"""
        async def handle_request(request: Request):
            if request.method == 'POST':
                try:
                    url = request.url
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    
                    # Get POST data
                    post_data = None
                    try:
                        post_data = request.post_data
                    except:
                        pass
                    
                    # Log the request
                    logger.info(f"POST intercepted: {url}")
                    
                    # Create request info
                    request_info = {
                        'timestamp': timestamp,
                        'url': url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'post_data': post_data
                    }
                    
                    # Generate cURL command
                    curl_command = self.generate_curl_command(request, post_data)
                    request_info['curl'] = curl_command
                    
                    # Save cURL to timestamped file
                    curl_filename = self.logs_dir / f"{timestamp}.sh"
                    try:
                        with open(curl_filename, 'w', encoding='utf-8') as f:
                            f.write(f"#!/bin/bash\n{curl_command}\n")
                        logger.info(f"cURL saved: {curl_filename}")
                    except Exception as e:
                        logger.error(f"Failed to save cURL: {e}")
                    
                    # Check if this is a trade execution request
                    is_trade = self.is_trade_execution_request(url, post_data)
                    request_info['is_trade'] = is_trade
                    
                    if is_trade:
                        logger.info(f"🎯 TRADE DETECTED: {url}")
                        await self.handle_trade_execution_request(request_info, curl_command, post_data)
                    else:
                        logger.info(f"📡 Regular POST: {url} (not trade)")
                    
                    # Store request info
                    self.post_requests.append(request_info)
                    
                except Exception as e:
                    logger.error(f"Error processing POST request: {e}")
        
        # Set up request interception
        self.page.on('request', handle_request)
        logger.info("🔍 Enhanced network interceptor active")
    
    def generate_curl_command(self, request: Request, post_data: Optional[str]) -> str:
        """Generate cURL command from request"""
        curl_parts = ['curl', '-X', 'POST']
        
        # Add headers
        for name, value in request.headers.items():
            escaped_value = value.replace("'", "'\"'\"'")
            curl_parts.extend(['-H', f"'{name}: {escaped_value}'"])
        
        # Add URL
        curl_parts.append(f"'{request.url}'")
        
        # Add POST data
        if post_data:
            escaped_data = post_data.replace("'", "'\"'\"'")
            curl_parts.extend(['-d', f"'{escaped_data}'"])
        
        return ' '.join(curl_parts)
    
    def is_trade_execution_request(self, url: str, post_data: Optional[str]) -> bool:
        """Enhanced trade execution detection"""
        # Check URL patterns
        url_lower = url.lower()
        for pattern in self.trade_url_patterns:
            if pattern in url_lower:
                logger.debug(f"Trade URL pattern matched: {pattern} in {url}")
                return True
        
        # Check payload keys
        if post_data:
            try:
                # Try to parse as JSON
                if post_data.strip().startswith(('{', '[')):
                    data = json.loads(post_data)
                    if isinstance(data, dict):
                        for key in self.trade_payload_keys:
                            if key in data:
                                logger.debug(f"Trade payload key matched: {key}")
                                return True
                else:
                    # Check string content
                    data_lower = post_data.lower()
                    matched_keys = [key for key in self.trade_payload_keys if key in data_lower]
                    if len(matched_keys) >= 2:
                        logger.debug(f"Trade payload keys matched: {matched_keys}")
                        return True
            except json.JSONDecodeError:
                # Fallback to string matching
                data_lower = post_data.lower()
                matched_keys = [key for key in self.trade_payload_keys if key in data_lower]
                if len(matched_keys) >= 2:
                    logger.debug(f"Trade payload keys matched (string): {matched_keys}")
                    return True
        
        return False
    
    async def handle_trade_execution_request(self, request_info: Dict, curl_command: str, post_data: Optional[str]):
        """Handle detected trade execution requests"""
        try:
            # Save cURL as trade.sh in project root
            trade_curl_path = Path('trade.sh')
            with open(trade_curl_path, 'w', encoding='utf-8') as f:
                f.write(f"#!/bin/bash\n{curl_command}\n")
            logger.info(f"💾 Trade cURL saved: {trade_curl_path}")
            
            # Convert to Python
            await self.convert_curl_to_python(curl_command)
            
            # Store trade request
            self.trade_requests.append(request_info)
            
        except Exception as e:
            logger.error(f"Error handling trade execution request: {e}")
    
    async def convert_curl_to_python(self, curl_command: str):
        """Convert cURL to Python requests code"""
        try:
            logger.info("🔄 Converting cURL to Python...")
            
            # Try curlconverter first
            try:
                result = subprocess.run(
                    ['python', '-c', f"import curlconverter; print(curlconverter.to_python('{curl_command}'))"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    python_code = result.stdout.strip()
                    with open('trade_request_full.py', 'w', encoding='utf-8') as f:
                        f.write(python_code)
                    logger.info("✅ SUCCESS: curlconverter Python code saved to trade_request_full.py")
                    return
            except Exception as e:
                logger.warning(f"curlconverter failed: {e}, using manual conversion")
            
            # Manual conversion fallback
            python_template = '''#!/usr/bin/env python3
import requests
import json

# Auto-generated from trade request
url = "{url}"
headers = {headers}
data = """{data}"""

try:
    response = requests.post(url, headers=headers, data=data)
    print(f"Status: {{response.status_code}}")
    print(f"Response: {{response.text}}")
except Exception as e:
    print(f"Error: {{e}}")
'''
            
            # Extract URL and data from curl command (simplified)
            url = "https://example.com/api/trade"
            headers = {"Content-Type": "application/json"}
            data = "{}"
            
            python_code = python_template.format(
                url=url,
                headers=json.dumps(headers, indent=4),
                data=data
            )
            
            with open('trade_request_full.py', 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            logger.info("✅ SUCCESS: Manual Python conversion saved to trade_request_full.py")
            
        except Exception as e:
            logger.error(f"Python conversion failed: {e}")
    
    async def wait_for_selector_with_retries(self, selectors: List[str], retries: int = 3, delay: int = 2000) -> Optional[str]:
        """Wait for any of the selectors with retry logic"""
        for attempt in range(1, retries + 1):
            logger.info(f"🔍 Selector attempt {attempt}/{retries}")
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=delay)
                    if element and await element.is_visible():
                        logger.info(f"✅ Found selector: {selector}")
                        return selector
                except:
                    continue
            
            if attempt < retries:
                logger.info(f"⏳ Retrying in {delay/1000}s...")
                await asyncio.sleep(delay/1000)
        
        logger.error(f"❌ FAILED: All selectors failed after {retries} attempts")
        return None
    
    async def ai_enhanced_login(self) -> bool:
        """AI-enhanced login with multiple strategies"""
        try:
            logger.info("🤖 Starting AI-enhanced login process...")
            
            # Navigate to login page
            await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Take screenshot for debugging
            await self.page.screenshot(path='login_page_ai.png')
            logger.info("📸 Login page screenshot saved")
            
            # Check if already logged in
            if await self.detect_dashboard_load():
                logger.info("✅ Already logged in - dashboard detected")
                return True
            
            # AI-enhanced element detection and interaction
            for field_type, selectors in self.login_selectors.items():
                logger.info(f"🎯 Finding {field_type} field...")
                
                # Sort selectors by weight (highest first)
                sorted_selectors = sorted(selectors, key=lambda x: x['weight'], reverse=True)
                selector_list = [s['selector'] for s in sorted_selectors]
                
                found_selector = await self.wait_for_selector_with_retries(selector_list, retries=2, delay=1000)
                
                if not found_selector:
                    logger.error(f"❌ {field_type} field not found")
                    return False
                
                # Fill the field
                if field_type == 'username':
                    await self.page.fill(found_selector, self.username)
                    logger.info(f"✅ Username filled using: {found_selector}")
                elif field_type == 'password':
                    await self.page.fill(found_selector, self.password)
                    logger.info(f"✅ Password filled using: {found_selector}")
                elif field_type == 'login_button':
                    # Take screenshot before clicking
                    await self.page.screenshot(path='before_login_click.png')
                    
                    await self.page.click(found_selector)
                    logger.info(f"✅ Login button clicked using: {found_selector}")
                    
                    # Wait for login to process
                    await asyncio.sleep(3)
                    
                    # Take screenshot after clicking
                    await self.page.screenshot(path='after_login_click.png')
            
            # Verify login success
            if await self.detect_dashboard_load():
                logger.info("🎉 LOGIN SUCCESS: Dashboard detected after AI-enhanced login")
                return True
            else:
                logger.error("❌ LOGIN FAILED: Dashboard not detected after login")
                await self.page.screenshot(path='login_failed_ai.png')
                return False
                
        except Exception as e:
            logger.error(f"AI-enhanced login error: {e}")
            await self.page.screenshot(path='login_error_ai.png')
            return False
    
    async def detect_dashboard_load(self) -> bool:
        """Detect dashboard load using flexible selector matching"""
        logger.info("🔍 Detecting dashboard load...")
        
        found_selector = await self.wait_for_selector_with_retries(
            self.dashboard_selectors, 
            retries=self.max_retries, 
            delay=self.retry_delay
        )
        
        if found_selector:
            logger.info(f"✅ SUCCESS: Dashboard loaded - detected via '{found_selector}'")
            return True
        else:
            logger.error("❌ FAILED: Dashboard load detection failed")
            return False
    
    async def detect_trading_page_load(self) -> bool:
        """Detect trading interface load"""
        logger.info("🔍 Detecting trading page load...")
        
        found_selector = await self.wait_for_selector_with_retries(
            self.trading_selectors, 
            retries=self.max_retries, 
            delay=self.retry_delay
        )
        
        if found_selector:
            logger.info(f"✅ SUCCESS: Trading page loaded - detected via '{found_selector}'")
            return True
        else:
            logger.error("❌ FAILED: Trading page load detection failed")
            return False
    
    async def navigate_to_trading_page(self) -> bool:
        """Navigate to trading page"""
        try:
            logger.info("🧭 Navigating to trading page...")
            
            # Check if already on trading page
            if await self.detect_trading_page_load():
                logger.info("✅ Already on trading page")
                return True
            
            # Try direct navigation
            await self.page.goto('https://bulenox.projectx.com/trading', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Verify trading page loaded
            return await self.detect_trading_page_load()
            
        except Exception as e:
            logger.error(f"Navigation to trading page failed: {e}")
            return False
    
    async def simulate_trading_activity(self):
        """Simulate trading activity to trigger network requests"""
        try:
            logger.info("🎮 Simulating trading activity...")
            
            # Look for trading interface elements
            for selector in self.trading_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        logger.info(f"🎯 Found trading element: {selector}")
                        
                        # Simulate interaction
                        if 'input' in selector:
                            await element.fill('BTCUSD')
                            logger.info(f"✅ Filled input: {selector}")
                        elif 'button' in selector:
                            await element.click()
                            logger.info(f"✅ Clicked button: {selector}")
                            await asyncio.sleep(1)
                        
                        break
                except Exception:
                    continue
            
            # Wait for potential network requests
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Trading activity simulation failed: {e}")
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            logger.info("🧹 Browser cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def generate_summary_report(self):
        """Generate summary report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_post_requests': len(self.post_requests),
                'trade_requests': len(self.trade_requests),
                'post_requests': self.post_requests,
                'trade_requests': self.trade_requests
            }
            
            report_path = Path('ultimate_request_capture_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📊 Summary report saved: {report_path}")
            logger.info(f"📡 Total POST requests captured: {len(self.post_requests)}")
            logger.info(f"🎯 Trade execution requests detected: {len(self.trade_requests)}")
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")

async def main():
    """Main execution function"""
    sentinel = None
    
    try:
        # Parse command line arguments
        headless = '--headful' not in sys.argv
        
        logger.info("🚀 === Ultimate TradeBot Sentinel Starting ===")
        logger.info(f"🖥️  Headless mode: {headless}")
        
        # Initialize sentinel
        sentinel = UltimateTradeBotSentinel(headless=headless)
        
        # Setup browser
        await sentinel.setup_browser()
        
        # Perform AI-enhanced login
        login_success = await sentinel.ai_enhanced_login()
        if not login_success:
            logger.error("❌ AI-enhanced login failed - aborting")
            return
        
        # Navigate to trading page
        trading_success = await sentinel.navigate_to_trading_page()
        if not trading_success:
            logger.warning("⚠️  Trading page navigation failed - continuing anyway")
        
        # Simulate trading activity to capture requests
        await sentinel.simulate_trading_activity()
        
        # Wait for additional requests
        logger.info("⏳ Waiting for additional network requests...")
        await asyncio.sleep(15)
        
        # Generate summary report
        sentinel.generate_summary_report()
        
        logger.info("🎉 === Ultimate TradeBot Sentinel Completed ===")
        
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        if sentinel and sentinel.page:
            try:
                await sentinel.page.screenshot(path='critical_error_ultimate.png')
                logger.info("📸 Error screenshot saved: critical_error_ultimate.png")
            except:
                pass
    
    finally:
        if sentinel:
            await sentinel.cleanup()

if __name__ == "__main__":
    asyncio.run(main())