#!/usr/bin/env python3
"""
Quick script to find current login form selectors on Bulenox
"""

import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def find_login_selectors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("[INFO] Navigating to Bulenox login page...")
            await page.goto("https://bulenox.projectx.com/login", wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            print("[INFO] Looking for input fields...")
            
            # Find all input elements
            inputs = await page.query_selector_all('input')
            print(f"[INFO] Found {len(inputs)} input elements:")
            
            for i, input_elem in enumerate(inputs):
                input_id = await input_elem.get_attribute('id')
                input_name = await input_elem.get_attribute('name')
                input_type = await input_elem.get_attribute('type')
                input_placeholder = await input_elem.get_attribute('placeholder')
                input_class = await input_elem.get_attribute('class')
                
                print(f"  Input {i+1}:")
                print(f"    ID: {input_id}")
                print(f"    Name: {input_name}")
                print(f"    Type: {input_type}")
                print(f"    Placeholder: {input_placeholder}")
                print(f"    Class: {input_class}")
                print()
            
            # Look for buttons
            buttons = await page.query_selector_all('button')
            print(f"[INFO] Found {len(buttons)} button elements:")
            
            for i, button in enumerate(buttons):
                button_text = await button.inner_text()
                button_type = await button.get_attribute('type')
                button_class = await button.get_attribute('class')
                button_id = await button.get_attribute('id')
                
                print(f"  Button {i+1}:")
                print(f"    Text: {button_text}")
                print(f"    Type: {button_type}")
                print(f"    Class: {button_class}")
                print(f"    ID: {button_id}")
                print()
            
            # Wait for user to inspect
            print("[INFO] Browser will stay open for 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(find_login_selectors())