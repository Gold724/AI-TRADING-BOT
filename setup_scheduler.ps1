# Simplified Trae Auto-Scheduling Setup Script

# Script configuration
$ErrorActionPreference = "Stop"

# Default values
$DeployScriptPath = "$PSScriptRoot\trae_deploy.ps1"
$NewsScriptPath = "$PSScriptRoot\auto_news_cron.ps1"
$LogFilePath = "$PSScriptRoot\logs\trae_scheduled_deploy.log"
$NewsLogFilePath = "$PSScriptRoot\logs\trae_news_fetch.log"

# Function to display colored messages
function Write-ColorOutput {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$ForegroundColor = "White"
    )
    
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# Function to display a banner
function Show-Banner {
    Clear-Host
    Write-ColorOutput "===================================================" "Cyan"
    Write-ColorOutput "           TRAE AUTO-SCHEDULING SETUP             " "Cyan"
    Write-ColorOutput "===================================================" "Cyan"
    Write-ColorOutput "Automating your deployment pipeline..." "Yellow"
    Write-ColorOutput "===================================================" "Cyan"
    Write-Host ""
}

# Function to set up Windows Task Scheduler job for deployment
function Setup-TaskScheduler {
    param (
        [Parameter(Mandatory=$true)]
        [string]$DeployScriptPath,
        
        [Parameter(Mandatory=$true)]
        [string]$LogFilePath
    )
    
    # Create log directory if it doesn't exist
    $logDir = Split-Path -Path $LogFilePath -Parent
    if (-not (Test-Path -Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }
    
    # Create the scheduled task
    $taskName = "TraeAutoDeployment"
    $taskDescription = "Automatically deploys Trae AI Trading Sentinel daily"
    
    # Check if the task already exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-ColorOutput "Scheduled task '$taskName' already exists. Updating..." "Yellow"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    # Create the action to run the PowerShell script
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$DeployScriptPath`" -LogPath `"$LogFilePath`""
    
    # Create a trigger for daily execution at 3:00 AM
    $trigger = New-ScheduledTaskTrigger -Daily -At 3am
    
    # Create the task settings
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    
    # Register the scheduled task
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription -RunLevel Highest -Force | Out-Null
    
    Write-ColorOutput "✅ Scheduled task '$taskName' has been created successfully!" "Green"
    Write-ColorOutput "👉 The system will automatically run the deployment script daily at 3:00 AM." "Yellow"
    Write-ColorOutput "👉 Logs will be written to $LogFilePath" "Yellow"
}

# Function to set up Windows Task Scheduler job for news fetching
function Setup-NewsTaskScheduler {
    param (
        [Parameter(Mandatory=$true)]
        [string]$NewsScriptPath,
        
        [Parameter(Mandatory=$true)]
        [string]$NewsLogFilePath
    )
    
    # Create log directory if it doesn't exist
    $logDir = Split-Path -Path $NewsLogFilePath -Parent
    if (-not (Test-Path -Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }
    
    # Create the scheduled task
    $taskName = "TraeNewsDataFetch"
    $taskDescription = "Automatically fetches economic news data for Trae AI Trading Sentinel daily"
    
    # Check if the task already exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-ColorOutput "Scheduled task '$taskName' already exists. Updating..." "Yellow"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    # Create the action to run the PowerShell script
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$NewsScriptPath`""
    
    # Create a trigger for daily execution at 12:00 AM
    $trigger = New-ScheduledTaskTrigger -Daily -At 12am
    
    # Create the task settings
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    
    # Register the scheduled task
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription -RunLevel Highest -Force | Out-Null
    
    Write-ColorOutput "✅ Scheduled task '$taskName' has been created successfully!" "Green"
    Write-ColorOutput "👉 The system will automatically fetch economic news data daily at 12:00 AM." "Yellow"
    Write-ColorOutput "👉 Logs will be written to $NewsLogFilePath" "Yellow"
}

# Main script execution
Show-Banner

# Set up Task Scheduler for deployment
Write-Host ""
Write-ColorOutput "SETTING UP DEPLOYMENT TASK SCHEDULER" "Green"
Write-ColorOutput "----------------------------------" "Green"
Setup-TaskScheduler -DeployScriptPath $DeployScriptPath -LogFilePath $LogFilePath

# Set up Task Scheduler for news fetching
Write-Host ""
Write-ColorOutput "SETTING UP NEWS FETCHING TASK" "Green"
Write-ColorOutput "---------------------------" "Green"
Setup-NewsTaskScheduler -NewsScriptPath $NewsScriptPath -NewsLogFilePath $NewsLogFilePath

# Final instructions
Write-Host ""
Write-ColorOutput "SETUP COMPLETE!" "Green"
Write-ColorOutput "-------------" "Green"
Write-Host ""
Write-ColorOutput "Your Trae deployment is now set to run automatically!" "Green"