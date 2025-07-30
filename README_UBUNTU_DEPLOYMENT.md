# AI Trading Sentinel - Ubuntu Deployment Guide

This guide provides instructions for deploying the AI Trading Sentinel on Ubuntu using Docker. The system is designed to run in a containerized environment, making it easy to deploy and manage.

## Prerequisites

- Ubuntu 20.04 LTS or newer
- Sudo access on your server
- Internet connection

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-trading-sentinel.git
   cd ai-trading-sentinel
   ```

2. Run the deployment script:
   ```bash
   chmod +x deploy_ubuntu.sh
   ./deploy_ubuntu.sh
   ```

3. The script will:
   - Install Docker and Docker Compose if not already installed
   - Create a `.env` file from the example if it doesn't exist
   - Build and start the Docker containers
   - Set up the Chrome profile for Selenium automation

4. Edit your `.env` file with your credentials:
   ```bash
   nano .env
   ```

5. Restart the services after editing the `.env` file:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Manual Setup

If you prefer to set up manually or the script fails, follow these steps:

1. Install Docker and Docker Compose:
   ```bash
   sudo apt-get update
   sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io
   sudo systemctl enable docker
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. Create necessary directories:
   ```bash
   mkdir -p backend/logs/screenshots
   mkdir -p temp_chrome_profile
   mkdir -p temp_chrome_profile_futures
   ```

3. Create and configure your `.env` file:
   ```bash
   cp .env.example .env
   nano .env
   ```

4. Build and start the containers:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

5. Set up the Chrome profile for Selenium:
   ```bash
   docker-compose exec backend python setup_chrome_profile_ubuntu.py
   ```

## Environment Variables

The following environment variables need to be set in your `.env` file:

- `API_KEY`: Your API key
- `TRADING_ACCOUNT_ID`: Your trading account ID
- `BULENOX_USERNAME`: Your Bulenox username
- `BULENOX_PASSWORD`: Your Bulenox password
- `FLASK_SECRET_KEY`: A secure random key for Flask
- `ENCRYPTION_KEY`: A secure Fernet key for encryption
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (optional)
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID (optional)

For QuantConnect integration (optional):
- `QUANTCONNECT_API_KEY`: Your QuantConnect API key
- `QUANTCONNECT_PROJECT_ID`: Your QuantConnect project ID

## Managing the Deployment

- View logs:
  ```bash
  docker-compose logs -f
  ```

- Stop the services:
  ```bash
  docker-compose down
  ```

- Restart the services:
  ```bash
  docker-compose restart
  ```

- Update the deployment:
  ```bash
  git pull
  docker-compose build
  docker-compose up -d
  ```

## Troubleshooting

### Chrome/Selenium Issues

If you encounter issues with Chrome or Selenium:

1. Check the logs:
   ```bash
   docker-compose logs backend
   ```

2. Try rebuilding the Chrome profile:
   ```bash
   docker-compose exec backend python setup_chrome_profile_ubuntu.py
   ```

3. Ensure your credentials in the `.env` file are correct.

### Container Issues

If containers fail to start:

1. Check Docker status:
   ```bash
   sudo systemctl status docker
   ```

2. Check container status:
   ```bash
   docker-compose ps
   ```

3. Rebuild containers:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Security Considerations

- The `.env` file contains sensitive information. Ensure it has restricted permissions:
  ```bash
  chmod 600 .env
  ```

- Consider using Docker secrets for production deployments.

- The system uses Chrome in headless mode, which is suitable for server environments.

## QuantConnect Integration

The AI Trading Sentinel includes integration with QuantConnect for algorithmic trading strategies, backtesting, and live trading. This integration allows you to leverage QuantConnect's powerful platform while managing your trades through the Sentinel system.

### Setup QuantConnect Integration

1. Uncomment and set the QuantConnect environment variables in your `.env` file:
   ```
   QC_API_KEY=your_quantconnect_api_key
   QC_PROJECT_ID=your_quantconnect_project_id
   ```

2. Restart the services:
   ```bash
   docker-compose restart
   ```

3. Test the integration:
   ```bash
   docker-compose exec backend python test_quantconnect.py
   ```

### Using QuantConnect with Sentinel

Once integrated, you can:

1. **Access QuantConnect API endpoints**:
   - `/api/quantconnect/status` - Check integration status
   - `/api/quantconnect/backtests` - List backtests
   - `/api/quantconnect/backtest/<id>` - Get specific backtest details
   - `/api/quantconnect/create-backtest` - Create a new backtest
   - `/api/quantconnect/deploy-live` - Deploy algorithm to live trading
   - `/api/quantconnect/stop-live` - Stop live algorithm
   - `/api/quantconnect/equity` - Get equity curve data
   - `/api/quantconnect/signals` - Get latest trading signals

2. **Customize the Strategy**:
   - Edit `backend/strategies/quantconnect_strategy.py` to modify the trading algorithm
   - The default implementation includes a simple momentum strategy

3. **Integrate with Other Brokers**:
   - Signals generated by QuantConnect can be executed through other brokers
   - Use the `/api/quantconnect/signals` endpoint to get signals and pass them to the trade execution endpoints

### Troubleshooting QuantConnect Integration

If you encounter issues with the QuantConnect integration:

1. Verify your API credentials are correct

2. Check the logs for specific errors:
   ```bash
   docker-compose logs backend | grep -i quantconnect
   ```

3. Run the test script to diagnose issues:
   ```bash
   docker-compose exec backend python test_quantconnect.py
   ```

4. Ensure your QuantConnect project exists and is properly configured

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.