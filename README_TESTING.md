# AI Trading Sentinel - Testing Guide

## Overview
This document provides instructions for testing the AI Trading Sentinel system, particularly focusing on the Bulenox integration for both spot and futures trading.

## Available Test Scripts

### 1. Selenium Login Test
**File:** `test_bulenox_selenium.py`

This script tests the basic Selenium integration with Bulenox, opening Chrome with Profile 13 and verifying login with saved credentials.

```bash
python test_bulenox_selenium.py
```

### 2. Futures Trading UI Test
**File:** `test_bulenox_futures.py`

This script tests the Bulenox futures trading interface, allowing you to verify that the system can:
- Navigate to the Bulenox trading page
- Search for futures symbols
- Set quantity, stop loss, and take profit values

```bash
python test_bulenox_futures.py
```

**Note:** This test uses a temporary Chrome profile and requires manual login.

### 3. API Futures Trade Test
**File:** `test_futures_trade.py`

This script tests the backend API for futures trading by sending a POST request to the Flask server.

```bash
python test_futures_trade.py
```

You can override the default symbol and side:

```bash
python test_futures_trade.py 6EU25 buy
```

## Testing Workflow

1. Start the Flask backend server:
   ```bash
   cd backend
   python main.py
   ```

2. Run the Selenium login test to verify Chrome profile integration:
   ```bash
   python test_bulenox_selenium.py
   ```

3. Run the futures trading UI test to verify the trading interface:
   ```bash
   python test_bulenox_futures.py
   ```

4. Run the API futures trade test to verify the backend integration:
   ```bash
   python test_futures_trade.py
   ```

## Troubleshooting

### Chrome Profile Issues

If you encounter errors related to Chrome profiles being in use:

1. Close all Chrome instances
2. Try using a different profile directory in the `.env` file:
   ```
   BULENOX_PROFILE_PATH=C:\Users\Admin\AppData\Local\Google\Chrome\User Data
   BULENOX_PROFILE_NAME=Profile 14
   ```

### Selenium WebDriver Issues

If you encounter WebDriver errors:

1. Update ChromeDriver:
   ```bash
   pip install webdriver-manager --upgrade
   ```

2. Check Chrome version compatibility with the installed ChromeDriver

### API Connection Issues

If the API tests fail:

1. Verify the Flask server is running on port 5000
2. Check for any error messages in the server logs
3. Verify network connectivity between the test script and the server

## Screenshots

All test scripts save screenshots in the `screenshots` directory for debugging purposes.