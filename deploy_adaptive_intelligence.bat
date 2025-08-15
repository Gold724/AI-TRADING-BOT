@echo off
REM Deployment script wrapper for TRAE AI Trading Bot with Adaptive Intelligence

echo === TRAE AI Trading Bot Deployment Script (Windows) ===
echo This batch file will launch the PowerShell deployment script
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as administrator
    echo Please right-click on this batch file and select "Run as administrator"
    pause
    exit /b 1
)

REM Launch the PowerShell script
echo Launching PowerShell deployment script...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0deploy_adaptive_intelligence.ps1"

REM Check if PowerShell script executed successfully
if %errorLevel% neq 0 (
    echo.
    echo Error: PowerShell deployment script failed
    pause
    exit /b 1
)

echo.
echo Deployment completed successfully
pause