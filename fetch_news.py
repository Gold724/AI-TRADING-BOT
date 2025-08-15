# fetch_news.py

import json
import logging
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fetch_news")

# Load environment variables
load_dotenv()

# Constants
NEWS_DATA_FILE = os.path.join("data", "forex_news.json")
FOREX_FACTORY_API_URL = os.getenv("FOREX_FACTORY_API_URL", "https://nfs.faireconomy.media/ff_calendar_thisweek.json")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)


def fetch_forex_factory_calendar() -> List[Dict]:
    """Fetch economic calendar data from Forex Factory

    Returns:
        List[Dict]: List of economic events
    """
    try:
        logger.info(f"Fetching economic calendar from {FOREX_FACTORY_API_URL}")
        response = requests.get(FOREX_FACTORY_API_URL, timeout=30)
        response.raise_for_status()
        
        # Parse the response
        events = response.json()
        logger.info(f"Successfully fetched {len(events)} economic events")
        
        # Process and standardize the events
        processed_events = []
        for event in events:
            # Convert to our standard format
            processed_event = {
                "title": event.get("title", ""),
                "country": event.get("country", ""),
                "currency": _map_country_to_currency(event.get("country", "")),
                "impact": _map_impact_level(event.get("impact", "")),
                "datetime": _parse_event_datetime(event),
                "forecast": event.get("forecast", ""),
                "previous": event.get("previous", ""),
                "source": "Forex Factory"
            }
            processed_events.append(processed_event)
        
        return processed_events
    except Exception as e:
        logger.error(f"Error fetching Forex Factory calendar: {e}")
        return []


def _map_country_to_currency(country: str) -> str:
    """Map country name to currency code

    Args:
        country (str): Country name

    Returns:
        str: Currency code
    """
    country_currency_map = {
        "US": "USD",
        "EUR": "EUR",  # Eurozone
        "UK": "GBP",
        "JP": "JPY",
        "CA": "CAD",
        "AU": "AUD",
        "NZ": "NZD",
        "CH": "CHF",
        "CN": "CNY",
        # Add more mappings as needed
    }
    
    return country_currency_map.get(country, "")


def _map_impact_level(impact: str) -> str:
    """Map Forex Factory impact level to standardized format

    Args:
        impact (str): Impact level from Forex Factory

    Returns:
        str: Standardized impact level (high, medium, low)
    """
    impact = impact.lower() if impact else ""
    
    if "high" in impact or "3" in impact or "red" in impact:
        return "high"
    elif "medium" in impact or "2" in impact or "orange" in impact or "moderate" in impact:
        return "medium"
    elif "low" in impact or "1" in impact or "yellow" in impact:
        return "low"
    else:
        return "low"  # Default to low if unknown


def _parse_event_datetime(event: Dict) -> str:
    """Parse event datetime from Forex Factory format

    Args:
        event (Dict): Event data from Forex Factory

    Returns:
        str: ISO format datetime string
    """
    try:
        # Forex Factory provides date and time separately
        date_str = event.get("date", "")
        time_str = event.get("time", "")
        
        if not date_str:
            return ""
        
        # Parse date (format may vary, adjust as needed)
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                # If no format worked, raise exception
                raise ValueError(f"Could not parse date: {date_str}")
        except Exception:
            # If date parsing fails, try to extract from timestamp
            if "timestamp" in event:
                date_obj = datetime.fromtimestamp(int(event["timestamp"]))
            else:
                return ""
        
        # Parse time if available
        if time_str:
            try:
                # Try different time formats
                for fmt in ["%H:%M", "%I:%M %p", "%H:%M:%S"]:
                    try:
                        time_obj = datetime.strptime(time_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Default to midnight if time parsing fails
                    time_obj = datetime.strptime("00:00", "%H:%M")
                
                # Combine date and time
                dt = datetime.combine(
                    date_obj.date(),
                    time_obj.time()
                )
            except Exception:
                # Default to midnight if time parsing fails
                dt = datetime.combine(date_obj.date(), datetime.min.time())
        else:
            # Default to midnight if no time provided
            dt = datetime.combine(date_obj.date(), datetime.min.time())
        
        return dt.isoformat()
    except Exception as e:
        logger.error(f"Error parsing event datetime: {e}")
        return ""


def fetch_and_save_news() -> bool:
    """Fetch economic news and save to file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Fetch news from Forex Factory
        events = fetch_forex_factory_calendar()
        
        if not events:
            logger.warning("No events fetched from Forex Factory")
            return False
        
        # Save to file
        with open(NEWS_DATA_FILE, "w") as f:
            json.dump(events, f, indent=2)
        
        logger.info(f"Saved {len(events)} economic events to {NEWS_DATA_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error fetching and saving news: {e}")
        return False


# For testing
if __name__ == "__main__":
    success = fetch_and_save_news()
    
    if success:
        print(f"Successfully fetched and saved economic news to {NEWS_DATA_FILE}")
        
        # Display the first few events
        try:
            with open(NEWS_DATA_FILE, "r") as f:
                events = json.load(f)
            
            print(f"\nFetched {len(events)} events. First 5 events:")
            for i, event in enumerate(events[:5]):
                print(f"\nEvent {i+1}:")
                print(f"  Title: {event.get('title')}")
                print(f"  Currency: {event.get('currency')}")
                print(f"  Impact: {event.get('impact')}")
                print(f"  Datetime: {event.get('datetime')}")
        except Exception as e:
            print(f"Error reading saved events: {e}")
    else:
        print("Failed to fetch and save economic news")