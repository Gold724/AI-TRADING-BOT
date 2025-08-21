#!/bin/bash

# AI Trading Sentinel - Enhanced Monitoring Deployment Script
# TRAE-SentinelOps: Production deployment for 24/7 monitoring

set -euo pipefail

# Configuration
APP_NAME="trae-sentinel"
APP_DIR="/opt/${APP_NAME}"
SERVICE_USER="${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
CONFIG_DIR="/etc/${APP_NAME}"
SYSTEMD_DIR="/etc/systemd/system"

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
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if ! command -v systemctl &> /dev/null; then
        log_error "systemd is required but not found"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not found"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not found"
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    apt-get update -qq
    
    # Install required packages
    apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        curl \
        wget \
        git \
        htop \
        iotop \
        nethogs \
        logrotate \
        supervisor \
        nginx \
        certbot \
        python3-certbot-nginx
    
    log_success "System dependencies installed"
}

# Create system user
create_user() {
    log_info "Creating system user: ${SERVICE_USER}"
    
    if ! id "${SERVICE_USER}" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir "${APP_DIR}" \
                --create-home --user-group "${SERVICE_USER}"
        log_success "User ${SERVICE_USER} created"
    else
        log_warning "User ${SERVICE_USER} already exists"
    fi
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."
    
    # Create main directories
    mkdir -p "${APP_DIR}" "${LOG_DIR}" "${DATA_DIR}" "${CONFIG_DIR}"
    mkdir -p "${APP_DIR}/logs" "${APP_DIR}/data" "${APP_DIR}/screenshots"
    mkdir -p "${DATA_DIR}/monitoring" "${DATA_DIR}/metrics" "${DATA_DIR}/alerts"
    
    # Set ownership
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "${APP_DIR}" "${LOG_DIR}" "${DATA_DIR}"
    
    # Set permissions
    chmod 755 "${APP_DIR}" "${LOG_DIR}" "${DATA_DIR}" "${CONFIG_DIR}"
    chmod 750 "${APP_DIR}/logs" "${APP_DIR}/data"
    
    log_success "Directory structure created"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    # Create virtual environment
    sudo -u "${SERVICE_USER}" python3 -m venv "${APP_DIR}/venv"
    
    # Upgrade pip
    sudo -u "${SERVICE_USER}" "${APP_DIR}/venv/bin/pip" install --upgrade pip
    
    # Install Python dependencies
    if [[ -f "${APP_DIR}/requirements.txt" ]]; then
        sudo -u "${SERVICE_USER}" "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"
    else
        # Install essential monitoring dependencies
        sudo -u "${SERVICE_USER}" "${APP_DIR}/venv/bin/pip" install \
            psutil \
            requests \
            aiohttp \
            asyncio \
            python-dotenv \
            schedule \
            matplotlib \
            seaborn \
            pandas \
            numpy
    fi
    
    log_success "Python environment setup completed"
}

# Deploy application files
deploy_application() {
    log_info "Deploying application files..."
    
    # Copy application files
    if [[ -d "./" ]]; then
        cp -r ./* "${APP_DIR}/" 2>/dev/null || true
        
        # Set ownership
        chown -R "${SERVICE_USER}:${SERVICE_USER}" "${APP_DIR}"
        
        # Make scripts executable
        find "${APP_DIR}" -name "*.py" -exec chmod +x {} \;
        find "${APP_DIR}" -name "*.sh" -exec chmod +x {} \;
    fi
    
    log_success "Application files deployed"
}

# Setup systemd services
setup_systemd_services() {
    log_info "Setting up systemd services..."
    
    # Copy service files
    if [[ -d "${APP_DIR}/systemd" ]]; then
        cp "${APP_DIR}/systemd/"*.service "${SYSTEMD_DIR}/"
        cp "${APP_DIR}/systemd/"*.timer "${SYSTEMD_DIR}/" 2>/dev/null || true
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable trae-enhanced-monitor.service
    systemctl enable trae-enhanced-monitor.timer 2>/dev/null || true
    
    # Enable other core services if they exist
    for service in trae-backend trae-trading-bot trae-health-monitor; do
        if [[ -f "${SYSTEMD_DIR}/${service}.service" ]]; then
            systemctl enable "${service}.service"
            log_info "Enabled ${service}.service"
        fi
    done
    
    log_success "Systemd services configured"
}

# Setup log rotation
setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/trae-sentinel << EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ${SERVICE_USER} ${SERVICE_USER}
    postrotate
        systemctl reload trae-enhanced-monitor.service 2>/dev/null || true
    endscript
}

${APP_DIR}/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ${SERVICE_USER} ${SERVICE_USER}
    copytruncate
}
EOF
    
    log_success "Log rotation configured"
}

# Setup monitoring dashboard (Nginx)
setup_monitoring_dashboard() {
    log_info "Setting up monitoring dashboard..."
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/trae-monitoring << EOF
server {
    listen 80;
    server_name monitoring.trae-sentinel.local;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # API proxy
    location /api/ {
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
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/api/health;
        access_log off;
    }
    
    # Static files
    location / {
        root ${APP_DIR}/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Logs location
    location /logs {
        alias ${LOG_DIR};
        autoindex on;
        auth_basic "Monitoring Logs";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/trae-monitoring /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    nginx -t && systemctl reload nginx
    
    log_success "Monitoring dashboard configured"
}

# Setup firewall
setup_firewall() {
    log_info "Configuring firewall..."
    
    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    # Configure firewall rules
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow monitoring ports (if needed)
    ufw allow 5000/tcp comment "Backend API"
    ufw allow 3000/tcp comment "Frontend Dev Server"
    
    # Enable firewall
    ufw --force enable
    
    log_success "Firewall configured"
}

# Create monitoring environment file
create_monitoring_env() {
    log_info "Creating monitoring environment configuration..."
    
    cat > "${CONFIG_DIR}/monitoring.env" << EOF
# AI Trading Sentinel - Monitoring Configuration
# Generated on $(date)

# Monitoring Settings
MONITORING_ENABLED=true
MONITORING_INTERVAL=60
HEALTH_CHECK_TIMEOUT=30
METRICS_RETENTION_DAYS=30

# Alert Settings
ALERT_COOLDOWN=1800
SLACK_WEBHOOK_URL=
EMAIL_ALERTS_ENABLED=false
SMS_ALERTS_ENABLED=false

# System Thresholds
CPU_THRESHOLD=85
MEMORY_THRESHOLD=90
DISK_THRESHOLD=95
LOAD_THRESHOLD=5.0

# Service URLs
BACKEND_URL=http://localhost:5000
FRONTEND_URL=http://localhost:3000
BULENOX_API_URL=http://localhost:5000/api/bulenox

# Logging
LOG_LEVEL=INFO
LOG_FILE=${LOG_DIR}/monitoring.log
VERBOSE_LOGGING=false
EOF
    
    # Set permissions
    chown "${SERVICE_USER}:${SERVICE_USER}" "${CONFIG_DIR}/monitoring.env"
    chmod 640 "${CONFIG_DIR}/monitoring.env"
    
    log_success "Monitoring environment configuration created"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start and enable services
    systemctl start trae-enhanced-monitor.service
    systemctl start trae-enhanced-monitor.timer 2>/dev/null || true
    
    # Start other services if they exist
    for service in trae-backend trae-trading-bot; do
        if systemctl is-enabled "${service}.service" &>/dev/null; then
            systemctl start "${service}.service"
            log_info "Started ${service}.service"
        fi
    done
    
    log_success "Services started"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check service status
    if systemctl is-active --quiet trae-enhanced-monitor.service; then
        log_success "Enhanced monitoring service is running"
    else
        log_error "Enhanced monitoring service is not running"
        systemctl status trae-enhanced-monitor.service
    fi
    
    # Check timer status
    if systemctl is-active --quiet trae-enhanced-monitor.timer; then
        log_success "Enhanced monitoring timer is active"
    else
        log_warning "Enhanced monitoring timer is not active"
    fi
    
    # Check log files
    if [[ -f "${LOG_DIR}/monitoring.log" ]]; then
        log_success "Monitoring log file exists"
    else
        log_warning "Monitoring log file not found"
    fi
    
    # Test health endpoint
    if curl -s http://localhost:5000/api/health &>/dev/null; then
        log_success "Health endpoint is responding"
    else
        log_warning "Health endpoint is not responding"
    fi
    
    log_success "Deployment verification completed"
}

# Display status
show_status() {
    echo
    log_info "=== AI Trading Sentinel - Enhanced Monitoring Status ==="
    echo
    
    # Service status
    echo "Service Status:"
    systemctl status trae-enhanced-monitor.service --no-pager -l || true
    echo
    
    # Timer status
    echo "Timer Status:"
    systemctl status trae-enhanced-monitor.timer --no-pager -l || true
    echo
    
    # Recent logs
    echo "Recent Logs:"
    journalctl -u trae-enhanced-monitor.service --no-pager -n 10 || true
    echo
    
    # System resources
    echo "System Resources:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')" 
    echo "Disk: $(df -h / | awk 'NR==2{printf "%s", $5}')"
    echo
    
    # Useful commands
    echo "Useful Commands:"
    echo "  View logs: journalctl -u trae-enhanced-monitor.service -f"
    echo "  Restart service: systemctl restart trae-enhanced-monitor.service"
    echo "  Check status: systemctl status trae-enhanced-monitor.service"
    echo "  View config: cat ${CONFIG_DIR}/monitoring.env"
    echo "  Monitor resources: htop"
    echo
}

# Main deployment function
main() {
    log_info "Starting AI Trading Sentinel Enhanced Monitoring Deployment"
    echo
    
    check_root
    check_requirements
    install_dependencies
    create_user
    create_directories
    deploy_application
    setup_python_env
    setup_systemd_services
    setup_log_rotation
    setup_monitoring_dashboard
    setup_firewall
    create_monitoring_env
    start_services
    verify_deployment
    
    echo
    log_success "Enhanced monitoring deployment completed successfully!"
    echo
    
    show_status
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_status
        ;;
    "restart")
        log_info "Restarting enhanced monitoring service..."
        systemctl restart trae-enhanced-monitor.service
        systemctl restart trae-enhanced-monitor.timer 2>/dev/null || true
        log_success "Services restarted"
        ;;
    "stop")
        log_info "Stopping enhanced monitoring service..."
        systemctl stop trae-enhanced-monitor.service
        systemctl stop trae-enhanced-monitor.timer 2>/dev/null || true
        log_success "Services stopped"
        ;;
    "logs")
        journalctl -u trae-enhanced-monitor.service -f
        ;;
    *)
        echo "Usage: $0 {deploy|status|restart|stop|logs}"
        echo "  deploy  - Deploy enhanced monitoring system"
        echo "  status  - Show system status"
        echo "  restart - Restart monitoring services"
        echo "  stop    - Stop monitoring services"
        echo "  logs    - Follow service logs"
        exit 1
        ;;
esac