# AI Trading Sentinel 🤖📈

AI Trading Sentinel is an autonomous, broker-integrated platform executing advanced market strategies via browser automation and backend intelligence.

## Features

- **Trade Execution Engine**: Integrates with brokers like Exness, Bulenox, and Binance
- **Strategy Automation**: Scheduled execution via internal Python scheduler
- **API + Backend**: Flask-based RESTful API
- **Frontend Integration**: React/Vite dashboard with real-time strategy control
- **Learning & Optimization**: Saves every trade with timestamp, config, and result
- **Autonomous Heartbeat**: Continuous signal monitoring and trade execution via `heartbeat.py`

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

## Autonomous Trading with Heartbeat

The `heartbeat.py` module provides a fully autonomous trading flow that continuously monitors for signals and executes trades without human intervention.

### How Heartbeat Works

1. **Signal Detection**: Continuously polls for new trade signals from Trae (webhook, API, or local file)
2. **Signal Validation**: Filters signals through rule-based strategy filters (e.g., Fibonacci level, liquidity, time filter)
3. **Broker Login**: Automatically logs into Bulenox using undetected-chromedriver with a saved Chrome profile
4. **Trade Execution**: Places validated trades with proper stop loss and take profit levels
5. **Notification**: Logs results and sends Slack alerts for each trade
6. **Continuous Operation**: Repeats this loop continuously with error handling and recovery

### Running Heartbeat

```bash
python heartbeat.py
```

For cloud deployment, the system is designed to run on platforms like Vast.ai with Docker support:

```bash
docker run -d --name trading-sentinel -v ./logs:/app/logs -v ./.env:/app/.env ai-trading-sentinel python heartbeat.py
```
3. Futures contracts have higher margin requirements than spot trading
4. The system automatically handles the futures trading interface differences

## GitHub Integration and Auto-Updates

The AI Trading Sentinel now includes GitHub integration for automatic updates and version control.

### Setting Up GitHub Integration

1. Configure your GitHub credentials in the `.env` file:
   ```
   GITHUB_REPO=ai-trading-sentinel
   GITHUB_USERNAME=your-username
   GITHUB_PAT=your-personal-access-token
   GITHUB_CHECK_INTERVAL_MINUTES=60
   AUTO_UPDATE_GITHUB=false
   RESTART_AFTER_UPDATE=false
   ```

2. To enable automatic updates, set `AUTO_UPDATE_GITHUB=true`
3. To enable automatic restart after updates, set `RESTART_AFTER_UPDATE=true`

### Using the Auto-Update Launcher

The system includes launcher scripts that handle GitHub updates and automatic restarts:

#### Windows
```powershell
.\start-sentinel-with-autoupdate.ps1
```

#### Linux/Mac
```bash
chmod +x start-sentinel-with-autoupdate.sh
./start-sentinel-with-autoupdate.sh
```

### How Auto-Updates Work

1. The system periodically checks for updates based on the `GITHUB_CHECK_INTERVAL_MINUTES` setting
2. When updates are detected, the system can automatically pull them from GitHub
3. If `RESTART_AFTER_UPDATE` is enabled, the system will restart to apply the updates
4. All update activities are logged and reported via Slack notifications

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

### GitHub Integration Issues

If GitHub integration is not working:

1. Verify your GitHub credentials in the `.env` file
2. Ensure your Personal Access Token has the necessary permissions
3. Check the logs for any GitHub-related error messages