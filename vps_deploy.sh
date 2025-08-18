+#!/bin/bash

# TRAE AI Trading Sentinel - VPS Deployment Script
# Ensures Flask backend runs persistently on Ubuntu VPS

set -e

echo "🚀 TRAE VPS Deployment Starting..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx ufw git curl

# Navigate to project directory
cd ~/ai-trading-sentinel

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 5000  # Flask API
sudo ufw --force enable

echo "🔥 Firewall configured for ports 22, 80, 443, 5000"

# Create systemd service for Flask backend
sudo tee /etc/systemd/system/trae-backend.service > /dev/null <<EOF
[Unit]
Description=TRAE AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
Environment=PATH=/root/ai-trading-sentinel/venv/bin
ExecStart=/root/ai-trading-sentinel/venv/bin/python backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable trae-backend
sudo systemctl start trae-backend

echo "🎯 TRAE Backend Service Started"

# Check service status
sudo systemctl status trae-backend --no-pager

# Test API endpoint
echo "🧪 Testing API endpoint..."
sleep 5
curl -f http://localhost:5000/api/health || echo "❌ API not responding"

echo "✅ VPS Deployment Complete!"
echo "📡 Backend accessible at: http://$(curl -s ifconfig.me):5000"
echo "🔍 Check logs: sudo journalctl -u trae-backend -f"
echo "🔄 Restart service: sudo systemctl restart trae-backend"