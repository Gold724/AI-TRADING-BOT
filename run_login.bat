@echo off
echo ===================================================
echo AI Trading Sentinel - Bulenox Login Assistant
echo ===================================================
echo.

REM Prompt for credentials
set /p BULENOX_USERNAME=Enter your Bulenox username: 
set /p BULENOX_PASSWORD=Enter your Bulenox password: 

echo.
echo Using Chrome profile: Profile 13
echo If login fails, you may need to update the profile in the script.
echo.

echo Starting login process...
echo ===================================================

REM Run the login script
python ai_login_bulenox.py

echo.
echo ===================================================
echo If login failed, please check the following:
echo 1. Verify your username and password
echo 2. Check your Chrome profile settings
echo 3. Ensure you have internet connectivity
echo 4. Try running with a different Chrome profile
echo ===================================================

pause