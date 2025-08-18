# Bulenox cURL Command Capture Tool

This tool automatically logs into Bulenox, places a trade, and captures the API request as a cURL command that can be used for programmatic trading.

## Prerequisites

- Node.js installed
- npm installed

## Setup

1. Install dependencies:

```bash
npm install
```

This will install Playwright and other required dependencies.

2. Set your Bulenox credentials:

Either edit the script directly to replace `your_username` and `XujhMzFf6K` in the batch/shell scripts, or set environment variables:

```bash
# On Windows
set BX64883=your_username
set XujhMzFf6K=your_password

# On Linux/Mac
export BX64883=your_username
export XujhMzFf6K=your_password
```

## Usage

1. Run the script:

```bash
# On Windows PowerShell (recommended)
.\capture_curl.ps1

# On Windows Command Prompt
capture_curl.bat

# On Linux/Mac
bash capture_curl.sh

# Or directly
npm start
# or
node bulenox_trade.js
```

2. The script will:
   - Open a browser window
   - Navigate to Bulenox login page
   - Log in with your credentials
   - Navigate to the trading interface
   - Place a small buy order for GOLD (0.01 lot size)
   - Capture the API request
   - Save the cURL command to `trade.sh`
   - Also save it to `trade_request.py` for compatibility with the existing system

3. Use the captured cURL command:

```bash
# Execute the trade request directly
bash trade.sh

# Or convert to Python using curlconverter
pip install curlconverter
python -c "from curlconverter import convert; print(convert(open('trade.sh').read()))"

# Or use the provided utility
python curl_to_python.py
```

## Troubleshooting

### Node.js Not Found

If you get an error about Node.js not being found:

1. Make sure Node.js is installed and in your PATH
2. Try running the script directly with `node bulenox_trade.js`

### Selector Issues

If the script fails to find elements on the page, you may need to update the selectors. The script includes fallback selectors, but if the Bulenox UI has changed significantly, you might need to:

1. Open Bulenox in your browser
2. Use browser developer tools (F12) to inspect the elements
3. Update the selectors in `bulenox_trade.js`

### Login Issues

If login fails:

1. Check that your credentials are correct
2. Try logging in manually to ensure your account is active
3. Check if Bulenox has implemented additional security measures like CAPTCHA

## Customization

- To place a sell order instead of buy, change the selector to target the sell button
- To trade a different symbol, change 'GOLD' to your desired symbol
- To change the trade amount, modify the '0.01' value

## Security Notes

- The script saves API requests with authentication tokens to local files
- Keep these files secure and do not share them
- Consider adding `trade.sh` and `trade_request.py` to your `.gitignore` file