# TradeBot Sentinel 🤖

**An Expert Automation Agent for Bulenox ProjectX Trading Platform**

TradeBot Sentinel is a sophisticated Playwright-based automation system designed to interact with the Bulenox ProjectX trading platform. It provides secure login, robust element detection, network request interception, and automatic code generation for trade execution.

## 🚀 Features

### Core Automation Capabilities
- **Secure Login**: Uses environment variables for credentials with robust fallback selectors
- **Time Sync Warning Detection**: Automatically handles modal dialogs during login
- **Dashboard Confirmation**: Multi-selector approach for reliable login verification
- **Trading Interface Navigation**: Smart navigation with retry mechanisms
- **Order Placement**: Comprehensive order placement with fallback strategies

### Advanced Network Interception
- **Real-time Request Monitoring**: Intercepts all POST requests during trading
- **Trade Detection**: Intelligent parsing of JSON and string content for trade keywords
- **cURL Generation**: Automatically saves intercepted requests as cURL commands
- **Python Code Conversion**: Converts cURL to full Python requests code using curlconverter

### Reliability & Debugging
- **Screenshot Capture**: Automatic screenshots on critical failures
- **Verbose Logging**: Comprehensive console logs for traceability
- **Retry Mechanisms**: Up to 3 retries with 2-second delays for dynamic elements
- **Graceful Error Handling**: Robust exception handling with browser cleanup

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- Windows/Linux/macOS
- Internet connection

### Environment Setup
1. **Clone or download** the AI Trading Sentinel project
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

### Environment Variables
Create a `.env` file with your Bulenox credentials:
```env
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
```

## 🎯 Usage

### Quick Start
```bash
# Run system tests first
python test_tradebot.py

# Execute TradeBot Sentinel
python tradebot_sentinel.py
```

### Configuration Options

#### Headless Mode
By default, the script runs in headless mode. To see the browser:
```python
# In tradebot_sentinel.py, modify:
browser = await playwright.chromium.launch(headless=False)  # Set to False
```

#### Custom Selectors
The script uses multiple fallback selectors. You can customize them in the script:
```python
# Login selectors
USERNAME_SELECTORS = [
    'input[name="username"]',
    'input[type="email"]',
    '#username',
    # Add your custom selectors
]
```

## 📁 Generated Files

When TradeBot Sentinel detects a trade execution request, it generates:

1. **`trade.sh`** - cURL command for the intercepted request
2. **`trade_request_full.py`** - Complete Python requests code
3. **`screenshot_*.png`** - Debug screenshots (on errors)

## 🔧 System Testing

Run the comprehensive test suite:
```bash
python test_tradebot.py
```

The test verifies:
- ✅ Environment setup (.env file, main script)
- ✅ Module imports (Playwright, curlconverter, requests)
- ✅ curlconverter functionality
- ✅ Playwright browser launch

## 🛠️ Troubleshooting

### Common Issues

**Login Failures**
- Verify credentials in `.env` file
- Check if Bulenox platform has updated selectors
- Review screenshot files for visual debugging

**Element Not Found**
- The script uses multiple fallback selectors
- Increase retry delays if the platform is slow
- Check console logs for detailed error information

**Network Interception Issues**
- Ensure the trading platform uses POST requests
- Verify trade keywords in the detection logic
- Check browser console for network errors

### Debug Mode
Enable detailed logging:
```python
# Set headless=False and add more logging
print(f"Debug: Current page URL: {page.url}")
print(f"Debug: Page title: {await page.title()}")
```

## 📊 Architecture

### Core Components
1. **Authentication Module**: Handles secure login with fallback strategies
2. **Navigation Engine**: Smart page navigation with retry mechanisms
3. **Network Interceptor**: Real-time request monitoring and parsing
4. **Code Generator**: Automatic cURL and Python code generation
5. **Error Handler**: Screenshot capture and graceful error recovery

### Security Features
- Environment variable-based credential management
- No hardcoded sensitive information
- Secure browser session handling
- Automatic cleanup on exit

## 🚨 Important Notes

### Compliance & Ethics
- **Use Responsibly**: Only use on accounts you own
- **Rate Limiting**: Respect platform rate limits
- **Terms of Service**: Ensure compliance with Bulenox ToS
- **Risk Management**: Test thoroughly before live trading

### Limitations
- Requires stable internet connection
- Platform UI changes may require selector updates
- Network interception depends on POST request patterns
- Browser automation may be detected by advanced anti-bot systems

## 📈 Advanced Usage

### Custom Trade Detection
Modify the trade detection logic:
```python
# In handle_request function
trade_keywords = ['symbol', 'amount', 'price', 'order', 'trade', 'buy', 'sell', 'execute']
# Add your custom keywords
```

### Integration with Other Systems
The generated Python code can be integrated into:
- Trading bots
- Portfolio management systems
- Risk management tools
- Backtesting frameworks

## 🔄 Updates & Maintenance

### Regular Maintenance
- Update Playwright browsers: `playwright install`
- Check for selector changes on platform updates
- Review and update trade detection keywords
- Test after major platform updates

### Version Control
- Keep backups of working configurations
- Document any custom modifications
- Test changes in a safe environment first

## 📞 Support

For issues and improvements:
1. Check the troubleshooting section
2. Review console logs and screenshots
3. Test with the latest dependencies
4. Verify platform compatibility

---

**⚠️ Disclaimer**: This tool is for educational and authorized use only. Users are responsible for compliance with all applicable laws and platform terms of service. Use at your own risk.

**🎯 TradeBot Sentinel** - Automating trading workflows with precision and reliability.