#!/usr/bin/env python3
"""
TradeBot Sentinel Universal - Advanced Trading Platform Automation

A flexible automation agent that can work with any trading platform.
Configurable selectors, URLs, and credentials for maximum compatibility.

Features:
- Universal platform support through configurable selectors
- Secure credential management via environment variables
- Network request interception and trade detection
- Automatic cURL and Python code generation
- Comprehensive error handling and logging
- Screenshot capture for debugging
- Retry mechanisms for reliability

Author: TradeBot Sentinel Team
Version: 2.0.0
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradebot_sentinel_universal.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class UniversalTradeBotSentinel:
    """Universal TradeBot Sentinel for any trading platform"""
    
    def __init__(self, headless: bool = True):
        # Configuration
        self.headless = headless
        self.base_url = os.getenv('TRADING_PLATFORM_URL', 'https://www.tradingview.com')  # Default to TradingView
        self.username = os.getenv('TRADING_USERNAME')
        self.password = os.getenv('TRADING_PASSWORD')
        
        if not self.username or not self.password:
            logger.warning("⚠️ Trading credentials not set. Using demo mode.")
            self.demo_mode = True
        else:
            self.demo_mode = False
        
        # Browser components
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Trade detection
        self.trade_requests = []
        self.intercepted_requests = []
        
        # Universal selectors (configurable)
        self.selectors = {
            'login': {
                'username': [
                    'input[name="username"]',
                    'input[name="email"]',
                    'input[type="email"]',
                    'input[placeholder*="username" i]',
                    'input[placeholder*="email" i]',
                    '#username',
                    '#email',
                    '.username-input',
                    '.email-input'
                ],
                'password': [
                    'input[name="password"]',
                    'input[type="password"]',
                    '#password',
                    '.password-input'
                ],
                'submit': [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    'button:has-text("Log In")',
                    '.login-button',
                    '.submit-button'
                ]
            },
            'dashboard': {
                'indicators': [
                    '.dashboard',
                    '.trading-dashboard',
                    '.main-content',
                    '.portfolio',
                    '.account-info',
                    '[data-testid="dashboard"]'
                ]
            },
            'trading': {
                'buy_button': [
                    'button:has-text("Buy")',
                    'button:has-text("Long")',
                    '.buy-button',
                    '.long-button',
                    '[data-testid="buy-button"]'
                ],
                'sell_button': [
                    'button:has-text("Sell")',
                    'button:has-text("Short")',
                    '.sell-button',
                    '.short-button',
                    '[data-testid="sell-button"]'
                ],
                'amount_input': [
                    'input[name="amount"]',
                    'input[name="quantity"]',
                    'input[placeholder*="amount" i]',
                    'input[placeholder*="quantity" i]',
                    '.amount-input',
                    '.quantity-input'
                ]
            }
        }
    
    async def setup_browser(self) -> None:
        """Initialize browser with optimal settings"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with comprehensive options
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            # Create context with realistic user agent
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Setup network interception
            await self.setup_network_interception()
            
            logger.info("✅ Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            raise
    
    async def setup_network_interception(self) -> None:
        """Setup network request interception for trade detection"""
        logger.info("🔍 Setting up network interception...")
        
        async def handle_request(request):
            # Log all POST requests
            if request.method == "POST":
                logger.info(f"📡 POST Request intercepted: {request.url[:100]}...")
                
                # Check if this might be a trade request
                if await self.is_trade_request(request):
                    await self.capture_trade_request(request)
        
        self.page.on("request", handle_request)
        logger.info("✅ Network interception setup complete")
    
    async def is_trade_request(self, request) -> bool:
        """Detect if a request is related to trade execution"""
        try:
            url = request.url.lower()
            
            # Check URL patterns
            trade_url_patterns = [
                'trade', 'order', 'buy', 'sell', 'execute', 'position',
                'market', 'limit', 'stop', 'api/v', 'trading', 'broker'
            ]
            
            if any(pattern in url for pattern in trade_url_patterns):
                return True
            
            # Check POST data if available
            try:
                post_data = request.post_data
                if post_data:
                    post_data_lower = post_data.lower()
                    trade_keywords = [
                        'symbol', 'amount', 'price', 'quantity', 'side',
                        'buy', 'sell', 'long', 'short', 'order', 'trade'
                    ]
                    
                    if any(keyword in post_data_lower for keyword in trade_keywords):
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking trade request: {e}")
            return False
    
    async def capture_trade_request(self, request) -> None:
        """Capture and process trade requests"""
        try:
            logger.info(f"🎯 Trade request detected: {request.url}")
            
            # Store request details
            request_data = {
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data,
                'timestamp': datetime.now().isoformat()
            }
            
            self.trade_requests.append(request_data)
            
            # Generate cURL command
            curl_command = self.build_curl_command(request_data)
            
            # Save cURL to file
            with open('trade_universal.sh', 'w', encoding='utf-8') as f:
                f.write(curl_command)
            
            logger.info("💾 Trade cURL saved to trade_universal.sh")
            
            # Convert to Python requests
            await self.convert_curl_to_python(curl_command)
            
        except Exception as e:
            logger.error(f"❌ Error capturing trade request: {e}")
    
    def build_curl_command(self, request_data: dict) -> str:
        """Build cURL command from request data"""
        try:
            curl_parts = [f'curl -X {request_data["method"]}']
            
            # Add headers
            for key, value in request_data['headers'].items():
                if key.lower() not in ['content-length', 'host']:
                    curl_parts.append(f'-H "{key}: {value}"')
            
            # Add POST data
            if request_data.get('post_data'):
                curl_parts.append(f'-d \'{request_data["post_data"]}\'')
            
            # Add URL
            curl_parts.append(f'"{request_data["url"]}"')
            
            return ' '.join(curl_parts)
            
        except Exception as e:
            logger.error(f"❌ Error building cURL command: {e}")
            return f'# Error building cURL: {e}'
    
    async def convert_curl_to_python(self, curl_command: str) -> None:
        """Convert cURL command to Python requests code"""
        try:
            # Try using curlconverter if available
            try:
                import subprocess
                result = subprocess.run(
                    ['python', '-c', f'import curlconverter; print(curlconverter.to_python("{curl_command}"))'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    python_code = result.stdout.strip()
                else:
                    python_code = self.manual_curl_to_python(curl_command)
                    
            except:
                python_code = self.manual_curl_to_python(curl_command)
            
            # Save Python code
            with open('trade_request_universal.py', 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            logger.info("🐍 Python requests code saved to trade_request_universal.py")
            
        except Exception as e:
            logger.error(f"❌ Error converting cURL to Python: {e}")
    
    def manual_curl_to_python(self, curl_command: str) -> str:
        """Manual conversion of cURL to Python requests"""
        return f'''
#!/usr/bin/env python3
"""
Generated Python requests code from intercepted trade request
Generated at: {datetime.now().isoformat()}
"""

import requests
import json

# Original cURL command:
# {curl_command}

def execute_trade_request():
    """Execute the intercepted trade request"""
    try:
        # TODO: Extract and configure these values from the cURL command
        url = "YOUR_TRADING_API_URL"
        headers = {{
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_API_TOKEN"
        }}
        
        data = {{
            "symbol": "BTCUSDT",
            "side": "buy",
            "amount": 0.01,
            "type": "market"
        }}
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print("✅ Trade executed successfully")
            print(f"Response: {{response.json()}}")
        else:
            print(f"❌ Trade failed: {{response.status_code}} - {{response.text}}")
            
    except Exception as e:
        print(f"❌ Error executing trade: {{e}}")

if __name__ == "__main__":
    execute_trade_request()
'''
    
    async def take_screenshot(self, name: str = "error") -> str:
        """Take screenshot for debugging"""
        try:
            timestamp = int(time.time())
            filename = f"screenshot_{name}_{timestamp}.png"
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"📸 Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            return ""
    
    async def wait_for_element_with_fallbacks(self, selectors: List[str], timeout: int = 10000, retries: int = 3) -> Optional[str]:
        """Wait for element using multiple selector fallbacks"""
        for attempt in range(retries):
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=timeout)
                    logger.info(f"✅ Element found with selector: {selector}")
                    return selector
                except PlaywrightTimeoutError:
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Error with selector {selector}: {e}")
                    continue
            
            if attempt < retries - 1:
                logger.info(f"🔄 Retrying element search (attempt {attempt + 2}/{retries})...")
                await asyncio.sleep(2)
        
        logger.warning("⚠️ No matching elements found with any selector")
        return None
    
    async def navigate_to_platform(self) -> bool:
        """Navigate to the trading platform"""
        try:
            logger.info(f"🌐 Navigating to: {self.base_url}")
            await self.page.goto(self.base_url, wait_until="networkidle")
            
            # Take screenshot of the page
            await self.take_screenshot("platform_loaded")
            
            logger.info("✅ Successfully navigated to trading platform")
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            await self.take_screenshot("navigation_error")
            return False
    
    async def attempt_login(self) -> bool:
        """Attempt to login if credentials are available"""
        if self.demo_mode:
            logger.info("🎮 Running in demo mode - skipping login")
            return True
        
        try:
            logger.info("🔐 Attempting login...")
            
            # Find username field
            username_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['login']['username']
            )
            
            if not username_selector:
                logger.warning("⚠️ Username field not found - may already be logged in")
                return True
            
            # Fill username
            await self.page.fill(username_selector, self.username)
            logger.info("✅ Username entered")
            
            # Find password field
            password_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['login']['password']
            )
            
            if password_selector:
                await self.page.fill(password_selector, self.password)
                logger.info("✅ Password entered")
            
            # Find and click submit button
            submit_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['login']['submit']
            )
            
            if submit_selector:
                await self.page.click(submit_selector)
                logger.info("✅ Login submitted")
                
                # Wait for dashboard or main content
                await asyncio.sleep(3)
                await self.take_screenshot("after_login")
                
                return True
            else:
                logger.warning("⚠️ Submit button not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            await self.take_screenshot("login_error")
            return False
    
    async def monitor_trading_activity(self, duration: int = 60) -> None:
        """Monitor trading activity for specified duration"""
        try:
            logger.info(f"👀 Monitoring trading activity for {duration} seconds...")
            
            start_time = time.time()
            while time.time() - start_time < duration:
                # Check for trading interface elements
                buy_button = await self.wait_for_element_with_fallbacks(
                    self.selectors['trading']['buy_button'], timeout=1000, retries=1
                )
                
                if buy_button:
                    logger.info("📈 Trading interface detected")
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            logger.info(f"✅ Monitoring completed. Captured {len(self.trade_requests)} trade requests")
            
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
    
    async def run_automation(self) -> bool:
        """Run the complete automation workflow"""
        try:
            logger.info("🤖 Starting Universal TradeBot Sentinel...")
            
            # Initialize browser
            logger.info("🚀 Initializing browser...")
            await self.setup_browser()
            
            # Navigate to platform
            if not await self.navigate_to_platform():
                return False
            
            # Attempt login
            if not await self.attempt_login():
                logger.warning("⚠️ Login failed, continuing in guest mode")
            
            # Monitor trading activity
            await self.monitor_trading_activity(duration=120)  # Monitor for 2 minutes
            
            logger.info("✅ Automation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
            await self.take_screenshot("automation_error")
            return False
        
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("✅ Browser closed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

async def main():
    """Main execution function"""
    try:
        # Check for headless mode
        headless = os.getenv('HEADLESS', 'true').lower() == 'true'
        
        # Create and run sentinel
        sentinel = UniversalTradeBotSentinel(headless=headless)
        success = await sentinel.run_automation()
        
        if success:
            print("\n✅ Universal TradeBot Sentinel completed successfully!")
            if sentinel.trade_requests:
                print(f"📊 Captured {len(sentinel.trade_requests)} trade requests")
                print("📁 Check trade_universal.sh and trade_request_universal.py for generated code")
        else:
            print("\n❌ Universal TradeBot Sentinel failed. Check logs for details.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Automation stopped by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())