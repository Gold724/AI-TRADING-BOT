#!/usr/bin/env python3
"""
TradeBot Sentinel - Bulenox ProjectX Trading Platform Automation
Expert automation agent for secure login, trade execution, and request interception.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import Optional, Dict, Any, List
import subprocess

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
    """TradeBot Sentinel - Advanced Bulenox Trading Automation"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.trade_requests: List[Dict] = []
        
        # Environment variables for secure login
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            logger.error("BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
            sys.exit(1)
            
        logger.info(f"TradeBot Sentinel initialized - Headless: {headless}")
    
    async def setup_browser(self) -> None:
        """Initialize browser with network interception"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await self.context.new_page()
            
            # Setup network interceptor for trade requests
            await self.setup_network_interceptor()
            
            logger.info("Browser setup completed successfully")
            
        except Exception as e:
            logger.error(f"Browser setup failed: {str(e)}")
            await self.cleanup()
            raise
    
    async def setup_network_interceptor(self) -> None:
        """Setup network interceptor to capture trade execution requests"""
        async def handle_request(request):
            if request.method == 'POST':
                logger.info(f"POST Request intercepted: {request.url}")
                
                try:
                    # Get request data
                    post_data = request.post_data
                    if post_data:
                        # Try to parse as JSON
                        try:
                            json_data = json.loads(post_data)
                            if self.is_trade_request(json_data):
                                await self.save_trade_request(request, json_data)
                        except json.JSONDecodeError:
                            # Check string content for trade keywords
                            if self.is_trade_request_string(post_data):
                                await self.save_trade_request(request, post_data)
                                
                except Exception as e:
                    logger.error(f"Error processing request: {str(e)}")
        
        self.page.on('request', handle_request)
        logger.info("Network interceptor setup completed")
    
    def is_trade_request(self, data: Dict) -> bool:
        """Check if request data contains trade-related information"""
        trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell', 'quantity', 'side']
        
        if isinstance(data, dict):
            data_str = json.dumps(data).lower()
            return any(keyword in data_str for keyword in trade_keywords)
        return False
    
    def is_trade_request_string(self, data: str) -> bool:
        """Check if string data contains trade-related keywords"""
        trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell', 'quantity', 'side']
        data_lower = data.lower()
        return any(keyword in data_lower for keyword in trade_keywords)
    
    async def save_trade_request(self, request, data) -> None:
        """Save trade request as cURL command and convert to Python"""
        try:
            # Build cURL command
            curl_command = f"curl -X POST '{request.url}'"
            
            # Add headers
            for name, value in request.headers.items():
                curl_command += f" -H '{name}: {value}'"
            
            # Add data
            if isinstance(data, dict):
                curl_command += f" -d '{json.dumps(data)}'"
            else:
                curl_command += f" -d '{data}'"
            
            # Save cURL command
            with open('trade.sh', 'w') as f:
                f.write(f"#!/bin/bash\n{curl_command}\n")
            
            logger.info("Trade request saved to trade.sh")
            
            # Convert to Python requests code
            await self.convert_curl_to_python()
            
            # Store request info
            self.trade_requests.append({
                'timestamp': datetime.now().isoformat(),
                'url': request.url,
                'method': request.method,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Error saving trade request: {str(e)}")
    
    async def convert_curl_to_python(self) -> None:
        """Convert cURL command to Python requests code using curlconverter"""
        try:
            # Check if curlconverter is installed
            result = subprocess.run(['python', '-c', 'import curlconverter'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning("curlconverter not installed. Installing...")
                subprocess.run(['pip', 'install', 'curlconverter'], check=True)
            
            # Read cURL command
            with open('trade.sh', 'r') as f:
                curl_content = f.read().strip()
                curl_command = curl_content.replace('#!/bin/bash\n', '')
            
            # Convert using curlconverter
            import curlconverter
            python_code = curlconverter.curl_to_python(curl_command)
            
            # Save Python code
            with open('trade_request_full.py', 'w') as f:
                f.write(f"#!/usr/bin/env python3\n")
                f.write(f"# Generated by TradeBot Sentinel - {datetime.now().isoformat()}\n\n")
                f.write(python_code)
            
            logger.info("Trade request converted to Python and saved as trade_request_full.py")
            
        except Exception as e:
            logger.error(f"Error converting cURL to Python: {str(e)}")
    
    async def login(self) -> bool:
        """Secure login to Bulenox ProjectX platform"""
        try:
            logger.info("Starting login process...")
            
            # Navigate to login page
            await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Handle potential Time Sync Warning modal
            await self.handle_time_sync_warning()
            
            # Login selectors with fallbacks
            username_selectors = [
                'input[name="username"]',
                'input[type="email"]',
                '#username',
                '#email',
                '.username-input',
                '.email-input'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password',
                '.password-input'
            ]
            
            login_button_selectors = [
                'button[type="submit"]',
                '.login-button',
                '.btn-login',
                '#login-btn',
                'input[type="submit"]'
            ]
            
            # Fill username with retries
            username_filled = await self.fill_with_fallback(username_selectors, self.username, "username")
            if not username_filled:
                await self.take_screenshot("login_username_failed")
                return False
            
            # Fill password with retries
            password_filled = await self.fill_with_fallback(password_selectors, self.password, "password")
            if not password_filled:
                await self.take_screenshot("login_password_failed")
                return False
            
            # Click login button with retries
            login_clicked = await self.click_with_fallback(login_button_selectors, "login button")
            if not login_clicked:
                await self.take_screenshot("login_button_failed")
                return False
            
            # Wait for login completion
            await asyncio.sleep(3)
            
            # Confirm login success
            if await self.confirm_login_success():
                logger.info("Login successful!")
                return True
            else:
                await self.take_screenshot("login_verification_failed")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            await self.take_screenshot("login_exception")
            return False
    
    async def handle_time_sync_warning(self) -> None:
        """Handle Time Sync Warning modal if present"""
        try:
            modal_selectors = [
                '.modal',
                '.time-sync-warning',
                '.warning-modal',
                '[role="dialog"]'
            ]
            
            for selector in modal_selectors:
                try:
                    modal = await self.page.wait_for_selector(selector, timeout=2000)
                    if modal:
                        logger.info("Time Sync Warning modal detected")
                        
                        # Try to close modal
                        close_selectors = [
                            '.modal .close',
                            '.modal button',
                            '.btn-close',
                            '[aria-label="Close"]'
                        ]
                        
                        for close_selector in close_selectors:
                            try:
                                await self.page.click(close_selector, timeout=1000)
                                logger.info("Time Sync Warning modal closed")
                                await asyncio.sleep(1)
                                return
                            except:
                                continue
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"No Time Sync Warning modal found: {str(e)}")
    
    async def fill_with_fallback(self, selectors: List[str], value: str, field_name: str) -> bool:
        """Fill input field with fallback selectors and retries"""
        for attempt in range(3):
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.fill(selector, value)
                    logger.info(f"{field_name} filled successfully with selector: {selector}")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to fill {field_name} with selector {selector}: {str(e)}")
                    continue
            
            if attempt < 2:
                logger.info(f"Retrying {field_name} fill (attempt {attempt + 2}/3)")
                await asyncio.sleep(2)
        
        logger.error(f"Failed to fill {field_name} after all attempts")
        return False
    
    async def click_with_fallback(self, selectors: List[str], element_name: str) -> bool:
        """Click element with fallback selectors and retries"""
        for attempt in range(3):
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.click(selector)
                    logger.info(f"{element_name} clicked successfully with selector: {selector}")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to click {element_name} with selector {selector}: {str(e)}")
                    continue
            
            if attempt < 2:
                logger.info(f"Retrying {element_name} click (attempt {attempt + 2}/3)")
                await asyncio.sleep(2)
        
        logger.error(f"Failed to click {element_name} after all attempts")
        return False
    
    async def confirm_login_success(self) -> bool:
        """Confirm login success by waiting for dashboard elements"""
        dashboard_selectors = [
            '.dashboard',
            '.main-content',
            '.user-menu',
            '.trading-interface',
            '.account-info',
            '.portfolio',
            '.nav-user'
        ]
        
        for attempt in range(3):
            for selector in dashboard_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    logger.info(f"Login confirmed with dashboard selector: {selector}")
                    return True
                except:
                    continue
            
            if attempt < 2:
                logger.info(f"Retrying login confirmation (attempt {attempt + 2}/3)")
                await asyncio.sleep(2)
        
        return False
    
    async def navigate_to_trading(self) -> bool:
        """Navigate to trading page if not already there"""
        try:
            logger.info("Navigating to trading interface...")
            
            # Check if already on trading page
            trading_indicators = [
                '.trading-interface',
                '.order-form',
                '.price-chart',
                '.order-book'
            ]
            
            for indicator in trading_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=2000)
                    logger.info("Already on trading page")
                    return True
                except:
                    continue
            
            # Navigate to trading page
            trading_nav_selectors = [
                'a[href*="trading"]',
                'a[href*="trade"]',
                '.nav-trading',
                '.menu-trading',
                'nav a:has-text("Trading")',
                'nav a:has-text("Trade")'
            ]
            
            nav_clicked = await self.click_with_fallback(trading_nav_selectors, "trading navigation")
            if not nav_clicked:
                # Try direct URL navigation
                await self.page.goto('https://bulenox.projectx.com/trading', wait_until='networkidle')
            
            await asyncio.sleep(3)
            
            # Confirm trading page loaded
            return await self.confirm_trading_ready()
            
        except Exception as e:
            logger.error(f"Failed to navigate to trading: {str(e)}")
            await self.take_screenshot("trading_navigation_failed")
            return False
    
    async def confirm_trading_ready(self) -> bool:
        """Confirm trading interface is ready"""
        trading_selectors = [
            '.trading-interface',
            '.order-form',
            '.buy-sell-buttons',
            '.price-input',
            '.amount-input',
            '.order-book'
        ]
        
        for attempt in range(3):
            for selector in trading_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    logger.info(f"Trading interface ready with selector: {selector}")
                    return True
                except:
                    continue
            
            if attempt < 2:
                logger.info(f"Retrying trading readiness check (attempt {attempt + 2}/3)")
                await asyncio.sleep(2)
        
        return False
    
    async def place_trade_order(self, symbol: str = "BTC/USDT", amount: str = "0.001", 
                               order_type: str = "market", side: str = "buy") -> bool:
        """Attempt to place a trade order with comprehensive fallback selectors"""
        try:
            logger.info(f"Attempting to place {side} order: {amount} {symbol}")
            
            # First try ORDER tab, then DOM tab, then generic selectors
            tab_strategies = [
                {
                    'name': 'ORDER tab',
                    'tab_selectors': ['.order-tab', '[data-tab="order"]', 'button:has-text("ORDER")'],
                    'form_selectors': {
                        'symbol': ['.order-form select[name="symbol"]', '.symbol-select', '#symbol'],
                        'amount': ['.order-form input[name="amount"]', '.amount-input', '#amount'],
                        'side': [f'.order-form .{side}-button', f'.{side}-btn', f'button:has-text("{side.upper()}")'],
                        'submit': ['.order-form button[type="submit"]', '.place-order-btn', '.submit-order']
                    }
                },
                {
                    'name': 'DOM tab',
                    'tab_selectors': ['.dom-tab', '[data-tab="dom"]', 'button:has-text("DOM")'],
                    'form_selectors': {
                        'amount': ['.dom-form input[name="amount"]', '.dom-amount', '.quantity-input'],
                        'side': [f'.dom-form .{side}-button', f'.dom-{side}', f'.{side}-order'],
                        'submit': ['.dom-form .place-order', '.dom-submit', '.execute-order']
                    }
                },
                {
                    'name': 'Generic',
                    'tab_selectors': [],
                    'form_selectors': {
                        'symbol': ['select[name="symbol"]', '.symbol-dropdown', '#trading-symbol'],
                        'amount': ['input[name="amount"]', '.amount', '#order-amount'],
                        'side': [f'.{side}-button', f'#{side}-btn', f'[data-side="{side}"]'],
                        'submit': ['button[type="submit"]', '.place-order', '.submit-trade']
                    }
                }
            ]
            
            for strategy in tab_strategies:
                logger.info(f"Trying {strategy['name']} strategy...")
                
                # Click tab if specified
                if strategy['tab_selectors']:
                    tab_clicked = await self.click_with_fallback(strategy['tab_selectors'], f"{strategy['name']} tab")
                    if not tab_clicked:
                        continue
                    await asyncio.sleep(1)
                
                # Fill form fields
                success = True
                
                # Symbol selection (if available)
                if 'symbol' in strategy['form_selectors']:
                    symbol_set = await self.select_with_fallback(strategy['form_selectors']['symbol'], symbol, "symbol")
                    if not symbol_set:
                        logger.warning(f"Could not set symbol for {strategy['name']} strategy")
                
                # Amount input
                if 'amount' in strategy['form_selectors']:
                    amount_filled = await self.fill_with_fallback(strategy['form_selectors']['amount'], amount, "amount")
                    if not amount_filled:
                        success = False
                
                # Side selection (buy/sell)
                if 'side' in strategy['form_selectors']:
                    side_clicked = await self.click_with_fallback(strategy['form_selectors']['side'], f"{side} button")
                    if not side_clicked:
                        success = False
                
                if success:
                    # Submit order
                    if 'submit' in strategy['form_selectors']:
                        submit_clicked = await self.click_with_fallback(strategy['form_selectors']['submit'], "submit order")
                        if submit_clicked:
                            logger.info(f"Order placed successfully using {strategy['name']} strategy")
                            await asyncio.sleep(2)  # Wait for order processing
                            return True
                
                logger.warning(f"{strategy['name']} strategy failed, trying next...")
            
            logger.error("All order placement strategies failed")
            await self.take_screenshot("order_placement_failed")
            return False
            
        except Exception as e:
            logger.error(f"Order placement failed: {str(e)}")
            await self.take_screenshot("order_placement_exception")
            return False
    
    async def select_with_fallback(self, selectors: List[str], value: str, field_name: str) -> bool:
        """Select option from dropdown with fallback selectors"""
        for attempt in range(3):
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.select_option(selector, value)
                    logger.info(f"{field_name} selected successfully with selector: {selector}")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to select {field_name} with selector {selector}: {str(e)}")
                    continue
            
            if attempt < 2:
                logger.info(f"Retrying {field_name} selection (attempt {attempt + 2}/3)")
                await asyncio.sleep(2)
        
        logger.error(f"Failed to select {field_name} after all attempts")
        return False
    
    async def take_screenshot(self, name: str) -> None:
        """Take screenshot for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{name}_{timestamp}.png"
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
    
    async def run_automation(self) -> None:
        """Main automation workflow"""
        try:
            logger.info("=== TradeBot Sentinel Starting ===")
            
            # Setup browser
            await self.setup_browser()
            
            # Login
            if not await self.login():
                logger.error("Login failed, aborting automation")
                return
            
            # Navigate to trading
            if not await self.navigate_to_trading():
                logger.error("Failed to access trading interface")
                return
            
            # Place test order
            await self.place_trade_order(
                symbol="BTC/USDT",
                amount="0.001",
                side="buy"
            )
            
            # Wait for potential trade requests
            logger.info("Monitoring for trade requests...")
            await asyncio.sleep(10)
            
            # Report results
            if self.trade_requests:
                logger.info(f"Captured {len(self.trade_requests)} trade requests")
                for i, req in enumerate(self.trade_requests, 1):
                    logger.info(f"Trade Request {i}: {req['url']}")
            else:
                logger.info("No trade requests captured")
            
            logger.info("=== TradeBot Sentinel Completed ===")
            
        except Exception as e:
            logger.error(f"Automation failed: {str(e)}")
            await self.take_screenshot("automation_failed")
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TradeBot Sentinel - Bulenox Trading Automation')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--visible', action='store_true', help='Run in visible mode (overrides headless)')
    args = parser.parse_args()
    
    headless = args.headless and not args.visible
    
    sentinel = TradeBotSentinel(headless=headless)
    await sentinel.run_automation()


if __name__ == "__main__":
    asyncio.run(main())