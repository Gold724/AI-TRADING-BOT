#!/bin/bash
# Restart Heartbeat for AI Trading Sentinel
# This script is called by the heartbeat monitor when issues are detected

echo "[$(date)] Attempting to restart AI Trading Sentinel Heartbeat..." >> logs/restart_log.txt

# Kill any existing heartbeat.py processes
pkill -f "python.*heartbeat\.py" || true

# Wait a moment for processes to terminate
sleep 2

# Update heartbeat status file to indicate restart
mkdir -p logs
echo "🔄 Heartbeat restarting - Triggered by monitor" > logs/heartbeat_status.txt
echo "$(date -Iseconds)" >> logs/heartbeat_status.txt
echo '{"session_active": false}' >> logs/heartbeat_status.txt

# Start the heartbeat in a new process
nohup python3 heartbeat.py > logs/heartbeat_restart.log 2>&1 &

# Save the PID for reference
echo $! > logs/heartbeat.pid

echo "[$(date)] Heartbeat restart initiated with PID $!" >> logs/restart_log.txt