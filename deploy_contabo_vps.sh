#!/bin/bash

# AI Trading Sentinel - Contabo VPS Deployment Script
# TRAE-SentinelOps: Complete 24/7 Cloud Deployment
# Version: 2.0.0
# Target: Ubuntu 22.04/24.04 LTS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ai-trading-sentinel"
APP_USER="tradebot"
APP_DIR="/opt/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
SERVICE_NAME="tradebot-sentinel"
GITHUB_REPO="https://github.com/YOUR_USERNAME/ai-trading-sentinel.git"
DOMAIN="your-domain.com"  # Optional: for HTTPS setup

# System Requirements
MIN_RAM_GB=4
MIN_DISK_GB=20
REQUIRED_PORTS=("22" "80" "443" "3000" "5000" "8080")

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

check_system_requirements() {
    log "Checking system requirements..."
    
    # Check RAM
    RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $RAM_GB -lt $MIN_RAM_GB ]]; then
        warn "RAM: ${RAM_GB}GB (recommended: ${MIN_RAM_GB}GB+)"
    else
        log "RAM: ${RAM_GB}GB ✓"
    fi
    
    # Check disk space
    DISK_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $DISK_GB -lt $MIN_DISK_GB ]]; then
        error "Insufficient disk space: ${DISK_GB}GB (required: ${MIN_DISK_GB}GB+)"
    else
        log "Disk space: ${DISK_GB}GB ✓"
    fi
    
    # Check Ubuntu version
    if ! grep -q "Ubuntu" /etc/os-release; then
        warn "Non-Ubuntu system detected. Proceeding with caution..."
    else
        UBUNTU_VERSION=$(lsb_release -rs)
        log "Ubuntu ${UBUNTU_VERSION} detected ✓"
    fi
}

setup_firewall() {
    log "Configuring UFW firewall..."
    
    # Install and enable UFW
    apt-get update -qq
    apt-get install -y ufw
    
    # Reset to defaults
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow required ports
    for port in "${REQUIRED_PORTS[@]}"; do
        ufw allow $port
        log "Opened port $port"
    done
    
    # Enable firewall
    ufw --force enable
    log "Firewall configured and enabled ✓"
}

install_dependencies() {
    log "Installing system dependencies..."
    
    # Update system
    apt-get update -qq
    apt-get upgrade -y
    
    # Install essential packages
    apt-get install -y \
        curl wget git unzip \
        build-essential software-properties-common \
        nginx supervisor redis-server \
        htop tmux vim nano \
        logrotate rsyslog \
        fail2ban ufw \
        certbot python3-certbot-nginx
    
    # Install Python 3.10+
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
    apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip
    
    # Install Node.js 18+ (for frontend)
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
    
    # Install Docker (optional)
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    
    log "Dependencies installed ✓"
}

setup_user() {
    log "Setting up application user..."
    
    # Create app user
    if ! id "$APP_USER" &>/dev/null; then
        useradd -r -m -s /bin/bash $APP_USER
        usermod -aG docker $APP_USER
        log "Created user: $APP_USER"
    else
        log "User $APP_USER already exists"
    fi
    
    # Create directories
    mkdir -p $APP_DIR $LOG_DIR
    chown -R $APP_USER:$APP_USER $APP_DIR $LOG_DIR
    chmod 755 $APP_DIR $LOG_DIR
    
    log "User and directories configured ✓"
}

install_playwright() {
    log "Installing Playwright and browsers..."
    
    # Install Playwright system dependencies
    apt-get install -y \
        libnss3-dev libatk-bridge2.0-dev libdrm-dev \
        libxcomposite-dev libxdamage-dev libxrandr-dev \
        libgbm-dev libxss-dev libasound2-dev
    
    # Install Playwright as app user
    sudo -u $APP_USER bash -c "
        cd $APP_DIR
        python3.10 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install playwright
        playwright install chromium
        playwright install-deps
    "
    
    log "Playwright installed ✓"
}

clone_repository() {
    log "Cloning application repository..."
    
    # Clone or update repository
    if [[ -d "$APP_DIR/.git" ]]; then
        sudo -u $APP_USER git -C $APP_DIR pull origin main
        log "Repository updated"
    else
        sudo -u $APP_USER git clone $GITHUB_REPO $APP_DIR
        log "Repository cloned"
    fi
    
    # Install Python dependencies
    sudo -u $APP_USER bash -c "
        cd $APP_DIR
        source venv/bin/activate
        pip install -r requirements.txt
    "
    
    # Install Node.js dependencies (if frontend exists)
    if [[ -f "$APP_DIR/package.json" ]]; then
        sudo -u $APP_USER bash -c "
            cd $APP_DIR
            npm install
            npm run build
        "
        log "Frontend built ✓"
    fi
    
    log "Application installed ✓"
}

setup_environment() {
    log "Setting up environment configuration..."
    
    # Create .env file template
    cat > $APP_DIR/.env << EOF
# AI Trading Sentinel - Production Environment
# Generated: $(date)

# Trading Configuration
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
TRADING_MODE=live
MAX_DAILY_TRADES=21
DAILY_PROFIT_TARGET=300
MAX_DRAWDOWN=150

# Fibonacci Strategy
FIBONACCI_SEQUENCE=10,10,20,30,50,80,130
GOLD_SYMBOL=GCZ25
DEFAULT_CONTRACTS=1
MAX_CONTRACTS=3

# API Configuration
FLASK_ENV=production
FLASK_DEBUG=false
API_PORT=5000
FRONTEND_PORT=3000

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Monitoring
SLACK_WEBHOOK_URL=your_slack_webhook
EMAIL_ALERTS=your_email@domain.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# GitHub (for CI/CD)
GITHUB_TOKEN=your_github_token
GITHUB_REPO_URL=$GITHUB_REPO

# VPS Configuration
VPS_IP=$(curl -s ifconfig.me)
VPS_HOSTNAME=$(hostname)
TIMEZONE=UTC
EOF

    chown $APP_USER:$APP_USER $APP_DIR/.env
    chmod 600 $APP_DIR/.env
    
    warn "Please edit $APP_DIR/.env with your actual credentials!"
    log "Environment configuration created ✓"
}

setup_systemd_service() {
    log "Setting up systemd service..."
    
    # Create systemd service file
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=AI Trading Sentinel Bot
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python tradebot_sentinel_playwright.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR $LOG_DIR /tmp

# Logging
StandardOutput=append:$LOG_DIR/bot.log
StandardError=append:$LOG_DIR/bot-error.log
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

    # Create Flask API service
    cat > /etc/systemd/system/${SERVICE_NAME}-api.service << EOF
[Unit]
Description=AI Trading Sentinel API
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 backend.main:app
Restart=always
RestartSec=5

# Logging
StandardOutput=append:$LOG_DIR/api.log
StandardError=append:$LOG_DIR/api-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    systemctl enable ${SERVICE_NAME}-api
    
    log "Systemd services configured ✓"
}

setup_nginx() {
    log "Configuring Nginx reverse proxy..."
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Create app configuration
    cat > /etc/nginx/sites-available/${APP_NAME} << EOF
server {
    listen 80;
    server_name $DOMAIN $(curl -s ifconfig.me);
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Frontend (React/Vite)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # API Backend
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket for real-time updates
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    
    # Static files
    location /static {
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Logs endpoint (restricted)
    location /logs {
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
        alias $LOG_DIR;
        autoindex on;
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
    
    # Test configuration
    nginx -t
    systemctl restart nginx
    systemctl enable nginx
    
    log "Nginx configured ✓"
}

setup_ssl() {
    log "Setting up SSL certificate..."
    
    if [[ "$DOMAIN" != "your-domain.com" ]]; then
        # Get Let's Encrypt certificate
        certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
        
        # Setup auto-renewal
        echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
        
        log "SSL certificate installed ✓"
    else
        warn "Domain not configured. Skipping SSL setup."
    fi
}

setup_monitoring() {
    log "Setting up monitoring and health checks..."
    
    # Create health check script
    cat > $APP_DIR/health_check.py << 'EOF'
#!/usr/bin/env python3

import requests
import subprocess
import smtplib
import os
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
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USERNAME')
        smtp_pass = os.getenv('SMTP_PASSWORD')
        alert_email = os.getenv('EMAIL_ALERTS')
        
        if not all([smtp_server, smtp_user, smtp_pass, alert_email]):
            return False
            
        msg = MIMEText(message)
        msg['Subject'] = f"[AI Trading Sentinel] {subject}"
        msg['From'] = smtp_user
        msg['To'] = alert_email
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send alert: {e}")
        return False

def main():
    issues = []
    
    # Check bot service
    if not check_service_status('tradebot-sentinel'):
        issues.append('Trading bot service is down')
    
    # Check API service
    if not check_service_status('tradebot-sentinel-api'):
        issues.append('API service is down')
    
    # Check API health
    if not check_api_health():
        issues.append('API health check failed')
    
    # Check disk space
    disk_usage = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
    if '9' in disk_usage.stdout.split()[-2]:  # >90% usage
        issues.append('Disk space critically low')
    
    if issues:
        alert_msg = f"Health check failed at {datetime.now()}:\n\n" + "\n".join(f"- {issue}" for issue in issues)
        send_alert("System Alert", alert_msg)
        print("CRITICAL: Issues detected")
        for issue in issues:
            print(f"  - {issue}")
        exit(1)
    else:
        print("OK: All systems healthy")

if __name__ == '__main__':
    main()
EOF

    chmod +x $APP_DIR/health_check.py
    chown $APP_USER:$APP_USER $APP_DIR/health_check.py
    
    # Setup cron job for health checks
    echo "*/5 * * * * $APP_USER cd $APP_DIR && ./health_check.py" >> /etc/crontab
    
    log "Monitoring configured ✓"
}

setup_logrotate() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/${APP_NAME} << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload ${SERVICE_NAME} || true
        systemctl reload ${SERVICE_NAME}-api || true
    endscript
}
EOF

    log "Log rotation configured ✓"
}

setup_github_cicd() {
    log "Setting up GitHub CI/CD webhook..."
    
    # Create deployment script
    cat > $APP_DIR/deploy.sh << EOF
#!/bin/bash

# Auto-deployment script
set -e

cd $APP_DIR

# Pull latest changes
sudo -u $APP_USER git pull origin main

# Update Python dependencies
sudo -u $APP_USER bash -c "
    source venv/bin/activate
    pip install -r requirements.txt
"

# Build frontend if needed
if [[ -f package.json ]]; then
    sudo -u $APP_USER npm install
    sudo -u $APP_USER npm run build
fi

# Restart services
systemctl restart ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}-api

echo "Deployment completed: \$(date)"
EOF

    chmod +x $APP_DIR/deploy.sh
    
    # Create webhook endpoint (simple)
    cat > $APP_DIR/webhook.py << 'EOF'
#!/usr/bin/env python3

from flask import Flask, request, jsonify
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'your-secret')

@app.route('/webhook', methods=['POST'])
def github_webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        return jsonify({'error': 'No signature'}), 401
    
    # Verify signature
    expected = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Trigger deployment
    try:
        subprocess.run(['/opt/ai-trading-sentinel/deploy.sh'], check=True)
        return jsonify({'status': 'deployed'})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
EOF

    log "CI/CD webhook configured ✓"
}

start_services() {
    log "Starting all services..."
    
    # Start Redis
    systemctl start redis-server
    systemctl enable redis-server
    
    # Start application services
    systemctl start ${SERVICE_NAME}
    systemctl start ${SERVICE_NAME}-api
    
    # Start Nginx
    systemctl start nginx
    
    log "All services started ✓"
}

show_status() {
    log "Deployment Status Summary"
    echo "========================="
    
    # Service status
    echo "Services:"
    systemctl is-active ${SERVICE_NAME} && echo "  ✓ Trading Bot: Running" || echo "  ✗ Trading Bot: Stopped"
    systemctl is-active ${SERVICE_NAME}-api && echo "  ✓ API: Running" || echo "  ✗ API: Stopped"
    systemctl is-active nginx && echo "  ✓ Nginx: Running" || echo "  ✗ Nginx: Stopped"
    systemctl is-active redis-server && echo "  ✓ Redis: Running" || echo "  ✗ Redis: Stopped"
    
    echo ""
    echo "URLs:"
    echo "  Frontend: http://$(curl -s ifconfig.me)"
    echo "  API: http://$(curl -s ifconfig.me)/api"
    echo "  Logs: http://$(curl -s ifconfig.me)/logs"
    
    echo ""
    echo "Important Files:"
    echo "  Config: $APP_DIR/.env"
    echo "  Logs: $LOG_DIR/"
    echo "  Service: /etc/systemd/system/${SERVICE_NAME}.service"
    
    echo ""
    echo "Management Commands:"
    echo "  Start bot: systemctl start ${SERVICE_NAME}"
    echo "  Stop bot: systemctl stop ${SERVICE_NAME}"
    echo "  View logs: journalctl -u ${SERVICE_NAME} -f"
    echo "  Health check: $APP_DIR/health_check.py"
    echo "  Deploy: $APP_DIR/deploy.sh"
    
    warn "Remember to:"
    warn "1. Edit $APP_DIR/.env with your credentials"
    warn "2. Configure your domain in Nginx if using HTTPS"
    warn "3. Set up GitHub webhook for auto-deployment"
    warn "4. Test the trading bot in simulation mode first"
}

# Main execution
main() {
    log "Starting AI Trading Sentinel VPS Deployment"
    log "Target: Contabo VPS (Ubuntu 22.04/24.04)"
    
    check_root
    check_system_requirements
    
    setup_firewall
    install_dependencies
    setup_user
    install_playwright
    clone_repository
    setup_environment
    setup_systemd_service
    setup_nginx
    setup_ssl
    setup_monitoring
    setup_logrotate
    setup_github_cicd
    start_services
    
    log "Deployment completed successfully! 🚀"
    show_status
}

# Run main function
main "$@"