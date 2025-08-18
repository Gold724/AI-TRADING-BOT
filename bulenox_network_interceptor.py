#!/usr/bin/env python3
"""
Bulenox Network Interceptor
Connects to existing Chrome instance with debugging enabled
Captures and saves trade-related network requests as cURL commands

Usage:
1. Launch Chrome with debugging: 
   chrome.exe --remote-debugging-port=9222 --user-data-dir="path" --profile-directory="Profile 13"
2. Navigate to Bulenox and login
3. Run this script: python bulenox_network_interceptor.py
4. Perform trading actions
5. Press Ctrl+C to stop and save logs
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Set UTF-8 encoding for Windows
if os.name == 'nt':
    os.system('chcp 65001 > nul')

os.environ['PYTHONIOENCODING'] = 'utf-8'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playwright'])
    subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
    from playwright.async_api import async_playwright

class BulenoxNetworkInterceptor:
    def __init__(self):
        self.setup_logging()
        self.trade_requests = []
        self.all_requests = []
        self.debug_port = 9222
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('network_interceptor.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def connect_to_existing_chrome(self):
        """Connect to existing Chrome instance with debugging enabled"""
        try:
            self.logger.info(f"🔗 Connecting to Chrome debug port {self.debug_port}...")
            
            playwright = await async_playwright().start()
            
            # Connect to existing Chrome instance
            browser = await playwright.chromium.connect_over_cdp(f"http://localhost:{self.debug_port}")
            
            # Get all contexts and pages
            contexts = browser.contexts
            if not contexts:
                self.logger.error("❌ No browser contexts found. Make sure Chrome is running with debugging enabled.")
                return None, None, None
                
            context = contexts[0]  # Use first context
            pages = context.pages
            
            if not pages:
                self.logger.error("❌ No pages found. Make sure you have Bulenox open in Chrome.")
                return None, None, None
                
            page = pages[0]  # Use first page
            
            self.logger.info(f"✅ Connected to Chrome! Found {len(pages)} page(s)")
            self.logger.info(f"📄 Current page URL: {page.url}")
            
            # Set up network interceptors
            await self._setup_network_interceptors(page)
            
            return playwright, browser, page
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Chrome: {e}")
            self.logger.error("Make sure Chrome is running with: --remote-debugging-port=9222")
            return None, None, None
    
    async def _setup_network_interceptors(self, page):
        """Setup network request/response interceptors"""
        self.logger.info("🕸️ Setting up network interceptors...")
        
        # Listen to all requests
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        
        self.logger.info("✅ Network interceptors active!")
        
    async def _on_request(self, request):
        """Handle outgoing requests"""
        try:
            url = request.url
            method = request.method
            
            # Log all POST requests
            if method == "POST":
                self.logger.info(f"📤 POST: {url}")
                
                # Check if this might be a trade request
                if await self._is_trade_request(request):
                    self.logger.info(f"🎯 POTENTIAL TRADE REQUEST: {url}")
                    await self._capture_trade_request(request)
                    
            # Store all requests for analysis
            self.all_requests.append({
                'timestamp': datetime.now().isoformat(),
                'method': method,
                'url': url,
                'headers': dict(request.headers)
            })
            
        except Exception as e:
            self.logger.error(f"❌ Error processing request: {e}")
    
    async def _on_response(self, response):
        """Handle incoming responses"""
        try:
            if response.request.method == "POST":
                self.logger.info(f"📥 Response {response.status}: {response.url}")
        except Exception as e:
            self.logger.error(f"❌ Error processing response: {e}")
    
    async def _is_trade_request(self, request) -> bool:
        """Determine if request is trade-related"""
        try:
            url = request.url.lower()
            
            # Check URL for trade-related keywords
            trade_keywords = [
                'trade', 'order', 'buy', 'sell', 'position', 'execute',
                'chart', 'symbol', 'market', 'price', 'amount', 'quantity'
            ]
            
            url_has_keywords = any(keyword in url for keyword in trade_keywords)
            
            # Check POST data if available
            post_data = request.post_data
            data_has_keywords = False
            
            if post_data:
                post_data_lower = post_data.lower()
                data_has_keywords = any(keyword in post_data_lower for keyword in trade_keywords)
            
            return url_has_keywords or data_has_keywords
            
        except Exception as e:
            self.logger.error(f"❌ Error checking trade request: {e}")
            return False
    
    async def _capture_trade_request(self, request):
        """Capture and save trade request as cURL command"""
        try:
            url = request.url
            method = request.method
            headers = request.headers
            post_data = request.post_data
            
            self.logger.info(f"💾 Capturing trade request: {method} {url}")
            
            # Build cURL command
            curl_parts = ['curl']
            
            # Add method
            if method != 'GET':
                curl_parts.append(f'-X {method}')
            
            # Add headers
            for name, value in headers.items():
                # Escape quotes in header values
                escaped_value = value.replace('"', '\\"')
                curl_parts.append(f'-H "{name}: {escaped_value}"')
            
            # Add POST data
            if post_data:
                # Escape quotes in post data
                escaped_data = post_data.replace('"', '\\"')
                curl_parts.append(f'-d "{escaped_data}"')
                
            # Add URL
            curl_parts.append(f"'{url}'")
            
            # Join all parts with spaces
            curl_command = ' '.join(curl_parts)
            
            # Save to file
            with open('trade.sh', 'w', encoding='utf-8') as f:
                f.write(curl_command)
                
            self.logger.info("[SAVED] Trade cURL command saved to trade.sh")
            
            # Store for later analysis
            self.trade_requests.append({
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'method': method,
                'headers': dict(headers),
                'post_data': post_data,
                'curl_command': curl_command
            })
            
        except Exception as e:
            self.logger.error(f"❌ Error capturing trade request: {e}")
    
    async def save_logs(self):
        """Save all captured data to files"""
        try:
            # Save all requests
            with open('all_requests.json', 'w', encoding='utf-8') as f:
                json.dump(self.all_requests, f, indent=2, ensure_ascii=False)
            
            # Save trade requests
            with open('trade_requests.json', 'w', encoding='utf-8') as f:
                json.dump(self.trade_requests, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"💾 Saved {len(self.all_requests)} total requests")
            self.logger.info(f"🎯 Saved {len(self.trade_requests)} trade requests")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving logs: {e}")

async def main():
    """Main execution function"""
    interceptor = BulenoxNetworkInterceptor()
    
    print("🤖 Bulenox Network Interceptor")
    print("==============================")
    print("📋 Instructions:")
    print("1. Make sure Chrome is running with debugging enabled")
    print("2. Navigate to Bulenox and login")
    print("3. This script will capture network requests")
    print("4. Perform trading actions")
    print("5. Press Ctrl+C to stop and save logs")
    print("")
    
    playwright, browser, page = await interceptor.connect_to_existing_chrome()
    
    if not all([playwright, browser, page]):
        print("❌ Failed to connect to Chrome. Exiting.")
        return False
    
    try:
        print("🎯 Monitoring network requests... Press Ctrl+C to stop")
        print("")
        
        # Keep the script running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping interceptor...")
        
    finally:
        # Save logs before closing
        await interceptor.save_logs()
        
        # Clean up
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
            
        print("✅ Network interceptor stopped and logs saved")
        return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)