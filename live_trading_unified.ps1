# ========================================================
# AI Trading Sentinel - Unified Live Trading Launcher (Windows)
# Enhanced Version with Session Management
# Features:
# 1. Pulls latest code from GitHub before starting
# 2. Runs monitor mode for stability check
# 3. Switches to headless mode if no errors
# 4. Watches GitHub for updates and auto-restarts
# 5. Logs all crashes, updates, and outputs
# 6. Session recovery and browser management
# 7. Network connectivity monitoring
# 8. Emergency stop and restart capabilities
# ========================================================

$SCRIPT = "tradebot_sentinel.py"
$LOG_DIR = "logs"
$ERROR_LOG = "$LOG_DIR\errors\live_errors.log"
$UPDATE_LOG = "$LOG_DIR\updates\update.log"
$SESSION_LOG = "$LOG_DIR\session\session.log"
$MONITOR_TIME = 60 # Seconds in monitor mode
$GIT_REPO_DIR = "C:\Users\Admin\Downloads\ai-trading-sentinel" # Current directory
$MAX_RETRIES = 3
$RETRY_DELAY = 30

# Create necessary directories
New-Item -ItemType Directory -Force -Path "$LOG_DIR\errors", "$LOG_DIR\updates", "$LOG_DIR\session", "$LOG_DIR\screenshots" | Out-Null

Write-Host "=== Starting AI Trading Sentinel Unified Launcher ==="
Add-Content -Path $SESSION_LOG -Value "$(Get-Date): Launcher started"

# Function to check network connectivity
function Test-NetworkConnectivity {
    try {
        $result = Test-NetConnection -ComputerName "bulenox.projectx.com" -Port 443 -InformationLevel Quiet
        return $result
    } catch {
        Add-Content -Path $ERROR_LOG -Value "$(Get-Date): Network connectivity issue detected"
        return $false
    }
}

# Function to kill any existing browser processes
function Stop-BrowserProcesses {
    Add-Content -Path $SESSION_LOG -Value "$(Get-Date): Cleaning up existing browser processes"
    Get-Process -Name "chrome", "msedge", "firefox" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*playwright*" } | Stop-Process -Force
    Start-Sleep -Seconds 5
}

# Function to check if bot is responsive
function Test-BotHealth {
    param($ProcessId)
    
    try {
        $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($process) {
            # Check if bot is actually trading (look for recent activity)
            $recentLogs = Get-ChildItem -Path $LOG_DIR -Filter "*.log" -Recurse | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-5) }
            return $recentLogs.Count -gt 0
        }
    } catch {
        return $false
    }
    return $false
}

# Step 0: Initial setup and cleanup
Write-Host "[0/5] Initial setup and cleanup..."
Stop-BrowserProcesses

# Check network connectivity
if (-not (Test-NetworkConnectivity)) {
    Write-Host "Network connectivity issue. Waiting 30 seconds..."
    Start-Sleep -Seconds 30
    if (-not (Test-NetworkConnectivity)) {
        Write-Host "Network still unavailable. Exiting."
        exit 1
    }
}

# Step 1: Pull latest code from GitHub
Write-Host "[1/5] Pulling latest code from GitHub..."
Set-Location $GIT_REPO_DIR
git reset --hard
git pull origin main *>> $UPDATE_LOG
Add-Content -Path $UPDATE_LOG -Value "$(Get-Date): Initial pull complete."

# Step 2: Run Monitor Mode with retry logic
Write-Host "[2/5] Running monitor mode for $MONITOR_TIME seconds..."
$retryCount = 0
while ($retryCount -lt $MAX_RETRIES) {
    Stop-BrowserProcesses
    
    # Set environment variables
    $env:BULENOX_USERNAME = "BX64883"
    $env:BULENOX_PASSWORD = "XujhMzFf6K"
    
    $monitorProcess = Start-Process -FilePath "python" -ArgumentList $SCRIPT, "--monitor" -RedirectStandardOutput "$LOG_DIR\monitor_output.log" -RedirectStandardError "$LOG_DIR\monitor_error.log" -PassThru -NoNewWindow
    
    Start-Sleep -Seconds $MONITOR_TIME
    
    $monitorOutput = Get-Content "$LOG_DIR\monitor_output.log" -ErrorAction SilentlyContinue
    $monitorError = Get-Content "$LOG_DIR\monitor_error.log" -ErrorAction SilentlyContinue
    
    if (($monitorOutput -match "Traceback|Error|Failed") -or ($monitorError -match "Traceback|Error|Failed")) {
        Add-Content -Path $ERROR_LOG -Value "$(Get-Date): Error in monitor mode (attempt $($retryCount + 1)). Retrying..."
        Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
        $retryCount++
        Start-Sleep -Seconds $RETRY_DELAY
    } else {
        Add-Content -Path $SESSION_LOG -Value "$(Get-Date): Monitor mode passed successfully"
        Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
        break
    }
}

if ($retryCount -eq $MAX_RETRIES) {
    Write-Host "Monitor mode failed after $MAX_RETRIES attempts. Exiting."
    exit 1
}

Write-Host "[3/5] Monitor mode passed. Starting headless mode..."

# Step 3: Start Headless Mode with session management
function Start-HeadlessMode {
    Stop-BrowserProcesses
    Add-Content -Path $SESSION_LOG -Value "$(Get-Date): Starting headless trading mode"
    
    # Set environment variables for session persistence
    $env:BULENOX_USERNAME = "BX64883"
    $env:BULENOX_PASSWORD = "XujhMzFf6K"
    $env:HEADLESS_MODE = "true"
    $env:SESSION_RECOVERY = "true"
    
    $liveProcess = Start-Process -FilePath "python" -ArgumentList $SCRIPT, "--headless" -RedirectStandardOutput "$LOG_DIR\live_output.log" -RedirectStandardError "$LOG_DIR\live_error.log" -PassThru -NoNewWindow
    return $liveProcess
}

$liveProcess = Start-HeadlessMode

# Step 4: GitHub Watcher (Background Job)
Write-Host "[4/5] Starting GitHub watcher..."
$gitWatcherJob = Start-Job -ScriptBlock {
    param($GIT_REPO_DIR, $UPDATE_LOG, $ERROR_LOG, $SESSION_LOG, $SCRIPT, $LOG_DIR)
    
    Set-Location $GIT_REPO_DIR
    $lastHash = git rev-parse HEAD
    
    while ($true) {
        git fetch origin main 2>$null
        $newHash = git rev-parse origin/main 2>$null
        
        if (($lastHash -ne $newHash) -and ($newHash)) {
            Add-Content -Path $UPDATE_LOG -Value "$(Get-Date): Update detected. Pulling changes..."
            git reset --hard
            git pull origin main *>> $UPDATE_LOG
            Add-Content -Path $UPDATE_LOG -Value "$(Get-Date): Restarting bot due to update..."
            
            # Signal main process to restart (create restart flag file)
            New-Item -Path "restart_flag.txt" -ItemType File -Force | Out-Null
            
            $lastHash = $newHash
        }
        Start-Sleep -Seconds 30
    }
} -ArgumentList $GIT_REPO_DIR, $UPDATE_LOG, $ERROR_LOG, $SESSION_LOG, $SCRIPT, $LOG_DIR

# Step 5: Enhanced Live Process Monitor with Health Checks
Write-Host "[5/5] Starting enhanced process monitor..."
$healthCheckFailures = 0
$maxHealthFailures = 3

while ($true) {
    # Check for restart flag from git watcher
    if (Test-Path "restart_flag.txt") {
        Remove-Item "restart_flag.txt" -Force
        Add-Content -Path $UPDATE_LOG -Value "$(Get-Date): Restart requested by git watcher"
        
        Stop-Process -Id $liveProcess.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 10
        Stop-BrowserProcesses
        
        # Test in monitor mode first
        $env:BULENOX_USERNAME = "BX64883"
        $env:BULENOX_PASSWORD = "XujhMzFf6K"
        $monitorProcess = Start-Process -FilePath "python" -ArgumentList $SCRIPT, "--monitor" -RedirectStandardOutput "$LOG_DIR\monitor_update.log" -RedirectStandardError "$LOG_DIR\monitor_update_error.log" -PassThru -NoNewWindow
        Start-Sleep -Seconds 60
        
        $monitorOutput = Get-Content "$LOG_DIR\monitor_update.log" -ErrorAction SilentlyContinue
        $monitorError = Get-Content "$LOG_DIR\monitor_update_error.log" -ErrorAction SilentlyContinue
        
        if (-not (($monitorOutput -match "Traceback|Error|Failed") -or ($monitorError -match "Traceback|Error|Failed"))) {
            Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
            $liveProcess = Start-HeadlessMode
            Add-Content -Path $UPDATE_LOG -Value "$(Get-Date): Bot restarted successfully after update"
        } else {
            Add-Content -Path $ERROR_LOG -Value "$(Get-Date): Update caused errors, reverting..."
            git reset --hard HEAD~1
            $liveProcess = Start-HeadlessMode
        }
    }
    
    if (-not (Test-BotHealth -ProcessId $liveProcess.Id)) {
        $healthCheckFailures++
        Add-Content -Path $ERROR_LOG -Value "$(Get-Date): Health check failed ($healthCheckFailures/$maxHealthFailures)"
        
        if ($healthCheckFailures -ge $maxHealthFailures) {
            Add-Content -Path $ERROR_LOG -Value "$(Get-Date): Bot health critical. Performing full restart..."
            
            # Kill current process
            Stop-Process -Id $liveProcess.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
            Stop-BrowserProcesses
            
            # Check network before restart
            if (Test-NetworkConnectivity) {
                # Full recovery cycle
                $env:BULENOX_USERNAME = "BX64883"
                $env:BULENOX_PASSWORD = "XujhMzFf6K"
                $monitorProcess = Start-Process -FilePath "python" -ArgumentList $SCRIPT, "--monitor" -RedirectStandardOutput "$LOG_DIR\monitor_recovery.log" -RedirectStandardError "$LOG_DIR\monitor_recovery_error.log" -PassThru -NoNewWindow
                Start-Sleep -Seconds 60
                
                $monitorOutput = Get-Content "$LOG_DIR\monitor_recovery.log" -ErrorAction SilentlyContinue
                $monitorError = Get-Content "$LOG_DIR\monitor_recovery_error.log" -ErrorAction SilentlyContinue
                
                if (-not (($monitorOutput -match "Traceback|Error|Failed") -or ($monitorError -match "Traceback|Error|Failed"))) {
                    Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
                    $liveProcess = Start-HeadlessMode
                    $healthCheckFailures = 0
                    Add-Content -Path $SESSION_LOG -Value "$(Get-Date): Full recovery completed successfully"
                } else {
                    Add-Content -Path $ERROR_LOG -Value "$(Get-Date): Recovery failed, waiting before retry"
                    Start-Sleep -Seconds 300 # Wait 5 minutes before next attempt
                }
            } else {
                Add-Content -Path $ERROR_LOG -Value "$(Get-Date): Network unavailable, waiting for connectivity"
                Start-Sleep -Seconds 60
            }
        }
    } else {
        $healthCheckFailures = 0
    }
    
    Start-Sleep -Seconds 30
}

# Cleanup on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-Process -Id $liveProcess.Id -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $gitWatcherJob -Force -ErrorAction SilentlyContinue
    Stop-BrowserProcesses
    Add-Content -Path $SESSION_LOG -Value "$(Get-Date): Launcher stopped"
}