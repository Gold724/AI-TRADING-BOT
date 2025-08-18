#!/bin/bash

# 🚀 AI Trading Sentinel - Frontend VPS Deployment Script
# Deploy React frontend to Contabo VPS with Nginx

set -e

echo "🚀 Starting Frontend VPS Deployment..."

# Configuration
VPS_IP="161.97.112.146"
VPS_USER="root"
SSH_PORT="22"
FRONTEND_DOMAIN="trading.trae.ai"  # Optional: replace with your domain
NGINX_SITE_PATH="/etc/nginx/sites-available/trae-frontend"
NGINX_ENABLED_PATH="/etc/nginx/sites-enabled/trae-frontend"
WEB_ROOT="/var/www/trae-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if frontend build exists
if [ ! -d "frontend/dist" ]; then
    print_error "Frontend build not found. Please run 'npm run build' in frontend directory first."
    exit 1
fi

print_status "Frontend build found. Proceeding with deployment..."

# Create deployment package
print_status "Creating deployment package..."
tar -czf frontend-dist.tar.gz -C frontend dist/

# Upload frontend build to VPS
print_status "Uploading frontend build to VPS..."
scp -P $SSH_PORT frontend-dist.tar.gz $VPS_USER@$VPS_IP:/tmp/

# SSH into VPS and setup frontend
print_status "Setting up frontend on VPS..."
ssh -p $SSH_PORT $VPS_USER@$VPS_IP << 'EOF'
set -e

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    apt update
    apt install -y nginx
    systemctl enable nginx
fi

# Create web root directory
sudo mkdir -p /var/www/trae-frontend

# Extract frontend build
cd /tmp
tar -xzf frontend-dist.tar.gz
sudo cp -r dist/* /var/www/trae-frontend/
sudo chown -R www-data:www-data /var/www/trae-frontend
sudo chmod -R 755 /var/www/trae-frontend

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/trae-frontend > /dev/null << 'NGINX_CONFIG'
server {
    listen 80;
    listen [::]:80;
    
    server_name 161.97.112.146 trading.trae.ai;
    root /var/www/trae-frontend;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Handle React Router (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket proxy for real-time updates
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
    
    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Deny access to hidden files
    location ~ /\. {
        deny all;
    }
}
NGINX_CONFIG

# Enable the site
sudo ln -sf /etc/nginx/sites-available/trae-frontend /etc/nginx/sites-enabled/

# Remove default Nginx site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager

# Configure firewall for HTTP/HTTPS
echo "Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Cleanup
rm -f /tmp/frontend-dist.tar.gz

echo "✅ Frontend deployment completed successfully!"
echo "🌐 Frontend is now accessible at: http://161.97.112.146"
echo "🔧 Backend API accessible at: http://161.97.112.146/api/"
echo "📡 WebSocket endpoint: ws://161.97.112.146/ws"
EOF

# Cleanup local files
rm -f frontend-dist.tar.gz

print_success "Frontend deployment completed!"
print_success "🌐 Frontend URL: http://$VPS_IP"
print_success "🔧 API URL: http://$VPS_IP/api/"
print_success "📡 WebSocket: ws://$VPS_IP/ws"

print_status "Testing frontend accessibility..."
curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP/ && echo " - Frontend: ✅ Accessible" || echo " - Frontend: ❌ Not accessible"
curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP/api/health && echo " - API: ✅ Accessible" || echo " - API: ❌ Not accessible"

print_success "🚀 AI Trading Sentinel is now fully deployed in the cloud!"
echo ""
echo "📋 Access Points:"
echo "   Frontend: http://$VPS_IP"
echo "   API: http://$VPS_IP/api/"
echo "   Health: http://$VPS_IP/api/health"
echo ""
echo "🔧 Management Commands:"
echo "   sudo systemctl status nginx"
echo "   sudo systemctl status trae-backend"
echo "   sudo tail -f /var/log/nginx/access.log"
echo "   sudo tail -f /var/log/nginx/error.log"