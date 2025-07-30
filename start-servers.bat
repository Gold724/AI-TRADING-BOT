@echo off
echo AI Trading Sentinel Startup Script
echo ===============================
echo.

:: Create logs directory if it doesn't exist
if not exist "%~dp0backend\logs" (
    mkdir "%~dp0backend\logs"
    echo Created logs directory at %~dp0backend\logs
)

:: Start the backend server
echo Starting backend server...
start "AI Trading Sentinel Backend" cmd /k "cd /d "%~dp0backend" && python main.py"

:: Wait a moment for the backend to initialize
echo Waiting for backend server to initialize...
timeout /t 3 /nobreak > nul

:: Start the frontend server
echo Starting frontend server...
start "AI Trading Sentinel Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Servers started successfully!
echo Backend running at: http://localhost:5000
echo Frontend running at: http://localhost:5176
echo.
echo Notes:
echo 1. Always ensure both frontend and backend servers are running
echo 2. The frontend proxy is configured to forward API requests to http://localhost:5000
echo 3. If you encounter connection errors, check that both servers are running
echo 4. To stop the servers, close the command prompt windows

pause