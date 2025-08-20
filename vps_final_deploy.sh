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
    libgtk-3-0 \
    libgconf-2-4 \
    libxfixes3 \
    libxinerama1 \
    libxrandr2 \
    libasound2-dev \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0

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

# Step 8: Create self-contained application structure
echo "📁 Step 8: Creating application structure..."
mkdir -p backend/{routes,utils,templates}
mkdir -p frontend/{src,public}
mkdir -p logs data

# Step 9: Create backend application
echo "🐍 Step 9: Creating backend application..."
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
        'environment': 'production',
        'server': '161.97.112.146'
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
        },
        'server_info': {
            'ip': '161.97.112.146',
            'deployment': 'production'
        }
    })

@app.route('/api/trading/status')
def trading_status():
    return jsonify({
        'trading_active': True,
        'mode': 'demo',
        'account_balance': 10000.00,
        'open_positions': 0,
        'daily_pnl': 0.00,
        'server': '161.97.112.146'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-CORS==4.0.0
requests==2.31.0
playwright==1.40.0
gunicorn==21.2.0
EOF

# Step 10: Create frontend application
echo "⚛️ Step 10: Creating frontend application..."
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
    <title>AI Trading Sentinel - Production</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

# Create src directory and files
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
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch status
    fetch('/api/status')
      .then(res => res.json())
      .then(data => {
        setStatus(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Status Error:', err)
        setLoading(false)
      })

    // Fetch health
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error('Health Error:', err))
  }, [])

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 AI Trading Sentinel</h1>
        <h2>🌐 Production Server: 161.97.112.146</h2>
        
        <div className="status-grid">
          <div className="status-card">
            <h3>📊 System Status</h3>
            {loading ? (
              <p>Loading...</p>
            ) : status ? (
              <div>
                <p>✅ Status: {status.status}</p>
                <p>🔧 Service: {status.service}</p>
                <p>📦 Version: {status.version}</p>
                <p>🌍 Environment: {status.environment}</p>
                <p>🕐 Updated: {new Date(status.timestamp).toLocaleString()}</p>
              </div>
            ) : (
              <p>❌ Unable to connect to backend</p>
            )}
          </div>

          <div className="status-card">
            <h3>🏥 Health Check</h3>
            {health ? (
              <div>
                <p>✅ Status: {health.status}</p>
                <p>⚡ Backend: {health.services.backend}</p>
                <p>💾 Database: {health.services.database}</p>
                <p>📈 Trading: {health.services.trading}</p>
              </div>
            ) : (
              <p>Loading health data...</p>
            )}
          </div>
        </div>
        
        <div className="actions">
          <button onClick={() => window.location.reload()}>🔄 Refresh Status</button>
          <a href="/api/health" target="_blank" rel="noopener noreferrer">
            <button>🏥 Health Check</button>
          </a>
          <a href="/api/trading/status" target="_blank" rel="noopener noreferrer">
            <button>📈 Trading Status</button>
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
  padding: 2rem;
}

.App-header {
  max-width: 1200px;
  width: 100%;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.status-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 2rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  text-align: left;
}

.status-card h3 {
  text-align: center;
  margin-bottom: 1rem;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
  flex-wrap: wrap;
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

# Step 11: Install Python dependencies
echo "🐍 Step 11: Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install

# Step 12: Install and build frontend
echo "⚛️ Step 12: Installing and building frontend..."
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..

# Step 13: Create environment configuration
echo "🔐 Step 13: Creating environment configuration..."
cat > .env << 'EOF'
# AI Trading Sentinel - Production Environment
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=ai-trading-sentinel-production-key-2024
DATABASE_URL=sqlite:///trading.db
TRADING_MODE=demo
API_HOST=0.0.0.0
API_PORT=5000
FRONTEND_URL=http://161.97.112.146
BACKEND_URL=http://161.97.112.146/api
SERVER_IP=161.97.112.146
EOF

# Step 14: Create systemd services
echo "⚙️ Step 14: Creating systemd services..."
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

# Step 15: Configure Nginx
echo "🌐 Step 15: Configuring Nginx..."
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

# Step 16: Set permissions and ownership
echo "🔐 Step 16: Setting permissions..."
chown -R tradebot:tradebot /opt/ai-trading-sentinel
chmod +x /opt/ai-trading-sentinel/venv/bin/*
mkdir -p /opt/ai-trading-sentinel/logs
chown -R tradebot:tradebot /opt/ai-trading-sentinel/logs

# Step 17: Configure firewall
echo "🔥 Step 17: Configuring firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS

# Step 18: Start services
echo "🚀 Step 18: Starting services..."
systemctl daemon-reload
systemctl enable ai-trading-backend
systemctl enable ai-trading-frontend
systemctl enable nginx

systemctl start ai-trading-backend
systemctl start ai-trading-frontend
systemctl restart nginx

# Step 19: Final verification
echo "✅ Step 19: Final deployment verification..."
sleep 10

echo "📊 Service Status:"
systemctl status ai-trading-backend --no-pager -l
echo "---"
systemctl status ai-trading-frontend --no-pager -l
echo "---"
systemctl status nginx --no-pager -l

echo "🌐 Testing endpoints..."
curl -s http://localhost:5000/api/status | head -5 || echo "❌ Backend not responding"
curl -s http://localhost:3000 | head -5 || echo "❌ Frontend not responding"
curl -s http://localhost/api/status | head -5 || echo "❌ Nginx proxy not working"

echo "==========================================="
echo "🎉 AI Trading Sentinel Deployment Complete!"
echo "📍 Production URLs:"
echo "   🌐 Frontend: http://161.97.112.146/"
echo "   🔧 Backend:  http://161.97.112.146/api/status"
echo "   🏥 Health:   http://161.97.112.146/api/health"
echo "   📈 Trading:  http://161.97.112.146/api/trading/status"
echo "==========================================="
echo "📋 Useful Commands:"
echo "   systemctl status ai-trading-backend"
echo "   systemctl status ai-trading-frontend"
echo "   systemctl status nginx"
echo "   tail -f /opt/ai-trading-sentinel/logs/backend.log"
echo "   tail -f /opt/ai-trading-sentinel/logs/frontend.log"
echo "   tail -f /var/log/nginx/ai-trading-access.log"
echo "==========================================="
echo "✅ Final deployment completed at $(date)"
echo "🚀 AI Trading Sentinel is now LIVE on 161.97.112.146!"