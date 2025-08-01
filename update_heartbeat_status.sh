#!/bin/bash
# Heartbeat Status Updater Shell Script
# This shell script provides easy commands to update the heartbeat status

LOG_DIR="logs"

if [ $# -eq 0 ]; then
    echo "Usage: ./update_heartbeat_status.sh [status_type]"
    echo ""
    echo "Available status types:"
    echo "  waiting    - Waiting for signals"
    echo "  login      - Login successful"
    echo "  trade      - Trade executed"
    echo "  profit     - Profit secured"
    echo "  error      - Error occurred"
    echo "  custom 'Your custom message'"
    echo ""
    exit 1
fi

case "$1" in
    "waiting")
        python update_heartbeat_status.py "🔄 Waiting for signals..." --log-dir "$LOG_DIR"
        ;;
    "login")
        python update_heartbeat_status.py "✅ Login successful - Session active" --log-dir "$LOG_DIR"
        ;;
    "trade")
        python update_heartbeat_status.py "💰 Trade executed - GOLD BUY @ 2350.00" --log-dir "$LOG_DIR"
        ;;
    "profit")
        python update_heartbeat_status.py "🎯 Profit secured! +$120.50 on GOLD" --log-dir "$LOG_DIR"
        ;;
    "error")
        python update_heartbeat_status.py "❌ Error occurred - Login failed" --log-dir "$LOG_DIR"
        ;;
    "custom")
        if [ -z "$2" ]; then
            echo "Error: Custom message required"
            exit 1
        fi
        python update_heartbeat_status.py "$2" --log-dir "$LOG_DIR"
        ;;
    *)
        echo "Unknown status type: $1"
        echo "Run without parameters to see available options"
        exit 1
        ;;
esac