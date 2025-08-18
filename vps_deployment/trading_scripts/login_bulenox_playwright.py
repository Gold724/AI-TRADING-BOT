#!/usr/bin/env python3
"""
AI Trading Sentinel - Enhanced Playwright Login with cURL Capture
================================================================
Advanced Bulenox login automation with comprehensive cURL capture capabilities
- Secure login using environment variables
- Robust element detection with fallback selectors
- Network request interception and cURL generation
- Trade execution detection and automation
- Screenshot capture for debugging
- Comprehensive error handling and retries
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import subprocess

class BulenoxPlaywrightBot:
    def __init__(self, headless=True, capture_mode=False):
        self.headless = headless
        self.capture_mode = capture_mode
        self.base_dir = Path.cwd()
        self.screenshots_dir = self.base_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Network capture storage
        self.captured_requests = []
        self.trade_requests = []
        
        # Login credentials from environment
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
            
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps and levels"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨",
            "NETWORK": "🌐",
            "TRADE": "💰"
        }.get(level, "ℹ️")
        
        print(f"[{timestamp}] {prefix} {message}")
        
    def capture_screenshot(self, page, name):
        """Capture screenshot for debugging"""
        try:
            screenshot_path = self.screenshots_dir / f"{name}_{int(time.time())}.png"
            page.screenshot(path=str(screenshot_path))
            self.log(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.log(f"Failed to capture screenshot: {str(e)}", "ERROR")
            return None
            
    def setup_network_interception(self, page):
        """Setup network request interception"""
        def handle_request(request):
            # Capture all requests if in capture mode
            if self.capture_mode:
                self.captured_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            # Log network activity
            self.log(f"Network: {request.method} {request.url}", "NETWORK")
            
            # Detect potential trade requests
            if self.is_trade_request(request):
                self.log(f"Trade request detected: {request.url}", "TRADE")
                self.save_trade_curl(request)
                
        page.on("request", handle_request)
        
    def is_trade_request(self, request):
        """Detect if request is a trade execution"""
        # Check URL patterns
        trade_url_patterns = [
            '/api/trade', '/trade', '/order', '/execute',
            '/buy', '/sell', '/position', '/market'
        ]
        
        url_lower = request.url.lower()
        if any(pattern in url_lower for pattern in trade_url_patterns):
            return True
            
        # Check POST data for trading keywords
        if request.method == 'POST' and request.post_data:
            try:
                post_data = request.post_data.lower()
                trade_keywords = [
                    'symbol', 'amount', 'price', 'order', 'trade',
                    'buy', 'sell', 'quantity', 'side', 'pair'
                ]
                
                if any(keyword in post_data for keyword in trade_keywords):
                    return True
                    
                # Try to parse as JSON
                try:
                    data = json.loads(request.post_data)
                    if any(key in str(data).lower() for key in trade_keywords):
                        return True
                except:
                    pass
                    
            except Exception:
                pass
                
        return False
        
    def save_trade_curl(self, request):
        """Save trade request as cURL command"""
        try:
            # Build cURL command
            curl_parts = ['curl']
            
            # Add method
            if request.method != 'GET':
                curl_parts.extend(['-X', request.method])
                
            # Add headers
            for name, value in request.headers.items():
                # Skip some headers that might cause issues
                if name.lower() not in ['host', 'content-length', 'connection']:
                    curl_parts.extend(['-H', f'"{name}: {value}"'])
                    
            # Add POST data
            if request.post_data:
                curl_parts.extend(['-d', f"'{request.post_data}'"])
                
            # Add URL
            curl_parts.append(f"'{request.url}'")
            
            # Join and save
            curl_command = ' '.join(curl_parts)
            
            # Save to trade.sh
            trade_file = self.base_dir / "trade.sh"
            trade_file.write_text(curl_command, encoding='utf-8')
            
            self.log(f"Trade cURL saved to: {trade_file}", "SUCCESS")
            
            # Also save to timestamped file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.base_dir / f"trade_backup_{timestamp}.sh"
            backup_file.write_text(curl_command, encoding='utf-8')
            
            # Convert to Python using curlconverter
            self.convert_curl_to_python(curl_command)
            
        except Exception as e:
            self.log(f"Failed to save trade cURL: {str(e)}", "ERROR")
            
    def convert_curl_to_python(self, curl_command):
        """Convert cURL to Python requests code"""
        try:
            # Check if curlconverter is available
            try:
                import curlconverter
            except ImportError:
                self.log("Installing curlconverter...", "INFO")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'curlconverter'], 
                             check=True, capture_output=True)
                import curlconverter
                
            # Convert cURL to Python
            python_code = curlconverter.curl_to_python(curl_command)
            
            # Save Python code
            python_file = self.base_dir / "trade_request_full.py"
            python_file.write_text(python_code, encoding='utf-8')
            
            self.log(f"Python requests code saved to: {python_file}", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to convert cURL to Python: {str(e)}", "ERROR")
            
    def wait_for_element_with_retry(self, page, selectors, timeout=10000, retries=3):
        """Wait for element with multiple selectors and retries"""
        if isinstance(selectors, str):
            selectors = [selectors]
            
        for attempt in range(retries):
            for selector in selectors:
                try:
                    element = page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        self.log(f"Found element with selector: {selector}")
                        return element
                except PlaywrightTimeoutError:
                    continue
                    
            if attempt < retries - 1:
                self.log(f"Retry {attempt + 1}/{retries} - waiting 2 seconds...", "WARNING")
                time.sleep(2)
                
        raise PlaywrightTimeoutError(f"Could not find element with any selector: {selectors}")
        
    def handle_time_sync_warning(self, page):
        """Handle time sync warning modal"""
        try:
            # Wait for potential time sync warning
            warning_selectors = [
                'div[class*="warning"]',
                'div[class*="modal"]',
                'div[class*="alert"]',
                '.time-sync-warning',
                '[data-testid="time-warning"]'
            ]
            
            for selector in warning_selectors:
                try:
                    warning = page.wait_for_selector(selector, timeout=3000)
                    if warning and warning.is_visible():
                        self.log("Time sync warning detected, attempting to dismiss...", "WARNING")
                        
                        # Try to find and click dismiss button
                        dismiss_selectors = [
                            'button[class*="close"]',
                            'button[class*="dismiss"]',
                            'button:has-text("OK")',
                            'button:has-text("Close")',
                            'button:has-text("Continue")',
                            '.modal-close',
                            '[data-testid="close-button"]'
                        ]
                        
                        for dismiss_selector in dismiss_selectors:
                            try:
                                dismiss_btn = page.wait_for_selector(dismiss_selector, timeout=2000)
                                if dismiss_btn and dismiss_btn.is_visible():
                                    dismiss_btn.click()
                                    self.log("Time sync warning dismissed", "SUCCESS")
                                    time.sleep(1)
                                    return True
                            except:
                                continue
                                
                        # If no dismiss button found, try pressing Escape
                        page.keyboard.press('Escape')
                        time.sleep(1)
                        return True
                        
                except PlaywrightTimeoutError:
                    continue
                    
        except Exception as e:
            self.log(f"Error handling time sync warning: {str(e)}", "ERROR")
            
        return False
        
    def login(self, page):
        """Perform login with robust error handling"""
        try:
            self.log("Navigating to Bulenox login page...")
            page.goto("https://bulenox.projectx.com/login", wait_until="networkidle")
            
            # Handle potential time sync warning
            self.handle_time_sync_warning(page)
            
            # Capture screenshot before login
            self.capture_screenshot(page, "before_login")
            
            # Wait for and fill username
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="username"]',
                'input[placeholder*="email"]',
                '#username',
                '#email',
                '.username-input',
                '.email-input'
            ]
            
            username_field = self.wait_for_element_with_retry(page, username_selectors)
            username_field.fill(self.username)
            self.log("Username filled")
            
            # Wait for and fill password
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password',
                '.password-input'
            ]
            
            password_field = self.wait_for_element_with_retry(page, password_selectors)
            password_field.fill(self.password)
            self.log("Password filled")
            
            # Find and click login button
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'input[type="submit"]',
                '.login-button',
                '.signin-button',
                '#login-btn',
                '#signin-btn'
            ]
            
            login_button = self.wait_for_element_with_retry(page, login_selectors)
            login_button.click()
            self.log("Login button clicked")
            
            # Handle potential time sync warning after login
            time.sleep(2)
            self.handle_time_sync_warning(page)
            
            # Wait for successful login (dashboard indicators)
            dashboard_selectors = [
                '.dashboard',
                '.main-content',
                '.trading-interface',
                '[data-testid="dashboard"]',
                '.user-menu',
                '.account-info',
                'nav[class*="main"]',
                '.sidebar',
                '.header-user'
            ]
            
            try:
                self.wait_for_element_with_retry(page, dashboard_selectors, timeout=15000)
                self.log("Login successful - dashboard loaded", "SUCCESS")
                
                # Capture screenshot after successful login
                self.capture_screenshot(page, "after_login")
                return True
                
            except PlaywrightTimeoutError:
                self.log("Dashboard not detected, checking for login errors...", "WARNING")
                
                # Check for error messages
                error_selectors = [
                    '.error-message',
                    '.alert-danger',
                    '.login-error',
                    '[class*="error"]',
                    '[data-testid="error"]'
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = page.wait_for_selector(selector, timeout=2000)
                        if error_element and error_element.is_visible():
                            error_text = error_element.text_content()
                            self.log(f"Login error detected: {error_text}", "ERROR")
                            self.capture_screenshot(page, "login_error")
                            return False
                    except:
                        continue
                        
                # If no specific error found, assume login failed
                self.log("Login appears to have failed - no dashboard detected", "ERROR")
                self.capture_screenshot(page, "login_failed")
                return False
                
        except Exception as e:
            self.log(f"Login error: {str(e)}", "ERROR")
            self.capture_screenshot(page, "login_exception")
            return False
            
    def navigate_to_trading(self, page):
        """Navigate to trading interface"""
        try:
            self.log("Navigating to trading interface...")
            
            # Look for trading/trade navigation links
            trading_selectors = [
                'a[href*="trade"]',
                'a[href*="trading"]',
                'a:has-text("Trade")',
                'a:has-text("Trading")',
                '.nav-trade',
                '.nav-trading',
                '[data-testid="trade-link"]',
                'nav a[class*="trade"]'
            ]
            
            for selector in trading_selectors:
                try:
                    trade_link = page.wait_for_selector(selector, timeout=3000)
                    if trade_link and trade_link.is_visible():
                        trade_link.click()
                        self.log(f"Clicked trading link: {selector}")
                        break
                except:
                    continue
            else:
                # If no trading link found, try direct URL
                self.log("No trading link found, trying direct URL...")
                page.goto("https://bulenox.projectx.com/trade", wait_until="networkidle")
                
            # Wait for trading interface to load
            trading_interface_selectors = [
                '.trading-interface',
                '.trade-panel',
                '.order-form',
                '.trading-view',
                '[data-testid="trading-interface"]',
                '.buy-sell-buttons',
                '.order-book'
            ]
            
            self.wait_for_element_with_retry(page, trading_interface_selectors, timeout=15000)
            self.log("Trading interface loaded successfully", "SUCCESS")
            
            # Capture screenshot of trading interface
            self.capture_screenshot(page, "trading_interface")
            return True
            
        except Exception as e:
            self.log(f"Failed to navigate to trading interface: {str(e)}", "ERROR")
            self.capture_screenshot(page, "trading_navigation_failed")
            return False
            
    def attempt_trade_order(self, page):
        """Attempt to place a test trade order to capture the request"""
        try:
            self.log("Attempting to place test trade order...")
            
            # Look for order form elements
            # First try ORDER tab
            order_tab_selectors = [
                'button:has-text("ORDER")',
                'tab:has-text("ORDER")',
                '.order-tab',
                '[data-testid="order-tab"]'
            ]
            
            for selector in order_tab_selectors:
                try:
                    order_tab = page.wait_for_selector(selector, timeout=3000)
                    if order_tab and order_tab.is_visible():
                        order_tab.click()
                        self.log("Clicked ORDER tab")
                        time.sleep(1)
                        break
                except:
                    continue
                    
            # Look for trading pair/symbol selector
            symbol_selectors = [
                'select[name*="symbol"]',
                'select[name*="pair"]',
                '.symbol-selector',
                '.pair-selector',
                '[data-testid="symbol-select"]'
            ]
            
            # Look for amount/quantity input
            amount_selectors = [
                'input[name*="amount"]',
                'input[name*="quantity"]',
                'input[name*="size"]',
                '.amount-input',
                '.quantity-input'
            ]
            
            # Look for buy/sell buttons
            buy_selectors = [
                'button:has-text("Buy")',
                'button:has-text("BUY")',
                '.buy-button',
                '[data-testid="buy-button"]'
            ]
            
            # Try to interact with form elements (without actually submitting)
            try:
                # Try to select a symbol
                for selector in symbol_selectors:
                    try:
                        symbol_element = page.wait_for_selector(selector, timeout=2000)
                        if symbol_element and symbol_element.is_visible():
                            # Just click to open dropdown, don't select
                            symbol_element.click()
                            time.sleep(0.5)
                            page.keyboard.press('Escape')  # Close dropdown
                            self.log("Interacted with symbol selector")
                            break
                    except:
                        continue
                        
                # Try to interact with amount field
                for selector in amount_selectors:
                    try:
                        amount_element = page.wait_for_selector(selector, timeout=2000)
                        if amount_element and amount_element.is_visible():
                            amount_element.click()
                            amount_element.fill("0.01")  # Small test amount
                            self.log("Filled amount field with test value")
                            break
                    except:
                        continue
                        
                # Hover over buy button (don't click to avoid actual trade)
                for selector in buy_selectors:
                    try:
                        buy_button = page.wait_for_selector(selector, timeout=2000)
                        if buy_button and buy_button.is_visible():
                            buy_button.hover()
                            self.log("Hovered over buy button")
                            break
                    except:
                        continue
                        
            except Exception as e:
                self.log(f"Error interacting with trade form: {str(e)}", "WARNING")
                
            # Wait a bit to see if any network requests were triggered
            time.sleep(3)
            
            self.log("Trade order interaction completed")
            return True
            
        except Exception as e:
            self.log(f"Failed to attempt trade order: {str(e)}", "ERROR")
            self.capture_screenshot(page, "trade_attempt_failed")
            return False
            
    def save_captured_requests(self):
        """Save all captured network requests"""
        if not self.captured_requests:
            self.log("No network requests captured", "WARNING")
            return
            
        # Save all requests to JSON file
        requests_file = self.base_dir / "captured_requests.json"
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(self.captured_requests, f, indent=2, ensure_ascii=False)
            
        self.log(f"Saved {len(self.captured_requests)} network requests to: {requests_file}")
        
        # Save trade-specific requests
        if self.trade_requests:
            trade_file = self.base_dir / "trade_requests.json"
            with open(trade_file, 'w', encoding='utf-8') as f:
                json.dump(self.trade_requests, f, indent=2, ensure_ascii=False)
                
            self.log(f"Saved {len(self.trade_requests)} trade requests to: {trade_file}")
            
    def run(self):
        """Main execution flow"""
        self.log("Starting Bulenox Playwright automation...", "INFO")
        self.log("=" * 60)
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions'
                ]
            )
            
            try:
                # Create context and page
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = context.new_page()
                
                # Setup network interception
                self.setup_network_interception(page)
                
                # Execute main flow
                success = True
                
                # Step 1: Login
                if not self.login(page):
                    self.log("Login failed, aborting...", "CRITICAL")
                    success = False
                else:
                    # Step 2: Navigate to trading
                    if not self.navigate_to_trading(page):
                        self.log("Failed to navigate to trading interface", "ERROR")
                        success = False
                    else:
                        # Step 3: Attempt trade interaction (if in capture mode)
                        if self.capture_mode:
                            self.attempt_trade_order(page)
                            
                        # Wait a bit more to capture any additional requests
                        time.sleep(5)
                        
                # Save captured data
                if self.capture_mode:
                    self.save_captured_requests()
                    
                # Final summary
                self.log("=" * 60)
                if success:
                    self.log("🎉 Automation completed successfully!", "SUCCESS")
                else:
                    self.log("❌ Automation completed with errors", "ERROR")
                    
                self.log(f"Screenshots saved to: {self.screenshots_dir}")
                if self.capture_mode:
                    self.log(f"Network requests captured: {len(self.captured_requests)}")
                    
                return success
                
            except Exception as e:
                self.log(f"Unexpected error: {str(e)}", "CRITICAL")
                self.capture_screenshot(page, "critical_error")
                return False
                
            finally:
                # Cleanup
                try:
                    browser.close()
                except:
                    pass
                    
def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description='Bulenox Playwright Automation')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run in headless mode (default: True)')
    parser.add_argument('--headed', action='store_true',
                       help='Run in headed mode (overrides --headless)')
    parser.add_argument('--capture-all', action='store_true',
                       help='Capture all network requests and attempt trade interaction')
    
    args = parser.parse_args()
    
    # Determine headless mode
    headless = args.headless and not args.headed
    
    try:
        bot = BulenoxPlaywrightBot(headless=headless, capture_mode=args.capture_all)
        success = bot.run()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"🚨 Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()