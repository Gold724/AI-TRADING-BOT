# AI Trading Sentinel - Cloud Deployment Guide

## Overview

This guide explains how to deploy the AI Trading Sentinel system to a cloud environment (Vast.ai or any Docker-compatible cloud provider) for 24/7 automated trading.

## Features

- **Headless Chrome Operation**: Runs in a containerized environment without GUI
- **Multi-Account Support**: Each account has its own profile and session
- **Webhook Integration**: Accepts trade signals via API endpoints
- **Persistent Logging**: Maintains detailed logs and screenshots
- **Environment-Driven Configuration**: All settings via environment variables

## Prerequisites

- Docker and Docker Compose installed on your local machine
- A Vast.ai account or other cloud provider that supports Docker
- Bulenox (ProjectX) account credentials

## Local Setup & Testing

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ai-trading-sentinel.git
   cd ai-trading-sentinel
   ```

2. **Create .env file**:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and add your Bulenox credentials and other settings.

3. **Build and run locally**:
   ```bash
   docker-compose build trading-sentinel
   docker-compose up trading-sentinel
   ```

4. **Test the API**:
   ```bash
   curl -X POST http://localhost:5001/api/login \
     -H "Content-Type: application/json" \
     -d '{"account_id": "BX64883"}'
   ```

## Cloud Deployment

### Option 1: Vast.ai

1. **Create a new instance on Vast.ai**:
   - Select Ubuntu 22.04 as the base image
   - Set disk space to at least 10GB
   - Enable HTTP ports (5000-5001)

2. **SSH into your instance**:
   ```bash
   ssh root@your-vast-ai-ip
   ```

3. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ai-trading-sentinel.git
   cd ai-trading-sentinel
   ```

4. **Create .env file**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

5. **Build and run**:
   ```bash
   docker-compose build trading-sentinel
   docker-compose up -d trading-sentinel
   ```

6. **Check logs**:
   ```bash
   docker-compose logs -f trading-sentinel
   ```

### Option 2: Docker Hub

1. **Pull the image**:
   ```bash
   docker pull yourusername/ai-trading-sentinel:latest
   ```

2. **Run with environment variables**:
   ```bash
   docker run -d \
     --name ai-trading-sentinel \
     -p 5001:5000 \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/.env:/app/.env \
     yourusername/ai-trading-sentinel:latest
   ```

## API Endpoints

### Health Check
```
GET /api/health
```
Returns the current status of the system.

### Login
```
POST /api/login
Content-Type: application/json

{
  "account_id": "BX64883",
  "session_id": "optional-custom-session-id"
}
```
Logs into Bulenox and creates a new session.

### Execute Trade
```
POST /api/trade
Content-Type: application/json

{
  "account_id": "BX64883",
  "session_id": "your-session-id",
  "signal": {
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": 1,
    "stop_loss": 50,
    "take_profit": 100
  }
}
```
Executes a trade using the specified session.

### Webhook
```
POST /api/webhook
Content-Type: application/json

{
  "account_id": "BX64883",
  "signal": {
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": 1,
    "stop_loss": 50,
    "take_profit": 100
  }
}
```
Creates a new session, logs in, executes the trade, and closes the session.

### List Sessions
```
GET /api/sessions
```
Lists all active sessions.

### Get Status
```
GET /api/status
```
Returns the current status of all sessions and recent trades.

## Troubleshooting

### Common Issues

1. **Login Failures**:
   - Check your credentials in the .env file
   - Verify that Bulenox is accessible from your cloud provider
   - Check the logs for specific error messages

2. **Chrome Crashes**:
   - Increase the memory allocation for your container
   - Check if Chrome is compatible with your cloud provider
   - Try using a different Chrome profile or temp profile

3. **Network Issues**:
   - Ensure your cloud provider allows outbound connections
   - Check if Bulenox has IP-based restrictions

### Logs

Logs are stored in the `logs` directory:
- `cloud_main.log`: API server logs
- `cloud_trade_executor.log`: Trade execution logs
- `{account_id}-session.log`: Session-specific logs
- `status.json`: Current status and trade history

Screenshots are stored in `logs/screenshots` directory.

## Maintenance

### Updating

```bash
git pull
docker-compose build trading-sentinel
docker-compose up -d trading-sentinel
```

### Backup

Regularly backup your logs directory:

```bash
tar -czvf backup-$(date +%Y%m%d).tar.gz logs
```

## Security Considerations

- Store your .env file securely and never commit it to version control
- Use a strong password for your Bulenox account
- Consider using a VPN or IP whitelisting if available
- Regularly update your Docker images and dependencies

## Support

For issues or questions, please open an issue on the GitHub repository or contact the maintainer.