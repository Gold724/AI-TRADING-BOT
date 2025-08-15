# PowerShell script for checking AI Trading Sentinel Remote UI services status

Write-Host "Checking AI Trading Sentinel Remote UI services status..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check the status of the services using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.override.yml ps

Write-Host ""
Write-Host "Checking container logs (last 10 lines):" -ForegroundColor Cyan
Write-Host ""

Write-Host "Sentinel Bot logs:" -ForegroundColor Yellow
Write-Host "-------------------------------"
docker-compose -f docker-compose.yml -f docker-compose.override.yml logs --tail=10 sentinel-bot

Write-Host ""
Write-Host "Frontend logs:" -ForegroundColor Yellow
Write-Host "-------------------------------"
docker-compose -f docker-compose.yml -f docker-compose.override.yml logs --tail=10 frontend