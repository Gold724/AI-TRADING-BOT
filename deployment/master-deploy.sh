#!/bin/bash

# TradeBot Sentinel - Master Deployment Script
# Orchestrates the complete deployment process for production infrastructure

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/tradebot-master-deploy-$(date +%Y%m%d-%H%M%S).log"
DEPLOY_USER="tradebot"
DEPLOY_DIR="/opt/tradebot-sentinel"
BACKUP_DIR="/opt/tradebot-backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Deployment phases
PHASE_PREP="PREPARATION"
PHASE_SECURITY="SECURITY"
PHASE_DEPS="DEPENDENCIES"
PHASE_APP="APPLICATION"
PHASE_SERVICES="SERVICES"
PHASE_WEB="FRONTEND"
PHASE_VERIFY="VERIFICATION"
PHASE_MONITOR="MONITORING"

# Current phase tracking
CURRENT_PHASE=""
START_TIME=$(date +%s)
PHASE_START_TIME=0

# Deployment options
SKIP_SECURITY=false
SKIP_DEPS=false
FORCE_REINSTALL=false
DRY_RUN=false
VERBOSE=false
QUIET=false
ENVIRONMENT="production"
DEPLOY_TARGET="systemd"  # systemd, docker, kubernetes

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_phase() {
    local phase="$1"
    local message="${2:-}"
    CURRENT_PHASE="$phase"
    PHASE_START_TIME=$(date +%s)
    
    echo "" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}========================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}PHASE: $phase${NC}" | tee -a "$LOG_FILE"
    if [ -n "$message" ]; then
        echo -e "${PURPLE}$message${NC}" | tee -a "$LOG_FILE"
    fi
    echo -e "${PURPLE}========================================${NC}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

log_info() {
    [ "$QUIET" = true ] && return 0
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

log_debug() {
    [ "$VERBOSE" = true ] || return 0
    echo -e "${CYAN}[DEBUG]${NC} $*" | tee -a "$LOG_FILE"
}

# Progress tracking
show_progress() {
    local current="$1"
    local total="$2"
    local description="$3"
    local percent=$((current * 100 / total))
    local bar_length=50
    local filled_length=$((percent * bar_length / 100))
    
    printf "\r${BLUE}[%3d%%]${NC} [" "$percent"
    printf "%*s" "$filled_length" | tr ' ' '█'
    printf "%*s" "$((bar_length - filled_length))" | tr ' ' '░'
    printf "] %s" "$description"
    
    if [ "$current" -eq "$total" ]; then
        echo ""
    fi
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log_error "Deployment failed at line $line_number with exit code $exit_code"
    log_error "Current phase: $CURRENT_PHASE"
    log_error "Check log file: $LOG_FILE"
    
    # Attempt rollback if we're past the preparation phase
    if [ "$CURRENT_PHASE" != "$PHASE_PREP" ] && [ "$DRY_RUN" = false ]; then
        log_warning "Attempting automatic rollback..."
        rollback_deployment || log_error "Rollback failed - manual intervention required"
    fi
    
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Rollback function
rollback_deployment() {
    log_warning "Starting deployment rollback..."
    
    # Stop services
    if systemctl is-active --quiet tradebot-sentinel 2>/dev/null; then
        sudo systemctl stop tradebot-sentinel || true
    fi
    
    if systemctl is-active --quiet tradebot-health-monitor 2>/dev/null; then
        sudo systemctl stop tradebot-health-monitor || true
    fi
    
    # Restore from backup if available
    local latest_backup=$(ls -t "$BACKUP_DIR"/tradebot-sentinel-backup-*.tar.gz 2>/dev/null | head -1 || echo "")
    
    if [ -n "$latest_backup" ] && [ -f "$latest_backup" ]; then
        log_info "Restoring from backup: $latest_backup"
        
        # Remove current deployment
        sudo rm -rf "${DEPLOY_DIR}.failed" || true
        sudo mv "$DEPLOY_DIR" "${DEPLOY_DIR}.failed" || true
        
        # Restore backup
        sudo mkdir -p "$DEPLOY_DIR"
        sudo tar -xzf "$latest_backup" -C "$DEPLOY_DIR" --strip-components=1
        sudo chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
        
        # Restart services
        sudo systemctl start tradebot-sentinel || true
        
        log_success "Rollback completed successfully"
    else
        log_warning "No backup available for rollback"
    fi
}

# Pre-deployment checks
check_prerequisites() {
    log_phase "$PHASE_PREP" "Checking prerequisites and system requirements"
    
    local checks=0
    local total_checks=8
    
    # Check if running as root
    show_progress $((++checks)) $total_checks "Checking user permissions"
    if [ "$EUID" -eq 0 ]; then
        log_error "This script should not be run as root"
        exit 1
    fi
    
    # Check sudo access
    show_progress $((++checks)) $total_checks "Verifying sudo access"
    if ! sudo -n true 2>/dev/null; then
        log_error "Sudo access required. Please run 'sudo -v' first"
        exit 1
    fi
    
    # Check OS compatibility
    show_progress $((++checks)) $total_checks "Checking OS compatibility"
    if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
        log_warning "This script is optimized for Ubuntu. Proceed with caution."
    fi
    
    # Check available disk space
    show_progress $((++checks)) $total_checks "Checking disk space"
    local available_space=$(df / | tail -1 | awk '{print $4}')
    local required_space=5242880  # 5GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_error "Insufficient disk space. Required: 5GB, Available: $((available_space / 1024 / 1024))GB"
        exit 1
    fi
    
    # Check memory
    show_progress $((++checks)) $total_checks "Checking memory"
    local total_memory=$(free -m | awk 'NR==2{print $2}')
    if [ "$total_memory" -lt 3072 ]; then  # 3GB minimum
        log_warning "Low memory detected: ${total_memory}MB. Minimum recommended: 3GB"
    fi
    
    # Check network connectivity
    show_progress $((++checks)) $total_checks "Testing network connectivity"
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        log_error "No internet connectivity detected"
        exit 1
    fi
    
    # Check if deployment directory exists
    show_progress $((++checks)) $total_checks "Checking deployment directory"
    if [ -d "$DEPLOY_DIR" ] && [ "$FORCE_REINSTALL" = false ]; then
        log_warning "Deployment directory already exists: $DEPLOY_DIR"
        log_info "Use --force to reinstall or --upgrade for upgrade deployment"
    fi
    
    # Check project files
    show_progress $((++checks)) $total_checks "Verifying project files"
    local required_files=(
        "requirements.txt"
        "src/main.py"
        "deployment/deploy-automation.sh"
        "deployment/security-hardening.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            log_error "Required file missing: $file"
            exit 1
        fi
    done
    
    log_success "All prerequisites checks passed"
}

# Create backup
create_backup() {
    if [ ! -d "$DEPLOY_DIR" ]; then
        log_debug "No existing deployment to backup"
        return 0
    fi
    
    log_info "Creating backup of existing deployment..."
    
    sudo mkdir -p "$BACKUP_DIR"
    local backup_file="$BACKUP_DIR/tradebot-sentinel-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    sudo tar -czf "$backup_file" -C "$(dirname "$DEPLOY_DIR")" "$(basename "$DEPLOY_DIR")"
    sudo chown "$USER:$USER" "$backup_file"
    
    log_success "Backup created: $backup_file"
    
    # Keep only last 5 backups
    local backup_count=$(ls -1 "$BACKUP_DIR"/tradebot-sentinel-backup-*.tar.gz 2>/dev/null | wc -l)
    if [ "$backup_count" -gt 5 ]; then
        ls -t "$BACKUP_DIR"/tradebot-sentinel-backup-*.tar.gz | tail -n +6 | xargs sudo rm -f
        log_info "Cleaned up old backups (keeping last 5)"
    fi
}

# Security hardening
setup_security() {
    if [ "$SKIP_SECURITY" = true ]; then
        log_info "Skipping security setup (--skip-security flag)"
        return 0
    fi
    
    log_phase "$PHASE_SECURITY" "Setting up security hardening"
    
    if [ ! -f "$SCRIPT_DIR/security-hardening.sh" ]; then
        log_error "Security hardening script not found"
        exit 1
    fi
    
    log_info "Running security hardening script..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would run: sudo $SCRIPT_DIR/security-hardening.sh"
    else
        sudo "$SCRIPT_DIR/security-hardening.sh" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    log_success "Security hardening completed"
}

# Install system dependencies
install_dependencies() {
    if [ "$SKIP_DEPS" = true ]; then
        log_info "Skipping dependency installation (--skip-deps flag)"
        return 0
    fi
    
    log_phase "$PHASE_DEPS" "Installing system dependencies"
    
    local packages=(
        "python3" "python3-pip" "python3-venv" "python3-dev"
        "nodejs" "npm"
        "postgresql" "postgresql-contrib" "redis-server"
        "nginx" "supervisor"
        "git" "curl" "wget" "unzip"
        "build-essential" "libssl-dev" "libffi-dev"
        "chromium-browser" "chromium-chromedriver"
        "htop" "iotop" "nethogs" "ncdu"
    )
    
    log_info "Updating package lists..."
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would run: sudo apt update"
    else
        sudo apt update 2>&1 | tee -a "$LOG_FILE"
    fi
    
    log_info "Installing system packages..."
    for i in "${!packages[@]}"; do
        local package="${packages[$i]}"
        show_progress $((i + 1)) ${#packages[@]} "Installing $package"
        
        if [ "$DRY_RUN" = true ]; then
            log_debug "[DRY RUN] Would install: $package"
        else
            sudo apt install -y "$package" >> "$LOG_FILE" 2>&1
        fi
    done
    
    log_success "System dependencies installed"
}

# Deploy application
deploy_application() {
    log_phase "$PHASE_APP" "Deploying TradeBot Sentinel application"
    
    # Create deployment user if not exists
    if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
        log_info "Creating deployment user: $DEPLOY_USER"
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY RUN] Would create user: $DEPLOY_USER"
        else
            sudo useradd -m -s /bin/bash "$DEPLOY_USER"
            sudo usermod -aG sudo "$DEPLOY_USER"
        fi
    fi
    
    # Create deployment directory
    log_info "Setting up deployment directory: $DEPLOY_DIR"
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would create directory: $DEPLOY_DIR"
    else
        sudo mkdir -p "$DEPLOY_DIR"
        sudo chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
    fi
    
    # Copy application files
    log_info "Copying application files..."
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would copy files from $PROJECT_ROOT to $DEPLOY_DIR"
    else
        sudo cp -r "$PROJECT_ROOT"/* "$DEPLOY_DIR/"
        sudo chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
    fi
    
    # Setup Python virtual environment
    log_info "Setting up Python virtual environment..."
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would setup Python venv in $DEPLOY_DIR"
    else
        sudo -u "$DEPLOY_USER" python3 -m venv "$DEPLOY_DIR/venv"
        sudo -u "$DEPLOY_USER" "$DEPLOY_DIR/venv/bin/pip" install --upgrade pip
        sudo -u "$DEPLOY_USER" "$DEPLOY_DIR/venv/bin/pip" install -r "$DEPLOY_DIR/requirements.txt"
        sudo -u "$DEPLOY_USER" "$DEPLOY_DIR/venv/bin/playwright" install chromium
    fi
    
    # Setup environment file
    log_info "Configuring environment..."
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would setup .env file"
    else
        if [ -f "$DEPLOY_DIR/.env.production" ]; then
            sudo cp "$DEPLOY_DIR/.env.production" "$DEPLOY_DIR/.env"
        elif [ -f "$DEPLOY_DIR/.env.example" ]; then
            sudo cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
            log_warning "Using example environment file. Please configure production settings."
        fi
        
        sudo chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR/.env"
        sudo chmod 600 "$DEPLOY_DIR/.env"
    fi
    
    log_success "Application deployment completed"
}

# Setup services
setup_services() {
    log_phase "$PHASE_SERVICES" "Setting up system services"
    
    case "$DEPLOY_TARGET" in
        "systemd")
            setup_systemd_services
            ;;
        "docker")
            setup_docker_services
            ;;
        "kubernetes")
            setup_kubernetes_services
            ;;
        *)
            log_error "Unknown deployment target: $DEPLOY_TARGET"
            exit 1
            ;;
    esac
    
    log_success "Services setup completed"
}

# Setup SystemD services
setup_systemd_services() {
    log_info "Setting up SystemD services..."
    
    local service_files=(
        "tradebot-sentinel.service"
        "tradebot-health-monitor.service"
    )
    
    for service_file in "${service_files[@]}"; do
        if [ -f "$DEPLOY_DIR/deployment/systemd/$service_file" ]; then
            log_info "Installing service: $service_file"
            if [ "$DRY_RUN" = true ]; then
                log_info "[DRY RUN] Would install: $service_file"
            else
                sudo cp "$DEPLOY_DIR/deployment/systemd/$service_file" "/etc/systemd/system/"
                sudo systemctl daemon-reload
                sudo systemctl enable "${service_file}"
            fi
        fi
    done
    
    # Start services
    if [ "$DRY_RUN" = false ]; then
        log_info "Starting TradeBot services..."
        sudo systemctl start tradebot-sentinel
        sudo systemctl start tradebot-health-monitor
        
        # Wait for services to start
        sleep 5
        
        # Check service status
        if sudo systemctl is-active --quiet tradebot-sentinel; then
            log_success "TradeBot Sentinel service started successfully"
        else
            log_error "Failed to start TradeBot Sentinel service"
            sudo journalctl -u tradebot-sentinel --no-pager -n 20
            exit 1
        fi
    fi
}

# Setup Docker services
setup_docker_services() {
    log_info "Setting up Docker services..."
    
    # Install Docker if not present
    if ! command -v docker >/dev/null 2>&1; then
        log_info "Installing Docker..."
        if [ "$DRY_RUN" = false ]; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker "$DEPLOY_USER"
        fi
    fi
    
    # Build and run containers
    if [ "$DRY_RUN" = false ]; then
        cd "$DEPLOY_DIR"
        sudo -u "$DEPLOY_USER" docker-compose up -d --build
    fi
}

# Setup Kubernetes services
setup_kubernetes_services() {
    log_info "Setting up Kubernetes services..."
    log_warning "Kubernetes deployment not yet implemented"
}

# Setup web frontend
setup_frontend() {
    log_phase "$PHASE_WEB" "Setting up web frontend"
    
    if [ ! -d "$DEPLOY_DIR/frontend" ]; then
        log_info "No frontend directory found, skipping frontend setup"
        return 0
    fi
    
    # Build frontend
    log_info "Building frontend application..."
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would build frontend"
    else
        cd "$DEPLOY_DIR/frontend"
        sudo -u "$DEPLOY_USER" npm install
        sudo -u "$DEPLOY_USER" npm run build
    fi
    
    # Setup Nginx
    log_info "Configuring Nginx..."
    if [ -f "$DEPLOY_DIR/deployment/nginx/tradebot-sentinel.conf" ]; then
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY RUN] Would configure Nginx"
        else
            sudo cp "$DEPLOY_DIR/deployment/nginx/tradebot-sentinel.conf" "/etc/nginx/sites-available/"
            sudo ln -sf "/etc/nginx/sites-available/tradebot-sentinel.conf" "/etc/nginx/sites-enabled/"
            sudo nginx -t
            sudo systemctl reload nginx
        fi
    fi
    
    log_success "Frontend setup completed"
}

# Setup monitoring
setup_monitoring() {
    log_phase "$PHASE_MONITOR" "Setting up monitoring and alerting"
    
    # Start health monitor
    if [ "$DRY_RUN" = false ]; then
        if sudo systemctl is-enabled --quiet tradebot-health-monitor; then
            sudo systemctl start tradebot-health-monitor
            log_success "Health monitoring started"
        fi
    fi
    
    # Setup log rotation
    log_info "Configuring log rotation..."
    if [ "$DRY_RUN" = false ]; then
        sudo tee /etc/logrotate.d/tradebot-sentinel >/dev/null <<EOF
/var/log/tradebot-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $DEPLOY_USER $DEPLOY_USER
    postrotate
        systemctl reload tradebot-sentinel || true
    endscript
}
EOF
    fi
    
    log_success "Monitoring setup completed"
}

# Verify deployment
verify_deployment() {
    log_phase "$PHASE_VERIFY" "Verifying deployment"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would run deployment verification"
        return 0
    fi
    
    if [ -f "$DEPLOY_DIR/deployment/verify-deployment.sh" ]; then
        log_info "Running deployment verification script..."
        cd "$DEPLOY_DIR"
        sudo -u "$DEPLOY_USER" "./deployment/verify-deployment.sh" 2>&1 | tee -a "$LOG_FILE"
    else
        log_warning "Verification script not found, running basic checks..."
        
        # Basic service checks
        if sudo systemctl is-active --quiet tradebot-sentinel; then
            log_success "✓ TradeBot Sentinel service is running"
        else
            log_error "✗ TradeBot Sentinel service is not running"
        fi
        
        # Basic API check
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "✓ API health endpoint is responding"
        else
            log_warning "✗ API health endpoint is not responding"
        fi
    fi
    
    log_success "Deployment verification completed"
}

# Generate deployment report
generate_report() {
    local end_time=$(date +%s)
    local total_time=$((end_time - START_TIME))
    local report_file="/tmp/tradebot-deployment-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "TradeBot Sentinel Deployment Report"
        echo "Generated: $(date)"
        echo "======================================"
        echo ""
        echo "Deployment Summary:"
        echo "  Environment: $ENVIRONMENT"
        echo "  Target: $DEPLOY_TARGET"
        echo "  Deploy Directory: $DEPLOY_DIR"
        echo "  Deploy User: $DEPLOY_USER"
        echo "  Total Time: $((total_time / 60))m $((total_time % 60))s"
        echo "  Log File: $LOG_FILE"
        echo ""
        echo "System Information:"
        echo "  Hostname: $(hostname)"
        echo "  OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"
        echo "  Kernel: $(uname -r)"
        echo "  Memory: $(free -h | awk 'NR==2{print $2}')"
        echo "  Disk: $(df -h / | tail -1 | awk '{print $2" ("$5" used)"}')"
        echo ""
        echo "Service Status:"
        systemctl status tradebot-sentinel --no-pager -l 2>/dev/null || echo "  TradeBot Sentinel: Not found"
        systemctl status tradebot-health-monitor --no-pager -l 2>/dev/null || echo "  Health Monitor: Not found"
        echo ""
        echo "Network Configuration:"
        echo "  IP Address: $(hostname -I | awk '{print $1}')"
        echo "  Open Ports: $(ss -tlnp | grep LISTEN | awk '{print $4}' | cut -d: -f2 | sort -n | tr '\n' ' ')"
        echo ""
        echo "Next Steps:"
        echo "  1. Configure environment variables in $DEPLOY_DIR/.env"
        echo "  2. Set up trading platform credentials"
        echo "  3. Configure notification settings (Slack, Email)"
        echo "  4. Test trading functionality in paper mode"
        echo "  5. Monitor logs: sudo journalctl -u tradebot-sentinel -f"
        echo "  6. Access web interface: http://$(hostname -I | awk '{print $1}'):8000"
    } > "$report_file"
    
    log_success "Deployment report generated: $report_file"
    
    # Display summary
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}DEPLOYMENT COMPLETED SUCCESSFULLY${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "Environment: ${CYAN}$ENVIRONMENT${NC}"
    echo -e "Target: ${CYAN}$DEPLOY_TARGET${NC}"
    echo -e "Time: ${CYAN}$((total_time / 60))m $((total_time % 60))s${NC}"
    echo -e "Report: ${CYAN}$report_file${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  • Configure .env file with your trading credentials"
    echo "  • Test the deployment: ./deployment/verify-deployment.sh"
    echo "  • Monitor services: sudo systemctl status tradebot-sentinel"
    echo "  • View logs: sudo journalctl -u tradebot-sentinel -f"
    echo ""
}

# Show usage
show_usage() {
    echo "TradeBot Sentinel - Master Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV     Deployment environment (production, staging) [default: production]"
    echo "  -t, --target TARGET       Deployment target (systemd, docker, kubernetes) [default: systemd]"
    echo "  -u, --user USER           Deployment user [default: tradebot]"
    echo "  -d, --directory DIR       Deployment directory [default: /opt/tradebot-sentinel]"
    echo "      --skip-security       Skip security hardening"
    echo "      --skip-deps           Skip dependency installation"
    echo "      --force               Force reinstallation"
    echo "      --dry-run             Show what would be done without executing"
    echo "  -v, --verbose             Enable verbose output"
    echo "  -q, --quiet               Suppress non-error output"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Standard production deployment"
    echo "  $0 --environment staging              # Deploy to staging"
    echo "  $0 --target docker                    # Deploy using Docker"
    echo "  $0 --dry-run                          # Preview deployment steps"
    echo "  $0 --skip-security --force            # Force reinstall without security"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--target)
            DEPLOY_TARGET="$2"
            shift 2
            ;;
        -u|--user)
            DEPLOY_USER="$2"
            shift 2
            ;;
        -d|--directory)
            DEPLOY_DIR="$2"
            shift 2
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --force)
            FORCE_REINSTALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ ! "$ENVIRONMENT" =~ ^(production|staging|development)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    exit 1
fi

if [[ ! "$DEPLOY_TARGET" =~ ^(systemd|docker|kubernetes)$ ]]; then
    log_error "Invalid deployment target: $DEPLOY_TARGET"
    exit 1
fi

# Main deployment function
main() {
    log_info "Starting TradeBot Sentinel deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Target: $DEPLOY_TARGET"
    log_info "Log file: $LOG_FILE"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi
    
    # Execute deployment phases
    check_prerequisites
    create_backup
    setup_security
    install_dependencies
    deploy_application
    setup_services
    setup_frontend
    setup_monitoring
    verify_deployment
    generate_report
    
    log_success "TradeBot Sentinel deployment completed successfully!"
}

# Run main function
main "$@"