# Bulenox Login and API Guide

## Login Methods

The AI Trading Sentinel provides multiple ways to log into Bulenox:

### 1. Environment Variables (Recommended)

Set these environment variables before running the application:

```
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
BULENOX_PROFILE_PATH=path_to_chrome_profile (optional)
BULENOX_PROFILE_NAME=profile_name (optional)
```

### 2. AI-Powered Login

The system includes AI-powered login functionality in `ai_login_bulenox.py` that handles:
- Automatic form detection and filling
- CAPTCHA recognition (if present)
- Session management with retry logic

### 3. Profile-Based Login

The `login_bulenox.py` script uses Chrome profiles for persistent login sessions:

```python
# Example usage
from login_bulenox import login_bulenox

driver = login_bulenox()
# Now use the authenticated driver for trading operations
```

### 4. Cookie-Based Login

For programmatic access, you can use cookie-based authentication as demonstrated in the test scripts.

## API Endpoints

The backend exposes several API endpoints for interacting with Bulenox:

### Health Check
```
GET /api/health
```

### Login
```
POST /api/login
Headers: {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}
Body: {"debug": true}
```

### Execute Trade
```
POST /api/trade
Headers: {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}
Body: {
  "symbol": "EURUSD",
  "direction": "buy",
  "quantity": 0.01,
  "tp": 1.0800,
  "sl": 1.0700
}
```

### Webhook for Automated Trading
```
POST /api/webhook
Headers: {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}
Body: {
  "account_id": "BX64883",
  "signal": {
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": 0.01
  }
}
```

### Logout
```
POST /api/logout
Headers: {"Authorization": "Bearer YOUR_API_KEY"}
```

## Using the API Examples

This repository includes example scripts for interacting with the Bulenox API:

### PowerShell Example

Run the PowerShell script:
```powershell
.\bulenox_api_examples.ps1
```

### Python Example

Run the Python script:
```bash
python bulenox_api_examples.py
```

## Security Recommendations

1. Store API keys in environment variables, not in code
2. Use HTTPS for all API communications in production
3. Implement proper error handling and logging
4. Rotate API keys periodically
5. Use IP whitelisting if possible

## Troubleshooting

If you encounter login issues:

1. Check the logs in `logs/` directory
2. Verify your credentials are correct
3. Try clearing browser cache and cookies
4. Check if Bulenox has changed their login page structure
5. Run the diagnostic script: `python login_diagnostic_detailed.py`