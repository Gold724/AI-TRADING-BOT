#!/bin/bash

# AI Trading Sentinel - Live Trading with Auto Endpoint Validation
# ----------------------------------------------------------------
# Steps:
# 1. Auto-capture latest cURLs (login + trade endpoints)
# 2. Validate endpoints before trading
# 3. Run monitor mode for stability check
# 4. Switch to headless live trading if all checks pass
# 5. Auto-restart if process fails

SCRIPT="tradebot_sentinel_advanced_pro.py"
VALIDATOR_SCRIPT="endpoint_validator.py"
CURL_CAPTURE_SCRIPT="login_bulenox_playwright.py"
LOG_DIR="logs"
ERROR_LOG="$LOG_DIR/errors/live_errors.log"
MONITOR_TIME=60  # Seconds for stability test

mkdir -p "$LOG_DIR/errors"

echo "=== AI Trading Sentinel Live Trading with Validation ==="

# Step 1: Auto-capture cURLs
echo "[1/5] Capturing latest cURLs..."
python "$CURL_CAPTURE_SCRIPT" --capture-all > "$LOG_DIR/curl_capture.log" 2>&1
if [ $? -ne 0 ]; then
    echo "Error during cURL capture. Check $LOG_DIR/curl_capture.log"
    exit 1
fi

# Step 2: Validate captured endpoints
echo "[2/5] Validating endpoints..."
python "$VALIDATOR_SCRIPT" > "$LOG_DIR/endpoint_validation.log" 2>&1
if ! grep -q "VERDICT: MISSION ACCOMPLISHED" "$LOG_DIR/endpoint_validation.log"; then
    echo "Endpoint validation failed. Check $LOG_DIR/endpoint_validation.log"
    exit 1
fi

# Step 3: Run monitor mode
echo "[3/5] Running monitor mode for ${MONITOR_TIME}s..."
python "$SCRIPT" --monitor > "$LOG_DIR/monitor_output.log" 2>&1 &
MONITOR_PID=$!
sleep $MONITOR_TIME

# Step 4: Check monitor mode output
if grep -q "Traceback" "$LOG_DIR/monitor_output.log"; then
    echo "Error detected in monitor mode. Check $LOG_DIR/monitor_output.log"
    kill $MONITOR_PID
    exit 1
fi

# Kill monitor process before starting headless mode
kill $MONITOR_PID
echo "[4/5] Monitor mode check passed. Starting headless mode..."

# Step 5: Start headless live trading
python "$SCRIPT" --headless > "$LOG_DIR/live_output.log" 2>&1 &
LIVE_PID=$!

# Continuous monitoring loop
while true; do
    if ! kill -0 $LIVE_PID 2>/dev/null; then
        echo "Live trading process stopped unexpectedly. Restarting from Step 1..."
        echo "$(date): Live process crashed" >> "$ERROR_LOG"
        exec "$0"  # Restart entire script from the beginning
    fi
    sleep 10
done