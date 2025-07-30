import requests
import json
import os

def test_symbol_status_api():
    """Test the symbol status API endpoint"""
    url = "http://localhost:5000/api/account/symbol-status"
    
    print(f"\nSending request to: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse Data:")
            print(json.dumps(data, indent=2))
            
            # Check key fields
            print("\nKey Fields:")
            print(f"Symbol: {data.get('symbol', 'Not found')}")
            print(f"Mode: {data.get('mode', 'Not found')}")
            print(f"Gold Symbol Confirmed: {data.get('gold_symbol_confirmed', 'Not found')}")
            print(f"Evaluation Mode: {data.get('evaluation_mode', 'Not found')}")
            print(f"Trading Rules: {data.get('trading_rules', 'Not found')}")
            print(f"Dev Mode: {data.get('dev_mode', 'Not found')}")
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print("AI Trading Sentinel - Symbol Status API Test")
    print("===========================================\n")
    
    success = test_symbol_status_api()
    
    print(f"\nTest {'succeeded' if success else 'failed'}")

if __name__ == "__main__":
    main()