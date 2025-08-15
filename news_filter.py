# news_filter.py

import json
import logging
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("news_filter")

# Load environment variables
load_dotenv()

# Constants
NEWS_DATA_FILE = os.path.join("data", "forex_news.json")
BANNED_PERIODS_FILE = os.path.join("data", "banned_periods.json")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)


class NewsAwareFilter:
    """Filter for avoiding trades during high-impact economic news events"""

    def __init__(self, news_data_file: str = NEWS_DATA_FILE):
        """Initialize the news filter

        Args:
            news_data_file (str): Path to the news data file
        """
        self.news_data_file = news_data_file
        self.news_events = self.fetch_news()

    def fetch_news(self) -> List[Dict]:
        """Fetch economic news events from file or default to empty list

        Returns:
            List[Dict]: List of news events
        """
        try:
            if os.path.exists(self.news_data_file):
                with open(self.news_data_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"News data file {self.news_data_file} not found.")
                return []
        except Exception as e:
            logger.error(f"Error loading news data: {e}")
            return []

    def is_safe_to_trade(self, pair: str) -> Tuple[bool, Optional[str]]:
        """Check if it's safe to trade a currency pair based on upcoming news

        Args:
            pair (str): Currency pair (e.g., 'EURUSD')

        Returns:
            Tuple[bool, Optional[str]]: (is_safe, reason_if_not_safe)
        """
        if not pair or len(pair) < 6:
            return False, "Invalid currency pair"

        # Extract base and quote currencies
        base, quote = pair[:3], pair[3:]
        
        # Current time in UTC
        now = datetime.utcnow()
        
        # Check each news event
        for event in self.news_events:
            # Skip if not high impact or not related to our pair
            if event.get("impact", "").lower() != "high":
                continue
                
            if event.get("currency") not in [base, quote]:
                continue
                
            # Parse event time
            try:
                event_time = datetime.fromisoformat(event.get("datetime", ""))
            except (ValueError, TypeError):
                continue
                
            # Check if event is within ±30 minutes of current time
            time_diff = abs((event_time - now).total_seconds())
            if time_diff < 1800:  # 30 minutes in seconds
                return False, f"High-impact {event.get('currency')} news: {event.get('title')} at {event_time.strftime('%H:%M UTC')}"
        
        return True, None

    def get_event_risk(self, pair: str) -> str:
        """Get the risk level for a currency pair based on upcoming news
        
        Args:
            pair (str): Currency pair (e.g., 'EURUSD')
            
        Returns:
            str: Risk level ('high', 'medium', 'low', or 'none')
        """
        if not pair or len(pair) < 6:
            return "unknown"
            
        # Extract base and quote currencies
        base, quote = pair[:3], pair[3:]
        
        # Current time in UTC
        now = datetime.utcnow()
        
        highest_risk = "none"
        
        # Check each news event
        for event in self.news_events:
            # Skip if not related to our pair
            if event.get("currency") not in [base, quote]:
                continue
                
            # Parse event time
            try:
                event_time = datetime.fromisoformat(event.get("datetime", ""))
            except (ValueError, TypeError):
                continue
                
            # Check if event is within ±60 minutes of current time
            time_diff = abs((event_time - now).total_seconds())
            if time_diff < 3600:  # 60 minutes in seconds
                impact = event.get("impact", "").lower()
                if impact == "high" and highest_risk != "high":
                    highest_risk = "high"
                elif impact == "medium" and highest_risk not in ["high"]:
                    highest_risk = "medium"
                elif impact == "low" and highest_risk == "none":
                    highest_risk = "low"
        
        return highest_risk
        
    def get_dynamic_lot_size(self, pair: str, base_lot: float) -> float:
        """Calculate adjusted lot size based on news risk
        
        Args:
            pair (str): Currency pair (e.g., 'EURUSD')
            base_lot (float): Base lot size
            
        Returns:
            float: Adjusted lot size based on news risk
        """
        risk_level = self.get_event_risk(pair)
        
        # Apply risk multipliers based on configuration
        if risk_level == "high":
            return base_lot * 0.25  # Reduce to 25% for high-impact news
        elif risk_level == "medium":
            return base_lot * 0.5   # Reduce to 50% for medium-impact news
        else:
            return base_lot          # No reduction for low/no impact
            
    def get_dynamic_contract_size(self, symbol: str, base_contracts: float) -> float:
        """Calculate adjusted contract size for futures trading based on news risk
        
        Args:
            symbol (str): Trading symbol (e.g., 'XAUUSD' for Gold)
            base_contracts (float): Base number of contracts
            
        Returns:
            float: Adjusted contract size based on news risk
        """
        # For gold futures, we need to check USD news impact
        risk_level = self.get_event_risk("XAUUSD")
        
        # Apply risk multipliers based on configuration
        if risk_level == "high":
            return base_contracts * 0.25  # Reduce to 25% for high-impact news
        elif risk_level == "medium":
            return base_contracts * 0.5   # Reduce to 50% for medium-impact news
        else:
            return base_contracts          # No reduction for low/no impact


# Helper functions that create a new instance of NewsAwareFilter
def get_dynamic_lot_size(pair: str, base_lot: float) -> float:
    """Adjust lot size based on news risk level (helper function)

    Args:
        pair (str): Currency pair (e.g., 'EURUSD')
        base_lot (float): Base lot size

    Returns:
        float: Adjusted lot size
    """
    # Create a new instance and use the class method
    return NewsAwareFilter().get_dynamic_lot_size(pair, base_lot)


def get_dynamic_contract_size(symbol: str, base_contracts: float) -> float:
    """Adjust contract size for futures trading based on news risk level (helper function)

    Args:
        symbol (str): Trading symbol (e.g., 'XAUUSD' for Gold)
        base_contracts (float): Base number of contracts

    Returns:
        float: Adjusted contract size
    """
    # Create a new instance and use the class method
    return NewsAwareFilter().get_dynamic_contract_size(symbol, base_contracts)


def update_banned_periods():
    """Update banned trading periods based on high-impact news events"""
    try:
        news_filter = NewsAwareFilter()
        banned_periods = []
        
        # Get current time
        now = datetime.utcnow()
        
        # Process each high-impact news event
        for event in news_filter.news_events:
            if event.get("impact", "").lower() != "high":
                continue
                
            try:
                event_time = datetime.fromisoformat(event.get("datetime", ""))
            except (ValueError, TypeError):
                continue
                
            # Only include future events or very recent ones
            if event_time < now - timedelta(minutes=30):
                continue
                
            # Create a banned period (±30 minutes around the event)
            banned_period = {
                "currency": event.get("currency"),
                "title": event.get("title"),
                "impact": event.get("impact"),
                "start": (event_time - timedelta(minutes=30)).isoformat(),
                "end": (event_time + timedelta(minutes=30)).isoformat()
            }
            
            banned_periods.append(banned_period)
        
        # Save to file
        with open(BANNED_PERIODS_FILE, "w") as f:
            json.dump(banned_periods, f, indent=2)
            
        logger.info(f"Updated banned periods with {len(banned_periods)} entries")
        return True
    except Exception as e:
        logger.error(f"Error updating banned periods: {e}")
        return False


# For testing
if __name__ == "__main__":
    # Create a test news event (current time ±15 minutes)
    now = datetime.utcnow()
    test_events = [
        {
            "title": "US Non-Farm Payrolls",
            "currency": "USD",
            "impact": "high",
            "datetime": (now + timedelta(minutes=15)).isoformat()
        },
        {
            "title": "ECB Interest Rate Decision",
            "currency": "EUR",
            "impact": "high",
            "datetime": (now + timedelta(hours=2)).isoformat()
        }
    ]
    
    # Save test events
    os.makedirs("data", exist_ok=True)
    with open(NEWS_DATA_FILE, "w") as f:
        json.dump(test_events, f, indent=2)
    
    # Test the filter
    news_filter = NewsAwareFilter()
    
    # Test pairs
    test_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    
    for pair in test_pairs:
        is_safe, reason = news_filter.is_safe_to_trade(pair)
        risk = news_filter.get_event_risk(pair)
        adjusted_lot = get_dynamic_lot_size(pair, 0.01)
        
        print(f"Pair: {pair}")
        print(f"  Safe to trade: {is_safe}")
        if not is_safe:
            print(f"  Reason: {reason}")
        print(f"  Risk level: {risk}")
        print(f"  Adjusted lot size (from 0.01): {adjusted_lot}")
        print()
    
    # Update banned periods
    update_banned_periods()
    print(f"Banned periods updated and saved to {BANNED_PERIODS_FILE}")