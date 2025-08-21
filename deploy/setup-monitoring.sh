#!/bin/bash
# AI Trading Sentinel - Production Monitoring Setup Script
# Deploy comprehensive monitoring stack on Contabo VPS
# Usage: ./setup-monitoring.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_DIR="/opt/trae-monitoring"
SERVICE_USER="trae"
DATA_DIR="/var/lib/trae-monitoring"
LOG_DIR="/var/log/trae-monitoring"

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
        error "This script must be run as root. Use: sudo ./setup-monitoring.sh"
    fi
}

check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if ! grep -q "Ubuntu" /etc/os-release; then
        warn "This script is optimized for Ubuntu. Proceeding anyway..."
    fi
    
    # Check available memory (minimum 2GB recommended)
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 2 ]]; then
        warn "Less than 2GB RAM detected. Monitoring stack may be resource-constrained."
    fi
    
    # Check disk space (minimum 10GB recommended)
    DISK_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $DISK_GB -lt 10 ]]; then
        warn "Less than 10GB free disk space. Consider cleanup or expansion."
    fi
    
    log "System check completed"
}

install_docker() {
    log "Installing Docker and Docker Compose..."
    
    # Update package index
    apt-get update
    
    # Install prerequisites
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        wget \
        unzip
    
    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up Docker repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add service user to docker group
    usermod -aG docker $SERVICE_USER || true
    
    log "Docker installation completed"
}

setup_directories() {
    log "Setting up monitoring directories..."
    
    # Create directories
    mkdir -p $MONITORING_DIR
    mkdir -p $DATA_DIR/{prometheus,grafana,alertmanager}
    mkdir -p $LOG_DIR
    
    # Create service user if not exists
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d $MONITORING_DIR $SERVICE_USER
        log "Created service user: $SERVICE_USER"
    fi
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_USER $MONITORING_DIR
    chown -R $SERVICE_USER:$SERVICE_USER $DATA_DIR
    chown -R $SERVICE_USER:$SERVICE_USER $LOG_DIR
    
    # Set proper permissions for Grafana
    chmod 755 $DATA_DIR/grafana
    
    log "Directory setup completed"
}

setup_firewall() {
    log "Configuring firewall rules..."
    
    # Install ufw if not present
    apt-get install -y ufw
    
    # Allow SSH (important!)
    ufw allow ssh
    
    # Allow monitoring ports
    ufw allow 3000/tcp  # Grafana
    ufw allow 9090/tcp  # Prometheus
    ufw allow 9093/tcp  # Alertmanager
    ufw allow 9100/tcp  # Node Exporter
    
    # Allow application ports
    ufw allow 5000/tcp  # Flask backend
    ufw allow 3001/tcp  # React frontend
    
    # Enable firewall
    ufw --force enable
    
    log "Firewall configuration completed"
}

deploy_monitoring_stack() {
    log "Deploying monitoring stack..."
    
    cd $MONITORING_DIR
    
    # Copy monitoring configuration files
    cp /home/$SERVICE_USER/ai-trading-sentinel/monitoring/* .
    
    # Create environment file
    cat > .env << EOF
# AI Trading Sentinel Monitoring Environment
COMPOSE_PROJECT_NAME=trae-monitoring
GRAFANA_ADMIN_PASSWORD=trae_admin_2024
PROMETHEUS_RETENTION_TIME=30d
PROMETHEUS_RETENTION_SIZE=10GB
ALERT_WEBHOOK_URL=
SLACK_API_URL=
EOF
    
    # Deploy with Docker Compose
    docker compose -f docker-compose.monitoring.yml up -d
    
    # Wait for services to start
    log "Waiting for services to start..."
    sleep 30
    
    # Check service health
    docker compose -f docker-compose.monitoring.yml ps
    
    log "Monitoring stack deployment completed"
}

setup_systemd_service() {
    log "Setting up systemd service for monitoring stack..."
    
    cat > /etc/systemd/system/trae-monitoring.service << EOF
[Unit]
Description=AI Trading Sentinel Monitoring Stack
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$MONITORING_DIR
ExecStart=/usr/bin/docker compose -f docker-compose.monitoring.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.monitoring.yml down
TimeoutStartSec=0
User=$SERVICE_USER
Group=$SERVICE_USER

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable trae-monitoring.service
    
    log "Systemd service setup completed"
}

setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/trae-monitoring << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        docker compose -f $MONITORING_DIR/docker-compose.monitoring.yml restart prometheus grafana alertmanager
    endscript
}
EOF
    
    log "Log rotation setup completed"
}

setup_health_checks() {
    log "Setting up health check scripts..."
    
    cat > /usr/local/bin/trae-monitoring-health << 'EOF'
#!/bin/bash
# Health check script for AI Trading Sentinel monitoring

MONITORING_DIR="/opt/trae-monitoring"
cd $MONITORING_DIR

echo "=== AI Trading Sentinel Monitoring Health Check ==="
echo "Timestamp: $(date)"
echo

# Check Docker services
echo "Docker Services Status:"
docker compose -f docker-compose.monitoring.yml ps
echo

# Check service endpoints
echo "Service Health Checks:"
echo -n "Prometheus: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy || echo "FAILED"
echo

echo -n "Grafana: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health || echo "FAILED"
echo

echo -n "Alertmanager: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9093/-/healthy || echo "FAILED"
echo

echo -n "Node Exporter: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9100/metrics || echo "FAILED"
echo

# Check disk usage
echo "Disk Usage:"
df -h $MONITORING_DIR
echo

# Check memory usage
echo "Memory Usage:"
free -h
echo

echo "=== Health Check Complete ==="
EOF
    
    chmod +x /usr/local/bin/trae-monitoring-health
    
    # Create daily health check cron job
    echo "0 8 * * * root /usr/local/bin/trae-monitoring-health >> $LOG_DIR/health-check.log 2>&1" > /etc/cron.d/trae-monitoring-health
    
    log "Health check setup completed"
}

print_access_info() {
    log "Monitoring stack setup completed successfully!"
    echo
    echo -e "${BLUE}=== Access Information ===${NC}"
    echo -e "${GREEN}Grafana Dashboard:${NC} http://$(curl -s ifconfig.me):3000"
    echo -e "${GREEN}Username:${NC} admin"
    echo -e "${GREEN}Password:${NC} trae_admin_2024"
    echo
    echo -e "${GREEN}Prometheus:${NC} http://$(curl -s ifconfig.me):9090"
    echo -e "${GREEN}Alertmanager:${NC} http://$(curl -s ifconfig.me):9093"
    echo
    echo -e "${BLUE}=== Management Commands ===${NC}"
    echo -e "${GREEN}Start monitoring:${NC} systemctl start trae-monitoring"
    echo -e "${GREEN}Stop monitoring:${NC} systemctl stop trae-monitoring"
    echo -e "${GREEN}Check status:${NC} systemctl status trae-monitoring"
    echo -e "${GREEN}View logs:${NC} docker compose -f $MONITORING_DIR/docker-compose.monitoring.yml logs -f"
    echo -e "${GREEN}Health check:${NC} /usr/local/bin/trae-monitoring-health"
    echo
    echo -e "${YELLOW}Note: Make sure to update firewall rules and configure alerts in Alertmanager!${NC}"
}

# Main execution
main() {
    log "Starting AI Trading Sentinel monitoring setup..."
    
    check_root
    check_system
    install_docker
    setup_directories
    setup_firewall
    deploy_monitoring_stack
    setup_systemd_service
    setup_log_rotation
    setup_health_checks
    print_access_info
    
    log "Setup completed successfully!"
}

# Run main function
main "$@"