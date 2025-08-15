# TRAE AI Trading Sentinel - LiveOps System

## Overview

The LiveOps system enables 24/7 automated trading operations for the TRAE AI Trading Sentinel. It provides robust functionality for multi-account trading, signal processing, trade execution, and system monitoring.

## Components

### 1. Stealth Executor

The Stealth Executor handles trade execution on various brokers using browser automation and API integration:

- **Supported Brokers**: Exness, Bulenox
- **Features**:
  - Selenium-based browser automation for web interfaces
  - API-based execution for brokers with API support
  - Screenshot capture for verification
  - Execution result logging

### 2. Account Manager

The Account Manager handles multiple trading accounts and enforces risk management rules:

- **Features**:
  - Multi-account support
  - Daily loss tracking and limits
  - Position tracking
  - Account status management (active/locked)

### 3. Signal Processor

The Signal Processor handles trading signals from various sources:

- **Signal Sources**:
  - Webhook (HTTP POST)
  - File drop (JSON/CSV)
  - External APIs
- **Features**:
  - Signal normalization
  - Signal validation
  - Signal tracking (pending, processed, failed)

### 4. Heartbeat Monitor

The Heartbeat Monitor ensures system health and continuous operation:

- **Features**:
  - Regular system health checks
  - Resource monitoring (CPU, memory)
  - Uptime tracking
  - Callback registration for periodic tasks

## Configuration

The LiveOps system is configured via `config/liveops_config.json`. Key configuration sections include:

- **System**: General system settings
- **Signal Sources**: Configuration for signal sources
- **Governance**: Trading rules and limits
- **Accounts**: Trading account configurations
- **Brokers**: Broker-specific settings
- **Notifications**: Alert configuration

## Deployment

The LiveOps system can be deployed using various methods:

### Systemd Service (Linux)

Use the provided `deployment/trae_liveops.service` file to set up a systemd service:

```bash
sudo cp deployment/trae_liveops.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trae_liveops
sudo systemctl start trae_liveops
```

### Supervisor (Linux/macOS)

Use the provided `deployment/supervisord.conf` file to set up supervisor:

```bash
sudo cp deployment/supervisord.conf /etc/supervisor/conf.d/trae_liveops.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start trae_liveops
```

### Windows Batch Script

Use the provided `deployment/start_trae_liveops.bat` script to start the system on Windows.

## Testing

Use the `test_liveops.py` script to test the LiveOps system:

```bash
python test_liveops.py --test all
```

Available test options:
- `heartbeat`: Test the heartbeat monitor
- `webhook`: Test the webhook handler
- `account`: Test the account manager
- `executor`: Test the stealth executor
- `signal`: Test the signal processor
- `all`: Run all tests

## Usage

Start the TRAE AI Trading Sentinel in LiveOps mode:

```bash
python main.py --phase 10 --liveops --webhook
```

Command line options:
- `--phase`: Trading phase (use 10 for LiveOps)
- `--liveops`: Enable LiveOps mode
- `--webhook`: Enable webhook server for receiving signals
- `--config`: Path to configuration file

## Monitoring

The LiveOps system generates logs and heartbeats that can be monitored:

- **Logs**: Check `logs/liveops/operations.log` for system logs
- **Heartbeats**: Check `logs/heartbeats.json` for system health data
- **Signals**: Check `data/processed_signals.json` and `data/failed_signals.json` for signal status

## Security

The LiveOps system includes several security features:

- Environment variables for sensitive credentials
- Optional webhook authentication
- Governance rules to prevent excessive trading
- Daily loss limits to protect capital