#!/bin/bash

# AI Trading Sentinel - One-Click VPS Deployment
# Run this single command on your Contabo VPS (Ubuntu 24.04)
# Usage: bash vps_one_click_deploy.sh

set -e
echo "🚀 Starting AI Trading Sentinel VPS Deployment..."

# Step 1: System Cleanup & Updates
echo "📦 Updating system packages..."
apt update && apt upgrade -y
apt --fix-broken install -y
apt autoremove -y && apt autoclean

# Step 2: Remove Conflicting Packages
echo "🔧 Removing conflicting Node.js/npm packages..."
apt remove --purge nodejs npm -y 2>/dev/null || true
apt autoremove -y

# Step 3: Install Essential Dependencies
echo "📋 Installing essential packages..."
apt install -y curl wget git python3 python3-pip python3-venv nginx ufw

# Step 4: Install Node.js 20.x
echo "🟢 Installing Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Step 5: Install Playwright Dependencies (Ubuntu 24.04 compatible)
echo "🎭 Installing Playwright dependencies..."
apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 \
  libxdamage1 libxrandr2 libgbm1 libxss1 libasound2t64 libatspi2.0-0 libgtk-3-0

# Step 6: Create User & Directories
echo "👤 Setting up tradebot user..."
useradd -m -s /bin/bash tradebot 2>/dev/null || true
mkdir -p /home/tradebot/ai-trading-sentinel
chown -R tradebot:tradebot /home/tradebot

# Step 7: Switch to tradebot user and setup application
echo "🏗️ Setting up application structure..."
sudo -u tradebot bash << 'EOF'
cd /home/tradebot/ai-trading-sentinel

# Create backend structure
mkdir -p backend logs

# Create Flask backend
cat > backend/main.py << 'BACKEND_EOF'
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'service': 'AI Trading Sentinel Backend',
        'version': '1.0.0'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'health': 'ok',
        'uptime': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    logger.info("Trading start requested")
    return jsonify({'message': 'Trading started', 'status': 'success'})

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    logger.info("Trading stop requested")
    return jsonify({'message': 'Trading stopped', 'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
BACKEND_EOF

# Create requirements.txt
cat > requirements.txt << 'REQ_EOF'
Flask==3.0.0
Flask-CORS==4.0.0
gunicorn==21.2.0
requests==2.31.0
playwright==1.40.0
REQ_EOF

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium

# Create frontend structure
mkdir -p frontend/public frontend/src

# Create package.json
cat > frontend/package.json << 'PKG_EOF'
{
  "name": "ai-trading-sentinel-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "serve": "serve -s dist -l 3000"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8",
    "serve": "^14.2.1"
  }
}
PKG_EOF

# Create Vite config
cat > frontend/vite.config.js << 'VITE_EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0'
  },
  build: {
    outDir: 'dist'
  }
})
VITE_EOF

# Create index.html
cat > frontend/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Trading Sentinel</title>
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
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
MAIN_EOF

cat > frontend/src/App.jsx << 'APP_EOF'
import React, { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState('Loading...')
  const [isTrading, setIsTrading] = useState(false)

  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setStatus(data.status))
      .catch(() => setStatus('Error'))
  }, [])

  const toggleTrading = async () => {
    const endpoint = isTrading ? '/api/trading/stop' : '/api/trading/start'
    try {
      await fetch(endpoint, { method: 'POST' })
      setIsTrading(!isTrading)
    } catch (error) {
      console.error('Trading toggle failed:', error)
    }
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 AI Trading Sentinel</h1>
        <p>Status: <span className={status === 'active' ? 'status-active' : 'status-error'}>{status}</span></p>
        <button 
          onClick={toggleTrading}
          className={isTrading ? 'btn-stop' : 'btn-start'}
        >
          {isTrading ? '⏹️ Stop Trading' : '▶️ Start Trading'}
        </button>
        <div className="info">
          <p>🔗 Backend API: <a href="/api/status" target="_blank">/api/status</a></p>
          <p>💚 Health Check: <a href="/api/health" target="_blank">/api/health</a></p>
        </div>
      </header>
    </div>
  )
}

export default App
APP_EOF

# Create CSS files
cat > frontend/src/App.css << 'CSS_EOF'
.App {
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
}

.App-header h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.status-active { color: #4ade80; font-weight: bold; }
.status-error { color: #f87171; font-weight: bold; }

.btn-start, .btn-stop {
  padding: 15px 30px;
  font-size: 1.2rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin: 20px;
  transition: all 0.3s ease;
}

.btn-start {
  background: #10b981;
  color: white;
}

.btn-stop {
  background: #ef4444;
  color: white;
}

.btn-start:hover, .btn-stop:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.info {
  margin-top: 2rem;
  padding: 1rem;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.info a {
  color: #60a5fa;
  text-decoration: none;
}

.info a:hover {
  text-decoration: underline;
}
CSS_EOF

cat > frontend/src/index.css << 'INDEX_CSS_EOF'
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}
INDEX_CSS_EOF

# Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..

# Create .env file
cat > .env << 'ENV_EOF'
# AI Trading Sentinel Environment Variables
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
HOST=0.0.0.0

# Add your broker credentials here
BROKER_USERNAME=your_username
BROKER_PASSWORD=your_password
BROKER_URL=https://your-broker.com

# Security
SECRET_KEY=your-secret-key-here
ENV_EOF

EOF

# Step 8: Create systemd services
echo "⚙️ Creating systemd services..."

# Backend service
cat > /etc/systemd/system/tradebot-backend.service << 'BACKEND_SERVICE_EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory=/home/tradebot/ai-trading-sentinel
Environment=PATH=/home/tradebot/ai-trading-sentinel/venv/bin
ExecStart=/home/tradebot/ai-trading-sentinel/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 backend.main:app
Restart=always
RestartSec=3
StandardOutput=append:/home/tradebot/ai-trading-sentinel/logs/backend.log
StandardError=append:/home/tradebot/ai-trading-sentinel/logs/backend.log

[Install]
WantedBy=multi-user.target
BACKEND_SERVICE_EOF

# Frontend service
cat > /etc/systemd/system/tradebot-frontend.service << 'FRONTEND_SERVICE_EOF'
[Unit]
Description=AI Trading Sentinel Frontend
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory=/home/tradebot/ai-trading-sentinel/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=always
RestartSec=3
StandardOutput=append:/home/tradebot/ai-trading-sentinel/logs/frontend.log
StandardError=append:/home/tradebot/ai-trading-sentinel/logs/frontend.log

[Install]
WantedBy=multi-user.target
FRONTEND_SERVICE_EOF

# Step 9: Configure Nginx
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/tradebot << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    # Frontend (React app)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX_EOF

# Enable Nginx site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/tradebot /etc/nginx/sites-enabled/
nginx -t

# Step 10: Set Permissions
echo "🔐 Setting permissions..."
chown -R tradebot:tradebot /home/tradebot/ai-trading-sentinel
chmod +x /home/tradebot/ai-trading-sentinel/backend/main.py

# Step 11: Configure Firewall
echo "🔥 Configuring UFW firewall..."
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Step 12: Start Services
echo "🚀 Starting all services..."
systemctl daemon-reload
systemctl enable tradebot-backend tradebot-frontend nginx
systemctl restart tradebot-backend tradebot-frontend nginx

# Step 13: Final Verification
echo "✅ Deployment complete! Verifying services..."
sleep 5

echo "📊 Service Status:"
systemctl is-active tradebot-backend && echo "✅ Backend: Running" || echo "❌ Backend: Failed"
systemctl is-active tradebot-frontend && echo "✅ Frontend: Running" || echo "❌ Frontend: Failed"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Failed"

echo ""
echo "🎉 AI Trading Sentinel Deployed Successfully!"
echo ""
echo "📱 Access URLs:"
echo "   Frontend: http://$(curl -s ifconfig.me)/"
echo "   Backend API: http://$(curl -s ifconfig.me)/api/status"
echo "   Health Check: http://$(curl -s ifconfig.me)/api/health"
echo ""
echo "📋 Useful Commands:"
echo "   Check logs: sudo journalctl -u tradebot-backend -f"
echo "   Restart services: sudo systemctl restart tradebot-backend tradebot-frontend"
echo "   Check status: sudo systemctl status tradebot-backend"
echo ""
echo "🔧 Next Steps:"
echo "   1. Edit /home/tradebot/ai-trading-sentinel/.env with your broker credentials"
echo "   2. Restart services: sudo systemctl restart tradebot-backend"
echo "   3. Monitor logs for any issues"
echo ""
echo "✨ Deployment Complete! Your AI Trading Sentinel is now live! ✨"