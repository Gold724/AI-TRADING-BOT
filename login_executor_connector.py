#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bulenox Login and Executor Connector

This module connects the AI-enhanced login functionality with the trade executor
for seamless login and trade execution on the Bulenox platform.

Features:
- Stealth login using undetected-chromedriver
- Profile 13-15 switching
- Retry logic and fallback XPath
- Strategic screenshots and logging
- Dashboard heartbeat integration
"""

import json
import logging
import os
import random
import time
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver

from ai_login_bulenox import ai_login_bulenox
from executor_bulenox import BulenoxExecutor, execute_trade

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("login_executor_connector")

# Load environment variables
load_dotenv()

# Heartbeat status file
HEARTBEAT_STATUS_FILE = os.path.join("logs", "heartbeat_status.txt")


def update_heartbeat_status(status, session_active=True):
    """
    Update the heartbeat status file with current status and timestamp

    Args:
        status (str): The current status message
        session_active (bool): Flag indicating if a trading session is active
    """
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        timestamp = datetime.now().isoformat()

        # Write to heartbeat status file
        with open(HEARTBEAT_STATUS_FILE, "w") as f:
            f.write(
                f"{status}\n{timestamp}\n{json.dumps({'session_active': session_active})}"
            )
            
        # Also update dashboard heartbeat file
        dashboard_heartbeat = os.path.join("logs", "dashboard_heartbeat.json")
        heartbeat_data = {
            "status": "online" if session_active else "offline",
            "timestamp": timestamp,
            "message": status,
            "session_id": datetime.now().strftime("%Y%m%d-%H%M%S")
        }
        
        with open(dashboard_heartbeat, "w") as f:
            json.dump(heartbeat_data, f, indent=2)

        logger.info(f"Updated heartbeat status: {status}")
    except Exception as e:
        logger.error(f"Error updating heartbeat status: {e}")


class BulenoxConnector:
    """
    Connector class that integrates login functionality with trade execution
    for the Bulenox trading platform.
    """

    def __init__(self, debug=False, profile_index=13):
        """
        Initialize the BulenoxConnector

        Args:
            debug (bool): Enable debug mode with additional logging and screenshots
            profile_index (int): Chrome profile index to use (13-15 recommended)
        """
        self.debug = debug
        self.profile_index = profile_index
        self.driver = None
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.executor = None
        
        # Create logs directory
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        self.screenshots_dir = os.path.join(self.logs_dir, "screenshots")
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Set environment variable for profile
        os.environ["BULENOX_PROFILE_NAME"] = f"Profile {profile_index}"
        
        # Dashboard heartbeat file
        self.dashboard_heartbeat = os.path.join(self.logs_dir, "dashboard_heartbeat.json")

    def login(self, max_retries=3):
        """
        Login to Bulenox using AI-powered stealth login with retry logic.
        
        Args:
            max_retries (int): Maximum number of login attempts
            
        Returns:
            bool: True if login successful, False otherwise
        """
        # Try different profiles if initial login fails
        profiles_to_try = [self.profile_index]
        
        # Add fallback profiles if not already included
        for profile in [13, 14, 15]:
            if profile != self.profile_index and len(profiles_to_try) < max_retries:
                profiles_to_try.append(profile)
        
        # Ensure we don't try more profiles than max_retries
        profiles_to_try = profiles_to_try[:max_retries]
        
        for attempt, profile in enumerate(profiles_to_try, 1):
            try:
                logger.info(f"Login attempt {attempt}/{max_retries} with Profile {profile}")
                update_heartbeat_status(f"🔄 Login attempt {attempt}/{max_retries} with Profile {profile}...")
                self._update_dashboard_heartbeat("connecting", f"Login attempt {attempt}/{max_retries} with Profile {profile}")
                
                # Set current profile for this attempt
                current_profile = profile
                os.environ["BULENOX_PROFILE_NAME"] = f"Profile {current_profile}"
                
                # Attempt login with AI-powered approach
                self.driver = ai_login_bulenox(debug=self.debug, profile_index=current_profile)
                
                if self.driver:
                    # Update heartbeat status
                    update_heartbeat_status("✅ ONLINE - AI Login Successful", session_active=True)
                    
                    # Update dashboard heartbeat
                    self._update_dashboard_heartbeat("online", f"Login successful with Profile {current_profile}")
                    
                    # Initialize executor
                    self.executor = BulenoxExecutor({"symbol": ""}, self.session_id)
                    
                    # Update profile index to the successful one
                    self.profile_index = current_profile
                    
                    logger.info(f"Successfully logged in to Bulenox using Profile {current_profile}")
                    return True
                
                logger.warning(f"Login attempt {attempt} with Profile {profile} failed")
                
                # Wait before retry with increasing backoff
                if attempt < len(profiles_to_try):
                    backoff_time = 5 * attempt
                    logger.info(f"Waiting {backoff_time} seconds before next attempt")
                    time.sleep(backoff_time)
                    
            except Exception as e:
                logger.error(f"Error during login attempt {attempt} with Profile {profile}: {e}")
                
                # Wait before retry with increasing backoff
                if attempt < len(profiles_to_try):
                    backoff_time = 5 * attempt
                    logger.info(f"Waiting {backoff_time} seconds before next attempt")
                    time.sleep(backoff_time)
        
        # If we get here, all login attempts failed
        update_heartbeat_status("❌ OFFLINE - All login attempts failed", session_active=False)
        self._update_dashboard_heartbeat("offline", f"Failed after {max_retries} attempts with different profiles")
        logger.error(f"Failed to login to Bulenox after {max_retries} attempts with different profiles")
        return False
    
    def execute_trade(self, signal):
        """
        Execute a trade on Bulenox platform
        
        Args:
            signal (dict): Trading signal with symbol, direction, quantity, etc.
                - symbol (str): Trading symbol
                - direction (str): Trade direction ('buy' or 'sell')
                - quantity (float): Trade quantity
                - tp (float, optional): Take profit level
                - sl (float, optional): Stop loss level
            
        Returns:
            dict: Trade execution result or None if login not successful
        """
        if not self.driver:
            logger.error("Cannot execute trade: Not logged in")
            update_heartbeat_status("❌ Cannot execute trade: Not logged in", session_active=False)
            self._update_dashboard_heartbeat("offline", "Not logged in")
            return {"success": False, "error": "Not logged in"}
        
        try:
            # Extract signal parameters
            symbol = signal.get('symbol')
            direction = signal.get('direction', 'buy')
            quantity = signal.get('quantity', 0.01)
            take_profit = signal.get('tp')
            stop_loss = signal.get('sl')
            
            logger.info(f"Executing trade: {symbol} {direction} {quantity}")
            update_heartbeat_status(f"🔄 Executing {direction.upper()} trade for {symbol}", session_active=True)
            self._update_dashboard_heartbeat("trading", f"Executing {direction.upper()} {symbol} {quantity}")
            
            # Take screenshot before trade execution
            screenshot_path = os.path.join(self.screenshots_dir, f"pre_trade_{self.session_id}_{int(time.time())}.png")
            try:
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Pre-trade screenshot saved: {screenshot_path}")
            except Exception as ss_err:
                logger.warning(f"Failed to save pre-trade screenshot: {ss_err}")
            
            # Execute the trade using BulenoxExecutor
            if not self.executor:
                self.executor = BulenoxExecutor(self.driver)
                
            result = self.executor.execute_trade(
                symbol=symbol,
                direction=direction,
                quantity=quantity,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            
            # Take screenshot after trade execution
            screenshot_path = os.path.join(self.screenshots_dir, f"post_trade_{self.session_id}_{int(time.time())}.png")
            try:
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Post-trade screenshot saved: {screenshot_path}")
            except Exception as ss_err:
                logger.warning(f"Failed to save post-trade screenshot: {ss_err}")
            
            # Update dashboard heartbeat with trade result
            if result.get("success", False):
                update_heartbeat_status(f"✅ {direction.upper()} trade executed for {symbol}", session_active=True)
                self._update_dashboard_heartbeat("online", f"Trade executed: {direction.upper()} {symbol} {quantity}")
            else:
                update_heartbeat_status(f"❌ Failed to execute {direction.upper()} trade for {symbol}", session_active=True)
                self._update_dashboard_heartbeat("warning", f"Trade failed: {direction.upper()} {symbol} {quantity}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            update_heartbeat_status(f"❌ Error executing trade: {str(e)[:50]}...", session_active=True)
            self._update_dashboard_heartbeat("error", f"Trade error: {str(e)[:50]}...")
            return {"success": False, "error": str(e)}
    
    def logout(self):
        """
        Logout from Bulenox and close the browser
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        if not self.driver:
            logger.warning("Cannot logout: Not logged in")
            return False
        
        try:
            logger.info("Logging out from Bulenox")
            update_heartbeat_status("🔄 Logging out from Bulenox...", session_active=False)
            
            # Navigate to logout page or click logout button
            try:
                # Try to find and click logout button
                self.driver.find_element_by_xpath("//button[contains(text(), 'Logout')]").click()
                time.sleep(2)  # Wait for logout to complete
            except:
                # If logout button not found, just close the browser
                pass
            
            # Close the browser
            self.driver.quit()
            self.driver = None
            
            logger.info("Successfully logged out from Bulenox")
            update_heartbeat_status("✅ OFFLINE - Logged out", session_active=False)
            self._update_dashboard_heartbeat("offline", "Logged out")
            return True
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            update_heartbeat_status(f"⚠️ Error during logout: {str(e)[:50]}...", session_active=False)
            self._update_dashboard_heartbeat("error", f"Logout error: {str(e)[:50]}...")
            
            # Force close the browser
            try:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
            except:
                pass
                
            return False
    
    def _update_dashboard_heartbeat(self, status, message):
        """
        Update the dashboard heartbeat file with current status
        
        Args:
            status (str): Status code (online, offline, error, warning, trading)
            message (str): Status message
        """
        try:
            timestamp = datetime.now().isoformat()
            
            heartbeat_data = {
                "timestamp": timestamp,
                "status": status,
                "message": message,
                "session_id": self.session_id,
                "profile": f"Profile {self.profile_index}"
            }
            
            with open(self.dashboard_heartbeat, "w") as f:
                json.dump(heartbeat_data, f, indent=2)
                
            logger.info(f"Updated dashboard heartbeat: {status} - {message}")
        except Exception as e:
            logger.error(f"Error updating dashboard heartbeat: {e}")


# Example usage
if __name__ == "__main__":
    # Create connector
    connector = BulenoxConnector(debug=True, profile_index=13)
    
    # Login
    login_success = connector.login()
    
    if login_success:
        # Example trade signal
        signal = {
            "symbol": "EURUSD",
            "direction": "buy",
            "quantity": 0.01,
            "tp": 1.0800,
            "sl": 1.0700,
        }
        
        # Execute trade
        result = connector.execute_trade(signal)
        print(f"Trade execution result: {result}")
        
        # Logout
        connector.logout()
    else:
        print("Login failed. Cannot execute trade.")