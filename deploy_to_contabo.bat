@echo off
setlocal enabledelayedexpansion

echo ====================================
echo AI Trading Sentinel - Contabo VPS Deployment
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.7 or higher.
    goto :end
)

REM Check if required packages are installed
python -c "import paramiko" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    if exist deployment_requirements.txt (
        pip install -r deployment_requirements.txt
    ) else (
        pip install paramiko cryptography pysftp tqdm
    )
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install required packages. Please check your internet connection.
        goto :end
    )
)

echo.
echo Please enter your Contabo VPS details:
echo --------------------------------

set /p VPS_IP=VPS IP Address: 
set /p VPS_PASSWORD=VPS Password: 
set /p SSH_PORT=SSH Port (default 22): 

if "%SSH_PORT%"=="" set SSH_PORT=22

echo.
echo Select .env file to upload:
echo --------------------------------
echo 1. Use .env.example (default)
echo 2. Use existing .env file
echo 3. Create new .env file

set /p ENV_CHOICE=Choice (1-3): 

if "%ENV_CHOICE%"=="1" (
    set ENV_FILE=.env.example
) else if "%ENV_CHOICE%"=="2" (
    if exist .env (
        set ENV_FILE=.env
    ) else (
        echo .env file not found. Using .env.example instead.
        set ENV_FILE=.env.example
    )
) else if "%ENV_CHOICE%"=="3" (
    echo.
    echo Creating new .env file...
    echo.
    set /p BULENOX_USERNAME=Bulenox Username: 
    set /p BULENOX_PASSWORD=Bulenox Password: 
    set /p SLACK_WEBHOOK_URL=Slack Webhook URL: 
    set /p MAX_DAILY_TRADES=Max Daily Trades (default 5): 
    set /p TRADE_INTERVAL_SECONDS=Trade Interval in Seconds (default 60): 
    
    if "%MAX_DAILY_TRADES%"=="" set MAX_DAILY_TRADES=5
    if "%TRADE_INTERVAL_SECONDS%"=="" set TRADE_INTERVAL_SECONDS=60
    
    (
    echo BULENOX_USERNAME=!BULENOX_USERNAME!
    echo BULENOX_PASSWORD=!BULENOX_PASSWORD!
    echo SLACK_WEBHOOK_URL=!SLACK_WEBHOOK_URL!
    echo MAX_DAILY_TRADES=!MAX_DAILY_TRADES!
    echo TRADE_INTERVAL_SECONDS=!TRADE_INTERVAL_SECONDS!
    echo SIGNAL_SOURCE=webhook
) > .env.temp
    
    set ENV_FILE=.env.temp
) else (
    echo Invalid choice. Using .env.example.
    set ENV_FILE=.env.example
)

echo.
echo Do you want to upload a Chrome profile? (y/n)
set /p CHROME_PROFILE_CHOICE=Choice: 

if /i "%CHROME_PROFILE_CHOICE%" == "y" (
    echo.
    echo Enter the path to your Chrome profile directory:
    echo (e.g. C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data\Default)
    set /p CHROME_PROFILE_PATH=Path: 
    
    if not exist "!CHROME_PROFILE_PATH!" (
        echo Chrome profile directory not found. Continuing without it.
        set CHROME_PROFILE_PARAM=
    ) else (
        set CHROME_PROFILE_PARAM=--chrome-profile "!CHROME_PROFILE_PATH!"
    )
) else (
    set CHROME_PROFILE_PARAM=
)

echo.
echo Starting deployment...
echo --------------------------------

python deploy_to_contabo.py --ip "%VPS_IP%" --password "%VPS_PASSWORD%" --port "%SSH_PORT%" --env-file "%ENV_FILE%" %CHROME_PROFILE_PARAM%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Deployment failed. Please check the error messages above.
) else (
    echo.
    echo Deployment completed successfully!
    echo Your AI Trading Sentinel is now running on your Contabo VPS.
    echo.
    echo To monitor the application:
    echo 1. SSH into your VPS: ssh root@%VPS_IP%
    echo 2. Attach to the tmux session: tmux attach -t trading_sentinel
    echo 3. To detach from the session: Press Ctrl+B, then D
)

if "%ENV_FILE%"==".env.temp" del .env.temp

:end
echo.
echo Press any key to exit...
pause > nul