#!/usr/bin/env pwsh
# Ubuntu Dependencies Fix Deployment Script - Windows Compatible
# This script deploys the Ubuntu dependency fixes to your VPS using Windows-native tools

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsHost,
    
    [Parameter(Mandatory=$true)]
    [string]$VpsUser,
    
    [Parameter(Mandatory=$true)]
    [string]$VpsDir,
    
    [Parameter(Mandatory=$false)]
    [string]$VpsPassword = "JfAJZ38VwU8j42LKa84PqIxVx"
)

# Validate parameters
if (-not $VpsHost -or -not $VpsUser -or -not $VpsDir) {
    Write-Host "Error: Missing required parameters" -ForegroundColor Red
    Write-Host "Usage: .\deploy_ubuntu_fix_windows.ps1 -VpsHost <host> -VpsUser <user> -VpsDir <directory>" -ForegroundColor Yellow
    exit 1
}

# Check if plink is available (PuTTY command line tool)
$plinkPath = $null
$possiblePaths = @(
    "plink",
    "C:\Program Files\PuTTY\plink.exe",
    "C:\Program Files (x86)\PuTTY\plink.exe",
    "$env:USERPROFILE\AppData\Local\Programs\PuTTY\plink.exe"
)

foreach ($path in $possiblePaths) {
    try {
        $result = & $path -V 2>$null
        if ($LASTEXITCODE -eq 0 -or $result -match "plink") {
            $plinkPath = $path
            Write-Host "Found plink at: $plinkPath" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $plinkPath) {
    Write-Host "PuTTY plink not found. Please install PuTTY from https://www.putty.org/" -ForegroundColor Red
    Write-Host "Or use the manual SSH method with the password: $VpsPassword" -ForegroundColor Yellow
    
    # Fallback to manual SSH
    Write-Host "\nFallback: Manual SSH commands to run on your VPS:" -ForegroundColor Cyan
    Write-Host "1. SSH to VPS: ssh $VpsUser@$VpsHost" -ForegroundColor Yellow
    Write-Host "2. Enter password: $VpsPassword" -ForegroundColor Yellow
    Write-Host "3. Run: wget -O fix_ubuntu_dependencies.sh https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/vps_deployment/fix_ubuntu_dependencies.sh" -ForegroundColor Yellow
    Write-Host "4. Run: chmod +x fix_ubuntu_dependencies.sh" -ForegroundColor Yellow
    Write-Host "5. Run: ./fix_ubuntu_dependencies.sh" -ForegroundColor Yellow
    exit 1
}

$sshTarget = "$VpsUser@$VpsHost"

# Test SSH connection using plink
Write-Host "Testing SSH connection to $VpsUser@$VpsHost..." -ForegroundColor Blue
Write-Host "Using plink for automated authentication..." -ForegroundColor Yellow

# First connection to accept host key
$testResult = & $plinkPath -ssh -batch -pw $VpsPassword $sshTarget "echo 'SSH connection successful'" 2>&1
if ($LASTEXITCODE -ne 0) {
    # Try with host key acceptance
    Write-Host "Accepting host key..." -ForegroundColor Yellow
    $acceptResult = echo "y" | & $plinkPath -ssh -pw $VpsPassword $sshTarget "echo 'SSH connection successful'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SSH connection failed. Error: $acceptResult" -ForegroundColor Red
        Write-Host "Please verify the VPS credentials and network connectivity." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "SSH connection successful!" -ForegroundColor Green

# Check if fix script exists locally
if (-not (Test-Path "./vps_deployment/fix_ubuntu_dependencies.sh")) {
    Write-Host "Creating Ubuntu dependencies fix script..." -ForegroundColor Blue
    
    # Create the vps_deployment directory if it doesn't exist
    if (-not (Test-Path "./vps_deployment")) {
        New-Item -ItemType Directory -Path "./vps_deployment" -Force | Out-Null
    }
    
    # Create the fix script
    $fixScript = @'
#!/bin/bash
# Ubuntu Dependencies Fix Script
# This script fixes common Ubuntu dependency issues for trading applications

echo "Starting Ubuntu dependencies fix..."
echo "======================================"

# Update package lists
echo "Updating package lists..."
sudo apt update

# Install essential build tools
echo "Installing essential build tools..."
sudo apt install -y build-essential curl wget git

# Install Python and pip
echo "Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Node.js and npm
echo "Installing Node.js and npm..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install system dependencies for Playwright
echo "Installing system dependencies for Playwright..."
sudo apt install -y \
    libnss3-dev \
    libatk-bridge2.0-dev \
    libdrm-dev \
    libxkbcommon-dev \
    libgtk-3-dev \
    libgbm-dev \
    libasound2-dev

# Install additional dependencies
echo "Installing additional dependencies..."
sudo apt install -y \
    xvfb \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0

# Install Chrome dependencies
echo "Installing Chrome dependencies..."
sudo apt install -y \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils

# Clean up
echo "Cleaning up..."
sudo apt autoremove -y
sudo apt autoclean

echo "======================================"
echo "Ubuntu dependencies fix completed!"
echo "You can now install Python packages and Playwright."
echo ""
echo "Next steps:"
echo "1. pip3 install -r requirements.txt"
echo "2. python3 -m playwright install"
echo "3. python3 -m playwright install-deps"
'@
    
    $fixScript | Out-File -FilePath "./vps_deployment/fix_ubuntu_dependencies.sh" -Encoding UTF8
    Write-Host "Fix script created successfully!" -ForegroundColor Green
}

# Copy the fix script to VPS using plink and pscp
Write-Host "Copying Ubuntu dependencies fix script to VPS..." -ForegroundColor Blue

# Check if pscp is available
$pscpPath = $plinkPath -replace "plink", "pscp"
if (-not (Test-Path $pscpPath)) {
    $pscpPath = "pscp"
}

# Copy file using pscp
$copyResult = & $pscpPath -pw $VpsPassword "./vps_deployment/fix_ubuntu_dependencies.sh" "${sshTarget}:${VpsDir}/" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to copy fix script. Error: $copyResult" -ForegroundColor Red
    Write-Host "Trying alternative method..." -ForegroundColor Yellow
    
    # Alternative: create script directly on VPS
    $createScriptCmd = @"
cat > $VpsDir/fix_ubuntu_dependencies.sh << 'EOF'
#!/bin/bash
echo "Starting Ubuntu dependencies fix..."
echo "======================================"
sudo apt update
sudo apt install -y build-essential curl wget git python3 python3-pip python3-venv python3-dev
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo apt install -y libnss3-dev libatk-bridge2.0-dev libdrm-dev libxkbcommon-dev libgtk-3-dev libgbm-dev libasound2-dev
sudo apt install -y xvfb libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 libcairo-gobject2 libgtk-3-0 libgdk-pixbuf2.0-0
sudo apt install -y fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgtk-3-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils
sudo apt autoremove -y
sudo apt autoclean
echo "======================================"
echo "Ubuntu dependencies fix completed!"
EOF
"@
    
    $createResult = & $plinkPath -ssh -pw $VpsPassword $sshTarget $createScriptCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create script on VPS. Error: $createResult" -ForegroundColor Red
        exit 1
    }
    Write-Host "Fix script created directly on VPS!" -ForegroundColor Green
} else {
    Write-Host "Fix script copied successfully!" -ForegroundColor Green
}

# Make the script executable
Write-Host "Making fix script executable..." -ForegroundColor Blue
$chmodResult = & $plinkPath -ssh -pw $VpsPassword $sshTarget "chmod +x $VpsDir/fix_ubuntu_dependencies.sh" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to make script executable. Error: $chmodResult" -ForegroundColor Red
    exit 1
}

# Execute the fix script on VPS
Write-Host "Executing Ubuntu dependencies fix on VPS..." -ForegroundColor Blue
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

$execResult = & $plinkPath -ssh -pw $VpsPassword $sshTarget "cd $VpsDir && ./fix_ubuntu_dependencies.sh" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Ubuntu dependencies fix completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps on your VPS:" -ForegroundColor Cyan
    Write-Host "1. SSH to VPS: ssh $VpsUser@$VpsHost" -ForegroundColor Yellow
    Write-Host "2. Enter password: $VpsPassword" -ForegroundColor Yellow
    Write-Host "3. Navigate to directory: cd $VpsDir" -ForegroundColor Yellow
    Write-Host "4. Install Python requirements: pip3 install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "5. Install Playwright: python3 -m playwright install" -ForegroundColor Yellow
    Write-Host "6. Install Playwright deps: python3 -m playwright install-deps" -ForegroundColor Yellow
    Write-Host "7. Set environment variables and run TradeBot Sentinel" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Ubuntu dependencies fix encountered issues" -ForegroundColor Yellow
    Write-Host "Output: $execResult" -ForegroundColor Gray
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Deployment script completed." -ForegroundColor Cyan