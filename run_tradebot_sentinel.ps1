#!/usr/bin/env pwsh
<#
.SYNOPSIS
    TradeBot Sentinel - PowerShell Runner
    
.DESCRIPTION
    PowerShell script to run the TradeBot Sentinel with proper environment setup
    
.PARAMETER Username
    Bulenox username (overrides environment variable)
    
.PARAMETER Password
    Bulenox password (overrides environment variable)
    
.PARAMETER Headless
    Run in headless mode (true/false, default: false for debugging)
    
.PARAMETER VerboseMode
    Enable verbose output
    
.EXAMPLE
    .\run_tradebot_sentinel.ps1
    
.EXAMPLE
    .\run_tradebot_sentinel.ps1 -Username "your_email@example.com" -Password "your_password" -Headless $false
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Username = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "",
    
    # Accept either boolean or string values robustly
    [Parameter(Mandatory=$false)]
    [object]$Headless = $true,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerboseMode
)

function Convert-ToBoolean {
    param(
        [Parameter(Mandatory=$false)] [object]$Value,
        [Parameter(Mandatory=$false)] [bool]$Default = $true
    )
    if ($null -eq $Value) { return $Default }
    if ($Value -is [bool]) { return [bool]$Value }
    $s = ([string]$Value).Trim().ToLower()
    switch -regex ($s) {
        '^(true|1|yes|y|on)$' { return $true }
        '^(false|0|no|n|off)$' { return $false }
        default { return $Default }
    }
}

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = "Red"
        "Green" = "Green"
        "Yellow" = "Yellow"
        "Blue" = "Blue"
        "Cyan" = "Cyan"
        "Magenta" = "Magenta"
        "White" = "White"
    }
    
    # Handle null or invalid color
    if (-not $colorMap.ContainsKey($Color)) {
        $Color = "White"
    }
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

# Banner
Write-ColorOutput "================================================================================" "Cyan"
Write-ColorOutput "🤖 TradeBot Sentinel - Expert Playwright Automation for Bulenox ProjectX" "Cyan"
Write-ColorOutput "================================================================================" "Cyan"
Write-Host ""

# Check if we're in the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$sentinelScript = Join-Path $scriptPath "tradebot_sentinel.py"

if (-not (Test-Path $sentinelScript)) {
    Write-ColorOutput "❌ Error: tradebot_sentinel.py not found in current directory" "Red"
    Write-ColorOutput "   Expected path: $sentinelScript" "Yellow"
    Write-ColorOutput "   Please run this script from the ai-trading-sentinel directory" "Yellow"
    exit 1
}

# Environment variable setup
Write-ColorOutput "🔧 Setting up environment variables..." "Blue"

# Use provided parameters or check existing environment variables
if ($Username -ne "") {
    $env:BULENOX_USERNAME = $Username
    Write-ColorOutput "✅ Username set from parameter" "Green"
} elseif ($env:BULENOX_USERNAME) {
    Write-ColorOutput "✅ Using existing BULENOX_USERNAME environment variable" "Green"
} else {
    Write-ColorOutput "❌ No username provided and BULENOX_USERNAME not set" "Red"
    $inputUsername = Read-Host "Please enter your Bulenox username/email"
    if ($inputUsername) {
        $env:BULENOX_USERNAME = $inputUsername
        Write-ColorOutput "✅ Username set interactively" "Green"
    } else {
        Write-ColorOutput "❌ Username is required" "Red"
        exit 1
    }
}

if ($Password -ne "") {
    $env:BULENOX_PASSWORD = $Password
    Write-ColorOutput "✅ Password set from parameter" "Green"
} elseif ($env:BULENOX_PASSWORD) {
    Write-ColorOutput "✅ Using existing BULENOX_PASSWORD environment variable" "Green"
} else {
    Write-ColorOutput "❌ No password provided and BULENOX_PASSWORD not set" "Red"
    $securePassword = Read-Host "Please enter your Bulenox password" -AsSecureString
    $password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword))
    if ($password) {
        $env:BULENOX_PASSWORD = $password
        Write-ColorOutput "✅ Password set interactively" "Green"
    } else {
        Write-ColorOutput "❌ Password is required" "Red"
        exit 1
    }
}

# Set headless mode using robust conversion
$resolvedHeadless = Convert-ToBoolean -Value $Headless -Default $true
$env:BULENOX_HEADLESS = $resolvedHeadless.ToString().ToLower()

# Display configuration
Write-Host ""
Write-ColorOutput "📋 Configuration:" "Blue"
Write-ColorOutput "   Username: $($env:BULENOX_USERNAME.Substring(0, [Math]::Min(3, $env:BULENOX_USERNAME.Length)))***" "White"
Write-ColorOutput "   Headless Mode: $env:BULENOX_HEADLESS" "White"
Write-ColorOutput "   Script Path: $sentinelScript" "White"

# Check Python and dependencies
Write-Host ""
Write-ColorOutput "🔍 Checking Python environment..." "Blue"

try {
    $pythonVersion = python --version 2>&1
    Write-ColorOutput "✅ Python: $pythonVersion" "Green"
} catch {
    Write-ColorOutput "❌ Python not found or not in PATH" "Red"
    Write-ColorOutput "   Please ensure Python is installed and accessible" "Yellow"
    exit 1
}

# Check if we're in a virtual environment
if ($env:VIRTUAL_ENV) {
    Write-ColorOutput "✅ Virtual environment active: $env:VIRTUAL_ENV" "Green"
} else {
    Write-ColorOutput "⚠️  No virtual environment detected" "Yellow"
    Write-ColorOutput "   Consider using: python -m venv venv; .\venv\Scripts\Activate.ps1" "Yellow"
}

# Check critical dependencies
Write-ColorOutput "🔍 Checking dependencies..." "Blue"

$dependencies = @("playwright", "playwright_stealth", "curlconverter")
$missingDeps = @()

foreach ($dep in $dependencies) {
    try {
        $checkCmd = "import $($dep.Replace('-', '_')); print('✅ $dep installed')"
        $result = python -c $checkCmd 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput $result "Green"
        } else {
            Write-ColorOutput "⚠️  $dep not installed" "Yellow"
            $missingDeps += $dep
        }
    } catch {
        Write-ColorOutput "⚠️  $dep not installed" "Yellow"
        $missingDeps += $dep
    }
}

# Auto-install missing dependencies
if ($missingDeps.Count -gt 0) {
    Write-ColorOutput "📦 Installing missing dependencies automatically..." "Blue"
    
    # Install Python packages
    foreach ($dep in $missingDeps) {
        Write-ColorOutput "   Installing $dep..." "Blue"
        python -m pip install $dep --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "   ⚠️  Failed to install $dep" "Yellow"
        } else {
            Write-ColorOutput "   ✅ $dep installed successfully" "Green"
        }
    }
    
    # Install playwright browsers if playwright was installed
    if ($missingDeps -contains "playwright") {
        Write-ColorOutput "   Installing Playwright browsers..." "Blue"
        python -m playwright install chromium --with-deps
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "   ✅ Playwright browsers installed" "Green"
        } else {
            Write-ColorOutput "   ⚠️  Browser installation may have failed" "Yellow"
        }
    }
}

# Run the TradeBot Sentinel
Write-Host ""
Write-ColorOutput "🚀 Starting TradeBot Sentinel..." "Green"
Write-ColorOutput "================================================================================" "Cyan"
Write-Host ""

# Set verbose mode if requested
if ($VerboseMode) {
    $env:PLAYWRIGHT_DEBUG = "1"
    Write-ColorOutput "🔍 Verbose mode enabled" "Blue"
}

# Run the Python script
try {
    python $sentinelScript
    $exitCode = $LASTEXITCODE
} catch {
    Write-ColorOutput "❌ Failed to run TradeBot Sentinel: $_" "Red"
    $exitCode = 1
}

# Results summary
Write-Host ""
Write-ColorOutput "================================================================================" "Cyan"

if ($exitCode -eq 0) {
    Write-ColorOutput "🎉 TradeBot Sentinel completed successfully!" "Green"
    Write-ColorOutput "📁 Check the following files:" "Green"
    Write-ColorOutput "   - trade.sh" "White"
    Write-ColorOutput "   - trade_request_full.py" "White"
    Write-ColorOutput "   - network_logs.json" "White"
    Write-ColorOutput "   - tradebot_sentinel.log" "White"
    Write-ColorOutput "   - screenshot_*.png" "White"
} else {
    Write-ColorOutput "❌ TradeBot Sentinel encountered issues" "Red"
    Write-ColorOutput "🔍 Check the following for debugging:" "Yellow"
    Write-ColorOutput "   - tradebot_sentinel.log" "White"
    Write-ColorOutput "   - screenshot_*.png" "White"
    Write-ColorOutput "   - network_logs.json" "White"
    
    Write-Host ""
    Write-ColorOutput "💡 Common Solutions:" "Blue"
    Write-ColorOutput "   1. Verify credentials are correct" "White"
    Write-ColorOutput "   2. Check if Bulenox site is accessible" "White"
    Write-ColorOutput "   3. Review screenshot files for anti-bot detection" "White"
    Write-ColorOutput "   4. Try running in non-headless mode for debugging" "White"
    Write-ColorOutput "   5. Check network logs for blocked requests" "White"
}

Write-ColorOutput "================================================================================" "Cyan"

# Open current directory if execution failed for manual inspection
if ($exitCode -ne 0) {
    $answer = Read-Host "Open current directory for manual inspection? (y/N)"
    if ($answer -match '^(y|Y)') {
        Start-Process .
    }
}

exit $exitCode