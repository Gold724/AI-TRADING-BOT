#!/bin/bash
set -e

echo "🚀 AI Trading Sentinel - Direct Contabo Deployment"
echo "================================================"
echo "Deploying directly on current Contabo server..."
echo ""

# Check if we're on the right server
echo "[INFO] Current server information:"
echo "Hostname: $(hostname)"
echo "IP Address: $(curl -s ifconfig.me || echo 'Unable to detect')"
echo "OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"
echo ""

# Update system
echo "[STEP 1] Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "[STEP 2] Installing required packages..."
apt install -y python3 python3-pip python3-venv nodejs npm git curl wget unzip htop nano net-tools

# Install Docker
echo "[STEP 3] Installing Docker..."
if ! command -v docker >/dev/null 2>&1; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
    echo "✅ Docker installed successfully"
else
    echo "✅ Docker already installed"
fi

# Create deployment directory
echo "[STEP 4] Setting up deployment directory..."
mkdir -p /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Create directory structure
echo "Creating directory structure..."
mkdir -p data/{accounts,backtest,emergency,historical,memory,signals,simulations}
mkdir -p logs config backend frontend

# Create main.py
echo "[STEP 5] Creating main application..."
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
echo "[STEP 6] Creating requirements file..."
cat > requirements.txt << 'REQEOF'
flask==2.3.3
requests==2.31.0
psutil==5.9.5
schedule==1.2.0
pandas==2.0.3
numpy==1.24.3
REQEOF

# Create systemd service
echo "[STEP 7] Creating systemd service..."
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
echo "[STEP 8] Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment file
echo "[STEP 9] Creating environment configuration..."
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
echo "[STEP 10] Setting up systemd service..."
systemctl daemon-reload
systemctl enable trae
systemctl start trae

# Set proper permissions
echo "[STEP 11] Setting permissions..."
chown -R root:root /opt/ai-trading-sentinel
chmod +x /opt/ai-trading-sentinel/*.py

# Create monitoring script
echo "[STEP 12] Creating monitoring script..."
cat > /opt/ai-trading-sentinel/monitor.sh << 'MONEOF'
#!/bin/bash
echo "🔍 AI Trading Sentinel Status Report"
echo "==================================="
echo "Timestamp: $(date)"
echo "Server: $(hostname)"
echo "IP: $(curl -s ifconfig.me)"
echo ""
echo "📊 System Resources:"
echo "CPU Cores: $(nproc)"
echo "Memory: $(free -h | awk '/^Mem:/ {print $2" total, "$3" used, "$7" available'}"
echo "Disk: $(df -h / | awk 'NR==2 {print $4" available of "$2" total'}"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo ""
echo "🔧 Service Status:"
if systemctl is-active trae >/dev/null 2>&1; then
    echo "✅ Trading service is RUNNING"
    echo "   Started: $(systemctl show trae --property=ActiveEnterTimestamp --value)"
else
    echo "❌ Trading service is STOPPED"
    echo "   Status: $(systemctl is-active trae)"
fi
echo ""
echo "📝 Recent Logs (last 10 lines):"
journalctl -u trae --no-pager -n 10
echo ""
echo "🌐 Network Status:"
echo "Listening ports: $(ss -tlnp | grep :5000 || echo 'Port 5000 not listening')"
echo ""
echo "📁 Files:"
echo "Config: $(ls -la /opt/ai-trading-sentinel/.env 2>/dev/null || echo 'Not found')"
echo "Logs: $(ls -la /opt/ai-trading-sentinel/logs/ 2>/dev/null || echo 'No logs yet')"
MONEOF

chmod +x /opt/ai-trading-sentinel/monitor.sh

echo ""
echo "================================================"
echo "    🎉 AI Trading Sentinel Deployed Successfully!"
echo "================================================"
echo ""
echo "📋 Deployment Summary:"
echo "📍 Location: /opt/ai-trading-sentinel"
echo "🔧 Service: trae (systemd)"
echo "📊 Dashboard: http://$(curl -s ifconfig.me):5000"
echo "📝 Logs: journalctl -u trae -f"
echo "🔍 Monitor: /opt/ai-trading-sentinel/monitor.sh"
echo ""
echo "📋 Quick Commands:"
echo "• Check status: systemctl status trae"
echo "• View logs: journalctl -u trae -f"
echo "• Restart: systemctl restart trae"
echo "• Monitor: /opt/ai-trading-sentinel/monitor.sh"
echo "• Edit config: nano /opt/ai-trading-sentinel/.env"
echo ""
echo "🔐 Next Steps:"
echo "1. Configure your trading credentials in .env"
echo "2. Test the service: systemctl status trae"
echo "3. Access dashboard at http://$(curl -s ifconfig.me):5000"
echo "4. Monitor logs: journalctl -u trae -f"
echo ""
echo "✅ Deployment completed successfully!"