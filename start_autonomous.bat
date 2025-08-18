@echo off
REM TradeBot Sentinel - Autonomous Operation Startup Script
REM This script starts the TradeBot Sentinel in fully autonomous mode

echo ========================================
echo TradeBot Sentinel - Autonomous Startup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "tradebot_sentinel_advanced_pro.py" (
    echo ERROR: tradebot_sentinel_advanced_pro.py not found
    echo Please ensure you're running this from the correct directory
    pause
    exit /b 1
)

if not exist "scheduler.py" (
    echo ERROR: scheduler.py not found
    echo Please ensure all required files are present
    pause
    exit /b 1
)

if not exist "cron_config.json" (
    echo ERROR: cron_config.json not found
    echo Please ensure the configuration file is present
    pause
    exit /b 1
)

REM Create necessary directories
echo Creating required directories...
if not exist "logs" mkdir logs
if not exist "logs\curls" mkdir logs\curls
if not exist "logs\json" mkdir logs\json
if not exist "logs\screenshots" mkdir logs\screenshots
if not exist "backups" mkdir backups

REM Check environment variables
echo Checking environment configuration...
if "%BULENOX_USERNAME%"=="" (
    echo WARNING: BULENOX_USERNAME not set
    echo Please set your trading platform credentials
)

if "%BULENOX_PASSWORD%"=="" (
    echo WARNING: BULENOX_PASSWORD not set
    echo Please set your trading platform credentials
)

REM Install required packages if needed
echo Installing/updating required packages...
pip install playwright asyncio aiofiles curlconverter schedule python-telegram-bot aiosmtplib >nul 2>&1

REM Install Playwright browsers
echo Installing Playwright browsers (this may take a few minutes)...
playwright install chromium >nul 2>&1

echo.
echo ========================================
echo Starting Autonomous Trading System
echo ========================================
echo.
echo The system will now start in autonomous mode.
echo Press Ctrl+C to stop the scheduler.
echo.
echo Logs will be available in the 'logs' directory.
echo Trade data will be saved in 'logs/trades.csv'.
echo Screenshots will be saved in 'logs/screenshots'.
echo.
echo Starting scheduler...
echo.

REM Start the scheduler
python scheduler.py --config cron_config.json --daemon

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start the scheduler
    echo Please check the logs for more information
    pause
    exit /b 1
)

echo.
echo ========================================
echo Autonomous Trading System Started
echo ========================================
echo.
echo The TradeBot Sentinel is now running autonomously.
echo Check 'logs/scheduler.log' for detailed logs.
echo.
echo To stop the system, run: stop_autonomous.bat
echo.
pause