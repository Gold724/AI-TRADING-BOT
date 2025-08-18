# AI Trading Sentinel - VPS Deployment Script
# Deploy to VPS: 161.97.112.146

$VPS_HOST = "161.97.112.146"
$VPS_USER = "root"
$VPS_DIR = "/root/AI-TRADING-BOT"

Write-Host "Deploying AI Trading Sentinel to VPS..." -ForegroundColor Green

# Test SSH connection first
Write-Host "Testing SSH connection to $VPS_HOST..." -ForegroundColor Yellow
try {
    $testResult = ssh $VPS_USER@$VPS_HOST "echo 'Connection successful'"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SSH connection successful" -ForegroundColor Green
    } else {
        Write-Host "SSH connection failed" -ForegroundColor Red
        Write-Host "Please ensure SSH key is configured and VPS is accessible" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "SSH connection error: $_" -ForegroundColor Red
    exit 1
}

# Create remote directory
Write-Host "Creating remote directory..." -ForegroundColor Blue
ssh $VPS_USER@$VPS_HOST "mkdir -p $VPS_DIR"

# Copy trading scripts
Write-Host "Copying trading scripts..." -ForegroundColor Blue
scp -r trading_scripts/* $VPS_USER@${VPS_HOST}:$VPS_DIR/

# Copy launchers
Write-Host "Copying launcher scripts..." -ForegroundColor Blue
scp -r launchers/* $VPS_USER@${VPS_HOST}:$VPS_DIR/

# Copy utilities
Write-Host "Copying utility scripts..." -ForegroundColor Blue
scp -r utilities/* $VPS_USER@${VPS_HOST}:$VPS_DIR/

# Copy config files
Write-Host "Copying configuration files..." -ForegroundColor Blue
scp -r config_files/* $VPS_USER@${VPS_HOST}:$VPS_DIR/

# Copy environment checker
Write-Host "Copying environment checker..." -ForegroundColor Blue
scp vps_environment_check.py $VPS_USER@${VPS_HOST}:$VPS_DIR/

# Set permissions
Write-Host "Setting file permissions..." -ForegroundColor Blue
ssh $VPS_USER@$VPS_HOST "chmod +x $VPS_DIR/*.py $VPS_DIR/*.sh"

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Blue
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && pip3 install -r requirements.txt"

# Install Playwright browsers
Write-Host "Installing Playwright browsers..." -ForegroundColor Blue
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 -m playwright install"

# Verify deployment
Write-Host "Verifying deployment..." -ForegroundColor Blue
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 vps_environment_check.py"

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Files deployed to: ${VPS_HOST}:${VPS_DIR}" -ForegroundColor Cyan
Write-Host "Ready to run trading bot on VPS" -ForegroundColor Cyan

# Test login to Bulenox
Write-Host "Testing Bulenox login..." -ForegroundColor Yellow
ssh $VPS_USER@$VPS_HOST "cd $VPS_DIR && python3 login_bulenox_playwright.py --test"

Write-Host "VPS Deployment Complete! Your AI Trading Sentinel is ready." -ForegroundColor Green