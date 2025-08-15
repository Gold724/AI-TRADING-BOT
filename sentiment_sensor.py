# sentiment_sensor.py

import json
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

# Try to import requests for API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Try to import BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sentiment_sensor")

# Constants
SENTIMENT_DATA_FILE = os.path.join("data", "sentiment_data.json")
SENTIMENT_CONFIG_FILE = os.path.join("config", "sentiment_config.json")
FOREX_FACTORY_CALENDAR_URL = "https://www.forexfactory.com/calendar"
TWITTER_SENTIMENT_ENDPOINT = "https://api.example.com/twitter_sentiment"  # Replace with actual API endpoint

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)


class SentimentSensor:
    """Real-Time Forex Factory & Twitter Filter
    
    This class is responsible for gathering and analyzing sentiment data from
    economic calendars (like Forex Factory) and social media (like Twitter)
    to provide real-time sentiment scores for trading decisions.
    """

    def __init__(self, sentiment_data_file: str = SENTIMENT_DATA_FILE,
                 sentiment_config_file: str = SENTIMENT_CONFIG_FILE):
        """Initialize the sentiment sensor

        Args:
            sentiment_data_file (str): Path to the sentiment data file
            sentiment_config_file (str): Path to the sentiment configuration file
        """
        self.sentiment_data_file = sentiment_data_file
        self.sentiment_config_file = sentiment_config_file
        self.config = self.load_config()
        self.sentiment_data = self.load_sentiment_data()
        self.last_update = self.sentiment_data.get("last_update", None)
        
        # Initialize currency pairs to monitor
        self.currency_pairs = self.config.get("currency_pairs", [])
        self.major_currencies = self.config.get("major_currencies", [])
        
        # Initialize update intervals
        self.calendar_update_interval = self.config.get("calendar_update_interval_minutes", 60)
        self.social_update_interval = self.config.get("social_update_interval_minutes", 30)

    def load_config(self) -> Dict:
        """Load sentiment configuration from file

        Returns:
            Dict: Sentiment configuration
        """
        default_config = {
            "calendar_update_interval_minutes": 60,
            "social_update_interval_minutes": 30,
            "sentiment_threshold_bullish": 60,
            "sentiment_threshold_bearish": 40,
            "volatility_threshold_high": 70,
            "impact_weights": {
                "high": 1.0,
                "medium": 0.6,
                "low": 0.3
            },
            "currency_pairs": [
                "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", 
                "USDCAD", "EURGBP", "EURJPY", "GBPJPY"
            ],
            "major_currencies": [
                "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"
            ],
            "social_media_enabled": False,  # Set to True when API keys are configured
            "api_keys": {
                "twitter": "",
                "other_service": ""
            }
        }

        try:
            if os.path.exists(self.sentiment_config_file):
                with open(self.sentiment_config_file, "r") as f:
                    return json.load(f)
            else:
                # Create default config file if it doesn't exist
                with open(self.sentiment_config_file, "w") as f:
                    json.dump(default_config, f, indent=4)
                return default_config
        except Exception as e:
            logger.error(f"Error loading sentiment config: {e}")
            return default_config

    def save_config(self) -> bool:
        """Save sentiment configuration to file

        Returns:
            bool: Success status
        """
        try:
            with open(self.sentiment_config_file, "w") as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving sentiment config: {e}")
            return False

    def load_sentiment_data(self) -> Dict:
        """Load sentiment data from file

        Returns:
            Dict: Sentiment data
        """
        default_data = {
            "last_update": None,
            "calendar_events": [],
            "currency_sentiment": {},
            "pair_sentiment": {},
            "volatility_alerts": []
        }

        try:
            if os.path.exists(self.sentiment_data_file):
                with open(self.sentiment_data_file, "r") as f:
                    return json.load(f)
            else:
                # Create default data file if it doesn't exist
                with open(self.sentiment_data_file, "w") as f:
                    json.dump(default_data, f, indent=4)
                return default_data
        except Exception as e:
            logger.error(f"Error loading sentiment data: {e}")
            return default_data

    def save_sentiment_data(self) -> bool:
        """Save sentiment data to file

        Returns:
            bool: Success status
        """
        try:
            # Update last update timestamp
            self.sentiment_data["last_update"] = datetime.utcnow().isoformat()
            self.last_update = self.sentiment_data["last_update"]
            
            with open(self.sentiment_data_file, "w") as f:
                json.dump(self.sentiment_data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving sentiment data: {e}")
            return False

    def update_sentiment_data(self, force: bool = False) -> bool:
        """Update sentiment data from all sources

        Args:
            force (bool, optional): Force update regardless of time interval. Defaults to False.

        Returns:
            bool: Success status
        """
        try:
            current_time = datetime.utcnow()
            update_needed = force
            
            # Check if update is needed based on last update time
            if self.last_update:
                last_update_time = datetime.fromisoformat(self.last_update)
                calendar_delta = timedelta(minutes=self.calendar_update_interval)
                social_delta = timedelta(minutes=self.social_update_interval)
                
                if current_time - last_update_time > calendar_delta:
                    update_needed = True
            else:
                update_needed = True
            
            if not update_needed:
                logger.info("No update needed, using cached sentiment data")
                return True
            
            # Update economic calendar data
            calendar_success = self.update_economic_calendar()
            
            # Update social media sentiment if enabled
            social_success = True
            if self.config.get("social_media_enabled", False):
                social_success = self.update_social_sentiment()
            
            # Calculate overall sentiment for currencies and pairs
            self.calculate_currency_sentiment()
            self.calculate_pair_sentiment()
            
            # Check for high volatility events
            self.detect_volatility_events()
            
            # Save updated data
            self.save_sentiment_data()
            
            return calendar_success and social_success
        except Exception as e:
            logger.error(f"Error updating sentiment data: {e}")
            return False

    def update_economic_calendar(self) -> bool:
        """Update economic calendar data from Forex Factory

        Returns:
            bool: Success status
        """
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            logger.warning("Requests or BeautifulSoup not available, using mock calendar data")
            return self.generate_mock_calendar_data()
        
        try:
            # Fetch calendar data from Forex Factory
            response = requests.get(FOREX_FACTORY_CALENDAR_URL)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch calendar data: {response.status_code}")
                return self.generate_mock_calendar_data()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract calendar events (this is a simplified example)
            # In a real implementation, you would need to parse the actual HTML structure
            calendar_events = []
            event_rows = soup.select(".calendar_row")  # Adjust selector based on actual HTML
            
            for row in event_rows:
                # Extract event data (adjust selectors based on actual HTML)
                currency = row.select_one(".currency").text.strip()
                event_name = row.select_one(".event").text.strip()
                impact = row.select_one(".impact").text.strip().lower()
                time_str = row.select_one(".time").text.strip()
                forecast = row.select_one(".forecast").text.strip()
                previous = row.select_one(".previous").text.strip()
                
                # Parse event time
                event_time = datetime.utcnow()  # Placeholder, parse actual time from time_str
                
                # Create event record
                event = {
                    "currency": currency,
                    "event": event_name,
                    "impact": impact,
                    "time": event_time.isoformat(),
                    "forecast": forecast,
                    "previous": previous
                }
                
                calendar_events.append(event)
            
            # Update sentiment data
            self.sentiment_data["calendar_events"] = calendar_events
            
            return True
        except Exception as e:
            logger.error(f"Error updating economic calendar: {e}")
            return self.generate_mock_calendar_data()

    def generate_mock_calendar_data(self) -> bool:
        """Generate mock calendar data for testing or when API is unavailable

        Returns:
            bool: Success status
        """
        try:
            # Generate mock calendar events
            current_time = datetime.utcnow()
            calendar_events = []
            
            # Sample event types
            event_types = [
                "Interest Rate Decision",
                "GDP",
                "CPI",
                "Unemployment Rate",
                "Retail Sales",
                "PMI",
                "Trade Balance",
                "Industrial Production"
            ]
            
            # Generate events for major currencies
            for currency in self.major_currencies:
                # High impact event
                event_time = current_time + timedelta(hours=random.randint(1, 24))
                calendar_events.append({
                    "currency": currency,
                    "event": random.choice(["Interest Rate Decision", "GDP", "CPI"]),
                    "impact": "high",
                    "time": event_time.isoformat(),
                    "forecast": f"{random.uniform(0.1, 5.0):.1f}%",
                    "previous": f"{random.uniform(0.1, 5.0):.1f}%"
                })
                
                # Medium impact event
                event_time = current_time + timedelta(hours=random.randint(1, 48))
                calendar_events.append({
                    "currency": currency,
                    "event": random.choice(["Unemployment Rate", "Retail Sales", "PMI"]),
                    "impact": "medium",
                    "time": event_time.isoformat(),
                    "forecast": f"{random.uniform(0.1, 10.0):.1f}%",
                    "previous": f"{random.uniform(0.1, 10.0):.1f}%"
                })
                
                # Low impact event
                event_time = current_time + timedelta(hours=random.randint(1, 72))
                calendar_events.append({
                    "currency": currency,
                    "event": random.choice(["Trade Balance", "Industrial Production"]),
                    "impact": "low",
                    "time": event_time.isoformat(),
                    "forecast": f"{random.uniform(-10.0, 10.0):.1f}B",
                    "previous": f"{random.uniform(-10.0, 10.0):.1f}B"
                })
            
            # Update sentiment data
            self.sentiment_data["calendar_events"] = calendar_events
            
            return True
        except Exception as e:
            logger.error(f"Error generating mock calendar data: {e}")
            return False

    def update_social_sentiment(self) -> bool:
        """Update social media sentiment data

        Returns:
            bool: Success status
        """
        if not REQUESTS_AVAILABLE or not self.config.get("social_media_enabled", False):
            logger.warning("Social media sentiment disabled or requests not available, using mock data")
            return self.generate_mock_social_data()
        
        try:
            # Check if API key is configured
            api_key = self.config.get("api_keys", {}).get("twitter", "")
            
            if not api_key:
                logger.warning("Twitter API key not configured, using mock data")
                return self.generate_mock_social_data()
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare query for each currency
            currency_sentiment = {}
            
            for currency in self.major_currencies:
                # Construct query for currency symbol (e.g., $USD, $EUR)
                query = f"${currency}"
                
                # Make API request
                response = requests.get(
                    f"{TWITTER_SENTIMENT_ENDPOINT}?query={query}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch sentiment for {currency}: {response.status_code}")
                    continue
                
                # Parse response
                data = response.json()
                
                # Extract sentiment scores
                sentiment = {
                    "bullish": data.get("bullish_score", 50),
                    "bearish": data.get("bearish_score", 50),
                    "neutral": data.get("neutral_score", 0),
                    "volume": data.get("tweet_volume", 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                currency_sentiment[currency] = sentiment
            
            # Update sentiment data
            self.sentiment_data["currency_sentiment"] = currency_sentiment
            
            return True
        except Exception as e:
            logger.error(f"Error updating social sentiment: {e}")
            return self.generate_mock_social_data()

    def generate_mock_social_data(self) -> bool:
        """Generate mock social media sentiment data for testing

        Returns:
            bool: Success status
        """
        try:
            # Generate mock sentiment for each currency
            currency_sentiment = {}
            
            for currency in self.major_currencies:
                # Generate random sentiment scores
                bullish = random.randint(30, 70)
                bearish = 100 - bullish
                
                sentiment = {
                    "bullish": bullish,
                    "bearish": bearish,
                    "neutral": random.randint(0, 20),
                    "volume": random.randint(1000, 10000),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                currency_sentiment[currency] = sentiment
            
            # Update sentiment data
            self.sentiment_data["currency_sentiment"] = currency_sentiment
            
            return True
        except Exception as e:
            logger.error(f"Error generating mock social data: {e}")
            return False

    def calculate_currency_sentiment(self) -> None:
        """Calculate overall sentiment for each currency based on calendar and social data"""
        try:
            # Get calendar events and social sentiment
            calendar_events = self.sentiment_data.get("calendar_events", [])
            social_sentiment = self.sentiment_data.get("currency_sentiment", {})
            
            # Initialize currency sentiment
            currency_sentiment = {}
            
            # Process each currency
            for currency in self.major_currencies:
                # Initialize sentiment scores
                calendar_score = 50  # Neutral by default
                social_score = 50  # Neutral by default
                
                # Calculate calendar-based sentiment
                currency_events = [e for e in calendar_events if e.get("currency") == currency]
                
                if currency_events:
                    # Calculate weighted impact
                    total_impact = 0
                    weighted_sentiment = 0
                    
                    for event in currency_events:
                        impact = event.get("impact", "low")
                        impact_weight = self.config["impact_weights"].get(impact, 0.1)
                        
                        # Determine if event is positive or negative
                        # This is a simplified approach - in reality, you would need to analyze
                        # the forecast vs. previous values and understand the economic implications
                        forecast = event.get("forecast", "")
                        previous = event.get("previous", "")
                        
                        # Extract numeric values if possible
                        forecast_value = self.extract_numeric_value(forecast)
                        previous_value = self.extract_numeric_value(previous)
                        
                        event_sentiment = 50  # Neutral by default
                        
                        if forecast_value is not None and previous_value is not None:
                            # For most economic indicators, higher is better (except unemployment, inflation)
                            event_name = event.get("event", "").lower()
                            
                            if "unemployment" in event_name or "inflation" in event_name or "cpi" in event_name:
                                # Lower is better
                                if forecast_value < previous_value:
                                    event_sentiment = 60  # Positive
                                elif forecast_value > previous_value:
                                    event_sentiment = 40  # Negative
                            else:
                                # Higher is better
                                if forecast_value > previous_value:
                                    event_sentiment = 60  # Positive
                                elif forecast_value < previous_value:
                                    event_sentiment = 40  # Negative
                        
                        weighted_sentiment += event_sentiment * impact_weight
                        total_impact += impact_weight
                    
                    if total_impact > 0:
                        calendar_score = int(weighted_sentiment / total_impact)
                
                # Get social sentiment if available
                if currency in social_sentiment:
                    bullish = social_sentiment[currency].get("bullish", 50)
                    bearish = social_sentiment[currency].get("bearish", 50)
                    social_score = bullish  # Use bullish score as overall sentiment
                
                # Calculate overall sentiment (70% calendar, 30% social)
                overall_sentiment = int(calendar_score * 0.7 + social_score * 0.3)
                
                # Determine sentiment direction
                if overall_sentiment >= self.config["sentiment_threshold_bullish"]:
                    direction = "bullish"
                elif overall_sentiment <= self.config["sentiment_threshold_bearish"]:
                    direction = "bearish"
                else:
                    direction = "neutral"
                
                # Calculate volatility score based on high-impact events
                high_impact_events = [e for e in currency_events if e.get("impact") == "high"]
                volatility_score = min(100, len(high_impact_events) * 20)
                
                # Store currency sentiment
                currency_sentiment[currency] = {
                    "overall_score": overall_sentiment,
                    "calendar_score": calendar_score,
                    "social_score": social_score,
                    "direction": direction,
                    "volatility_score": volatility_score,
                    "high_impact_events": len(high_impact_events),
                    "updated": datetime.utcnow().isoformat()
                }
            
            # Update sentiment data
            self.sentiment_data["currency_sentiment"] = currency_sentiment
        except Exception as e:
            logger.error(f"Error calculating currency sentiment: {e}")

    def calculate_pair_sentiment(self) -> None:
        """Calculate sentiment for currency pairs based on individual currency sentiment"""
        try:
            # Get currency sentiment
            currency_sentiment = self.sentiment_data.get("currency_sentiment", {})
            
            # Initialize pair sentiment
            pair_sentiment = {}
            
            # Process each currency pair
            for pair in self.currency_pairs:
                # Extract base and quote currencies
                if len(pair) != 6:
                    continue
                
                base_currency = pair[:3]
                quote_currency = pair[3:]
                
                # Skip if either currency is missing
                if base_currency not in currency_sentiment or quote_currency not in currency_sentiment:
                    continue
                
                # Get sentiment for each currency
                base_data = currency_sentiment[base_currency]
                quote_data = currency_sentiment[quote_currency]
                
                # Calculate pair sentiment
                # For a currency pair like EURUSD, if EUR is bullish and USD is bearish,
                # then the pair is strongly bullish
                base_score = base_data["overall_score"]
                quote_score = 100 - quote_data["overall_score"]  # Invert quote currency
                
                # Calculate overall pair sentiment
                overall_score = int((base_score + quote_score) / 2)
                
                # Determine sentiment direction
                if overall_score >= self.config["sentiment_threshold_bullish"]:
                    direction = "bullish"
                elif overall_score <= self.config["sentiment_threshold_bearish"]:
                    direction = "bearish"
                else:
                    direction = "neutral"
                
                # Calculate volatility score (max of both currencies)
                volatility_score = max(
                    base_data["volatility_score"],
                    quote_data["volatility_score"]
                )
                
                # Determine if high volatility
                high_volatility = volatility_score >= self.config["volatility_threshold_high"]
                
                # Store pair sentiment
                pair_sentiment[pair] = {
                    "overall_score": overall_score,
                    "direction": direction,
                    "volatility_score": volatility_score,
                    "high_volatility": high_volatility,
                    "base_currency_score": base_score,
                    "quote_currency_score": quote_score,
                    "updated": datetime.utcnow().isoformat()
                }
            
            # Update sentiment data
            self.sentiment_data["pair_sentiment"] = pair_sentiment
        except Exception as e:
            logger.error(f"Error calculating pair sentiment: {e}")

    def detect_volatility_events(self) -> None:
        """Detect high volatility events and generate alerts"""
        try:
            # Get calendar events
            calendar_events = self.sentiment_data.get("calendar_events", [])
            
            # Filter for high-impact events in the next 24 hours
            current_time = datetime.utcnow()
            cutoff_time = current_time + timedelta(hours=24)
            
            high_impact_events = []
            
            for event in calendar_events:
                # Skip if not high impact
                if event.get("impact") != "high":
                    continue
                
                # Parse event time
                event_time = datetime.fromisoformat(event.get("time", current_time.isoformat()))
                
                # Check if event is within the next 24 hours
                if current_time <= event_time <= cutoff_time:
                    high_impact_events.append(event)
            
            # Generate volatility alerts
            volatility_alerts = []
            
            for event in high_impact_events:
                currency = event.get("currency")
                event_name = event.get("event")
                event_time = event.get("time")
                
                # Find affected pairs
                affected_pairs = [pair for pair in self.currency_pairs if currency in pair]
                
                # Create alert
                alert = {
                    "currency": currency,
                    "event": event_name,
                    "time": event_time,
                    "affected_pairs": affected_pairs,
                    "alert_level": "high",
                    "created": datetime.utcnow().isoformat()
                }
                
                volatility_alerts.append(alert)
            
            # Update sentiment data
            self.sentiment_data["volatility_alerts"] = volatility_alerts
        except Exception as e:
            logger.error(f"Error detecting volatility events: {e}")

    def extract_numeric_value(self, value_str: str) -> Optional[float]:
        """Extract numeric value from string

        Args:
            value_str (str): String containing numeric value

        Returns:
            Optional[float]: Extracted numeric value or None if not found
        """
        if not value_str:
            return None
        
        # Extract numeric part using regex
        match = re.search(r'-?\d+\.?\d*', value_str)
        
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        
        return None

    def get_pair_sentiment(self, pair: str) -> Dict:
        """Get sentiment data for a specific currency pair

        Args:
            pair (str): Currency pair (e.g., "EURUSD")

        Returns:
            Dict: Sentiment data for the pair
        """
        # Update sentiment data if needed
        self.update_sentiment_data()
        
        # Get pair sentiment
        pair_sentiment = self.sentiment_data.get("pair_sentiment", {})
        
        # Return sentiment for the requested pair
        if pair in pair_sentiment:
            return pair_sentiment[pair]
        else:
            return {
                "overall_score": 50,
                "direction": "neutral",
                "volatility_score": 0,
                "high_volatility": False,
                "message": f"No sentiment data available for {pair}"
            }

    def get_currency_sentiment(self, currency: str) -> Dict:
        """Get sentiment data for a specific currency

        Args:
            currency (str): Currency code (e.g., "USD")

        Returns:
            Dict: Sentiment data for the currency
        """
        # Update sentiment data if needed
        self.update_sentiment_data()
        
        # Get currency sentiment
        currency_sentiment = self.sentiment_data.get("currency_sentiment", {})
        
        # Return sentiment for the requested currency
        if currency in currency_sentiment:
            return currency_sentiment[currency]
        else:
            return {
                "overall_score": 50,
                "direction": "neutral",
                "volatility_score": 0,
                "message": f"No sentiment data available for {currency}"
            }

    def get_upcoming_events(self, hours: int = 24, currency: Optional[str] = None) -> List[Dict]:
        """Get upcoming economic events

        Args:
            hours (int, optional): Number of hours to look ahead. Defaults to 24.
            currency (Optional[str], optional): Filter by currency. Defaults to None.

        Returns:
            List[Dict]: List of upcoming events
        """
        # Update sentiment data if needed
        self.update_sentiment_data()
        
        # Get calendar events
        calendar_events = self.sentiment_data.get("calendar_events", [])
        
        # Filter events
        current_time = datetime.utcnow()
        cutoff_time = current_time + timedelta(hours=hours)
        
        upcoming_events = []
        
        for event in calendar_events:
            # Parse event time
            event_time = datetime.fromisoformat(event.get("time", current_time.isoformat()))
            
            # Check if event is within the specified time window
            if current_time <= event_time <= cutoff_time:
                # Filter by currency if specified
                if currency is None or event.get("currency") == currency:
                    upcoming_events.append(event)
        
        # Sort by time
        upcoming_events.sort(key=lambda x: x.get("time", ""))
        
        return upcoming_events

    def get_volatility_alerts(self) -> List[Dict]:
        """Get current volatility alerts

        Returns:
            List[Dict]: List of volatility alerts
        """
        # Update sentiment data if needed
        self.update_sentiment_data()
        
        # Return volatility alerts
        return self.sentiment_data.get("volatility_alerts", [])

    def adjust_confidence(self, pair: str, base_confidence: int) -> Tuple[int, str]:
        """Adjust confidence score based on sentiment data

        Args:
            pair (str): Currency pair
            base_confidence (int): Base confidence score (0-100)

        Returns:
            Tuple[int, str]: Adjusted confidence score and reason
        """
        # Get pair sentiment
        sentiment = self.get_pair_sentiment(pair)
        
        # Initialize adjustment
        adjustment = 0
        reason = ""
        
        # Adjust based on sentiment direction
        direction = sentiment.get("direction", "neutral")
        
        if direction == "bullish":
            adjustment += 10
            reason += "Bullish sentiment (+10). "
        elif direction == "bearish":
            adjustment -= 10
            reason += "Bearish sentiment (-10). "
        
        # Adjust for high volatility
        if sentiment.get("high_volatility", False):
            adjustment -= 15
            reason += "High volatility detected (-15). "
        
        # Check for upcoming high-impact events
        upcoming_events = self.get_upcoming_events(hours=6)
        high_impact_events = [e for e in upcoming_events if e.get("impact") == "high"]
        
        if high_impact_events:
            adjustment -= 10
            reason += f"Upcoming high-impact events ({len(high_impact_events)}) (-10). "
        
        # Calculate adjusted confidence
        adjusted_confidence = max(0, min(100, base_confidence + adjustment))
        
        if not reason:
            reason = "No significant sentiment factors."
        
        return adjusted_confidence, reason

    def get_sentiment_summary(self) -> Dict:
        """Get a summary of current sentiment data

        Returns:
            Dict: Sentiment summary
        """
        # Update sentiment data if needed
        self.update_sentiment_data()
        
        # Get pair sentiment
        pair_sentiment = self.sentiment_data.get("pair_sentiment", {})
        
        # Categorize pairs by sentiment
        bullish_pairs = []
        bearish_pairs = []
        neutral_pairs = []
        high_volatility_pairs = []
        
        for pair, data in pair_sentiment.items():
            direction = data.get("direction", "neutral")
            
            if direction == "bullish":
                bullish_pairs.append(pair)
            elif direction == "bearish":
                bearish_pairs.append(pair)
            else:
                neutral_pairs.append(pair)
            
            if data.get("high_volatility", False):
                high_volatility_pairs.append(pair)
        
        # Get upcoming high-impact events
        upcoming_events = self.get_upcoming_events(hours=24)
        high_impact_events = [e for e in upcoming_events if e.get("impact") == "high"]
        
        # Create summary
        summary = {
            "bullish_pairs": bullish_pairs,
            "bearish_pairs": bearish_pairs,
            "neutral_pairs": neutral_pairs,
            "high_volatility_pairs": high_volatility_pairs,
            "upcoming_high_impact_events": len(high_impact_events),
            "updated": datetime.utcnow().isoformat()
        }
        
        return summary


# Helper functions
def get_pair_sentiment(pair: str) -> Dict:
    """Get sentiment data for a specific currency pair (helper function)

    Args:
        pair (str): Currency pair (e.g., "EURUSD")

    Returns:
        Dict: Sentiment data for the pair
    """
    sensor = SentimentSensor()
    return sensor.get_pair_sentiment(pair)


def adjust_confidence(pair: str, base_confidence: int) -> Tuple[int, str]:
    """Adjust confidence score based on sentiment data (helper function)

    Args:
        pair (str): Currency pair
        base_confidence (int): Base confidence score (0-100)

    Returns:
        Tuple[int, str]: Adjusted confidence score and reason
    """
    sensor = SentimentSensor()
    return sensor.adjust_confidence(pair, base_confidence)


def get_upcoming_events(hours: int = 24, currency: Optional[str] = None) -> List[Dict]:
    """Get upcoming economic events (helper function)

    Args:
        hours (int, optional): Number of hours to look ahead. Defaults to 24.
        currency (Optional[str], optional): Filter by currency. Defaults to None.

    Returns:
        List[Dict]: List of upcoming events
    """
    sensor = SentimentSensor()
    return sensor.get_upcoming_events(hours, currency)


def get_volatility_alerts() -> List[Dict]:
    """Get current volatility alerts (helper function)

    Returns:
        List[Dict]: List of volatility alerts
    """
    sensor = SentimentSensor()
    return sensor.get_volatility_alerts()


def get_sentiment_summary() -> Dict:
    """Get a summary of current sentiment data (helper function)

    Returns:
        Dict: Sentiment summary
    """
    sensor = SentimentSensor()
    return sensor.get_sentiment_summary()


# For testing
if __name__ == "__main__":
    # Create an instance of the sentiment sensor
    sensor = SentimentSensor()
    
    # Update sentiment data
    print("Updating sentiment data...")
    sensor.update_sentiment_data(force=True)
    
    # Print sentiment summary
    print("\nSentiment Summary:")
    summary = sensor.get_sentiment_summary()
    
    print(f"Bullish Pairs: {', '.join(summary['bullish_pairs'])}")
    print(f"Bearish Pairs: {', '.join(summary['bearish_pairs'])}")
    print(f"Neutral Pairs: {', '.join(summary['neutral_pairs'])}")
    print(f"High Volatility Pairs: {', '.join(summary['high_volatility_pairs'])}")
    print(f"Upcoming High-Impact Events: {summary['upcoming_high_impact_events']}")
    
    # Print pair sentiment
    print("\nPair Sentiment:")
    for pair in ["EURUSD", "GBPUSD", "USDJPY"]:
        sentiment = sensor.get_pair_sentiment(pair)
        print(f"\n{pair}:")
        print(f"  Direction: {sentiment['direction']}")
        print(f"  Overall Score: {sentiment['overall_score']}")
        print(f"  Volatility Score: {sentiment['volatility_score']}")
        print(f"  High Volatility: {sentiment['high_volatility']}")
    
    # Test confidence adjustment
    print("\nConfidence Adjustment Test:")
    base_confidence = 70
    
    for pair in ["EURUSD", "GBPUSD", "USDJPY"]:
        adjusted, reason = sensor.adjust_confidence(pair, base_confidence)
        print(f"\n{pair}:")
        print(f"  Base Confidence: {base_confidence}")
        print(f"  Adjusted Confidence: {adjusted}")
        print(f"  Reason: {reason}")
    
    # Print upcoming events
    print("\nUpcoming Events (next 24 hours):")
    events = sensor.get_upcoming_events(hours=24)
    
    for event in events[:5]:  # Show first 5 events
        currency = event.get("currency")
        event_name = event.get("event")
        impact = event.get("impact")
        event_time = datetime.fromisoformat(event.get("time")).strftime("%Y-%m-%d %H:%M")
        
        print(f"  {event_time} - {currency} {event_name} (Impact: {impact})")
    
    # Print volatility alerts
    print("\nVolatility Alerts:")
    alerts = sensor.get_volatility_alerts()
    
    for alert in alerts:
        currency = alert.get("currency")
        event_name = alert.get("event")
        event_time = datetime.fromisoformat(alert.get("time")).strftime("%Y-%m-%d %H:%M")
        affected_pairs = ", ".join(alert.get("affected_pairs", []))
        
        print(f"  {event_time} - {currency} {event_name}")
        print(f"    Affected Pairs: {affected_pairs}")