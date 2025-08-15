# Gold Futures Trading with Bulenox

This document provides instructions for executing gold futures trades with Bulenox using the Trae AI Trading Sentinel system.

## Overview

The Trae AI Trading Sentinel system has been updated to support gold futures trading with the following features:

- News-aware trading for gold futures (XAUUSD)
- Contract size adjustment based on news impact
- Integration with Bulenox trading platform

## Configuration

Gold futures trading is configured in the `sentinel_config.yml` file under the `news_aware_trading.gold_futures` section:

```yaml
# Gold futures trading configuration
gold_futures:
  # Enable gold futures trading
  enabled: true
  # Symbol for gold futures
  symbol: "XAUUSD"
  # Use contracts instead of lot sizes for gold futures
  use_contracts: true
  # Base contract size for gold futures
  base_contract_size: 1
  # Maximum allowed contract size
  max_contract_size: 10
```

## News-Aware Trading

The system includes a news-aware filter that adjusts contract sizes based on economic news events:

- High-impact news: Reduces contract size to 25% of base size
- Medium-impact news: Reduces contract size to 50% of base size
- Low-impact news: Reduces contract size to 80% of base size

This helps manage risk during volatile market conditions around major economic announcements.

## Executing Trades

Two scripts are provided for executing gold futures trades:

### 1. Demo Script (No Real Trades)

The `execute_gold_trade.py` script demonstrates the process of logging into Bulenox and preparing a gold futures trade without actually executing it:

```bash
python execute_gold_trade.py
```

### 2. Real Trading Script

The `execute_real_gold_trade.py` script can be used to execute actual trades (currently in simulation mode for safety):

```bash
python execute_real_gold_trade.py
```

To enable real trading, edit the script and uncomment the `executor.execute_trade` line.

## Trade Parameters

When executing a gold futures trade, you need to specify the following parameters:

- **Symbol**: XAUUSD (Gold)
- **Direction**: buy or sell
- **Quantity**: Number of contracts (will be adjusted based on news impact)
- **Entry Price**: Market price or limit price
- **Take Profit**: Target price for profit-taking
- **Stop Loss**: Price level to limit potential losses

## Logging

All trade activities are logged in the following files:

- `logs/trade_log.json`: Records all trade attempts, including success/failure status
- `logs/screenshots/`: Contains screenshots of the trading platform during execution
- `logs/heartbeat_status.txt`: Real-time status updates of the trading system

## Troubleshooting

If you encounter issues with Bulenox login or trade execution:

1. Check that your Chrome profile is correctly configured in the environment variables:
   - `BULENOX_PROFILE_PATH`: Path to Chrome user data directory
   - `BULENOX_PROFILE_NAME`: Profile name (e.g., "Profile 13")

2. Verify that the Bulenox platform is accessible and your account is active

3. Check the log files for specific error messages

## Safety Features

The system includes several safety features:

- News-aware trading to reduce position sizes during high-impact events
- Maximum contract size limits
- Trade logging for audit purposes
- Screenshot capture for verification

## Testing

You can test the news-aware contract size adjustment functionality without executing trades:

```bash
python test_gold_futures.py
```

This will simulate the impact of news events on contract sizing for gold futures trades.