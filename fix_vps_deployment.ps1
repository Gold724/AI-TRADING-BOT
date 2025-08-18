# Fix VPS Deployment - Copy Missing TradeBot Sentinel Files
# PowerShell script to fix missing files on your VPS

param(
    [string]$VpsHost = $env:VPS_HOST,
    [string]$VpsUser = "root",
    [string]$VpsDir = "/root/AI-TRADING-BOT"
)

Write-Host "🔧 Fixing VPS Deployment - TradeBot Sentinel" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "VPS Host: $VpsHost" -ForegroundColor Yellow
Write-Host "VPS User: $VpsUser" -ForegroundColor Yellow
Write-Host "VPS Directory: $VpsDir" -ForegroundColor Yellow
Write-Host ""

if (-not $VpsHost) {
    Write-Host "❌ VPS_HOST not specified. Please provide it as parameter or environment variable" -ForegroundColor Red
    Write-Host "Usage: .\fix_vps_deployment.ps1 -VpsHost 'your-vps-ip'" -ForegroundColor Yellow
    exit 1
}

# Test VPS connection
Write-Host "🔍 Testing VPS connection..." -ForegroundColor Blue
try {
    $sshTarget = "$VpsUser@$VpsHost"
    $testResult = ssh -o ConnectTimeout=10 $sshTarget "echo 'Connection successful'"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ VPS connection successful" -ForegroundColor Green
    } else {
        throw "SSH connection failed"
    }
} catch {
    Write-Host "❌ Cannot connect to VPS. Please check:" -ForegroundColor Red
    Write-Host "   - VPS_HOST is correct" -ForegroundColor Yellow
    Write-Host "   - SSH key is properly configured" -ForegroundColor Yellow
    Write-Host "   - VPS is running and accessible" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Create directory structure
Write-Host "📁 Creating directory structure..." -ForegroundColor Blue
$sshTarget = "$VpsUser@$VpsHost"
ssh $sshTarget "mkdir -p $VpsDir"

# Copy main TradeBot Sentinel script
Write-Host "📦 Copying TradeBot Sentinel scripts..." -ForegroundColor Blue
if (Test-Path "login_bulenox_playwright.py") {
    $scpTarget = "$VpsUser@$VpsHost`:$VpsDir/"
    scp "login_bulenox_playwright.py" $scpTarget
    Write-Host "✅ Copied login_bulenox_playwright.py" -ForegroundColor Green
} else {
    Write-Host "⚠️ login_bulenox_playwright.py not found in current directory" -ForegroundColor Yellow
}

# Copy from vps_deployment directory
if (Test-Path "vps_deployment\trading_scripts") {
    Write-Host "📦 Copying from vps_deployment/trading_scripts..." -ForegroundColor Blue
    $scpTarget = "$VpsUser@$VpsHost`:$VpsDir/"
    scp "vps_deployment\trading_scripts\*" $scpTarget
    Write-Host "✅ Copied trading scripts" -ForegroundColor Green
}

if (Test-Path "vps_deployment\utilities") {
    Write-Host "📦 Copying utilities..." -ForegroundColor Blue
    $scpTarget = "$VpsUser@$VpsHost`:$VpsDir/"
    scp "vps_deployment\utilities\*" $scpTarget
    Write-Host "✅ Copied utilities" -ForegroundColor Green
}

if (Test-Path "vps_deployment\launchers") {
    Write-Host "📦 Copying launchers..." -ForegroundColor Blue
    $scpTarget = "$VpsUser@$VpsHost`:$VpsDir/"
    scp "vps_deployment\launchers\*" $scpTarget
    Write-Host "✅ Copied launchers" -ForegroundColor Green
}

# Copy requirements.txt
if (Test-Path "requirements.txt") {
    $scpTarget = "$VpsUser@$VpsHost`:$VpsDir/"
    scp "requirements.txt" $scpTarget
    Write-Host "✅ Copied requirements.txt" -ForegroundColor Green
} elseif (Test-Path "vps_deployment\utilities\requirements.txt") {
    $scpTarget = "$VpsUser@$VpsHost`:$VpsDir/"
    scp "vps_deployment\utilities\requirements.txt" $scpTarget
    Write-Host "✅ Copied requirements.txt from utilities" -ForegroundColor Green
}

# Set proper permissions
Write-Host "🔐 Setting file permissions..." -ForegroundColor Blue
$sshTarget = "$VpsUser@$VpsHost"
ssh $sshTarget "chmod +x $VpsDir/*.py $VpsDir/*.sh 2>/dev/null || true"

# Verify files exist
Write-Host "🔍 Verifying deployed files..." -ForegroundColor Blue
ssh $sshTarget "ls -la $VpsDir/"

Write-Host ""
Write-Host "✅ VPS deployment fix completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. SSH to your VPS: ssh $VpsUser@$VpsHost" -ForegroundColor Yellow
Write-Host "2. Navigate to directory: cd $VpsDir" -ForegroundColor Yellow
Write-Host "3. Install dependencies: pip3 install -r requirements.txt" -ForegroundColor Yellow
Write-Host "4. Install Playwright: python3 -m playwright install" -ForegroundColor Yellow
Write-Host "5. Set environment variables:" -ForegroundColor Yellow
Write-Host "   export BULENOX_USERNAME='your_username'" -ForegroundColor Gray
Write-Host "   export BULENOX_PASSWORD='your_password'" -ForegroundColor Gray
Write-Host "6. Run TradeBot Sentinel: python3 login_bulenox_playwright.py --headless" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 TradeBot Sentinel is ready for deployment!" -ForegroundColor Green