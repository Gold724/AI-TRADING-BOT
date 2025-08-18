<#
.SYNOPSIS
    TradeBot Sentinel - Environment Configuration Helper

.DESCRIPTION
    Interactive script to help configure the .env file with trading credentials
    and system settings for TradeBot Sentinel on Windows.

.PARAMETER Interactive
    Run in interactive mode to configure settings step by step

.PARAMETER Template
    Create a basic .env template with default values

.PARAMETER Validate
    Validate existing .env file configuration

.EXAMPLE
    .\configure-env.ps1 -Interactive
    Run interactive configuration wizard

.EXAMPLE
    .\configure-env.ps1 -Template
    Create basic .env template

.EXAMPLE
    .\configure-env.ps1 -Validate
    Validate existing configuration
#>

param(
    [switch]$Interactive,
    [switch]$Template,
    [switch]$Validate,
    [switch]$Help
)

# Configuration
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExampleFile = Join-Path $ProjectRoot ".env.example"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

# Show help
function Show-Help {
    Write-Host @"
🔧 TradeBot Sentinel - Environment Configuration Helper

Usage:
    .\configure-env.ps1 [OPTIONS]

Options:
    -Interactive    Run interactive configuration wizard
    -Template      Create basic .env template with defaults
    -Validate      Validate existing .env configuration
    -Help          Show this help message

Examples:
    .\configure-env.ps1 -Interactive
    .\configure-env.ps1 -Template
    .\configure-env.ps1 -Validate

Configuration File Location:
    $EnvFile

"@
}

# Create template .env file
function New-EnvTemplate {
    Write-Log "Creating .env template..." "INFO"
    
    if (Test-Path $EnvFile) {
        $overwrite = Read-Host ".env file already exists. Overwrite? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Log "Template creation cancelled." "WARNING"
            return
        }
    }
    
    $template = @"
# TradeBot Sentinel - Windows Configuration
# Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# =============================================================================
# TRADING PLATFORM CREDENTIALS (REQUIRED)
# =============================================================================
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here

# =============================================================================
# AUTOMATION SETTINGS
# =============================================================================
# Auto-execute detected trades (true/false)
AUTO_EXECUTE=false

# Run in simulation mode (true/false)
SIMULATION=true

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================
# Run browser in headless mode (true/false)
HEADLESS=true

# Browser timeout settings (milliseconds)
PAGE_TIMEOUT=30000
MAX_RETRIES=3
RETRY_DELAY=2000

# =============================================================================
# API CONFIGURATION
# =============================================================================
API_HOST=localhost
API_PORT=8000
SECRET_KEY=change_this_secret_key_in_production

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL=INFO
LOG_FILE=logs/tradebot.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# =============================================================================
# NOTIFICATION SETTINGS (OPTIONAL)
# =============================================================================
# Telegram Bot Integration
# TELEGRAM_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id

# Email Notifications
# EMAIL_SMTP_SERVER=smtp.gmail.com
# EMAIL_SMTP_PORT=587
# EMAIL_USERNAME=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password
# EMAIL_TO=alerts@yourdomain.com

# =============================================================================
# WINDOWS SPECIFIC SETTINGS
# =============================================================================
# Service configuration
SERVICE_NAME=TradeBotSentinel
SERVICE_DISPLAY_NAME=TradeBot Sentinel Service
SERVICE_DESCRIPTION=Automated Trading Bot for Windows

# Performance settings
WORKER_PROCESSES=1
WORKER_THREADS=2
MEMORY_LIMIT_MB=512

"@
    
    try {
        $template | Out-File -FilePath $EnvFile -Encoding UTF8
        Write-Log "Template created successfully: $EnvFile" "SUCCESS"
        Write-Log "Please edit the file and update your credentials." "INFO"
        
        # Offer to open in notepad
        $openFile = Read-Host "Open .env file in Notepad for editing? (Y/n)"
        if ($openFile -ne "n" -and $openFile -ne "N") {
            Start-Process notepad.exe $EnvFile
        }
    }
    catch {
        Write-Log "Failed to create template: $($_.Exception.Message)" "ERROR"
    }
}

# Interactive configuration
function Start-InteractiveConfig {
    Write-Host @"
🔧 TradeBot Sentinel - Interactive Configuration

This wizard will help you configure TradeBot Sentinel for Windows.
Press Ctrl+C at any time to cancel.

"@
    
    # Check if .env exists
    if (Test-Path $EnvFile) {
        $overwrite = Read-Host ".env file already exists. Overwrite? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Log "Configuration cancelled." "WARNING"
            return
        }
    }
    
    # Collect configuration
    $config = @{}
    
    Write-Host "`n=== Trading Platform Credentials ===" -ForegroundColor Cyan
    $config.BULENOX_USERNAME = Read-Host "Enter your trading platform username"
    $config.BULENOX_PASSWORD = Read-Host "Enter your trading platform password" -AsSecureString
    $config.BULENOX_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($config.BULENOX_PASSWORD))
    
    Write-Host "`n=== Automation Settings ===" -ForegroundColor Cyan
    $autoExecute = Read-Host "Auto-execute trades? (y/N)"
    $config.AUTO_EXECUTE = if ($autoExecute -eq "y" -or $autoExecute -eq "Y") { "true" } else { "false" }
    
    $simulation = Read-Host "Run in simulation mode? (Y/n)"
    $config.SIMULATION = if ($simulation -eq "n" -or $simulation -eq "N") { "false" } else { "true" }
    
    Write-Host "`n=== Browser Settings ===" -ForegroundColor Cyan
    $headless = Read-Host "Run browser in headless mode? (Y/n)"
    $config.HEADLESS = if ($headless -eq "n" -or $headless -eq "N") { "false" } else { "true" }
    
    Write-Host "`n=== API Configuration ===" -ForegroundColor Cyan
    $apiPort = Read-Host "API port (default: 8000)"
    $config.API_PORT = if ([string]::IsNullOrWhiteSpace($apiPort)) { "8000" } else { $apiPort }
    
    Write-Host "`n=== Notifications (Optional) ===" -ForegroundColor Cyan
    $setupNotifications = Read-Host "Setup Telegram notifications? (y/N)"
    if ($setupNotifications -eq "y" -or $setupNotifications -eq "Y") {
        $config.TELEGRAM_TOKEN = Read-Host "Telegram Bot Token"
        $config.TELEGRAM_CHAT_ID = Read-Host "Telegram Chat ID"
    }
    
    # Generate .env content
    $envContent = @"
# TradeBot Sentinel - Windows Configuration
# Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Trading Platform Credentials
BULENOX_USERNAME=$($config.BULENOX_USERNAME)
BULENOX_PASSWORD=$($config.BULENOX_PASSWORD)

# Automation Settings
AUTO_EXECUTE=$($config.AUTO_EXECUTE)
SIMULATION=$($config.SIMULATION)

# Browser Configuration
HEADLESS=$($config.HEADLESS)
PAGE_TIMEOUT=30000
MAX_RETRIES=3
RETRY_DELAY=2000

# API Configuration
API_HOST=localhost
API_PORT=$($config.API_PORT)
SECRET_KEY=$(([System.Web.Security.Membership]::GeneratePassword(32, 8)))

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/tradebot.log

"@
    
    # Add notifications if configured
    if ($config.TELEGRAM_TOKEN) {
        $envContent += @"

# Telegram Notifications
TELEGRAM_TOKEN=$($config.TELEGRAM_TOKEN)
TELEGRAM_CHAT_ID=$($config.TELEGRAM_CHAT_ID)

"@
    }
    
    # Add Windows-specific settings
    $envContent += @"

# Windows Service Configuration
SERVICE_NAME=TradeBotSentinel
SERVICE_DISPLAY_NAME=TradeBot Sentinel Service
WORKER_PROCESSES=1
MEMORY_LIMIT_MB=512
"@
    
    try {
        $envContent | Out-File -FilePath $EnvFile -Encoding UTF8
        Write-Log "Configuration saved successfully!" "SUCCESS"
        Write-Log "File location: $EnvFile" "INFO"
        
        # Set secure permissions
        $acl = Get-Acl $EnvFile
        $acl.SetAccessRuleProtection($true, $false)
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule($env:USERNAME, "FullControl", "Allow")
        $acl.SetAccessRule($accessRule)
        Set-Acl $EnvFile $acl
        
        Write-Log "Secure permissions applied to .env file." "SUCCESS"
        
        # Offer to run verification
        $runVerify = Read-Host "Run deployment verification now? (Y/n)"
        if ($runVerify -ne "n" -and $runVerify -ne "N") {
            & "$PSScriptRoot\verify-windows-deployment.ps1"
        }
    }
    catch {
        Write-Log "Failed to save configuration: $($_.Exception.Message)" "ERROR"
    }
}

# Validate existing configuration
function Test-EnvConfiguration {
    Write-Log "Validating .env configuration..." "INFO"
    
    if (-not (Test-Path $EnvFile)) {
        Write-Log ".env file not found: $EnvFile" "ERROR"
        Write-Log "Run with -Template or -Interactive to create one." "INFO"
        return $false
    }
    
    $envContent = Get-Content $EnvFile -Raw
    $issues = @()
    $warnings = @()
    
    # Required settings
    $requiredSettings = @(
        "BULENOX_USERNAME",
        "BULENOX_PASSWORD",
        "API_PORT",
        "LOG_LEVEL"
    )
    
    foreach ($setting in $requiredSettings) {
        if ($envContent -notmatch "^$setting=.+$") {
            $issues += "Missing required setting: $setting"
        }
    }
    
    # Check for default/placeholder values
    $placeholders = @(
        @{"Setting" = "BULENOX_USERNAME"; "Value" = "your_username_here"},
        @{"Setting" = "BULENOX_PASSWORD"; "Value" = "your_password_here"},
        @{"Setting" = "SECRET_KEY"; "Value" = "change_this_secret_key_in_production"}
    )
    
    foreach ($placeholder in $placeholders) {
        if ($envContent -match "^$($placeholder.Setting)=$($placeholder.Value)$") {
            $warnings += "Placeholder value detected for $($placeholder.Setting)"
        }
    }
    
    # Check file permissions
    try {
        $acl = Get-Acl $EnvFile
        $accessRules = $acl.Access | Where-Object { $_.IdentityReference -like "*Users*" -or $_.IdentityReference -like "*Everyone*" }
        if ($accessRules) {
            $warnings += "File permissions may be too permissive (accessible by Users/Everyone)"
        }
    }
    catch {
        $warnings += "Could not check file permissions"
    }
    
    # Report results
    if ($issues.Count -eq 0) {
        Write-Log "Configuration validation passed!" "SUCCESS"
    } else {
        Write-Log "Configuration validation failed:" "ERROR"
        foreach ($issue in $issues) {
            Write-Log "  - $issue" "ERROR"
        }
    }
    
    if ($warnings.Count -gt 0) {
        Write-Log "Configuration warnings:" "WARNING"
        foreach ($warning in $warnings) {
            Write-Log "  - $warning" "WARNING"
        }
    }
    
    return ($issues.Count -eq 0)
}

# Main execution
if ($Help -or (-not $Interactive -and -not $Template -and -not $Validate)) {
    Show-Help
    exit 0
}

if ($Template) {
    New-EnvTemplate
}

if ($Interactive) {
    Start-InteractiveConfig
}

if ($Validate) {
    $isValid = Test-EnvConfiguration
    exit $(if ($isValid) { 0 } else { 1 })
}