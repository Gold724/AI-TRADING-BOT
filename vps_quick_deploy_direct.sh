#!/bin/bash

# AI Trading Sentinel - VPS Quick Deploy Script
# For Contabo VPS (Ubuntu 22.04/24.04)
# Run this script on the VPS via VNC terminal

set -e  # Exit on any error

echo "🚀 AI Trading Sentinel - VPS Production Deployment"
echo "================================================="
echo "VPS: $(hostname -I | awk '{print $1}')"
echo "User: $(whoami)"
echo "Date: $(date)"
echo ""

# Step 1: System Updates
echo "📦 Step 1: Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install Required Packages
echo "🔧 Step 2: Installing required packages..."
apt install -y python3 python3-pip python3-venv nodejs npm nginx git curl wget unzip

# Install Playwright dependencies
apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Step 3: Create Application User
echo "👤 Step 3: Setting up application user..."
if ! id "tradebot" &>/dev/null; then
    useradd -m -s /bin/bash tradebot
    usermod -aG sudo tradebot
fi

# Step 4: Setup Application Directory
echo "📁 Step 4: Setting up application directory..."
mkdir -p /opt/ai-trading-sentinel
chown tradebot:tradebot /opt/ai-trading-sentinel
cd /opt/ai-trading-sentinel

# Step 5: Clone Repository
echo "📥 Step 5: Cloning repository..."
if [ ! -d ".git" ]; then
    sudo -u tradebot git clone https://github.com/your-username/ai-trading-sentinel.git .
else
    sudo -u tradebot git pull origin main
fi

# Step 6: Python Environment Setup
echo "🐍 Step 6: Setting up Python environment..."
sudo -u tradebot python3 -m venv venv
sudo -u tradebot ./venv/bin/pip install --upgrade pip
sudo -u tradebot ./venv/bin/pip install -r requirements.txt

# Install Playwright browsers
sudo -u tradebot ./venv/bin/playwright install chromium

# Step 7: Frontend Build
echo "⚛️ Step 7: Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Step 8: Environment Configuration
echo "🔐 Step 8: Environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  Creating template .env file - YOU MUST EDIT THIS!"
    cat > .env << 'EOF'
# AI Trading Sentinel - Production Environment
# EDIT THESE VALUES BEFORE RUNNING!

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-key-change-this

# Bulenox Trading Configuration
BULENOX_USERNAME=your-bulenox-username
BULENOX_PASSWORD=your-bulenox-password
BULENOX_DEMO=False

# Server Configuration
HOST=0.0.0.0
PORT=5000
FRONTEND_PORT=3000

# Security
CORS_ORIGINS=http://161.97.112.146,https://161.97.112.146

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ai-trading-sentinel/app.log

# GitHub (for CI/CD)
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-username/ai-trading-sentinel

# Monitoring
SLACK_WEBHOOK_URL=your-slack-webhook-url
EMAIL_ALERTS=your-email@domain.com
EOF
    chown tradebot:tradebot .env
    chmod 600 .env
fi

# Step 9: Create Log Directory
echo "📝 Step 9: Setting up logging..."
mkdir -p /var/log/ai-trading-sentinel
chown tradebot:tradebot /var/log/ai-trading-sentinel

# Step 10: Backend Service Configuration
echo "🔧 Step 10: Configuring backend service..."
cat > /etc/systemd/system/ai-trading-backend.service << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=tradebot
Group=tradebot
WorkingDirectory=/opt/ai-trading-sentinel
Environment=PATH=/opt/ai-trading-sentinel/venv/bin
EnvironmentFile=/opt/ai-trading-sentinel/.env
ExecStart=/opt/ai-trading-sentinel/venv/bin/python backend_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Step 11: Frontend Service Configuration
echo "🌐 Step 11: Configuring frontend service..."
cat > /etc/systemd/system/ai-trading-frontend.service << 'EOF'
[Unit]
Description=AI Trading Sentinel Frontend
After=network.target

[Service]
Type=simple
User=tradebot
Group=tradebot
WorkingDirectory=/opt/ai-trading-sentinel/frontend
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=VITE_API_URL=http://161.97.112.146:5000
Environment=VITE_WEBSOCKET_URL=ws://161.97.112.146:5000
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 3000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Step 12: Nginx Configuration
echo "🔧 Step 12: Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-trading-sentinel << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;

    # Frontend (React/Vite)
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
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket Support
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Step 13: Firewall Configuration
echo "🔥 Step 13: Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw allow 3000/tcp

# Step 14: Start Services
echo "🚀 Step 14: Starting services..."
systemctl daemon-reload
systemctl enable ai-trading-backend
systemctl enable ai-trading-frontend
systemctl enable nginx

systemctl start ai-trading-backend
systemctl start ai-trading-frontend
systemctl restart nginx

# Step 15: Deployment Verification
echo "✅ Step 15: Verifying deployment..."
sleep 5

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "📊 Service Status:"
systemctl status ai-trading-backend --no-pager -l
echo ""
systemctl status ai-trading-frontend --no-pager -l
echo ""
systemctl status nginx --no-pager -l
echo ""

echo "🌐 Production URLs:"
echo "Frontend: http://161.97.112.146/"
echo "Backend API: http://161.97.112.146/api/status"
echo "WebSocket: ws://161.97.112.146/socket.io"
echo ""

echo "⚠️  IMPORTANT: Edit /opt/ai-trading-sentinel/.env with your credentials!"
echo ""
echo "🔧 Useful Commands:"
echo "- Check logs: journalctl -u ai-trading-backend -f"
echo "- Restart backend: systemctl restart ai-trading-backend"
echo "- Restart frontend: systemctl restart ai-trading-frontend"
echo "- Check status: systemctl status ai-trading-backend"
echo "- Edit config: nano /opt/ai-trading-sentinel/.env"
echo ""
echo "✅ Deployment completed successfully!"