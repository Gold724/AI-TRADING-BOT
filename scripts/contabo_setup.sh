#!/bin/bash
# AI Trading Sentinel - Contabo VPS Production Setup Script
# Comprehensive deployment with security hardening and monitoring
# Usage: ./contabo_setup.sh [--skip-updates] [--dev-mode]

set -euo pipefail

# Configuration
APP_NAME="ai-trading-sentinel"
APP_USER="sentinel"
APP_DIR="/opt/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
DATA_DIR="/var/lib/${APP_NAME}"
BACKUP_DIR="/backup/${APP_NAME}"
PYTHON_VERSION="3.11"
NODE_VERSION="18"
DOCKER_COMPOSE_VERSION="2.21.0"

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

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons."
        log_info "Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    SKIP_UPDATES=false
    DEV_MODE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-updates)
                SKIP_UPDATES=true
                shift
                ;;
            --dev-mode)
                DEV_MODE=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [--skip-updates] [--dev-mode]"
                echo "  --skip-updates: Skip system updates"
                echo "  --dev-mode: Install development tools"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

# System updates and basic packages
update_system() {
    if [[ "$SKIP_UPDATES" == "false" ]]; then
        log_info "Updating system packages..."
        sudo apt update && sudo apt upgrade -y
        sudo apt install -y \
            curl wget git unzip \
            build-essential software-properties-common \
            apt-transport-https ca-certificates gnupg lsb-release \
            htop iotop nethogs \
            fail2ban ufw \
            logrotate rsync \
            jq tree \
            supervisor nginx \
            postgresql-client redis-tools
    else
        log_warning "Skipping system updates"
    fi
}

# Install Python 3.11
install_python() {
    log_info "Installing Python ${PYTHON_VERSION}..."
    
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt update
        sudo apt install -y \
            python${PYTHON_VERSION} \
            python${PYTHON_VERSION}-dev \
            python${PYTHON_VERSION}-venv \
            python3-pip
    fi
    
    # Set Python 3.11 as default
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1
    
    # Upgrade pip
    python3 -m pip install --upgrade pip setuptools wheel
}

# Install Node.js
install_nodejs() {
    log_info "Installing Node.js ${NODE_VERSION}..."
    
    if ! command -v node &> /dev/null || [[ "$(node -v)" != "v${NODE_VERSION}"* ]]; then
        curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
        sudo apt install -y nodejs
    fi
    
    # Install global packages
    sudo npm install -g pm2 yarn
}

# Install Docker and Docker Compose
install_docker() {
    log_info "Installing Docker and Docker Compose..."
    
    if ! command -v docker &> /dev/null; then
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Add Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io
        
        # Add user to docker group
        sudo usermod -aG docker $USER
    fi
    
    # Install Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        sudo curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
}

# Create application user and directories
setup_app_user() {
    log_info "Setting up application user and directories..."
    
    # Create application user
    if ! id "$APP_USER" &>/dev/null; then
        sudo useradd -r -s /bin/bash -d "$APP_DIR" -m "$APP_USER"
        sudo usermod -aG docker "$APP_USER"
    fi
    
    # Create directories
    sudo mkdir -p "$APP_DIR" "$LOG_DIR" "$DATA_DIR" "$BACKUP_DIR"
    sudo mkdir -p "$DATA_DIR"/{screenshots,logs,config,data}
    
    # Set permissions
    sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR" "$LOG_DIR" "$DATA_DIR" "$BACKUP_DIR"
    sudo chmod -R 755 "$APP_DIR"
    sudo chmod -R 750 "$LOG_DIR" "$DATA_DIR" "$BACKUP_DIR"
}

# Install Playwright dependencies
install_playwright_deps() {
    log_info "Installing Playwright dependencies..."
    
    sudo apt install -y \
        libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
        libgtk-3-0 libatspi2.0-0 libxss1 libasound2 \
        xvfb fonts-liberation fonts-dejavu-core \
        libgbm1 libxrandr2 libasound2-dev
}

# Configure firewall
setup_firewall() {
    log_info "Configuring UFW firewall..."
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (adjust port if needed)
    sudo ufw allow 22/tcp comment 'SSH'
    
    # Allow HTTP/HTTPS
    sudo ufw allow 80/tcp comment 'HTTP'
    sudo ufw allow 443/tcp comment 'HTTPS'
    
    # Allow specific monitoring ports (localhost only)
    sudo ufw allow from 127.0.0.1 to any port 3000 comment 'Grafana'
    sudo ufw allow from 127.0.0.1 to any port 9090 comment 'Prometheus'
    
    # Enable UFW
    sudo ufw --force enable
    
    log_success "Firewall configured successfully"
}

# Configure Fail2Ban
setup_fail2ban() {
    log_info "Configuring Fail2Ban..."
    
    sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600
EOF

    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
}

# Setup log rotation
setup_logrotate() {
    log_info "Configuring log rotation..."
    
    sudo tee /etc/logrotate.d/${APP_NAME} > /dev/null <<EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ${APP_USER} ${APP_USER}
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
        docker-compose -f ${APP_DIR}/docker-compose.yml restart trading-sentinel > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 www-data adm
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
EOF
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up system monitoring..."
    
    # Create monitoring script
    sudo tee /usr/local/bin/sentinel-monitor > /dev/null <<'EOF'
#!/bin/bash
# AI Trading Sentinel System Monitor

APP_DIR="/opt/ai-trading-sentinel"
LOG_FILE="/var/log/ai-trading-sentinel/monitor.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEM=85
ALERT_THRESHOLD_DISK=90

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check system resources
check_resources() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    if (( $(echo "$CPU_USAGE > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        log_message "HIGH CPU USAGE: ${CPU_USAGE}%"
    fi
    
    if (( MEM_USAGE > ALERT_THRESHOLD_MEM )); then
        log_message "HIGH MEMORY USAGE: ${MEM_USAGE}%"
    fi
    
    if (( DISK_USAGE > ALERT_THRESHOLD_DISK )); then
        log_message "HIGH DISK USAGE: ${DISK_USAGE}%"
    fi
}

# Check Docker containers
check_containers() {
    cd "$APP_DIR" || exit 1
    
    if ! docker-compose ps | grep -q "Up"; then
        log_message "CONTAINER DOWN: Trading Sentinel container is not running"
        # Attempt restart
        docker-compose up -d
    fi
}

# Check application health
check_app_health() {
    if ! curl -f http://localhost/health > /dev/null 2>&1; then
        log_message "HEALTH CHECK FAILED: Application not responding"
    fi
}

# Main monitoring function
main() {
    check_resources
    check_containers
    check_app_health
}

main
EOF

    sudo chmod +x /usr/local/bin/sentinel-monitor
    
    # Create cron job for monitoring
    echo "*/5 * * * * /usr/local/bin/sentinel-monitor" | sudo crontab -u root -
}

# Setup backup system
setup_backup() {
    log_info "Setting up backup system..."
    
    sudo tee /usr/local/bin/sentinel-backup > /dev/null <<EOF
#!/bin/bash
# AI Trading Sentinel Backup Script

APP_DIR="${APP_DIR}"
BACKUP_DIR="${BACKUP_DIR}"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\${BACKUP_DIR}/sentinel_backup_\${DATE}.tar.gz"

# Create backup
tar -czf "\$BACKUP_FILE" \
    -C "\$APP_DIR" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='screenshots' \
    .

# Keep only last 7 days of backups
find "\$BACKUP_DIR" -name "sentinel_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$BACKUP_FILE"
EOF

    sudo chmod +x /usr/local/bin/sentinel-backup
    
    # Create daily backup cron job
    echo "0 2 * * * /usr/local/bin/sentinel-backup" | sudo crontab -u "$APP_USER" -
}

# Install development tools (optional)
install_dev_tools() {
    if [[ "$DEV_MODE" == "true" ]]; then
        log_info "Installing development tools..."
        sudo apt install -y \
            vim nano \
            tmux screen \
            git-flow \
            postgresql-client \
            redis-tools \
            httpie \
            tree \
            ncdu
    fi
}

# Create systemd service for the application
setup_systemd_service() {
    log_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/${APP_NAME}.service > /dev/null <<EOF
[Unit]
Description=AI Trading Sentinel
Requires=docker.service
After=docker.service
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=${APP_USER}
Group=${APP_USER}

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ${APP_NAME}.service
}

# Final security hardening
security_hardening() {
    log_info "Applying security hardening..."
    
    # Disable root login
    sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    
    # Disable password authentication (uncomment if using SSH keys)
    # sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    
    # Set secure SSH configuration
    sudo tee -a /etc/ssh/sshd_config > /dev/null <<EOF

# AI Trading Sentinel Security Settings
Protocol 2
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers ${USER} ${APP_USER}
EOF

    # Restart SSH service
    sudo systemctl restart ssh
    
    # Set kernel parameters for security
    sudo tee /etc/sysctl.d/99-security.conf > /dev/null <<EOF
# Network security
net.ipv4.conf.default.rp_filter=1
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.all.accept_redirects=0
net.ipv6.conf.all.accept_redirects=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.all.accept_source_route=0
net.ipv6.conf.all.accept_source_route=0
net.ipv4.conf.all.log_martians=1
net.ipv4.icmp_echo_ignore_broadcasts=1
net.ipv4.icmp_ignore_bogus_error_responses=1
net.ipv4.tcp_syncookies=1
kernel.dmesg_restrict=1
EOF

    sudo sysctl -p /etc/sysctl.d/99-security.conf
}

# Main installation function
main() {
    log_info "Starting AI Trading Sentinel Contabo VPS setup..."
    
    check_root
    parse_args "$@"
    
    # System setup
    update_system
    install_python
    install_nodejs
    install_docker
    install_playwright_deps
    
    # Application setup
    setup_app_user
    
    # Security and monitoring
    setup_firewall
    setup_fail2ban
    setup_logrotate
    setup_monitoring
    setup_backup
    setup_systemd_service
    
    # Optional development tools
    install_dev_tools
    
    # Final security hardening
    security_hardening
    
    log_success "AI Trading Sentinel setup completed successfully!"
    log_info "Next steps:"
    echo "  1. Reboot the system: sudo reboot"
    echo "  2. Clone the repository to ${APP_DIR}"
    echo "  3. Configure environment variables"
    echo "  4. Deploy using Docker Compose"
    echo "  5. Configure SSL certificates (recommended)"
    
    log_warning "Please reboot the system to ensure all changes take effect."
}

# Run main function with all arguments
main "$@"