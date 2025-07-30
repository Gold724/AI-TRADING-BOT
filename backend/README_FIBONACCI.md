# Fibonacci Retest Reentry Strategy

## Overview
The Fibonacci Retest Reentry Strategy (FibRakai) is a modular trading agent that implements a Fibonacci-based retest strategy using Python. The strategy:

- Enters trades at Fibonacci-based price levels
- Closes partial positions at defined Fibonacci targets
- Detects retests for reentry
- Operates without broker API (uses Selenium for UI trading on Bulenox)

## Architecture

### Components

1. **FibonacciExecutor** (`utils/executor_fibonacci.py`)
   - Extends the `StealthExecutor` class
   - Implements Fibonacci retest strategy logic
   - Handles trade execution, monitoring, and reentry

2. **API Endpoint** (`backend/main.py`)
   - `/api/trade/fibonacci` endpoint for triggering the strategy
   - Accepts JSON payload with trade parameters

3. **Test Script** (`test_fibonacci_executor.py`)
   - Command-line tool for testing the Fibonacci strategy

### Fibonacci Levels

The strategy uses the following Fibonacci levels:
- 0.382
- 0.500
- 0.618
- 0.705
- 0.786

Partial take profits are distributed across these levels with the following percentages:
- Level 1 (0.382): 30% of position
- Level 2 (0.500): 20% of position
- Level 3 (0.618): 20% of position
- Level 4 (0.705): 20% of position
- Level 5 (0.786): 10% of position

## Usage

### API Endpoint

Send a POST request to `/api/trade/fibonacci` with the following JSON payload:

```json
{
  "symbol": "EURUSD",
  "side": "buy",
  "quantity": 0.1,
  "entry": 1.0850,
  "fib_low": 1.0800,
  "fib_high": 1.0900,
  "stopLoss": 1.0780,
  "takeProfit": 1.0950,
  "stealth_level": 2
}
```

#### Required Parameters

- `symbol`: Trading symbol
- `side`: Trade direction ("buy" or "sell")
- `quantity`: Trade size
- `entry`: Entry price
- `fib_low`: Lower bound of Fibonacci range
- `fib_high`: Upper bound of Fibonacci range

#### Optional Parameters

- `stopLoss`: Stop loss price
- `takeProfit`: Take profit price
- `stealth_level`: Level of stealth for browser automation (1-3)
- `direction`: Explicitly set direction ("long" or "short"), otherwise derived from `side`

### Test Script

Run the test script to test the Fibonacci executor:

```bash
python test_fibonacci_executor.py --symbol EURUSD --side buy --quantity 0.1 --entry 1.0850 --fib_low 1.0800 --fib_high 1.0900
```

Additional options:

```bash
python test_fibonacci_executor.py --help
```

## Strategy Logic

1. **Initial Trade Placement**:
   - Place trade at the specified entry price
   - Set stop loss and take profit if provided

2. **Fibonacci Target Calculation**:
   - Calculate Fibonacci targets based on the provided range
   - For long trades: targets = fib_low + (fib_high - fib_low) * fib_level
   - For short trades: targets = fib_high - (fib_high - fib_low) * fib_level

3. **Partial Position Closing**:
   - Monitor price movements
   - Close partial positions at each Fibonacci target
   - Use predefined percentages for each level

4. **Retest Detection and Reentry**:
   - After taking partial profits, monitor for price rejection and retest
   - When a retest is detected, regenerate signal and reenter the trade
   - Continue the process for subsequent Fibonacci levels

## Implementation Details

### Stealth Features

The Fibonacci executor inherits stealth features from the `StealthExecutor` class:

- Random user agent rotation
- Human-like typing and mouse movements
- Anti-detection measures for automated browsers
- Proxy support (at higher stealth levels)

### Browser Automation

The strategy uses Selenium with undetected-chromedriver to interact with the Bulenox trading platform:

- Navigates to the trading interface
- Selects trading symbols
- Sets trade parameters (quantity, stop loss, take profit)
- Executes trades via UI elements
- Monitors price movements for strategy execution

## Dependencies

- Python 3.7+
- Flask
- Selenium
- undetected-chromedriver
- Chrome browser with saved profile