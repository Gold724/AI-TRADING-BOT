# TradeBot Sentinel - Windows Service Wrapper
# PowerShell script for managing TradeBot Sentinel as a Windows service

param(
    [string]$Action = "help",
    [string]$ServiceName = "TradeBotSentinel",
    [string]$ServiceDisplayName = "TradeBot Sentinel Trading Bot",
    [string]$ServiceDescription = "Automated trading bot for financial markets",
    [string]$WorkingDirectory = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$PythonPath = "python.exe",
    [string]$ScriptPath = "main.py",
    [string]$LogPath = "logs\service.log",
    [switch]$UseNSSM = $false,
    [switch]$UseTaskScheduler = $false,
    [switch]$Verbose = $false
)

# Set error action preference
$ErrorActionPreference = "Continue"

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"
$Purple = "Magenta"

# Logging function
function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "INFO" { Write-Host $logMessage -ForegroundColor $Blue }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor $Green }
        "WARNING" { Write-Host $logMessage -ForegroundColor $Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor $Red }
        "DEBUG" { if ($Verbose) { Write-Host $logMessage -ForegroundColor $Purple } }
        default { Write-Host $logMessage }
    }
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-NSSM {
    try {
        $nssmVersion = nssm version 2>$null
        return $nssmVersion -ne $null
    }
    catch {
        return $false
    }
}

function Install-NSSMService {
    Write-Log "INFO" "Installing service using NSSM..."
    
    if (-not (Test-NSSM)) {
        Write-Log "ERROR" "NSSM is not installed or not in PATH"
        Write-Log "INFO" "Download NSSM from: https://nssm.cc/download"
        return $false
    }
    
    # Check if service already exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Log "WARNING" "Service '$ServiceName' already exists. Use 'remove' action first."
        return $false
    }
    
    # Resolve full paths
    $fullWorkingDir = Resolve-Path $WorkingDirectory -ErrorAction SilentlyContinue
    if (-not $fullWorkingDir) {
        Write-Log "ERROR" "Working directory not found: $WorkingDirectory"
        return $false
    }
    
    $fullScriptPath = Join-Path $fullWorkingDir $ScriptPath
    if (-not (Test-Path $fullScriptPath)) {
        Write-Log "ERROR" "Script not found: $fullScriptPath"
        return $false
    }
    
    $fullLogPath = Join-Path $fullWorkingDir $LogPath
    $logDir = Split-Path $fullLogPath -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    try {
        # Install the service
        & nssm install $ServiceName $PythonPath $ScriptPath
        
        # Configure service parameters
        & nssm set $ServiceName AppDirectory $fullWorkingDir
        & nssm set $ServiceName DisplayName $ServiceDisplayName
        & nssm set $ServiceName Description $ServiceDescription
        & nssm set $ServiceName Start SERVICE_AUTO_START
        
        # Configure logging
        & nssm set $ServiceName AppStdout $fullLogPath
        & nssm set $ServiceName AppStderr $fullLogPath
        & nssm set $ServiceName AppRotateFiles 1
        & nssm set $ServiceName AppRotateOnline 1
        & nssm set $ServiceName AppRotateSeconds 86400  # Daily rotation
        & nssm set $ServiceName AppRotateBytes 10485760  # 10MB max size
        
        # Configure restart behavior
        & nssm set $ServiceName AppThrottle 5000  # 5 second throttle
        & nssm set $ServiceName AppExit Default Restart
        & nssm set $ServiceName AppRestartDelay 30000  # 30 second delay
        
        # Configure environment
        & nssm set $ServiceName AppEnvironmentExtra "PYTHONUNBUFFERED=1"
        
        Write-Log "SUCCESS" "Service '$ServiceName' installed successfully"
        Write-Log "INFO" "Service will log to: $fullLogPath"
        return $true
    }
    catch {
        Write-Log "ERROR" "Failed to install service: $($_.Exception.Message)"
        return $false
    }
}

function Remove-NSSMService {
    Write-Log "INFO" "Removing NSSM service..."
    
    if (-not (Test-NSSM)) {
        Write-Log "ERROR" "NSSM is not installed or not in PATH"
        return $false
    }
    
    # Check if service exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $existingService) {
        Write-Log "WARNING" "Service '$ServiceName' does not exist"
        return $true
    }
    
    try {
        # Stop service if running
        if ($existingService.Status -eq "Running") {
            Write-Log "INFO" "Stopping service..."
            Stop-Service -Name $ServiceName -Force
            Start-Sleep -Seconds 5
        }
        
        # Remove the service
        & nssm remove $ServiceName confirm
        
        Write-Log "SUCCESS" "Service '$ServiceName' removed successfully"
        return $true
    }
    catch {
        Write-Log "ERROR" "Failed to remove service: $($_.Exception.Message)"
        return $false
    }
}

function Install-TaskSchedulerService {
    Write-Log "INFO" "Installing service using Task Scheduler..."
    
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Log "WARNING" "Scheduled task '$ServiceName' already exists. Use 'remove' action first."
        return $false
    }
    
    # Resolve full paths
    $fullWorkingDir = Resolve-Path $WorkingDirectory -ErrorAction SilentlyContinue
    if (-not $fullWorkingDir) {
        Write-Log "ERROR" "Working directory not found: $WorkingDirectory"
        return $false
    }
    
    $fullScriptPath = Join-Path $fullWorkingDir $ScriptPath
    if (-not (Test-Path $fullScriptPath)) {
        Write-Log "ERROR" "Script not found: $fullScriptPath"
        return $false
    }
    
    try {
        # Create action
        $action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $fullWorkingDir
        
        # Create trigger (at startup)
        $trigger = New-ScheduledTaskTrigger -AtStartup
        
        # Create settings
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
        
        # Create principal (run as SYSTEM)
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        
        # Register the task
        Register-ScheduledTask -TaskName $ServiceName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description $ServiceDescription
        
        Write-Log "SUCCESS" "Scheduled task '$ServiceName' created successfully"
        Write-Log "INFO" "Task will start automatically at system startup"
        return $true
    }
    catch {
        Write-Log "ERROR" "Failed to create scheduled task: $($_.Exception.Message)"
        return $false
    }
}

function Remove-TaskSchedulerService {
    Write-Log "INFO" "Removing Task Scheduler service..."
    
    # Check if task exists
    $existingTask = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
    if (-not $existingTask) {
        Write-Log "WARNING" "Scheduled task '$ServiceName' does not exist"
        return $true
    }
    
    try {
        # Stop task if running
        if ($existingTask.State -eq "Running") {
            Write-Log "INFO" "Stopping scheduled task..."
            Stop-ScheduledTask -TaskName $ServiceName
            Start-Sleep -Seconds 5
        }
        
        # Remove the task
        Unregister-ScheduledTask -TaskName $ServiceName -Confirm:$false
        
        Write-Log "SUCCESS" "Scheduled task '$ServiceName' removed successfully"
        return $true
    }
    catch {
        Write-Log "ERROR" "Failed to remove scheduled task: $($_.Exception.Message)"
        return $false
    }
}

function Start-TradeBotService {
    Write-Log "INFO" "Starting TradeBot service..."
    
    # Try NSSM service first
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        try {
            Start-Service -Name $ServiceName
            Write-Log "SUCCESS" "Service '$ServiceName' started successfully"
            return $true
        }
        catch {
            Write-Log "ERROR" "Failed to start service: $($_.Exception.Message)"
            return $false
        }
    }
    
    # Try scheduled task
    $task = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
    if ($task) {
        try {
            Start-ScheduledTask -TaskName $ServiceName
            Write-Log "SUCCESS" "Scheduled task '$ServiceName' started successfully"
            return $true
        }
        catch {
            Write-Log "ERROR" "Failed to start scheduled task: $($_.Exception.Message)"
            return $false
        }
    }
    
    Write-Log "ERROR" "No service or scheduled task found with name '$ServiceName'"
    return $false
}

function Stop-TradeBotService {
    Write-Log "INFO" "Stopping TradeBot service..."
    
    # Try NSSM service first
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        try {
            Stop-Service -Name $ServiceName -Force
            Write-Log "SUCCESS" "Service '$ServiceName' stopped successfully"
            return $true
        }
        catch {
            Write-Log "ERROR" "Failed to stop service: $($_.Exception.Message)"
            return $false
        }
    }
    
    # Try scheduled task
    $task = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
    if ($task) {
        try {
            Stop-ScheduledTask -TaskName $ServiceName
            Write-Log "SUCCESS" "Scheduled task '$ServiceName' stopped successfully"
            return $true
        }
        catch {
            Write-Log "ERROR" "Failed to stop scheduled task: $($_.Exception.Message)"
            return $false
        }
    }
    
    Write-Log "ERROR" "No service or scheduled task found with name '$ServiceName'"
    return $false
}

function Get-TradeBotServiceStatus {
    Write-Log "INFO" "Checking TradeBot service status..."
    
    # Check NSSM service
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "NSSM Service Status:" -ForegroundColor $Yellow
        Write-Host "  Name: $($service.Name)" -ForegroundColor $Blue
        Write-Host "  Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { $Green } else { $Red })
        Write-Host "  Start Type: $($service.StartType)" -ForegroundColor $Blue
        
        if (Test-NSSM) {
            try {
                $nssmStatus = & nssm status $ServiceName 2>$null
                Write-Host "  NSSM Status: $nssmStatus" -ForegroundColor $Blue
            }
            catch {
                Write-Host "  NSSM Status: Unknown" -ForegroundColor $Yellow
            }
        }
        
        return $true
    }
    
    # Check scheduled task
    $task = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "Scheduled Task Status:" -ForegroundColor $Yellow
        Write-Host "  Name: $($task.TaskName)" -ForegroundColor $Blue
        Write-Host "  State: $($task.State)" -ForegroundColor $(if ($task.State -eq "Running") { $Green } else { $Red })
        Write-Host "  Last Run: $($task.LastRunTime)" -ForegroundColor $Blue
        Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor $Blue
        
        return $true
    }
    
    Write-Host "No service or scheduled task found with name '$ServiceName'" -ForegroundColor $Red
    return $false
}

function Show-ServiceLogs {
    param([int]$Lines = 50)
    
    Write-Log "INFO" "Showing service logs (last $Lines lines)..."
    
    $logFile = Join-Path $WorkingDirectory $LogPath
    
    if (Test-Path $logFile) {
        Write-Host "Log file: $logFile" -ForegroundColor $Blue
        Write-Host "=" * 80 -ForegroundColor $Purple
        
        Get-Content $logFile -Tail $Lines | ForEach-Object {
            if ($_ -match "ERROR|CRITICAL|EXCEPTION") {
                Write-Host $_ -ForegroundColor $Red
            }
            elseif ($_ -match "WARNING|WARN") {
                Write-Host $_ -ForegroundColor $Yellow
            }
            elseif ($_ -match "SUCCESS|COMPLETED") {
                Write-Host $_ -ForegroundColor $Green
            }
            else {
                Write-Host $_
            }
        }
        
        Write-Host "=" * 80 -ForegroundColor $Purple
    }
    else {
        Write-Log "WARNING" "Log file not found: $logFile"
    }
}

function Test-Prerequisites {
    Write-Log "INFO" "Checking prerequisites..."
    
    $allGood = $true
    
    # Check administrator rights
    if (-not (Test-Administrator)) {
        Write-Log "ERROR" "Administrator rights required for service management"
        $allGood = $false
    }
    
    # Check Python
    try {
        $pythonVersion = & $PythonPath --version 2>$null
        if ($pythonVersion) {
            Write-Log "SUCCESS" "Python found: $pythonVersion"
        }
        else {
            Write-Log "ERROR" "Python not found at: $PythonPath"
            $allGood = $false
        }
    }
    catch {
        Write-Log "ERROR" "Python not accessible: $($_.Exception.Message)"
        $allGood = $false
    }
    
    # Check script file
    $fullScriptPath = Join-Path $WorkingDirectory $ScriptPath
    if (Test-Path $fullScriptPath) {
        Write-Log "SUCCESS" "Script found: $fullScriptPath"
    }
    else {
        Write-Log "ERROR" "Script not found: $fullScriptPath"
        $allGood = $false
    }
    
    # Check service method availability
    if ($UseNSSM) {
        if (Test-NSSM) {
            Write-Log "SUCCESS" "NSSM is available"
        }
        else {
            Write-Log "ERROR" "NSSM not found. Download from: https://nssm.cc/download"
            $allGood = $false
        }
    }
    elseif ($UseTaskScheduler) {
        Write-Log "SUCCESS" "Task Scheduler will be used"
    }
    else {
        # Auto-detect best method
        if (Test-NSSM) {
            Write-Log "INFO" "NSSM detected - will use NSSM for service management"
            $script:UseNSSM = $true
        }
        else {
            Write-Log "INFO" "NSSM not found - will use Task Scheduler"
            $script:UseTaskScheduler = $true
        }
    }
    
    return $allGood
}

function Show-Help {
    Write-Host "TradeBot Sentinel - Windows Service Wrapper" -ForegroundColor $Green
    Write-Host ""
    Write-Host "Usage: .\service-wrapper.ps1 [ACTION] [OPTIONS]" -ForegroundColor $Blue
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor $Yellow
    Write-Host "  install          Install TradeBot as Windows service"
    Write-Host "  remove           Remove TradeBot service"
    Write-Host "  start            Start TradeBot service"
    Write-Host "  stop             Stop TradeBot service"
    Write-Host "  restart          Restart TradeBot service"
    Write-Host "  status           Show service status"
    Write-Host "  logs             Show service logs"
    Write-Host "  test             Test prerequisites"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor $Yellow
    Write-Host "  -ServiceName <name>        Service name [default: TradeBotSentinel]"
    Write-Host "  -WorkingDirectory <path>   Working directory [default: current]"
    Write-Host "  -PythonPath <path>         Python executable [default: python.exe]"
    Write-Host "  -ScriptPath <path>         Main script [default: main.py]"
    Write-Host "  -UseNSSM                   Force use of NSSM"
    Write-Host "  -UseTaskScheduler          Force use of Task Scheduler"
    Write-Host "  -Verbose                   Enable verbose output"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor $Yellow
    Write-Host "  .\service-wrapper.ps1 install                    # Install service (auto-detect method)"
    Write-Host "  .\service-wrapper.ps1 install -UseNSSM           # Install using NSSM"
    Write-Host "  .\service-wrapper.ps1 start                      # Start service"
    Write-Host "  .\service-wrapper.ps1 status                     # Check status"
    Write-Host "  .\service-wrapper.ps1 logs                       # View logs"
    Write-Host ""
    Write-Host "Prerequisites:" -ForegroundColor $Yellow
    Write-Host "  - Run as Administrator"
    Write-Host "  - Python installed and accessible"
    Write-Host "  - NSSM installed (optional, for better service management)"
    Write-Host "  - Download NSSM from: https://nssm.cc/download"
    Write-Host ""
}

function Main {
    Write-Host "=" * 80 -ForegroundColor $Purple
    Write-Host "TradeBot Sentinel - Windows Service Management" -ForegroundColor $Green
    Write-Host "=" * 80 -ForegroundColor $Purple
    Write-Host ""
    
    switch ($Action.ToLower()) {
        "install" {
            if (-not (Test-Prerequisites)) {
                Write-Log "ERROR" "Prerequisites not met. Cannot install service."
                exit 1
            }
            
            if ($UseNSSM -or $script:UseNSSM) {
                $success = Install-NSSMService
            }
            else {
                $success = Install-TaskSchedulerService
            }
            
            if ($success) {
                Write-Log "INFO" "Service installed successfully. Use 'start' action to begin."
            }
            else {
                exit 1
            }
        }
        "remove" {
            if (-not (Test-Administrator)) {
                Write-Log "ERROR" "Administrator rights required"
                exit 1
            }
            
            # Try both methods
            $nssmSuccess = Remove-NSSMService
            $taskSuccess = Remove-TaskSchedulerService
            
            if (-not ($nssmSuccess -or $taskSuccess)) {
                exit 1
            }
        }
        "start" {
            if (-not (Start-TradeBotService)) {
                exit 1
            }
        }
        "stop" {
            if (-not (Stop-TradeBotService)) {
                exit 1
            }
        }
        "restart" {
            Write-Log "INFO" "Restarting TradeBot service..."
            Stop-TradeBotService
            Start-Sleep -Seconds 5
            if (-not (Start-TradeBotService)) {
                exit 1
            }
        }
        "status" {
            if (-not (Get-TradeBotServiceStatus)) {
                exit 1
            }
        }
        "logs" {
            Show-ServiceLogs
        }
        "test" {
            if (-not (Test-Prerequisites)) {
                exit 1
            }
            Write-Log "SUCCESS" "All prerequisites met!"
        }
        "help" {
            Show-Help
        }
        default {
            Write-Log "ERROR" "Unknown action: $Action"
            Show-Help
            exit 1
        }
    }
}

# Show help if requested
if ($args -contains "-h" -or $args -contains "--help") {
    Show-Help
    exit 0
}

# Run main function
try {
    Main
}
catch {
    Write-Log "ERROR" "Service wrapper failed: $($_.Exception.Message)"
    Write-Log "ERROR" "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}