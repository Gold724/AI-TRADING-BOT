#!/bin/bash
# Start Heartbeat Monitor for AI Trading Sentinel
# This script starts the heartbeat monitor in the background

echo "Starting AI Trading Sentinel Heartbeat Monitor..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if heartbeat_monitor.py exists
if [ ! -f "heartbeat_monitor.py" ]; then
    echo "Error: heartbeat_monitor.py not found"
    exit 1
fi

# Start the heartbeat monitor in the background
nohup python3 heartbeat_monitor.py --interval 60 --max-age 5 --restart "bash restart_heartbeat.sh" > logs/heartbeat_monitor_nohup.log 2>&1 &

# Save the PID for later reference
echo $! > logs/heartbeat_monitor.pid

echo "Heartbeat monitor started successfully in background with PID $(cat logs/heartbeat_monitor.pid)."
echo "To check status: python3 heartbeat_monitor.py --check"
echo "To stop: kill -15 $(cat logs/heartbeat_monitor.pid)"