# GitHub Secrets Setup Script for AI Trading Sentinel
# This script helps configure all required GitHub Secrets for deployment

Write-Host "=== AI Trading Sentinel - GitHub Secrets Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is installed
if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI (gh) is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "winget install GitHub.cli" -ForegroundColor Yellow
    Write-Host "Then run 'gh auth login' to authenticate" -ForegroundColor Yellow
    exit 1
}

# Check if user is authenticated
try {
    $authStatus = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Please authenticate with GitHub first:" -ForegroundColor Red
        Write-Host "gh auth login" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "Please authenticate with GitHub first:" -ForegroundColor Red
    Write-Host "gh auth login" -ForegroundColor Yellow
    exit 1
}

Write-Host "GitHub CLI authenticated successfully" -ForegroundColor Green
Write-Host ""

# Get repository information
$repoInfo = gh repo view --json owner,name | ConvertFrom-Json
$owner = $repoInfo.owner.login
$repo = $repoInfo.name

Write-Host "Repository: $owner/$repo" -ForegroundColor Cyan
Write-Host ""

# Function to set GitHub secret
function Set-GitHubSecret {
    param(
        [string]$SecretName,
        [string]$SecretValue,
        [string]$Description = ""
    )
    
    try {
        Write-Host "Setting secret: $SecretName" -ForegroundColor Yellow
        echo $SecretValue | gh secret set $SecretName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Success: $SecretName set" -ForegroundColor Green
        } else {
            Write-Host "  Failed: Could not set $SecretName" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Read SSH private key
$sshKeyPath = "./deploy_key"
if (Test-Path $sshKeyPath) {
    $sshPrivateKey = Get-Content $sshKeyPath -Raw
    Write-Host "SSH private key found: $sshKeyPath" -ForegroundColor Green
} else {
    Write-Host "SSH private key not found at: $sshKeyPath" -ForegroundColor Red
    Write-Host "Please run the SSH key generation script first" -ForegroundColor Yellow
    exit 1
}

# Read SSH public key for display
$sshPubKeyPath = "./deploy_key.pub"
if (Test-Path $sshPubKeyPath) {
    $sshPublicKey = Get-Content $sshPubKeyPath -Raw
    Write-Host "SSH public key found: $sshPubKeyPath" -ForegroundColor Green
} else {
    Write-Host "SSH public key not found at: $sshPubKeyPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Setting GitHub Secrets ===" -ForegroundColor Cyan
Write-Host ""

# Set SSH-related secrets
Set-GitHubSecret -SecretName "CONTABO_SSH_PRIVATE_KEY" -SecretValue $sshPrivateKey -Description "SSH private key for VPS deployment"
Set-GitHubSecret -SecretName "CONTABO_VPS_HOST" -SecretValue "161.97.112.146" -Description "VPS IP address"
Set-GitHubSecret -SecretName "CONTABO_VPS_USER" -SecretValue "root" -Description "VPS username"

# Prompt for broker credentials
Write-Host ""
Write-Host "=== Broker Credentials ===" -ForegroundColor Cyan
$bulenoxUsername = Read-Host "Enter Bulenox Username"
$bulenoxPassword = Read-Host "Enter Bulenox Password" -AsSecureString
$bulenoxPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($bulenoxPassword))

Set-GitHubSecret -SecretName "BULENOX_USERNAME" -SecretValue $bulenoxUsername -Description "Bulenox broker username"
Set-GitHubSecret -SecretName "BULENOX_PASSWORD" -SecretValue $bulenoxPasswordPlain -Description "Bulenox broker password"

# Prompt for Slack webhook
Write-Host ""
Write-Host "=== Slack Integration ===" -ForegroundColor Cyan
Write-Host "Please provide your Slack webhook URL for notifications:"
Write-Host "(Get it from: https://api.slack.com/apps -> Your App -> Incoming Webhooks)" -ForegroundColor Gray
$slackWebhook = Read-Host "Slack Webhook URL"

if ($slackWebhook -and $slackWebhook.StartsWith("https://hooks.slack.com/")) {
    Set-GitHubSecret -SecretName "SLACK_WEBHOOK_URL" -SecretValue $slackWebhook -Description "Slack webhook for deployment notifications"
} else {
    Write-Host "Invalid Slack webhook URL. Skipping..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== GitHub Secrets Configuration Complete ===" -ForegroundColor Green
Write-Host ""

# Display current secrets (names only)
Write-Host "Current repository secrets:" -ForegroundColor Cyan
try {
    gh secret list
} catch {
    Write-Host "Could not list secrets" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== VPS Setup Instructions ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps to complete the setup:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Add SSH public key to VPS:" -ForegroundColor White
Write-Host "   ssh root@161.97.112.146" -ForegroundColor Gray
Write-Host "   mkdir -p ~/.ssh" -ForegroundColor Gray
Write-Host "   echo '$($sshPublicKey.Trim())' >> ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host "   chmod 600 ~/.ssh/authorized_keys" -ForegroundColor Gray
Write-Host "   chmod 700 ~/.ssh" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test SSH connection:" -ForegroundColor White
Write-Host "   ssh -i deploy_key root@161.97.112.146" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Update GitHub workflow:" -ForegroundColor White
Write-Host "   Copy COMPLETE_DEPLOYMENT_FIX.yml to .github/workflows/" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test deployment:" -ForegroundColor White
Write-Host "   git add . && git commit -m 'Fix deployment' && git push" -ForegroundColor Gray
Write-Host ""

# Create quick reference file
$quickRef = @"
# AI Trading Sentinel - Quick Reference

## GitHub Secrets Configured:
- CONTABO_SSH_PRIVATE_KEY: SSH private key for VPS access
- CONTABO_VPS_HOST: 161.97.112.146
- CONTABO_VPS_USER: root
- BULENOX_USERNAME: Broker username
- BULENOX_PASSWORD: Broker password
- SLACK_WEBHOOK_URL: Slack notifications

## SSH Public Key (add to VPS):
$($sshPublicKey.Trim())

## VPS Setup Commands:
```bash
ssh root@161.97.112.146
mkdir -p ~/.ssh
echo '$($sshPublicKey.Trim())' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

## Test SSH Connection:
```bash
ssh -i deploy_key root@161.97.112.146
```

## Deploy Workflow:
1. Copy COMPLETE_DEPLOYMENT_FIX.yml to .github/workflows/
2. Commit and push changes
3. Monitor GitHub Actions for deployment status

## Emergency Commands:
```bash
# Check service status
ssh root@161.97.112.146 'sudo systemctl status trae-trading-bot'

# View logs
ssh root@161.97.112.146 'sudo journalctl -u trae-trading-bot -f'

# Restart service
ssh root@161.97.112.146 'sudo systemctl restart trae-trading-bot'
```

Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@

$quickRef | Out-File -FilePath "DEPLOYMENT_QUICK_REFERENCE.md" -Encoding UTF8
Write-Host "Quick reference saved to: DEPLOYMENT_QUICK_REFERENCE.md" -ForegroundColor Green
Write-Host ""
Write-Host "Setup completed! Check the quick reference file for next steps." -ForegroundColor Green