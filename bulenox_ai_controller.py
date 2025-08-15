#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

# Import Bulenox AI Selenium module
from bulenox_ai_selenium import login_bulenox_ai, place_bulenox_trade

# Import Dreamer Mode for simulation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from liveops.dreamer_mode import DreamerMode

# Create logs directory
os.makedirs(os.path.join('logs', 'bulenox'), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'bulenox', 'controller.log'), mode='a')
    ]
)

logger = logging.getLogger("trae.bulenox.controller")

class BulenoxAIController:
    """Controller for Bulenox AI Selenium trading.
    
    This class integrates the Bulenox AI Selenium module with the TRAE AI system,
    supporting both Dreamer Mode (simulated trades) and Real Mode (live execution).
    """
    
    def __init__(self, config_path: str = "config/bulenox_controller_config.json"):
        """Initialize the Bulenox AI Controller.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize Dreamer Mode if enabled
        self.dreamer_mode = None
        if self.config.get("dreamer_mode", {}).get("enabled", False):
            logger.info("Initializing Dreamer Mode for simulated trades")
            self.dreamer_mode = DreamerMode(self.config.get("dreamer_mode", {}))
        
        # Initialize session state
        self.session_active = False
        self.bulenox_instance = None
        self.last_activity = datetime.now()
        
        # Create trade log file
        self.trade_log_path = os.path.join('logs', 'bulenox', 'trades.json')
        if not os.path.exists(self.trade_log_path):
            with open(self.trade_log_path, 'w') as f:
                json.dump([], f)
        
        logger.info("Bulenox AI Controller initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        default_config = {
            "dreamer_mode": {
                "enabled": False,
                "simulation_id": f"sim_{int(time.time())}"
            },
            "session": {
                "auto_login": True,
                "headless": False,
                "debug": True,
                "session_timeout": 3600  # 1 hour
            },
            "trading": {
                "default_quantity": 1,  # Default number of contracts
                "default_tp_pips": 50,  # Default take profit in pips
                "default_sl_pips": 30,  # Default stop loss in pips
                "max_trades_per_day": 10,
                "allowed_symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "ES"]
            },
            "security": {
                "api_key_required": True,
                "api_key": "${TRAE_API_KEY}"
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    loaded_config = json.load(f)
                
                # Merge with default config
                for key, value in loaded_config.items():
                    if key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
                
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                
                # Save default config
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, "w") as f:
                    json.dump(default_config, f, indent=2)
                
                logger.info(f"Default configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
        
        return default_config
    
    def _log_trade(self, trade_data: Dict[str, Any]) -> None:
        """Log trade to file.
        
        Args:
            trade_data (Dict[str, Any]): Trade data
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in trade_data:
                trade_data["timestamp"] = datetime.now().isoformat()
            
            # Load existing trades
            trades = []
            if os.path.exists(self.trade_log_path):
                with open(self.trade_log_path, "r") as f:
                    trades = json.load(f)
            
            # Add new trade
            trades.append(trade_data)
            
            # Save trades
            with open(self.trade_log_path, "w") as f:
                json.dump(trades, f, indent=2)
            
            logger.info(f"Trade logged: {trade_data['symbol']} {trade_data['side']} {trade_data.get('quantity', 1)} contracts")
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def start_session(self, headless: bool = None, debug: bool = None) -> bool:
        """Start a Bulenox trading session.
        
        Args:
            headless (bool, optional): Run in headless mode. Defaults to config value.
            debug (bool, optional): Enable debug mode. Defaults to config value.
            
        Returns:
            bool: True if session started successfully, False otherwise
        """
        try:
            # Use provided values or defaults from config
            if headless is None:
                headless = self.config.get("session", {}).get("headless", False)
            
            if debug is None:
                debug = self.config.get("session", {}).get("debug", True)
            
            # Check if session is already active
            if self.session_active and self.bulenox_instance:
                logger.info("Session already active")
                return True
            
            # Start new session
            logger.info(f"Starting Bulenox session (headless={headless}, debug={debug})")
            
            # Login to Bulenox
            self.bulenox_instance = login_bulenox_ai(debug=debug)
            
            if self.bulenox_instance:
                self.session_active = True
                self.last_activity = datetime.now()
                logger.info("Bulenox session started successfully")
                return True
            else:
                logger.error("Failed to start Bulenox session")
                return False
        except Exception as e:
            logger.error(f"Error starting Bulenox session: {e}")
            return False
    
    def end_session(self) -> bool:
        """End the Bulenox trading session.
        
        Returns:
            bool: True if session ended successfully, False otherwise
        """
        try:
            if self.bulenox_instance:
                self.bulenox_instance.close()
                self.bulenox_instance = None
                self.session_active = False
                logger.info("Bulenox session ended")
                return True
            else:
                logger.warning("No active session to end")
                return False
        except Exception as e:
            logger.error(f"Error ending Bulenox session: {e}")
            return False
    
    def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade based on a signal.
        
        Args:
            signal (Dict[str, Any]): Trading signal
            
        Returns:
            Dict[str, Any]: Execution result
        """
        try:
            # Extract signal data
            symbol = signal.get("symbol")
            side = signal.get("direction", "BUY").lower()
            quantity = signal.get("quantity", self.config.get("trading", {}).get("default_quantity", 1))
            
            # Convert lot_size to quantity if present (for compatibility with existing signals)
            if "lot_size" in signal and "quantity" not in signal:
                # For Bulenox, we use contracts instead of lot sizes
                # Typical conversion: 0.01 lot = 1 contract, but this varies by instrument
                lot_size = signal.get("lot_size", 0.01)
                quantity = max(1, int(lot_size * 100))  # Convert lot size to contracts
                logger.info(f"Converted lot_size {lot_size} to {quantity} contracts")
            
            # Get take profit and stop loss
            tp_pips = signal.get("take_profit", self.config.get("trading", {}).get("default_tp_pips", 50))
            sl_pips = signal.get("stop_loss", self.config.get("trading", {}).get("default_sl_pips", 30))
            
            # Check if symbol is allowed
            allowed_symbols = self.config.get("trading", {}).get("allowed_symbols", [])
            if allowed_symbols and symbol not in allowed_symbols:
                logger.warning(f"Symbol {symbol} not in allowed symbols list: {allowed_symbols}")
                return {
                    "success": False,
                    "message": f"Symbol {symbol} not allowed",
                    "signal_id": signal.get("signal_id", "unknown")
                }
            
            # Check if Dreamer Mode is enabled
            if self.dreamer_mode and self.config.get("dreamer_mode", {}).get("enabled", False):
                logger.info(f"Executing trade in Dreamer Mode: {symbol} {side} {quantity} contracts")
                
                # Convert contracts to lot size for Dreamer Mode
                lot_size = quantity / 100  # Convert contracts to lot size
                
                # Simulate trade
                result = self.dreamer_mode.simulate_trade(
                    account_id=signal.get("account_id", "default"),
                    broker="Bulenox",
                    symbol=symbol,
                    action=side.upper(),
                    lot_size=lot_size,
                    take_profit=tp_pips,
                    stop_loss=sl_pips
                )
                
                # Log simulated trade
                trade_data = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "take_profit": tp_pips,
                    "stop_loss": sl_pips,
                    "timestamp": datetime.now().isoformat(),
                    "signal_id": signal.get("signal_id", "unknown"),
                    "simulated": True,
                    "result": result
                }
                self._log_trade(trade_data)
                
                return {
                    "success": True,
                    "message": "Trade executed in Dreamer Mode",
                    "signal_id": signal.get("signal_id", "unknown"),
                    "simulated": True,
                    "result": result
                }
            
            # Real mode execution
            logger.info(f"Executing real trade: {symbol} {side} {quantity} contracts")
            
            # Check if session is active, start if not
            if not self.session_active or not self.bulenox_instance:
                session_started = self.start_session()
                if not session_started:
                    return {
                        "success": False,
                        "message": "Failed to start Bulenox session",
                        "signal_id": signal.get("signal_id", "unknown")
                    }
            
            # Update last activity time
            self.last_activity = datetime.now()
            
            # Convert pips to price levels for stop loss and take profit
            # This is a simplified conversion and may need adjustment based on the symbol
            current_price = 0  # This would be fetched from the market in a real implementation
            
            # Execute trade using Bulenox AI Selenium
            success = place_bulenox_trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                stop_loss=sl_pips,  # Using pips directly, the module will convert to price
                take_profit=tp_pips,  # Using pips directly, the module will convert to price
                debug=self.config.get("session", {}).get("debug", True)
            )
            
            # Log trade
            trade_data = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "take_profit": tp_pips,
                "stop_loss": sl_pips,
                "timestamp": datetime.now().isoformat(),
                "signal_id": signal.get("signal_id", "unknown"),
                "simulated": False,
                "success": success
            }
            self._log_trade(trade_data)
            
            if success:
                return {
                    "success": True,
                    "message": "Trade executed successfully",
                    "signal_id": signal.get("signal_id", "unknown"),
                    "simulated": False,
                    "trade_data": trade_data
                }
            else:
                return {
                    "success": False,
                    "message": "Trade execution failed",
                    "signal_id": signal.get("signal_id", "unknown"),
                    "simulated": False
                }
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "signal_id": signal.get("signal_id", "unknown")
            }
    
    def check_session_health(self) -> Dict[str, Any]:
        """Check the health of the Bulenox session.
        
        Returns:
            Dict[str, Any]: Session health status
        """
        try:
            # Check if session is active
            if not self.session_active or not self.bulenox_instance:
                return {
                    "active": False,
                    "message": "No active session",
                    "last_activity": None
                }
            
            # Check session timeout
            session_timeout = self.config.get("session", {}).get("session_timeout", 3600)  # 1 hour default
            time_since_activity = (datetime.now() - self.last_activity).total_seconds()
            
            if time_since_activity > session_timeout:
                logger.info(f"Session timeout reached ({time_since_activity:.1f}s > {session_timeout}s)")
                self.end_session()
                return {
                    "active": False,
                    "message": "Session timeout reached",
                    "last_activity": self.last_activity.isoformat()
                }
            
            return {
                "active": True,
                "message": "Session active",
                "last_activity": self.last_activity.isoformat(),
                "time_since_activity": time_since_activity
            }
        except Exception as e:
            logger.error(f"Error checking session health: {e}")
            return {
                "active": False,
                "message": f"Error: {str(e)}",
                "last_activity": self.last_activity.isoformat() if self.last_activity else None
            }
    
    def toggle_dreamer_mode(self, enabled: bool) -> Dict[str, Any]:
        """Toggle Dreamer Mode.
        
        Args:
            enabled (bool): Enable or disable Dreamer Mode
            
        Returns:
            Dict[str, Any]: Toggle result
        """
        try:
            # Update config
            if "dreamer_mode" not in self.config:
                self.config["dreamer_mode"] = {}
            
            self.config["dreamer_mode"]["enabled"] = enabled
            
            # Save config
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            
            # Initialize or clear Dreamer Mode
            if enabled and not self.dreamer_mode:
                self.dreamer_mode = DreamerMode(self.config.get("dreamer_mode", {}))
                logger.info("Dreamer Mode initialized")
            elif not enabled and self.dreamer_mode:
                self.dreamer_mode = None
                logger.info("Dreamer Mode disabled")
            
            return {
                "success": True,
                "dreamer_mode": enabled,
                "message": f"Dreamer Mode {'enabled' if enabled else 'disabled'}"
            }
        except Exception as e:
            logger.error(f"Error toggling Dreamer Mode: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Bulenox AI Controller for TRAE AI Trading Sentinel")
    parser.add_argument("--config", type=str, default="config/bulenox_controller_config.json", help="Path to configuration file")
    parser.add_argument("--start-session", action="store_true", help="Start a Bulenox trading session")
    parser.add_argument("--end-session", action="store_true", help="End the Bulenox trading session")
    parser.add_argument("--execute", type=str, help="Execute a trade from a JSON signal file")
    parser.add_argument("--dreamer", type=str, choices=["on", "off"], help="Toggle Dreamer Mode")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--mode", type=str, choices=["test", "live", "simulation"], help="Operation mode (test, live, or simulation)")
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    
    # Handle test mode
    if args.mode == "test":
        print("Running in TEST mode - validating configuration and dependencies")
        try:
            # Verify config directory exists
            config_dir = os.path.dirname(args.config)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                print(f"Created config directory: {config_dir}")
            
            # Create a test configuration if it doesn't exist
            if not os.path.exists(args.config):
                test_config = {
                    "dreamer_mode": {"enabled": True, "simulation_id": f"test_{int(time.time())}"},
                    "session": {"auto_login": False, "headless": True, "debug": True},
                    "trading": {"default_quantity": 1, "allowed_symbols": ["EURUSD", "XAUUSD"]},
                    "security": {"api_key_required": False}
                }
                with open(args.config, "w") as f:
                    json.dump(test_config, f, indent=2)
                print(f"Created test configuration at {args.config}")
            
            # Test controller initialization
            controller = BulenoxAIController(config_path=args.config)
            print("Controller initialized successfully")
            
            # Test dreamer mode
            if not controller.dreamer_mode:
                print("Enabling Dreamer Mode for testing")
                controller.toggle_dreamer_mode(True)
            
            # Print test results
            print("\nTest completed successfully. System is properly configured.")
            print("To run a simulated trade, use: --mode simulation --execute <signal_file>")
            return
            
        except Exception as e:
            print(f"Test failed: {e}")
            return
    
    # Create controller for normal operation
    controller = BulenoxAIController(config_path=args.config)
    
    # Handle simulation mode
    if args.mode == "simulation":
        print("Running in SIMULATION mode - trades will be simulated")
        controller.toggle_dreamer_mode(True)
    
    # Handle live mode
    if args.mode == "live":
        print("Running in LIVE mode - trades will be executed on the market")
        controller.toggle_dreamer_mode(False)
    
    # Process commands
    if args.start_session:
        success = controller.start_session(headless=args.headless, debug=args.debug)
        print(f"Session started: {success}")
    
    elif args.end_session:
        success = controller.end_session()
        print(f"Session ended: {success}")
    
    elif args.execute:
        try:
            with open(args.execute, "r") as f:
                signal = json.load(f)
            
            result = controller.execute_trade(signal)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error executing trade: {e}")
    
    elif args.dreamer is not None:
        enabled = args.dreamer.lower() == "on"
        result = controller.toggle_dreamer_mode(enabled)
        print(json.dumps(result, indent=2))
    
    else:
        # Default: print status
        health = controller.check_session_health()
        print(json.dumps(health, indent=2))


if __name__ == "__main__":
    main()