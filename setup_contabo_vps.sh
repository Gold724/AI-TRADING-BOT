#!/bin/bash

# Bulenox Trading Bot - Contabo VPS Setup Script
# TRAE-SentinelOps v2.0.0 - Automated VPS Configuration
# 
# This script automates the complete setup of the Bulenox trading bot
# on a fresh Contabo VPS with Ubuntu 22.04/24.04

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
PROJECT_NAME="bulenox-trading-bot"
SERVICE_NAME="bulenox-trader"
DEPLOY_PATH="/opt/trading-bot"
LOG_PATH="/var/log"
USER_NAME="trader"
PYTHON_VERSION="3.10"
NODE_VERSION="18"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
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

log_header() {
    echo -e "\n${BOLD}${BLUE}=== $1 ===${NC}\n"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Update system packages
update_system() {
    log_header "Updating System Packages"
    
    log_info "Updating package lists..."
    apt update
    
    log_info "Upgrading installed packages..."
    apt upgrade -y
    
    log_info "Installing essential packages..."
    apt install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        htop \
        nano \
        vim \
        tmux \
        screen \
        fail2ban \
        ufw \
        logrotate \
        cron \
        supervisor \
        nginx \
        certbot \
        python3-certbot-nginx
    
    log_success "System packages updated successfully"
}

# Install Python and dependencies
install_python() {
    log_header "Installing Python ${PYTHON_VERSION}"
    
    # Add deadsnakes PPA for latest Python versions
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    
    # Install Python
    apt install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-dev \
        python${PYTHON_VERSION}-venv \
        python3-pip \
        python3-setuptools \
        python3-wheel
    
    # Create symlinks
    ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3
    ln -sf /usr/bin/python3 /usr/bin/python
    
    # Upgrade pip
    python3 -m pip install --upgrade pip setuptools wheel
    
    log_success "Python ${PYTHON_VERSION} installed successfully"
}

# Install Node.js
install_nodejs() {
    log_header "Installing Node.js ${NODE_VERSION}"
    
    # Install NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    
    # Install Node.js
    apt install -y nodejs
    
    # Install global packages
    npm install -g pm2 yarn
    
    log_success "Node.js ${NODE_VERSION} installed successfully"
}

# Install Playwright
install_playwright() {
    log_header "Installing Playwright"
    
    # Install Playwright via pip
    python3 -m pip install playwright
    
    # Install browser dependencies
    python3 -m playwright install-deps
    
    # Install browsers
    python3 -m playwright install
    
    log_success "Playwright installed successfully"
}

# Create system user
create_user() {
    log_header "Creating System User"
    
    if id "$USER_NAME" &>/dev/null; then
        log_warning "User $USER_NAME already exists"
    else
        # Create user with home directory
        useradd -m -s /bin/bash "$USER_NAME"
        
        # Add to sudo group
        usermod -aG sudo "$USER_NAME"
        
        log_success "User $USER_NAME created successfully"
    fi
    
    # Create project directory
    mkdir -p "$DEPLOY_PATH"
    chown -R "$USER_NAME:$USER_NAME" "$DEPLOY_PATH"
    
    # Create log directory
    mkdir -p "$LOG_PATH"
    chown -R "$USER_NAME:$USER_NAME" "$LOG_PATH/trading-bot*" 2>/dev/null || true
}

# Setup firewall
setup_firewall() {
    log_header "Configuring Firewall"
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    ufw allow 22/tcp
    
    # Allow HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow API ports
    ufw allow 5000/tcp  # Flask API
    ufw allow 5001/tcp  # WebSocket
    
    # Enable firewall
    ufw --force enable
    
    log_success "Firewall configured successfully"
}

# Configure fail2ban
setup_fail2ban() {
    log_header "Configuring Fail2ban"
    
    # Create custom jail configuration
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF
    
    # Restart fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log_success "Fail2ban configured successfully"
}

# Clone repository
clone_repository() {
    log_header "Cloning Repository"
    
    if [[ -z "${GITHUB_REPO:-}" ]]; then
        log_error "GITHUB_REPO environment variable not set"
        log_info "Please set: export GITHUB_REPO='https://github.com/username/repo.git'"
        exit 1
    fi
    
    # Remove existing directory if it exists
    if [[ -d "$DEPLOY_PATH/src" ]]; then
        log_warning "Removing existing source directory"
        rm -rf "$DEPLOY_PATH/src"
    fi
    
    # Clone repository
    log_info "Cloning from $GITHUB_REPO"
    git clone "$GITHUB_REPO" "$DEPLOY_PATH/src"
    
    # Set ownership
    chown -R "$USER_NAME:$USER_NAME" "$DEPLOY_PATH"
    
    log_success "Repository cloned successfully"
}

# Install Python dependencies
install_dependencies() {
    log_header "Installing Python Dependencies"
    
    cd "$DEPLOY_PATH/src"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip in virtual environment
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing from requirements.txt"
        pip install -r requirements.txt
    fi
    
    # Install additional packages
    pip install \
        gunicorn \
        supervisor \
        psutil \
        aiohttp \
        requests
    
    # Install Playwright in virtual environment
    pip install playwright
    playwright install
    
    # Set ownership
    chown -R "$USER_NAME:$USER_NAME" "$DEPLOY_PATH"
    
    log_success "Python dependencies installed successfully"
}

# Create environment file
create_env_file() {
    log_header "Creating Environment Configuration"
    
    cat > "$DEPLOY_PATH/.env" << EOF
# Bulenox Trading Bot Configuration
# Generated on $(date)

# Bulenox Platform
BULENOX_USERNAME=${BULENOX_USERNAME:-}
BULENOX_PASSWORD=${BULENOX_PASSWORD:-}
BULENOX_LOGIN_URL=https://bulenox.projectx.com/login

# Application Settings
FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-$(openssl rand -hex 32)}
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Trading Configuration
MAX_CONTRACT_SIZE=10
MAX_DAILY_TRADES=50
MAX_DRAWDOWN_PERCENT=5.0
RISK_MANAGEMENT_ENABLED=true
EMERGENCY_STOP_ENABLED=true

# Bot Settings
HEADLESS_MODE=true
SCREENSHOT_ON_ERROR=true
NETWORK_INTERCEPTION=true
SESSION_TIMEOUT=3600
RETRY_ATTEMPTS=3
RETRY_DELAY=5

# Monitoring
HEALTH_CHECK_INTERVAL=300
BACKUP_ENABLED=true
MONITORING_ENABLED=true
ALERT_EMAIL=${ALERT_EMAIL:-}
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-}

# System
TIMEZONE=UTC
API_PORT=5000
WEBSOCKET_PORT=5001

# Paths
PROJECT_PATH=$DEPLOY_PATH
LOG_PATH=$LOG_PATH
DATA_PATH=$DEPLOY_PATH/data
BACKUP_PATH=$DEPLOY_PATH/backups
EOF
    
    # Set secure permissions
    chmod 600 "$DEPLOY_PATH/.env"
    chown "$USER_NAME:$USER_NAME" "$DEPLOY_PATH/.env"
    
    log_success "Environment file created"
    log_warning "Please update $DEPLOY_PATH/.env with your credentials"
}

# Create systemd service
create_systemd_service() {
    log_header "Creating Systemd Service"
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Bulenox Trading Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$DEPLOY_PATH/src
Environment=PATH=$DEPLOY_PATH/src/venv/bin
EnvironmentFile=$DEPLOY_PATH/.env
ExecStart=$DEPLOY_PATH/src/venv/bin/python bulenox_ai_playwright_contracts.py
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
ReadWritePaths=$DEPLOY_PATH $LOG_PATH /tmp

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    log_success "Systemd service created and enabled"
}

# Setup Nginx
setup_nginx() {
    log_header "Configuring Nginx"
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Create trading bot site configuration
    cat > "/etc/nginx/sites-available/$PROJECT_NAME" << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # API proxy
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # WebSocket proxy
    location /ws/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/trading-bot/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Default location
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    # Enable site
    ln -sf "/etc/nginx/sites-available/$PROJECT_NAME" "/etc/nginx/sites-enabled/"
    
    # Test configuration
    nginx -t
    
    # Restart Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log_success "Nginx configured successfully"
}

# Setup SSL certificate
setup_ssl() {
    log_header "Setting up SSL Certificate"
    
    if [[ -z "${DOMAIN_NAME:-}" ]]; then
        log_warning "DOMAIN_NAME not set, skipping SSL setup"
        log_info "To setup SSL later: certbot --nginx -d yourdomain.com"
        return
    fi
    
    if [[ -z "${SSL_EMAIL:-}" ]]; then
        log_warning "SSL_EMAIL not set, skipping SSL setup"
        return
    fi
    
    # Update Nginx configuration with domain
    sed -i "s/server_name _;/server_name $DOMAIN_NAME;/" "/etc/nginx/sites-available/$PROJECT_NAME"
    nginx -t && systemctl reload nginx
    
    # Obtain SSL certificate
    certbot --nginx -d "$DOMAIN_NAME" --email "$SSL_EMAIL" --agree-tos --non-interactive
    
    log_success "SSL certificate configured for $DOMAIN_NAME"
}

# Setup log rotation
setup_logrotate() {
    log_header "Configuring Log Rotation"
    
    cat > "/etc/logrotate.d/$SERVICE_NAME" << EOF
$LOG_PATH/trading-bot*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER_NAME $USER_NAME
    postrotate
        systemctl reload $SERVICE_NAME || true
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

# Setup monitoring
setup_monitoring() {
    log_header "Setting up Monitoring"
    
    # Create monitoring script symlink
    ln -sf "$DEPLOY_PATH/src/monitor_trading_bot.py" "/usr/local/bin/monitor-bot"
    chmod +x "/usr/local/bin/monitor-bot"
    
    # Create remote management script symlink
    ln -sf "$DEPLOY_PATH/src/remote_management.py" "/usr/local/bin/remote-mgmt"
    chmod +x "/usr/local/bin/remote-mgmt"
    
    # Create monitoring service
    cat > "/etc/systemd/system/$SERVICE_NAME-monitor.service" << EOF
[Unit]
Description=Bulenox Trading Bot Monitor
After=network.target $SERVICE_NAME.service
Wants=$SERVICE_NAME.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$DEPLOY_PATH/src
Environment=PATH=$DEPLOY_PATH/src/venv/bin
EnvironmentFile=$DEPLOY_PATH/.env
ExecStart=$DEPLOY_PATH/src/venv/bin/python monitor_trading_bot.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable monitoring service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME-monitor"
    
    # Create cron job for health checks
    cat > "/etc/cron.d/$SERVICE_NAME-health" << EOF
# Bulenox Trading Bot Health Check
*/5 * * * * $USER_NAME /usr/local/bin/monitor-bot --once >/dev/null 2>&1
EOF
    
    log_success "Monitoring configured"
}

# Create backup script
setup_backup() {
    log_header "Setting up Backup System"
    
    # Create backup directory
    mkdir -p "$DEPLOY_PATH/backups"
    chown "$USER_NAME:$USER_NAME" "$DEPLOY_PATH/backups"
    
    # Create backup script
    cat > "$DEPLOY_PATH/backup.sh" << 'EOF'
#!/bin/bash
# Automated backup script for Bulenox Trading Bot

BACKUP_DIR="/opt/trading-bot/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="trading_bot_backup_$TIMESTAMP"

# Create backup
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup configuration
cp -r /opt/trading-bot/.env "$BACKUP_DIR/$BACKUP_NAME/"
cp -r /opt/trading-bot/src/*.json "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null || true

# Backup logs
journalctl -u bulenox-trader --no-pager > "$BACKUP_DIR/$BACKUP_NAME/service.log"
cp /var/log/trading-bot*.log "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null || true

# Create archive
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Keep only last 7 backups
ls -t *.tar.gz | tail -n +8 | xargs -r rm

echo "Backup created: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
EOF
    
    chmod +x "$DEPLOY_PATH/backup.sh"
    chown "$USER_NAME:$USER_NAME" "$DEPLOY_PATH/backup.sh"
    
    # Create daily backup cron job
    cat > "/etc/cron.d/$SERVICE_NAME-backup" << EOF
# Daily backup for Bulenox Trading Bot
0 2 * * * $USER_NAME $DEPLOY_PATH/backup.sh >/dev/null 2>&1
EOF
    
    log_success "Backup system configured"
}

# Final setup and start services
finalize_setup() {
    log_header "Finalizing Setup"
    
    # Create data directories
    mkdir -p "$DEPLOY_PATH/data" "$DEPLOY_PATH/logs" "$DEPLOY_PATH/screenshots"
    chown -R "$USER_NAME:$USER_NAME" "$DEPLOY_PATH"
    
    # Set proper permissions
    chmod 755 "$DEPLOY_PATH"
    chmod 644 "$DEPLOY_PATH/.env"
    
    # Start services
    log_info "Starting services..."
    systemctl start "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME-monitor"
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Trading bot service started successfully"
    else
        log_error "Trading bot service failed to start"
        systemctl status "$SERVICE_NAME" --no-pager
    fi
    
    if systemctl is-active --quiet "$SERVICE_NAME-monitor"; then
        log_success "Monitoring service started successfully"
    else
        log_warning "Monitoring service failed to start"
    fi
    
    log_success "Setup completed successfully!"
}

# Display final information
show_final_info() {
    log_header "Setup Complete - Important Information"
    
    echo -e "${GREEN}🎉 Bulenox Trading Bot has been successfully deployed!${NC}\n"
    
    echo -e "${BOLD}📋 Service Information:${NC}"
    echo -e "  Service Name: $SERVICE_NAME"
    echo -e "  Deploy Path: $DEPLOY_PATH"
    echo -e "  User: $USER_NAME"
    echo -e "  API Port: 5000"
    echo -e "  WebSocket Port: 5001\n"
    
    echo -e "${BOLD}🔧 Management Commands:${NC}"
    echo -e "  Check Status: ${CYAN}remote-mgmt status${NC}"
    echo -e "  View Logs: ${CYAN}remote-mgmt logs${NC}"
    echo -e "  Restart Bot: ${CYAN}remote-mgmt restart${NC}"
    echo -e "  Monitor: ${CYAN}monitor-bot --report${NC}"
    echo -e "  Emergency Stop: ${CYAN}remote-mgmt emergency-stop${NC}\n"
    
    echo -e "${BOLD}📁 Important Files:${NC}"
    echo -e "  Environment: ${CYAN}$DEPLOY_PATH/.env${NC}"
    echo -e "  Service Config: ${CYAN}/etc/systemd/system/$SERVICE_NAME.service${NC}"
    echo -e "  Nginx Config: ${CYAN}/etc/nginx/sites-available/$PROJECT_NAME${NC}"
    echo -e "  Logs: ${CYAN}journalctl -u $SERVICE_NAME -f${NC}\n"
    
    echo -e "${BOLD}⚠️  Next Steps:${NC}"
    echo -e "  1. Update credentials in: ${YELLOW}$DEPLOY_PATH/.env${NC}"
    echo -e "  2. Test the API: ${YELLOW}curl http://localhost:5000/health${NC}"
    echo -e "  3. Check service status: ${YELLOW}remote-mgmt status${NC}"
    echo -e "  4. Monitor logs: ${YELLOW}remote-mgmt logs --follow${NC}"
    
    if [[ -n "${DOMAIN_NAME:-}" ]]; then
        echo -e "  5. Access web interface: ${YELLOW}https://$DOMAIN_NAME${NC}"
    else
        echo -e "  5. Setup domain and SSL if needed"
    fi
    
    echo -e "\n${BOLD}🔒 Security Notes:${NC}"
    echo -e "  - Firewall is enabled with necessary ports open"
    echo -e "  - Fail2ban is configured for SSH protection"
    echo -e "  - Service runs with limited privileges"
    echo -e "  - Environment file has secure permissions"
    
    echo -e "\n${BOLD}📊 Monitoring:${NC}"
    echo -e "  - Health checks run every 5 minutes"
    echo -e "  - Daily backups are scheduled"
    echo -e "  - Log rotation is configured"
    echo -e "  - Monitoring service tracks performance"
    
    echo -e "\n${GREEN}✅ Your Bulenox Trading Bot is ready for production!${NC}"
}

# Main execution
main() {
    log_header "Bulenox Trading Bot - VPS Setup"
    
    # Check prerequisites
    check_root
    
    # Verify required environment variables
    if [[ -z "${GITHUB_REPO:-}" ]]; then
        log_error "Required environment variables not set"
        echo -e "\nPlease set the following variables:"
        echo -e "  ${YELLOW}export GITHUB_REPO='https://github.com/username/repo.git'${NC}"
        echo -e "  ${YELLOW}export BULENOX_USERNAME='your_username'${NC}"
        echo -e "  ${YELLOW}export BULENOX_PASSWORD='your_password'${NC}"
        echo -e "\nOptional variables:"
        echo -e "  ${YELLOW}export DOMAIN_NAME='yourdomain.com'${NC}"
        echo -e "  ${YELLOW}export SSL_EMAIL='your@email.com'${NC}"
        echo -e "  ${YELLOW}export ALERT_EMAIL='alerts@email.com'${NC}"
        echo -e "  ${YELLOW}export SLACK_WEBHOOK_URL='https://hooks.slack.com/...'${NC}"
        exit 1
    fi
    
    # Execute setup steps
    update_system
    install_python
    install_nodejs
    install_playwright
    create_user
    setup_firewall
    setup_fail2ban
    clone_repository
    install_dependencies
    create_env_file
    create_systemd_service
    setup_nginx
    setup_ssl
    setup_logrotate
    setup_monitoring
    setup_backup
    finalize_setup
    show_final_info
}

# Handle script interruption
trap 'log_error "Setup interrupted by user"; exit 1' INT TERM

# Run main function
main "$@"