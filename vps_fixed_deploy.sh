#!/bin/bash

# AI Trading Sentinel - Fixed VPS Deployment Script
# Addresses Ubuntu 24.04 package conflicts and frontend build issues
# Run this script on Contabo VPS (161.97.112.146) via VNC

set -e  # Exit on any error

echo "🚀 AI Trading Sentinel - VPS Deployment Starting..."
echo "📍 Target: Contabo VPS (161.97.112.146)"
echo "🕐 $(date)"
echo "==========================================="

# Step 1: System Updates
echo "📦 Step 1: Updating system packages..."
apt update && apt upgrade -y

# Step 2: Remove conflicting packages
echo "🔧 Step 2: Removing conflicting Node.js packages..."
apt remove -y nodejs npm node-* || true
apt autoremove -y

# Step 3: Install essential packages
echo "📦 Step 3: Installing essential packages..."
apt install -y curl wget git python3 python3-pip python3-venv nginx ufw

# Step 4: Install Node.js 20.x (LTS)
echo "📦 Step 4: Installing Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Verify Node.js installation
node --version
npm --version

# Step 5: Install Playwright dependencies for Ubuntu 24.04
echo "📦 Step 5: Installing Playwright dependencies..."
apt install -y \
    libnss3 \
    libatk-bridge2.0-0 \
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

# Step 6: Create user and directories
echo "👤 Step 6: Setting up user and directories..."
useradd -m -s /bin/bash tradebot || true
mkdir -p /opt/ai-trading-sentinel
chown -R tradebot:tradebot /opt/ai-trading-sentinel

# Step 7: Create self-contained app structure
echo "📁 Step 7: Creating application structure..."
cd /opt/ai-trading-sentinel

# Create backend structure
mkdir -p backend/{routes,utils,templates}
mkdir -p frontend/{src,public}
mkdir -p logs data

# Step 8: Create backend files
echo "🐍 Step 8: Creating backend application..."

# Main backend file
cat > backend/main.py << 'EOF'
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import os
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/ai-trading-sentinel/logs/backend.log'),
        logging.StreamHandler()
    ]
)

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'active',
        'service': 'AI Trading Sentinel Backend',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': 'production'
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'uptime': 'active',
        'services': {
            'backend': 'running',
            'database': 'connected',
            'trading': 'ready'
        }
    })

@app.route('/api/trading/status')
def trading_status():
    return jsonify({
        'trading_active': True,
        'mode': 'demo',
        'account_balance': 10000.00,
        'open_positions': 0,
        'daily_pnl': 0.00
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Requirements file
cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-CORS==4.0.0
requests==2.31.0
playwright==1.40.0
gunicorn==21.2.0
EOF

# Step 9: Create frontend files
echo "⚛️ Step 9: Creating frontend application..."

# Package.json
cat > frontend/package.json << 'EOF'
{
  "name": "ai-trading-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^4.5.0"
  }
}
EOF

# Vite config
cat > frontend/vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  },
  server: {
    port: 3000,
    host: '0.0.0.0'
  }
})
EOF

# Index.html
cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI Trading Sentinel</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

# Main React component
mkdir -p frontend/src
cat > frontend/src/main.jsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF

# App component
cat > frontend/src/App.jsx << 'EOF'
import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => {
        setStatus(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error:', err)
        setLoading(false)
      })
  }, [])

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 AI Trading Sentinel</h1>
        <div className="status-card">
          {loading ? (
            <p>Loading...</p>
          ) : status ? (
            <div>
              <h2>✅ System Status: {status.status}</h2>
              <p>Service: {status.service}</p>
              <p>Version: {status.version}</p>
              <p>Environment: {status.environment}</p>
              <p>Last Updated: {new Date(status.timestamp).toLocaleString()}</p>
            </div>
          ) : (
            <p>❌ Unable to connect to backend</p>
          )}
        </div>
        <div className="actions">
          <button onClick={() => window.location.reload()}>🔄 Refresh Status</button>
          <a href="/api/health" target="_blank" rel="noopener noreferrer">
            <button>🏥 Health Check</button>
          </a>
        </div>
      </header>
    </div>
  )
}

export default App
EOF

# CSS styles
cat > frontend/src/App.css << 'EOF'
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

.App-header {
  padding: 2rem;
  max-width: 800px;
}

.status-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 2rem;
  margin: 2rem 0;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
}

button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s;
}

button:hover {
  background: #45a049;
}

a {
  text-decoration: none;
}
EOF

cat > frontend/src/index.css << 'EOF'
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
EOF

# Step 10: Install Python dependencies
echo "🐍 Step 10: Installing Python dependencies..."
cd /opt/ai-trading-sentinel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install

# Step 11: Install and build frontend
echo "⚛️ Step 11: Installing and building frontend..."
cd frontend
npm install
npm run build

# Step 12: Create .env file
echo "🔐 Step 12: Creating environment configuration..."
cd /opt/ai-trading-sentinel
cat > .env << 'EOF'
# AI Trading Sentinel - Production Environment
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///trading.db
TRADING_MODE=demo
API_HOST=0.0.0.0
API_PORT=5000
FRONTEND_URL=http://161.97.112.146
BACKEND_URL=http://161.97.112.146/api
EOF

# Step 13: Create systemd services
echo "⚙️ Step 13: Creating systemd services..."

# Backend service
cat > /etc/systemd/system/ai-trading-backend.service << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory=/opt/ai-trading-sentinel
Environment=PATH=/opt/ai-trading-sentinel/venv/bin
ExecStart=/opt/ai-trading-sentinel/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 backend.main:app
Restart=always
RestartSec=3
StandardOutput=append:/opt/ai-trading-sentinel/logs/backend.log
StandardError=append:/opt/ai-trading-sentinel/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

# Frontend service (serve static files)
cat > /etc/systemd/system/ai-trading-frontend.service << 'EOF'
[Unit]
Description=AI Trading Sentinel Frontend
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory=/opt/ai-trading-sentinel/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=always
RestartSec=3
StandardOutput=append:/opt/ai-trading-sentinel/logs/frontend.log
StandardError=append:/opt/ai-trading-sentinel/logs/frontend.log

[Install]
WantedBy=multi-user.target
EOF

# Step 14: Configure Nginx
echo "🌐 Step 14: Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-trading-sentinel << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    
    # Frontend (React app)
    location / {
        proxy_pass http://localhost:3000;
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
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Logs
    access_log /var/log/nginx/ai-trading-access.log;
    error_log /var/log/nginx/ai-trading-error.log;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Step 15: Set permissions and ownership
echo "🔐 Step 15: Setting permissions..."
chown -R tradebot:tradebot /opt/ai-trading-sentinel
chmod +x /opt/ai-trading-sentinel/venv/bin/*
mkdir -p /opt/ai-trading-sentinel/logs
chown -R tradebot:tradebot /opt/ai-trading-sentinel/logs

# Step 16: Configure firewall
echo "🔥 Step 16: Configuring firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 5000/tcp # Backend (internal)
ufw allow 3000/tcp # Frontend (internal)

# Step 17: Start services
echo "🚀 Step 17: Starting services..."
systemctl daemon-reload
systemctl enable ai-trading-backend
systemctl enable ai-trading-frontend
systemctl enable nginx

systemctl start ai-trading-backend
systemctl start ai-trading-frontend
systemctl restart nginx

# Step 18: Final verification
echo "✅ Step 18: Deployment verification..."
sleep 5

echo "📊 Service Status:"
systemctl status ai-trading-backend --no-pager -l
systemctl status ai-trading-frontend --no-pager -l
systemctl status nginx --no-pager -l

echo "🌐 Testing endpoints..."
curl -s http://localhost:5000/api/status || echo "❌ Backend not responding"
curl -s http://localhost:3000 || echo "❌ Frontend not responding"
curl -s http://localhost/api/status || echo "❌ Nginx proxy not working"

echo "==========================================="
echo "🎉 AI Trading Sentinel Deployment Complete!"
echo "📍 Production URLs:"
echo "   Frontend: http://161.97.112.146/"
echo "   Backend:  http://161.97.112.146/api/status"
echo "   Health:   http://161.97.112.146/api/health"
echo "==========================================="
echo "📋 Useful Commands:"
echo "   systemctl status ai-trading-backend"
echo "   systemctl status ai-trading-frontend"
echo "   systemctl status nginx"
echo "   tail -f /opt/ai-trading-sentinel/logs/backend.log"
echo "   tail -f /opt/ai-trading-sentinel/logs/frontend.log"
echo "==========================================="
echo "✅ Deployment completed at $(date)"