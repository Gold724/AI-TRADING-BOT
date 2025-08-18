#!/bin/bash

# =============================================================================
# VNC Frontend Deployment Script for AI Trading Sentinel
# Automates: VNC connection, frontend upload, Nginx config, web testing
# Target: Contabo VPS 161.97.112.146
# =============================================================================

set -e  # Exit on any error

VPS_IP="161.97.112.146"
VNC_PORT="5901"
WEB_PORT="80"
FRONTEND_ZIP="frontend-cloud.zip"
WEB_ROOT="/var/www/html"

echo "🚀 AI Trading Sentinel - VNC Frontend Deployment"
echo "================================================="
echo "VPS Target: $VPS_IP"
echo "VNC Access: $VPS_IP:$VNC_PORT"
echo "Web Access: http://$VPS_IP"
echo ""

# Step 1: VNC Connection Instructions
echo "📡 STEP 1: VNC Connection Setup"
echo "------------------------------"
echo "1. Download VNC Viewer: https://www.realvnc.com/en/connect/download/viewer/"
echo "2. Connect to: $VPS_IP:$VNC_PORT"
echo "3. Enter VNC password when prompted"
echo "4. You should see XFCE4 desktop environment"
echo ""
echo "⚠️  Manual Action Required: Connect via VNC Viewer before proceeding"
echo "Press ENTER when VNC connection is established..."
read -p ""

# Step 2: Frontend Upload Commands (to be executed in VNC terminal)
echo "📦 STEP 2: Frontend Upload Commands"
echo "----------------------------------"
echo "Execute these commands in VNC terminal:"
echo ""
cat << 'EOF'
# Navigate to web root
sudo mkdir -p /var/www/html
cd /var/www/html

# Remove existing files
sudo rm -rf *

# Upload frontend-cloud.zip (use file manager or wget)
# Option A: If you have the zip locally in VNC
sudo cp /path/to/frontend-cloud.zip .

# Option B: Download from local machine (if accessible)
# wget http://your-local-ip/frontend-cloud.zip

# Extract frontend
sudo unzip frontend-cloud.zip
sudo rm frontend-cloud.zip

# Set proper permissions
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html

# Verify extraction
ls -la /var/www/html
EOF

echo ""
echo "⚠️  Manual Action Required: Execute above commands in VNC terminal"
echo "Press ENTER when frontend upload is complete..."
read -p ""

# Step 3: Nginx Configuration
echo "🔧 STEP 3: Nginx Configuration"
echo "------------------------------"
echo "Execute these commands in VNC terminal:"
echo ""
cat << 'EOF'
# Create Nginx configuration for trading frontend
sudo tee /etc/nginx/sites-available/trading-frontend << 'NGINX_EOF'
server {
    listen 80;
    server_name 161.97.112.146;
    root /var/www/html;
    index index.html index.htm;

    # Frontend static files
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support for real-time updates
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;
}
NGINX_EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/trading-frontend /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Check Nginx status
sudo systemctl status nginx
EOF

echo ""
echo "⚠️  Manual Action Required: Execute above Nginx commands in VNC terminal"
echo "Press ENTER when Nginx configuration is complete..."
read -p ""

# Step 4: Web Access Testing
echo "🌐 STEP 4: Web Access Testing"
echo "-----------------------------"
echo "Testing web access to http://$VPS_IP"
echo ""

# Test from VNC terminal
echo "Execute these test commands in VNC terminal:"
echo ""
cat << 'EOF'
# Test local access
curl -I http://localhost
curl -I http://161.97.112.146

# Check if frontend files are served
curl -s http://localhost | head -20

# Test API endpoint
curl -I http://localhost/api/health

# Check Nginx error logs if issues
sudo tail -f /var/log/nginx/error.log
EOF

echo ""
echo "🎯 DEPLOYMENT VERIFICATION"
echo "=========================="
echo "1. Open browser and navigate to: http://$VPS_IP"
echo "2. You should see the AI Trading Sentinel dashboard"
echo "3. Verify API connectivity and real-time updates"
echo "4. Test trading bot controls (start/stop/status)"
echo ""
echo "✅ If successful, your AI Trading Sentinel is globally accessible!"
echo "🔒 Security: Consider setting up HTTPS with Let's Encrypt for production"
echo "📊 Monitoring: Check logs at /var/log/nginx/ for access patterns"
echo ""
echo "🚀 Global Trading Access: http://$VPS_IP"
echo "🎮 VNC Management: $VPS_IP:$VNC_PORT"
echo "🔧 Backend API: http://$VPS_IP/api/"
echo ""
echo "Deployment script completed! 🎉"