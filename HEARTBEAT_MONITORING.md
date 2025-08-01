# Sentinel Heartbeat Monitoring System

## Overview

The Sentinel Heartbeat Monitoring System provides real-time visibility into the operational status of your AI Trading Sentinel. It allows you to monitor the current state of the trading system, including login status, trade execution, and error conditions.

## Components

### Backend

1. **Heartbeat Status Endpoint**
   - Located in `cloud_main.py`
   - Endpoint: `/api/heartbeat/status`
   - Returns current status, timestamp, and session activity state

2. **Heartbeat Status File**
   - Located at `logs/heartbeat_status.txt`
   - Contains the current status message and timestamp
   - Updated by the trading system during key operations

### Frontend

1. **HeartbeatStatus Component**
   - Located in `frontend/src/components/HeartbeatStatus.tsx`
   - Displays the current heartbeat status with visual indicators
   - Polls the backend endpoint at regular intervals

2. **HeartbeatMonitor Component**
   - Located in `frontend/src/components/HeartbeatMonitor.tsx`
   - Provides a dedicated monitoring interface with controls
   - Accessible via the "Heartbeat Monitor" tab in the main UI

3. **RemoteControlPanel Integration**
   - The heartbeat status is also displayed in the Remote Control Panel

## Status Messages

The heartbeat system uses emoji-prefixed status messages to indicate different states:

- 🔄 Waiting for signals... - System is idle and waiting for trading signals
- ✅ Login successful - Successfully logged into the trading platform
- 💰 Trade executed - A trade has been successfully placed
- 🎯 Profit secured - A trade has closed with profit
- ❌ Error occurred - An error has been encountered

## Testing Tools

The following tools are provided for testing the heartbeat monitoring system:

### Python Script

```bash
python update_heartbeat_status.py "Your status message" --log-dir logs
```

### Windows Batch File

```bash
update_heartbeat_status.bat [status_type]
```

Available status types:
- `waiting` - Waiting for signals
- `login` - Login successful
- `trade` - Trade executed
- `profit` - Profit secured
- `error` - Error occurred
- `custom "Your custom message"` - Custom status message

### Linux/Mac Shell Script

```bash
./update_heartbeat_status.sh [status_type]
```

Available status types are the same as for the Windows batch file.

## Integration with Existing Systems

### Manual Trade Test

The `manual_trade_test.py` script updates the heartbeat status during its execution, providing real-time feedback on the trade testing process.

### Cloud API

The Cloud API exposes the heartbeat status via the `/api/heartbeat/status` endpoint, allowing external systems to monitor the trading system's status.

### Slack Notifications

The heartbeat status is synchronized with Slack notifications, ensuring consistent status reporting across all channels.

## Implementation Guide

### Adding Heartbeat Updates to Custom Scripts

To update the heartbeat status from your custom scripts:

```python
import os
import datetime

def update_heartbeat_status(status_message, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    status_file = os.path.join(log_dir, "heartbeat_status.txt")
    timestamp = datetime.datetime.now().isoformat()
    
    with open(status_file, 'w') as f:
        f.write(f"{status_message}\n{timestamp}")
```

### Monitoring Heartbeat in Production

For production monitoring, consider:

1. Setting up alerts based on heartbeat status
2. Implementing automatic recovery based on heartbeat failures
3. Logging heartbeat history for trend analysis

## Troubleshooting

- If the heartbeat status is not updating, check that the `logs` directory exists and is writable
- If the frontend is not displaying the status, check the network connection to the backend API
- For persistent issues, check the application logs for more detailed error information