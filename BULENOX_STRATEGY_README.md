# Bulenox Gold Scalping Strategy

## Tesla 3-6-9 + Fibonacci Position Sizing Model

### Overview

The Bulenox Gold Scalping Strategy combines the Tesla 3-6-9 trade rhythm with an intra-session Fibonacci growth model for position sizing. This hybrid approach provides a structured framework for gold futures trading with clear entry/exit criteria, risk management, and position sizing rules.

### Strategy Objective

- **Target**: $15,000 profit in 28 days
- **Daily Target**: $535.71
- **Risk Management**: Stop trading for the day if daily profit target is hit or daily max drawdown of $267 is reached
- **Position Sizing**: Never exceed 3 contracts per trade (1 is the default)

### Core Strategy Components

#### 1. Tesla 3-6-9 Trading Structure

The trading day is divided into three distinct sessions:

- **Morning Session**: 03:00 - 06:00 NY time
- **Midday Session**: 08:20 - 11:30 NY time
- **Afternoon Session**: 13:00 - 15:30 NY time

Each session executes exactly 3 trades if opportunities arise, for a maximum of 9 trades per day, maintaining the Tesla rhythm: 3 trades per session × 3 sessions per day.

#### 2. Fibonacci Position Sizing

Inside each session, the strategy follows a Fibonacci sequence for per-trade profit targets:

```
$10 → $10 → $20 → $30 → $50 → $80 → $130
```

This sequence resets:
- At the start of each new session
- After a losing trade

Position sizing (number of contracts) may increase proportionally with the Fibonacci sequence, but never exceeds the maximum of 3 contracts per trade.

#### 3. Entry Signals

The strategy enters trades based on the following confluence of signals:

- **VWAP Confluence**: Price interacting with VWAP (Value-Weighted Average Price)
- **Volume Spike**: Significant increase in trading volume
- **Session High/Low Sweep Rejection**: Price sweeps session high/low but fails to continue in that direction

#### 4. Risk Management

- **Daily Profit Target**: $535.71
- **Daily Max Drawdown**: $267
- **Max Contracts**: 3 per trade
- **Default Contracts**: 1 per trade
- **No Opposite Positions**: No long and short positions held simultaneously

#### 5. Exit Logic

- **Take Profit**: ~0.15% from entry price
- **Stop Loss**: ~0.02% from entry price
- **Order Types**: Market orders for entries, limit + stop orders for exits
- **Bracket Orders**: TP/SL brackets attached to each entry

### Configuration Parameters

The strategy is highly configurable through the `bulenox_strategy_config.py` file:

```python
# Core strategy parameters
DAILY_PROFIT_TARGET = 535.71
DAILY_MAX_DRAWDOWN = 267.00
MAX_TRADES_PER_DAY = 9
MAX_CONTRACTS = 3
DEFAULT_CONTRACTS = 1

# Fibonacci sequence configuration
FIBONACCI_PROFIT_SEQUENCE = [10, 10, 20, 30, 50, 80, 130]

# Trading sessions (NY time)
TRADING_SESSIONS = {
    'morning': {'start': time(3, 0), 'end': time(6, 0), 'name': 'Morning Session'},
    'midday': {'start': time(8, 20), 'end': time(11, 30), 'name': 'Midday Session'},
    'afternoon': {'start': time(13, 0), 'end': time(15, 30), 'name': 'Afternoon Session'}
}

# Risk management parameters
MIN_RISK_REWARD_RATIO = 2.5
BASE_TAKE_PROFIT_PERCENT = 0.15
BASE_STOP_LOSS_PERCENT = 0.02
MAX_CONSECUTIVE_LOSSES = 3

# Technical indicators
VWAP_PERIOD = 20
VOLUME_SPIKE_THRESHOLD = 2.0
MIN_VOLUME_RATIO = 1.5
```

### Implementation Details

#### File Structure

- **bulenox_gold_scalping_strategy.py**: Main strategy implementation
- **bulenox_strategy_config.py**: Configuration parameters
- **test_bulenox_strategy.py**: Test suite for validation

#### Key Classes and Methods

**BulenoxGoldScalpingStrategy**

Main strategy class that implements the Tesla 3-6-9 + Fibonacci model:

- **Initialize**: Sets up the strategy with configuration parameters
- **OnData**: Main data processing and signal generation
- **GetCurrentTradingSession**: Determines the current trading session
- **GetCurrentFibonacciTarget**: Gets the current Fibonacci profit target
- **AdvanceFibonacciSequence**: Advances to the next Fibonacci level
- **ResetFibonacciSequence**: Resets the Fibonacci sequence
- **CalculatePositionSize**: Determines position size based on Fibonacci level
- **ShouldStopTradingForDay**: Checks if daily profit/loss limits are reached
- **HasReachedMaxTrades**: Checks if maximum trades for the day are reached
- **HasReachedSessionLimit**: Checks if session trade limit is reached
- **PlaceEntryOrder**: Places entry orders with attached TP/SL brackets
- **OnOrderEvent**: Handles order events (fills, cancellations)
- **HandleOrderFill**: Processes filled orders
- **HandleEntryFill**: Processes entry order fills
- **HandleTakeProfitFill**: Processes take profit order fills
- **HandleStopLossFill**: Processes stop loss order fills
- **CancelRemainingOrders**: Cancels remaining orders in a bracket
- **LogTradeEntry**: Logs trade entry details
- **LogTradeExit**: Logs trade exit details
- **LogDailySummary**: Logs daily performance summary
- **LogSessionAnalysis**: Logs session performance analysis
- **LogFibonacciAnalysis**: Logs Fibonacci sequence progression
- **CalculateMaxConsecutiveLosses**: Calculates maximum consecutive losses
- **CalculateSharpeRatio**: Calculates Sharpe ratio for performance evaluation

### Deployment

#### QuantConnect Setup

1. Create a new algorithm in QuantConnect
2. Upload the strategy files:
   - bulenox_gold_scalping_strategy.py
   - bulenox_strategy_config.py
3. Set the appropriate backtest parameters:
   - Start date
   - End date
   - Initial capital
4. Run the backtest to validate the strategy

#### Live Trading Setup

1. Ensure the strategy passes all tests in test_bulenox_strategy.py
2. Configure the strategy parameters in bulenox_strategy_config.py
3. Deploy to QuantConnect live trading
4. Connect to Bulenox live account
5. Monitor performance using the built-in logging system

### Performance Tracking

The strategy includes a comprehensive logging system that tracks:

- **Trade Details**: Entry/exit prices, times, quantities
- **Session Performance**: Trades per session, profit/loss per session
- **Fibonacci Progression**: Tracking of Fibonacci sequence advancement
- **Daily Summary**: Daily profit/loss, number of trades, win rate
- **Risk Metrics**: Maximum drawdown, Sharpe ratio, win/loss ratio

### Risk Warnings

- **Market Volatility**: Gold futures can experience significant volatility, especially during economic announcements
- **Slippage**: The strategy assumes minimal slippage, which may not be realistic in all market conditions
- **Execution Delays**: The strategy assumes immediate execution, which may not be realistic in all market conditions
- **Past Performance**: Past performance is not indicative of future results

### Testing and Validation

The strategy includes a comprehensive test suite in test_bulenox_strategy.py that validates:

- Configuration parameters
- Trading session definitions
- Fibonacci sequence logic
- Position sizing calculations
- Risk management rules
- Logging functionality

Run the test suite before deploying to ensure all components are functioning correctly:

```bash
python test_bulenox_strategy.py
```

### Customization

The strategy can be customized by modifying the parameters in bulenox_strategy_config.py:

- **Risk Profile**: Adjust profit targets and drawdown limits
- **Trading Sessions**: Modify session times to target different market hours
- **Fibonacci Sequence**: Adjust the sequence values for different profit targets
- **Technical Indicators**: Tune VWAP period and volume thresholds

### Conclusion

The Bulenox Gold Scalping Strategy combines the structured approach of the Tesla 3-6-9 trading rhythm with the progressive position sizing of the Fibonacci sequence. This hybrid model provides a disciplined framework for gold futures trading with clear entry/exit criteria, risk management rules, and position sizing guidelines.

By following the Tesla rhythm of 3 trades per session across 3 sessions per day, and using the Fibonacci sequence to guide profit targets and position sizing, the strategy aims to achieve consistent profitability while managing risk effectively.