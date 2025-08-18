#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bulenox AI Selenium Module

This module provides a simplified interface to the BulenoxAISeleniumAdaptiveUC class,
which implements AI-enhanced Selenium automation for the Bulenox trading platform.

This file serves as a compatibility layer, importing and re-exporting the functions
from bulenox_ai_selenium_adaptive_uc.py to maintain backward compatibility with
existing code that imports from bulenox_ai_selenium.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bulenox_ai_selenium")

# Import the functions from the adaptive UC version
from bulenox_ai_selenium_adaptive_uc import (
    login_bulenox_ai,
    place_bulenox_trade,
    BulenoxAISeleniumAdaptiveUC
)

# Log that this compatibility module was loaded
logger.info("Loaded bulenox_ai_selenium compatibility module (using adaptive UC implementation)")

# Re-export the functions and class
__all__ = ["login_bulenox_ai", "place_bulenox_trade", "BulenoxAISeleniumAdaptiveUC"]