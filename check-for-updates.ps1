# AI Trading Sentinel Update Checker
# This script checks for updates to the application

Write-Host "AI Trading Sentinel Update Checker" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Function to check if git is installed
function Test-GitInstalled {
    try {
        $gitVersion = git --version
        return $true
    } catch {
        return $false
    }
}

# Function to check if the directory is a git repository
function Test-GitRepository {
    param(
        [string]$Path
    )
    
    if (Test-Path -Path "$Path\.git") {
        return $true
    }
    return $false
}

# Check if git is installed
if (-not (Test-GitInstalled)) {
    Write-Host "✗ Git is not installed or not in your PATH" -ForegroundColor Red
    Write-Host "  Please install Git from https://git-scm.com/downloads" -ForegroundColor Yellow
    exit
}

# Check if the current directory is a git repository
if (-not (Test-GitRepository -Path $PSScriptRoot)) {
    Write-Host "✗ This directory is not a Git repository" -ForegroundColor Red
    Write-Host "  Updates can only be checked for Git repositories" -ForegroundColor Yellow
    exit
}

# Get the current branch
$currentBranch = git -C $PSScriptRoot rev-parse --abbrev-ref HEAD
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan

# Fetch the latest changes
Write-Host "\nFetching latest changes..." -ForegroundColor Cyan
git -C $PSScriptRoot fetch

# Check if there are any updates
$localCommit = git -C $PSScriptRoot rev-parse HEAD
$remoteCommit = git -C $PSScriptRoot rev-parse @{u}

if ($localCommit -eq $remoteCommit) {
    Write-Host "\n✓ Your application is up to date" -ForegroundColor Green
} else {
    Write-Host "\n! Updates are available" -ForegroundColor Yellow
    
    # Show the changes
    Write-Host "\nChanges since your last update:" -ForegroundColor Cyan
    git -C $PSScriptRoot log --oneline --graph --decorate --pretty=format:"%C(auto)%h%d %s %C(green)(%cr) %C(bold blue)<%an>" HEAD..@{u}
    
    # Ask if the user wants to update
    $updateNow = Read-Host "\nDo you want to update now? (y/n)"
    
    if ($updateNow -eq "y") {
        # Check if there are any running servers
        $port5000InUse = $null -ne (Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 5000 })
        $port5176InUse = $null -ne (Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 5176 })
        
        if ($port5000InUse -or $port5176InUse) {
            Write-Host "\n! Servers are currently running" -ForegroundColor Yellow
            Write-Host "  Please stop the servers before updating" -ForegroundColor Yellow
            $stopServers = Read-Host "Do you want to stop the servers now? (y/n)"
            
            if ($stopServers -eq "y") {
                # Stop processes using ports 5000 and 5176
                if ($port5000InUse) {
                    $processId = (Get-NetTCPConnection -LocalPort 5000 -State Listen).OwningProcess
                    if ($processId) {
                        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                        if ($process) {
                            Write-Host "Stopping process $($process.ProcessName) (PID: $processId) using port 5000" -ForegroundColor Yellow
                            Stop-Process -Id $processId -Force
                        }
                    }
                }
                
                if ($port5176InUse) {
                    $processId = (Get-NetTCPConnection -LocalPort 5176 -State Listen).OwningProcess
                    if ($processId) {
                        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                        if ($process) {
                            Write-Host "Stopping process $($process.ProcessName) (PID: $processId) using port 5176" -ForegroundColor Yellow
                            Stop-Process -Id $processId -Force
                        }
                    }
                }
                
                # Wait for processes to stop
                Start-Sleep -Seconds 2
            } else {
                Write-Host "Update cancelled. Please stop the servers and try again." -ForegroundColor Yellow
                exit
            }
        }
        
        # Pull the latest changes
        Write-Host "\nUpdating..." -ForegroundColor Cyan
        git -C $PSScriptRoot pull
        
        # Check if npm packages need to be updated
        Write-Host "\nChecking for package updates..." -ForegroundColor Cyan
        if (Test-Path -Path "$PSScriptRoot\frontend\package.json") {
            $updatePackages = Read-Host "Do you want to update npm packages? (y/n)"
            
            if ($updatePackages -eq "y") {
                Write-Host "Updating npm packages..." -ForegroundColor Cyan
                Set-Location -Path "$PSScriptRoot\frontend"
                npm install
                Set-Location -Path $PSScriptRoot
            }
        }
        
        # Check if Python packages need to be updated
        if (Test-Path -Path "$PSScriptRoot\backend\requirements.txt") {
            $updatePythonPackages = Read-Host "Do you want to update Python packages? (y/n)"
            
            if ($updatePythonPackages -eq "y") {
                Write-Host "Updating Python packages..." -ForegroundColor Cyan
                pip install -r "$PSScriptRoot\backend\requirements.txt" --upgrade
            }
        }
        
        Write-Host "\n✓ Update completed successfully" -ForegroundColor Green
        
        # Ask if the user wants to restart the servers
        $restartServers = Read-Host "Do you want to restart the servers now? (y/n)"
        
        if ($restartServers -eq "y") {
            & "$PSScriptRoot\start-servers.ps1"
        }
    } else {
        Write-Host "Update cancelled. You can update later by running this script again." -ForegroundColor Yellow
    }
}