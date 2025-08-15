# ai_components/news_guard.py

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Union
import requests
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_components.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("news_guard")

# Constants
NEWS_DATA_FILE = os.path.join("data", "forex_news.json")
NEWS_CONFIG_FILE = os.path.join("config", "news_config.json")

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)


class NewsGuard:
    """AI-enhanced news monitoring and impact assessment for trading"""
    
    def __init__(self, news_data_file: str = NEWS_DATA_FILE, 
                 news_config_file: str = NEWS_CONFIG_FILE,
                 window_minutes: int = 60):
        """Initialize the news guard
        
        Args:
            news_data_file (str): Path to the news data file
            news_config_file (str): Path to the news configuration file
            window_minutes (int): Time window in minutes to check for upcoming news
        """
        self.news_data_file = news_data_file
        self.news_config_file = news_config_file
        self.window_minutes = window_minutes
        self.news_config = self.load_news_config()
        self.news_data = self.load_news_data()
        self.currency_pairs = self._generate_currency_pairs()
    
    def load_news_config(self) -> Dict:
        """Load news configuration from file
        
        Returns:
            Dict: News configuration
        """
        default_config = {
            "impact_levels": {
                "high": {
                    "avoid_minutes_before": 30,
                    "avoid_minutes_after": 30,
                    "risk_multiplier": 0.5
                },
                "medium": {
                    "avoid_minutes_before": 15,
                    "avoid_minutes_after": 15,
                    "risk_multiplier": 0.75
                },
                "low": {
                    "avoid_minutes_before": 5,
                    "avoid_minutes_after": 5,
                    "risk_multiplier": 0.9
                }
            },
            "currency_impact": {
                "USD": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "XAUUSD"],
                "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD"],
                "GBP": ["GBPUSD", "EURGBP", "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD"],
                "JPY": ["USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "CADJPY", "NZDJPY"],
                "CHF": ["USDCHF", "EURCHF", "GBPCHF", "CHFJPY", "AUDCHF", "CADCHF", "NZDCHF"],
                "AUD": ["AUDUSD", "EURAUD", "GBPAUD", "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD"],
                "CAD": ["USDCAD", "EURCAD", "GBPCAD", "CADJPY", "CADCHF", "AUDCAD", "NZDCAD"],
                "NZD": ["NZDUSD", "EURNZD", "GBPNZD", "NZDJPY", "NZDCHF", "NZDCAD", "AUDNZD"]
            },
            "api": {
                "enabled": False,
                "url": "https://api.forexfactory.com/news",
                "api_key": ""
            },
            "refresh_interval_minutes": 60
        }
        
        try:
            if os.path.exists(self.news_config_file):
                with open(self.news_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.news_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading news config: {e}")
            return default_config
    
    def load_news_data(self) -> List[Dict]:
        """Load news data from file
        
        Returns:
            List[Dict]: News data
        """
        try:
            if os.path.exists(self.news_data_file):
                with open(self.news_data_file, "r") as f:
                    data = json.load(f)
                    
                    # Convert string dates to datetime objects
                    for event in data:
                        if "datetime" in event and isinstance(event["datetime"], str):
                            try:
                                event["datetime"] = datetime.fromisoformat(event["datetime"])
                            except ValueError:
                                # If conversion fails, use current time
                                event["datetime"] = datetime.utcnow()
                    
                    return data
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading news data: {e}")
            return []
    
    def _generate_currency_pairs(self) -> Dict[str, List[str]]:
        """Generate a mapping of currency pairs to their component currencies
        
        Returns:
            Dict[str, List[str]]: Mapping of currency pairs to component currencies
        """
        pairs = {}
        
        # Extract from currency_impact in config
        for currency, affected_pairs in self.news_config.get("currency_impact", {}).items():
            for pair in affected_pairs:
                if pair not in pairs:
                    pairs[pair] = []
                if currency not in pairs[pair]:
                    pairs[pair].append(currency)
        
        return pairs
    
    def is_news_soon(self, pair: str, window_minutes: Optional[int] = None) -> bool:
        """Check if there is high-impact news coming soon for a currency pair
        
        Args:
            pair (str): Currency pair to check
            window_minutes (Optional[int]): Time window in minutes to check
                                           (defaults to self.window_minutes)
        
        Returns:
            bool: True if there is high-impact news coming soon, False otherwise
        """
        if window_minutes is None:
            window_minutes = self.window_minutes
            
        # Get currencies from pair
        if len(pair) >= 6:
            base_currency = pair[:3]
            quote_currency = pair[3:6]
            currencies = [base_currency, quote_currency]
        else:
            logger.warning(f"Invalid currency pair format: {pair}")
            return False
            
        # Check for upcoming news
        now = datetime.now()
        upcoming_news = self.get_upcoming_news(window_minutes)
        
        for news in upcoming_news:
            if news.get("impact", "").lower() == "high":
                news_currency = news.get("currency", "")
                if news_currency in currencies:
                    return True
                    
        return False
    
    def should_modify_trade(self, pair: str, window_minutes: Optional[int] = None) -> bool:
        """Check if a trade should be modified due to medium-impact news
        
        Args:
            pair (str): Currency pair to check
            window_minutes (Optional[int]): Time window in minutes to check
                                           (defaults to self.window_minutes)
        
        Returns:
            bool: True if the trade should be modified, False otherwise
        """
        if window_minutes is None:
            window_minutes = self.window_minutes
            
        # Get currencies from pair
        if len(pair) >= 6:
            base_currency = pair[:3]
            quote_currency = pair[3:6]
            currencies = [base_currency, quote_currency]
        else:
            logger.warning(f"Invalid currency pair format: {pair}")
            return False
            
        # Check for upcoming news
        now = datetime.now()
        upcoming_news = self.get_upcoming_news(window_minutes)
        
        for news in upcoming_news:
            impact = news.get("impact", "").lower()
            if impact == "medium":
                news_currency = news.get("currency", "")
                if news_currency in currencies:
                    return True
                    
        return False
    
    def get_upcoming_news(self, window_minutes: Optional[int] = None) -> List[Dict]:
        """Get upcoming news events within the specified time window
        
        Args:
            window_minutes (Optional[int]): Time window in minutes to check
                                           (defaults to self.window_minutes)
        
        Returns:
            List[Dict]: Upcoming news events
        """
        if window_minutes is None:
            window_minutes = self.window_minutes
        now = datetime.utcnow()
        upcoming = []
        
        for event in self.news_data:
            event_time = event.get("datetime")
            
            # Skip events without a datetime or impact
            if not event_time or "impact" not in event:
                continue
            
            # Convert string to datetime if needed
            if isinstance(event_time, str):
                try:
                    event_time = datetime.fromisoformat(event_time)
                    event["datetime"] = event_time
                except ValueError:
                    continue
            
            # Check if event is in the future and within window
            time_until = (event_time - now).total_seconds() / 60
            if 0 <= time_until <= window_minutes:
                # Add minutes_until field for convenience
                event_copy = event.copy()
                event_copy["minutes_until"] = time_until
                upcoming.append(event_copy)
        
        # Sort by time
        upcoming.sort(key=lambda x: x.get("minutes_until", 0))
        
        return upcoming
    
    def get_affected_pairs(self) -> Dict[str, Dict]:
        """Get currency pairs affected by upcoming news
        
        Returns:
            Dict[str, Dict]: Affected currency pairs with impact details
        """
        upcoming_news = self.get_upcoming_news()
        affected_pairs = {}
        
        for event in upcoming_news:
            currency = event.get("currency")
            impact = event.get("impact")
            minutes_until = event.get("minutes_until", 0)
            
            if not currency or not impact:
                continue
            
            # Get impact config
            impact_config = self.news_config.get("impact_levels", {}).get(impact.lower(), {})
            if not impact_config:
                continue
            
            # Get affected pairs for this currency
            currency_pairs = self.news_config.get("currency_impact", {}).get(currency, [])
            
            for pair in currency_pairs:
                # If pair already affected by higher impact news, skip
                if pair in affected_pairs:
                    existing_impact = affected_pairs[pair].get("impact")
                    if existing_impact == "high" or (existing_impact == "medium" and impact.lower() == "low"):
                        continue
                
                affected_pairs[pair] = {
                    "impact": impact.lower(),
                    "currency": currency,
                    "event": event.get("title", "Unknown Event"),
                    "minutes_until": minutes_until,
                    "risk_multiplier": impact_config.get("risk_multiplier", 1.0)
                }
        
        return affected_pairs
    
    def is_news_soon(self, symbol: str) -> Tuple[bool, Optional[Dict]]:
        """Check if there is high-impact news coming soon for a symbol
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            Tuple[bool, Optional[Dict]]: (is_affected, event_details)
        """
        # Standardize symbol format
        symbol = symbol.upper().replace("/", "")
        
        # Get affected pairs
        affected_pairs = self.get_affected_pairs()
        
        # Check if symbol is affected
        if symbol in affected_pairs:
            return True, affected_pairs[symbol]
        
        return False, None
    
    def should_modify_trade(self, symbol: str) -> Tuple[bool, str, float]:
        """Determine if a trade should be modified due to upcoming news
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            Tuple[bool, str, float]: (should_modify, reason, risk_multiplier)
        """
        is_affected, event = self.is_news_soon(symbol)
        
        if not is_affected or not event:
            return False, "No upcoming news", 1.0
        
        impact = event.get("impact", "low")
        minutes_until = event.get("minutes_until", 0)
        event_name = event.get("event", "Unknown Event")
        risk_multiplier = event.get("risk_multiplier", 1.0)
        
        if impact == "high":
            return True, f"High-impact news '{event_name}' in {minutes_until:.1f} minutes", risk_multiplier
        elif impact == "medium":
            return True, f"Medium-impact news '{event_name}' in {minutes_until:.1f} minutes", risk_multiplier
        elif impact == "low":
            # For low impact, only modify if very close
            if minutes_until < 10:
                return True, f"Low-impact news '{event_name}' in {minutes_until:.1f} minutes", risk_multiplier
        
        return False, "News impact not significant", 1.0
    
    def refresh_news_data(self) -> bool:
        """Refresh news data from API or file
        
        Returns:
            bool: Success status
        """
        api_config = self.news_config.get("api", {})
        
        if api_config.get("enabled", False):
            # Fetch from API
            try:
                url = api_config.get("url", "")
                api_key = api_config.get("api_key", "")
                
                if not url:
                    logger.error("API URL not configured")
                    return False
                
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Save to file
                    with open(self.news_data_file, "w") as f:
                        json.dump(data, f, indent=4)
                    
                    # Reload data
                    self.news_data = self.load_news_data()
                    return True
                else:
                    logger.error(f"API request failed: {response.status_code} {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error refreshing news data from API: {e}")
                return False
        else:
            logger.info("API not enabled, using existing news data")
            return True


# Helper functions for external use
def is_news_soon(symbol: str) -> bool:
    """Check if there is high-impact news coming soon for a symbol (helper function)
    
    Args:
        symbol (str): Trading symbol
    
    Returns:
        bool: True if affected by upcoming news, False otherwise
    """
    news_guard = NewsGuard()
    is_affected, _ = news_guard.is_news_soon(symbol)
    return is_affected


# For testing
if __name__ == "__main__":
    # Create news guard
    news_guard = NewsGuard()
    
    # Test symbols
    test_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
    
    # Get upcoming news
    upcoming_news = news_guard.get_upcoming_news()
    print(f"Found {len(upcoming_news)} upcoming news events")
    
    for event in upcoming_news[:5]:  # Show first 5 events
        print(f"\n{event.get('title', 'Unknown Event')}:")
        print(f"  Currency: {event.get('currency', 'Unknown')}")
        print(f"  Impact: {event.get('impact', 'Unknown')}")
        print(f"  Time: {event.get('datetime', 'Unknown')}")
        print(f"  Minutes until: {event.get('minutes_until', 0):.1f}")
    
    # Get affected pairs
    affected_pairs = news_guard.get_affected_pairs()
    print(f"\nAffected pairs: {', '.join(affected_pairs.keys()) if affected_pairs else 'None'}")
    
    # Test symbols
    print("\nTesting symbols:")
    for symbol in test_symbols:
        is_affected, event = news_guard.is_news_soon(symbol)
        should_modify, reason, multiplier = news_guard.should_modify_trade(symbol)
        
        print(f"\n{symbol}:")
        print(f"  Affected by news: {is_affected}")
        if is_affected and event:
            print(f"  Event: {event.get('event', 'Unknown')}")
            print(f"  Impact: {event.get('impact', 'Unknown')}")
            print(f"  Minutes until: {event.get('minutes_until', 0):.1f}")
        
        print(f"  Should modify trade: {should_modify}")
        print(f"  Reason: {reason}")
        print(f"  Risk multiplier: {multiplier}")