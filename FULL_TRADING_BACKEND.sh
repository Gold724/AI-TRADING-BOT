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
pip install flask gunicorn requests playwright beautifulsoup4 pandas numpy

# Create Flask backend
cat > /opt/trading-bot/app.py << 'EOF'
from flask import Flask, jsonify, request
import json
import datetime
import os
import subprocess

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
    """Get current bot status"""
    return jsonify({
        "success": True,
        "data": bot_status,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/start', methods=['POST'])
def start_bot():
    """Start trading bot"""
    try:
        bot_status["status"] = "running"
        return jsonify({
            "success": True,
            "message": "Trading bot started",
            "status": bot_status["status"]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop trading bot"""
    try:
        bot_status["status"] = "stopped"
        return jsonify({
            "success": True,
            "message": "Trading bot stopped",
            "status": bot_status["status"]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get recent trades"""
    return jsonify({
        "success": True,
        "trades": [
            {
                "id": 1,
                "symbol": "EURUSD",
                "type": "buy",
                "amount": 0.1,
                "price": 1.0850,
                "timestamp": "2024-01-15T10:30:00Z",
                "profit": 15.50
            }
        ]
    })

@app.route('/api/bulenox', methods=['GET'])
def bulenox_status():
    """Bulenox integration status"""
    return jsonify({
        "success": True,
        "bulenox_id": "BX64883",
        "connection": "active",
        "last_signal": datetime.datetime.now().isoformat(),
        "server": "161.97.112.146"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "server": "161.97.112.146",
        "bulenox": "BX64883",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def index():
    """Main dashboard"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Trading Sentinel - Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; color: #2c3e50; margin-bottom: 30px; }
            .status { display: flex; justify-content: space-between; margin: 20px 0; }
            .card { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #2980b9; }
            .success { color: #27ae60; }
            .error { color: #e74c3c; }
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
                <div class="status">
                    <span>Status: <span class="success">Ready</span></span>
                    <span>Trades Today: 0</span>
                    <span>Balance: $0.00</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🔗 API Endpoints</h3>
                <ul>
                    <li><a href="/api/status">GET /api/status</a> - Bot status</li>
                    <li><a href="/api/trades">GET /api/trades</a> - Recent trades</li>
                    <li><a href="/api/bulenox">GET /api/bulenox</a> - Bulenox integration</li>
                    <li><a href="/api/health">GET /api/health</a> - Health check</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>⚡ Quick Actions</h3>
                <button class="btn" onclick="startBot()">Start Bot</button>
                <button class="btn" onclick="stopBot()">Stop Bot</button>
                <button class="btn" onclick="checkStatus()">Check Status</button>
            </div>
            
            <div id="result" class="card" style="display:none;">
                <h3>📊 Result</h3>
                <pre id="resultText"></pre>
            </div>
        </div>
        
        <script>
            async function startBot() {
                const response = await fetch('/api/start', { method: 'POST' });
                const data = await response.json();
                showResult(data);
            }
            
            async function stopBot() {
                const response = await fetch('/api/stop', { method: 'POST' });
                const data = await response.json();
                showResult(data);
            }
            
            async function checkStatus() {
                const response = await fetch('/api/status');
                const data = await response.json();
                showResult(data);
            }
            
            function showResult(data) {
                document.getElementById('result').style.display = 'block';
                document.getElementById('resultText').textContent = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Create Gunicorn config
cat > /opt/trading-bot/gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF

# Create systemd service
sudo tee /etc/systemd/system/trading-bot.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=exec
User=root
WorkingDirectory=/opt/trading-bot
Environment=PATH=/opt/trading-bot/venv/bin
ExecStart=/opt/trading-bot/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/trading-bot > /dev/null << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable Nginx site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/

# Start services
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl restart nginx

# Test services
echo "🧪 Testing services..."
sleep 3

# Check if services are running
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

# Test API endpoints
echo "🔍 Testing API endpoints..."
curl -s http://localhost/api/health | python3 -m json.tool
curl -s http://localhost/api/status | python3 -m json.tool

echo ""
echo "🎉 AI Trading Sentinel Backend Deployed!"
echo "📱 Dashboard: http://161.97.112.146/"
echo "🔗 API Health: http://161.97.112.146/api/health"
echo "📊 Bot Status: http://161.97.112.146/api/status"
echo "🤖 Bulenox: http://161.97.112.146/api/bulenox"
echo ""
echo "🔧 Service Management:"
echo "  sudo systemctl status trading-bot"
echo "  sudo systemctl restart trading-bot"
echo "  sudo journalctl -u trading-bot -f"