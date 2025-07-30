# Futures Trading Guide

## Overview

This guide explains how to use the AI Trading Sentinel system for futures trading through the Bulenox platform. The system now supports trading futures contracts with automatic symbol mapping from standard forex symbols to their futures equivalents.

## Supported Futures Symbols

The system supports the following futures symbols:

| Standard Symbol | Futures Symbol | Description |
|----------------|----------------|-------------|
| GBPUSD | MBTQ25 | British Pound futures contract expiring in 2025 |
| EURUSD | 6EU25 | Euro FX futures contract expiring in 2025 |
| USDJPY | 6J25 | Japanese Yen futures contract expiring in 2025 |
| ES | ES25 | E-mini S&P 500 futures contract expiring in 2025 |

## Testing the Futures Trading Functionality

### 1. Test the Bulenox Futures UI

This test opens the Bulenox platform and attempts to navigate to the futures trading interface without executing a trade. It's useful for verifying that the system can access the platform and locate the correct trading elements.

```bash
python test_bulenox_futures_mbtq25.py
```

### 2. Test the Futures Executor

This test verifies that the `BulenoxFuturesExecutor` class can properly map symbols and navigate the trading interface. By default, it tests with the GBPUSD/MBTQ25 symbol.

```bash
python test_futures_executor.py
```

To test all supported futures symbols:

```bash
python test_futures_executor.py --all
```

### 3. Test the API Endpoint

This test verifies that the Flask API endpoint for futures trading is working correctly. It sends a trade request to the API and displays the response.

```bash
python test_api_futures.py
```

You can customize the test parameters:

```bash
python test_api_futures.py --symbol EURUSD --side sell --quantity 2 --stop-loss 1.0800 --take-profit 1.0600
```

## Using the API

### Execute a Futures Trade

To execute a futures trade through the API, send a POST request to the `/api/trade/futures` endpoint:

```bash
curl -X POST http://localhost:5000/api/trade/futures \
  -H "Content-Type: application/json" \
  -d '{"broker":"bulenox","symbol":"GBPUSD","side":"buy","quantity":1,"stopLoss":1.2500,"takeProfit":1.2700}'
```

The system will automatically map the standard symbol (e.g., `GBPUSD`) to its futures equivalent (e.g., `MBTQ25`).

## Troubleshooting

### Symbol Not Found

If the system cannot find a symbol on the Bulenox platform:

1. Verify that the symbol is supported by checking the mapping in the `executor_bulenox_futures.py` file.
2. Check the screenshots in the `logs/screenshots` directory to see what happened during the trade attempt.
3. Try running the `test_bulenox_futures_mbtq25.py` script to see if the system can navigate to the symbol manually.

### Login Issues

If the system cannot log in to the Bulenox platform:

1. Run the `setup_bulenox_profile.py` script to refresh your login session.
2. Check that your Chrome profile is correctly configured in the `.env` file.
3. Verify that the Bulenox platform is accessible from your network.

## Adding New Futures Symbols

To add support for a new futures symbol:

1. Identify the futures symbol format used by the Bulenox platform.
2. Update the `_futures_symbol_map` dictionary in the `executor_bulenox_futures.py` file.
3. Test the new symbol using the `test_futures_executor.py` script.

```python
# Example of adding a new futures symbol mapping
self._futures_symbol_map = {
    "GBPUSD": "MBTQ25",
    "EURUSD": "6EU25",
    "USDJPY": "6J25",
    "ES": "ES25",
    "NEW_SYMBOL": "NEW_FUTURES_SYMBOL",  # Add your new mapping here
}
```