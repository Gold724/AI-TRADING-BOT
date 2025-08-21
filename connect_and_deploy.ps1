# Connect to Contabo and Deploy AI Trading Sentinel
# Run this script from Windows to get deployment instructions

Write-Host "🚀 AI Trading Sentinel - Contabo Deployment Helper" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

$contaboIP = "161.97.112.146"
$username = "root"

Write-Host "📋 Deployment Instructions:" -ForegroundColor Cyan
Write-Host ""
Write-Host "❌ You cannot run Linux commands on Windows!" -ForegroundColor Red
Write-Host "✅ You need to connect to your Contabo server first." -ForegroundColor Green
Write-Host ""

Write-Host "🔧 Step 1: Test Connection" -ForegroundColor Yellow
Write-Host "Run this command to test if your server is reachable:" -ForegroundColor White
Write-Host "ping $contaboIP" -ForegroundColor Gray
Write-Host ""

Write-Host "🔑 Step 2: Connect via SSH" -ForegroundColor Yellow
Write-Host "Try these SSH connection methods:" -ForegroundColor White
Write-Host ""
Write-Host "Method 1 (Password):" -ForegroundColor Cyan
Write-Host "ssh $username@$contaboIP" -ForegroundColor Gray
Write-Host ""
Write-Host "Method 2 (Force Password):" -ForegroundColor Cyan
Write-Host "ssh -o PreferredAuthentications=password $username@$contaboIP" -ForegroundColor Gray
Write-Host ""
Write-Host "Method 3 (Different Port):" -ForegroundColor Cyan
Write-Host "ssh -p 2222 $username@$contaboIP" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 Step 3: Deploy on Contabo Server" -ForegroundColor Yellow
Write-Host "Once connected to your Contabo server, run these commands:" -ForegroundColor White
Write-Host ""

# Create deployment commands file
$deployScript = @'
#!/bin/bash
# AI Trading Sentinel Deployment Script
# Run this on your Contabo server (Linux)

echo "AI Trading Sentinel - Deployment Starting..."
echo "Server: $(hostname)"
echo "User: $(whoami)"
echo ""

# Update system
echo "[1/8] Updating system..."
sudo apt update -y

# Install packages
echo "[2/8] Installing packages..."
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Create directory
echo "[3/8] Creating directory..."
sudo mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Create main application
echo "[4/8] Creating application..."
sudo tee main.py > /dev/null << "APPEOF"
#!/usr/bin/env python3
import logging
import time
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trading.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("AI Trading Sentinel Starting...")
    logger.info(f"Server: {os.uname().nodename}")
    
    counter = 0
    try:
        while True:
            counter += 1
            logger.info(f"Heartbeat #{counter} - System running OK")
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("AI Trading Sentinel stopped")

if __name__ == "__main__":
    main()
APPEOF

# Setup Python environment
echo "[5/8] Setting up Python..."
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install flask requests psutil

# Create systemd service
echo "[6/8] Creating service..."
sudo tee /etc/systemd/system/trae.service > /dev/null << "SVCEOF"
[Unit]
Description=AI Trading Sentinel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-trading-sentinel
ExecStart=/opt/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVCEOF

# Set permissions and start
echo "[7/8] Starting service..."
sudo chown -R root:root /opt/ai-trading-sentinel
sudo chmod +x /opt/ai-trading-sentinel/main.py
sudo systemctl daemon-reload
sudo systemctl enable trae
sudo systemctl start trae

# Check status
echo "[8/8] Checking status..."
echo ""
echo "Deployment completed!"
sudo systemctl status trae --no-pager
echo ""
echo "To view logs: sudo journalctl -u trae -f"
echo "To restart: sudo systemctl restart trae"
echo "To stop: sudo systemctl stop trae"
'@

Write-Host "💾 Creating deployment script file..." -ForegroundColor Yellow
$deployScript | Out-File -FilePath "contabo_deploy.sh" -Encoding UTF8
Write-Host "✅ Deployment script created: contabo_deploy.sh" -ForegroundColor Green
Write-Host ""

Write-Host "🎯 Quick Actions:" -ForegroundColor Cyan
Write-Host "1. Test connection: ping $contaboIP" -ForegroundColor White
Write-Host "2. Connect via SSH: ssh $username@$contaboIP" -ForegroundColor White
Write-Host "3. Upload script: scp contabo_deploy.sh $username@${contaboIP}:/tmp/" -ForegroundColor White
Write-Host "4. Run on server: chmod +x /tmp/contabo_deploy.sh && /tmp/contabo_deploy.sh" -ForegroundColor White
Write-Host ""

Write-Host "⚠️  Remember: Run the deployment ON THE CONTABO SERVER, not on Windows!" -ForegroundColor Red
Write-Host ""

# Test connectivity
Write-Host "🔍 Testing connectivity to Contabo server..." -ForegroundColor Yellow
try {
    if (Test-Connection -ComputerName $contaboIP -Count 2 -Quiet) {
        Write-Host "✅ Server $contaboIP is reachable!" -ForegroundColor Green
        Write-Host "You can proceed with SSH connection." -ForegroundColor White
    } else {
        Write-Host "❌ Server $contaboIP is not reachable." -ForegroundColor Red
        Write-Host "Check your internet connection or server status." -ForegroundColor White
    }
} catch {
    Write-Host "⚠️  Could not test connection. Try manual ping." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Green
Write-Host "1. Connect to your Contabo server via SSH" -ForegroundColor White
Write-Host "2. Upload and run the deployment script" -ForegroundColor White
Write-Host "3. Verify the service is running" -ForegroundColor White
Write-Host ""