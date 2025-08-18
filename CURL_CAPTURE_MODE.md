# TradeBot Sentinel - cURL Capture Mode 🎯

## Overview

The **cURL Capture Mode** is a specialized automation script that intercepts and captures all network requests from your trading session, converting them into reusable cURL commands. This mode is perfect for:

- **API Reverse Engineering**: Capture the exact requests your browser makes
- **Trade Automation**: Get the precise cURL commands for trade execution
- **Request Analysis**: Understand the complete request flow
- **Integration Development**: Build your own trading bots with captured APIs

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements_curl_capture.txt

# Install Playwright browsers
playwright install chromium

# Configure your .env file
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
BROKER_URL=https://bulenox.projectx.com
```

### 2. Run cURL Capture Mode

**Headless Mode (Default):**
```bash
python tradebot_curl_capture.py
```

**Visible Browser Mode:**
```bash
python tradebot_curl_capture.py --visible
```

## 📋 Capture Process

The script follows these 7 steps exactly as requested:

### Step 1: Open Chromium with Persistent Context
- Launches Chromium browser with persistent session
- Uses stored credentials from `.env` file
- Sets up anti-detection measures

### Step 2: Automatic Login
- Navigates to broker login page
- Automatically fills username/password from environment variables
- Handles various login form selectors with fallbacks
- Detects successful login via dashboard elements

### Step 3: Network Request Interception
- Intercepts ALL POST requests
- Captures requests with `application/json` content-type
- Real-time monitoring of network traffic

### Step 4: Request Saving
For each intercepted request:
- **cURL File**: `logs/curls/YYYYMMDD_HHMMSS_description.curl`
- **JSON Data**: `logs/json/YYYYMMDD_HHMMSS_description.json`
- **Complete Headers**: All headers, cookies, and query parameters
- **Raw POST Data**: Exact payload as sent by browser

### Step 5: Smart Tagging
Requests are automatically tagged based on URL patterns and content:
- `login_auth` - Authentication requests
- `account_info` - Account/profile data requests
- `trade_execution` - Trade/order execution requests
- `portfolio_info` - Portfolio/position requests
- `market_data` - Market price/quote requests
- `api_request` - Generic API calls

### Step 6: Generate trade.sh
- Creates `trade.sh` with the latest trade execution cURL
- Ready-to-use bash script for trade replication
- Includes timestamp and metadata

### Step 7: Completion Confirmation
- Displays capture status for each request type
- Shows "✅ All cURLs Captured" when complete
- Generates final summary report

## 📁 Output Structure

```
ai-trading-sentinel/
├── logs/
│   ├── curls/                    # cURL command files
│   │   ├── 20241201_143022_login_auth.curl
│   │   ├── 20241201_143045_account_info.curl
│   │   └── 20241201_143102_trade_execution.curl
│   ├── json/                     # JSON request data
│   │   ├── 20241201_143022_login_auth.json
│   │   ├── 20241201_143045_account_info.json
│   │   └── 20241201_143102_trade_execution.json
│   ├── curl_capture.log          # Detailed session logs
│   └── capture_error.png         # Error screenshots (if any)
├── trade.sh                      # Latest trade execution cURL
└── tradebot_curl_capture.py      # Main capture script
```

## 🎯 Sample Output Files

### cURL File Example (`logs/curls/20241201_143102_trade_execution.curl`)
```bash
#!/bin/bash
# TradeBot Sentinel - cURL Capture
# Timestamp: 2024-12-01T14:31:02.123456
# URL: https://api.bulenox.projectx.com/v1/orders
# Description: trade_execution

curl -X POST 'https://api.bulenox.projectx.com/v1/orders' \
  -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRF-Token: abc123def456' \
  -d '{
  "symbol": "BTCUSD",
  "side": "buy",
  "amount": 0.001,
  "price": 45000,
  "type": "limit"
}'

# End of cURL command
```

### JSON Data Example (`logs/json/20241201_143102_trade_execution.json`)
```json
{
  "timestamp": "2024-12-01T14:31:02.123456",
  "url": "https://api.bulenox.projectx.com/v1/orders",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "Content-Type": "application/json",
    "X-CSRF-Token": "abc123def456"
  },
  "post_data": "{\"symbol\":\"BTCUSD\",\"side\":\"buy\",\"amount\":0.001,\"price\":45000,\"type\":\"limit\"}",
  "description": "trade_execution"
}
```

## 🔧 Configuration Options

### Environment Variables (.env)
```bash
# Required - Broker Credentials
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password

# Optional - Broker URL
BROKER_URL=https://bulenox.com

# Optional - Capture Settings
MAX_WAIT_TIME=300                # Maximum wait time in seconds
WAIT_INTERVAL=10                 # Check interval in seconds
```

### Command Line Options
```bash
# Run with visible browser (for debugging)
python tradebot_curl_capture.py --visible

# Run in headless mode (default, faster)
python tradebot_curl_capture.py --headless

# Show help
python tradebot_curl_capture.py --help
```

## 📊 Real-time Monitoring

During capture, you'll see real-time logs:

```
2024-12-01 14:30:15 - INFO - 🚀 Starting cURL Capture Mode
2024-12-01 14:30:18 - INFO - 🌐 Navigating to https://bulenox.projectx.com
2024-12-01 14:30:22 - INFO - ✅ Username entered
2024-12-01 14:30:23 - INFO - ✅ Password entered
2024-12-01 14:30:24 - INFO - 🔐 Login submitted
2024-12-01 14:30:27 - INFO - ✅ Login successful - Dashboard loaded
2024-12-01 14:30:30 - INFO - 📝 Captured login_auth: logs/curls/20241201_143030_login_auth.curl
2024-12-01 14:30:35 - INFO - 📝 Captured account_info: logs/curls/20241201_143035_account_info.curl
2024-12-01 14:30:45 - INFO - 📝 Captured trade_execution: logs/curls/20241201_143045_trade_execution.curl
2024-12-01 14:30:46 - INFO - ✅ Generated trade.sh with latest trade execution
2024-12-01 14:30:47 - INFO - 📊 Capture Status: Login ✅ | Account ✅ | Trade ✅
2024-12-01 14:30:47 - INFO - ✅ All cURLs Captured - Session Complete!
```

## 🛡️ Safety Features

- **Error Screenshots**: Automatic screenshots on failures
- **Robust Selectors**: Multiple fallback selectors for each element
- **Retry Logic**: 3 retries with 2-second delays for dynamic elements
- **Graceful Shutdown**: Proper browser cleanup on interruption
- **Secure Logging**: Sensitive data handling in logs

## 🔍 Troubleshooting

### Common Issues

**1. Login Failed**
```bash
# Check credentials in .env
BULENOX_USERNAME=correct_username
BULENOX_PASSWORD=correct_password
```

**2. No Requests Captured**
```bash
# Run in visible mode to debug
python tradebot_curl_capture.py --visible
```

**3. Browser Not Found**
```bash
# Reinstall Playwright browsers
playwright install chromium
```

**4. Permission Errors**
```bash
# Check directory permissions
mkdir -p logs/curls logs/json
chmod 755 logs/curls logs/json
```

### Debug Mode

For detailed debugging, check the log file:
```bash
tail -f logs/curl_capture.log
```

## 🎯 Use Cases

### 1. API Integration
```bash
# Capture trade execution
python tradebot_curl_capture.py --visible

# Use generated trade.sh
bash trade.sh
```

### 2. Request Analysis
```bash
# Analyze captured JSON data
cat logs/json/*_trade_execution.json | jq .
```

### 3. Automation Development
```bash
# Convert cURL to Python requests
curl-to-python < logs/curls/20241201_143102_trade_execution.curl
```

## 📈 Success Metrics

The capture session is considered successful when:
- ✅ **Login cURL**: Authentication request captured
- ✅ **Account cURL**: Account/profile request captured  
- ✅ **Trade cURL**: Trade execution request captured
- ✅ **trade.sh**: Generated with latest trade execution

## 🔗 Integration Examples

### Python Requests
```python
import requests
import json

# Load captured request data
with open('logs/json/20241201_143102_trade_execution.json') as f:
    request_data = json.load(f)

# Execute request
response = requests.post(
    request_data['url'],
    headers=request_data['headers'],
    data=request_data['post_data']
)
```

### Node.js Axios
```javascript
const axios = require('axios');
const fs = require('fs');

// Load captured request
const requestData = JSON.parse(
    fs.readFileSync('logs/json/20241201_143102_trade_execution.json')
);

// Execute request
axios.post(requestData.url, 
    JSON.parse(requestData.post_data),
    { headers: requestData.headers }
);
```

## 🎉 Next Steps

After successful capture:

1. **Analyze Requests**: Review captured cURL commands and JSON data
2. **Test Execution**: Run `bash trade.sh` to test trade execution
3. **Build Integration**: Use captured APIs in your trading bot
4. **Automate Trading**: Implement automated trading logic
5. **Monitor Performance**: Track execution success rates

---

**🎯 TradeBot Sentinel - cURL Capture Mode**  
*Precision Network Request Capture for Trading Automation*

**Status**: ✅ Ready for Production  
**Last Updated**: December 1, 2024  
**Version**: 1.0.0