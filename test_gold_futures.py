#!/usr/bin/env python
# test_gold_futures.py - Test script for gold futures trading with contract size adjustment

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
            "title": "Gold Inventory Report",
            "country": "United States",
            "currency": "XAU",
            "impact": "medium",
            "datetime": (now + timedelta(minutes=10)).isoformat(),  # Medium impact event coming soon
            "forecast": "",
            "previous": ""
        }
    ]
    
    # Write to the test file
    with open("data/forex_news.json", "w") as f:
        json.dump(test_events, f, indent=2)
    
    print(f"Created test news data with {len(test_events)} events")
    return test_events

# Import the news filter module
try:
    from news_filter import NewsAwareFilter, get_dynamic_contract_size, update_banned_periods
    print("Successfully imported NewsAwareFilter and get_dynamic_contract_size")
except ImportError as e:
    print(f"Error importing NewsAwareFilter: {e}")
    print("Make sure news_filter.py is in the current directory")
    sys.exit(1)

# Main test function
def test_gold_futures():
    # Create test data
    test_events = create_test_news_data()
    
    # Update banned periods
    update_banned_periods()
    print("Updated banned periods based on test data")
    
    # Initialize the filter
    news_filter = NewsAwareFilter()
    
    # Test gold futures trading
    symbol = "XAUUSD"  # Gold futures symbol
    
    print("\nTesting gold futures contract size adjustment:")
    
    # Test different base contract sizes
    base_contracts_list = [1, 2, 5, 10]
    
    for base_contracts in base_contracts_list:
        # Get risk level and adjusted contract size
        risk_level = news_filter.get_event_risk(symbol)
        adjusted_contracts = news_filter.get_dynamic_contract_size(symbol, base_contracts)
        
        # Also test the helper function
        helper_adjusted_contracts = get_dynamic_contract_size(symbol, base_contracts)
        
        print(f"\nGold Futures (XAUUSD):")
        print(f"  Risk level: {risk_level}")
        print(f"  Base contracts: {base_contracts} → Adjusted contracts: {adjusted_contracts}")
        print(f"  Helper function result: {helper_adjusted_contracts}")
        
        # Find which event is causing the risk level
        for event in test_events:
            event_time = datetime.fromisoformat(event['datetime'])
            time_diff = (event_time - datetime.utcnow()).total_seconds() / 60
            if abs(time_diff) < 60 and (event['currency'] == "USD" or event['currency'] == "XAU"):
                print(f"  Affected by: {event['title']} ({event['impact']} impact) in {time_diff:.1f} minutes")

# Run the tests
if __name__ == "__main__":
    print("=== Gold Futures Trading Test ===\n")
    test_gold_futures()
    print("\n=== Test Complete ===")