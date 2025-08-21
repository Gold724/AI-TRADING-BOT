#!/bin/bash
# AI Trading Sentinel - Complete Production Deployment Script
# TRAE-SentinelOps: Deploy trading bot with monitoring on Contabo VPS
# Usage: ./deploy-production.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="trae-sentinel"
APP_USER="trae"
INSTALL_DIR="/opt/trae-sentinel"
REPO_URL="https://github.com/your-org/ai-trading-sentinel.git"
BRANCH="main"
PYTHON_VERSION="3.10"
NODE_VERSION="18"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

success() {
    echo -e "${PURPLE}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root. Use: sudo ./deploy-production.sh"
    fi
}

# System requirements check
check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if ! grep -q "Ubuntu" /etc/os-release; then
        warn "This script is optimized for Ubuntu. Proceeding anyway..."
    fi
    
    # Check memory (minimum 4GB for production)
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 4 ]]; then
        warn "Less than 4GB RAM detected ($MEMORY_GB GB). Performance may be affected."
    fi
    
    # Check disk space (minimum 20GB)
    DISK_GB=$(df / | tail -1 | awk '{print int($4/1024/1024)}')
    if [[ $DISK_GB -lt 20 ]]; then
        error "Insufficient disk space. Need at least 20GB, found ${DISK_GB}GB"
    fi
    
    success "System requirements check passed"
}

# Update system packages
update_system() {
    log "Updating system packages..."
    
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get upgrade -y
    apt-get install -y \
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
        python3-dev \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        nginx \
        ufw \
        fail2ban \
        htop \
        tree \
        jq \
        bc
    
    success "System packages updated"
}

# Install Docker and Docker Compose
install_docker() {
    log "Installing Docker and Docker Compose..."
    
    # Remove old Docker versions
    apt-get remove -y docker docker-engine docker.io containerd runc || true
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add user to docker group
    usermod -aG docker $APP_USER || true
    
    # Install Docker Compose (standalone)
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    success "Docker and Docker Compose installed"
}

# Create application user
create_user() {
    log "Creating application user: $APP_USER"
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir "$INSTALL_DIR" \
                --create-home --comment "Trae Trading Bot" "$APP_USER"
        
        # Add to docker group
        usermod -aG docker "$APP_USER"
        
        success "User $APP_USER created"
    else
        info "User $APP_USER already exists"
    fi
}

# Setup application directories
setup_directories() {
    log "Setting up application directories..."
    
    # Create directory structure
    mkdir -p "$INSTALL_DIR"/{data,logs,config,backups,scripts}
    mkdir -p /var/log/trae-sentinel
    mkdir -p /var/lib/trae-sentinel
    mkdir -p /etc/trae-sentinel
    
    # Set ownership
    chown -R "$APP_USER:$APP_USER" "$INSTALL_DIR"
    chown -R "$APP_USER:$APP_USER" /var/log/trae-sentinel
    chown -R "$APP_USER:$APP_USER" /var/lib/trae-sentinel
    chown -R "$APP_USER:$APP_USER" /etc/trae-sentinel
    
    # Set permissions
    chmod 755 "$INSTALL_DIR"
    chmod 750 /var/log/trae-sentinel
    chmod 750 /var/lib/trae-sentinel
    chmod 750 /etc/trae-sentinel
    
    success "Directories configured"
}

# Clone application repository
clone_repository() {
    log "Cloning application repository..."
    
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        info "Repository already exists, updating..."
        cd "$INSTALL_DIR"
        sudo -u "$APP_USER" git fetch origin
        sudo -u "$APP_USER" git reset --hard "origin/$BRANCH"
    else
        sudo -u "$APP_USER" git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    fi
    
    cd "$INSTALL_DIR"
    chown -R "$APP_USER:$APP_USER" .
    
    success "Repository cloned/updated"
}

# Setup Python environment
setup_python() {
    log "Setting up Python environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    sudo -u "$APP_USER" python3 -m venv venv
    
    # Activate and install dependencies
    sudo -u "$APP_USER" bash -c '
        source venv/bin/activate
        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt
        pip install gunicorn supervisor
    '
    
    success "Python environment configured"
}

# Setup Node.js environment (for frontend)
setup_nodejs() {
    log "Setting up Node.js environment..."
    
    cd "$INSTALL_DIR"
    
    if [[ -f "package.json" ]]; then
        sudo -u "$APP_USER" npm install
        sudo -u "$APP_USER" npm run build || true
        success "Node.js environment configured"
    else
        info "No package.json found, skipping Node.js setup"
    fi
}

# Configure firewall
setup_firewall() {
    log "Configuring firewall..."
    
    # Reset UFW
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH access
    ufw allow ssh
    
    # Application ports
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw allow 5000/tcp  # Flask API
    
    # Monitoring ports (restrict to local network)
    ufw allow from 10.0.0.0/8 to any port 3000    # Grafana
    ufw allow from 172.16.0.0/12 to any port 3000
    ufw allow from 192.168.0.0/16 to any port 3000
    ufw allow from 10.0.0.0/8 to any port 9090    # Prometheus
    ufw allow from 172.16.0.0/12 to any port 9090
    ufw allow from 192.168.0.0/16 to any port 9090
    ufw allow from 10.0.0.0/8 to any port 9093    # Alertmanager
    ufw allow from 172.16.0.0/12 to any port 9093
    ufw allow from 192.168.0.0/16 to any port 9093
    
    # Enable firewall
    ufw --force enable
    
    success "Firewall configured"
}

# Setup monitoring stack
setup_monitoring() {
    log "Setting up monitoring stack..."
    
    cd "$INSTALL_DIR/monitoring"
    
    # Create monitoring network
    sudo -u "$APP_USER" docker network create monitoring || true
    
    # Start monitoring services
    sudo -u "$APP_USER" docker-compose -f docker-compose.monitoring.yml up -d
    
    # Wait for services to start
    sleep 30
    
    # Import Grafana dashboard
    if [[ -f "grafana-dashboard.json" ]]; then
        info "Importing Grafana dashboard..."
        # Dashboard import will be handled by Grafana provisioning
    fi
    
    success "Monitoring stack deployed"
}

# Setup systemd services
setup_systemd() {
    log "Setting up systemd services..."
    
    cd "$INSTALL_DIR/deploy"
    
    # Run systemd setup script
    if [[ -f "setup-systemd.sh" ]]; then
        chmod +x setup-systemd.sh
        ./setup-systemd.sh
    else
        error "SystemD setup script not found"
    fi
    
    success "SystemD services configured"
}

# Configure Nginx reverse proxy
setup_nginx() {
    log "Configuring Nginx reverse proxy..."
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Create Trae Sentinel site configuration
    cat > /etc/nginx/sites-available/trae-sentinel << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location / {
        root /opt/trae-sentinel/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1y;
        add_header Cache-Control "public, immutable";
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
    ln -sf /etc/nginx/sites-available/trae-sentinel /etc/nginx/sites-enabled/
    
    # Test configuration
    nginx -t
    
    # Restart Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    success "Nginx configured"
}

# Setup SSL with Let's Encrypt (optional)
setup_ssl() {
    read -p "Do you want to setup SSL with Let's Encrypt? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Setting up SSL with Let's Encrypt..."
        
        # Install Certbot
        apt-get install -y certbot python3-certbot-nginx
        
        read -p "Enter your domain name: " DOMAIN
        read -p "Enter your email address: " EMAIL
        
        # Get certificate
        certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
        
        # Setup auto-renewal
        systemctl enable certbot.timer
        
        success "SSL configured for $DOMAIN"
    else
        info "Skipping SSL setup"
    fi
}

# Create backup script
setup_backup() {
    log "Setting up backup system..."
    
    cat > "$INSTALL_DIR/scripts/backup.sh" << 'EOF'
#!/bin/bash
# Trae Sentinel Backup Script

BACKUP_DIR="/opt/trae-sentinel/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="trae-backup-$DATE.tar.gz"

# Create backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude="/opt/trae-sentinel/venv" \
    --exclude="/opt/trae-sentinel/node_modules" \
    --exclude="/opt/trae-sentinel/.git" \
    --exclude="/opt/trae-sentinel/backups" \
    /opt/trae-sentinel \
    /var/lib/trae-sentinel \
    /etc/trae-sentinel

# Keep only last 7 backups
find "$BACKUP_DIR" -name "trae-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
EOF
    
    chmod +x "$INSTALL_DIR/scripts/backup.sh"
    chown "$APP_USER:$APP_USER" "$INSTALL_DIR/scripts/backup.sh"
    
    # Setup daily backup cron job
    echo "0 2 * * * $APP_USER $INSTALL_DIR/scripts/backup.sh" > /etc/cron.d/trae-backup
    
    success "Backup system configured"
}

# Final system configuration
final_setup() {
    log "Performing final system configuration..."
    
    # Set timezone
    timedatectl set-timezone UTC
    
    # Configure log rotation
    cat > /etc/logrotate.d/trae-sentinel << 'EOF'
/var/log/trae-sentinel/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 trae trae
    postrotate
        systemctl reload trae.service > /dev/null 2>&1 || true
    endscript
}
EOF
    
    # Setup system monitoring
    cat > /etc/cron.d/trae-monitoring << 'EOF'
# Trae Sentinel System Monitoring
*/5 * * * * root /opt/trae-sentinel/scripts/system-monitor.sh
EOF
    
    success "Final configuration completed"
}

# Display deployment summary
show_summary() {
    success "🚀 Trae AI Trading Sentinel Deployment Complete!"
    echo
    echo -e "${GREEN}=== DEPLOYMENT SUMMARY ===${NC}"
    echo -e "${BLUE}Application Directory:${NC} $INSTALL_DIR"
    echo -e "${BLUE}Service User:${NC} $APP_USER"
    echo -e "${BLUE}Log Directory:${NC} /var/log/trae-sentinel"
    echo -e "${BLUE}Data Directory:${NC} /var/lib/trae-sentinel"
    echo
    echo -e "${GREEN}=== ACCESS URLS ===${NC}"
    echo -e "${BLUE}Web Interface:${NC} http://$(curl -s ifconfig.me)"
    echo -e "${BLUE}API Endpoint:${NC} http://$(curl -s ifconfig.me)/api"
    echo -e "${BLUE}Grafana Dashboard:${NC} http://$(curl -s ifconfig.me):3000 (admin/admin)"
    echo -e "${BLUE}Prometheus:${NC} http://$(curl -s ifconfig.me):9090"
    echo -e "${BLUE}Alertmanager:${NC} http://$(curl -s ifconfig.me):9093"
    echo
    echo -e "${GREEN}=== SERVICE MANAGEMENT ===${NC}"
    echo -e "${BLUE}Start Trading Bot:${NC} systemctl start trae.service"
    echo -e "${BLUE}Stop Trading Bot:${NC} systemctl stop trae.service"
    echo -e "${BLUE}View Logs:${NC} journalctl -u trae.service -f"
    echo -e "${BLUE}Service Status:${NC} systemctl status trae.service"
    echo
    echo -e "${GREEN}=== MONITORING ===${NC}"
    echo -e "${BLUE}Health Check:${NC} $INSTALL_DIR/scripts/health-check.sh"
    echo -e "${BLUE}System Monitor:${NC} $INSTALL_DIR/scripts/system-monitor.sh"
    echo -e "${BLUE}Backup Script:${NC} $INSTALL_DIR/scripts/backup.sh"
    echo
    echo -e "${YELLOW}⚠️  IMPORTANT NEXT STEPS:${NC}"
    echo -e "${RED}1. Update environment file: $INSTALL_DIR/.env${NC}"
    echo -e "${RED}2. Configure broker credentials${NC}"
    echo -e "${RED}3. Setup Slack/email notifications in alertmanager.yml${NC}"
    echo -e "${RED}4. Start the trading service: systemctl start trae.service${NC}"
    echo -e "${RED}5. Monitor logs and verify functionality${NC}"
    echo
    success "Deployment completed successfully! 🎉"
}

# Main deployment function
main() {
    log "🚀 Starting Trae AI Trading Sentinel Production Deployment..."
    
    check_root
    check_system
    update_system
    install_docker
    create_user
    setup_directories
    clone_repository
    setup_python
    setup_nodejs
    setup_firewall
    setup_monitoring
    setup_systemd
    setup_nginx
    setup_ssl
    setup_backup
    final_setup
    show_summary
    
    success "🎯 Production deployment completed successfully!"
}

# Execute main function
main "$@"