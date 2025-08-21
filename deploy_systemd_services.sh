#!/bin/bash

# AI Trading Sentinel - SystemD Services Deployment Script
# Configures production-ready services for 24/7 operation

set -e

echo "🚀 AI Trading Sentinel - SystemD Services Deployment"
echo "==================================================="

# Configuration
DEPLOY_PATH="/opt/ai-trading-sentinel"
SERVICE_DIR="/etc/systemd/system"
LOG_DIR="/var/log/trae"
USER="root"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# Step 1: Create deployment directory
log_info "Creating deployment directory structure..."
mkdir -p $DEPLOY_PATH
mkdir -p $LOG_DIR
chown -R $USER:$USER $DEPLOY_PATH
chown -R $USER:$USER $LOG_DIR

# Step 2: Install systemd service files
log_info "Installing systemd service files..."

# Copy service files
cp systemd/trae-backend.service $SERVICE_DIR/
cp systemd/trae-trading-bot.service $SERVICE_DIR/
cp systemd/trae-health-monitor.service $SERVICE_DIR/

# Set proper permissions
chmod 644 $SERVICE_DIR/trae-*.service
chown root:root $SERVICE_DIR/trae-*.service

log_success "Service files installed"

# Step 3: Reload systemd daemon
log_info "Reloading systemd daemon..."
systemctl daemon-reload

# Step 4: Enable services
log_info "Enabling services for auto-start..."
systemctl enable trae-backend.service
systemctl enable trae-trading-bot.service
systemctl enable trae-health-monitor.service

log_success "Services enabled for auto-start"

# Step 5: Create log rotation configuration
log_info "Setting up log rotation..."
cat > /etc/logrotate.d/trae << 'EOF'
/var/log/trae/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload trae-backend trae-trading-bot trae-health-monitor
    endscript
}
EOF

# Step 6: Create monitoring scripts
log_info "Creating monitoring and management scripts..."

# Service status script
cat > /usr/local/bin/trae-status << 'EOF'
#!/bin/bash
echo "🤖 AI Trading Sentinel - Service Status"
echo "======================================="
echo
echo "📊 Service Status:"
systemctl status trae-backend --no-pager -l
echo
systemctl status trae-trading-bot --no-pager -l
echo
systemctl status trae-health-monitor --no-pager -l
echo
echo "📈 Resource Usage:"
echo "Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5" used)"}')"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo
echo "🔗 Network Ports:"
netstat -tlnp | grep -E ':(5000|8080)'
echo
echo "📝 Recent Logs (last 10 lines):"
journalctl -u trae-backend -n 5 --no-pager
echo "---"
journalctl -u trae-trading-bot -n 5 --no-pager
EOF

chmod +x /usr/local/bin/trae-status

# Service restart script
cat > /usr/local/bin/trae-restart << 'EOF'
#!/bin/bash
echo "🔄 Restarting AI Trading Sentinel Services..."
echo "============================================="
systemctl restart trae-backend
echo "✅ Backend restarted"
systemctl restart trae-trading-bot
echo "✅ Trading bot restarted"
systemctl restart trae-health-monitor
echo "✅ Health monitor restarted"
echo
echo "📊 Service Status:"
systemctl is-active trae-backend trae-trading-bot trae-health-monitor
EOF

chmod +x /usr/local/bin/trae-restart

# Service logs script
cat > /usr/local/bin/trae-logs << 'EOF'
#!/bin/bash
case $1 in
    backend)
        journalctl -u trae-backend -f
        ;;
    bot)
        journalctl -u trae-trading-bot -f
        ;;
    monitor)
        journalctl -u trae-health-monitor -f
        ;;
    all)
        journalctl -u trae-backend -u trae-trading-bot -u trae-health-monitor -f
        ;;
    *)
        echo "Usage: trae-logs [backend|bot|monitor|all]"
        echo "Example: trae-logs all"
        ;;
esac
EOF

chmod +x /usr/local/bin/trae-logs

log_success "Management scripts created"

# Step 7: Create firewall rules
log_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 5000/tcp comment "TRAE Backend API"
    ufw allow 22/tcp comment "SSH"
    log_success "Firewall rules added"
else
    log_warning "UFW not found, skipping firewall configuration"
fi

# Step 8: Create health check endpoint
log_info "Setting up health check endpoint..."
cat > /usr/local/bin/trae-health-check << 'EOF'
#!/bin/bash
# Health check script for external monitoring

API_URL="http://localhost:5000/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL 2>/dev/null)

if [ "$RESPONSE" = "200" ]; then
    echo "OK - API responding"
    exit 0
else
    echo "CRITICAL - API not responding (HTTP $RESPONSE)"
    exit 2
fi
EOF

chmod +x /usr/local/bin/trae-health-check

# Step 9: Display deployment summary
echo
log_success "SystemD Services Deployment Complete!"
echo
echo "📋 Installed Services:"
echo "   • trae-backend.service      - Flask API server"
echo "   • trae-trading-bot.service  - Main trading bot"
echo "   • trae-health-monitor.service - System health monitoring"
echo
echo "🛠️  Management Commands:"
echo "   • trae-status              - View service status"
echo "   • trae-restart             - Restart all services"
echo "   • trae-logs [service]      - View service logs"
echo "   • trae-health-check        - Check API health"
echo
echo "🚀 Start Services:"
echo "   systemctl start trae-backend"
echo "   systemctl start trae-trading-bot"
echo "   systemctl start trae-health-monitor"
echo
echo "📊 Monitor Services:"
echo "   systemctl status trae-backend"
echo "   journalctl -u trae-trading-bot -f"
echo "   trae-status"
echo
echo "🔗 API Endpoints:"
echo "   • Health Check: http://localhost:5000/api/health"
echo "   • Status: http://localhost:5000/api/status"
echo "   • Dashboard: http://localhost:5000"
echo
log_info "Ready for production deployment!"