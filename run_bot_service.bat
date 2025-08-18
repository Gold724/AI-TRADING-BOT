@echo off
REM AI Trading Sentinel - Windows Service Alternative
REM This batch file runs the bot continuously with auto-restart

cd /d "%~dp0"

echo ========================================
echo AI Trading Sentinel - Service Mode
echo ========================================
echo Starting at %date% %time%
echo.

:RESTART_LOOP
echo [%date% %time%] Starting AI Trading Sentinel...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [%date% %time%] Virtual environment activated
) else (
    echo [%date% %time%] No virtual environment found, using system Python
)

REM Run the main bot
python main.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Bot exited normally
) else (
    echo [%date% %time%] Bot crashed with error code %ERRORLEVEL%
)

echo [%date% %time%] Waiting 30 seconds before restart...
timeout /t 30 /nobreak >nul

echo [%date% %time%] Restarting bot...
echo.
goto RESTART_LOOP