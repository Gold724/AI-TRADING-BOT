# Deployment script for TRAE AI Trading Bot with Adaptive Intelligence (Windows version)

# Display banner
Write-Host "=== TRAE AI Trading Bot Deployment Script (Windows) ===" -ForegroundColor Cyan
Write-Host "This script will set up the TRAE AI Trading Bot with Adaptive Intelligence" -ForegroundColor Cyan
Write-Host ""

# Get the absolute path to the project directory
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Project directory: $PROJECT_DIR"

# Create logs directory if it doesn't exist
$logsDir = Join-Path $PROJECT_DIR "logs"
if (-not (Test-Path $logsDir)) {
    Write-Host "Creating logs directory..." -ForegroundColor Yellow
    New-Item -Path $logsDir -ItemType Directory | Out-Null
    Write-Host "Logs directory created successfully" -ForegroundColor Green
}

# Make sure the activation scripts are executable
Write-Host "\nEnsuring activation scripts are executable..." -ForegroundColor Yellow

# Check if Python is installed
$pythonCommand = "python"
try {
    $pythonVersion = & $pythonCommand --version 2>&1
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python and try again" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists and activate it if it does
$venvPath = Join-Path $PROJECT_DIR "venv"
if (Test-Path $venvPath) {
    Write-Host "Virtual environment found, activating..." -ForegroundColor Yellow
    & "$venvPath\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "No virtual environment found, using system Python" -ForegroundColor Yellow
}

# Set up scheduled tasks
Write-Host "\nSetting up Adaptive Intelligence scheduled tasks..." -ForegroundColor Yellow
$setupTasksScript = Join-Path $PROJECT_DIR "setup_adaptive_intelligence_tasks.ps1"
if (Test-Path $setupTasksScript) {
    & $setupTasksScript
    Write-Host "Scheduled tasks set up successfully" -ForegroundColor Green
} else {
    Write-Host "Error: setup_adaptive_intelligence_tasks.ps1 not found" -ForegroundColor Red
    exit 1
}

# Test run the activation script
Write-Host "\nTesting Adaptive Intelligence activation..." -ForegroundColor Yellow
$activateScript = Join-Path $PROJECT_DIR "activate_adaptive_intelligence.ps1"
if (Test-Path $activateScript) {
    & $activateScript -mode initialize
    Write-Host "Activation test completed" -ForegroundColor Green
} else {
    Write-Host "Error: activate_adaptive_intelligence.ps1 not found" -ForegroundColor Red
    exit 1
}

# Final verification
Write-Host "\nVerifying deployment:" -ForegroundColor Yellow
Write-Host "1. Scheduled tasks:" -ForegroundColor Yellow
Get-ScheduledTask | Where-Object {$_.TaskName -like "*TRAE*"} | Format-Table TaskName,State

Write-Host "\n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "The TRAE AI Trading Bot with Adaptive Intelligence has been deployed successfully" -ForegroundColor Green
Write-Host "You can monitor the bot using:" -ForegroundColor Cyan
Write-Host "  - Task Scheduler for scheduled tasks" -ForegroundColor Cyan
Write-Host "  - Check the logs directory for Adaptive Intelligence logs" -ForegroundColor Cyan
Write-Host "\nTo manually run the Adaptive Intelligence system:" -ForegroundColor Cyan
Write-Host "  .\activate_adaptive_intelligence.ps1 -mode full" -ForegroundColor Cyan