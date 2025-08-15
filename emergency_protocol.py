# emergency_protocol.py

import json
import logging
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import threading

# Try to import from other modules
try:
    from trade_evaluator import TradePerformanceEvaluator
except ImportError:
    # Define a minimal version if the import fails
    class TradePerformanceEvaluator:
        def get_strategy_performance(self, strategy_name):
            return {}
        def get_daily_drawdown(self):
            return 0.0

try:
    from slack_reporter import send_slack_message
except ImportError:
    # Define a minimal version if the import fails
    def send_slack_message(message, channel="#alerts"):
        logging.info(f"Would send to Slack: {message} (to {channel})")
        return True

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("emergency_protocol")

# Constants
EMERGENCY_DIR = os.path.join("data", "emergency")
EMERGENCY_STATE_FILE = os.path.join(EMERGENCY_DIR, "emergency_state.json")
EMERGENCY_LOG_FILE = os.path.join(EMERGENCY_DIR, "emergency_log.json")
TRADE_HISTORY_FILE = os.path.join("data", "trade_history.json")
STRATEGY_STATS_FILE = os.path.join("data", "strategy_stats.json")

# Ensure directories exist
os.makedirs(EMERGENCY_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)


class EmergencyProtocol:
    """Emergency protocol for detecting and responding to anomalous market conditions"""

    def __init__(self, trade_history_file: str = TRADE_HISTORY_FILE,
                 strategy_stats_file: str = STRATEGY_STATS_FILE,
                 emergency_state_file: str = EMERGENCY_STATE_FILE,
                 emergency_log_file: str = EMERGENCY_LOG_FILE):
        """Initialize the emergency protocol

        Args:
            trade_history_file (str): Path to the trade history file
            strategy_stats_file (str): Path to the strategy statistics file
            emergency_state_file (str): Path to the emergency state file
            emergency_log_file (str): Path to the emergency log file
        """
        self.trade_history_file = trade_history_file
        self.strategy_stats_file = strategy_stats_file
        self.emergency_state_file = emergency_state_file
        self.emergency_log_file = emergency_log_file
        self.evaluator = TradePerformanceEvaluator(trade_history_file, strategy_stats_file)
        
        # Load emergency state
        self.emergency_state = self.load_emergency_state()
        self.emergency_log = self.load_emergency_log()
        
        # Initialize monitoring thread
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
    def load_emergency_state(self) -> Dict:
        """Load emergency state from file

        Returns:
            Dict: Emergency state data
        """
        default_state = {
            "active": False,
            "level": "normal",  # normal, caution, warning, critical, emergency
            "reason": None,
            "start_time": None,
            "end_time": None,
            "affected_strategies": [],
            "affected_symbols": [],
            "trading_paused": False,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        try:
            if os.path.exists(self.emergency_state_file):
                with open(self.emergency_state_file, "r") as f:
                    return json.load(f)
            else:
                # Create default state file if it doesn't exist
                with open(self.emergency_state_file, "w") as f:
                    json.dump(default_state, f, indent=4)
                return default_state
        except Exception as e:
            logger.error(f"Error loading emergency state: {e}")
            return default_state
            
    def load_emergency_log(self) -> List[Dict]:
        """Load emergency log from file

        Returns:
            List[Dict]: Emergency log entries
        """
        try:
            if os.path.exists(self.emergency_log_file):
                with open(self.emergency_log_file, "r") as f:
                    return json.load(f)
            else:
                # Create empty log file if it doesn't exist
                with open(self.emergency_log_file, "w") as f:
                    json.dump([], f, indent=4)
                return []
        except Exception as e:
            logger.error(f"Error loading emergency log: {e}")
            return []
            
    def save_emergency_state(self) -> bool:
        """Save emergency state to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update last updated timestamp
            self.emergency_state["last_updated"] = datetime.utcnow().isoformat()
            
            with open(self.emergency_state_file, "w") as f:
                json.dump(self.emergency_state, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving emergency state: {e}")
            return False
            
    def save_emergency_log(self) -> bool:
        """Save emergency log to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.emergency_log_file, "w") as f:
                json.dump(self.emergency_log, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving emergency log: {e}")
            return False
            
    def load_trade_history(self) -> List[Dict]:
        """Load trade history from file

        Returns:
            List[Dict]: List of trade records
        """
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"Trade history file {self.trade_history_file} not found.")
                return []
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return []
            
    def add_emergency_log_entry(self, level: str, reason: str, 
                              affected_strategies: List[str] = None,
                              affected_symbols: List[str] = None,
                              actions_taken: List[str] = None) -> bool:
        """Add an entry to the emergency log

        Args:
            level (str): Emergency level (caution, warning, critical, emergency)
            reason (str): Reason for the emergency
            affected_strategies (List[str], optional): Affected strategies. Defaults to None.
            affected_symbols (List[str], optional): Affected symbols. Defaults to None.
            actions_taken (List[str], optional): Actions taken. Defaults to None.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create log entry
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "reason": reason,
                "affected_strategies": affected_strategies or [],
                "affected_symbols": affected_symbols or [],
                "actions_taken": actions_taken or [],
                "emergency_active": self.emergency_state["active"],
                "trading_paused": self.emergency_state["trading_paused"]
            }
            
            # Add entry to log
            self.emergency_log.append(entry)
            
            # Save log
            return self.save_emergency_log()
        except Exception as e:
            logger.error(f"Error adding emergency log entry: {e}")
            return False
            
    def activate_emergency(self, level: str, reason: str, 
                         affected_strategies: List[str] = None,
                         affected_symbols: List[str] = None,
                         pause_trading: bool = False) -> bool:
        """Activate emergency protocol

        Args:
            level (str): Emergency level (caution, warning, critical, emergency)
            reason (str): Reason for the emergency
            affected_strategies (List[str], optional): Affected strategies. Defaults to None.
            affected_symbols (List[str], optional): Affected symbols. Defaults to None.
            pause_trading (bool, optional): Whether to pause trading. Defaults to False.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update emergency state
            self.emergency_state["active"] = True
            self.emergency_state["level"] = level
            self.emergency_state["reason"] = reason
            self.emergency_state["start_time"] = datetime.utcnow().isoformat()
            self.emergency_state["end_time"] = None
            self.emergency_state["affected_strategies"] = affected_strategies or []
            self.emergency_state["affected_symbols"] = affected_symbols or []
            self.emergency_state["trading_paused"] = pause_trading
            
            # Save emergency state
            state_saved = self.save_emergency_state()
            
            # Add log entry
            actions = ["Activated emergency protocol"]
            if pause_trading:
                actions.append("Paused trading")
                
            log_added = self.add_emergency_log_entry(
                level, reason, affected_strategies, affected_symbols, actions
            )
            
            # Send notification
            self.send_emergency_notification(
                level, reason, affected_strategies, affected_symbols, pause_trading
            )
            
            return state_saved and log_added
        except Exception as e:
            logger.error(f"Error activating emergency: {e}")
            return False
            
    def deactivate_emergency(self, reason: str = "Manual deactivation") -> bool:
        """Deactivate emergency protocol

        Args:
            reason (str, optional): Reason for deactivation. Defaults to "Manual deactivation".

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if emergency is active
            if not self.emergency_state["active"]:
                logger.info("Emergency protocol is not active.")
                return True
                
            # Update emergency state
            self.emergency_state["active"] = False
            self.emergency_state["end_time"] = datetime.utcnow().isoformat()
            self.emergency_state["trading_paused"] = False
            
            # Save emergency state
            state_saved = self.save_emergency_state()
            
            # Add log entry
            level = self.emergency_state["level"]
            affected_strategies = self.emergency_state["affected_strategies"]
            affected_symbols = self.emergency_state["affected_symbols"]
            
            log_added = self.add_emergency_log_entry(
                level, f"Deactivated: {reason}", 
                affected_strategies, affected_symbols, 
                ["Deactivated emergency protocol", "Resumed trading"]
            )
            
            # Send notification
            self.send_deactivation_notification(reason)
            
            return state_saved and log_added
        except Exception as e:
            logger.error(f"Error deactivating emergency: {e}")
            return False
            
    def update_emergency_level(self, level: str, reason: str) -> bool:
        """Update emergency level

        Args:
            level (str): New emergency level
            reason (str): Reason for the update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if emergency is active
            if not self.emergency_state["active"]:
                logger.warning("Cannot update level: Emergency protocol is not active.")
                return False
                
            # Get current level
            current_level = self.emergency_state["level"]
            
            # Update emergency state
            self.emergency_state["level"] = level
            
            # Save emergency state
            state_saved = self.save_emergency_state()
            
            # Add log entry
            affected_strategies = self.emergency_state["affected_strategies"]
            affected_symbols = self.emergency_state["affected_symbols"]
            
            log_added = self.add_emergency_log_entry(
                level, f"Level changed from {current_level} to {level}: {reason}", 
                affected_strategies, affected_symbols, 
                [f"Updated emergency level to {level}"]
            )
            
            # Send notification
            self.send_level_change_notification(current_level, level, reason)
            
            return state_saved and log_added
        except Exception as e:
            logger.error(f"Error updating emergency level: {e}")
            return False
            
    def send_emergency_notification(self, level: str, reason: str,
                                   affected_strategies: List[str],
                                   affected_symbols: List[str],
                                   trading_paused: bool) -> bool:
        """Send emergency notification

        Args:
            level (str): Emergency level
            reason (str): Reason for the emergency
            affected_strategies (List[str]): Affected strategies
            affected_symbols (List[str]): Affected symbols
            trading_paused (bool): Whether trading is paused

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format message
            message = f"🚨 *EMERGENCY ALERT - {level.upper()}* 🚨\n"
            message += f"*Reason:* {reason}\n"
            
            if affected_strategies:
                message += f"*Affected Strategies:* {', '.join(affected_strategies)}\n"
                
            if affected_symbols:
                message += f"*Affected Symbols:* {', '.join(affected_symbols)}\n"
                
            message += f"*Trading Status:* {'PAUSED ⛔' if trading_paused else 'Active with caution ⚠️'}\n"
            message += f"*Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            
            # Send to Slack
            channel = "#alerts" if level in ["critical", "emergency"] else "#trading"
            return send_slack_message(message, channel)
        except Exception as e:
            logger.error(f"Error sending emergency notification: {e}")
            return False
            
    def send_deactivation_notification(self, reason: str) -> bool:
        """Send deactivation notification

        Args:
            reason (str): Reason for deactivation

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format message
            message = f"✅ *EMERGENCY DEACTIVATED* ✅\n"
            message += f"*Reason:* {reason}\n"
            message += f"*Previous Level:* {self.emergency_state['level'].upper()}\n"
            
            if self.emergency_state["start_time"]:
                start_time = datetime.fromisoformat(self.emergency_state["start_time"])
                end_time = datetime.utcnow()
                duration = end_time - start_time
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                message += f"*Duration:* {hours}h {minutes}m {seconds}s\n"
                
            message += f"*Trading Status:* Resumed ✅\n"
            message += f"*Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            
            # Send to Slack
            return send_slack_message(message, "#trading")
        except Exception as e:
            logger.error(f"Error sending deactivation notification: {e}")
            return False
            
    def send_level_change_notification(self, old_level: str, new_level: str, reason: str) -> bool:
        """Send level change notification

        Args:
            old_level (str): Old emergency level
            new_level (str): New emergency level
            reason (str): Reason for the change

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format message
            if new_level in ["critical", "emergency"]:
                message = f"🔴 *EMERGENCY ESCALATED TO {new_level.upper()}* 🔴\n"
            elif old_level in ["critical", "emergency"] and new_level not in ["critical", "emergency"]:
                message = f"🟠 *EMERGENCY DOWNGRADED TO {new_level.upper()}* 🟠\n"
            else:
                message = f"🟡 *EMERGENCY LEVEL CHANGED: {old_level.upper()} → {new_level.upper()}* 🟡\n"
                
            message += f"*Reason:* {reason}\n"
            
            if self.emergency_state["affected_strategies"]:
                message += f"*Affected Strategies:* {', '.join(self.emergency_state['affected_strategies'])}\n"
                
            if self.emergency_state["affected_symbols"]:
                message += f"*Affected Symbols:* {', '.join(self.emergency_state['affected_symbols'])}\n"
                
            message += f"*Trading Status:* {'PAUSED ⛔' if self.emergency_state['trading_paused'] else 'Active with caution ⚠️'}\n"
            message += f"*Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            
            # Send to Slack
            channel = "#alerts" if new_level in ["critical", "emergency"] else "#trading"
            return send_slack_message(message, channel)
        except Exception as e:
            logger.error(f"Error sending level change notification: {e}")
            return False
            
    def check_daily_drawdown(self) -> Tuple[bool, float]:
        """Check daily drawdown

        Returns:
            Tuple[bool, float]: (threshold_exceeded, drawdown_percentage)
        """
        try:
            # Get daily drawdown from evaluator
            drawdown = self.evaluator.get_daily_drawdown()
            
            # Check if drawdown exceeds threshold
            threshold_exceeded = drawdown >= 2.0  # 2% daily drawdown threshold
            
            return threshold_exceeded, drawdown
        except Exception as e:
            logger.error(f"Error checking daily drawdown: {e}")
            return False, 0.0
            
    def check_consecutive_losses(self, strategy_name: Optional[str] = None, 
                                threshold: int = 5) -> Tuple[bool, int, List[str]]:
        """Check consecutive losses

        Args:
            strategy_name (Optional[str], optional): Strategy to check. Defaults to None (all strategies).
            threshold (int, optional): Consecutive loss threshold. Defaults to 5.

        Returns:
            Tuple[bool, int, List[str]]: (threshold_exceeded, max_consecutive_losses, affected_strategies)
        """
        try:
            # Load trade history
            trades = self.load_trade_history()
            
            if not trades:
                return False, 0, []
                
            # Get unique strategies
            strategies = set()
            for trade in trades:
                if "strategy" in trade:
                    strategies.add(trade["strategy"])
                    
            # Filter strategies if specified
            if strategy_name:
                strategies = [s for s in strategies if s == strategy_name]
                
            # Check consecutive losses for each strategy
            max_consecutive_losses = 0
            affected_strategies = []
            
            for strategy in strategies:
                # Filter trades for this strategy and sort by timestamp (newest first)
                strategy_trades = [trade for trade in trades if trade.get("strategy") == strategy]
                strategy_trades.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                # Count consecutive losses
                consecutive_losses = 0
                for trade in strategy_trades:
                    if trade.get("profit_loss", 0) < 0:
                        consecutive_losses += 1
                    else:
                        break
                        
                # Check if threshold is exceeded
                if consecutive_losses >= threshold:
                    affected_strategies.append(strategy)
                    
                # Update max consecutive losses
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                
            # Check if threshold is exceeded for any strategy
            threshold_exceeded = max_consecutive_losses >= threshold
            
            return threshold_exceeded, max_consecutive_losses, affected_strategies
        except Exception as e:
            logger.error(f"Error checking consecutive losses: {e}")
            return False, 0, []
            
    def check_win_rate_anomaly(self, strategy_name: Optional[str] = None,
                             lookback_trades: int = 10,
                             threshold: float = 30.0) -> Tuple[bool, float, List[str]]:
        """Check for win rate anomaly

        Args:
            strategy_name (Optional[str], optional): Strategy to check. Defaults to None (all strategies).
            lookback_trades (int, optional): Number of trades to look back. Defaults to 10.
            threshold (float, optional): Win rate threshold. Defaults to 30.0.

        Returns:
            Tuple[bool, float, List[str]]: (threshold_exceeded, min_win_rate, affected_strategies)
        """
        try:
            # Load trade history
            trades = self.load_trade_history()
            
            if not trades:
                return False, 0.0, []
                
            # Get unique strategies
            strategies = set()
            for trade in trades:
                if "strategy" in trade:
                    strategies.add(trade["strategy"])
                    
            # Filter strategies if specified
            if strategy_name:
                strategies = [s for s in strategies if s == strategy_name]
                
            # Check win rate for each strategy
            min_win_rate = 100.0
            affected_strategies = []
            
            for strategy in strategies:
                # Filter trades for this strategy and sort by timestamp (newest first)
                strategy_trades = [trade for trade in trades if trade.get("strategy") == strategy]
                strategy_trades.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                # Limit to lookback trades
                recent_trades = strategy_trades[:lookback_trades]
                
                if not recent_trades:
                    continue
                    
                # Count wins
                wins = sum(1 for trade in recent_trades if trade.get("profit_loss", 0) > 0)
                
                # Calculate win rate
                win_rate = (wins / len(recent_trades)) * 100
                
                # Check if threshold is exceeded
                if win_rate <= threshold:
                    affected_strategies.append(strategy)
                    
                # Update min win rate
                min_win_rate = min(min_win_rate, win_rate)
                
            # Check if threshold is exceeded for any strategy
            threshold_exceeded = min_win_rate <= threshold
            
            return threshold_exceeded, min_win_rate, affected_strategies
        except Exception as e:
            logger.error(f"Error checking win rate anomaly: {e}")
            return False, 0.0, []
            
    def check_volatility_spike(self, symbol: Optional[str] = None,
                             volatility_multiplier: float = 3.0) -> Tuple[bool, List[str]]:
        """Check for volatility spike

        Args:
            symbol (Optional[str], optional): Symbol to check. Defaults to None (all symbols).
            volatility_multiplier (float, optional): Volatility multiplier threshold. Defaults to 3.0.

        Returns:
            Tuple[bool, List[str]]: (threshold_exceeded, affected_symbols)
        """
        # This is a placeholder for actual volatility calculation
        # In a real implementation, this would use market data to calculate volatility
        return False, []
            
    def check_emergency_conditions(self) -> bool:
        """Check all emergency conditions

        Returns:
            bool: True if any emergency condition is detected, False otherwise
        """
        try:
            # Check daily drawdown
            drawdown_exceeded, drawdown = self.check_daily_drawdown()
            
            if drawdown_exceeded:
                logger.warning(f"Daily drawdown threshold exceeded: {drawdown:.2f}%")
                
                self.activate_emergency(
                    "critical", 
                    f"Daily drawdown threshold exceeded: {drawdown:.2f}%", 
                    pause_trading=True
                )
                return True
                
            # Check consecutive losses
            losses_exceeded, consecutive_losses, affected_strategies = self.check_consecutive_losses()
            
            if losses_exceeded:
                logger.warning(f"Consecutive losses threshold exceeded: {consecutive_losses} losses")
                
                self.activate_emergency(
                    "warning", 
                    f"Consecutive losses threshold exceeded: {consecutive_losses} losses", 
                    affected_strategies=affected_strategies,
                    pause_trading=False
                )
                return True
                
            # Check win rate anomaly
            win_rate_anomaly, win_rate, affected_strategies = self.check_win_rate_anomaly()
            
            if win_rate_anomaly:
                logger.warning(f"Win rate anomaly detected: {win_rate:.2f}% win rate")
                
                self.activate_emergency(
                    "caution", 
                    f"Win rate anomaly detected: {win_rate:.2f}% win rate", 
                    affected_strategies=affected_strategies,
                    pause_trading=False
                )
                return True
                
            # Check volatility spike
            volatility_spike, affected_symbols = self.check_volatility_spike()
            
            if volatility_spike:
                logger.warning(f"Volatility spike detected")
                
                self.activate_emergency(
                    "warning", 
                    f"Volatility spike detected", 
                    affected_symbols=affected_symbols,
                    pause_trading=False
                )
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error checking emergency conditions: {e}")
            return False
            
    def start_monitoring(self, interval_seconds: int = 300) -> bool:
        """Start monitoring for emergency conditions

        Args:
            interval_seconds (int, optional): Monitoring interval in seconds. Defaults to 300 (5 minutes).

        Returns:
            bool: True if monitoring started, False otherwise
        """
        try:
            # Check if monitoring is already running
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                logger.warning("Monitoring is already running.")
                return False
                
            # Reset stop event
            self.stop_monitoring.clear()
            
            # Define monitoring function
            def monitor():
                logger.info(f"Starting emergency monitoring (interval: {interval_seconds} seconds)")
                
                while not self.stop_monitoring.is_set():
                    # Check emergency conditions
                    self.check_emergency_conditions()
                    
                    # Wait for next check
                    self.stop_monitoring.wait(interval_seconds)
                    
                logger.info("Emergency monitoring stopped.")
                
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
            self.monitoring_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return False
            
    def stop_monitoring(self) -> bool:
        """Stop monitoring for emergency conditions

        Returns:
            bool: True if monitoring stopped, False otherwise
        """
        try:
            # Check if monitoring is running
            if not self.monitoring_thread or not self.monitoring_thread.is_alive():
                logger.warning("Monitoring is not running.")
                return False
                
            # Set stop event
            self.stop_monitoring.set()
            
            # Wait for thread to stop
            self.monitoring_thread.join(timeout=5.0)
            
            return not self.monitoring_thread.is_alive()
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return False
            
    def is_trading_allowed(self, strategy_name: Optional[str] = None,
                          symbol: Optional[str] = None) -> Tuple[bool, str]:
        """Check if trading is allowed

        Args:
            strategy_name (Optional[str], optional): Strategy to check. Defaults to None.
            symbol (Optional[str], optional): Symbol to check. Defaults to None.

        Returns:
            Tuple[bool, str]: (allowed, reason)
        """
        try:
            # Check if emergency is active
            if not self.emergency_state["active"]:
                return True, "No active emergency"
                
            # Check if trading is paused
            if self.emergency_state["trading_paused"]:
                return False, f"Trading paused due to {self.emergency_state['level']} emergency: {self.emergency_state['reason']}"
                
            # Check if strategy is affected
            if strategy_name and self.emergency_state["affected_strategies"]:
                if strategy_name in self.emergency_state["affected_strategies"]:
                    return False, f"Strategy {strategy_name} affected by {self.emergency_state['level']} emergency"
                    
            # Check if symbol is affected
            if symbol and self.emergency_state["affected_symbols"]:
                if symbol in self.emergency_state["affected_symbols"]:
                    return False, f"Symbol {symbol} affected by {self.emergency_state['level']} emergency"
                    
            # Trading is allowed but with caution
            return True, f"Trading allowed with caution ({self.emergency_state['level']} emergency active)"
        except Exception as e:
            logger.error(f"Error checking if trading is allowed: {e}")
            return False, f"Error checking trading status: {e}"


# Helper functions
def is_trading_allowed(strategy_name: Optional[str] = None,
                      symbol: Optional[str] = None) -> Tuple[bool, str]:
    """Check if trading is allowed (helper function)

    Args:
        strategy_name (Optional[str], optional): Strategy to check. Defaults to None.
        symbol (Optional[str], optional): Symbol to check. Defaults to None.

    Returns:
        Tuple[bool, str]: (allowed, reason)
    """
    protocol = EmergencyProtocol()
    return protocol.is_trading_allowed(strategy_name, symbol)


def activate_emergency(level: str, reason: str, 
                     affected_strategies: List[str] = None,
                     affected_symbols: List[str] = None,
                     pause_trading: bool = False) -> bool:
    """Activate emergency protocol (helper function)

    Args:
        level (str): Emergency level (caution, warning, critical, emergency)
        reason (str): Reason for the emergency
        affected_strategies (List[str], optional): Affected strategies. Defaults to None.
        affected_symbols (List[str], optional): Affected symbols. Defaults to None.
        pause_trading (bool, optional): Whether to pause trading. Defaults to False.

    Returns:
        bool: True if successful, False otherwise
    """
    protocol = EmergencyProtocol()
    return protocol.activate_emergency(level, reason, affected_strategies, affected_symbols, pause_trading)


def deactivate_emergency(reason: str = "Manual deactivation") -> bool:
    """Deactivate emergency protocol (helper function)

    Args:
        reason (str, optional): Reason for deactivation. Defaults to "Manual deactivation".

    Returns:
        bool: True if successful, False otherwise
    """
    protocol = EmergencyProtocol()
    return protocol.deactivate_emergency(reason)


def start_emergency_monitoring(interval_seconds: int = 300) -> bool:
    """Start monitoring for emergency conditions (helper function)

    Args:
        interval_seconds (int, optional): Monitoring interval in seconds. Defaults to 300 (5 minutes).

    Returns:
        bool: True if monitoring started, False otherwise
    """
    protocol = EmergencyProtocol()
    return protocol.start_monitoring(interval_seconds)


# For testing
if __name__ == "__main__":
    # Create emergency protocol
    protocol = EmergencyProtocol()
    
    # Test activating emergency
    print("Activating emergency protocol...")
    protocol.activate_emergency(
        "warning",
        "Testing emergency protocol",
        affected_strategies=["fibonacci_retracement", "support_resistance"],
        affected_symbols=["EURUSD", "GBPUSD"],
        pause_trading=False
    )
    
    # Test checking if trading is allowed
    print("\nChecking if trading is allowed...")
    allowed, reason = protocol.is_trading_allowed("fibonacci_retracement", "EURUSD")
    print(f"Trading allowed: {allowed}, Reason: {reason}")
    
    allowed, reason = protocol.is_trading_allowed("trend_following", "USDJPY")
    print(f"Trading allowed: {allowed}, Reason: {reason}")
    
    # Test updating emergency level
    print("\nUpdating emergency level...")
    protocol.update_emergency_level("critical", "Escalating emergency for testing")
    
    # Test deactivating emergency
    print("\nDeactivating emergency protocol...")
    protocol.deactivate_emergency("Testing complete")
    
    # Test starting monitoring
    print("\nStarting emergency monitoring...")
    protocol.start_monitoring(interval_seconds=10)
    
    # Wait for a few monitoring cycles
    print("Waiting for monitoring cycles...")
    time.sleep(30)
    
    # Test stopping monitoring
    print("\nStopping emergency monitoring...")
    protocol.stop_monitoring()