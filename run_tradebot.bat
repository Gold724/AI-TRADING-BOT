@echo off
REM TradeBot Sentinel - Windows Execution Script
REM This script sets up environment variables and runs the TradeBot Sentinel

echo ===== TradeBot Sentinel - Windows Launcher =====
echo.

REM Set Bulenox credentials
set BULENOX_USERNAME=BX64883
set BULENOX_PASSWORD=XujhMzFf6K

echo Credentials configured:
echo - Username: %BULENOX_USERNAME%
echo - Password: [HIDDEN]
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if the main script exists
if not exist "login_bulenox_playwright.py" (
    echo ERROR: login_bulenox_playwright.py not found
    echo Please ensure you're running this from the correct directory
    pause
    exit /b 1
)

REM Check for command line argument
if "%1"=="--visible" (
    echo Running TradeBot Sentinel in VISIBLE mode (for debugging)...
    echo.
    python login_bulenox_playwright.py --visible
) else if "%1"=="--help" (
    echo.
    echo Usage: run_tradebot.bat [options]
    echo.
    echo Options:
    echo   --visible    Run with visible browser (for debugging)
    echo   --help       Show this help message
    echo.
    echo Default: Runs in headless mode
    echo.
    pause
    exit /b 0
) else (
    echo Running TradeBot Sentinel in HEADLESS mode (default)...
    echo.
    python login_bulenox_playwright.py
)

REM Check exit code
if %errorlevel% equ 0 (
    echo.
    echo ===== TradeBot Sentinel completed successfully =====
    echo.
    echo Generated files:
    if exist "trade.sh" echo - trade.sh (cURL command)
    if exist "trade_request_full.py" echo - trade_request_full.py (Python requests code)
    if exist "tradebot_sentinel.log" echo - tradebot_sentinel.log (execution log)
    if exist "screenshot_*.png" echo - screenshot_*.png (debug screenshots)
    echo.
) else (
    echo.
    echo ===== TradeBot Sentinel encountered an error =====
    echo Exit code: %errorlevel%
    echo.
    echo Troubleshooting:
    echo 1. Check tradebot_sentinel.log for detailed error messages
    echo 2. Run with --visible flag to see browser interactions
    echo 3. Verify your Bulenox credentials are correct
    echo 4. Ensure stable internet connection
    echo.
)

echo Press any key to exit...
pause >nul