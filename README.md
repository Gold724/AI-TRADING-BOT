# AI Trading Sentinel

AI Trading Sentinel is an autonomous, broker-integrated platform executing advanced market strategies via browser automation and backend intelligence.

## Features

- **Trade Execution Engine**: Integrates with brokers like Exness, Bulenox, and Binance
- **Strategy Automation**: Scheduled execution via internal Python scheduler
- **API + Backend**: Flask-based RESTful API
- **Frontend Integration**: React/Vite dashboard with real-time strategy control
- **Learning & Optimization**: Saves every trade with timestamp, config, and result

## Setup Instructions

### 1. Environment Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update with your credentials

### 2. Broker Setup

#### Bulenox Setup

1. Run the setup script to configure your Chrome profile for Bulenox:
   ```
   python setup_bulenox_profile.py
   ```
2. Log in to Bulenox with your credentials when the browser opens
3. Update your `.env` file with the correct Chrome profile settings
4. Restart the Flask server

### 3. Running the System

#### Backend

Start the Flask server:
```
python backend/main.py
```

The server will run on http://localhost:5000 with the following endpoints:
- `/api/health` - Health check endpoint
- `/api/strategies` - List available trading strategies
- `/api/trade` - Execute a trade
- `/api/trade/history` - View trade history

#### Frontend (Coming Soon)

Start the React frontend:
```
cd frontend
npm install
npm run dev
```

## Trading Strategies

The system supports various trading strategies including:
- Liquidity Logic (Smart Money Concepts)
- Volume-Weighted Signals
- Fibonacci Entries + Bollinger Confluence
- Fair Value Gaps (FVG), Order Blocks, and OTE

## API Usage

### Execute a Trade

```bash
curl -X POST http://localhost:5000/api/trade \
  -H "Content-Type: application/json" \
  -d '{"broker":"bulenox","symbol":"EURUSD","side":"buy","quantity":0.01,"stopLoss":1.0800,"takeProfit":1.1200}'
```

## Futures Trading

The system supports trading futures contracts through the Bulenox broker.

### Futures Symbol Format

Futures symbols follow a specific format, for example:
- `6EU25` - Euro FX futures contract expiring in 2025
- `6J25` - Japanese Yen futures contract expiring in 2025
- `ES25` - E-mini S&P 500 futures contract expiring in 2025

### Execute a Futures Trade

```bash
curl -X POST http://localhost:5000/api/trade/futures \
  -H "Content-Type: application/json" \
  -d '{"broker":"bulenox","symbol":"6EU25","side":"buy","quantity":1,"stopLoss":1.0800,"takeProfit":1.1200}'
```

### Futures Trading Tips

1. Always verify the correct symbol format for the futures contract you want to trade
2. Be aware of contract specifications including tick size, multiplier, and expiration dates
3. Futures contracts have higher margin requirements than spot trading
4. The system automatically handles the futures trading interface differences

## Troubleshooting

### Chrome Profile Issues

If you encounter issues with Chrome profiles:

1. Make sure Chrome is not running when you start the setup script
2. Try using a different Chrome profile by updating the `.env` file
3. Check that the Chrome WebDriver is compatible with your Chrome version

### Trade Execution Failures

If trades fail to execute:

1. Check the server logs for error messages
2. Verify that you're logged in to the broker platform
3. Run the setup script again to refresh your login session