import requests
import json
import sys

def test_futures_trade():
    # API endpoint
    url = "http://localhost:5000/api/trade/futures"
    
    # Default trade parameters
    trade_data = {
        "broker": "bulenox",
        "symbol": "6EU25",  # Euro FX futures contract
        "side": "buy",
        "quantity": 1,
        "stopLoss": 1.0800,
        "takeProfit": 1.1200
    }
    
    # Allow command line override of symbol
    if len(sys.argv) > 1:
        trade_data["symbol"] = sys.argv[1]
    
    # Allow command line override of side
    if len(sys.argv) > 2:
        trade_data["side"] = sys.argv[2].lower()
    
    print(f"\nSending futures trade request:")
    print(json.dumps(trade_data, indent=2))
    print("\nExecuting trade...")
    
    try:
        # Send the request
        response = requests.post(url, json=trade_data)
        
        # Print the response
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and response.json().get("status") == "success":
            print("\n✅ Trade executed successfully!")
        else:
            print("\n❌ Trade execution failed.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the Flask server is running on http://localhost:5000")

if __name__ == "__main__":
    print("AI Trading Sentinel - Futures Trade Test")
    print("===========================================\n")
    print("Usage: python test_futures_trade.py [symbol] [buy|sell]")
    print("Example: python test_futures_trade.py 6EU25 buy\n")
    
    test_futures_trade()