#!/usr/bin/env python3
"""
TradeBot Sentinel - Bulenox ProjectX Trading Platform Automation
Expert automation agent for secure login, trade execution, and request interception.
"""

import asyncio
import os
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradebot_sentinel.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradeBotSentinel:
    """TradeBot Sentinel - Expert automation for Bulenox ProjectX trading platform"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.trade_requests = []
        self.screenshots_dir = Path('screenshots')
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Load credentials from environment
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
    
    async def setup_browser(self):
        """Initialize browser with network interception"""
        logger.info("Setting up browser with network interception...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await self.context.new_page()
        
        # Setup network interception
        await self.setup_network_interception()
        
        logger.info("Browser setup completed successfully")
    
    async def setup_network_interception(self):
        """Setup network request interception to capture trade requests"""
        logger.info("Setting up network request interception...")
        
        async def handle_request(request):
            if request.method == 'POST':
                logger.info(f"POST request intercepted: {request.url}")
                
                # Get request data
                try:
                    post_data = request.post_data
                    if post_data:
                        # Check if this looks like a trade request
                        if self.is_trade_request(request.url, post_data):
                            logger.info("Trade execution request detected!")
                            await self.save_trade_request(request)
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
        
        self.page.on('request', handle_request)
    
    def is_trade_request(self, url, post_data):
        """Detect if a request is a trade execution request"""
        trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell']
        
        # Check URL
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in trade_keywords):
            return True
        
        # Check POST data
        if post_data:
            data_lower = post_data.lower()
            if any(keyword in data_lower for keyword in trade_keywords):
                return True
        
        return False
    
    async def save_trade_request(self, request):
        """Save trade request as cURL command and convert to Python"""
        try:
            curl_command = await self.convert_to_curl(request)
            
            # Save cURL command
            with open('trade.sh', 'w') as f:
                f.write(curl_command)
            
            logger.info("Trade request saved to trade.sh")
            
            # Convert to Python requests code
            await self.convert_curl_to_python()
            
        except Exception as e:
            logger.error(f"Error saving trade request: {e}")
    
    async def convert_to_curl(self, request):
        """Convert Playwright request to cURL command"""
        curl_parts = ['curl']
        
        # Add method
        curl_parts.append(f"-X {request.method}")
        
        # Add headers
        headers = await request.all_headers()
        for name, value in headers.items():
            curl_parts.append(f"-H '{name}: {value}'")
        
        # Add URL
        curl_parts.append(f"'{request.url}'")
        
        # Add POST data if present
        post_data = request.post_data
        if post_data:
            # Escape single quotes in data
            data_str = post_data.replace("'", "'\"'\"'")
            curl_parts.append(f"-d '{data_str}'")
        
        return ' \\
  '.join(curl_parts)
    
    async def convert_curl_to_python(self):
        """Convert cURL command to Python requests code using curlconverter"""
        try:
            # Check if curlconverter is installed
            result = subprocess.run(['curlconverter', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("curlconverter not found. Please install it: pip install curlconverter")
                return
            
            # Convert cURL to Python
            with open('trade.sh', 'r') as f:
                curl_command = f.read()
            
            result = subprocess.run(['curlconverter', '--language', 'python'], 
                                  input=curl_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                with open('trade_request_full.py', 'w') as f:
                    f.write(result.stdout)
                logger.info("Python requests code saved to trade_request_full.py")
            else:
                logger.error(f"Error converting cURL to Python: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error in cURL to Python conversion: {e}")
    
    async def take_screenshot(self, filename):
        """Take screenshot for debugging"""
        try:
            screenshot_path = self.screenshots_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(screenshot_path))
            logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    async def wait_for_element_with_retry(self, selectors, timeout=10000, retries=3):
        """Wait for element with multiple selectors and retry logic"""
        for attempt in range(retries):
            for selector in selectors:
                try:
                    logger.info(f"Attempt {attempt + 1}: Waiting for selector: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        logger.info(f"Element found with selector: {selector}")
                        return element
                except Exception as e:
                    logger.warning(f"Selector {selector} failed: {e}")
                    continue
            
            if attempt < retries - 1:
                logger.info(f"Retrying in 2 seconds... (attempt {attempt + 1}/{retries})")
                await asyncio.sleep(2)
        
        raise Exception(f"Failed to find element after {retries} attempts")
    
    async def login(self):
        """Secure login to Bulenox ProjectX platform"""
        logger.info("Starting login process...")
        
        try:
            # Navigate to login page
            await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
            await self.take_screenshot('login_page')
            
            # Handle potential Time Sync Warning modal
            try:
                time_sync_selectors = [
                    '[data-testid="time-sync-warning"]',
                    '.time-sync-modal',
                    '.modal-time-sync',
                    'div:has-text("Time Sync Warning")',
                    'button:has-text("Continue")'
                ]
                
                time_sync_element = await self.wait_for_element_with_retry(
                    time_sync_selectors, timeout=5000, retries=1
                )
                
                if time_sync_element:
                    logger.info("Time Sync Warning detected, handling...")
                    continue_button = await self.page.query_selector('button:has-text("Continue")')
                    if continue_button:
                        await continue_button.click()
                        await asyncio.sleep(2)
                        
            except Exception:
                logger.info("No Time Sync Warning detected, proceeding...")
            
            # Login form selectors with fallbacks
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
                '#username',
                '#email'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="password" i]',
                '#password'
            ]
            
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'input[type="submit"]',
                '.login-button',
                '#login-button'
            ]
            
            # Fill username
            username_field = await self.wait_for_element_with_retry(username_selectors)
            await username_field.fill(self.username)
            logger.info("Username filled successfully")
            
            # Fill password
            password_field = await self.wait_for_element_with_retry(password_selectors)
            await password_field.fill(self.password)
            logger.info("Password filled successfully")
            
            await self.take_screenshot('before_login')
            
            # Click login button
            login_button = await self.wait_for_element_with_retry(login_button_selectors)
            await login_button.click()
            logger.info("Login button clicked")
            
            # Wait for login success
            dashboard_selectors = [
                '[data-testid="dashboard"]',
                '.dashboard',
                '.main-dashboard',
                'div:has-text("Dashboard")',
                'div:has-text("Welcome")',
                '.user-menu',
                '.trading-interface'
            ]
            
            await self.wait_for_element_with_retry(dashboard_selectors, timeout=15000)
            await self.take_screenshot('after_login')
            logger.info("Login successful!")
            
        except Exception as e:
            await self.take_screenshot('login_failure')
            logger.error(f"Login failed: {e}")
            raise
    
    async def navigate_to_trading(self):
        """Navigate to trading page and confirm readiness"""
        logger.info("Navigating to trading interface...")
        
        try:
            # Trading page selectors
            trading_nav_selectors = [
                'a[href*="trading"]',
                'a:has-text("Trading")',
                'a:has-text("Trade")',
                '.nav-trading',
                '#trading-link'
            ]
            
            # Try to find and click trading navigation
            try:
                trading_nav = await self.wait_for_element_with_retry(
                    trading_nav_selectors, timeout=5000, retries=1
                )
                await trading_nav.click()
                logger.info("Clicked trading navigation")
            except Exception:
                logger.info("Trading navigation not found, assuming already on trading page")
            
            # Confirm trading interface is ready
            trading_interface_selectors = [
                '.trading-interface',
                '.order-form',
                '.trade-panel',
                'div:has-text("Order")',
                'button:has-text("Buy")',
                'button:has-text("Sell")'
            ]
            
            await self.wait_for_element_with_retry(trading_interface_selectors, timeout=15000)
            await self.take_screenshot('trading_interface')
            logger.info("Trading interface ready!")
            
        except Exception as e:
            await self.take_screenshot('trading_navigation_failure')
            logger.error(f"Failed to navigate to trading interface: {e}")
            raise
    
    async def place_trade_order(self):
        """Attempt to place a trade order with comprehensive selector fallbacks"""
        logger.info("Attempting to place trade order...")
        
        try:
            # Order tab selectors (primary approach)
            order_tab_selectors = [
                'button:has-text("ORDER")',
                'tab:has-text("ORDER")',
                '.order-tab',
                '#order-tab',
                'a[href*="order"]'
            ]
            
            # Try ORDER tab first
            try:
                order_tab = await self.wait_for_element_with_retry(
                    order_tab_selectors, timeout=5000, retries=1
                )
                await order_tab.click()
                logger.info("ORDER tab clicked successfully")
            except Exception:
                logger.info("ORDER tab not found, trying DOM tab...")
                
                # DOM tab selectors (fallback)
                dom_tab_selectors = [
                    'button:has-text("DOM")',
                    'tab:has-text("DOM")',
                    '.dom-tab',
                    '#dom-tab'
                ]
                
                try:
                    dom_tab = await self.wait_for_element_with_retry(
                        dom_tab_selectors, timeout=5000, retries=1
                    )
                    await dom_tab.click()
                    logger.info("DOM tab clicked successfully")
                except Exception:
                    logger.info("DOM tab not found, using generic selectors...")
            
            # Generic order form selectors
            buy_button_selectors = [
                'button:has-text("Buy")',
                'button:has-text("BUY")',
                '.buy-button',
                '#buy-button',
                'input[value="Buy"]'
            ]
            
            sell_button_selectors = [
                'button:has-text("Sell")',
                'button:has-text("SELL")',
                '.sell-button',
                '#sell-button',
                'input[value="Sell"]'
            ]
            
            # Try to find buy or sell button
            try:
                buy_button = await self.wait_for_element_with_retry(
                    buy_button_selectors, timeout=5000, retries=1
                )
                await buy_button.click()
                logger.info("Buy button clicked - trade order initiated!")
            except Exception:
                try:
                    sell_button = await self.wait_for_element_with_retry(
                        sell_button_selectors, timeout=5000, retries=1
                    )
                    await sell_button.click()
                    logger.info("Sell button clicked - trade order initiated!")
                except Exception:
                    logger.warning("No buy/sell buttons found, trade order may not have been placed")
            
            await self.take_screenshot('trade_order_placed')
            
            # Wait a moment for any network requests to be captured
            await asyncio.sleep(3)
            
        except Exception as e:
            await self.take_screenshot('trade_order_failure')
            logger.error(f"Failed to place trade order: {e}")
            raise
    
    async def run_automation(self):
        """Main automation workflow"""
        logger.info("Starting TradeBot Sentinel automation...")
        
        try:
            await self.setup_browser()
            await self.login()
            await self.navigate_to_trading()
            await self.place_trade_order()
            
            logger.info("Automation completed successfully!")
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            await self.take_screenshot('critical_error')
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        logger.info("Cleaning up browser resources...")
        
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point"""
    # Load environment variables from .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Create and run the automation
    sentinel = TradeBotSentinel(headless=True)  # Set to False for debugging
    await sentinel.run_automation()

if __name__ == "__main__":
    asyncio.run(main())