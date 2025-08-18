#!/usr/bin/env python3
"""
Simple diagnostic script to inspect the Bulenox login page structure
"""

import asyncio
from playwright.async_api import async_playwright
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def inspect_login_page():
    """Inspect the login page to understand its structure"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            logger.info("Navigating to login page...")
            await page.goto("https://bulenox.projectx.com/login", wait_until="domcontentloaded", timeout=60000)
            
            # Wait a bit for any dynamic content
            await page.wait_for_timeout(5000)
            
            # Take screenshot
            await page.screenshot(path="debug_login_page.png", full_page=True)
            logger.info("Screenshot saved: debug_login_page.png")
            
            # Get page title
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Get page URL
            url = page.url
            logger.info(f"Current URL: {url}")
            
            # Look for all input elements
            inputs = await page.query_selector_all("input")
            logger.info(f"Found {len(inputs)} input elements:")
            
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute("type") or "text"
                input_name = await input_elem.get_attribute("name") or "(no name)"
                input_id = await input_elem.get_attribute("id") or "(no id)"
                input_placeholder = await input_elem.get_attribute("placeholder") or "(no placeholder)"
                input_class = await input_elem.get_attribute("class") or "(no class)"
                
                logger.info(f"  Input {i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}', class='{input_class}'")
            
            # Look for all form elements
            forms = await page.query_selector_all("form")
            logger.info(f"Found {len(forms)} form elements")
            
            # Look for buttons
            buttons = await page.query_selector_all("button")
            logger.info(f"Found {len(buttons)} button elements:")
            
            for i, button in enumerate(buttons):
                button_text = await button.inner_text()
                button_type = await button.get_attribute("type") or "button"
                button_class = await button.get_attribute("class") or "(no class)"
                logger.info(f"  Button {i+1}: text='{button_text}', type='{button_type}', class='{button_class}'")
            
            # Get page content (first 1000 chars)
            content = await page.content()
            logger.info(f"Page content preview (first 1000 chars): {content[:1000]}")
            
            # Wait for user to see the page
            logger.info("Waiting 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            logger.error(f"Error inspecting page: {e}")
            await page.screenshot(path="debug_error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_login_page())