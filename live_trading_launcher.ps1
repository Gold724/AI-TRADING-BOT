# AI Trading Sentinel - Live Trading with Auto Endpoint Validation
# ----------------------------------------------------------------
# PowerShell version for Windows environment
# Steps:
# 1. Auto-capture latest cURLs (login + trade endpoints)
# 2. Validate endpoints before trading
# 3. Run monitor mode for stability check
# 4. Switch to headless live trading if all checks pass
# 5. Auto-restart if process fails

param(
    [int]$MonitorTime = 60,  # Seconds for stability test
    [switch]$SkipValidation,  # Skip endpoint validation
    [switch]$Verbose         # Enable verbose logging
)

# Configuration
$SCRIPT = "tradebot_sentinel_advanced_pro.py"
$VALIDATOR_SCRIPT = "endpoint_validator.py"
$CURL_CAPTURE_SCRIPT = "login_bulenox_playwright.py"
$LOG_DIR = "logs"
$ERROR_LOG = "$LOG_DIR\errors\live_errors.log"

# Create log directories
if (!(Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}
if (!(Test-Path "$LOG_DIR\errors")) {
    New-Item -ItemType Directory -Path "$LOG_DIR\errors" -Force | Out-Null
}

# Enhanced logging function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $emoji = switch ($Level) {
        "INFO" { "[INFO]" }
        "SUCCESS" { "[SUCCESS]" }
        "WARNING" { "[WARNING]" }
        "ERROR" { "[ERROR]" }
        "CRITICAL" { "[CRITICAL]" }
        default { "[INFO]" }
    }
    
    $logMessage = "[$timestamp] $emoji $Message"
    Write-Host $logMessage
    
    # Also log to file
    $logMessage | Out-File -FilePath "$LOG_DIR\launcher.log" -Append -Encoding UTF8
}

# Function to check if Python script is running
function Test-ProcessRunning {
    param([int]$ProcessId)
    
    try {
        $process = Get-Process -Id $ProcessId -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Function to kill process safely
function Stop-ProcessSafely {
    param([int]$ProcessId)
    
    try {
        if (Test-ProcessRunning -ProcessId $ProcessId) {
            Stop-Process -Id $ProcessId -Force
            Start-Sleep -Seconds 2
            Write-Log "Process $ProcessId terminated" "INFO"
        }
    }
    catch {
        Write-Log "Error stopping process $ProcessId : $($_.Exception.Message)" "WARNING"
    }
}

# Function to run Python script and capture output
function Start-PythonScript {
    param(
        [string]$ScriptPath,
        [string[]]$Arguments = @(),
        [string]$OutputFile,
        [bool]$Background = $false
    )
    
    $pythonArgs = @($ScriptPath) + $Arguments
    
    if ($Background) {
        $process = Start-Process -FilePath "python" -ArgumentList $pythonArgs -RedirectStandardOutput $OutputFile -RedirectStandardError $OutputFile -PassThru -WindowStyle Hidden
        return $process.Id
    }
    else {
        $process = Start-Process -FilePath "python" -ArgumentList $pythonArgs -RedirectStandardOutput $OutputFile -RedirectStandardError $OutputFile -Wait -PassThru
        return $process.ExitCode
    }
}

# Main execution
try {
    Write-Log "=== AI Trading Sentinel Live Trading with Validation ===" "INFO"
    Write-Log "Monitor Time: $MonitorTime seconds" "INFO"
    Write-Log "Skip Validation: $SkipValidation" "INFO"
    
    # Step 1: Auto-capture cURLs
    Write-Log "[1/5] Capturing latest cURLs..." "INFO"
    $exitCode = Start-PythonScript -ScriptPath $CURL_CAPTURE_SCRIPT -Arguments @("--capture-all") -OutputFile "$LOG_DIR\curl_capture.log"
    
    if ($exitCode -ne 0) {
        Write-Log "Error during cURL capture. Check $LOG_DIR\curl_capture.log" "ERROR"
        Get-Content "$LOG_DIR\curl_capture.log" | Select-Object -Last 10 | ForEach-Object { Write-Log $_ "ERROR" }
        exit 1
    }
    Write-Log "cURL capture completed successfully" "SUCCESS"
    
    # Step 2: Validate captured endpoints (unless skipped)
    if (-not $SkipValidation) {
        Write-Log "[2/5] Validating endpoints..." "INFO"
        $exitCode = Start-PythonScript -ScriptPath $VALIDATOR_SCRIPT -OutputFile "$LOG_DIR\endpoint_validation.log"
        
        # Check validation results
        $validationOutput = Get-Content "$LOG_DIR\endpoint_validation.log" -Raw
        if ($validationOutput -notmatch "VERDICT: MISSION ACCOMPLISHED") {
            Write-Log "Endpoint validation failed. Check $LOG_DIR\endpoint_validation.log" "ERROR"
            Get-Content "$LOG_DIR\endpoint_validation.log" | Select-Object -Last 10 | ForEach-Object { Write-Log $_ "ERROR" }
            exit 1
        }
        Write-Log "Endpoint validation passed" "SUCCESS"
    }
    else {
        Write-Log "[2/5] Skipping endpoint validation (--SkipValidation flag set)" "WARNING"
    }
    
    # Step 3: Run monitor mode
    Write-Log "[3/5] Running monitor mode for $MonitorTime seconds..." "INFO"
    $monitorPid = Start-PythonScript -ScriptPath $SCRIPT -Arguments @("--monitor") -OutputFile "$LOG_DIR\monitor_output.log" -Background $true
    
    Write-Log "Monitor process started with PID: $monitorPid" "INFO"
    Start-Sleep -Seconds $MonitorTime
    
    # Step 4: Check monitor mode output
    $monitorOutput = Get-Content "$LOG_DIR\monitor_output.log" -Raw -ErrorAction SilentlyContinue
    if ($monitorOutput -match "Traceback|Exception|Error") {
        Write-Log "Error detected in monitor mode. Check $LOG_DIR\monitor_output.log" "ERROR"
        Get-Content "$LOG_DIR\monitor_output.log" | Select-Object -Last 10 | ForEach-Object { Write-Log $_ "ERROR" }
        Stop-ProcessSafely -ProcessId $monitorPid
        exit 1
    }
    
    # Kill monitor process before starting headless mode
    Stop-ProcessSafely -ProcessId $monitorPid
    Write-Log "[4/5] Monitor mode check passed. Starting headless mode..." "SUCCESS"
    
    # Step 5: Start headless live trading
    Write-Log "[5/5] Starting headless live trading..." "INFO"
    $livePid = Start-PythonScript -ScriptPath $SCRIPT -Arguments @("--headless") -OutputFile "$LOG_DIR\live_output.log" -Background $true
    
    Write-Log "Live trading process started with PID: $livePid" "SUCCESS"
    Write-Log "AI Trading Sentinel is now running in live mode!" "SUCCESS"
    Write-Log "Monitor logs: $LOG_DIR\live_output.log" "INFO"
    Write-Log "Press Ctrl+C to stop the trading bot" "INFO"
    
    # Continuous monitoring loop
    $restartCount = 0
    $maxRestarts = 5
    
    while ($true) {
        Start-Sleep -Seconds 10
        
        if (-not (Test-ProcessRunning -ProcessId $livePid)) {
            $restartCount++
            $errorMessage = "$(Get-Date): Live process crashed (Restart #$restartCount)"
            Write-Log $errorMessage "ERROR"
            $errorMessage | Out-File -FilePath $ERROR_LOG -Append -Encoding UTF8
            
            if ($restartCount -ge $maxRestarts) {
                Write-Log "Maximum restart attempts ($maxRestarts) reached. Stopping." "CRITICAL"
                break
            }
            
            Write-Log "Restarting live trading process..." "WARNING"
            
            # Wait a bit before restarting
            Start-Sleep -Seconds 5
            
            # Restart the live trading process
            $livePid = Start-PythonScript -ScriptPath $SCRIPT -Arguments @("--headless") -OutputFile "$LOG_DIR\live_output.log" -Background $true
            Write-Log "Live trading process restarted with PID: $livePid" "INFO"
        }
        
        # Optional: Check for specific error patterns in log
        if ($Verbose) {
            $recentLogs = Get-Content "$LOG_DIR\live_output.log" -Tail 5 -ErrorAction SilentlyContinue
            if ($recentLogs -match "CRITICAL|FATAL") {
                Write-Log "Critical error detected in live trading logs" "WARNING"
            }
        }
    }
}
catch {
    Write-Log "Fatal error in launcher: $($_.Exception.Message)" "CRITICAL"
    
    # Clean up any running processes
    if ($monitorPid -and (Test-ProcessRunning -ProcessId $monitorPid)) {
        Stop-ProcessSafely -ProcessId $monitorPid
    }
    if ($livePid -and (Test-ProcessRunning -ProcessId $livePid)) {
        Stop-ProcessSafely -ProcessId $livePid
    }
    
    exit 1
}
finally {
    Write-Log "AI Trading Sentinel launcher session ended" "INFO"
}