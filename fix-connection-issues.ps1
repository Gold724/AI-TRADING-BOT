# AI Trading Sentinel Connection Issue Fixer
# This script attempts to fix common connection issues between frontend and backend

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    return $null -ne $connections
}

# Function to check if a process is running
function Test-ProcessRunning {
    param(
        [string]$ProcessName
    )
    
    $process = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    return $null -ne $process
}

# Function to kill a process by port
function Stop-ProcessByPort {
    param(
        [int]$Port
    )
    
    $processId = (Get-NetTCPConnection -LocalPort $Port -State Listen).OwningProcess
    if ($processId) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Stopping process $($process.ProcessName) (PID: $processId) using port $Port" -ForegroundColor Yellow
            Stop-Process -Id $processId -Force
            Start-Sleep -Seconds 1
            return $true
        }
    }
    return $false
}

# Function to verify Vite config
function Verify-ViteConfig {
    $viteConfigPath = "$PSScriptRoot\frontend\vite.config.ts"
    
    if (Test-Path $viteConfigPath) {
        $viteConfig = Get-Content $viteConfigPath -Raw
        
        if ($viteConfig -match "target:\s*'http://localhost:5000'") {
            Write-Host "✓ Vite proxy configuration is correct" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ Vite proxy configuration is incorrect" -ForegroundColor Red
            
            # Ask user if they want to fix it
            $fixConfig = Read-Host "Do you want to fix the Vite configuration? (y/n)"
            if ($fixConfig -eq "y") {
                # Create a backup
                Copy-Item $viteConfigPath "$viteConfigPath.backup"
                
                # Replace with correct configuration
                $correctConfig = @"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
"@
                Set-Content -Path $viteConfigPath -Value $correctConfig
                Write-Host "✓ Vite configuration has been fixed" -ForegroundColor Green
                Write-Host "  A backup was created at $viteConfigPath.backup" -ForegroundColor Cyan
                return $true
            }
            return $false
        }
    } else {
        Write-Host "✗ Could not find Vite configuration file at $viteConfigPath" -ForegroundColor Red
        return $false
    }
}

Write-Host "AI Trading Sentinel Connection Issue Fixer" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Step 1: Check if ports are in use by other applications
Write-Host "\nStep 1: Checking if required ports are available..." -ForegroundColor Cyan

$backendPortInUse = Test-PortInUse -Port 5000
$frontendPortInUse = Test-PortInUse -Port 5176

if ($backendPortInUse) {
    Write-Host "Port 5000 (backend) is in use" -ForegroundColor Yellow
    $releasePort = Read-Host "Do you want to release port 5000? (y/n)"
    if ($releasePort -eq "y") {
        $released = Stop-ProcessByPort -Port 5000
        if ($released) {
            Write-Host "✓ Port 5000 has been released" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to release port 5000" -ForegroundColor Red
        }
    }
} else {
    Write-Host "✓ Port 5000 (backend) is available" -ForegroundColor Green
}

if ($frontendPortInUse) {
    Write-Host "Port 5176 (frontend) is in use" -ForegroundColor Yellow
    $releasePort = Read-Host "Do you want to release port 5176? (y/n)"
    if ($releasePort -eq "y") {
        $released = Stop-ProcessByPort -Port 5176
        if ($released) {
            Write-Host "✓ Port 5176 has been released" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to release port 5176" -ForegroundColor Red
        }
    }
} else {
    Write-Host "✓ Port 5176 (frontend) is available" -ForegroundColor Green
}

# Step 2: Verify Vite configuration
Write-Host "\nStep 2: Verifying Vite proxy configuration..." -ForegroundColor Cyan
Verify-ViteConfig

# Step 3: Check if backend server is running
Write-Host "\nStep 3: Checking if backend server is running..." -ForegroundColor Cyan
$backendRunning = Test-PortInUse -Port 5000

if (-not $backendRunning) {
    Write-Host "✗ Backend server is not running" -ForegroundColor Red
    $startBackend = Read-Host "Do you want to start the backend server? (y/n)"
    if ($startBackend -eq "y") {
        Write-Host "Starting backend server..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py"
        Write-Host "✓ Backend server started in a new window" -ForegroundColor Green
    }
} else {
    Write-Host "✓ Backend server is running on port 5000" -ForegroundColor Green
}

# Step 4: Check if frontend server is running
Write-Host "\nStep 4: Checking if frontend server is running..." -ForegroundColor Cyan
$frontendRunning = Test-PortInUse -Port 5176

if (-not $frontendRunning) {
    Write-Host "✗ Frontend server is not running" -ForegroundColor Red
    $startFrontend = Read-Host "Do you want to start the frontend server? (y/n)"
    if ($startFrontend -eq "y") {
        Write-Host "Starting frontend server..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"
        Write-Host "✓ Frontend server started in a new window" -ForegroundColor Green
    }
} else {
    Write-Host "✓ Frontend server is running on port 5176" -ForegroundColor Green
}

# Final summary
Write-Host "\nConnection Issue Fixing Complete" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host "\nNext Steps:" -ForegroundColor White
Write-Host "1. Open your browser and navigate to http://localhost:5176" -ForegroundColor White
Write-Host "2. If you still see connection errors, try refreshing the page" -ForegroundColor White
Write-Host "3. If issues persist, restart both servers using .\start-servers.ps1" -ForegroundColor White
Write-Host "\nRemember: Both frontend and backend servers must be running for the application to work correctly." -ForegroundColor Yellow