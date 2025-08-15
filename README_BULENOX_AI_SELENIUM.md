# Bulenox AI Selenium Module

An AI-enhanced Selenium automation module for the Bulenox trading platform, designed to provide reliable login and trading operations with adaptive techniques. Now fully integrated with the TRAE AI Trading Sentinel for automated trading execution.

## Features

- **AI-Enhanced Element Detection**: Uses weighted selectors and adaptive approaches to find UI elements reliably
- **Robust Login Process**: Handles various login scenarios with intelligent error recovery
- **Trading Operations**: Supports placing trades with futures contracts
- **Comprehensive Logging**: Detailed logging and screenshot capture for debugging
- **Performance Monitoring**: Tracks and visualizes login and operation performance
- **TRAE AI Integration**: Fully integrated with TRAE AI for automated signal execution
- **Dreamer Mode Support**: Simulated trading for testing and strategy validation
- **Cloud Deployment Ready**: Scripts for deploying to Contabo VPS
- **Secure API Endpoints**: Authenticated REST API for trade execution and monitoring

## Key Differences: Bulenox vs. Exness

| Feature | Bulenox | Exness |
|---------|---------|--------|
| **Trading Unit** | Contracts (1, 3, etc.) | Lot Sizes (0.01, 0.02, etc.) |
| **Market Type** | Primarily Futures | Primarily Spot |
| **Symbol Format** | Futures Codes (e.g., GC for Gold) | Standard Forex Pairs (e.g., XAUUSD) |

## Installation

### Prerequisites

- Python 3.7+
- Chrome browser installed
- ChromeDriver (automatically managed by webdriver-manager)

### Required Python Packages

```bash
pip install selenium webdriver-manager python-dotenv numpy matplotlib
```

## Configuration

Create a `.env` file in the project root with the following variables:

```
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
BULENOX_PROFILE_PATH=C:\Users\YourUser\AppData\Local\Google\Chrome\User Data
BULENOX_PROFILE_NAME=Profile 1
```

## Usage

### Basic Login

```python
from bulenox_ai_selenium import login_bulenox_ai

# Initialize and login
bulenox_instance = login_bulenox_ai(debug=True)

# Close when done
bulenox_instance.close()
```

### Placing a Trade

```python
from bulenox_ai_selenium import login_bulenox_ai, place_bulenox_trade

# Place a trade
success = place_bulenox_trade(
    symbol="EURUSD",
    side="buy",
    quantity=1,  # Number of contracts
    stop_loss=30,  # In pips
    take_profit=50,  # In pips
    debug=True
)



## TRAE AI Integration

### Bulenox AI Controller

The `bulenox_ai_controller.py` module provides a high-level interface for integrating Bulenox trading with the TRAE AI system. It supports both real trading and simulated trading via Dreamer Mode.

```python
from bulenox_ai_controller import BulenoxAIController

# Initialize controller
controller = BulenoxAIController()

# Start a session
controller.start_session(headless=False, debug=True)

# Execute a trade
signal = {
    "symbol": "EURUSD",
    "direction": "BUY",
    "quantity": 1,
    "take_profit": 50,
    "stop_loss": 30
}
result = controller.execute_trade(signal)

# Check session health
health = controller.check_session_health()

# Toggle Dreamer Mode
controller.toggle_dreamer_mode(enabled=True)

# End session when done
controller.end_session()
```

### Command Line Interface

```bash
# Start a Bulenox session
python bulenox_ai_controller.py --start-session

# Execute a trade from a JSON signal file
python bulenox_ai_controller.py --execute test/test_bulenox_signal.json

# Toggle Dreamer Mode
python bulenox_ai_controller.py --dreamer on

# Check session status
python bulenox_ai_controller.py
```

### API Endpoints

The `api/bulenox_endpoints.py` module provides REST API endpoints for interacting with the Bulenox AI Controller.

#### Available Endpoints

- **GET /api/bulenox/status**: Get the status of the Bulenox AI Controller
- **POST /api/bulenox/session/start**: Start a Bulenox trading session
- **POST /api/bulenox/session/end**: End the Bulenox trading session
- **POST /api/bulenox/trade/execute**: Execute a trade based on a signal
- **POST /api/bulenox/dreamer/toggle**: Toggle Dreamer Mode
- **GET /api/bulenox/logs**: Get Bulenox trade logs
- **GET /api/bulenox/test/signal**: Get a test signal for validation

#### Example API Requests

```bash
# Get status
curl -X GET http://localhost:5000/api/bulenox/status -H "X-API-Key: your_api_key"

# Start session
curl -X POST http://localhost:5000/api/bulenox/session/start \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"headless": true, "debug": true}'

# Execute trade
curl -X POST http://localhost:5000/api/bulenox/trade/execute \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "direction": "BUY", "quantity": 1, "take_profit": 50, "stop_loss": 30}'
```

### Complete Example

```python
from bulenox_ai_selenium import login_bulenox_ai, place_bulenox_trade

# Login to Bulenox
bulenox = login_bulenox_ai(debug=True)

if bulenox:
    # Place a trade
    success = place_bulenox_trade(
        symbol="EURUSD",
        side="buy",
        quantity=1,
        stop_loss=30,
        take_profit=50,
        debug=True
    )
    
    print(f"Trade placed successfully: {success}")
    
    # Close the browser when done
    bulenox.close()
```

## Cloud Deployment

The TRAE AI Trading Sentinel with Bulenox AI Selenium integration can be deployed to a Contabo VPS using the provided deployment scripts.

### Deploying to Contabo VPS (Linux/Ubuntu)

1. **SSH into your Contabo VPS**:
   ```bash
   ssh root@your-contabo-ip
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ai-trading-sentinel.git /opt/trae-ai-sentinel
   cd /opt/trae-ai-sentinel
   ```

3. **Run the deployment script**:
   ```bash
   chmod +x deploy/contabo_deploy.sh
   ./deploy/contabo_deploy.sh
   ```

4. **Update Bulenox credentials**:
   ```bash
   nano /opt/trae-ai-sentinel/.env
   ```
   Update the `BULENOX_USERNAME`, `BULENOX_PASSWORD`, and `BULENOX_PROFILE_PATH` values.

5. **Restart services**:
   ```bash
   supervisorctl restart trae:
   ```

### Deploying from Windows to Contabo VPS

1. **Open PowerShell as Administrator**

2. **Navigate to the repository**:
   ```powershell
   cd C:\path\to\ai-trading-sentinel
   ```

3. **Run the deployment script**:
   ```powershell
   .\deploy\contabo_deploy.ps1
   ```

4. **Follow the on-screen instructions**

## Troubleshooting

### Chrome Profile Issues

If you encounter issues with Chrome profiles:

1. **Create a new Chrome profile**:
   - Open Chrome and go to `chrome://settings/profiles`
   - Create a new profile
   - Sign in to your Google account (optional)
   - Close Chrome

2. **Update the profile path**:
   - Update the `BULENOX_PROFILE_PATH` in your `.env` file to point to the new profile directory

3. **Clear browser cache**:
   - Open Chrome with the profile
   - Go to `chrome://settings/clearBrowserData`
   - Clear browsing data
   - Close Chrome

### Selenium Issues

1. **Update undetected-chromedriver**:
   ```bash
   pip install --upgrade undetected-chromedriver
   ```

2. **Check Chrome version**:
   - Make sure your Chrome browser version is compatible with the installed chromedriver
   - You can check your Chrome version by going to `chrome://settings/help`

3. **Enable debug mode**:
   - Run the controller with debug mode enabled to see detailed logs
   ```bash
   python bulenox_ai_controller.py --start-session --debug
   ```

## Security Considerations

1. **API Key Protection**:
   - Keep your API key secure
   - Use HTTPS for all API communications
   - Rotate API keys regularly

2. **Credential Management**:
   - Store credentials securely (e.g., using environment variables)
   - Do not hardcode credentials in source code
   - Use a secure vault for production deployments

3. **Access Control**:
   - Limit access to the API endpoints
   - Use IP whitelisting if possible
   - Implement rate limiting to prevent abuse

## Monitoring and Maintenance

1. **Log Monitoring**:
   - Check logs regularly for errors and issues
   - Logs are stored in the `logs/bulenox/` directory

2. **Session Health**:
   - Monitor session health using the `/api/bulenox/status` endpoint
   - Restart sessions if they become unresponsive

3. **Trade Verification**:
   - Verify trades using the `/api/bulenox/logs` endpoint
   - Compare executed trades with expected signals

## Advanced Usage

### Manual Trading Operations

```python
from bulenox_ai_selenium import login_bulenox_ai

# Login
bulenox = login_bulenox_ai(debug=True)

if bulenox:
    try:
        # Navigate to trading
        bulenox.navigate_to_trading()
        
        # Search for symbol
        bulenox.search_symbol("EURUSD")  # Will be mapped to futures symbol
        
        # Place trade manually
        bulenox.place_trade(
            symbol="EURUSD",
            side="buy",
            quantity=2,
            stop_loss=1.0850,
            take_profit=1.0950
        )
    finally:
        # Close when done
        bulenox.close()
```

## Testing

Run the test script to verify the AI-enhanced login functionality:

```bash
python test_bulenox_ai_selenium.py
```

This will:
1. Attempt to log in to Bulenox using the AI-enhanced Selenium module
2. Navigate to the trading page
3. Take screenshots of the process
4. Generate a performance comparison visualization
5. Keep the browser open for manual inspection

## Futures Contract Sizes

Bulenox trades futures contracts with the following standard sizes:

- **Gold (XAUUSD → GC)**: 1 contract = 100 troy ounces
- **E-mini S&P 500 (ES)**: 1 contract = $50 × S&P 500 Index
- **Euro FX (EURUSD → 6EU25)**: 1 contract = €125,000
- **British Pound (GBPUSD → MBTQ25)**: 1 contract = £62,500
- **Japanese Yen (USDJPY → 6J25)**: 1 contract = ¥12,500,000

## Troubleshooting

### Screenshots

When debug mode is enabled, screenshots are saved in the `logs/screenshots` directory with timestamps and descriptive names.

### Heartbeat Status

The module maintains a heartbeat status file at `logs/heartbeat_status.txt` that can be monitored to track the current state of operations.

### Common Issues

1. **Chrome crashes on startup**: Try using a different Chrome profile or creating a new one
2. **Login form not found**: Check if the login page structure has changed
3. **Element not found errors**: The AI-enhanced selectors should adapt, but if persistent errors occur, update the selectors in the code

## Advanced Configuration

### Custom Element Selectors

The module uses weighted selectors to find elements. You can customize these in the `BulenoxAISelenium` class initialization:

```python
bulenox = BulenoxAISelenium(debug=True)

# Add a new selector with higher weight
bulenox.selectors["login_button"].insert(0, {
    "by": By.ID,
    "value": "new-login-button-id",
    "weight": 1.0
})
### Symbol Mapping

The module automatically maps common symbols to their futures equivalents. You can customize this mapping:

```python
bulenox = BulenoxAISelenium(debug=True)

# Add or update symbol mapping
bulenox.futures_symbols["USDCAD"] = "6C25"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.