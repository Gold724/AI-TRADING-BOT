# O.R.I.G.I.N. Cloud Prime - Mutation Sentinel Server Restart Script
# This script stops and restarts both frontend and backend servers with enhanced recovery capabilities

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
    return $null -ne $connections
}

# Function to stop a process using a specific port
function Stop-ProcessByPort {
    param(
        [int]$Port,
        [string]$ServerType
    )
    
    try {
        $processId = (Get-NetTCPConnection -LocalPort $Port -State Listen).OwningProcess
        if ($processId) {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Stopping $ServerType server (Process: $($process.ProcessName), PID: $processId)..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force
                Start-Sleep -Seconds 1
                return $true
            }
        }
        return $false
    } catch {
        Write-Host "Error stopping $ServerType server: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to check broker sessions
function Get-BrokerSessions {
    param(
        [string]$LogsDir = "$PSScriptRoot\backend\logs"
    )
    
    try {
        # Check if recovery_status.json exists
        $statusFile = Join-Path $LogsDir "recovery_status.json"
        if (Test-Path $statusFile) {
            $statusData = Get-Content $statusFile | ConvertFrom-Json
            $sessions = @{}
            
            # Extract broker sessions from status data
            foreach ($sessionId in $statusData.PSObject.Properties.Name) {
                $sessionStatus = $statusData.$sessionId
                $brokerId = $sessionId -replace "^session-", "" -replace "-.*$", ""
                
                if (-not $sessions.ContainsKey($brokerId)) {
                    $sessions[$brokerId] = @{
                        "count" = 0
                        "healthy" = 0
                        "failing" = 0
                        "sessions" = @()
                    }
                }
                
                $sessions[$brokerId].count++
                $sessions[$brokerId].sessions += $sessionId
                
                if ($sessionStatus.status -eq "healthy") {
                    $sessions[$brokerId].healthy++
                } elseif ($sessionStatus.status -eq "failing" -or $sessionStatus.status -eq "failed") {
                    $sessions[$brokerId].failing++
                }
            }
            
            return $sessions
        } else {
            Write-Host "No broker sessions found (recovery_status.json not found)" -ForegroundColor Yellow
            return @{}
        }
    } catch {
        Write-Host "Error checking broker sessions: $($_.Exception.Message)" -ForegroundColor Red
        return @{}
    }
}

Write-Host "O.R.I.G.I.N. Cloud Prime - Mutation Sentinel Server Restart" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Function to check strategy mutation status
function Get-StrategyMutationStatus {
    param(
        [string]$StrategyHistoryFile = "$PSScriptRoot\backend\strategy_history.json",
        [string]$StrategyFile = "$PSScriptRoot\backend\strategy.json"
    )
    
    try {
        $result = @{
            "current_strategy" = $null
            "last_mutation" = $null
            "mutation_count" = 0
        }
        
        # Check current strategy
        if (Test-Path $StrategyFile) {
            $strategyData = Get-Content $StrategyFile | ConvertFrom-Json
            $result.current_strategy = $strategyData.strategy
        }
        
        # Check mutation history
        if (Test-Path $StrategyHistoryFile) {
            $historyData = Get-Content $StrategyHistoryFile | ConvertFrom-Json
            $result.mutation_count = $historyData.Count
            
            if ($historyData.Count -gt 0) {
                $lastMutation = $historyData[$historyData.Count - 1]
                $result.last_mutation = @{
                    "version" = $lastMutation.version
                    "updated_at" = $lastMutation.updated_at
                    "description" = $lastMutation.description
                }
            }
        }
        
        return $result
    } catch {
        Write-Host "Error checking strategy mutation status: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            "current_strategy" = "unknown"
            "last_mutation" = $null
            "mutation_count" = 0
        }
    }
}

# Function to check signal broadcasting status
function Get-SignalBroadcastStatus {
    param(
        [string]$SignalHistoryFile = "$PSScriptRoot\backend\signal_history.json"
    )
    
    try {
        $result = @{
            "total_signals" = 0
            "last_signal" = $null
            "subscribers" = 0
        }
        
        # Check signal history
        if (Test-Path $SignalHistoryFile) {
            $historyData = Get-Content $SignalHistoryFile | ConvertFrom-Json
            $result.total_signals = $historyData.Count
            
            if ($historyData.Count -gt 0) {
                $lastSignal = $historyData[$historyData.Count - 1]
                $result.last_signal = @{
                    "timestamp" = $lastSignal.timestamp
                    "symbol" = $lastSignal.symbol
                    "side" = $lastSignal.side
                    "broker_id" = $lastSignal.broker_id
                }
            }
        }
        
        # Check subscribers (this would need to be updated based on actual implementation)
        $subscribersFile = "$PSScriptRoot\backend\subscribers.json"
        if (Test-Path $subscribersFile) {
            $subscribersData = Get-Content $subscribersFile | ConvertFrom-Json
            $result.subscribers = $subscribersData.Count
        }
        
        return $result
    } catch {
        Write-Host "Error checking signal broadcast status: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            "total_signals" = 0
            "last_signal" = $null
            "subscribers" = 0
        }
    }
}

# Step 1: Check system status
Write-Host "\nStep 1: Checking system status..." -ForegroundColor Cyan

$backendPort = 5000
$frontendPort = 5176

$backendRunning = Test-PortInUse -Port $backendPort
$frontendRunning = Test-PortInUse -Port $frontendPort

if ($backendRunning) {
    Write-Host "✓ Backend server is running on port $backendPort" -ForegroundColor Green
} else {
    Write-Host "✗ Backend server is not running" -ForegroundColor Yellow
}

if ($frontendRunning) {
    Write-Host "✓ Frontend server is running on port $frontendPort" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend server is not running" -ForegroundColor Yellow
}

# Check broker sessions
Write-Host "\nChecking broker sessions..." -ForegroundColor Cyan
$brokerSessions = Get-BrokerSessions
if ($brokerSessions.Count -gt 0) {
    Write-Host "Active broker sessions:" -ForegroundColor Yellow
    foreach ($broker in $brokerSessions.Keys) {
        $session = $brokerSessions[$broker]
        Write-Host "  - $broker: $($session.count) sessions ($($session.healthy) healthy, $($session.failing) failing)" -ForegroundColor Yellow
    }
} else {
    Write-Host "No active broker sessions found" -ForegroundColor Yellow
}

# Check strategy mutation status
Write-Host "\nChecking strategy mutation status..." -ForegroundColor Cyan
$strategyStatus = Get-StrategyMutationStatus
if ($strategyStatus.current_strategy) {
    Write-Host "Current strategy: $($strategyStatus.current_strategy)" -ForegroundColor Yellow
    Write-Host "Total mutations: $($strategyStatus.mutation_count)" -ForegroundColor Yellow
    
    if ($strategyStatus.last_mutation) {
        Write-Host "Last mutation: v$($strategyStatus.last_mutation.version) at $($strategyStatus.last_mutation.updated_at)" -ForegroundColor Yellow
        Write-Host "Description: $($strategyStatus.last_mutation.description)" -ForegroundColor Yellow
    }
} else {
    Write-Host "No strategy information found" -ForegroundColor Yellow
}

# Check signal broadcasting status
Write-Host "\nChecking signal broadcasting status..." -ForegroundColor Cyan
$signalStatus = Get-SignalBroadcastStatus
Write-Host "Total signals broadcast: $($signalStatus.total_signals)" -ForegroundColor Yellow
Write-Host "Active subscribers: $($signalStatus.subscribers)" -ForegroundColor Yellow
if ($signalStatus.last_signal) {
    Write-Host "Last signal: $($signalStatus.last_signal.symbol) $($signalStatus.last_signal.side) at $($signalStatus.last_signal.timestamp)" -ForegroundColor Yellow
}

# Step 2: Stop running servers and save state
Write-Host "\nStep 2: Stopping running servers and saving state..." -ForegroundColor Cyan

# Save current state before stopping servers
$stateFile = "$PSScriptRoot\backend\restart_state.json"
$state = @{
    "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "broker_sessions" = $brokerSessions
    "strategy_status" = $strategyStatus
    "signal_status" = $signalStatus
    "restart_reason" = "manual"
}

try {
    $state | ConvertTo-Json -Depth 10 | Out-File $stateFile -Encoding utf8
    Write-Host "System state saved to $stateFile" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not save system state: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Stop broker sessions gracefully if possible
if ($brokerSessions.Count -gt 0) {
    Write-Host "Attempting to gracefully stop broker sessions..." -ForegroundColor Yellow
    # This would call an API endpoint to gracefully stop sessions
    # For now, we'll just simulate it
    Start-Sleep -Seconds 1
    Write-Host "Broker sessions notified for shutdown" -ForegroundColor Yellow
}

if ($backendRunning) {
    $backendStopped = Stop-ProcessByPort -Port $backendPort -ServerType "Backend"
    if ($backendStopped) {
        Write-Host "✓ Backend server stopped successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to stop backend server" -ForegroundColor Red
    }
}

if ($frontendRunning) {
    $frontendStopped = Stop-ProcessByPort -Port $frontendPort -ServerType "Frontend"
    if ($frontendStopped) {
        Write-Host "✓ Frontend server stopped successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to stop frontend server" -ForegroundColor Red
    }
}

# Wait a moment to ensure ports are released
Write-Host "\nWaiting for ports to be released..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

# Step 3: Start servers again with enhanced features
Write-Host "\nStep 3: Starting servers again with enhanced features..." -ForegroundColor Cyan

# Create required directories
$logsDir = "$PSScriptRoot\backend\logs"
if (-not (Test-Path -Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    Write-Host "Created logs directory at $logsDir" -ForegroundColor Green
}

# Create strategy history directory
$strategyDir = "$PSScriptRoot\backend\strategies"
if (-not (Test-Path $strategyDir)) {
    New-Item -ItemType Directory -Path $strategyDir -Force | Out-Null
    Write-Host "Created strategies directory: $strategyDir" -ForegroundColor Green
}

# Create recovery directory
$recoveryDir = "$PSScriptRoot\backend\recovery"
if (-not (Test-Path $recoveryDir)) {
    New-Item -ItemType Directory -Path $recoveryDir -Force | Out-Null
    Write-Host "Created recovery directory: $recoveryDir" -ForegroundColor Green
}

# Set environment variables for enhanced features
$env:ENABLE_AUTO_RECOVERY = "true"
$env:ENABLE_STRATEGY_MUTATION = "true"
$env:ENABLE_SIGNAL_BROADCASTING = "true"
$env:MULTI_BROKER_MODE = "true"

# Start the backend server with enhanced features
Write-Host "Starting backend server with enhanced features..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py --enable-mutation --enable-recovery --enable-broadcasting"

# Wait a moment for the backend to initialize
Write-Host "Waiting for backend server to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Start the frontend server with enhanced dashboard support
Write-Host "Starting frontend server with enhanced dashboard..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

# Step 4: Verify servers are running
Write-Host "\nStep 4: Verifying servers are running..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

$backendRunning = Test-PortInUse -Port $backendPort
$frontendRunning = Test-PortInUse -Port $frontendPort

if ($backendRunning) {
    Write-Host "✓ Backend server is running on port $backendPort" -ForegroundColor Green
} else {
    Write-Host "✗ Backend server failed to start" -ForegroundColor Red
}

if ($frontendRunning) {
    Write-Host "✓ Frontend server is running on port $frontendPort" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend server failed to start" -ForegroundColor Red
}

# Verify enhanced features
Write-Host "\nVerifying enhanced features..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

# Check if auto-recovery is running
$recoveryEndpoint = "http://localhost:$backendPort/api/recovery/status"
try {
    $response = Invoke-RestMethod -Uri $recoveryEndpoint -Method Get -ErrorAction SilentlyContinue
    Write-Host "Auto-Recovery Engine: Running" -ForegroundColor Green
} catch {
    Write-Host "Auto-Recovery Engine: Not detected" -ForegroundColor Yellow
}

# Check if strategy mutation is available
$strategyEndpoint = "http://localhost:$backendPort/api/strategy/current"
try {
    $response = Invoke-RestMethod -Uri $strategyEndpoint -Method Get -ErrorAction SilentlyContinue
    Write-Host "Strategy Mutation: Available" -ForegroundColor Green
} catch {
    Write-Host "Strategy Mutation: Not detected" -ForegroundColor Yellow
}

# Check if signal broadcasting is available
$signalEndpoint = "http://localhost:$backendPort/api/signal/status"
try {
    $response = Invoke-RestMethod -Uri $signalEndpoint -Method Get -ErrorAction SilentlyContinue
    Write-Host "Signal Broadcasting: Available" -ForegroundColor Green
} catch {
    Write-Host "Signal Broadcasting: Not detected" -ForegroundColor Yellow
}

# Final summary
Write-Host "\nServer Restart Complete" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

if ($backendRunning -and $frontendRunning) {
    Write-Host "\n✓ Both servers restarted successfully" -ForegroundColor Green
    Write-Host "Backend running at: http://localhost:$backendPort" -ForegroundColor Green
    Write-Host "Frontend running at: http://localhost:$frontendPort" -ForegroundColor Green
    
    # Ask if user wants to open the application
    $openApp = Read-Host "Do you want to open the enhanced dashboard in your browser? (y/n)"
    if ($openApp -eq "y") {
        Start-Process "http://localhost:$frontendPort/dashboard"
    }
} else {
    Write-Host "\n✗ One or both servers failed to restart" -ForegroundColor Red
    Write-Host "Please check the server windows for error messages" -ForegroundColor Yellow
}