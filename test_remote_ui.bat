@echo off
setlocal enabledelayedexpansion

echo AI Trading Sentinel - Remote UI Test
echo =====================================

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if requests module is installed
python -c "import requests" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing requests module...
    pip install requests
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to install requests module
        exit /b 1
    )
)

REM Get the remote API URL
set "API_URL=http://localhost:5000"

if exist ".env" (
    for /f "tokens=1,* delims==" %%a in (.env) do (
        if "%%a"=="VAST_INSTANCE_IP" set "VAST_IP=%%b"
    )
    
    if defined VAST_IP (
        set "API_URL=http://!VAST_IP!:5000"
    )
)

echo.
echo 1. Test local API (http://localhost:5000)
echo 2. Test remote API (!API_URL!)
echo 3. Test custom API URL
echo.

set /p CHOICE="Enter your choice (1-3): "

if "%CHOICE%"=="1" (
    python test_remote_ui.py --url http://localhost:5000
) else if "%CHOICE%"=="2" (
    python test_remote_ui.py --url !API_URL!
) else if "%CHOICE%"=="3" (
    set /p CUSTOM_URL="Enter custom API URL: "
    python test_remote_ui.py --url !CUSTOM_URL!
) else (
    echo Invalid choice
    exit /b 1
)

echo.
echo Test completed.
echo.

pause