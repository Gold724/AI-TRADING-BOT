# TradeBot Sentinel - PowerShell Execution Script
# This script sets up environment variables and runs the TradeBot Sentinel

Write-Host "===== TradeBot Sentinel - PowerShell Launcher =====" -ForegroundColor Cyan
Write-Host ""

# Set Bulenox credentials
$env:BULENOX_USERNAME = "BX64883"
$env:BULENOX_PASSWORD = "XujhMzFf6K"

Write-Host "Credentials configured:" -ForegroundColor Green
Write-Host "- Username: $env:BULENOX_USERNAME"
Write-Host "- Password: [HIDDEN]"
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if the main script exists
if (-not (Test-Path "login_bulenox_playwright.py")) {
    Write-Host "ERROR: login_bulenox_playwright.py not found" -ForegroundColor Red
    Write-Host "Please ensure you're running this from the correct directory" -ForegroundColor Yellow
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Parse command line arguments
param(
    [switch]$Visible,
    [switch]$Help
)

if ($Help) {
    Write-Host ""
    Write-Host "Usage: .\run_tradebot.ps1 [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Visible     Run with visible browser (for debugging)"
    Write-Host "  -Help        Show this help message"
    Write-Host ""
    Write-Host "Default: Runs in headless mode" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

# Run the TradeBot Sentinel
if ($Visible) {
    Write-Host "Running TradeBot Sentinel in VISIBLE mode (for debugging)..." -ForegroundColor Yellow
    Write-Host ""
    python login_bulenox_playwright.py --visible
} else {
    Write-Host "Running TradeBot Sentinel in HEADLESS mode (default)..." -ForegroundColor Green
    Write-Host ""
    python login_bulenox_playwright.py
}

# Check exit code and display results
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===== TradeBot Sentinel completed successfully =====" -ForegroundColor Green
    Write-Host ""
    Write-Host "Generated files:" -ForegroundColor Cyan
    
    if (Test-Path "trade.sh") {
        Write-Host "- trade.sh (cURL command)" -ForegroundColor White
    }
    if (Test-Path "trade_request_full.py") {
        Write-Host "- trade_request_full.py (Python requests code)" -ForegroundColor White
    }
    if (Test-Path "tradebot_sentinel.log") {
        Write-Host "- tradebot_sentinel.log (execution log)" -ForegroundColor White
    }
    
    $screenshots = Get-ChildItem -Name "screenshot_*.png" -ErrorAction SilentlyContinue
    if ($screenshots) {
        Write-Host "- screenshot_*.png (debug screenshots)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "Trade execution details saved for manual review and automation." -ForegroundColor Green
    
} else {
    Write-Host ""
    Write-Host "===== TradeBot Sentinel encountered an error =====" -ForegroundColor Red
    Write-Host "Exit code: $LASTEXITCODE" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Cyan
    Write-Host "1. Check tradebot_sentinel.log for detailed error messages" -ForegroundColor White
    Write-Host "2. Run with -Visible flag to see browser interactions" -ForegroundColor White
    Write-Host "3. Verify your Bulenox credentials are correct" -ForegroundColor White
    Write-Host "4. Ensure stable internet connection" -ForegroundColor White
    Write-Host "5. Check if Playwright browsers are installed: playwright install" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host