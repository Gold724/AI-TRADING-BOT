# Bulenox Trade Request Capture Tool

## Overview

This tool automatically captures the cURL request for Bulenox's `/trade` API endpoint by:

1. Rotating through accounts from a CSV file
2. Logging in to each account
3. Triggering a dummy trade (small volume)
4. Capturing the API request and saving it as Python code

## Files

- `bulenox_capture_auto.py` - The main script
- `accounts.csv` - CSV file containing account credentials
- `trade_request.py` - Output file (will be created when a request is captured)

## Requirements

```
pip install playwright curlconverter
python -m playwright install
```

## Usage

1. Update `accounts.csv` with your actual Bulenox account credentials
2. Run the script:

```
python bulenox_capture_auto.py
```

3. The script will:
   - Try each account in sequence
   - Automatically navigate to the trading page
   - Select EURUSD as the trading instrument
   - Set a small volume (0.01)
   - Click the Buy button
   - Capture the trade API request
   - Save the request as Python code in `trade_request.py`

## Selectors

The script uses multiple selectors for each UI element to maximize compatibility:

- **Symbol/Market Selection**:
  - Input fields with placeholders like 'Search symbol', 'Symbol'
  - Symbol dropdown items
  - Symbol list items

- **Volume/Amount Input**:
  - Input fields with placeholders like 'Volume', 'Lot Size', 'Size'
  - Input fields with related class names
  - Input fields near volume-related text

- **Buy/Sell Buttons**:
  - Buttons with text 'Buy' or 'Sell'
  - Buttons with related class names
  - Div elements styled as buttons

## Troubleshooting

If the script fails to capture the trade request:

1. Check the console output for errors
2. Verify your account credentials
3. Inspect the Bulenox trading interface to identify any changes in selectors
4. Update the selectors in the script if necessary

## Notes

- The script uses a small trade volume (0.01) to minimize impact
- It stops after the first successful capture
- The captured request will include all headers and authentication tokens