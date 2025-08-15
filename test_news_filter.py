#!/usr/bin/env python
# test_news_filter.py - Test script for the news-aware filter functionality

import json
import os
import sys
from datetime import datetime, timedelta

# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

# Create a test forex_news.json file with some sample data
def create_test_news_data():
    # Current time for reference
    now = datetime.utcnow()
    
    # Create some test news events
    test_events = [
        {
            "title": "Non-Farm Payrolls",
            "country": "United States",
            "currency": "USD",
            "impact": "high",
            "datetime": (now + timedelta(minutes=15)).isoformat(),  # High impact event coming soon
            "forecast": "200K",
            "previous": "175K"
        },
        {
            "title": "ECB Press Conference",
            "country": "European Union",
            "currency": "EUR",
            "impact": "high",
            "datetime": (now + timedelta(hours=2)).isoformat(),  # High impact event in 2 hours
            "forecast": "",
            "previous": ""
        },
        {
            "title": "Retail Sales m/m",
            "country": "United Kingdom",
            "currency": "GBP",
            "impact": "medium",
            "datetime": (now + timedelta(minutes=10)).isoformat(),  # Medium impact event coming soon
            "forecast": "0.3%",
            "previous": "0.2%"
        }
    ]
    
    # Write to the test file
    with open("data/forex_news.json", "w") as f:
        json.dump(test_events, f, indent=2)
    
    print(f"Created test news data with {len(test_events)} events")
    return test_events

# Import the news filter module
try:
    from news_filter import NewsAwareFilter, update_banned_periods
    print("Successfully imported NewsAwareFilter")
except ImportError as e:
    print(f"Error importing NewsAwareFilter: {e}")
    print("Make sure news_filter.py is in the current directory")
    sys.exit(1)

# Main test function
def test_news_filter():
    # Create test data
    test_events = create_test_news_data()
    
    # Update banned periods
    update_banned_periods()
    print("Updated banned periods based on test data")
    
    # Initialize the filter
    news_filter = NewsAwareFilter()
    
    # Test currency pairs
    test_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    
    print("\nTesting is_safe_to_trade for different currency pairs:")
    for pair in test_pairs:
        is_safe = news_filter.is_safe_to_trade(pair)
        risk_level = news_filter.get_event_risk(pair)
        
        base_lot = 0.01
        adjusted_lot = news_filter.get_dynamic_lot_size(pair, base_lot)
        
        print(f"\n{pair}:")
        print(f"  Safe to trade: {'✅ Yes' if is_safe else '❌ No'}")
        print(f"  Risk level: {risk_level}")
        print(f"  Base lot: {base_lot} → Adjusted lot: {adjusted_lot}")
        
        if not is_safe:
            # Find which event is causing the block
            for event in test_events:
                event_time = datetime.fromisoformat(event['datetime'])
                time_diff = (event_time - datetime.utcnow()).total_seconds() / 60
                if abs(time_diff) < 30 and event['currency'] in pair:
                    print(f"  Blocked due to: {event['title']} ({event['impact']} impact) in {time_diff:.1f} minutes")

# Run the tests
if __name__ == "__main__":
    print("=== News-Aware Filter Test ===\n")
    test_news_filter()
    print("\n=== Test Complete ===")