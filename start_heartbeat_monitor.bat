@echo off
REM Start Heartbeat Monitor for AI Trading Sentinel
REM This script starts the heartbeat monitor in the background

echo Starting AI Trading Sentinel Heartbeat Monitor...

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if heartbeat_monitor.py exists
if not exist heartbeat_monitor.py (
    echo Error: heartbeat_monitor.py not found
    exit /b 1
)

REM Start the heartbeat monitor in the background
start /B python heartbeat_monitor.py --interval 60 --max-age 5 --restart "python restart_heartbeat.bat"

echo Heartbeat monitor started successfully in background.
echo To check status: python heartbeat_monitor.py --check