#!/usr/bin/env python3
"""
Test Chrome Browser Opening Visibly
"""

import asyncio
from playwright.async_api import async_playwright

async def test_chrome_visible():
    print("[INFO] Starting Chrome browser test (visible mode)...")
    
    async with async_playwright() as playwright:
        # Launch Chrome in visible mode
        browser = await playwright.chromium.launch(
            headless=False,  # This makes Chrome visible
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security'
            ]
        )
        
        print("[SUCCESS] Chrome browser launched successfully!")
        
        # Create a new page
        page = await browser.new_page()
        print("[INFO] New page created")
        
        # Navigate to Bulenox login page
        print("[INFO] Navigating to Bulenox login page...")
        await page.goto('https://bulenox.projectx.com/login')
        
        # Wait for page to load
        await page.wait_for_load_state('networkidle')
        print(f"[SUCCESS] Page loaded: {page.url}")
        
        # Take a screenshot
        await page.screenshot(path='chrome_visible_test.png')
        print("[INFO] Screenshot saved as chrome_visible_test.png")
        
        # Keep browser open for 10 seconds so you can see it
        print("[INFO] Keeping browser open for 10 seconds...")
        await page.wait_for_timeout(10000)
        
        # Close browser
        await browser.close()
        print("[SUCCESS] Browser closed successfully")

if __name__ == "__main__":
    asyncio.run(test_chrome_visible())