# PowerShell script for stopping AI Trading Sentinel Remote UI services

Write-Host "Stopping AI Trading Sentinel Remote UI services..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Stop the services using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.override.yml down

Write-Host ""
Write-Host "Remote UI services stopped successfully!" -ForegroundColor Green