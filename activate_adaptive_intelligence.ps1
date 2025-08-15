# PowerShell script to activate the TRAE Adaptive Intelligence System

# Default values
$Mode = "full"
$ForceReport = $false
$ConfigDir = "config"
$DataDir = "data"

# Parse command line arguments
param (
    [Parameter(Mandatory=$false)]
    [ValidateSet("initialize", "evaluate", "report", "full")]
    [string]$mode = "full",
    
    [Parameter(Mandatory=$false)]
    [switch]$forceReport = $false,
    
    [Parameter(Mandatory=$false)]
    [string]$configDir = "config",
    
    [Parameter(Mandatory=$false)]
    [string]$dataDir = "data"
)

# Display script banner
Write-Host "=== TRAE Adaptive Intelligence System ===" -ForegroundColor Cyan
Write-Host "Mode: $mode" -ForegroundColor White
Write-Host "Force report: $forceReport" -ForegroundColor White
Write-Host "Config directory: $configDir" -ForegroundColor White
Write-Host "Data directory: $dataDir" -ForegroundColor White
Write-Host ""

# Ensure Python virtual environment is activated if it exists
if (Test-Path -Path "venv\Scripts\activate.ps1") {
    Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\activate.ps1
}

# Build command arguments
$cmdArgs = "--mode $mode --config-dir $configDir --data-dir $dataDir"

if ($forceReport) {
    $cmdArgs = "$cmdArgs --force-report"
}

# Run the Python script
Write-Host "Executing: python activate_adaptive_intelligence.py $cmdArgs" -ForegroundColor Green
try {
    python activate_adaptive_intelligence.py $cmdArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Adaptive Intelligence System execution completed successfully" -ForegroundColor Green
    } else {
        Write-Host "Error: Adaptive Intelligence System execution failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}