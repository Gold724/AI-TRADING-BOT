@echo off
echo Starting AI Trading Sentinel Remote UI in development mode...

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Start the services using docker-compose with the override file
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

echo.
echo Remote UI started successfully!
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:5000
echo.
echo Press any key to view logs (Ctrl+C to exit logs)...
pause >nul

docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f