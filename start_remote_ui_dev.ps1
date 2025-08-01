# PowerShell script for starting AI Trading Sentinel Remote UI in development mode

Write-Host "Starting AI Trading Sentinel Remote UI in development mode..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Start the services using docker-compose with the override file
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

Write-Host ""
Write-Host "Remote UI started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to view logs (Ctrl+C to exit logs)..." -ForegroundColor Cyan
Read-Host | Out-Null

docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f