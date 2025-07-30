@echo off
echo 🚀 AI Trading Sentinel - Vast.ai Deployment
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Error: Python is not installed or not in PATH.
    echo Please install Python and try again.
    exit /b 1
)

REM Check if the deployment script exists
if not exist deploy_to_vast.py (
    echo ❌ Error: deploy_to_vast.py not found.
    echo Please ensure you are in the correct directory.
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ❌ Error: .env file not found.
    echo Please create a .env file with the required environment variables.
    exit /b 1
)

echo 📡 Running deployment script...
echo.

python deploy_to_vast.py

echo.
echo 🔍 Deployment process completed.
echo.

pause