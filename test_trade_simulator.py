#!/usr/bin/env python3
"""
Test Trade Simulator for TradeBot Sentinel

This script simulates actual trade execution to test the improved trade detection
logic in trae_trade_capture.py. It creates realistic trade POST requests that
should be captured by the network interceptor.
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def simulate_trade_request(page):
    """Simulate a real trade POST request"""
    
    # Simulate various trade request types
    trade_requests = [
        {
            "url": "https://bulenox.projectx.com/api/trade/execute",
            "data": {
                "symbol": "GOLD",
                "side": "buy",
                "quantity": "0.01",
                "order_type": "market",
                "price": None,
                "stop_loss": None,
                "take_profit": None
            }
        },
        {
            "url": "https://bulenox.projectx.com/v1/order/place",
            "data": {
                "instrument": "/GC",
                "side": "sell", 
                "volume": "0.05",
                "type": "limit",
                "price": "2650.50",
                "execute_immediately": True
            }
        },
        {
            "url": "https://bulenox.projectx.com/trade/submit",
            "data": {
                "action": "buy",
                "symbol": "EURUSD",
                "quantity": "1.0",
                "order_type": "market",
                "position": "long"
            }
        }
    ]
    
    print("Simulating trade requests...")
    
    for i, trade in enumerate(trade_requests, 1):
        print(f"\nSimulating trade request {i}...")
        
        try:
            # Use page.evaluate to make the request from browser context
            response = await page.evaluate(f"""
                fetch('{trade["url"]}', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer fake-token-123'
                    }},
                    body: JSON.stringify({json.dumps(trade["data"])})
                }}).then(r => r.text()).catch(e => e.message)
            """)
            
            print(f"Trade request {i} sent to {trade['url']}")
            print(f"Response: {response}")
            
        except Exception as e:
            print(f"Trade request {i} failed: {e}")
        
        # Wait between requests
        await asyncio.sleep(2)

async def main():
    print("Starting Trade Request Simulator...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Set up request interceptor to see what gets captured
        captured_requests = []
        
        def on_request(request):
            if request.method.upper() == "POST":
                print(f"INTERCEPTED: {request.method} -> {request.url}")
                captured_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'data': request.post_data
                })
        
        page.on("request", on_request)
        
        # Go to a test page
        await page.goto("https://httpbin.org/")
        await page.wait_for_load_state("networkidle")
        
        # Simulate trade requests
        await simulate_trade_request(page)
        
        print(f"\nTotal requests captured: {len(captured_requests)}")
        for req in captured_requests:
            print(f"- {req['method']} {req['url']}")
        
        await browser.close()
        print("Simulation completed!")

if __name__ == "__main__":
    asyncio.run(main())