#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Error Handler and Logger for TradeBot Sentinel

This module provides robust error handling, logging, and screenshot capture
capabilities for the TradeBot Sentinel automation system.

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Union
import json
import os
from functools import wraps
from playwright.async_api import Page, Browser, BrowserContext
import time

class TradeBotLogger:
    """Enhanced logger for TradeBot Sentinel with multiple output formats."""
    
    def __init__(self, name: str = "TradeBot-Sentinel", log_level: str = "INFO"):
        """Initialize the logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger = self._setup_logger()
        self.session_id = self._generate_session_id()
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{int(time.time())}_{os.getpid()}"
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with multiple handlers."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(ColoredFormatter(simple_formatter))
        logger.addHandler(console_handler)
        
        # File handler for detailed logs
        log_file = self.logs_dir / f"tradebot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Error file handler
        error_file = self.logs_dir / f"tradebot_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self.logger
    
    def log_session_start(self, config: Dict[str, Any] = None) -> None:
        """Log session start with configuration."""
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 TradeBot Sentinel Session Started - ID: {self.session_id}")
        self.logger.info("=" * 80)
        
        if config:
            self.logger.info("Configuration:")
            for key, value in config.items():
                # Hide sensitive information
                if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                    value = "***HIDDEN***"
                self.logger.info(f"  {key}: {value}")
    
    def log_session_end(self, success: bool = True, summary: Dict[str, Any] = None) -> None:
        """Log session end with summary."""
        self.logger.info("=" * 80)
        status = "✅ COMPLETED SUCCESSFULLY" if success else "❌ COMPLETED WITH ERRORS"
        self.logger.info(f"🏁 TradeBot Sentinel Session Ended - {status}")
        
        if summary:
            self.logger.info("Session Summary:")
            for key, value in summary.items():
                self.logger.info(f"  {key}: {value}")
        
        self.logger.info(f"Session ID: {self.session_id}")
        self.logger.info("=" * 80)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, base_formatter: logging.Formatter):
        super().__init__()
        self.base_formatter = base_formatter
    
    def format(self, record: logging.LogRecord) -> str:
        log_message = self.base_formatter.format(record)
        color = self.COLORS.get(record.levelname, '')
        return f"{color}{log_message}{self.RESET}"

class ScreenshotManager:
    """Manages screenshot capture for debugging and error reporting."""
    
    def __init__(self, logger: logging.Logger, screenshots_dir: str = "screenshots"):
        """Initialize screenshot manager.
        
        Args:
            logger: Logger instance
            screenshots_dir: Directory to save screenshots
        """
        self.logger = logger
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.session_dir = self.screenshots_dir / f"session_{int(time.time())}"
        self.session_dir.mkdir(exist_ok=True)
    
    async def capture_screenshot(self, page: Page, name: str, 
                               context: str = "") -> Optional[str]:
        """Capture a screenshot with descriptive naming.
        
        Args:
            page: Playwright page instance
            name: Screenshot name/identifier
            context: Additional context for the screenshot
            
        Returns:
            Path to saved screenshot or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{name}.png"
            if context:
                filename = f"{timestamp}_{context}_{name}.png"
            
            screenshot_path = self.session_dir / filename
            
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            self.logger.info(f"📸 Screenshot captured: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot '{name}': {e}")
            return None
    
    async def capture_error_screenshot(self, page: Page, error: Exception, 
                                     context: str = "") -> Optional[str]:
        """Capture screenshot when an error occurs.
        
        Args:
            page: Playwright page instance
            error: The exception that occurred
            context: Additional context
            
        Returns:
            Path to saved screenshot or None if failed
        """
        error_name = type(error).__name__
        screenshot_name = f"error_{error_name}"
        
        if context:
            screenshot_name = f"error_{context}_{error_name}"
        
        return await self.capture_screenshot(page, screenshot_name, "ERROR")
    
    async def capture_debug_screenshot(self, page: Page, step: str) -> Optional[str]:
        """Capture screenshot for debugging purposes.
        
        Args:
            page: Playwright page instance
            step: Current step/operation
            
        Returns:
            Path to saved screenshot or None if failed
        """
        return await self.capture_screenshot(page, step, "DEBUG")
    
    def get_session_screenshots(self) -> list:
        """Get list of all screenshots from current session.
        
        Returns:
            List of screenshot file paths
        """
        try:
            return [str(f) for f in self.session_dir.glob("*.png")]
        except Exception as e:
            self.logger.error(f"Error getting session screenshots: {e}")
            return []

class ErrorHandler:
    """Comprehensive error handler with retry logic and recovery strategies."""
    
    def __init__(self, logger: logging.Logger, screenshot_manager: ScreenshotManager):
        """Initialize error handler.
        
        Args:
            logger: Logger instance
            screenshot_manager: Screenshot manager instance
        """
        self.logger = logger
        self.screenshot_manager = screenshot_manager
        self.error_counts = {}
        self.max_retries = 3
        self.retry_delay = 2
    
    async def handle_error(self, error: Exception, page: Optional[Page] = None, 
                          context: str = "", critical: bool = False) -> bool:
        """Handle an error with logging, screenshots, and recovery attempts.
        
        Args:
            error: The exception that occurred
            page: Optional Playwright page for screenshots
            context: Context where the error occurred
            critical: Whether this is a critical error
            
        Returns:
            True if error was handled/recovered, False if critical
        """
        error_type = type(error).__name__
        error_key = f"{context}_{error_type}" if context else error_type
        
        # Track error frequency
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log the error
        log_level = logging.CRITICAL if critical else logging.ERROR
        self.logger.log(log_level, f"❌ Error in {context}: {error_type} - {str(error)}")
        self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        
        # Capture screenshot if page is available
        if page:
            try:
                await self.screenshot_manager.capture_error_screenshot(page, error, context)
            except Exception as screenshot_error:
                self.logger.warning(f"Failed to capture error screenshot: {screenshot_error}")
        
        # Check if we should attempt recovery
        if critical or self.error_counts[error_key] > self.max_retries:
            self.logger.critical(f"Critical error or max retries exceeded for {error_key}")
            return False
        
        # Attempt recovery based on error type
        recovery_success = await self._attempt_recovery(error, page, context)
        
        if recovery_success:
            self.logger.info(f"✅ Recovered from error: {error_key}")
        else:
            self.logger.warning(f"⚠️ Failed to recover from error: {error_key}")
        
        return recovery_success
    
    async def _attempt_recovery(self, error: Exception, page: Optional[Page], 
                              context: str) -> bool:
        """Attempt to recover from specific error types.
        
        Args:
            error: The exception that occurred
            page: Optional Playwright page
            context: Error context
            
        Returns:
            True if recovery was successful
        """
        error_type = type(error).__name__
        
        try:
            if "TimeoutError" in error_type and page:
                self.logger.info("Attempting recovery from timeout error...")
                await asyncio.sleep(self.retry_delay)
                
                # Try to refresh the page
                await page.reload(wait_until='networkidle')
                await asyncio.sleep(2)
                return True
            
            elif "ElementNotFound" in error_type or "NoSuchElement" in error_type:
                self.logger.info("Attempting recovery from element not found error...")
                await asyncio.sleep(self.retry_delay)
                return True
            
            elif "NetworkError" in error_type or "ConnectionError" in error_type:
                self.logger.info("Attempting recovery from network error...")
                await asyncio.sleep(self.retry_delay * 2)  # Longer delay for network issues
                return True
            
            else:
                # Generic recovery - just wait and retry
                self.logger.info(f"Attempting generic recovery for {error_type}...")
                await asyncio.sleep(self.retry_delay)
                return True
        
        except Exception as recovery_error:
            self.logger.error(f"Recovery attempt failed: {recovery_error}")
            return False
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered.
        
        Returns:
            Dictionary with error statistics
        """
        total_errors = sum(self.error_counts.values())
        return {
            'total_errors': total_errors,
            'unique_errors': len(self.error_counts),
            'error_breakdown': self.error_counts.copy(),
            'most_common_error': max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }

def async_error_handler(logger: logging.Logger, screenshot_manager: ScreenshotManager = None,
                       max_retries: int = 3, retry_delay: float = 2.0):
    """Decorator for async functions to add comprehensive error handling.
    
    Args:
        logger: Logger instance
        screenshot_manager: Optional screenshot manager
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_error = e
                    func_name = func.__name__
                    
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed for {func_name}: {e}")
                        
                        # Capture screenshot if page is available in args
                        if screenshot_manager:
                            for arg in args:
                                if hasattr(arg, 'screenshot'):  # Likely a Page object
                                    try:
                                        await screenshot_manager.capture_error_screenshot(
                                            arg, e, f"{func_name}_retry_{attempt + 1}"
                                        )
                                        break
                                    except:
                                        pass
                        
                        await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(f"All attempts failed for {func_name}: {e}")
                        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            
            raise last_error
        
        return wrapper
    return decorator

def create_error_handling_system(log_level: str = "INFO") -> tuple:
    """Create a complete error handling system.
    
    Args:
        log_level: Logging level
        
    Returns:
        Tuple of (logger_instance, screenshot_manager, error_handler)
    """
    # Create logger
    tradebot_logger = TradeBotLogger(log_level=log_level)
    logger = tradebot_logger.get_logger()
    
    # Create screenshot manager
    screenshot_manager = ScreenshotManager(logger)
    
    # Create error handler
    error_handler = ErrorHandler(logger, screenshot_manager)
    
    return tradebot_logger, screenshot_manager, error_handler

async def safe_page_operation(page: Page, operation: Callable, 
                            error_handler: ErrorHandler, 
                            context: str = "", 
                            critical: bool = False) -> Any:
    """Safely execute a page operation with error handling.
    
    Args:
        page: Playwright page instance
        operation: Async operation to execute
        error_handler: Error handler instance
        context: Operation context
        critical: Whether failure is critical
        
    Returns:
        Operation result or None if failed
    """
    try:
        return await operation()
    except Exception as e:
        handled = await error_handler.handle_error(e, page, context, critical)
        if not handled:
            raise
        return None

if __name__ == "__main__":
    # Test the error handling system
    async def test_error_handling():
        logger_sys, screenshot_mgr, error_hdlr = create_error_handling_system("DEBUG")
        logger = logger_sys.get_logger()
        
        logger.info("Error handling system test started")
        
        # Test error handling
        try:
            raise ValueError("Test error")
        except Exception as e:
            await error_hdlr.handle_error(e, context="test_context")
        
        # Print error summary
        summary = error_hdlr.get_error_summary()
        logger.info(f"Error summary: {summary}")
        
        logger.info("Error handling system test completed")
    
    print("Error Handler module loaded successfully!")
    print("Running test...")
    asyncio.run(test_error_handling())