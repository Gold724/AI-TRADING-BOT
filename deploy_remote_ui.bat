@echo off
echo ======================================
echo AI Trading Sentinel - Remote UI Deployment
echo ======================================

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo Error: .env file not found
    echo Please create a .env file with the required variables
    exit /b 1
)

echo.
echo Choose deployment option:
echo 1. Deploy both backend and frontend
echo 2. Deploy backend API only
echo 3. Deploy frontend UI only
echo 4. Dry run (validate configuration only)
echo.

set /p OPTION="Enter option (1-4): "

if "%OPTION%"=="1" (
    echo Deploying both backend and frontend...
    python deploy_remote_ui.py
) else if "%OPTION%"=="2" (
    echo Deploying backend API only...
    python deploy_remote_ui.py --backend-only
) else if "%OPTION%"=="3" (
    echo Deploying frontend UI only...
    python deploy_remote_ui.py --frontend-only
) else if "%OPTION%"=="4" (
    echo Running in dry-run mode...
    python deploy_remote_ui.py --dry-run
) else (
    echo Invalid option selected
    exit /b 1
)

echo.
echo Deployment script completed
echo.

pause