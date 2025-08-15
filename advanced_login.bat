@echo off
echo ===================================================
echo AI Trading Sentinel - Advanced Bulenox Login
echo ===================================================
echo.

REM Prompt for credentials
set /p BULENOX_USERNAME=Enter your Bulenox username: 
set /p BULENOX_PASSWORD=Enter your Bulenox password: 

echo.
echo Available Chrome profiles:
dir /b "%LOCALAPPDATA%\Google\Chrome\User Data" | findstr "Profile"
echo Default
echo.

set /p BULENOX_PROFILE_NAME=Enter Chrome profile to use (e.g. Default, Profile 1): 

echo.
echo Starting login process with profile: %BULENOX_PROFILE_NAME%
echo ===================================================

REM Run the login script with specified profile
python -c "import os; os.environ['BULENOX_PROFILE_NAME'] = '%BULENOX_PROFILE_NAME%'; exec(open('ai_login_bulenox.py').read())"

echo.
echo ===================================================
echo If login failed, please try a different Chrome profile
echo or check your credentials.
echo ===================================================

pause