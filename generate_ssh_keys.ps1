# Generate SSH Keys for AI Trading Sentinel Deployment
# PowerShell script to create SSH key pair and setup deployment

Write-Host "Generating SSH Key Pair for AI Trading Sentinel Deployment" -ForegroundColor Green

# Create .ssh directory if it doesn't exist
$sshDir = "$env:USERPROFILE\.ssh"
if (!(Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force
    Write-Host "Created .ssh directory: $sshDir" -ForegroundColor Yellow
}

# Generate SSH key pair
$keyPath = "$sshDir\trae_deploy_key"
$publicKeyPath = "$keyPath.pub"

Write-Host "Generating RSA 4096-bit key pair..." -ForegroundColor Cyan

# Use ssh-keygen to generate key pair
try {
    & ssh-keygen -t rsa -b 4096 -f $keyPath -N '""' -C "trae-deployment-key"
    Write-Host "SSH key pair generated successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to generate SSH key pair: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Check if files were created
if ((Test-Path $keyPath) -and (Test-Path $publicKeyPath)) {
    Write-Host "Key files created:" -ForegroundColor Green
    Write-Host "   Private key: $keyPath" -ForegroundColor White
    Write-Host "   Public key: $publicKeyPath" -ForegroundColor White
} else {
    Write-Host "Key generation failed - files not found" -ForegroundColor Red
    exit 1
}

# Set proper permissions on private key (Windows equivalent)
try {
    $acl = Get-Acl $keyPath
    $acl.SetAccessRuleProtection($true, $false)
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule($env:USERNAME, "FullControl", "Allow")
    $acl.SetAccessRule($accessRule)
    Set-Acl $keyPath $acl
    Write-Host "Set secure permissions on private key" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not set secure permissions: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Display public key content
Write-Host "`nPUBLIC KEY CONTENT (copy this to VPS):" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
$publicKeyContent = Get-Content $publicKeyPath
Write-Host $publicKeyContent -ForegroundColor White
Write-Host "=" * 60 -ForegroundColor Gray

# Display private key content for GitHub Secrets
Write-Host "`nPRIVATE KEY CONTENT (copy this to GitHub Secrets):" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
$privateKeyContent = Get-Content $keyPath -Raw
Write-Host $privateKeyContent -ForegroundColor White
Write-Host "=" * 60 -ForegroundColor Gray

# Create deployment instructions
$instructionsPath = "$PSScriptRoot\SSH_DEPLOYMENT_INSTRUCTIONS.txt"
$instructions = @"
AI Trading Sentinel SSH Deployment Setup Instructions

1. ADD PUBLIC KEY TO VPS:
   ssh root@161.97.112.146
   mkdir -p ~/.ssh
   echo '$publicKeyContent' >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   exit

2. ADD TO GITHUB SECRETS:
   Go to: https://github.com/YOUR_USERNAME/ai-trading-sentinel/settings/secrets/actions
   
   Secret Name: CONTABO_SSH_PRIVATE_KEY
   Secret Value: (copy the private key content above)
   
   Secret Name: CONTABO_VPS_HOST
   Secret Value: 161.97.112.146
   
   Secret Name: CONTABO_VPS_USER
   Secret Value: root

3. TEST SSH CONNECTION:
   ssh -i "$keyPath" root@161.97.112.146 "echo 'SSH connection successful'"

4. UPDATE SLACK WEBHOOK:
   Get new webhook URL from Slack and add as SLACK_WEBHOOK_URL secret

5. RUN GITHUB ACTIONS:
   Push changes to main branch or manually trigger workflow

Generated: $(Get-Date)
Key Location: $keyPath
Public Key Location: $publicKeyPath
"@

Set-Content -Path $instructionsPath -Value $instructions
Write-Host "`nInstructions saved to: $instructionsPath" -ForegroundColor Green

# Test SSH connection (optional)
Write-Host "`nTesting SSH connection to VPS..." -ForegroundColor Cyan
try {
    $testResult = & ssh -i $keyPath -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@161.97.112.146 "echo 'SSH test successful'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SSH connection test successful!" -ForegroundColor Green
    } else {
        Write-Host "SSH connection test failed (expected if public key not yet added to VPS)" -ForegroundColor Yellow
        Write-Host "   Error: $testResult" -ForegroundColor Red
    }
} catch {
    Write-Host "SSH test failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`nNext Steps:" -ForegroundColor Green
Write-Host "1. Copy public key to VPS authorized_keys" -ForegroundColor White
Write-Host "2. Add private key to GitHub Secrets" -ForegroundColor White
Write-Host "3. Update Slack webhook URL" -ForegroundColor White
Write-Host "4. Test deployment workflow" -ForegroundColor White

Write-Host "`nSSH key generation completed!" -ForegroundColor Green