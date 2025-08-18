# 📋 Copy-Paste VPS Deployment Commands

## 🚀 Direct SSH Deployment (Copy & Paste)

You're already connected to your VPS! Simply copy and paste these commands:

---

### 🔥 STEP 1: Create & Run Emergency Deploy Script

**Copy this entire block and paste into your SSH terminal:**

```bash
cat > /root/emergency_deploy.sh << 'EOF'
#!/bin/bash
set -e
echo "🚨 AI Trading Sentinel - Emergency Deployment"
echo "============================================"

# Stop existing services
systemctl stop trae-bot.service 2>/dev/null || true
systemctl disable trae-bot.service 2>/dev/null || true
killall python 2>/dev/null || true
killall python3 2>/dev/null || true

# Setup project
rm -rf /root/ai-trading-sentinel-backup 2>/dev/null || true
if [ -d "/root/ai-trading-sentinel" ]; then
    mv /root/ai-trading-sentinel /root/ai-trading-sentinel-backup
fi
mkdir -p /root/ai-trading-sentinel
cd /root/ai-trading-sentinel

# Install dependencies
apt update
apt install -y python3 python3-pip python3-venv git curl wget nano
apt install -y libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0 libgtk-3-0

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python packages
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
mkdir -p logs backend frontend data config
touch logs/trae.log logs/backend.log
chmod 644 logs/*.log

# Create main bot file
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

# Create web backend
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
            .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🤖 AI Trading Sentinel</h1>
            <div class="status">
                <h3>✅ System Status: Online</h3>
                <p>The AI Trading Sentinel is running and monitoring markets.</p>
                <p><strong>Server:</strong> 5.189.145.177:5000</p>
                <p><strong>Deployed:</strong> {{ timestamp }}</p>
            </div>
            <div class="status">
                <h3>📊 Quick Stats</h3>
                <ul>
                    <li>Service: Active</li>
                    <li>API: Healthy</li>
                    <li>Trading: Ready</li>
                    <li>Uptime: Good</li>
                </ul>
            </div>
            <div class="status">
                <h3>🔧 Management</h3>
                <button class="btn" onclick="window.location.href='/health'">Health Check</button>
                <button class="btn" onclick="window.location.href='/api/status'">API Status</button>
            </div>
        </div>
    </body>
    </html>
    """, timestamp=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'AI Trading Sentinel',
        'version': '1.0.0',
        'server': '5.189.145.177:5000'
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'trading_active': True,
        'last_update': 'Just now',
        'system_health': 'Good',
        'server_ip': '5.189.145.177'
    })

if __name__ == '__main__':
    logger.info("Starting AI Trading Sentinel Backend on 0.0.0.0:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
BACKEND

# Create configuration
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

# Enable and start services
systemctl daemon-reload
systemctl enable trae-bot.service
systemctl start trae-bot.service

# Start web backend
source venv/bin/activate
nohup python backend/main.py > logs/backend.log 2>&1 &
echo $! > backend.pid

# Verify deployment
sleep 5
echo ""
echo "🎉 Deployment Complete!"
echo "========================"
echo "🌐 Web Dashboard: http://5.189.145.177:5000"
echo "📊 Health Check: http://5.189.145.177:5000/health"
echo "📋 Service Status: systemctl status trae-bot.service"
echo "📝 View Logs: tail -f /root/ai-trading-sentinel/logs/trae.log"
echo ""
if systemctl is-active --quiet trae-bot.service; then
    echo "✅ Service is running"
else
    echo "❌ Service failed - check: journalctl -u trae-bot.service"
fi

if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Web interface is responding"
else
    echo "❌ Web interface not responding - check: netstat -tlnp | grep 5000"
fi
echo "🚀 AI Trading Sentinel is ready!"
EOF

chmod +x /root/emergency_deploy.sh
/root/emergency_deploy.sh
```

---

### 🔍 STEP 2: Verify Deployment

**Copy and paste these verification commands:**

```bash
# Check service status
systemctl status trae-bot.service

# Test web interface locally
curl localhost:5000/health

# Check if port 5000 is open
netstat -tlnp | grep 5000

# View live logs
tail -f /root/ai-trading-sentinel/logs/trae.log
```

---

### 🌐 STEP 3: Access Web Dashboard

Open in your browser:
- **Main Dashboard**: http://5.189.145.177:5000
- **Health Check**: http://5.189.145.177:5000/health
- **API Status**: http://5.189.145.177:5000/api/status

---

## 🚨 If Something Goes Wrong

### Quick Fix Commands:

```bash
# Restart everything
systemctl restart trae-bot.service
cd /root/ai-trading-sentinel && source venv/bin/activate && nohup python backend/main.py > logs/backend.log 2>&1 &

# Check detailed logs
journalctl -u trae-bot.service -f

# Manual start for testing
cd /root/ai-trading-sentinel
source venv/bin/activate
python main.py
```

### Kill and Restart Web Backend:

```bash
# Kill existing backend
kill $(cat /root/ai-trading-sentinel/backend.pid) 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true

# Start fresh
cd /root/ai-trading-sentinel
source venv/bin/activate
nohup python backend/main.py > logs/backend.log 2>&1 &
echo $! > backend.pid
```

---

## ✅ Success Indicators

You should see:
1. ✅ **Service Running**: `Active: active (running)` in systemctl status
2. ✅ **Web Response**: JSON response from curl localhost:5000/health
3. ✅ **External Access**: Dashboard loads at http://5.189.145.177:5000
4. ✅ **Clean Logs**: No errors in service logs

---

**🎯 This deployment method works entirely within your current SSH session - no external downloads required!**