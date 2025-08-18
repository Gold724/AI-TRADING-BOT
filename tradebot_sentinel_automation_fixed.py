#!/usr/bin/env python3
"""
TradeBot Sentinel — Expert Automation Agent for Bulenox ProjectX Trading Platform

This script automates:
1. Secure login using environment variables
2. Time Sync Warning modal detection and handling
3. Dashboard confirmation with multiple selector fallbacks
4. Trading page navigation and readiness confirmation
5. Trade order placement with robust selector fallbacks
6. Network request interception for trade execution detection
7. cURL command generation and Python requests code conversion
8. Screenshot capture on critical failures
9. Verbose logging for complete traceability

Author: TradeBot Sentinel Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradebot_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('TradeBotSentinel')

class TradeBotSentinelAutomation:
    """TradeBot Sentinel Automation Agent for Bulenox ProjectX"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.trade_requests: List[Dict] = []
        
        # Login credentials from environment
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
        
        logger.info(f"🤖 TradeBot Sentinel initialized - Headless: {headless}")
    
    async def setup_browser(self):
        """Initialize browser and setup network interception"""
        try:
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
            
            logger.info("✅ Browser setup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            await self.capture_screenshot("browser_setup_error")
            raise
    
    async def setup_network_interception(self):
        """Setup network request interception to capture trade requests"""
        async def handle_request(request):
            if request.method == 'POST':
                logger.info(f"📡 POST Request intercepted: {request.url}")
                
                # Check if this might be a trade execution request
                try:
                    post_data = request.post_data
                    if post_data:
                        # Try to parse as JSON
                        try:
                            json_data = json.loads(post_data)
                            if self.is_trade_request(json_data):
                                await self.save_trade_request(request, json_data)
                        except json.JSONDecodeError:
                            # Check string content for trade keywords
                            if self.contains_trade_keywords(post_data):
                                await self.save_trade_request(request, post_data)
                except Exception as e:
                    logger.warning(f"⚠️ Error processing request data: {e}")
        
        self.page.on('request', handle_request)
        logger.info("🔍 Network interception setup completed")
    
    def is_trade_request(self, data: Any) -> bool:
        """Check if request data contains trade-related information"""
        trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell', 'quantity', 'side']
        
        if isinstance(data, dict):
            data_str = json.dumps(data).lower()
        else:
            data_str = str(data).lower()
        
        return any(keyword in data_str for keyword in trade_keywords)
    
    def contains_trade_keywords(self, data: str) -> bool:
        """Check if string data contains trade keywords"""
        trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell', 'quantity', 'side']
        data_lower = data.lower()
        return any(keyword in data_lower for keyword in trade_keywords)
    
    async def save_trade_request(self, request, data):
        """Save trade request as cURL command and convert to Python"""
        try:
            # Generate cURL command
            curl_command = await self.generate_curl_command(request, data)
            
            # Save cURL to file
            with open('trade.sh', 'w') as f:
                f.write(curl_command)
            
            logger.info("💾 Trade request saved to trade.sh")
            
            # Convert to Python requests code
            await self.convert_curl_to_python()
            
            # Store for analysis
            self.trade_requests.append({
                'url': request.url,
                'method': request.method,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'curl_command': curl_command
            })
            
        except Exception as e:
            logger.error(f"❌ Error saving trade request: {e}")
    
    async def generate_curl_command(self, request, data) -> str:
        """Generate cURL command from request"""
        headers = await request.all_headers()
        
        curl_parts = [f"curl -X {request.method}"]
        curl_parts.append(f"'{request.url}'")
        
        # Add headers
        for name, value in headers.items():
            if name.lower() not in ['content-length', 'host']:
                curl_parts.append(f"-H '{name}: {value}'")
        
        # Add data
        if isinstance(data, dict):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        curl_parts.append(f"-d '{data_str}'")
        
        return ' \\
  '.join(curl_parts)
    
    async def convert_curl_to_python(self):
        """Convert cURL command to Python requests code using curlconverter"""
        try:
            # Check if curlconverter is installed
            result = subprocess.run(['python', '-c', 'import curlconverter'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning("⚠️ curlconverter not installed. Installing...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'curlconverter'], 
                             check=True)
            
            # Read cURL command
            with open('trade.sh', 'r') as f:
                curl_command = f.read()
            
            # Convert using curlconverter
            import curlconverter
            python_code = curlconverter.to_python(curl_command)
            
            # Save Python code
            with open('trade_request_full.py', 'w') as f:
                f.write(python_code)
            
            logger.info("🐍 Python requests code saved to trade_request_full.py")
            
        except Exception as e:
            logger.error(f"❌ Error converting cURL to Python: {e}")
    
    async def login(self) -> bool:
        """Perform secure login with robust selector fallbacks"""
        try:
            logger.info("🔐 Starting login process...")
            
            # Navigate to login page (adjust URL as needed)
            await self.page.goto('https://bulenox-projectx.com/login', wait_until='networkidle')
            
            # Wait for login form with multiple selector attempts
            login_selectors = [
                'input[name="username"]',
                'input[type="email"]',
                '#username',
                '#email',
                '.username-input',
                '.email-input'
            ]
            
            username_input = await self.wait_for_any_selector(login_selectors, "username input")
            if not username_input:
                return False
            
            # Fill username
            await username_input.fill(self.username)
            logger.info("✅ Username filled")
            
            # Find password input
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password',
                '.password-input'
            ]
            
            password_input = await self.wait_for_any_selector(password_selectors, "password input")
            if not password_input:
                return False
            
            # Fill password
            await password_input.fill(self.password)
            logger.info("✅ Password filled")
            
            # Find and click login button
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '.login-button',
                '#login-btn',
                'button:has-text("Login")',
                'button:has-text("Sign In")'
            ]
            
            login_button = await self.wait_for_any_selector(login_button_selectors, "login button")
            if not login_button:
                return False
            
            await login_button.click()
            logger.info("🔄 Login button clicked")
            
            # Handle potential Time Sync Warning modal
            await self.handle_time_sync_warning()
            
            # Confirm login success
            return await self.confirm_login_success()
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            await self.capture_screenshot("login_error")
            return False
    
    async def handle_time_sync_warning(self):
        """Detect and handle Time Sync Warning modals"""
        try:
            # Wait a bit for potential modal to appear
            await asyncio.sleep(2)
            
            time_sync_selectors = [
                '.time-sync-warning',
                '.modal:has-text("Time Sync")',
                '.alert:has-text("sync")',
                'div:has-text("time sync warning")',
                '.warning-modal'
            ]
            
            for selector in time_sync_selectors:
                try:
                    modal = await self.page.wait_for_selector(selector, timeout=3000)
                    if modal:
                        logger.info("⚠️ Time Sync Warning detected")
                        
                        # Try to find and click dismiss/OK button
                        dismiss_selectors = [
                            'button:has-text("OK")',
                            'button:has-text("Dismiss")',
                            'button:has-text("Continue")',
                            '.modal-close',
                            '.btn-primary'
                        ]
                        
                        for dismiss_selector in dismiss_selectors:
                            try:
                                dismiss_btn = await self.page.wait_for_selector(dismiss_selector, timeout=2000)
                                if dismiss_btn:
                                    await dismiss_btn.click()
                                    logger.info("✅ Time Sync Warning dismissed")
                                    return
                            except:
                                continue
                        
                        # If no dismiss button found, try pressing Escape
                        await self.page.keyboard.press('Escape')
                        logger.info("⌨️ Pressed Escape to dismiss modal")
                        return
                        
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"⚠️ Error handling time sync warning: {e}")
    
    async def confirm_login_success(self) -> bool:
        """Confirm login success by waiting for dashboard selectors"""
        dashboard_selectors = [
            '.dashboard',
            '.main-content',
            '.trading-interface',
            '.user-menu',
            '.account-info',
            '#dashboard',
            '.nav-user'
        ]
        
        for attempt in range(3):
            logger.info(f"🔍 Login confirmation attempt {attempt + 1}/3")
            
            element = await self.wait_for_any_selector(dashboard_selectors, "dashboard", timeout=10000)
            if element:
                logger.info("✅ Login successful - Dashboard detected")
                return True
            
            await asyncio.sleep(2)
        
        logger.error("❌ Login confirmation failed - Dashboard not detected")
        await self.capture_screenshot("login_confirmation_failed")
        return False
    
    async def navigate_to_trading(self) -> bool:
        """Navigate to trading page and confirm readiness"""
        try:
            logger.info("📈 Navigating to trading page...")
            
            # Look for trading navigation links
            trading_nav_selectors = [
                'a[href*="trading"]',
                'a[href*="trade"]',
                '.nav-trading',
                '.menu-trading',
                'button:has-text("Trading")',
                'a:has-text("Trade")'
            ]
            
            trading_link = await self.wait_for_any_selector(trading_nav_selectors, "trading navigation")
            if trading_link:
                await trading_link.click()
                logger.info("🔄 Trading navigation clicked")
            else:
                # Try direct URL navigation
                current_url = self.page.url
                trading_url = current_url.replace('/dashboard', '/trading').replace('/home', '/trading')
                await self.page.goto(trading_url, wait_until='networkidle')
                logger.info(f"🔄 Direct navigation to: {trading_url}")
            
            # Confirm trading interface is ready
            return await self.confirm_trading_readiness()
            
        except Exception as e:
            logger.error(f"❌ Trading navigation failed: {e}")
            await self.capture_screenshot("trading_navigation_error")
            return False
    
    async def confirm_trading_readiness(self) -> bool:
        """Confirm trading interface is ready"""
        trading_interface_selectors = [
            '.trading-panel',
            '.order-form',
            '.buy-sell-buttons',
            '.trading-interface',
            '.order-book',
            '#trading-form'
        ]
        
        for attempt in range(3):
            logger.info(f"🔍 Trading readiness check {attempt + 1}/3")
            
            element = await self.wait_for_any_selector(trading_interface_selectors, "trading interface", timeout=10000)
            if element:
                logger.info("✅ Trading interface ready")
                return True
            
            await asyncio.sleep(2)
        
        logger.error("❌ Trading interface not ready")
        await self.capture_screenshot("trading_readiness_failed")
        return False
    
    async def place_trade_order(self, symbol: str = "BTCUSDT", amount: float = 0.001, side: str = "buy") -> bool:
        """Attempt to place a trade order with robust selector fallbacks"""
        try:
            logger.info(f"📊 Placing {side} order: {amount} {symbol}")
            
            # First try ORDER tab
            if await self.try_order_tab_placement(symbol, amount, side):
                return True
            
            # Fallback to DOM tab
            if await self.try_dom_tab_placement(symbol, amount, side):
                return True
            
            # Final fallback to generic selectors
            return await self.try_generic_placement(symbol, amount, side)
            
        except Exception as e:
            logger.error(f"❌ Trade order placement failed: {e}")
            await self.capture_screenshot("trade_order_error")
            return False
    
    async def try_order_tab_placement(self, symbol: str, amount: float, side: str) -> bool:
        """Try placing order using ORDER tab selectors"""
        try:
            logger.info("🎯 Attempting ORDER tab placement...")
            
            # Click ORDER tab
            order_tab_selectors = [
                '.tab-order',
                '#order-tab',
                'button:has-text("ORDER")',
                '.order-tab-button'
            ]
            
            order_tab = await self.wait_for_any_selector(order_tab_selectors, "ORDER tab")
            if order_tab:
                await order_tab.click()
                await asyncio.sleep(1)
            
            # Fill symbol
            symbol_selectors = [
                'input[name="symbol"]',
                '.symbol-input',
                '#trading-symbol'
            ]
            
            symbol_input = await self.wait_for_any_selector(symbol_selectors, "symbol input")
            if symbol_input:
                await symbol_input.fill(symbol)
            
            # Fill amount
            amount_selectors = [
                'input[name="amount"]',
                'input[name="quantity"]',
                '.amount-input',
                '.quantity-input'
            ]
            
            amount_input = await self.wait_for_any_selector(amount_selectors, "amount input")
            if amount_input:
                await amount_input.fill(str(amount))
            
            # Click buy/sell button
            button_selectors = [
                f'.btn-{side}',
                f'button:has-text("{side.upper()}")',
                f'.{side}-button',
                f'#{side}-btn'
            ]
            
            trade_button = await self.wait_for_any_selector(button_selectors, f"{side} button")
            if trade_button:
                await trade_button.click()
                logger.info(f"✅ ORDER tab {side} button clicked")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ ORDER tab placement failed: {e}")
            return False
    
    async def try_dom_tab_placement(self, symbol: str, amount: float, side: str) -> bool:
        """Try placing order using DOM tab selectors"""
        try:
            logger.info("🎯 Attempting DOM tab placement...")
            
            # Click DOM tab
            dom_tab_selectors = [
                '.tab-dom',
                '#dom-tab',
                'button:has-text("DOM")',
                '.dom-tab-button'
            ]
            
            dom_tab = await self.wait_for_any_selector(dom_tab_selectors, "DOM tab")
            if dom_tab:
                await dom_tab.click()
                await asyncio.sleep(1)
            
            # Look for DOM-specific order placement
            dom_order_selectors = [
                f'.dom-{side}',
                f'.depth-{side}',
                f'.orderbook-{side}'
            ]
            
            dom_button = await self.wait_for_any_selector(dom_order_selectors, f"DOM {side} button")
            if dom_button:
                await dom_button.click()
                logger.info(f"✅ DOM tab {side} button clicked")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ DOM tab placement failed: {e}")
            return False
    
    async def try_generic_placement(self, symbol: str, amount: float, side: str) -> bool:
        """Try placing order using generic selectors"""
        try:
            logger.info("🎯 Attempting generic placement...")
            
            # Generic buy/sell buttons
            generic_selectors = [
                f'button[data-side="{side}"]',
                f'.trade-{side}',
                f'.order-{side}',
                f'input[value="{side.upper()}"]'
            ]
            
            generic_button = await self.wait_for_any_selector(generic_selectors, f"generic {side} button")
            if generic_button:
                await generic_button.click()
                logger.info(f"✅ Generic {side} button clicked")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Generic placement failed: {e}")
            return False
    
    async def wait_for_any_selector(self, selectors: List[str], description: str, timeout: int = 5000):
        """Wait for any of the provided selectors to appear"""
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=timeout)
                if element:
                    logger.info(f"✅ Found {description}: {selector}")
                    return element
            except:
                continue
        
        logger.warning(f"⚠️ Could not find {description} with any selector")
        return None
    
    async def capture_screenshot(self, name: str):
        """Capture screenshot for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{name}_{timestamp}.png"
            await self.page.screenshot(path=filename, full_page=True)
            logger.info(f"📸 Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"❌ Screenshot capture failed: {e}")
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("🧹 Browser cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    async def run_automation(self):
        """Main automation workflow"""
        try:
            logger.info("🚀 Starting TradeBot Sentinel automation...")
            
            # Setup browser
            await self.setup_browser()
            
            # Login
            if not await self.login():
                logger.error("❌ Login failed, aborting automation")
                return False
            
            # Navigate to trading
            if not await self.navigate_to_trading():
                logger.error("❌ Trading navigation failed, aborting automation")
                return False
            
            # Place a test trade order
            if not await self.place_trade_order():
                logger.error("❌ Trade order placement failed")
                return False
            
            # Wait a bit for potential network requests
            logger.info("⏳ Waiting for trade execution requests...")
            await asyncio.sleep(10)
            
            # Report results
            logger.info(f"📊 Automation completed. Captured {len(self.trade_requests)} trade requests.")
            
            if self.trade_requests:
                logger.info("💾 Trade request files generated:")
                logger.info("  - trade.sh (cURL command)")
                logger.info("  - trade_request_full.py (Python requests code)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
            await self.capture_screenshot("automation_error")
            return False
        
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TradeBot Sentinel Automation')
    parser.add_argument('--headless', action='store_true', default=True, 
                       help='Run in headless mode (default: True)')
    parser.add_argument('--visible', action='store_true', 
                       help='Run in visible mode (overrides headless)')
    
    args = parser.parse_args()
    
    headless = args.headless and not args.visible
    
    automation = TradeBotSentinelAutomation(headless=headless)
    success = await automation.run_automation()
    
    if success:
        logger.info("🎉 TradeBot Sentinel automation completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 TradeBot Sentinel automation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
