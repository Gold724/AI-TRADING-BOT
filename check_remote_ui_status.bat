@echo off
echo Checking AI Trading Sentinel Remote UI services status...

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Check the status of the services using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.override.yml ps

echo.
echo Checking container logs (last 10 lines):
echo.

echo Cloud Trading Sentinel logs:
echo -------------------------------
docker-compose -f docker-compose.yml -f docker-compose.override.yml logs --tail=10 sentinel-bot

echo.
echo Frontend logs:
echo -------------------------------
docker-compose -f docker-compose.yml -f docker-compose.override.yml logs --tail=10 frontend

echo.
echo Press any key to exit...
pause >nul