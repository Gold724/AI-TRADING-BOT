# run_trae.ps1
# PowerShell script to run the TRAE AI Trading System

param (
    [string]$Environment = "development",
    [string]$Broker = "mock",
    [switch]$SkipTest = $false,
    [string]$ConfigPath = "config/deploy_config.json"
)

# Display banner
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "         TRAE AI TRADING SYSTEM" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher and try again." -ForegroundColor Red
    exit 1
}

# Check if requirements are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
python -c "import pandas, numpy, matplotlib, streamlit" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install dependencies." -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Host "Dependencies already installed." -ForegroundColor Green
}

# Build command arguments
$args = @("deploy.py")
$args += "--environment", $Environment
$args += "--broker", $Broker
$args += "--config", $ConfigPath
if ($SkipTest) {
    $args += "--skip-test"
}

# Display configuration
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Environment: $Environment" -ForegroundColor Yellow
Write-Host "  Broker: $Broker" -ForegroundColor Yellow
Write-Host "  Config Path: $ConfigPath" -ForegroundColor Yellow
Write-Host "  Skip Test: $SkipTest" -ForegroundColor Yellow
Write-Host ""

# Run the deployment script
Write-Host "Starting TRAE AI Trading System..." -ForegroundColor Cyan
Write-Host ""

try {
    & python $args
} catch {
    Write-Host "Error: Failed to start TRAE AI Trading System." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}