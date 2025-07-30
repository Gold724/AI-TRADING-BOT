import requests
import json
import sys
import argparse

def test_stealth_trade():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test stealth trade execution')
    parser.add_argument('-s', '--symbol', type=str, default='EURUSD', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('-d', '--side', type=str, default='buy', choices=['buy', 'sell'], help='Trade side (buy or sell)')
    parser.add_argument('-l', '--level', type=int, default=2, choices=[1, 2, 3], help='Stealth level (1-3)')
    parser.add_argument('-q', '--quantity', type=float, default=0.01, help='Trade quantity')
    parser.add_argument('-sl', '--stoploss', type=float, default=1.0800, help='Stop loss price')
    parser.add_argument('-tp', '--takeprofit', type=float, default=1.1200, help='Take profit price')
    
    args = parser.parse_args()
    
    # API endpoint
    url = "http://localhost:5000/api/trade/stealth"
    
    # Trade parameters from command line arguments
    trade_data = {
        "broker": "bulenox",
        "symbol": args.symbol,
        "side": args.side.lower(),
        "quantity": args.quantity,
        "stopLoss": args.stoploss,
        "takeProfit": args.takeprofit,
        "stealth_level": args.level
    }
    
    print(f"\nSending stealth trade request:")
    print(json.dumps(trade_data, indent=2))
    print("\nExecuting trade...")
    
    try:
        # Send the request
        response = requests.post(url, json=trade_data)
        
        # Print the response
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Print detailed error if available
        if response.status_code != 200:
            print(f"\nDetailed Error Information:")
            try:
                error_data = response.json()
                if 'message' in error_data:
                    print(f"Error Message: {error_data['message']}")
                if 'traceback' in error_data:
                    print(f"\nError Traceback:\n{error_data['traceback']}")
                print(f"\nFull Error Data: {error_data}")
            except Exception as e:
                print(f"Could not parse error response: {e}")
                print(f"Raw Response: {response.text}")
        
        if response.status_code == 200 and response.json().get("status") == "success":
            print("\n✅ Trade executed successfully!")
        else:
            print("\n❌ Trade execution failed.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the Flask server is running on http://localhost:5000")

if __name__ == "__main__":
    print("AI Trading Sentinel - Stealth Trade Test")
    print("===========================================\n")
    test_stealth_trade()