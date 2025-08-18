#!/bin/bash

# 🚀 AI Trading Sentinel - VPS Deployment Script (Fixed Version)
# Handles Node.js dependency conflicts automatically

set -e  # Exit on any error

# Configuration
VPS_IP="${1:-localhost}"
REPO_URL="${2:-https://github.com/Gold724/AI-TRADING-BOT.git}"
INSTALL_DIR="/opt/ai-trading-sentinel"
LOG_FILE="/tmp/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log "🚀 Starting AI Trading Sentinel deployment on $VPS_IP"
log "📋 Repository: $REPO_URL"
log "📁 Install Directory: $INSTALL_DIR"

# Update system packages
log "📦 Updating system packages..."
apt update && apt upgrade -y

# Install basic dependencies (excluding Node.js for now)
log "🔧 Installing basic dependencies..."
apt install -y python3 python3-pip python3-venv nginx git curl wget unzip htop vim nano

# Fix Node.js dependency conflicts
log "🔧 Resolving Node.js dependency conflicts..."

# Remove any existing Node.js installations
log_warning "Removing conflicting Node.js packages..."
apt remove --purge -y nodejs npm node-* 2>/dev/null || true
apt autoremove -y

# Remove NodeSource repository if it exists
rm -f /etc/apt/sources.list.d/nodesource.list
rm -f /etc/apt/keyrings/nodesource.gpg

# Clean npm cache and directories
rm -rf /usr/local/lib/node_modules 2>/dev/null || true
rm -rf ~/.npm 2>/dev/null || true

# Update package lists
apt update

# Install Node.js 20.x LTS via NodeSource (clean installation)
log "📦 Installing Node.js 20.x LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Verify Node.js installation
NODE_VERSION=$(node --version 2>/dev/null || echo "not installed")
NPM_VERSION=$(npm --version 2>/dev/null || echo "not installed")

if [[ "$NODE_VERSION" == "not installed" ]] || [[ "$NPM_VERSION" == "not installed" ]]; then
    log_error "Node.js installation failed. Trying alternative method..."
    
    # Alternative: Use Ubuntu's Node.js
    apt remove --purge -y nodejs npm 2>/dev/null || true
    rm -f /etc/apt/sources.list.d/nodesource.list
    apt update
    apt install -y nodejs npm
    
    NODE_VERSION=$(node --version 2>/dev/null || echo "failed")
    NPM_VERSION=$(npm --version 2>/dev/null || echo "failed")
    
    if [[ "$NODE_VERSION" == "failed" ]]; then
        log_error "All Node.js installation methods failed. Please install manually."
        exit 1
    fi
fi

log_success "Node.js $NODE_VERSION installed"
log_success "npm $NPM_VERSION installed"

# Install PM2 globally
log "📦 Installing PM2 process manager..."
npm install -g pm2
PM2_VERSION=$(pm2 --version 2>/dev/null || echo "failed")

if [[ "$PM2_VERSION" == "failed" ]]; then
    log_error "PM2 installation failed"
    exit 1
fi

log_success "PM2 $PM2_VERSION installed"

# Install Python dependencies
log "🐍 Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install playwright selenium requests flask flask-cors python-dotenv schedule

# Install Playwright browsers
log "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install-deps

# Create installation directory
log "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Clone repository
log "📥 Cloning repository..."
if [ -d ".git" ]; then
    log_warning "Repository already exists, pulling latest changes..."
    git pull origin main || git pull origin master
else
    git clone "$REPO_URL" .
fi

# Set proper permissions
chown -R root:root "$INSTALL_DIR"
chmod +x *.sh 2>/dev/null || true

# Create Python virtual environment
log "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || log_warning "requirements.txt not found, skipping..."

# Build frontend if it exists
if [ -d "frontend" ]; then
    log "🎨 Building frontend..."
    cd frontend
    npm install
    npm run build 2>/dev/null || npm run dev &
    cd ..
fi

# Create .env file from template
log "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.production.template" ]; then
        cp .env.production.template .env
    elif [ -f ".env.template" ]; then
        cp .env.template .env
    else
        cat > .env << EOF
# AI Trading Sentinel Configuration
TRADING_MODE=DEMO
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here
VPS_IP=$VPS_IP
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
FLASK_ENV=production
DEBUG=False
EOF
    fi
    chmod 600 .env
    log_success "Environment file created at $INSTALL_DIR/.env"
    log_warning "Please edit .env with your Bulenox credentials!"
fi

# Configure Nginx
log "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/ai-trading-sentinel << EOF
server {
    listen 80;
    server_name $VPS_IP;
    
    # Main dashboard
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # API endpoints
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Trading panel
    location /trading {
        proxy_pass http://localhost:8090;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Setup VNC Server
log "🖥️  Setting up VNC server..."
apt install -y xfce4 xfce4-goodies tightvncserver

# Create VNC startup script
mkdir -p /root/.vnc
cat > /root/.vnc/xstartup << EOF
#!/bin/bash
xrdb \$HOME/.Xresources
startxfce4 &
EOF
chmod +x /root/.vnc/xstartup

# Set VNC password (default: trading123)
echo "trading123" | vncpasswd -f > /root/.vnc/passwd
chmod 600 /root/.vnc/passwd

# Create VNC service
cat > /etc/systemd/system/vncserver@1.service << EOF
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

systemctl daemon-reload
systemctl enable vncserver@1.service
systemctl start vncserver@1.service

# Create PM2 ecosystem file
log "⚙️  Setting up PM2 services..."
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'ai-trading-backend',
      script: 'venv/bin/python',
      args: 'backend_main.py',
      cwd: '$INSTALL_DIR',
      env: {
        FLASK_ENV: 'production',
        PYTHONPATH: '$INSTALL_DIR'
      },
      error_file: 'logs/backend-error.log',
      out_file: 'logs/backend-out.log',
      log_file: 'logs/backend.log'
    },
    {
      name: 'ai-trading-bot',
      script: 'venv/bin/python',
      args: 'main.py',
      cwd: '$INSTALL_DIR',
      env: {
        PYTHONPATH: '$INSTALL_DIR'
      },
      error_file: 'logs/bot-error.log',
      out_file: 'logs/bot-out.log',
      log_file: 'logs/bot.log'
    }
  ]
};
EOF

# Create logs directory
mkdir -p logs

# Start PM2 services
log "🚀 Starting services..."
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Create update script
log "📝 Creating update script..."
cat > update.sh << 'EOF'
#!/bin/bash
cd /opt/ai-trading-sentinel
git pull origin main || git pull origin master
source venv/bin/activate
pip install -r requirements.txt
if [ -d "frontend" ]; then
    cd frontend && npm install && npm run build && cd ..
fi
pm2 restart all
echo "✅ Update completed!"
EOF
chmod +x update.sh

# Final verification
log "🔍 Running final verification..."

# Check services
SERVICE_STATUS=$(pm2 jlist | jq -r '.[].pm2_env.status' 2>/dev/null || echo "unknown")
NGINX_STATUS=$(systemctl is-active nginx)
VNC_STATUS=$(systemctl is-active vncserver@1.service)

log_success "Deployment completed!"
echo ""
echo "=== 🎉 AI Trading Sentinel Deployment Summary ==="
echo ""
echo "📍 VPS IP: $VPS_IP"
echo "📁 Installation: $INSTALL_DIR"
echo "🌐 Web Dashboard: http://$VPS_IP"
echo "🔌 API Endpoints: http://$VPS_IP:5000"
echo "📊 Trading Panel: http://$VPS_IP/trading"
echo "🖥️  VNC Desktop: $VPS_IP:5901 (password: trading123)"
echo ""
echo "=== Service Status ==="
echo "🔧 PM2 Services: $SERVICE_STATUS"
echo "🌐 Nginx: $NGINX_STATUS"
echo "🖥️  VNC Server: $VNC_STATUS"
echo ""
echo "=== Next Steps ==="
echo "1. Edit credentials: nano $INSTALL_DIR/.env"
echo "2. Restart services: pm2 restart all"
echo "3. Check status: pm2 status"
echo "4. View logs: pm2 logs"
echo "5. Update system: $INSTALL_DIR/update.sh"
echo ""
echo "🚀 Your AI Trading Sentinel is ready for 24/7 operation!"
echo ""

# Save deployment info
cat > /root/deployment-info.txt << EOF
AI Trading Sentinel Deployment
Date: $(date)
VPS IP: $VPS_IP
Installation: $INSTALL_DIR
Node.js: $NODE_VERSION
npm: $NPM_VERSION
PM2: $PM2_VERSION

Access URLs:
- Dashboard: http://$VPS_IP
- API: http://$VPS_IP:5000
- Trading: http://$VPS_IP/trading
- VNC: $VPS_IP:5901

Credentials to configure:
- Edit: $INSTALL_DIR/.env
- VNC Password: trading123
EOF

log_success "Deployment information saved to /root/deployment-info.txt"
log "📋 Check deployment status anytime with: cat /root/deployment-info.txt"