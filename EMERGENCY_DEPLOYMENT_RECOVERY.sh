#!/bin/bash

# 🚨 EMERGENCY DEPLOYMENT RECOVERY SCRIPT
# For AI Trading Sentinel - Critical CI/CD Pipeline Restoration
# This script provides immediate deployment recovery while fixing GitHub Actions

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${RED}🚨 EMERGENCY DEPLOYMENT RECOVERY${NC}"
echo -e "${RED}=================================${NC}"
echo -e "${YELLOW}AI Trading Sentinel - Critical System Recovery${NC}"
echo ""

# Configuration
VPS_HOST="185.244.214.70"
VPS_USER="root"
DEPLOY_PATH="/opt/trae"
BACKUP_PATH="/opt/trae/backup"
LOG_FILE="/var/log/trae-recovery.log"

echo -e "${BLUE}Target VPS: ${VPS_HOST}${NC}"
echo -e "${BLUE}Deploy Path: ${DEPLOY_PATH}${NC}"
echo -e "${BLUE}Recovery Time: $(date)${NC}"
echo ""

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check VPS connectivity
check_vps_connection() {
    echo -e "${YELLOW}🔍 Checking VPS connectivity...${NC}"
    if ping -c 3 "$VPS_HOST" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ VPS is reachable${NC}"
        return 0
    else
        echo -e "${RED}❌ VPS is not reachable${NC}"
        return 1
    fi
}

# Function to test SSH connection
test_ssh_connection() {
    echo -e "${YELLOW}🔐 Testing SSH connection...${NC}"
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "${VPS_USER}@${VPS_HOST}" "echo 'SSH OK'" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SSH connection successful${NC}"
        return 0
    else
        echo -e "${RED}❌ SSH connection failed${NC}"
        echo -e "${YELLOW}Trying alternative SSH methods...${NC}"
        
        # Try with password authentication
        echo -e "${BLUE}Please enter VPS password when prompted:${NC}"
        if ssh -o ConnectTimeout=10 -o PreferredAuthentications=password "${VPS_USER}@${VPS_HOST}" "echo 'SSH OK'"; then
            echo -e "${GREEN}✅ SSH with password successful${NC}"
            return 0
        else
            echo -e "${RED}❌ All SSH methods failed${NC}"
            return 1
        fi
    fi
}

# Function to create emergency deployment package
create_emergency_package() {
    echo -e "${YELLOW}📦 Creating emergency deployment package...${NC}"
    
    # Create temporary directory
    TEMP_DIR="/tmp/trae-emergency-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$TEMP_DIR"
    
    # Copy essential files
    if [ -f "main.py" ]; then
        cp main.py "$TEMP_DIR/"
    fi
    
    if [ -f "requirements.txt" ]; then
        cp requirements.txt "$TEMP_DIR/"
    fi
    
    # Copy source directory if exists
    if [ -d "src" ]; then
        cp -r src "$TEMP_DIR/"
    fi
    
    # Copy configuration files
    cp *.py "$TEMP_DIR/" 2>/dev/null || true
    cp *.json "$TEMP_DIR/" 2>/dev/null || true
    cp .env "$TEMP_DIR/" 2>/dev/null || true
    
    # Create emergency configuration
    cat > "$TEMP_DIR/emergency_config.py" << 'EOF'
#!/usr/bin/env python3
"""
Emergency Configuration for AI Trading Sentinel
Generated during recovery process
"""

import os
from datetime import datetime

# Emergency deployment info
EMERGENCY_DEPLOYMENT = True
DEPLOYMENT_TIME = datetime.now().isoformat()
RECOVERY_MODE = True

# Basic configuration
HEADLESS_MODE = True
LOG_LEVEL = "INFO"
API_PORT = 5000
MAX_RETRIES = 3
TIMEOUT = 30

# Safety settings
EMERGENCY_STOP_ENABLED = True
MAX_DRAWDOWN_PERCENT = 2.0  # Conservative during recovery
MAX_DAILY_TRADES = 10       # Reduced during recovery

print(f"🚨 Emergency configuration loaded at {DEPLOYMENT_TIME}")
EOF
    
    # Create emergency startup script
    cat > "$TEMP_DIR/emergency_start.sh" << 'EOF'
#!/bin/bash

# Emergency startup script for AI Trading Sentinel
echo "🚨 Starting AI Trading Sentinel in EMERGENCY MODE"
echo "Time: $(date)"

# Set emergency environment
export EMERGENCY_MODE=true
export LOG_LEVEL=INFO
export HEADLESS_MODE=true

# Create logs directory
mkdir -p logs

# Start with Python
if [ -f "main.py" ]; then
    echo "Starting main.py..."
    python3 main.py 2>&1 | tee logs/emergency-$(date +%Y%m%d-%H%M%S).log
elif [ -f "src/main.py" ]; then
    echo "Starting src/main.py..."
    cd src
    python3 main.py 2>&1 | tee ../logs/emergency-$(date +%Y%m%d-%H%M%S).log
else
    echo "❌ No main.py found!"
    exit 1
fi
EOF
    
    chmod +x "$TEMP_DIR/emergency_start.sh"
    
    # Create archive
    tar -czf "emergency-deployment.tar.gz" -C "$TEMP_DIR" .
    
    echo -e "${GREEN}✅ Emergency package created: emergency-deployment.tar.gz${NC}"
    echo -e "${BLUE}Package contents:${NC}"
    tar -tzf "emergency-deployment.tar.gz" | head -10
    
    # Cleanup
    rm -rf "$TEMP_DIR"
}

# Function to deploy emergency package
deploy_emergency_package() {
    echo -e "${YELLOW}🚀 Deploying emergency package to VPS...${NC}"
    
    # Upload package
    echo -e "${BLUE}Uploading emergency package...${NC}"
    scp -o ConnectTimeout=30 emergency-deployment.tar.gz "${VPS_USER}@${VPS_HOST}:/tmp/"
    
    # Deploy on VPS
    ssh "${VPS_USER}@${VPS_HOST}" << 'DEPLOY_SCRIPT'
set -e

echo "🚨 EMERGENCY DEPLOYMENT STARTING"
echo "Time: $(date)"

# Create deployment directory
mkdir -p /opt/trae/emergency
cd /opt/trae/emergency

# Backup current if exists
if [ -d "/opt/trae/current" ]; then
    echo "📦 Backing up current deployment..."
    cp -r /opt/trae/current /opt/trae/backup-emergency-$(date +%Y%m%d-%H%M%S) || true
fi

# Extract emergency package
echo "📦 Extracting emergency package..."
tar -xzf /tmp/emergency-deployment.tar.gz

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    python3 -m pip install -r requirements.txt
fi

# Set permissions
chmod +x *.py 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true

# Stop existing service
echo "🛑 Stopping existing services..."
systemctl stop trae-trading-bot 2>/dev/null || true
killall python3 2>/dev/null || true
sleep 5

# Create emergency systemd service
echo "⚙️ Creating emergency service..."
cat > /etc/systemd/system/trae-emergency.service << 'SERVICE_EOF'
[Unit]
Description=TRAE AI Trading Bot - Emergency Mode
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/trae/emergency
Environment=EMERGENCY_MODE=true
Environment=LOG_LEVEL=INFO
Environment=HEADLESS_MODE=true
ExecStart=/bin/bash emergency_start.sh
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Start emergency service
echo "🚀 Starting emergency service..."
systemctl daemon-reload
systemctl enable trae-emergency
systemctl start trae-emergency

# Wait and check status
sleep 10
if systemctl is-active --quiet trae-emergency; then
    echo "✅ Emergency service started successfully"
    systemctl status trae-emergency --no-pager -l
else
    echo "❌ Emergency service failed to start"
    systemctl status trae-emergency --no-pager -l
    journalctl -u trae-emergency --no-pager -n 20
    exit 1
fi

echo "🎉 EMERGENCY DEPLOYMENT COMPLETED"
echo "Service: trae-emergency"
echo "Status: $(systemctl is-active trae-emergency)"
echo "Logs: journalctl -u trae-emergency -f"
DEPLOY_SCRIPT
    
    echo -e "${GREEN}✅ Emergency deployment completed${NC}"
}

# Function to verify deployment
verify_emergency_deployment() {
    echo -e "${YELLOW}🔍 Verifying emergency deployment...${NC}"
    
    # Check service status
    if ssh "${VPS_USER}@${VPS_HOST}" "systemctl is-active --quiet trae-emergency"; then
        echo -e "${GREEN}✅ Emergency service is running${NC}"
    else
        echo -e "${RED}❌ Emergency service is not running${NC}"
        return 1
    fi
    
    # Check logs
    echo -e "${BLUE}Recent logs:${NC}"
    ssh "${VPS_USER}@${VPS_HOST}" "journalctl -u trae-emergency --no-pager -n 10"
    
    # Test API if available
    echo -e "${YELLOW}Testing API endpoint...${NC}"
    if curl -f -m 10 "http://${VPS_HOST}:5000/health" 2>/dev/null; then
        echo -e "${GREEN}✅ API is responding${NC}"
    else
        echo -e "${YELLOW}⚠️ API not responding (may be normal)${NC}"
    fi
    
    echo -e "${GREEN}✅ Emergency deployment verification completed${NC}"
}

# Function to create monitoring script
create_emergency_monitoring() {
    echo -e "${YELLOW}📊 Setting up emergency monitoring...${NC}"
    
    # Create monitoring script on VPS
    ssh "${VPS_USER}@${VPS_HOST}" << 'MONITOR_SCRIPT'
cat > /opt/trae/emergency_monitor.sh << 'EOF'
#!/bin/bash

# Emergency monitoring script for AI Trading Sentinel
LOG_FILE="/var/log/trae-emergency-monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔍 Emergency monitoring check started"

# Check service status
if systemctl is-active --quiet trae-emergency; then
    log "✅ Service is running"
else
    log "❌ Service is down - attempting restart"
    systemctl restart trae-emergency
    sleep 10
    if systemctl is-active --quiet trae-emergency; then
        log "✅ Service restarted successfully"
    else
        log "🚨 CRITICAL: Service restart failed"
        # Send alert (implement your preferred method)
    fi
fi

# Check system resources
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

log "📊 Memory usage: ${MEM_USAGE}%"
log "📊 Disk usage: ${DISK_USAGE}%"

if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    log "⚠️ High memory usage: ${MEM_USAGE}%"
fi

if [ "$DISK_USAGE" -gt 90 ]; then
    log "⚠️ High disk usage: ${DISK_USAGE}%"
fi

log "🔍 Emergency monitoring check completed"
EOF

chmod +x /opt/trae/emergency_monitor.sh

# Create cron job for monitoring
echo "*/5 * * * * /opt/trae/emergency_monitor.sh" | crontab -

echo "✅ Emergency monitoring setup completed"
echo "Monitor logs: tail -f /var/log/trae-emergency-monitor.log"
MONITOR_SCRIPT
    
    echo -e "${GREEN}✅ Emergency monitoring configured${NC}"
}

# Main execution
main() {
    echo -e "${PURPLE}🚨 STARTING EMERGENCY RECOVERY PROCESS${NC}"
    echo ""
    
    # Step 1: Check connectivity
    if ! check_vps_connection; then
        echo -e "${RED}❌ Cannot reach VPS. Check network connection.${NC}"
        exit 1
    fi
    
    # Step 2: Test SSH
    if ! test_ssh_connection; then
        echo -e "${RED}❌ Cannot establish SSH connection.${NC}"
        echo -e "${YELLOW}Please ensure:${NC}"
        echo "1. SSH keys are properly configured"
        echo "2. VPS is accessible"
        echo "3. Correct credentials are used"
        exit 1
    fi
    
    # Step 3: Create emergency package
    create_emergency_package
    
    # Step 4: Deploy emergency package
    deploy_emergency_package
    
    # Step 5: Verify deployment
    verify_emergency_deployment
    
    # Step 6: Setup monitoring
    create_emergency_monitoring
    
    # Success summary
    echo ""
    echo -e "${GREEN}🎉 EMERGENCY RECOVERY COMPLETED SUCCESSFULLY!${NC}"
    echo -e "${GREEN}===========================================${NC}"
    echo ""
    echo -e "${BLUE}Emergency Service Status:${NC}"
    ssh "${VPS_USER}@${VPS_HOST}" "systemctl status trae-emergency --no-pager -l"
    echo ""
    echo -e "${BLUE}Access Information:${NC}"
    echo -e "${YELLOW}VPS SSH:${NC} ssh ${VPS_USER}@${VPS_HOST}"
    echo -e "${YELLOW}Service Status:${NC} systemctl status trae-emergency"
    echo -e "${YELLOW}Live Logs:${NC} journalctl -u trae-emergency -f"
    echo -e "${YELLOW}Monitor Logs:${NC} tail -f /var/log/trae-emergency-monitor.log"
    echo -e "${YELLOW}API Endpoint:${NC} http://${VPS_HOST}:5000"
    echo ""
    echo -e "${PURPLE}Next Steps:${NC}"
    echo "1. Monitor the emergency service for stability"
    echo "2. Fix GitHub Actions CI/CD pipeline"
    echo "3. Test automated deployments"
    echo "4. Gradually restore full functionality"
    echo ""
    echo -e "${RED}⚠️ IMPORTANT: This is an emergency deployment.${NC}"
    echo -e "${RED}Fix the CI/CD pipeline as soon as possible.${NC}"
}

# Handle script arguments
case "${1:-}" in
    "--check-only")
        check_vps_connection && test_ssh_connection
        ;;
    "--package-only")
        create_emergency_package
        ;;
    "--deploy-only")
        deploy_emergency_package
        ;;
    "--verify-only")
        verify_emergency_deployment
        ;;
    "--monitor-only")
        create_emergency_monitoring
        ;;
    *)
        main
        ;;
esac

echo -e "${GREEN}Emergency recovery script completed.${NC}"