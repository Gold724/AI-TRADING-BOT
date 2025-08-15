# Trae AI Trading Bot - Windows Service Setup Script

param (
    [string]$ServiceName = "trae",
    [string]$DisplayName = "Trae AI Trading Bot",
    [string]$Description = "AI Trading Bot service for automated trading",
    [string]$WorkingDirectory = (Get-Location).Path,
    [string]$PythonPath = "$WorkingDirectory\venv\Scripts\python.exe",
    [string]$MainScript = "$WorkingDirectory\main.py",
    [string]$LogPath = "$WorkingDirectory\logs"
)

# Colors for console output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

# Check if running as administrator
function Test-Administrator {
    $user = [Security.Principal.WindowsIdentity]::GetCurrent();
    $principal = New-Object Security.Principal.WindowsPrincipal $user
    return $principal.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "This script requires administrator privileges." -ForegroundColor $ErrorColor
    Write-Host "Please run PowerShell as Administrator and execute this script again." -ForegroundColor $ErrorColor
    Write-Host "\nTo run as Administrator:" -ForegroundColor $InfoColor
    Write-Host "1. Right-click on PowerShell and select 'Run as Administrator'" -ForegroundColor $InfoColor
    Write-Host "2. Navigate to this directory: $WorkingDirectory" -ForegroundColor $InfoColor
    Write-Host "3. Run: .\setup_windows_service.ps1" -ForegroundColor $InfoColor
    exit 1
}

# Create logs directory if it doesn't exist
if (-not (Test-Path $LogPath)) {
    Write-Host "Creating logs directory at $LogPath..." -ForegroundColor $InfoColor
    New-Item -Path $LogPath -ItemType Directory -Force | Out-Null
}

# Check if service already exists
$serviceExists = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($serviceExists) {
    Write-Host "Service '$ServiceName' already exists. Stopping and removing..." -ForegroundColor $WarningColor
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    $deleteCmd = "sc.exe delete $ServiceName"
    Write-Host "Running: $deleteCmd" -ForegroundColor $InfoColor
    Invoke-Expression $deleteCmd | Out-Host
    Start-Sleep -Seconds 2  # Wait for service to be fully removed
}

# Create the service using SC command
Write-Host "Creating service using SC command..." -ForegroundColor $InfoColor

# Create the binPath with proper quoting
$binPath = '"' + $PythonPath + '" "' + $MainScript + '"'
Write-Host "Using binPath: $binPath" -ForegroundColor $InfoColor

# Create the service
$createCmd = "sc.exe create $ServiceName binPath= `"$binPath`" DisplayName= `"$DisplayName`" start= auto"
Write-Host "Running: $createCmd" -ForegroundColor $InfoColor
Invoke-Expression $createCmd | Out-Host

# Set description
$descCmd = "sc.exe description $ServiceName `"$Description`""
Write-Host "Running: $descCmd" -ForegroundColor $InfoColor
Invoke-Expression $descCmd | Out-Host

# Configure failure actions (restart on failure)
$failureCmd = "sc.exe failure $ServiceName reset= 86400 actions= restart/30000/restart/60000/restart/120000"
Write-Host "Running: $failureCmd" -ForegroundColor $InfoColor
Invoke-Expression $failureCmd | Out-Host

# Check if service was created successfully
$serviceCreated = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($serviceCreated) {
    Write-Host "Service '$ServiceName' created successfully." -ForegroundColor $SuccessColor
    Write-Host "Service status: $($serviceCreated.Status)" -ForegroundColor $InfoColor
    
    if ($serviceCreated.Status -ne "Running") {
        Write-Host "Starting service..." -ForegroundColor $InfoColor
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 3  # Wait for service to start
        $serviceCreated = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Write-Host "Service status: $($serviceCreated.Status)" -ForegroundColor $InfoColor
    }
    
    Write-Host "\nYou can now use the healthcheck.ps1 script to monitor the service:" -ForegroundColor $InfoColor
    Write-Host "  .\healthcheck.ps1 -ServiceName \"$ServiceName\" -SlackWebhookUrl \"your-slack-webhook-url\" -RestartOnFailure" -ForegroundColor $InfoColor
} else {
    Write-Host "Failed to create service '$ServiceName'." -ForegroundColor $ErrorColor
}