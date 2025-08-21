#!/bin/bash

# AI Trading Sentinel - Production Deployment Script
# This script is executed on the VPS by the GitHub Actions CI/CD pipeline

set -euo pipefail

# Configuration
APP_NAME="ai-trading-sentinel"
APP_DIR="/opt/${APP_NAME}"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/${APP_NAME}/deployment.log"
MAX_BACKUPS=5
HEALTH_CHECK_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5

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

# Cleanup function
cleanup() {
    log_info "Performing cleanup..."
    # Remove temporary files
    rm -f /tmp/deployment_*.tmp
    # Ensure services are running
    docker-compose ps
}

# Set trap for cleanup
trap cleanup EXIT

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error_exit "This script must be run as root"
fi

# Create necessary directories
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

log_info "Starting deployment of AI Trading Sentinel..."

# Step 1: Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check if Docker is running
if ! systemctl is-active --quiet docker; then
    log_warning "Docker is not running, starting it..."
    systemctl start docker || error_exit "Failed to start Docker"
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    error_exit "Docker Compose is not installed"
fi

# Check disk space (require at least 2GB free)
AVAILABLE_SPACE=$(df "$APP_DIR" | awk 'NR==2 {print $4}')
REQUIRED_SPACE=2097152  # 2GB in KB
if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
    error_exit "Insufficient disk space. Required: 2GB, Available: $((AVAILABLE_SPACE/1024/1024))GB"
fi

log_success "Pre-deployment checks passed"

# Step 2: Create backup
log_info "Creating backup of current deployment..."

BACKUP_NAME="${APP_NAME}-backup-$(date +%Y%m%d-%H%M%S)"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

if [[ -d "$APP_DIR" ]]; then
    # Stop services before backup
    cd "$APP_DIR"
    docker-compose down --timeout 30 || log_warning "Failed to stop services gracefully"
    
    # Create backup
    cp -r "$APP_DIR" "$BACKUP_PATH" || error_exit "Failed to create backup"
    
    # Backup database
    if docker ps -a | grep -q redis; then
        log_info "Backing up Redis data..."
        docker run --rm --volumes-from redis -v "${BACKUP_PATH}:/backup" alpine tar czf /backup/redis-data.tar.gz /data || log_warning "Redis backup failed"
    fi
    
    log_success "Backup created: $BACKUP_PATH"
else
    log_info "No existing deployment found, skipping backup"
fi

# Step 3: Clean up old backups
log_info "Cleaning up old backups..."
find "$BACKUP_DIR" -name "${APP_NAME}-backup-*" -type d | sort -r | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -rf
log_success "Old backups cleaned up"

# Step 4: Update application code
log_info "Updating application code..."

cd "$APP_DIR"

# Fetch latest changes
git fetch origin || error_exit "Failed to fetch from origin"

# Get current commit for rollback
CURRENT_COMMIT=$(git rev-parse HEAD)
log_info "Current commit: $CURRENT_COMMIT"

# Reset to latest main branch
git reset --hard origin/main || error_exit "Failed to reset to origin/main"

NEW_COMMIT=$(git rev-parse HEAD)
log_info "New commit: $NEW_COMMIT"

if [[ "$CURRENT_COMMIT" == "$NEW_COMMIT" ]]; then
    log_info "No new changes detected"
else
    log_success "Code updated successfully"
fi

# Step 5: Update environment configuration
log_info "Updating environment configuration..."

# Ensure .env file exists with production settings
if [[ ! -f ".env" ]]; then
    log_warning ".env file not found, creating from template"
    cp .env.example .env || error_exit "Failed to create .env file"
fi

# Update environment to production
sed -i 's/ENVIRONMENT=.*/ENVIRONMENT=production/' .env
sed -i 's/DEBUG=.*/DEBUG=false/' .env

log_success "Environment configuration updated"

# Step 6: Build and update Docker images
log_info "Building and updating Docker images..."

# Pull latest images
docker-compose pull || error_exit "Failed to pull Docker images"

# Build custom images if needed
docker-compose build --no-cache || error_exit "Failed to build Docker images"

log_success "Docker images updated"

# Step 7: Database migrations (if needed)
log_info "Running database migrations..."

# Start database services first
docker-compose up -d redis postgres || error_exit "Failed to start database services"

# Wait for databases to be ready
log_info "Waiting for databases to be ready..."
sleep 10

# Run migrations if migration script exists
if [[ -f "scripts/migrate.py" ]]; then
    docker-compose run --rm backend python scripts/migrate.py || log_warning "Database migration failed"
else
    log_info "No migration script found, skipping"
fi

log_success "Database migrations completed"

# Step 8: Start services
log_info "Starting application services..."

# Start all services
docker-compose up -d --remove-orphans || error_exit "Failed to start services"

log_success "Services started"

# Step 9: Health checks
log_info "Performing health checks..."

# Function to check service health
check_health() {
    local service_name=$1
    local health_url=$2
    local max_attempts=$((HEALTH_CHECK_TIMEOUT / HEALTH_CHECK_INTERVAL))
    local attempt=1
    
    log_info "Checking health of $service_name..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, waiting ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
        ((attempt++))
    done
    
    log_error "$service_name health check failed after $max_attempts attempts"
    return 1
}

# Check API health
if ! check_health "API" "http://localhost/api/health"; then
    error_exit "API health check failed"
fi

# Check frontend
if ! check_health "Frontend" "http://localhost/"; then
    error_exit "Frontend health check failed"
fi

# Check WebSocket (if available)
if command -v wscat &> /dev/null; then
    log_info "Checking WebSocket connection..."
    timeout 10 wscat -c ws://localhost/ws --close || log_warning "WebSocket check failed"
fi

log_success "All health checks passed"

# Step 10: Performance verification
log_info "Running performance verification..."

# Check response times
API_RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/api/health)
log_info "API response time: ${API_RESPONSE_TIME}s"

if (( $(echo "$API_RESPONSE_TIME > 2.0" | bc -l) )); then
    log_warning "API response time is high: ${API_RESPONSE_TIME}s"
fi

# Check memory usage
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | grep -E "(backend|frontend|redis)" || true)
log_info "Memory usage:\n$MEMORY_USAGE"

log_success "Performance verification completed"

# Step 11: Security checks
log_info "Running security checks..."

# Check for exposed ports
EXPOSED_PORTS=$(netstat -tuln | grep LISTEN | grep -E ":(22|80|443|5432|6379)" || true)
log_info "Exposed ports:\n$EXPOSED_PORTS"

# Check SSL certificate (if HTTPS is configured)
if [[ -f "/etc/nginx/ssl/cert.pem" ]]; then
    CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/nginx/ssl/cert.pem | cut -d= -f2)
    log_info "SSL certificate expires: $CERT_EXPIRY"
fi

log_success "Security checks completed"

# Step 12: Update monitoring and alerts
log_info "Updating monitoring configuration..."

# Restart monitoring services if they exist
if systemctl is-enabled --quiet prometheus; then
    systemctl reload prometheus || log_warning "Failed to reload Prometheus"
fi

if systemctl is-enabled --quiet grafana-server; then
    systemctl restart grafana-server || log_warning "Failed to restart Grafana"
fi

log_success "Monitoring configuration updated"

# Step 13: Clean up Docker resources
log_info "Cleaning up Docker resources..."

# Remove unused images
docker image prune -f || log_warning "Failed to prune Docker images"

# Remove unused volumes (be careful with this)
# docker volume prune -f || log_warning "Failed to prune Docker volumes"

# Remove unused networks
docker network prune -f || log_warning "Failed to prune Docker networks"

log_success "Docker cleanup completed"

# Step 14: Final verification
log_info "Running final verification..."

# Check all services are running
SERVICE_STATUS=$(docker-compose ps --services --filter "status=running")
EXPECTED_SERVICES=("backend" "frontend" "redis" "nginx")

for service in "${EXPECTED_SERVICES[@]}"; do
    if echo "$SERVICE_STATUS" | grep -q "$service"; then
        log_success "$service is running"
    else
        log_error "$service is not running"
        docker-compose logs "$service" | tail -20
        error_exit "Service $service failed to start"
    fi
done

# Step 15: Send deployment notification
log_info "Sending deployment notification..."

# Create deployment summary
DEPLOYMENT_SUMMARY="
🚀 **AI Trading Sentinel Deployment Successful**

**Details:**
- Environment: Production
- Commit: $NEW_COMMIT
- Deployment Time: $(date)
- Services: $(echo "$SERVICE_STATUS" | wc -l) running
- Health Status: All checks passed

**Services:**
$(docker-compose ps --format "table {{.Service}}\t{{.State}}\t{{.Ports}}")

**System Resources:**
- CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%
- Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')
- Disk Usage: $(df -h "$APP_DIR" | awk 'NR==2 {print $5}')

**Access URLs:**
- Frontend: https://trading.yourdomain.com
- API: https://trading.yourdomain.com/api
- Monitoring: https://monitoring.yourdomain.com
"

# Save deployment info
echo "$DEPLOYMENT_SUMMARY" > /tmp/deployment_summary.txt

# Send to Slack if webhook is configured
if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$DEPLOYMENT_SUMMARY\"}" \
        "$SLACK_WEBHOOK_URL" || log_warning "Failed to send Slack notification"
fi

log_success "Deployment notification sent"

# Step 16: Create deployment record
log_info "Creating deployment record..."

DEPLOYMENT_RECORD="{
    \"timestamp\": \"$(date -Iseconds)\",
    \"commit\": \"$NEW_COMMIT\",
    \"environment\": \"production\",
    \"status\": \"success\",
    \"services\": [$(echo "$SERVICE_STATUS" | sed 's/^/\"/;s/$/\"/' | paste -sd,)],
    \"backup_path\": \"$BACKUP_PATH\",
    \"deployment_duration\": \"$SECONDS seconds\"
}"

echo "$DEPLOYMENT_RECORD" > "${APP_DIR}/deployment_record.json"

log_success "Deployment record created"

# Final success message
log_success "🎉 AI Trading Sentinel deployment completed successfully!"
log_info "Deployment took $SECONDS seconds"
log_info "Application is now running at: https://trading.yourdomain.com"
log_info "Monitoring dashboard: https://monitoring.yourdomain.com"
log_info "Logs can be viewed with: docker-compose logs -f"

exit 0