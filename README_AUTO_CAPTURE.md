# Bulenox Auto Trade Request Capture Tool

## Overview

This tool automatically captures the cURL requests for Bulenox's `/trade` API endpoint by:

1. Rotating through accounts from a CSV file
2. Logging in to each account
3. Triggering a dummy trade (small volume)
4. Capturing the API request and saving it as Python code
5. Storing individual requests for each account

## Files

- `bulenox_auto_capture.py` - The main script
- `accounts.csv` - CSV file containing account credentials
- `trade_request.py` - Latest captured request
- `trade_requests/` - Directory containing all captured requests by account

## Requirements

```
pip install playwright dotenv curlconverter
python -m playwright install
```

## Usage

### Option 1: Using accounts.csv

1. Update `accounts.csv` with your actual Bulenox account credentials:

```
email,password
account1@example.com,pass1
account2@example.com,pass2
account3@example.com,pass3
```

2. Run the script:

```
python bulenox_auto_capture.py
```

### Option 2: Using environment variables

1. Create a `.env` file with your credentials:

```
BULENOX_EMAIL=your_email@example.com
BULENOX_PASSWORD=your_password
```

2. Run the script (it will use environment variables if accounts.csv is not found):

```
python bulenox_auto_capture.py
```

## How It Works

The script will:

1. Try each account in sequence (or use environment variables)
2. Automatically navigate to the trading page
3. Select EURUSD as the trading instrument
4. Set a small volume (0.01)
5. Click the Buy button
6. Capture the trade API request
7. Save the request as Python code in both:
   - `trade_request.py` (latest capture)
   - `trade_requests/email_at_domain_com_trade.py` (per-account capture)
8. Stop after the first successful capture

## Selectors

The script uses multiple selectors for each UI element to maximize compatibility:

- **Symbol/Market Selection**:
  - Input fields with placeholders like 'Search symbol', 'Symbol'
  - Symbol dropdown items
  - Symbol list items
  - Direct input[name='symbol']

- **Volume/Amount Input**:
  - Input fields with placeholders like 'Volume', 'Lot Size', 'Size'
  - Input fields with related class names
  - Input fields near volume-related text
  - Direct input[name='amount']

- **Side Selection**:
  - Dropdown select[name='side']
  - Dropdown with class 'side-selector'

- **Buy/Sell Buttons**:
  - Buttons with text 'Buy' or 'Sell'
  - Buttons with related class names
  - Div elements styled as buttons
  - Submit buttons

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
- You can modify the captured Python request to execute real trades