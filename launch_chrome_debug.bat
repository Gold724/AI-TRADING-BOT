@echo off
echo ========================================
echo 🚀 LAUNCHING CHROME WITH DEBUG MODE
echo ========================================
echo.
echo Using Profile: Profile 13
echo Debug Port: 9222
echo.
echo After Chrome opens:
echo 1. Navigate to Bulenox and login
echo 2. Run: python bulenox_network_interceptor.py
echo 3. Perform trading actions
echo 4. Press Ctrl+C to stop and save logs
echo.
echo ========================================

:: Close any existing Chrome instances
taskkill /f /im chrome.exe 2>nul
timeout /t 2 /nobreak >nul

:: Launch Chrome with debugging enabled
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\Admin\AppData\Local\Google\Chrome\User Data" --profile-directory="Profile 13" --disable-web-security --disable-features=VizDisplayCompositor

echo.
echo ✅ Chrome launched with debugging enabled!
echo 🌐 You can now navigate to Bulenox
echo 🤖 Run the interceptor: python bulenox_network_interceptor.py
echo.
pause