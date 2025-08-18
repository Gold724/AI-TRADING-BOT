#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Automation Module for TradeBot Sentinel

This module provides robust trading automation for the Bulenox trading platform
with navigation, order placement, and multiple selector strategies.

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from playwright.async_api import Page, ElementHandle
import json
import time

class TradingAutomation:
    """Handles robust trading automation for Bulenox trading platform."""
    
    def __init__(self, page: Page, logger: Optional[logging.Logger] = None):
        """Initialize the trading automation.
        
        Args:
            page: Playwright page instance
            logger: Optional logger instance
        """
        self.page = page
        self.logger = logger or logging.getLogger(__name__)
        
        # Trading page navigation selectors
        self.navigation_selectors = {
            'trading_menu': [
                'a[href*="trading"]',
                'a[href*="trade"]',
                '.nav-link:has-text("Trading")',
                '.menu-item:has-text("Trade")',
                '#trading-menu',
                '.trading-nav',
                'button:has-text("Trading")',
                '[data-testid="trading-link"]'
            ],
            'trading_page_indicators': [
                '.trading-interface',
                '.trading-dashboard',
                '.order-form',
                '.trading-panel',
                '#trading-page',
                '.trade-container',
                '[data-testid="trading-interface"]',
                '.market-data'
            ]
        }
        
        # Order form selectors with multiple fallback strategies
        self.order_selectors = {
            'order_tab': [
                '.tab:has-text("ORDER")',
                '.order-tab',
                '#order-tab',
                'button:has-text("ORDER")',
                '.nav-tab:has-text("Order")',
                '[data-tab="order"]',
                '.trading-tab:has-text("ORDER")'
            ],
            'dom_tab': [
                '.tab:has-text("DOM")',
                '.dom-tab',
                '#dom-tab',
                'button:has-text("DOM")',
                '.nav-tab:has-text("DOM")',
                '[data-tab="dom"]',
                '.trading-tab:has-text("DOM")'
            ],
            'symbol_field': [
                'input[name="symbol"]',
                'input[placeholder*="symbol" i]',
                '.symbol-input',
                '#symbol',
                'input[data-field="symbol"]',
                '.instrument-selector input',
                '.trading-symbol input'
            ],
            'amount_field': [
                'input[name="amount"]',
                'input[name="quantity"]',
                'input[name="size"]',
                'input[placeholder*="amount" i]',
                'input[placeholder*="quantity" i]',
                '.amount-input',
                '.quantity-input',
                '#amount',
                '#quantity',
                'input[data-field="amount"]'
            ],
            'price_field': [
                'input[name="price"]',
                'input[placeholder*="price" i]',
                '.price-input',
                '#price',
                'input[data-field="price"]',
                '.limit-price input'
            ],
            'order_type': [
                'select[name="orderType"]',
                'select[name="type"]',
                '.order-type-select',
                '#order-type',
                'select[data-field="orderType"]',
                '.order-type dropdown'
            ],
            'side_buy': [
                'button:has-text("BUY")',
                'button:has-text("Buy")',
                '.buy-button',
                '.btn-buy',
                '#buy-btn',
                'input[value="buy"]',
                '[data-side="buy"]'
            ],
            'side_sell': [
                'button:has-text("SELL")',
                'button:has-text("Sell")',
                '.sell-button',
                '.btn-sell',
                '#sell-btn',
                'input[value="sell"]',
                '[data-side="sell"]'
            ],
            'submit_order': [
                'button[type="submit"]',
                'button:has-text("Place Order")',
                'button:has-text("Submit")',
                'button:has-text("Execute")',
                '.submit-order',
                '.place-order-btn',
                '#submit-order',
                '.order-submit'
            ]
        }
        
        # Generic fallback selectors for any trading interface
        self.generic_selectors = {
            'input_fields': [
                'input[type="text"]',
                'input[type="number"]',
                '.form-control',
                '.input-field'
            ],
            'buttons': [
                'button',
                '.btn',
                'input[type="button"]',
                'input[type="submit"]'
            ],
            'dropdowns': [
                'select',
                '.dropdown',
                '.select-field'
            ]
        }
    
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
    
    async def navigate_to_trading_page(self, max_retries: int = 3) -> bool:
        """Navigate to the trading page.
        
        Args:
            max_retries: Maximum number of navigation attempts
            
        Returns:
            True if navigation successful, False otherwise
        """
        self.logger.info("Navigating to trading page...")
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Navigation attempt {attempt + 1}/{max_retries}")
                
                # Check if already on trading page
                if await self.verify_trading_page():
                    self.logger.info("Already on trading page")
                    return True
                
                # Find and click trading menu/link
                trading_link = await self.find_element_with_fallbacks(
                    self.navigation_selectors['trading_menu'],
                    timeout=10000
                )
                
                if trading_link:
                    await trading_link.click()
                    self.logger.info("Clicked trading navigation link")
                    
                    # Wait for page to load
                    await asyncio.sleep(2)
                    
                    # Verify we're on trading page
                    if await self.verify_trading_page():
                        self.logger.info("Successfully navigated to trading page")
                        return True
                else:
                    self.logger.warning("Could not find trading navigation link")
                    # Try direct URL navigation as fallback
                    current_url = self.page.url
                    base_url = '/'.join(current_url.split('/')[:3])
                    trading_urls = [
                        f"{base_url}/trading",
                        f"{base_url}/trade",
                        f"{base_url}/platform",
                        f"{base_url}/dashboard/trading"
                    ]
                    
                    for url in trading_urls:
                        try:
                            await self.page.goto(url)
                            await asyncio.sleep(2)
                            if await self.verify_trading_page():
                                self.logger.info(f"Successfully navigated to trading page via URL: {url}")
                                return True
                        except Exception as e:
                            self.logger.debug(f"Failed to navigate to {url}: {e}")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Navigation attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2)
        
        self.logger.error("Failed to navigate to trading page after all attempts")
        return False
    
    async def verify_trading_page(self, timeout: int = 10000) -> bool:
        """Verify that we're on the trading page.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            True if on trading page, False otherwise
        """
        trading_element = await self.find_element_with_fallbacks(
            self.navigation_selectors['trading_page_indicators'],
            timeout=timeout
        )
        
        if trading_element:
            self.logger.info("Trading page confirmed")
            return True
        
        self.logger.warning("Trading page not detected")
        return False
    
    async def place_order(self, symbol: str, amount: float, price: Optional[float] = None, 
                         side: str = "buy", order_type: str = "market", max_retries: int = 3) -> bool:
        """Place a trading order with robust element detection.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSD")
            amount: Order amount/quantity
            price: Order price (for limit orders)
            side: Order side ("buy" or "sell")
            order_type: Order type ("market" or "limit")
            max_retries: Maximum number of order placement attempts
            
        Returns:
            True if order placed successfully, False otherwise
        """
        self.logger.info(f"Placing {side.upper()} order: {amount} {symbol} @ {price or 'market'}")
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Order placement attempt {attempt + 1}/{max_retries}")
                
                # Step 1: Try to access ORDER tab first
                if not await self.select_order_tab():
                    # Fallback to DOM tab
                    if not await self.select_dom_tab():
                        # Use generic approach
                        self.logger.warning("Could not find ORDER or DOM tab, using generic approach")
                
                # Step 2: Fill order details
                if await self.fill_order_form(symbol, amount, price, side, order_type):
                    # Step 3: Submit order
                    if await self.submit_order():
                        self.logger.info("Order placed successfully!")
                        return True
                    else:
                        self.logger.warning("Failed to submit order")
                else:
                    self.logger.warning("Failed to fill order form")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Order placement attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2)
        
        self.logger.error("Failed to place order after all attempts")
        return False
    
    async def select_order_tab(self) -> bool:
        """Select the ORDER tab.
        
        Returns:
            True if ORDER tab selected, False otherwise
        """
        self.logger.info("Selecting ORDER tab...")
        
        order_tab = await self.find_element_with_fallbacks(
            self.order_selectors['order_tab'],
            timeout=5000
        )
        
        if order_tab:
            await order_tab.click()
            self.logger.info("ORDER tab selected")
            await asyncio.sleep(1)
            return True
        
        self.logger.warning("Could not find ORDER tab")
        return False
    
    async def select_dom_tab(self) -> bool:
        """Select the DOM tab as fallback.
        
        Returns:
            True if DOM tab selected, False otherwise
        """
        self.logger.info("Selecting DOM tab as fallback...")
        
        dom_tab = await self.find_element_with_fallbacks(
            self.order_selectors['dom_tab'],
            timeout=5000
        )
        
        if dom_tab:
            await dom_tab.click()
            self.logger.info("DOM tab selected")
            await asyncio.sleep(1)
            return True
        
        self.logger.warning("Could not find DOM tab")
        return False
    
    async def fill_order_form(self, symbol: str, amount: float, price: Optional[float], 
                             side: str, order_type: str) -> bool:
        """Fill the order form with the provided details.
        
        Args:
            symbol: Trading symbol
            amount: Order amount
            price: Order price (optional)
            side: Order side
            order_type: Order type
            
        Returns:
            True if form filled successfully, False otherwise
        """
        self.logger.info("Filling order form...")
        
        try:
            # Fill symbol
            symbol_field = await self.find_element_with_fallbacks(
                self.order_selectors['symbol_field'],
                timeout=5000
            )
            
            if symbol_field:
                await symbol_field.clear()
                await symbol_field.fill(symbol)
                self.logger.info(f"Symbol filled: {symbol}")
            else:
                self.logger.warning("Could not find symbol field")
            
            # Fill amount
            amount_field = await self.find_element_with_fallbacks(
                self.order_selectors['amount_field'],
                timeout=5000
            )
            
            if amount_field:
                await amount_field.clear()
                await amount_field.fill(str(amount))
                self.logger.info(f"Amount filled: {amount}")
            else:
                self.logger.warning("Could not find amount field")
            
            # Fill price (for limit orders)
            if price and order_type.lower() == "limit":
                price_field = await self.find_element_with_fallbacks(
                    self.order_selectors['price_field'],
                    timeout=5000
                )
                
                if price_field:
                    await price_field.clear()
                    await price_field.fill(str(price))
                    self.logger.info(f"Price filled: {price}")
                else:
                    self.logger.warning("Could not find price field")
            
            # Select order type
            order_type_select = await self.find_element_with_fallbacks(
                self.order_selectors['order_type'],
                timeout=3000
            )
            
            if order_type_select:
                await order_type_select.select_option(order_type)
                self.logger.info(f"Order type selected: {order_type}")
            
            # Select side (buy/sell)
            side_selectors = self.order_selectors['side_buy'] if side.lower() == 'buy' else self.order_selectors['side_sell']
            side_button = await self.find_element_with_fallbacks(side_selectors, timeout=3000)
            
            if side_button:
                await side_button.click()
                self.logger.info(f"Side selected: {side.upper()}")
            else:
                self.logger.warning(f"Could not find {side.upper()} button")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error filling order form: {e}")
            return False
    
    async def submit_order(self) -> bool:
        """Submit the order.
        
        Returns:
            True if order submitted successfully, False otherwise
        """
        self.logger.info("Submitting order...")
        
        try:
            submit_button = await self.find_element_with_fallbacks(
                self.order_selectors['submit_order'],
                timeout=5000
            )
            
            if submit_button:
                await submit_button.click()
                self.logger.info("Order submit button clicked")
                
                # Wait for order processing
                await asyncio.sleep(2)
                
                # Check for confirmation or error messages
                await self.check_order_status()
                
                return True
            else:
                self.logger.error("Could not find order submit button")
                return False
                
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            return False
    
    async def check_order_status(self) -> None:
        """Check for order confirmation or error messages."""
        try:
            # Check for success messages
            success_selectors = [
                '.success-message',
                '.order-success',
                '.alert-success',
                '.confirmation-message',
                '[data-testid="order-success"]'
            ]
            
            success_element = await self.find_element_with_fallbacks(
                success_selectors,
                timeout=3000
            )
            
            if success_element:
                success_text = await success_element.text_content()
                self.logger.info(f"Order success: {success_text}")
                return
            
            # Check for error messages
            error_selectors = [
                '.error-message',
                '.order-error',
                '.alert-danger',
                '.alert-error',
                '[data-testid="order-error"]'
            ]
            
            error_element = await self.find_element_with_fallbacks(
                error_selectors,
                timeout=3000
            )
            
            if error_element:
                error_text = await error_element.text_content()
                self.logger.error(f"Order error: {error_text}")
            
        except Exception as e:
            self.logger.debug(f"Error checking order status: {e}")
    
    async def capture_trading_interface_screenshot(self, filename: str = None) -> str:
        """Capture screenshot of the trading interface for debugging.
        
        Args:
            filename: Optional filename for the screenshot
            
        Returns:
            Path to the saved screenshot
        """
        if not filename:
            timestamp = int(time.time())
            filename = f"trading_interface_{timestamp}.png"
        
        try:
            await self.page.screenshot(path=filename, full_page=True)
            self.logger.info(f"Trading interface screenshot saved: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return ""

async def navigate_and_trade(page: Page, symbol: str, amount: float, price: Optional[float] = None,
                           side: str = "buy", order_type: str = "market", 
                           logger: Optional[logging.Logger] = None) -> bool:
    """Convenience function to navigate to trading page and place an order.
    
    Args:
        page: Playwright page instance
        symbol: Trading symbol
        amount: Order amount
        price: Order price (optional)
        side: Order side
        order_type: Order type
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    trading_automation = TradingAutomation(page, logger)
    
    # Navigate to trading page
    if not await trading_automation.navigate_to_trading_page():
        return False
    
    # Place order
    return await trading_automation.place_order(symbol, amount, price, side, order_type)

if __name__ == "__main__":
    # Test the trading automation module
    print("Trading automation module loaded successfully!")
    print("To test trading, run the main tradebot_sentinel.py script.")