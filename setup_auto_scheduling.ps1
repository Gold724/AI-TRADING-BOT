<#
.SYNOPSIS
    Trae Auto-Scheduling & CI/CD Integration Setup Script
.DESCRIPTION
    This script sets up auto-scheduling for Trae deployment via Task Scheduler and configures GitHub Actions for CI/CD integration.
.NOTES
    Created by: Trae AI
    Version: 1.0
#>

# Script configuration
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Trae Auto-Scheduling Setup"

# Default values
$DeployScriptPath = "$PSScriptRoot\trae_deploy.ps1"
$NewsScriptPath = "$PSScriptRoot\auto_news_cron.ps1"
$SshKeyPath = "D:\anki\trae_vps"
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
        [string]$SshKeyPath,
        
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
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$DeployScriptPath`" -SshKeyPath `"$SshKeyPath`" -LogPath `"$LogFilePath`""
    
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

# Function to update GitHub workflow file
function Update-GitHubWorkflow {
    # Check if .github/workflows directory exists
    $workflowsDir = Join-Path -Path $PSScriptRoot -ChildPath ".github\workflows"
    
    if (-not (Test-Path -Path $workflowsDir)) {
        Write-ColorOutput "Creating GitHub workflows directory..." "Yellow"
        New-Item -Path $workflowsDir -ItemType Directory -Force | Out-Null
    }
    
    # Path to the workflow file
    $workflowFilePath = Join-Path -Path $workflowsDir -ChildPath "trae_auto_deployment.yml"
    
    # Create the workflow file content
    $workflowContent = @"
name: Trae Auto Deployment

on:
  push:
    branches:
      - main
  workflow_dispatch:
  schedule:
    # Run daily at 3:00 AM UTC
    - cron: '0 3 * * *'

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up SSH key
      run: |
        mkdir -p ~/.ssh
        echo "`${{ secrets.VPS_SSH_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan `${{ secrets.CONTABO_VPS_IP || '161.97.112.146' }} >> ~/.ssh/known_hosts

    - name: Deploy via SSH
      run: |
        ssh `${{ secrets.CONTABO_USERNAME || 'root' }}@`${{ secrets.CONTABO_VPS_IP || '161.97.112.146' }} 'bash /opt/trae/trae_deploy.sh --auto'

    - name: Send Slack notification
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: `${{ job.status }}
        fields: repo,message,commit,author,action,eventName,ref,workflow
      env:
        SLACK_WEBHOOK_URL: `${{ secrets.SLACK_WEBHOOK_URL }}
"@
    
    # Write the workflow file
    $workflowContent | Out-File -FilePath $workflowFilePath -Encoding utf8 -Force
    
    Write-ColorOutput "✅ GitHub Actions workflow file created at: $workflowFilePath" "Green"
    Write-ColorOutput "👉 Remember to add your SSH private key to GitHub Secrets as 'VPS_SSH_KEY'" "Yellow"
}

# Main script execution
Show-Banner

# Step 1: Collect deployment script information
Write-Host ""
Write-ColorOutput "STEP 1: DEPLOYMENT SCRIPT INFORMATION" "Green"
Write-ColorOutput "----------------------------------" "Green"

$inputDeployScriptPath = Read-Host "Enter the path to your deployment script (default: $DeployScriptPath)"
if ($inputDeployScriptPath) {
    $DeployScriptPath = $inputDeployScriptPath
}

if (-not (Test-Path -Path $DeployScriptPath -PathType Leaf)) {
    Write-ColorOutput "Warning: Deployment script not found at $DeployScriptPath" "Yellow"
    $createScript = Read-Host "Do you want to create a basic deployment script? (y/n)"
    
    if ($createScript -eq "y") {
        $basicScript = @"
<#
.SYNOPSIS
    Trae Deployment Script
.DESCRIPTION
    This script deploys the Trae AI Trading Sentinel application.
#>

param (
    [string]\$SshKeyPath,
    [string]\$LogPath
)

# Log function
function Write-Log {
    param ([string]\$Message)
    \$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[\$timestamp] \$Message" | Out-File -Append -FilePath \$LogPath -Encoding utf8
    Write-Host "[\$timestamp] \$Message"
}

Write-Log "Starting Trae deployment..."

# Add your deployment logic here
# Example: git pull, build, restart services, etc.

Write-Log "Deployment completed successfully."
"@
        
        $basicScript | Out-File -FilePath $DeployScriptPath -Encoding utf8 -Force
        Write-ColorOutput "Basic deployment script created at $DeployScriptPath" "Green"
        Write-ColorOutput "Please customize it with your specific deployment logic." "Yellow"
    } else {
        Write-ColorOutput "Please create a deployment script and run this setup again." "Red"
        exit 1
    }
}

# Step 2: Collect SSH key information
Write-Host ""
Write-ColorOutput "STEP 2: SSH KEY INFORMATION" "Green"
Write-ColorOutput "------------------------" "Green"

$inputSshKeyPath = Read-Host "Enter the path to your SSH private key file (default: $SshKeyPath)"
if ($inputSshKeyPath) {
    $SshKeyPath = $inputSshKeyPath
}

if (-not (Test-Path -Path $SshKeyPath -PathType Leaf)) {
    Write-ColorOutput "Warning: SSH key not found at $SshKeyPath" "Yellow"
    Write-ColorOutput "Please ensure your SSH key is available before running the scheduled task." "Yellow"
}

# Step 3: Collect log file information
Write-Host ""
Write-ColorOutput "STEP 3: LOG FILE INFORMATION" "Green"
Write-ColorOutput "-------------------------" "Green"

$inputLogFilePath = Read-Host "Enter the path for the log file (default: $LogFilePath)"
if ($inputLogFilePath) {
    $LogFilePath = $inputLogFilePath
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
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$NewsScriptPath`"`""
    
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

# Step 4: Set up Task Scheduler
Write-Host ""
Write-ColorOutput "STEP 4: SETTING UP TASK SCHEDULER" "Green"
Write-ColorOutput "------------------------------" "Green"

$setupTask = Read-Host "Do you want to set up a scheduled task for automatic deployment? (y/n)"
if ($setupTask -eq "y") {
    Setup-TaskScheduler -DeployScriptPath $DeployScriptPath -SshKeyPath $SshKeyPath -LogFilePath $LogFilePath
} else {
    Write-ColorOutput "Task Scheduler setup skipped." "Yellow"
}

# Step 4b: Set up News Task Scheduler
Write-Host ""
Write-ColorOutput "STEP 4b: SETTING UP NEWS FETCHING TASK" "Green"
Write-ColorOutput "----------------------------------" "Green"

$setupNewsTask = Read-Host "Do you want to set up a scheduled task for automatic news data fetching? (y/n)"
if ($setupNewsTask -eq "y") {
    Setup-NewsTaskScheduler -NewsScriptPath $NewsScriptPath -NewsLogFilePath $NewsLogFilePath
    
    # Run initial news fetch
    $runInitialFetch = Read-Host "Do you want to run an initial news data fetch now? (y/n)"
    if ($runInitialFetch -eq "y") {
        Write-ColorOutput "Running initial news data fetch..." "Yellow"
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$NewsScriptPath"
        Write-ColorOutput "Initial news data fetch completed." "Green"
    }
} else {
    Write-ColorOutput "News Task Scheduler setup skipped." "Yellow"
}

# Step 5: Update GitHub workflow
Write-Host ""
Write-ColorOutput "STEP 5: SETTING UP GITHUB ACTIONS" "Green"
Write-ColorOutput "-----------------------------" "Green"

$setupGitHub = Read-Host "Do you want to set up GitHub Actions for CI/CD integration? (y/n)"
if ($setupGitHub -eq "y") {
    Update-GitHubWorkflow
} else {
    Write-ColorOutput "GitHub Actions setup skipped." "Yellow"
}

# Final instructions
Write-Host ""
Write-ColorOutput "SETUP COMPLETE!" "Green"
Write-ColorOutput "-------------" "Green"
Write-Host ""
Write-ColorOutput "🔐 Notes for Secure Setup:" "Yellow"
Write-ColorOutput "1. Make sure your private key at $SshKeyPath has proper permissions (chmod 600 on Linux/macOS)." "White"
Write-ColorOutput "2. For GitHub Actions, go to Settings > Secrets in your GitHub repo and add:" "White"
Write-ColorOutput "   - VPS_SSH_KEY: contents of your private key file" "White"
Write-ColorOutput "   - CONTABO_VPS_IP: your VPS IP address" "White"
Write-ColorOutput "   - CONTABO_USERNAME: your VPS username" "White"
Write-ColorOutput "3. If you are using Slack notifications, add SLACK_WEBHOOK_URL to your GitHub Secrets." "White"
Write-Host ""
Write-ColorOutput "Your Trae deployment is now set to run automatically! 🚀" "Green"