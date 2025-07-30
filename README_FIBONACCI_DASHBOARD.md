# 🧠 AI Trading Sentinel - Fibonacci Strategy Dashboard

## Overview

The Fibonacci Strategy Dashboard is a comprehensive web-based interface for monitoring, managing, and executing Fibonacci trading strategies within the AI Trading Sentinel ecosystem. This dashboard provides a unified view of active trades, trade history, available signals, and performance metrics, allowing traders to efficiently manage their Fibonacci-based trading operations.

## Features

### Dashboard Tab
- **Active Trades Monitoring**: View all currently active Fibonacci trades with their status, current level, and next target.
- **Quick Trade Execution**: Execute new Fibonacci trades directly from the dashboard with customizable parameters.
- **Recent Activity Feed**: Stay updated with the latest trading activities and events.
- **Key Performance Metrics**: Monitor active trades count, total trades, success rate, and overall profit/loss.

### Signals Tab
- **Signal Management**: View, add, edit, and delete Fibonacci trading signals.
- **Signal Execution**: Execute saved signals with a single click.
- **Signal Details**: View comprehensive information about each signal including symbol, side, entry price, and Fibonacci levels.

### Trade History Tab
- **Historical Trade Records**: Access a complete history of all executed Fibonacci trades.
- **Trade Details**: View detailed information about each trade including timestamp, symbol, side, quantity, price, action, Fibonacci level, and status.

### Analytics Tab
- **Performance Metrics**: Visualize trading performance over time.
- **Symbol Distribution**: Analyze trade distribution across different symbols.
- **Fibonacci Level Analysis**: Understand the effectiveness of different Fibonacci levels in your trading strategy.

### Settings Tab
- **Configuration Options**: Customize dashboard settings including file paths and refresh intervals.
- **Utility Tools**: Access additional tools such as report generation, data visualization, and strategy simulation.

## Architecture

The Fibonacci Strategy Dashboard is built on a Flask-based web server that interfaces with the existing Fibonacci strategy implementation. Key components include:

1. **Web Interface**: A responsive HTML/CSS/JavaScript frontend for user interaction.
2. **API Endpoints**: RESTful API endpoints for retrieving data and executing actions.
3. **Data Management**: Functions for loading and saving trade history and signal data.
4. **Trade Execution**: Integration with the `FibonacciExecutor` for executing trades.

## Installation and Setup

### Prerequisites
- Python 3.7+
- Flask
- All dependencies required by the AI Trading Sentinel project

### Installation

1. Ensure the AI Trading Sentinel project is properly set up.
2. The dashboard is included in the `backend` directory as `fibonacci_strategy_dashboard.py`.

### Running the Dashboard

```bash
python backend/fibonacci_strategy_dashboard.py
```

Additional command-line options:
- `--host`: Server host (default: 127.0.0.1)
- `--port`: Server port (default: 5001)
- `--history`: Trade history file path (default: logs/fibonacci_trades.json)
- `--signals`: Signals file path (default: sample_fibonacci_signals.json)

Example:
```bash
python backend/fibonacci_strategy_dashboard.py --port 5002 --history custom_history.json
```

## Usage Guide

### Executing a Quick Trade

1. Navigate to the Dashboard tab.
2. Fill in the Quick Trade form with the required parameters:
   - Symbol (e.g., EURUSD, BTCUSD)
   - Side (Buy/Sell)
   - Quantity
   - Entry Price
   - Fibonacci Low
   - Fibonacci High
   - Optional: Stop Loss, Take Profit
   - Stealth Level (1-3)
3. Click "Execute Trade" to start the trade execution.

### Managing Signals

1. Navigate to the Signals tab.
2. To add a new signal, click "Add New Signal" and fill in the required information.
3. To execute an existing signal, click the "Execute" button next to the signal.
4. To edit or delete a signal, use the respective buttons next to the signal.

### Monitoring Active Trades

1. Navigate to the Dashboard tab.
2. The Active Fibonacci Trades table displays all currently active trades.
3. Use the "View" button to see detailed information about a specific trade.
4. Use the "Close" button to manually close a trade if needed.

### Analyzing Trade History

1. Navigate to the Trade History tab.
2. Review the complete history of executed trades with their details.

## Integration with Existing Systems

The Fibonacci Strategy Dashboard integrates seamlessly with the existing AI Trading Sentinel ecosystem, particularly with the Fibonacci strategy implementation. It utilizes the same `FibonacciExecutor` class for trade execution and accesses the same trade history and signal files.

## Security Considerations

- The dashboard is designed for local use and does not implement authentication by default.
- For production deployment, additional security measures should be implemented, including proper authentication, HTTPS, and input validation.

## Future Enhancements

1. **Real-time Data Updates**: Implement WebSocket for real-time updates without page refresh.
2. **Advanced Analytics**: Add more sophisticated performance analysis and visualization tools.
3. **Multi-Strategy Support**: Extend the dashboard to support other trading strategies beyond Fibonacci.
4. **User Authentication**: Add user accounts and authentication for multi-user environments.
5. **Mobile Optimization**: Enhance mobile responsiveness for on-the-go trading management.

## Troubleshooting

### Common Issues

1. **Dashboard Not Loading**: Ensure the Flask server is running and accessible at the specified host and port.
2. **Trade Execution Failures**: Check the console output for error messages and ensure the trading interface is properly configured.
3. **Missing Data**: Verify that the history and signals files exist at the specified paths.

## Contributing

Contributions to the Fibonacci Strategy Dashboard are welcome. Please follow the existing code style and add appropriate tests for new features.

---

*This dashboard is part of the AI Trading Sentinel project, designed to provide a comprehensive solution for automated trading with a focus on Fibonacci strategies.*