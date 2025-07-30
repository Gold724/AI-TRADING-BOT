# 🧠 C.Y.P.H.E.R.
## Cybernetic Yield Protocol for Harmonized Entry & Routing

CYPHER is the secure broker access agent of the AI Trading Sentinel system, designed to handle authentication, login flows, and session management for trading platforms.

## 🔐 Core Features

- **Secure Authentication**: Manages login flows via Selenium with robust error handling
- **Session Persistence**: Maintains persistent login sessions using cookies and Chrome profiles
- **Credential Security**: Securely loads credentials from environment variables or encrypted storage
- **Headful Debugging**: Supports headful browser mode for debugging and monitoring
- **Robust Selectors**: Uses multiple selector strategies to handle UI changes gracefully
- **Comprehensive Logging**: Detailed logging of all access attempts with session IDs

## 📋 Implementation Details

### File Structure

- `executor_bulenox.py` - Main CYPHER implementation for Bulenox broker
- `test_cypher_login.py` - Test script for verifying login functionality
- `logs/broker_login.log` - Detailed login attempt logs
- `screenshots/` - Captures of login process for debugging
- `sessions/` - Storage for persistent session data

### Configuration

CYPHER can be configured using environment variables or a `secrets.json` file:

```
# Required credentials
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password

# Optional configuration
BULENOX_PROFILE_PATH=C:\Users\Admin\AppData\Local\Google\Chrome\User Data
BULENOX_PROFILE_NAME=Profile 15
CHROMEDRIVER_PATH=D:\aibot\chromedriver-win64\chromedriver-win64\chromedriver.exe
```

## 🚀 Usage

### Basic Usage

```python
from backend.executor_bulenox import BulenoxExecutor

# Initialize the executor
executor = BulenoxExecutor()

# Check if login works
if executor.health():
    print("CYPHER login successful")
else:
    print("CYPHER login failed")

# Execute a trade
signal = {
    'symbol': 'BTCUSD',
    'direction': 'BUY',
    'amount': 0.01
}

result = executor.execute_trade(signal=signal, stopLoss=5, takeProfit=10)
```

### Integration with Flask Backend

The CYPHER module is integrated with the Flask backend in `main.py`. When the `/api/trade` endpoint is called, it triggers the login process if not already logged in.

## 🧪 Testing

Run the test script to verify CYPHER functionality:

```bash
python test_cypher_login.py
```

The test script performs three tests:
1. Direct login via the `health()` method
2. Cookie persistence between login attempts
3. Chrome profile reuse for session persistence

## 🔧 Troubleshooting

### Common Issues

1. **Login Failures**
   - Check credentials in environment variables or `secrets.json`
   - Examine screenshots in the `screenshots/` directory
   - Review logs in `logs/broker_login.log`

2. **Chrome Profile Issues**
   - Verify the profile path exists and is accessible
   - Try creating a new Chrome profile specifically for CYPHER

3. **ChromeDriver Compatibility**
   - Ensure ChromeDriver version matches your Chrome browser version
   - Set the correct path in environment variables

## 🔄 Future Improvements

1. Implement encrypted credential storage with key rotation
2. Add support for 2FA authentication flows
3. Develop a health monitoring dashboard for login status
4. Implement automatic recovery for failed login attempts
5. Add support for additional brokers beyond Bulenox

## 🛡️ Security Considerations

- Never hardcode credentials in the source code
- Regularly rotate passwords and update stored credentials
- Use dedicated Chrome profiles to isolate broker sessions
- Implement proper error handling to avoid exposing sensitive information
- Monitor login attempts for suspicious activity

---

*Access is sacred. The gate must know you before it opens.*