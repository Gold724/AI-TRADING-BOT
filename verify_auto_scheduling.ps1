<#
.SYNOPSIS
    Verify Trae Auto-Scheduling Setup
.DESCRIPTION
    This script verifies that the auto-scheduling setup is correctly configured.
.NOTES
    Created by: Trae AI
    Version: 1.0
#>

# Script configuration
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Verify Trae Auto-Scheduling"

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
    Write-ColorOutput "        VERIFY TRAE AUTO-SCHEDULING SETUP         " "Cyan"
    Write-ColorOutput "===================================================" "Cyan"
    Write-ColorOutput "Checking your deployment automation..." "Yellow"
    Write-ColorOutput "===================================================" "Cyan"
    Write-Host ""
}

# Function to check Task Scheduler setup
function Check-TaskScheduler {
    $taskName = "TraeAutoDeployment"
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    
    if ($task) {
        Write-ColorOutput "✅ Scheduled task '$taskName' exists" "Green"
        Write-ColorOutput "   - State: $($task.State)" "White"
        Write-ColorOutput "   - Last Run Time: $($task.LastRunTime)" "White"
        Write-ColorOutput "   - Next Run Time: $($task.NextRunTime)" "White"
        return $true
    } else {
        Write-ColorOutput "❌ Scheduled task '$taskName' not found" "Red"
        Write-ColorOutput "   Run setup_auto_scheduling.ps1 to create the scheduled task" "Yellow"
        return $false
    }
}

# Function to check GitHub workflow file
function Check-GitHubWorkflow {
    $workflowPath = Join-Path -Path $PSScriptRoot -ChildPath ".github\workflows\trae_auto_deployment.yml"
    
    if (Test-Path -Path $workflowPath) {
        Write-ColorOutput "✅ GitHub Actions workflow file exists" "Green"
        
        # Check if the workflow file contains the required elements
        $workflowContent = Get-Content -Path $workflowPath -Raw
        
        $hasSchedule = $workflowContent -match "schedule:"
        $hasCron = $workflowContent -match "cron:"
        $hasSSHKey = $workflowContent -match "secrets.VPS_SSH_KEY"
        $hasDeployStep = $workflowContent -match "Deploy via SSH"
        
        if ($hasSchedule -and $hasCron -and $hasSSHKey -and $hasDeployStep) {
            Write-ColorOutput "   - Workflow file contains all required elements" "White"
            return $true
        } else {
            Write-ColorOutput "⚠️ Workflow file may be missing required elements" "Yellow"
            if (-not $hasSchedule) { Write-ColorOutput "   - Missing schedule configuration" "Yellow" }
            if (-not $hasCron) { Write-ColorOutput "   - Missing cron schedule" "Yellow" }
            if (-not $hasSSHKey) { Write-ColorOutput "   - Missing SSH key setup" "Yellow" }
            if (-not $hasDeployStep) { Write-ColorOutput "   - Missing deployment step" "Yellow" }
            return $false
        }
    } else {
        Write-ColorOutput "❌ GitHub Actions workflow file not found" "Red"
        Write-ColorOutput "   Run setup_auto_scheduling.ps1 to create the workflow file" "Yellow"
        return $false
    }
}

# Function to check Linux setup script
function Check-LinuxSetupScript {
    $scriptPath = Join-Path -Path $PSScriptRoot -ChildPath "setup_auto_scheduling.sh"
    
    if (Test-Path -Path $scriptPath) {
        Write-ColorOutput "✅ Linux setup script exists" "Green"
        
        # Check if the script contains the required elements
        $scriptContent = Get-Content -Path $scriptPath -Raw
        
        $hasCrontab = $scriptContent -match "crontab"
        $hasDeployScript = $scriptContent -match "DEPLOY_SCRIPT"
        $hasSSHKey = $scriptContent -match "SSH_KEY"
        
        if ($hasCrontab -and $hasDeployScript -and $hasSSHKey) {
            Write-ColorOutput "   - Script contains all required elements" "White"
            return $true
        } else {
            Write-ColorOutput "⚠️ Script may be missing required elements" "Yellow"
            if (-not $hasCrontab) { Write-ColorOutput "   - Missing crontab setup" "Yellow" }
            if (-not $hasDeployScript) { Write-ColorOutput "   - Missing deployment script path" "Yellow" }
            if (-not $hasSSHKey) { Write-ColorOutput "   - Missing SSH key path" "Yellow" }
            return $false
        }
    } else {
        Write-ColorOutput "❌ Linux setup script not found" "Red"
        Write-ColorOutput "   Create setup_auto_scheduling.sh to enable Linux auto-scheduling" "Yellow"
        return $false
    }
}

# Function to check deployment script
function Check-DeploymentScript {
    $psScriptPath = Join-Path -Path $PSScriptRoot -ChildPath "trae_deploy.ps1"
    $shScriptPath = Join-Path -Path $PSScriptRoot -ChildPath "trae_deploy.sh"
    
    $psExists = Test-Path -Path $psScriptPath
    $shExists = Test-Path -Path $shScriptPath
    
    if ($psExists -or $shExists) {
        Write-ColorOutput "✅ Deployment script exists" "Green"
        
        if ($shExists) {
            # Check if the script contains the auto parameter
            $scriptContent = Get-Content -Path $shScriptPath -Raw
            
            $hasAutoParam = $scriptContent -match "--auto"
            
            if ($hasAutoParam) {
                Write-ColorOutput "   - Linux script supports auto mode" "White"
            } else {
                Write-ColorOutput "⚠️ Linux script may not support auto mode" "Yellow"
                Write-ColorOutput "   - Add --auto parameter handling to trae_deploy.sh" "Yellow"
            }
        }
        
        return $true
    } else {
        Write-ColorOutput "❌ Deployment script not found" "Red"
        Write-ColorOutput "   Create trae_deploy.ps1 or trae_deploy.sh for deployment" "Yellow"
        return $false
    }
}

# Function to check documentation
function Check-Documentation {
    $docPath = Join-Path -Path $PSScriptRoot -ChildPath "AUTO_SCHEDULING.md"
    
    if (Test-Path -Path $docPath) {
        Write-ColorOutput "✅ Auto-scheduling documentation exists" "Green"
        return $true
    } else {
        Write-ColorOutput "❌ Auto-scheduling documentation not found" "Red"
        Write-ColorOutput "   Create AUTO_SCHEDULING.md to document the setup process" "Yellow"
        return $false
    }
}

# Main script execution
Show-Banner

# Check all components
$taskSchedulerOk = Check-TaskScheduler
Write-Host ""

$githubWorkflowOk = Check-GitHubWorkflow
Write-Host ""

$linuxSetupOk = Check-LinuxSetupScript
Write-Host ""

$deploymentScriptOk = Check-DeploymentScript
Write-Host ""

$documentationOk = Check-Documentation
Write-Host ""

# Summary
Write-ColorOutput "===================================================" "Cyan"
Write-ColorOutput "                VERIFICATION SUMMARY               " "Cyan"
Write-ColorOutput "===================================================" "Cyan"
Write-Host ""

$allOk = $taskSchedulerOk -and $githubWorkflowOk -and $linuxSetupOk -and $deploymentScriptOk -and $documentationOk

if ($allOk) {
    Write-ColorOutput "✅ All auto-scheduling components are properly configured!" "Green"
} else {
    Write-ColorOutput "⚠️ Some auto-scheduling components need attention" "Yellow"
    Write-ColorOutput "   Please address the issues mentioned above" "Yellow"
}

Write-Host ""
Write-ColorOutput "For more information, see AUTO_SCHEDULING.md" "Cyan"