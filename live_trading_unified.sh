#!/bin/bash

# ========================================================
# AI Trading Sentinel - Unified Live Trading Launcher
# Enhanced Version with Session Management
# Features:
# 1. Pulls latest code from GitHub before starting
# 2. Runs monitor mode for stability check
# 3. Switches to headless mode if no errors
# 4. Watches GitHub for updates and auto-restarts
# 5. Logs all crashes, updates, and outputs
# 6. Session recovery and browser management
# 7. Network connectivity monitoring
# 8. Emergency stop and restart capabilities
# ========================================================

SCRIPT="tradebot_sentinel.py"
LOG_DIR="logs"
ERROR_LOG="$LOG_DIR/errors/live_errors.log"
UPDATE_LOG="$LOG_DIR/updates/update.log"
SESSION_LOG="$LOG_DIR/session/session.log"
MONITOR_TIME=60 # Seconds in monitor mode
GIT_REPO_DIR="/root/ai-trading-sentinel" # Change to your repo path
MAX_RETRIES=3
RETRY_DELAY=30

# Create necessary directories
mkdir -p "$LOG_DIR/errors" "$LOG_DIR/updates" "$LOG_DIR/session" "$LOG_DIR/screenshots"

echo "=== Starting AI Trading Sentinel Unified Launcher ==="
echo "$(date): Launcher started" >> "$SESSION_LOG"

# Function to check network connectivity
check_network() {
    if ping -c 1 bulenox.projectx.com &> /dev/null; then
        return 0
    else
        echo "$(date): Network connectivity issue detected" >> "$ERROR_LOG"
        return 1
    fi
}

# Function to kill any existing browser processes
cleanup_browsers() {
    echo "$(date): Cleaning up existing browser processes" >> "$SESSION_LOG"
    pkill -f "chrome" 2>/dev/null || true
    pkill -f "chromium" 2>/dev/null || true
    pkill -f "playwright" 2>/dev/null || true
    sleep 5
}

# Function to check if bot is responsive
check_bot_health() {
    local pid=$1
    if kill -0 "$pid" 2>/dev/null; then
        # Check if bot is actually trading (look for recent activity)
        if find "$LOG_DIR" -name "*.log" -mmin -5 | grep -q .; then
            return 0
        fi
    fi
    return 1
}

# Step 0: Initial setup and cleanup
echo "[0/5] Initial setup and cleanup..."
cleanup_browsers

# Check network connectivity
if ! check_network; then
    echo "Network connectivity issue. Waiting 30 seconds..."
    sleep 30
    if ! check_network; then
        echo "Network still unavailable. Exiting."
        exit 1
    fi
fi

# Step 1: Pull latest code from GitHub
echo "[1/5] Pulling latest code from GitHub..."
cd "$GIT_REPO_DIR" || exit
git reset --hard
git pull origin main >> "$UPDATE_LOG" 2>&1
echo "$(date): Initial pull complete." >> "$UPDATE_LOG"

# Step 2: Run Monitor Mode with retry logic
echo "[2/5] Running monitor mode for ${MONITOR_TIME}s..."
retry_count=0
while [ $retry_count -lt $MAX_RETRIES ]; do
    cleanup_browsers
    python "$SCRIPT" --monitor > "$LOG_DIR/monitor_output.log" 2>&1 &
    MONITOR_PID=$!
    
    sleep $MONITOR_TIME
    
    if grep -q "Traceback\|Error\|Failed" "$LOG_DIR/monitor_output.log"; then
        echo "$(date): Error in monitor mode (attempt $((retry_count + 1))). Retrying..." >> "$ERROR_LOG"
        kill $MONITOR_PID 2>/dev/null || true
        retry_count=$((retry_count + 1))
        sleep $RETRY_DELAY
    else
        echo "$(date): Monitor mode passed successfully" >> "$SESSION_LOG"
        kill $MONITOR_PID 2>/dev/null || true
        break
    fi
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "Monitor mode failed after $MAX_RETRIES attempts. Exiting."
    exit 1
fi

echo "[3/5] Monitor mode passed. Starting headless mode..."

# Step 3: Start Headless Mode with session management
start_headless_mode() {
    cleanup_browsers
    echo "$(date): Starting headless trading mode" >> "$SESSION_LOG"
    
    # Set environment variables for session persistence
    export BULENOX_USERNAME="BX64883"
    export BULENOX_PASSWORD="XujhMzFf6K"
    export HEADLESS_MODE="true"
    export SESSION_RECOVERY="true"
    
    python "$SCRIPT" --headless --session-recovery > "$LOG_DIR/live_output.log" 2>&1 &
    return $!
}

LIVE_PID=$(start_headless_mode)

# Step 4: GitHub Watcher (Background)
echo "[4/5] Starting GitHub watcher..."
(
    cd "$GIT_REPO_DIR" || exit
    LAST_HASH=$(git rev-parse HEAD)
    while true; do
        git fetch origin main 2>/dev/null
        NEW_HASH=$(git rev-parse origin/main 2>/dev/null)
        if [ "$LAST_HASH" != "$NEW_HASH" ] && [ -n "$NEW_HASH" ]; then
            echo "$(date): Update detected. Pulling changes..." >> "$UPDATE_LOG"
            git reset --hard
            git pull origin main >> "$UPDATE_LOG" 2>&1
            echo "$(date): Restarting bot due to update..." >> "$UPDATE_LOG"
            
            # Kill current process
            kill $LIVE_PID 2>/dev/null || true
            sleep 10
            cleanup_browsers
            
            # Test in monitor mode first
            python "$SCRIPT" --monitor > "$LOG_DIR/monitor_update.log" 2>&1 &
            MONITOR_PID=$!
            sleep $MONITOR_TIME
            
            if ! grep -q "Traceback\|Error\|Failed" "$LOG_DIR/monitor_update.log"; then
                kill $MONITOR_PID 2>/dev/null || true
                LIVE_PID=$(start_headless_mode)
                echo "$(date): Bot restarted successfully after update" >> "$UPDATE_LOG"
            else
                echo "$(date): Update caused errors, reverting..." >> "$ERROR_LOG"
                git reset --hard HEAD~1
                LIVE_PID=$(start_headless_mode)
            fi
            LAST_HASH=$NEW_HASH
        fi
        sleep 30
    done
) &
GIT_WATCHER_PID=$!

# Step 5: Enhanced Live Process Monitor with Health Checks
echo "[5/5] Starting enhanced process monitor..."
health_check_failures=0
max_health_failures=3

while true; do
    if ! check_bot_health $LIVE_PID; then
        health_check_failures=$((health_check_failures + 1))
        echo "$(date): Health check failed ($health_check_failures/$max_health_failures)" >> "$ERROR_LOG"
        
        if [ $health_check_failures -ge $max_health_failures ]; then
            echo "$(date): Bot health critical. Performing full restart..." >> "$ERROR_LOG"
            
            # Kill current process
            kill $LIVE_PID 2>/dev/null || true
            sleep 5
            cleanup_browsers
            
            # Check network before restart
            if check_network; then
                # Full recovery cycle
                python "$SCRIPT" --monitor > "$LOG_DIR/monitor_recovery.log" 2>&1 &
                MONITOR_PID=$!
                sleep $MONITOR_TIME
                
                if ! grep -q "Traceback\|Error\|Failed" "$LOG_DIR/monitor_recovery.log"; then
                    kill $MONITOR_PID 2>/dev/null || true
                    LIVE_PID=$(start_headless_mode)
                    health_check_failures=0
                    echo "$(date): Full recovery completed successfully" >> "$SESSION_LOG"
                else
                    echo "$(date): Recovery failed, waiting before retry" >> "$ERROR_LOG"
                    sleep 300 # Wait 5 minutes before next attempt
                fi
            else
                echo "$(date): Network unavailable, waiting for connectivity" >> "$ERROR_LOG"
                sleep 60
            fi
        fi
    else
        health_check_failures=0
    fi
    
    sleep 30
done

# Cleanup on exit
trap 'kill $LIVE_PID $GIT_WATCHER_PID 2>/dev/null; cleanup_browsers; echo "$(date): Launcher stopped" >> "$SESSION_LOG"' EXIT