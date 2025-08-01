@echo off
REM Heartbeat Status Updater Batch File
REM This batch file provides easy commands to update the heartbeat status

IF "%1"=="" (
    echo Usage: update_heartbeat_status.bat [status_type]
    echo.
    echo Available status types:
    echo   waiting    - Waiting for signals
    echo   login      - Login successful
    echo   trade      - Trade executed
    echo   profit     - Profit secured
    echo   error      - Error occurred
    echo   custom "Your custom message"
    echo.
    exit /b
)

SET LOG_DIR=logs

IF "%1"=="waiting" (
    python update_heartbeat_status.py "🔄 Waiting for signals..." --log-dir %LOG_DIR%
    exit /b
)

IF "%1"=="login" (
    python update_heartbeat_status.py "✅ Login successful - Session active" --log-dir %LOG_DIR%
    exit /b
)

IF "%1"=="trade" (
    python update_heartbeat_status.py "💰 Trade executed - GOLD BUY @ 2350.00" --log-dir %LOG_DIR%
    exit /b
)

IF "%1"=="profit" (
    python update_heartbeat_status.py "🎯 Profit secured! +$120.50 on GOLD" --log-dir %LOG_DIR%
    exit /b
)

IF "%1"=="error" (
    python update_heartbeat_status.py "❌ Error occurred - Login failed" --log-dir %LOG_DIR%
    exit /b
)

IF "%1"=="custom" (
    IF "%~2"=="" (
        echo Error: Custom message required
        exit /b
    )
    python update_heartbeat_status.py "%~2" --log-dir %LOG_DIR%
    exit /b
)

echo Unknown status type: %1
echo Run without parameters to see available options