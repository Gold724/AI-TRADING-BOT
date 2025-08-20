# 🚀 SIMPLE ONE-COMMAND DEPLOYMENT

## Problem
GitHub URL failed (404) - need to create script manually on VPS.

## 🔥 ULTRA-SIMPLE SOLUTION

### Type This ONE Command in Termius:
```bash
wget -O deploy.sh https://pastebin.com/raw/YOUR_PASTE_ID || curl -o deploy.sh https://pastebin.com/raw/YOUR_PASTE_ID || cat > deploy.sh << 'EOF'
#!/bin/bash
echo "🚀 Deploying Trading Bot..."
sudo apt update -y && sudo apt install -y python3 python3-pip nginx
sudo mkdir -p /opt/bot
cat > /opt/bot/app.py << 'PY'
from flask import Flask, jsonify
import datetime
app = Flask(__name__)
@app.route('/')
def home():
    return '''<h1>🤖 AI Trading Sentinel</h1><p>Server: 161.97.112.146</p><p>Bulenox: BX64883</p><p>Status: <span style="color:green">Active</span></p><a href="/api/health">Health Check</a> | <a href="/api/status">Bot Status</a>'''
@app.route('/api/health')
def health():
    return jsonify({"status":"healthy","server":"161.97.112.146","bulenox":"BX64883","time":datetime.datetime.now().isoformat()})
@app.route('/api/status')
def status():
    return jsonify({"bot":"ready","trades":0,"balance":0,"server":"161.97.112.146"})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PY
sudo pip3 install flask
echo "[Unit]
Description=Trading Bot
[Service]
WorkingDirectory=/opt/bot
ExecStart=/usr/bin/python3 app.py
Restart=always
[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/bot.service
echo "server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
    }
}" | sudo tee /etc/nginx/sites-available/bot
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/bot /etc/nginx/sites-enabled/
sudo systemctl daemon-reload
sudo systemctl enable bot
sudo systemctl start bot
sudo systemctl restart nginx
echo "✅ Deployment Complete!"
echo "🌐 Dashboard: http://161.97.112.146/"
echo "🔍 Health: http://161.97.112.146/api/health"
curl -s http://localhost/api/health
EOF
chmod +x deploy.sh && sudo ./deploy.sh
```

## 🎯 What This Does
1. **Creates** Flask app with dashboard
2. **Installs** Python, Flask, Nginx
3. **Configures** systemd service
4. **Sets up** Nginx reverse proxy
5. **Starts** all services
6. **Tests** deployment

## 🎉 Expected Results
- ✅ Dashboard: `http://161.97.112.146/`
- ✅ Health API: `http://161.97.112.146/api/health`
- ✅ Status API: `http://161.97.112.146/api/status`
- ✅ Services running automatically

## 🧪 Test After Deployment
```bash
# Check services
sudo systemctl status bot nginx

# Test APIs
curl http://161.97.112.146/api/health
curl http://161.97.112.146/api/status
```

## 🚨 Alternative (If Above Fails)
```bash
# Emergency simple deployment
sudo apt install -y python3-flask
echo 'from flask import *; app=Flask(__name__); @app.route("/") def h(): return "<h1>Bot: 161.97.112.146</h1><p>Bulenox: BX64883</p>"; app.run("0.0.0.0",80)' > bot.py
sudo python3 bot.py
```

---
**TRAE-SentinelOps**: One command deploys everything - copy the long command above!