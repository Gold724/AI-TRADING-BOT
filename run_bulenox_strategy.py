#!/usr/bin/env python3
"""
Bulenox Gold Scalping Strategy Runner

This script integrates the Bulenox Gold Scalping Strategy with the TradeBot Sentinel
automation system to execute trades on the Bulenox ProjectX trading platform.

It combines the Tesla 3-6-9 trade rhythm with Fibonacci position sizing for gold futures trading.
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
import json
import signal
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"bulenox_strategy_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BulenoxStrategyRunner")

# Import strategy configuration
try:
    from bulenox_strategy_config import CONFIG
    logger.info("Successfully loaded strategy configuration")
except ImportError as e:
    logger.error(f"Failed to import strategy configuration: {e}")
    logger.error("Please ensure bulenox_strategy_config.py is in the current directory")
    sys.exit(1)

class BulenoxStrategyRunner:
    """Runner class to execute the Bulenox Gold Scalping Strategy via TradeBot Sentinel"""
    
    def __init__(self, headless=True, debug=False):
        """Initialize the strategy runner
        
        Args:
            headless (bool): Run browser in headless mode
            debug (bool): Enable debug logging
        """
        self.headless = headless
        self.debug = debug
        self.tradebot_process = None
        self.stop_event = threading.Event()
        
        # Set up logging level based on debug flag
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
        
        # Validate environment
        self._validate_environment()
        
        # Load trading sessions
        self.trading_sessions = CONFIG.TRADING_SESSIONS
        
        # Initialize state
        self.current_session = None
        self.session_trades = {session: 0 for session in self.trading_sessions}
        self.trades_today = 0
        self.daily_pnl = 0
        self.current_fib_index = 0
        self.fib_sequence = CONFIG.FIBONACCI_PROFIT_SEQUENCE
        
        logger.info("BulenoxStrategyRunner initialized successfully")
    
    def _validate_environment(self):
        """Validate that all required components are available"""
        # Check for TradeBot Sentinel script
        tradebot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "tradebot_sentinel_bulenox_automation.py")
        if not os.path.exists(tradebot_path):
            logger.error(f"TradeBot Sentinel script not found at {tradebot_path}")
            sys.exit(1)
        
        # Check for environment variables
        required_vars = ["BULENOX_USERNAME", "BULENOX_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please set these variables before running the script")
            sys.exit(1)
        
        logger.info("Environment validation successful")
    
    def get_current_session(self):
        """Determine the current trading session based on time"""
        now = datetime.now()
        current_time = now.time()
        
        for session_name, session_info in self.trading_sessions.items():
            if session_info['start'] <= current_time <= session_info['end']:
                return session_name
        
        return None
    
    def should_start_trading(self):
        """Determine if trading should start based on session and limits"""
        # Check if we're in a valid trading session
        self.current_session = self.get_current_session()
        if not self.current_session:
            logger.info("Not currently in a trading session")
            return False
        
        # Check if we've reached daily profit target
        if self.daily_pnl >= CONFIG.DAILY_PROFIT_TARGET:
            logger.info(f"Daily profit target reached: ${self.daily_pnl:.2f}")
            return False
        
        # Check if we've hit daily max drawdown
        if self.daily_pnl <= -CONFIG.DAILY_MAX_DRAWDOWN:
            logger.info(f"Daily max drawdown reached: ${self.daily_pnl:.2f}")
            return False
        
        # Check if we've reached max trades for the day
        if self.trades_today >= CONFIG.MAX_TRADES_PER_DAY:
            logger.info(f"Maximum trades for the day reached: {self.trades_today}")
            return False
        
        # Check if we've reached max trades for the current session
        if self.session_trades[self.current_session] >= 3:  # 3 trades per session
            logger.info(f"Maximum trades for {self.current_session} session reached")
            return False
        
        return True
    
    def get_current_position_size(self):
        """Calculate position size based on Fibonacci sequence"""
        # Get current Fibonacci value
        current_fib = self.fib_sequence[self.current_fib_index]
        
        # Calculate contracts based on Fibonacci value
        # This is a simplified calculation - adjust as needed
        base_contract_value = 10  # $10 per contract
        contracts = max(1, min(CONFIG.MAX_CONTRACTS, current_fib // base_contract_value))
        
        return contracts
    
    def advance_fibonacci(self):
        """Advance to the next Fibonacci level"""
        if self.current_fib_index < len(self.fib_sequence) - 1:
            self.current_fib_index += 1
            logger.info(f"Advanced Fibonacci index to {self.current_fib_index} (${self.fib_sequence[self.current_fib_index]})")
    
    def reset_fibonacci(self):
        """Reset Fibonacci sequence to the beginning"""
        self.current_fib_index = 0
        logger.info(f"Reset Fibonacci sequence to index {self.current_fib_index} (${self.fib_sequence[self.current_fib_index]})")
    
    def execute_trade(self):
        """Execute a trade using TradeBot Sentinel"""
        # Determine position size
        contracts = self.get_current_position_size()
        
        # Prepare trade parameters
        trade_params = {
            "symbol": "GOLD",
            "direction": "BUY",  # Simplified - in real implementation, determine based on signals
            "quantity": contracts,
            "session": self.current_session,
            "fib_level": self.current_fib_index,
            "target_profit": self.fib_sequence[self.current_fib_index]
        }
        
        # Log trade attempt
        logger.info(f"Attempting to execute trade: {json.dumps(trade_params)}")
        
        # Create command to run TradeBot Sentinel
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                        "tradebot_sentinel_bulenox_automation.py"),
            "--symbol", trade_params["symbol"],
            "--direction", trade_params["direction"],
            "--quantity", str(trade_params["quantity"]),
        ]
        
        if not self.headless:
            cmd.append("--no-headless")
        
        if self.debug:
            cmd.append("--debug")
        
        # Execute TradeBot Sentinel
        try:
            logger.info(f"Executing command: {' '.join(cmd)}")
            self.tradebot_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for process to complete
            stdout, stderr = self.tradebot_process.communicate(timeout=300)  # 5 minute timeout
            
            # Process results
            if self.tradebot_process.returncode == 0:
                logger.info("Trade execution successful")
                
                # Update trade counters
                self.trades_today += 1
                self.session_trades[self.current_session] += 1
                
                # For this example, assume a successful trade and advance Fibonacci
                # In a real implementation, parse the actual trade result
                self.daily_pnl += self.fib_sequence[self.current_fib_index]
                self.advance_fibonacci()
                
                logger.info(f"Updated daily PnL: ${self.daily_pnl:.2f}")
                return True
            else:
                logger.error(f"Trade execution failed with code {self.tradebot_process.returncode}")
                logger.error(f"Error: {stderr}")
                
                # Reset Fibonacci on failure
                self.reset_fibonacci()
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Trade execution timed out")
            if self.tradebot_process:
                self.tradebot_process.kill()
            return False
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False
    
    def run_trading_session(self):
        """Run a complete trading session"""
        logger.info(f"Starting trading session: {self.current_session}")
        
        # Reset Fibonacci sequence at the start of a new session
        self.reset_fibonacci()
        
        # Execute up to 3 trades in this session
        trades_executed = 0
        while trades_executed < 3 and not self.stop_event.is_set():
            if self.should_start_trading():
                logger.info(f"Executing trade {trades_executed + 1} of 3 for {self.current_session} session")
                
                # Execute the trade
                if self.execute_trade():
                    trades_executed += 1
                    
                    # Wait between trades
                    wait_time = 60  # 1 minute between trades
                    logger.info(f"Waiting {wait_time} seconds before next trade")
                    
                    # Use stop_event to allow for clean shutdown
                    if self.stop_event.wait(wait_time):
                        logger.info("Received stop signal during wait")
                        break
                else:
                    # Wait longer after a failed trade
                    wait_time = 180  # 3 minutes after failure
                    logger.info(f"Waiting {wait_time} seconds after failed trade")
                    
                    if self.stop_event.wait(wait_time):
                        logger.info("Received stop signal during wait")
                        break
            else:
                # Trading conditions no longer met
                logger.info("Trading conditions no longer met, ending session")
                break
        
        logger.info(f"Completed {trades_executed} trades in {self.current_session} session")
        return trades_executed
    
    def run(self):
        """Main execution loop"""
        logger.info("Starting Bulenox Gold Scalping Strategy Runner")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Main trading loop
            while not self.stop_event.is_set():
                if self.should_start_trading():
                    # Run the current trading session
                    self.run_trading_session()
                
                # Check if we should continue trading today
                if self.daily_pnl >= CONFIG.DAILY_PROFIT_TARGET:
                    logger.info(f"Daily profit target reached: ${self.daily_pnl:.2f}")
                    logger.info("Stopping trading for today")
                    
                    # Wait until tomorrow
                    self._wait_until_tomorrow()
                    continue
                
                if self.daily_pnl <= -CONFIG.DAILY_MAX_DRAWDOWN:
                    logger.info(f"Daily max drawdown reached: ${self.daily_pnl:.2f}")
                    logger.info("Stopping trading for today")
                    
                    # Wait until tomorrow
                    self._wait_until_tomorrow()
                    continue
                
                # Wait for next check
                logger.info("Waiting for next trading session check")
                if self.stop_event.wait(300):  # Check every 5 minutes
                    break
            
            logger.info("Trading loop ended")
            
        except Exception as e:
            logger.error(f"Error in main execution loop: {e}")
        finally:
            logger.info("Shutting down Bulenox Strategy Runner")
            self._cleanup()
    
    def _wait_until_tomorrow(self):
        """Wait until the next trading day"""
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        
        wait_seconds = (tomorrow - datetime.now()).total_seconds()
        logger.info(f"Waiting until tomorrow ({wait_seconds:.0f} seconds)")
        
        # Reset daily counters
        self.trades_today = 0
        self.daily_pnl = 0
        self.session_trades = {session: 0 for session in self.trading_sessions}
        
        # Wait until tomorrow, but allow for clean shutdown
        self.stop_event.wait(wait_seconds)
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down")
        self.stop_event.set()
    
    def _cleanup(self):
        """Clean up resources"""
        if self.tradebot_process and self.tradebot_process.poll() is None:
            logger.info("Terminating TradeBot process")
            self.tradebot_process.terminate()
            try:
                self.tradebot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("TradeBot process did not terminate, forcing kill")
                self.tradebot_process.kill()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Bulenox Gold Scalping Strategy Runner")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in visible mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Print banner
    print("\n" + "="*80)
    print("BULENOX GOLD SCALPING STRATEGY RUNNER")
    print("Tesla 3-6-9 + Fibonacci Position Sizing Model")
    print("="*80 + "\n")
    
    # Print configuration summary
    print(f"Daily Profit Target: ${CONFIG.DAILY_PROFIT_TARGET:.2f}")
    print(f"Daily Max Drawdown: ${CONFIG.DAILY_MAX_DRAWDOWN:.2f}")
    print(f"Max Trades Per Day: {CONFIG.MAX_TRADES_PER_DAY}")
    print(f"Fibonacci Sequence: {CONFIG.FIBONACCI_PROFIT_SEQUENCE}")
    print("\nTrading Sessions:")
    for name, session in CONFIG.TRADING_SESSIONS.items():
        print(f"  {name.title()}: {session['start']} - {session['end']}")
    print("\n" + "-"*80 + "\n")
    
    # Create and run the strategy runner
    runner = BulenoxStrategyRunner(
        headless=not args.no_headless,
        debug=args.debug
    )
    
    try:
        runner.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
    finally:
        logger.info("Bulenox Strategy Runner shutdown complete")

if __name__ == "__main__":
    main()