#!/usr/bin/env python3
"""
TradeBot Sentinel Advanced+Pro - Bulenox ProjectX Trading Platform Automation
Pro-level automation with bulletproof trade detection, auto-execution, and historical logging.
"""

import asyncio
import os
import json
import subprocess
import sys
import csv
import argparse
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradebot_sentinel_advanced.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradeBotSentinelAdvanced:
    """TradeBot Sentinel Advanced - Pro-level automation for Bulenox ProjectX trading platform"""
    
    def __init__(self, headless=True, monitor_mode=False, simulation_mode=False):
        self.headless = headless
        self.monitor_mode = monitor_mode
        self.simulation_mode = simulation_mode
        self.browser = None
        self.context = None
        self.page = None
        self.trade_requests = []
        
        # Create directory structure
        self.setup_directories()
        
        # Load configuration from environment
        self.load_config()
        
        # Initialize monitoring stats
        self.daily_trade_count = 0
        self.last_detected_trade = None
        self.execution_status = "Ready"
        
    def setup_directories(self):
        """Create required directory structure"""
        self.screenshots_dir = Path('screenshots')
        self.logs_dir = Path('logs')
        self.curls_dir = self.logs_dir / 'curls'
        self.json_dir = self.logs_dir / 'json'
        
        # Create all directories
        for directory in [self.screenshots_dir, self.logs_dir, self.curls_dir, self.json_dir]:
            directory.mkdir(exist_ok=True)
            
        logger.info("Directory structure created successfully")
    
    def load_config(self):
        """Load configuration from environment variables"""
        # Core credentials
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("BULENOX_USERNAME and BULENOX_PASSWORD environment variables must be set")
        
        # Advanced features configuration
        self.auto_execute = os.getenv('AUTO_EXECUTE', 'False').lower() == 'true'
        self.simulation = os.getenv('SIMULATION', 'False').lower() == 'true' or self.simulation_mode
        
        # Notification settings
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Retry settings
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '2000'))
        
        logger.info(f"Configuration loaded - Auto Execute: {self.auto_execute}, Simulation: {self.simulation}")
    
    async def waitForSelectorWithRetries(self, page: Page, selectors: List[str], retries: int = 3, delay: int = 2000) -> Optional[object]:
        """Advanced selector waiting with multiple fallbacks and retries"""
        for attempt in range(retries):
            for selector in selectors:
                try:
                    logger.info(f"Attempt {attempt + 1}/{retries}: Waiting for selector: {selector}")
                    element = await page.wait_for_selector(selector, timeout=delay)
                    if element:
                        logger.info(f"Element found with selector: {selector}")
                        return element
                except Exception as e:
                    logger.warning(f"Selector {selector} failed: {e}")
                    continue
            
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay/1000} seconds... (attempt {attempt + 1}/{retries})")
                await asyncio.sleep(delay / 1000)
        
        logger.error(f"Failed to find element after {retries} attempts with selectors: {selectors}")
        return None
    
    async def setup_browser(self):
        """Initialize browser with advanced network interception"""
        logger.info("Setting up browser with Pro-level network interception...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await self.context.new_page()
        
        # Setup Pro-level network interception
        await self.setup_network_interception()
        
        logger.info("Browser setup completed successfully")
    
    async def setup_network_interception(self):
        """Setup bulletproof network request interception"""
        logger.info("Setting up bulletproof trade detection...")
        
        async def handle_request(request):
            if request.method == 'POST':
                logger.info(f"POST request intercepted: {request.url}")
                
                try:
                    post_data = request.post_data
                    headers = await request.all_headers()
                    
                    # Pro-level dual-criteria matching
                    if self.is_trade_request_pro(request.url, post_data, headers):
                        logger.info("🎯 TRADE EXECUTION REQUEST DETECTED! (Pro-Level Detection)")
                        await self.handle_trade_detection(request)
                        
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
        
        self.page.on('request', handle_request)
    
    def is_trade_request_pro(self, url: str, post_data: str, headers: Dict) -> bool:
        """Pro-level trade detection with dual-criteria matching"""
        # URL pattern matching
        trade_url_patterns = ['/trade', '/orders', '/execute', '/api/trade', '/trading', '/order']
        url_lower = url.lower()
        url_match = any(pattern in url_lower for pattern in trade_url_patterns)
        
        # JSON keyword matching
        json_keywords = ['symbol', 'price', 'order', 'amount', 'quantity', 'side', 'buy', 'sell', 'market', 'limit']
        json_match = False
        
        if post_data:
            try:
                # Try to parse as JSON
                json_data = json.loads(post_data)
                json_str = json.dumps(json_data).lower()
                json_match = any(keyword in json_str for keyword in json_keywords)
            except json.JSONDecodeError:
                # Fallback to string matching
                data_lower = post_data.lower()
                json_match = any(keyword in data_lower for keyword in json_keywords)
        
        # Pro-level detection: URL OR JSON criteria
        is_trade = url_match or json_match
        
        if is_trade:
            logger.info(f"✅ Trade detected - URL Match: {url_match}, JSON Match: {json_match}")
        
        return is_trade
    
    async def handle_trade_detection(self, request):
        """Handle detected trade with Pro-level logging and execution"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        try:
            # Save to timestamped files
            curl_command = await self.convert_to_curl(request)
            json_data = await self.extract_json_data(request)
            
            # Save cURL to timestamped file
            curl_file = self.curls_dir / f"{timestamp}.sh"
            with open(curl_file, 'w', encoding='utf-8') as f:
                f.write(curl_command)
            
            # Save JSON to timestamped file
            json_file = self.json_dir / f"{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'url': request.url,
                    'method': request.method,
                    'headers': await request.all_headers(),
                    'post_data': request.post_data,
                    'parsed_data': json_data
                }, f, indent=2)
            
            # Always overwrite latest trade files
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write(curl_command)
            
            # Convert to Python requests
            await self.convert_curl_to_python()
            
            # Update monitoring stats
            self.last_detected_trade = {
                'timestamp': timestamp,
                'url': request.url,
                'data': json_data
            }
            self.daily_trade_count += 1
            
            # Log to historical CSV
            await self.log_trade_to_csv(timestamp, json_data)
            
            # Log detailed detection
            await self.log_trade_detection(timestamp, request, json_data)
            
            # Auto-execution if enabled
            if self.auto_execute and not self.simulation:
                await self.execute_trade(timestamp)
            
            # Send notifications
            await self.send_notifications(timestamp, json_data)
            
            logger.info(f"✅ Trade detection completed - Files saved with timestamp: {timestamp}")
            
        except Exception as e:
            logger.error(f"Error handling trade detection: {e}")
    
    async def extract_json_data(self, request) -> Dict:
        """Extract and parse JSON data from request"""
        try:
            post_data = request.post_data
            if post_data:
                return json.loads(post_data)
        except json.JSONDecodeError:
            pass
        
        return {'raw_data': request.post_data or 'No data'}
    
    async def convert_to_curl(self, request) -> str:
        """Convert Playwright request to cURL command"""
        curl_parts = ['curl']
        
        # Add method
        curl_parts.append(f"-X {request.method}")
        
        # Add headers
        headers = await request.all_headers()
        for name, value in headers.items():
            # Escape single quotes in header values
            escaped_value = value.replace("'", "'\"'\"'")
            curl_parts.append(f"-H '{name}: {escaped_value}'")
        
        # Add URL
        curl_parts.append(f"'{request.url}'")
        
        # Add POST data if present
        post_data = request.post_data
        if post_data:
            # Escape single quotes in data
            data_str = post_data.replace("'", "'\"'\"'")
            curl_parts.append(f"-d '{data_str}'")
        
        return ' \\ '.join(curl_parts)
    
    async def convert_curl_to_python(self):
        """Convert cURL command to Python requests code using curlconverter"""
        try:
            # Check if curlconverter is installed
            result = subprocess.run(['curlconverter', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("curlconverter not found. Installing...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'curlconverter'])
            
            # Convert cURL to Python
            with open('trade.sh', 'r', encoding='utf-8') as f:
                curl_command = f.read()
            
            result = subprocess.run(['curlconverter', '--language', 'python'], 
                                  input=curl_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                with open('trade_request_full.py', 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                logger.info("✅ Python requests code saved to trade_request_full.py")
            else:
                logger.error(f"Error converting cURL to Python: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error in cURL to Python conversion: {e}")
    
    async def log_trade_to_csv(self, timestamp: str, json_data: Dict):
        """Log trade to historical CSV file"""
        csv_file = self.logs_dir / 'trade_log.csv'
        
        # Extract trade details
        symbol = json_data.get('symbol', 'UNKNOWN')
        side = json_data.get('side', json_data.get('type', 'UNKNOWN'))
        qty = json_data.get('quantity', json_data.get('amount', json_data.get('qty', 'UNKNOWN')))
        price = json_data.get('price', 'UNKNOWN')
        status = 'DETECTED'
        
        # Create CSV if it doesn't exist
        if not csv_file.exists():
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'symbol', 'side', 'qty', 'price', 'status'])
        
        # Append trade data
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, symbol, side, qty, price, status])
        
        logger.info(f"✅ Trade logged to CSV: {symbol} {side} {qty} @ {price}")
    
    async def log_trade_detection(self, timestamp: str, request, json_data: Dict):
        """Log detailed trade detection information"""
        log_file = self.logs_dir / 'trade_detections.log'
        
        log_entry = {
            'timestamp': timestamp,
            'url': request.url,
            'method': request.method,
            'headers': await request.all_headers(),
            'post_data': request.post_data,
            'parsed_data': json_data,
            'auto_execute': self.auto_execute,
            'simulation': self.simulation
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"TRADE DETECTION - {timestamp}\n")
            f.write(f"{'='*80}\n")
            f.write(json.dumps(log_entry, indent=2))
            f.write(f"\n{'='*80}\n")
        
        logger.info(f"✅ Detailed trade detection logged")
    
    async def execute_trade(self, timestamp: str):
        """Execute trade automatically if AUTO_EXECUTE is enabled"""
        if self.simulation:
            logger.info("🔄 SIMULATION MODE: Skipping actual trade execution")
            self.execution_status = f"SIMULATED - {timestamp}"
            return
        
        logger.info("🚀 AUTO-EXECUTION: Executing trade...")
        self.execution_status = "EXECUTING"
        
        try:
            # Execute the trade.sh script
            result = subprocess.run(['bash', 'trade.sh'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ Trade executed successfully!")
                self.execution_status = f"SUCCESS - {timestamp}"
                
                # Wait for trade confirmation in dashboard
                await self.wait_for_trade_confirmation()
                
            else:
                logger.error(f"❌ Trade execution failed: {result.stderr}")
                self.execution_status = f"FAILED - {timestamp}"
            
            # Update CSV with execution status
            await self.update_trade_status_in_csv(timestamp, self.execution_status)
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Trade execution timed out")
            self.execution_status = f"TIMEOUT - {timestamp}"
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            self.execution_status = f"ERROR - {timestamp}"
    
    async def wait_for_trade_confirmation(self):
        """Wait for trade confirmation in dashboard with retries"""
        confirmation_selectors = [
            '.trade-confirmation',
            '.order-filled',
            '.execution-success',
            'div:has-text("Order Filled")',
            'div:has-text("Trade Executed")',
            '.success-message'
        ]
        
        for attempt in range(5):
            try:
                logger.info(f"Waiting for trade confirmation (attempt {attempt + 1}/5)...")
                element = await self.waitForSelectorWithRetries(
                    self.page, confirmation_selectors, retries=1, delay=2000
                )
                
                if element:
                    logger.info("✅ Trade confirmation received!")
                    await self.take_screenshot('trade_confirmed')
                    return True
                    
            except Exception as e:
                logger.warning(f"Trade confirmation attempt {attempt + 1} failed: {e}")
            
            await asyncio.sleep(2)
        
        logger.warning("⚠️ Trade confirmation not received within timeout")
        return False
    
    async def update_trade_status_in_csv(self, timestamp: str, status: str):
        """Update trade status in CSV file"""
        csv_file = self.logs_dir / 'trade_log.csv'
        
        if not csv_file.exists():
            return
        
        # Read existing data
        rows = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Update matching timestamp
        for i, row in enumerate(rows):
            if len(row) > 0 and row[0] == timestamp:
                if len(row) >= 6:
                    row[5] = status  # Update status column
                break
        
        # Write back to file
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        logger.info(f"✅ Trade status updated in CSV: {status}")
    
    async def send_notifications(self, timestamp: str, json_data: Dict):
        """Send Telegram/Email notifications if configured"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        try:
            symbol = json_data.get('symbol', 'UNKNOWN')
            side = json_data.get('side', json_data.get('type', 'UNKNOWN'))
            qty = json_data.get('quantity', json_data.get('amount', 'UNKNOWN'))
            price = json_data.get('price', 'UNKNOWN')
            
            message = f"🤖 TradeBot Sentinel Alert\n\n"
            message += f"📊 Trade Detected: {symbol}\n"
            message += f"📈 Side: {side}\n"
            message += f"💰 Quantity: {qty}\n"
            message += f"💵 Price: {price}\n"
            message += f"⏰ Time: {timestamp}\n"
            message += f"🔄 Auto Execute: {self.auto_execute}\n"
            message += f"🎮 Simulation: {self.simulation}"
            
            # Send Telegram notification
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Telegram notification sent successfully")
            else:
                logger.error(f"❌ Telegram notification failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    async def take_screenshot(self, filename: str):
        """Take screenshot for debugging"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = self.screenshots_dir / f"{filename}_{timestamp}.png"
            await self.page.screenshot(path=str(screenshot_path))
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    async def login(self):
        """Secure login to Bulenox ProjectX platform with advanced selectors"""
        logger.info("🔐 Starting secure login process...")
        
        try:
            # Navigate to login page
            await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
            await self.take_screenshot('login_page')
            
            # Handle potential Time Sync Warning modal
            time_sync_selectors = [
                '[data-testid="time-sync-warning"]',
                '.time-sync-modal',
                '.modal-time-sync',
                'div:has-text("Time Sync Warning")',
                'button:has-text("Continue")',
                'button:has-text("OK")',
                '.modal-close'
            ]
            
            time_sync_element = await self.waitForSelectorWithRetries(
                self.page, time_sync_selectors, retries=1, delay=3000
            )
            
            if time_sync_element:
                logger.info("⚠️ Time Sync Warning detected, handling...")
                await time_sync_element.click()
                await asyncio.sleep(2)
            
            # Advanced login form selectors with comprehensive fallbacks
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="user" i]',
                '#username',
                '#email',
                '#user',
                '.username-input',
                '.email-input'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="password" i]',
                '#password',
                '.password-input'
            ]
            
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                'input[type="submit"]',
                '.login-button',
                '.signin-button',
                '#login-button',
                '#signin-button'
            ]
            
            # Fill username with advanced retry logic
            username_field = await self.waitForSelectorWithRetries(
                self.page, username_selectors, retries=self.max_retries, delay=self.retry_delay
            )
            if not username_field:
                raise Exception("Username field not found")
            
            await username_field.fill(self.username)
            logger.info("✅ Username filled successfully")
            
            # Fill password with advanced retry logic
            password_field = await self.waitForSelectorWithRetries(
                self.page, password_selectors, retries=self.max_retries, delay=self.retry_delay
            )
            if not password_field:
                raise Exception("Password field not found")
            
            await password_field.fill(self.password)
            logger.info("✅ Password filled successfully")
            
            await self.take_screenshot('before_login')
            
            # Click login button with advanced retry logic
            login_button = await self.waitForSelectorWithRetries(
                self.page, login_button_selectors, retries=self.max_retries, delay=self.retry_delay
            )
            if not login_button:
                raise Exception("Login button not found")
            
            await login_button.click()
            logger.info("✅ Login button clicked")
            
            # Wait for login success with comprehensive dashboard selectors
            dashboard_selectors = [
                '[data-testid="dashboard"]',
                '.dashboard',
                '.main-dashboard',
                '.dashboard-container',
                'div:has-text("Dashboard")',
                'div:has-text("Welcome")',
                '.user-menu',
                '.trading-interface',
                '.account-info',
                '.balance-info',
                '.portfolio'
            ]
            
            dashboard_element = await self.waitForSelectorWithRetries(
                self.page, dashboard_selectors, retries=5, delay=5000
            )
            
            if not dashboard_element:
                raise Exception("Login failed - Dashboard not found")
            
            await self.take_screenshot('after_login')
            logger.info("✅ Login successful!")
            
        except Exception as e:
            await self.take_screenshot('login_failure')
            logger.error(f"❌ Login failed: {e}")
            raise
    
    async def navigate_to_trading(self):
        """Navigate to trading page with advanced selectors"""
        logger.info("📈 Navigating to trading interface...")
        
        try:
            # Advanced trading page selectors
            trading_nav_selectors = [
                'a[href*="trading"]',
                'a[href*="trade"]',
                'a:has-text("Trading")',
                'a:has-text("Trade")',
                'a:has-text("Markets")',
                '.nav-trading',
                '.trading-nav',
                '#trading-link',
                '#trade-link',
                'button:has-text("Trading")',
                'button:has-text("Trade")'
            ]
            
            # Try to find and click trading navigation
            trading_nav = await self.waitForSelectorWithRetries(
                self.page, trading_nav_selectors, retries=2, delay=3000
            )
            
            if trading_nav:
                await trading_nav.click()
                logger.info("✅ Trading navigation clicked")
                await asyncio.sleep(2)
            else:
                logger.info("ℹ️ Trading navigation not found, assuming already on trading page")
            
            # Confirm trading interface is ready with comprehensive selectors
            trading_interface_selectors = [
                '.trading-interface',
                '.trade-interface',
                '.order-form',
                '.trading-form',
                '.trade-panel',
                '.trading-panel',
                '.order-panel',
                'div:has-text("Order")',
                'div:has-text("Trade")',
                'button:has-text("Buy")',
                'button:has-text("Sell")',
                '.buy-button',
                '.sell-button',
                '.order-book',
                '.price-chart'
            ]
            
            trading_interface = await self.waitForSelectorWithRetries(
                self.page, trading_interface_selectors, retries=5, delay=5000
            )
            
            if not trading_interface:
                raise Exception("Trading interface not found")
            
            await self.take_screenshot('trading_interface')
            logger.info("✅ Trading interface ready!")
            
        except Exception as e:
            await self.take_screenshot('trading_navigation_failure')
            logger.error(f"❌ Failed to navigate to trading interface: {e}")
            raise
    
    async def place_trade_order(self):
        """Attempt to place a trade order with comprehensive selector fallbacks"""
        logger.info("📊 Attempting to place trade order...")
        
        try:
            # Advanced order tab selectors
            order_tab_selectors = [
                'button:has-text("ORDER")',
                'tab:has-text("ORDER")',
                'a:has-text("ORDER")',
                '.order-tab',
                '#order-tab',
                'a[href*="order"]',
                'button[data-tab="order"]'
            ]
            
            # Try ORDER tab first
            order_tab = await self.waitForSelectorWithRetries(
                self.page, order_tab_selectors, retries=2, delay=3000
            )
            
            if order_tab:
                await order_tab.click()
                logger.info("✅ ORDER tab clicked successfully")
                await asyncio.sleep(1)
            else:
                logger.info("ℹ️ ORDER tab not found, trying DOM tab...")
                
                # DOM tab selectors (fallback)
                dom_tab_selectors = [
                    'button:has-text("DOM")',
                    'tab:has-text("DOM")',
                    'a:has-text("DOM")',
                    '.dom-tab',
                    '#dom-tab',
                    'button[data-tab="dom"]'
                ]
                
                dom_tab = await self.waitForSelectorWithRetries(
                    self.page, dom_tab_selectors, retries=2, delay=3000
                )
                
                if dom_tab:
                    await dom_tab.click()
                    logger.info("✅ DOM tab clicked successfully")
                    await asyncio.sleep(1)
                else:
                    logger.info("ℹ️ DOM tab not found, using generic selectors...")
            
            # Comprehensive buy/sell button selectors
            buy_button_selectors = [
                'button:has-text("Buy")',
                'button:has-text("BUY")',
                'button:has-text("Long")',
                '.buy-button',
                '.long-button',
                '#buy-button',
                '#long-button',
                'input[value="Buy"]',
                'button[data-side="buy"]',
                'button[data-action="buy"]'
            ]
            
            sell_button_selectors = [
                'button:has-text("Sell")',
                'button:has-text("SELL")',
                'button:has-text("Short")',
                '.sell-button',
                '.short-button',
                '#sell-button',
                '#short-button',
                'input[value="Sell"]',
                'button[data-side="sell"]',
                'button[data-action="sell"]'
            ]
            
            # Try to find and click buy button first
            buy_button = await self.waitForSelectorWithRetries(
                self.page, buy_button_selectors, retries=2, delay=3000
            )
            
            if buy_button:
                await buy_button.click()
                logger.info("✅ Buy button clicked - trade order initiated!")
                await self.take_screenshot('buy_order_placed')
            else:
                # Try sell button as fallback
                sell_button = await self.waitForSelectorWithRetries(
                    self.page, sell_button_selectors, retries=2, delay=3000
                )
                
                if sell_button:
                    await sell_button.click()
                    logger.info("✅ Sell button clicked - trade order initiated!")
                    await self.take_screenshot('sell_order_placed')
                else:
                    logger.warning("⚠️ No buy/sell buttons found, trade order may not have been placed")
            
            # Wait for network requests to be captured
            await asyncio.sleep(5)
            
        except Exception as e:
            await self.take_screenshot('trade_order_failure')
            logger.error(f"❌ Failed to place trade order: {e}")
            raise
    
    async def run_simulation_mode(self):
        """Run in simulation mode - replay trades from logs"""
        logger.info("🎮 Running in SIMULATION MODE...")
        
        json_files = list(self.json_dir.glob('*.json'))
        if not json_files:
            logger.warning("No historical trade files found for simulation")
            return
        
        logger.info(f"Found {len(json_files)} historical trades to simulate")
        
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    trade_data = json.load(f)
                
                logger.info(f"🔄 Simulating trade from {json_file.name}")
                
                # Simulate trade execution
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                await self.log_trade_to_csv(timestamp, trade_data.get('parsed_data', {}))
                
                # Update status as simulated
                await self.update_trade_status_in_csv(timestamp, 'SIMULATED')
                
                await asyncio.sleep(1)  # Simulate processing time
                
            except Exception as e:
                logger.error(f"Error simulating trade from {json_file}: {e}")
        
        logger.info("✅ Simulation mode completed")
    
    async def run_monitor_mode(self):
        """Run in monitor mode - show real-time dashboard"""
        logger.info("📊 Running in MONITOR MODE...")
        
        while True:
            try:
                # Clear screen (works on most terminals)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("\n" + "="*60)
                print("🤖 TRADEBOT SENTINEL ADVANCED - MONITOR DASHBOARD")
                print("="*60)
                print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"📊 Daily Trade Count: {self.daily_trade_count}")
                print(f"⚡ Execution Status: {self.execution_status}")
                print(f"🔄 Auto Execute: {'✅ ON' if self.auto_execute else '❌ OFF'}")
                print(f"🎮 Simulation: {'✅ ON' if self.simulation else '❌ OFF'}")
                
                if self.last_detected_trade:
                    print("\n📈 LAST DETECTED TRADE:")
                    print(f"   ⏰ Time: {self.last_detected_trade['timestamp']}")
                    print(f"   🌐 URL: {self.last_detected_trade['url']}")
                    print(f"   📊 Data: {json.dumps(self.last_detected_trade['data'], indent=6)}")
                else:
                    print("\n📈 LAST DETECTED TRADE: None")
                
                print("\n" + "="*60)
                print("Press Ctrl+C to exit monitor mode")
                print("="*60)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                logger.info("\n👋 Monitor mode stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitor mode: {e}")
                await asyncio.sleep(5)
    
    async def run_automation(self):
        """Main automation workflow with advanced features"""
        logger.info("🚀 Starting TradeBot Sentinel Advanced automation...")
        
        try:
            if self.simulation_mode:
                await self.run_simulation_mode()
                return
            
            if self.monitor_mode:
                await self.run_monitor_mode()
                return
            
            # Standard automation workflow
            await self.setup_browser()
            await self.login()
            await self.navigate_to_trading()
            await self.place_trade_order()
            
            logger.info("✅ Automation completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
            await self.take_screenshot('critical_error')
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        logger.info("🧹 Cleaning up browser resources...")
        
        try:
            if self.browser:
                await self.browser.close()
                logger.info("✅ Browser closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point with CLI argument support"""
    parser = argparse.ArgumentParser(description='TradeBot Sentinel Advanced - Pro-level trading automation')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--visible', action='store_true', help='Run with visible browser (opposite of headless)')
    parser.add_argument('--monitor', action='store_true', help='Run in monitor mode')
    parser.add_argument('--simulation', action='store_true', help='Run in simulation mode')
    
    args = parser.parse_args()
    
    # Load environment variables from .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Determine headless mode
    headless = args.headless and not args.visible
    
    # Create and run the automation
    sentinel = TradeBotSentinelAdvanced(
        headless=headless,
        monitor_mode=args.monitor,
        simulation_mode=args.simulation
    )
    
    await sentinel.run_automation()

if __name__ == "__main__":
    asyncio.run(main())