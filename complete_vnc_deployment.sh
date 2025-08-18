#!/bin/bash

# AI Trading Sentinel - Complete VNC Deployment Script
# This script completes all remaining deployment tasks via VNC
# Run this script on the VPS via VNC terminal

set -e  # Exit on any error

VPS_IP="161.97.112.146"
WEB_ROOT="/var/www/html"
FRONTEND_ZIP="frontend-cloud.zip"
LOG_FILE="/var/log/deployment.log"

echo "🚀 AI Trading Sentinel - Complete VNC Deployment"
echo "================================================="
echo "VPS IP: $VPS_IP"
echo "Web Root: $WEB_ROOT"
echo "Log File: $LOG_FILE"
echo ""

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check service status
check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        log_message "✅ $service is running"
        return 0
    else
        log_message "❌ $service is not running"
        return 1
    fi
}

# Function to test port connectivity
test_port() {
    local port=$1
    local service=$2
    if netstat -tuln | grep -q ":$port "; then
        log_message "✅ $service: Port $port is listening"
        return 0
    else
        log_message "❌ $service: Port $port is not listening"
        return 1
    fi
}

log_message "Starting complete VNC deployment..."

# STEP 1: System Updates and Dependencies
log_message "📦 STEP 1: System Updates and Dependencies"
echo "----------------------------------------"

sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx unzip wget curl net-tools htop tree

# STEP 2: Verify VNC Server
log_message "🖥️  STEP 2: VNC Server Verification"
echo "----------------------------------"

if check_service "vncserver@1"; then
    log_message "VNC server is running on display :1"
else
    log_message "Starting VNC server..."
    sudo systemctl start vncserver@1
    sudo systemctl enable vncserver@1
fi

test_port 5901 "VNC Server"

# STEP 3: Frontend Upload and Extraction
log_message "📁 STEP 3: Frontend Upload and Extraction"
echo "----------------------------------------"

# Create web directory if it doesn't exist
sudo mkdir -p "$WEB_ROOT"
sudo chown -R www-data:www-data "$WEB_ROOT"
sudo chmod -R 755 "$WEB_ROOT"

# Check if frontend files already exist
if [ -f "$WEB_ROOT/index.html" ]; then
    log_message "Frontend files already exist in $WEB_ROOT"
    log_message "Backing up existing files..."
    sudo mv "$WEB_ROOT" "$WEB_ROOT.backup.$(date +%Y%m%d_%H%M%S)"
    sudo mkdir -p "$WEB_ROOT"
    sudo chown -R www-data:www-data "$WEB_ROOT"
fi

# Instructions for manual frontend upload
echo ""
log_message "📋 FRONTEND UPLOAD INSTRUCTIONS:"
echo "================================="
echo "Since you're using VNC, please follow these steps:"
echo ""
echo "Option A - Local File Server (Recommended):"
echo "1. On your Windows machine, run: python local_file_server.py"
echo "2. In this VNC terminal, run:"
echo "   cd /tmp"
echo "   wget http://YOUR_LOCAL_IP:8000/frontend-cloud.zip"
echo "   sudo unzip frontend-cloud.zip -d $WEB_ROOT/"
echo ""
echo "Option B - Direct Upload via VNC:"
echo "1. Open Firefox in VNC desktop"
echo "2. Download frontend-cloud.zip to /tmp/"
echo "3. Extract: sudo unzip /tmp/frontend-cloud.zip -d $WEB_ROOT/"
echo ""
echo "Option C - GitHub Download:"
echo "1. wget https://github.com/YOUR_USERNAME/ai-trading-sentinel/releases/download/latest/frontend-cloud.zip"
echo "2. sudo unzip frontend-cloud.zip -d $WEB_ROOT/"
echo ""
read -p "Press Enter after you've uploaded and extracted the frontend files..."

# Verify frontend files
if [ -f "$WEB_ROOT/index.html" ]; then
    log_message "✅ Frontend files successfully deployed"
    log_message "Files in $WEB_ROOT:"
    ls -la "$WEB_ROOT" | tee -a "$LOG_FILE"
else
    log_message "❌ Frontend files not found. Please check upload process."
    echo "Current contents of $WEB_ROOT:"
    ls -la "$WEB_ROOT"
fi

# STEP 4: Nginx Configuration for Global Trading Access
log_message "🌐 STEP 4: Nginx Configuration"
echo "------------------------------"

# Backup existing nginx config
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Create optimized Nginx configuration
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    root /var/www/html;
    index index.html index.htm;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Frontend static files
    location / {
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:5000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Security: Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|log|config)$ {
        deny all;
    }
}
EOF

# Test and reload Nginx
log_message "Testing Nginx configuration..."
if sudo nginx -t; then
    log_message "✅ Nginx configuration is valid"
    sudo systemctl reload nginx
    sudo systemctl enable nginx
else
    log_message "❌ Nginx configuration error"
    sudo nginx -t
fi

check_service "nginx"
test_port 80 "Nginx Web Server"

# STEP 5: Flask Backend Setup
log_message "🔌 STEP 5: Flask Backend Setup"
echo "-----------------------------"

# Check if Flask backend is running
if test_port 5000 "Flask Backend"; then
    log_message "Flask backend is already running"
else
    log_message "Flask backend not running. Setting up..."
    
    # Navigate to project directory (assuming it exists)
    if [ -d "/root/ai-trading-sentinel" ]; then
        cd /root/ai-trading-sentinel
        log_message "Found project directory: /root/ai-trading-sentinel"
    elif [ -d "/home/ubuntu/ai-trading-sentinel" ]; then
        cd /home/ubuntu/ai-trading-sentinel
        log_message "Found project directory: /home/ubuntu/ai-trading-sentinel"
    else
        log_message "⚠️  Project directory not found. Please clone the repository first."
        echo "To clone the repository:"
        echo "git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git"
        echo "cd ai-trading-sentinel"
    fi
    
    # Install Python dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        log_message "Installing Python dependencies..."
        pip3 install -r requirements.txt
    fi
    
    # Start Flask backend (this would need to be customized based on your setup)
    log_message "⚠️  Flask backend setup requires manual configuration"
    echo "To start the Flask backend:"
    echo "1. Ensure your Flask app is configured to bind to 0.0.0.0:5000"
    echo "2. Run: python3 app.py (or your main Flask file)"
    echo "3. Or use: gunicorn --bind 0.0.0.0:5000 app:app"
fi

# STEP 6: Firewall Configuration
log_message "🔥 STEP 6: Firewall Configuration"
echo "--------------------------------"

# Configure UFW firewall
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (for future SSL)
sudo ufw allow 5901/tcp  # VNC
sudo ufw allow 5000/tcp  # Flask API (optional, since it's proxied)

sudo ufw status verbose | tee -a "$LOG_FILE"

# STEP 7: System Monitoring Setup
log_message "📊 STEP 7: System Monitoring Setup"
echo "----------------------------------"

# Create monitoring script
sudo tee /usr/local/bin/trading-monitor.sh > /dev/null << 'EOF'
#!/bin/bash
# AI Trading Sentinel Monitoring Script

LOG_FILE="/var/log/trading-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "$DATE - System Health Check" >> "$LOG_FILE"

# Check services
for service in nginx vncserver@1; do
    if systemctl is-active --quiet "$service"; then
        echo "$DATE - ✅ $service: Running" >> "$LOG_FILE"
    else
        echo "$DATE - ❌ $service: Not running" >> "$LOG_FILE"
        # Attempt to restart
        systemctl start "$service"
    fi
done

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$DATE - ⚠️  Disk usage high: ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEM_USAGE" -gt 80 ]; then
    echo "$DATE - ⚠️  Memory usage high: ${MEM_USAGE}%" >> "$LOG_FILE"
fi
EOF

sudo chmod +x /usr/local/bin/trading-monitor.sh

# Add to crontab for regular monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/trading-monitor.sh") | crontab -

log_message "✅ Monitoring script installed and scheduled"

# STEP 8: Final Verification
log_message "🔍 STEP 8: Final Verification"
echo "----------------------------"

echo ""
log_message "🎯 DEPLOYMENT VERIFICATION:"
echo "==========================="

# Test services
echo "Service Status:"
for service in nginx vncserver@1; do
    if check_service "$service"; then
        echo "  ✅ $service"
    else
        echo "  ❌ $service"
    fi
done

echo ""
echo "Port Status:"
test_port 80 "HTTP" && echo "  ✅ HTTP (80)"
test_port 5901 "VNC" && echo "  ✅ VNC (5901)"
test_port 5000 "API" && echo "  ✅ API (5000)" || echo "  ⚠️  API (5000) - May need manual start"

echo ""
echo "File System:"
if [ -f "$WEB_ROOT/index.html" ]; then
    echo "  ✅ Frontend files deployed"
else
    echo "  ❌ Frontend files missing"
fi

echo ""
log_message "🚀 DEPLOYMENT SUMMARY:"
echo "======================"
echo "• VPS IP: $VPS_IP"
echo "• VNC Access: vnc://$VPS_IP:5901"
echo "• Web Access: http://$VPS_IP"
echo "• API Access: http://$VPS_IP/api/health"
echo "• Log File: $LOG_FILE"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Test web access: curl http://$VPS_IP"
echo "2. Start Flask backend if not running"
echo "3. Configure SSL with Let's Encrypt (optional)"
echo "4. Set up automated backups"
echo "5. Configure trading bot credentials"
echo ""
echo "🎉 VNC Deployment Complete!"
echo "Access your AI Trading Sentinel at: http://$VPS_IP"

log_message "VNC deployment script completed successfully"