# O.R.I.G.I.N. Cloud Prime - Signal Broadcasting Module
# Distributes trading signals to multiple brokers and accounts

import os
import json
import time
import logging
import uuid
import threading
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/signal_broadcasting.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("signal_broadcaster")

class SignalBroadcaster:
    """Manages signal broadcasting to multiple brokers and accounts"""
    
    def __init__(self, 
                 history_file: str = "signal_history.json",
                 subscribers_file: str = "subscribers.json",
                 request_timeout: int = 10):
        """Initialize the signal broadcaster
        
        Args:
            history_file: Path to the signal history file
            subscribers_file: Path to the subscribers file
            request_timeout: Timeout for signal delivery requests in seconds
        """
        self.history_file = history_file
        self.subscribers_file = subscribers_file
        self.request_timeout = request_timeout
        
        # Load signal history and subscribers
        self.signal_history = self._load_signal_history()
        self.subscribers = self._load_subscribers()
        
        logger.info(f"Signal Broadcaster initialized with {len(self.subscribers)} subscribers")
    
    def _load_signal_history(self) -> List[Dict[str, Any]]:
        """Load the signal history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading signal history: {str(e)}")
            return []
    
    def _save_signal_history(self) -> bool:
        """Save the signal history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.signal_history, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving signal history: {str(e)}")
            return False
    
    def _load_subscribers(self) -> List[Dict[str, Any]]:
        """Load the subscribers from file"""
        try:
            if os.path.exists(self.subscribers_file):
                with open(self.subscribers_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading subscribers: {str(e)}")
            return []
    
    def _save_subscribers(self) -> bool:
        """Save the subscribers to file"""
        try:
            with open(self.subscribers_file, 'w') as f:
                json.dump(self.subscribers, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving subscribers: {str(e)}")
            return False
    
    def add_subscriber(self, subscriber: Dict[str, Any]) -> bool:
        """Add a new subscriber
        
        Args:
            subscriber: Dictionary with subscriber details including:
                - id: Unique identifier
                - name: Display name
                - endpoint: URL to receive signals
                - broker_id: Broker identifier
                - account_id: Account identifier
                - filters: Optional signal filters
                
        Returns:
            Success status
        """
        try:
            # Ensure required fields
            required_fields = ["id", "name", "endpoint", "broker_id"]
            for field in required_fields:
                if field not in subscriber:
                    logger.error(f"Missing required field '{field}' in subscriber")
                    return False
            
            # Check if subscriber already exists
            for existing in self.subscribers:
                if existing["id"] == subscriber["id"]:
                    logger.warning(f"Subscriber with ID {subscriber['id']} already exists, updating")
                    existing.update(subscriber)
                    self._save_subscribers()
                    return True
            
            # Add new subscriber
            self.subscribers.append(subscriber)
            self._save_subscribers()
            logger.info(f"Added new subscriber: {subscriber['name']} ({subscriber['broker_id']})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding subscriber: {str(e)}")
            return False
    
    def remove_subscriber(self, subscriber_id: str) -> bool:
        """Remove a subscriber
        
        Args:
            subscriber_id: Unique identifier of the subscriber
            
        Returns:
            Success status
        """
        try:
            initial_count = len(self.subscribers)
            self.subscribers = [s for s in self.subscribers if s["id"] != subscriber_id]
            
            if len(self.subscribers) < initial_count:
                self._save_subscribers()
                logger.info(f"Removed subscriber with ID {subscriber_id}")
                return True
            else:
                logger.warning(f"Subscriber with ID {subscriber_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error removing subscriber: {str(e)}")
            return False
    
    def broadcast_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast a signal to all subscribers
        
        Args:
            signal: Dictionary with signal details
            
        Returns:
            Dictionary with broadcast results
        """
        try:
            # Add metadata to the signal
            signal_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            enriched_signal = signal.copy()
            enriched_signal.update({
                "id": signal_id,
                "timestamp": timestamp,
                "source": signal.get("source", "unknown")
            })
            
            # Add to history
            self.signal_history.append(enriched_signal)
            self._save_signal_history()
            
            # Prepare for broadcasting
            results = {
                "signal_id": signal_id,
                "timestamp": timestamp,
                "total_subscribers": len(self.subscribers),
                "successful": 0,
                "failed": 0,
                "filtered": 0,
                "details": []
            }
            
            # Broadcast to each subscriber in parallel
            threads = []
            for subscriber in self.subscribers:
                # Check if signal passes subscriber's filters
                if "filters" in subscriber and not self._passes_filters(enriched_signal, subscriber["filters"]):
                    results["filtered"] += 1
                    results["details"].append({
                        "subscriber_id": subscriber["id"],
                        "status": "filtered",
                        "reason": "Signal did not pass filters"
                    })
                    continue
                
                # Create thread for delivery
                thread = threading.Thread(
                    target=self._deliver_signal,
                    args=(enriched_signal, subscriber, results)
                )
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete with timeout
            for thread in threads:
                thread.join(timeout=self.request_timeout + 2)  # Add buffer to the timeout
            
            logger.info(f"Signal {signal_id} broadcast complete: {results['successful']} successful, {results['failed']} failed, {results['filtered']} filtered")
            return results
            
        except Exception as e:
            logger.error(f"Error broadcasting signal: {str(e)}")
            return {
                "error": str(e),
                "successful": 0,
                "failed": 0,
                "filtered": 0
            }
    
    def _deliver_signal(self, signal: Dict[str, Any], subscriber: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Deliver a signal to a specific subscriber
        
        Args:
            signal: The signal to deliver
            subscriber: The subscriber to deliver to
            results: Dictionary to update with results
        """
        try:
            # Prepare signal for this specific subscriber
            delivery_signal = signal.copy()
            
            # Add subscriber-specific fields
            if "account_id" in subscriber:
                delivery_signal["account_id"] = subscriber["account_id"]
            delivery_signal["broker_id"] = subscriber["broker_id"]
            
            # Send the signal
            response = requests.post(
                subscriber["endpoint"],
                json=delivery_signal,
                timeout=self.request_timeout
            )
            
            # Process response
            detail = {
                "subscriber_id": subscriber["id"],
                "broker_id": subscriber["broker_id"],
                "timestamp": datetime.now().isoformat()
            }
            
            if response.status_code >= 200 and response.status_code < 300:
                detail["status"] = "success"
                detail["response_code"] = response.status_code
                with threading.Lock():
                    results["successful"] += 1
                    results["details"].append(detail)
                logger.info(f"Signal delivered successfully to {subscriber['name']} ({subscriber['broker_id']})")
            else:
                detail["status"] = "failed"
                detail["response_code"] = response.status_code
                detail["error"] = response.text[:200]  # Limit error text length
                with threading.Lock():
                    results["failed"] += 1
                    results["details"].append(detail)
                logger.error(f"Failed to deliver signal to {subscriber['name']} ({subscriber['broker_id']}): {response.status_code}")
                
        except requests.RequestException as e:
            detail = {
                "subscriber_id": subscriber["id"],
                "broker_id": subscriber["broker_id"],
                "status": "failed",
                "error": str(e)[:200],  # Limit error text length
                "timestamp": datetime.now().isoformat()
            }
            with threading.Lock():
                results["failed"] += 1
                results["details"].append(detail)
            logger.error(f"Request error delivering signal to {subscriber['name']} ({subscriber['broker_id']}): {str(e)}")
            
        except Exception as e:
            detail = {
                "subscriber_id": subscriber["id"],
                "broker_id": subscriber["broker_id"],
                "status": "failed",
                "error": str(e)[:200],  # Limit error text length
                "timestamp": datetime.now().isoformat()
            }
            with threading.Lock():
                results["failed"] += 1
                results["details"].append(detail)
            logger.error(f"Error delivering signal to {subscriber['name']} ({subscriber['broker_id']}): {str(e)}")
    
    def _passes_filters(self, signal: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if a signal passes the subscriber's filters
        
        Args:
            signal: The signal to check
            filters: Dictionary of filters to apply
            
        Returns:
            True if the signal passes all filters, False otherwise
        """
        try:
            # Symbol filter
            if "symbols" in filters and signal.get("symbol") not in filters["symbols"]:
                return False
            
            # Side filter (buy/sell)
            if "sides" in filters and signal.get("side") not in filters["sides"]:
                return False
            
            # Quantity filter
            if "min_quantity" in filters and signal.get("quantity", 0) < filters["min_quantity"]:
                return False
            if "max_quantity" in filters and signal.get("quantity", 0) > filters["max_quantity"]:
                return False
            
            # Source filter
            if "sources" in filters and signal.get("source") not in filters["sources"]:
                return False
            
            # Custom filter function (for advanced filtering)
            if "custom_filter" in filters and callable(filters["custom_filter"]):
                return filters["custom_filter"](signal)
            
            # All filters passed
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            return False  # Fail closed for safety
    
    def get_signal_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the signal broadcast history
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of historical signals
        """
        return self.signal_history[-limit:] if limit > 0 else self.signal_history.copy()
    
    def get_subscribers(self) -> List[Dict[str, Any]]:
        """Get the list of subscribers
        
        Returns:
            List of subscribers
        """
        return self.subscribers.copy()

# Helper functions for creating filters
def filter_by_symbol(symbols: List[str]):
    """Create a filter function for specific symbols"""
    return lambda signal: signal.get("symbol") in symbols

def filter_by_side(sides: List[str]):
    """Create a filter function for specific sides (buy/sell)"""
    return lambda signal: signal.get("side") in sides

def filter_by_min_quantity(min_quantity: float):
    """Create a filter function for minimum quantity"""
    return lambda signal: signal.get("quantity", 0) >= min_quantity

def filter_by_max_quantity(max_quantity: float):
    """Create a filter function for maximum quantity"""
    return lambda signal: signal.get("quantity", 0) <= max_quantity

def filter_by_source(sources: List[str]):
    """Create a filter function for specific signal sources"""
    return lambda signal: signal.get("source") in sources

def create_filter(filter_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a filter dictionary from a configuration
    
    Args:
        filter_config: Dictionary with filter configuration
        
    Returns:
        Filter dictionary
    """
    filters = {}
    
    if "symbols" in filter_config:
        filters["symbols"] = filter_config["symbols"]
    
    if "sides" in filter_config:
        filters["sides"] = filter_config["sides"]
    
    if "min_quantity" in filter_config:
        filters["min_quantity"] = filter_config["min_quantity"]
    
    if "max_quantity" in filter_config:
        filters["max_quantity"] = filter_config["max_quantity"]
    
    if "sources" in filter_config:
        filters["sources"] = filter_config["sources"]
    
    if "custom" in filter_config and callable(filter_config["custom"]):
        filters["custom_filter"] = filter_config["custom"]
    
    return filters

# Create a global instance
signal_broadcaster = SignalBroadcaster()