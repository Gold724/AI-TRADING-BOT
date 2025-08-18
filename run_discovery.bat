@echo off
REM TradeBot Sentinel - Trade Endpoint Discovery Launcher
REM Automatically captures missing 70% of trade execution endpoints

echo ========================================
echo 🎯 TradeBot Sentinel - Trade Discovery
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if setup has been run
if not exist "logs\curls" (
    echo 🔧 Running initial setup...
    python setup_discovery.py
    if errorlevel 1 (
        echo ❌ Setup failed
        pause
        exit /b 1
    )
)

REM Check environment variables
if "%BULENOX_USERNAME%"=="" (
    echo ⚠️ BULENOX_USERNAME not set!
    echo Please set your environment variables:
    echo set BULENOX_USERNAME=your_username
    echo set BULENOX_PASSWORD=your_password
    echo.
    echo Or create a .env file with your credentials
    pause
    exit /b 1
)

if "%BULENOX_PASSWORD%"=="" (
    echo ⚠️ BULENOX_PASSWORD not set!
    echo Please set your environment variables:
    echo set BULENOX_USERNAME=your_username
    echo set BULENOX_PASSWORD=your_password
    echo.
    echo Or create a .env file with your credentials
    pause
    exit /b 1
)

echo ✅ Environment configured
echo 👤 Username: %BULENOX_USERNAME%
echo 🔐 Password: [HIDDEN]
echo.

REM Ask user for run mode
echo 🎮 Select run mode:
echo 1. Visible mode (recommended for first run)
echo 2. Headless mode (automated)
echo 3. Debug mode (visible + verbose logging)
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo 🖥️ Running in VISIBLE mode...
    python trade_endpoint_discovery.py --visible
) else if "%choice%"=="2" (
    echo 👻 Running in HEADLESS mode...
    python trade_endpoint_discovery.py --headless
) else if "%choice%"=="3" (
    echo 🐛 Running in DEBUG mode...
    set VERBOSE_LOGGING=true
    python trade_endpoint_discovery.py --visible
) else (
    echo ❌ Invalid choice, defaulting to visible mode
    python trade_endpoint_discovery.py --visible
)

REM Check if discovery was successful
if errorlevel 1 (
    echo.
    echo ❌ Discovery failed! Check logs for details:
    echo 📁 logs/trade_endpoint_discovery.log
    echo 📸 logs/screenshots/
    pause
    exit /b 1
)

echo.
echo ========================================
echo 🎉 Discovery completed successfully!
echo ========================================
echo.
echo 📊 Results:
echo 📁 Captured cURLs: logs/curls/
echo 📄 JSON bodies: logs/json/
echo 📸 Screenshots: logs/screenshots/
echo 🐍 Python code: trade_request_full.py
echo 📋 Summary: logs/endpoints/discovery_summary.json
echo.

REM Show summary if available
if exist "logs\endpoints\discovery_summary.json" (
    echo 📈 Quick Summary:
    python -c "import json; data=json.load(open('logs/endpoints/discovery_summary.json')); print(f'🎯 Endpoints Captured: {data[\"total_endpoints_captured\"]}'); print(f'🎬 Unique Actions: {len(data[\"captured_actions\"])}'); print('📋 Actions:'); [print(f'  ✅ {action}') for action in data['captured_actions']]"
    echo.
)

echo 🚀 Ready for VPS deployment!
echo.
echo Next steps:
echo 1. Review captured endpoints in logs/curls/
echo 2. Test generated Python code: trade_request_full.py
echo 3. Deploy to VPS for automated trading
echo.
pause