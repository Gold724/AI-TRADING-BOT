# Bulenox Trade Request Tool

This tool provides a simple way to execute trades on the Bulenox trading platform using their API. It includes:

1. A Python implementation of the trade request API
2. A user-friendly script to execute trades

## Files

- `bulenox_trade_request.py` - Core implementation of the Bulenox trade API
- `use_bulenox_trade.py` - Interactive script to execute trades
- `trade_request.py` - Original cURL command captured from Bulenox

## Requirements

```
requests
python-dotenv
```

Install with: `pip install requests python-dotenv`

## Usage

### Option 1: Run the interactive script

```bash
python use_bulenox_trade.py
```

This will prompt you for:
- Your Bulenox authorization token (or read from BULENOX_TOKEN environment variable)
- Trading symbol (default: EURUSD)
- Volume/lot size (default: 0.01)
- Side - buy or sell (default: buy)

### Option 2: Import in your own code

```python
from bulenox_trade_request import execute_bulenox_trade

# Execute a trade
result = execute_bulenox_trade(
    token="YOUR_TOKEN_HERE",
    symbol="EURUSD",
    volume=0.01,
    side="buy",
    trade_type="market"
)

print(result)
```

## Getting Your Token

To get your Bulenox authorization token:

1. Log in to your Bulenox account
2. Open browser developer tools (F12)
3. Go to the Network tab
4. Perform any action that makes an API request
5. Look for requests to bulenox.com
6. Find the "Authorization" header in the request headers
7. Copy the token part (after "Bearer ")

Alternatively, you can use the `bulenox_auto_capture.py` script to automatically capture this token.

## Security Notes

- Never hardcode your token in your scripts
- Use environment variables or secure credential storage
- You can create a `.env` file with `BULENOX_TOKEN=your_token_here`

## Disclaimer

This tool is for educational purposes only. Use at your own risk. Always verify trades before execution in a production environment.