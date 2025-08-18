#!/bin/bash

# TradeBot Sentinel Monitoring Stack Startup Script
# Orchestrates deployment of complete monitoring infrastructure

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$SCRIPT_DIR/monitoring-startup.log"
PID_FILE="$SCRIPT_DIR/monitoring.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

info() { log "INFO" "$@"; }
warn() { log "WARN" "$@"; }
error() { log "ERROR" "$@"; }
success() { log "SUCCESS" "$@"; }

# Print colored output
print_status() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Docker
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        missing_deps+=("docker-compose")
    fi
    
    # Check curl
    if ! command_exists curl; then
        missing_deps+=("curl")
    fi
    
    # Check jq
    if ! command_exists jq; then
        missing_deps+=("jq")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "Missing dependencies: ${missing_deps[*]}"
        error "Please install the missing dependencies and try again."
        exit 1
    fi
    
    success "All prerequisites satisfied"
}

# Create necessary directories
setup_directories() {
    info "Setting up directories..."
    
    local dirs=(
        "$SCRIPT_DIR/data/prometheus"
        "$SCRIPT_DIR/data/grafana"
        "$SCRIPT_DIR/data/loki"
        "$SCRIPT_DIR/data/alertmanager"
        "$SCRIPT_DIR/logs"
        "$SCRIPT_DIR/config"
        "$SCRIPT_DIR/ssl"
        "$PROJECT_ROOT/logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            info "Created directory: $dir"
        fi
    done
    
    # Set proper permissions
    chmod 755 "$SCRIPT_DIR/data"/*
    chmod 755 "$SCRIPT_DIR/logs"
    
    success "Directories setup complete"
}

# Load environment variables
load_environment() {
    info "Loading environment configuration..."
    
    # Load from .env file if it exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
        info "Loaded environment from $PROJECT_ROOT/.env"
    fi
    
    # Set default values if not provided
    export ENVIRONMENT=${ENVIRONMENT:-production}
    export GRAFANA_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
    export GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-$(openssl rand -base64 32)}
    export PROMETHEUS_RETENTION=${PROMETHEUS_RETENTION:-30d}
    export LOKI_RETENTION=${LOKI_RETENTION:-31d}
    
    # Alert configuration
    export SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-}
    export EMAIL_FROM=${EMAIL_FROM:-tradebot@example.com}
    export EMAIL_TO=${EMAIL_TO:-admin@example.com}
    export SMTP_HOST=${SMTP_HOST:-smtp.gmail.com}
    export SMTP_PORT=${SMTP_PORT:-587}
    export SMTP_USERNAME=${SMTP_USERNAME:-}
    export SMTP_PASSWORD=${SMTP_PASSWORD:-}
    
    # Database configuration (if using)
    export POSTGRES_USER=${POSTGRES_USER:-tradebot}
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}
    export POSTGRES_DB=${POSTGRES_DB:-tradebot}
    export REDIS_PASSWORD=${REDIS_PASSWORD:-$(openssl rand -base64 32)}
    
    success "Environment configuration loaded"
}

# Validate configuration files
validate_configs() {
    info "Validating configuration files..."
    
    local configs=(
        "prometheus.yml"
        "alert_rules.yml"
        "alertmanager-config.yml"
        "loki-config.yml"
        "promtail-config.yml"
        "blackbox-config.yml"
        "grafana-datasources.yml"
        "grafana-dashboards.yml"
        "docker-compose.monitoring.yml"
    )
    
    local missing_configs=()
    
    for config in "${configs[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$config" ]; then
            missing_configs+=("$config")
        fi
    done
    
    if [ ${#missing_configs[@]} -ne 0 ]; then
        error "Missing configuration files: ${missing_configs[*]}"
        exit 1
    fi
    
    # Validate YAML syntax
    for config in "${configs[@]}"; do
        if [[ "$config" == *.yml ]] || [[ "$config" == *.yaml ]]; then
            if command_exists yq; then
                if ! yq eval . "$SCRIPT_DIR/$config" >/dev/null 2>&1; then
                    error "Invalid YAML syntax in $config"
                    exit 1
                fi
            fi
        fi
    done
    
    success "Configuration validation complete"
}

# Create Docker networks
setup_networks() {
    info "Setting up Docker networks..."
    
    # Create monitoring network
    if ! docker network ls | grep -q "monitoring"; then
        docker network create monitoring --driver bridge
        info "Created monitoring network"
    fi
    
    # Create tradebot network if it doesn't exist
    if ! docker network ls | grep -q "tradebot-network"; then
        docker network create tradebot-network --driver bridge
        info "Created tradebot-network"
    fi
    
    success "Docker networks setup complete"
}

# Generate SSL certificates (self-signed for development)
setup_ssl() {
    info "Setting up SSL certificates..."
    
    local ssl_dir="$SCRIPT_DIR/ssl"
    local cert_file="$ssl_dir/cert.pem"
    local key_file="$ssl_dir/key.pem"
    
    if [ ! -f "$cert_file" ] || [ ! -f "$key_file" ]; then
        info "Generating self-signed SSL certificate..."
        
        openssl req -x509 -newkey rsa:4096 -keyout "$key_file" -out "$cert_file" \
            -days 365 -nodes -subj "/C=US/ST=State/L=City/O=TradeBot/CN=localhost"
        
        chmod 600 "$key_file"
        chmod 644 "$cert_file"
        
        info "SSL certificate generated"
    else
        info "SSL certificate already exists"
    fi
    
    success "SSL setup complete"
}

# Start monitoring stack
start_monitoring() {
    info "Starting monitoring stack..."
    
    cd "$SCRIPT_DIR"
    
    # Pull latest images
    info "Pulling Docker images..."
    docker-compose -f docker-compose.monitoring.yml pull
    
    # Start services
    info "Starting monitoring services..."
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # Wait for services to be ready
    info "Waiting for services to start..."
    sleep 30
    
    success "Monitoring stack started"
}

# Health check for services
health_check() {
    info "Performing health checks..."
    
    local services=(
        "prometheus:9090:/api/v1/status/config"
        "grafana:3000:/api/health"
        "alertmanager:9093:/api/v1/status"
        "loki:3100:/ready"
    )
    
    local failed_services=()
    
    for service in "${services[@]}"; do
        local name=$(echo "$service" | cut -d: -f1)
        local port=$(echo "$service" | cut -d: -f2)
        local endpoint=$(echo "$service" | cut -d: -f3)
        local url="http://localhost:$port$endpoint"
        
        info "Checking $name at $url"
        
        if curl -sf "$url" >/dev/null 2>&1; then
            success "$name is healthy"
        else
            error "$name health check failed"
            failed_services+=("$name")
        fi
    done
    
    if [ ${#failed_services[@]} -ne 0 ]; then
        error "Health check failed for: ${failed_services[*]}"
        return 1
    fi
    
    success "All services are healthy"
}

# Setup Grafana dashboards
setup_grafana() {
    info "Setting up Grafana dashboards..."
    
    # Wait for Grafana to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "http://localhost:3000/api/health" >/dev/null 2>&1; then
            break
        fi
        info "Waiting for Grafana to be ready (attempt $attempt/$max_attempts)..."
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "Grafana failed to start within expected time"
        return 1
    fi
    
    # Import dashboard
    local dashboard_file="$SCRIPT_DIR/grafana-dashboard.json"
    if [ -f "$dashboard_file" ]; then
        info "Importing TradeBot dashboard..."
        
        curl -X POST \
            -H "Content-Type: application/json" \
            -d @"$dashboard_file" \
            "http://$GRAFANA_ADMIN_USER:$GRAFANA_ADMIN_PASSWORD@localhost:3000/api/dashboards/db" \
            >/dev/null 2>&1 || warn "Dashboard import may have failed"
        
        success "Grafana dashboard imported"
    fi
}

# Display service URLs
show_urls() {
    print_status "$GREEN" "\n=== TradeBot Sentinel Monitoring Stack ==="
    print_status "$BLUE" "Grafana Dashboard: http://localhost:3000"
    print_status "$BLUE" "  Username: $GRAFANA_ADMIN_USER"
    print_status "$BLUE" "  Password: $GRAFANA_ADMIN_PASSWORD"
    print_status "$BLUE" "\nPrometheus: http://localhost:9090"
    print_status "$BLUE" "AlertManager: http://localhost:9093"
    print_status "$BLUE" "Loki: http://localhost:3100"
    print_status "$BLUE" "Jaeger: http://localhost:16686"
    print_status "$BLUE" "\nHealth Endpoint: http://localhost:8001/health"
    print_status "$BLUE" "Metrics Endpoint: http://localhost:8001/metrics"
    print_status "$GREEN" "\n=== Monitoring Stack Ready ==="
}

# Save process information
save_pid() {
    echo $$ > "$PID_FILE"
    info "Process ID saved to $PID_FILE"
}

# Cleanup function
cleanup() {
    info "Cleaning up..."
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
}

# Signal handlers
trap cleanup EXIT
trap 'error "Script interrupted"; exit 1' INT TERM

# Main execution
main() {
    print_status "$GREEN" "Starting TradeBot Sentinel Monitoring Stack..."
    
    save_pid
    
    check_prerequisites
    setup_directories
    load_environment
    validate_configs
    setup_networks
    setup_ssl
    start_monitoring
    
    # Wait a bit for services to stabilize
    sleep 60
    
    health_check
    setup_grafana
    
    show_urls
    
    success "Monitoring stack deployment complete!"
    
    # Keep script running to maintain logging
    if [ "${1:-}" != "--no-wait" ]; then
        info "Monitoring stack is running. Press Ctrl+C to stop."
        while true; do
            sleep 300  # Check every 5 minutes
            if ! health_check >/dev/null 2>&1; then
                warn "Some services are unhealthy. Check logs for details."
            fi
        done
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --no-wait    Start services and exit (don't wait)"
    echo "  --help       Show this help message"
    echo "  --stop       Stop monitoring stack"
    echo "  --restart    Restart monitoring stack"
    echo "  --status     Show status of monitoring services"
    echo "  --logs       Show logs from monitoring services"
}

# Stop monitoring stack
stop_monitoring() {
    info "Stopping monitoring stack..."
    cd "$SCRIPT_DIR"
    docker-compose -f docker-compose.monitoring.yml down
    success "Monitoring stack stopped"
}

# Show status
show_status() {
    info "Monitoring stack status:"
    cd "$SCRIPT_DIR"
    docker-compose -f docker-compose.monitoring.yml ps
}

# Show logs
show_logs() {
    cd "$SCRIPT_DIR"
    docker-compose -f docker-compose.monitoring.yml logs -f
}

# Handle command line arguments
case "${1:-}" in
    --help)
        usage
        exit 0
        ;;
    --stop)
        stop_monitoring
        exit 0
        ;;
    --restart)
        stop_monitoring
        sleep 5
        main --no-wait
        exit 0
        ;;
    --status)
        show_status
        exit 0
        ;;
    --logs)
        show_logs
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac