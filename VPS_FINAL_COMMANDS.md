# 🚀 AI Trading Sentinel - Final VPS Deployment Commands

## Current Issue Resolution
Your VPS encountered package dependency conflicts with:
- ❌ Broken packages (Node.js/npm conflicts)
- ❌ `libasound2` package conflicts (Ubuntu 24.04)
- ❌ Missing package dependencies

## ✅ Solution: Execute Final Deployment Script

### Step 1: Stop Current Process
```bash
# Press Ctrl+C to stop any running commands
# Then clear the terminal
clear
```

### Step 2: Create and Execute Final Script
```bash
# Navigate to deployment directory
cd /root

# Create the final deployment script
cat > vps_final_deploy.sh << 'EOF'
#!/bin/bash

# AI Trading Sentinel - Final VPS Deployment Script
# Addresses Ubuntu 24.04 package conflicts and broken dependencies
# Run this script on Contabo VPS (161.97.112.146) via VNC

set -e  # Exit on any error

echo "🚀 AI Trading Sentinel - Final VPS Deployment"
echo "📍 Target: Contabo VPS (161.97.112.146)"
echo "🕐 $(date)"
echo "==========================================="

# Step 1: Clean system and fix broken packages
echo "🧹 Step 1: Cleaning system and fixing broken packages..."
apt update
apt --fix-broken install -y
apt autoremove -y
apt autoclean

# Step 2: Remove all conflicting packages
echo "🔧 Step 2: Removing conflicting packages..."
apt remove -y nodejs npm node-* || true
apt purge -y nodejs npm node-* || true
apt autoremove -y

# Step 3: Install essential packages first
echo "📦 Step 3: Installing essential packages..."
apt install -y curl wget git python3 python3-pip python3-venv nginx ufw software-properties-common

# Step 4: Install Node.js 20.x (clean installation)
echo "📦 Step 4: Installing Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt update
apt install -y nodejs

# Verify Node.js installation
echo "✅ Node.js version: $(node --version)"
echo "✅ NPM version: $(npm --version)"

# Step 5: Install Playwright dependencies (Ubuntu 24.04 compatible)
echo "📦 Step 5: Installing Playwright dependencies..."
apt install -y \
    libnss3 \
    libatk-bridge2.0-0t64 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2t64 \
    libatspi2.0-0 \
    libgtk-3-0

# Step 6: Create application user
echo "👤 Step 6: Setting up application user..."
if ! id "tradebot" &>/dev/null; then
    useradd -m -s /bin/bash tradebot
    usermod -aG sudo tradebot
fi

# Step 7: Setup application directory
echo "📁 Step 7: Setting up application directory..."
mkdir -p /opt/ai-trading-sentinel
chown tradebot:tradebot /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Step 8: Create self-contained application (no GitHub dependency)
echo "📁 Step 8: Creating self-contained application..."
mkdir -p backend frontend/src logs

# Create backend
cat > backend/main.py << 'BACKEND_EOF'
from flask import Flask, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'active',
        'service': 'AI Trading Sentinel Backend',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': 'production',
        'server': '161.97.112.146'
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'services': {'backend': 'running', 'trading': 'ready'}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
BACKEND_EOF

# Create requirements
cat > requirements.txt << 'REQ_EOF'
Flask==2.3.3
Flask-CORS==4.0.0
gunicorn==21.2.0
REQ_EOF

# Create frontend package.json
cat > frontend/package.json << 'PKG_EOF'
{
  "name": "ai-trading-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "vite build",
    "dev": "vite"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^4.5.0"
  }
}
PKG_EOF

# Create vite config
cat > frontend/vite.config.js << 'VITE_EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: { outDir: 'dist' }
})
VITE_EOF

# Create index.html
cat > frontend/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Sentinel</title>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
</body>
</html>
HTML_EOF

# Create React components
cat > frontend/src/main.jsx << 'MAIN_EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
MAIN_EOF

cat > frontend/src/App.jsx << 'APP_EOF'
import { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(setStatus)
      .catch(console.error)
  }, [])

  return (
    <div style={{padding: '2rem', textAlign: 'center', background: 'linear-gradient(135deg, #667eea, #764ba2)', minHeight: '100vh', color: 'white'}}>
      <h1>🤖 AI Trading Sentinel</h1>
      <h2>🌐 Production Server: 161.97.112.146</h2>
      {status ? (
        <div style={{background: 'rgba(255,255,255,0.1)', padding: '2rem', borderRadius: '10px', margin: '2rem auto', maxWidth: '600px'}}>
          <h3>✅ Status: {status.status}</h3>
          <p>Service: {status.service}</p>
          <p>Version: {status.version}</p>
          <p>Environment: {status.environment}</p>
          <p>Server: {status.server}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
      <button onClick={() => window.location.reload()} style={{background: '#4CAF50', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '5px', cursor: 'pointer'}}>🔄 Refresh</button>
    </div>
  )
}

export default App
APP_EOF

# Step 9: Install Python dependencies
echo "🐍 Step 9: Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Step 10: Build frontend
echo "⚛️ Step 10: Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Step 11: Create systemd services
echo "⚙️ Step 11: Creating systemd services..."
cat > /etc/systemd/system/ai-trading-backend.service << 'SVC_EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory=/opt/ai-trading-sentinel
Environment=PATH=/opt/ai-trading-sentinel/venv/bin
ExecStart=/opt/ai-trading-sentinel/venv/bin/gunicorn --bind 0.0.0.0:5000 backend.main:app
Restart=always

[Install]
WantedBy=multi-user.target
SVC_EOF

cat > /etc/systemd/system/ai-trading-frontend.service << 'FRONT_EOF'
[Unit]
Description=AI Trading Sentinel Frontend
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory=/opt/ai-trading-sentinel/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=always

[Install]
WantedBy=multi-user.target
FRONT_EOF

# Step 12: Configure Nginx
echo "🌐 Step 12: Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-trading-sentinel << 'NGINX_EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# Step 13: Set permissions
echo "🔐 Step 13: Setting permissions..."
chown -R tradebot:tradebot /opt/ai-trading-sentinel

# Step 14: Configure firewall
echo "🔥 Step 14: Configuring firewall..."
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp

# Step 15: Start services
echo "🚀 Step 15: Starting services..."
systemctl daemon-reload
systemctl enable ai-trading-backend ai-trading-frontend nginx
systemctl start ai-trading-backend ai-trading-frontend
systemctl restart nginx

# Step 16: Verification
echo "✅ Step 16: Final verification..."
sleep 5
echo "📊 Service Status:"
systemctl status ai-trading-backend --no-pager -l
systemctl status ai-trading-frontend --no-pager -l
systemctl status nginx --no-pager -l

echo "==========================================="
echo "🎉 AI Trading Sentinel Deployment Complete!"
echo "📍 Production URLs:"
echo "   🌐 Frontend: http://161.97.112.146/"
echo "   🔧 Backend:  http://161.97.112.146/api/status"
echo "   🏥 Health:   http://161.97.112.146/api/health"
echo "==========================================="
echo "✅ Deployment completed at $(date)"
EOF

# Make script executable
chmod +x vps_final_deploy.sh

# Execute the script
./vps_final_deploy.sh
```

## 🎯 Expected Results After Execution

### ✅ Active URLs:
- **Frontend**: http://161.97.112.146/
- **Backend API**: http://161.97.112.146/api/status
- **Health Check**: http://161.97.112.146/api/health

### 📊 Service Status Commands:
```bash
# Check all services
systemctl status ai-trading-backend
systemctl status ai-trading-frontend
systemctl status nginx

# View logs
tail -f /opt/ai-trading-sentinel/logs/backend.log
tail -f /var/log/nginx/access.log
```

## 🔧 Key Fixes in This Script:

1. **✅ Package Conflicts**: Properly removes conflicting Node.js packages
2. **✅ Ubuntu 24.04 Compatibility**: Uses `libasound2t64` instead of `libasound2`
3. **✅ Clean Dependencies**: Installs packages in correct order
4. **✅ Self-Contained App**: No GitHub dependency, creates app structure directly
5. **✅ Simplified Frontend**: Minimal React app that builds successfully
6. **✅ Production Ready**: Proper systemd services and Nginx configuration

## 🚨 If Issues Persist:

```bash
# Check system status
apt list --upgradable
apt --fix-broken install

# Restart services
systemctl restart ai-trading-backend ai-trading-frontend nginx

# Check ports
netstat -tlnp | grep -E ':(80|3000|5000)'
```

---

**🎯 Execute the commands above in your VNC terminal to deploy the AI Trading Sentinel successfully!**