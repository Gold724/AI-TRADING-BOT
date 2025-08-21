#!/usr/bin/env python3
"""
TradeBot Sentinel - cURL Capture Mode
Specialized script for capturing all network requests as cURL commands

Author: TradeBot Sentinel Team
Version: 1.0.0
Date: 2024-12-01
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import argparse
import sys

# Load environment variables
load_dotenv()

class TradeBotCurlCapture:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.captured_requests = []
        self.login_captured = False
        self.account_captured = False
        self.trade_captured = False
        self.latest_trade_curl = None
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('logs/curl_capture.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        """Create necessary directories"""
        directories = ['logs', 'logs/curls', 'logs/json']
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    def get_request_description(self, url, post_data):
        """Determine request type based on URL and data"""
        url_lower = url.lower()
        post_data_lower = str(post_data).lower() if post_data else ""
        
        # Login detection
        if any(keyword in url_lower for keyword in ['login', 'auth', 'signin', 'authenticate']):
            return 'login_auth'
        
        # Account info detection
        if any(keyword in url_lower for keyword in ['account', 'profile', 'user', 'balance']):
            return 'account_info'
            
        # Trade execution detection
        if any(keyword in url_lower for keyword in ['trade', 'order', 'execute', 'buy', 'sell']):
            return 'trade_execution'
            
        # Check POST data for trade keywords
        if any(keyword in post_data_lower for keyword in ['symbol', 'amount', 'price', 'order', 'trade']):
            return 'trade_execution'
            
        # Portfolio/positions
        if any(keyword in url_lower for keyword in ['portfolio', 'position', 'holding']):
            return 'portfolio_info'
            
        # Market data
        if any(keyword in url_lower for keyword in ['market', 'price', 'quote', 'ticker']):
            return 'market_data'
            
        # Default
        return 'api_request'
        
    def convert_to_curl(self, request, response_headers=None):
        """Convert intercepted request to cURL command"""
        curl_parts = ['curl -X', request.method]
        
        # Add URL
        curl_parts.extend(["'", request.url, "'"])
        
        # Add headers
        if request.headers:
            for name, value in request.headers.items():
                if name.lower() not in ['content-length', 'host']:
                    curl_parts.extend(['-H', f"'{name}: {value}'"])
        
        # Add POST data
        if request.method == 'POST' and request.post_data:
            try:
                # Try to parse as JSON for pretty formatting
                json_data = json.loads(request.post_data)
                formatted_json = json.dumps(json_data, indent=2)
                curl_parts.extend(['-d', f"'{formatted_json}'"])
            except (json.JSONDecodeError, TypeError):
                # Fallback to raw data
                curl_parts.extend(['-d', f"'{request.post_data}'"])
        
        return ' '.join(curl_parts)
        
    async def save_request(self, request, description):
        """Save request as cURL and JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate cURL command
        curl_command = self.convert_to_curl(request)
        
        # Save cURL file
        curl_filename = f"logs/curls/{timestamp}_{description}.curl"
        with open(curl_filename, 'w', encoding='utf-8') as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"# TradeBot Sentinel - cURL Capture\n")
            f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"# URL: {request.url}\n")
            f.write(f"# Description: {description}\n\n")
            f.write(curl_command)
            f.write("\n\n# End of cURL command\n")
            
        # Save JSON data if available
        if request.post_data:
            json_filename = f"logs/json/{timestamp}_{description}.json"
            request_data = {
                'timestamp': datetime.now().isoformat(),
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data,
                'description': description
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, indent=2, ensure_ascii=False)
                
        # Track latest trade execution
        if description == 'trade_execution':
            self.latest_trade_curl = curl_command
            self.trade_captured = True
            
        # Update capture status
        if description == 'login_auth':
            self.login_captured = True
        elif description == 'account_info':
            self.account_captured = True
            
        self.logger.info(f"📝 Captured {description}: {curl_filename}")
        
    async def handle_request(self, request):
        """Handle intercepted network request"""
        try:
            # Only capture POST requests or JSON content
            if (request.method == 'POST' or 
                (request.headers and 'application/json' in request.headers.get('content-type', ''))):
                
                description = self.get_request_description(request.url, request.post_data)
                await self.save_request(request, description)
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
            
    async def wait_for_selector_with_retries(self, page, selectors, retries=3, delay=2000):
        """Wait for selector with retry logic"""
        if isinstance(selectors, str):
            selectors = [selectors]
            
        for attempt in range(retries):
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=delay)
                    if element:
                        self.logger.info(f"✅ Found selector: {selector}")
                        return element
                except Exception:
                    continue
                    
            if attempt < retries - 1:
                self.logger.info(f"🔄 Retry {attempt + 1}/{retries} for selectors")
                await asyncio.sleep(2)
                
        raise Exception(f"No valid selector found after {retries} attempts")
        
    async def login_to_bulenox(self, page):
        """Login to Bulenox platform"""
        username = os.getenv('BULENOX_USERNAME')
        password = os.getenv('BULENOX_PASSWORD')
        broker_url = os.getenv('BROKER_URL', 'https://bulenox.projectx.com')
        
        if not username or not password:
            raise Exception("BULENOX_USERNAME and BULENOX_PASSWORD must be set in .env")
            
        self.logger.info(f"🌐 Navigating to {broker_url}")
        await page.goto(broker_url)
        
        # Wait for login form
        login_selectors = [
            'input[name="userName"]',  # Bulenox ProjectX uses userName
            'input[name="username"]',
            'input[name="email"]', 
            'input[type="email"]',
            '#username',
            '#email',
            '.username-input',
            '.email-input'
        ]
        
        username_input = await self.wait_for_selector_with_retries(page, login_selectors)
        await username_input.fill(username)
        self.logger.info("✅ Username entered")
        
        # Password field
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            '#password',
            '.password-input'
        ]
        
        password_input = await self.wait_for_selector_with_retries(page, password_selectors)
        await password_input.fill(password)
        self.logger.info("✅ Password entered")
        
        # Submit login
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            '.login-button',
            '.submit-button',
            'button:has-text("Login")',
            'button:has-text("Sign In")'
        ]
        
        submit_button = await self.wait_for_selector_with_retries(page, submit_selectors)
        await submit_button.click()
        self.logger.info("🔐 Login submitted")
        
        # Wait for successful login
        dashboard_selectors = [
            '.dashboard',
            '.trading-interface',
            '.account-info',
            '[data-testid="dashboard"]',
            '.main-content',
            '.user-menu'
        ]
        
        try:
            await self.wait_for_selector_with_retries(page, dashboard_selectors, retries=5, delay=3000)
            self.logger.info("✅ Login successful - Dashboard loaded")
        except Exception:
            self.logger.warning("⚠️ Dashboard not detected, but continuing...")
            
    async def navigate_to_trading(self, page):
        """Navigate to trading interface"""
        trading_selectors = [
            'a[href*="trade"]',
            'a[href*="trading"]',
            '.trading-link',
            '.trade-button',
            'button:has-text("Trade")',
            'nav a:has-text("Trading")'
        ]
        
        try:
            trading_link = await self.wait_for_selector_with_retries(page, trading_selectors)
            await trading_link.click()
            self.logger.info("📈 Navigated to trading interface")
            
            # Wait for trading interface to load
            trading_interface_selectors = [
                '.trading-interface',
                '.order-form',
                '.trade-panel',
                '.buy-sell-buttons'
            ]
            
            await self.wait_for_selector_with_retries(page, trading_interface_selectors)
            self.logger.info("✅ Trading interface loaded")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not navigate to trading interface: {e}")
            
    def generate_trade_sh(self):
        """Generate trade.sh with latest trade execution cURL"""
        if self.latest_trade_curl:
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n")
                f.write("# TradeBot Sentinel - Latest Trade Execution\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                f.write(self.latest_trade_curl)
                f.write("\n")
            self.logger.info("✅ Generated trade.sh with latest trade execution")
        else:
            self.logger.warning("⚠️ No trade execution captured, trade.sh not generated")
            
    def check_completion_status(self):
        """Check if all required requests have been captured"""
        status = {
            'login': '✅' if self.login_captured else '❌',
            'account': '✅' if self.account_captured else '❌', 
            'trade': '✅' if self.trade_captured else '❌'
        }
        
        self.logger.info(f"📊 Capture Status: Login {status['login']} | Account {status['account']} | Trade {status['trade']}")
        
        return self.login_captured and self.account_captured and self.trade_captured
        
    async def run_capture_session(self, headless=True):
        """Run the main capture session"""
        async with async_playwright() as p:
            # Launch browser with persistent context
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--allow-running-insecure-content'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Set up request interception
            page.on('request', self.handle_request)
            
            try:
                self.logger.info("🚀 Starting cURL Capture Mode")
                
                # Step 1 & 2: Login
                await self.login_to_bulenox(page)
                
                # Step 3: Navigate to trading (triggers account requests)
                await self.navigate_to_trading(page)
                
                # Wait for requests to be captured
                self.logger.info("⏳ Waiting for network requests...")
                await asyncio.sleep(10)
                
                # Check if we need to wait longer for trade execution
                max_wait_time = 300  # 5 minutes
                wait_interval = 10
                elapsed_time = 0
                
                while not self.check_completion_status() and elapsed_time < max_wait_time:
                    self.logger.info(f"⏳ Waiting for requests... ({elapsed_time}s/{max_wait_time}s)")
                    await asyncio.sleep(wait_interval)
                    elapsed_time += wait_interval
                    
                # Generate final trade.sh
                self.generate_trade_sh()
                
                # Final status
                if self.check_completion_status():
                    self.logger.info("✅ All cURLs Captured - Session Complete!")
                else:
                    self.logger.warning("⚠️ Some requests may not have been captured")
                    
            except Exception as e:
                self.logger.error(f"❌ Error during capture session: {e}")
                await page.screenshot(path='logs/capture_error.png')
                
            finally:
                await browser.close()
                
def main():
    parser = argparse.ArgumentParser(description='TradeBot Sentinel - cURL Capture Mode')
    parser.add_argument('--visible', action='store_true', help='Run with visible browser')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (default)')
    
    args = parser.parse_args()
    
    # Default to headless unless --visible is specified
    headless = not args.visible
    
    capture = TradeBotCurlCapture()
    
    try:
        asyncio.run(capture.run_capture_session(headless=headless))
    except KeyboardInterrupt:
        print("\n🛑 Capture session interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        
if __name__ == "__main__":
    main()