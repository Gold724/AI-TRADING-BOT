# AI Trading Sentinel Server Status Checker
# This script checks the status of both frontend and backend servers

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    return $null -ne $connections
}

# Function to test API endpoint
function Test-ApiEndpoint {
    param(
        [string]$Url
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

Write-Host "AI Trading Sentinel Server Status Check" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check backend server status
Write-Host "\nChecking Backend Server (Port 5000)..." -ForegroundColor Cyan
$backendRunning = Test-PortInUse -Port 5000

if ($backendRunning) {
    Write-Host "✓ Backend server is running on port 5000" -ForegroundColor Green
    
    # Test API health endpoint
    $healthEndpoint = "http://localhost:5000/api/health"
    $healthCheck = Test-ApiEndpoint -Url $healthEndpoint
    
    if ($healthCheck) {
        Write-Host "✓ Backend API health check passed" -ForegroundColor Green
    } else {
        Write-Host "✗ Backend API health check failed" -ForegroundColor Red
        Write-Host "  The server is running but not responding to API requests" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Backend server is NOT running on port 5000" -ForegroundColor Red
    Write-Host "  To start the backend server, run: cd .\backend; python main.py" -ForegroundColor Yellow
}

# Check frontend server status
Write-Host "\nChecking Frontend Server (Port 5176)..." -ForegroundColor Cyan
$frontendRunning = Test-PortInUse -Port 5176

if ($frontendRunning) {
    Write-Host "✓ Frontend server is running on port 5176" -ForegroundColor Green
    
    # Test frontend
    $frontendUrl = "http://localhost:5176"
    $frontendCheck = Test-ApiEndpoint -Url $frontendUrl
    
    if ($frontendCheck) {
        Write-Host "✓ Frontend is accessible" -ForegroundColor Green
    } else {
        Write-Host "✗ Frontend is not accessible" -ForegroundColor Red
        Write-Host "  The server is running but not responding to requests" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Frontend server is NOT running on port 5176" -ForegroundColor Red
    Write-Host "  To start the frontend server, run: cd .\frontend; npm run dev" -ForegroundColor Yellow
}

# Check Vite proxy configuration
Write-Host "\nChecking Vite Proxy Configuration..." -ForegroundColor Cyan
$viteConfigPath = "$PSScriptRoot\frontend\vite.config.ts"

if (Test-Path $viteConfigPath) {
    $viteConfig = Get-Content $viteConfigPath -Raw
    
    if ($viteConfig -match "target:\s*'http://localhost:5000'") {
        Write-Host "✓ Vite proxy is correctly configured to target http://localhost:5000" -ForegroundColor Green
    } else {
        Write-Host "✗ Vite proxy configuration may be incorrect" -ForegroundColor Red
        Write-Host "  Check $viteConfigPath and ensure the proxy target is set to 'http://localhost:5000'" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Could not find Vite configuration file" -ForegroundColor Red
    Write-Host "  Expected at: $viteConfigPath" -ForegroundColor Yellow
}

# Provide troubleshooting guidance
Write-Host "\nTroubleshooting Guide:" -ForegroundColor Cyan
Write-Host "1. If either server is not running, use the start-servers.ps1 script to start both servers" -ForegroundColor White
Write-Host "2. If you see 'net::ERR_ABORTED' errors in the browser console:" -ForegroundColor White
Write-Host "   - Ensure the backend server is running on port 5000" -ForegroundColor White
Write-Host "   - Check that the Vite proxy is correctly configured" -ForegroundColor White
Write-Host "3. Remember that PowerShell commands should use semicolons (;) instead of ampersands (&&)" -ForegroundColor White
Write-Host "4. If all else fails, try restarting both servers" -ForegroundColor White

Write-Host "\nTo start both servers automatically, run: .\start-servers.ps1" -ForegroundColor Green