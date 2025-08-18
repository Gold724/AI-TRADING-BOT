@echo off
echo Bulenox cURL Command Capture Tool
echo ====================================

echo Setting environment variables...
set BX64883=your_username
set XujhMzFf6K=XujhMzFf6K

echo Installing dependencies...
call npm install

echo.
echo Running Playwright script to capture cURL command...
node bulenox_trade.js

echo.
if exist trade.sh (
    echo cURL command captured successfully!
    echo The command has been saved to trade.sh and trade_request.py
    echo.
    echo You can run the command with: bash trade.sh
) else (
    echo Failed to capture cURL command.
    echo Please check the console output for errors.
)

echo.
echo Press any key to exit...
pause > nul