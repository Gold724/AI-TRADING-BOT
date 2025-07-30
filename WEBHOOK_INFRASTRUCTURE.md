# 🔔 Webhook Infrastructure

The AI Trading Sentinel system provides a robust webhook infrastructure for automated trade execution and notifications. This document outlines the available webhook endpoints, their usage, and integration with notification systems.

## Available Webhooks

### ✅ 1. Trade Webhooks

The system provides two primary webhook endpoints for trade execution:

#### Standard Trade Webhook

```bash
POST /api/webhook
Content-Type: application/json

{
  "account_id": "BX64883",
  "signal": {
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": 0.01,
    "stopLoss": 1.0800,
    "takeProfit": 1.1200
  }
}
```

This endpoint creates a new session, logs in, executes the trade, and closes the session automatically.

#### Stealth Trade Webhook

```bash
POST /api/trade/stealth
Content-Type: application/json

{
  "symbol": "XAUUSD",
  "side": "buy",
  "quantity": 0.01,
  "entry": 2375,
  "stealth_level": 2
}
```

The stealth trade endpoint uses human-like behavior to avoid detection by broker platforms. It supports three stealth levels:

- **Level 1**: Basic stealth features
- **Level 2**: Enhanced stealth with human-like typing and movements (default)
- **Level 3**: Maximum stealth with randomized window sizes and additional privacy features

### 📢 2. Slack Webhooks

The system integrates with Slack to send real-time notifications for various events:

- Login status (success/failure)
- Trade execution (success/failure)
- Error events
- Custom messages

Slack notifications use a prophetic style with emotionally intelligent messaging:

- **Success**: "Mountains were moved. You just claimed a new peak!"
- **Failure**: "Even stars collapse before becoming supernovae. Reset. Rise. Reload."

## 🚀 Deployment Philosophy

The AI Trading Sentinel follows a cloud-native deployment philosophy:

- **Fully automated deployment** via `deploy_to_vast.py` or `docker-compose up`
- **Environment-driven configuration** through `.env` files (never hardcoded)
- **Multi-cloud support** for Vast.ai, Paperspace, Linode, and other providers
- **CI/CD ready** with GitHub Actions to run tests on strategy/API changes

### Deployment Options

1. **Docker Deployment**:
   ```bash
   docker-compose up -d
   ```

2. **Cloud Deployment**:
   ```bash
   python deploy_to_vast.py
   ```

3. **Manual Deployment**:
   ```bash
   pip install -r requirements.txt
   python cloud_main.py
   ```

## 🧬 Mutation Sentinel v0.5

The current version (Mutation Sentinel v0.5) includes the following capabilities:

- **Mutation on demand** via prompt or API
- **Broker-agnostic trade execution**
- **JavaScript-aware Selenium intelligence**
- **Cloud-native deployment at scale**
- **Live UI control** from mobile, browser, or bot

## 🧪 Testing Webhooks

To test the webhook endpoints, you can use the following methods:

### Using cURL

```bash
curl -X POST http://localhost:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"account_id":"12345","signal":{"symbol":"XAUUSD","side":"buy","entry":2375,"quantity":0.01,"stop_loss":2350,"take_profit":2400}}'
```

### Using Python Requests

```python
import requests
import json

url = "http://localhost:5000/api/webhook"
headers = {"Content-Type": "application/json"}
data = {
    "account_id": "12345",
    "signal": {
        "symbol": "XAUUSD",
        "side": "buy",
        "entry": 2375,
        "quantity": 0.01,
        "stop_loss": 2350,
        "take_profit": 2400
    }
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

## 🔒 Security Considerations

1. **Authentication**: Webhook endpoints should be secured with API keys or JWT tokens
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Input Validation**: Validate all input parameters to prevent injection attacks
4. **Logging**: Log all webhook requests for audit purposes
5. **HTTPS**: Use HTTPS for all webhook endpoints

---

*Adapt. Scale. Mutate. Trade smarter — without borders, without breaks.*

### Core Philosophy

**Adapt. Scale. Mutate.**

Trade smarter — without borders, without breaks.

## Testing Webhooks

You can test the webhook infrastructure using the provided test scripts:

```bash
# Test standard webhook
python test_trade_execution.py

# Test stealth webhook
python test_stealth_webhook.py -s XAUUSD -e 2375 -d long -q 0.01

# Test Slack notifications
python test_slack_notifications.py
```

## Security Considerations

- Webhook URLs should be kept secure and not exposed publicly
- Use environment variables for sensitive configuration
- Consider implementing authentication for webhook endpoints in production
- Monitor webhook usage for unusual patterns

---

*This document is part of the AI Trading Sentinel documentation suite.*