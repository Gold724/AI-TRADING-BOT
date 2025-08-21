# Contabo SSH Setup and Deployment Script (PowerShell)
# This script sets up SSH keys and deploys the AI Trading Sentinel from Windows

param(
    [string]$TargetIP = "161.97.112.146",
    [string]$Username = "root"
)

# Colors for output
function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

Write-Host "🔐 AI Trading Sentinel - SSH Setup & Deployment" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Configuration
$SSHDir = "$env:USERPROFILE\.ssh"
$SSHKeyPath = "$SSHDir\id_rsa"
$SSHPubKeyPath = "$SSHDir\id_rsa.pub"

# Step 1: Check SSH client availability
function Test-SSHClient {
    Write-Info "Checking SSH client availability..."
    
    try {
        $null = Get-Command ssh -ErrorAction Stop
        $sshVersion = ssh -V 2>&1
        Write-Success "SSH client found: $sshVersion"
        return $true
    }
    catch {
        Write-Error "SSH client not found. Please install OpenSSH."
        Write-Info "To install OpenSSH on Windows 10/11:"
        Write-Info "Run as Administrator: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"
        return $false
    }
}

# Step 2: Generate SSH key if not exists
function New-SSHKey {
    Write-Info "Setting up SSH key..."
    
    # Create .ssh directory if it doesn't exist
    if (!(Test-Path $SSHDir)) {
        New-Item -ItemType Directory -Path $SSHDir -Force | Out-Null
        Write-Info "Created .ssh directory at $SSHDir"
    }
    
    if (!(Test-Path $SSHKeyPath)) {
        Write-Info "Generating new SSH key pair..."
        try {
            $keygenArgs = @("-t", "rsa", "-b", "4096", "-f", $SSHKeyPath, "-N", """""", "-C", "ai-trading-sentinel@contabo")
            & ssh-keygen @keygenArgs
            Write-Success "SSH key generated at $SSHKeyPath"
        }
        catch {
            Write-Error "Failed to generate SSH key: $_"
            return $false
        }
    }
    else {
        Write-Info "SSH key already exists at $SSHKeyPath"
    }
    
    return $true
}

# Step 3: Test connectivity
function Test-ServerConnectivity {
    Write-Info "Testing connectivity to $TargetIP..."
    
    try {
        $ping = Test-Connection -ComputerName $TargetIP -Count 2 -Quiet
        if ($ping) {
            Write-Success "Server is reachable"
        }
        else {
            Write-Warning "Server ping failed, but SSH might still work"
        }
    }
    catch {
        Write-Warning "Connectivity test failed: $_"
    }
    
    # Test SSH port
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connection = $tcpClient.BeginConnect($TargetIP, 22, $null, $null)
        $wait = $connection.AsyncWaitHandle.WaitOne(5000, $false)
        
        if ($wait -and $tcpClient.Connected) {
            Write-Success "SSH port 22 is open"
            $tcpClient.Close()
            return $true
        }
        else {
            Write-Error "SSH port 22 is not accessible"
            $tcpClient.Close()
            return $false
        }
    }
    catch {
        Write-Error "Cannot connect to SSH port: $_"
        return $false
    }
}

# Step 4: Copy SSH key to server
function Install-SSHKey {
    Write-Info "Installing SSH key on target server..."
    Write-Warning "You will be prompted for the root password"
    
    # Read public key
    if (!(Test-Path $SSHPubKeyPath)) {
        Write-Error "Public key not found at $SSHPubKeyPath"
        return $false
    }
    
    $publicKey = Get-Content $SSHPubKeyPath -Raw
    $publicKey = $publicKey.Trim()
    
    # Create command to install key
    $installCmd = "mkdir -p ~/.ssh && echo '$publicKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh && echo 'SSH key installed successfully'"
    
    try {
        # Use ssh to install the key
        $sshArgs = @("$Username@$TargetIP", $installCmd)
        $result = & ssh @sshArgs
        
        if ($result -match "SSH key installed successfully") {
            Write-Success "SSH key installation completed"
            return $true
        }
        else {
            Write-Error "SSH key installation may have failed"
            return $false
        }
    }
    catch {
        Write-Error "Failed to install SSH key: $_"
        return $false
    }
}

# Step 5: Test SSH key authentication
function Test-SSHKeyAuth {
    Write-Info "Testing SSH key authentication..."
    
    try {
        $sshArgs = @("-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "$Username@$TargetIP", "echo 'SSH key authentication successful'")
        $result = & ssh @sshArgs 2>$null
        
        if ($result -match "successful") {
            Write-Success "SSH key authentication is working"
            return $true
        }
        else {
            Write-Error "SSH key authentication failed"
            return $false
        }
    }
    catch {
        Write-Error "SSH key authentication test failed: $_"
        return $false
    }
}

# Step 6: Create and upload deployment script
function Deploy-TradingBot {
    Write-Info "Creating deployment script..."
    
    # Create deployment script content
    $deployScript = @'
#!/bin/bash
set -e

echo "🚀 Starting AI Trading Sentinel deployment..."

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nodejs npm git curl wget unzip htop nano net-tools

# Install Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
fi

# Create deployment directory
mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

echo "Setting up AI Trading Sentinel files..."

# Create directory structure
mkdir -p data/{accounts,backtest,emergency,historical,memory,signals,simulations}
mkdir -p logs config backend frontend

# Create main.py
cat > main.py << 'MAINEOF'
#!/usr/bin/env python3
"""
AI Trading Sentinel - Main Application
"""

import os
import sys
import logging
import time
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/trading.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 AI Trading Sentinel Starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Trading Mode: {os.getenv('TRADING_MODE', 'simulation')}")
    
    logger.info("✅ AI Trading Sentinel is running")
    
    # Keep running
    try:
        while True:
            time.sleep(60)  # Check every minute
            logger.info("💓 Heartbeat - System running normally")
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        logger.info("👋 AI Trading Sentinel stopped")

if __name__ == "__main__":
    main()
MAINEOF

# Create requirements.txt
cat > requirements.txt << 'REQEOF'
flask==2.3.3
requests==2.31.0
psutil==5.9.5
schedule==1.2.0
pandas==2.0.3
numpy==1.24.3
REQEOF

# Create systemd service
cat > /etc/systemd/system/trae.service << 'SERVICEEOF'
[Unit]
Description=AI Trading Sentinel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-trading-sentinel
Environment=PATH=/opt/ai-trading-sentinel/venv/bin
ExecStart=/opt/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment file
cat > .env << 'ENVEOF'
# AI Trading Sentinel Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=5000
FRONTEND_PORT=3000

# Trading Configuration
TRADING_MODE=simulation
RISK_LEVEL=medium
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0

# Monitoring
MONITORING_ENABLED=true
ALERT_EMAIL=admin@example.com

# Security
SECRET_KEY=change-this-secret-key-$(date +%s)
JWT_SECRET=change-this-jwt-secret-$(date +%s)
ENVEOF

# Enable and start service
echo "Setting up systemd service..."
systemctl daemon-reload
systemctl enable trae
systemctl start trae

# Set proper permissions
chown -R root:root /opt/ai-trading-sentinel
chmod +x /opt/ai-trading-sentinel/*.py

echo "✅ AI Trading Sentinel deployed successfully!"
echo "📍 Location: /opt/ai-trading-sentinel"
echo "🔧 Service: systemctl status trae"
echo "📊 Dashboard: http://$(curl -s ifconfig.me):5000"
echo "📝 Logs: journalctl -u trae -f"
'@
    
    # Write deployment script to temp file
    $tempScript = "$env:TEMP\deploy_ai_trading.sh"
    $deployScript | Out-File -FilePath $tempScript -Encoding UTF8 -NoNewline
    
    try {
        Write-Info "Uploading deployment script to server..."
        $scpArgs = @($tempScript, "${Username}@${TargetIP}:/tmp/deploy_ai_trading.sh")
        & scp @scpArgs
        
        Write-Info "Executing deployment script on server..."
        $sshArgs = @("$Username@$TargetIP", "chmod +x /tmp/deploy_ai_trading.sh && /tmp/deploy_ai_trading.sh")
        & ssh @sshArgs
        
        Write-Success "Deployment completed successfully!"
        return $true
    }
    catch {
        Write-Error "Deployment failed: $_"
        return $false
    }
    finally {
        # Clean up temp file
        if (Test-Path $tempScript) {
            Remove-Item $tempScript -Force
        }
    }
}

# Step 7: Validate deployment
function Test-Deployment {
    Write-Info "Validating deployment..."
    
    $validationScript = @'
echo "🔍 Deployment Validation Report"
echo "=============================="

# Check deployment directory
if [ -d "/opt/ai-trading-sentinel" ]; then
    echo "✅ Deployment directory exists"
    cd /opt/ai-trading-sentinel
    
    # Check Python environment
    if [ -d "venv" ]; then
        echo "✅ Python virtual environment created"
    fi
    
    # Check service status
    if systemctl is-active trae >/dev/null 2>&1; then
        echo "✅ Trading service is running"
    else
        echo "⚠️  Trading service status: $(systemctl is-active trae)"
    fi
    
    # Show system info
    echo ""
    echo "📊 System Information:"
    echo "CPU: $(nproc) cores"
    echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
    echo "Disk: $(df -h / | awk 'NR==2 {print $4}') available"
    echo "IP: $(curl -s ifconfig.me)"
    echo "Uptime: $(uptime -p)"
    
    # Show service logs
    echo ""
    echo "📝 Recent Service Logs:"
    journalctl -u trae --no-pager -n 5
else
    echo "❌ Deployment directory not found"
fi
'@
    
    try {
        $sshArgs = @("$Username@$TargetIP", $validationScript)
        $result = & ssh @sshArgs
        Write-Host $result
        Write-Success "Validation completed!"
        return $true
    }
    catch {
        Write-Error "Validation failed: $_"
        return $false
    }
}

# Main execution function
function Start-Deployment {
    Write-Info "Starting SSH setup and deployment process..."
    Write-Host ""
    
    # Step 1: Check SSH client
    if (!(Test-SSHClient)) {
        return $false
    }
    
    # Step 2: Generate SSH key
    if (!(New-SSHKey)) {
        return $false
    }
    
    # Step 3: Test connectivity
    if (!(Test-ServerConnectivity)) {
        return $false
    }
    
    # Step 4: Install SSH key (requires password)
    Write-Host ""
    Write-Warning "The next step requires the root password for $TargetIP"
    Write-Info "Please enter the password when prompted..."
    Write-Host ""
    
    if (!(Install-SSHKey)) {
        Write-Error "Failed to install SSH key. Please check the password and try again."
        return $false
    }
    
    # Step 5: Test SSH key authentication
    if (!(Test-SSHKeyAuth)) {
        Write-Error "SSH key authentication is not working. Please check the setup."
        return $false
    }
    
    # Step 6: Deploy trading bot
    if (!(Deploy-TradingBot)) {
        return $false
    }
    
    # Step 7: Validate deployment
    if (!(Test-Deployment)) {
        return $false
    }
    
    # Success message
    Write-Host ""
    Write-Success "🎉 AI Trading Sentinel deployment completed successfully!"
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. SSH into server: ssh root@$TargetIP"
    Write-Host "2. Configure credentials: nano /opt/ai-trading-sentinel/.env"
    Write-Host "3. Check service: systemctl status trae"
    Write-Host "4. Monitor logs: journalctl -u trae -f"
    Write-Host "5. Access dashboard: http://$TargetIP:5000"
    Write-Host ""
    
    return $true
}

# Execute main function
if ($MyInvocation.InvocationName -ne '.') {
    Start-Deployment
}