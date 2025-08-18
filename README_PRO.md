# TradeBot Sentinel Advanced Pro 🚀

**Ultimate Trading Automation with Pro-Level Trade Detection & Auto-Execution**

## 🌟 Pro Features

### 🎯 Bulletproof Trade Detection
- **Dual-Criteria Matching**: URL patterns + JSON keyword detection
- **Real-time Network Interception**: Captures ALL POST requests
- **Advanced Fallback Selectors**: Multiple selector strategies for reliability
- **Historical Logging**: Complete audit trail of all detected trades

### 🤖 Auto-Execution Layer
- **Automatic Trade Execution**: Execute detected trades instantly
- **Confirmation Monitoring**: Wait for trade confirmations in dashboard
- **Risk Management**: Built-in safety checks and limits
- **Simulation Mode**: Test without real execution

### 📊 Real-Time Monitoring
- **Live Dashboard**: Monitor trades, status, and performance
- **CSV Logging**: Structured trade data for analysis
- **Screenshot Capture**: Visual debugging on errors
- **Performance Metrics**: Track success rates and timing

### 🔔 Smart Notifications
- **Telegram Integration**: Instant trade alerts
- **Email Notifications**: Backup notification system
- **Custom Alert Rules**: Configure when to notify

## 🚀 Quick Start

### 1. Installation
```bash
# Install dependencies
pip install playwright python-dotenv requests

# Install Playwright browsers
playwright install chromium

# Install curlconverter for Python conversion
pip install curlconverter
```

### 2. Configuration
Edit `.env` file with your credentials:
```env
# Required
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password

# Optional Pro Features
AUTO_EXECUTE=False          # Enable auto-execution
SIMULATION=True            # Safe testing mode
TELEGRAM_TOKEN=your_token  # Telegram notifications
```

### 3. Basic Usage
```bash
# Standard automation (visible browser)
python tradebot_sentinel_advanced_pro.py --visible

# Headless mode
python tradebot_sentinel_advanced_pro.py --headless

# Monitor mode (real-time dashboard)
python tradebot_sentinel_advanced_pro.py --monitor

# Simulation mode (replay logged trades)
python tradebot_sentinel_advanced_pro.py --simulation
```

## 🎮 Operating Modes

### 1. **Automation Mode** (Default)
- Logs into Bulenox platform
- Navigates to trading interface
- Places test order to trigger detection
- Captures and logs all trade requests
- Optionally executes trades automatically

### 2. **Monitor Mode** (`--monitor`)
- Real-time status dashboard
- Live trade count and statistics
- Recent trade history display
- Auto-refresh every 10 seconds

### 3. **Simulation Mode** (`--simulation`)
- Replays previously captured trades
- Safe testing without real execution
- Validates detection logic
- Performance benchmarking

## 🔧 Advanced Configuration

### Trade Detection Patterns
```env
# URL patterns to match
TRADE_URL_PATTERNS=/trade,/orders,/execute,/api/trade,/submit

# Keywords in POST data
TRADE_KEYWORDS=symbol,price,order,amount,buy,sell,quantity,side,type
```

### Auto-Execution Settings
```env
AUTO_EXECUTE=True           # Enable automatic execution
EXECUTION_TIMEOUT=10        # Max execution time (seconds)
CONFIRMATION_RETRIES=5      # Confirmation check attempts
CONFIRMATION_DELAY=2        # Delay between checks (seconds)
```

### Risk Management
```env
MAX_DAILY_TRADES=50         # Daily trade limit
MAX_TRADE_AMOUNT=1000       # Maximum trade size
RISK_CHECK_ENABLED=True     # Enable safety checks
```

### Telegram Notifications
```env
TELEGRAM_TOKEN=bot_token    # Get from @BotFather
TELEGRAM_CHAT_ID=chat_id    # Your chat ID
```

## 📁 Output Files

### Generated Files
- `trade.sh` - Latest cURL command (always updated)
- `trade_request_full.py` - Python requests code
- `logs/trade_log.csv` - Structured trade data
- `logs/trade_detections.log` - Detailed detection logs
- `logs/curls/TIMESTAMP.sh` - Historical cURL commands
- `logs/json/TIMESTAMP.json` - Raw POST data

### Log Structure
```
logs/
├── tradebot_advanced_pro.log    # Main application log
├── trade_log.csv                # CSV trade data
├── trade_detections.log         # Detailed detections
├── curls/                       # Historical cURL commands
│   ├── 20241201_143022.sh
│   └── 20241201_143045.sh
└── json/                        # Raw POST data
    ├── 20241201_143022.json
    └── 20241201_143045.json
```

## 🛡️ Safety Features

### Built-in Protections
- **Simulation Mode**: Test without real trades
- **Confirmation Checks**: Verify trade execution
- **Error Screenshots**: Visual debugging
- **Timeout Protection**: Prevent hanging
- **Rate Limiting**: Avoid overwhelming servers

### Risk Controls
- Daily trade limits
- Maximum trade amount caps
- Execution timeout limits
- Confirmation requirements

## 🔍 Troubleshooting

### Common Issues

**Login Failed**
```bash
# Check credentials in .env
# View screenshot: login_failed.png
# Check logs for specific error
```

**No Trades Detected**
```bash
# Verify URL patterns in .env
# Check keyword matching
# Enable debug logging
```

**Auto-Execution Failed**
```bash
# Check trade.sh file exists
# Verify bash/curl availability
# Review execution logs
```

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python tradebot_sentinel_advanced_pro.py --visible
```

## 📊 Performance Monitoring

### Key Metrics
- **Detection Rate**: Trades captured vs missed
- **Execution Success**: Successful auto-executions
- **Response Time**: Average detection latency
- **Error Rate**: Failed operations percentage

### Monitoring Dashboard
```
==================================================
📊 TRADEBOT SENTINEL ADVANCED PRO - MONITOR
==================================================
🕐 Time: 2024-12-01 14:30:22
📈 Daily Trade Count: 15
🎯 Last Trade Status: Confirmed
🤖 Auto Execute: ✅
🎮 Simulation: ❌

📋 Recent Trades:
   20241201_143022,BTCUSDT,BUY,0.001,45000,detected
   20241201_143045,ETHUSDT,SELL,0.1,3200,executed
```

## 🔗 Integration Examples

### Telegram Bot Setup
1. Create bot with @BotFather
2. Get bot token
3. Get your chat ID
4. Add to .env file

### Custom Webhooks
```python
# Add to handle_detected_trade method
async def send_webhook(self, trade_data):
    webhook_url = "https://your-webhook.com/trade"
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=trade_data)
```

## 🚨 Important Notes

### Security
- Never commit .env file to version control
- Use strong, unique passwords
- Enable 2FA on trading accounts
- Monitor logs for suspicious activity

### Legal & Compliance
- Ensure compliance with platform ToS
- Understand regulatory requirements
- Use simulation mode for testing
- Maintain proper audit trails

### Performance
- Monitor system resources
- Adjust timeouts for your network
- Use headless mode for production
- Regular log cleanup recommended

## 📈 Advanced Usage

### Custom Trade Logic
```python
# Extend the TradeBotSentinelAdvancedPro class
class CustomTradeBot(TradeBotSentinelAdvancedPro):
    async def custom_trade_filter(self, request):
        # Add your custom logic here
        return True
```

### Batch Processing
```bash
# Process multiple accounts
for account in accounts.txt; do
    BULENOX_USERNAME=$account python tradebot_sentinel_advanced_pro.py
done
```

### API Integration
```python
# Convert to REST API
from fastapi import FastAPI
app = FastAPI()

@app.post("/start-bot")
async def start_bot():
    bot = TradeBotSentinelAdvancedPro()
    return await bot.run_automation()
```

## 🆘 Support

For issues, questions, or feature requests:
1. Check the logs first
2. Review this documentation
3. Test in simulation mode
4. Capture screenshots of errors
5. Provide detailed error descriptions

---

**⚠️ Disclaimer**: This tool is for educational and automation purposes. Users are responsible for compliance with platform terms of service and applicable regulations. Always test thoroughly in simulation mode before enabling auto-execution.

**🔒 Security**: Keep your credentials secure and never share your .env file. Monitor your accounts regularly for unauthorized activity.

**📊 Performance**: Results may vary based on network conditions, platform changes, and configuration. Regular updates and monitoring are recommended.