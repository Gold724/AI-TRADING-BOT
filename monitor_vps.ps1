#!/usr/bin/env pwsh
<#
.SYNOPSIS
    VPS Monitoring Script for AI Trading Sentinel
    
.DESCRIPTION
    Monitors the Contabo VPS deployment status, bot installation, and system health.
    Provides comprehensive reporting and Slack notifications.
    
.PARAMETER Host
    VPS IP address or hostname
    
.PARAMETER User
    SSH username (default: root)
    
.PARAMETER KeyPath
    Path to SSH private key (default: ./trae_deploy_key)
    
.PARAMETER Verbose
    Enable verbose output
    
.EXAMPLE
    .\monitor_vps.ps1 -Host "your-vps-ip" -Verbose
    
.EXAMPLE
    .\monitor_vps.ps1 -Host "192.168.1.100" -User "ubuntu" -KeyPath "./my_key"
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Host = $env:VPS_HOST,
    
    [Parameter(Mandatory=$false)]
    [string]$User = $env:VPS_USER,
    
    [Parameter(Mandatory=$false)]
    [string]$KeyPath = $env:SSH_KEY_PATH,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-Prerequisites {
    Write-ColorOutput "🔍 Checking prerequisites..." "Info"
    
    # Check if Python is available
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "✅ Python: $pythonVersion" "Success"
    }
    catch {
        Write-ColorOutput "❌ Python not found. Please install Python 3.7+" "Error"
        return $false
    }
    
    # Check if required Python packages are available
    $requiredPackages = @("requests")
    foreach ($package in $requiredPackages) {
        try {
            $result = pip show $package 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Python package '$package': Installed" "Success"
            } else {
                Write-ColorOutput "⚠️ Python package '$package': Not found, installing..." "Warning"
                pip install $package
                if ($LASTEXITCODE -ne 0) {
                    Write-ColorOutput "❌ Failed to install '$package'" "Error"
                    return $false
                }
            }
        }
        catch {
            Write-ColorOutput "❌ Error checking package '$package': $_" "Error"
            return $false
        }
    }
    
    # Check if SSH key exists
    if ($KeyPath -and (Test-Path $KeyPath)) {
        Write-ColorOutput "✅ SSH Key: Found at $KeyPath" "Success"
    } elseif (Test-Path "./trae_deploy_key") {
        $KeyPath = "./trae_deploy_key"
        Write-ColorOutput "✅ SSH Key: Found at $KeyPath" "Success"
    } else {
        Write-ColorOutput "⚠️ SSH Key: Not found, will prompt for password" "Warning"
    }
    
    return $true
}

function Set-EnvironmentVariables {
    param(
        [string]$VpsHost,
        [string]$VpsUser,
        [string]$SshKeyPath
    )
    
    Write-ColorOutput "🔧 Setting environment variables..." "Info"
    
    # Set VPS_HOST
    if ($VpsHost) {
        $env:VPS_HOST = $VpsHost
        Write-ColorOutput "✅ VPS_HOST: $VpsHost" "Success"
    } elseif (-not $env:VPS_HOST) {
        $VpsHost = Read-Host "Enter VPS IP address or hostname"
        $env:VPS_HOST = $VpsHost
    }
    
    # Set VPS_USER
    if ($VpsUser) {
        $env:VPS_USER = $VpsUser
    } elseif (-not $env:VPS_USER) {
        $env:VPS_USER = "root"
    }
    Write-ColorOutput "✅ VPS_USER: $($env:VPS_USER)" "Success"
    
    # Set SSH_KEY_PATH
    if ($SshKeyPath -and (Test-Path $SshKeyPath)) {
        $env:SSH_KEY_PATH = $SshKeyPath
        Write-ColorOutput "✅ SSH_KEY_PATH: $SshKeyPath" "Success"
    } elseif (Test-Path "./trae_deploy_key") {
        $env:SSH_KEY_PATH = "./trae_deploy_key"
        Write-ColorOutput "✅ SSH_KEY_PATH: ./trae_deploy_key" "Success"
    }
    
    # Set SLACK_WEBHOOK_URL if available
    if ($env:SLACK_WEBHOOK_URL) {
        Write-ColorOutput "✅ SLACK_WEBHOOK_URL: Configured" "Success"
    } else {
        Write-ColorOutput "⚠️ SLACK_WEBHOOK_URL: Not set (notifications disabled)" "Warning"
    }
}

function Invoke-VPSMonitoring {
    Write-ColorOutput "🚀 Starting VPS monitoring..." "Header"
    Write-ColorOutput "Target: $($env:VPS_USER)@$($env:VPS_HOST)" "Info"
    Write-ColorOutput ("-" * 60) "Info"
    
    try {
        # Run the Python monitoring script
        if ($Verbose) {
            python vps_monitor.py
        } else {
            python vps_monitor.py 2>&1 | Where-Object { $_ -notmatch "^\s*$" }
        }
        
        $exitCode = $LASTEXITCODE
        
        switch ($exitCode) {
            0 {
                Write-ColorOutput "\n✅ VPS monitoring completed successfully!" "Success"
                Write-ColorOutput "All systems are operational." "Success"
            }
            1 {
                Write-ColorOutput "\n❌ VPS monitoring detected critical errors!" "Error"
                Write-ColorOutput "Please check the detailed report above." "Error"
            }
            2 {
                Write-ColorOutput "\n⚠️ VPS monitoring detected warnings!" "Warning"
                Write-ColorOutput "Some issues require attention." "Warning"
            }
            130 {
                Write-ColorOutput "\n⚠️ Monitoring interrupted by user." "Warning"
            }
            default {
                Write-ColorOutput "\n❌ Monitoring failed with exit code: $exitCode" "Error"
            }
        }
        
        return $exitCode
    }
    catch {
        Write-ColorOutput "\n❌ Failed to run VPS monitoring: $_" "Error"
        return 1
    }
}

function Show-MonitoringResults {
    Write-ColorOutput "\nChecking for monitoring results..." "Info"
    
    # Find the most recent monitoring result file
    $resultFiles = Get-ChildItem -Path "." -Name "vps_monitor_*.json" | Sort-Object Name -Descending
    
    if ($resultFiles.Count -gt 0) {
        $latestFile = $resultFiles[0]
        Write-ColorOutput "Latest results: $latestFile" "Success"
        
        try {
            $results = Get-Content $latestFile | ConvertFrom-Json
            
            Write-ColorOutput "\nSUMMARY" "Header"
            Write-ColorOutput "Timestamp: $($results.timestamp)" "Info"
            Write-ColorOutput "Status: $($results.status.ToUpper())" "Info"
            Write-ColorOutput "Summary: $($results.summary)" "Info"
            
            if ($Verbose -and $results.connectivity) {
                Write-ColorOutput "\nDETAILED RESULTS" "Header"
                
                Write-ColorOutput "\nInstallation Checks:" "Info"
                foreach ($check in $results.installation.PSObject.Properties) {
                    $status = if ($check.Value.success) { "OK" } else { "FAIL" }
                    Write-ColorOutput "  $status $($check.Name)" "Info"
                }
                
                Write-ColorOutput "\nHealth Checks:" "Info"
                foreach ($check in $results.health.PSObject.Properties) {
                    $status = if ($check.Value.success) { "OK" } else { "FAIL" }
                    Write-ColorOutput "  $status $($check.Name)" "Info"
                }
            }
        }
        catch {
            Write-ColorOutput "Could not parse results file: $_" "Warning"
        }
    } else {
        Write-ColorOutput "No monitoring result files found." "Warning"
    }
}

function Main {
    try {
        Write-ColorOutput "🤖 AI Trading Sentinel - VPS Monitor" "Header"
        Write-ColorOutput "TRAE-SentinelOps Deployment Monitoring" "Header"
        Write-ColorOutput ("=" * 60) "Header"
        
        # Check prerequisites
        if (-not (Test-Prerequisites)) {
            Write-ColorOutput "❌ Prerequisites check failed. Exiting." "Error"
            exit 1
        }
        
        # Set environment variables
        Set-EnvironmentVariables -VpsHost $Host -VpsUser $User -SshKeyPath $KeyPath
        
        # Validate required variables
        if (-not $env:VPS_HOST) {
            Write-ColorOutput "❌ VPS_HOST is required. Use -Host parameter or set VPS_HOST environment variable." "Error"
            exit 1
        }
        
        # Run monitoring
        $exitCode = Invoke-VPSMonitoring
        
        # Show results
        Show-MonitoringResults
        
        Write-ColorOutput "\n🏁 VPS monitoring completed." "Header"
        exit $exitCode
        
    }
    catch {
        Write-ColorOutput "\nUnexpected error: $_" "Error"
        Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" "Error"
        exit 1
    }
}

# Run main function
Main