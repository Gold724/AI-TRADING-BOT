#!/usr/bin/env python3
"""
Simple Network Capture Test
Tests if our network interception is working correctly
"""

import asyncio
import json
import logging
from datetime import datetime
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_network_capture():
    """Test network request capture"""
    logger.info("🧪 Testing Network Capture...")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    
    # Setup network interception
    captured_requests = []
    
    async def handle_request(request):
        if request.method == 'POST':
            logger.info(f"📤 POST: {request.url}")
            
            # Check for trade keywords
            trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell']
            url_lower = request.url.lower()
            post_data = request.post_data or ''
            
            is_trade = any(keyword in url_lower for keyword in ['trade', 'order', 'buy', 'sell'])
            if post_data:
                is_trade = is_trade or any(keyword in post_data.lower() for keyword in trade_keywords)
            
            if is_trade:
                logger.info(f"🎯 POTENTIAL TRADE REQUEST: {request.url}")
                captured_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'data': post_data,
                    'timestamp': datetime.now().isoformat()
                })
    
    context.on('request', handle_request)
    
    page = await context.new_page()
    
    # Navigate to a test page that makes POST requests
    await page.goto('https://httpbin.org/forms/post')
    await page.fill('input[name="custname"]', 'Test User')
    await page.fill('input[name="custtel"]', '123456789')
    await page.fill('input[name="custemail"]', 'test@example.com')
    await page.select_option('select[name="size"]', 'large')
    
    # Submit form to generate POST request
    await page.click('input[type="submit"]')
    await asyncio.sleep(2)
    
    logger.info(f"📊 Captured {len(captured_requests)} potential trade requests")
    
    if captured_requests:
        with open('test_capture.json', 'w') as f:
            json.dump(captured_requests, f, indent=2)
        logger.info("💾 Test results saved to test_capture.json")
    
    await browser.close()
    logger.info("✅ Network capture test completed")

if __name__ == "__main__":
    asyncio.run(test_network_capture())