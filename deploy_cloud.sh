#!/bin/bash
# AI Trading Sentinel - Cloud Deployment Script
# Supports: Ubuntu 20.04+, Debian 10+, CentOS 8+

set -e

echo "☁️ AI Trading Sentinel - Cloud Deployment"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    echo "💡 Usage: sudo bash deploy_cloud.sh"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "❌ Cannot detect OS version"
    exit 1
fi

echo "🖥️ Detected OS: $OS $VER"

# Update system
echo "📦 Updating system packages..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt update && apt upgrade -y
    apt install -y curl wget git python3 python3-pip python3-venv
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    yum update -y
    yum install -y curl wget git python3 python3-pip
else
    echo "⚠️ Unsupported OS. Manual installation required."
fi

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    usermod -aG docker $SUDO_USER 2>/dev/null || true
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Create application directory
echo "📁 Setting up application directory..."
APP_DIR="/opt/ai-trading-sentinel"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or update repository
echo "📥 Setting up application code..."
if [ -d ".git" ]; then
    echo "🔄 Updating existing repository..."
    git pull
else
    echo "📥 Cloning repository..."
    # If current directory has files, clone to temp and move
    if [ "$(ls -A .)" ]; then
        git clone https://github.com/Gold724/AI-TRADING-BOT.git temp-repo
        mv temp-repo/* .
        mv temp-repo/.* . 2>/dev/null || true
        rm -rf temp-repo
    else
        git clone https://github.com/Gold724/AI-TRADING-BOT.git .
    fi
fi

# Set up environment
echo "⚙️ Configuring environment..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# AI Trading Sentinel - Production Environment
ENVIRONMENT=production
HEADLESS=true
AUTO_EXECUTION_ENABLED=true
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Browser Settings
BROWSER_TIMEOUT=60
PAGE_LOAD_TIMEOUT=60
CHROME_BINARY_PATH=/usr/bin/google-chrome

# Trading Settings
RISK_MANAGEMENT=true
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=4.0

# Monitoring
HEALTH_CHECK_INTERVAL=300
LOG_RETENTION_DAYS=30

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=3000

# Database (if using)
# DATABASE_URL=sqlite:///data/trading.db

# Notifications (configure as needed)
# SLACK_WEBHOOK_URL=
# TELEGRAM_BOT_TOKEN=
# TELEGRAM_CHAT_ID=

# Broker Credentials (REQUIRED - ADD YOUR CREDENTIALS)
# BROKER_USERNAME=
# BROKER_PASSWORD=
# BROKER_API_KEY=
# BROKER_SECRET=
EOF
    echo "📋 Created production .env file"
    echo "⚠️ IMPORTANT: Edit .env file with your broker credentials!"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
mkdir -p logs data/accounts data/signals data/backtest chrome_profiles
chown -R $SUDO_USER:$SUDO_USER . 2>/dev/null || true

# Install Chrome/Chromium for headless browsing
echo "🌐 Installing Chrome for headless browsing..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    if ! command -v google-chrome &> /dev/null; then
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
        apt update
        apt install -y google-chrome-stable
        echo "✅ Chrome installed"
    else
        echo "✅ Chrome already installed"
    fi
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    if ! command -v google-chrome &> /dev/null; then
        yum install -y chromium
        echo "✅ Chromium installed"
    else
        echo "✅ Chromium already installed"
    fi
fi

# Set up systemd service
echo "🔧 Setting up systemd service..."
cat > /etc/systemd/system/ai-trading-sentinel.service << EOF
[Unit]
Description=AI Trading Sentinel Bot
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$APP_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-trading-sentinel

# Set up firewall (basic)
echo "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow ssh
    ufw allow 8000/tcp  # API
    ufw allow 3000/tcp  # Frontend
    echo "✅ UFW firewall configured"
elif command -v firewall-cmd &> /dev/null; then
    systemctl start firewalld
    systemctl enable firewalld
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --permanent --add-port=3000/tcp
    firewall-cmd --reload
    echo "✅ Firewalld configured"
fi

# Build and start containers
echo "🚀 Building and starting application..."
if [ -f "docker-compose.yml" ]; then
    docker-compose build
    docker-compose up -d
    echo "✅ Application started with Docker Compose"
else
    echo "⚠️ No docker-compose.yml found, starting with Python..."
    # Fallback to Python virtual environment
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    nohup python3 main.py > logs/app.log 2>&1 &
    echo "✅ Application started with Python"
fi

echo ""
echo "🎉 Cloud deployment complete!"
echo "=============================="
echo ""
echo "📋 Next Steps:"
echo "1. Edit $APP_DIR/.env with your broker credentials"
echo "2. Restart service: sudo systemctl restart ai-trading-sentinel"
echo "3. Check status: sudo systemctl status ai-trading-sentinel"
echo "4. View logs: sudo journalctl -u ai-trading-sentinel -f"
echo ""
echo "🌐 Access Points:"
echo "• API: http://$(curl -s ifconfig.me):8000"
echo "• Frontend: http://$(curl -s ifconfig.me):3000"
echo "• Logs: $APP_DIR/logs/"
echo ""
echo "🔧 Management Commands:"
echo "• Start: sudo systemctl start ai-trading-sentinel"
echo "• Stop: sudo systemctl stop ai-trading-sentinel"
echo "• Restart: sudo systemctl restart ai-trading-sentinel"
echo "• Status: sudo systemctl status ai-trading-sentinel"
echo "• Logs: sudo journalctl -u ai-trading-sentinel -f"
echo ""
echo "⚠️ SECURITY REMINDER:"
echo "• Change default passwords in .env"
echo "• Configure SSL/TLS for production"
echo "• Set up monitoring and backups"
echo "• Review firewall rules"