# AI Trading Sentinel Startup Script
# This script starts both the frontend and backend servers

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    return $null -ne $connections
}

# Create logs directory if it doesn't exist
$logsDir = "$PSScriptRoot\backend\logs"
if (-not (Test-Path -Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "Created logs directory at $logsDir"
}

# Check if backend port is already in use
if (Test-PortInUse -Port 5000) {
    Write-Host "Warning: Port 5000 is already in use. Backend server may not start properly." -ForegroundColor Yellow
}

# Check if frontend port is already in use
if (Test-PortInUse -Port 5176) {
    Write-Host "Warning: Port 5176 is already in use. Frontend server may not start properly." -ForegroundColor Yellow
}

# Start the backend server
Write-Host "Starting backend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py"

# Wait a moment for the backend to initialize
Write-Host "Waiting for backend server to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Start the frontend server
Write-Host "Starting frontend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host "
Servers started successfully!" -ForegroundColor Green
Write-Host "Backend running at: http://localhost:5000" -ForegroundColor Green
Write-Host "Frontend running at: http://localhost:5176" -ForegroundColor Green
Write-Host "
Notes:" -ForegroundColor Yellow
Write-Host "1. Always ensure both frontend and backend servers are running" -ForegroundColor Yellow
Write-Host "2. The frontend proxy is configured to forward API requests to http://localhost:5000" -ForegroundColor Yellow
Write-Host "3. If you encounter connection errors, check that both servers are running" -ForegroundColor Yellow
Write-Host "4. To stop the servers, close the PowerShell windows or press Ctrl+C in each window" -ForegroundColor Yellow