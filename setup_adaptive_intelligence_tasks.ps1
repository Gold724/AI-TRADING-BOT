# PowerShell script to set up scheduled tasks for the TRAE Adaptive Intelligence System

# Display banner
Write-Host "=== Setting up TRAE Adaptive Intelligence Scheduled Tasks ===" -ForegroundColor Cyan

# Get the absolute path to the project directory
$ProjectDir = $PSScriptRoot
Write-Host "Project directory: $ProjectDir" -ForegroundColor White
Write-Host ""

# Create logs directory if it doesn't exist
$LogsDir = Join-Path -Path $ProjectDir -ChildPath "logs"
if (-not (Test-Path -Path $LogsDir)) {
    Write-Host "Creating logs directory..." -ForegroundColor Yellow
    New-Item -Path $LogsDir -ItemType Directory | Out-Null
}

# Function to create or update a scheduled task
function Set-AdaptiveIntelligenceTask {
    param (
        [string]$TaskName,
        [string]$Description,
        [string]$Mode,
        [string]$LogFile,
        [string]$Schedule,
        [int]$Hour,
        [int]$Minute
    )
    
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Host "Updating existing task: $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    } else {
        Write-Host "Creating new task: $TaskName" -ForegroundColor Green
    }
    
    # Create action to run the PowerShell script
    $action = New-ScheduledTaskAction `
        -Execute "PowerShell.exe" `
        -Argument "-ExecutionPolicy Bypass -File `"$ProjectDir\activate_adaptive_intelligence.ps1`" -mode $Mode" `
        -WorkingDirectory $ProjectDir
    
    # Create trigger based on schedule type
    switch ($Schedule) {
        "Daily" {
            $trigger = New-ScheduledTaskTrigger -Daily -At "$($Hour):$($Minute.ToString('00'))"
        }
        "Weekly" {
            $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "$($Hour):$($Minute.ToString('00'))"
        }
        "Monthly" {
            $trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At "$($Hour):$($Minute.ToString('00'))"
        }
    }
    
    # Create principal (run whether user is logged in or not)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries
    
    # Register the task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $Description `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings
    
    Write-Host "Task '$TaskName' has been registered successfully" -ForegroundColor Green
}

# Set up daily evaluation task (runs at 00:15 every day)
Set-AdaptiveIntelligenceTask `
    -TaskName "TRAE_AdaptiveIntelligence_Daily" `
    -Description "Daily evaluation of trading strategies for TRAE AI Trading Bot" `
    -Mode "evaluate" `
    -LogFile "$LogsDir\adaptive_intelligence_daily.log" `
    -Schedule "Daily" `
    -Hour 0 `
    -Minute 15

# Set up weekly report task (runs at 01:00 every Sunday)
Set-AdaptiveIntelligenceTask `
    -TaskName "TRAE_AdaptiveIntelligence_Weekly" `
    -Description "Weekly report generation for TRAE AI Trading Bot" `
    -Mode "report" `
    -LogFile "$LogsDir\adaptive_intelligence_weekly.log" `
    -Schedule "Weekly" `
    -Hour 1 `
    -Minute 0

# Set up monthly full run task (runs at 02:00 on the 1st of each month)
Set-AdaptiveIntelligenceTask `
    -TaskName "TRAE_AdaptiveIntelligence_Monthly" `
    -Description "Monthly full run of Adaptive Intelligence for TRAE AI Trading Bot" `
    -Mode "full" `
    -LogFile "$LogsDir\adaptive_intelligence_monthly.log" `
    -Schedule "Monthly" `
    -Hour 2 `
    -Minute 0

# Verify task creation
Write-Host ""
Write-Host "Verifying scheduled tasks..." -ForegroundColor Yellow
Get-ScheduledTask | Where-Object {$_.TaskName -like "TRAE_AdaptiveIntelligence*"} | Format-Table TaskName, State, LastRunTime

Write-Host ""
Write-Host "Scheduled tasks for TRAE Adaptive Intelligence System have been set up successfully." -ForegroundColor Cyan
Write-Host "Logs will be written to the logs directory." -ForegroundColor White