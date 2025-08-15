# news_guard.py

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set

# Try to import the NewsAwareFilter from news_filter.py
try:
    from news_filter import NewsAwareFilter
except ImportError:
    # Define a minimal version if the import fails
    class NewsAwareFilter:
        def is_safe_to_trade(self, pair):
            return True, None
        
        def get_event_risk(self, pair):
            return "none"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("news_guard")

# Constants
NEWS_DATA_FILE = os.path.join("data", "forex_news.json")
AFFECTED_PAIRS_FILE = os.path.join("data", "affected_pairs.json")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)


class NewsGuard:
    """Real-time monitor for high-impact economic news events"""

    def __init__(self, news_data_file: str = NEWS_DATA_FILE, 
                 affected_pairs_file: str = AFFECTED_PAIRS_FILE,
                 window_minutes: int = 60):
        """Initialize the news guard

        Args:
            news_data_file (str): Path to the news data file
            affected_pairs_file (str): Path to store affected pairs
            window_minutes (int): Time window to monitor (in minutes)
        """
        self.news_data_file = news_data_file
        self.affected_pairs_file = affected_pairs_file
        self.window_minutes = window_minutes
        self.news_filter = NewsAwareFilter(news_data_file)
        self.affected_pairs = self.load_affected_pairs()
        
    def load_affected_pairs(self) -> Dict[str, List[Dict]]:
        """Load affected pairs from file or create empty dict

        Returns:
            Dict[str, List[Dict]]: Dictionary of affected pairs and their events
        """
        try:
            if os.path.exists(self.affected_pairs_file):
                with open(self.affected_pairs_file, "r") as f:
                    return json.load(f)
            else:
                logger.info(f"Affected pairs file {self.affected_pairs_file} not found. Creating new file.")
                return {}
        except Exception as e:
            logger.error(f"Error loading affected pairs: {e}")
            return {}

    def save_affected_pairs(self) -> bool:
        """Save affected pairs to file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.affected_pairs_file, "w") as f:
                json.dump(self.affected_pairs, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving affected pairs: {e}")
            return False

    def get_upcoming_news(self) -> List[Dict]:
        """Get upcoming news events within the specified window

        Returns:
            List[Dict]: List of upcoming news events
        """
        try:
            # Load news data
            if os.path.exists(self.news_data_file):
                with open(self.news_data_file, "r") as f:
                    news_events = json.load(f)
            else:
                logger.warning(f"News data file {self.news_data_file} not found.")
                return []
                
            # Current time in UTC
            now = datetime.utcnow()
            
            # Filter for upcoming events within the window
            upcoming_events = []
            for event in news_events:
                try:
                    event_time = datetime.fromisoformat(event.get("datetime", ""))
                    time_diff = (event_time - now).total_seconds() / 60  # Convert to minutes
                    
                    # Include events within the window and high/medium impact
                    if 0 <= time_diff <= self.window_minutes and event.get("impact", "").lower() in ["high", "medium"]:
                        # Add time difference for easier processing
                        event["minutes_until"] = time_diff
                        upcoming_events.append(event)
                except (ValueError, TypeError):
                    continue
                    
            return upcoming_events
        except Exception as e:
            logger.error(f"Error getting upcoming news: {e}")
            return []

    def get_affected_currencies(self) -> Set[str]:
        """Get currencies affected by upcoming high-impact news

        Returns:
            Set[str]: Set of affected currency codes
        """
        upcoming_events = self.get_upcoming_news()
        affected_currencies = set()
        
        for event in upcoming_events:
            if event.get("impact", "").lower() == "high":
                currency = event.get("currency")
                if currency:
                    affected_currencies.add(currency)
                    
        return affected_currencies

    def get_affected_pairs(self, base_pairs: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Get trading pairs affected by upcoming news events

        Args:
            base_pairs (Optional[List[str]]): List of pairs to check. If None, uses common forex pairs.

        Returns:
            Dict[str, List[Dict]]: Dictionary of affected pairs and their events
        """
        if base_pairs is None:
            # Common forex pairs
            base_pairs = [
                "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
                "EURGBP", "EURJPY", "GBPJPY", "XAUUSD", "XAGUSD"
            ]
            
        affected_currencies = self.get_affected_currencies()
        affected_pairs = {}
        upcoming_events = self.get_upcoming_news()
        
        for pair in base_pairs:
            if len(pair) < 6:
                continue
                
            # Extract base and quote currencies
            base, quote = pair[:3], pair[3:]
            
            # Check if either currency is affected
            if base in affected_currencies or quote in affected_currencies:
                # Find relevant events
                relevant_events = []
                for event in upcoming_events:
                    if event.get("impact", "").lower() == "high" and event.get("currency") in [base, quote]:
                        relevant_events.append({
                            "title": event.get("title", "Unknown Event"),
                            "currency": event.get("currency", ""),
                            "impact": event.get("impact", "high"),
                            "datetime": event.get("datetime", ""),
                            "minutes_until": event.get("minutes_until", 0)
                        })
                        
                if relevant_events:
                    affected_pairs[pair] = relevant_events
                    
        # Update and save affected pairs
        self.affected_pairs = affected_pairs
        self.save_affected_pairs()
        
        return affected_pairs

    def should_modify_trade(self, pair: str) -> Tuple[bool, str, float]:
        """Determine if a trade should be modified based on upcoming news

        Args:
            pair (str): Currency pair to check

        Returns:
            Tuple[bool, str, float]: (should_modify, reason, risk_multiplier)
        """
        # Update affected pairs
        self.get_affected_pairs()
        
        # Check if pair is affected
        if pair in self.affected_pairs:
            events = self.affected_pairs[pair]
            if not events:
                return False, "", 1.0
                
            # Sort events by time
            events.sort(key=lambda x: x.get("minutes_until", 0))
            next_event = events[0]
            
            minutes_until = next_event.get("minutes_until", 0)
            event_title = next_event.get("title", "Unknown Event")
            event_currency = next_event.get("currency", "")
            
            # Determine risk multiplier based on time until event
            if minutes_until <= 15:
                # Very close to event - reduce size by 75%
                risk_multiplier = 0.25
                reason = f"High-impact {event_currency} news '{event_title}' in {minutes_until:.0f} minutes"
            elif minutes_until <= 30:
                # Close to event - reduce size by 50%
                risk_multiplier = 0.5
                reason = f"High-impact {event_currency} news '{event_title}' in {minutes_until:.0f} minutes"
            else:
                # Further away - reduce size by 25%
                risk_multiplier = 0.75
                reason = f"High-impact {event_currency} news '{event_title}' in {minutes_until:.0f} minutes"
                
            return True, reason, risk_multiplier
            
        return False, "", 1.0

    def monitor_news(self, callback=None, interval_seconds: int = 300) -> None:
        """Continuously monitor for upcoming news events

        Args:
            callback: Function to call when affected pairs change
            interval_seconds (int): Interval between checks in seconds
        """
        logger.info(f"Starting news monitoring with {self.window_minutes} minute window")
        
        try:
            while True:
                # Get affected pairs
                previous_affected = set(self.affected_pairs.keys())
                current_affected = set(self.get_affected_pairs().keys())
                
                # Check for changes
                if previous_affected != current_affected:
                    new_affected = current_affected - previous_affected
                    no_longer_affected = previous_affected - current_affected
                    
                    if new_affected:
                        logger.info(f"Newly affected pairs: {', '.join(new_affected)}")
                    if no_longer_affected:
                        logger.info(f"No longer affected pairs: {', '.join(no_longer_affected)}")
                        
                    # Call callback if provided
                    if callback and callable(callback):
                        callback(self.affected_pairs)
                        
                # Log current status
                if current_affected:
                    logger.info(f"Currently affected pairs: {', '.join(current_affected)}")
                else:
                    logger.info("No pairs currently affected by high-impact news")
                    
                # Sleep until next check
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("News monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in news monitoring: {e}")


# Helper functions
def get_affected_pairs() -> Dict[str, List[Dict]]:
    """Get trading pairs affected by upcoming news events (helper function)

    Returns:
        Dict[str, List[Dict]]: Dictionary of affected pairs and their events
    """
    news_guard = NewsGuard()
    return news_guard.get_affected_pairs()


def should_modify_trade(pair: str) -> Tuple[bool, str, float]:
    """Determine if a trade should be modified based on upcoming news (helper function)

    Args:
        pair (str): Currency pair to check

    Returns:
        Tuple[bool, str, float]: (should_modify, reason, risk_multiplier)
    """
    news_guard = NewsGuard()
    return news_guard.should_modify_trade(pair)


def start_news_monitor(callback=None, interval_seconds: int = 300) -> None:
    """Start monitoring for upcoming news events (helper function)

    Args:
        callback: Function to call when affected pairs change
        interval_seconds (int): Interval between checks in seconds
    """
    news_guard = NewsGuard()
    news_guard.monitor_news(callback, interval_seconds)


# Integration with main trade loop
def apply_news_guard_to_trade(trade_signal: Dict) -> Dict:
    """Apply news guard logic to a trade signal

    Args:
        trade_signal (Dict): The original trade signal

    Returns:
        Dict: Modified trade signal with news guard applied
    """
    # Extract the symbol from the trade signal
    symbol = trade_signal.get("symbol", "")
    if not symbol:
        return trade_signal
        
    # Check if trade should be modified
    should_modify, reason, risk_multiplier = should_modify_trade(symbol)
    
    if should_modify:
        # Modify the trade signal
        original_lot_size = trade_signal.get("lot_size", 0.01)
        adjusted_lot_size = original_lot_size * risk_multiplier
        
        # Update the trade signal
        trade_signal["original_lot_size"] = original_lot_size
        trade_signal["lot_size"] = adjusted_lot_size
        trade_signal["news_guard_applied"] = True
        trade_signal["news_guard_reason"] = reason
        trade_signal["news_guard_multiplier"] = risk_multiplier
        
        logger.info(f"News Guard applied to {symbol}: {reason}")
        logger.info(f"Adjusted lot size from {original_lot_size} to {adjusted_lot_size}")
    
    return trade_signal


# For testing
if __name__ == "__main__":
    print("=== News Guard Test ===\n")
    
    # Create an instance of the news guard
    news_guard = NewsGuard()
    
    # Get upcoming news events
    upcoming_news = news_guard.get_upcoming_news()
    print(f"Found {len(upcoming_news)} upcoming high/medium impact news events in the next {news_guard.window_minutes} minutes")
    
    for event in upcoming_news:
        print(f"\n{event.get('title', 'Unknown Event')}:")
        print(f"  Currency: {event.get('currency', 'Unknown')}")
        print(f"  Impact: {event.get('impact', 'Unknown')}")
        print(f"  Time: {event.get('datetime', 'Unknown')}")
        print(f"  Minutes until: {event.get('minutes_until', 0):.1f}")
    
    # Get affected pairs
    affected_pairs = news_guard.get_affected_pairs()
    print(f"\nAffected pairs: {', '.join(affected_pairs.keys()) if affected_pairs else 'None'}")
    
    # Test trade modification
    test_pairs = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    print("\nTesting trade modification:")
    
    for pair in test_pairs:
        should_modify, reason, multiplier = news_guard.should_modify_trade(pair)
        print(f"\n{pair}:")
        if should_modify:
            print(f"  Should modify: Yes")
            print(f"  Reason: {reason}")
            print(f"  Risk multiplier: {multiplier}")
            
            # Test trade signal modification
            test_signal = {"symbol": pair, "lot_size": 0.1}
            modified_signal = apply_news_guard_to_trade(test_signal)
            print(f"  Original lot size: {test_signal['lot_size']}")
            print(f"  Modified lot size: {modified_signal['lot_size']}")
        else:
            print(f"  Should modify: No")
    
    print("\n=== Test Complete ===")