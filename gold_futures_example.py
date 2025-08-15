#!/usr/bin/env python
# gold_futures_example.py - Example of using the news-aware filter for gold futures trading

import os
from datetime import datetime

# Import our news filter functionality
from news_filter import NewsAwareFilter, get_dynamic_contract_size

# Hard-coded configuration (since yaml module might not be available)
def load_config():
    # Return a hard-coded configuration that matches sentinel_config.yml
    return {
        "news_aware_trading": {
            "gold_futures": {
                "enabled": True,
                "symbol": "XAUUSD",
                "use_contracts": True,
                "base_contract_size": 1,
                "max_contract_size": 10
            }
        }
    }

# Main function
def main():
    print("=== Gold Futures Trading Example ===\n")
    
    # Load configuration
    config = load_config()
    gold_config = config.get("news_aware_trading", {}).get("gold_futures", {})
    
    # Check if gold futures trading is enabled
    if not gold_config.get("enabled", False):
        print("Gold futures trading is not enabled in the configuration.")
        return
    
    # Get gold futures symbol from config
    symbol = gold_config.get("symbol", "XAUUSD")
    base_contract_size = gold_config.get("base_contract_size", 1)
    max_contract_size = gold_config.get("max_contract_size", 10)
    
    print(f"Gold Futures Symbol: {symbol}")
    print(f"Base Contract Size: {base_contract_size}")
    print(f"Maximum Contract Size: {max_contract_size}\n")
    
    # Create news filter instance
    news_filter = NewsAwareFilter()
    
    # Check if it's safe to trade
    is_safe, reason = news_filter.is_safe_to_trade(symbol)
    
    print(f"Safe to trade {symbol}: {'Yes' if is_safe else 'No'}")
    if not is_safe:
        print(f"Reason: {reason}")
    
    # Get risk level
    risk_level = news_filter.get_event_risk(symbol)
    print(f"Current risk level: {risk_level}")
    
    # Calculate adjusted contract sizes for different base sizes
    print("\nAdjusted Contract Sizes:")
    for base_size in [1, 2, 5, 10]:
        if base_size <= max_contract_size:
            adjusted_size = get_dynamic_contract_size(symbol, base_size)
            print(f"  Base: {base_size} → Adjusted: {adjusted_size}")
    
    print("\nTrading Decision:")
    if is_safe:
        adjusted_size = get_dynamic_contract_size(symbol, base_contract_size)
        print(f"  Proceed with trading using {adjusted_size} contracts")
    else:
        print(f"  Avoid trading due to high-impact news")

# Run the example
if __name__ == "__main__":
    main()
    print("\n=== Example Complete ===")