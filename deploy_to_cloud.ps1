# AI Trading Sentinel - Cloud Deployment Script (PowerShell)
# Automated deployment to Contabo VPS or any cloud provider

param(
    [string]$VpsHost = "",
    [string]$VpsUser = "root",
    [string]$SshKeyPath = "~\.ssh\id_rsa",
    [string]$GitRepo = "https://github.com/yourusername/ai-trading-sentinel.git",
    [string]$Domain = "",
    [string]$Email = "",
    [switch]$SkipConfirmation
)

# Configuration
$ProjectName = "ai-trading-sentinel"
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Status {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# Function to check if command exists
function Test-CommandExists {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to get user input
function Get-UserInput {
    param(
        [string]$Prompt,
        [string]$Default = ""
    )
    
    if ($Default) {
        $input = Read-Host "$Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($input)) {
            return $Default
        }
        return $input
    }
    else {
        return Read-Host $Prompt
    }
}

# Function to validate inputs
function Test-Inputs {
    if ([string]::IsNullOrWhiteSpace($VpsHost)) {
        Write-Error "VPS host is required"
        exit 1
    }
    
    if ([string]::IsNullOrWhiteSpace($GitRepo)) {
        Write-Error "Git repository URL is required"
        exit 1
    }
}

# Function to test SSH connection
function Test-SshConnection {
    Write-Status "Testing SSH connection to $VpsUser@$VpsHost..."
    
    try {
        $result = ssh -i $SshKeyPath -o ConnectTimeout=10 -o BatchMode=yes "$VpsUser@$VpsHost" "echo 'SSH connection successful'" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "SSH connection established"
            return $true
        }
        else {
            throw "SSH connection failed"
        }
    }
    catch {
        Write-Error "SSH connection failed"
        Write-Warning "Please ensure:"
        Write-Host "  1. SSH key is properly configured: $SshKeyPath"
        Write-Host "  2. VPS is accessible: $VpsHost"
        Write-Host "  3. User has proper permissions: $VpsUser"
        return $false
    }
}

# Function to setup VPS environment
function Set-VpsEnvironment {
    Write-Status "Setting up VPS environment..."
    
    $setupScript = @'
set -e

echo "🔄 Updating system packages..."
apt update && apt upgrade -y

echo "📦 Installing essential packages..."
apt install -y \
    curl \
    wget \
    git \
    htop \
    screen \
    tmux \
    ufw \
    fail2ban \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm

echo "🐳 Installing Docker..."
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    systemctl enable docker
    systemctl start docker
fi

echo "🐙 Installing Docker Compose..."
if ! command -v docker-compose >/dev/null 2>&1; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "🔒 Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp

echo "🛡️ Configuring Fail2Ban..."
systemctl enable fail2ban
systemctl start fail2ban

echo "✅ VPS environment setup completed"
'@
    
    $setupScript | ssh -i $SshKeyPath "$VpsUser@$VpsHost" 'bash -s'
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "VPS environment setup completed"
    }
    else {
        throw "VPS environment setup failed"
    }
}

# Function to deploy application
function Deploy-Application {
    Write-Status "Deploying AI Trading Sentinel..."
    
    $deployScript = @"
set -e

echo "📥 Cloning repository..."
if [ -d "$ProjectName" ]; then
    cd $ProjectName
    git pull origin main
else
    git clone $GitRepo $ProjectName
    cd $ProjectName
fi

echo "🔧 Setting up environment..."
cat > .env << EOF
BULENOX_USERNAME=BX64883
BULENOX_PASSWORD=XujhMzFf6K
ENVIRONMENT=production
HEADLESS=true
LOG_LEVEL=INFO
REDIS_PASSWORD=`$(openssl rand -hex 16)
DASHBOARD_SECRET=`$(openssl rand -hex 16)
TZ=UTC
EOF

chmod 600 .env

echo "🏗️ Building and starting containers..."
docker-compose down --remove-orphans || true
docker-compose build --no-cache
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service status..."
docker-compose ps

echo "📊 Checking logs..."
docker-compose logs --tail=20

echo "✅ Application deployment completed"
"@
    
    $deployScript | ssh -i $SshKeyPath "$VpsUser@$VpsHost" 'bash -s'
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Application deployed successfully"
    }
    else {
        throw "Application deployment failed"
    }
}

# Function to setup monitoring
function Set-Monitoring {
    Write-Status "Setting up monitoring and health checks..."
    
    $monitoringScript = @'
set -e

cd ai-trading-sentinel

echo "📊 Creating monitoring script..."
cat > monitor_trading_bot.sh << "EOF"
#!/bin/bash

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️ Some containers are not running, restarting..."
    docker-compose restart
fi

# Check application health
if ! curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "⚠️ Application health check failed, restarting..."
    docker-compose restart trading-bot
fi

# Clean up old logs
find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Clean up old screenshots
find screenshots/ -name "*.png" -mtime +3 -delete 2>/dev/null || true

echo "✅ Health check completed at $(date)"
EOF

chmod +x monitor_trading_bot.sh

echo "⏰ Setting up cron job for monitoring..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/ai-trading-sentinel/monitor_trading_bot.sh >> /root/ai-trading-sentinel/logs/monitor.log 2>&1") | crontab -

echo "🔄 Creating auto-update script..."
cat > auto_update.sh << "EOF"
#!/bin/bash
set -e

cd /root/ai-trading-sentinel

echo "🔍 Checking for updates..."
git fetch origin

LATEST_COMMIT=$(git rev-parse origin/main)
CURRENT_COMMIT=$(git rev-parse HEAD)

if [ "$LATEST_COMMIT" != "$CURRENT_COMMIT" ]; then
    echo "📥 New updates found, deploying..."
    
    # Pull updates
    git pull origin main
    
    # Rebuild and restart
    docker-compose build --no-cache
    docker-compose up -d
    
    echo "✅ Update completed successfully!"
else
    echo "✅ Already up to date!"
fi
EOF

chmod +x auto_update.sh

echo "⏰ Setting up cron job for auto-updates..."
(crontab -l 2>/dev/null; echo "0 */6 * * * /root/ai-trading-sentinel/auto_update.sh >> /root/ai-trading-sentinel/logs/update.log 2>&1") | crontab -

echo "✅ Monitoring setup completed"
'@
    
    $monitoringScript | ssh -i $SshKeyPath "$VpsUser@$VpsHost" 'bash -s'
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Monitoring and auto-update configured"
    }
    else {
        throw "Monitoring setup failed"
    }
}

# Function to setup SSL (optional)
function Set-SSL {
    if (-not [string]::IsNullOrWhiteSpace($Domain) -and -not [string]::IsNullOrWhiteSpace($Email)) {
        Write-Status "Setting up SSL certificate for $Domain..."
        
        $sslScript = @"
set -e

echo "🔒 Installing Certbot..."
apt install -y certbot python3-certbot-nginx

echo "📜 Obtaining SSL certificate..."
certbot --nginx -d $Domain --email $Email --agree-tos --non-interactive

echo "⏰ Setting up auto-renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

echo "✅ SSL setup completed"
"@
        
        $sslScript | ssh -i $SshKeyPath "$VpsUser@$VpsHost" 'bash -s'
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "SSL certificate configured for $Domain"
        }
        else {
            Write-Warning "SSL setup failed, continuing without SSL"
        }
    }
    else {
        Write-Warning "Skipping SSL setup (domain and email not provided)"
    }
}

# Function to display final information
function Show-FinalInfo {
    Write-Success "🎉 AI Trading Sentinel deployment completed!"
    Write-Host ""
    Write-Host "📋 Deployment Summary:" -ForegroundColor White
    Write-Host "  • VPS Host: $VpsHost"
    Write-Host "  • Application URL: http://$VpsHost:8080"
    if (-not [string]::IsNullOrWhiteSpace($Domain)) {
        Write-Host "  • Domain: https://$Domain"
    }
    Write-Host "  • Dashboard: http://$VpsHost:3000"
    Write-Host ""
    Write-Host "🔧 Management Commands:" -ForegroundColor White
    Write-Host "  • SSH to VPS: ssh -i $SshKeyPath $VpsUser@$VpsHost"
    Write-Host "  • View logs: docker-compose logs -f"
    Write-Host "  • Restart services: docker-compose restart"
    Write-Host "  • Update application: ./auto_update.sh"
    Write-Host "  • Monitor health: ./monitor_trading_bot.sh"
    Write-Host ""
    Write-Host "📊 Monitoring:" -ForegroundColor White
    Write-Host "  • Health checks run every 5 minutes"
    Write-Host "  • Auto-updates check every 6 hours"
    Write-Host "  • Logs are automatically rotated"
    Write-Host ""
    Write-Warning "⚠️ Important: Save your VPS credentials and SSH keys securely!"
}

# Main deployment function
function Start-Deployment {
    Write-Host "🚀 AI Trading Sentinel - Cloud Deployment Script" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Get deployment configuration if not provided
    if ([string]::IsNullOrWhiteSpace($VpsHost)) {
        Write-Status "Please provide deployment configuration:"
        $script:VpsHost = Get-UserInput "VPS Host/IP"
        $script:VpsUser = Get-UserInput "VPS Username" "root"
        $script:SshKeyPath = Get-UserInput "SSH Key Path" "~\.ssh\id_rsa"
        $script:GitRepo = Get-UserInput "Git Repository URL" "https://github.com/yourusername/ai-trading-sentinel.git"
        $script:Domain = Get-UserInput "Domain (optional)"
        $script:Email = Get-UserInput "Email for SSL (optional)"
    }
    
    Write-Host ""
    
    # Validate inputs
    Test-Inputs
    
    # Test SSH connection
    if (-not (Test-SshConnection)) {
        exit 1
    }
    
    # Confirm deployment
    if (-not $SkipConfirmation) {
        Write-Host ""
        Write-Warning "⚠️ This will deploy AI Trading Sentinel to $VpsHost"
        $confirm = Read-Host "Do you want to continue? (y/N)"
        if ($confirm -notmatch '^[Yy]$') {
            Write-Error "Deployment cancelled"
            exit 1
        }
    }
    
    Write-Host ""
    
    try {
        # Execute deployment steps
        Set-VpsEnvironment
        Deploy-Application
        Set-Monitoring
        Set-SSL
        
        # Display final information
        Show-FinalInfo
    }
    catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        Write-Host "Please check the error above and try again." -ForegroundColor Yellow
        exit 1
    }
}

# Check prerequisites
if (-not (Test-CommandExists "ssh")) {
    Write-Error "SSH client is required but not found. Please install OpenSSH or Git for Windows."
    exit 1
}

if (-not (Test-CommandExists "git")) {
    Write-Error "Git is required but not installed. Please install Git for Windows."
    exit 1
}

# Run main function
Start-Deployment