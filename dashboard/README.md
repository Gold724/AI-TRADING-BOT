# TRAE AI Trading Sentinel - Cloud Control Panel

## Overview

The Cloud Control Panel provides a web-based dashboard for managing and monitoring your TRAE AI Trading Sentinel. It offers a user-friendly interface to execute trades, view statistics, toggle simulation mode, and monitor system status.

## Features

- **Dashboard Overview**: View key trading statistics, account balances, and system status
- **Manual Trade Execution**: Execute trades directly from the dashboard
- **Dreamer Mode**: Toggle simulation mode for risk-free testing
- **TRAE AI Agent**: Start/stop the AI agent for automated trading signals
- **Logs Viewer**: Access system, trade, and error logs
- **Account Management**: View account balances and performance
- **Signal Monitoring**: Track incoming trading signals

## Installation

### Prerequisites

- TRAE AI Trading Sentinel installed and configured
- Node.js and npm (for development only)
- Modern web browser

### Setup

1. Start the Control Panel API:

```bash
python3 api/control_panel_api.py
```

2. Access the dashboard by opening `index.html` in your browser or navigating to:

```
http://localhost:5000
```

Or if HTTPS is configured:

```
https://yourdomain.com
```

## Usage

### Authentication

1. Log in with your credentials (default admin user is created on first run)
2. For security, change the default password after first login

### Dashboard Navigation

- **Overview**: Main dashboard with statistics and system status
- **Trades**: View and manage trades
- **Signals**: Monitor incoming trading signals
- **Accounts**: View account balances and performance
- **Logs**: Access system, trade, and error logs
- **Settings**: Configure system settings

### Manual Trade Execution

1. Navigate to the "Execute Trade" section
2. Select account, symbol, action (BUY/SELL), and volume
3. Optionally set take profit and stop loss levels
4. Click "Execute" to send the trade

### Dreamer Mode (Simulation)

1. Toggle the "Dreamer Mode" switch to enable/disable simulation
2. When enabled, all trades will be simulated without real execution
3. Simulation results are stored and can be viewed in the dashboard

### TRAE AI Agent

1. Toggle the "TRAE AI Agent" switch to start/stop the AI agent
2. When enabled, the AI agent will analyze markets and generate signals
3. Configure the AI agent settings in the "Settings" section

## Development

The dashboard is built with HTML, CSS, and JavaScript, using the following libraries:

- React for UI components
- Chart.js for data visualization
- Axios for API requests
- Tailwind CSS for styling

To modify the dashboard:

1. Edit the HTML, CSS, and JavaScript files in the `dashboard` directory
2. For advanced development, set up a local development environment with Node.js

## Troubleshooting

### Common Issues

- **Cannot access dashboard**: Ensure the API is running and check your network connection
- **Authentication errors**: Verify your credentials or reset the password
- **No data displayed**: Check if the LiveOps system is running and generating data
- **API connection errors**: Verify API endpoint configuration and network connectivity

### Logs

Check the following logs for troubleshooting:

- `logs/api.log`: Control Panel API logs
- `logs/system.log`: System logs
- `logs/errors.log`: Error logs

## Security Considerations

- Always use HTTPS in production environments
- Change default passwords immediately
- Use strong passwords for all accounts
- Regularly update API keys
- Restrict access to the dashboard to trusted networks
- Enable JWT authentication for all API endpoints

## License

The Cloud Control Panel is part of the TRAE AI Trading Sentinel and is subject to the same licensing terms. See the main project documentation for details on the tiered licensing model.