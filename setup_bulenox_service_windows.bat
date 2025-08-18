@echo off
setlocal enabledelayedexpansion

echo ===== Bulenox Sentinel Windows Service Setup =====
echo.

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator.
    echo Please right-click on the script and select "Run as administrator".
    pause
    exit /b 1
)

:: Set paths
set "INSTALL_DIR=C:\opt\bulenox"
set "PYTHON_PATH=%INSTALL_DIR%\venv\Scripts\python.exe"
set "SCRIPT_PATH=%INSTALL_DIR%\bulenox_ai_selenium_adaptive_uc.py"
set "LOG_DIR=%INSTALL_DIR%"
set "OUTPUT_LOG=%LOG_DIR%\bulenox_output.log"
set "ERROR_LOG=%LOG_DIR%\bulenox_error.log"

:: Create directories if they don't exist
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo Created directory: %INSTALL_DIR%
)

if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    echo Created log directory: %LOG_DIR%
)

:: Create empty log files if they don't exist
if not exist "%OUTPUT_LOG%" (
    type nul > "%OUTPUT_LOG%"
    echo Created output log file: %OUTPUT_LOG%
)

if not exist "%ERROR_LOG%" (
    type nul > "%ERROR_LOG%"
    echo Created error log file: %ERROR_LOG%
)

:: Check if NSSM is installed
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo NSSM (Non-Sucking Service Manager) is not installed or not in PATH.
    echo.
    echo Please download NSSM from https://nssm.cc/download
    echo Extract the zip file and copy nssm.exe to C:\Windows\System32
    echo Then run this script again.
    pause
    exit /b 1
)

:: Check if Python script exists
if not exist "%SCRIPT_PATH%" (
    echo Warning: The Python script %SCRIPT_PATH% does not exist.
    echo You will need to copy your script to this location before starting the service.
    echo.
    set /p CONTINUE=Do you want to continue anyway? (Y/N): 
    if /i "!CONTINUE!" neq "Y" exit /b 1
)

:: Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo Warning: Python not found at %PYTHON_PATH%
    echo You will need to set up a virtual environment before starting the service.
    echo.
    set /p CONTINUE=Do you want to continue anyway? (Y/N): 
    if /i "!CONTINUE!" neq "Y" exit /b 1
)

:: Install the service using NSSM
echo Installing Bulenox Sentinel service...

:: Remove existing service if it exists
nssm stop BulenoxSentinel >nul 2>&1
nssm remove BulenoxSentinel confirm >nul 2>&1

:: Create new service
nssm install BulenoxSentinel "%PYTHON_PATH%"
nssm set BulenoxSentinel AppParameters "%SCRIPT_PATH%"
nssm set BulenoxSentinel AppDirectory "%INSTALL_DIR%"
nssm set BulenoxSentinel DisplayName "Bulenox Sentinel"
nssm set BulenoxSentinel Description "Bulenox Sentinel (Adaptive Selenium) service"
nssm set BulenoxSentinel Start SERVICE_AUTO_START

:: Configure stdout/stderr redirection
nssm set BulenoxSentinel AppStdout "%OUTPUT_LOG%"
nssm set BulenoxSentinel AppStderr "%ERROR_LOG%"

:: Configure service recovery options
nssm set BulenoxSentinel AppRestartDelay 5000
nssm set BulenoxSentinel AppThrottle 5000
nssm set BulenoxSentinel AppExit Default Restart
nssm set BulenoxSentinel AppRestartDelay 5000

:: Set failure actions (restart on failure)
nssm set BulenoxSentinel AppFailureActions Restart/5000/Restart/10000/Restart/15000

echo Service installed successfully!
echo.

:: Ask if user wants to start the service now
set /p START_NOW=Do you want to start the service now? (Y/N): 
if /i "%START_NOW%" equ "Y" (
    echo Starting Bulenox Sentinel service...
    nssm start BulenoxSentinel
    timeout /t 2 >nul
    sc query BulenoxSentinel
) else (
    echo You can start the service later using: net start BulenoxSentinel
)

echo.
echo ===== Setup Complete =====
echo.
echo To view logs, use the view_bulenox_logs.ps1 PowerShell script:
echo   - View output log: .\view_bulenox_logs.ps1
echo   - View error log: .\view_bulenox_logs.ps1 -LogType error
echo   - Monitor log in real-time: .\view_bulenox_logs.ps1 -Follow
echo.
echo To manage the service:
echo   - Start: net start BulenoxSentinel
echo   - Stop: net stop BulenoxSentinel
echo   - Remove: nssm remove BulenoxSentinel
echo.

pause