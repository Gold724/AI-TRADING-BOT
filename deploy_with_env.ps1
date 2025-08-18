# AI Trading Sentinel - Cloud Deployment with .env Configuration
# This script reads VPS credentials from .env file and deploys to cloud

param(
    [switch]$SkipConfirmation
)

# Color functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Status { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Error "❌ .env file not found!"
    Write-Host "Please create a .env file with your VPS credentials."
    exit 1
}

# Function to read .env file
function Get-EnvVariable {
    param($Name)
    $content = Get-Content ".env" -ErrorAction SilentlyContinue
    foreach ($line in $content) {
        if ($line -match "^$Name=(.*)$") {
            return $matches[1].Trim('"').Trim("'")
        }
    }
    return $null
}

# Read VPS credentials from .env
$VpsHost = Get-EnvVariable "VPS_HOST"
$VpsUser = Get-EnvVariable "VPS_USER" 
$SshKeyPath = Get-EnvVariable "SSH_KEY_PATH"
$GitRepo = Get-EnvVariable "GIT_REPO"
$Domain = Get-EnvVariable "DOMAIN"
$Email = Get-EnvVariable "EMAIL"

# Validate required credentials
$missingVars = @()
if ([string]::IsNullOrWhiteSpace($VpsHost)) { $missingVars += "VPS_HOST" }
if ([string]::IsNullOrWhiteSpace($VpsUser)) { $missingVars += "VPS_USER" }
if ([string]::IsNullOrWhiteSpace($SshKeyPath)) { $missingVars += "SSH_KEY_PATH" }
if ([string]::IsNullOrWhiteSpace($GitRepo)) { $missingVars += "GIT_REPO" }

if ($missingVars.Count -gt 0) {
    Write-Error "❌ Missing required VPS credentials in .env file:"
    foreach ($var in $missingVars) {
        Write-Host "  • $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please update your .env file with the following variables:" -ForegroundColor Yellow
    Write-Host "VPS_HOST=your.vps.ip.address" -ForegroundColor Gray
    Write-Host "VPS_USER=root" -ForegroundColor Gray
    Write-Host "SSH_KEY_PATH=C:\\path\\to\\your\\ssh\\key" -ForegroundColor Gray
    Write-Host "GIT_REPO=https://github.com/yourusername/ai-trading-sentinel.git" -ForegroundColor Gray
    Write-Host "DOMAIN=yourdomain.com (optional)" -ForegroundColor Gray
    Write-Host "EMAIL=your@email.com (optional)" -ForegroundColor Gray
    exit 1
}

# Display configuration
Write-Host "🚀 AI Trading Sentinel - Cloud Deployment" -ForegroundColor Magenta
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host ""
Write-Status "📋 Configuration from .env file:"
Write-Host "  • VPS Host: $VpsHost" -ForegroundColor White
Write-Host "  • VPS User: $VpsUser" -ForegroundColor White
Write-Host "  • SSH Key: $SshKeyPath" -ForegroundColor White
Write-Host "  • Git Repo: $GitRepo" -ForegroundColor White
if (-not [string]::IsNullOrWhiteSpace($Domain)) {
    Write-Host "  • Domain: $Domain" -ForegroundColor White
}
if (-not [string]::IsNullOrWhiteSpace($Email)) {
    Write-Host "  • Email: $Email" -ForegroundColor White
}
Write-Host ""

# Confirmation
if (-not $SkipConfirmation) {
    $confirm = Read-Host "Do you want to proceed with deployment? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Warning "Deployment cancelled by user."
        exit 0
    }
}

# Prepare deployment parameters
$deployParams = @{
    'VpsHost' = $VpsHost
    'VpsUser' = $VpsUser
    'SshKeyPath' = $SshKeyPath
    'GitRepo' = $GitRepo
}

if (-not [string]::IsNullOrWhiteSpace($Domain)) {
    $deployParams['Domain'] = $Domain
}
if (-not [string]::IsNullOrWhiteSpace($Email)) {
    $deployParams['Email'] = $Email
}
if ($SkipConfirmation) {
    $deployParams['SkipConfirmation'] = $true
}

# Execute deployment
try {
    Write-Status "🔄 Executing deployment script with .env credentials..."
    & ".\deploy_to_cloud.ps1" @deployParams
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "🎉 Deployment completed successfully!"
        Write-Host ""
        Write-Host "📋 Quick Access:" -ForegroundColor White
        Write-Host "  • SSH: ssh -i $SshKeyPath $VpsUser@$VpsHost"
        Write-Host "  • Dashboard: http://$VpsHost:3000"
        Write-Host "  • Trading Interface: http://$VpsHost:8080"
        if (-not [string]::IsNullOrWhiteSpace($Domain)) {
            Write-Host "  • Domain: https://$Domain"
        }
        Write-Host ""
        Write-Success "✅ AI Trading Sentinel is now running 24/7 in the cloud!"
    } else {
        Write-Error "❌ Deployment failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} catch {
    Write-Error "❌ Deployment failed: $($_.Exception.Message)"
    exit 1
}