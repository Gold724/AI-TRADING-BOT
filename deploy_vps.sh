#!/bin/bash
# 🚀 AI Trading Sentinel - IP Deployment Script
# Run this on your Contabo VPS

set -e

VPS_IP="192.168.1.100"
GITHUB_REPO="https://github.com/Gold724/AI-TRADING-BOT.git"
APP_DIR="/opt/ai-trading-sentinel"

echo "🚀 Starting AI Trading Sentinel deployment on $VPS_IP"

# 1. System Updates
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install Dependencies
echo "🔧 Installing dependencies..."
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx git curl wget

# Install PM2 for process management
sudo npm install -g pm2

# 3. Clone Repository
echo "📥 Cloning repository..."
if [ -d "$APP_DIR" ]; then
    echo "Directory exists, pulling latest changes..."
    cd $APP_DIR
    git pull origin main
else
    sudo git clone $GITHUB_REPO $APP_DIR
    sudo chown -R $USER:$USER $APP_DIR
    cd $APP_DIR
fi

# 4. Python Environment Setup
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn supervisor

# 5. Frontend Build
echo "⚛️ Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# 6. Create Production Environment
echo "🔐 Setting up environment..."
cp .env .env.production

# Update environment for production
cat >> .env.production << EOF

# Production Settings
FLASK_ENV=production
FLASK_DEBUG=False
VPS_IP=$VPS_IP
API_URL=http://$VPS_IP:5000
FRONTEND_URL=http://$VPS_IP:3000
SENTINEL_URL=http://$VPS_IP:8090
EOF

# 7. Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/trading-sentinel << EOF
server {
    listen 80;
    server_name $VPS_IP;
    
    # Frontend (React build)
    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
    
    # Sentinel Control Panel
    location /sentinel/ {
        proxy_pass http://127.0.0.1:8090/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/trading-sentinel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# 8. Create PM2 Ecosystem
echo "⚙️ Setting up PM2 processes..."
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'trading-backend',
      script: 'venv/bin/gunicorn',
      args: '--bind 127.0.0.1:5000 --workers 2 backend_main:app',
      cwd: '$APP_DIR',
      env: {
        PYTHONPATH: '$APP_DIR',
        FLASK_ENV: 'production'
      },
      restart_delay: 5000,
      max_restarts: 10
    },
    {
      name: 'trading-sentinel',
      script: 'venv/bin/python',
      args: 'bulenox_sentinel.py',
      cwd: '$APP_DIR',
      env: {
        PYTHONPATH: '$APP_DIR',
        DISPLAY: ':99'
      },
      restart_delay: 5000,
      max_restarts: 10
    }
  ]
};
EOF

# 9. Install Xvfb for headless browser
echo "🖥️ Installing virtual display..."
sudo apt install -y xvfb

# Create Xvfb service
sudo tee /etc/systemd/system/xvfb.service << EOF
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable xvfb
sudo systemctl start xvfb

# 10. Configure VNC and SSH
echo "🖥️ Configuring VNC and remote access..."
sudo ufw allow ssh
sudo ufw allow 5901/tcp  # VNC port
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Install VNC server
sudo apt install -y tightvncserver xfce4 xfce4-goodies

# Setup VNC for root user
echo "Setting up VNC server..."
vncserver :1 -geometry 1920x1080 -depth 24

# Create VNC startup script
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF

chmod +x ~/.vnc/xstartup

# Create VNC service
sudo tee /etc/systemd/system/vncserver@.service > /dev/null << 'EOF'
[Unit]
Description=Start TightVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/root

PIDFile=/root/.vnc/%H:%i.pid
ExecStartPre=-/usr/bin/vncserver -kill :%i > /dev/null 2>&1
ExecStart=/usr/bin/vncserver -depth 24 -geometry 1920x1080 :%i
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
EOF

# Enable VNC service
sudo systemctl daemon-reload
sudo systemctl enable vncserver@1.service
sudo systemctl start vncserver@1.service

# 11. Start Services
echo "🚀 Starting services..."
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 12. Create Update Script
echo "📝 Creating update script..."
cat > update.sh << 'EOF'
#!/bin/bash
cd /opt/ai-trading-sentinel
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
pm2 restart all
echo "✅ Update complete!"
EOF
chmod +x update.sh

# 13. Setup Monitoring
echo "📊 Setting up monitoring..."
cat > health_check.sh << 'EOF'
#!/bin/bash
# Check if services are running
if ! pm2 list | grep -q "online"; then
    echo "⚠️ Services down, restarting..."
    pm2 restart all
fi

# Check if Nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "⚠️ Nginx down, restarting..."
    sudo systemctl restart nginx
fi
EOF
chmod +x health_check.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/ai-trading-sentinel/health_check.sh") | crontab -

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════"
echo "📱 Access URLs:"
echo "   Main Dashboard: http://$VPS_IP"
echo "   API Endpoints:  http://$VPS_IP/api"
echo "   Trading Panel:  http://$VPS_IP/sentinel"
echo ""
echo "🖥️ Remote Access:"
echo "   VNC: vnc://$VPS_IP:5901 (or use Contabo VNC console)"
echo "   SSH: ssh root@$VPS_IP (backup access)"
echo "   📱 Use VNC client or Contabo dashboard for visual management"
echo ""
echo "🔧 Management Commands:"
echo "   View logs:      pm2 logs"
echo "   Restart:        pm2 restart all"
echo "   Update:         ./update.sh"
echo "   Health check:   ./health_check.sh"
echo ""
echo "💡 Next Steps:"
echo "   1. Test all URLs above"
echo "   2. Configure your .env credentials"
echo "   3. Start trading!"
echo "═══════════════════════════════════════"
