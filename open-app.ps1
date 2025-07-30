# AI Trading Sentinel App Launcher
# This script checks if servers are running and opens the app in the browser

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    return $null -ne $connections
}

Write-Host "AI Trading Sentinel App Launcher" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Check if servers are running
$backendRunning = Test-PortInUse -Port 5000
$frontendRunning = Test-PortInUse -Port 5176

$allRunning = $true

if (-not $backendRunning) {
    Write-Host "✗ Backend server is not running" -ForegroundColor Red
    $allRunning = $false
} else {
    Write-Host "✓ Backend server is running" -ForegroundColor Green
}

if (-not $frontendRunning) {
    Write-Host "✗ Frontend server is not running" -ForegroundColor Red
    $allRunning = $false
} else {
    Write-Host "✓ Frontend server is running" -ForegroundColor Green
}

# If servers aren't running, ask to start them
if (-not $allRunning) {
    Write-Host "\nOne or both servers are not running." -ForegroundColor Yellow
    $startServers = Read-Host "Do you want to start the servers now? (y/n)"
    
    if ($startServers -eq "y") {
        # Start the servers using the start-servers script
        Write-Host "Starting servers..." -ForegroundColor Cyan
        & "$PSScriptRoot\start-servers.ps1"
        
        # Wait for servers to initialize
        Write-Host "Waiting for servers to initialize..." -ForegroundColor Cyan
        Start-Sleep -Seconds 5
    } else {
        Write-Host "Servers must be running to open the application." -ForegroundColor Yellow
        exit
    }
}

# Open the application in the default browser
Write-Host "\nOpening AI Trading Sentinel in your browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5176"

Write-Host "\nApplication launched successfully!" -ForegroundColor Green
Write-Host "If you encounter any issues:" -ForegroundColor Yellow
Write-Host "1. Check that both servers are running" -ForegroundColor Yellow
Write-Host "2. Run .\check-server-status.ps1 to diagnose problems" -ForegroundColor Yellow
Write-Host "3. Run .\fix-connection-issues.ps1 to fix common issues" -ForegroundColor Yellow