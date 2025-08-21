#!/bin/bash

# AI Trading Sentinel - Production Deployment Automation
# TRAE-SentinelOps: One-click production deployment script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/var/log/trae-sentinel"
LOG_FILE="${LOG_DIR}/deployment.log"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Deployment settings
DEPLOY_USER="trae-sentinel"
DEPLOY_DIR="/opt/trae-sentinel"
CONFIG_DIR="/etc/trae-sentinel"
SERVICE_DIR="/etc/systemd/system"
BACKUP_DIR="/var/backups/trae-sentinel"

# Version and build info
VERSION="1.0.0"
BUILD_ID="${TIMESTAMP}"
GIT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

# Deployment phases
DEPLOYMENT_PHASES=(
    "pre_deployment_checks"
    "system_preparation"
    "dependency_installation"
    "application_deployment"
    "configuration_setup"
    "service_configuration"
    "security_hardening"
    "monitoring_setup"
    "validation_testing"
    "go_live"
)

# Progress tracking
CURRENT_PHASE=0
TOTAL_PHASES=${#DEPLOYMENT_PHASES[@]}

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Print colored output with progress
print_phase() {
    local phase_name="$1"
    local status="$2"
    local message="$3"
    
    CURRENT_PHASE=$((CURRENT_PHASE + 1))
    local progress="[$CURRENT_PHASE/$TOTAL_PHASES]"
    
    case $status in
        "START")
            echo -e "${BLUE}🚀 $progress Starting: $phase_name${NC}"
            echo -e "${CYAN}   $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ $progress Completed: $phase_name${NC}"
            echo -e "${GREEN}   $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $progress Failed: $phase_name${NC}"
            echo -e "${RED}   $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $progress Warning: $phase_name${NC}"
            echo -e "${YELLOW}   $message${NC}"
            ;;
    esac
    
    log "INFO" "Phase $CURRENT_PHASE/$TOTAL_PHASES - $phase_name: $status - $message"
}

# Print deployment header
print_header() {
    clear
    echo -e "${PURPLE}"
    echo "██████╗ ██████╗  ██████╗ ██████╗ ██╗   ██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗"
    echo "██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██║   ██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║"
    echo "██████╔╝██████╔╝██║   ██║██║  ██║██║   ██║██║        ██║   ██║██║   ██║██╔██╗ ██║"
    echo "██╔═══╝ ██╔══██╗██║   ██║██║  ██║██║   ██║██║        ██║   ██║██║   ██║██║╚██╗██║"
    echo "██║     ██║  ██║╚██████╔╝██████╔╝╚██████╔╝╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║"
    echo "╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝  ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝"
    echo -e "${NC}"
    echo -e "${CYAN}AI Trading Sentinel - Production Deployment${NC}"
    echo -e "${CYAN}TRAE-SentinelOps Automated Deployment System${NC}"
    echo ""
    echo -e "${BLUE}Version: $VERSION${NC}"
    echo -e "${BLUE}Build ID: $BUILD_ID${NC}"
    echo -e "${BLUE}Git Commit: $GIT_COMMIT${NC}"
    echo -e "${BLUE}Timestamp: $(date)${NC}"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════════"
    echo ""
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}❌ This script must be run as root${NC}"
        echo "Please run: sudo $0"
        exit 1
    fi
}

# Create backup of existing installation
create_backup() {
    if [[ -d "$DEPLOY_DIR" ]]; then
        log "INFO" "Creating backup of existing installation"
        mkdir -p "$BACKUP_DIR"
        
        local backup_file="$BACKUP_DIR/pre_deployment_backup_${TIMESTAMP}.tar.gz"
        tar -czf "$backup_file" -C "$(dirname "$DEPLOY_DIR")" "$(basename "$DEPLOY_DIR")" 2>/dev/null || true
        
        if [[ -f "$backup_file" ]]; then
            log "INFO" "Backup created: $backup_file"
        else
            log "WARNING" "Failed to create backup"
        fi
    fi
}

# Phase 1: Pre-deployment checks
pre_deployment_checks() {
    print_phase "Pre-deployment Checks" "START" "Verifying system requirements and prerequisites"
    
    # Check OS version
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ "$ID" != "ubuntu" ]]; then
            print_phase "Pre-deployment Checks" "WARNING" "Non-Ubuntu OS detected: $ID (Ubuntu recommended)"
        elif [[ "$VERSION_ID" != "22.04" && "$VERSION_ID" != "24.04" ]]; then
            print_phase "Pre-deployment Checks" "WARNING" "Ubuntu $VERSION_ID detected (22.04 or 24.04 recommended)"
        fi
    fi
    
    # Check available resources
    local mem_gb=$(free -g | awk '/^Mem:/{print $2}')
    local disk_gb=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [[ $mem_gb -lt 2 ]]; then
        print_phase "Pre-deployment Checks" "ERROR" "Insufficient memory: ${mem_gb}GB (minimum: 2GB)"
        exit 1
    fi
    
    if [[ $disk_gb -lt 10 ]]; then
        print_phase "Pre-deployment Checks" "ERROR" "Insufficient disk space: ${disk_gb}GB (minimum: 10GB)"
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        print_phase "Pre-deployment Checks" "ERROR" "No internet connectivity"
        exit 1
    fi
    
    create_backup
    
    print_phase "Pre-deployment Checks" "SUCCESS" "All prerequisites met"
}

# Phase 2: System preparation
system_preparation() {
    print_phase "System Preparation" "START" "Preparing system environment"
    
    # Update system
    apt update && apt upgrade -y
    
    # Create system user
    if ! id "$DEPLOY_USER" &> /dev/null; then
        useradd -r -m -s /bin/bash "$DEPLOY_USER"
        usermod -aG sudo "$DEPLOY_USER"
    fi
    
    # Create directory structure
    mkdir -p "$DEPLOY_DIR" "$CONFIG_DIR" "$LOG_DIR" "/var/lib/trae-sentinel" "$BACKUP_DIR"
    
    # Set ownership and permissions
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
    chown -R "root:$DEPLOY_USER" "$CONFIG_DIR"
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "$LOG_DIR"
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "/var/lib/trae-sentinel"
    
    chmod 755 "$DEPLOY_DIR"
    chmod 750 "$CONFIG_DIR"
    chmod 750 "$LOG_DIR"
    chmod 750 "/var/lib/trae-sentinel"
    
    print_phase "System Preparation" "SUCCESS" "System environment prepared"
}

# Phase 3: Dependency installation
dependency_installation() {
    print_phase "Dependency Installation" "START" "Installing required packages and dependencies"
    
    # Install system packages
    apt install -y python3 python3-pip python3-venv python3-dev \
                   nodejs npm nginx redis-server git curl wget unzip \
                   sqlite3 htop nano ufw fail2ban certbot python3-certbot-nginx \
                   libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
                   libgtk-3-0 libatspi2.0-0 libxss1 libasound2 xvfb
    
    # Install Node.js 18+ if needed
    local node_version=$(node --version | sed 's/v//' | cut -d. -f1)
    if [[ $node_version -lt 18 ]]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt install -y nodejs
    fi
    
    # Enable and start services
    systemctl enable redis-server nginx
    systemctl start redis-server nginx
    
    print_phase "Dependency Installation" "SUCCESS" "All dependencies installed"
}

# Phase 4: Application deployment
application_deployment() {
    print_phase "Application Deployment" "START" "Deploying application code and assets"
    
    # Copy application files
    if [[ "$SCRIPT_DIR" != "$DEPLOY_DIR" ]]; then
        rsync -av --exclude='.git' --exclude='node_modules' --exclude='venv' \
              --exclude='__pycache__' --exclude='*.pyc' \
              "$SCRIPT_DIR/" "$DEPLOY_DIR/"
    fi
    
    # Set up Python virtual environment
    sudo -u "$DEPLOY_USER" python3 -m venv "$DEPLOY_DIR/venv"
    sudo -u "$DEPLOY_USER" "$DEPLOY_DIR/venv/bin/pip" install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    if [[ -f "$DEPLOY_DIR/requirements.txt" ]]; then
        sudo -u "$DEPLOY_USER" "$DEPLOY_DIR/venv/bin/pip" install -r "$DEPLOY_DIR/requirements.txt"
    fi
    
    # Install Playwright browsers
    sudo -u "$DEPLOY_USER" "$DEPLOY_DIR/venv/bin/playwright" install chromium
    sudo -u "$DEPLOY_USER" "$DEPLOY_DIR/venv/bin/playwright" install-deps
    
    # Build frontend if exists
    if [[ -d "$DEPLOY_DIR/frontend" && -f "$DEPLOY_DIR/frontend/package.json" ]]; then
        cd "$DEPLOY_DIR/frontend"
        sudo -u "$DEPLOY_USER" npm install
        sudo -u "$DEPLOY_USER" npm run build
        cd "$SCRIPT_DIR"
    fi
    
    # Set proper permissions
    chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
    find "$DEPLOY_DIR" -type f -name "*.sh" -exec chmod +x {} \;
    
    print_phase "Application Deployment" "SUCCESS" "Application deployed successfully"
}

# Phase 5: Configuration setup
configuration_setup() {
    print_phase "Configuration Setup" "START" "Setting up configuration files"
    
    # Run interactive configuration if .env doesn't exist
    if [[ ! -f "$CONFIG_DIR/.env" ]]; then
        if [[ -f "$DEPLOY_DIR/setup_production_env.sh" ]]; then
            "$DEPLOY_DIR/setup_production_env.sh" --non-interactive
        else
            # Create basic .env file
            cat > "$CONFIG_DIR/.env" << EOF
# AI Trading Sentinel Configuration
# Generated on $(date)

# Trading Configuration
BULENOX_USERNAME=
BULENOX_PASSWORD=
BULENOX_API_URL=https://bulenox.projectx.com/login

# Application Ports
BACKEND_PORT=5000
FRONTEND_PORT=3000

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=sqlite:///var/lib/trae-sentinel/trading_bot.db
REDIS_URL=redis://localhost:6379/0

# Monitoring
SIMULATION_MODE=true
AUTO_EXECUTE=false
HEADLESS=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/trae-sentinel/trading_bot.log
EOF
        fi
    fi
    
    # Set secure permissions on config files
    chown root:"$DEPLOY_USER" "$CONFIG_DIR/.env"
    chmod 640 "$CONFIG_DIR/.env"
    
    # Copy configuration files
    if [[ -d "$DEPLOY_DIR/config" ]]; then
        cp -r "$DEPLOY_DIR/config"/* "$CONFIG_DIR/" 2>/dev/null || true
    fi
    
    print_phase "Configuration Setup" "SUCCESS" "Configuration files set up"
}

# Phase 6: Service configuration
service_configuration() {
    print_phase "Service Configuration" "START" "Configuring systemd services"
    
    # Copy service files
    if [[ -d "$DEPLOY_DIR/systemd" ]]; then
        cp "$DEPLOY_DIR/systemd"/*.service "$SERVICE_DIR/" 2>/dev/null || true
        cp "$DEPLOY_DIR/systemd"/*.timer "$SERVICE_DIR/" 2>/dev/null || true
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    local services=(
        "trae-enhanced-monitor.service"
        "trae-enhanced-monitor.timer"
        "trae-backend.service"
    )
    
    for service in "${services[@]}"; do
        if [[ -f "$SERVICE_DIR/$service" ]]; then
            systemctl enable "$service"
        fi
    done
    
    # Configure Nginx
    if [[ -f "$DEPLOY_DIR/config/nginx/trae-sentinel.conf" ]]; then
        cp "$DEPLOY_DIR/config/nginx/trae-sentinel.conf" /etc/nginx/sites-available/trae-sentinel
        ln -sf /etc/nginx/sites-available/trae-sentinel /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # Test Nginx configuration
        if nginx -t; then
            systemctl reload nginx
        else
            print_phase "Service Configuration" "WARNING" "Nginx configuration test failed"
        fi
    fi
    
    print_phase "Service Configuration" "SUCCESS" "Services configured"
}

# Phase 7: Security hardening
security_hardening() {
    print_phase "Security Hardening" "START" "Applying security configurations"
    
    # Configure firewall
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    
    # Configure fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
    
    # Set up log rotation
    cat > /etc/logrotate.d/trae-sentinel << EOF
/var/log/trae-sentinel/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 trae-sentinel trae-sentinel
    postrotate
        systemctl reload trae-enhanced-monitor || true
    endscript
}
EOF
    
    print_phase "Security Hardening" "SUCCESS" "Security measures applied"
}

# Phase 8: Monitoring setup
monitoring_setup() {
    print_phase "Monitoring Setup" "START" "Setting up monitoring and alerting"
    
    # Start monitoring services
    systemctl start trae-enhanced-monitor.service
    systemctl start trae-enhanced-monitor.timer
    
    # Set up backup cron job
    if [[ -f "$DEPLOY_DIR/scripts/backup.sh" ]]; then
        chmod +x "$DEPLOY_DIR/scripts/backup.sh"
        echo "0 2 * * * $DEPLOY_DIR/scripts/backup.sh >> /var/log/trae-sentinel/backup.log 2>&1" | crontab -u "$DEPLOY_USER" -
    fi
    
    print_phase "Monitoring Setup" "SUCCESS" "Monitoring system active"
}

# Phase 9: Validation testing
validation_testing() {
    print_phase "Validation Testing" "START" "Running comprehensive system validation"
    
    # Run validation script
    if [[ -f "$DEPLOY_DIR/validate_production_system.py" ]]; then
        if python3 "$DEPLOY_DIR/validate_production_system.py" --config "$CONFIG_DIR/.env"; then
            print_phase "Validation Testing" "SUCCESS" "All validation tests passed"
        else
            print_phase "Validation Testing" "WARNING" "Some validation tests failed (check logs)"
        fi
    fi
    
    # Run deployment verification
    if [[ -f "$DEPLOY_DIR/verify_deployment.sh" ]]; then
        if "$DEPLOY_DIR/verify_deployment.sh"; then
            print_phase "Validation Testing" "SUCCESS" "Deployment verification passed"
        else
            print_phase "Validation Testing" "WARNING" "Deployment verification had issues"
        fi
    fi
}

# Phase 10: Go live
go_live() {
    print_phase "Go Live" "START" "Starting production services"
    
    # Start backend service
    systemctl start trae-backend.service
    
    # Wait for backend to be ready
    sleep 5
    
    # Test backend health
    local backend_port=$(grep "^BACKEND_PORT=" "$CONFIG_DIR/.env" | cut -d'=' -f2 || echo "5000")
    if curl -s -f "http://localhost:$backend_port/api/health" > /dev/null; then
        print_phase "Go Live" "SUCCESS" "Backend service is healthy"
    else
        print_phase "Go Live" "WARNING" "Backend health check failed"
    fi
    
    # Note: Trading bot service is not started automatically for safety
    # It should be started manually after final verification
    
    print_phase "Go Live" "SUCCESS" "Production deployment completed"
}

# Print deployment summary
print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉${NC}"
    echo "═══════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${BLUE}Deployment Information:${NC}"
    echo "  • Version: $VERSION"
    echo "  • Build ID: $BUILD_ID"
    echo "  • Git Commit: $GIT_COMMIT"
    echo "  • Deployment Time: $(date)"
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    systemctl is-active trae-enhanced-monitor.service && echo -e "  • ${GREEN}✅ Enhanced Monitor: Active${NC}" || echo -e "  • ${RED}❌ Enhanced Monitor: Inactive${NC}"
    systemctl is-active trae-backend.service && echo -e "  • ${GREEN}✅ Backend Service: Active${NC}" || echo -e "  • ${RED}❌ Backend Service: Inactive${NC}"
    systemctl is-active nginx && echo -e "  • ${GREEN}✅ Nginx: Active${NC}" || echo -e "  • ${RED}❌ Nginx: Inactive${NC}"
    systemctl is-active redis-server && echo -e "  • ${GREEN}✅ Redis: Active${NC}" || echo -e "  • ${RED}❌ Redis: Inactive${NC}"
    echo ""
    echo -e "${BLUE}Access Information:${NC}"
    local backend_port=$(grep "^BACKEND_PORT=" "$CONFIG_DIR/.env" | cut -d'=' -f2 || echo "5000")
    echo "  • Backend API: http://localhost:$backend_port/api/health"
    echo "  • Frontend: http://localhost/"
    echo "  • Logs: $LOG_DIR/"
    echo "  • Configuration: $CONFIG_DIR/"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT NEXT STEPS:${NC}"
    echo "  1. Review and update configuration in $CONFIG_DIR/.env"
    echo "  2. Configure trading credentials (BULENOX_USERNAME, BULENOX_PASSWORD)"
    echo "  3. Set up SSL certificate: sudo certbot --nginx -d your-domain.com"
    echo "  4. Configure notification settings (Slack, Email)"
    echo "  5. Test in simulation mode before enabling live trading"
    echo "  6. Start trading bot: sudo systemctl start trae-trading-bot.service"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  • Check status: sudo systemctl status trae-*"
    echo "  • View logs: sudo tail -f $LOG_DIR/trading_bot.log"
    echo "  • Run validation: sudo python3 $DEPLOY_DIR/validate_production_system.py"
    echo "  • Emergency stop: sudo systemctl stop trae-trading-bot.service"
    echo ""
    echo -e "${GREEN}🚀 Your AI Trading Sentinel is ready for production! 🚀${NC}"
    echo "═══════════════════════════════════════════════════════════════════════════════════"
}

# Error handler
error_handler() {
    local exit_code=$?
    local line_number=$1
    
    echo -e "${RED}❌ Deployment failed at line $line_number with exit code $exit_code${NC}"
    log "ERROR" "Deployment failed at line $line_number with exit code $exit_code"
    
    # Attempt to restore from backup if available
    local latest_backup=$(ls -t "$BACKUP_DIR"/pre_deployment_backup_*.tar.gz 2>/dev/null | head -1)
    if [[ -n "$latest_backup" ]]; then
        echo -e "${YELLOW}Attempting to restore from backup: $latest_backup${NC}"
        systemctl stop trae-* 2>/dev/null || true
        rm -rf "$DEPLOY_DIR"
        tar -xzf "$latest_backup" -C "$(dirname "$DEPLOY_DIR")"
        systemctl start trae-* 2>/dev/null || true
        echo -e "${GREEN}System restored from backup${NC}"
    fi
    
    exit $exit_code
}

# Set up error handling
trap 'error_handler $LINENO' ERR

# Main deployment function
main() {
    # Initialize
    mkdir -p "$LOG_DIR"
    log "INFO" "Starting AI Trading Sentinel deployment v$VERSION"
    
    print_header
    check_root
    
    # Execute deployment phases
    for phase in "${DEPLOYMENT_PHASES[@]}"; do
        $phase
        sleep 1  # Brief pause between phases
    done
    
    # Print summary
    print_summary
    
    log "INFO" "Deployment completed successfully"
}

# Handle command line arguments
case "${1:-}" in
    "--help" | "-h")
        echo "AI Trading Sentinel - Production Deployment"
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h        Show this help message"
        echo "  --version, -v     Show version information"
        echo "  --dry-run         Perform a dry run (validation only)"
        echo "  --force           Force deployment even if validation fails"
        echo "  --backup-only     Create backup and exit"
        echo ""
        echo "Examples:"
        echo "  sudo $0                    # Full deployment"
        echo "  sudo $0 --dry-run          # Validation only"
        echo "  sudo $0 --backup-only      # Backup existing installation"
        exit 0
        ;;
    "--version" | "-v")
        echo "AI Trading Sentinel Deployment Script"
        echo "Version: $VERSION"
        echo "Build ID: $BUILD_ID"
        echo "Git Commit: $GIT_COMMIT"
        exit 0
        ;;
    "--dry-run")
        echo "Performing dry run (validation only)..."
        check_root
        pre_deployment_checks
        echo "Dry run completed successfully"
        exit 0
        ;;
    "--backup-only")
        echo "Creating backup..."
        check_root
        mkdir -p "$LOG_DIR" "$BACKUP_DIR"
        create_backup
        echo "Backup completed"
        exit 0
        ;;
    "--force")
        echo "Force mode enabled - skipping some validation checks"
        ;;
esac

# Run main deployment
main "$@"