# Simple Deployment Guide for AI Trading Sentinel on Contabo
# This script provides clear instructions without embedding bash code

Write-Host "AI Trading Sentinel - Contabo Deployment Guide" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

$contaboIP = "161.97.112.146"
$username = "root"

Write-Host "IMPORTANT: You are on Windows, but need to deploy to Linux!" -ForegroundColor Red
Write-Host "Follow these steps to deploy on your Contabo server:" -ForegroundColor Green
Write-Host ""

# Test connectivity first
Write-Host "Step 1: Testing connectivity..." -ForegroundColor Yellow
try {
    if (Test-Connection -ComputerName $contaboIP -Count 2 -Quiet) {
        Write-Host "SUCCESS: Server $contaboIP is reachable!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Server $contaboIP is not reachable." -ForegroundColor Red
        Write-Host "Check your internet connection or server status." -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "WARNING: Could not test connection automatically." -ForegroundColor Yellow
    Write-Host "Try manual ping: ping $contaboIP" -ForegroundColor White
}

Write-Host ""
Write-Host "Step 2: Connect to your Contabo server" -ForegroundColor Yellow
Write-Host "Run ONE of these SSH commands:" -ForegroundColor White
Write-Host ""
Write-Host "Option A (Standard):" -ForegroundColor Cyan
Write-Host "ssh $username@$contaboIP" -ForegroundColor Gray
Write-Host ""
Write-Host "Option B (Force Password):" -ForegroundColor Cyan
Write-Host "ssh -o PreferredAuthentications=password $username@$contaboIP" -ForegroundColor Gray
Write-Host ""
Write-Host "Option C (Different Port):" -ForegroundColor Cyan
Write-Host "ssh -p 2222 $username@$contaboIP" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 3: Create deployment script on Contabo" -ForegroundColor Yellow
Write-Host "Once connected to your server, create the deployment script:" -ForegroundColor White
Write-Host ""
Write-Host "nano deploy.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "Then copy and paste this content into the file:" -ForegroundColor White
Write-Host ""

# Create the deployment script content as a separate file
$scriptContent = @'
#!/bin/bash
# AI Trading Sentinel Deployment Script
echo "Starting AI Trading Sentinel deployment..."

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

# Create main.py
echo "[4/8] Creating main application..."
sudo cat > main.py << "EOF"
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
EOF

# Setup Python environment
echo "[5/8] Setting up Python environment..."
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install flask requests psutil

# Create systemd service
echo "[6/8] Creating systemd service..."
sudo cat > /etc/systemd/system/trae.service << "EOF"
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
EOF

# Set permissions and start service
echo "[7/8] Starting service..."
sudo chown -R root:root /opt/ai-trading-sentinel
sudo chmod +x /opt/ai-trading-sentinel/main.py
sudo systemctl daemon-reload
sudo systemctl enable trae
sudo systemctl start trae

# Check status
echo "[8/8] Checking deployment status..."
echo ""
echo "SUCCESS: Deployment completed!"
sudo systemctl status trae --no-pager
echo ""
echo "Service Management Commands:"
echo "View logs: sudo journalctl -u trae -f"
echo "Restart: sudo systemctl restart trae"
echo "Stop: sudo systemctl stop trae"
echo "Status: sudo systemctl status trae"
'@

# Save the script content to a file
$scriptContent | Out-File -FilePath "contabo_deploy_script.txt" -Encoding UTF8

Write-Host "SUCCESS: Deployment script saved to: contabo_deploy_script.txt" -ForegroundColor Green
Write-Host "You can copy the content from this file and paste it into nano on your server." -ForegroundColor White
Write-Host ""

Write-Host "Step 4: Execute the deployment" -ForegroundColor Yellow
Write-Host "After creating the script file on your server:" -ForegroundColor White
Write-Host ""
Write-Host "chmod +x deploy.sh" -ForegroundColor Gray
Write-Host "./deploy.sh" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 5: Verify deployment" -ForegroundColor Yellow
Write-Host "Check if the service is running:" -ForegroundColor White
Write-Host ""
Write-Host "sudo systemctl status trae" -ForegroundColor Gray
Write-Host "sudo journalctl -u trae -f" -ForegroundColor Gray
Write-Host ""

Write-Host "Summary:" -ForegroundColor Green
Write-Host "1. Server connectivity tested" -ForegroundColor White
Write-Host "2. SSH connection commands provided" -ForegroundColor White
Write-Host "3. Deployment script created: contabo_deploy_script.txt" -ForegroundColor White
Write-Host "4. Step-by-step instructions provided" -ForegroundColor White
Write-Host ""
Write-Host "REMEMBER: Execute the deployment script ON YOUR CONTABO SERVER!" -ForegroundColor Red
Write-Host ""