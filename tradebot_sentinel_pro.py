#!/usr/bin/env python3
"""
TradeBot Sentinel Pro - Enhanced Version for Bulenox ProjectX Trading Platform
Upgraded with enhanced POST capture, targeted trade detection, and retry logic
"""

import asyncio
import os
import sys
import json
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright
import logging
from datetime import datetime
import re

# Setup logging without Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradebot_sentinel_pro.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.info("python-dotenv not installed, using system environment variables")

class TradeBotSentinelPro:
    def __init__(self):
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        self.broker_url = os.getenv('BROKER_URL', 'https://bulenox.projectx.com/login')
        self.context = None
        self.page = None
        self.intercepted_requests = []
        self.trade_detection_count = 0
        
        # Create directory structure
        self.setup_directories()
        
        if not self.username or not self.password:
            logger.error("Missing credentials! Please set BULENOX_USERNAME and BULENOX_PASSWORD")
            sys.exit(1)
        
        logger.info(f"Credentials loaded for user: {self.username[:3]}***")
        logger.info(f"Using broker URL: {self.broker_url}")
    
    def setup_directories(self):
        """Create necessary directory structure"""
        directories = [
            Path('logs'),
            Path('logs/curls')
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ensured: {directory}")
    
    async def waitForSelectorWithRetries(self, page, selectors, retries=3, delay=2000):
        """Wait for selector with retry logic
        
        Args:
            page: Playwright page object
            selectors: List of selectors to try or single selector string
            retries: Number of retry attempts (default: 3)
            delay: Delay between retries in milliseconds (default: 2000)
        
        Returns:
            Found selector string or None if all failed
        
        Raises:
            Exception: If no selector found after all retries
        """
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for attempt in range(retries):
            logger.info(f"Selector attempt {attempt + 1}/{retries}")
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        logger.info(f"Found selector: {selector}")
                        return selector
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay}ms...")
                await page.wait_for_timeout(delay)
        
        raise Exception(f"No valid selector found after {retries} attempts from: {selectors}")
    
    async def setup_browser(self):
        """Setup browser with persistent context and network interception"""
        playwright = await async_playwright().start()
        
        # Create unique profile directory
        profile_dir = Path.cwd() / "chrome_profiles" / f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Using Chrome profile: {profile_dir}")
        
        # Launch persistent context
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,  # Visible for debugging
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--start-maximized'
            ]
        )
        
        # Get or create page
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        
        # Setup network interception
        await self.setup_network_interception()
        
        logger.info("Browser setup complete with network interception")
    
    async def setup_network_interception(self):
        """Setup enhanced network request interception"""
        async def handle_request(request):
            # Capture ALL POST requests
            if request.method == 'POST':
                logger.info(f"POST Request intercepted: {request.url}")
                await self.capture_all_post_requests(request)
                
                # Check if this is a trade-specific request
                if self.is_trade_request(request):
                    await self.capture_trade_request(request)
        
        async def handle_response(response):
            # Log responses for POST requests
            if response.request.method == 'POST':
                logger.info(f"POST Response: {response.url} - Status: {response.status}")
        
        self.page.on('request', handle_request)
        self.page.on('response', handle_response)
    
    async def capture_all_post_requests(self, request):
        """Capture all POST requests to timestamped files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Include milliseconds
        filename = f"post_request_{timestamp}.sh"
        filepath = Path('logs/curls') / filename
        
        # Build cURL command
        curl_command = f"curl -X {request.method} '{request.url}'"
        
        # Add headers
        for name, value in request.headers.items():
            curl_command += f" -H '{name}: {value}'"
        
        # Add POST data if available
        post_data = request.post_data
        if post_data:
            curl_command += f" -d '{post_data}'"
        
        # Save to timestamped file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(curl_command)
            logger.info(f"POST request saved to: {filepath}")
        except Exception as e:
            logger.error(f"Error saving POST request: {e}")
    
    def is_trade_request(self, request):
        """Enhanced trade request detection with dual criteria"""
        url = request.url.lower()
        
        # Criteria 1: URL pattern match
        trade_url_patterns = ['/trade', '/orders', '/execute']
        url_match = any(pattern in url for pattern in trade_url_patterns)
        
        # Criteria 2: Body JSON contains trade keywords
        body_match = False
        detected_keywords = []
        
        try:
            post_data = request.post_data
            if post_data:
                post_data_lower = post_data.lower()
                trade_keywords = ['symbol', 'price', 'order', 'amount']
                
                for keyword in trade_keywords:
                    if keyword in post_data_lower:
                        detected_keywords.append(keyword)
                        body_match = True
        except:
            pass
        
        # Log detection details
        if url_match or body_match:
            detection_info = {
                'url_match': url_match,
                'body_match': body_match,
                'detected_keywords': detected_keywords,
                'url': request.url
            }
            logger.info(f"Trade request detected: {detection_info}")
            return True
        
        return False
    
    async def capture_trade_request(self, request):
        """Capture trade-specific request and log detection"""
        self.trade_detection_count += 1
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        logger.info(f"Capturing trade request #{self.trade_detection_count}: {request.url}")
        
        # Build cURL command
        curl_command = f"curl -X {request.method} '{request.url}'"
        
        # Add headers
        for name, value in request.headers.items():
            curl_command += f" -H '{name}: {value}'"
        
        # Add POST data if available
        post_data = request.post_data
        if post_data:
            curl_command += f" -d '{post_data}'"
        
        # Save to trade.sh (overwrite previous)
        try:
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write(curl_command)
            logger.info("Trade request saved to trade.sh")
        except Exception as e:
            logger.error(f"Error saving trade.sh: {e}")
            return
        
        # Convert to Python requests code
        await self.convert_curl_to_python(curl_command)
        
        # Log detection details
        await self.log_trade_detection(request, timestamp)
        
        # Store for analysis
        self.intercepted_requests.append({
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
            'post_data': post_data,
            'timestamp': datetime.now().isoformat(),
            'detection_count': self.trade_detection_count
        })
    
    async def log_trade_detection(self, request, timestamp):
        """Log trade detection details to trade_detections.log"""
        # Determine detected keywords
        detected_keywords = []
        try:
            post_data = request.post_data
            if post_data:
                post_data_lower = post_data.lower()
                trade_keywords = ['symbol', 'price', 'order', 'amount']
                detected_keywords = [kw for kw in trade_keywords if kw in post_data_lower]
        except:
            pass
        
        # Check URL patterns
        url = request.url.lower()
        url_patterns = ['/trade', '/orders', '/execute']
        detected_url_patterns = [pattern for pattern in url_patterns if pattern in url]
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'url': request.url,
            'detected_keywords': detected_keywords,
            'detected_url_patterns': detected_url_patterns,
            'curl_filename': f'post_request_{timestamp}.sh',
            'trade_sh_updated': True,
            'detection_count': self.trade_detection_count
        }
        
        # Append to trade detections log
        log_file = Path('logs/trade_detections.log')
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
            logger.info(f"Trade detection logged to: {log_file}")
        except Exception as e:
            logger.error(f"Error logging trade detection: {e}")
    
    async def convert_curl_to_python(self, curl_command):
        """Convert cURL command to Python requests code using curlconverter"""
        try:
            # Check if curlconverter is available
            result = subprocess.run(['python', '-c', 'import curlconverter'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Try to use curlconverter
                try:
                    import curlconverter
                    python_code = curlconverter.to_python(curl_command)
                    
                    # Add header comment
                    header = f'''#!/usr/bin/env python3
# Generated from cURL command at {datetime.now()}
# Trade detection count: {self.trade_detection_count}

'''
                    python_code = header + python_code
                    
                except Exception as e:
                    logger.warning(f"curlconverter failed: {e}, using template")
                    python_code = self.create_python_template(curl_command)
            else:
                logger.info("curlconverter not available, using template")
                python_code = self.create_python_template(curl_command)
            
            # Save to trade_request_full.py (overwrite previous)
            with open('trade_request_full.py', 'w', encoding='utf-8') as f:
                f.write(python_code)
            
            logger.info("Python requests code saved to trade_request_full.py")
            
        except Exception as e:
            logger.error(f"Error converting cURL to Python: {e}")
    
    def create_python_template(self, curl_command):
        """Create Python template when curlconverter is not available"""
        return f'''#!/usr/bin/env python3
# Generated from cURL command at {datetime.now()}
# Trade detection count: {self.trade_detection_count}
# Original cURL: {curl_command}

import requests
import json
from datetime import datetime

# TODO: Extract URL, headers, and data from cURL command
# This is a template - customize with actual values

url = "# Extract URL from cURL command"
headers = {{
    # Extract headers from cURL command
}}
data = {{
    # Extract POST data from cURL command
}}

response = requests.post(url, headers=headers, json=data)
print(f"Response: {{response.status_code}} - {{response.text}}")

# Original cURL command:
# {curl_command}
'''
    
    async def navigate_to_login(self):
        """Navigate to login page"""
        logger.info(f"Navigating to: {self.broker_url}")
        
        try:
            await self.page.goto(self.broker_url, wait_until='networkidle', timeout=30000)
            await self.page.wait_for_timeout(3000)  # Wait for page to stabilize
            
            # Take screenshot
            await self.page.screenshot(path='login_page_pro.png')
            logger.info("Screenshot saved: login_page_pro.png")
            
            # Check if we got a 404 or other error
            title = await self.page.title()
            if '404' in title or 'not found' in title.lower():
                logger.error(f"Login page returned 404 error. Title: {title}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to login page: {e}")
            await self.page.screenshot(path='navigation_error_pro.png')
            return False
    
    async def find_login_elements(self):
        """Find login form elements using retry logic"""
        logger.info("Searching for login elements with retry logic...")
        
        # Extended selectors for different login page layouts
        username_selectors = [
            'input[type="email"]',
            'input[type="text"]',
            'input[name="email"]',
            'input[name="username"]',
            'input[name="login"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]',
            'input[placeholder*="login" i]',
            '#email', '#username', '#login',
            '.email-input', '.username-input', '.login-input'
        ]
        
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[placeholder*="password" i]',
            '#password',
            '.password-input'
        ]
        
        button_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign In")',
            'button:has-text("Log In")',
            'button:has-text("Enter")',
            '.login-button', '.btn-login', '.submit-btn',
            '#login-btn', '#submit'
        ]
        
        # Use retry logic to find elements
        try:
            username_field = await self.waitForSelectorWithRetries(self.page, username_selectors)
        except Exception as e:
            logger.error(f"Username field not found: {e}")
            username_field = None
        
        try:
            password_field = await self.waitForSelectorWithRetries(self.page, password_selectors)
        except Exception as e:
            logger.error(f"Password field not found: {e}")
            password_field = None
        
        try:
            login_button = await self.waitForSelectorWithRetries(self.page, button_selectors)
        except Exception as e:
            logger.warning(f"Login button not found: {e}")
            login_button = None
        
        return {
            'username_field': username_field,
            'password_field': password_field,
            'login_button': login_button
        }
    
    async def perform_login(self, elements):
        """Perform login using found elements"""
        username_field = elements.get('username_field')
        password_field = elements.get('password_field')
        login_button = elements.get('login_button')
        
        if not username_field or not password_field:
            logger.error("Required login fields not found")
            return False
        
        try:
            logger.info("Filling login credentials...")
            
            # Clear and fill username
            await self.page.fill(username_field, '')
            await self.page.fill(username_field, self.username)
            await self.page.wait_for_timeout(1000)
            
            # Clear and fill password
            await self.page.fill(password_field, '')
            await self.page.fill(password_field, self.password)
            await self.page.wait_for_timeout(1000)
            
            # Take screenshot before login
            await self.page.screenshot(path='before_login_submit_pro.png')
            logger.info("Screenshot saved: before_login_submit_pro.png")
            
            # Submit login
            if login_button:
                await self.page.click(login_button)
                logger.info(f"Clicked login button: {login_button}")
            else:
                await self.page.press(password_field, 'Enter')
                logger.info("Pressed Enter on password field")
            
            # Wait for navigation or response
            await self.page.wait_for_timeout(5000)
            
            # Take screenshot after login
            await self.page.screenshot(path='after_login_submit_pro.png')
            logger.info("Screenshot saved: after_login_submit_pro.png")
            
            return await self.verify_login_success()
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            await self.page.screenshot(path='login_error_pro.png')
            return False
    
    async def verify_login_success(self):
        """Verify if login was successful"""
        current_url = self.page.url
        title = await self.page.title()
        
        logger.info(f"After login - URL: {current_url}")
        logger.info(f"After login - Title: {title}")
        
        # Check for success indicators
        success_indicators = [
            'dashboard', 'trading', 'account', 'portfolio', 'wallet',
            'home', 'main', 'trade', 'market'
        ]
        
        # Check URL
        url_success = any(indicator in current_url.lower() for indicator in success_indicators)
        
        # Check title
        title_success = any(indicator in title.lower() for indicator in success_indicators)
        
        # Check for login-specific failure indicators
        failure_indicators = ['login', 'signin', 'error', '404', 'not found']
        url_failure = any(indicator in current_url.lower() for indicator in failure_indicators)
        title_failure = any(indicator in title.lower() for indicator in failure_indicators)
        
        if url_success or title_success:
            logger.info("Login appears successful!")
            return True
        elif url_failure or title_failure:
            logger.error("Login appears to have failed")
            return False
        else:
            logger.warning("Login status unclear - manual verification needed")
            return False
    
    async def navigate_to_trading(self):
        """Navigate to trading page using retry logic"""
        current_url = self.page.url.lower()
        
        if 'trade' in current_url or 'trading' in current_url:
            logger.info("Already on trading page")
            return True
        
        # Look for trading navigation links with retry logic
        trading_selectors = [
            'a[href*="trade"]',
            'a[href*="trading"]',
            'a:has-text("Trade")',
            'a:has-text("Trading")',
            '.nav-trade', '.trading-link'
        ]
        
        try:
            trading_link = await self.waitForSelectorWithRetries(self.page, trading_selectors)
            await self.page.click(trading_link)
            logger.info(f"Clicked trading link: {trading_link}")
            await self.page.wait_for_timeout(3000)
            return True
        except Exception as e:
            logger.warning(f"Could not find trading navigation link: {e}")
            return False
    
    async def attempt_test_trade(self):
        """Look for trading interface elements using retry logic"""
        logger.info("Looking for trading interface elements with retry logic...")
        
        # Take screenshot of current page
        await self.page.screenshot(path='trading_interface_pro.png')
        logger.info("Screenshot saved: trading_interface_pro.png")
        
        # Look for common trading interface elements
        trade_selectors = [
            'button:has-text("Buy")',
            'button:has-text("Sell")',
            'button:has-text("Trade")',
            'button:has-text("Order")',
            '.buy-button', '.sell-button', '.trade-button',
            '#buy-btn', '#sell-btn', '#trade-btn'
        ]
        
        try:
            trading_button = await self.waitForSelectorWithRetries(self.page, trade_selectors)
            logger.info(f"Found trading button: {trading_button}")
            # Don't actually click - just log that we found it
            return True
        except Exception as e:
            logger.warning(f"No trading interface elements found: {e}")
            return False
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
                logger.info("Browser context closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def generate_summary_report(self):
        """Generate enhanced summary report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_requests_captured': len(self.intercepted_requests),
            'trade_detections_count': self.trade_detection_count,
            'requests': self.intercepted_requests,
            'directories_created': ['logs', 'logs/curls'],
            'files_generated': [
                'trade.sh',
                'trade_request_full.py',
                'logs/trade_detections.log'
            ]
        }
        
        with open('trade_requests_summary_pro.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Enhanced summary report saved: {len(self.intercepted_requests)} total requests, {self.trade_detection_count} trade detections")

async def main():
    """Main execution function"""
    logger.info("Starting TradeBot Sentinel Pro - Enhanced Version")
    
    sentinel = TradeBotSentinelPro()
    
    try:
        # Setup browser with network interception
        await sentinel.setup_browser()
        
        # Navigate to login page
        if not await sentinel.navigate_to_login():
            logger.error("Failed to navigate to login page")
            return
        
        # Find login elements with retry logic
        elements = await sentinel.find_login_elements()
        if not elements['username_field'] or not elements['password_field']:
            logger.error("Could not find required login elements")
            return
        
        # Perform login
        login_success = await sentinel.perform_login(elements)
        if not login_success:
            logger.error("Login failed")
            return
        
        logger.info("Login successful! Proceeding to trading interface...")
        
        # Navigate to trading page
        await sentinel.navigate_to_trading()
        
        # Look for trading interface (but don't actually trade)
        await sentinel.attempt_test_trade()
        
        # Keep browser open for manual inspection and trade capture
        logger.info("Keeping browser open for 60 seconds for manual inspection...")
        logger.info("You can now manually place a trade to test enhanced network interception")
        logger.info("All POST requests will be captured to logs/curls/ directory")
        logger.info("Trade-specific requests will update trade.sh and trade_request_full.py")
        await asyncio.sleep(60)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await sentinel.page.screenshot(path='unexpected_error_pro.png')
    finally:
        # Generate enhanced summary report
        sentinel.generate_summary_report()
        await sentinel.cleanup()
        logger.info("TradeBot Sentinel Pro completed")

if __name__ == "__main__":
    asyncio.run(main())