#!/bin/bash
# AI Trading Sentinel - 24/7 Monitoring Setup Script
# Configure comprehensive monitoring, alerts, and auto-restart mechanisms

set -e

echo "🔧 Setting up 24/7 monitoring system..."

# Install monitoring dependencies
sudo apt-get update
sudo apt-get install -y htop iotop nethogs curl jq mailutils python3-pip

# Install Python dependencies for monitoring dashboard
pip3 install flask psutil

# Create monitoring directories
sudo mkdir -p /opt/ai-trading-sentinel/monitoring
sudo mkdir -p /var/log/ai-trading-sentinel
sudo mkdir -p /opt/ai-trading-sentinel/scripts

# Create health check script
sudo tee /opt/ai-trading-sentinel/scripts/health_check.sh > /dev/null << 'EOF'
#!/bin/bash
# Health check script for AI Trading Sentinel

LOG_FILE="/var/log/ai-trading-sentinel/health_check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Function to log messages
log_message() {
    echo "[$DATE] $1" >> $LOG_FILE
}

# Check Flask backend
check_backend() {
    if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
        log_message "✅ Backend health check: PASSED"
        return 0
    else
        log_message "❌ Backend health check: FAILED"
        return 1
    fi
}

# Check frontend
check_frontend() {
    if curl -s -f http://localhost/ > /dev/null 2>&1; then
        log_message "✅ Frontend health check: PASSED"
        return 0
    else
        log_message "❌ Frontend health check: FAILED"
        return 1
    fi
}

# Check system resources
check_resources() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    DISK_USAGE=$(df -h / | awk 'NR==2{printf "%s", $5}' | sed 's/%//')
    
    log_message "📊 System Resources - CPU: ${CPU_USAGE}%, Memory: ${MEMORY_USAGE}%, Disk: ${DISK_USAGE}%"
    
    # Alert if resources are high
    if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
        log_message "⚠️  HIGH CPU USAGE: ${CPU_USAGE}%"
        return 1
    fi
    
    if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
        log_message "⚠️  HIGH MEMORY USAGE: ${MEMORY_USAGE}%"
        return 1
    fi
    
    if [ "$DISK_USAGE" -gt 90 ]; then
        log_message "⚠️  HIGH DISK USAGE: ${DISK_USAGE}%"
        return 1
    fi
    
    return 0
}

# Check trading bot process
check_trading_bot() {
    if pgrep -f "python.*main.py" > /dev/null; then
        log_message "✅ Trading bot process: RUNNING"
        return 0
    else
        log_message "❌ Trading bot process: NOT RUNNING"
        return 1
    fi
}

# Main health check
main() {
    log_message "🔍 Starting health check..."
    
    FAILED_CHECKS=0
    
    check_backend || ((FAILED_CHECKS++))
    check_frontend || ((FAILED_CHECKS++))
    check_resources || ((FAILED_CHECKS++))
    check_trading_bot || ((FAILED_CHECKS++))
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        log_message "✅ All health checks passed"
        exit 0
    else
        log_message "❌ $FAILED_CHECKS health check(s) failed"
        exit 1
    fi
}

main
EOF

# Create auto-restart script
sudo tee /opt/ai-trading-sentinel/scripts/auto_restart.sh > /dev/null << 'EOF'
#!/bin/bash
# Auto-restart script for AI Trading Sentinel services

LOG_FILE="/var/log/ai-trading-sentinel/auto_restart.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

log_message() {
    echo "[$DATE] $1" >> $LOG_FILE
}

# Restart backend service
restart_backend() {
    log_message "🔄 Restarting backend service..."
    sudo systemctl restart ai-trading-sentinel-backend
    sleep 5
    
    if sudo systemctl is-active --quiet ai-trading-sentinel-backend; then
        log_message "✅ Backend service restarted successfully"
        return 0
    else
        log_message "❌ Failed to restart backend service"
        return 1
    fi
}

# Restart nginx
restart_nginx() {
    log_message "🔄 Restarting Nginx..."
    sudo systemctl restart nginx
    sleep 3
    
    if sudo systemctl is-active --quiet nginx; then
        log_message "✅ Nginx restarted successfully"
        return 0
    else
        log_message "❌ Failed to restart Nginx"
        return 1
    fi
}

# Check if restart is needed
if ! /opt/ai-trading-sentinel/scripts/health_check.sh; then
    log_message "⚠️  Health check failed, attempting auto-restart..."
    
    restart_backend
    restart_nginx
    
    # Wait and check again
    sleep 10
    if /opt/ai-trading-sentinel/scripts/health_check.sh; then
        log_message "✅ Auto-restart successful"
    else
        log_message "❌ Auto-restart failed, manual intervention required"
        /opt/ai-trading-sentinel/scripts/send_alert.sh "CRITICAL" "Auto-restart failed after health check failure"
    fi
else
    log_message "✅ System healthy, no restart needed"
fi
EOF

# Create simple monitoring dashboard
sudo tee /opt/ai-trading-sentinel/scripts/monitoring_dashboard.py > /dev/null << 'EOF'
#!/usr/bin/env python3
# Simple monitoring dashboard for AI Trading Sentinel

import json
import time
import subprocess
import psutil
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

def get_system_stats():
    """Get current system statistics"""
    try:
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'backend_status': subprocess.call(['systemctl', 'is-active', '--quiet', 'ai-trading-sentinel-backend']) == 0,
            'nginx_status': subprocess.call(['systemctl', 'is-active', '--quiet', 'nginx']) == 0,
            'uptime': subprocess.check_output(['uptime', '-p']).decode().strip()
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/api/status')
def status():
    return jsonify(get_system_stats())

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
EOF

# Create alert notification script
sudo tee /opt/ai-trading-sentinel/scripts/send_alert.sh > /dev/null << 'EOF'
#!/bin/bash
# Alert notification script

ALERT_TYPE="$1"
MESSAGE="$2"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log alert
echo "[$TIMESTAMP] ALERT: $ALERT_TYPE - $MESSAGE" >> /var/log/ai-trading-sentinel/alerts.log

# Email alert (configure with your email settings)
send_email_alert() {
    SUBJECT="[AI Trading Sentinel] $ALERT_TYPE Alert"
    BODY="Alert Time: $TIMESTAMP\n\nMessage: $MESSAGE\n\nServer: $(hostname)\nIP: $(curl -s ifconfig.me 2>/dev/null || echo 'N/A')"
    
    echo -e "$BODY" | mail -s "$SUBJECT" "your-email@gmail.com" 2>/dev/null || echo "Email alert failed"
}

# Simple webhook alert (replace with your webhook URL)
send_webhook_alert() {
    PAYLOAD=$(cat <<EOF
{
    "alert_type": "$ALERT_TYPE",
    "message": "$MESSAGE",
    "timestamp": "$TIMESTAMP",
    "server": "$(hostname)",
    "ip": "$(curl -s ifconfig.me 2>/dev/null || echo 'N/A')"
}
EOF
)
    
    curl -X POST -H 'Content-type: application/json' \
        --data "$PAYLOAD" \
        "https://your-webhook-url.com/alerts" 2>/dev/null || echo "Webhook alert failed"
}

# Send alerts (uncomment as needed)
# send_email_alert
# send_webhook_alert

echo "Alert logged: $ALERT_TYPE - $MESSAGE"
EOF

# Make scripts executable
sudo chmod +x /opt/ai-trading-sentinel/scripts/*.sh
sudo chmod +x /opt/ai-trading-sentinel/scripts/*.py

# Create systemd service for monitoring dashboard
sudo tee /etc/systemd/system/ai-trading-monitoring.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Sentinel Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-trading-sentinel/scripts
ExecStart=/usr/bin/python3 /opt/ai-trading-sentinel/scripts/monitoring_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start monitoring service
sudo systemctl daemon-reload
sudo systemctl enable ai-trading-monitoring
sudo systemctl start ai-trading-monitoring

# Setup cron jobs for automated monitoring
(crontab -l 2>/dev/null; echo "# AI Trading Sentinel Monitoring") | crontab -
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/ai-trading-sentinel/scripts/health_check.sh") | crontab -
(crontab -l 2>/dev/null; echo "*/10 * * * * /opt/ai-trading-sentinel/scripts/auto_restart.sh") | crontab -

# Setup log rotation
sudo tee /etc/logrotate.d/ai-trading-sentinel > /dev/null << 'EOF'
/var/log/ai-trading-sentinel/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

# Create monitoring status check
sudo tee /opt/ai-trading-sentinel/scripts/monitoring_status.sh > /dev/null << 'EOF'
#!/bin/bash
echo "=== AI Trading Sentinel Monitoring Status ==="
echo "Monitoring Dashboard: $(systemctl is-active ai-trading-monitoring)"
echo "Backend Service: $(systemctl is-active ai-trading-sentinel-backend 2>/dev/null || echo 'not-configured')"
echo "Nginx Service: $(systemctl is-active nginx)"
echo ""
echo "=== Recent Health Checks ==="
tail -n 10 /var/log/ai-trading-sentinel/health_check.log 2>/dev/null || echo "No health check logs found"
echo ""
echo "=== System Resources ==="
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $3 "/" $2 " (" $5 ")"}')"
echo ""
echo "=== Monitoring URLs ==="
echo "Monitoring Dashboard: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR-VPS-IP'):3000/api/status"
echo "Health Check: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR-VPS-IP'):3000/health"
EOF

sudo chmod +x /opt/ai-trading-sentinel/scripts/monitoring_status.sh

echo "✅ 24/7 Monitoring system setup complete!"
echo ""
echo "=== Monitoring Services ==="
echo "• Health checks run every 5 minutes"
echo "• Auto-restart runs every 10 minutes"
echo "• Monitoring dashboard: http://YOUR-VPS-IP:3000"
echo "• Logs: /var/log/ai-trading-sentinel/"
echo ""
echo "=== Commands ==="
echo "• Check status: sudo /opt/ai-trading-sentinel/scripts/monitoring_status.sh"
echo "• View logs: sudo tail -f /var/log/ai-trading-sentinel/health_check.log"
echo "• Manual health check: sudo /opt/ai-trading-sentinel/scripts/health_check.sh"
echo ""
echo "=== Next Steps ==="
echo "1. Configure email alerts in /opt/ai-trading-sentinel/scripts/send_alert.sh"
echo "2. Test monitoring: curl http://localhost:3000/api/status"
echo "3. Verify cron jobs: crontab -l"