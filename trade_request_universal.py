
#!/usr/bin/env python3
"""
Generated Python requests code from intercepted trade request
Generated at: 2025-08-15T16:11:46.068773
"""

import requests
import json

# Original cURL command:
# curl -X POST -H "sec-ch-ua-platform: "Windows"" -H "referer: https://www.tradingview.com/" -H "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" -H "sec-ch-ua: "Not;A=Brand";v="99", "HeadlessChrome";v="139", "Chromium";v="139"" -H "content-type: text/plain;charset=UTF-8" -H "sec-ch-ua-mobile: ?0" -d '{"event":"report_stash","params":{"symbol_resolved":[{"c":1,"a":{"symbol":"NASDAQ_DLY:NDX","cluster":null,"userId":"0"}},{"c":1,"a":{"symbol":"SP:SPX","cluster":null,"userId":"0"}},{"c":1,"a":{"symbol":"DJ:DJI","cluster":null,"userId":"0"}},{"c":1,"a":{"symbol":"TVC:NI225","cluster":null,"userId":"0"}},{"c":1,"a":{"symbol":"SP:SPX","cluster":null,"userId":"0"}}],"symbol_resolve_time_frame":[{"v":883.2999999998137,"a":{"symbol":"NASDAQ_DLY:NDX","cluster":null,"userId":"0"}},{"v":888.5999999996275,"a":{"symbol":"SP:SPX","cluster":null,"userId":"0"}},{"v":1211.2000000001863,"a":{"symbol":"DJ:DJI","cluster":null,"userId":"0"}},{"v":1206.5999999996275,"a":{"symbol":"TVC:NI225","cluster":null,"userId":"0"}},{"v":1070.7000000001863,"a":{"symbol":"SP:SPX","cluster":null,"userId":"0"}}]}}' "https://telemetry.tradingview.com/free/report"

def execute_trade_request():
    """Execute the intercepted trade request"""
    try:
        # TODO: Extract and configure these values from the cURL command
        url = "YOUR_TRADING_API_URL"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_API_TOKEN"
        }
        
        data = {
            "symbol": "BTCUSDT",
            "side": "buy",
            "amount": 0.01,
            "type": "market"
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print("✅ Trade executed successfully")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Trade failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error executing trade: {e}")

if __name__ == "__main__":
    execute_trade_request()
