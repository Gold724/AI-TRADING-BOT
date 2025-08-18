#!/usr/bin/env python3
"""
TradeBot Sentinel - Advanced Bulenox ProjectX Trading Platform Automation

This script automates:
1. Secure login using environment variables
2. Time Sync Warning modal detection and handling
3. Dashboard confirmation with multiple selector fallbacks
4. Trading page navigation and readiness confirmation
5. Trade order placement with robust selector fallbacks
6. Network request interception for trade execution detection
7. cURL command generation and Python requests conversion
8. Screenshot capture on critical failures
9. Comprehensive logging and error handling

Author: TradeBot Sentinel AI
Version: 2.0
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
        logging.FileHandler('tradebot_sentinel.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradeBotSentinel:
    """Advanced automation agent for Bulenox ProjectX trading platform"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "https://bulenox.projectx.com"  # Updated to Bulenox ProjectX trading URL
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.trade_requests: List[Dict] = []
        self.screenshot_counter = 0
        
        # Environment variables
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
        
        # Selector configurations with fallbacks
        self.selectors = {
            'login': {
                'username': [
                    'input[name="username"]',
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
            'time_sync_warning': [
                '.time-sync-warning',
                '.modal:has-text("Time Sync")',
                '.alert:has-text("Time Sync")',
                '[data-testid="time-sync-modal"]',
                '.warning-modal:has-text("sync")',
                'div:has-text("Time Sync Warning")'
            ],
            'dashboard': [
                '.dashboard',
                '.main-dashboard',
                '[data-testid="dashboard"]',
                '.trading-dashboard',
                '.user-dashboard',
                'main[role="main"]',
                '.content-main',
                '#dashboard'
            ],
            'trading_page': {
                'nav_link': [
                    'a:has-text("Trading")',
                    'a:has-text("Trade")',
                    'nav a[href*="trading"]',
                    'nav a[href*="trade"]',
                    '.nav-trading',
                    '.menu-trading'
                ],
                'interface': [
                    '.trading-interface',
                    '.trade-panel',
                    '[data-testid="trading-interface"]',
                    '.order-panel',
                    '.trading-form',
                    '#trading-interface'
                ]
            },
            'order_placement': {
                'order_tab': [
                    'button:has-text("ORDER")',
                    '.order-tab',
                    '[data-testid="order-tab"]',
                    'tab:has-text("ORDER")',
                    '.tab-order'
                ],
                'dom_tab': [
                    'button:has-text("DOM")',
                    '.dom-tab',
                    '[data-testid="dom-tab"]',
                    'tab:has-text("DOM")',
                    '.tab-dom'
                ],
                'generic': [
                    '.order-form',
                    '.trade-form',
                    'form[data-testid="order-form"]',
                    '.buy-sell-buttons',
                    '.order-buttons'
                ]
            }
        }
    
    async def setup_browser(self) -> None:
        """Initialize browser with network interception"""
        logger.info("🚀 Initializing TradeBot Sentinel...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await self.context.new_page()
        
        # Setup network interception
        await self.setup_network_interception()
        
        logger.info("✅ Browser initialized successfully")
    
    async def setup_network_interception(self) -> None:
        """Setup network request interception for trade detection"""
        logger.info("🔍 Setting up network interception...")
        
        async def handle_request(request):
            if request.method == 'POST':
                logger.info(f"📡 POST Request intercepted: {request.url}")
                
                # Check if this might be a trade execution request
                if await self.is_trade_request(request):
                    await self.capture_trade_request(request)
        
        self.page.on('request', handle_request)
        logger.info("✅ Network interception setup complete")
    
    async def is_trade_request(self, request) -> bool:
        """Detect if a request is a trade execution request"""
        try:
            # Check URL for trading-related endpoints
            url_keywords = ['trade', 'order', 'buy', 'sell', 'execute', 'position']
            if any(keyword in request.url.lower() for keyword in url_keywords):
                return True
            
            # Check POST data for trading keywords
            post_data = request.post_data
            if post_data:
                post_data_lower = post_data.lower()
                trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell', 'quantity', 'side']
                if any(keyword in post_data_lower for keyword in trade_keywords):
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"⚠️ Error checking trade request: {e}")
            return False
    
    async def capture_trade_request(self, request) -> None:
        """Capture and save trade execution request as cURL"""
        try:
            logger.info("🎯 Trade execution request detected!")
            
            # Build cURL command
            curl_command = self.build_curl_command(request)
            
            # Save to trade.sh
            with open('trade.sh', 'w') as f:
                f.write(curl_command)
            
            logger.info("💾 cURL command saved to trade.sh")
            
            # Convert to Python requests
            await self.convert_curl_to_python(curl_command)
            
            # Store request info
            self.trade_requests.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Error capturing trade request: {e}")
    
    def build_curl_command(self, request) -> str:
        """Build cURL command from request"""
        curl_parts = [f'curl -X {request.method}']
        
        # Add headers
        for name, value in request.headers.items():
            curl_parts.append(f'-H "{name}: {value}"')
        
        # Add POST data
        if request.post_data:
            curl_parts.append(f'-d \'{request.post_data}\'')
        
        # Add URL
        curl_parts.append(f'"{request.url}"')
        
        return ' '.join(curl_parts)
    
    async def convert_curl_to_python(self, curl_command: str) -> None:
        """Convert cURL command to Python requests code"""
        try:
            # Try to use curlconverter if available
            import subprocess
            
            # Save curl command to temp file
            with open('temp_curl.txt', 'w') as f:
                f.write(curl_command)
            
            # Convert using curlconverter
            result = subprocess.run(
                ['python', '-m', 'curlconverter', '--language', 'python', 'temp_curl.txt'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                python_code = result.stdout
            else:
                # Fallback: manual conversion
                python_code = self.manual_curl_to_python(curl_command)
            
            # Save Python code
            with open('trade_request_full.py', 'w') as f:
                f.write(python_code)
            
            logger.info("🐍 Python requests code saved to trade_request_full.py")
            
            # Cleanup
            if os.path.exists('temp_curl.txt'):
                os.remove('temp_curl.txt')
                
        except Exception as e:
            logger.warning(f"⚠️ curlconverter not available, using manual conversion: {e}")
            python_code = self.manual_curl_to_python(curl_command)
            
            with open('trade_request_full.py', 'w') as f:
                f.write(python_code)
            
            logger.info("🐍 Python requests code saved to trade_request_full.py (manual conversion)")
    
    def manual_curl_to_python(self, curl_command: str) -> str:
        """Manual conversion of cURL to Python requests"""
        python_template = '''import requests
import json

# Auto-generated from cURL command
# Original cURL: {curl_command}

url = "{url}"

headers = {{
{headers}
}}

{data_section}

response = requests.{method}(url, headers=headers{data_param})

print(f"Status Code: {{response.status_code}}")
print(f"Response: {{response.text}}")
'''
        
        # Extract URL (simplified)
        url_match = curl_command.split('"')[-2] if '"' in curl_command else "https://example.com"
        
        # Extract method
        method = 'post' if '-X POST' in curl_command else 'get'
        
        # Basic headers
        headers_str = '    "Content-Type": "application/json",\n    "User-Agent": "TradeBot-Sentinel/2.0"'
        
        # Data section
        if '-d' in curl_command:
            data_section = 'data = {"placeholder": "data"}  # Replace with actual data'
            data_param = ', json=data'
        else:
            data_section = '# No data for this request'
            data_param = ''
        
        return python_template.format(
            curl_command=curl_command.replace('\n', ' '),
            url=url_match,
            method=method,
            headers=headers_str,
            data_section=data_section,
            data_param=data_param
        )
    
    async def take_screenshot(self, name: str = "error") -> str:
        """Take screenshot for debugging"""
        try:
            self.screenshot_counter += 1
            filename = f"screenshot_{name}_{self.screenshot_counter}_{int(time.time())}.png"
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"📸 Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Failed to take screenshot: {e}")
            return ""
    
    async def wait_for_element_with_fallbacks(self, selectors: List[str], timeout: int = 10000, retries: int = 3) -> Optional[str]:
        """Wait for element using fallback selectors with retries"""
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
                logger.info(f"🔄 Retry {attempt + 1}/{retries} in 2 seconds...")
                await asyncio.sleep(2)
        
        logger.error(f"❌ No element found with any selector after {retries} attempts")
        return None
    
    async def login(self) -> bool:
        """Perform secure login with robust error handling"""
        try:
            logger.info("🔐 Starting login process...")
            
            # Navigate to login page
            login_url = f"{self.base_url}/login"
            logger.info(f"🌐 Navigating to: {login_url}")
            await self.page.goto(login_url, wait_until="networkidle")
            
            # Wait for username field
            username_selector = await self.wait_for_element_with_fallbacks(self.selectors['login']['username'])
            if not username_selector:
                await self.take_screenshot("login_username_not_found")
                return False
            
            # Fill username
            await self.page.fill(username_selector, self.username)
            logger.info("✅ Username filled")
            
            # Wait for password field
            password_selector = await self.wait_for_element_with_fallbacks(self.selectors['login']['password'])
            if not password_selector:
                await self.take_screenshot("login_password_not_found")
                return False
            
            # Fill password
            await self.page.fill(password_selector, self.password)
            logger.info("✅ Password filled")
            
            # Submit login
            submit_selector = await self.wait_for_element_with_fallbacks(self.selectors['login']['submit'])
            if not submit_selector:
                await self.take_screenshot("login_submit_not_found")
                return False
            
            await self.page.click(submit_selector)
            logger.info("✅ Login form submitted")
            
            # Check for Time Sync Warning modal
            await self.handle_time_sync_warning()
            
            # Confirm login success
            return await self.confirm_login_success()
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            await self.take_screenshot("login_error")
            return False
    
    async def handle_time_sync_warning(self) -> None:
        """Detect and handle Time Sync Warning modal"""
        try:
            logger.info("🕐 Checking for Time Sync Warning modal...")
            
            time_sync_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['time_sync_warning'], 
                timeout=5000, 
                retries=1
            )
            
            if time_sync_selector:
                logger.info("⚠️ Time Sync Warning detected!")
                
                # Try to find and click dismiss/OK button
                dismiss_selectors = [
                    'button:has-text("OK")',
                    'button:has-text("Dismiss")',
                    'button:has-text("Close")',
                    '.modal-close',
                    '.btn-close',
                    '[data-dismiss="modal"]'
                ]
                
                dismiss_selector = await self.wait_for_element_with_fallbacks(dismiss_selectors, timeout=3000)
                if dismiss_selector:
                    await self.page.click(dismiss_selector)
                    logger.info("✅ Time Sync Warning dismissed")
                else:
                    logger.warning("⚠️ Could not find dismiss button for Time Sync Warning")
            else:
                logger.info("✅ No Time Sync Warning detected")
                
        except Exception as e:
            logger.warning(f"⚠️ Error handling Time Sync Warning: {e}")
    
    async def confirm_login_success(self) -> bool:
        """Confirm successful login by waiting for dashboard"""
        try:
            logger.info("🔍 Confirming login success...")
            
            dashboard_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['dashboard'], 
                timeout=15000, 
                retries=3
            )
            
            if dashboard_selector:
                logger.info("✅ Login successful - Dashboard loaded")
                return True
            else:
                logger.error("❌ Login failed - Dashboard not found")
                await self.take_screenshot("login_failed_no_dashboard")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error confirming login: {e}")
            await self.take_screenshot("login_confirmation_error")
            return False
    
    async def navigate_to_trading_page(self) -> bool:
        """Navigate to trading page and confirm readiness"""
        try:
            logger.info("📈 Navigating to trading page...")
            
            # Find trading navigation link
            nav_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['trading_page']['nav_link']
            )
            
            if not nav_selector:
                logger.warning("⚠️ Trading navigation link not found, assuming already on trading page")
            else:
                await self.page.click(nav_selector)
                logger.info("✅ Trading navigation clicked")
                await asyncio.sleep(2)  # Allow page to load
            
            # Confirm trading interface is ready
            interface_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['trading_page']['interface'],
                timeout=15000,
                retries=3
            )
            
            if interface_selector:
                logger.info("✅ Trading interface ready")
                return True
            else:
                logger.error("❌ Trading interface not found")
                await self.take_screenshot("trading_interface_not_found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error navigating to trading page: {e}")
            await self.take_screenshot("trading_navigation_error")
            return False
    
    async def place_trade_order(self) -> bool:
        """Attempt to place a trade order with fallback selectors"""
        try:
            logger.info("💰 Attempting to place trade order...")
            
            # Try ORDER tab first
            order_tab_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['order_placement']['order_tab'],
                timeout=5000,
                retries=1
            )
            
            if order_tab_selector:
                await self.page.click(order_tab_selector)
                logger.info("✅ ORDER tab selected")
                await asyncio.sleep(1)
            else:
                logger.info("ℹ️ ORDER tab not found, trying DOM tab...")
                
                # Try DOM tab as fallback
                dom_tab_selector = await self.wait_for_element_with_fallbacks(
                    self.selectors['order_placement']['dom_tab'],
                    timeout=5000,
                    retries=1
                )
                
                if dom_tab_selector:
                    await self.page.click(dom_tab_selector)
                    logger.info("✅ DOM tab selected")
                    await asyncio.sleep(1)
                else:
                    logger.info("ℹ️ DOM tab not found, using generic selectors...")
            
            # Look for generic order placement elements
            generic_selector = await self.wait_for_element_with_fallbacks(
                self.selectors['order_placement']['generic'],
                timeout=10000,
                retries=2
            )
            
            if generic_selector:
                logger.info("✅ Order placement interface found")
                
                # Simulate order placement (click on buy/sell area)
                # Note: Actual implementation would depend on specific UI
                await self.page.click(generic_selector)
                logger.info("✅ Trade order placement attempted")
                
                # Wait a moment for any network requests
                await asyncio.sleep(3)
                
                return True
            else:
                logger.error("❌ No order placement interface found")
                await self.take_screenshot("order_placement_not_found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error placing trade order: {e}")
            await self.take_screenshot("order_placement_error")
            return False
    
    async def run_automation(self) -> bool:
        """Main automation workflow"""
        try:
            logger.info("🤖 Starting TradeBot Sentinel automation...")
            
            # Setup browser
            await self.setup_browser()
            
            # Login
            if not await self.login():
                logger.error("❌ Login failed, aborting automation")
                return False
            
            # Navigate to trading page
            if not await self.navigate_to_trading_page():
                logger.error("❌ Failed to navigate to trading page, aborting automation")
                return False
            
            # Place trade order
            if not await self.place_trade_order():
                logger.error("❌ Failed to place trade order")
                return False
            
            logger.info("✅ TradeBot Sentinel automation completed successfully!")
            
            # Summary
            logger.info(f"📊 Summary:")
            logger.info(f"   - Trade requests captured: {len(self.trade_requests)}")
            logger.info(f"   - cURL saved: {'✅' if os.path.exists('trade.sh') else '❌'}")
            logger.info(f"   - Python code saved: {'✅' if os.path.exists('trade_request_full.py') else '❌'}")
            
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
            if self.browser:
                await self.browser.close()
                logger.info("✅ Browser closed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


async def main():
    """Main entry point"""
    # Check for headless mode override
    headless = '--headful' not in sys.argv
    
    sentinel = TradeBotSentinel(headless=headless)
    success = await sentinel.run_automation()
    
    if success:
        print("\n🎉 TradeBot Sentinel completed successfully!")
        print("📁 Check the following files:")
        print("   - trade.sh (cURL command)")
        print("   - trade_request_full.py (Python requests code)")
        print("   - tradebot_sentinel.log (detailed logs)")
        sys.exit(0)
    else:
        print("\n❌ TradeBot Sentinel failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())