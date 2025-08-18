#!/usr/bin/env python3
"""
bulenox_ai_playwright_contracts.py
Modern Playwright-based Bulenox automation with CONTRACT SIZE focus

Key Features:
- 100% Playwright (NO Selenium)
- Contract-based trading (NOT lot sizes)
- Stealth automation with anti-detection
- Network request interception
- Robust error handling and retries
- Screenshot capture on failures

IMPORTANT: Bulenox uses CONTRACTS, not lot sizes!
- 1 contract = 1 contract (not 0.01 lot like Exness)
- Minimum quantity is typically 1 contract
- Risk management should be based on contract counts

Author: TRAE-SentinelOps
Version: 2.0.0 (Playwright Migration)
Date: 2025-01-17
"""

import os
import sys
import json
import asyncio
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Request, Response
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    print("Then run: playwright install")
    sys.exit(1)

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BulenoxPlaywright')

# Load environment variables
load_dotenv()

class BulenoxPlaywrightAutomation:
    """Modern Playwright-based Bulenox automation with contract size focus"""
    
    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logged_in = False
        
        # Contract-based trading configuration
        self.min_contract_size = 1  # Minimum 1 contract for Bulenox
        self.max_contract_size = 10  # Safety limit
        
        # Network interception
        self.captured_requests: List[Dict] = []
        
        # Directories
        self.root_dir = Path(__file__).parent
        self.logs_dir = self.root_dir / "logs"
        self.screenshots_dir = self.logs_dir / "screenshots"
        self.logs_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Credentials
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        self.base_url = "https://bulenox.projectx.com"
        
        if not self.username or not self.password:
            logger.warning("⚠️  BULENOX_USERNAME and BULENOX_PASSWORD not set in environment")
            
        # Selectors for Bulenox platform
        self.selectors = {
            'login': {
                'username': [
                    'input[name="username"]',
                    'input[type="email"]',
                    'input[placeholder*="username" i]',
                    'input[placeholder*="email" i]',
                    '#username',
                    '#email'
                ],
                'password': [
                    'input[name="password"]',
                    'input[type="password"]',
                    '#password'
                ],
                'submit': [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    '.login-button',
                    '#login-btn'
                ]
            },
            'trading': {
                'symbol_search': [
                    'input[placeholder*="symbol" i]',
                    'input[placeholder*="search" i]',
                    '.symbol-search',
                    '#symbol-input'
                ],
                'buy_button': [
                    'button:has-text("BUY")',
                    'button:has-text("Buy")',
                    '.buy-button',
                    '#buy-btn'
                ],
                'sell_button': [
                    'button:has-text("SELL")',
                    'button:has-text("Sell")',
                    '.sell-button',
                    '#sell-btn'
                ],
                'quantity': [
                    'input[name="quantity"]',
                    'input[placeholder*="quantity" i]',
                    'input[placeholder*="amount" i]',
                    'input[placeholder*="contracts" i]',
                    '.quantity-input',
                    '#quantity'
                ],
                'stop_loss': [
                    'input[name="stop_loss"]',
                    'input[placeholder*="stop" i]',
                    '.stop-loss-input',
                    '#stop-loss'
                ],
                'take_profit': [
                    'input[name="take_profit"]',
                    'input[placeholder*="profit" i]',
                    '.take-profit-input',
                    '#take-profit'
                ],
                'confirm': [
                    'button:has-text("Confirm")',
                    'button:has-text("Execute")',
                    'button:has-text("Place Order")',
                    '.confirm-button',
                    '#confirm-btn'
                ]
            },
            'modals': {
                'time_sync_warning': [
                    '.modal:has-text("Time Sync")',
                    '.warning:has-text("sync")',
                    '[data-testid="time-sync-modal"]'
                ],
                'close_modal': [
                    'button:has-text("OK")',
                    'button:has-text("Close")',
                    '.modal-close',
                    '.close-btn',
                    '[aria-label="Close"]'
                ]
            }
        }
        
    async def init_browser(self) -> bool:
        """Initialize Playwright browser with stealth settings"""
        try:
            playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
            self.browser = await playwright.chromium.launch(
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
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            # Create context with stealth settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Setup network interception
            await self._setup_network_interception()
            
            logger.info("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser: {e}")
            return False
            
    async def _setup_network_interception(self):
        """Setup network request/response interception"""
        async def handle_request(request: Request):
            if self.debug:
                logger.debug(f"🌐 Request: {request.method} {request.url}")
                
        async def handle_response(response: Response):
            # Capture trade-related requests
            if any(keyword in response.url.lower() for keyword in ['trade', 'order', 'execute', 'position']):
                try:
                    request_data = {
                        'timestamp': datetime.now().isoformat(),
                        'method': response.request.method,
                        'url': response.url,
                        'status': response.status,
                        'headers': dict(response.headers),
                    }
                    
                    # Try to get request body for POST requests
                    if response.request.method == 'POST':
                        try:
                            post_data = response.request.post_data
                            if post_data:
                                request_data['post_data'] = post_data
                        except:
                            pass
                            
                    self.captured_requests.append(request_data)
                    logger.info(f"📡 Captured trade request: {response.request.method} {response.url}")
                    
                except Exception as e:
                    logger.debug(f"Failed to capture request: {e}")
                    
        self.page.on('request', handle_request)
        self.page.on('response', handle_response)
        
    async def _find_element_with_fallbacks(self, selectors: List[str], timeout: int = 10000) -> Optional[str]:
        """Find element using multiple selector fallbacks"""
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                return selector
            except:
                continue
        return None
        
    async def _handle_modals(self) -> bool:
        """Handle any modal dialogs that might appear"""
        try:
            # Check for time sync warning modal
            time_sync_selector = await self._find_element_with_fallbacks(
                self.selectors['modals']['time_sync_warning'], 
                timeout=3000
            )
            
            if time_sync_selector:
                logger.info("⚠️  Time sync warning modal detected")
                
                # Try to close it
                close_selector = await self._find_element_with_fallbacks(
                    self.selectors['modals']['close_modal'],
                    timeout=3000
                )
                
                if close_selector:
                    await self.page.click(close_selector)
                    logger.info("✅ Modal closed successfully")
                    await asyncio.sleep(1)
                    return True
                    
        except Exception as e:
            logger.debug(f"Modal handling error: {e}")
            
        return False
        
    async def login(self) -> bool:
        """Login to Bulenox platform"""
        if not self.username or not self.password:
            logger.error("❌ Username or password not provided")
            return False
            
        try:
            logger.info(f"🚀 Navigating to Bulenox login: {self.base_url}/login")
            await self.page.goto(f"{self.base_url}/login", wait_until='networkidle')
            
            # Handle any initial modals
            await self._handle_modals()
            
            # Find and fill username
            username_selector = await self._find_element_with_fallbacks(
                self.selectors['login']['username']
            )
            if not username_selector:
                logger.error("❌ Username field not found")
                await self._take_screenshot("login_username_not_found")
                return False
                
            await self.page.fill(username_selector, self.username)
            logger.info("✅ Username filled")
            
            # Find and fill password
            password_selector = await self._find_element_with_fallbacks(
                self.selectors['login']['password']
            )
            if not password_selector:
                logger.error("❌ Password field not found")
                await self._take_screenshot("login_password_not_found")
                return False
                
            await self.page.fill(password_selector, self.password)
            logger.info("✅ Password filled")
            
            # Find and click submit button
            submit_selector = await self._find_element_with_fallbacks(
                self.selectors['login']['submit']
            )
            if not submit_selector:
                logger.error("❌ Submit button not found")
                await self._take_screenshot("login_submit_not_found")
                return False
                
            await self.page.click(submit_selector)
            logger.info("🔄 Login submitted")
            
            # Wait for navigation and handle any post-login modals
            await asyncio.sleep(3)
            await self._handle_modals()
            
            # Verify login success by checking URL or dashboard elements
            current_url = self.page.url
            if 'dashboard' in current_url.lower() or 'trading' in current_url.lower():
                self.logged_in = True
                logger.info("✅ Login successful!")
                await self._take_screenshot("login_success")
                return True
            else:
                logger.error(f"❌ Login may have failed. Current URL: {current_url}")
                await self._take_screenshot("login_failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            await self._take_screenshot("login_error")
            return False
            
    def validate_contract_size(self, quantity: float) -> int:
        """Validate and convert quantity to contract size
        
        Args:
            quantity: Input quantity (could be contracts or lot size)
            
        Returns:
            int: Valid contract size (minimum 1)
        """
        try:
            # Ensure we have a valid number
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                logger.warning(f"⚠️  Invalid quantity {quantity}, using minimum 1 contract")
                return self.min_contract_size
                
            # Convert to integer contracts
            contracts = int(quantity)
            
            # Apply minimum
            if contracts < self.min_contract_size:
                logger.warning(f"⚠️  Quantity {contracts} below minimum, using {self.min_contract_size} contract")
                contracts = self.min_contract_size
                
            # Apply maximum for safety
            if contracts > self.max_contract_size:
                logger.warning(f"⚠️  Quantity {contracts} above maximum, using {self.max_contract_size} contracts")
                contracts = self.max_contract_size
                
            logger.info(f"📊 Contract size validated: {quantity} → {contracts} contracts")
            return contracts
            
        except Exception as e:
            logger.error(f"❌ Contract validation error: {e}")
            return self.min_contract_size
            
    async def place_trade(self, symbol: str, side: str, quantity: float, 
                         stop_loss: Optional[float] = None, 
                         take_profit: Optional[float] = None) -> bool:
        """Place a trade with contract-based quantity
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            side: 'BUY' or 'SELL'
            quantity: Quantity in CONTRACTS (not lot sizes)
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
            
        Returns:
            bool: True if trade placed successfully
        """
        if not self.logged_in:
            logger.error("❌ Not logged in. Please login first.")
            return False
            
        # Validate contract size
        contracts = self.validate_contract_size(quantity)
        
        try:
            logger.info(f"🎯 Placing trade: {side} {contracts} contracts of {symbol}")
            
            # Navigate to trading page if needed
            current_url = self.page.url
            if 'trading' not in current_url.lower():
                await self.page.goto(f"{self.base_url}/trading", wait_until='networkidle')
                await asyncio.sleep(2)
                
            # Search for symbol
            symbol_selector = await self._find_element_with_fallbacks(
                self.selectors['trading']['symbol_search']
            )
            if symbol_selector:
                await self.page.fill(symbol_selector, symbol)
                await self.page.press(symbol_selector, 'Enter')
                await asyncio.sleep(1)
                logger.info(f"✅ Symbol {symbol} selected")
            else:
                logger.warning("⚠️  Symbol search field not found, continuing...")
                
            # Click buy/sell button
            if side.upper() == 'BUY':
                button_selector = await self._find_element_with_fallbacks(
                    self.selectors['trading']['buy_button']
                )
            else:
                button_selector = await self._find_element_with_fallbacks(
                    self.selectors['trading']['sell_button']
                )
                
            if not button_selector:
                logger.error(f"❌ {side} button not found")
                await self._take_screenshot(f"trade_{side.lower()}_button_not_found")
                return False
                
            await self.page.click(button_selector)
            logger.info(f"✅ {side} button clicked")
            await asyncio.sleep(1)
            
            # Fill quantity (contracts)
            quantity_selector = await self._find_element_with_fallbacks(
                self.selectors['trading']['quantity']
            )
            if quantity_selector:
                await self.page.fill(quantity_selector, str(contracts))
                logger.info(f"✅ Quantity set to {contracts} contracts")
            else:
                logger.warning("⚠️  Quantity field not found")
                
            # Fill stop loss if provided
            if stop_loss:
                sl_selector = await self._find_element_with_fallbacks(
                    self.selectors['trading']['stop_loss']
                )
                if sl_selector:
                    await self.page.fill(sl_selector, str(stop_loss))
                    logger.info(f"✅ Stop loss set to {stop_loss}")
                    
            # Fill take profit if provided
            if take_profit:
                tp_selector = await self._find_element_with_fallbacks(
                    self.selectors['trading']['take_profit']
                )
                if tp_selector:
                    await self.page.fill(tp_selector, str(take_profit))
                    logger.info(f"✅ Take profit set to {take_profit}")
                    
            # Confirm trade
            confirm_selector = await self._find_element_with_fallbacks(
                self.selectors['trading']['confirm']
            )
            if confirm_selector:
                await self.page.click(confirm_selector)
                logger.info("🚀 Trade confirmed!")
                await asyncio.sleep(2)
                
                # Take screenshot of result
                await self._take_screenshot(f"trade_executed_{symbol}_{side.lower()}")
                
                return True
            else:
                logger.error("❌ Confirm button not found")
                await self._take_screenshot("trade_confirm_not_found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            await self._take_screenshot("trade_error")
            return False
            
    async def _take_screenshot(self, name: str):
        """Take a screenshot for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            await self.page.screenshot(path=str(filepath))
            logger.info(f"📸 Screenshot saved: {filepath}")
        except Exception as e:
            logger.debug(f"Screenshot error: {e}")
            
    async def save_captured_requests(self):
        """Save captured network requests to file"""
        if not self.captured_requests:
            return
            
        try:
            requests_file = self.logs_dir / "captured_requests.json"
            with open(requests_file, 'w') as f:
                json.dump(self.captured_requests, f, indent=2)
            logger.info(f"💾 Saved {len(self.captured_requests)} requests to {requests_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save requests: {e}")
            
    async def close(self):
        """Clean up browser resources"""
        try:
            await self.save_captured_requests()
            
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
                
            logger.info("🔄 Browser closed successfully")
        except Exception as e:
            logger.error(f"❌ Error closing browser: {e}")


# Compatibility functions for existing code
async def login_bulenox_ai(username: str = None, password: str = None, 
                          headless: bool = True, debug: bool = False) -> BulenoxPlaywrightAutomation:
    """Login to Bulenox using Playwright (compatibility function)
    
    Returns:
        BulenoxPlaywrightAutomation: Logged in automation instance
    """
    # Use environment variables if not provided
    if not username:
        username = os.getenv('BULENOX_USERNAME')
    if not password:
        password = os.getenv('BULENOX_PASSWORD')
        
    automation = BulenoxPlaywrightAutomation(headless=headless, debug=debug)
    
    # Override credentials if provided
    if username:
        automation.username = username
    if password:
        automation.password = password
        
    # Initialize and login
    if await automation.init_browser():
        if await automation.login():
            return automation
            
    # Cleanup on failure
    await automation.close()
    raise Exception("Failed to login to Bulenox")


async def place_bulenox_trade(symbol: str, side: str, quantity: float, 
                             stop_loss: Optional[float] = None, 
                             take_profit: Optional[float] = None, 
                             debug: bool = False) -> bool:
    """Place a trade on Bulenox using contracts (compatibility function)
    
    IMPORTANT: quantity is in CONTRACTS, not lot sizes!
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        side: 'BUY' or 'SELL'
        quantity: Quantity in CONTRACTS (not lot sizes)
        stop_loss: Optional stop loss price
        take_profit: Optional take profit price
        debug: Enable debug logging
        
    Returns:
        bool: True if trade placed successfully
    """
    automation = None
    try:
        # Login first
        automation = await login_bulenox_ai(debug=debug)
        
        # Place trade
        result = await automation.place_trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Trade placement failed: {e}")
        return False
        
    finally:
        if automation:
            await automation.close()


async def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulenox Playwright Automation')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--test-trade', action='store_true', help='Place a test trade')
    parser.add_argument('--symbol', default='EURUSD', help='Trading symbol')
    parser.add_argument('--side', choices=['BUY', 'SELL'], default='BUY', help='Trade side')
    parser.add_argument('--quantity', type=float, default=1, help='Quantity in contracts')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    automation = BulenoxPlaywrightAutomation(headless=args.headless, debug=args.debug)
    
    try:
        # Initialize browser
        if not await automation.init_browser():
            logger.error("❌ Failed to initialize browser")
            return
            
        # Login
        if not await automation.login():
            logger.error("❌ Login failed")
            return
            
        logger.info("✅ Login successful!")
        
        # Test trade if requested
        if args.test_trade:
            logger.info(f"🎯 Placing test trade: {args.side} {args.quantity} contracts of {args.symbol}")
            success = await automation.place_trade(
                symbol=args.symbol,
                side=args.side,
                quantity=args.quantity
            )
            
            if success:
                logger.info("✅ Test trade placed successfully!")
            else:
                logger.error("❌ Test trade failed")
        else:
            # Keep session alive
            logger.info("🔄 Session active. Press Ctrl+C to exit...")
            try:
                while True:
                    await asyncio.sleep(10)
                    # Heartbeat - could add health checks here
            except KeyboardInterrupt:
                logger.info("👋 Shutting down...")
                
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        
    finally:
        await automation.close()


if __name__ == "__main__":
    asyncio.run(main())