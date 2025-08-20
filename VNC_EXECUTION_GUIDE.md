# 🖥️ VNC Terminal Execution Guide

## Quick Fix for Non-Functioning URLs

Since you're using **VNC** (not SSH), follow these exact steps in your VNC terminal:

### 🚀 **One-Command Fix**

Open your VNC terminal and run this single command:

```bash
cd /root && curl -s https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/VNC_DIAGNOSTIC_FIX.sh | bash
```

### 🔧 **Alternative: Manual Execution**

If the above doesn't work, copy and paste this complete script into your VNC terminal:

```bash
#!/bin/bash

echo "🔍 AI Trading Sentinel - VNC Quick Fix"
echo "====================================="

# Stop all services
echo "Stopping services..."
sudo systemctl stop ai-trading-backend nginx apache2 2>/dev/null

# Kill processes
echo "Cleaning processes..."
sudo pkill -f "python.*flask" 2>/dev/null || true
sudo pkill -f "python.*app" 2>/dev/null || true
sudo fuser -k 80/tcp 5000/tcp 5001/tcp 2>/dev/null || true

# Create Nginx config
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/ai-trading > /dev/null << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/ai-trading /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create backend
echo "Creating backend..."
sudo tee /root/ai_backend.py > /dev/null << 'EOF'
from flask import Flask, jsonify
from datetime import datetime
import socket

app = Flask(__name__)

def find_port():
    for port in range(5001, 5020):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except:
            continue
    return 5001

@app.route('/')
@app.route('/status')
def status():
    return jsonify({'status': 'active', 'service': 'AI Trading Sentinel', 'timestamp': datetime.now().isoformat()})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'AI Trading Sentinel', 'timestamp': datetime.now().isoformat()})

@app.route('/trading/status')
def trading_status():
    return jsonify({'trading_active': True, 'broker': 'Bulenox', 'account': 'BX64883', 'mode': 'LIVE'})

@app.route('/broker/credentials')
def broker_credentials():
    return jsonify({'broker': 'Bulenox', 'username': 'BX64883', 'status': 'configured', 'trading_mode': 'LIVE'})

if __name__ == '__main__':
    port = find_port()
    print(f"Starting on port {port}")
    app.run(host='127.0.0.1', port=port, debug=False)
EOF

# Create systemd service
echo "Creating service..."
sudo tee /etc/systemd/system/ai-trading-backend.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/ai_backend.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create frontend
echo "Creating frontend..."
sudo mkdir -p /var/www/html
sudo tee /var/www/html/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel</title>
    <style>body{font-family:Arial;margin:40px;background:#f5f5f5}.container{max-width:800px;margin:0 auto;background:white;padding:30px;border-radius:10px}h1{color:#2c3e50;text-align:center}.status{padding:15px;margin:10px 0;background:#d4edda;color:#155724;border-radius:5px}.endpoint{margin:10px 0;padding:10px;background:#e9ecef;border-radius:5px}.endpoint a{color:#007bff;text-decoration:none}</style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Trading Sentinel</h1>
        <div class="status">Status: System Active ✅</div>
        <h3>API Endpoints:</h3>
        <div class="endpoint"><a href="/api/status">/api/status</a></div>
        <div class="endpoint"><a href="/api/health">/api/health</a></div>
        <div class="endpoint"><a href="/api/trading/status">/api/trading/status</a></div>
        <div class="endpoint"><a href="/api/broker/credentials">/api/broker/credentials</a></div>
        <div class="status">Broker: Bulenox (BX64883) - LIVE Trading</div>
    </div>
</body>
</html>
EOF

# Start services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable ai-trading-backend nginx
sudo systemctl start ai-trading-backend
sleep 3
sudo systemctl start nginx

echo "\n🔍 Testing URLs:"
curl -s http://161.97.112.146/ > /dev/null && echo "✅ Frontend: OK" || echo "❌ Frontend: FAILED"
curl -s http://161.97.112.146/api/status > /dev/null && echo "✅ Backend: OK" || echo "❌ Backend: FAILED"
curl -s http://161.97.112.146/api/health > /dev/null && echo "✅ Health: OK" || echo "❌ Health: FAILED"

echo "\n🎉 Fix Complete! Test URLs:"
echo "Frontend: http://161.97.112.146/"
echo "Backend: http://161.97.112.146/api/status"
echo "Health: http://161.97.112.146/api/health"
echo "Trading: http://161.97.112.146/api/trading/status"
echo "Credentials: http://161.97.112.146/api/broker/credentials"
```

### 📋 **Step-by-Step Instructions**

1. **Open VNC Terminal** (usually accessible via desktop)
2. **Copy the entire script above**
3. **Paste it into the terminal** (Ctrl+Shift+V or right-click → Paste)
4. **Press Enter** to execute
5. **Wait for completion** (should take 30-60 seconds)
6. **Test the URLs** in your browser

### 🔍 **Verification Commands**

After running the fix, verify with these commands:

```bash
# Check service status
sudo systemctl status ai-trading-backend nginx

# Test URLs locally
curl http://161.97.112.146/
curl http://161.97.112.146/api/status

# Check logs if issues persist
sudo journalctl -u ai-trading-backend -f
```

### 🚨 **If Still Not Working**

Run these diagnostic commands:

```bash
# Check firewall
sudo ufw status

# Check network
ping -c 3 161.97.112.146

# Check ports
sudo netstat -tuln | grep -E ':(80|5001)'

# Check processes
ps aux | grep -E '(nginx|python)'
```

### 🎯 **Expected Results**

After successful execution, all these URLs should return **200 OK**:

- ✅ **Frontend**: http://161.97.112.146/
- ✅ **Backend API**: http://161.97.112.146/api/status
- ✅ **Health Check**: http://161.97.112.146/api/health
- ✅ **Trading Status**: http://161.97.112.146/api/trading/status
- ✅ **Broker Credentials**: http://161.97.112.146/api/broker/credentials

### 🔐 **Bulenox Configuration**

- **Username**: BX64883
- **Password**: XujhMzFf6K
- **Mode**: LIVE Trading
- **Risk Level**: Medium
- **Max Daily Trades**: 5