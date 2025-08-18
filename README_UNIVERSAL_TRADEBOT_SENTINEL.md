# 🤖 Universal TradeBot Sentinel

**The Ultimate Trading Platform Automation Agent**

A powerful, configurable automation agent designed to work with any trading platform. Built with Playwright for robust browser automation, network request interception, and automatic code generation.

## 🌟 Key Features

### 🔐 **Secure Authentication**
- Environment variable-based credential management
- Automatic fallback to demo mode when credentials aren't provided
- Support for any trading platform login system

### 🕵️ **Advanced Network Interception**
- Real-time monitoring of all network requests
- Intelligent trade request detection using keyword analysis
- Automatic capture of POST requests with trading-related content

### 🔄 **Automatic Code Generation**
- **cURL Command Generation**: Saves intercepted requests as executable shell scripts
- **Python Requests Conversion**: Automatically converts cURL to Python using `curlconverter`
- Ready-to-use code for trade replication and API integration

### 🎯 **Universal Platform Support**
- **TradingView**: Default configuration for easy testing
- **Binance**: Cryptocurrency trading platform
- **Coinbase Pro**: Professional crypto trading
- **Kraken**: Advanced crypto exchange
- **Bybit**: Derivatives and spot trading
- **Custom Platforms**: Easily configurable for any trading site

### 🛡️ **Robust Error Handling**
- Automatic screenshot capture on critical failures
- Comprehensive logging with multiple levels
- Graceful browser cleanup regardless of errors
- Retry mechanisms for unstable UI elements

### 📊 **Comprehensive Monitoring**
- Real-time console logging with emojis for clarity
- Configurable monitoring duration
- Trade request counting and summary reporting
- Performance metrics and timing analysis

## 🚀 Quick Start

### 1. **Installation**

```bash
# Install required dependencies
pip install playwright python-dotenv curlconverter

# Install Playwright browsers
playwright install
```

### 2. **Configuration**

Copy the universal configuration template:
```bash
cp .env.universal .env
```

Edit `.env` with your platform settings:
```env
# Choose your trading platform
TRADING_PLATFORM_URL=https://www.tradingview.com

# Optional: Add credentials (leave empty for demo mode)
TRADING_USERNAME=your_username
TRADING_PASSWORD=your_password

# Browser settings
HEADLESS=false
BROWSER_TIMEOUT=30000

# Monitoring settings
MONITORING_DURATION=120
SCREENSHOT_ON_ERROR=true
```

### 3. **Run the Sentinel**

```bash
python tradebot_sentinel_universal.py
```

## 📋 Platform Configuration Examples

### **TradingView (Default)**
```env
TRADING_PLATFORM_URL=https://www.tradingview.com
TRADING_USERNAME=your_tradingview_username
TRADING_PASSWORD=your_tradingview_password
```

### **Binance**
```env
TRADING_PLATFORM_URL=https://www.binance.com
TRADING_USERNAME=your_binance_email
TRADING_PASSWORD=your_binance_password
```

### **Coinbase Pro**
```env
TRADING_PLATFORM_URL=https://pro.coinbase.com
TRADING_USERNAME=your_coinbase_email
TRADING_PASSWORD=your_coinbase_password
```

### **Custom Platform**
```env
TRADING_PLATFORM_URL=https://your-platform.com/login
TRADING_USERNAME=your_username
TRADING_PASSWORD=your_password
CUSTOM_TRADE_KEYWORDS=execute,position,order,trade
```

## 🔧 Advanced Configuration

### **Environment Variables**

| Variable | Description | Default |
|----------|-------------|----------|
| `TRADING_PLATFORM_URL` | Target trading platform URL | `https://www.tradingview.com` |
| `TRADING_USERNAME` | Login username/email | None (demo mode) |
| `TRADING_PASSWORD` | Login password | None (demo mode) |
| `HEADLESS` | Run browser in headless mode | `false` |
| `BROWSER_TIMEOUT` | Browser timeout in milliseconds | `30000` |
| `MONITORING_DURATION` | How long to monitor (seconds) | `120` |
| `SCREENSHOT_ON_ERROR` | Capture screenshots on errors | `true` |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `LOG_FILE` | Log file name | `tradebot_sentinel_universal.log` |
| `CUSTOM_TRADE_KEYWORDS` | Additional trade detection keywords | `execute,position,market_order,limit_order` |

### **Trade Detection Keywords**

The sentinel automatically detects trade requests by analyzing POST request content for these keywords:
- `symbol`, `amount`, `price`, `order`, `trade`
- `buy`, `sell`, `execute`, `position`
- `market_order`, `limit_order`
- Custom keywords from `CUSTOM_TRADE_KEYWORDS`

## 📁 Generated Files

After successful execution, the sentinel generates:

### **trade_universal.sh**
- Complete cURL command for the intercepted trade request
- Ready to execute from command line
- Includes all headers and authentication

### **trade_request_universal.py**
- Python requests code converted from cURL
- Template for API integration
- Includes error handling and response processing

### **Screenshots**
- `screenshot_*_error_*.png`: Error screenshots for debugging
- `screenshot_platform_loaded_*.png`: Success confirmation screenshots

### **Logs**
- `tradebot_sentinel_universal.log`: Detailed execution logs
- Console output with real-time status updates

## 🎯 Use Cases

### **1. API Discovery**
- Reverse engineer trading platform APIs
- Understand request/response formats
- Extract authentication mechanisms

### **2. Trade Automation**
- Automate repetitive trading tasks
- Implement algorithmic trading strategies
- Create custom trading bots

### **3. Integration Development**
- Build custom trading applications
- Integrate with existing systems
- Create trading dashboards and tools

### **4. Testing & Validation**
- Test trading platform functionality
- Validate API endpoints
- Debug trading workflows

## 🛠️ Troubleshooting

### **Common Issues**

**1. Browser Launch Fails**
```bash
# Install Playwright browsers
playwright install

# For Ubuntu/Debian
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

**2. Network Resolution Errors**
- Check internet connection
- Verify platform URL is accessible
- Try different DNS servers

**3. Login Failures**
- Verify credentials in `.env` file
- Check for CAPTCHA or 2FA requirements
- Review platform-specific login flow

**4. No Trade Requests Detected**
- Increase `MONITORING_DURATION`
- Add custom keywords to `CUSTOM_TRADE_KEYWORDS`
- Check if platform uses WebSocket for trading

### **Debug Mode**

Enable detailed logging:
```env
LOG_LEVEL=DEBUG
HEADLESS=false
SCREENSHOT_ON_ERROR=true
```

## 🔒 Security Best Practices

### **Credential Management**
- Never commit `.env` files to version control
- Use strong, unique passwords
- Enable 2FA when available
- Regularly rotate credentials

### **Network Security**
- Use HTTPS-only platforms
- Verify SSL certificates
- Monitor for suspicious network activity
- Use VPN for additional privacy

### **Code Security**
- Review generated code before execution
- Validate API endpoints
- Implement rate limiting
- Use secure coding practices

## 📈 Performance Optimization

### **Browser Performance**
- Use headless mode for production: `HEADLESS=true`
- Adjust timeout values based on platform speed
- Close unused browser tabs and windows

### **Network Optimization**
- Filter requests by domain to reduce noise
- Use specific keywords for trade detection
- Implement request caching where appropriate

### **Resource Management**
- Monitor memory usage during long runs
- Implement cleanup procedures
- Use appropriate monitoring durations

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

### **Development Setup**

```bash
# Clone repository
git clone <repository-url>
cd ai-trading-sentinel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install

# Run tests
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

**Important**: This tool is for educational and research purposes. Always:
- Comply with platform Terms of Service
- Follow applicable financial regulations
- Use appropriate risk management
- Test thoroughly before live trading
- Understand the risks involved in automated trading

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review generated log files
- Create an issue with detailed information
- Include screenshots and error messages

---

**🚀 Happy Trading with Universal TradeBot Sentinel!**