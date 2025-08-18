#!/bin/bash

# AI Trading Sentinel - Contabo VPS Deployment Script
# TRAE-SentinelOps Production Deployment
# Ubuntu 22.04/24.04 LTS Compatible

set -euo pipefail

# Configuration
APP_NAME="ai-trading-sentinel"
APP_USER="sentinel"
APP_DIR="/opt/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
SERVICE_NAME="${APP_NAME}"
GITHUB_REPO="https://github.com/YOUR_USERNAME/${APP_NAME}.git"
PYTHON_VERSION="3.11"
NODE_VERSION="18"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        log_info "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# System update and basic packages
install_system_packages() {
    log_info "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    
    log_info "Installing essential packages..."
    sudo apt install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        build-essential \
        nginx \
        ufw \
        fail2ban \
        htop \
        tree \
        jq \
        supervisor \
        logrotate
}

# Install Python 3.11
install_python() {
    log_info "Installing Python ${PYTHON_VERSION}..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        python3-pip
    
    # Set Python 3.11 as default
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1
}

# Install Node.js
install_nodejs() {
    log_info "Installing Node.js ${NODE_VERSION}..."
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
    sudo apt install -y nodejs
    
    # Install global packages
    sudo npm install -g pm2 yarn
}

# Install Docker
install_docker() {
    log_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker installed. Please log out and back in for group changes to take effect."
}

# Install Playwright dependencies
install_playwright_deps() {
    log_info "Installing Playwright system dependencies..."
    sudo apt install -y \
        libnss3 \
        libnspr4 \
        libatk-bridge2.0-0 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libxss1 \
        libasound2 \
        libatspi2.0-0 \
        libgtk-3-0
}

# Create application user and directories
setup_app_user() {
    log_info "Creating application user and directories..."
    
    # Create user if doesn't exist
    if ! id "$APP_USER" &>/dev/null; then
        sudo useradd -r -m -s /bin/bash $APP_USER
        log_success "Created user: $APP_USER"
    fi
    
    # Create directories
    sudo mkdir -p $APP_DIR $LOG_DIR
    sudo chown -R $APP_USER:$APP_USER $APP_DIR $LOG_DIR
    sudo chmod 755 $APP_DIR $LOG_DIR
}

# Clone and setup application
setup_application() {
    log_info "Setting up application..."
    
    # Clone repository
    if [ ! -d "$APP_DIR/.git" ]; then
        sudo -u $APP_USER git clone $GITHUB_REPO $APP_DIR
    else
        sudo -u $APP_USER git -C $APP_DIR pull origin main
    fi
    
    # Create Python virtual environment
    sudo -u $APP_USER python3 -m venv $APP_DIR/venv
    
    # Install Python dependencies
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
    
    # Install Playwright browsers
    sudo -u $APP_USER $APP_DIR/venv/bin/playwright install chromium
    
    # Setup frontend if exists
    if [ -f "$APP_DIR/frontend/package.json" ]; then
        log_info "Setting up frontend..."
        sudo -u $APP_USER bash -c "cd $APP_DIR/frontend && npm install && npm run build"
    fi
}

# Configure environment variables
setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Create .env file template if doesn't exist
    if [ ! -f "$APP_DIR/.env" ]; then
        sudo -u $APP_USER tee $APP_DIR/.env > /dev/null <<EOF
# AI Trading Sentinel - Production Configuration

# Broker Configuration
BROKER_URL=https://bulenox.projectx.com/login
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password

# Trading Configuration
AUTO_EXECUTE=false
SIMULATION=true
RISK_PERCENTAGE=1.0
MAX_DAILY_TRADES=10
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=3.0

# Browser Configuration
HEADLESS=true
BROWSER_TIMEOUT=30000
PAGE_TIMEOUT=15000

# Monitoring
HEALTH_CHECK_INTERVAL=60
LOG_LEVEL=INFO
MAX_LOG_SIZE=100MB
LOG_RETENTION_DAYS=30

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EMAIL_SMTP_SERVER=
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_TO=

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Database (if using)
DATABASE_URL=sqlite:////$APP_DIR/data/trading.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2

# Frontend Configuration
VITE_API_URL=https://your-domain.com/api
VITE_WEBSOCKET_URL=wss://your-domain.com/ws
EOF
        
        log_warning "Please edit $APP_DIR/.env with your actual configuration"
    fi
}

# Configure systemd service
setup_systemd_service() {
    log_info "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=AI Trading Sentinel
After=network.target
Wants=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python main.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR $LOG_DIR /tmp

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
}

# Configure Nginx reverse proxy
setup_nginx() {
    log_info "Setting up Nginx reverse proxy..."
    
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    
    # Frontend (if exists)
    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket endpoints
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test and reload Nginx
    sudo nginx -t && sudo systemctl reload nginx
}

# Configure firewall
setup_firewall() {
    log_info "Configuring UFW firewall..."
    
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (adjust port if needed)
    sudo ufw allow 22/tcp
    
    # Allow HTTP/HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    log_success "Firewall configured and enabled"
}

# Configure log rotation
setup_logrotate() {
    log_info "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/$APP_NAME > /dev/null <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up basic monitoring..."
    
    # Create monitoring script
    sudo tee /usr/local/bin/sentinel-monitor > /dev/null <<'EOF'
#!/bin/bash

# Simple monitoring script for AI Trading Sentinel
SERVICE_NAME="ai-trading-sentinel"
LOG_FILE="/var/log/sentinel-monitor.log"
ALERT_EMAIL="admin@yourdomain.com"

check_service() {
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): Service $SERVICE_NAME is down, attempting restart" >> $LOG_FILE
        systemctl restart $SERVICE_NAME
        
        # Send alert (requires mail setup)
        # echo "AI Trading Sentinel service was down and has been restarted" | mail -s "Service Alert" $ALERT_EMAIL
    fi
}

check_disk_space() {
    USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $USAGE -gt 85 ]; then
        echo "$(date): Disk usage is ${USAGE}%" >> $LOG_FILE
    fi
}

check_memory() {
    MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $MEM_USAGE -gt 90 ]; then
        echo "$(date): Memory usage is ${MEM_USAGE}%" >> $LOG_FILE
    fi
}

check_service
check_disk_space
check_memory
EOF

    sudo chmod +x /usr/local/bin/sentinel-monitor
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/sentinel-monitor") | sudo crontab -
}

# Main deployment function
main() {
    log_info "Starting AI Trading Sentinel deployment on Contabo VPS..."
    
    check_root
    
    log_info "Step 1: Installing system packages..."
    install_system_packages
    
    log_info "Step 2: Installing Python..."
    install_python
    
    log_info "Step 3: Installing Node.js..."
    install_nodejs
    
    log_info "Step 4: Installing Docker..."
    install_docker
    
    log_info "Step 5: Installing Playwright dependencies..."
    install_playwright_deps
    
    log_info "Step 6: Setting up application user..."
    setup_app_user
    
    log_info "Step 7: Setting up application..."
    setup_application
    
    log_info "Step 8: Configuring environment..."
    setup_environment
    
    log_info "Step 9: Setting up systemd service..."
    setup_systemd_service
    
    log_info "Step 10: Configuring Nginx..."
    setup_nginx
    
    log_info "Step 11: Setting up firewall..."
    setup_firewall
    
    log_info "Step 12: Setting up log rotation..."
    setup_logrotate
    
    log_info "Step 13: Setting up monitoring..."
    setup_monitoring
    
    log_success "Deployment completed successfully!"
    
    echo
    log_info "Next steps:"
    echo "1. Edit $APP_DIR/.env with your actual configuration"
    echo "2. Start the service: sudo systemctl start $SERVICE_NAME"
    echo "3. Check status: sudo systemctl status $SERVICE_NAME"
    echo "4. View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "5. Configure SSL certificate (recommended)"
    echo
    log_warning "Please reboot the system to ensure all changes take effect"
}

# Run main function
main "$@"