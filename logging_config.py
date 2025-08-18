#!/usr/bin/env python3
"""
AI Trading Sentinel - Logging Configuration
Centralized logging setup for the trading bot.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime

def setup_logging(log_level="INFO", log_file=None, enable_console=True):
    """
    Set up logging configuration for the trading bot.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): Path to log file (optional)
        enable_console (bool): Enable console logging
    
    Returns:
        logging.Logger: Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set up log file path
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"trading_{timestamp}.log"
    
    # Configure logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("ai_trading_sentinel")
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name (str): Logger name (optional)
    
    Returns:
        logging.Logger: Logger instance
    """
    if name:
        return logging.getLogger(f"ai_trading_sentinel.{name}")
    return logging.getLogger("ai_trading_sentinel")

def log_trade_action(logger, action, symbol, quantity, price, timestamp=None):
    """
    Log a trading action with structured format.
    
    Args:
        logger: Logger instance
        action (str): Trading action (BUY, SELL, etc.)
        symbol (str): Trading symbol
        quantity (float): Trade quantity
        price (float): Trade price
        timestamp (datetime): Trade timestamp (optional)
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    logger.info(
        f"TRADE_ACTION | {action} | {symbol} | Qty: {quantity} | Price: {price} | Time: {timestamp}"
    )

def log_risk_event(logger, event_type, description, severity="WARNING"):
    """
    Log a risk management event.
    
    Args:
        logger: Logger instance
        event_type (str): Type of risk event
        description (str): Event description
        severity (str): Event severity level
    """
    log_method = getattr(logger, severity.lower(), logger.warning)
    log_method(f"RISK_EVENT | {event_type} | {description}")

def log_browser_action(logger, action, url=None, element=None, success=True):
    """
    Log a browser automation action.
    
    Args:
        logger: Logger instance
        action (str): Browser action performed
        url (str): Target URL (optional)
        element (str): Target element (optional)
        success (bool): Action success status
    """
    status = "SUCCESS" if success else "FAILED"
    details = []
    
    if url:
        details.append(f"URL: {url}")
    if element:
        details.append(f"Element: {element}")
    
    detail_str = " | ".join(details)
    if detail_str:
        detail_str = f" | {detail_str}"
    
    logger.info(f"BROWSER_ACTION | {action} | {status}{detail_str}")

# Initialize default logger
default_logger = None

def init_default_logger():
    """
    Initialize the default logger with environment settings.
    """
    global default_logger
    
    # Get settings from environment
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "logs/trading.log")
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    # Adjust log level for debug mode
    if debug_mode:
        log_level = "DEBUG"
    
    default_logger = setup_logging(
        log_level=log_level,
        log_file=log_file,
        enable_console=True
    )
    
    return default_logger

# Auto-initialize on import
if default_logger is None:
    try:
        default_logger = init_default_logger()
    except Exception as e:
        # Fallback to basic logging if initialization fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        default_logger = logging.getLogger("ai_trading_sentinel")
        default_logger.warning(f"Failed to initialize advanced logging: {e}")