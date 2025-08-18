#!/usr/bin/env pwsh
<#
.SYNOPSIS
    TRAE AI Trading Sentinel - Login Troubleshooter Runner
    
.DESCRIPTION
    PowerShell script to run the enhanced login troubleshooter with proper environment setup
    
.PARAMETER Username
    Bulenox username (overrides environment variable)
    
.PARAMETER Password
    Bulenox password (overrides environment variable)
    
.PARAMETER Headless
    Run in headless mode (true/false, default: false for debugging)
    
.PARAMETER VerboseLogging
    Enable verbose output
    
.EXAMPLE
    .\run_login_troubleshooter.ps1
    
.EXAMPLE
    .\run_login_troubleshooter.ps1 -Username "your_email@example.com" -Password "your_password" -Headless $false
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$Username = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Password = "",
    
    [Parameter(Mandatory=$false)]
    [bool]$Headless = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$VerboseLogging
)

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
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

# Banner
Write-ColorOutput "================================================================================" "Cyan"
Write-ColorOutput "🔧 TRAE AI Trading Sentinel - Enhanced Login Troubleshooter" "Cyan"
Write-ColorOutput "================================================================================" "Cyan"
Write-Host ""

# Check if we're in the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$troubleshooterScript = Join-Path $scriptPath "ultimate_login_troubleshooter.py"

if (-not (Test-Path $troubleshooterScript)) {
    Write-ColorOutput "❌ Error: ultimate_login_troubleshooter.py not found in current directory" "Red"
    Write-ColorOutput "   Expected path: $troubleshooterScript" "Yellow"
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

# Set headless mode
$env:BULENOX_HEADLESS = $Headless.ToString().ToLower()

# Display configuration
Write-Host ""
Write-ColorOutput "📋 Configuration:" "Blue"
Write-ColorOutput "   Username: $($env:BULENOX_USERNAME.Substring(0, [Math]::Min(3, $env:BULENOX_USERNAME.Length)))***" "White"
Write-ColorOutput "   Headless Mode: $env:BULENOX_HEADLESS" "White"
Write-ColorOutput "   Script Path: $troubleshooterScript" "White"

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

$dependencies = @("playwright", "playwright-stealth")
foreach ($dep in $dependencies) {
    try {
        $result = python -c "import $($dep.Replace('-', '_')); print('✅ $dep installed')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput $result "Green"
        } else {
            Write-ColorOutput "⚠️  $dep not installed" "Yellow"
        }
    } catch {
        Write-ColorOutput "⚠️  $dep not installed" "Yellow"
    }
}

# Install missing dependencies if needed
$installChoice = Read-Host "`nInstall missing dependencies automatically? (y/N)"
if ($installChoice -eq "y" -or $installChoice -eq "Y") {
    Write-ColorOutput "📦 Installing dependencies..." "Blue"
    python -m pip install playwright playwright-stealth --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ Dependencies installed successfully" "Green"
    } else {
        Write-ColorOutput "⚠️  Some dependencies may have failed to install" "Yellow"
    }
}

# Create debug directory
$debugDir = Join-Path $scriptPath "login_debug"
if (-not (Test-Path $debugDir)) {
    New-Item -ItemType Directory -Path $debugDir -Force | Out-Null
    Write-ColorOutput "📁 Created debug directory: $debugDir" "Blue"
}

# Run the troubleshooter
Write-Host ""
Write-ColorOutput "🚀 Starting Enhanced Login Troubleshooter..." "Green"
Write-ColorOutput "================================================================================" "Cyan"
Write-Host ""

# Set verbose mode if requested
if ($PSBoundParameters.ContainsKey('VerboseLogging')) {
    $env:PLAYWRIGHT_DEBUG = "1"
}

# Run the Python script
try {
    python $troubleshooterScript
    $exitCode = $LASTEXITCODE
} catch {
    Write-ColorOutput "❌ Failed to run troubleshooter: $_" "Red"
    $exitCode = 1
}

# Results summary
Write-Host ""
Write-ColorOutput "================================================================================" "Cyan"

if ($exitCode -eq 0) {
    Write-ColorOutput "🎉 Login Troubleshooter completed successfully!" "Green"
    Write-ColorOutput "✅ Login automation should now work properly" "Green"
} else {
    Write-ColorOutput "❌ Login Troubleshooter encountered issues" "Red"
    Write-ColorOutput "🔍 Check the debug files for detailed analysis:" "Yellow"
    Write-ColorOutput "   Debug Directory: $debugDir" "White"
    Write-ColorOutput "   Screenshots: $debugDir\screenshot_*.png" "White"
    Write-ColorOutput "   HTML Sources: $debugDir\html_*.html" "White"
    Write-ColorOutput "   Network Logs: $debugDir\network_log.json" "White"
    
    Write-Host ""
    Write-ColorOutput "💡 Common Solutions:" "Blue"
    Write-ColorOutput "   1. Verify credentials are correct" "White"
    Write-ColorOutput "   2. Check if login page structure changed" "White"
    Write-ColorOutput "   3. Review network logs for blocked requests" "White"
    Write-ColorOutput "   4. Try different domains or login URLs" "White"
    Write-ColorOutput "   5. Check for anti-bot detection in screenshots" "White"
}

Write-ColorOutput "================================================================================" "Cyan"

# Open debug directory if troubleshooting failed
if ($exitCode -ne 0) {
    $openDebug = Read-Host "`nOpen debug directory for manual inspection? (y/N)"
    if ($openDebug -eq "y" -or $openDebug -eq "Y") {
        try {
            Invoke-Item $debugDir
        } catch {
            Write-ColorOutput "Could not open debug directory automatically" "Yellow"
            Write-ColorOutput "Please navigate to: $debugDir" "White"
        }
    }
}

exit $exitCode