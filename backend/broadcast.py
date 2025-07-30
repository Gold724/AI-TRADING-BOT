import os
import sys
import json
import logging
import datetime
import threading
import time
import requests
from typing import Dict, List, Any, Optional, Callable

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, "broadcast.log")),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger("BROADCAST")

class SignalBroadcaster:
    """Broadcasts trading signals to multiple bots/accounts."""
    
    def __init__(self):
        self.subscribers = []
        self.signal_history = []
        self.history_file = os.path.join(log_dir, "signal_history.json")
        self.load_history()
        self.filters = {}
        logger.info("Signal Broadcaster initialized")
    
    def load_history(self):
        """Load signal history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.signal_history = json.load(f)
                logger.info(f"Loaded {len(self.signal_history)} signals from history")
        except Exception as e:
            logger.error(f"Error loading signal history: {str(e)}")
            self.signal_history = []
    
    def save_history(self):
        """Save signal history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.signal_history, f, indent=2)
            logger.info(f"Saved {len(self.signal_history)} signals to history")
        except Exception as e:
            logger.error(f"Error saving signal history: {str(e)}")
    
    def add_subscriber(self, subscriber_id: str, endpoint: str, broker_id: str = None, 
                      account_id: str = None, filter_func: Callable = None):
        """Add a subscriber to receive signals.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            endpoint: API endpoint to send signals to
            broker_id: Optional broker identifier for filtering
            account_id: Optional account identifier for filtering
            filter_func: Optional function to filter signals for this subscriber
        """
        subscriber = {
            "id": subscriber_id,
            "endpoint": endpoint,
            "broker_id": broker_id,
            "account_id": account_id,
            "added_at": datetime.datetime.now().isoformat()
        }
        
        self.subscribers.append(subscriber)
        
        if filter_func and callable(filter_func):
            self.filters[subscriber_id] = filter_func
        
        logger.info(f"Added subscriber: {subscriber_id} for broker {broker_id} and account {account_id}")
        return True
    
    def remove_subscriber(self, subscriber_id: str):
        """Remove a subscriber."""
        for i, subscriber in enumerate(self.subscribers):
            if subscriber["id"] == subscriber_id:
                self.subscribers.pop(i)
                if subscriber_id in self.filters:
                    del self.filters[subscriber_id]
                logger.info(f"Removed subscriber: {subscriber_id}")
                return True
        
        logger.warning(f"Subscriber not found: {subscriber_id}")
        return False
    
    def broadcast_signal(self, signal: Dict[str, Any], source: str = "manual"):
        """Broadcast a signal to all subscribers.
        
        Args:
            signal: The trading signal to broadcast
            source: Source of the signal (e.g., "manual", "strategy", "webhook")
        """
        if not signal or not isinstance(signal, dict):
            logger.error("Invalid signal format")
            return False
        
        # Add metadata to signal
        signal_with_meta = signal.copy()
        signal_with_meta["broadcast_time"] = datetime.datetime.now().isoformat()
        signal_with_meta["source"] = source
        signal_with_meta["broadcast_id"] = f"bcast-{int(time.time())}-{len(self.signal_history) + 1}"
        
        # Add to history
        self.signal_history.append(signal_with_meta)
        self.save_history()
        
        # Track successful deliveries
        successful_deliveries = 0
        failed_deliveries = 0
        
        # Broadcast to each subscriber
        threads = []
        for subscriber in self.subscribers:
            # Check if signal passes filter for this subscriber
            subscriber_id = subscriber["id"]
            if subscriber_id in self.filters and not self.filters[subscriber_id](signal):
                logger.info(f"Signal filtered out for subscriber {subscriber_id}")
                continue
            
            # Create a thread for each delivery
            thread = threading.Thread(
                target=self._deliver_signal,
                args=(signal_with_meta, subscriber, successful_deliveries, failed_deliveries)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all deliveries to complete
        for thread in threads:
            thread.join(timeout=10.0)  # 10 second timeout
        
        logger.info(f"Signal broadcast complete: {successful_deliveries} successful, {failed_deliveries} failed")
        return successful_deliveries > 0
    
    def _deliver_signal(self, signal: Dict[str, Any], subscriber: Dict[str, Any], 
                       successful_deliveries: int, failed_deliveries: int):
        """Deliver a signal to a specific subscriber."""
        try:
            # Prepare signal for this subscriber
            delivery_signal = signal.copy()
            
            # Add subscriber-specific fields
            if subscriber.get("broker_id"):
                delivery_signal["broker_id"] = subscriber["broker_id"]
            
            if subscriber.get("account_id"):
                delivery_signal["account_id"] = subscriber["account_id"]
            
            # Send the signal
            response = requests.post(
                subscriber["endpoint"],
                json=delivery_signal,
                headers={"Content-Type": "application/json"},
                timeout=5.0  # 5 second timeout
            )
            
            if response.status_code in (200, 201, 202):
                logger.info(f"Signal delivered to {subscriber['id']}")
                successful_deliveries += 1
            else:
                logger.error(f"Failed to deliver signal to {subscriber['id']}: {response.status_code} {response.text}")
                failed_deliveries += 1
        
        except Exception as e:
            logger.error(f"Error delivering signal to {subscriber['id']}: {str(e)}")
            failed_deliveries += 1
    
    def get_signal_history(self, limit: int = 50, filter_func: Callable = None):
        """Get signal broadcast history.
        
        Args:
            limit: Maximum number of signals to return
            filter_func: Optional function to filter signals
        """
        if filter_func and callable(filter_func):
            filtered_history = [signal for signal in self.signal_history if filter_func(signal)]
            return filtered_history[-limit:] if limit > 0 else filtered_history
        else:
            return self.signal_history[-limit:] if limit > 0 else self.signal_history
    
    def get_subscribers(self):
        """Get list of current subscribers."""
        return self.subscribers

# Create a global instance of the broadcaster
broadcaster = SignalBroadcaster()

# Example filter functions
def filter_by_symbol(signal: Dict[str, Any], symbols: List[str]):
    """Filter signals by symbol."""
    return signal.get("symbol") in symbols

def filter_by_side(signal: Dict[str, Any], sides: List[str]):
    """Filter signals by side (buy/sell)."""
    return signal.get("side") in sides

def filter_by_min_quantity(signal: Dict[str, Any], min_quantity: float):
    """Filter signals by minimum quantity."""
    return signal.get("quantity", 0) >= min_quantity

# Create combined filters
def create_filter(filter_config: Dict[str, Any]):
    """Create a filter function from a configuration dictionary."""
    def filter_func(signal):
        # Symbol filter
        if "symbols" in filter_config and signal.get("symbol") not in filter_config["symbols"]:
            return False
        
        # Side filter
        if "sides" in filter_config and signal.get("side") not in filter_config["sides"]:
            return False
        
        # Min quantity filter
        if "min_quantity" in filter_config and signal.get("quantity", 0) < filter_config["min_quantity"]:
            return False
        
        # Max quantity filter
        if "max_quantity" in filter_config and signal.get("quantity", 0) > filter_config["max_quantity"]:
            return False
        
        # Source filter
        if "sources" in filter_config and signal.get("source") not in filter_config["sources"]:
            return False
        
        # Custom filter function
        if "custom_filter" in filter_config and callable(filter_config["custom_filter"]):
            return filter_config["custom_filter"](signal)
        
        # All filters passed
        return True
    
    return filter_func