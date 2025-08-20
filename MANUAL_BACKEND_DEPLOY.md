# 🚀 MANUAL BACKEND DEPLOYMENT

## Problem
The GitHub URL was a placeholder - we need to create the script manually on the VPS.

## 🔥 SOLUTION: Type These Commands in Termius

### Step 1: Create the Deployment Script
```bash
cat > FULL_TRADING_BACKEND.sh << 'EOF'
#!/bin/bash

echo "🚀 Deploying AI Trading Sentinel Backend..."

# Stop existing services
sudo systemctl stop nginx 2>/dev/null
sudo pkill -f python 2>/dev/null
sudo pkill -f gunicorn 2>/dev/null

# Create directories
sudo mkdir -p /opt/trading-bot
sudo mkdir -p /var/log/trading-bot
sudo mkdir -p /var/www/html/api

# Install Python dependencies
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv nginx

# Create virtual environment
cd /opt/trading-bot
sudo python3 -m venv venv
sudo chown -R $USER:$USER /opt/trading-bot

# Activate venv and install packages
source venv/bin/activate
pip install flask gunicorn requests

# Create Flask backend
cat > /opt/trading-bot/app.py << 'PYEOF'
from flask import Flask, jsonify, request
import json
import datetime
import os

app = Flask(__name__)

# Trading bot status
bot_status = {
    "status": "ready",
    "last_trade": None,
    "balance": 0.0,
    "trades_today": 0,
    "bulenox_id": "BX64883",
    "server_ip": "161.97.112.146"
}

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "success": True,
        "data": bot_status,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "server": "161.97.112.146",
        "bulenox": "BX64883",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .header { text-align: center; color: #2c3e50; }
        .card { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .success { color: #27ae60; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Trading Sentinel</h1>
            <p>Server: 161.97.112.146 | Bulenox: BX64883</p>
        </div>
        <div class="card">
            <h3>🎯 Bot Status</h3>
            <p>Status: <span class="success">Ready</span></p>
            <p>Backend: <span class="success">Active</span></p>
        </div>
        <div class="card">
            <h3>🔗 API Endpoints</h3>
            <ul>
                <li><a href="/api/status">GET /api/status</a> - Bot status</li>
                <li><a href="/api/health">GET /api/health</a> - Health check</li>
            </ul>
        </div>
    </div>
</body>
</html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

# Create systemd service
sudo tee /etc/systemd/system/trading-bot.service > /dev/null << 'SVCEOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/trading-bot
Environment=PATH=/opt/trading-bot/venv/bin
ExecStart=/opt/trading-bot/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/trading-bot > /dev/null << 'NGXEOF'
server {
    listen 80;
    server_name 161.97.112.146;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGXEOF

# Enable Nginx site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/

# Start services
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl restart nginx

echo "🧪 Testing services..."
sleep 3

# Test services
if systemctl is-active --quiet trading-bot; then
    echo "✅ Trading bot service: RUNNING"
else
    echo "❌ Trading bot service: FAILED"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service: RUNNING"
else
    echo "❌ Nginx service: FAILED"
fi

echo "🔍 Testing API endpoints..."
curl -s http://localhost/api/health
echo ""
curl -s http://localhost/api/status

echo ""
echo "🎉 AI Trading Sentinel Backend Deployed!"
echo "📱 Dashboard: http://161.97.112.146/"
echo "🔗 API Health: http://161.97.112.146/api/health"
echo "📊 Bot Status: http://161.97.112.146/api/status"
EOF
```

### Step 2: Make Executable and Run
```bash
chmod +x FULL_TRADING_BACKEND.sh
sudo ./FULL_TRADING_BACKEND.sh
```

## 🎯 Expected Results
- ✅ Flask backend installed and running
- ✅ Systemd service created and active
- ✅ Nginx configured as reverse proxy
- ✅ Dashboard accessible at `http://161.97.112.146/`
- ✅ API endpoints working

## 🧪 Test Commands After Deployment
```bash
# Test health
curl http://161.97.112.146/api/health

# Test status
curl http://161.97.112.146/api/status

# Check services
sudo systemctl status trading-bot
sudo systemctl status nginx
```

## 🚨 If Issues Occur
```bash
# Check logs
sudo journalctl -u trading-bot -n 20
sudo nginx -t

# Restart services
sudo systemctl restart trading-bot nginx
```

---
**TRAE-SentinelOps**: Manual deployment script ready - copy and paste the commands above!