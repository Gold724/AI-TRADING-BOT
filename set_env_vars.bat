@echo off
REM Set environment variables for TradeBot Sentinel
REM Replace with your actual Bulenox credentials

set BULENOX_USERNAME=your_username_here
set BULENOX_PASSWORD=your_password_here

echo Environment variables set:
echo BULENOX_USERNAME=%BULENOX_USERNAME%
echo BULENOX_PASSWORD=[HIDDEN]

echo.
echo Now you can run:
echo python tradebot_sentinel_playwright.py
echo or
echo python tradebot_sentinel_playwright.py --headful

pause