#!/usr/bin/env python3
"""
Debug Trace Script for Trade Detection Logic

This script isolates the trade detection logic from trae_trade_capture.py 
to debug why chart requests are being falsely detected as trades.
"""

def debug_trade_detection(url, post_data=None):
    """Debug the trade detection logic with the same patterns"""
    print(f"\nDEBUG: Analyzing {url}")
    print(f"POST data: {post_data[:200] if post_data else 'None'}...")
    
    # Trade detection patterns from the script
    trade_url_patterns = ["/api/trade", "/v1/trade", "/trade/execute", "/order", "/position", "/submit", "/place"]
    exclude_patterns = ["/charts", "/data", "/quote", "/price", "/history", "/candles", "/ohlc", "/market-data"]
    
    url_lower = url.lower()
    url_matches = any(pattern in url_lower for pattern in trade_url_patterns)
    is_excluded = any(pattern in url_lower for pattern in exclude_patterns)
    
    print(f"URL matches trade patterns: {url_matches}")
    print(f"URL is excluded: {is_excluded}")
    
    data_matches = False
    keyword_count = 0
    if post_data and not is_excluded:
        pd = post_data.lower()
        trade_keywords = ["order", "trade", "buy", "sell", "quantity", "volume", "side", "market", "limit", "stop", "position", "execute", "place"]
        keyword_count = sum(1 for k in trade_keywords if k in pd)
        data_matches = keyword_count >= 2
        
        # Show which keywords were found
        found_keywords = [k for k in trade_keywords if k in pd]
        print(f"Found trade keywords ({keyword_count}): {found_keywords}")
    
    would_detect = (url_matches and not is_excluded) or data_matches
    print(f"FINAL DECISION: {'TRADE DETECTED' if would_detect else 'NOT A TRADE'}")
    print("-" * 50)
    
    return would_detect

def test_actual_chart_request():
    """Test with the actual chart request that was falsely detected"""
    url = "https://userapi.bulenox.projectx.com/charts"
    
    # This is the post data from the false positive
    post_data = '''{"content":"{\\"resolution\\":\\"240\\",\\"symbol_type\\":\\"futures\\",\\"exchange\\":\\"Futures\\",\\"listed_exchange\\":\\"Futures\\",\\"symbol\\":\\"/GC\\",\\"short_name\\":\\"/GC\\",\\"legs\\":\\"[{\\\\\\"symbol\\\\\\":\\\\\\"}/GC\\\\\\",\\\\\\"pro_symbol\\\\\\":\\\\\\"Futures:/GC\\\\\\"}]\\",\\"id\\":\\"d274156e-4aee-4c50-8de9-b3cc7b01767c\\",\\"name\\":\\"default\\",\\"description\\":\\"\\",\\"charts_symbols\\":\\"{\\\\\\"1\\\\\\":{\\\\\\"symbol\\\\\\":\\\\\\"}/GC\\\\\\"}}\\"'''
    
    debug_trade_detection(url, post_data)

def test_real_trade_requests():
    """Test with simulated real trade requests"""
    print("TESTING REAL TRADE REQUESTS:")
    
    # Test 1: Actual trade execution
    debug_trade_detection(
        "https://bulenox.projectx.com/api/trade/execute",
        '{"symbol":"GOLD","side":"buy","quantity":"0.01","order_type":"market"}'
    )
    
    # Test 2: Order placement
    debug_trade_detection(
        "https://bulenox.projectx.com/v1/order/place", 
        '{"instrument":"/GC","side":"sell","volume":"0.05","type":"limit","price":"2650.50"}'
    )
    
    # Test 3: Chart data (should be excluded)
    debug_trade_detection(
        "https://bulenox.projectx.com/api/charts/data",
        '{"symbol":"/GC","resolution":"240","exchange":"Futures"}'
    )

if __name__ == "__main__":
    print("=" * 60)
    print("DEBUGGING TRADE DETECTION LOGIC")
    print("=" * 60)
    
    print("\n1. Testing the actual chart request that was falsely detected:")
    test_actual_chart_request()
    
    print("\n2. Testing with various real requests:")
    test_real_trade_requests()
    
    print("\nDEBUG COMPLETE")