#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trae.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.main")

# Ensure necessary directories exist
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/screenshots", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Load environment variables from .env file
load_dotenv()

# Import TRAE components
try:
    from sentinel_decider import SentinelDecider, DeciderMode
    from liveops.stealth_executor import StealthExecutor
    from liveops.account_manager import AccountManager
    from liveops.heartbeat_monitor import HeartbeatMonitor
    
    # Import Bulenox components
    from ai_login_bulenox import ai_login_bulenox, update_heartbeat_status
    from executor_bulenox import BulenoxExecutor, execute_trade
    BULENOX_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    BULENOX_AVAILABLE = False
    sys.exit(1)


class BulenoxIntegration:
    """Integration class to connect login_bulenox.py with executor_bulenox.py."""
    
    def __init__(self, debug=False):
        """Initialize the Bulenox integration.
        
        Args:
            debug (bool): Enable debug mode
        """
        self.driver = None
        self.executor = None
        self.debug = debug
        self.heartbeat_file = "logs/heartbeat_status.txt"
        self.profile_index = int(os.getenv("CHROME_PROFILE_INDEX", "13"))
        self.username = os.getenv("BULENOX_USERNAME")
        self.password = os.getenv("BULENOX_PASSWORD")
        
        if not self.username or not self.password:
            logger.warning("Bulenox credentials not set in environment variables")
        
        logger.info(f"Bulenox integration initialized with profile index {self.profile_index}")
    
    def login(self):
        """Login to Bulenox using AI-powered stealth login.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info(f"Attempting AI-powered login to Bulenox with profile {self.profile_index}")
            
            # Attempt login with AI-powered approach
            self.driver = ai_login_bulenox(debug=self.debug)
            
            if self.driver:
                # Update heartbeat status
                update_heartbeat_status("✅ ONLINE - AI Login Successful")
                
                # Initialize executor
                self.executor = BulenoxExecutor(self.driver)
                
                logger.info("Successfully logged in to Bulenox using AI-powered login")
                return True
            else:
                update_heartbeat_status("❌ OFFLINE - AI Login Failed")
                logger.error("Failed to login to Bulenox using AI-powered login")
                return False
                
        except Exception as e:
            update_heartbeat_status("ERROR", self.heartbeat_file)
            logger.error(f"Error during Bulenox login: {e}")
            return False
    
    def is_logged_in(self):
        """Check if we're logged in to Bulenox.
        
        Returns:
            bool: True if logged in, False otherwise
        """
        return self.driver is not None
    
    def execute_trade(self, signal):
        """Execute a trade on Bulenox.
        
        Args:
            signal (dict): The trading signal
            
        Returns:
            dict: Trade execution result
        """
        if not self.is_logged_in():
            raise Exception("Not logged in to Bulenox")
        
        try:
            logger.info(f"Executing trade on Bulenox: {signal['id']}")
            
            # Execute trade using executor_bulenox
            result = execute_trade(
                driver=self.driver,
                signal=signal,
                debug=self.debug
            )
            
            # Update heartbeat status
            update_heartbeat_status("TRADING", self.heartbeat_file)
            
            return result
        except Exception as e:
            logger.error(f"Error executing trade on Bulenox: {e}")
            update_heartbeat_status("ERROR", self.heartbeat_file)
            raise
    
    def logout(self):
        """Logout from Bulenox.
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        if not self.driver:
            logger.info("Not logged in to Bulenox")
            return True
        
        try:
            logger.info("Logging out from Bulenox")
            
            # Quit the WebDriver
            self.driver.quit()
            self.driver = None
            self.executor = None
            
            # Update heartbeat status
            update_heartbeat_status("OFFLINE", self.heartbeat_file)
            
            logger.info("Successfully logged out from Bulenox")
            return True
        except Exception as e:
            logger.error(f"Error during Bulenox logout: {e}")
            return False
    
    def __init__(self, debug: bool = False):
        """Initialize Bulenox integration.
        
        Args:
            debug (bool, optional): Enable debug mode. Defaults to False.
        """
        self.driver = None
        self.debug = debug
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.executor = None
        logger.info("Bulenox integration initialized")
    
    def login(self) -> bool:
        """Login to Bulenox platform using AI-powered login with enhanced retry logic.
        
        Returns:
            bool: True if login successful, False otherwise.
        """
        try:
            from login_executor_connector import BulenoxConnector
            
            logger.info("Logging in to Bulenox using enhanced AI-powered login...")
            update_heartbeat_status("🔄 Initializing enhanced AI-powered login to Bulenox...")
            
            # Create connector with profile switching and retry logic
            profile_index = int(os.getenv("BULENOX_PROFILE_INDEX", "13"))
            self.connector = BulenoxConnector(debug=self.debug, profile_index=profile_index)
            
            # Login with retry logic
            login_success = self.connector.login(max_retries=3)
            
            if login_success:
                # Get the driver from the connector
                self.driver = self.connector.driver
                update_heartbeat_status("✅ Successfully logged in to Bulenox with enhanced AI login", session_active=True)
                logger.info("Enhanced AI-powered login successful")
                return True
            else:
                update_heartbeat_status("❌ Login failed after multiple attempts", session_active=False)
                logger.error("Login failed after multiple attempts")
                return False
        except Exception as e:
            update_heartbeat_status(f"❌ Login error: {str(e)[:50]}...", session_active=False)
            logger.error(f"Error during login: {e}")
            return False
    
    def execute_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade on Bulenox platform using enhanced connector.
        
        Args:
            signal (Dict[str, Any]): Trading signal with symbol, direction, etc.
            
        Returns:
            Dict[str, Any]: Trade execution result
        """
        if not hasattr(self, 'connector') or not self.connector:
            logger.error("Enhanced connector not initialized. Cannot execute trade.")
            return {"success": False, "error": "Enhanced connector not initialized"}
        
        try:
            logger.info(f"Executing trade using enhanced connector: {signal}")
            update_heartbeat_status(f"🔄 Executing trade with enhanced connector: {signal['symbol']} {signal.get('direction', 'buy')}")
            
            # Use the connector to execute the trade
            result = self.connector.execute_trade(signal)
            
            if result and result.get("success", False):
                logger.info(f"Trade executed successfully: {signal['symbol']}")
                update_heartbeat_status(f"✅ Trade executed: {signal['symbol']} {signal.get('direction', 'buy')}")
            else:
                logger.error(f"Trade execution failed: {signal['symbol']}")
                update_heartbeat_status(f"❌ Trade failed: {signal['symbol']} {signal.get('direction', 'buy')}")
            
            return result
        except Exception as e:
            error_msg = f"Error executing trade: {e}"
            logger.error(error_msg)
            update_heartbeat_status(f"❌ {error_msg[:50]}...")
            return {"success": False, "error": str(e)}
    
    def logout(self) -> bool:
        """Logout from Bulenox platform using enhanced connector.
        
        Returns:
            bool: True if logout successful, False otherwise.
        """
        if not hasattr(self, 'connector') or not self.connector:
            logger.warning("Enhanced connector not initialized. Nothing to logout from.")
            return True
        
        try:
            logger.info("Logging out from Bulenox using enhanced connector...")
            update_heartbeat_status("🔄 Logging out from Bulenox using enhanced connector...")
            
            # Use the connector to logout
            logout_success = self.connector.logout()
            return logout_success
        except Exception as e:
            error_msg = f"Error during logout: {e}"
            logger.error(error_msg)
            update_heartbeat_status(f"⚠️ {error_msg[:50]}...", session_active=False)
            return False


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TRAE AI Trading Sentinel")
    parser.add_argument(
        "--phase", 
        type=int, 
        default=int(os.getenv("TRAE_PHASE", "10")),
        help="TRAE phase number (default: 10)"
    )
    parser.add_argument(
        "--liveops", 
        action="store_true", 
        default=os.getenv("TRAE_LIVEOPS", "true").lower() == "true",
        help="Enable LiveOps mode"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--webhook", 
        action="store_true", 
        default=False,
        help="Start webhook server for signal reception"
    )
    parser.add_argument(
        "--bulenox", 
        action="store_true", 
        default=os.getenv("USE_BULENOX", "false").lower() == "true",
        help="Enable Bulenox integration"
    )
    parser.add_argument(
        "--auto-login", 
        action="store_true", 
        default=os.getenv("AUTO_LOGIN", "true").lower() == "true",
        help="Automatically login to Bulenox on startup"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        default=os.getenv("DEBUG", "false").lower() == "true",
        help="Enable debug mode"
    )
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Configuration file {config_path} not found, using defaults")
            return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def start_webhook_server(port: int = 5000):
    """Start webhook server for receiving trading signals.
    
    Args:
        port (int, optional): Port to listen on. Defaults to 5000.
    """
    try:
        from flask import Flask, request, jsonify
        import threading
        
        app = Flask(__name__)
        webhook_secret = os.getenv("WEBHOOK_SECRET", "")

        
        
        @app.route("/signal", methods=["POST"])
        def receive_signal():
            # Verify webhook secret if provided
            if webhook_secret:
                auth_header = request.headers.get("Authorization", "")
                if not auth_header or auth_header != f"Bearer {webhook_secret}":
                    return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
            # Process signal
            try:
                signal_data = request.json
                logger.info(f"Received signal: {signal_data}")
                
                # Save signal to file for processing
                with open("data/incoming_signals.json", "a") as f:
                    f.write(json.dumps(signal_data) + "\n")
                
                return jsonify({"status": "success", "message": "Signal received"})
            except Exception as e:
                logger.error(f"Error processing webhook signal: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        # Start Flask in a separate thread
        threading.Thread(
            target=lambda: app.run(host="0.0.0.0", port=port, debug=False),
            daemon=True
        ).start()
        
        logger.info(f"Webhook server started on port {port}")
    except ImportError:
        logger.error("Flask not installed. Cannot start webhook server.")
    except Exception as e:
        logger.error(f"Error starting webhook server: {e}")


def process_signals(decider: SentinelDecider, bulenox=None):
    """Process incoming trading signals.
    
    Args:
        decider (SentinelDecider): The sentinel decider instance
        bulenox (BulenoxIntegration, optional): Bulenox integration instance
    """
    signals_file = "data/incoming_signals.json"
    processed_file = "data/processed_signals.json"
    
    # Create processed signals file if it doesn't exist
    if not os.path.exists(processed_file):
        with open(processed_file, "w") as f:
            f.write("[]")
    
    # Load processed signal IDs
    try:
        with open(processed_file, "r") as f:
            processed_signals = json.load(f)
    except json.JSONDecodeError:
        processed_signals = []
    
    # Check for new signals
    if os.path.exists(signals_file):
        new_processed = []
        with open(signals_file, "r") as f:
            for line in f:
                try:
                    signal = json.loads(line.strip())
                    signal_id = signal.get("id", str(hash(line)))
                    
                    # Skip already processed signals
                    if signal_id in [p.get("id") for p in processed_signals]:
                        continue
                    
                    # Process the signal
                    logger.info(f"Processing signal: {signal_id}")
                    result = decider.decide_trade(signal)
                    
                    # Execute via Bulenox if integration is enabled and trade should be executed
                    if bulenox and result.get("action") == "execute":
                        logger.info(f"Executing trade via Bulenox: {signal_id}")
                        
                        # Ensure we're logged in
                        if not bulenox.driver:
                            logger.info("Not logged in to Bulenox. Attempting login...")
                            if not bulenox.login():
                                logger.error("Failed to login to Bulenox. Cannot execute trade.")
                                raise Exception("Bulenox login failed")
                        
                        # Execute the trade
                        trade_result = bulenox.execute_trade(signal)
                        logger.info(f"Bulenox trade execution result: {trade_result}")
                        
                        # Add trade result to result
                        result["trade_result"] = trade_result
                    
                    # Record processed signal
                    processed_record = {
                        "id": signal_id,
                        "timestamp": datetime.now().isoformat(),
                        "signal": signal,
                        "result": result
                    }
                    new_processed.append(processed_record)
                    
                except Exception as e:
                    logger.error(f"Error processing signal: {e}")
        
        # Update processed signals file
        if new_processed:
            processed_signals.extend(new_processed)
            with open(processed_file, "w") as f:
                json.dump(processed_signals, f, indent=2)
            
            # Truncate signals file after processing
            with open(signals_file, "w") as f:
                pass


def main():
    """Main entry point for TRAE AI Trading Sentinel."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Log startup information
    logger.info(f"Starting TRAE AI Trading Sentinel - Phase {args.phase}")
    logger.info(f"LiveOps mode: {'Enabled' if args.liveops else 'Disabled'}")
    logger.info(f"Bulenox integration: {'Enabled' if args.bulenox else 'Disabled'}")
    
    # Display Phase 13 activation banner if Bulenox is enabled
    if args.bulenox:
        print("\n" + "="*80)
        print("🧠 Phase 13: TRAE Bulenox Integration")
        print("🎯 Objective: Connect login_bulenox.py with executor_bulenox.py for real orders")
        print("\nTRAE, initiate Phase 13: Bulenox Integration. You are now connected to the Bulenox trading platform.")
        print("Begin execution of automated trading operations with stealth login capabilities.")
        print("\n🚀 Final Trigger: TRAE, begin Bulenox Integration. Accept signal stream. Execute with stealth. Track everything.")
        print("="*80 + "\n")
        
        logger.info("Phase 13 Bulenox Integration initiated")
    # Display Phase 10 activation banner if in LiveOps mode
    elif args.liveops and args.phase == 10:
        print("\n" + "="*80)
        print("🧠 Phase 10: TRAE LiveOps Activation (Post-Governance)")
        print("🎯 Objective: Transition to full-time automated trading operations")
        print("\nTRAE, initiate Phase 10: LiveOps Activation. You are now a sovereign AI Trading Sentinel with full governance.")
        print("Begin execution of automated trading operations, persistent deployment, and governance enforcement.")
        print("\n🚀 Final Trigger: TRAE, begin LiveOps. Accept signal stream. Govern your actions. Execute with stealth. Track everything. Protect equity.")
        print("="*80 + "\n")
        
        logger.info("Phase 10 LiveOps Activation initiated")
    
    # Ensure required directories exist
    os.makedirs("logs/liveops", exist_ok=True)
    os.makedirs("data/accounts", exist_ok=True)
    os.makedirs("data/signals", exist_ok=True)
    
    # Initialize Bulenox integration if enabled
    bulenox = None
    if args.bulenox:
        logger.info("Initializing Bulenox integration")
        bulenox = BulenoxIntegration(debug=args.debug)
        
        # Auto-login if enabled
        if args.auto_login:
            logger.info("Auto-login enabled. Attempting to login to Bulenox...")
            if bulenox.login():
                logger.info("Successfully logged in to Bulenox")
            else:
                logger.warning("Failed to login to Bulenox. Will retry when needed.")
    
    # Initialize the sentinel decider
    decider = SentinelDecider(
        phase=args.phase,
        liveops_mode=args.liveops,
        automated_trading=True,
        multi_account=True,
        passive_learning=True
    )
    
    # Start webhook server if requested
    if args.webhook:
        webhook_port = int(os.getenv("WEBHOOK_PORT", "5000"))
        start_webhook_server(port=webhook_port)
    
    # Main processing loop
    try:
        logger.info("Entering main processing loop")
        while True:
            # Process any incoming signals
            process_signals(decider, bulenox=bulenox)
            
            # Sleep to avoid high CPU usage
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        # Cleanup
        if bulenox and bulenox.driver:
            logger.info("Logging out from Bulenox...")
            bulenox.logout()
        
        logger.info("TRAE AI Trading Sentinel shutting down")


if __name__ == "__main__":
    main()