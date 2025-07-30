import requests
import json
import argparse

def test_futures_api(symbol="GBPUSD", side="buy", quantity=1, stop_loss=1.2500, take_profit=1.2700):
    """Test the futures trading API endpoint"""
    url = "http://localhost:5000/api/trade/futures"
    
    payload = {
        "broker": "bulenox",
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "stopLoss": stop_loss,
        "takeProfit": take_profit
    }
    
    print(f"\nSending futures trade request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test the futures trading API endpoint")
    parser.add_argument("--symbol", type=str, default="GBPUSD", help="Trading symbol (e.g., GBPUSD, EURUSD)")
    parser.add_argument("--side", type=str, default="buy", choices=["buy", "sell"], help="Trade side")
    parser.add_argument("--quantity", type=int, default=1, help="Trade quantity")
    parser.add_argument("--stop-loss", type=float, default=1.2500, help="Stop loss price")
    parser.add_argument("--take-profit", type=float, default=1.2700, help="Take profit price")
    
    args = parser.parse_args()
    
    success = test_futures_api(
        symbol=args.symbol,
        side=args.side,
        quantity=args.quantity,
        stop_loss=args.stop_loss,
        take_profit=args.take_profit
    )
    
    print(f"\nTest {'succeeded' if success else 'failed'}")

if __name__ == "__main__":
    main()