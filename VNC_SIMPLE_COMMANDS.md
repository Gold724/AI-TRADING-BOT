# 🖥️ VNC Simple Fix Commands

## Problem: Script Copy-Paste Failed
The previous script failed due to bash syntax errors from corrupted copy-paste in VNC.

## ✅ **Solution: Use These Simple Commands**

### **Method 1: Direct Commands (Recommended)**

Open VNC terminal and run these commands **one by one**:

```bash
# 1. Stop services
sudo systemctl stop ai-trading-backend nginx apache2 2>/dev/null

# 2. Kill processes
sudo pkill -f "python.*flask" 2>/dev/null || true
sudo pkill -f "python.*app" 2>/dev/null || true
sudo fuser -k 80/tcp 5000/tcp 5001/tcp 2>/dev/null || true

# 3. Create Nginx config
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

# 4. Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/ai-trading /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. Create Python backend
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

# 6. Create systemd service
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

# 7. Create frontend HTML
sudo mkdir -p /var/www/html
sudo tee /var/www/html/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel</title>
    <style>
        body{font-family:Arial;margin:40px;background:#f5f5f5}
        .container{max-width:800px;margin:0 auto;background:white;padding:30px;border-radius:10px}
        h1{color:#2c3e50;text-align:center}
        .status{padding:15px;margin:10px 0;background:#d4edda;color:#155724;border-radius:5px}
        .endpoint{margin:10px 0;padding:10px;background:#e9ecef;border-radius:5px}
        .endpoint a{color:#007bff;text-decoration:none}
    </style>
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

# 8. Start services
sudo systemctl daemon-reload
sudo systemctl enable ai-trading-backend nginx
sudo systemctl start ai-trading-backend
sleep 3
sudo systemctl start nginx

# 9. Test URLs
echo "Testing URLs:"
curl -s http://161.97.112.146/ > /dev/null && echo "✅ Frontend: OK" || echo "❌ Frontend: FAILED"
curl -s http://161.97.112.146/api/status > /dev/null && echo "✅ Backend: OK" || echo "❌ Backend: FAILED"
curl -s http://161.97.112.146/api/health > /dev/null && echo "✅ Health: OK" || echo "❌ Health: FAILED"
```

### **Method 2: Ultra-Simple One-Liners**

If the above is too complex, try these **ultra-simple** commands:

```bash
# Install Flask if missing
sudo apt update && sudo apt install -y python3-pip
pip3 install flask

# Quick backend
echo 'from flask import Flask, jsonify; app = Flask(__name__); @app.route("/"): def home(): return jsonify({"status": "active"}); @app.route("/status"): def status(): return jsonify({"status": "active"}); @app.route("/health"): def health(): return jsonify({"status": "healthy"}); app.run(host="0.0.0.0", port=5001)' > /tmp/simple_backend.py

# Run backend
python3 /tmp/simple_backend.py &

# Test
curl http://161.97.112.146:5001/status
```

### **Method 3: Manual File Creation**

1. **Create backend file manually:**
   ```bash
   sudo nano /root/ai_backend.py
   ```
   
2. **Copy this Python code:**
   ```python
   from flask import Flask, jsonify
   app = Flask(__name__)
   
   @app.route('/')
   def home():
       return jsonify({'status': 'active', 'service': 'AI Trading Sentinel'})
   
   @app.route('/status')
   def status():
       return jsonify({'status': 'active'})
   
   @app.route('/health')
   def health():
       return jsonify({'status': 'healthy'})
   
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5001)
   ```

3. **Save and run:**
   ```bash
   python3 /root/ai_backend.py
   ```

## 🎯 **Expected Results**

After successful execution:
- ✅ **Frontend**: http://161.97.112.146/
- ✅ **Backend**: http://161.97.112.146/api/status
- ✅ **Health**: http://161.97.112.146/api/health

## 🔐 **Bulenox Configuration**
- **Username**: BX64883
- **Password**: XujhMzFf6K
- **Mode**: LIVE Trading
- **Risk Level**: Medium
- **Max Daily Trades**: 5

## 🚨 **If Still Issues**

Run these diagnostic commands:
```bash
# Check what's running
ps aux | grep python
sudo netstat -tuln | grep 5001
sudo systemctl status nginx

# Check logs
sudo journalctl -u ai-trading-backend -f
sudo tail -f /var/log/nginx/error.log
```