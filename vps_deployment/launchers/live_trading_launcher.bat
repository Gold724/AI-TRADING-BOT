@echo off
REM AI Trading Sentinel - Live Trading with Auto Endpoint Validation
REM ----------------------------------------------------------------
REM Windows Batch version
REM Steps:
REM 1. Auto-capture latest cURLs (login + trade endpoints)
REM 2. Validate endpoints before trading
REM 3. Run monitor mode for stability check
REM 4. Switch to headless live trading if all checks pass
REM 5. Auto-restart if process fails

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT=tradebot_sentinel_advanced_pro.py
set VALIDATOR_SCRIPT=endpoint_validator.py
set CURL_CAPTURE_SCRIPT=login_bulenox_playwright.py
set LOG_DIR=logs
set ERROR_LOG=%LOG_DIR%\errors\live_errors.log
set MONITOR_TIME=60

REM Create log directories
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%LOG_DIR%\errors" mkdir "%LOG_DIR%\errors"

REM Enhanced logging function
set "log_file=%LOG_DIR%\launcher_batch.log"

echo === AI Trading Sentinel Live Trading with Validation ===
echo [%date% %time%] INFO: Starting AI Trading Sentinel launcher >> "%log_file%"
echo [%date% %time%] INFO: Starting AI Trading Sentinel launcher

REM Step 1: Auto-capture cURLs
echo [1/5] Capturing latest cURLs...
echo [%date% %time%] INFO: Step 1 - Capturing cURLs >> "%log_file%"
python "%CURL_CAPTURE_SCRIPT%" --capture-all > "%LOG_DIR%\curl_capture.log" 2>&1
if !errorlevel! neq 0 (
    echo [%date% %time%] ERROR: cURL capture failed >> "%log_file%"
    echo ERROR: cURL capture failed. Check %LOG_DIR%\curl_capture.log
    type "%LOG_DIR%\curl_capture.log"
    exit /b 1
)
echo [%date% %time%] SUCCESS: cURL capture completed >> "%log_file%"
echo SUCCESS: cURL capture completed

REM Step 2: Validate captured endpoints
echo [2/5] Validating endpoints...
echo [%date% %time%] INFO: Step 2 - Validating endpoints >> "%log_file%"
python "%VALIDATOR_SCRIPT%" > "%LOG_DIR%\endpoint_validation.log" 2>&1

REM Check validation results
findstr /C:"VERDICT: MISSION ACCOMPLISHED" "%LOG_DIR%\endpoint_validation.log" >nul
if !errorlevel! neq 0 (
    echo [%date% %time%] ERROR: Endpoint validation failed >> "%log_file%"
    echo ERROR: Endpoint validation failed. Check %LOG_DIR%\endpoint_validation.log
    type "%LOG_DIR%\endpoint_validation.log"
    exit /b 1
)
echo [%date% %time%] SUCCESS: Endpoint validation passed >> "%log_file%"
echo SUCCESS: Endpoint validation passed

REM Step 3: Run monitor mode
echo [3/5] Running monitor mode for %MONITOR_TIME% seconds...
echo [%date% %time%] INFO: Step 3 - Starting monitor mode >> "%log_file%"
start /B python "%SCRIPT%" --monitor > "%LOG_DIR%\monitor_output.log" 2>&1

REM Get the PID of the monitor process (approximate)
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find /C "python.exe"') do set monitor_count=%%i

REM Wait for monitor time
timeout /t %MONITOR_TIME% /nobreak >nul

REM Step 4: Check monitor mode output
echo [4/5] Checking monitor mode results...
echo [%date% %time%] INFO: Step 4 - Checking monitor results >> "%log_file%"
findstr /C:"Traceback" "%LOG_DIR%\monitor_output.log" >nul
if !errorlevel! equ 0 (
    echo [%date% %time%] ERROR: Error detected in monitor mode >> "%log_file%"
    echo ERROR: Error detected in monitor mode. Check %LOG_DIR%\monitor_output.log
    type "%LOG_DIR%\monitor_output.log"
    REM Kill monitor processes
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *monitor*" >nul 2>&1
    exit /b 1
)

REM Kill monitor processes before starting headless mode
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *monitor*" >nul 2>&1
echo [%date% %time%] SUCCESS: Monitor mode check passed >> "%log_file%"
echo SUCCESS: Monitor mode check passed. Starting headless mode...

REM Step 5: Start headless live trading
echo [5/5] Starting headless live trading...
echo [%date% %time%] INFO: Step 5 - Starting headless live trading >> "%log_file%"
start /B python "%SCRIPT%" --headless > "%LOG_DIR%\live_output.log" 2>&1

echo [%date% %time%] SUCCESS: Live trading started >> "%log_file%"
echo SUCCESS: AI Trading Sentinel is now running in live mode!
echo Monitor logs: %LOG_DIR%\live_output.log
echo Press Ctrl+C to stop the trading bot

REM Continuous monitoring loop
set restart_count=0
set max_restarts=5

:monitor_loop
timeout /t 10 /nobreak >nul

REM Check if live trading process is still running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *headless*" 2>nul | find /I "python.exe" >nul
if !errorlevel! neq 0 (
    set /a restart_count+=1
    echo [%date% %time%] ERROR: Live process crashed (Restart #!restart_count!) >> "%ERROR_LOG%"
    echo [%date% %time%] ERROR: Live process crashed (Restart #!restart_count!) >> "%log_file%"
    echo WARNING: Live process crashed (Restart #!restart_count!)
    
    if !restart_count! geq %max_restarts% (
        echo [%date% %time%] CRITICAL: Maximum restart attempts reached >> "%log_file%"
        echo CRITICAL: Maximum restart attempts (%max_restarts%) reached. Stopping.
        goto :cleanup
    )
    
    echo Restarting live trading process...
    echo [%date% %time%] INFO: Restarting live trading process >> "%log_file%"
    
    REM Wait before restarting
    timeout /t 5 /nobreak >nul
    
    REM Restart the live trading process
    start /B python "%SCRIPT%" --headless > "%LOG_DIR%\live_output.log" 2>&1
    echo [%date% %time%] INFO: Live trading process restarted >> "%log_file%"
    echo Live trading process restarted
)

REM Check for critical errors in recent logs
if exist "%LOG_DIR%\live_output.log" (
    for /f "tokens=*" %%i in ('tail -5 "%LOG_DIR%\live_output.log" 2^>nul ^| findstr /C:"CRITICAL" /C:"FATAL"') do (
        echo [%date% %time%] WARNING: Critical error detected in logs >> "%log_file%"
        echo WARNING: Critical error detected in live trading logs
    )
)

goto :monitor_loop

:cleanup
echo [%date% %time%] INFO: Cleaning up processes >> "%log_file%"
echo Cleaning up processes...

REM Kill any remaining Python processes related to trading
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *trading*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *monitor*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *headless*" >nul 2>&1

echo [%date% %time%] INFO: AI Trading Sentinel launcher session ended >> "%log_file%"
echo AI Trading Sentinel launcher session ended

endlocal
pause