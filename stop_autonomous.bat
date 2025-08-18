@echo off
REM TradeBot Sentinel - Stop Autonomous Operation Script
REM This script stops the TradeBot Sentinel autonomous system

echo ========================================
echo TradeBot Sentinel - Stop Autonomous
echo ========================================
echo.

REM Kill any running Python processes related to TradeBot
echo Stopping TradeBot Sentinel processes...

REM Kill scheduler
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *scheduler*" >nul 2>&1

REM Kill any TradeBot processes
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr "tradebot"') do (
    taskkill /F /PID %%i >nul 2>&1
)

REM Kill any Playwright/Chromium processes
taskkill /F /IM chromium.exe >nul 2>&1
taskkill /F /IM chrome.exe >nul 2>&1

REM Send stop signal to scheduler if it's running as a service
if exist "scheduler.pid" (
    echo Sending stop signal to scheduler...
    python -c "import os, signal; pid = int(open('scheduler.pid').read().strip()); os.kill(pid, signal.SIGTERM)" >nul 2>&1
    del scheduler.pid >nul 2>&1
)

REM Clean up any lock files
if exist "*.lock" del *.lock >nul 2>&1
if exist "logs\*.lock" del logs\*.lock >nul 2>&1

echo.
echo ========================================
echo System Stopped
echo ========================================
echo.
echo The TradeBot Sentinel autonomous system has been stopped.
echo.
echo Final system status:
echo - All Python processes terminated
echo - Browser processes closed
echo - Lock files cleaned up
echo.
echo To restart the system, run: start_autonomous.bat
echo.
pause