# AI Trading Sentinel - Deploy on Current Contabo Server
# This script uploads and runs the deployment on your current server

Write-Host "🚀 AI Trading Sentinel - Contabo Direct Deployment" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""

# Since you're already on the Contabo server, we'll create a simple deployment
# that works with your current server setup

$deployScript = @'
#!/bin/bash
set -e

echo "🚀 AI Trading Sentinel - Direct Deployment"
echo "========================================="
echo "Deploying on current server: $(hostname)"
echo "IP Address: $(curl -s ifconfig.me 2>/dev/null || echo 'localhost')"
echo ""

# Update system
echo "[1/10] Updating system..."
sudo apt update -y

# Install packages
echo "[2/10] Installing packages..."
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Create directory
echo "[3/10] Creating directory..."
sudo mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Create main app
echo "[4/10] Creating main application..."
sudo tee main.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import os
import sys
import logging
import time
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/trading.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 AI Trading Sentinel Starting...")
    logger.info(f"Server: {os.uname().nodename}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    
    try:
        while True:
            logger.info("💓 System running - Heartbeat OK")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        logger.info("👋 AI Trading Sentinel stopped")

if __name__ == "__main__":
    main()
EOF

# Create requirements
echo "[5/10] Creating requirements..."
sudo tee requirements.txt > /dev/null << 'EOF'
flask==2.3.3
requests==2.31.0
psutil==5.9.5
EOF

# Setup Python environment
echo "[6/10] Setting up Python environment..."
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt

# Create systemd service
echo "[7/10] Creating systemd service..."
sudo tee /etc/systemd/system/trae.service > /dev/null << 'EOF'
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

# Set permissions
echo "[8/10] Setting permissions..."
sudo chown -R root:root /opt/ai-trading-sentinel
sudo chmod +x /opt/ai-trading-sentinel/main.py

# Enable service
echo "[9/10] Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable trae
sudo systemctl start trae

# Final status
echo "[10/10] Checking status..."
echo ""
echo "✅ Deployment completed!"
echo "📍 Location: /opt/ai-trading-sentinel"
echo "🔧 Service: $(sudo systemctl is-active trae)"
echo "📊 Status: $(sudo systemctl status trae --no-pager -l)"
echo "📝 Logs: sudo journalctl -u trae -f"
echo ""
'@

Write-Host "[INFO] Creating deployment script..." -ForegroundColor Yellow
$deployScript | Out-File -FilePath "deploy_local.sh" -Encoding UTF8

Write-Host "[INFO] Deployment script created: deploy_local.sh" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Copy this script to your Contabo server" -ForegroundColor White
Write-Host "2. Run: chmod +x deploy_local.sh; ./deploy_local.sh" -ForegroundColor White
Write-Host "3. Check status: sudo systemctl status trae" -ForegroundColor White
Write-Host "4. View logs: sudo journalctl -u trae -f" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Manual Commands for your current server:" -ForegroundColor Cyan
Write-Host "sudo mkdir -p /opt/ai-trading-sentinel" -ForegroundColor Gray
Write-Host "cd /opt/ai-trading-sentinel" -ForegroundColor Gray
Write-Host "sudo apt update && sudo apt install -y python3 python3-pip python3-venv" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Ready for deployment on your Contabo server!" -ForegroundColor Green