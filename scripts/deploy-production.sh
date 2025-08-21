#!/bin/bash

# AI Trading Sentinel - Production Deployment Script
# This script deploys the complete system to a Contabo VPS with monitoring stack

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-trading-sentinel"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
DATA_DIR="${DEPLOY_DIR}/data"
LOGS_DIR="${DATA_DIR}/logs"
BACKUP_DIR="${DATA_DIR}/backups"
SSL_DIR="/etc/letsencrypt"
NGINX_CONF_DIR="/etc/nginx"
SYSTEMD_DIR="/etc/systemd/system"

# Functions
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

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running on Ubuntu/Debian
    if ! command -v apt-get &> /dev/null; then
        log_error "This script requires Ubuntu/Debian with apt-get"
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        log_error "No internet connectivity detected"
        exit 1
    fi
    
    # Check if .env.production exists
    if [[ ! -f ".env.production" ]]; then
        log_error ".env.production file not found. Please create it from .env.production.example"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

update_system() {
    log_info "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
    apt-get install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
    log_success "System updated successfully"
}

install_docker() {
    log_info "Installing Docker and Docker Compose..."
    
    # Remove old Docker versions
    apt-get remove -y docker docker-engine docker.io containerd runc || true
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Install Docker Compose (standalone)
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group if not root
    if [[ -n "${SUDO_USER:-}" ]]; then
        usermod -aG docker "$SUDO_USER"
    fi
    
    log_success "Docker installed successfully"
}

setup_directories() {
    log_info "Setting up directory structure..."
    
    # Create main directories
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$DATA_DIR"/{logs,backups,postgresql,redis,prometheus,grafana,loki,alertmanager}
    mkdir -p "$LOGS_DIR"/{trading-bot,backend,nginx,postgresql,redis,security,audit}
    mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}
    
    # Set permissions
    chown -R 1000:1000 "$DATA_DIR"
    chmod -R 755 "$DATA_DIR"
    
    log_success "Directory structure created"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Copy environment file
    cp .env.production "${DEPLOY_DIR}/.env"
    
    # Set secure permissions
    chmod 600 "${DEPLOY_DIR}/.env"
    chown root:root "${DEPLOY_DIR}/.env"
    
    # Source environment variables
    set -a
    source "${DEPLOY_DIR}/.env"
    set +a
    
    log_success "Environment configured"
}

setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    # Install Certbot
    apt-get install -y certbot python3-certbot-nginx
    
    # Check if domain is provided
    if [[ -z "${DOMAIN:-}" ]]; then
        log_warning "No domain provided, skipping SSL setup"
        return 0
    fi
    
    # Stop nginx if running
    systemctl stop nginx || true
    
    # Obtain SSL certificate
    certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email "${SSL_EMAIL:-admin@${DOMAIN}}"
    
    # Setup auto-renewal
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
    
    log_success "SSL certificates configured"
}

setup_nginx() {
    log_info "Setting up Nginx..."
    
    # Install Nginx
    apt-get install -y nginx
    
    # Backup original config
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    
    # Copy our Nginx configuration
    cp nginx.conf /etc/nginx/nginx.conf
    
    # Test configuration
    nginx -t
    
    # Enable and start Nginx
    systemctl enable nginx
    systemctl start nginx
    
    log_success "Nginx configured"
}

setup_firewall() {
    log_info "Configuring firewall..."
    
    # Install UFW
    apt-get install -y ufw
    
    # Reset UFW
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    ufw allow 22/tcp
    
    # Allow HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow monitoring ports (only from localhost)
    ufw allow from 127.0.0.1 to any port 3000  # Grafana
    ufw allow from 127.0.0.1 to any port 9090  # Prometheus
    ufw allow from 127.0.0.1 to any port 9093  # Alertmanager
    ufw allow from 127.0.0.1 to any port 3100  # Loki
    
    # Enable UFW
    ufw --force enable
    
    log_success "Firewall configured"
}

setup_fail2ban() {
    log_info "Setting up Fail2Ban..."
    
    # Install Fail2Ban
    apt-get install -y fail2ban
    
    # Create custom configuration
    cat > /etc/fail2ban/jail.local << EOF
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

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
EOF
    
    # Start and enable Fail2Ban
    systemctl enable fail2ban
    systemctl start fail2ban
    
    log_success "Fail2Ban configured"
}

deploy_application() {
    log_info "Deploying application..."
    
    # Copy application files
    rsync -av --exclude='.git' --exclude='node_modules' --exclude='venv' --exclude='__pycache__' . "$DEPLOY_DIR/"
    
    # Set ownership
    chown -R 1000:1000 "$DEPLOY_DIR"
    
    # Build and start services
    cd "$DEPLOY_DIR"
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Build custom images
    docker-compose -f docker-compose.prod.yml build
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "Application deployed"
}

setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Wait for services to start
    sleep 30
    
    # Check if Prometheus is accessible
    if curl -f http://localhost:9090/-/healthy &> /dev/null; then
        log_success "Prometheus is running"
    else
        log_warning "Prometheus health check failed"
    fi
    
    # Check if Grafana is accessible
    if curl -f http://localhost:3000/api/health &> /dev/null; then
        log_success "Grafana is running"
    else
        log_warning "Grafana health check failed"
    fi
    
    # Check if Alertmanager is accessible
    if curl -f http://localhost:9093/-/healthy &> /dev/null; then
        log_success "Alertmanager is running"
    else
        log_warning "Alertmanager health check failed"
    fi
    
    log_success "Monitoring stack deployed"
}

setup_backup() {
    log_info "Setting up backup system..."
    
    # Create backup script
    cat > /usr/local/bin/backup-trading-sentinel.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/ai-trading-sentinel/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DAILY_DIR="$BACKUP_DIR/daily"
WEEKLY_DIR="$BACKUP_DIR/weekly"
MONTHLY_DIR="$BACKUP_DIR/monthly"

# Create backup directories
mkdir -p "$DAILY_DIR" "$WEEKLY_DIR" "$MONTHLY_DIR"

# Backup PostgreSQL
docker exec ai-trading-sentinel-postgres-1 pg_dumpall -U postgres > "$DAILY_DIR/postgres_$DATE.sql"

# Backup Redis
docker exec ai-trading-sentinel-redis-1 redis-cli BGSAVE
sleep 5
docker cp ai-trading-sentinel-redis-1:/data/dump.rdb "$DAILY_DIR/redis_$DATE.rdb"

# Backup configuration files
tar -czf "$DAILY_DIR/config_$DATE.tar.gz" -C /opt/ai-trading-sentinel .

# Backup logs
tar -czf "$DAILY_DIR/logs_$DATE.tar.gz" -C /opt/ai-trading-sentinel/data/logs .

# Weekly backup (copy daily to weekly on Sundays)
if [[ $(date +%u) -eq 7 ]]; then
    cp "$DAILY_DIR/postgres_$DATE.sql" "$WEEKLY_DIR/"
    cp "$DAILY_DIR/redis_$DATE.rdb" "$WEEKLY_DIR/"
    cp "$DAILY_DIR/config_$DATE.tar.gz" "$WEEKLY_DIR/"
fi

# Monthly backup (copy daily to monthly on 1st of month)
if [[ $(date +%d) -eq 01 ]]; then
    cp "$DAILY_DIR/postgres_$DATE.sql" "$MONTHLY_DIR/"
    cp "$DAILY_DIR/redis_$DATE.rdb" "$MONTHLY_DIR/"
    cp "$DAILY_DIR/config_$DATE.tar.gz" "$MONTHLY_DIR/"
fi

# Cleanup old backups (keep 7 daily, 4 weekly, 12 monthly)
find "$DAILY_DIR" -name "*.sql" -mtime +7 -delete
find "$DAILY_DIR" -name "*.rdb" -mtime +7 -delete
find "$DAILY_DIR" -name "*.tar.gz" -mtime +7 -delete

find "$WEEKLY_DIR" -name "*.sql" -mtime +28 -delete
find "$WEEKLY_DIR" -name "*.rdb" -mtime +28 -delete
find "$WEEKLY_DIR" -name "*.tar.gz" -mtime +28 -delete

find "$MONTHLY_DIR" -name "*.sql" -mtime +365 -delete
find "$MONTHLY_DIR" -name "*.rdb" -mtime +365 -delete
find "$MONTHLY_DIR" -name "*.tar.gz" -mtime +365 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x /usr/local/bin/backup-trading-sentinel.sh
    
    # Setup cron job for daily backups
    echo "0 2 * * * /usr/local/bin/backup-trading-sentinel.sh >> /var/log/backup.log 2>&1" | crontab -
    
    log_success "Backup system configured"
}

setup_logrotate() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/ai-trading-sentinel << EOF
/opt/ai-trading-sentinel/data/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 1000 1000
    postrotate
        docker-compose -f /opt/ai-trading-sentinel/docker-compose.prod.yml restart promtail
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

setup_health_monitoring() {
    log_info "Setting up health monitoring..."
    
    # Create health check script
    cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash

CHECK_INTERVAL=60
LOG_FILE="/var/log/health-check.log"
ALERT_EMAIL="${ALERT_EMAIL:-admin@localhost}"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_service() {
    local service_name="$1"
    local check_url="$2"
    
    if curl -f -s "$check_url" > /dev/null; then
        log_message "✓ $service_name is healthy"
        return 0
    else
        log_message "✗ $service_name is unhealthy"
        return 1
    fi
}

restart_service() {
    local service_name="$1"
    log_message "Restarting $service_name..."
    cd /opt/ai-trading-sentinel
    docker-compose -f docker-compose.prod.yml restart "$service_name"
}

send_alert() {
    local message="$1"
    echo "$message" | mail -s "AI Trading Sentinel Alert" "$ALERT_EMAIL"
    log_message "Alert sent: $message"
}

# Main health check loop
while true; do
    failed_services=()
    
    # Check core services
    check_service "Backend API" "http://localhost:8000/health" || failed_services+=("backend")
    check_service "Frontend" "http://localhost:3000" || failed_services+=("frontend")
    check_service "PostgreSQL" "http://localhost:5432" || failed_services+=("postgres")
    check_service "Redis" "http://localhost:6379" || failed_services+=("redis")
    
    # Check monitoring services
    check_service "Prometheus" "http://localhost:9090/-/healthy" || failed_services+=("prometheus")
    check_service "Grafana" "http://localhost:3000/api/health" || failed_services+=("grafana")
    check_service "Alertmanager" "http://localhost:9093/-/healthy" || failed_services+=("alertmanager")
    
    # Restart failed services
    for service in "${failed_services[@]}"; do
        restart_service "$service"
        send_alert "Service $service was unhealthy and has been restarted"
    done
    
    sleep "$CHECK_INTERVAL"
done
EOF
    
    chmod +x /usr/local/bin/health-check.sh
    
    # Create systemd service for health monitoring
    cat > /etc/systemd/system/health-monitor.service << EOF
[Unit]
Description=AI Trading Sentinel Health Monitor
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/health-check.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable health-monitor.service
    systemctl start health-monitor.service
    
    log_success "Health monitoring configured"
}

print_summary() {
    log_success "\n=== DEPLOYMENT COMPLETED SUCCESSFULLY ==="
    echo -e "${GREEN}Application URL:${NC} https://${DOMAIN:-localhost}"
    echo -e "${GREEN}Grafana Dashboard:${NC} https://${DOMAIN:-localhost}/grafana"
    echo -e "${GREEN}Prometheus:${NC} https://${DOMAIN:-localhost}/prometheus"
    echo -e "${GREEN}API Documentation:${NC} https://${DOMAIN:-localhost}/api/docs"
    echo ""
    echo -e "${YELLOW}Important Notes:${NC}"
    echo "• Default Grafana credentials: admin / admin (change on first login)"
    echo "• SSL certificates will auto-renew via cron job"
    echo "• Daily backups are scheduled at 2:00 AM"
    echo "• Health monitoring is active and will auto-restart failed services"
    echo "• Logs are rotated daily and kept for 30 days"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "• View logs: docker-compose -f /opt/ai-trading-sentinel/docker-compose.prod.yml logs -f"
    echo "• Restart services: docker-compose -f /opt/ai-trading-sentinel/docker-compose.prod.yml restart"
    echo "• Check status: docker-compose -f /opt/ai-trading-sentinel/docker-compose.prod.yml ps"
    echo "• Manual backup: /usr/local/bin/backup-trading-sentinel.sh"
    echo "• View health logs: tail -f /var/log/health-check.log"
}

# Main execution
main() {
    log_info "Starting AI Trading Sentinel production deployment..."
    
    check_root
    check_prerequisites
    update_system
    install_docker
    setup_directories
    setup_environment
    setup_ssl
    setup_nginx
    setup_firewall
    setup_fail2ban
    deploy_application
    setup_monitoring
    setup_backup
    setup_logrotate
    setup_health_monitoring
    
    print_summary
}

# Run main function
main "$@"