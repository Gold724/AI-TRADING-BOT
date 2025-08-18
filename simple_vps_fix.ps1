# Simple VPS Fix Script - Copy Missing TradeBot Sentinel Files
param(
    [Parameter(Mandatory=$true)]
    [string]$VpsHost,
    [string]$VpsUser = "root",
    [string]$VpsDir = "/root/AI-TRADING-BOT"
)

Write-Host "🔧 Simple VPS Fix - TradeBot Sentinel" -ForegroundColor Cyan
Write-Host "VPS Host: $VpsHost" -ForegroundColor Yellow
Write-Host "VPS User: $VpsUser" -ForegroundColor Yellow
Write-Host "VPS Directory: $VpsDir" -ForegroundColor Yellow
Write-Host ""

# Test connection
Write-Host "🔍 Testing VPS connection..." -ForegroundColor Blue
$sshTarget = "$VpsUser@$VpsHost"
$testCmd = "ssh -o ConnectTimeout=10 $sshTarget 'echo Connection OK'"
Invoke-Expression $testCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cannot connect to VPS" -ForegroundColor Red
    exit 1
}

Write-Host "✅ VPS connection successful" -ForegroundColor Green
Write-Host ""

# Create directory
Write-Host "📁 Creating directory..." -ForegroundColor Blue
$createDirCmd = "ssh $sshTarget 'mkdir -p $VpsDir'"
Invoke-Expression $createDirCmd

# Copy main script
Write-Host "📦 Copying login_bulenox_playwright.py..." -ForegroundColor Blue
$scpTarget = "$VpsUser@$VpsHost`:$VpsDir/"
$copyCmd = "scp login_bulenox_playwright.py $scpTarget"
Invoke-Expression $copyCmd

# Copy trading scripts
Write-Host "📦 Copying trading scripts..." -ForegroundColor Blue
$copyTradingCmd = "scp vps_deployment\trading_scripts\* $scpTarget"
Invoke-Expression $copyTradingCmd

# Copy utilities
Write-Host "📦 Copying utilities..." -ForegroundColor Blue
$copyUtilCmd = "scp vps_deployment\utilities\* $scpTarget"
Invoke-Expression $copyUtilCmd

# Copy requirements
Write-Host "📦 Copying requirements.txt..." -ForegroundColor Blue
$copyReqCmd = "scp requirements.txt $scpTarget"
Invoke-Expression $copyReqCmd

# Set permissions
Write-Host "🔐 Setting permissions..." -ForegroundColor Blue
$permCmd = "ssh $sshTarget 'chmod +x $VpsDir/*.py $VpsDir/*.sh'"
Invoke-Expression $permCmd

# Verify
Write-Host "🔍 Verifying files..." -ForegroundColor Blue
$listCmd = "ssh $sshTarget 'ls -la $VpsDir/'"
Invoke-Expression $listCmd

Write-Host ""
Write-Host "✅ VPS fix completed!" -ForegroundColor Green
Write-Host "📋 Next: SSH to VPS and run: python3 login_bulenox_playwright.py --headless" -ForegroundColor Yellow