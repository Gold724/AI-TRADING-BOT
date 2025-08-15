# Phase 11: Global Control Panel & Simulation Mode

## Overview

Phase 11 extends the TRAE AI Trading Sentinel with a comprehensive cloud control panel, simulation capabilities, enhanced security, and automated scheduling. This phase transforms the system from a local trading tool into a globally accessible, secure trading platform with advanced features for both simulation and live trading.

## New Components

### 1. Scheduled Auto-Runs & Logs

The `setup_liveops_scheduler.py` script configures automated execution of the trading system:

- **Market-Based Scheduling**: Automatically starts the system at market open times (NY, London)
- **Session Logging**: Creates timestamped logs for each trading session
- **Performance Reports**: Generates daily PnL summaries and trade statistics
- **Cross-Platform Support**: Works with crontab (Linux/macOS) and Task Scheduler (Windows)

### 2. Secure Endpoints

The `setup_liveops_security.py` and `setup_https.py` scripts enhance API security:

- **API Authentication**: Implements JWT and API key authentication for all endpoints
- **HTTPS Support**: Configures secure HTTPS connections with Let's Encrypt or self-signed certificates
- **Access Control**: Restricts access to sensitive endpoints like `/api/trade/stealth`
- **Secure Storage**: Properly manages secrets and credentials

### 3. Dreamer Mode (Simulations)

The `liveops/dreamer_mode.py` module provides a comprehensive simulation environment:

- **Dry-Run Flag**: Enables simulation mode without affecting real accounts
- **Realistic Responses**: Simulates broker responses for testing strategies
- **State Management**: Tracks simulated positions, balances, and P&L
- **Backtesting Support**: Can be used for historical strategy testing

### 4. Market AI Agent

The `trae_ai.py` script implements an AI-powered market analysis agent:

- **Technical Analysis**: Calculates indicators across multiple timeframes
- **Pattern Recognition**: Identifies chart patterns and market conditions
- **Signal Generation**: Creates trading signals based on configured strategies
- **Automated Execution**: Can trigger stealth execution when conditions are met
- **Configurable Strategies**: Customizable through `trae_ai_config.json`

### 5. Cloud Control Panel

The dashboard provides a web-based interface for managing the trading system:

- **Dashboard Overview**: Shows key statistics, account balances, and system status
- **Trade Management**: Displays recent trades and allows manual execution
- **Signal Monitoring**: Tracks incoming trading signals
- **System Controls**: Toggles for Dreamer Mode and TRAE AI Agent
- **Logs Viewer**: Access to system, trade, and error logs

### 6. Tiered Licensing Model

The `setup_licensing.py` script implements a flexible licensing system:

- **Free Tier**: Signals only, no execution
- **Standard Tier**: Manual execution via dashboard
- **Pro Tier**: Auto execution with webhooks
- **Elite Tier**: Stealth mode with secure AI-assisted trading

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Required Python packages (see `requirements.txt`)
- Access to trading accounts (Exness, Bulenox, etc.)
- Domain name (optional, for HTTPS)

### Setup Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure LiveOps**:
   ```bash
   python setup_liveops.py
   ```

3. **Setup Auto-Scheduling**:
   ```bash
   python setup_liveops_scheduler.py
   ```

4. **Configure Security**:
   ```bash
   python setup_liveops_security.py
   ```

5. **Setup HTTPS** (optional):
   ```bash
   python setup_https.py --domain yourdomain.com --email your@email.com
   ```
   Or for self-signed certificates:
   ```bash
   python setup_https.py --domain localhost --self-signed
   ```

6. **Configure Licensing** (optional):
   ```bash
   python setup_licensing.py
   ```

## Usage

### Starting the System

1. **Start the LiveOps System**:
   ```bash
   python main.py --liveops
   ```

2. **Start with Dreamer Mode**:
   ```bash
   python main.py --liveops --dreamer
   ```

3. **Start the Control Panel API**:
   ```bash
   python api/control_panel_api.py
   ```

4. **Start the TRAE AI Agent**:
   ```bash
   python trae_ai.py --start
   ```

### Accessing the Dashboard

1. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```
   Or if HTTPS is configured:
   ```
   https://yourdomain.com
   ```

2. Log in with your credentials (default admin user is created on first run)

## Deployment

For production deployment, refer to the `DEPLOYMENT.md` file for detailed instructions on:

- Deploying to a Contabo VPS
- Setting up GitHub integration
- Configuring systemd services
- Securing your production environment

## Configuration

### LiveOps Configuration

Edit `config/liveops_config.json` to configure:

- System settings (heartbeat interval, log level, directories)
- Signal sources (webhook, file_drop, Tremius, TRAE AI)
- Governance rules (max daily loss, trading hours, allowed symbols)
- Account configurations
- Notification settings

### TRAE AI Configuration

Edit `trae_ai_config.json` to configure:

- Analysis interval
- Symbols and timeframes
- Technical indicators
- Trading strategies
- Risk management parameters
- Execution settings

## Security Considerations

- Always use HTTPS in production environments
- Change default passwords immediately
- Use strong passwords for all accounts
- Regularly update API keys
- Restrict access to the dashboard to trusted networks
- Enable JWT authentication for all API endpoints

## Troubleshooting

Check the following logs for troubleshooting:

- `logs/system.log`: System logs
- `logs/trades.log`: Trade execution logs
- `logs/signals.log`: Signal processing logs
- `logs/errors.log`: Error logs
- `logs/api.log`: Control Panel API logs

## License

The TRAE AI Trading Sentinel is subject to the tiered licensing model. Use `setup_licensing.py` to manage your license.