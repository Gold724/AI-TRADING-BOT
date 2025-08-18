# AI Trading Sentinel - Live Trading with Auto Endpoint Validation
# ----------------------------------------------------------------
# Steps:
# 1. Auto-capture latest cURLs (login + trade endpoints)
# 2. Validate endpoints before trading
# 3. Run monitor mode for stability check
# 4. Switch to headless live trading if all checks pass
# 5. Auto-restart if process fails

$SCRIPT = "tradebot_sentinel_advanced_pro.py"
$VALIDATOR_SCRIPT = "endpoint_validator.py"
$CURL_CAPTURE_SCRIPT = "login_bulenox_playwright.py"
$LOG_DIR = "logs"
$ERROR_LOG = "$LOG_DIR\errors\live_errors.log"
$MONITOR_TIME = 60  # Seconds for stability test

# Create log directories
if (!(Test-Path "$LOG_DIR\errors")) {
    New-Item -ItemType Directory -Path "$LOG_DIR\errors" -Force | Out-Null
}

Write-Host "=== AI Trading Sentinel Live Trading with Validation ===" -ForegroundColor Cyan

# Step 1: Auto-capture cURLs
Write-Host "[1/5] Capturing latest cURLs..." -ForegroundColor Yellow
$captureResult = Start-Process -FilePath "python" -ArgumentList "$CURL_CAPTURE_SCRIPT", "--capture-all" -RedirectStandardOutput "$LOG_DIR\curl_capture.log" -RedirectStandardError "$LOG_DIR\curl_capture.log" -Wait -PassThru
if ($captureResult.ExitCode -ne 0) {
    Write-Host "Error during cURL capture. Check $LOG_DIR\curl_capture.log" -ForegroundColor Red
    exit 1
}

# Step 2: Validate captured endpoints
Write-Host "[2/5] Validating endpoints..." -ForegroundColor Yellow
$validationResult = Start-Process -FilePath "python" -ArgumentList "$VALIDATOR_SCRIPT" -RedirectStandardOutput "$LOG_DIR\endpoint_validation.log" -RedirectStandardError "$LOG_DIR\endpoint_validation.log" -Wait -PassThru
$validationContent = Get-Content "$LOG_DIR\endpoint_validation.log" -Raw
if ($validationContent -notmatch "VERDICT: MISSION ACCOMPLISHED") {
    Write-Host "Endpoint validation failed. Check $LOG_DIR\endpoint_validation.log" -ForegroundColor Red
    exit 1
}

# Step 3: Run monitor mode
Write-Host "[3/5] Running monitor mode for $MONITOR_TIME seconds..." -ForegroundColor Yellow
$monitorProcess = Start-Process -FilePath "python" -ArgumentList "$SCRIPT", "--monitor" -RedirectStandardOutput "$LOG_DIR\monitor_output.log" -RedirectStandardError "$LOG_DIR\monitor_output.log" -PassThru
Start-Sleep -Seconds $MONITOR_TIME

# Step 4: Check monitor mode output
$monitorContent = Get-Content "$LOG_DIR\monitor_output.log" -Raw -ErrorAction SilentlyContinue
if ($monitorContent -match "Traceback") {
    Write-Host "Error detected in monitor mode. Check $LOG_DIR\monitor_output.log" -ForegroundColor Red
    Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Kill monitor process before starting headless mode
Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "[4/5] Monitor mode check passed. Starting headless mode..." -ForegroundColor Green

# Step 5: Start headless live trading
$liveProcess = Start-Process -FilePath "python" -ArgumentList "$SCRIPT", "--headless" -RedirectStandardOutput "$LOG_DIR\live_output.log" -RedirectStandardError "$LOG_DIR\live_output.log" -PassThru

Write-Host "[5/5] Live trading started. Monitoring for crashes..." -ForegroundColor Green

# Continuous monitoring loop
while ($true) {
    if ($liveProcess.HasExited) {
        Write-Host "Live trading process stopped unexpectedly. Restarting from Step 1..." -ForegroundColor Red
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content -Path "$ERROR_LOG" -Value "$timestamp: Live process crashed"
        
        # Restart entire script
        & $PSCommandPath
        exit
    }
    Start-Sleep -Seconds 10
}