# AI Trading Sentinel - 24/7 Monitoring Setup Script
# Configure comprehensive monitoring, alerts, and auto-restart mechanisms

Write-Host "AI Trading Sentinel - 24/7 Monitoring Setup" -ForegroundColor Blue
Write-Host "============================================" -ForegroundColor Blue

# Configuration
$VPS_IP = "185.244.214.70"
$MONITORING_PORT = "3000"
$ALERT_EMAIL = "your-email@gmail.com"
$SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

# Create monitoring configuration
$monitoringConfig = @'
#!/bin/bash
# AI Trading Sentinel - 24/7 Monitoring System
# This script sets up comprehensive monitoring for production deployment

set -e

echo "🔧 Setting up 24/7 monitoring system..."

# Install monitoring dependencies
sudo apt-get update
sudo apt-get install -y htop iotop nethogs curl jq mailutils

# Create monitoring directories
sudo mkdir -p /opt/ai-trading-sentinel/monitoring
sudo mkdir -p /var/log/ai-trading-sentinel
sudo mkdir -p /opt/ai-trading-sentinel/scripts

# Create health check script
cat > /opt/ai-trading-sentinel/scripts/health_check.sh << 'EOF'
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
cat > /opt/ai-trading-sentinel/scripts/auto_restart.sh << 'EOF'
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
        # Send alert (implement email/Slack notification here)
    fi
else
    log_message "✅ System healthy, no restart needed"
fi
EOF

# Create alert notification script
cat > /opt/ai-trading-sentinel/scripts/send_alert.sh << 'EOF'
#!/bin/bash
# Alert notification script

ALERT_TYPE="$1"
MESSAGE="$2"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Email alert (configure with your email settings)
send_email_alert() {
    SUBJECT="[AI Trading Sentinel] $ALERT_TYPE Alert"
    BODY="Alert Time: $TIMESTAMP\n\nMessage: $MESSAGE\n\nServer: $(hostname)\nIP: $(curl -s ifconfig.me)"
    
    echo -e "$BODY" | mail -s "$SUBJECT" "your-email@gmail.com"
}

# Slack alert (configure with your Slack webhook)
send_slack_alert() {
    PAYLOAD=$(cat <<EOF
{
    "text": "🚨 AI Trading Sentinel Alert",
    "attachments": [
        {
            "color": "danger",
            "fields": [
                {
                    "title": "Alert Type",
                    "value": "$ALERT_TYPE",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$TIMESTAMP",
                    "short": true
                },
                {
                    "title": "Message",
                    "value": "$MESSAGE",
                    "short": false
                },
                {
                    "title": "Server",
                    "value": "$(hostname) ($(curl -s ifconfig.me))",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)
    
    curl -X POST -H 'Content-type: application/json' \
        --data "$PAYLOAD" \
        "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
}

# Send alerts
send_email_alert
send_slack_alert

echo "Alert sent: $ALERT_TYPE - $MESSAGE"
EOF

# Create monitoring dashboard script
cat > /opt/ai-trading-sentinel/scripts/monitoring_dashboard.py << 'EOF'
#!/usr/bin/env python3
# Simple monitoring dashboard for AI Trading Sentinel

import json
import time
import subprocess
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

def get_system_stats():
    """Get current system statistics"""
    try:
        # CPU usage
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | awk -F'%' '{print $1}'"
        cpu_usage = subprocess.check_output(cpu_cmd, shell=True).decode().strip()
        
        # Memory usage
        mem_cmd = "free | grep Mem | awk '{printf(\"%.1f\", $3/$2 * 100.0)}'"
        memory_usage = subprocess.check_output(mem_cmd, shell=True).decode().strip()
        
        # Disk usage
        disk_cmd = "df -h / | awk 'NR==2{printf \"%s\", $5}' | sed 's/%//'"
        disk_usage = subprocess.check_output(disk_cmd, shell=True).decode().strip()
        
        # Service status
        backend_status = subprocess.call(['systemctl', 'is-active', '--quiet', 'ai-trading-sentinel-backend']) == 0
        nginx_status = subprocess.call(['systemctl', 'is-active', '--quiet', 'nginx']) == 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': float(cpu_usage) if cpu_usage else 0,
            'memory_usage': float(memory_usage) if memory_usage else 0,
            'disk_usage': int(disk_usage) if disk_usage else 0,
            'backend_status': backend_status,
            'nginx_status': nginx_status
        }
    except Exception as e:
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

@app.route('/')
def dashboard():
    """Main monitoring dashboard"""
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Trading Sentinel - Monitoring Dashboard</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stat-value { font-size: 2em; font-weight: bold; margin: 10px 0; }
            .status-ok { color: #27ae60; }
            .status-error { color: #e74c3c; }
            .status-warning { color: #f39c12; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Trading Sentinel - Monitoring Dashboard</h1>
                <p>Real-time system monitoring and health status</p>
            </div>
            
            <div class="stats-grid" id="stats-grid">
                <!-- Stats will be loaded here -->
            </div>
        </div>
        
        <script>
            function updateStats() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        const grid = document.getElementById('stats-grid');
                        grid.innerHTML = `
                            <div class="stat-card">
                                <h3>CPU Usage</h3>
                                <div class="stat-value ${data.cpu_usage > 80 ? 'status-error' : data.cpu_usage > 60 ? 'status-warning' : 'status-ok'}">
                                    ${data.cpu_usage}%
                                </div>
                            </div>
                            <div class="stat-card">
                                <h3>Memory Usage</h3>
                                <div class="stat-value ${data.memory_usage > 85 ? 'status-error' : data.memory_usage > 70 ? 'status-warning' : 'status-ok'}">
                                    ${data.memory_usage}%
                                </div>
                            </div>
                            <div class="stat-card">
                                <h3>Disk Usage</h3>
                                <div class="stat-value ${data.disk_usage > 90 ? 'status-error' : data.disk_usage > 75 ? 'status-warning' : 'status-ok'}">
                                    ${data.disk_usage}%
                                </div>
                            </div>
                            <div class="stat-card">
                                <h3>Backend Service</h3>
                                <div class="stat-value ${data.backend_status ? 'status-ok' : 'status-error'}">
                                    ${data.backend_status ? '✅ Running' : '❌ Stopped'}
                                </div>
                            </div>
                            <div class="stat-card">
                                <h3>Nginx Service</h3>
                                <div class="stat-value ${data.nginx_status ? 'status-ok' : 'status-error'}">
                                    ${data.nginx_status ? '✅ Running' : '❌ Stopped'}
                                </div>
                            </div>
                            <div class="stat-card">
                                <h3>Last Update</h3>
                                <div class="stat-value status-ok">
                                    ${new Date(data.timestamp).toLocaleTimeString()}
                                </div>
                            </div>
                        `;
                    })
                    .catch(error => {
                        console.error('Error fetching stats:', error);
                    });
            }
            
            // Update stats immediately and then every 30 seconds
            updateStats();
            setInterval(updateStats, 30000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(template)

@app.route('/api/stats')
def api_stats():
    """API endpoint for system statistics"""
    return jsonify(get_system_stats())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
EOF

# Create systemd service for monitoring dashboard
cat > /etc/systemd/system/ai-trading-monitoring.service << 'EOF'
[Unit]
Description=AI Trading Sentinel Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-trading-sentinel
ExecStart=/usr/bin/python3 /opt/ai-trading-sentinel/scripts/monitoring_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create cron jobs for automated monitoring
echo "# AI Trading Sentinel - Automated Monitoring" > /tmp/ai-trading-cron
echo "# Health check every 5 minutes" >> /tmp/ai-trading-cron
echo "*/5 * * * * /opt/ai-trading-sentinel/scripts/health_check.sh" >> /tmp/ai-trading-cron
echo "# Auto-restart check every 10 minutes" >> /tmp/ai-trading-cron
echo "*/10 * * * * /opt/ai-trading-sentinel/scripts/auto_restart.sh" >> /tmp/ai-trading-cron
echo "# Log rotation daily at 2 AM" >> /tmp/ai-trading-cron
echo "0 2 * * * find /var/log/ai-trading-sentinel -name '*.log' -mtime +7 -delete" >> /tmp/ai-trading-cron

# Install cron jobs
crontab /tmp/ai-trading-cron

# Make scripts executable
chmod +x /opt/ai-trading-sentinel/scripts/*.sh
chmod +x /opt/ai-trading-sentinel/scripts/*.py

# Enable and start monitoring service
systemctl daemon-reload
systemctl enable ai-trading-monitoring
systemctl start ai-trading-monitoring

# Configure log rotation
cat > /etc/logrotate.d/ai-trading-sentinel << 'EOF'
/var/log/ai-trading-sentinel/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload ai-trading-sentinel-backend
    endscript
}
EOF

echo "✅ 24/7 monitoring system setup complete!"
echo ""
echo "📊 Monitoring Dashboard: http://$(curl -s ifconfig.me):3000"
echo "📁 Log Directory: /var/log/ai-trading-sentinel"
echo "🔧 Scripts Directory: /opt/ai-trading-sentinel/scripts"
echo ""
echo "🔍 Manual Commands:"
echo "  Health Check: /opt/ai-trading-sentinel/scripts/health_check.sh"
echo "  Auto Restart: /opt/ai-trading-sentinel/scripts/auto_restart.sh"
echo "  View Logs: tail -f /var/log/ai-trading-sentinel/health_check.log"
echo "  Service Status: systemctl status ai-trading-monitoring"
'@

# Save monitoring setup script
$monitoringConfig | Out-File -FilePath "monitoring_setup.sh" -Encoding UTF8

# Create Windows monitoring script
$windowsMonitoring = @'
# Windows Monitoring Script for AI Trading Sentinel
# Run this locally to monitor the VPS deployment

$VPS_IP = "185.244.214.70"
$FRONTEND_URL = "http://$VPS_IP"
$API_URL = "http://$VPS_IP/api"
$MONITORING_URL = "http://$VPS_IP:3000"

function Test-Endpoint {
    param([string]$Url, [string]$Name)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $Name: OK (Status: $($response.StatusCode))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  $Name: Warning (Status: $($response.StatusCode))" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ $Name: Failed - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-MonitoringStatus {
    Write-Host ""
    Write-Host "🔍 AI Trading Sentinel - Health Check" -ForegroundColor Blue
    Write-Host "====================================" -ForegroundColor Blue
    Write-Host "Time: $(Get-Date)" -ForegroundColor Gray
    Write-Host ""
    
    $frontendOk = Test-Endpoint -Url $FRONTEND_URL -Name "Frontend"
    $apiOk = Test-Endpoint -Url "$API_URL/health" -Name "API Health"
    $monitoringOk = Test-Endpoint -Url $MONITORING_URL -Name "Monitoring Dashboard"
    
    Write-Host ""
    if ($frontendOk -and $apiOk) {
        Write-Host "🎉 System Status: HEALTHY" -ForegroundColor Green
    } else {
        Write-Host "⚠️  System Status: ISSUES DETECTED" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "📊 Access URLs:" -ForegroundColor Cyan
    Write-Host "  Frontend: $FRONTEND_URL" -ForegroundColor White
    Write-Host "  API: $API_URL" -ForegroundColor White
    Write-Host "  Monitoring: $MONITORING_URL" -ForegroundColor White
    Write-Host ""
}

# Continuous monitoring mode
if ($args[0] -eq "-continuous") {
    Write-Host "Starting continuous monitoring (Ctrl+C to stop)..." -ForegroundColor Yellow
    while ($true) {
        Clear-Host
        Show-MonitoringStatus
        Start-Sleep -Seconds 30
    }
} else {
    Show-MonitoringStatus
    Write-Host "💡 Tip: Run with -continuous flag for real-time monitoring" -ForegroundColor Gray
}
'@

# Save Windows monitoring script
$windowsMonitoring | Out-File -FilePath "monitor_vps.ps1" -Encoding UTF8

Write-Info "Creating deployment verification script..."

# Create deployment verification script
$verificationScript = @'
#!/bin/bash
# AI Trading Sentinel - Deployment Verification Script

echo "🔍 AI Trading Sentinel - Deployment Verification"
echo "==============================================="

# Test all endpoints
echo "Testing endpoints..."

# Frontend
if curl -s -f http://localhost/ > /dev/null; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FAILED"
fi

# API Health
if curl -s -f http://localhost/api/health > /dev/null; then
    echo "✅ API Health: OK"
else
    echo "❌ API Health: FAILED"
fi

# Backend direct
if curl -s -f http://localhost:8080/health > /dev/null; then
    echo "✅ Backend Direct: OK"
else
    echo "❌ Backend Direct: FAILED"
fi

# Monitoring Dashboard
if curl -s -f http://localhost:3000/ > /dev/null; then
    echo "✅ Monitoring Dashboard: OK"
else
    echo "❌ Monitoring Dashboard: FAILED"
fi

echo ""
echo "📊 Service Status:"
systemctl is-active ai-trading-sentinel-backend && echo "✅ Backend Service: Running" || echo "❌ Backend Service: Stopped"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Stopped"
systemctl is-active ai-trading-monitoring && echo "✅ Monitoring: Running" || echo "❌ Monitoring: Stopped"

echo ""
echo "🔧 System Resources:"
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "Memory: $(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')%"
echo "Disk: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo ""
echo "📁 Log Files:"
echo "Health Check: /var/log/ai-trading-sentinel/health_check.log"
echo "Auto Restart: /var/log/ai-trading-sentinel/auto_restart.log"
echo "Backend: /var/log/ai-trading-sentinel/backend.log"

echo ""
echo "🌐 External Access:"
echo "Frontend: http://$(curl -s ifconfig.me)/"
echo "API: http://$(curl -s ifconfig.me)/api/"
echo "Monitoring: http://$(curl -s ifconfig.me):3000/"
'@

# Save verification script
$verificationScript | Out-File -FilePath "verify_deployment.sh" -Encoding UTF8

Write-Success "24/7 monitoring setup files created successfully!"

Write-Host ""
Write-Host "📋 MONITORING SETUP INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Upload monitoring files to VPS:"
Write-Host "   - monitoring_setup.sh"
Write-Host "   - verify_deployment.sh"
Write-Host ""
Write-Host "2. Run on VPS:"
Write-Host "   chmod +x monitoring_setup.sh verify_deployment.sh"
Write-Host "   sudo ./monitoring_setup.sh"
Write-Host "   ./verify_deployment.sh"
Write-Host ""
Write-Host "3. Monitor locally (Windows):"
Write-Host "   .\monitor_vps.ps1"
Write-Host "   .\monitor_vps.ps1 -continuous"
Write-Host ""
Write-Host "📊 Monitoring Features:" -ForegroundColor Cyan
Write-Host "  • Health checks every 5 minutes"
Write-Host "  • Auto-restart on failures"
Write-Host "  • Real-time monitoring dashboard"
Write-Host "  • Email and Slack alerts"
Write-Host "  • Log rotation and cleanup"
Write-Host "  • System resource monitoring"
Write-Host ""
Write-Warning "🔧 Configuration Required:"
Write-Host "  1. Update email settings in send_alert.sh"
Write-Host "  2. Configure Slack webhook URL"
Write-Host "  3. Adjust monitoring thresholds as needed"
Write-Host "  4. Test alert notifications"
Write-Host ""
Write-Success "🎉 Ready for 24/7 production deployment!"