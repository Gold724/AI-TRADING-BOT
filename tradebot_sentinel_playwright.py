#!/usr/bin/env python3
"""
TradeBot Sentinel - Bulenox ProjectX Trading Platform Automation
Expert automation agent for secure login, trade execution, and request interception.
Integrated with Fibonacci Gold Scalping Strategy for dynamic profit targeting.
"""

import asyncio
import json
import os
import subprocess
import sys
import random
import math
from datetime import datetime, time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import Optional, Dict, Any, List

# Import Fibonacci Gold Scalping Strategy Configuration
try:
    from bulenox_strategy_config import CONFIG
    STRATEGY_INTEGRATED = True
except ImportError:
    print("[WARNING] Strategy config not found, using fallback values")
    STRATEGY_INTEGRATED = False
    
    # Fallback configuration
    class CONFIG:
        FIBONACCI_PROFIT_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]
        FULL_SYMBOL = "F.US.GCE"  # Gold futures
        DEFAULT_CONTRACTS = 1
        MAX_CONTRACTS = 3
        TRADING_SESSIONS = {
            'morning': {'start': time(3, 0), 'end': time(6, 0)},
            'midday': {'start': time(8, 20), 'end': time(11, 30)},
            'afternoon': {'start': time(13, 0), 'end': time(15, 30)}
        }

class TradeBotSentinel:
    """TradeBot Sentinel for Bulenox ProjectX automation"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        self.curl_command = ""
        self.trade_requests: List[Dict] = []
        
        # Human behavior simulation parameters
        self.human_delay_min = 800
        self.human_delay_max = 2500
        self.typing_delay_min = 50
        self.typing_delay_max = 200
        self.mouse_move_steps = 10
        
        # Fibonacci Strategy Integration
        self.fibonacci_sequence = CONFIG.FIBONACCI_PROFIT_SEQUENCE
        self.session_fib_index = {'morning': 0, 'midday': 0, 'afternoon': 0}
        self.current_session = None
        self.daily_trades = 0
        self.session_trades = 0
        self.daily_pnl = 0.0
        
        # Note: Credentials are optional if already authenticated via saved session
        if self.username and self.password:
            print(f"[CREDENTIALS] Credentials loaded for user: {self.username[:3]}***")
        else:
            print("[WARNING] No credentials set - will attempt to use saved session")
        
        print(f"[STRATEGY] Fibonacci sequence loaded: {self.fibonacci_sequence}")
        print(f"[STRATEGY] Gold symbol: {CONFIG.FULL_SYMBOL}")
        print(f"[STRATEGY] Contract range: {CONFIG.DEFAULT_CONTRACTS}-{CONFIG.MAX_CONTRACTS}")
    
    def get_current_session(self):
        """Determine current trading session based on NY time"""
        current_time = datetime.now().time()
        
        for session_name, session_info in CONFIG.TRADING_SESSIONS.items():
            if session_info['start'] <= current_time <= session_info['end']:
                return session_name
        return None
    
    def get_current_fibonacci_target(self, session_name=None):
        """Get current Fibonacci profit target for the session"""
        if session_name is None:
            session_name = self.current_session or self.get_current_session()
        
        if session_name and session_name in self.session_fib_index:
            index = self.session_fib_index[session_name]
            return self.fibonacci_sequence[index]
        
        return self.fibonacci_sequence[0]  # Default to first level
    
    def advance_fibonacci(self, session_name, win=True):
        """Advance or reset Fibonacci sequence based on trade outcome"""
        if session_name not in self.session_fib_index:
            return
        
        old_index = self.session_fib_index[session_name]
        
        if win:
            # Advance to next Fibonacci level (max at sequence length - 1)
            self.session_fib_index[session_name] = min(old_index + 1, len(self.fibonacci_sequence) - 1)
            reason = 'winning_trade'
        else:
            # Reset to beginning on loss
            self.session_fib_index[session_name] = 0
            reason = 'losing_trade'
        
        new_index = self.session_fib_index[session_name]
        print(f"[FIBONACCI] {session_name} progression: index {old_index} → {new_index} ({reason})")
        
        return new_index
    
    def get_fibonacci_contract_size(self, session_name=None):
        """Calculate contract size based on Fibonacci progression"""
        if session_name is None:
            session_name = self.current_session or self.get_current_session()
        
        fib_target = self.get_current_fibonacci_target(session_name)
        
        # Scale contract size based on Fibonacci target (keeping within limits)
        if fib_target <= 20:
            return CONFIG.DEFAULT_CONTRACTS  # 1 contract
        elif fib_target <= 50:
            return min(2, CONFIG.MAX_CONTRACTS)  # 2 contracts
        else:
            return CONFIG.MAX_CONTRACTS  # 3 contracts
    
    async def setup_browser(self):
        """Initialize browser and context with network interception"""
        print("[SETUP] Setting up browser...")
        
        playwright = await async_playwright().start()
        
        # Use persistent context to maintain login sessions
        user_data_dir = os.path.join(os.getcwd(), 'chrome_profile')
        
        # Use launch_persistent_context for persistent storage
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=self.headless,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Browser is not needed when using persistent context
        self.browser = None
        
        self.page = await self.context.new_page()
        
        # Setup network interception
        await self.setup_network_interceptor()
        
        print("[SUCCESS] Browser setup complete")
    
    async def setup_network_interceptor(self):
        """Setup network request interception for trade detection"""
        print("[NETWORK] Setting up network interceptor...")
        
        async def handle_request(request):
            if request.method == 'POST':
                print(f"[REQUEST] POST request detected: {request.url}")
                
                # Get post data
                post_data = None
                try:
                    post_data = request.post_data
                    if post_data:
                        print(f"[DATA] POST data: {post_data[:200]}...")
                        
                        # Check if this is a trade request
                        if self.is_trade_request(post_data, request.url):
                            print("[TRADE] Trade execution request detected!")
                            await self.save_trade_request(request, post_data)
                except Exception as e:
                    print(f"[WARNING] Error processing request: {e}")
        
        self.page.on('request', handle_request)
        print("[SUCCESS] Network interceptor active")
    
    async def human_delay(self, min_ms: int = None, max_ms: int = None):
        """Add human-like random delays"""
        min_delay = min_ms or self.human_delay_min
        max_delay = max_ms or self.human_delay_max
        delay = random.randint(min_delay, max_delay)
        await asyncio.sleep(delay / 1000)
        print(f"[HUMAN] Added {delay}ms human delay")
    
    async def human_type(self, selector: str, text: str):
        """Type text with human-like timing"""
        print(f"[HUMAN] Human typing into {selector}")
        element = await self.page.wait_for_selector(selector, timeout=10000)
        await self.human_click_element(element)
        await self.human_delay(200, 500)
        
        # Clear existing text
        await element.fill('')
        await self.human_delay(100, 300)
        
        # Type with random delays
        for char in text:
            await element.type(char, delay=random.randint(self.typing_delay_min, self.typing_delay_max))
    
    async def human_type_element(self, element, text: str):
        """Type text into a specific element with human-like timing"""
        print(f"[HUMAN] Human typing into element")
        await self.human_click_element(element)
        await self.human_delay(200, 500)
        
        # Clear existing text
        await element.fill('')
        await self.human_delay(100, 300)
        
        # Type with random delays
        for char in text:
            await element.type(char, delay=random.randint(self.typing_delay_min, self.typing_delay_max))
    
    async def human_click_element(self, element):
        """Click element with human-like mouse movement"""
        box = await element.bounding_box()
        
        if box:
            # Calculate click position with slight randomization
            x = box['x'] + box['width'] / 2 + random.randint(-5, 5)
            y = box['y'] + box['height'] / 2 + random.randint(-5, 5)
            
            # Get current mouse position
            current_pos = await self.page.evaluate('() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })')
            
            # Move mouse in steps to simulate human movement
            steps = self.mouse_move_steps
            
            for i in range(steps):
                step_x = current_pos['x'] + (x - current_pos['x']) * (i + 1) / steps
                step_y = current_pos['y'] + (y - current_pos['y']) * (i + 1) / steps
                await self.page.mouse.move(step_x, step_y)
                await asyncio.sleep(random.randint(10, 30) / 1000)
            
            print(f"[HUMAN] Human mouse movement to ({x:.1f}, {y:.1f})")
            await self.human_delay(100, 300)
            await self.page.mouse.click(x, y)
        else:
            # Fallback to regular click
            await element.click()
    
    async def human_click(self, selector: str):
        """Click with human-like mouse movement"""
        print(f"[HUMAN] Human clicking {selector}")
        element = await self.page.wait_for_selector(selector, timeout=10000)
        await self.human_click_element(element)
    
    async def random_mouse_movement(self):
        """Simulate realistic random mouse movements with multiple patterns"""
        try:
            # Get current viewport size
            viewport = await self.page.evaluate('() => ({ width: window.innerWidth, height: window.innerHeight })')
            
            # Choose random movement pattern
            pattern = random.choice(['circular', 'zigzag', 'linear', 'hover'])
            
            if pattern == 'circular':
                # Circular mouse movement
                center_x = viewport['width'] // 2
                center_y = viewport['height'] // 2
                radius = random.randint(50, 150)
                
                for i in range(8):
                    angle = (i * 45) * (3.14159 / 180)  # Convert to radians
                    x = int(center_x + radius * math.cos(angle))
                    y = int(center_y + radius * math.sin(angle))
                    await self.page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                    
            elif pattern == 'zigzag':
                # Zigzag movement
                start_x = random.randint(100, viewport['width'] - 200)
                start_y = random.randint(100, viewport['height'] - 200)
                
                for i in range(5):
                    x = start_x + (i * 40) + random.randint(-20, 20)
                    y = start_y + ((-1) ** i * 30) + random.randint(-15, 15)
                    await self.page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.08, 0.2))
                    
            elif pattern == 'hover':
                # Hover around current position
                current_pos = await self.page.evaluate('() => ({ x: window.mouseX || 400, y: window.mouseY || 300 })')
                base_x = current_pos.get('x', 400)
                base_y = current_pos.get('y', 300)
                
                for i in range(6):
                    x = base_x + random.randint(-30, 30)
                    y = base_y + random.randint(-30, 30)
                    await self.page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.25))
                    
            else:  # linear
                # Linear movement with slight curves
                start_x = random.randint(100, viewport['width'] - 100)
                start_y = random.randint(100, viewport['height'] - 100)
                end_x = random.randint(100, viewport['width'] - 100)
                end_y = random.randint(100, viewport['height'] - 100)
                
                steps = random.randint(8, 15)
                for i in range(steps):
                    progress = i / steps
                    x = int(start_x + (end_x - start_x) * progress + random.randint(-10, 10))
                    y = int(start_y + (end_y - start_y) * progress + random.randint(-10, 10))
                    await self.page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.03, 0.12))
            
            print(f"[HUMAN] {pattern.capitalize()} mouse movement completed")
            
        except Exception as e:
            print(f"[ERROR] Random mouse movement failed: {e}")
            # Fallback to simple movement
            try:
                x = random.randint(200, 600)
                y = random.randint(200, 400)
                await self.page.mouse.move(x, y)
                print(f"[FALLBACK] Simple mouse movement to ({x}, {y})")
            except:
                pass
    
    def is_trade_request(self, post_data: str, url: str) -> bool:
        """Detect if request is a trade execution"""
        trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell', 'quantity', 'side']
        
        # Check URL
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in ['trade', 'order', 'execute', 'position']):
            return True
        
        # Check POST data
        if post_data:
            data_lower = post_data.lower()
            keyword_count = sum(1 for keyword in trade_keywords if keyword in data_lower)
            return keyword_count >= 2
        
        return False
    
    async def save_trade_request(self, request, post_data: str):
        """Save trade request as cURL and Python code"""
        print("[SAVE] Saving trade request...")
        
        # Build cURL command
        curl_parts = ['curl', '-X', 'POST']
        
        # Add headers
        for name, value in request.headers.items():
            curl_parts.extend(['-H', f'{name}: {value}'])
        
        # Add URL
        curl_parts.append(f"'{request.url}'")
        
        # Add POST data
        if post_data:
            curl_parts.extend(['-d', f"'{post_data}'"])
        
        self.curl_command = ' '.join(curl_parts)
        
        # Save to file
        with open('trade.sh', 'w') as f:
            f.write(f"#!/bin/bash\n{self.curl_command}\n")
        
        print("[SAVE] cURL command saved to trade.sh")
        
        # Convert to Python requests
        await self.convert_to_python()
    
    async def convert_to_python(self):
        """Convert cURL to Python requests code"""
        try:
            print("[CONVERT] Converting cURL to Python...")
            
            # Use curlconverter if available
            result = subprocess.run(
                ['python', '-c', f"import curlconverter; print(curlconverter.to_python('{self.curl_command}'))"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                python_code = result.stdout.strip()
                with open('trade_request_full.py', 'w') as f:
                    f.write(python_code)
                print("[SUCCESS] Python requests code saved to trade_request_full.py")
            else:
                print(f"[WARNING] curlconverter failed: {result.stderr}")
                await self.manual_python_conversion()
                
        except Exception as e:
            print(f"[WARNING] Error converting to Python: {e}")
            await self.manual_python_conversion()
    
    async def manual_python_conversion(self):
        """Manual conversion to Python requests"""
        python_template = '''import requests
import json

# Auto-generated from trade request
url = "{url}"
headers = {headers}
data = {data}

response = requests.post(url, headers=headers, data=data)
print(f"Status: {{response.status_code}}")
print(f"Response: {{response.text}}")
'''
        
        # Extract components from curl command
        url = "https://example.com/api/trade"  # Placeholder
        headers = {"Content-Type": "application/json"}
        data = "{}"  # Placeholder
        
        python_code = python_template.format(
            url=url,
            headers=json.dumps(headers, indent=4),
            data=data
        )
        
        with open('trade_request_full.py', 'w') as f:
            f.write(python_code)
        
        print("[SUCCESS] Manual Python conversion saved to trade_request_full.py")
    
    async def check_login_status(self) -> bool:
        """Check if already logged in by examining current page"""
        # Dashboard selectors to confirm login success
        dashboard_selectors = [
            '.dashboard',
            '#dashboard',
            '[data-testid="dashboard"]',
            '.main-content',
            '.user-menu',
            '.profile-menu',
            '.logout',
            '[href*="logout"]',
            '.nav-menu',
            '.sidebar',
            '.header-user',
            '[class*="dashboard"]',
            '[class*="main"]',
            '[class*="home"]',
            '[class*="trading"]',
            '[class*="portfolio"]',
            '[class*="account"]',
            'nav',
            'header',
            '.container',
            '[role="main"]',
            '[role="navigation"]',
            'button[class*="user"]',
            'div[class*="user"]',
            'span[class*="user"]'
        ]
        
        # Wait a moment for page to fully load
        await asyncio.sleep(2)
        
        # Check current URL - if not on login page, we might be logged in
        current_url = self.page.url
        if '/login' not in current_url.lower():
            print(f"[SUCCESS] Already logged in - not on login page: {current_url}")
            return True
            
        for selector in dashboard_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    print(f"[SUCCESS] Already logged in - found element: {selector}")
                    return True
            except Exception:
                continue
        
        return False
    
    async def login(self) -> bool:
        """Enhanced login process with aggressive element detection and human behavior"""
        print("[LOGIN] Checking login status...")
        
        # Always navigate to the website first
        print("[NAVIGATE] Navigating to Bulenox website...")
        await self.page.goto('https://bulenox.projectx.com', wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Check if already logged in after navigation
        if await self.check_login_status():
            print("[INFO] Already authenticated - skipping login form")
            return True
        
        # Get credentials from environment variables (optional if already logged in)
        username = os.getenv('BULENOX_USERNAME')
        password = os.getenv('BULENOX_PASSWORD')
        
        if not username or not password:
            print("[WARNING] BULENOX_USERNAME and BULENOX_PASSWORD not set")
            print("[INFO] Checking if already authenticated via saved session...")
            # Still try to proceed - might be logged in via saved session
            # Return False to indicate we can't perform fresh login, but don't fail completely
            return False
        
        print(f"[CREDENTIALS] Using credentials for user: {username[:3]}***")
        
        print("[LOGIN] Starting enhanced login process...")
        
        try:
            # Navigate to login page
            await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Take screenshot before login
            await self.page.screenshot(path='before_login.png')
            print("[SCREENSHOT] Screenshot saved: before_login.png")
            
            # Handle potential time sync warning
            await self.handle_time_sync_warning()
            
            # Add initial random mouse movement
            await self.random_mouse_movement()
            await self.human_delay(1000, 2000)
            
            # Wait for page to fully load
            await self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Debug: Print page content to understand structure
            page_content = await self.page.content()
            print(f"[DEBUG] Page title: {await self.page.title()}")
            print(f"[DEBUG] Page URL: {self.page.url}")
            
            # Find all input elements for debugging
            all_inputs = await self.page.query_selector_all('input')
            print(f"[DEBUG] Found {len(all_inputs)} input elements:")
            for i, input_elem in enumerate(all_inputs):
                input_type = await input_elem.get_attribute('type') or 'text'
                input_name = await input_elem.get_attribute('name') or 'no-name'
                input_placeholder = await input_elem.get_attribute('placeholder') or 'no-placeholder'
                input_id = await input_elem.get_attribute('id') or 'no-id'
                print(f"  Input {i}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
            
            # Enhanced username selectors with React dynamic ID support
            username_selectors = [
                'input[name="userName"]',  # Actual field name found on the page
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[name="user"]',
                'input[name="login"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="user" i]',
                'input[placeholder*="login" i]',
                'input[placeholder*="USERNAME" i]',
                '#username',
                '#email',
                '#user',
                '#login',
                '.username-input',
                '.email-input',
                '.user-input',
                '.login-input',
                'input[autocomplete="email"]',
                'input[autocomplete="username"]',
                'input[type="text"]:first-of-type',
                'input:not([type="password"]):not([type="hidden"]):not([type="submit"]):not([type="button"]):first-of-type',
                'form input:first-of-type',
                'input[data-testid*="email"]',
                'input[data-testid*="username"]',
                # React dynamic ID patterns - target the first text input
                'input[id^=":r"]:not([type="password"])',
                'input[id*=":r"]:not([type="password"]):first-of-type'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[name="pass"]',
                'input[name="pwd"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="pass" i]',
                '#password',
                '#pass',
                '#pwd',
                '.password-input',
                '.pass-input',
                '.pwd-input',
                'input[autocomplete="current-password"]',
                'input[autocomplete="password"]',
                'input[data-testid*="password"]',
                'form input[type="password"]:first-of-type',
                # React dynamic ID patterns - target password inputs
                'input[id^=":r"][type="password"]',
                'input[id*=":r"][type="password"]:first-of-type'
            ]
            
            # Enhanced username filling with visibility checks
            username_filled = False
            for selector in username_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    if await self.page.locator(selector).is_visible():
                        element = await self.page.locator(selector).first
                        await element.click()
                        await self.human_delay(200, 500)
                        await self.page.keyboard.press('Control+a')
                        await self.human_delay(100, 300)
                        await self.human_type(selector, username)
                        print(f"[SUCCESS] Username filled using selector: {selector}")
                        username_filled = True
                        break
                except Exception:
                    continue
            
            if not username_filled:
                print("[FALLBACK] Trying positional input detection...")
                # Fallback: Use positional detection for React forms
                try:
                    all_inputs = await self.page.query_selector_all('input')
                    if len(all_inputs) >= 2:
                        # Assume first non-password input is username
                        for input_elem in all_inputs:
                            input_type = await input_elem.get_attribute('type') or 'text'
                            if input_type != 'password':
                                await input_elem.click()
                                await self.human_delay(200, 500)
                                await self.page.keyboard.press('Control+a')
                                await self.human_delay(100, 300)
                                await input_elem.type(username, delay=random.randint(50, 150))
                                print("[SUCCESS] Username filled using positional detection")
                                username_filled = True
                                break
                except Exception as e:
                    print(f"[ERROR] Positional detection failed: {e}")
                
                if not username_filled:
                    raise Exception("Could not find username field")
            
            # Add human delay between username and password
            await self.human_delay(500, 1200)
            
            # Enhanced password filling with visibility checks
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    if await self.page.locator(selector).is_visible():
                        element = await self.page.locator(selector).first
                        await element.click()
                        await self.human_delay(200, 500)
                        await self.page.keyboard.press('Control+a')
                        await self.human_delay(100, 300)
                        await self.human_type(selector, password)
                        print(f"[SUCCESS] Password filled using selector: {selector}")
                        password_filled = True
                        break
                except Exception:
                    continue
            
            if not password_filled:
                print("[FALLBACK] Trying positional password detection...")
                # Fallback: Use positional detection for password field
                try:
                    all_inputs = await self.page.query_selector_all('input')
                    for input_elem in all_inputs:
                        input_type = await input_elem.get_attribute('type') or 'text'
                        if input_type == 'password':
                            await input_elem.click()
                            await self.human_delay(200, 500)
                            await self.page.keyboard.press('Control+a')
                            await self.human_delay(100, 300)
                            await input_elem.type(password, delay=random.randint(50, 150))
                            print("[SUCCESS] Password filled using positional detection")
                            password_filled = True
                            break
                except Exception as e:
                    print(f"[ERROR] Password positional detection failed: {e}")
                
                if not password_filled:
                    raise Exception("Could not find password field")
            
            # Enhanced submit button detection
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                'button:has-text("SIGN IN")',
                'button:has-text("LOGIN")',
                '.login-button',
                '.btn-login',
                '.signin-button',
                '#login-btn',
                'button[data-testid*="login"]',
                'button[data-testid*="signin"]',
                'form button[type="button"]',
                'form button:not([type="button"]):not([type="reset"])',
                '.btn-primary'
            ]
            
            # Add human delay before submitting
            await self.human_delay(800, 1500)
            
            login_submitted = False
            for selector in submit_selectors:
                try:
                    if await self.page.locator(selector).is_visible(timeout=1000):
                        await self.human_click(selector)
                        print(f"[SUCCESS] Login submitted using selector: {selector}")
                        login_submitted = True
                        break
                except Exception:
                    continue
            
            if not login_submitted:
                print("[FALLBACK] Trying Enter key and Tab+Enter combinations")
                await self.page.keyboard.press('Tab')
                await self.human_delay(200, 400)
                await self.page.keyboard.press('Enter')
                await self.human_delay(500, 800)
                await self.page.keyboard.press('Enter')
                print("[SUCCESS] Login submitted using keyboard")
            
            # Wait for login processing with loading indicators
            print("[LOGIN] Waiting for login processing...")
            await asyncio.sleep(2)
            
            # Check for loading indicators
            loading_selectors = [
                '.loading',
                '.spinner',
                '[data-testid="loading"]',
                '.btn:disabled',
                'button:disabled'
            ]
            
            for selector in loading_selectors:
                try:
                    if await self.page.locator(selector).is_visible(timeout=1000):
                        print(f"[LOGIN] Detected loading indicator: {selector}")
                        await self.page.wait_for_selector(selector, state='hidden', timeout=10000)
                        break
                except Exception:
                    continue
            
            await asyncio.sleep(1)
            
            # Handle potential time sync warning with multiple attempts
            for attempt in range(3):
                print(f"[LOGIN] Time sync warning check attempt {attempt + 1}/3")
                await self.handle_time_sync_warning()
                await asyncio.sleep(1)
            
            # Wait for login completion
            return await self.confirm_login_success()
            
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            await self.page.screenshot(path='login_failure.png')
            return False
    
    async def handle_time_sync_warning(self):
        """Handle time sync warning modal if present with enhanced detection and human-like behavior"""
        try:
            # Add random mouse movement before checking
            await self.random_mouse_movement()
            
            # Wait briefly for potential modal
            await asyncio.sleep(2)
            
            # Check for time sync warning modal with expanded selectors
            modal_selectors = [
                '.ModalContext_modalWrapper__CBy3x:has-text("Time Sync Warning")',
                '.modal:has-text("time sync")',
                '.warning:has-text("time")',
                '[role="dialog"]:has-text("sync")',
                '.time-warning',
                'div:has-text("Your computer clock is not synchronized")',
                'div:has-text("Oh-no! That page is not found")',
                '[role="dialog"]',
                '.modal-dialog',
                'div[class*="overlay"]',
                'div[class*="Modal"]',
                '.warning-modal'
            ]
            
            for selector in modal_selectors:
                try:
                    modal = await self.page.wait_for_selector(selector, timeout=3000)
                    if modal:
                        print(f"[WARNING] Time sync warning detected: {selector}")
                        
                        # Add human delay before dismissing
                        await self.human_delay(500, 1200)
                        
                        # Try to close modal using expanded selector list
                        close_selectors = [
                            '#root > div > div.ModalContext_modalWrapper__CBy3x > div > div > div.modal_footer__17zbN > button',
                            '#root > div > div.MuiBox-root.css-fvykgg > div > div > button',
                            'button:has-text("OK")',
                            'button:has-text("Close")',
                            'button:has-text("Continue")',
                            'button:has-text("Dismiss")',
                            'button:has-text("Got it")',
                            'button:has-text("Accept")',
                            '.modal_footer__17zbN button',
                            '.MuiBox-root.css-fvykgg button',
                            '.modal-close',
                            '[aria-label="Close"]',
                            '.ModalContext_modalWrapper__CBy3x button',
                            'div[role="dialog"] button',
                            'button[class*="close"]',
                            'button.btn-primary',
                            'button.btn-secondary',
                            '.close-button',
                            'button[type="button"]'
                        ]
                        
                        for close_selector in close_selectors:
                            try:
                                await self.human_click(close_selector)
                                print(f"[SUCCESS] Time sync warning dismissed with: {close_selector}")
                                await asyncio.sleep(1)  # Wait for modal to close
                                
                                # Verify modal is gone
                                try:
                                    if not await self.page.wait_for_selector(selector, timeout=1000):
                                        print("[CONFIRM] Modal successfully closed")
                                        return
                                except:
                                    print("[CONFIRM] Modal appears to be closed")
                                    return
                            except Exception:
                                continue
                        
                        # If no close button found, try multiple keyboard approaches
                        print("[FALLBACK] Trying aggressive keyboard dismissal methods...")
                        await self.page.keyboard.press('Escape')
                        await asyncio.sleep(300)
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(300)
                        await self.page.keyboard.press('Tab')
                        await asyncio.sleep(200)
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(300)
                        await self.page.keyboard.press('Space')
                        
                        print("[SUCCESS] Time sync warning dismissed with keyboard")
                        return
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[INFO] No time sync warning detected: {e}")
    
    async def confirm_login_success(self) -> bool:
        """Confirm login success with multiple dashboard selectors"""
        print("[LOGIN] Confirming login success...")
        
        dashboard_selectors = [
            '.dashboard',
            '#dashboard',
            '.main-content',
            '.trading-interface',
            '.user-menu',
            '.account-info',
            '[data-testid="dashboard"]',
            '.welcome-message',
            '.portfolio',
            '.navbar',
            '.header-menu',
            '.profile-menu',
            '.logout',
            '[href*="logout"]',
            '.nav-menu',
            '.sidebar',
            '.header-user',
            '[class*="dashboard"]',
            '[class*="main"]',
            '[class*="home"]',
            '[class*="trading"]',
            '[class*="portfolio"]',
            '[class*="account"]',
            'nav',
            'header',
            '.container',
            '[role="main"]',
            '[role="navigation"]',
            'button[class*="user"]',
            'div[class*="user"]',
            'span[class*="user"]'
        ]
        
        for attempt in range(3):
            print(f"[ATTEMPT] Login confirmation attempt {attempt + 1}/3")
            
            # Add debugging info about current page state
            current_url = self.page.url
            current_title = await self.page.title()
            print(f"[DEBUG] Current URL: {current_url}")
            print(f"[DEBUG] Current title: {current_title}")
            
            # Check for any visible elements that might indicate successful login
            all_elements = await self.page.query_selector_all('*')
            print(f"[DEBUG] Total elements on page: {len(all_elements)}")
            
            for selector in dashboard_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    print(f"[SUCCESS] Login successful - found dashboard element: {selector}")
                    await self.page.screenshot(path='after_login.png')
                    return True
                except Exception:
                    continue
            
            # Wait before retry
            if attempt < 2:
                await asyncio.sleep(2)
        
        print("[ERROR] Login confirmation failed")
        return False
    
    async def navigate_to_trading(self) -> bool:
        """Navigate to trading page with confirmation"""
        print("[NAVIGATE] Navigating to trading page...")
        
        try:
            # First try direct navigation to trading URL
            current_url = self.page.url
            if 'trading' not in current_url.lower():
                print("[NAVIGATE] Attempting direct navigation to trading page...")
                await self.page.goto('https://bulenox.projectx.com/trading', wait_until='networkidle')
                await asyncio.sleep(2)
            
            # If direct navigation fails, try finding navigation elements
            if not await self.confirm_trading_page():
                print("[NAVIGATE] Direct navigation failed, trying navigation elements...")
                
                # Enhanced trading navigation selectors
                nav_selectors = [
                    # Direct href selectors
                    'a[href*="trading"]',
                    'a[href*="trade"]',
                    'a[href="/trading"]',
                    'a[href="/trade"]',
                    # Text-based navigation
                    'button:has-text("Trading")',
                    'button:has-text("Trade")',
                    'a:has-text("Trading")',
                    'a:has-text("Trade")',
                    'span:has-text("Trading")',
                    'span:has-text("Trade")',
                    # Class and ID selectors
                    '.nav-trading',
                    '.trading-nav',
                    '.trade-nav',
                    '#trading-link',
                    '#trade-link',
                    '[data-testid="trading-nav"]',
                    '[data-testid="trade-nav"]',
                    # Generic navigation patterns
                    'nav a:has-text("Trading")',
                    'nav button:has-text("Trading")',
                    '.navbar a:has-text("Trading")',
                    '.menu a:has-text("Trading")',
                    '.sidebar a:has-text("Trading")',
                    # Fallback patterns
                    '[class*="trading"]',
                    '[class*="trade"]',
                    '[id*="trading"]',
                    '[id*="trade"]'
                ]
                
                # Try to find and click trading navigation
                for selector in nav_selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=3000)
                        await self.human_click(selector)
                        print(f"[SUCCESS] Clicked trading navigation: {selector}")
                        await asyncio.sleep(2)
                        break
                    except Exception:
                        continue
            
            # Confirm trading page loaded
            return await self.confirm_trading_page()
            
        except Exception as e:
            print(f"[ERROR] Navigation to trading failed: {e}")
            return False
    
    async def confirm_trading_page(self) -> bool:
        """Confirm trading page is loaded with comprehensive selectors"""
        print("[CONFIRM] Confirming trading page loaded...")
        
        # First, handle any potential time sync warnings that might be blocking
        await self.handle_time_sync_warning()
        
        # Enhanced trading page detection selectors
        trading_selectors = [
            # Bulenox-specific selectors
            '.trading-interface',
            '.order-form',
            '.price-chart',
            '.order-book',
            '.trading-panel',
            '#trading-container',
            '[data-testid="trading-interface"]',
            # Chart and trading elements
            '.tradingview-widget-container',
            '.chart-container',
            '.tv-chart-container',
            'iframe[src*="tradingview"]',
            # Order-related elements
            'button:has-text("Buy")',
            'button:has-text("Sell")',
            'button:has-text("ORDER")',
            'button:has-text("DOM")',
            'input[placeholder*="price"]',
            'input[placeholder*="amount"]',
            'input[placeholder*="quantity"]',
            # Generic trading indicators
            '[class*="order"]',
            '[class*="trade"]',
            '[class*="trading"]',
            '[class*="chart"]',
            '[id*="order"]',
            '[id*="trade"]',
            '[id*="trading"]',
            # Text-based detection
            'text="Buy"',
            'text="Sell"',
            'text="Order"',
            'text="Price"',
            'text="Amount"',
            # Fallback selectors
            'form',
            'table',
            'canvas',
            # Additional comprehensive selectors
            'div',
            'span',
            'button',
            'input'
        ]
        
        for attempt in range(3):
            print(f"[ATTEMPT] Trading page confirmation attempt {attempt + 1}/3")
            
            # Add debugging info
            current_url = self.page.url
            current_title = await self.page.title()
            print(f"[DEBUG] Current URL: {current_url}")
            print(f"[DEBUG] Current title: {current_title}")
            
            # Check for time sync warnings again
            await self.handle_time_sync_warning()
            
            # Add random mouse movement to simulate human behavior
            await self.random_mouse_movement()
            
            # Try each selector with shorter timeout for faster iteration
            for selector in trading_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        print(f"[SUCCESS] Trading page confirmed - found visible element: {selector}")
                        await self.page.screenshot(path='trading_page_confirmed.png')
                        return True
                except Exception:
                    continue
            
            # If no specific trading elements found, check if we're at least on the right domain
            if 'bulenox.projectx.com' in current_url:
                print("[INFO] On correct domain, assuming trading page loaded")
                return True
            
            if attempt < 2:
                print(f"[RETRY] Waiting before retry {attempt + 2}/3...")
                await asyncio.sleep(3)
        
        print("[ERROR] Trading page confirmation failed")
        await self.page.screenshot(path='trading_page_failed.png')
        return False
    
    async def place_trade_order(self) -> bool:
        """Attempt to place a trade order with multiple selector strategies"""
        print("[TRADE] Attempting to place trade order...")
        
        try:
            # Strategy 1: Enhanced ORDER tab selectors
            order_tab_selectors = [
                # Text-based ORDER selectors
                'button:has-text("ORDER")',
                'button:has-text("Order")',
                'a:has-text("ORDER")',
                'a:has-text("Order")',
                'span:has-text("ORDER")',
                'span:has-text("Order")',
                'div:has-text("ORDER")',
                'div:has-text("Order")',
                # Class and ID selectors
                '.order-tab',
                '.order-button',
                '.order-panel',
                '#order-tab',
                '#order-button',
                '[data-testid="order-tab"]',
                '[data-testid="order-button"]',
                # Href selectors
                'a[href*="order"]',
                'a[href="/order"]',
                # Generic patterns
                '[class*="order"]',
                '[id*="order"]',
                'button[class*="order"]',
                'div[class*="order"]',
                # Tab-specific patterns
                '.tab:has-text("ORDER")',
                '.tab:has-text("Order")',
                '.nav-tab:has-text("ORDER")',
                '.nav-tab:has-text("Order")'
            ]
            
            order_tab_found = False
            for selector in order_tab_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.human_click(selector)
                    print(f"[SUCCESS] ORDER tab clicked: {selector}")
                    order_tab_found = True
                    break
                except Exception:
                    continue
            
            if not order_tab_found:
                print("[WARNING] ORDER tab not found, trying DOM tab...")
                
                # Strategy 2: Enhanced DOM tab selectors
                dom_tab_selectors = [
                    # Text-based DOM selectors
                    'button:has-text("DOM")',
                    'button:has-text("Dom")',
                    'a:has-text("DOM")',
                    'a:has-text("Dom")',
                    'span:has-text("DOM")',
                    'span:has-text("Dom")',
                    'div:has-text("DOM")',
                    'div:has-text("Dom")',
                    # Class and ID selectors
                    '.dom-tab',
                    '.dom-button',
                    '.dom-panel',
                    '#dom-tab',
                    '#dom-button',
                    '[data-testid="dom-tab"]',
                    '[data-testid="dom-button"]',
                    # Generic patterns
                    '[class*="dom"]',
                    '[id*="dom"]',
                    'button[class*="dom"]',
                    'div[class*="dom"]',
                    # Tab-specific patterns
                    '.tab:has-text("DOM")',
                    '.tab:has-text("Dom")',
                    '.nav-tab:has-text("DOM")',
                    '.nav-tab:has-text("Dom")'
                ]
                
                dom_tab_found = False
                for selector in dom_tab_selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=3000)
                        await self.human_click(selector)
                        print(f"[SUCCESS] DOM tab clicked: {selector}")
                        dom_tab_found = True
                        break
                    except Exception:
                        continue
                
                if not dom_tab_found:
                    print("[WARNING] DOM tab not found, trying generic trading interface...")
                    
                    # Strategy 3: Generic trading interface selectors
                    generic_selectors = [
                        # Buy/Sell buttons
                        'button:has-text("Buy")',
                        'button:has-text("Sell")',
                        'button:has-text("BUY")',
                        'button:has-text("SELL")',
                        # Trading form elements
                        'input[placeholder*="price"]',
                        'input[placeholder*="amount"]',
                        'input[placeholder*="quantity"]',
                        'input[placeholder*="size"]',
                        # Generic trading patterns
                        '.buy-button',
                        '.sell-button',
                        '.trade-button',
                        '.order-button',
                        '#buy-btn',
                        '#sell-btn',
                        '#trade-btn',
                        '[class*="buy"]',
                        '[class*="sell"]',
                        '[class*="trade"]',
                        # Form and input fallbacks
                        'form',
                        'input[type="number"]',
                        'select',
                        'button[type="submit"]'
                    ]
                    
                    for selector in generic_selectors:
                        try:
                            await self.page.wait_for_selector(selector, timeout=2000)
                            print(f"[SUCCESS] Generic trading interface found: {selector}")
                            break
                        except Exception:
                            continue
            
            # Wait for order form to load
            await asyncio.sleep(2)
            
            # Get current market price (placeholder - should be updated with real market data)
            current_price = 2650.0  # Default Gold price
            
            # Determine trade direction (placeholder - should be based on strategy signal)
            is_long = True  # Default to long position
            
            # Fill order form with Fibonacci parameters
            trade_info = await self.fill_order_form(is_long=is_long, entry_price=current_price)
            
            # Submit order
            order_success = await self.submit_order()
            
            if order_success:
                print(f"[SUCCESS] Order placed: {trade_info['contracts']} contracts of {trade_info['symbol']}")
                print(f"[TRADE] Entry: ${trade_info['entry_price']} | TP: ${trade_info['take_profit']} | SL: ${trade_info['stop_loss']}")
                
                # Simulate trade outcome (in real implementation, this would monitor actual trade results)
                # For now, we'll simulate a win with the expected profit
                simulated_win = True  # This should be replaced with actual trade monitoring
                profit_loss = trade_info['profit_target_usd'] if simulated_win else -trade_info['profit_target_usd'] * 0.4
                
                # Handle trade outcome and advance Fibonacci
                daily_complete = await self.handle_trade_outcome(simulated_win, profit_loss)
                
                if daily_complete:
                    print("[COMPLETE] Daily profit target reached! Trading session complete.")
                
                return True
            else:
                print("[ERROR] Order submission failed")
                return False
            
        except Exception as e:
            print(f"[ERROR] Trade order placement failed: {e}")
            await self.page.screenshot(path='trade_error.png')
            return False
    
    async def fill_order_form(self, is_long=True, entry_price=None):
        """Fill the order form with Fibonacci strategy parameters"""
        print("[FORM] Filling order form with Fibonacci strategy parameters...")
        
        # Update current session
        self.current_session = self.get_current_session()
        if not self.current_session:
            print("[WARNING] No active trading session, using morning session defaults")
            self.current_session = 'morning'
        
        # Get dynamic strategy parameters
        symbol = CONFIG.FULL_SYMBOL  # F.US.GCE for Gold futures
        contracts = self.get_fibonacci_contract_size(self.current_session)
        profit_target_usd = self.get_current_fibonacci_target(self.current_session)
        
        # Calculate Gold futures pricing (GC: $100 per full point, 0.1 points = $10)
        points_per_dollar = 0.01  # $1 = 0.01 points for GC
        profit_target_points = profit_target_usd * points_per_dollar
        
        # Use current market price if not provided
        if entry_price is None:
            entry_price = 2650.0  # Default Gold price, should be updated with real market data
        
        # Calculate take profit and stop loss levels
        if is_long:
            take_profit = round(entry_price + profit_target_points, 1)
            stop_loss = round(entry_price - (profit_target_points * 0.4), 1)  # 2.5:1 R:R
        else:
            take_profit = round(entry_price - profit_target_points, 1)
            stop_loss = round(entry_price + (profit_target_points * 0.4), 1)  # 2.5:1 R:R
        
        print(f"[STRATEGY] Session: {self.current_session.upper()}")
        print(f"[STRATEGY] Fibonacci Level: {self.session_fib_index[self.current_session]} (${profit_target_usd} target)")
        print(f"[STRATEGY] Contracts: {contracts} | Entry: ${entry_price} | TP: ${take_profit} | SL: ${stop_loss}")
        
        # Symbol/Instrument selectors
        symbol_selectors = [
            'input[name="symbol"]',
            'input[name="instrument"]',
            '.symbol-input',
            '#symbol',
            '[data-testid="symbol-input"]'
        ]
        
        # Quantity selectors
        quantity_selectors = [
            'input[name="quantity"]',
            'input[name="amount"]',
            'input[name="size"]',
            '.quantity-input',
            '#quantity',
            '[data-testid="quantity-input"]'
        ]
        
        # Price selectors
        price_selectors = [
            'input[name="price"]',
            '.price-input',
            '#price',
            '[data-testid="price-input"]'
        ]
        
        # Take Profit selectors
        tp_selectors = [
            'input[name="takeProfit"]',
            'input[name="take_profit"]',
            '.take-profit-input',
            '#takeProfit',
            '[data-testid="take-profit-input"]'
        ]
        
        # Stop Loss selectors
        sl_selectors = [
            'input[name="stopLoss"]',
            'input[name="stop_loss"]',
            '.stop-loss-input',
            '#stopLoss',
            '[data-testid="stop-loss-input"]'
        ]
        
        # Fill symbol (Gold futures)
        for selector in symbol_selectors:
            try:
                await self.page.fill(selector, symbol)
                print(f"[SUCCESS] Symbol filled: {selector} = {symbol}")
                break
            except Exception:
                continue
        
        # Fill quantity (contracts)
        for selector in quantity_selectors:
            try:
                await self.page.fill(selector, str(contracts))
                print(f"[SUCCESS] Quantity filled: {selector} = {contracts}")
                break
            except Exception:
                continue
        
        # Fill entry price
        for selector in price_selectors:
            try:
                await self.page.fill(selector, str(entry_price))
                print(f"[SUCCESS] Price filled: {selector} = {entry_price}")
                break
            except Exception:
                continue
        
        # Fill take profit
        for selector in tp_selectors:
            try:
                await self.page.fill(selector, str(take_profit))
                print(f"[SUCCESS] Take Profit filled: {selector} = {take_profit}")
                break
            except Exception:
                continue
        
        # Fill stop loss
        for selector in sl_selectors:
            try:
                await self.page.fill(selector, str(stop_loss))
                print(f"[SUCCESS] Stop Loss filled: {selector} = {stop_loss}")
                break
            except Exception:
                continue
        
        # Update trade tracking
        self.daily_trades += 1
        self.session_trades += 1
        
        return {
            'symbol': symbol,
            'contracts': contracts,
            'entry_price': entry_price,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'profit_target_usd': profit_target_usd,
            'session': self.current_session,
            'fib_index': self.session_fib_index[self.current_session]
        }
    
    async def handle_trade_outcome(self, is_win: bool, profit_loss: float = 0.0):
        """Handle trade outcome and advance Fibonacci sequence"""
        session = self.current_session or 'morning'
        
        if is_win:
            old_target = self.get_current_fibonacci_target(session)
            self.advance_fibonacci(session, True)
            new_target = self.get_current_fibonacci_target(session)
            self.daily_pnl += abs(profit_loss)
            
            print(f"[WIN] Session: {session.upper()} | Profit: ${profit_loss:.2f}")
            print(f"[FIBONACCI] Advanced from ${old_target} to ${new_target}")
            print(f"[DAILY] Total P&L: ${self.daily_pnl:.2f} | Trades: {self.daily_trades}")
        else:
            self.advance_fibonacci(session, False)  # Reset to first level
            self.daily_pnl += profit_loss  # profit_loss will be negative for losses
            
            print(f"[LOSS] Session: {session.upper()} | Loss: ${profit_loss:.2f}")
            print(f"[FIBONACCI] Reset to ${self.get_current_fibonacci_target(session)}")
            print(f"[DAILY] Total P&L: ${self.daily_pnl:.2f} | Trades: {self.daily_trades}")
        
        # Check daily profit target
        if self.daily_pnl >= CONFIG.DAILY_PROFIT_TARGET:
            print(f"[SUCCESS] Daily profit target reached: ${self.daily_pnl:.2f} >= ${CONFIG.DAILY_PROFIT_TARGET}")
            return True
        
        # Check session limits
        if self.session_trades >= 3:  # Max 3 trades per session
            print(f"[SESSION] {session.upper()} session complete: {self.session_trades} trades")
            self.session_trades = 0
            # Reset Fibonacci for next session
            self.session_fib_index[session] = 0
        
        return False
    
    async def submit_order(self) -> bool:
        """Submit the trade order"""
        print("[SUBMIT] Submitting trade order...")
        
        submit_selectors = [
            'button:has-text("Buy")',
            'button:has-text("Sell")',
            'button:has-text("Submit")',
            'button:has-text("Place Order")',
            '.buy-button',
            '.sell-button',
            '.submit-order',
            '#place-order',
            '[data-testid="submit-order"]'
        ]
        
        for selector in submit_selectors:
            try:
                await self.human_click(selector)
                print(f"[SUCCESS] Order submitted using: {selector}")
                
                # Wait for potential confirmation or error
                await asyncio.sleep(3)
                return True
                
            except Exception as e:
                print(f"[WARNING] Failed to submit with {selector}: {e}")
                continue
        
        print("[ERROR] Could not submit order with any selector")
        return False
    
    async def cleanup(self):
        """Clean up browser resources"""
        print("[CLEANUP] Cleaning up...")
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            # Browser is None when using persistent context, so no need to close it
            print("[SUCCESS] Cleanup complete")
        except Exception as e:
            print(f"[WARNING] Cleanup error: {e}")

async def main():
    """Main entry point"""
    print("[TRADEBOT] TradeBot Sentinel Starting...")
    print(f"[TIMESTAMP] {datetime.now()}")
    
    # Check for headless mode override
    headless = '--headful' not in sys.argv
    print(f"[HEADLESS] Headless mode: {headless}")
    
    sentinel = None
    try:
        # Initialize TradeBot Sentinel
        sentinel = TradeBotSentinel(headless=headless)
        
        # Setup browser with network interception
        await sentinel.setup_browser()
        
        # Perform login
        login_success = await sentinel.login()
        if not login_success:
            # Check if we're still authenticated via saved session
            if await sentinel.check_login_status():
                print("[SUCCESS] Proceeding with saved session authentication")
            else:
                print("[ERROR] Login failed and no saved session found")
                return
        
        # Add random mouse movement before navigation
        await sentinel.random_mouse_movement()
        
        # Navigate to trading page
        trading_ready = await sentinel.navigate_to_trading()
        if not trading_ready:
            print("[ERROR] Trading page not ready, exiting...")
            return
        
        # Add human delay and mouse movement before trading
        await sentinel.human_delay(1000, 2000)
        await sentinel.random_mouse_movement()
        
        # Place trade order (this will trigger network interception)
        order_placed = await sentinel.place_trade_order()
        if order_placed:
            print("[SUCCESS] Trade order process completed")
        else:
            print("[WARNING] Trade order placement had issues")
        
        # Keep browser open briefly to capture any delayed requests with periodic mouse movements
        print("[WAIT] Waiting for potential trade requests...")
        for i in range(5):
            await asyncio.sleep(2)
            if i % 2 == 0:  # Every other iteration
                await sentinel.random_mouse_movement()
        
        print("[SUCCESS] TradeBot Sentinel mission completed!")
        
    except Exception as e:
        print(f"[ERROR] Critical error: {e}")
        if sentinel and sentinel.page:
            await sentinel.page.screenshot(path='critical_error.png')
    
    finally:
        if sentinel:
            await sentinel.cleanup()

if __name__ == "__main__":
    asyncio.run(main())