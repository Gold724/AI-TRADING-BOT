# AI Trading Sentinel Launcher with Auto-Update Support
# This script launches the AI Trading Sentinel with support for automatic GitHub updates

Write-Host "AI Trading Sentinel Launcher" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path "logs")) {
    New-Item -Path "logs" -ItemType Directory | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Using Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in your PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check if the .env file exists
if (-not (Test-Path -Path ".env")) {
    Write-Host "No .env file found. Running heartbeat.py to create a default one..." -ForegroundColor Yellow
    python -c "import heartbeat; print('Default .env file created')" | Out-Null
    
    if (Test-Path -Path ".env") {
        Write-Host "Default .env file created. Please edit it with your settings before continuing." -ForegroundColor Green
        Write-Host "Press any key to open the .env file for editing..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        notepad .env
        
        Write-Host "\nAfter saving your changes, press any key to continue..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } else {
        Write-Host "Failed to create .env file" -ForegroundColor Red
        exit 1
    }
}

# Check if GitHub integration is configured
$envContent = Get-Content -Path ".env" -Raw
if ($envContent -match "GITHUB_USERNAME=your-username") {
    Write-Host "\nGitHub integration is not configured in your .env file" -ForegroundColor Yellow
    $configureGitHub = Read-Host "Do you want to configure GitHub integration now? (y/n)"
    
    if ($configureGitHub -eq "y") {
        $githubUsername = Read-Host "Enter your GitHub username"
        $githubPat = Read-Host "Enter your GitHub Personal Access Token"
        $githubRepo = Read-Host "Enter your GitHub repository name (default: ai-trading-sentinel)"
        
        if ([string]::IsNullOrEmpty($githubRepo)) {
            $githubRepo = "ai-trading-sentinel"
        }
        
        # Update the .env file
        $envContent = $envContent -replace "GITHUB_USERNAME=your-username", "GITHUB_USERNAME=$githubUsername"
        $envContent = $envContent -replace "GITHUB_PAT=your-personal-access-token", "GITHUB_PAT=$githubPat"
        $envContent = $envContent -replace "GITHUB_REPO=ai-trading-sentinel", "GITHUB_REPO=$githubRepo"
        
        # Ask about auto-update
        $autoUpdate = Read-Host "Enable automatic GitHub updates? (y/n)"
        if ($autoUpdate -eq "y") {
            $envContent = $envContent -replace "AUTO_UPDATE_GITHUB=false", "AUTO_UPDATE_GITHUB=true"
            
            # Ask about auto-restart
            $autoRestart = Read-Host "Enable automatic restart after updates? (y/n)"
            if ($autoRestart -eq "y") {
                $envContent = $envContent -replace "RESTART_AFTER_UPDATE=false", "RESTART_AFTER_UPDATE=true"
            }
        }
        
        # Save the updated .env file
        $envContent | Set-Content -Path ".env"
        Write-Host "GitHub integration configured successfully" -ForegroundColor Green
    }
}

# Ask about debug mode
$debugMode = Read-Host "\nEnable debug mode? (y/n)"
$debugArg = ""
if ($debugMode -eq "y") {
    $debugArg = "--debug"
    Write-Host "Debug mode enabled" -ForegroundColor Yellow
}

# Start the sentinel with auto-update support
Write-Host "\nStarting AI Trading Sentinel with auto-update support..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the sentinel\n" -ForegroundColor Yellow

try {
    python start_sentinel_with_autoupdate.py $debugArg
} catch {
    Write-Host "\nError starting the sentinel: $_" -ForegroundColor Red
}