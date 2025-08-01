# AI Trading Sentinel - Heartbeat Monitoring System

## Overview

The Heartbeat Monitoring System is a critical component of the AI Trading Sentinel that ensures continuous operation and provides real-time status monitoring. This system tracks the health of the trading sentinel's core processes, detects failures, and can automatically restart components when necessary.

## Deployment Options

The AI Trading Sentinel can be deployed in various environments:

### 1. Local Deployment

Run the system on your local machine for development and testing.

### 2. Docker Deployment

Use Docker Compose for containerized deployment (see Docker Integration section below).

### 3. Contabo VPS Deployment

Deploy to a Contabo VPS for 24/7 operation in the cloud:

```bash
# Windows
deploy_to_contabo.bat

# Linux/macOS
./deploy_to_contabo.sh
```

See [CONTABO_VPS_DEPLOYMENT.md](./CONTABO_VPS_DEPLOYMENT.md) for detailed instructions.

## Components

### 1. Heartbeat Status File

The central mechanism for status tracking is the `heartbeat_status.txt` file located in the `logs` directory. This file contains:

- Current status message with emoji indicator
- Timestamp of the last status update
- JSON-formatted session activity flag

### 2. Status Update Functions

The `update_heartbeat_status()` function has been integrated into key components:

- `login_bulenox.py` - Tracks login attempts and session establishment
- `slack_reporter.py` - Records notification events and communication status
- `heartbeat.py` - Updates the main trading loop status at each critical step

### 3. Heartbeat Monitor

The `heartbeat_monitor.py` utility provides continuous monitoring of the heartbeat status:

```bash
python heartbeat_monitor.py [options]
```

Options:
- `--interval`, `-i`: Check interval in seconds (default: 60)
- `--max-age`, `-m`: Maximum age in minutes for heartbeat to be considered healthy (default: 5)
- `--no-notify`, `-n`: Disable Slack notifications
- `--restart`, `-r`: Command to restart heartbeat if unhealthy (e.g., 'python heartbeat.py')
- `--check`, `-c`: Just check current status and exit

### 4. REST API Endpoint

The `/api/heartbeat/status` endpoint in `cloud_main.py` provides JSON access to heartbeat status:

```json
{
  "status": "✅ Heartbeat active - Signal validation in progress",
  "timestamp": "2023-06-15T14:30:45.123456",
  "session_active": true,
  "uptime": 3600,
  "last_update": "2023-06-15T14:30:45.123456"
}
```

## Docker Integration

The heartbeat monitor is integrated into the Docker Compose configuration:

```yaml
# Heartbeat Monitor Service
heartbeat-monitor:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: heartbeat-monitor
  volumes:
    - ./logs:/app/logs
    - ./.env:/app/.env
  environment:
    - TZ=UTC
    - PYTHONUNBUFFERED=1
  restart: unless-stopped
  command: python heartbeat_monitor.py --interval 60 --max-age 5 --restart "docker restart trading-sentinel"
  depends_on:
    - trading-sentinel
```

## Status Indicators

The heartbeat system uses emoji indicators for clear status visualization:

- ✅ - Healthy/Success (login successful, trade executed)
- ⏳ - In Progress (signal validation, login attempt)
- ❌ - Error/Failure (login failed, trade execution error)
- 🔄 - Restart/Retry (attempting to restart component)
- ❓ - Unknown (status file missing or corrupted)

## Integration Points

1. **Login Process**: Status updates at initialization, Chrome setup, navigation, and authentication
2. **Slack Notifications**: Status updates before sending and after success/failure
3. **Main Heartbeat Loop**: Updates at signal detection, validation, login, and trade execution
4. **REST API**: Status endpoint for external monitoring and dashboards

## Monitoring Best Practices

1. Set up external monitoring to check the `/api/heartbeat/status` endpoint
2. Configure the heartbeat monitor with appropriate restart commands
3. Use Slack notifications for critical status changes
4. Review logs regularly for patterns of failures or delays

## Troubleshooting

If the heartbeat becomes unhealthy:

1. Check the `logs/heartbeat_monitor.log` file for error messages
2. Verify the `logs/heartbeat_status.txt` file exists and contains valid data
3. Ensure the trading sentinel container is running
4. Check for Chrome driver or browser issues in the main logs
5. Verify network connectivity to trading platforms and Slack