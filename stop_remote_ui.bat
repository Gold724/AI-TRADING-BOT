@echo off
echo Stopping AI Trading Sentinel Remote UI services...

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Stop the services using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.override.yml down

echo.
echo Remote UI services stopped successfully!