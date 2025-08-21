#!/bin/bash

# AI Trading Sentinel - Contabo VPS Production Deployment
# TRAE-SentinelOps: Complete 24/7 Cloud Deployment
# Version: 3.0.0 - Production Ready
# Target: Ubuntu 22.04/24.04 LTS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration - Update these values
APP_NAME="ai-trading-sentinel"
APP_USER="tradebot"
APP_DIR="/opt/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
SERVICE_NAME="tradebot-sentinel"
GITHUB_REPO="https://github.com/YOUR_USERNAME/ai-trading-sentinel.git"
DOMAIN="your-domain.com"  # Update with your actual domain
SSL_EMAIL="admin@your-domain.com"  # Update with your email

# System Requirements
MIN_RAM_GB=4
MIN_DISK_GB=20
REQUIRED_PORTS=("22" "80" "443" "3000" "5000" "8080")

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS] $1${NC}"
}

header() {
    echo -e "\n${MAGENTA}========================================${NC}"
    echo -e "${MAGENTA} $1${NC}"
    echo -e "${MAGENTA}========================================${NC}\n"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Check system requirements
check_system_requirements() {
    header "Checking System Requirements"
    
    # Check RAM
    local ram_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $ram_gb -lt $MIN_RAM_GB ]]; then
        warn "RAM: ${ram_gb}GB (minimum ${MIN_RAM_GB}GB recommended)"
    else
        log "RAM: ${ram_gb}GB [OK]"
    fi
    
    # Check disk space
    local disk_gb=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ $disk_gb -lt $MIN_DISK_GB ]]; then
        warn "Disk space: ${disk_gb}GB (minimum ${MIN_DISK_GB}GB recommended)"
    else
        log "Disk space: ${disk_gb}GB [OK]"
    fi
    
    # Check OS
    local os_version=$(lsb_release -d | cut -f2)
    log "OS: $os_version"
    
    success "System requirements check completed"
}

# Update system packages
update_system() {
    header "Updating System Packages"
    
    export DEBIAN_FRONTEND=noninteractive
    
    log "Updating package lists..."
    apt update -qq
    
    log "Upgrading system packages..."
    apt upgrade -y -qq
    
    log "Installing essential packages..."
    apt install -y -qq \
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
        fail2ban \
        ufw \
        logrotate \
        cron \
        supervisor
    
    success "System packages updated"
}

# Install Python and dependencies
install_python() {
    header "Installing Python Environment"
    
    log "Installing Python 3.10+..."
    apt install -y -qq python3 python3-pip python3-venv python3-dev
    
    # Verify Python version
    local python_version=$(python3 --version | cut -d' ' -f2)
    log "Python version: $python_version"
    
    # Install pip packages
    log "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    success "Python environment installed"
}

# Install Node.js for frontend
install_nodejs() {
    header "Installing Node.js Environment"
    
    log "Adding NodeSource repository..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    
    log "Installing Node.js..."
    apt install -y -qq nodejs
    
    # Verify installation
    local node_version=$(node --version)
    local npm_version=$(npm --version)
    log "Node.js version: $node_version"
    log "npm version: $npm_version"
    
    success "Node.js environment installed"
}

# Install Docker
install_docker() {
    header "Installing Docker"
    
    log "Adding Docker repository..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt update -qq
    
    log "Installing Docker Engine..."
    apt install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    log "Starting Docker service..."
    systemctl start docker
    systemctl enable docker
    
    # Add app user to docker group
    usermod -aG docker $APP_USER 2>/dev/null || true
    
    # Verify installation
    local docker_version=$(docker --version | cut -d' ' -f3 | sed 's/,//')
    log "Docker version: $docker_version"
    
    success "Docker installed and configured"
}

# Install Nginx
install_nginx() {
    header "Installing Nginx"
    
    log "Installing Nginx..."
    apt install -y -qq nginx
    
    log "Starting Nginx service..."
    systemctl start nginx
    systemctl enable nginx
    
    # Verify installation
    local nginx_version=$(nginx -v 2>&1 | cut -d' ' -f3 | sed 's/nginx\///')
    log "Nginx version: $nginx_version"
    
    success "Nginx installed and configured"
}

# Install Certbot for SSL
install_certbot() {
    header "Installing Certbot for SSL"
    
    log "Installing Certbot..."
    apt install -y -qq certbot python3-certbot-nginx
    
    success "Certbot installed"
}

# Create application user
create_app_user() {
    header "Creating Application User"
    
    if id "$APP_USER" &>/dev/null; then
        log "User $APP_USER already exists"
    else
        log "Creating user $APP_USER..."
        useradd -r -s /bin/bash -d $APP_DIR -m $APP_USER
        success "User $APP_USER created"
    fi
}

# Setup application directories
setup_directories() {
    header "Setting Up Application Directories"
    
    log "Creating application directories..."
    mkdir -p $APP_DIR
    mkdir -p $LOG_DIR
    mkdir -p /etc/$APP_NAME
    
    log "Setting directory permissions..."
    chown -R $APP_USER:$APP_USER $APP_DIR
    chown -R $APP_USER:$APP_USER $LOG_DIR
    chmod 755 $APP_DIR
    chmod 755 $LOG_DIR
    
    success "Application directories created"
}

# Clone and setup application
setup_application() {
    header "Setting Up Application"
    
    log "Cloning repository..."
    if [[ -d "$APP_DIR/.git" ]]; then
        log "Repository already exists, pulling latest changes..."
        cd $APP_DIR
        sudo -u $APP_USER git pull origin main
    else
        sudo -u $APP_USER git clone $GITHUB_REPO $APP_DIR
        cd $APP_DIR
    fi
    
    log "Setting up Python virtual environment..."
    sudo -u $APP_USER python3 -m venv venv
    
    log "Installing Python dependencies..."
    sudo -u $APP_USER ./venv/bin/pip install --upgrade pip
    sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt
    
    log "Installing frontend dependencies..."
    if [[ -f "frontend/package.json" ]]; then
        cd frontend
        sudo -u $APP_USER npm install
        sudo -u $APP_USER npm run build
        cd ..
    fi
    
    success "Application setup completed"
}

# Configure environment variables
setup_environment() {
    header "Configuring Environment Variables"
    
    log "Creating production environment file..."
    
    cat > $APP_DIR/.env.production << EOF
# AI Trading Sentinel - Production Environment
# Generated: $(date)

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)

# Database Settings
DATABASE_URL=sqlite:///$APP_DIR/data/trading.db

# Trading Platform Credentials (UPDATE THESE)
BULENOX_USERNAME=your_username_here
BULENOX_PASSWORD=your_password_here
BROKER_URL=https://bulenox.projectx.com/login

# Browser Settings
HEADLESS=true
USE_TEMP_PROFILE=true
SCREENSHOT_ON_FAILURE=true
CHROME_OPTS=--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu --window-size=1920,1080

# Logging
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/trading.log

# Security
JWT_SECRET_KEY=$(openssl rand -base64 32)
SESSION_TIMEOUT=3600

# Monitoring
HEALTH_CHECK_INTERVAL=300
ALERT_EMAIL=admin@your-domain.com

# API Settings
API_HOST=0.0.0.0
API_PORT=5000
FRONTEND_PORT=3000

EOF
    
    chown $APP_USER:$APP_USER $APP_DIR/.env.production
    chmod 600 $APP_DIR/.env.production
    
    warn "Please update the credentials in $APP_DIR/.env.production"
    
    success "Environment configuration created"
}

# Setup systemd services
setup_systemd_services() {
    header "Setting Up Systemd Services"
    
    # Backend API service
    log "Creating backend service..."
    cat > /etc/systemd/system/${SERVICE_NAME}-api.service << EOF
[Unit]
Description=AI Trading Sentinel API
After=network.target
Wants=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env.production
ExecStart=$APP_DIR/venv/bin/python backend_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}-api

[Install]
WantedBy=multi-user.target
EOF

    # Trading bot service
    log "Creating trading bot service..."
    cat > /etc/systemd/system/${SERVICE_NAME}-bot.service << EOF
[Unit]
Description=AI Trading Sentinel Bot
After=network.target ${SERVICE_NAME}-api.service
Wants=network.target
Requires=${SERVICE_NAME}-api.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env.production
ExecStart=$APP_DIR/venv/bin/python tradebot_sentinel_bulenox_automation.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}-bot

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service (if using Node.js server)
    if [[ -f "$APP_DIR/frontend/package.json" ]]; then
        log "Creating frontend service..."
        cat > /etc/systemd/system/${SERVICE_NAME}-frontend.service << EOF
[Unit]
Description=AI Trading Sentinel Frontend
After=network.target ${SERVICE_NAME}-api.service
Wants=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/frontend
Environment=NODE_ENV=production
Environment=VITE_API_URL=https://$DOMAIN/api
ExecStart=/usr/bin/npm run preview
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}-frontend

[Install]
WantedBy=multi-user.target
EOF
    fi
    
    log "Reloading systemd daemon..."
    systemctl daemon-reload
    
    success "Systemd services configured"
}

# Configure Nginx reverse proxy
setup_nginx_config() {
    header "Configuring Nginx Reverse Proxy"
    
    log "Creating Nginx configuration..."
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend (React/Vite)
    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API Backend
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # WebSocket endpoint
    location /ws {
        proxy_pass http://127.0.0.1:5000;
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
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Admin panel (password protected)
    location /admin {
        auth_basic "Admin Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    nginx -t
    
    success "Nginx configuration created"
}

# Setup SSL certificate
setup_ssl() {
    header "Setting Up SSL Certificate"
    
    if [[ "$DOMAIN" != "your-domain.com" ]] && [[ "$SSL_EMAIL" != "admin@your-domain.com" ]]; then
        log "Obtaining SSL certificate for $DOMAIN..."
        
        # Stop nginx temporarily
        systemctl stop nginx
        
        # Get certificate
        certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email $SSL_EMAIL --agree-tos --non-interactive
        
        # Start nginx
        systemctl start nginx
        
        # Setup auto-renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet --nginx" | crontab -
        
        success "SSL certificate installed for $DOMAIN"
    else
        warn "Domain and email not configured. Skipping SSL setup."
        warn "Update DOMAIN and SSL_EMAIL variables and run: certbot --nginx -d yourdomain.com"
    fi
}

# Configure firewall
setup_firewall() {
    header "Configuring Firewall"
    
    log "Resetting UFW to defaults..."
    ufw --force reset
    
    log "Setting default policies..."
    ufw default deny incoming
    ufw default allow outgoing
    
    log "Opening required ports..."
    for port in "${REQUIRED_PORTS[@]}"; do
        ufw allow $port
        log "Opened port $port"
    done
    
    log "Enabling UFW..."
    ufw --force enable
    
    success "Firewall configured"
}

# Setup fail2ban
setup_fail2ban() {
    header "Configuring Fail2ban"
    
    log "Creating jail configuration..."
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
EOF
    
    log "Restarting fail2ban..."
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    success "Fail2ban configured"
}

# Setup log rotation
setup_logrotate() {
    header "Setting Up Log Rotation"
    
    log "Creating logrotate configuration..."
    cat > /etc/logrotate.d/$APP_NAME << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload ${SERVICE_NAME}-api || true
        systemctl reload ${SERVICE_NAME}-bot || true
    endscript
}
EOF
    
    success "Log rotation configured"
}

# Setup monitoring
setup_monitoring() {
    header "Setting Up Monitoring"
    
    log "Creating health check script..."
    cat > $APP_DIR/health_monitor.py << 'EOF'
#!/usr/bin/env python3

import requests
import subprocess
import smtplib
import os
import json
from email.mime.text import MIMEText
from datetime import datetime

def check_service_status(service_name):
    """Check if systemd service is running"""
    try:
        result = subprocess.run(['systemctl', 'is-active', service_name], 
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except:
        return False

def check_api_health():
    """Check API endpoint health"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=10)
        return response.status_code == 200
    except:
        return False

def send_alert(subject, message):
    """Send email alert"""
    try:
        alert_email = os.getenv('ALERT_EMAIL')
        if not alert_email:
            return False
            
        # Log to file instead of email for now
        with open('/var/log/ai-trading-sentinel/alerts.log', 'a') as f:
            f.write(f"[{datetime.now()}] {subject}: {message}\n")
        return True
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False

def main():
    issues = []
    
    # Check services
    services = ['tradebot-sentinel-api', 'tradebot-sentinel-bot']
    for service in services:
        if not check_service_status(service):
            issues.append(f'{service} is down')
    
    # Check API health
    if not check_api_health():
        issues.append('API health check failed')
    
    # Check disk space
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            usage = lines[1].split()[4].replace('%', '')
            if int(usage) > 90:
                issues.append(f'Disk usage high: {usage}%')
    except:
        pass
    
    # Report issues
    if issues:
        message = '\n'.join(issues)
        send_alert('System Alert', message)
        print(f"Issues detected: {message}")
    else:
        print("All systems operational")

if __name__ == '__main__':
    main()
EOF
    
    chmod +x $APP_DIR/health_monitor.py
    chown $APP_USER:$APP_USER $APP_DIR/health_monitor.py
    
    log "Creating monitoring cron job..."
    echo "*/5 * * * * $APP_USER $APP_DIR/venv/bin/python $APP_DIR/health_monitor.py" > /etc/cron.d/$APP_NAME-monitor
    
    success "Monitoring configured"
}

# Create admin user for Nginx
create_admin_user() {
    header "Creating Admin User"
    
    log "Creating admin user for web interface..."
    
    # Generate random password
    local admin_password=$(openssl rand -base64 12)
    
    # Create htpasswd file
    echo "admin:$(openssl passwd -apr1 $admin_password)" > /etc/nginx/.htpasswd
    
    log "Admin credentials created:"
    log "Username: admin"
    log "Password: $admin_password"
    warn "Please save these credentials securely!"
    
    success "Admin user created"
}

# Start services
start_services() {
    header "Starting Services"
    
    log "Starting and enabling services..."
    
    # Start services in order
    systemctl enable ${SERVICE_NAME}-api
    systemctl start ${SERVICE_NAME}-api
    sleep 5
    
    systemctl enable ${SERVICE_NAME}-bot
    systemctl start ${SERVICE_NAME}-bot
    
    if [[ -f "/etc/systemd/system/${SERVICE_NAME}-frontend.service" ]]; then
        systemctl enable ${SERVICE_NAME}-frontend
        systemctl start ${SERVICE_NAME}-frontend
    fi
    
    # Restart nginx
    systemctl restart nginx
    
    success "All services started"
}

# Display deployment summary
show_deployment_summary() {
    header "Deployment Summary"
    
    echo -e "${GREEN}AI Trading Sentinel has been successfully deployed!${NC}\n"
    
    echo -e "${CYAN}System Information:${NC}"
    echo -e "  Server: $(hostname -I | awk '{print $1}')"
    echo -e "  Domain: $DOMAIN"
    echo -e "  SSL: $(if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then echo "Enabled"; else echo "Not configured"; fi)"
    echo -e "  OS: $(lsb_release -d | cut -f2)\n"
    
    echo -e "${CYAN}Service Status:${NC}"
    for service in "${SERVICE_NAME}-api" "${SERVICE_NAME}-bot"; do
        local status=$(systemctl is-active $service)
        local color=$([[ "$status" == "active" ]] && echo "$GREEN" || echo "$RED")
        echo -e "  $service: ${color}$status${NC}"
    done
    echo
    
    echo -e "${CYAN}Access URLs:${NC}"
    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        echo -e "  Web Interface: ${YELLOW}https://$DOMAIN${NC}"
        echo -e "  API Endpoint: ${YELLOW}https://$DOMAIN/api${NC}"
    else
        local server_ip=$(hostname -I | awk '{print $1}')
        echo -e "  Web Interface: ${YELLOW}http://$server_ip${NC}"
        echo -e "  API Endpoint: ${YELLOW}http://$server_ip/api${NC}"
    fi
    echo
    
    echo -e "${CYAN}Important Files:${NC}"
    echo -e "  Application: ${YELLOW}$APP_DIR${NC}"
    echo -e "  Environment: ${YELLOW}$APP_DIR/.env.production${NC}"
    echo -e "  Logs: ${YELLOW}$LOG_DIR${NC}"
    echo -e "  Nginx Config: ${YELLOW}/etc/nginx/sites-available/$APP_NAME${NC}\n"
    
    echo -e "${CYAN}Management Commands:${NC}"
    echo -e "  Check status: ${YELLOW}systemctl status ${SERVICE_NAME}-api${NC}"
    echo -e "  View logs: ${YELLOW}journalctl -u ${SERVICE_NAME}-api -f${NC}"
    echo -e "  Restart bot: ${YELLOW}systemctl restart ${SERVICE_NAME}-bot${NC}"
    echo -e "  Monitor health: ${YELLOW}$APP_DIR/venv/bin/python $APP_DIR/health_monitor.py${NC}\n"
    
    echo -e "${RED}Next Steps:${NC}"
    echo -e "  1. Update credentials in: ${YELLOW}$APP_DIR/.env.production${NC}"
    echo -e "  2. Configure domain DNS to point to this server"
    echo -e "  3. Run SSL setup: ${YELLOW}certbot --nginx -d $DOMAIN${NC}"
    echo -e "  4. Test trading functionality"
    echo -e "  5. Setup monitoring alerts\n"
    
    success "Deployment completed successfully!"
}

# Main deployment function
main() {
    header "AI Trading Sentinel - Contabo VPS Deployment"
    
    log "Starting deployment process..."
    
    # Pre-deployment checks
    check_root
    check_system_requirements
    
    # System setup
    update_system
    install_python
    install_nodejs
    install_docker
    install_nginx
    install_certbot
    
    # Application setup
    create_app_user
    setup_directories
    setup_application
    setup_environment
    
    # Service configuration
    setup_systemd_services
    setup_nginx_config
    
    # Security setup
    setup_firewall
    setup_fail2ban
    create_admin_user
    
    # Monitoring and maintenance
    setup_logrotate
    setup_monitoring
    
    # SSL setup (if domain configured)
    setup_ssl
    
    # Start services
    start_services
    
    # Show summary
    show_deployment_summary
    
    log "Deployment process completed!"
}

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi