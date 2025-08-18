#!/usr/bin/env python3
"""
TradeBot Sentinel - Trade Endpoint Discovery Script
Automatically discovers and captures all missing trade execution endpoints
for complete VPS automation deployment.

This script:
1. Logs into Bulenox trading platform
2. Navigates through ORDER and DOM trading modes
3. Clicks all trade execution buttons (BUY, SELL, Cancel, Modify)
4. Intercepts and saves all POST/PUT/DELETE requests as cURL files
5. Organizes captured endpoints for VPS deployment

Usage:
    python trade_endpoint_discovery.py [--headless] [--visible]
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Request, Response
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trade_endpoint_discovery.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set console encoding to UTF-8 for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
logger = logging.getLogger(__name__)

class TradeEndpointDiscovery:
    """Automated trade endpoint discovery and capture system."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Environment variables
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("BULENOX_USERNAME and BULENOX_PASSWORD environment variables required")
        
        # Create directories
        self.setup_directories()
        
        # Captured requests tracking
        self.captured_requests: List[Dict] = []
        self.action_mapping: Dict[str, str] = {}
        
        # UI Selectors
        self.selectors = {
            'login': {
                'username': 'input[name="userName"]',
                'password': 'input[name="password"]',
                'login_button': 'button[type="submit"]'
            },
            'trade_symbols': {
                'order_mode': '#\\:r1b\\:',
                'dom_mode': '#\\:r19\\:'
            },
            'trade_amounts': {
                'order_mode': '#\\:r19\\:',
                'dom_mode': '#domTab > div > div.MuiBox-root.css-8bdrja > div:nth-child(3) > div.commonOrderOptions_mainBoxNotMobile__zlgnm.MuiBox-root.css-0 > div.MuiBox-root.css-9jol9y > div > button.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedNeutral.MuiButton-sizeMedium.MuiButton-containedSizeMedium.MuiButton-root.MuiButton-contained.MuiButton-containedNeutral.MuiButton-sizeMedium.MuiButton-containedSizeMedium.css-1cijfts'
            },
            'trade_buttons': {
                'order_buy': '#orderCardTab > div > div > div.commonOrderOptions_mainBoxNotMobile__zlgnm.MuiBox-root.css-0 > div.commonOrderOptions_buttonBoxNotMobile__47orV.MuiBox-root.css-p58oka > button.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeLarge.MuiButton-containedSizeLarge.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeLarge.MuiButton-containedSizeLarge.css-ry6hsj',
                'order_sell': '#orderCardTab > div > div > div.commonOrderOptions_mainBoxNotMobile__zlgnm.MuiBox-root.css-0 > div.commonOrderOptions_buttonBoxNotMobile__47orV.MuiBox-root.css-p58oka > button.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedError.MuiButton-sizeLarge.MuiButton-containedSizeLarge.MuiButton-root.MuiButton-contained.MuiButton-containedError.MuiButton-sizeLarge.MuiButton-containedSizeLarge.css-1i5yab8',
                'dom_buy': '#domTab > div > div.MuiBox-root.css-8bdrja > div:nth-child(3) > div.commonOrderOptions_mainBoxNotMobile__zlgnm.MuiBox-root.css-0 > div.commonOrderOptions_buttonBoxNotMobile__47orV.MuiBox-root.css-p58oka > button.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeLarge.MuiButton-containedSizeLarge.MuiButton-root.MuiButton-contained.MuiButton-containedSuccess.MuiButton-sizeLarge.MuiButton-containedSizeLarge.css-ry6hsj',
                'dom_sell': '#domTab > div > div.MuiBox-root.css-8bdrja > div:nth-child(3) > div.commonOrderOptions_mainBoxNotMobile__zlgnm.MuiBox-root.css-0 > div.commonOrderOptions_buttonBoxNotMobile__47orV.MuiBox-root.css-p58oka > button.MuiButtonBase-root.MuiButton-root.MuiButton-contained.MuiButton-containedError.MuiButton-sizeLarge.MuiButton-containedSizeLarge.MuiButton-root.MuiButton-contained.MuiButton-containedError.MuiButton-sizeLarge.MuiButton-containedSizeLarge.css-1i5yab8'
            },
            'management': {
                'cancel_trade': '#positionTab > div > div > div.MuiDataGrid-main.css-opb0c2 > div.MuiDataGrid-virtualScroller.css-1pzb349 > div > div > div > div:nth-child(8) > button > svg',
                'positions_tab': '#rc-tabs-8-tab-positionTab > div'
            },
            'modals': {
                'time_sync_proceed': '#root > div > div.ModalContext_modalWrapper__CBy3x > div > div > div.modal_footer__17zbN > button'
            }
        }
    
    def setup_directories(self):
        """Create required directories for logs and captures."""
        directories = [
            'logs/curls',
            'logs/json',
            'logs/screenshots',
            'logs/endpoints'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ensured: {directory}")
    
    async def wait_for_selector_with_retries(self, selector: str, timeout: int = 10000, retries: int = 3) -> bool:
        """Wait for selector with retry logic and fallback selectors."""
        for attempt in range(retries):
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                logger.info(f"✅ Selector found: {selector[:50]}...")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1}/{retries} failed for selector: {selector[:50]}... - {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                else:
                    logger.error(f"❌ All attempts failed for selector: {selector[:50]}...")
                    return False
        return False
    
    async def setup_network_interception(self):
        """Setup network request interception for capturing trade endpoints."""
        async def handle_request(request: Request):
            # Only capture POST, PUT, DELETE requests to Bulenox API
            if (request.method in ['POST', 'PUT', 'DELETE'] and 
                'userapi.bulenox.projectx.com' in request.url):
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                
                # Determine action type based on URL and payload
                action_type = self.determine_action_type(request)
                
                request_data = {
                    'timestamp': timestamp,
                    'action_type': action_type,
                    'method': request.method,
                    'url': request.url,
                    'headers': dict(request.headers),
                    'post_data': request.post_data
                }
                
                self.captured_requests.append(request_data)
                
                # Save as cURL file
                await self.save_curl_file(request_data)
                
                # Save JSON body if present
                if request.post_data:
                    await self.save_json_file(request_data)
                
                logger.info(f"🎯 Captured {action_type}: {request.method} {request.url}")
        
        async def handle_response(response: Response):
            # Log response status for captured requests
            if (response.request.method in ['POST', 'PUT', 'DELETE'] and 
                'userapi.bulenox.projectx.com' in response.url):
                logger.info(f"📡 Response {response.status}: {response.url}")
        
        self.page.on('request', handle_request)
        self.page.on('response', handle_response)
        logger.info("🔍 Network interception enabled")
    
    def determine_action_type(self, request: Request) -> str:
        """Determine the action type based on URL and request data."""
        url = request.url.lower()
        post_data = request.post_data or ''
        
        # URL-based detection
        if '/orders' in url:
            if 'buy' in post_data.lower() or 'side":"buy' in post_data.lower():
                return 'order_buy_execution'
            elif 'sell' in post_data.lower() or 'side":"sell' in post_data.lower():
                return 'order_sell_execution'
            else:
                return 'order_management'
        elif '/positions' in url:
            return 'position_management'
        elif '/cancel' in url:
            return 'order_cancellation'
        elif '/modify' in url or '/update' in url:
            return 'order_modification'
        elif '/accounts' in url:
            return 'account_data'
        elif '/trades' in url:
            return 'trade_history'
        else:
            # Content-based detection
            if any(keyword in post_data.lower() for keyword in ['buy', 'sell', 'order', 'trade']):
                return 'trade_execution'
            else:
                return 'api_request'
    
    async def save_curl_file(self, request_data: Dict):
        """Save request as cURL file."""
        timestamp = request_data['timestamp']
        action_type = request_data['action_type']
        
        filename = f"logs/curls/{timestamp}_{action_type}.curl"
        
        # Build cURL command
        curl_command = f"#!/bin/bash\n"
        curl_command += f"# TradeBot Sentinel - Trade Endpoint Discovery\n"
        curl_command += f"# Timestamp: {datetime.now().isoformat()}\n"
        curl_command += f"# URL: {request_data['url']}\n"
        curl_command += f"# Action: {action_type}\n\n"
        
        curl_command += f"curl -X {request_data['method']} '{request_data['url']}' \\"
        
        # Add headers
        for key, value in request_data['headers'].items():
            if key.lower() not in ['content-length', 'host']:
                curl_command += f"  -H '{key}: {value}' \\"
        
        # Add post data
        if request_data['post_data']:
            curl_command += f"  -d '{request_data['post_data']}'\n"
        else:
            curl_command = curl_command.rstrip(' \\') + '\n'
        
        curl_command += "\n# End of cURL command\n"
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(curl_command)
        
        # Update action mapping
        self.action_mapping[action_type] = filename
        
        logger.info(f"💾 Saved cURL: {filename}")
    
    async def save_json_file(self, request_data: Dict):
        """Save JSON request body."""
        if not request_data['post_data']:
            return
        
        timestamp = request_data['timestamp']
        action_type = request_data['action_type']
        
        filename = f"logs/json/{timestamp}_{action_type}.json"
        
        try:
            # Try to parse and pretty-print JSON
            json_data = json.loads(request_data['post_data'])
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # Save as raw text if not valid JSON
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(request_data['post_data'])
        
        logger.info(f"📄 Saved JSON: {filename}")
    
    async def take_screenshot(self, action: str, stage: str = 'before'):
        """Take screenshot before/after actions."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs/screenshots/{timestamp}_{action}_{stage}.png"
        
        await self.page.screenshot(path=filename, full_page=True)
        logger.info(f"[SCREENSHOT] {filename}")
    
    async def login(self) -> bool:
        """Login to Bulenox platform."""
        logger.info("[LOGIN] Starting login process...")
        
        try:
            # Navigate to login page
            await self.page.goto('https://bulenox.projectx.com/login', wait_until='networkidle')
            await self.take_screenshot('login', 'page_loaded')
            
            # Handle Time Sync Warning if present
            await self.handle_time_sync_warning()
            
            # Wait for login form
            if not await self.wait_for_selector_with_retries(self.selectors['login']['username']):
                logger.error("❌ Login form not found")
                return False
            
            # Fill username
            await self.page.fill(self.selectors['login']['username'], self.username)
            logger.info(f"✅ Username filled: {self.username}")
            
            # Fill password
            await self.page.fill(self.selectors['login']['password'], self.password)
            logger.info("✅ Password filled")
            
            await self.take_screenshot('login', 'credentials_filled')
            
            # Click login button
            await self.page.click(self.selectors['login']['login_button'])
            logger.info("✅ Login button clicked")
            
            # Wait for successful login (dashboard elements)
            dashboard_selectors = [
                '#root > div > div.MuiBox-root.css-tuiyjr',
                '.trading-interface',
                '#orderCardTab',
                '#domTab'
            ]
            
            login_success = False
            for selector in dashboard_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    login_success = True
                    logger.info(f"✅ Login successful - found: {selector}")
                    break
                except:
                    continue
            
            if not login_success:
                logger.error("❌ Login failed - dashboard not loaded")
                await self.take_screenshot('login', 'failed')
                return False
            
            await self.take_screenshot('login', 'success')
            logger.info("🎉 Login completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login error: {str(e)}")
            await self.take_screenshot('login', 'error')
            return False
    
    async def handle_time_sync_warning(self):
        """Handle Time Sync Warning modal if present."""
        try:
            await self.page.wait_for_selector(self.selectors['modals']['time_sync_proceed'], timeout=3000)
            await self.page.click(self.selectors['modals']['time_sync_proceed'])
            logger.info("✅ Time Sync Warning handled")
            await asyncio.sleep(1)
        except:
            # Modal not present, continue
            pass
    
    async def navigate_to_trading_interface(self) -> bool:
        """Navigate to trading interface and ensure it's ready."""
        logger.info("🎯 Navigating to trading interface...")
        
        try:
            # Check if already on trading page
            current_url = self.page.url
            if '/trade' not in current_url:
                await self.page.goto('https://bulenox.projectx.com/trade', wait_until='networkidle')
                logger.info("✅ Navigated to trading page")
            
            # Wait for trading interface elements
            trading_selectors = [
                '#orderCardTab',
                '#domTab',
                self.selectors['trade_buttons']['order_buy'],
                self.selectors['trade_buttons']['dom_buy']
            ]
            
            for selector in trading_selectors:
                if await self.wait_for_selector_with_retries(selector, timeout=5000):
                    logger.info(f"✅ Trading interface ready: {selector[:30]}...")
                    break
            else:
                logger.error("❌ Trading interface not ready")
                return False
            
            await self.take_screenshot('trading_interface', 'ready')
            return True
            
        except Exception as e:
            logger.error(f"❌ Trading interface error: {str(e)}")
            return False
    
    async def execute_order_mode_trades(self):
        """Execute trades in ORDER mode to capture endpoints."""
        logger.info("📊 Executing ORDER mode trades...")
        
        try:
            # Ensure ORDER tab is active
            await self.page.click('#orderCardTab')
            await asyncio.sleep(2)
            
            # Set symbol (if needed)
            symbol_input = self.selectors['trade_symbols']['order_mode']
            if await self.wait_for_selector_with_retries(symbol_input, timeout=5000):
                await self.page.fill(symbol_input, '/GC')
                logger.info("✅ ORDER symbol set: /GC")
            
            # Set amount (if needed)
            amount_input = self.selectors['trade_amounts']['order_mode']
            if await self.wait_for_selector_with_retries(amount_input, timeout=5000):
                await self.page.fill(amount_input, '1')
                logger.info("✅ ORDER amount set: 1")
            
            await self.take_screenshot('order_mode', 'setup_complete')
            
            # Execute BUY order
            logger.info("🟢 Executing ORDER BUY...")
            buy_button = self.selectors['trade_buttons']['order_buy']
            if await self.wait_for_selector_with_retries(buy_button):
                await self.take_screenshot('order_buy', 'before')
                await self.page.click(buy_button)
                await asyncio.sleep(3)  # Wait for request to complete
                await self.take_screenshot('order_buy', 'after')
                logger.info("✅ ORDER BUY executed")
            else:
                logger.error("❌ ORDER BUY button not found")
            
            # Execute SELL order
            logger.info("🔴 Executing ORDER SELL...")
            sell_button = self.selectors['trade_buttons']['order_sell']
            if await self.wait_for_selector_with_retries(sell_button):
                await self.take_screenshot('order_sell', 'before')
                await self.page.click(sell_button)
                await asyncio.sleep(3)  # Wait for request to complete
                await self.take_screenshot('order_sell', 'after')
                logger.info("✅ ORDER SELL executed")
            else:
                logger.error("❌ ORDER SELL button not found")
                
        except Exception as e:
            logger.error(f"❌ ORDER mode execution error: {str(e)}")
    
    async def execute_dom_mode_trades(self):
        """Execute trades in DOM mode to capture endpoints."""
        logger.info("📈 Executing DOM mode trades...")
        
        try:
            # Switch to DOM tab
            await self.page.click('#domTab')
            await asyncio.sleep(2)
            
            # Set symbol (if needed)
            symbol_input = self.selectors['trade_symbols']['dom_mode']
            if await self.wait_for_selector_with_retries(symbol_input, timeout=5000):
                await self.page.fill(symbol_input, '/GC')
                logger.info("✅ DOM symbol set: /GC")
            
            await self.take_screenshot('dom_mode', 'setup_complete')
            
            # Execute BUY order
            logger.info("🟢 Executing DOM BUY...")
            buy_button = self.selectors['trade_buttons']['dom_buy']
            if await self.wait_for_selector_with_retries(buy_button):
                await self.take_screenshot('dom_buy', 'before')
                await self.page.click(buy_button)
                await asyncio.sleep(3)  # Wait for request to complete
                await self.take_screenshot('dom_buy', 'after')
                logger.info("✅ DOM BUY executed")
            else:
                logger.error("❌ DOM BUY button not found")
            
            # Execute SELL order
            logger.info("🔴 Executing DOM SELL...")
            sell_button = self.selectors['trade_buttons']['dom_sell']
            if await self.wait_for_selector_with_retries(sell_button):
                await self.take_screenshot('dom_sell', 'before')
                await self.page.click(sell_button)
                await asyncio.sleep(3)  # Wait for request to complete
                await self.take_screenshot('dom_sell', 'after')
                logger.info("✅ DOM SELL executed")
            else:
                logger.error("❌ DOM SELL button not found")
                
        except Exception as e:
            logger.error(f"❌ DOM mode execution error: {str(e)}")
    
    async def execute_position_management(self):
        """Execute position management actions to capture endpoints."""
        logger.info("📋 Executing position management...")
        
        try:
            # Switch to positions tab
            positions_tab = self.selectors['management']['positions_tab']
            if await self.wait_for_selector_with_retries(positions_tab):
                await self.page.click(positions_tab)
                await asyncio.sleep(2)
                logger.info("✅ Switched to positions tab")
            
            await self.take_screenshot('positions', 'tab_active')
            
            # Try to cancel a trade (if any positions exist)
            cancel_button = self.selectors['management']['cancel_trade']
            if await self.wait_for_selector_with_retries(cancel_button, timeout=5000):
                logger.info("🗑️ Executing trade cancellation...")
                await self.take_screenshot('cancel_trade', 'before')
                await self.page.click(cancel_button)
                await asyncio.sleep(3)
                await self.take_screenshot('cancel_trade', 'after')
                logger.info("✅ Trade cancellation executed")
            else:
                logger.info("ℹ️ No positions to cancel")
            
            # Look for any editable fields in positions table
            editable_selectors = [
                'input[type="text"]',
                'input[type="number"]',
                '.MuiInput-input',
                '[contenteditable="true"]'
            ]
            
            for selector in editable_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        logger.info(f"📝 Found {len(elements)} editable fields: {selector}")
                        # Try to modify first editable field
                        await elements[0].fill('999')
                        await asyncio.sleep(1)
                        # Trigger change event
                        await elements[0].press('Enter')
                        await asyncio.sleep(2)
                        logger.info("✅ Position modification attempted")
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Position management error: {str(e)}")
    
    async def generate_python_requests(self):
        """Generate Python requests code from captured cURLs."""
        logger.info("🐍 Generating Python requests code...")
        
        python_code = '''#!/usr/bin/env python3
"""
TradeBot Sentinel - Auto-generated Trade Requests
Generated from captured cURL commands
"""

import requests
import json
from datetime import datetime

class BulenoxTradeExecutor:
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_headers = {
            'authorization': f'Bearer {bearer_token}',
            'content-type': 'application/json',
            'x-app-type': 'px-desktop',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
'''
        
        # Generate methods for each captured action
        for action_type, filename in self.action_mapping.items():
            method_name = action_type.replace('-', '_')
            python_code += f'''    def {method_name}(self, **kwargs):
        """Execute {action_type} request."""
        # Implementation based on captured cURL: {filename}
        # TODO: Add specific implementation
        pass
    
'''
        
        python_code += '''    def execute_trade(self, symbol: str, side: str, amount: float, mode: str = 'ORDER'):
        """Execute a trade with the specified parameters."""
        if mode.upper() == 'ORDER':
            if side.upper() == 'BUY':
                return self.order_buy_execution(symbol=symbol, amount=amount)
            else:
                return self.order_sell_execution(symbol=symbol, amount=amount)
        elif mode.upper() == 'DOM':
            if side.upper() == 'BUY':
                return self.dom_buy_execution(symbol=symbol, amount=amount)
            else:
                return self.dom_sell_execution(symbol=symbol, amount=amount)
        else:
            raise ValueError(f"Unknown mode: {mode}")

if __name__ == "__main__":
    # Example usage
    executor = BulenoxTradeExecutor("your_bearer_token_here")
    # executor.execute_trade("/GC", "BUY", 1.0, "ORDER")
'''
        
        # Save Python file
        with open('trade_request_full.py', 'w', encoding='utf-8') as f:
            f.write(python_code)
        
        logger.info("✅ Python requests code generated: trade_request_full.py")
    
    async def generate_endpoint_summary(self):
        """Generate summary of captured endpoints."""
        logger.info("📊 Generating endpoint summary...")
        
        summary = {
            'discovery_timestamp': datetime.now().isoformat(),
            'total_endpoints_captured': len(self.captured_requests),
            'action_mapping': self.action_mapping,
            'captured_actions': list(set([req['action_type'] for req in self.captured_requests])),
            'endpoints_by_method': {},
            'unique_urls': list(set([req['url'] for req in self.captured_requests]))
        }
        
        # Group by HTTP method
        for req in self.captured_requests:
            method = req['method']
            if method not in summary['endpoints_by_method']:
                summary['endpoints_by_method'][method] = []
            summary['endpoints_by_method'][method].append({
                'url': req['url'],
                'action_type': req['action_type']
            })
        
        # Save summary
        with open('logs/endpoints/discovery_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Endpoint summary saved: {len(self.captured_requests)} endpoints captured")
        
        # Print summary to console
        print("\n" + "="*60)
        print("🎯 TRADE ENDPOINT DISCOVERY COMPLETE")
        print("="*60)
        print(f"📊 Total Endpoints Captured: {len(self.captured_requests)}")
        print(f"🎬 Unique Actions: {len(summary['captured_actions'])}")
        print(f"🌐 Unique URLs: {len(summary['unique_urls'])}")
        print("\n📋 Captured Actions:")
        for action in summary['captured_actions']:
            print(f"  ✅ {action}")
        print("\n🔗 Captured URLs:")
        for url in summary['unique_urls']:
            print(f"  🌐 {url}")
        print("="*60)
    
    async def run_discovery(self):
        """Main discovery process."""
        logger.info("🚀 Starting Trade Endpoint Discovery...")
        
        async with async_playwright() as p:
            # Launch browser
            self.browser = await p.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create context with persistent session
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Setup network interception
            await self.setup_network_interception()
            
            try:
                # Step 1: Login
                if not await self.login():
                    logger.error("❌ Login failed, aborting discovery")
                    return False
                
                # Step 2: Navigate to trading interface
                if not await self.navigate_to_trading_interface():
                    logger.error("❌ Trading interface not ready, aborting discovery")
                    return False
                
                # Step 3: Execute ORDER mode trades
                await self.execute_order_mode_trades()
                
                # Step 4: Execute DOM mode trades
                await self.execute_dom_mode_trades()
                
                # Step 5: Execute position management
                await self.execute_position_management()
                
                # Step 6: Generate Python requests code
                await self.generate_python_requests()
                
                # Step 7: Generate endpoint summary
                await self.generate_endpoint_summary()
                
                logger.info("🎉 Trade Endpoint Discovery completed successfully!")
                return True
                
            except Exception as e:
                logger.error(f"❌ Discovery error: {str(e)}")
                await self.take_screenshot('discovery', 'error')
                return False
            
            finally:
                # Cleanup
                if self.browser:
                    await self.browser.close()
                logger.info("🧹 Browser cleanup completed")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='TradeBot Sentinel - Trade Endpoint Discovery')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--visible', action='store_true', help='Run in visible mode (opposite of headless)')
    
    args = parser.parse_args()
    
    # Determine headless mode
    headless = True  # Default
    if args.visible:
        headless = False
    elif args.headless:
        headless = True
    
    print(f"[DISCOVERY] TradeBot Sentinel - Trade Endpoint Discovery")
    print(f"[MODE] {'Headless' if headless else 'Visible'}")
    print(f"[USERNAME] {os.getenv('BULENOX_USERNAME', 'Not set')}")
    print(f"[WORKDIR] {os.getcwd()}")
    print("="*60)
    
    # Run discovery
    discovery = TradeEndpointDiscovery(headless=headless)
    
    try:
        result = asyncio.run(discovery.run_discovery())
        if result:
            print("\n🎉 Discovery completed successfully!")
            print("📁 Check logs/curls/ for captured cURL files")
            print("📄 Check logs/json/ for JSON request bodies")
            print("📸 Check logs/screenshots/ for action screenshots")
            print("🐍 Check trade_request_full.py for Python code")
            sys.exit(0)
        else:
            print("\n❌ Discovery failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Discovery interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()