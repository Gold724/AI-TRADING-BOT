# TradeBot Sentinel — Automation Agent

🤖 **Expert automation agent specialized in interacting with Bulenox ProjectX's trading platform via Playwright**

## Overview

TradeBot Sentinel is a powerful automation agent that provides:

- **Secure Login**: Environment-based credential management with robust fallback selectors
- **Modal Handling**: Automatic detection and dismissal of Time Sync Warning modals
- **Dashboard Confirmation**: Multi-selector approach for reliable login verification
- **Trading Navigation**: Intelligent navigation to trading interfaces with retry logic
- **Order Placement**: Robust order placement with ORDER tab, DOM tab, and generic fallbacks
- **Network Interception**: Real-time capture of trade execution requests
- **Code Generation**: Automatic cURL and Python requests code generation
- **Error Handling**: Comprehensive screenshot capture and verbose logging
- **Retry Logic**: Built-in retry mechanisms for handling dynamic UI elements

## Quick Start

### 1. Setup Environment

```bash
# Run the setup script
python setup_automation.py
```

This will:
- Install required Python packages
- Install Playwright Chromium browser
- Create environment variables template
- Validate the setup

### 2. Configure Credentials

```bash
# Copy the template
cp .env.template .env

# Edit .env with your credentials
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
```

### 3. Run Automation

```bash
# Headless mode (default)
python tradebot_sentinel_automation.py

# Visible mode (for debugging)
python tradebot_sentinel_automation.py --visible
```

## Features

### 🔐 Secure Authentication
- Environment variable-based credential management
- Robust fallback selectors for login elements
- Automatic handling of Time Sync Warning modals
- Multi-selector dashboard confirmation

### 🎯 Trading Automation
- Intelligent navigation to trading interfaces
- Multiple selector strategies (ORDER tab → DOM tab → generic)
- Retry logic for dynamic UI elements
- Screenshot capture on critical failures

### 🌐 Network Interception
- Real-time POST request monitoring
- Trade execution detection via JSON parsing
- Keyword-based filtering (symbol, amount, price, order, trade, buy, sell)
- Automatic cURL command generation

### 🐍 Code Generation
- Automatic conversion of cURL to Python requests
- Full Python code with proper imports and error handling
- Saved as `trade_request_full.py` for immediate use

### 📊 Comprehensive Logging
- Verbose console output for every step
- Error screenshots with timestamps
- Network request/response logging
- Detailed selector fallback tracking

## File Structure

```
ai-trading-sentinel/
├── tradebot_sentinel_automation.py    # Main automation script
├── setup_automation.py                # Setup and validation script
├── requirements_automation.txt        # Python dependencies
├── README_AUTOMATION.md               # This documentation
├── .env.template                      # Environment variables template
├── .env                              # Your credentials (create from template)
├── trade.sh                          # Generated cURL command
├── trade_request_full.py             # Generated Python requests code
└── screenshots/                      # Error screenshots directory
```

## Generated Files

### `trade.sh`
Contains the intercepted cURL command:
```bash
curl -X POST 'https://api.bulenox.projectx.com/trade' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer token...' \
  -d '{"symbol":"BTCUSDT","amount":100,"price":50000}'
```

### `trade_request_full.py`
Full Python implementation:
```python
import requests
import json

def execute_trade():
    url = 'https://api.bulenox.projectx.com/trade'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token...'
    }
    data = {
        'symbol': 'BTCUSDT',
        'amount': 100,
        'price': 50000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Trade execution failed: {e}")
        return None

if __name__ == "__main__":
    result = execute_trade()
    print(f"Trade result: {result}")
```

## Troubleshooting

### Common Issues

1. **Login Failed**
   - Verify credentials in `.env` file
   - Check if Time Sync modal is blocking login
   - Run in visible mode to debug: `python tradebot_sentinel_automation.py --visible`

2. **Trading Interface Not Found**
   - Ensure you're on the correct trading page
   - Check if page structure has changed
   - Review screenshot in `screenshots/` directory

3. **No Trade Requests Intercepted**
   - Verify network interception is working
   - Check console logs for POST request detection
   - Ensure trade execution actually occurred

4. **cURL Conversion Failed**
   - Install curlconverter: `pip install curlconverter`
   - Check if `trade.sh` file was created correctly
   - Verify cURL command syntax

### Debug Mode

Run with visible browser for debugging:
```bash
python tradebot_sentinel_automation.py --visible
```

This will:
- Show browser window
- Slow down interactions
- Display detailed console output
- Capture screenshots on errors

## Security Notes

- Never commit `.env` file to version control
- Store credentials securely
- Use environment variables in production
- Regularly rotate authentication tokens
- Monitor generated trade requests before execution

## Requirements

- Python 3.7+
- Playwright
- curlconverter
- python-dotenv
- requests
- aiohttp

See `requirements_automation.txt` for complete list.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review console logs and error screenshots
3. Run in visible mode for debugging
4. Verify environment setup with `python setup_automation.py`

---

**TradeBot Sentinel** — Your reliable automation agent for Bulenox ProjectX trading platform.