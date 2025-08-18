#!/usr/bin/env python3
"""
Simple Login Debug Script for Bulenox Trading Platform
Focuses on login process without Unicode characters to avoid encoding issues
"""

import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import logging
from datetime import datetime

# Setup logging without Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_login_debug.log', encoding='utf-8'),
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

class SimpleLoginDebugger:
    def __init__(self):
        self.username = os.getenv('BULENOX_USERNAME')
        self.password = os.getenv('BULENOX_PASSWORD')
        self.context = None
        self.page = None
        
        if not self.username or not self.password:
            logger.error("Missing credentials! Please set BULENOX_USERNAME and BULENOX_PASSWORD")
            sys.exit(1)
        
        logger.info(f"Credentials loaded for user: {self.username[:3]}***")
    
    async def setup_browser(self):
        """Setup browser with persistent context"""
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
        
        logger.info("Browser setup complete")
    
    async def navigate_to_login(self):
        """Navigate to login page"""
        login_url = "https://bulenox.projectx.com/login"
        logger.info(f"Navigating to: {login_url}")
        
        try:
            await self.page.goto(login_url, wait_until='networkidle', timeout=30000)
            await self.page.wait_for_timeout(3000)  # Wait for page to stabilize
            
            # Take screenshot
            await self.page.screenshot(path='login_page_debug.png')
            logger.info("Screenshot saved: login_page_debug.png")
            
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to login page: {e}")
            return False
    
    async def analyze_login_page(self):
        """Analyze the current page to understand login elements"""
        logger.info("Analyzing login page elements...")
        
        try:
            # Get page title
            title = await self.page.title()
            logger.info(f"Page title: {title}")
            
            # Get current URL
            current_url = self.page.url
            logger.info(f"Current URL: {current_url}")
            
            # Look for common login form elements
            login_selectors = [
                'input[type="email"]',
                'input[type="text"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[placeholder*="email"]',
                'input[placeholder*="Email"]',
                'input[placeholder*="username"]',
                'input[placeholder*="Username"]'
            ]
            
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password"]',
                'input[placeholder*="Password"]'
            ]
            
            button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                '.login-button',
                '.btn-login'
            ]
            
            # Check for username/email field
            username_field = None
            for selector in login_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        username_field = selector
                        logger.info(f"Found username field: {selector}")
                        break
                except:
                    continue
            
            # Check for password field
            password_field = None
            for selector in password_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        password_field = selector
                        logger.info(f"Found password field: {selector}")
                        break
                except:
                    continue
            
            # Check for login button
            login_button = None
            for selector in button_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        login_button = selector
                        logger.info(f"Found login button: {selector}")
                        break
                except:
                    continue
            
            # Get all form elements for analysis
            forms = await self.page.query_selector_all('form')
            logger.info(f"Found {len(forms)} form(s) on the page")
            
            # Get all input elements
            inputs = await self.page.query_selector_all('input')
            logger.info(f"Found {len(inputs)} input element(s) on the page")
            
            for i, input_elem in enumerate(inputs):
                try:
                    input_type = await input_elem.get_attribute('type')
                    input_name = await input_elem.get_attribute('name')
                    input_placeholder = await input_elem.get_attribute('placeholder')
                    logger.info(f"Input {i+1}: type='{input_type}', name='{input_name}', placeholder='{input_placeholder}'")
                except:
                    continue
            
            return {
                'username_field': username_field,
                'password_field': password_field,
                'login_button': login_button,
                'forms_count': len(forms),
                'inputs_count': len(inputs)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing login page: {e}")
            return None
    
    async def attempt_login(self, analysis_result):
        """Attempt to login using discovered elements"""
        if not analysis_result:
            logger.error("No analysis result available for login attempt")
            return False
        
        username_field = analysis_result.get('username_field')
        password_field = analysis_result.get('password_field')
        login_button = analysis_result.get('login_button')
        
        if not username_field or not password_field:
            logger.error("Could not find required login fields")
            return False
        
        try:
            logger.info("Attempting to fill login form...")
            
            # Fill username
            await self.page.fill(username_field, self.username)
            logger.info("Username filled")
            await self.page.wait_for_timeout(1000)
            
            # Fill password
            await self.page.fill(password_field, self.password)
            logger.info("Password filled")
            await self.page.wait_for_timeout(1000)
            
            # Take screenshot before clicking login
            await self.page.screenshot(path='before_login_click.png')
            logger.info("Screenshot saved: before_login_click.png")
            
            # Click login button
            if login_button:
                await self.page.click(login_button)
                logger.info(f"Clicked login button: {login_button}")
            else:
                # Try pressing Enter on password field
                await self.page.press(password_field, 'Enter')
                logger.info("Pressed Enter on password field")
            
            # Wait for navigation or response
            await self.page.wait_for_timeout(5000)
            
            # Take screenshot after login attempt
            await self.page.screenshot(path='after_login_attempt.png')
            logger.info("Screenshot saved: after_login_attempt.png")
            
            # Check current URL
            current_url = self.page.url
            logger.info(f"URL after login attempt: {current_url}")
            
            # Check for common success indicators
            success_indicators = [
                'dashboard',
                'trading',
                'account',
                'portfolio',
                'wallet'
            ]
            
            url_indicates_success = any(indicator in current_url.lower() for indicator in success_indicators)
            
            if url_indicates_success:
                logger.info("Login appears successful based on URL")
                return True
            else:
                logger.info("Login may have failed - still on login page or error page")
                
                # Check for error messages
                error_selectors = [
                    '.error',
                    '.alert-danger',
                    '.login-error',
                    '[class*="error"]',
                    '[class*="invalid"]'
                ]
                
                for selector in error_selectors:
                    try:
                        error_elem = await self.page.query_selector(selector)
                        if error_elem:
                            error_text = await error_elem.text_content()
                            logger.error(f"Error message found: {error_text}")
                    except:
                        continue
                
                return False
        
        except Exception as e:
            logger.error(f"Error during login attempt: {e}")
            await self.page.screenshot(path='login_error.png')
            return False
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
                logger.info("Browser context closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main execution function"""
    logger.info("Starting Simple Login Debug Script")
    
    debugger = SimpleLoginDebugger()
    
    try:
        # Setup browser
        await debugger.setup_browser()
        
        # Navigate to login page
        if not await debugger.navigate_to_login():
            logger.error("Failed to navigate to login page")
            return
        
        # Analyze login page
        analysis = await debugger.analyze_login_page()
        if not analysis:
            logger.error("Failed to analyze login page")
            return
        
        # Attempt login
        login_success = await debugger.attempt_login(analysis)
        
        if login_success:
            logger.info("LOGIN SUCCESSFUL!")
        else:
            logger.error("LOGIN FAILED - Check screenshots for details")
        
        # Keep browser open for manual inspection
        logger.info("Keeping browser open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await debugger.cleanup()
        logger.info("Script completed")

if __name__ == "__main__":
    asyncio.run(main())