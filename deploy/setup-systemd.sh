#!/bin/bash
# AI Trading Sentinel - SystemD Service Setup Script
# Configure production systemd services for 24/7 operation
# Usage: ./setup-systemd.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_USER="trae"
INSTALL_DIR="/opt/trae-sentinel"
SERVICE_DIR="/etc/systemd/system"
LOG_DIR="/var/log/trae-sentinel"
DATA_DIR="/var/lib/trae-sentinel"

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

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root. Use: sudo ./setup-systemd.sh"
    fi
}

create_user() {
    log "Creating service user: $SERVICE_USER"
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir "$INSTALL_DIR" \
                --create-home --comment "Trae Trading Bot" "$SERVICE_USER"
        log "✓ User $SERVICE_USER created"
    else
        log "✓ User $SERVICE_USER already exists"
    fi
}

setup_directories() {
    log "Setting up directories..."
    
    # Create required directories
    mkdir -p "$INSTALL_DIR"/{data,logs,scripts,config}
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p /var/run/trae-sentinel
    
    # Set ownership and permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" /var/run/trae-sentinel
    
    # Set secure permissions
    chmod 755 "$INSTALL_DIR"
    chmod 750 "$LOG_DIR"
    chmod 750 "$DATA_DIR"
    chmod 755 /var/run/trae-sentinel
    
    log "✓ Directories configured"
}

install_services() {
    log "Installing systemd services..."
    
    # Copy service files
    if [[ -f "../trae.service" ]]; then
        cp ../trae.service "$SERVICE_DIR/trae.service"
        log "✓ Main service installed"
    else
        error "trae.service file not found"
    fi
    
    if [[ -f "../systemd/trae-sentinel-monitor.service" ]]; then
        cp ../systemd/trae-sentinel-monitor.service "$SERVICE_DIR/"
        log "✓ Monitor service installed"
    else
        error "trae-sentinel-monitor.service file not found"
    fi
    
    if [[ -f "../systemd/trae-sentinel-monitor.timer" ]]; then
        cp ../systemd/trae-sentinel-monitor.timer "$SERVICE_DIR/"
        log "✓ Monitor timer installed"
    else
        error "trae-sentinel-monitor.timer file not found"
    fi
    
    # Copy health check script
    if [[ -f "../scripts/health-check.sh" ]]; then
        cp ../scripts/health-check.sh "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/health-check.sh"
        chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/scripts/health-check.sh"
        log "✓ Health check script installed"
    else
        error "health-check.sh script not found"
    fi
}

setup_logrotate() {
    log "Configuring log rotation..."
    
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
    
    log "✓ Log rotation configured"
}

setup_environment() {
    log "Setting up environment file..."
    
    if [[ ! -f "$INSTALL_DIR/.env" ]]; then
        cat > "$INSTALL_DIR/.env" << 'EOF'
# Trae AI Trading Sentinel - Production Environment
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

# Environment
TRAE_ENV=production
TRAE_LOG_LEVEL=INFO
TRAE_DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_WORKERS=2

# Database
DATABASE_URL=sqlite:///var/lib/trae-sentinel/trading.db

# Redis (if used)
REDIS_URL=redis://localhost:6379/0

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=120

# Trading Configuration
MAX_POSITION_SIZE=1000
RISK_LIMIT=0.02
STOP_LOSS_PERCENT=0.01

# Broker Credentials (SECURE THESE!)
# BROKER_USERNAME=
# BROKER_PASSWORD=
# BROKER_API_KEY=

# Notifications
# SLACK_WEBHOOK_URL=
# EMAIL_SMTP_SERVER=
# EMAIL_USERNAME=
# EMAIL_PASSWORD=
EOF
        
        chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
        chmod 600 "$INSTALL_DIR/.env"
        
        warn "Environment file created at $INSTALL_DIR/.env"
        warn "Please update it with your actual credentials before starting the service"
    else
        log "✓ Environment file already exists"
    fi
}

enable_services() {
    log "Enabling and starting services..."
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable trae.service
    systemctl enable trae-sentinel-monitor.timer
    
    log "✓ Services enabled"
    log "Services are ready but not started. Use the following commands:"
    echo -e "${BLUE}  Start main service:    systemctl start trae.service${NC}"
    echo -e "${BLUE}  Start health monitor:  systemctl start trae-sentinel-monitor.timer${NC}"
    echo -e "${BLUE}  Check status:          systemctl status trae.service${NC}"
    echo -e "${BLUE}  View logs:             journalctl -u trae.service -f${NC}"
}

install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        wget \
        git \
        bc \
        logrotate \
        systemd
    
    log "✓ Dependencies installed"
}

show_status() {
    log "SystemD Service Setup Complete!"
    echo
    echo -e "${GREEN}Next Steps:${NC}"
    echo -e "${BLUE}1. Update environment file: $INSTALL_DIR/.env${NC}"
    echo -e "${BLUE}2. Deploy your application code to: $INSTALL_DIR${NC}"
    echo -e "${BLUE}3. Install Python dependencies in virtual environment${NC}"
    echo -e "${BLUE}4. Start the services:${NC}"
    echo -e "   ${YELLOW}sudo systemctl start trae.service${NC}"
    echo -e "   ${YELLOW}sudo systemctl start trae-sentinel-monitor.timer${NC}"
    echo
    echo -e "${GREEN}Service Management Commands:${NC}"
    echo -e "${BLUE}  Status:   systemctl status trae.service${NC}"
    echo -e "${BLUE}  Logs:     journalctl -u trae.service -f${NC}"
    echo -e "${BLUE}  Restart:  systemctl restart trae.service${NC}"
    echo -e "${BLUE}  Stop:     systemctl stop trae.service${NC}"
    echo
    echo -e "${GREEN}Health Monitor:${NC}"
    echo -e "${BLUE}  Status:   systemctl status trae-sentinel-monitor.timer${NC}"
    echo -e "${BLUE}  Logs:     journalctl -u trae-sentinel-monitor.service -f${NC}"
    echo -e "${BLUE}  Manual:   /opt/trae-sentinel/scripts/health-check.sh${NC}"
}

# Main execution
main() {
    log "Starting Trae AI Trading Sentinel SystemD Setup..."
    
    check_root
    install_dependencies
    create_user
    setup_directories
    install_services
    setup_logrotate
    setup_environment
    enable_services
    show_status
    
    log "Setup completed successfully!"
}

# Run main function
main "$@"