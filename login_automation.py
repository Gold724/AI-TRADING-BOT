#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login Automation Module for TradeBot Sentinel

This module provides robust login automation for the Bulenox trading platform
with fallback selectors and Time Sync Warning modal handling.

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from playwright.async_api import Page, Browser, ElementHandle

class LoginAutomation:
    """Handles robust login automation for Bulenox trading platform."""
    
    def __init__(self, page: Page, logger: Optional[logging.Logger] = None):
        """Initialize the login automation.
        
        Args:
            page: Playwright page instance
            logger: Optional logger instance
        """
        self.page = page
        self.logger = logger or logging.getLogger(__name__)
        
        # Login page selectors with fallbacks
        self.login_selectors = {
            'username_field': [
                'input[name="username"]',
                'input[id="username"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]',
                'input[type="text"]:first-of-type',
                '.login-form input[type="text"]',
                '#login-username',
                '.username-input',
                'input.form-control:first-of-type'
            ],
            'password_field': [
                'input[name="password"]',
                'input[id="password"]',
                'input[type="password"]',
                'input[placeholder*="password" i]',
                '.login-form input[type="password"]',
                '#login-password',
                '.password-input'
            ],
            'login_button': [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                '.login-button',
                '#login-btn',
                '.btn-login',
                'button.btn-primary',
                '.submit-btn'
            ]
        }
        
        # Time Sync Warning modal selectors
        self.time_sync_selectors = {
            'modal': [
                '.time-sync-warning',
                '.modal:has-text("Time Sync")',
                '.alert:has-text("time")',
                '.warning:has-text("sync")',
                '[data-testid="time-sync-modal"]',
                '.modal-dialog:has-text("time")',
                '.popup:has-text("sync")'
            ],
            'close_button': [
                '.time-sync-warning .close',
                '.modal .btn-close',
                '.modal button:has-text("Close")',
                '.modal button:has-text("OK")',
                '.modal button:has-text("Continue")',
                '.alert .close',
                'button[aria-label="Close"]',
                '.modal-header .close'
            ]
        }
        
        # Dashboard confirmation selectors
        self.dashboard_selectors = [
            '.dashboard',
            '.trading-dashboard',
            '.main-dashboard',
            '#dashboard',
            '.user-dashboard',
            '.trading-interface',
            '.portfolio-view',
            '.account-overview',
            '[data-testid="dashboard"]',
            '.welcome-message'
        ]
        
    async def find_element_with_fallbacks(self, selectors: List[str], timeout: int = 5000) -> Optional[ElementHandle]:
        """Find element using fallback selectors.
        
        Args:
            selectors: List of CSS selectors to try
            timeout: Timeout in milliseconds for each selector
            
        Returns:
            ElementHandle if found, None otherwise
        """
        for selector in selectors:
            try:
                self.logger.debug(f"Trying selector: {selector}")
                element = await self.page.wait_for_selector(selector, timeout=timeout)
                if element:
                    self.logger.debug(f"Found element with selector: {selector}")
                    return element
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        self.logger.warning(f"No element found with any of the provided selectors")
        return None
    
    async def handle_time_sync_warning(self, max_retries: int = 3) -> bool:
        """Handle Time Sync Warning modal if it appears.
        
        Args:
            max_retries: Maximum number of retries to handle the modal
            
        Returns:
            True if modal was handled or not present, False if failed
        """
        self.logger.info("Checking for Time Sync Warning modal...")
        
        for attempt in range(max_retries):
            try:
                # Check if modal is present
                modal = await self.find_element_with_fallbacks(
                    self.time_sync_selectors['modal'], 
                    timeout=2000
                )
                
                if not modal:
                    self.logger.info("No Time Sync Warning modal detected")
                    return True
                
                self.logger.warning(f"Time Sync Warning modal detected (attempt {attempt + 1})")
                
                # Try to close the modal
                close_button = await self.find_element_with_fallbacks(
                    self.time_sync_selectors['close_button'],
                    timeout=3000
                )
                
                if close_button:
                    await close_button.click()
                    self.logger.info("Clicked Time Sync Warning close button")
                    
                    # Wait for modal to disappear
                    await asyncio.sleep(1)
                    
                    # Verify modal is gone
                    modal_check = await self.find_element_with_fallbacks(
                        self.time_sync_selectors['modal'],
                        timeout=1000
                    )
                    
                    if not modal_check:
                        self.logger.info("Time Sync Warning modal successfully closed")
                        return True
                else:
                    self.logger.warning("Could not find close button for Time Sync Warning modal")
                    # Try pressing Escape key as fallback
                    await self.page.keyboard.press('Escape')
                    await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error handling Time Sync Warning modal: {e}")
        
        self.logger.error("Failed to handle Time Sync Warning modal after all retries")
        return False
    
    async def perform_login(self, username: str, password: str, max_retries: int = 3) -> bool:
        """Perform login with robust element detection and error handling.
        
        Args:
            username: Bulenox username
            password: Bulenox password
            max_retries: Maximum number of login attempts
            
        Returns:
            True if login successful, False otherwise
        """
        self.logger.info("Starting login process...")
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Login attempt {attempt + 1}/{max_retries}")
                
                # Find username field
                username_field = await self.find_element_with_fallbacks(
                    self.login_selectors['username_field'],
                    timeout=10000
                )
                
                if not username_field:
                    self.logger.error("Could not find username field")
                    continue
                
                # Clear and fill username
                await username_field.clear()
                await username_field.fill(username)
                self.logger.info("Username entered successfully")
                
                # Find password field
                password_field = await self.find_element_with_fallbacks(
                    self.login_selectors['password_field'],
                    timeout=5000
                )
                
                if not password_field:
                    self.logger.error("Could not find password field")
                    continue
                
                # Clear and fill password
                await password_field.clear()
                await password_field.fill(password)
                self.logger.info("Password entered successfully")
                
                # Find and click login button
                login_button = await self.find_element_with_fallbacks(
                    self.login_selectors['login_button'],
                    timeout=5000
                )
                
                if not login_button:
                    self.logger.error("Could not find login button")
                    continue
                
                await login_button.click()
                self.logger.info("Login button clicked")
                
                # Wait for page to process login
                await asyncio.sleep(2)
                
                # Handle Time Sync Warning modal if it appears
                if not await self.handle_time_sync_warning():
                    self.logger.warning("Failed to handle Time Sync Warning modal, but continuing...")
                
                # Check for login success
                if await self.verify_login_success():
                    self.logger.info("Login successful!")
                    return True
                else:
                    self.logger.warning(f"Login attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Login attempt {attempt + 1} failed with error: {e}")
                await asyncio.sleep(2)
        
        self.logger.error("All login attempts failed")
        return False
    
    async def verify_login_success(self, timeout: int = 15000) -> bool:
        """Verify that login was successful by checking for dashboard elements.
        
        Args:
            timeout: Timeout in milliseconds to wait for dashboard
            
        Returns:
            True if login successful, False otherwise
        """
        self.logger.info("Verifying login success...")
        
        # Wait for any dashboard element to appear
        dashboard_element = await self.find_element_with_fallbacks(
            self.dashboard_selectors,
            timeout=timeout
        )
        
        if dashboard_element:
            self.logger.info("Dashboard detected - login successful")
            return True
        
        # Additional checks for login success
        try:
            # Check if we're still on login page (indicates failure)
            login_form = await self.find_element_with_fallbacks(
                self.login_selectors['username_field'],
                timeout=2000
            )
            
            if login_form:
                self.logger.warning("Still on login page - login may have failed")
                return False
            
            # Check for error messages
            error_selectors = [
                '.error-message',
                '.alert-danger',
                '.login-error',
                '.invalid-credentials',
                '[data-testid="error-message"]'
            ]
            
            error_element = await self.find_element_with_fallbacks(
                error_selectors,
                timeout=2000
            )
            
            if error_element:
                error_text = await error_element.text_content()
                self.logger.error(f"Login error detected: {error_text}")
                return False
            
        except Exception as e:
            self.logger.debug(f"Error during login verification: {e}")
        
        # If we can't find login form and no errors, assume success
        self.logger.info("Login appears successful (no login form detected)")
        return True
    
    async def wait_for_page_ready(self, timeout: int = 30000) -> bool:
        """Wait for the page to be fully loaded and ready.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            True if page is ready, False if timeout
        """
        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            
            # Wait for any loading indicators to disappear
            loading_selectors = [
                '.loading',
                '.spinner',
                '.loader',
                '[data-testid="loading"]',
                '.loading-overlay'
            ]
            
            for selector in loading_selectors:
                try:
                    await self.page.wait_for_selector(selector, state='hidden', timeout=5000)
                except:
                    pass  # Selector not found or already hidden
            
            self.logger.info("Page is ready")
            return True
            
        except Exception as e:
            self.logger.warning(f"Page ready check failed: {e}")
            return False

async def perform_bulenox_login(page: Page, username: str, password: str, logger: Optional[logging.Logger] = None) -> bool:
    """Convenience function to perform Bulenox login.
    
    Args:
        page: Playwright page instance
        username: Bulenox username
        password: Bulenox password
        logger: Optional logger instance
        
    Returns:
        True if login successful, False otherwise
    """
    login_automation = LoginAutomation(page, logger)
    return await login_automation.perform_login(username, password)

if __name__ == "__main__":
    # Test the login automation module
    import sys
    from pathlib import Path
    
    # Add parent directory to path for imports
    sys.path.append(str(Path(__file__).parent))
    
    from env_handler import get_environment
    
    async def test_login():
        """Test the login automation."""
        try:
            # Load environment variables
            env_vars = get_environment()
            
            print("Login automation module loaded successfully!")
            print("To test login, run the main tradebot_sentinel.py script.")
            
        except Exception as e:
            print(f"Error loading environment: {e}")
    
    asyncio.run(test_login())