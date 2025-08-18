# Simple deployment script that reads from .env file
param([switch]$SkipConfirmation)

# Read .env file
function Get-EnvVar($name) {
    if (Test-Path ".env") {
        $content = Get-Content ".env"
        foreach ($line in $content) {
            if ($line -match "^$name=(.*)$") {
                return $matches[1].Trim('"').Trim("'")
            }
        }
    }
    return $null
}

# Get credentials
$vpsHost = Get-EnvVar "VPS_HOST"
$vpsUser = Get-EnvVar "VPS_USER"
$sshKey = Get-EnvVar "SSH_KEY_PATH"
$gitRepo = Get-EnvVar "GIT_REPO"
$domain = Get-EnvVar "DOMAIN"
$email = Get-EnvVar "EMAIL"

# Check required values
if (-not $vpsHost -or -not $vpsUser -or -not $sshKey -or -not $gitRepo) {
    Write-Host "Missing required VPS credentials in .env file:" -ForegroundColor Red
    Write-Host "Required: VPS_HOST, VPS_USER, SSH_KEY_PATH, GIT_REPO" -ForegroundColor Yellow
    exit 1
}

# Display config
Write-Host "AI Trading Sentinel - Cloud Deployment" -ForegroundColor Cyan
Write-Host "VPS Host: $vpsHost" -ForegroundColor White
Write-Host "VPS User: $vpsUser" -ForegroundColor White
Write-Host "Git Repo: $gitRepo" -ForegroundColor White

# Confirm
if (-not $SkipConfirmation) {
    $confirm = Read-Host "Deploy to cloud? (y/N)"
    if ($confirm -ne 'y') {
        Write-Host "Cancelled" -ForegroundColor Yellow
        exit 0
    }
}

# Build parameters
$params = @("-VpsHost", $vpsHost, "-VpsUser", $vpsUser, "-SshKeyPath", $sshKey, "-GitRepo", $gitRepo)
if ($domain) { $params += @("-Domain", $domain) }
if ($email) { $params += @("-Email", $email) }
if ($SkipConfirmation) { $params += "-SkipConfirmation" }

# Execute
Write-Host "Starting deployment..." -ForegroundColor Cyan
& ".\deploy_to_cloud.ps1" @params

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Deployment failed with exit code $LASTEXITCODE" -ForegroundColor Red
}