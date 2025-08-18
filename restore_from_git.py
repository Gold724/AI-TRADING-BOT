#!/usr/bin/env python3
import subprocess
import os

def restore_original_file():
    """Restore the original file from git if available"""
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Git repository detected")
            
            # Restore the file from the last commit
            restore_result = subprocess.run(
                ['git', 'checkout', 'HEAD', '--', 'tradebot_sentinel_playwright.py'],
                capture_output=True, text=True
            )
            
            if restore_result.returncode == 0:
                print("✅ File restored from git")
                return True
            else:
                print(f"❌ Git restore failed: {restore_result.stderr}")
        else:
            print("❌ Not a git repository")
    except FileNotFoundError:
        print("❌ Git not found")
    
    # Fallback: Create a minimal working version
    print("🔧 Creating minimal working version...")
    
    minimal_content = '''#!/usr/bin/env python3
"""
TradeBot Sentinel - Automated Trading Bot for Bulenox ProjectX
A sophisticated Playwright-based automation agent for secure trading operations.
"""

import asyncio
import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class TradeBotSentinel:
    """Advanced trading automation agent with comprehensive error handling"""
    
    def __init__(self, playwright, username: str, password: str, headless: bool = True):
        """Initialize TradeBot Sentinel with enhanced configuration"""
        self.playwright = playwright
        self.username = username
        self.password = password
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.trade_intercepted = False
        self.curl_command = None
        
        # Enhanced selectors with fallbacks
        self.login_selectors = {
            'username': ['input[name="email"]', 'input[type="email"]', '#email', '.email-input'],
            'password': ['input[name="password"]', 'input[type="password"]', '#password', '.password-input'],
            'submit': ['button[type="submit"]', '.login-btn', '#login-button', 'input[type="submit"]']
        }
        
        self.dashboard_selectors = [
            '.dashboard', '#dashboard', '.main-content', '.trading-interface',
            '.user-dashboard', '[data-testid="dashboard"]'
        ]
        
        self.trading_selectors = {
            'order_tab': ['#ORDER', '.order-tab', '[data-tab="order"]'],
            'dom_tab': ['#DOM', '.dom-tab', '[data-tab="dom"]'],
            'buy_button': ['.buy-btn', '#buy-button', '[data-action="buy"]'],
            'sell_button': ['.sell-btn', '#sell-button', '[data-action="sell"]']
        }
    
    async def setup_browser(self):
        """Initialize browser with stealth configuration"""
        print("🚀 Initializing browser with stealth mode...")
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Setup network interception
        await self.setup_network_interception()
        
        self.page = await self.context.new_page()
        await self.inject_stealth_script()
        
        print("✅ Browser initialized successfully")
    
    async def setup_network_interception(self):
        """Setup network interception to capture trade requests"""
        async def handle_request(request):
            if request.method == 'POST':
                print(f"📡 Intercepted POST request: {request.url}")
                
                # Check if this is a trade request
                try:
                    post_data = request.post_data
                    if post_data and any(keyword in post_data.lower() for keyword in 
                                       ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell']):
                        print("🎯 Trade execution request detected!")
                        await self.save_curl_command(request)
                        self.trade_intercepted = True
                except Exception as e:
                    print(f"⚠️ Error processing request data: {e}")
        
        self.context.on('request', handle_request)
    
    async def save_curl_command(self, request):
        """Save intercepted request as cURL command"""
        headers = await request.all_headers()
        post_data = request.post_data or ''
        
        curl_parts = [f'curl -X POST "{request.url}"']
        
        for name, value in headers.items():
            curl_parts.append(f'-H "{name}: {value}"')
        
        if post_data:
            curl_parts.append(f'-d \'{post_data}\'')
        
        self.curl_command = ' \\
  '.join(curl_parts)
        
        # Save to file
        with open('trade.sh', 'w') as f:
            f.write(f"#!/bin/bash\n{self.curl_command}\n")
        
        print("💾 cURL command saved to trade.sh")
        
        # Convert to Python requests
        await self.convert_to_python()
    
    async def convert_to_python(self):
        """Convert cURL to Python requests code"""
        try:
            import curlconverter
            python_code = curlconverter.to_python(self.curl_command)
            
            with open('trade_request_full.py', 'w') as f:
                f.write(python_code)
            
            print("🐍 Python requests code saved to trade_request_full.py")
        except ImportError:
            print("⚠️ curlconverter not installed, installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'curlconverter'])
            # Retry conversion
            await self.convert_to_python()
        except Exception as e:
            print(f"❌ Error converting to Python: {e}")
    
    async def inject_stealth_script(self):
        """Inject JavaScript to avoid detection"""
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        """
        await self.page.add_init_script(stealth_script)
    
    async def login(self):
        """Perform secure login with comprehensive error handling"""
        print("🔐 Starting secure login process...")
        
        try:
            await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
            await self.page.wait_for_timeout(2000)
            
            # Handle username
            username_filled = False
            for selector in self.login_selectors['username']:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, self.username)
                    username_filled = True
                    print(f"✅ Username filled using selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not username_filled:
                raise Exception("❌ Could not find username field")
            
            # Handle password
            password_filled = False
            for selector in self.login_selectors['password']:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, self.password)
                    password_filled = True
                    print(f"✅ Password filled using selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not password_filled:
                raise Exception("❌ Could not find password field")
            
            # Submit login
            submitted = False
            for selector in self.login_selectors['submit']:
                try:
                    await self.page.click(selector)
                    submitted = True
                    print(f"✅ Login submitted using selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not submitted:
                raise Exception("❌ Could not find submit button")
            
            # Wait for login completion
            await self.wait_for_dashboard()
            print("✅ Login successful!")
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            await self.page.screenshot(path='login_failure.png')
            return False
    
    async def wait_for_dashboard(self):
        """Wait for dashboard with multiple selector fallbacks"""
        for attempt in range(3):
            for selector in self.dashboard_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    print(f"✅ Dashboard loaded with selector: {selector}")
                    return True
                except Exception:
                    continue
            
            if attempt < 2:
                print(f"⏳ Dashboard not found, retrying... (attempt {attempt + 1}/3)")
                await self.page.wait_for_timeout(2000)
        
        raise Exception("❌ Dashboard not found after 3 attempts")
    
    async def navigate_to_trading(self):
        """Navigate to trading page with enhanced error handling"""
        print("📈 Navigating to trading interface...")
        
        try:
            # Try to find trading link or navigate directly
            trading_url = 'https://bulenox.projectx.com/trading'
            await self.page.goto(trading_url, wait_until='networkidle')
            await self.page.wait_for_timeout(3000)
            
            # Verify trading interface is loaded
            trading_loaded = False
            for selector in ['.trading-interface', '#trading-panel', '.order-form']:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    trading_loaded = True
                    print(f"✅ Trading interface loaded with selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not trading_loaded:
                print("⚠️ Trading interface not detected, but continuing...")
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation to trading failed: {e}")
            await self.page.screenshot(path='trading_navigation_failure.png')
            return False
    
    async def place_trade_order(self, symbol='BTCUSDT', side='buy', amount='0.001'):
        """Attempt to place a trade order with comprehensive fallback handling"""
        print(f"📊 Attempting to place {side.upper()} order for {symbol}...")
        
        try:
            # Try ORDER tab first
            order_clicked = False
            for selector in self.trading_selectors['order_tab']:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    order_clicked = True
                    print(f"✅ ORDER tab clicked using selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not order_clicked:
                # Try DOM tab as fallback
                for selector in self.trading_selectors['dom_tab']:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.click(selector)
                        print(f"✅ DOM tab clicked as fallback using selector: {selector}")
                        break
                    except Exception:
                        continue
            
            await self.page.wait_for_timeout(2000)
            
            # Try to click buy/sell button based on side
            button_selectors = self.trading_selectors['buy_button'] if side.lower() == 'buy' else self.trading_selectors['sell_button']
            
            button_clicked = False
            for selector in button_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    button_clicked = True
                    print(f"✅ {side.upper()} button clicked using selector: {selector}")
                    break
                except Exception:
                    continue
            
            if not button_clicked:
                print(f"⚠️ Could not find {side.upper()} button, but trade request might still be intercepted")
            
            # Wait for potential network requests
            await self.page.wait_for_timeout(5000)
            
            if self.trade_intercepted:
                print("🎯 Trade execution request successfully intercepted!")
                return True
            else:
                print("⚠️ No trade execution request detected")
                return False
                
        except Exception as e:
            print(f"❌ Trade order placement failed: {e}")
            await self.page.screenshot(path='trade_order_failure.png')
            return False
    
    async def run_automation(self):
        """Run the complete automation sequence"""
        print("🤖 Starting TradeBot Sentinel automation...")
        
        try:
            await self.setup_browser()
            
            if not await self.login():
                return False
            
            if not await self.navigate_to_trading():
                return False
            
            if not await self.place_trade_order():
                print("⚠️ Trade order placement had issues, but continuing...")
            
            # Wait a bit more for any delayed requests
            await self.page.wait_for_timeout(10000)
            
            if self.trade_intercepted:
                print("✅ Automation completed successfully with trade interception!")
            else:
                print("⚠️ Automation completed but no trade requests were intercepted")
            
            return True
            
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return False
        finally:
            if self.browser:
                await self.browser.close()
                print("🔒 Browser closed")

async def main():
    """Main entry point"""
    # Check environment variables
    if not os.getenv('BULENOX_USERNAME') or not os.getenv('BULENOX_PASSWORD'):
        print("❌ Error: BULENOX_USERNAME and BULENOX_PASSWORD environment variables are required")
        print("Set them in PowerShell:")
        print('$env:BULENOX_USERNAME = "your_email@example.com"')
        print('$env:BULENOX_PASSWORD = "your_password"')
        return False
    
    headless = os.getenv('BULENOX_HEADLESS', 'true').lower() == 'true'
    
    async with async_playwright() as playwright:
        sentinel = TradeBotSentinel(
            playwright=playwright,
            username=os.getenv('BULENOX_USERNAME'),
            password=os.getenv('BULENOX_PASSWORD'),
            headless=headless
        )
        
        success = await sentinel.run_automation()
        return success

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open('tradebot_sentinel_playwright.py', 'w', encoding='utf-8') as f:
        f.write(minimal_content)
    
    print("✅ Minimal working version created!")
    return True

if __name__ == "__main__":
    restore_original_file()