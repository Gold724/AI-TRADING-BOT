@echo off
REM TradeBot Sentinel - Run PowerShell as Administrator
REM This batch file helps launch PowerShell scripts with elevated privileges

echo ========================================
echo TradeBot Sentinel - Admin Launcher
echo ========================================
echo.
echo This will launch PowerShell as Administrator to run deployment scripts.
echo Please click "Yes" when prompted by Windows UAC.
echo.
pause

REM Launch PowerShell as Administrator
powershell.exe -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -NoProfile -File "%~dp0setup-windows-deployment.ps1"' -Verb RunAs"

echo.
echo Script launched! Check the new PowerShell window for progress.
echo You can close this window now.
pause