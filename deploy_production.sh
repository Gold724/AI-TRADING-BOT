#!/bin/bash

# AI Trading Sentinel - Production Deployment Script
# Comprehensive automation for Contabo VPS deployment

set -euo pipefail

# Configuration
DEPLOYMENT_USER="aitrading"
DEPLOYMENT_PATH="/home/aitrading/ai-trading-sentinel"
PYTHON_VERSION="3.10"
NODE_VERSION="18"
LOG_FILE="/var/log/aitrading-deployment.log"
BACKUP_DIR="/home/aitrading/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check system requirements
check_system() {
    log_info "Checking system requirements..."
    
    # Check OS
    if ! grep -q "Ubuntu" /etc/os-release; then
        log_warning "This script is optimized for Ubuntu. Proceeding anyway..."
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 10485760 ]]; then
        error_exit "Insufficient disk space. At least 10GB required."
    fi
    
    # Check memory (minimum 2GB)
    available_memory=$(free -m | awk 'NR==2{print $2}')
    if [[ $available_memory -lt 2048 ]]; then
        log_warning "Less than 2GB RAM available. Performance may be affected."
    fi
    
    log_success "System requirements check completed"
}

# Create deployment user
create_user() {
    log_info "Setting up deployment user..."
    
    if ! id "$DEPLOYMENT_USER" &>/dev/null; then
        sudo useradd -m -s /bin/bash "$DEPLOYMENT_USER"
        sudo usermod -aG sudo "$DEPLOYMENT_USER"
        log_success "User $DEPLOYMENT_USER created"
    else
        log_info "User $DEPLOYMENT_USER already exists"
    fi
    
    # Create necessary directories
    sudo -u "$DEPLOYMENT_USER" mkdir -p "$DEPLOYMENT_PATH"
    sudo -u "$DEPLOYMENT_USER" mkdir -p "$BACKUP_DIR"
    sudo -u "$DEPLOYMENT_USER" mkdir -p "$DEPLOYMENT_PATH/logs"
    sudo -u "$DEPLOYMENT_USER" mkdir -p "$DEPLOYMENT_PATH/temp"
    sudo -u "$DEPLOYMENT_USER" mkdir -p "$DEPLOYMENT_PATH/data"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install essential packages
    sudo apt install -y \
        curl \
        wget \
        git \
        build-essential \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        unzip \
        htop \
        nginx \
        fail2ban \
        ufw \
        logrotate \
        supervisor \
        xvfb \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libdrm2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libxss1 \
        libnss3
    
    log_success "System dependencies installed"
}

# Install Python
install_python() {
    log_info "Installing Python $PYTHON_VERSION..."
    
    # Add deadsnakes PPA for latest Python versions
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    
    # Install Python and pip
    sudo apt install -y \
        python$PYTHON_VERSION \
        python$PYTHON_VERSION-venv \
        python$PYTHON_VERSION-dev \
        python3-pip
    
    # Create symlink
    sudo ln -sf /usr/bin/python$PYTHON_VERSION /usr/bin/python3
    
    log_success "Python $PYTHON_VERSION installed"
}

# Install Node.js
install_nodejs() {
    log_info "Installing Node.js $NODE_VERSION..."
    
    # Install NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
    sudo apt install -y nodejs
    
    # Verify installation
    node_version=$(node --version)
    npm_version=$(npm --version)
    
    log_success "Node.js $node_version and npm $npm_version installed"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    cd "$DEPLOYMENT_PATH"
    
    # Create virtual environment
    sudo -u "$DEPLOYMENT_USER" python3 -m venv venv
    
    # Activate and upgrade pip
    sudo -u "$DEPLOYMENT_USER" bash -c "source venv/bin/activate && pip install --upgrade pip setuptools wheel"
    
    log_success "Python virtual environment created"
}

# Install application dependencies
install_app_deps() {
    log_info "Installing application dependencies..."
    
    cd "$DEPLOYMENT_PATH"
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        sudo -u "$DEPLOYMENT_USER" bash -c "source venv/bin/activate && pip install -r requirements.txt"
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found, skipping Python dependencies"
    fi
    
    # Install Node.js dependencies and build frontend
    if [[ -d "AI-TRADING-BOT/frontend" ]]; then
        cd "AI-TRADING-BOT/frontend"
        sudo -u "$DEPLOYMENT_USER" npm ci
        sudo -u "$DEPLOYMENT_USER" npm run build
        cd "../.."
        log_success "Frontend built successfully"
    else
        log_warning "Frontend directory not found, skipping frontend build"
    fi
}

# Configure Nginx
setup_nginx() {
    log_info "Configuring Nginx..."
    
    # Copy Nginx configuration
    if [[ -f "nginx/aitrading-sentinel.conf" ]]; then
        sudo cp nginx/aitrading-sentinel.conf /etc/nginx/sites-available/
        sudo ln -sf /etc/nginx/sites-available/aitrading-sentinel.conf /etc/nginx/sites-enabled/
        
        # Remove default site
        sudo rm -f /etc/nginx/sites-enabled/default
        
        # Test configuration
        sudo nginx -t
        
        # Create SSL directory and self-signed certificate (for development)
        sudo mkdir -p /etc/ssl/private
        if [[ ! -f "/etc/ssl/certs/aitrading-sentinel.crt" ]]; then
            sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout /etc/ssl/private/aitrading-sentinel.key \
                -out /etc/ssl/certs/aitrading-sentinel.crt \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        fi
        
        log_success "Nginx configured"
    else
        log_warning "Nginx configuration file not found"
    fi
}

# Setup systemd services
setup_systemd() {
    log_info "Setting up systemd services..."
    
    # Copy service files
    if [[ -d "systemd" ]]; then
        sudo cp systemd/*.service /etc/systemd/system/
        sudo systemctl daemon-reload
        
        # Enable services
        sudo systemctl enable aitrading-backend.service
        sudo systemctl enable aitrading-bot.service
        sudo systemctl enable aitrading-monitor.service
        
        log_success "Systemd services configured"
    else
        log_warning "Systemd service files not found"
    fi
}

# Configure firewall
setup_firewall() {
    log_info "Configuring firewall..."
    
    # Reset UFW
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (change port if needed)
    sudo ufw allow 22/tcp
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow Flask API (localhost only)
    sudo ufw allow from 127.0.0.1 to any port 5000
    
    # Enable firewall
    sudo ufw --force enable
    
    log_success "Firewall configured"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    cd "$DEPLOYMENT_PATH"
    
    # Run monitoring setup
    sudo -u "$DEPLOYMENT_USER" bash -c "source venv/bin/activate && python monitoring_setup.py --setup"
    
    log_success "Monitoring configured"
}

# Create backup script
setup_backup() {
    log_info "Setting up backup system..."
    
    cat > /tmp/backup_script.sh << 'EOF'
#!/bin/bash

# AI Trading Sentinel Backup Script
BACKUP_DIR="/home/aitrading/backups"
SOURCE_DIR="/home/aitrading/ai-trading-sentinel"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="aitrading_backup_$DATE"

# Create backup
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
cp -r "$SOURCE_DIR" "$BACKUP_DIR/$BACKUP_NAME/"

# Compress backup
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Keep only last 7 backups
ls -t *.tar.gz | tail -n +8 | xargs -r rm

echo "Backup completed: $BACKUP_NAME.tar.gz"
EOF

    sudo mv /tmp/backup_script.sh /home/aitrading/backup.sh
    sudo chown aitrading:aitrading /home/aitrading/backup.sh
    sudo chmod +x /home/aitrading/backup.sh
    
    # Add to crontab
    (sudo -u aitrading crontab -l 2>/dev/null; echo "0 2 * * * /home/aitrading/backup.sh") | sudo -u aitrading crontab -
    
    log_success "Backup system configured"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start and enable Nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    # Start AI Trading Sentinel services
    sudo systemctl start aitrading-backend
    sudo systemctl start aitrading-bot
    sudo systemctl start aitrading-monitor
    
    # Wait for services to start
    sleep 10
    
    # Check service status
    services=("nginx" "aitrading-backend" "aitrading-bot" "aitrading-monitor")
    for service in "${services[@]}"; do
        if sudo systemctl is-active --quiet "$service"; then
            log_success "$service is running"
        else
            log_error "$service failed to start"
            sudo systemctl status "$service" --no-pager
        fi
    done
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Test API endpoints
    if curl -f http://localhost:5000/api/health >/dev/null 2>&1; then
        log_success "Backend API is responding"
    else
        log_error "Backend API is not responding"
    fi
    
    if curl -f http://localhost/api/health >/dev/null 2>&1; then
        log_success "Nginx proxy is working"
    else
        log_error "Nginx proxy is not working"
    fi
    
    # Run comprehensive health check
    cd "$DEPLOYMENT_PATH"
    sudo -u "$DEPLOYMENT_USER" bash -c "source venv/bin/activate && python monitoring_setup.py --health-check"
}

# Display deployment summary
show_summary() {
    log_info "Deployment Summary"
    echo "==========================================="
    echo "Deployment Path: $DEPLOYMENT_PATH"
    echo "User: $DEPLOYMENT_USER"
    echo "Python Version: $(python3 --version)"
    echo "Node Version: $(node --version)"
    echo "Nginx Status: $(sudo systemctl is-active nginx)"
    echo "Backend Status: $(sudo systemctl is-active aitrading-backend)"
    echo "Bot Status: $(sudo systemctl is-active aitrading-bot)"
    echo "Monitor Status: $(sudo systemctl is-active aitrading-monitor)"
    echo "==========================================="
    echo "Frontend URL: https://$(hostname -I | awk '{print $1}')"
    echo "API URL: https://$(hostname -I | awk '{print $1}')/api"
    echo "Logs: $DEPLOYMENT_PATH/logs/"
    echo "==========================================="
}

# Main deployment function
main() {
    log_info "Starting AI Trading Sentinel deployment..."
    
    # Parse command line arguments
    SKIP_DEPS=false
    SKIP_BUILD=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--skip-deps] [--skip-build] [--help]"
                echo "  --skip-deps   Skip system dependency installation"
                echo "  --skip-build  Skip application build steps"
                echo "  --help        Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Create log file
    sudo touch "$LOG_FILE"
    sudo chmod 666 "$LOG_FILE"
    
    # Run deployment steps
    check_root
    check_system
    create_user
    
    if [[ "$SKIP_DEPS" == "false" ]]; then
        install_system_deps
        install_python
        install_nodejs
    fi
    
    setup_python_env
    
    if [[ "$SKIP_BUILD" == "false" ]]; then
        install_app_deps
    fi
    
    setup_nginx
    setup_systemd
    setup_firewall
    setup_monitoring
    setup_backup
    start_services
    run_health_checks
    show_summary
    
    log_success "AI Trading Sentinel deployment completed successfully!"
}

# Run main function with all arguments
main "$@"