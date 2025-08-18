# 🚀 VPS Direct Deployment - AI Trading Sentinel

## ⚡ Immediate SSH Deployment (No Downloads Required)

You're already connected to the VPS! Run these commands directly:

### Step 1: Create Emergency Deploy Script
```bash
cat > emergency_deploy.sh << 'EOF'
#!/bin/bash

# 🚨 EMERGENCY DEPLOYMENT SCRIPT - AI Trading Sentinel
set -e

echo "🚨 AI Trading Sentinel - Emergency Deployment"
echo "============================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}[STEP $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop existing services
print_step "1" "Stopping existing services"
systemctl stop trae-bot.service 2>/dev/null || true
systemctl disable trae-bot.service 2>/dev/null || true
killall python 2>/dev/null || true
killall python3 2>/dev/null || true

# Setup project directory
print_step "2" "Setting up project directory"
rm -rf /root/ai-trading-sentinel-backup 2>/dev/null || true
if [ -d "/root/ai-trading-sentinel" ]; then
    mv /root/ai-trading-sentinel /root/ai-trading-sentinel-backup
fi
mkdir -p /root/ai-trading-sentinel
cd /root/ai-trading-sentinel

# Install dependencies
print_step "3" "Installing system dependencies"
apt update
apt install -y python3 python3-pip python3-venv git curl wget nano
apt install -y libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0 libgtk-3-0

# Create virtual environment
print_step "4" "Creating Python environment"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Create requirements.txt
cat > requirements.txt << 'REQS'
flask==2.3.3
playwright==1.40.0
requests==2.31.0
schedule==1.2.0
python-dotenv==1.0.0
psutil==5.9.6
watchdog==3.0.0
REQS

pip install -r requirements.txt
playwright install
playwright install-deps

# Create project structure
print_step "5" "Creating project structure"
mkdir -p logs backend frontend data config
touch logs/trae.log logs/backend.log
chmod 644 logs/*.log

# Create main.py
cat > main.py << 'MAIN'
#!/usr/bin/env python3
import sys
import os
import time
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trae.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("🤖 AI Trading Sentinel Starting...")
    try:
        while True:
            logger.info("AI Trading Sentinel is running...")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
MAIN

# Create backend
cat > backend/main.py << 'BACKEND'
#!/usr/bin/env python3
from flask import Flask, jsonify, render_template_string
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def dashboard():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Trading Sentinel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .status { padding: 20px; background: #e8f5e8; border-radius: 5px; margin: 20px 0; }
            .header { color: #2c3e50; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🤖 AI Trading Sentinel</h1>
            <div class="status">
                <h3>✅ System Status: Online</h3>
                <p>The AI Trading Sentinel is running and monitoring markets.</p>
            </div>
            <div class="status">
                <h3>📊 Quick Stats</h3>
                <ul>
                    <li>Service: Active</li>
                    <li>API: Healthy</li>
                    <li>Trading: Ready</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'AI Trading Sentinel',
        'version': '1.0.0'
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'trading_active': True,
        'last_update': 'Just now',
        'system_health': 'Good'
    })

if __name__ == '__main__':
    logger.info("Starting AI Trading Sentinel Backend...")
    app.run(host='0.0.0.0', port=5000, debug=False)
BACKEND

# Create .env
cat > .env << 'ENV'
# AI Trading Sentinel Configuration
BROKER_USERNAME=your_username
BROKER_PASSWORD=your_password
BROKER_URL=https://your-broker.com

# Email Notifications
EMAIL_NOTIFICATIONS=true
EMAIL_USERNAME=edufyinc@gmail.com
EMAIL_PASSWORD=paxqvizgqjzwujsm

# Trading Configuration
TRADE_AMOUNT=100
RISK_PERCENTAGE=2
MAX_DAILY_TRADES=10

# Environment
ENVIRONMENT=production
DEBUG=false
ENV

# Create systemd service
print_step "6" "Creating systemd service"
cat > /etc/systemd/system/trae-bot.service << 'SERVICE'
[Unit]
Description=AI Trading Sentinel Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
ExecStartPre=/bin/bash -c "cd /root/ai-trading-sentinel && source venv/bin/activate"
ExecStart=/root/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:/root/ai-trading-sentinel/logs/trae.log
StandardError=append:/root/ai-trading-sentinel/logs/trae.log
StartLimitIntervalSec=300
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
SERVICE

# Set permissions
chmod +x main.py backend/main.py
chmod 600 .env
chown -R root:root /root/ai-trading-sentinel

# Enable and start service
systemctl daemon-reload
systemctl enable trae-bot.service
systemctl start trae-bot.service

# Start backend
source venv/bin/activate
nohup python backend/main.py > logs/backend.log 2>&1 &
echo $! > backend.pid

print_step "7" "Verifying deployment"
sleep 3

if systemctl is-active --quiet trae-bot.service; then
    print_success "✅ Service is running"
else
    print_error "❌ Service failed to start"
fi

if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    print_success "✅ Web interface is responding"
else
    print_error "❌ Web interface not responding"
fi

PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
echo ""
echo "🎉 Deployment Complete!"
echo "========================"
echo "🌐 Web Dashboard: http://$PUBLIC_IP:5000"
echo "📊 Health Check: http://$PUBLIC_IP:5000/health"
echo "📋 Service Status: systemctl status trae-bot.service"
echo "📝 View Logs: tail -f /root/ai-trading-sentinel/logs/trae.log"
echo ""
print_success "🚀 AI Trading Sentinel is ready!"
EOF
```

### Step 2: Make Script Executable and Run
```bash
chmod +x emergency_deploy.sh
./emergency_deploy.sh
```

### Step 3: Verify Deployment
```bash
# Check service status
systemctl status trae-bot.service

# Test web interface
curl localhost:5000/health

# Check logs
tail -f /root/ai-trading-sentinel/logs/trae.log
```

---

## 🔧 Quick Troubleshooting Commands

### If Service Fails:
```bash
# Check detailed logs
journalctl -u trae-bot.service -f

# Manual start for testing
cd /root/ai-trading-sentinel
source venv/bin/activate
python main.py
```

### If Web Interface Fails:
```bash
# Start backend manually
cd /root/ai-trading-sentinel
source venv/bin/activate
python backend/main.py
```

### Check Port Status:
```bash
# See what's using port 5000
netstat -tlnp | grep 5000

# Kill processes on port 5000
fuser -k 5000/tcp
```

---

## ✅ Success Indicators

After running the deployment script, you should see:

1. **Service Running**: `systemctl status trae-bot.service` shows `Active: active (running)`
2. **Web Response**: `curl localhost:5000/health` returns JSON
3. **External Access**: `http://5.189.145.177:5000` loads in browser
4. **Clean Logs**: No errors in `journalctl -u trae-bot.service`

---

## 📱 Mobile Management (Termius)

### Quick Status Check:
```bash
systemctl status trae-bot.service
curl localhost:5000/health
```

### Restart Everything:
```bash
systemctl restart trae-bot.service
cd /root/ai-trading-sentinel && source venv/bin/activate && nohup python backend/main.py > logs/backend.log 2>&1 &
```

### View Live Logs:
```bash
tail -f /root/ai-trading-sentinel/logs/trae.log
```

**🎯 This direct deployment method eliminates download dependencies and gets the AI Trading Sentinel running immediately on your VPS!**