#!/usr/bin/env python3
"""
TradeBot Sentinel - Comprehensive Bulenox ProjectX Trading Platform Automation

This script provides robust automation for:
1. Secure login with environment variables
2. Time Sync Warning modal detection and handling
3. Dashboard confirmation with multiple selectors
4. Trading page navigation with retries
5. Trade order placement with fallback selectors
6. Network request interception and trade detection
7. Automatic cURL and Python code generation
8. Screenshot capture on critical failures
9. Verbose logging for debugging

Author: TradeBot Sentinel AI
Version: 1.0.0
Date: 2025-01-13
"""

import asyncio
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    import curlconverter
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Please install: pip install playwright curlconverter")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tradebot_sentinel.log')
    ]
)
logger = logging.getLogger(__name__)

class TradeBotSentinel:
    """Comprehensive TradeBot Sentinel for Bulenox ProjectX automation"""
    
    def __init__(self, headless: bool = True, test_mode: bool = False):
        self.headless = headless
        self.test_mode = test_mode
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.trade_requests: List[Dict] = []
        
        # URLs
        self.login_url = "https://bulenox.projectx.com/login"
        self.trading_url = "https://bulenox.projectx.com/trading"
        
        # Credentials from environment
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            logger.error("Missing BULENOX_USERNAME or BULENOX_PASSWORD environment variables")
            if not test_mode:
                sys.exit(1)
    
    async def setup_browser(self) -> None:
        """Initialize browser with stealth settings"""
        logger.info(f"Setting up browser (headless={self.headless})")
        
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Create context with additional stealth
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
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
        """)
        
        self.page = await self.context.new_page()
        
        # Setup network interception
        await self.setup_network_interception()
        
        logger.info("Browser setup completed")
    
    async def setup_network_interception(self) -> None:
        """Setup network request interception to capture trade requests"""
        logger.info("Setting up network interception")
        
        async def handle_request(request):
            """Handle network requests and detect trade execution"""
            if request.method == 'POST':
                url = request.url
                logger.info(f"POST request intercepted: {url}")
                
                try:
                    # Get request data
                    post_data = request.post_data
                    headers = request.headers
                    
                    # Check if this looks like a trade request
                    is_trade_request = self.is_trade_request(url, post_data, headers)
                    
                    if is_trade_request:
                        logger.info(f"Trade execution request detected: {url}")
                        
                        trade_request = {
                            'url': url,
                            'method': 'POST',
                            'headers': headers,
                            'post_data': post_data,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.trade_requests.append(trade_request)
                        await self.save_trade_request(trade_request)
                        
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
        
        self.page.on('request', handle_request)
    
    def is_trade_request(self, url: str, post_data: Optional[str], headers: Dict) -> bool:
        """Detect if a request is a trade execution request"""
        # Check URL patterns
        trade_url_patterns = [
            '/trade', '/order', '/execute', '/buy', '/sell',
            '/position', '/market', '/limit'
        ]
        
        if any(pattern in url.lower() for pattern in trade_url_patterns):
            return True
        
        # Check post data for trade keywords
        if post_data:
            trade_keywords = [
                'symbol', 'amount', 'price', 'order', 'trade',
                'buy', 'sell', 'quantity', 'volume', 'side'
            ]
            
            post_data_lower = post_data.lower()
            if any(keyword in post_data_lower for keyword in trade_keywords):
                return True
            
            # Try to parse as JSON
            try:
                data = json.loads(post_data)
                if any(key in data for key in trade_keywords):
                    return True
            except:
                pass
        
        return False
    
    async def save_trade_request(self, trade_request: Dict) -> None:
        """Save trade request as cURL and Python code"""
        logger.info("Saving trade request as cURL and Python code")
        
        try:
            # Generate cURL command
            curl_parts = ['curl -X POST']
            
            # Add headers
            for key, value in trade_request['headers'].items():
                curl_parts.append(f'-H "{key}: {value}"')
            
            # Add post data
            if trade_request['post_data']:
                curl_parts.append(f'-d \'{trade_request["post_data"]}\'')
            
            # Add URL
            curl_parts.append(f'"{trade_request["url"]}"')
            
            curl_command = ' '.join(curl_parts)
            
            # Save to file
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write('#!/bin/bash\n')
                f.write(f'# Trade request captured at {trade_request["timestamp"]}\n')
                f.write(curl_command + '\n')
            
            logger.info("cURL command saved to trade.sh")
            
            # Convert to Python manually (more reliable than curlconverter)
            try:
                python_code = self.convert_curl_to_python(trade_request)
                
                with open('trade_request_full.py', 'w', encoding='utf-8') as f:
                    f.write(f'# Trade request captured at {trade_request["timestamp"]}\n')
                    f.write(f'# Original URL: {trade_request["url"]}\n\n')
                    f.write(python_code)
                
                logger.info("Python code saved to trade_request_full.py")
                
            except Exception as e:
                logger.error(f"Error converting cURL to Python: {e}")
                
        except Exception as e:
            logger.error(f"Error saving trade request: {e}")
    
    def convert_curl_to_python(self, trade_request: dict) -> str:
        """Convert trade request to Python requests code"""
        try:
            # Build Python code
            python_lines = [
                "import requests",
                "import json",
                "",
                "# Trade request",
                f"url = '{trade_request['url']}'"  
            ]
            
            # Add headers
            if trade_request['headers']:
                python_lines.append("headers = {")
                for key, value in trade_request['headers'].items():
                    python_lines.append(f"    '{key}': '{value}',")
                python_lines.append("}")
            else:
                python_lines.append("headers = {}")
            
            # Add data
            if trade_request['post_data']:
                try:
                    # Try to parse as JSON
                    json.loads(trade_request['post_data'])
                    python_lines.append(f"data = '{trade_request['post_data']}'")
                except:
                    # If not JSON, treat as string
                    python_lines.append(f"data = '{trade_request['post_data']}'")
            else:
                python_lines.append("data = None")
            
            # Add request call
            python_lines.extend([
                "",
                "# Execute request",
                "response = requests.post(url, headers=headers, data=data)",
                "print(f'Status: {response.status_code}')",
                "print(f'Response: {response.text}')"
            ])
            
            return "\n".join(python_lines)
            
        except Exception as e:
            logger.error(f"Error converting to Python: {e}")
            return f"# Error converting cURL to Python: {e}"
    
    async def take_screenshot(self, filename: str, description: str = "") -> None:
        """Take screenshot for debugging"""
        try:
            if self.page:
                screenshot_path = f"screenshots/{filename}"
                os.makedirs("screenshots", exist_ok=True)
                await self.page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path} - {description}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    async def wait_for_element_with_retry(self, selectors: List[str], timeout: int = 10000, retries: int = 3) -> Optional[str]:
        """Wait for element with multiple selectors and retry logic"""
        for attempt in range(retries):
            logger.info(f"Attempt {attempt + 1}/{retries} - Waiting for elements: {selectors}")
            
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=timeout)
                    logger.info(f"Found element with selector: {selector}")
                    return selector
                except Exception:
                    continue
            
            if attempt < retries - 1:
                logger.info(f"Retry {attempt + 1} failed, waiting 2 seconds...")
                await asyncio.sleep(2)
        
        logger.error(f"Failed to find any element after {retries} attempts")
        return None
    
    async def handle_time_sync_warning(self) -> bool:
        """Handle Time Sync Warning modal if it appears"""
        logger.info("Checking for Time Sync Warning modal")
        
        time_sync_selectors = [
            '[data-testid="time-sync-modal"]',
            '.time-sync-warning',
            '.modal:has-text("Time Sync")',
            '.alert:has-text("time")',
            'div:has-text("Time Sync Warning")',
            '[class*="time-sync"]',
            '[id*="time-sync"]'
        ]
        
        try:
            # Check if modal exists
            for selector in time_sync_selectors:
                try:
                    modal = await self.page.wait_for_selector(selector, timeout=2000)
                    if modal:
                        logger.info(f"Time Sync Warning modal detected with selector: {selector}")
                        
                        # Try to close it
                        close_selectors = [
                            f'{selector} button:has-text("OK")',
                            f'{selector} button:has-text("Close")',
                            f'{selector} button:has-text("Continue")',
                            f'{selector} .close',
                            f'{selector} [aria-label="Close"]',
                            'button:has-text("OK")',
                            'button:has-text("Close")',
                            'button:has-text("Continue")'
                        ]
                        
                        for close_selector in close_selectors:
                            try:
                                await self.page.click(close_selector, timeout=2000)
                                logger.info(f"Closed Time Sync Warning with: {close_selector}")
                                await asyncio.sleep(1)
                                return True
                            except:
                                continue
                        
                        # If no close button found, try pressing Escape
                        await self.page.keyboard.press('Escape')
                        logger.info("Attempted to close modal with Escape key")
                        return True
                        
                except:
                    continue
            
            logger.info("No Time Sync Warning modal detected")
            return False
            
        except Exception as e:
            logger.error(f"Error handling Time Sync Warning: {e}")
            return False
    
    async def login(self) -> bool:
        """Perform secure login with robust error handling"""
        logger.info(f"Starting login process to {self.login_url}")
        
        try:
            # Navigate to login page with increased timeout
            try:
                await self.page.goto(self.login_url, wait_until='networkidle', timeout=60000)  # 60 seconds
            except Exception as e:
                logger.warning(f"Failed with networkidle, trying domcontentloaded: {e}")
                await self.page.goto(self.login_url, wait_until='domcontentloaded', timeout=60000)
            await self.take_screenshot("01_login_page.png", "Login page loaded")
            
            # Handle Time Sync Warning if it appears
            await self.handle_time_sync_warning()
            
            if self.test_mode:
                logger.info("Test mode: Skipping actual login")
                return True
            
            # Wait for login form with multiple selectors
            username_selectors = [
                'input[name="userName"]',
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
                '#username',
                '#email',
                '.username-input',
                '.email-input',
                'input[data-testid="username"]',
                'input[data-testid="email"]'
            ]
            
            username_selector = await self.wait_for_element_with_retry(username_selectors)
            if not username_selector:
                await self.take_screenshot("error_no_username_field.png", "Username field not found")
                return False
            
            # Fill username
            await self.page.fill(username_selector, self.username)
            logger.info("Username filled")
            
            # Wait for password field (found via diagnostic: name='password')
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password',
                '.password-input',
                'input[data-testid="password"]',
                'input[placeholder*="password" i]'
            ]
            
            password_selector = await self.wait_for_element_with_retry(password_selectors)
            if not password_selector:
                await self.take_screenshot("error_no_password_field.png", "Password field not found")
                return False
            
            # Fill password
            await self.page.fill(password_selector, self.password)
            logger.info("Password filled")
            
            # Find and click login button (found via diagnostic: text='SIGN IN', type='submit')
            login_button_selectors = [
                'button:has-text("SIGN IN")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                '.login-button',
                '.signin-button',
                '#login-button',
                '#signin-button',
                'button[data-testid="login"]',
                'button[data-testid="signin"]'
            ]
            
            login_button_selector = await self.wait_for_element_with_retry(login_button_selectors)
            if not login_button_selector:
                await self.take_screenshot("error_no_login_button.png", "Login button not found")
                return False
            
            # Click login button
            await self.page.click(login_button_selector)
            logger.info("Login button clicked")
            
            # Wait for navigation or dashboard
            await asyncio.sleep(3)
            
            # Handle Time Sync Warning again if it appears after login
            await self.handle_time_sync_warning()
            
            # Confirm login success
            return await self.confirm_login_success()
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            await self.take_screenshot("error_login_failed.png", f"Login failed: {e}")
            return False
    
    async def confirm_login_success(self) -> bool:
        """Confirm login success by checking for dashboard elements"""
        logger.info("Confirming login success")
        
        dashboard_selectors = [
            '.dashboard',
            '.main-content',
            '.user-dashboard',
            '.trading-dashboard',
            '[data-testid="dashboard"]',
            '.navbar .user-menu',
            '.header .user-info',
            '.sidebar',
            '.main-nav',
            'nav',
            '.logout',
            '.sign-out',
            'button:has-text("Logout")',
            'a:has-text("Logout")',
            '.user-profile',
            '.account-info'
        ]
        
        success_selector = await self.wait_for_element_with_retry(dashboard_selectors, timeout=15000)
        
        if success_selector:
            logger.info(f"Login successful - Found dashboard element: {success_selector}")
            await self.take_screenshot("02_login_success.png", "Login successful")
            return True
        else:
            logger.error("Login failed - No dashboard elements found")
            await self.take_screenshot("error_login_failed_no_dashboard.png", "No dashboard found after login")
            return False
    
    async def navigate_to_trading(self) -> bool:
        """Navigate to trading page with retry logic"""
        logger.info(f"Navigating to trading page: {self.trading_url}")
        
        try:
            # Navigate to trading page
            await self.page.goto(self.trading_url, wait_until='networkidle')
            await self.take_screenshot("03_trading_page.png", "Trading page loaded")
            
            # Wait for trading interface elements
            trading_selectors = [
                '.trading-interface',
                '.order-form',
                '.trade-panel',
                '.buy-sell-buttons',
                'button:has-text("Buy")',
                'button:has-text("Sell")',
                '.order-book',
                '.price-chart',
                '[data-testid="trading-interface"]',
                '.trading-dashboard',
                '.market-data',
                '.order-entry'
            ]
            
            trading_selector = await self.wait_for_element_with_retry(trading_selectors, timeout=15000)
            
            if trading_selector:
                logger.info(f"Trading page ready - Found element: {trading_selector}")
                return True
            else:
                logger.error("Trading page not ready - No trading interface found")
                await self.take_screenshot("error_trading_page_not_ready.png", "Trading interface not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to navigate to trading page: {e}")
            await self.take_screenshot("error_trading_navigation_failed.png", f"Trading navigation failed: {e}")
            return False
    
    async def place_trade_order(self) -> bool:
        """Attempt to place a trade order with fallback selectors"""
        logger.info("Attempting to place trade order")
        
        try:
            # First try ORDER tab selectors
            order_tab_selectors = [
                'button:has-text("ORDER")',
                '.order-tab',
                '[data-testid="order-tab"]',
                '#order-tab',
                'a:has-text("ORDER")',
                '.tab:has-text("ORDER")'
            ]
            
            order_tab_selector = await self.wait_for_element_with_retry(order_tab_selectors, timeout=5000)
            
            if order_tab_selector:
                await self.page.click(order_tab_selector)
                logger.info(f"Clicked ORDER tab: {order_tab_selector}")
                await asyncio.sleep(1)
            else:
                # Try DOM tab as fallback
                logger.info("ORDER tab not found, trying DOM tab")
                dom_tab_selectors = [
                    'button:has-text("DOM")',
                    '.dom-tab',
                    '[data-testid="dom-tab"]',
                    '#dom-tab',
                    'a:has-text("DOM")',
                    '.tab:has-text("DOM")'
                ]
                
                dom_tab_selector = await self.wait_for_element_with_retry(dom_tab_selectors, timeout=5000)
                
                if dom_tab_selector:
                    await self.page.click(dom_tab_selector)
                    logger.info(f"Clicked DOM tab: {dom_tab_selector}")
                    await asyncio.sleep(1)
                else:
                    logger.info("Neither ORDER nor DOM tab found, proceeding with generic selectors")
            
            # Look for buy/sell buttons or order form
            trade_action_selectors = [
                'button:has-text("Buy")',
                'button:has-text("Sell")',
                '.buy-button',
                '.sell-button',
                '[data-testid="buy-button"]',
                '[data-testid="sell-button"]',
                '.order-submit',
                'button[type="submit"]',
                '.place-order',
                '.execute-trade'
            ]
            
            trade_button_selector = await self.wait_for_element_with_retry(trade_action_selectors, timeout=10000)
            
            if trade_button_selector:
                logger.info(f"Found trade button: {trade_button_selector}")
                
                if self.test_mode:
                    logger.info("Test mode: Would click trade button but skipping actual execution")
                    await self.take_screenshot("04_trade_button_found.png", "Trade button found in test mode")
                    return True
                else:
                    # In real mode, click the button
                    await self.page.click(trade_button_selector)
                    logger.info("Trade button clicked")
                    await self.take_screenshot("04_trade_order_placed.png", "Trade order placed")
                    
                    # Wait a moment for any network requests
                    await asyncio.sleep(3)
                    return True
            else:
                logger.error("No trade buttons or order form found")
                await self.take_screenshot("error_no_trade_buttons.png", "No trade buttons found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to place trade order: {e}")
            await self.take_screenshot("error_trade_order_failed.png", f"Trade order failed: {e}")
            return False
    
    async def run_automation(self) -> bool:
        """Run the complete automation workflow"""
        logger.info("Starting TradeBot Sentinel automation")
        
        try:
            # Setup browser
            await self.setup_browser()
            
            # Login
            if not await self.login():
                logger.error("Login failed, aborting automation")
                return False
            
            # Navigate to trading
            if not await self.navigate_to_trading():
                logger.error("Failed to navigate to trading page, aborting automation")
                return False
            
            # Place trade order
            if not await self.place_trade_order():
                logger.error("Failed to place trade order")
                return False
            
            # Check if we captured any trade requests
            if self.trade_requests:
                logger.info(f"Captured {len(self.trade_requests)} trade requests")
                for i, req in enumerate(self.trade_requests):
                    logger.info(f"Trade request {i+1}: {req['url']}")
            else:
                logger.info("No trade requests captured")
            
            logger.info("Automation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            await self.take_screenshot("error_automation_failed.png", f"Automation failed: {e}")
            return False
        
        finally:
            await self.cleanup()
    
    async def cleanup(self) -> None:
        """Clean up browser resources"""
        logger.info("Cleaning up browser resources")
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='TradeBot Sentinel - Bulenox ProjectX Automation')
    parser.add_argument('--visible', action='store_true', help='Run in visible mode (not headless)')
    parser.add_argument('--test', action='store_true', help='Run in test mode (skip actual trading)')
    
    args = parser.parse_args()
    
    # Create and run automation
    sentinel = TradeBotSentinel(
        headless=not args.visible,
        test_mode=args.test
    )
    
    try:
        success = asyncio.run(sentinel.run_automation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()