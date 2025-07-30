# AI Trading Sentinel API Endpoint Tester
# This script tests the API endpoints to ensure they are working correctly

param(
    [switch]$Verbose,
    [string]$LogFile = "logs/api_test_results.log",
    [switch]$ShowResponseContent
)

# Function to test an API endpoint
function Test-ApiEndpoint {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [string]$Description = "",
        [switch]$Verbose,
        [string]$LogFile = "logs/api_test_results.log"
    )
    
    Write-Host "Testing $Description ($Url)..." -ForegroundColor Cyan
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] Testing $Description ($Url) - "
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method $Method -TimeoutSec 5 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Success (Status: $($response.StatusCode))" -ForegroundColor Green
            
            # Show response content summary if verbose
            if ($Verbose) {
                try {
                    $content = $response.Content | ConvertFrom-Json
                    Write-Host "  Response:" -ForegroundColor Gray
                    $contentSummary = $content | ConvertTo-Json -Depth 1 -Compress
                    Write-Host "  $contentSummary" -ForegroundColor Gray
                } catch {
                    # If not JSON, show first 100 characters
                    $contentPreview = $response.Content.Substring(0, [Math]::Min(100, $response.Content.Length))
                    Write-Host "  Response (first 100 chars): $contentPreview..." -ForegroundColor Gray
                }
            }
            
            $logEntry += "SUCCESS (Status: $($response.StatusCode))"
            Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
            return $true
        } else {
            Write-Host "✗ Failed (Status: $($response.StatusCode))" -ForegroundColor Red
            $logEntry += "FAILED (Status: $($response.StatusCode))"
            Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
            return $false
        }
    } catch {
        Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
        $logEntry += "ERROR: $($_.Exception.Message)"
        Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
        return $false
    }
}

# Create logs directory if it doesn't exist
$logsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Yellow
}

# Set full path for log file
$LogFile = Join-Path $PSScriptRoot $LogFile

# Add timestamp to log file
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "\n[$timestamp] ===== API ENDPOINT TEST RUN STARTED =====" -ErrorAction SilentlyContinue

Write-Host "AI Trading Sentinel API Endpoint Tester" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Verbose mode: $($Verbose -or $ShowResponseContent)" -ForegroundColor Yellow
Write-Host "Log file: $LogFile" -ForegroundColor Yellow

# Check if backend server is running
try {
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 5000 }
    $backendRunning = $null -ne $connections
} catch {
    $backendRunning = $false
}

if (-not $backendRunning) {
    Write-Host "\n✗ Backend server is not running on port 5000" -ForegroundColor Red
    $startBackend = Read-Host "Do you want to start the backend server? (y/n)"
    
    if ($startBackend -eq "y") {
        Write-Host "Starting backend server..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py"
        
        # Wait for server to start
        Write-Host "Waiting for backend server to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    } else {
        Write-Host "Backend server must be running to test API endpoints." -ForegroundColor Yellow
        exit
    }
}

# Define the API endpoints to test
$endpoints = @(
    # Core API endpoints
    @{Url = "http://localhost:5000/api/health"; Description = "Health Check"},
    @{Url = "http://localhost:5000/api/logs?type=main"; Description = "Logs"},
    
    # Strategy API endpoints
    @{Url = "http://localhost:5000/api/strategy"; Description = "Current Strategy"},
    @{Url = "http://localhost:5000/api/strategy/history"; Description = "Strategy History"},
    @{Url = "http://localhost:5000/api/strategy/available"; Description = "Available Strategies"},
    
    # Trading API endpoints
    @{Url = "http://localhost:5000/api/signal"; Description = "Trading Signal"},
    @{Url = "http://localhost:5000/api/trade/history"; Description = "Trade History"},
    @{Url = "http://localhost:5000/api/brokers"; Description = "Broker Configuration"},
    @{Url = "http://localhost:5000/api/account/symbol-status"; Description = "Symbol Status"},
    
    # Progress tracking endpoints
    @{Url = "http://localhost:5000/api/progress/summary"; Description = "Progress Summary"},
    @{Url = "http://localhost:5000/api/daily-plan"; Description = "Daily Trading Plan"},
    @{Url = "http://localhost:5000/api/per-trade-targets?daily_target=100"; Description = "Per-Trade Targets"},
    @{Url = "http://localhost:5000/api/mode"; Description = "Trading Mode"},
    
    # Dashboard API endpoints
    @{Url = "http://localhost:5000/api/dashboard/status"; Description = "Dashboard Status"},
    @{Url = "http://localhost:5000/api/dashboard/trading"; Description = "Dashboard Trading Metrics"},
    @{Url = "http://localhost:5000/api/dashboard/brokers"; Description = "Dashboard Broker Status"},
    @{Url = "http://localhost:5000/api/dashboard/strategies"; Description = "Dashboard Strategy Info"},
    @{Url = "http://localhost:5000/api/dashboard/signals"; Description = "Dashboard Signal Metrics"},
    @{Url = "http://localhost:5000/api/dashboard/health"; Description = "Dashboard Health Status"},
    @{Url = "http://localhost:5000/api/dashboard/lunar"; Description = "Lunar Phase Information"}
)

# Test each endpoint
Write-Host "\nTesting API Endpoints..." -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

$successCount = 0
$failCount = 0
$results = @()

# Group endpoints by category for reporting
$categories = @{
    "Core" = @("Health Check", "Logs")
    "Strategy" = @("Current Strategy", "Strategy History", "Available Strategies")
    "Trading" = @("Trading Signal", "Trade History", "Broker Configuration", "Symbol Status")
    "Progress" = @("Progress Summary", "Daily Trading Plan", "Per-Trade Targets", "Trading Mode")
    "Dashboard" = @("Dashboard Status", "Dashboard Trading Metrics", "Dashboard Broker Status", 
                   "Dashboard Strategy Info", "Dashboard Signal Metrics", "Dashboard Health Status", 
                   "Lunar Phase Information")
}

foreach ($endpoint in $endpoints) {
    Write-Host ""
    $verboseFlag = $Verbose -or ($ShowResponseContent -and $endpoint.Description -match "Dashboard|Strategy|Signal")
    $success = Test-ApiEndpoint -Url $endpoint.Url -Description $endpoint.Description -Verbose:$verboseFlag -LogFile $LogFile
    
    # Store result for summary
    $category = "Other"
    foreach ($cat in $categories.Keys) {
        if ($categories[$cat] -contains $endpoint.Description) {
            $category = $cat
            break
        }
    }
    
    $results += [PSCustomObject]@{
        Category = $category
        Description = $endpoint.Description
        Url = $endpoint.Url
        Success = $success
    }
    
    if ($success) {
        $successCount++
    } else {
        $failCount++
    }
}

# Summary
Write-Host "\nAPI Endpoint Test Summary" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan
Write-Host "Total endpoints tested: $($endpoints.Count)" -ForegroundColor White
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "White" })

# Add timestamp to log file for summary
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] TEST SUMMARY: $successCount successful, $failCount failed out of $($endpoints.Count) total endpoints" -ErrorAction SilentlyContinue

# Display results by category
Write-Host "\nResults by Category:" -ForegroundColor Cyan
foreach ($category in $categories.Keys | Sort-Object) {
    $categoryResults = $results | Where-Object { $_.Category -eq $category }
    $categorySuccessCount = ($categoryResults | Where-Object { $_.Success -eq $true }).Count
    $categoryTotalCount = $categoryResults.Count
    
    $statusColor = if ($categorySuccessCount -eq $categoryTotalCount) { "Green" } elseif ($categorySuccessCount -eq 0) { "Red" } else { "Yellow" }
    Write-Host "$category APIs: $categorySuccessCount/$categoryTotalCount" -ForegroundColor $statusColor
    
    # Log category results
    Add-Content -Path $LogFile -Value "[$timestamp] CATEGORY: $category - $categorySuccessCount/$categoryTotalCount successful" -ErrorAction SilentlyContinue
    
    # Show failed endpoints in this category
    $failedInCategory = $categoryResults | Where-Object { $_.Success -eq $false }
    if ($failedInCategory.Count -gt 0) {
        foreach ($failed in $failedInCategory) {
            Write-Host "  ✗ $($failed.Description) ($($failed.Url))" -ForegroundColor Red
        }
    }
}

# Provide guidance based on results
if ($failCount -gt 0) {
    Write-Host "\nTroubleshooting Tips:" -ForegroundColor Yellow
    
    # Core API failures
    if (($results | Where-Object { $_.Category -eq "Core" -and $_.Success -eq $false }).Count -gt 0) {
        Write-Host "Core API Issues:" -ForegroundColor White
        Write-Host "1. Ensure the backend server is running on port 5000" -ForegroundColor White
        Write-Host "2. Check backend/logs/server.log for errors" -ForegroundColor White
    }
    
    # Strategy API failures
    if (($results | Where-Object { $_.Category -eq "Strategy" -and $_.Success -eq $false }).Count -gt 0) {
        Write-Host "\nStrategy API Issues:" -ForegroundColor White
        Write-Host "1. Verify strategy files exist in the /strategies directory" -ForegroundColor White
        Write-Host "2. Check if strategy_history.json is accessible and valid" -ForegroundColor White
    }
    
    # Trading API failures
    if (($results | Where-Object { $_.Category -eq "Trading" -and $_.Success -eq $false }).Count -gt 0) {
        Write-Host "\nTrading API Issues:" -ForegroundColor White
        Write-Host "1. Check broker configurations in brokers.json" -ForegroundColor White
        Write-Host "2. Verify trade history file exists and is valid" -ForegroundColor White
    }
    
    # Dashboard API failures
    if (($results | Where-Object { $_.Category -eq "Dashboard" -and $_.Success -eq $false }).Count -gt 0) {
        Write-Host "\nDashboard API Issues:" -ForegroundColor White
        Write-Host "1. Verify dashboard_data.json exists and is valid" -ForegroundColor White
        Write-Host "2. Check permissions on dashboard data files" -ForegroundColor White
    }
    
    Write-Host "\nGeneral Troubleshooting:" -ForegroundColor White
    Write-Host "1. Run .\restart-servers.ps1 to restart both frontend and backend servers" -ForegroundColor White
    Write-Host "2. Check for Python dependency issues with 'pip list'" -ForegroundColor White
    Write-Host "3. Verify network connectivity and firewall settings" -ForegroundColor White
} else {
    Write-Host "\n✓ All API endpoints are working correctly" -ForegroundColor Green
    
    # Check if frontend server is running
    try {
        $frontendConnections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 5176 }
        $frontendRunning = $null -ne $frontendConnections
    } catch {
        $frontendRunning = $false
    }
    
    if (-not $frontendRunning) {
        Write-Host "Frontend server is not running on port 5176" -ForegroundColor Yellow
        Write-Host "Would you like to start the frontend server? (y/n)" -ForegroundColor Yellow
        $startFrontend = Read-Host
        
        if ($startFrontend -eq "y") {
            Write-Host "Starting frontend server..." -ForegroundColor Yellow
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"
            
            # Wait for server to start
            Write-Host "Waiting for frontend server to start..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
            
            # Open browser
            Write-Host "Opening application in browser..." -ForegroundColor Yellow
            Start-Process "http://localhost:5176"
        } else {
            Write-Host "You can now start the frontend server manually when ready" -ForegroundColor White
        }
    } else {
        Write-Host "Frontend server is already running on port 5176" -ForegroundColor Green
        Write-Host "Would you like to open the application in your browser? (y/n)" -ForegroundColor Yellow
        $openBrowser = Read-Host
        
        if ($openBrowser -eq "y") {
            Write-Host "Opening application in browser..." -ForegroundColor Yellow
            Start-Process "http://localhost:5176"
        }
    }
}

# Add final log entry
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] ===== API ENDPOINT TEST RUN COMPLETED =====" -ErrorAction SilentlyContinue

Write-Host "\nTest results saved to: $LogFile" -ForegroundColor Cyan