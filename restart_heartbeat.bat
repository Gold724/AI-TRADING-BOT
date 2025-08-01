@echo off
REM Restart Heartbeat for AI Trading Sentinel
REM This script is called by the heartbeat monitor when issues are detected

echo [%date% %time%] Attempting to restart AI Trading Sentinel Heartbeat... >> logs\restart_log.txt

REM Kill any existing heartbeat.py processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq heartbeat.py" >nul 2>&1

REM Wait a moment for processes to terminate
timeout /t 2 /nobreak >nul

REM Update heartbeat status file to indicate restart
if not exist logs mkdir logs
echo 🔄 Heartbeat restarting - Triggered by monitor > logs\heartbeat_status.txt
echo %date%T%time% >> logs\heartbeat_status.txt
echo {"session_active": false} >> logs\heartbeat_status.txt

REM Start the heartbeat in a new window
start "AI Trading Sentinel Heartbeat" cmd /c "python heartbeat.py"

echo [%date% %time%] Heartbeat restart initiated >> logs\restart_log.txt