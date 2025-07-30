import requests
import json
import argparse
import os
from datetime import datetime

def test_stealth_webhook():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test stealth trade webhook')
    parser.add_argument('-i', '--ip', type=str, default='127.0.0.1', help='Server IP address')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Server port')
    parser.add_argument('-s', '--symbol', type=str, default='GOLD', help='Trading symbol')
    parser.add_argument('-e', '--entry', type=float, default=2375, help='Entry price')
    parser.add_argument('-d', '--direction', type=str, default='long', choices=['long', 'short'], help='Trade direction')
    parser.add_argument('-q', '--quantity', type=float, default=0.01, help='Trade quantity')
    
    args = parser.parse_args()
    
    # API endpoint
    url = f"http://{args.ip}:{args.port}/api/trade/stealth"
    
    # Convert 'long'/'short' to 'buy'/'sell' for the API
    side = "buy" if args.direction.lower() == "long" else "sell"
    
    # Trade parameters from command line arguments
    trade_data = {
        "symbol": args.symbol,
        "side": side,  # API expects 'buy' or 'sell'
        "quantity": args.quantity,
        "entry": args.entry,
        "direction": args.direction,  # Include original direction for reference
        "stealth_level": 2  # Default stealth level
    }
    
    print("\n🧠 O.R.I.G.I.N. — Trade Relay System Activated")
    print("===========================================\n")
    print(f"📡 Sending webhook to: {url}")
    print(f"📊 Payload:")
    print(json.dumps(trade_data, indent=2))
    print("\n⏳ Executing trade...")
    
    try:
        # Send the request
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=trade_data, headers=headers, timeout=60)
        
        # Print the response
        print(f"\n📬 Response Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"📄 Response Body: {json.dumps(response_json, indent=2)}")
            
            # Check for success
            if response.status_code == 200 and response_json.get("status") == "success":
                print("\n✅ Trade signal successfully relayed!")
                print("\n🔍 Expected outcomes:")
                print("  ✓ Bot logged into Bulenox using stealth automation")
                print("  ✓ Executed the trade or simulated it in demo mode")
                print("  ✓ Sent prophetic alert to Slack (if configured)")
                print("  ✓ Logged trade session to status.json")
                print("  ✓ Saved screenshots to /logs/screens/ folder")
                
                # Check for screenshots
                screenshots_dir = os.path.join(os.getcwd(), "logs", "screenshots")
                if os.path.exists(screenshots_dir):
                    recent_screenshots = [f for f in os.listdir(screenshots_dir) 
                                        if f.endswith(".png") and 
                                        datetime.now().strftime("%Y%m%d") in f]
                    if recent_screenshots:
                        print(f"\n📸 Recent screenshots ({len(recent_screenshots)}):")
                        for i, screenshot in enumerate(sorted(recent_screenshots, reverse=True)[:5]):
                            print(f"  {i+1}. {screenshot}")
            else:
                print("\n❌ Trade relay failed.")
                
                # Print detailed error if available
                if response_json and 'message' in response_json:
                    print(f"\n⚠️ Error Message: {response_json['message']}")
                if response_json and 'traceback' in response_json:
                    print(f"\n🔍 Error Details:\n{response_json['traceback']}")
                    
                # Check logs directory for error information
                logs_dir = os.path.join(os.getcwd(), "logs")
                if os.path.exists(logs_dir):
                    print("\n📋 Checking logs for additional information...")
                    
                    # Check stealth_trades.json
                    stealth_log_path = os.path.join(logs_dir, "stealth_trades.json")
                    if os.path.exists(stealth_log_path):
                        try:
                            with open(stealth_log_path, 'r') as f:
                                stealth_logs = json.load(f)
                                if stealth_logs and isinstance(stealth_logs, list) and len(stealth_logs) > 0:
                                    latest_log = stealth_logs[-1]
                                    print(f"\n📝 Latest stealth trade log:")
                                    print(json.dumps(latest_log, indent=2))
                        except Exception as e:
                            print(f"Could not read stealth_trades.json: {e}")
                    
                    # Check status.json
                    status_log_path = os.path.join(logs_dir, "status.json")
                    if os.path.exists(status_log_path):
                        try:
                            with open(status_log_path, 'r') as f:
                                status_data = json.load(f)
                                if 'trades' in status_data and len(status_data['trades']) > 0:
                                    latest_status = status_data['trades'][-1]
                                    print(f"\n📊 Latest status log:")
                                    print(json.dumps(latest_status, indent=2))
                        except Exception as e:
                            print(f"Could not read status.json: {e}")
        except Exception as e:
            print(f"\n⚠️ Could not parse JSON response: {e}")
            print(f"📄 Raw Response: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n⚠️ Make sure the Flask server is running at the specified address")
        print(f"   URL: {url}")
    except requests.exceptions.Timeout:
        print("\n⚠️ Request timed out after 60 seconds")
        print("The server might be processing the request but taking too long to respond")
        print("Check the server logs and screenshots directory for any activity")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")

    print("\n🌑 Stealth signal ripple complete.")

if __name__ == "__main__":
    test_stealth_webhook()